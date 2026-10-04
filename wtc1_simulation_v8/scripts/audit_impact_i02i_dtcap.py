"""I02I-F saved-history audit. No rephasing, smoothing or gate promotion."""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
import numpy as np
import run_impact_i02i_dtcap as f
import audit_impact_i02i_fixed_penalty as columns

ROOT, OUT, CFG = f.ROOT, f.OUT, f.CFG
DEST=OUT/'verification_r1'
SUMMARY=DEST/'summary.json'

def audit_case(cfg,case):
    folder=OUT/case['id'];dest=DEST/case['id'];dest.mkdir()
    # Redirect the old audit function only inside this new process. The old
    # script, configuration, histories and audits remain byte-identical.
    previous=f.inherited.OUT
    try:
        f.inherited.OUT=OUT
        inherited=f.inherited.audit_case(cfg,case,dest/'inherited')
    finally:f.inherited.OUT=previous
    h,a=f.inherited.cached.read_history(folder);idx={s.strip():i for i,s in enumerate(h)}
    ci=columns.columns(h,'SEAM_HISTORY',6)[1];nodes=columns.columns(h,'NODES',6)
    get=lambda name:a[:,idx[name]]
    t=a[:,0];off=a[:,ci[0]];dt=np.diff(t);breaks=np.flatnonzero(np.diff(off)<-.5)+1
    j=int(breaks[0]) if len(breaks) else None
    post=np.arange(len(t))>=(j+2 if j is not None else len(t))
    mass_node=cfg['connector']['mass_g']/2
    momentum={};signals={};fieldnames=['time_ms','OFF']
    history=[t,off]
    for axis,velocity,impulse in [('X',2,4),('Y',3,5)]:
        j1=a[:,nodes[1][impulse]];j2=a[:,nodes[2][impulse]]
        p=get(axis+'-MOMENTUM');nodal=mass_node*(a[:,nodes[1][velocity]]+a[:,nodes[2][velocity]])
        residual=j1+j2-p;scale=max(float(np.max(np.abs(j1))),float(np.max(np.abs(j2))),1e-15)
        pscale=float(np.max(np.abs(p)));nerror=np.abs(nodal-p)
        # Quantization diagnostic only. Raw residuals determine the gates.
        ulps=np.spacing(np.abs(j1).astype(np.float32)).astype(float)+np.spacing(np.abs(j2).astype(np.float32)).astype(float)
        values={'max_raw_residual_N_ms':float(np.max(np.abs(residual))),
            'boundary_impulse_scale_N_ms':scale,'raw_boundary_residual_fraction':float(np.max(np.abs(residual)))/scale,
            'global_momentum_peak_N_ms':pscale,
            'raw_net_momentum_residual_fraction':None if pscale==0 else float(np.max(np.abs(residual)))/pscale,
            'max_nodal_momentum_error_N_ms':float(np.max(nerror)),
            'nodal_momentum_error_fraction':0. if pscale==0 and float(np.max(nerror))==0 else float(np.max(nerror))/max(pscale,1e-15),
            'max_sum_float32_impulse_ulps_N_ms':float(np.max(ulps)),
            'float32_ulp_over_peak_net_momentum':None if pscale==0 else float(np.max(ulps))/pscale,
            'no_quantization_correction_applied':True}
        if np.any(post):
            values.update(post_max_raw_residual_N_ms=float(np.max(np.abs(residual[post]))),
                post_raw_boundary_residual_fraction=float(np.max(np.abs(residual[post])))/scale,
                post_nodal_error_fraction=float(np.max(nerror[post]))/max(pscale,1e-15))
        momentum[axis]=values;signals[axis]=(j1,j2,p)
        fieldnames += [axis+'_node1_impulse_N_ms',axis+'_node2_impulse_N_ms',axis+'_global_momentum_N_ms',axis+'_nodal_momentum_N_ms',axis+'_raw_residual_N_ms']
        history += [j1,j2,p,nodal,residual]
    cap=case['maximum_dt_ms'];actual=get('TIME STEP')
    sampling={'rows':len(t),'cycles':inherited['metrics']['engine_cycles'],'requested_maximum_dt_ms':cap,
        'maximum_saved_solver_dt_ms':float(np.max(actual)),
        'minimum_saved_solver_dt_ms':float(np.min(actual)),
        'maximum_recorded_dt_ms':float(np.max(dt)),
        'maximum_post_OFF_recorded_dt_ms':None if j is None else float(np.max(dt[j:])),
        'last_recorded_time_ms':float(t[-1]),'declared_end_ms':json.loads((folder/'generation.json').read_text())['end_ms'],
        'CSV_time_difference_tolerance_ms':cfg['gates']['csv_time_difference_tolerance_ms'],
        'last_record_is_not_extrapolated':True}
    added=float(np.max(np.abs(get('ADDED MASS'))))
    checks=dict(inherited['checks'])
    checks.update(maximum_saved_solver_dt=bool(np.max(actual)<=cap*(1+cfg['gates']['maximum_solver_dt_relative_tolerance'])),
        maximum_recorded_dt_with_CSV_roundoff=bool(np.max(dt)<=cap+cfg['gates']['csv_time_difference_tolerance_ms']),
        no_added_mass=added<=cfg['gates']['added_mass_g'],
        covered_end_without_extrapolation=sampling['declared_end_ms']-t[-1]<=cfg['gates']['end_coverage_steps']*cap+cfg['gates']['csv_time_difference_tolerance_ms'],
        zero_force_after_settled_OFF=True if j is None else bool(np.max(np.abs(a[j+2:,ci[1:3]]))<=cfg['gates']['force_zero_N']))
    for axis,v in momentum.items():
        checks['raw_impulse_boundary_'+axis]=v['raw_boundary_residual_fraction']<=cfg['gates']['impulse_boundary_fraction']
        checks['nodal_momentum_'+axis]=v['nodal_momentum_error_fraction']<=cfg['gates']['nodal_momentum_fraction']
        if j is not None:checks['post_OFF_raw_impulse_'+axis]=v['post_raw_boundary_residual_fraction']<=cfg['gates']['impulse_boundary_fraction']
    events=[]
    for e in inherited['deactivation_events']:
        j=e['row'];k=e['force_zero_row'];ie=get('INTERNAL ENERGY')*.001;ke=get('KINETIC ENERGY')*.001;we=get('EXTERNAL WORK')*.001
        v=dict(e);v.pop('rows_near_event')
        v.update(IE_settled_minus_last_active_J=float(ie[k]-ie[j-1]),
            KE_settled_minus_last_active_J=float(ke[k]-ke[j-1]),
            WE_settled_minus_last_active_J=float(we[k]-we[j-1]),
            partition_on_OFF_row_not_used=True)
        events.append(v)
    rawcsv=next(folder.glob('*.csv'))
    result={'created_utc':f.NOW(),'case':case,'metrics':inherited['metrics'],'sampling':sampling,
        'momentum':momentum,'events':events,'added_mass_g':added,'checks':{k:bool(v) for k,v in checks.items()},
        'all_checks_pass':all(checks.values()),'raw_history_sha256':f.sha(rawcsv),
        'audit_script_sha256':f.sha(__file__),'inherited_audit_script_sha256':f.sha(f.inherited.__file__),
        'physical_propagation_qualified':False,'free_body_inertia_qualified':False,
        'interpretation':'Raw unshifted histories; inherited strict same-row OFF/FX failures remain failed. IE retained after deletion is numerical unrecovered work.'}
    f.dump(dest/'audit.json',result)
    with (dest/'momentum.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.writer(file);writer.writerow(fieldnames);writer.writerows(zip(*history))
    return result,(t,signals)

def audit():
    assert not DEST.exists(),'Preserve audit revisions';DEST.mkdir()
    cfg=json.loads(CFG.read_text(encoding='utf-8'));results={};signals={}
    for c in cfg['cases']:
        results[c['id']],signals[c['id']]=audit_case(cfg,c)
    comparisons=[]
    for left,right in cfg['comparison_pairs']:
        a,b=results[left],results[right];ea,eb=a['events'],b['events']
        energy=abs(a['metrics']['final_IE_J']-b['metrics']['final_IE_J'])/max(abs(a['metrics']['final_IE_J']),abs(b['metrics']['final_IE_J']),1e-15)
        event=abs(ea[0]['OFF_time_ms']-eb[0]['OFF_time_ms']) if ea and eb else None
        checks={'final_internal_work':energy<=cfg['gates']['comparison_energy_fraction'],
            'event_time_within_two_coarse_steps':event is not None and event<=2*a['case']['maximum_dt_ms']+cfg['gates']['csv_time_difference_tolerance_ms']}
        row={'cases':[left,right],'final_IE_difference_fraction':energy,'event_time_difference_ms':event}
        if left.startswith('AFTER'):
            ts=cfg['comparison_common_post_failure_times_ms'];ta,sa=signals[left];tb,sb=signals[right]
            covered=[t for t in ts if ta[0]<=t<=ta[-1] and tb[0]<=t<=tb[-1]]
            av=np.interp(covered,ta,sa['X'][1]);bv=np.interp(covered,tb,sb['X'][1]);scale=max(a['momentum']['X']['global_momentum_peak_N_ms'],b['momentum']['X']['global_momentum_peak_N_ms'])
            diff=float(np.max(np.abs(av-bv)))/scale
            checks.update(all_requested_post_failure_times_covered=len(covered)==len(ts),
                post_failure_small_channel_impulse=diff<=cfg['gates']['after_failure_impulse_comparison_fraction'])
            row.update(requested_times_ms=ts,assessed_times_ms=covered,impulse_difference_fraction=diff,no_extrapolation=True)
        row['checks']={k:bool(v) for k,v in checks.items()};comparisons.append(row)
    old=json.loads((f.D/'impulse_diagnostics.json').read_text(encoding='utf-8'))
    old_after=old['cases']['SHEAR_AFTER_FAILURE']['X']['residual_fraction_of_boundary_impulse']
    new_after={n:v['momentum']['X']['raw_boundary_residual_fraction'] for n,v in results.items() if n.startswith('AFTER')}
    # Preserve the E sensitivity and missing-point limitations as a cached review.
    e=json.loads((f.E/'verification_r1/summary.json').read_text(encoding='utf-8'))
    review={n:{'maximum_KE_IE_fraction':v['case_audit']['metrics']['maximum_kinetic_to_internal_significant_window'],
        'failed_case_gates':[k for k,ok in v['case_audit']['gates'].items() if not ok],
        'failed_or_unassessed_comparison_gates':[k for k,ok in v['comparison']['checks'].items() if not ok],
        'coverage':v['comparison']['coverage'],'maximum_ctoa_difference_fraction':v['comparison']['maximum_ctoa_difference_fraction']}
        for n,v in e['cases'].items()}
    f.dump(OUT/'cached_E_sensitivity_review.json',{'created_utc':f.NOW(),'cases':review,
        'source_summary_sha256':f.sha(f.E/'verification_r1/summary.json'),'gates_closed_by_F':False,
        'no_solver_rerun':True,'no_missing_point_extrapolation':True})
    summary={'iteration':'IMPACT-I02I-F','created_utc':f.NOW(),'cases':results,'comparisons':comparisons,
        'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),
        'case_checks_total':sum(len(v['checks']) for v in results.values()),
        'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparisons),
        'comparison_checks_total':sum(len(v['checks']) for v in comparisons),
        'all_scientific_checks_pass':all(v['all_checks_pass'] for v in results.values()) and all(all(v['checks'].values()) for v in comparisons),
        'cached_D_after_failure_X_raw_boundary_residual_fraction':old_after,
        'F_after_failure_X_raw_boundary_residual_fractions':new_after,
        'strict_same_row_OFF_FX_failed_cases':[n for n,v in results.items() if not v['checks']['strict_same_row_OFF_FX']],
        'runtime_seconds':json.loads((OUT/'execution_complete.json').read_text())['runtime_seconds'],
        'config_sha256':f.sha(CFG),'audit_script_sha256':f.sha(__file__),
        'software':{'python':sys.version,'numpy':np.__version__,'solver':'OpenRadioss VERS2026, one thread; executable SHA-256 in execution records'},
        'old_solvers_rerun':False,'E_sensitivities_resolved':False,
        'physical_propagation_qualified':False,'mixed_mode_dissipation_calibrated':False,
        'free_body_inertia_qualified':False,'source_convention_verified':False}
    f.dump(SUMMARY,summary)
    print(json.dumps({k:summary[k] for k in ['case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds','all_scientific_checks_pass','F_after_failure_X_raw_boundary_residual_fractions']}),flush=True)

if __name__=='__main__':audit()
