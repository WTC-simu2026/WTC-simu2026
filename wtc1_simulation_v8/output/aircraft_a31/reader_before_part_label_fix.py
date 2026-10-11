"""Face-loaded volume sandwich with unconstrained interior and independent reference."""
from run_aircraft_a30 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories,constitutive,mesh,native_gate,skin,core,continuous_I
import argparse,inspect,ast,shutil,re,traceback,time,urllib.request
from pathlib import Path
import numpy as np
import run_aircraft_a30 as previous
import linear_sandwich_reference_aircraft_a31 as independent
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a31'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a31_predeclaration.json'
PREV=previous.OUT

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A30';assert read(PREV/'sandwich_qualification_review.json')['sandwich_manufactured_scope_pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    modes=['SHEAR_XZ','SHEAR_YZ','NORMAL_TENSION','NORMAL_COMPRESSION'];c={'iteration':'AIRCRAFT-A31','declared_utc':now(),'seed':1102056,'random_draws':0,'purpose':'Only lower and upper physical outer faces constrained; all skin/core interior nodes free. Test real load transmission rather than imposed internal strains. Preserve A30 geometry, volume,density,LAW12/LAW28 and perfect-bond hypothesis, unchanged whole aircraft.',
      'parent_configuration':rel(previous.CFG),'parent_configuration_sha256':streamsha(previous.CFG),'geometry':read(previous.CFG)['geometry'],'skin':read(previous.CFG)['skin'],'core':read(previous.CFG)['core'],'cases':[f'{m}_N{n}' for m in modes for n in [6,12]]+['SHEAR_XZ_N12_HALF'],
      'loading':{'ramp_ms':.5,'duration_ms':.5,'displacement_mm':.009,'shape':'3s²-2s³','bottom_face':'z=-4.5,XYZfixed','top_face':'z=4.5: XYZprescribed, one component delta*s, other two0','all_interior_nodes_free':True,'modes':{'SHEAR_XZ':{'axis':0,'sign':1},'SHEAR_YZ':{'axis':1,'sign':1},'NORMAL_TENSION':{'axis':2,'sign':1},'NORMAL_COMPRESSION':{'axis':2,'sign':-1}},'amplitude_reason':'nominal displacement/thickness=.001, low elastic regime; source material/yield estimates, not a native response fit','duration_reason':'more than7transits over10mm at weakest source-core in-plane wave speed sqrt(E11/rho)≈144mm/ms. Quasi-static adequacy tested, not presumed.'},
      'independent_reference':{'method':'heterogeneous small-strain conventional8node finite elements,2x2x2Gauss; source3Dtensors, same physical geometry and face boundary conditions; positive-Jacobian,symmetry,equilibrium,virtual-work checks','iterative_solver':'matrix-free Jacobi-preconditioned CG, relative norm1e-10+absolute1e-11N,12000iterations max','native_operator_not_used':True},
      'native_reaction_protocol':{'prior_evidence':rel(core.OUT/'core_verified_review.json'),'observation':'same binary A20REACcomponents act as accumulated nodal impulses, contrary to force label; verify summed raw values against physical momentum before differentiating','units':'raw g*mm/ms toNs factor1e-3; d(raw)/d(time_ms) gives N; subtract prescribed top nodal inertia to recover internal static traction','check_both_interpretations':True,'ambiguous_interpretation_not_qualified':True},
      'acceptance':{'mass_relative':1e-6,'ADMAS_relative':1e-9,'native_full_energy_fraction':.02,'energy_absolute_J':1e-7,'native_RKE_absolute_J':1e-7,'static_IE_fraction':.02,'static_reaction_fraction':.02,'static_reaction_absolute_N':1e-5,'reaction_window':'max error in final10% of ramp, divide by ramp amplitude','interior_displacement_fraction_of_delta':.02,'interior_displacement_absolute_mm':2e-6,'quasi_static_KE_fraction_of_reference':.01,'impulse_momentum_fraction':.02,'impulse_momentum_absolute_Ns':1e-9,'native_boundary_work_fraction':.02,'plastic_work_absolute_J':1e-7,'spatial_change_fraction':.05,'half_actual_dt_ratio_max':.6,'time_change_fraction':.002,'all_native_fields_finite_and_no_erosion':True},
      'qualification':'fineN12candidate requires every original mode gate plus spatial/time convergence and native field audit. Coarse failed gates retained separately, never rewritten. Perfect bond and unmeasured materials remain hypotheses.',
      'execution':{'CPU_threads':1,'GPU':False,'mass_scaling':False,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'history_dt_ms':.001,'animation_dt_ms':.05,'per_process_cap_s':1800,'estimated_minutes':[30,60]},'whole_aircraft_inputs_changed':False,'whole_insertion_ready':False,'old_native_solver_reruns':0,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_reference_and_native':True});sources=[]
    for q in [previous.CFG,PREV/'publication_verification.json',PREV/'sandwich_qualification_review.json',Path(previous.__file__),Path(independent.__file__),Path(skin.__file__),core.OUT/'core_verified_review.json',ROOT/'wtc1_simulation_v8/scripts/verify_aircraft_a20_core.py',ROOT/'wtc1_simulation_v8/scripts/linear_hexa_reference_aircraft_a23.py',ROOT/'wtc1_simulation_v8/output/aircraft_a25/root_geometry_preparation.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad']:sources.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size})
    sd=OUT/'sources';sd.mkdir();u='https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm';q=sd/'th_node.html';q.write_bytes(urllib.request.urlopen(u,timeout=45).read());sources.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size,'url':u,'redistribution':'exclude_third_party'})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'source_archive_rescanned':False,'no_known_damage_target':True});dump(OUT/'whole_cost_observation.json',{'created_utc':now(),'cached_A20_seconds':1191.4197074999975,'cached_A20_physical_ms':20.0001221,'simple_linear_10s_estimate_days':1191.4197074999975*10000/20.0001221/86400,'qualification':'Order-of-magnitude baseline, not a predicted runtime for new discretization or late contact. A mass-neutral efficient formulation or verified regime transition is required; no invented ballistic continuation.'});print({'A31_declared':True,'native_controls':9,'CPU_minutes':[30,60]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def mode(cid):
    key=re.sub(r'_N\d+(?:_HALF)?$','',cid);p=read(CFG)['loading']['modes'][key];return p['axis'],p['sign']*.009

def reference(cid,X,B,parts,bottom,top):
    dest=OUT/'references'/f'{cid}.json';dest.parent.mkdir(exist_ok=True)
    if dest.exists():return read(dest)
    n=int(re.search(r'_N(6|12)',cid).group(1));cache=dest.parent/f'matrix_N{n}.npz';meta=dest.parent/f'matrix_N{n}.json'
    if cache.exists():
        z=np.load(cache);K,dofs,diag=z['K'],z['dofs'],z['diag'];assembly=read(meta)['assembly'];cached=(K,dofs,diag,assembly)
    else:
        cached=independent.assemble(X,B,parts,constitutive(),np.diag([1,1,138,.5,24,41]));K,dofs,diag,assembly=cached;np.savez_compressed(cache,K=K,dofs=dofs,diag=diag);dump(meta,{'created_utc':now(),'configuration_sha256':streamsha(CFG),'assembly':assembly,'matrix_sha256':streamsha(cache),'source_sha256':streamsha(Path(independent.__file__))})
    ax,delta=mode(cid);r=independent.solve(X,B,parts,constitutive(),np.diag([1,1,138,.5,24,41]),bottom,top,ax,delta,cached);dump(dest,{'created_utc':now(),'case':cid,'configuration_sha256':streamsha(CFG),'reference_before_native':True,**r});print({'reference':cid,'seconds':r['seconds'],'CG_iterations':r['CG_iterations'],'energy_J':r['energy_J']},flush=True);return read(dest)

def imposed(L,X,cid,bottom,top):
    T=np.linspace(0,.5,5001);s=3*(T/.5)**2-2*(T/.5)**3;ax,delta=mode(cid);counter=10000;cache={}
    for ni in bottom+top:
        L+=group(ni,f'BOUNDARY_NODE_{ni}',[ni])
        for a,dr in enumerate('XYZ'):
            val=delta*s if ni in top and a==ax else np.zeros(len(T));key=val.tobytes()
            if key not in cache:counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}',f'FACE_DISPLACEMENT_{counter}']+[ff(t,v) for t,v in zip(T,val)]
            counter+=1;L+=[f'/IMPDISP/{counter}',f'BOUNDARY_{ni}_{dr}',ii(cache[key])+f'{dr:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def create_runner():
    s=inspect.getsource(previous.run_one);audit=[]
    changes=[("n='A30_'+cid","n='A31_'+cid"),("duration=.05 if free else .1","duration=.5"),("free=cid.startswith('FREE')","free=False"),("P=parent();mats=","bottom=[int(i+1) for i,x in enumerate(X) if x[2]==-4.5];top=[int(i+1) for i,x in enumerate(X) if x[2]==4.5];reference(cid,X,B,parts,bottom,top);P=parent();mats="),("L=imposed(L,X,cid)","L=imposed(L,X,cid,bottom,top)"),("+['/END'];(d/(n+'_0000.rad'))","+['/TH/NODE/2','FACE_IMPULSES',''.join(f'{v:>10}' for v in ['REACX','REACY','REACZ'])]+[ii(i,0) for i in bottom+top]+['/END'];(d/(n+'_0000.rad'))"),("ff(0,.025)","ff(0,.05)"),("'physical_shared_faces':True","'physical_shared_faces':True,'bottom_node_ids':bottom,'top_node_ids':top,'interior_nodes_free':True")]
    for a,b in changes:
        n=s.count(a);assert n>0,a;s=s.replace(a,b);audit.append({'old':a,'new':b,'count':n})
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());dest=OUT/'runner_derivation.json'
    if not dest.exists():dump(dest,{'created_utc':now(),'source':rel(Path(previous.__file__)),'source_sha256':streamsha(Path(previous.__file__)),'derived_source':s,'changes':audit,'previous_solvers_not_rerun':True})

def cumulative_trap(y,T):return np.concatenate([np.zeros_like(y[:1]),np.cumsum((y[1:]+y[:-1])*.5*np.diff(T).reshape((-1,)+(1,)*(y.ndim-1)),axis=0)],axis=0)

def review(d,n):
    guard();a=read(CFG)['acceptance'];g=read(d/'generation.json');ref=read(OUT/'references'/f"{g['case']}.json");H=histories(d/(n+'T01.csv'));T=H['time'];X0=np.asarray(g['nodes_mm']);m=np.asarray(g['known_nodal_masses_g']);nk=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(nk)==6*len(X0);node=np.column_stack([H[k] for k in nk]).reshape(len(T),len(X0),6);X=X0+node[:,:,:3];V=node[:,:,3:];bottom=np.asarray(g['bottom_node_ids'])-1;top=np.asarray(g['top_node_ids'])-1;faces=np.concatenate([bottom,top]);fk=[k for k in H if k.startswith('FACE_IMPULSES')];assert len(fk)==3*len(faces);Q=np.column_stack([H[k] for k in fk]).reshape(len(T),len(faces),3);ax,delta=mode(g['case']);s=3*(T/.5)**2-2*(T/.5)**3;acc=delta*(6-12*T/.5)/.5**2;velocity=delta*(6*T/.5-6*(T/.5)**2)/.5
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;IE=H['INTERNAL ENERGY']*.001;KE=H['KINETIC ENERGY']*.001;R=E-E[0]-EW;P=np.sum(m[None,:,None]*V,axis=1)*.001;L=np.sum(m[None,:,None]*np.cross(X,V),axis=1)*1e-6;raw_impulse=Q.sum(axis=1)*.001;force_impulse=cumulative_trap(Q.sum(axis=1),T)*.001;dp=P-P[0];ptol=.02*float(np.linalg.norm(dp,axis=1).max())+1e-9;err_impulse=float(np.linalg.norm(raw_impulse-raw_impulse[0]-dp,axis=1).max());err_force=float(np.linalg.norm(force_impulse-dp,axis=1).max());impulse_pass=err_impulse<ptol;force_pass=err_force<ptol;protocol=impulse_pass and not force_pass
    Fn=np.gradient(Q,T,axis=0,edge_order=2);Ftop=Fn[:,len(bottom):,ax].sum(axis=1)-float(m[top].sum())*acc;window=(T>=.45)&(s>0);static_force_error=float(abs(Ftop[window]/s[window]-ref['top_reaction_N']).max());Wnodes=cumulative_trap(np.sum(Fn*V[:,faces,:],axis=(1,2)),T)*.001;work_error=float(abs(Wnodes-EW).max());U=np.asarray(ref['displacements_mm'])*s[-1];free=np.setdiff1d(np.arange(len(X0)),faces);uerr=float(abs(node[-1,free,:3]-U[free]).max());boundary=np.zeros((len(T),len(faces),3));boundary[:,len(bottom):,ax]=delta*s[:,None];berr=float(abs(node[:,faces,:3]-boundary).max());pw_keys=[k for k in H if k.startswith('SANDWICH_PARTS') and k.strip().endswith('PW')];assert len(pw_keys)==3;PW=sum(H[k] for k in pw_keys)*.001;target=ref['energy_J']*s[-1]**2;scale=max(float(abs(E).max()),float(abs(EW).max()));moment_from_impulses=(np.sum(np.cross(X[:,faces,:],Q),axis=1)-cumulative_trap(np.sum(np.cross(V[:,faces,:],Q),axis=1),T))*1e-6;ldiagnostic=float(np.linalg.norm(moment_from_impulses-moment_from_impulses[0]-(L-L[0]),axis=1).max())
    checks={'normal_termination':True,'strict_zero_warnings':read(d/'starter_gate.json')['pass'],'native_frames':read(d/'native_frame_gate.json')['pass'],'physical_mass':bool(abs(H['MASS'][0]-.2214)<1e-6*.2214),'constant_mass':bool(abs(H['MASS']-H['MASS'][0]).max()<1e-6*.2214),'no_ADMAS':bool(abs(H['ADDED MASS']).max()<1e-9*.2214),'native_full_balance':bool(abs(R).max()<.02*scale+1e-7),'nonnegative_IE':bool(IE.min()>-1e-7),'no_native_RKE':bool(abs(H['ROTATION ENERGY']).max()*.001<1e-7),'independent_static_IE':bool(abs(IE[-1]-target)<.02*target+1e-7),'independent_static_reaction':bool(protocol and static_force_error<.02*abs(ref['top_reaction_N'])+1e-5),'independent_interior_displacements':bool(uerr<.02*abs(delta)+2e-6),'boundary_displacements':bool(berr<2e-6),'quasi_static_final_KE':bool(KE[-1]<.01*target+1e-7),'elastic_part_PW':bool(abs(PW).max()<1e-7),'reaction_impulse_interpretation_verified':bool(protocol),'independent_boundary_work':bool(protocol and work_error<.02*max(float(abs(EW).max()),target)+1e-7)}
    np.savez_compressed(d/'histories_SI.npz',time_ms=T,total_J=E,IE_J=IE,KE_J=KE,EW_J=EW,residual_J=R,positions_mm=X,velocities_m_s=V,physical_L_kg_m2_s=L,momentum_Ns=P,time_step_ms=H['TIME STEP'],top_internal_force_N=Ftop,boundary_work_J=Wnodes,raw_face_impulses=Q);r={'created_utc':now(),'case':g['case'],'last_ms':float(T[-1]),'native_mass_g':float(H['MASS'][0]),'maximum_residual_J':float(abs(R).max()),'elastic_reference_J':target,'native_elastic_comparison_J':float(IE[-1]),'final_KE_J':float(KE[-1]),'reference_force_N':ref['top_reaction_N'],'maximum_late_static_force_error_N':static_force_error,'maximum_interior_displacement_error_mm':uerr,'maximum_boundary_work_error_J':work_error,'maximum_native_PW_J':float(abs(PW).max()),'reaction_protocol':{'raw_impulse_error_Ns':err_impulse,'time_integrated_force_error_Ns':err_force,'tolerance_Ns':ptol,'impulse_candidate_pass':impulse_pass,'force_candidate_pass':force_pass,'verified_unambiguous_impulse':protocol},'angular_impulse_diagnostic_error_kg_m2_s':ldiagnostic,'angular_diagnostic_is_not_new_postrun_gate':True,'checks':checks,'pass':all(checks.values()),'whole_insertion_ready':False};dump(d/'review.json',r);print({'case':g['case'],'pass':r['pass'],'failed':[k for k,v in checks.items() if not v],'IE_J':float(IE[-1]),'ref_J':target},flush=True)

def run():
    guard();create_runner()
    for cid in read(CFG)['cases']:
        d=OUT/'w0'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
    dump(OUT/'native_case_summary.json',{'created_utc':now(),'cases':[read(OUT/'w0'/cid/'review.json') for cid in read(CFG)['cases']],'whole_insertion_ready':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
