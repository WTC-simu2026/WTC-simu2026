"""New native mixed/path witnesses, complete material Jacobian and trial-state oracles."""
from probe_aircraft_a60 import ROOT,OUT,CFG,read,dump,sha,now,rel,engine
from material_aircraft_a60 import State,trial,run_path,path_values
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records
import numpy as np,json,struct,time

def native_review():
    engine();cfg=read(CFG);p=cfg['cohesive'];lim=cfg['acceptance'];rows=[]
    for case in cfg['cases']:
        d=OUT/'native'/case['id'];name=read(d/'generation.json')['name'];H=histories(d/(name+'T01.csv'));T=H['time'];V=np.column_stack(list(H.values()));rr=records(d/(name+'T01'))
        nr=next(n for n in range(3,10) if sum(map(len,rr[-n:]))==V.shape[1]*4 and len(rr[-n])==4)
        header=len(rr)-len(T)*nr;assert header>0;frames=[rr[header+k*nr:header+(k+1)*nr] for k in range(len(T))];sizes=[len(v) for v in frames[0]]
        assert all([len(v) for v in f]==sizes for f in frames)
        binary=np.asarray([np.concatenate([np.frombuffer(b,dtype='>f4').astype(float) for b in f]) for f in frames]);assert binary.shape==V.shape and np.allclose(binary,V,rtol=6e-7,atol=1e-12)
        N=np.stack([np.column_stack([v for k,v in H.items() if k.startswith('REACTION_'+axis)]).reshape(len(T),8,3) for axis in 'XYZ'],axis=-1)
        # Native fields per axis are displacement, velocity and reaction impulse.
        q=N[:,4:,0,:].mean(axis=1);impulse=N[:,:4,2,:].sum(axis=1);forces=-np.gradient(impulse,T,axis=0)
        tr,state,limits=run_path(q,p);area=case['L_mm']**2;reference=tr*area
        strengths=np.array([p['TT_MPa'],p['TT_MPa'],p['TN_MPa']]);error=float((abs(forces-reference)/(area*strengths)).max())
        EW=H['EXTERNAL WORK']*.001;IE=H['INTERNAL ENERGY']*.001;KE=H['KINETIC ENERGY']*.001;residual=IE+KE+H['ROTATION ENERGY']*.001+H['HOURGLASS ENERGY']*.001-EW;residual-=residual[0]
        motion=float(abs(q-path_values(T,case,p)).max());work=float(np.sum((N[1:,:,1,:]+N[:-1,:,1,:])*.5*np.diff(N[:,:,2,:],axis=0))*.001)
        model_increment=np.sum((reference[1:]+reference[:-1])*.5*np.diff(q,axis=0),axis=1)*.001;model_work=np.r_[0,np.cumsum(model_increment)]
        target=max(p['GI_N_mm'],p['GII_N_mm'])*area*.001
        expected_G=None
        if case['proportional']:
            direction=np.asarray(case['direction']);kn=p['EN_N_mm3']*direction[2]**2;ks=p['ET_N_mm3']*np.sum(direction[:2]**2);wN=kn/(kn+ks);wS=ks/(kn+ks);exponent=p['power_exponent']
            expected_G=((wN/p['GI_N_mm'])**exponent+(wS/p['GII_N_mm'])**exponent)**(-1/exponent);target=expected_G*area*.001
        tests={'native_binary_all_CSV_channels':True,'native_loaded_end_time':bool(T[-1]>=1-1e-6),'native_normal_no_USER_BREAK':('NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace') and 'USER BREAK' not in (d/'engine.log').read_text(errors='replace')),
           'mass_8g':bool(np.allclose(H['MASS'],8,rtol=1e-6,atol=1e-6)),'no_added_mass':bool(np.all(H['ADDED MASS']==0)),'imposed_vector_motion':motion<=lim['prescribed_motion_mm'],'all_three_native_tractions':error<=lim['traction_maximum_relative'],
           'global_work_energy':float(abs(residual).max())<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'native_impulse_work':abs(work-EW[-1])<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],
           'complete_own_work_vs_native_IE':float(abs(model_work-IE).max())<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'reference_damage_irreversible':bool(np.all(np.diff(state[:,1])>=-1e-12))}
        if expected_G is not None:tests['mixed_power_law_final_G']=abs(IE[-1]/area*1000-expected_G)<=lim['work_per_area_G_fraction']*expected_G
        if case['id'].startswith('MIX'):
            reload=abs(float(np.interp(.75,T,IE)-np.interp(.25,T,IE)))/target;tests['equal_peak_reload_no_new_energy']=reload<=lim['equal_peak_energy_fraction']
        else:reload=None
        result={'case':case,'checks':{k:bool(v) for k,v in tests.items()},'pass':all(tests.values()),'failed_checks':[k for k,v in tests.items() if not v],'native_rows':len(T),'native_record_sizes':sizes,'maximum_traction_relative_error':error,'maximum_motion_error_mm':motion,'maximum_global_residual_J':float(abs(residual).max()),'impulse_work_error_J':abs(work-EW[-1]),'maximum_reference_work_IE_difference_J':float(abs(model_work-IE).max()),'native_final_IE_J':float(IE[-1]),'expected_mixed_G_N_mm':expected_G,'native_work_per_area_N_mm':float(IE[-1]/area*1000),'reload_energy_difference_fraction':reload,'final_reference_state':state[-1].tolist(),'physical_fracture_data_measured':False,'whole_transfer_qualified':False}
        np.savez_compressed(d/'mixed_diagnostics.npz',time_s=T*.001,gap_mm=q,native_force_N=forces,reference_force_N=reference,reference_state=state,reference_thresholds_mm=limits,reference_work_J=model_work,native_IE_J=IE,native_EW_J=EW,native_KE_J=KE,residual_J=residual)
        dump(d/'mixed_review.json',result);rows.append(result);print(json.dumps({'case':case['id'],'failed':result['failed_checks'],'traction_error':error,'native_G':result['native_work_per_area_N_mm']}),flush=True)
    dt=abs(rows[0]['native_final_IE_J']-rows[1]['native_final_IE_J'])/rows[0]['native_final_IE_J'];area=abs(rows[0]['native_work_per_area_N_mm']-rows[2]['native_work_per_area_N_mm'])/rows[0]['native_work_per_area_N_mm']
    checks={'all_new_cases_pass':all(r['pass'] for r in rows),'half_dt_mixed_work':dt<=lim['half_dt_work_fraction'],'area_normalized_mixed_work':area<=lim['area_normalized_work_fraction']}
    dump(OUT/'mixed_native_review.json',{'created_utc':now(),'cases':rows,'checks':checks,'pass':all(checks.values()),'half_dt_difference_fraction':dt,'area_difference_fraction':area,'native_Engine_integration_ready':False,'new_whole_physical_credit_s':0})

def newton(target,start,p,mutate=False):
    K=np.diag([p['ET_N_mm3'],p['ET_N_mm3'],p['EN_N_mm3']])*4
    base=State();f=trial(target,base,p)[0]+K@target;x=np.asarray(start,float).copy();trace=[]
    for iteration in range(30):
        tr,C,state,_=trial(x,base,p);r=tr+K@x-f;trace.append({'iteration':iteration,'gap':x.tolist(),'base_state':base.__dict__,'trial_state':state.__dict__,'residual':float(np.linalg.norm(r))})
        if np.linalg.norm(r)<1e-8:return x,state,trace
        if mutate:base=state
        x-=np.linalg.solve(C+K,r)
    return x,state,trace

def oracles():
    engine();p=read(CFG)['cohesive'];checks=[];jacobians=[]
    def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
    samples=[([.025,.01,.04],State(),'elastic'),([.11,.08,.13],State(.03,.02),'mixed_loading'),([.1,.06,.07],State(.22,.7),'unloading'),([.04,.025,-.03],State(.18,.6),'compression_shear'),([.25,.12,.08],State(.2,.45),'ratio_change')]
    for gap,base,label in samples:
        q=np.asarray(gap,float);F,C,state,_=trial(q,base,p);eps=1e-7;FD=np.column_stack([(trial(q+eps*np.eye(3)[j],base,p)[0]-trial(q-eps*np.eye(3)[j],base,p)[0])/(2*eps) for j in range(3)])
        e=float(abs(C-FD).max()/max(1,abs(C).max()));check('all_component_material_Jacobian_FD_'+label,e<1e-7,e)
        digest=repr(base);a=trial(q+.17,base,p);b=trial(q,base,p);check('discarded_trial_no_state_pollution_'+label,repr(base)==digest and np.array_equal(F,b[0]) and b[2]==state)
        check('damage_and_peak_monotone_'+label,state.damage>=base.damage and state.peak>=base.peak)
        jacobians.append({'case':label,'gap_mm':q.tolist(),'Jacobian_N_mm3':C.tolist(),'normalized_nonsymmetry':float(abs(C-C.T).max()/max(1,abs(C).max())),'state':state.__dict__})
    for q in [[0,0,.15],[.4,0,0]]:
        vector=np.asarray(q,float);F,C,state,_=trial(vector,State(),p);j=int(np.argmax(abs(vector)));k=p['EN_N_mm3'] if j==2 else p['ET_N_mm3'];T=p['TN_MPa'] if j==2 else p['TT_MPa'];G=p['GI_N_mm'] if j==2 else p['GII_N_mm'];expected=-T/(2*G/T-T/k)
        check('independent_pure_closed_softening_'+str(j),abs(C[j,j]-expected)<1e-8)
    check('mixed_material_Jacobian_is_generally_nonsymmetric',any(j['normalized_nonsymmetry']>1e-3 for j in jacobians))
    target=np.asarray([.11,.08,.13]);roots=[];traces=[]
    for start in [[0,0,0],[.4,.3,.45],[-.03,.02,.07]]:
        q,state,trace=newton(target,start,p);roots.append(q);traces.append({'start':start,'converged_gap':q.tolist(),'state':state.__dict__,'iterations':trace});check('Newton_committed_state_frozen_'+str(start),np.linalg.norm(q-target)<1e-10 and all(t['base_state']==State().__dict__ for t in trace))
    q,bad,wrong=newton(target,[.4,.3,.45],p,True);check('negative_control_premature_commit_is_detected',np.linalg.norm(q-target)>1e-4,{'wrong_gap':q.tolist(),'damage':bad.damage})
    result={'created_utc':now(),'checks':checks,'pass':all(c['pass'] for c in checks),'sample_Jacobians':jacobians,'Newton_trials':traces,'preserved_wrong_state_negative_control':wrong,'source_branch':'displacement criterion / linear softening / power-law mixing / asymmetric compression','moving_frame_geometry_and_native_state_rollback_qualified':False,'native_solver_symmetry_compatibility_qualified':False,'native_Engine_integration_ready':False}
    dump(OUT/'material_Jacobian_state_review.json',result);print(json.dumps({'oracles_pass':result['pass'],'checks':len(checks),'failed':[c['name'] for c in checks if not c['pass']]}),flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['native_review','oracles']);globals()[parser.parse_args().action]()
