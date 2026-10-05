"""Correct generic beam channel interpretation using native labels; no solver reruns."""
import csv,copy,json,sys
import numpy as np
from run_aircraft_a04 import OUT,CFG,ROOT,PREV,read,dump,sha,rel,now,preserved
from audit_aircraft_a03 import integrate

def main():
    dest=OUT/'cached_review';assert not dest.exists();dest.mkdir();cfg=read(CFG)
    probe=OUT/'history_label_probe';p=probe/'A04_ELASTIC_HIGHY_N5T02.csv'
    with p.open() as f:k=next(csv.reader(f))
    bk=[s for s in k if s.startswith('FORWARD_BEAM_DIAGNOSTIC')]
    order=['F1','F2','F3','M1','M2','M3','IE','SX','EPSP']
    assert len(bk)==696*9
    assert all(all(s.split()[3]==var for s,var in zip(bk[9*i:9*i+9],order)) for i in range(696))
    assert read(probe/'provenance.json')['source_files_unchanged']
    correction=[];cases=[];rawproof=[]
    for case in cfg['execution']['cases']:
        d=OUT/'r1'/case['id'];r=copy.deepcopy(read(d/'audit.json'));z=np.load(d/'balance_history_SI.npz');s=np.load(d/'verified_states_SI.npz');B=z['beam_history_native'];eps=B[:,:,8];sx=B[:,:,7]
        previous={k:r[k] for k in ['maximum_sampled_beam_plastic_strain','maximum_sampled_beam_abs_SX_MPa']}
        r.update(maximum_sampled_beam_plastic_strain=float(np.max(eps)),maximum_sampled_beam_abs_SX_MPa=float(np.max(abs(sx))),beam_history_native_order=order)
        inds=np.flatnonzero(np.max(eps,axis=1)>cfg['acceptance']['plastic_strain_diagnostic_limit'])
        r['first_saved_beam_plastic_strain_above_diagnostic_limit_ms']=float(z['time_s'][inds[0]]*1000) if len(inds) else None
        r['sampled_beam_strain_below_same_diagnostic_limit']=float(np.max(eps))<=cfg['acceptance']['plastic_strain_diagnostic_limit']
        if previous!={q:r[q] for q in previous}:correction.append({'case':case['id'],'original_audit_sha256':sha(d/'audit.json'),'original_interpretation':previous,'corrected_interpretation':{q:r[q] for q in previous},'why':'Requested deck variable order differs from native canonical order; original raw columns and first audits preserved.'})
        # Independently verify saved arrays and scalar energy extraction from native histories.
        finite=all(np.all(np.isfinite(s[k])) for k in s.files) and all(np.all(np.isfinite(z[k])) for k in z.files)
        assert finite and len(s['node_ids'])==35020 and np.array_equal(s['node_ids'],np.arange(1,35021))
        assert float(np.max(abs(z['energy_residual_J'])))==r['maximum_energy_residual_J']
        assert np.all(z['global_plastic_work_J']<=np.array([q for q in z['generated_energy_J']])+1.)
        r['saved_arrays_reread_pass']=True
        J=z['contact_impulse_Ns'];Pf=z['facade_momentum_Ns'];P=z['global_momentum_Ns'];js=z['support_as_cumulative_impulse_Ns'];jf=z['support_as_force_integral_Ns'];forceJ=integrate(J*1000,z['time_s']*1000)*.001
        e_c=float(np.max(np.linalg.norm(Pf-Pf[0]-J-js,axis=1)));e_f=float(np.max(np.linalg.norm(Pf-Pf[0]-forceJ-js,axis=1)))
        r['contact_history_interpretation_test']={'cumulative_impulse_balance_max_error_Ns':e_c,'as_force_integral_balance_max_error_Ns':e_f,'force_hypothesis_rejected_for_nonzero_contact':bool(case['contact'] and e_f>r['momentum_allowance_Ns'] and e_c<r['momentum_allowance_Ns'])}
        r['support_history_interpretation_test']={'cumulative_balance_max_error_Ns':float(np.max(np.linalg.norm(P-P[0]-js,axis=1))),'force_integral_balance_max_error_Ns':float(np.max(np.linalg.norm(P-P[0]-jf,axis=1))),'maximum_support_impulse_norm_Ns':float(np.max(np.linalg.norm(js,axis=1))),'independently_distinguished':False,'reason':'Support signal is below global momentum CSV quantization/declared absolute allowance; preserve both interpretations.'}
        rawproof.append({'case':case['id'],'audit_path':rel(d/'audit.json'),'audit_sha256':sha(d/'audit.json'),'state_sha256':sha(d/'verified_states_SI.npz'),'history_sha256':sha(d/'balance_history_SI.npz'),'states':len(s['time_s']),'saved_arrays_finite':finite})
        cases.append(r)
    nom,half=cases[3],cases[4];zz=[np.load(OUT/'r1'/r['case']['id']/'balance_history_SI.npz') for r in [nom,half]];tc=min(z['time_s'][-1] for z in zz)
    J=[np.array([np.interp(tc,z['time_s'],z['contact_impulse_Ns'][:,i]) for i in range(3)]) for z in zz];gen=[float(np.interp(tc,z['time_s'],z['generated_energy_J'])) for z in zz]
    jd=float(np.linalg.norm(J[1]-J[0])/np.linalg.norm(J[0]));ed=abs(gen[1]-gen[0])/gen[0]
    old=np.load(PREV/'r0/CONTACT_F200_DT080/balance_history_SI.npz');to=old['time_s'][-1];comparison=[]
    for r in cases[:2]+[nom]:
        z=np.load(OUT/'r1'/r['case']['id']/'balance_history_SI.npz');res=float(np.interp(to,z['time_s'],z['energy_residual_J']));oldres=float(old['energy_residual_J'][-1]);comparison.append({'case':r['case']['id'],'common_time_ms':to*1000,'A03_energy_residual_J':oldres,'A04_energy_residual_J':res,'difference_J':res-oldres})
    # Locate the controlling nose triangle without equating computational degeneracy to fracture.
    mesh=read(OUT/'r1/mesh.json');orig=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json');s=np.load(OUT/'r1/PLASTIC_NOMINAL/verified_states_SI.npz');nodes=np.array(mesh['original_triangle_node_ids'][4049])-1;x0=s['initial_positions_m'][nodes];A0=np.linalg.norm(np.cross(x0[1]-x0[0],x0[2]-x0[0]))/2;area=[]
    for t,disp in zip(s['time_s'],s['displacement_m']):
        x=x0+disp[nodes];A=np.linalg.norm(np.cross(x[1]-x[0],x[2]-x[0]))/2;area.append({'time_ms':float(t*1000),'area_ratio_to_initial':float(A/A0)})
    checks={'saved_arrays_and_native_graph_pass':all(r['saved_arrays_reread_pass'] and r['checks']['native_original_connectivity_preserved'] for r in cases),'all_starters_zero_errors_and_warnings':all(r['checks']['starter_zero_errors'] and r['checks']['starter_zero_warnings'] for r in cases),'half_dt_impulse':jd<cfg['acceptance']['half_dt_impulse_difference_fraction'],'half_dt_generated_energy':ed<cfg['acceptance']['half_dt_generated_energy_difference_fraction'],'all_requested_horizons_reached':all(r['requested_horizon_reached'] for r in cases),'all_declared_numerical_checks_pass':all(r['all_declared_checks_pass'] for r in cases),'local_energy_qualified':all(r['checks']['energy_local_within_declared_limit'] for r in cases)}
    result={'created_utc':now(),'cases':cases,'checks':checks,'integrity_only_pass':checks['saved_arrays_and_native_graph_pass'] and checks['all_starters_zero_errors_and_warnings'],'all_declared_checks_pass':all(checks.values()),'half_dt_common_time_ms':tc*1000,'half_dt_impulse_relative_difference':jd,'half_dt_generated_energy_relative_difference':ed,'A03_cached_comparison':comparison,'beam_corrections':correction,'native_beam_channel_order':order,'beam_order_native_probe':rel(p),'native_label_unit_garbage_ignored':True,'saved_result_proof':rawproof,'nose_triangle_4050':{'part':orig['triangular_shells'][4049]['part'],'nodes':(nodes+1).tolist(),'initial_area_m2':float(A0),'area_history':area},'old_files_preserved':preserved(),'old_A03_elastic_failures_retained':True,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':checks['local_energy_qualified'],'radome_reconstructed':False,'NIST_outcomes_used_as_target':False,'partial_runs_have_no_verified_end_time':True,'python_version':sys.version,'numpy_version':np.__version__}
    dump(dest/'review.json',result);print({'review_integrity_pass':result['integrity_only_pass'],'beam_corrections':len(correction),'requested_horizons_reached':sum(r['requested_horizon_reached'] for r in cases),'half_dt_impulse_fraction':jd,'old_files_preserved':result['old_files_preserved']})

if __name__=='__main__':main()
