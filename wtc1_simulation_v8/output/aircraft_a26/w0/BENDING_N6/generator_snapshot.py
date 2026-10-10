"""Metal DKT_S3 translation-only plate, independent inertial and elastic controls."""
from run_aircraft_a25 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories
import argparse,json,shutil,re,traceback,time,urllib.request
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a26'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a26_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a25'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A25';OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={'iteration':'AIRCRAFT-A26','declared_utc':now(),'seed':1102051,'random_draws':0,'purpose':'Test DKT_S3 (Ish3n31) plate with translations only, bending from neighboring out-of-plane nodal displacements. No inferred shell rotational inertia or repaired RKE. Before composite/core/root integration.',
      'plate':{'bounds_mm':[[-5,-5,0],[5,5,0]],'thickness_mm':.5,'volume_mm3':50,'rho_g_mm3':.00278,'mass_g':.139,'E_MPa':73100,'nu':.33,'yield_MPa':324,'hardening':0,'fracture':'absent inherited LAW2','formulation':'TYPE1 Ish3n31 DKT_S3; same LAW2 card, triangular mesh, no rotational initial conditions'},
      'cases':['FREE_ROTATION_X_N12','FREE_ROTATION_Y_N12','FREE_ROTATION_Z_N12','FREE_TRANSLATION_N12','FREE_ROTATION_Y_N12_HALF','MEMBRANE_N6','MEMBRANE_N12','BENDING_N6','BENDING_N12'],
      'motion':{'free_duration_ms':.05,'free_omega_rad_ms':10,'translation_m_s':[-200,5,2],'elastic_duration_ms':.1,'membrane_axial_strain':.001,'membrane_transverse_strain':-.00033,'curvature_per_mm':.001,'ramp':'3s²-2s³','bending_displacement':'z=k*x²/2; x-displacement=-k²*x³/6 eliminates leading membrane stretch; all nodes prescribed. Interior elements with full neighbor stencil compared to Kirchhoff bending, boundary response kept separately.'},
      'acceptance':{'mass_relative':1e-6,'added_mass_relative':1e-9,'native_energy_fraction':.02,'native_energy_absolute_J':1e-7,'free_energy_fraction':.002,'free_momentum_fraction':.002,'physical_angular_fraction':.002,'physical_angular_absolute_kg_m2_s':1e-9,'known_discrete_initial_KE_fraction':.002,'physical_continuum_initial_KE_fraction':.02,'native_RKE_absolute_J':1e-7,'elastic_reference_fraction':.02,'elastic_absolute_J':1e-7,'elastic_mesh_fraction':.05,'position_mm':.002,'velocity_m_s':.005,'actual_dt_ratio_max':.6},
      'execution':{'CPU_threads':1,'GPU':False,'mass_scaling':False,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'history_dt_ms':.001,'animation_dt_ms':.025,'per_process_cap_s':600,'estimated_minutes':[3,8]},
      'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_3_node_triangle_without_rot_dof_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm'],
      'constraints':'No body/sandwich/whole input changed. LAW25 composite and core coupling require separate declared witnesses. Prototype curvature does not target observed damage. Refinement changes lumped masses at nodes, preserving volume and density; record discrete and continuum inertia separately.',
      'whole_insertion_ready':False,'old_A20_A25_native_solver_reruns':0,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True});sd=OUT/'sources';sd.mkdir();sources=[]
    for j,u in enumerate(c['sources']):
        q=sd/f'primary_{j}.html';q.write_bytes(urllib.request.urlopen(u,timeout=45).read());sources.append({'url':u,'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size,'redistribution':'exclude_third_party'})
    for q in [PREV/'shell_inertia_diagnostic.json',PREV/'root_geometry_preparation.json',PREV/'publication_verification.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad']:
        if not q.exists() and q.suffix=='.rad':continue
        sources.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'archive_rescanned':False,'source_outputs_unchanged':True});print({'declared':'AIRCRAFT-A26','native_cases':9,'estimated_CPU_minutes':[3,8]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def mesh(n):
    X=np.array([[x,y,0] for y in np.linspace(-5,5,n+1) for x in np.linspace(-5,5,n+1)]);tri=[];parts=[];mass=np.zeros(len(X))
    for j in range(n):
        for i in range(n):
            a=j*(n+1)+i+1;b=a+1;d=a+n+1;c=d+1;pair=[[a,b,c],[a,c,d]] if (i+j)%2==0 else [[a,b,d],[b,c,d]]
            for t in pair:
                area=np.linalg.norm(np.cross(X[t[1]-1]-X[t[0]-1],X[t[2]-1]-X[t[0]-1]))/2;mass[np.asarray(t)-1]+=area*.5*.00278/3;tri.append(t);parts.append(11 if 0<i<n-1 and 0<j<n-1 else 1)
    return X,tri,parts,mass

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;cache={};counter=10000
    for ni,q in enumerate(X,1):
        L+=group(ni,f'PRESCRIBED_NODE_{ni}',[ni]);D=np.array([.001*q[0],-.00033*q[1],0]) if cid.startswith('MEMBRANE') else np.array([-.001**2*q[0]**3/6,0,.001*q[0]**2/2])
        for a,direction in enumerate('XYZ'):
            val=D[a]*s;key=val.tobytes()
            if key not in cache:
                counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}',f'KNOWN_DISPLACEMENT_{counter}']+[ff(t,v) for t,v in zip(T,val)]
            fid=cache[key];counter+=1;L+=[f'/IMPDISP/{counter}',f'PRESCRIBED_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def run_one(cid):
    guard();c=read(CFG);ncell=int(re.search(r'_N(6|12)',cid).group(1));X,tri,parts,mass=mesh(ncell);free=cid.startswith('FREE');half=cid.endswith('_HALF');duration=.05 if free else .1;d=OUT/'w0'/cid;n='A26_'+cid;assert not d.exists();d.mkdir(parents=True);P=parent();bp=P['/PROP/TYPE1/1'].copy();bp[1]='HALF_MM_DKT_S3_TRANSLATIONS_ONLY';bp[2]=ii(24,4,31,2);bp[4]=ii(5)+' '*10+ff(.5,.833333333333);mats=P['/MAT/LAW2/1']+bp
    for part,title in [(1,'PLATE_EDGE'),(11,'PLATE_INTERIOR')]:mats+=['/PART/'+str(part),title,ii(1,1,0),'/SH3N/'+str(part)]+[ii(k+1,*tr) for k,(tr,p) in enumerate(zip(tri,parts)) if p==part]
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(X)]+mats
    omega=np.zeros(3);V=np.zeros_like(X)
    if free:
        omega=np.eye(3)['XYZ'.index(re.search('ROTATION_([XYZ])',cid).group(1))]*10 if 'ROTATION' in cid else np.zeros(3);V=np.cross(omega,X) if 'ROTATION' in cid else np.tile([-200,5,2],(len(X),1))
        for ni,v in enumerate(V,1):L+=group(ni,f'INITIAL_NODE_{ni}',[ni])+[f'/INIVEL/TRA/{ni}','INITIAL_TRANSLATIONAL_VELOCITY',ff(*v)+ii(ni,0),ff(0)+ii(0)]
    else:L=imposed(L,X,cid)
    L+=['/TH/PART/1','PLATE_SCOPE',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(1,11),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(i,0) for i in range(1,len(X)+1)]+['/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8');E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/DT',ff(.2 if half else .4,0),'/DTIX',ff(.0000125 if half else .000025,.0000125 if half else .000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(duration),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');g={'created_utc':now(),'case':cid,'name':n,'mesh_n':ncell,'free':free,'duration_ms':duration,'nodes_mm':X.tolist(),'triangles':tri,'triangle_parts':parts,'known_nodal_masses_g':mass.tolist(),'known_mass_g':float(mass.sum()),'initial_velocity_m_s':V.tolist(),'initial_omega_rad_ms':omega.tolist(),'physical_plate_dimensions_mm':[10,10,.5],'Ish3n':31,'rotational_initial_conditions':False,'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__))};dump(d/'generation.json',g);en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',600,en);t=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',t)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',t)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,t[-4000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',600,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',600,en);review(d,n)
    except Exception:dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'whole_insertion_ready':False});raise

def review(d,n):
    guard();g=read(d/'generation.json');H=histories(d/(n+'T01.csv'));T=H['time'];X0=np.asarray(g['nodes_mm']);m=np.asarray(g['known_nodal_masses_g']);keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(keys)==6*len(X0);node=np.column_stack([H[k] for k in keys]).reshape(len(T),len(X0),6);X=X0+node[:,:,:3];V=node[:,:,3:];terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;IE=H['INTERNAL ENERGY']*.001;R=E-E[0]-EW;L=np.sum(m[None,:,None]*np.cross(X,V),axis=1)*1e-6;P=np.sum(m[None,:,None]*V,axis=1)*.001;checks={'normal_termination':True,'strict_zero_warnings':read(d/'starter_gate.json')['pass'],'physical_mass':abs(H['MASS'][0]-.139)<1e-6*.139,'constant_mass':abs(H['MASS']-H['MASS'][0]).max()<1e-6*.139,'no_ADMAS':abs(H['ADDED MASS']).max()<1e-9*.139,'native_full_balance':abs(R).max()<.02*max(float(abs(E).max()),float(abs(EW).max()))+1e-7,'nonnegative_IE':IE.min()>-1e-7,'no_native_RKE':abs(H['ROTATION ENERGY']).max()*.001<1e-7};ref=None;actual=None
    if g['free']:
        v=np.asarray(g['initial_velocity_m_s']);known=.5*np.sum(m[:,None]*v*v)*.001;om=np.asarray(g['initial_omega_rad_ms']);dm=np.array([10.,10,.5]);Icont=.139*(sum(dm**2)-dm**2)/12;phys=.5*np.sum(Icont*om**2)*.001 if 'ROTATION' in g['case'] else known;checks.update(known_initial_KE=abs(E[0]-known)<.002*known+1e-7,physical_continuum_initial_KE=abs(E[0]-phys)<.02*phys+1e-7,no_external_work=abs(EW).max()<1e-7,free_native_energy=abs(E-E[0]).max()<.002*E[0]+1e-7,free_linear_momentum=abs(P-P[0]).max()<.002*np.linalg.norm(P[0])+1e-9,free_physical_angular_momentum=np.linalg.norm(L-L[0],axis=1).max()<.002*np.linalg.norm(L[0])+1e-9)
        if 'TRANSLATION' in g['case']:checks.update(uniform_position=abs(X-X0[None,:,:]-T[:,None,None]*np.array([-200,5,2])).max()<.002,uniform_velocity=abs(V-np.array([-200,5,2])).max()<.005)
    else:
        if g['case'].startswith('MEMBRANE'):ref=.5*73100*.001**2*50*.001;actual=float(IE[-1])
        else:
            area=(10*(g['mesh_n']-2)/g['mesh_n'])**2;D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*area*.001;actual=float(next(v[-1]*.001 for k,v in H.items() if k.startswith('PLATE_INTERIOR') and k.strip().endswith('IE')))
        checks['independent_elastic_reference']=abs(actual-ref)<.02*ref+1e-7
    checks={k:bool(v) for k,v in checks.items()};np.savez_compressed(d/'histories_SI.npz',time_ms=T,total_J=E,IE_J=IE,EW_J=EW,residual_J=R,positions_mm=X,velocities_m_s=V,physical_L_kg_m2_s=L,momentum_Ns=P,time_step_ms=H['TIME STEP']);r={'created_utc':now(),'case':g['case'],'last_ms':float(T[-1]),'maximum_residual_J':float(abs(R).max()),'maximum_native_RKE_J':float(abs(H['ROTATION ENERGY']).max()*.001),'native_initial_total_J':float(E[0]),'elastic_reference_J':ref,'native_elastic_comparison_J':actual,'maximum_physical_L_drift_kg_m2_s':float(np.linalg.norm(L-L[0],axis=1).max()),'checks':checks,'pass':all(checks.values()),'whole_insertion_ready':False};dump(d/'review.json',r);print({'case':g['case'],'pass':r['pass'],'failed':[k for k,v in checks.items() if not v],'RKE_J':r['maximum_native_RKE_J']},flush=True)

def run():
    guard()
    for cid in read(CFG)['cases']:
        d=OUT/'w0'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case; no implicit rerun'
        else:run_one(cid)
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'cases':[read(OUT/'w0'/cid/'review.json') for cid in read(CFG)['cases']],'whole_insertion_ready':False,'composite_skin_and_core_not_qualified':True,'objective1_complete':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
