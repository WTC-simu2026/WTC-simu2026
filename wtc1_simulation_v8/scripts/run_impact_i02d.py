"""Immutable eccentric shell/cohesive verification decks, g-mm-ms-N units."""
from __future__ import annotations
import argparse,json,math,os,subprocess,time
from pathlib import Path
import numpy as np
from run_impact_i02c import f,i,sha,dump,RUNTIME,ROOT
from generate_v8v_deformable_projectile import type7_lines
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02d_lap_joint.json'

def generate(cfg,c,d):
    g=cfg['geometry'];m=cfg['material'];j=cfg['joint'];ex=cfg['execution'];patch=c['geometry']=='patch'
    a=g['overlap_mm']/2;b=g['width_mm'];L=g['grip_x_mm'];h=c['h_mm'];ny=math.ceil(b/h)
    angle=math.radians(c.get('rotation_deg',0));R=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1.]])
    R[abs(R)<1e-14]=0
    nodes=[];quads=[];parts=[];grids=[];lumps=[];bricks=[];areas=[]
    xs0=np.linspace(-a,a,math.ceil(2*a/h)+1)
    for p,z,t in [(1,0,g['skin_thickness_mm']),(2,g['midplane_offset_mm'],g['flange_thickness_mm'])]:
        xs=xs0 if patch else np.r_[np.linspace(-L,-a,math.ceil((L-a)/h)+1)[:-1],xs0] if p==1 else np.r_[xs0,np.linspace(a,L,math.ceil((L-a)/h)+1)[1:]]
        grid={}
        for ix,x in enumerate(xs):
            for iy,y in enumerate(np.linspace(-b/2,b/2,ny+1)):
                grid[ix,iy]=len(nodes)+1;nodes.append((R@np.array([x,y,z])).tolist());lumps.append(0.)
        for ix in range(len(xs)-1):
            for iy in range(ny):
                q=[grid[ix,iy],grid[ix+1,iy],grid[ix+1,iy+1],grid[ix,iy+1]];quads.append(q);parts.append(p)
                mass=m['rho_g_mm3']*(xs[ix+1]-xs[ix])*b/ny*t
                for n in q:lumps[n-1]+=mass/4
        grids.append((xs,grid))
    for ix in range(len(xs0)-1):
        for iy in range(ny):
            faces=[]
            for xs,grid in grids:
                k=int(np.argmin(abs(xs-xs0[ix])));faces.extend([grid[k,iy],grid[k+1,iy],grid[k+1,iy+1],grid[k,iy+1]])
            bricks.append(faces);area=(xs0[ix+1]-xs0[ix])*b/ny;areas.append(area)
            for n in faces:lumps[n-1]+=j['rho_g_mm3']*area/8
    xs,grid=grids[0];left=list(grid.values()) if patch else [grid[0,k] for k in range(ny+1)]
    xs,grid=grids[1];right=list(grid.values()) if patch else [grid[len(xs)-1,k] for k in range(ny+1)]
    allnodes=list(range(1,len(nodes)+1));top=list(grids[1][1].values());name='I02D_'+c['id']
    lines=['#RADIOSS STARTER','/BEGIN',name,i(2026,0),f('g','mm','ms'),f('g','mm','ms'),'/TITLE',name,'/ANALY',i(0,'',0,0),'/SPMD',i(0,0)+f(0,1),
           '/MAT/ELAST/1','GENERIC_ELASTIC_SHELLS',f(m['rho_g_mm3']),f(m['E_MPa'],m['nu']),'/MAT/LAW117/2','SMEARED_CONNECTION_HYPOTHESIS',f(j['rho_g_mm3']),
           f(j['normal_Fp_N']/j['d0_mm']/(2*a*b),j['tangent_Fp_N']/j['d0_mm']/(2*a*b))+i(1,4,2),
           i(0,0)+f(j['normal_Fp_N']/(2*a*b),j['tangent_Fp_N']/(2*a*b),1),
           f(.5*j['normal_Fp_N']*j['df_mm']/(2*a*b),.5*j['tangent_Fp_N']*j['df_mm']/(2*a*b),2,1,1),'/NODE']
    lines += [i(n)+f(*p) for n,p in enumerate(nodes,1)]
    for pid,thick in [(1,g['skin_thickness_mm']),(2,g['flange_thickness_mm'])]:
        lines += [f'/PART/{pid}',f'ELASTIC_STRIP_{pid}',i(pid,1,0),f'/PROP/SHELL/{pid}','FULLY_INTEGRATED_ELASTIC',i(24,-1,0,0,0,'')+f(0),f(0,0,0,0,0),i(0,'')+f(thick),f'/SHELL/{pid}']
        lines += [i(e,*q) for e,(q,p) in enumerate(zip(quads,parts),1) if p==pid]
    lines += ['/PART/3','COHESIVE_PATCH',i(3,2,0),'/PROP/TYPE43/3','FULL_NONLINEAR_COHESIVE',i(4,'','','','','','','')+f(cfg['cohesive_reference_thickness_mm']),'/BRICK/3']
    lines += [i(len(quads)+k+1,*q) for k,q in enumerate(bricks)]
    for gid,group in {1:allnodes,2:left,3:right,4:top}.items():
        lines += [f'/GRNOD/NODE/{gid}',f'GROUP_{gid}']
        lines += [i(*group[k:k+10]) for k in range(0,len(group),10)]
    lines += ['/BCS/1','LEFT_GRIP',f"{'111':>6}{'111':>4}"+i(0,2)]
    axis=1 if c.get('rotation_deg',0)==90 else 0
    trans=list('111');trans[axis]='0';trans[2]='0'
    lines += ['/BCS/2','RIGHT_GRIP_COMPLEMENT',f"{''.join(trans):>6}{'111':>4}"+i(0,3)]
    for k,axisid in enumerate([axis,2]):
        curve=[]
        for pa,pb in zip(c['path'][:-1],c['path'][1:]):
            for u in np.linspace(0,1,2000,endpoint=False):curve.append((float(pa[0]+(pb[0]-pa[0])*u),float(pa[k+1]+(pb[k+1]-pa[k+1])*(3*u*u-2*u*u*u))))
        curve.append((c['path'][-1][0],c['path'][-1][k+1]))
        lines += [f'/FUNCT/{90+k}',f'GRIP_DISPLACEMENT_{k}']+[f(t,x) for t,x in curve]
        lines += [f'/IMPDISP/{k+1}',f'GRIP_{k}',i(90+k,'XYZ'[axisid],0,0,3,'',0),f(1,1,0,1e30)]
    if c.get('contact'):
        lines += ['/SURF/PART/30','LOWER_SHELL_CONTACT',i(1)]
        contact=type7_lines(1,'INDEPENDENT_AFTER_FAILURE_CONTACT',4,30)
        contact[2]=i(4,30,4,0,1000,'',0,1000,0,0)
        contact[5]=f(cfg['contact']['stiffness_scale'],0,cfg['contact']['gap_mm'],0,1e30)
        contact[6]=f"{'':7}{0:1d}{0:1d}{0:1d}{'':20}{1000:10d}"+f(cfg['contact']['vis_s'],0,.2)
        lines += contact
    lines += ['/TH/PART/1','PART_HISTORY',i('IE','KE','MASS','HE'),i(1,2,3),'/TH/NODE/2','NODE_HISTORY',i('D','V','VR','REACX','REACY','REACZ','REACXX','REACYY','REACZZ')]
    lines += [i(n,0) for n in allnodes]
    lines += ['/TH/BRIC/3','COHESIVE_HISTORY',i('OFF','LOCSTRS','IE')]
    lines += [i(len(quads)+k+1) for k in range(len(bricks))]
    lines += ['/END']
    (d/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    end=c['path'][-1][0];dt=ex['maximum_dt_ms']*c.get('dt_factor',1)
    eng=['/ANIM/DT',f(0,end/(ex['animation_states']-1)),'/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/BRICK/DAMA','/DT',f(ex['dt_scale'],0),'/DTIX',f(dt,dt),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',f(end),'/TFILE/4',f(ex['history_dt_ms']),'/VERS/2026']
    (d/(name+'_0001.rad')).write_text('\n'.join(eng)+'\n',encoding='utf-8')
    meta={'name':name,'case':c,'nodes_mm':nodes,'quads':quads,'parts':parts,'bricks':bricks,'areas_mm2':areas,'nodal_mass_g':lumps,'initial_mass_g':sum(lumps),'cohesive_mass_g':j['rho_g_mm3']*2*a*b,'left':left,'right':right,'top':top,'rotation':R.tolist(),'axis':axis,'end_ms':end,'history_dt_ms':ex['history_dt_ms'],'config_snapshot':cfg,'generator_sha256':sha(Path(__file__))}
    dump(d/'generation.json',meta);return meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--revision',default='R1');a=p.parse_args();cfg=json.loads(CFG.read_text());c=next(c for c in cfg['cases'] if c['id']==a.case).copy();c['id']=c['id'].replace('_R0','_'+a.revision)
    d=ROOT/cfg['output_root']/c['id']
    if d.exists():raise RuntimeError('Existing case preserved '+str(d))
    d.mkdir(parents=True);meta=generate(cfg,c,d);env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m')
    rec=[]
    for exe,args,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
        command=[str(RUNTIME/exe),*args];start=time.perf_counter();proc=subprocess.run(command,cwd=d,env=env,capture_output=True,timeout=cfg['execution']['maximum_case_wall_seconds'])
        (d/log).write_bytes(proc.stdout+proc.stderr);rec.append({'command':command,'returncode':proc.returncode,'seconds':time.perf_counter()-start,'executable_sha256':sha(RUNTIME/exe)});dump(d/'execution.json',rec)
        if proc.returncode:raise RuntimeError(str(d/log))
    print(json.dumps({'case':c['id'],'seconds':sum(r['seconds'] for r in rec),'nodes':len(meta['nodes_mm']),'shells':len(meta['quads']),'cohesive_bricks':len(meta['bricks'])}))
if __name__=='__main__':main()
