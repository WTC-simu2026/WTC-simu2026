"""Declared alternative metal solid-shell; no artificial rotational inertia or mass scaling."""
from run_aircraft_a26 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories,OUT
from run_aircraft_a23 import brick_grid
import run_aircraft_a26 as A26
import inspect,argparse,shutil,re,traceback
from pathlib import Path
import numpy as np
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a26_solidshell_w2.json'

def declare():
    assert not CFG.exists();h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_solidshell.json',h)
    c=read(A26.CFG);c.update(revision='w1',declared_utc=now(),parent_configuration_sha256=streamsha(A26.CFG),purpose='Alternative HA8 solid-shell metal plate: preserve physical volume/material/mass, translations only. DKT w0 angular checks pass but zero-P absolute gate and bending native work balance fail; preserve those failures.',
      cases=['FREE_ROTATION_X_N12','FREE_ROTATION_Y_N12','FREE_ROTATION_Z_N12','FREE_TRANSLATION_N12','FREE_ROTATION_Y_N12_HALF','MEMBRANE_N6','MEMBRANE_N12','BENDING_N6','BENDING_N12'],
      changes={'property':'TYPE20 HA8 Isolid14 Ismstr4 Icstr010 Inpts222, standard thickness bottom-to-top s direction per official documentation. No independently rotating nodes. Native readback and geometry record required.','mesh':'NxNx1 through thickness, matched50mm3 at N6/N12. Lumped nodal masses integrate all hexa volumes, physical continuum tensor is separate. One thickness layer; no exact continuum inertia claim.','material':'identical LAW2 metal card. No LAW25/composite conversion.','reference':'3D uniaxial affine elastic field, then plane-stress cylindrical bending with through-thickness displacement. E/nu/thickness preserved; independent analytic energy, all volume compared.','bending':'ux=-k*x*z-k²*x³/6; uy=0; uz=k*x²/2+nu/(1-nu)*k*z²/2. Plane stress sigma_z=0 to first order, curvature_y=0.'},
      objective1_complete=False,whole_insertion_ready=False)
    dump(CFG,c);dump(OUT/'solidshell_w2_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True});source=OUT/'sources/tshell.html';assert not source.exists();shutil.copy2(ROOT/'wtc1_simulation_v8/output/aircraft_a25/sources/tshell.html',source);dump(OUT/'solidshell_sources.json',{'created_utc':now(),'files':[{'path':rel(source),'sha256':streamsha(source),'bytes':source.stat().st_size,'url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type20_tshell_starter_r.htm','redistribution':'exclude_third_party'}],'material_source_addendum':rel(OUT/'material_source_addendum.json')});print({'A26_w1_declared':True,'native_cases':9,'CPU_minutes':[3,8]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'solidshell_w2_guard.json')['sha256']

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;cache={};counter=10000
    for ni,q in enumerate(X,1):
        x,y,z=q;L+=group(ni,f'PRESCRIBED_NODE_{ni}',[ni]);D=np.array([.001*x,-.00033*y,-.00033*z]) if cid.startswith('MEMBRANE') else np.array([-.001*x*z-.001**2*x**3/6,0,.001*x*x/2+.33/(1-.33)*.001*z*z/2])
        for a,direction in enumerate('XYZ'):
            val=D[a]*s;key=val.tobytes()
            if key not in cache:
                counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}',f'KNOWN_DISPLACEMENT_{counter}']+[ff(t,v) for t,v in zip(T,val)]
            fid=cache[key];counter+=1;L+=[f'/IMPDISP/{counter}',f'PRESCRIBED_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def review(d,n):
    # Reuse the original energy, mass, inertia and momentum gates verbatim; compare new volume's bending rather than DKT interior subset.
    s=inspect.getsource(A26.review)
    s=s.replace("m=np.asarray(g['known_nodal_masses_g'])","m=np.asarray(g['known_nodal_masses_g'])")
    old="area=(10*(g['mesh_n']-2)/g['mesh_n'])**2;D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*area*.001;actual=float(next(v[-1]*.001 for k,v in H.items() if k.startswith('PLATE_INTERIOR') and k.strip().endswith('IE')))"
    assert s.count(old)==1;s=s.replace(old,"D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*100*.001;actual=float(IE[-1])")
    namespace=dict(globals());exec(compile(s,__file__+'::review','exec'),namespace);namespace['review'](d,n)
    p=OUT/'solidshell_w2_review_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(A26.__file__)),'sha256':streamsha(Path(A26.__file__)),'only_reference_scope_changed':'Full volume HA8 solid-shell rather than interior DKT triangle patch','derived_source':s,'acceptance_thresholds_unchanged':True})

def run_one(cid):
    guard();ncell=int(re.search(r'_N(6|12)',cid).group(1));X,b,m,left,right=brick_grid([ncell,ncell,1],[-5,-5,-.25],[5,5,.25]);free=cid.startswith('FREE');half=cid.endswith('_HALF');duration=.05 if free else .1;d=OUT/'w2'/cid;n='A26_HA8_'+cid;assert not d.exists();d.mkdir(parents=True);P=parent();prop=['/PROP/TYPE20/1','HALF_MM_HA8_SOLID_SHELL_TRANSLATIONS',ii(14,4)+' '*20+ii(10,222)+' '*20+ff(0),ff(0,0,0),ff(0,0,0,0,0),' '*20+ii(2)];materials=P['/MAT/LAW2/1']+prop+['/PART/1','METAL_FULL_VOLUME',ii(1,1,0),'/BRICK/1']+[ii(j+1,*conn) for j,conn in enumerate(b)];L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(X)]+materials;omega=np.zeros(3);V=np.zeros_like(X)
    if free:
        omega=np.eye(3)['XYZ'.index(re.search('ROTATION_([XYZ])',cid).group(1))]*10 if 'ROTATION' in cid else np.zeros(3);V=np.cross(omega,X) if 'ROTATION' in cid else np.tile([-200,5,2],(len(X),1))
        for ni,v in enumerate(V,1):L+=group(ni,f'INITIAL_NODE_{ni}',[ni])+[f'/INIVEL/TRA/{ni}','INITIAL_TRANSLATIONAL_VELOCITY',ff(*v)+ii(ni,0),ff(0)+ii(0)]
    else:L=imposed(L,X,cid)
    L+=['/TH/PART/1','VOLUME_SCOPE',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(1),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(i,0) for i in range(1,len(X)+1)]+['/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8');E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/ANIM/BRICK/TENS/STRESS','/DT',ff(.2 if half else .4,0),'/DTIX',ff(.0000125 if half else .000025,.0000125 if half else .000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(duration),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'case':cid,'name':n,'mesh_n':ncell,'free':free,'duration_ms':duration,'nodes_mm':X.tolist(),'bricks':b,'known_nodal_masses_g':m.tolist(),'known_mass_g':float(m.sum()),'initial_velocity_m_s':V.tolist(),'initial_omega_rad_ms':omega.tolist(),'physical_plate_dimensions_mm':[10,10,.5],'TYPE20':True,'Icstr':10,'rotational_initial_conditions':False,'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__))});en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',600,en);t=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',t)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',t)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,t[-4000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',600,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',600,en);review(d,n)
    except Exception:dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'whole_insertion_ready':False});raise

def run():
    guard()
    for cid in read(CFG)['cases']:
        d=OUT/'w2'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
    dump(OUT/'native_case_summary_w2.json',{'created_utc':now(),'cases':[read(OUT/'w2'/cid/'review.json') for cid in read(CFG)['cases']],'whole_insertion_ready':False,'composite_and_curved_root_not_qualified':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
