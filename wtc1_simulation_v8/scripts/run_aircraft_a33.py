"""Face-loaded efficient skin with genuinely free physical interior nodes."""
import run_aircraft_a32 as previous
from run_aircraft_a32 import *
from diagnose_aircraft_a32_surface_bending import field
import inspect,ast
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a33'
PREV=previous.OUT
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a33_predeclaration.json'
CASES=['PATCH_NORMAL_Z_N12_Z2','FREE_ROTATION_Y_N12_Z2','FREE_TRANSLATION_N12_Z2','FACE_BENDING_N12_Z1','FACE_BENDING_N12_Z2','FACE_BENDING_N24_Z2','FACE_BENDING_N24_Z4','FACE_BENDING_N24_Z2_HALF']
REFERENCE=PREV/'surface_reference_extension/N192_Z16_EXACT_FACE.json'

def declare():
    assert not CFG.exists() and not OUT.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A32';assert read(PREV/'publication_verification.json')['pass'];diag=read(PREV/'surface_bending_extended_diagnostic.json');assert all(diag['reference_refinement_checks'].values())
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={'iteration':'AIRCRAFT-A33','declared_utc':now(),'seed':1102058,'random_draws':0,'purpose':'Physical interior nodes allow transverse and edge relaxation in a source-mass-preserving efficient TYPE6/Isolid24 skin. Keep A32 failed gates, test continuum equivalence and actual force/work transfer before coupling or whole insertion.',
       'parent_configuration':rel(previous.CFG),'parent_configuration_sha256':streamsha(previous.CFG),'material':read(previous.CFG)['material'],'geometry':{'bounds_mm':[[-5,-5,-.25],[5,5,.25]],'volume_mm3':50,'density_g_mm3':.00183,'mass_g':.0915,'XY':[12,24],'physical_Z_cells':[1,2,4]},
       'formulation':'TYPE6 Isolid24 Ismstr4 Icpre3 Iframe2,source full3D LAW12,axesY,-X,Z,dn1e-20','cases':CASES,'negative_control':'FACE_BENDING_N12_Z1 is separately declared against the now refined face-loaded reference; never rewrite its old A32 result. Its failure is retained, not a stop for multi-cell candidates.',
       'loading':{'free_duration_ms':.05,'ramp_duration_ms':.1,'history_ms':.001,'animation_ms':.025,'bending_curvature_per_mm':.001,'bending_faces_only':True,'physical_interior_nodes_free':True,'face_field':'ux=-k*x*z-k²*x³/6,uy=0,uz=k*x²/2, multiplied by3s²-2s³','patch_Z':'All nodes imposed epsilonZZ=.001; exact full3D C reference','free_rotation_rad_ms':10,'free_translation_m_s':[-200,5,2]},
       'reference':{'source':rel(REFERENCE),'sha256':streamsha(REFERENCE),'energy_J':read(REFERENCE)['energy_J'],'mesh':[192,192,16],'prior_refinement':diag['reference_refinement_checks'],'boundary_identical_physical_faces':True,'native_operator_not_used':True,'continuous_inertia_g_mm2':read(previous.CFG)['reference']['continuous_inertia_g_mm2'],'matching_nodes':'Exact coincident grid indices from nested192x192x16reference; no response fitting'},
       'acceptance':{**read(previous.CFG)['acceptance'],'final_KE_fraction_of_reference':.01,'plastic_work_absolute_J':1e-7,'boundary_displacement_absolute_mm':2e-6,'interior_relaxation_fraction':.02,'interior_relaxation_absolute_mm':2e-6,'impulse_momentum_fraction':.02,'impulse_momentum_absolute_Ns':1e-9,'boundary_work_fraction':.02,'scope':'Z2candidate requires own free/affine/bending gates and XY/time refinement. Z4is thickness refinement; original failures retained.'},
       'execution':{'CPU_threads':1,'GPU':False,'mass_scaling':False,'DT_factor':.4,'half_DT_factor':.2,'per_process_cap_s':600,'estimated_minutes':[1,10]},
       'reaction_protocol':'A31 same-binary impulse interpretation is prior evidence. Bending requires unambiguous raw-impulse vs force-integration comparison. Symmetric affine patch has zero net momentum: only raw-sum consistency and boundary work are tested there, no standalone unambiguous interpretation claim.',
       'stop_rule':'Stop native campaign on fatal, nonfinite output or failed full energy balance. Complete separately declared elastic references even when their gate fails, retaining failures for diagnosis.',
       'whole_aircraft_inputs_changed':False,'whole_insertion_ready':False,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'old_native_solver_reruns':0}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_results':True})
    files=[previous.CFG,Path(previous.__file__),REFERENCE,PREV/'surface_bending_extended_diagnostic.json',PREV/'publication_verification.json',Path(source_skin.__file__),PREV/'sources/type6.html',ROOT/'wtc1_simulation_v8/output/aircraft_a31/curved_root_surface_mapping.json']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in files],'no_new_archive_scan':True,'known_damage_target':False});print({'A33_declared':True,'native_controls':len(CASES),'CPU_minutes':[1,10]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;counter=10000;cache={};D=field(X,True)
    if cid.startswith('PATCH_'):D=np.zeros_like(X);D[:,2]=.001*X[:,2]
    faces=[]
    for ni,x in enumerate(X,1):
        if not cid.startswith('PATCH_') and abs(x[2])!=.25:continue
        faces.append(ni);L+=group(ni,'PRESCRIBED_FACE_NODE',[ni])
        for ax,dr in enumerate('XYZ'):
            val=D[ni-1,ax]*s;key=val.tobytes()
            if key not in cache:counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}','PHYSICAL_FACE_FIELD']+[ff(t,u) for t,u in zip(T,val)]
            counter+=1;L+=[f'/IMPDISP/{counter}','TRANSLATIONS_ONLY',ii(cache[key])+f'{dr:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/NODE/2','FACE_IMPULSES',''.join(f'{v:>10}' for v in ['REACX','REACY','REACZ'])]+[ii(i,0) for i in faces]
    return L

def reference_nodes(X):
    q=read(REFERENCE);U=np.asarray(q['displacements_mm']).reshape(17,193,193,3);ix=np.rint((X[:,0]+5)*192/10).astype(int);iy=np.rint((X[:,1]+5)*192/10).astype(int);iz=np.rint((X[:,2]+.25)*16/.5).astype(int)
    target=np.column_stack([-5+ix*10/192,-5+iy*10/192,-.25+iz*.5/16]);assert np.max(abs(target-X))<1e-12
    return U[iz,iy,ix]

def cumulative_trap(y,T):return np.concatenate([np.zeros_like(y[:1]),np.cumsum((y[1:]+y[:-1])*.5*np.diff(T).reshape((-1,)+(1,)*(y.ndim-1)),axis=0)],axis=0)

def review(d,n):
    g=read(d/'generation.json');H=histories(d/(n+'T01.csv'));T=H['time'];c=read(CFG);X0=np.asarray(g['nodes_mm']);m=np.asarray(g['nodal_masses_g']);nk=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(nk)==6*len(X0);node=np.column_stack([H[k] for k in nk]).reshape(len(T),len(X0),6);X=X0+node[:,:,:3];V=node[:,:,3:];P=np.sum(m[None,:,None]*V,axis=1)*.001;L=np.sum(m[None,:,None]*np.cross(X,V),axis=1)*1e-6
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;IE=H['INTERNAL ENERGY']*.001;HE=H['HOURGLASS ENERGY']*.001;KE=H['KINETIC ENERGY']*.001;R=E-E[0]-EW
    checks={'native_termination':True,'strict_zero_warnings':read(d/'starter_gate.json')['pass'],'native_frame':read(d/'native_frame_gate.json')['pass'],'physical_mass':bool(abs(H['MASS']-.0915).max()<1e-6*.0915),'no_ADMAS':bool(abs(H['ADDED MASS']).max()<1e-9*.0915),'native_full_balance':bool(abs(R).max()<.02*max(float(abs(E).max()),float(abs(EW).max()))+1e-7),'no_native_RKE':bool(abs(H['ROTATION ENERGY']).max()*.001<1e-7),'finite_histories':bool(np.isfinite(node).all() and np.isfinite(E).all())}
    cid=g['case'];target=None;diagnostics={};elastic=IE+HE
    if g['free']:
        expected=.5*np.sum(m[:,None]*np.asarray(g['initial_velocity_m_s'])**2)*.001;checks.update(known_lumped_initial_KE=bool(abs(KE[0]-expected)<.002*expected+1e-7),free_energy=bool(abs(E-E[0]).max()<.002*abs(E[0])+1e-7),free_physical_L=bool(np.linalg.norm(L-L[0],axis=1).max()<.002*np.linalg.norm(L[0])+1e-12),free_momentum=bool(np.linalg.norm(P-P[0],axis=1).max()<.002*np.linalg.norm(P[0])+1e-9))
        if 'ROTATION' in cid:
            omega=np.asarray(g['initial_omega_rad_ms']);cont=.5*omega@np.diag(c['reference']['continuous_inertia_g_mm2'])@omega*.001;checks['continuous_initial_KE']=bool(abs(KE[0]-cont)<.02*cont+1e-7)
    else:
        s=3*(T/.1)**2-2*(T/.1)**3;patch=cid.startswith('PATCH_');ref=float(.5*source_skin.patch_strain('PATCH_NORMAL_Z_N12')@constitutive()@source_skin.patch_strain('PATCH_NORMAL_Z_N12')*50*.001) if patch else c['reference']['energy_J'];target=ref*s[-1]**2
        checks['independent_elastic_energy']=bool(abs(elastic[-1]-target)<.02*target+1e-7);checks['quasi_static_final_KE']=bool(KE[-1]<.01*target+1e-7)
        faces=np.arange(len(X0)) if patch else np.flatnonzero(abs(X0[:,2])==.25);fk=[k for k in H if k.startswith('FACE_IMPULSES')];assert len(fk)==3*len(faces);Q=np.column_stack([H[k] for k in fk]).reshape(len(T),len(faces),3);raw=Q.sum(axis=1)*.001;dp=P-P[0];ptol=.02*float(np.linalg.norm(dp,axis=1).max())+1e-9;ie=float(np.linalg.norm(raw-raw[0]-dp,axis=1).max());fe=float(np.linalg.norm(cumulative_trap(Q.sum(axis=1),T)*.001-dp,axis=1).max());protocol=ie<ptol and fe>=ptol
        Fn=np.gradient(Q,T,axis=0,edge_order=2);W=cumulative_trap(np.sum(Fn*V[:,faces,:],axis=(1,2)),T)*.001;we=float(abs(W-EW).max());checks['reaction_sum_momentum_consistent' if patch else 'reaction_impulse_interpretation_verified']=bool(ie<ptol if patch else protocol);checks['independent_boundary_work']=bool((ie<ptol if patch else protocol) and we<.02*max(float(abs(EW).max()),target)+1e-7)
        base=field(X0,True)
        if patch:base=np.zeros_like(X0);base[:,2]=.001*X0[:,2]
        berr=float(abs(node[:,faces,:3]-s[:,None,None]*base[faces]).max());checks['boundary_displacements']=berr<2e-6
        free=np.setdiff1d(np.arange(len(X0)),faces)
        if len(free):
            refU=reference_nodes(X0);err=float(abs(node[-1,free,:3]-s[-1]*refU[free]).max());warp=float(abs(refU[free]-base[free]).max());tol=.02*warp+2e-6;checks['independent_interior_relaxation']=err<tol;diagnostics.update(maximum_interior_displacement_error_mm=err,reference_relaxation_mm=warp,interior_tolerance_mm=tol)
        pw=[k for k in H if k.startswith('DECLARED_PHYSICAL_SKIN') and k.strip().endswith('PW')];assert len(pw)==1;PW=H[pw[0]]*.001;checks['elastic_PW']=bool(abs(PW).max()<1e-7);diagnostics.update(raw_impulse_error_Ns=ie,force_interpretation_error_Ns=fe,impulse_tolerance_Ns=ptol,maximum_boundary_work_error_J=we,maximum_boundary_displacement_error_mm=berr,maximum_PW_J=float(abs(PW).max()))
    np.savez_compressed(d/'histories_SI.npz',time_ms=T,IE_J=IE,HE_J=HE,KE_J=KE,total_J=E,EW_J=EW,residual_J=R,positions_mm=X,velocities_m_s=V,physical_L_kg_m2_s=L,momentum_Ns=P,time_step_ms=H['TIME STEP'])
    r={'created_utc':now(),'branch':'w1','case':cid,'checks':{k:bool(v) for k,v in checks.items()},'pass':all(checks.values()),'last_ms':float(T[-1]),'actual_median_dt_ms':float(np.median(H['TIME STEP'][1:])),'native_IE_J':float(IE[-1]),'native_HE_J':float(HE[-1]),'final_KE_J':float(KE[-1]),'independent_reference_J':target,'maximum_residual_J':float(abs(R).max()),'negative_control':cid=='FACE_BENDING_N12_Z1','diagnostics':diagnostics,'whole_insertion_ready':False};dump(d/'review.json',r);print({'A33':cid,'pass':r['pass'],'failed':[k for k,v in checks.items() if not v],'IE_HE_J':r['native_IE_J']+r['native_HE_J'],'reference_J':target},flush=True)

def create_runner():
    s=inspect.getsource(previous.run_one);changes={"n='A32_'":"n='A33_'", "ncell=int(re.search(r'_N(6|12)',cid).group(1))":"ncell=int(re.search(r'_N(\\d+)',cid).group(1));nz=int(re.search(r'_Z(\\d+)',cid).group(1))",'brick_grid([ncell,ncell,1]':'brick_grid([ncell,ncell,nz]',"'geometric_Z_elements':1":"'geometric_Z_elements':nz"}
    for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());dump(OUT/'runner_derivation.json',{'created_utc':now(),'source':rel(Path(previous.__file__)),'source_sha256':streamsha(Path(previous.__file__)),'derived_source':s,'literal_changes':changes,'old_native_runs':0})

def run():
    guard();create_runner();rows=[]
    for cid in read(CFG)['cases']:
        run_one('w1',cid);r=read(OUT/'w1'/cid/'review.json');rows.append(r);assert r['checks']['native_full_balance'] and r['checks']['finite_histories'],'Stop rule: full balance or finite history failed'
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'cases':rows,'completed':True,'candidate_cases_exclude_negative_control_only':True,'whole_insertion_ready':False,'objective1_complete':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
