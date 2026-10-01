"""New coupled shell/zero-length joint verification decks; immutable case dirs."""
from __future__ import annotations
import argparse, hashlib, json, math, os, subprocess, time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/impact_i02c_deformable_joint.json'
RUNTIME=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def f(*v):return ''.join(f'{x:20.12g}' if isinstance(x,(int,float)) else f'{x:>20}' for x in v)
def i(*v):return ''.join(f'{x:10d}' if isinstance(x,int) else f'{x:>10}' for x in v)

def generate(cfg,c,directory):
    g=cfg['geometry'];mat=cfg['material'];joint=cfg['joint']; ex=cfg['execution']
    L=g['strip_length_mm'];b=g['width_mm'];nx=math.ceil(L/c['h_mm']);ny=math.ceil(b/c['h_mm'])
    angle=math.radians(c.get('rotation_deg',0));R=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1.]])
    # Keep exact 90-degree mappings to make frame verification unambiguous.
    R[abs(R)<1e-14]=0
    normal=c['mode']=='normal'; axis=2 if normal else (1 if c.get('rotation_deg',0)==90 else 0)
    local_axis=2 if normal else 0; direction='XYZ'[axis]
    nodes=[];quads=[];parts=[];grids=[];weights=[];links=[];lumps=[]
    for part,(xa,xb,thick) in enumerate([(-L,0,g['skin_thickness_mm']),(0,L,g['flange_thickness_mm'])],1):
        grid=[]
        for x in np.linspace(xa,xb,nx+1):
            row=[]
            for y in np.linspace(-b/2,b/2,ny+1):
                row.append(len(nodes)+1); nodes.append((R@np.array([x,y,0])).tolist());lumps.append(0.)
            grid.append(row)
        for ix in range(nx):
            for iy in range(ny):
                q=[grid[ix][iy],grid[ix+1][iy],grid[ix+1][iy+1],grid[ix][iy+1]]
                quads.append(q);parts.append(part)
                mass=mat['rho_g_mm3']*L/nx*b/ny*thick
                for n in q:lumps[n-1]+=mass/4
        grids.append(grid)
    for j,(n1,n2) in enumerate(zip(grids[0][-1],grids[1][0])):
        links.append([n1,n2]);weights.append(b/ny/g['rivet_pitch_mm']*(.5 if j in (0,ny) else 1))
    fixed=grids[0][0]; moving=grids[1][-1]; allnodes=list(range(1,len(nodes)+1))
    rightnodes=[n for row in grids[1] for n in row]
    free=c['loading']=='free';dynamic=c['loading']=='dynamic'
    name='I02C_'+c['id']; peak=joint['normal_Fp_N' if normal else 'tangent_Fp_N']; d0=joint['d0_mm'];df=joint['df_mm'][c.get('energy','base')]
    lines=['#RADIOSS STARTER','/BEGIN',name,i(2026,0),f('g','mm','ms'),f('g','mm','ms'),'/TITLE',name,'/ANALY',i(0,'',0,0),'/SPMD',i(0,0)+f(0,1),
           '/MAT/ELAST/1','GENERIC_ELASTIC_NO_SHELL_FAILURE',f(mat['rho_g_mm3']),f(mat['E_MPa'],mat['nu']),
           '/SKEW/FIX/1','STRIP_AXES_FIXED',f(0,0,0),f(*R[:,1].tolist()),f(*R[:,2].tolist()),'/NODE']
    lines += [i(n)+f(*p) for n,p in enumerate(nodes,1)]
    for pid,thick in [(1,g['skin_thickness_mm']),(2,g['flange_thickness_mm'])]:
        lines += [f'/PART/{pid}',f'ELASTIC_STRIP_{pid}',i(pid,1,0),f'/PROP/SHELL/{pid}','FULLY_INTEGRATED_ELASTIC',
                  i(24,-1,0,0,0,'')+f(0),f(0,0,0,0,0),i(0,'')+f(thick),f'/SHELL/{pid}']
        lines += [i(e,*q) for e,(q,p) in enumerate(zip(quads,parts),1) if p==pid]
    springids=[]
    for j,((n1,n2),w) in enumerate(zip(links,weights)):
        pid=10+j;eid=len(quads)+j+1;springids.append(eid)
        lines += [f'/PART/{pid}',f'WEIGHTED_SEAM_{j}',i(pid,0,0),f'/PROP/TYPE8/{pid}','ZERO_LENGTH_SINGLE_MODE_H2',f(0,0)+i(1,0,0,0,0,1)]
        for a in range(6):
            active=a==local_axis
            lines += [f(peak/d0*w*c.get('stiffness_pad',1) if active else 0,0,1,0,1),
                      i(100+j if active else 0,2 if active else 0,0,0,0,'')+f(-1e30,df if active else 1e30),f(1,0,1,0)]
        lines += [i(0)+f(1e30),f'/FUNCT/{100+j}',f'JOINT_ENVELOPE_{j}']
        lines += [f(x,y*w) for x,y in [(-100,0),(0,0),(d0,peak),(df,0),(100,0)]]
        lines += [f'/SPRING/{pid}',i(eid,n1,n2,0,0,0,0,'','',1)]
    groups={1:allnodes,2:fixed,3:moving,4:rightnodes}
    for gid,nodelist in groups.items():
        lines += [f'/GRNOD/NODE/{gid}',f'GROUP_{gid}']
        for start in range(0,len(nodelist),10):lines.append(i(*nodelist[start:start+10]))
    trans=list('111');trans[axis]='0';rots=list('111')
    if normal:rots[1]='0'
    lines += ['/BCS/1','PLANE_STRAIN_MODE_CONSTRAINT',f"{''.join(trans):>6}{''.join(rots):>4}"+i(0,1)]
    if not free:
        # Only the remaining free DOFs here: no duplicate blocked translations.
        t=list('000');t[axis]='1';r=list('000')
        if normal:r[1]='1'
        lines += ['/BCS/2','LEFT_GRIP',f"{''.join(t):>6}{''.join(r):>4}"+i(0,2)]
    if normal:
        lines += ['/BCS/3','RIGHT_GRIP_ROTATION',f"{'000':>6}{'010':>4}"+i(0,3)]
    if free or dynamic:
        end=c.get('end_ms',.4) if dynamic else .2
        m=sum(lumps[n-1] for n in (rightnodes if dynamic else allnodes))
        vel=math.sqrt(2000*c['initial_energy_J']/m) if dynamic else c['velocity_m_s']
        v=[0.,0.,0.];v[axis]=vel
        lines += ['/INIVEL/TRA/1','INITIAL_MOMENTUM',f(*v)+i(4 if dynamic else 1,0),f(0)+i(0)]
        path=[]
    else:
        if normal:path=[(0,0),(8,.01),(10,.01)]
        elif c['loading']=='elastic':path=[(0,0),(1,.01),(1.2,.01)]
        elif c['loading']=='cycle':path=[(0,0),(1,.30),(2,c.get('minimum_grip_mm',0)),(3,.30),(4,1.15),(4.2,1.15),(5.2,c.get('minimum_grip_mm',0)),(6.2,.30),(6.4,.30)]
        else:path=[(0,0),(1,1.15),(1.2,1.15)]
        end=path[-1][0];smooth=[]
        for (ta,da),(tb,db) in zip(path[:-1],path[1:]):
            for u in np.linspace(0,1,2000,endpoint=False):smooth.append((float(ta+(tb-ta)*u),float(da+(db-da)*(3*u*u-2*u*u*u))))
        smooth.append(path[-1]);lines+=['/FUNCT/90','SMOOTH_GRIP_DISPLACEMENT']+[f(t,d) for t,d in smooth]
        lines+=['/IMPDISP/1','RIGHT_GRIP_DISPLACEMENT',i(90,direction,0,0,3,'',0),f(1,1,0,1e30)]
    lines+=['/TH/SPRING/1','JOINT_HISTORY',i('OFF','FX','FY','FZ','LX','LY','LZ','IE')]
    lines += [i(e,'')+f'JOINT_{j}' for j,e in enumerate(springids)]
    lines+=['/TH/NODE/2','NODE_HISTORY',i('D'+direction,'V'+direction,'REAC'+direction)]
    lines += [i(n,0) for n in allnodes]
    lines+=['/TH/PART/3','STRIP_HISTORY',i('IE','KE','MASS','HE'),i(1,2),'/END']
    (directory/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    hdt=ex['dynamic_history_dt_ms'] if dynamic else ex['normal_history_dt_ms'] if normal else ex['history_dt_ms']
    dt=ex['maximum_dt_ms']*c.get('dt_factor',1)
    engine=['/ANIM/DT',f(0,end/(ex['animation_states']-1)),'/ANIM/VECT/DISP','/ANIM/VECT/VEL',
            '/DT',f(ex['dt_scale'],0),'/DTIX',f(dt,dt),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',f(end),'/TFILE/4',f(hdt),'/VERS/2026']
    (directory/(name+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8')
    meta={'name':name,'case':c,'nodes_mm':nodes,'quads':quads,'parts':parts,'links':links,'weights':weights,'spring_ids':springids,'nodal_mass_g':lumps,
          'fixed_nodes':[] if free else fixed,'moving_nodes':moving,'right_nodes':rightnodes,'axis':axis,'local_axis':local_axis,'rotation':R.tolist(),
          'peak_N':peak,'d0_mm':d0,'df_mm':df,'full_joint_energy_J':.5*peak*df*.001*sum(weights),'initial_mass_g':sum(lumps),'end_ms':end,'history_dt_ms':hdt,'path':path}
    dump(directory/'generation.json',meta);return meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--revision',default='R0');a=p.parse_args()
    cfg=json.loads(CONFIG.read_text());c=next(c for c in cfg['cases'] if c['id']==a.case).copy();c['id']=c['id'].replace('_R0','_'+a.revision)
    c['stiffness_pad']=1.00000001 if a.revision in ('R2','R3') else 1.0
    if a.revision=='R3':
        c['minimum_grip_mm']=.05
        if c['id'].startswith('DYN_LOW_'):c['end_ms']=.032
        if c['id'].startswith('DYN_G_HIGH_'):c['end_ms']=.21
    directory=ROOT/cfg['output_root']/c['id']
    if directory.exists():raise RuntimeError('Existing case preserved: '+str(directory))
    directory.mkdir(parents=True);meta=generate(cfg,c,directory)
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m')
    records=[]
    for exe,args,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
        cmd=[str(RUNTIME/exe),*args];start=time.perf_counter()
        proc=subprocess.run(cmd,cwd=directory,env=env,capture_output=True,timeout=cfg['execution']['maximum_case_wall_seconds'])
        (directory/log).write_bytes(proc.stdout+proc.stderr)
        records.append({'command':cmd,'returncode':proc.returncode,'seconds':time.perf_counter()-start,'executable_sha256':sha(RUNTIME/exe)});dump(directory/'execution.json',records)
        if proc.returncode:raise RuntimeError(str(directory/log))
    print(json.dumps({'case':c['id'],'seconds':sum(r['seconds'] for r in records),'nodes':len(meta['nodes_mm']),'shells':len(meta['quads'])}))
if __name__=='__main__':main()
