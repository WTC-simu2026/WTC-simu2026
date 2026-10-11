"""Declared conformal volume sandwich: shared physical faces, no rigid offsets."""
from run_aircraft_a29 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories,constitutive
import test_aircraft_a29_law12 as skin
import run_aircraft_a20 as core
import argparse,json,shutil,re,traceback,time
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a30'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a30_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a29'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A29';st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A29';assert st['aircraft_a29_key_results']['explicit_LAW12_prototype_pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={'iteration':'AIRCRAFT-A30','declared_utc':now(),'seed':1102055,'random_draws':0,'purpose':'Conformal volume sandwich using explicit LAW12 skins and unchanged source LAW28 core. Physical face sharing is a newly declared perfect-bond hypothesis; old Spot5 and whole aircraft inputs are preserved. Free physical invariants and manufactured elastic fields before surface-loaded coupling and real root insertion.',
      'geometry':{'XY_bounds_mm':[-5,5],'lower_skin_Z_mm':[-4.5,-4],'core_Z_mm':[-4,4],'upper_skin_Z_mm':[4,4.5],'XY_meshes':[6,12],'geometric_Z_elements':{'skin_each':4,'core':12},'faces':'identical node IDs at z=-4 and z=4, no duplicate interface masses, rigid-body offset or independent rotations','continuous_physical_mass_g':.2214,'no_added_or_scaled_mass':True},
      'skin':{'law':'LAW12/4','configuration':rel(skin.CFG),'configuration_sha256':streamsha(skin.CFG),'rho_g_mm3':.00183,'E_MPa':[22000,22000,10000],'nu12_nu23_nu31':[.25,.25,.25],'new_transverse_Poisson_assumptions':True,'G_MPa':[4000,4000,4000],'axes_global_rows':[[0,1,0],[-1,0,0],[0,0,1]],'property':'TYPE6 Isolid18 Ismstr0(auto2) Icpre3 Iframe2','historical_strength_and_fracture_qualified':False},
      'core':{'law':'unchanged source LAW28/28 and constant plateau curves280..285','rho_g_mm3':.000048,'E_MPa':[1,1,138],'G_MPa':[.5,24,41],'axes_global_rows':np.eye(3).tolist(),'property':'TYPE6 Isolid14 Ismstr4 Icpre3 Gauss222 Iframe2, same scalar property inputs as cached A20 core','reference':'uncoupled tangent C=diag(E11,E22,E33,G12,G23,G31)','unmeasured_parameters':['E11','E22','G12','in_plane_yield','failure_strains','fracture_energy','postpeak','rate_dependence'],'cached_A20_material_controls_reused':True,'no_new_core_failure_claim':True},
      'cases':['FREE_ROTATION_X_N12','FREE_ROTATION_Y_N12','FREE_ROTATION_Z_N12','FREE_TRANSLATION_N12','FREE_ROTATION_Y_N12_HALF','AFFINE_EXTENSION_N6','AFFINE_EXTENSION_N12','CONSTRAINED_BENDING_N6','CONSTRAINED_BENDING_N12'],
      'loading':{'free_duration_ms':.05,'free_omega_rad_ms':1,'free_omega_reason':'Keep low-strength core elastic: estimated rho*omega²*R² below weakest declared .1MPa yield. New sandwich amplitude declared before any native results, no claim of high-speed A29 amplitude equivalence.','translation_m_s':[-200,5,2],'elastic_duration_ms':.1,'ramp':'3s²-2s³','axial_strain':.001,'affine':'ux=.001*x; uy=uz=0, all nodes prescribed. Constrained 3D extension, not free uniaxial contraction.','curvature_per_mm':.0001,'bending':'ux=-k*x*z-k²*x³/6;uy=0;uz=k*x²/2. All nodes prescribed, epsilon_y=epsilon_z=0 to first order. Constrained transverse bending, not free plate bending.','small_strain_limit_reason':'κ chosen for max skin strain4.5e-4 on9mm sandwich, same elastic order as A29 plate; not native response fit.'},
      'reference':{'extension':'0.5*epsilon²*sum(Cxx_region*physical_volume_region), J conversion1e-3 from native g/mm/ms energy','bending':'0.5*kappa²*area*sum(Cxx_region*integral(z²dz)), source tensor, native values not used','continuous_inertia':'analytic sum of each layer rectangular prism about global origin including physical offset; compare separate known lumped tensor','limitations':'Manufactured fields constrain every node. They verify coupled native mass, conservation and constitutive response, not free interior transmission, delamination or real attachment capacity.'},
      'acceptance':read(skin.CFG)['acceptance'],'execution':{'CPU_threads':1,'GPU':False,'mass_scaling':False,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'per_process_cap_s':1800,'estimated_minutes':[10,25]},'sources':['A29 explicit LAW12 qualification','A20 verified LAW28 controls','actual source A20 deck','A25 root inventory'],'whole_aircraft_inputs_changed':False,'old_native_solver_reruns':0,'whole_insertion_ready':False,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True});sources=[]
    for q in [PREV/'composite_qualification_review.json',PREV/'publication_verification.json',skin.CFG,Path(skin.__file__),core.CFG,Path(core.__file__),core.OUT/'core_verified_review.json',core.OUT/'sandwich_type2_review.json',ROOT/'wtc1_simulation_v8/output/aircraft_a25/root_geometry_preparation.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad',ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a28_a29/final_remote_verification.json']:sources.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'core_material_card':parent()['/MAT/LAW28/28'],'archive_rescanned':False,'source_outputs_not_modified':True});print({'A30_declared':True,'native_controls':9,'CPU_minutes':[10,25],'whole_impact_not_run':True},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def mesh(n):
    Z=np.concatenate([np.linspace(-4.5,-4,5),np.linspace(-4,4,13)[1:],np.linspace(4,4.5,5)[1:]]);axes=[np.linspace(-5,5,n+1),np.linspace(-5,5,n+1),Z];X=np.array([[x,y,z] for z in Z for y in axes[1] for x in axes[0]]);B=[];parts=[];m=np.zeros(len(X));volumes={1:0.,2:0.,28:0.};ids=lambda i,j,k:1+i+(n+1)*j+(n+1)**2*k
    for k in range(len(Z)-1):
        pid=1 if k<4 else 28 if k<16 else 2;rho=.000048 if pid==28 else .00183;ev=(10/n)**2*(Z[k+1]-Z[k]);
        for j in range(n):
            for i in range(n):
                conn=[ids(i,j,k),ids(i+1,j,k),ids(i+1,j+1,k),ids(i,j+1,k),ids(i,j,k+1),ids(i+1,j,k+1),ids(i+1,j+1,k+1),ids(i,j+1,k+1)];B.append(conn);parts.append(pid);m[np.asarray(conn)-1]+=rho*ev/8;volumes[pid]+=ev
    assert np.allclose([volumes[1],volumes[2],volumes[28]],[50,50,800]) and abs(m.sum()-.2214)<1e-12
    return X,B,parts,m

def independent_reference(cid):
    C=constitutive();Cc=np.diag([1,1,138,.5,24,41]);e=.001;k=.0001
    if cid.startswith('AFFINE'):return .5*e*e*(C[0,0]*100+Cc[0,0]*800)*.001
    moment_skin=2*(4.5**3-4**3)/3;moment_core=2*4**3/3;return .5*k*k*100*(C[0,0]*moment_skin+Cc[0,0]*moment_core)*.001

def continuous_I():
    result=np.zeros(3)
    for lo,hi,rho in [(-4.5,-4,.00183),(-4,4,.000048),(4,4.5,.00183)]:
        M=100*(hi-lo)*rho;var=[100/12,100/12,(hi-lo)**2/12+((lo+hi)/2)**2];result+=M*(sum(var)-np.array(var))
    return result

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;cache={};counter=10000
    for ni,(x,y,z) in enumerate(X,1):
        D=np.array([.001*x,0,0]) if cid.startswith('AFFINE') else np.array([-.0001*x*z-.0001**2*x**3/6,0,.0001*x*x/2]);L+=group(ni,f'PRESCRIBED_NODE_{ni}',[ni])
        for a,dr in enumerate('XYZ'):
            val=D[a]*s;key=val.tobytes()
            if key not in cache:counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}',f'KNOWN_DISPLACEMENT_{counter}']+[ff(t,v) for t,v in zip(T,val)]
            counter+=1;L+=[f'/IMPDISP/{counter}',f'PRESCRIBED_{ni}_{dr}',ii(cache[key])+f'{dr:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def native_gate(d,n):
    t=(d/(n+'_0000.out')).read_text();checks={};flags={};header='Isolid  Ismstr   Icpre  Iframe    IHKT Itetra4 Itetra10 IMATVIS ICONTROL'
    for pid,want in [(1,[18,2,3,2,0,0,0,0,0]),(2,[18,2,3,2,0,0,0,0,0]),(28,[14,4,3,2,0,0,0,0,0])]:
        p=re.search(r'Part id,name:\s*'+str(pid)+r'\s+.*?'+re.escape(header)+r'\s+'+r'\s+'.join([r'(\d+)']*9),t,re.S);assert p,f'Missing part{pid}readback';flags[pid]=list(map(int,p.groups()));checks['part_'+str(pid)]=flags[pid]==want
    axes={}
    for sid,want in [(1,[[0,1,0],[-1,0,0],[0,0,1]]),(28,np.eye(3).tolist())]:
        p=re.search(r'SKEW SYSTEM SETS.*?\n\s*'+str(sid)+r'\s+0\s+0\s+0\s+([^\n]+)\n\s+([^\n]+)\n\s+([^\n]+)',t,re.S);assert p;axes[sid]=[[float(v) for v in line.split()][:3] for line in p.groups()];checks['skew_'+str(sid)]=bool(np.allclose(axes[sid],want,atol=1e-6,rtol=0))
    dump(d/'native_frame_gate.json',{'created_utc':now(),'part_flags':flags,'axes_rows':axes,'checks':checks,'pass':all(checks.values()),'before_Engine':True});assert all(checks.values()),checks

def run_one(cid):
    guard();ncell=int(re.search(r'_N(6|12)',cid).group(1));X,B,parts,m=mesh(ncell);free=cid.startswith('FREE');half=cid.endswith('HALF');duration=.05 if free else .1;d=OUT/'w0'/cid;n='A30_'+cid;assert not d.exists();d.mkdir(parents=True);P=parent();mats=skin.law12_card()+skin.property_card()+P['/MAT/LAW28/28']+core.skew_card(28)+core.solid_property()
    for fid in range(280,286):mats+=P[f'/FUNCT/{fid}']
    for pid,mid,prop,title in [(1,4,1,'LOWER_VOLUME_SKIN'),(2,4,1,'UPPER_VOLUME_SKIN'),(28,28,28,'UNCHANGED_SOURCE_CORE')]:mats+=[f'/PART/{pid}',title,ii(prop,mid,0),f'/BRICK/{pid}']+[ii(j+1,*conn) for j,(conn,p) in enumerate(zip(B,parts)) if p==pid]
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(X)]+mats;omega=np.zeros(3);V=np.zeros_like(X)
    if free:
        omega=np.eye(3)['XYZ'.index(re.search('ROTATION_([XYZ])',cid).group(1))] if 'ROTATION' in cid else np.zeros(3);V=np.cross(omega,X) if 'ROTATION' in cid else np.tile([-200,5,2],(len(X),1))
        for ni,v in enumerate(V,1):L+=group(ni,f'INITIAL_NODE_{ni}',[ni])+[f'/INIVEL/TRA/{ni}','INITIAL_TRANSLATIONAL_VELOCITY',ff(*v)+ii(ni,0),ff(0)+ii(0)]
    else:L=imposed(L,X,cid)
    L+=['/TH/PART/1','SANDWICH_PARTS',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(1,2,28),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(i,0) for i in range(1,len(X)+1)]+['/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8');E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/ANIM/BRICK/TENS/STRESS','/DT',ff(.2 if half else .4,0),'/DTIX',ff(.0000125 if half else .000025,.0000125 if half else .000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(duration),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'case':cid,'name':n,'mesh_n':ncell,'free':free,'duration_ms':duration,'nodes_mm':X.tolist(),'bricks':B,'brick_parts':parts,'known_nodal_masses_g':m.tolist(),'known_mass_g':float(m.sum()),'continuous_inertia_g_mm2':continuous_I().tolist(),'initial_velocity_m_s':V.tolist(),'initial_omega_rad_ms':omega.tolist(),'physical_shared_faces':True,'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__))});en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',1800,en);t=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',t)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',t)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,t[-4000:];native_gate(d,n);assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',1800,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',1800,en);review(d,n)
    except Exception:dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'whole_insertion_ready':False});raise

def review(d,n):
    guard();g=read(d/'generation.json');H=histories(d/(n+'T01.csv'));T=H['time'];X0=np.asarray(g['nodes_mm']);m=np.asarray(g['known_nodal_masses_g']);keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(keys)==6*len(X0);node=np.column_stack([H[k] for k in keys]).reshape(len(T),len(X0),6);X=X0+node[:,:,:3];V=node[:,:,3:];terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;IE=H['INTERNAL ENERGY']*.001;R=E-E[0]-EW;L=np.sum(m[None,:,None]*np.cross(X,V),axis=1)*1e-6;P=np.sum(m[None,:,None]*V,axis=1)*.001;M=.2214;checks={'normal_termination':True,'strict_zero_warnings':read(d/'starter_gate.json')['pass'],'native_frames':read(d/'native_frame_gate.json')['pass'],'physical_mass':bool(abs(H['MASS'][0]-M)<1e-6*M),'constant_mass':bool(abs(H['MASS']-H['MASS'][0]).max()<1e-6*M),'no_ADMAS':bool(abs(H['ADDED MASS']).max()<1e-9*M),'native_full_balance':bool(abs(R).max()<.02*max(float(abs(E).max()),float(abs(EW).max()))+1e-7),'nonnegative_IE':bool(IE.min()>-1e-7),'no_native_RKE':bool(abs(H['ROTATION ENERGY']).max()*.001<1e-7)};ref=None;known=None;phys=None
    if g['free']:
        v=np.asarray(g['initial_velocity_m_s']);om=np.asarray(g['initial_omega_rad_ms']);known=float(.5*np.sum(m[:,None]*v*v)*.001);phys=float(.5*np.sum(continuous_I()*om**2)*.001) if 'ROTATION' in g['case'] else known;checks.update(known_initial_KE=bool(abs(E[0]-known)<.002*known+1e-7),physical_continuum_initial_KE=bool(abs(E[0]-phys)<.02*phys+1e-7),no_external_work=bool(abs(EW).max()<1e-7),free_native_energy=bool(abs(E-E[0]).max()<.002*E[0]+1e-7),free_linear_momentum=bool(abs(P-P[0]).max()<.002*np.linalg.norm(P[0])+1e-9),free_physical_angular_momentum=bool(np.linalg.norm(L-L[0],axis=1).max()<.002*np.linalg.norm(L[0])+1e-9))
        if 'TRANSLATION' in g['case']:checks.update(uniform_position=bool(abs(X-X0[None,:,:]-T[:,None,None]*np.array([-200,5,2])).max()<.002),uniform_velocity=bool(abs(V-np.array([-200,5,2])).max()<.005))
    else:ref=independent_reference(g['case']);checks['independent_constrained_elastic_reference']=bool(abs(IE[-1]-ref)<.02*ref+1e-7)
    np.savez_compressed(d/'histories_SI.npz',time_ms=T,total_J=E,IE_J=IE,EW_J=EW,residual_J=R,positions_mm=X,velocities_m_s=V,physical_L_kg_m2_s=L,momentum_Ns=P,time_step_ms=H['TIME STEP']);r={'created_utc':now(),'case':g['case'],'last_ms':float(T[-1]),'maximum_residual_J':float(abs(R).max()),'native_mass_g':float(H['MASS'][0]),'maximum_native_RKE_J':float(abs(H['ROTATION ENERGY']).max()*.001),'native_initial_total_J':float(E[0]),'known_initial_total_J':known,'continuous_initial_total_J':phys,'elastic_reference_J':ref,'native_elastic_comparison_J':float(IE[-1]) if ref is not None else None,'maximum_physical_L_drift_kg_m2_s':float(np.linalg.norm(L-L[0],axis=1).max()),'checks':checks,'pass':all(checks.values()),'whole_insertion_ready':False,'free_interior_transmission_qualified':False};dump(d/'review.json',r);print({'case':g['case'],'pass':r['pass'],'failed':[k for k,v in checks.items() if not v]},flush=True)

def run():
    guard()
    for cid in read(CFG)['cases']:
        d=OUT/'w0'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'cases':[read(OUT/'w0'/cid/'review.json') for cid in read(CFG)['cases']],'whole_insertion_ready':False,'manufactured_field_scope_only':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
