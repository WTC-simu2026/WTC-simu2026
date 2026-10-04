"""H saved raw elastic/fracture histories, no time shift or extrapolation."""
from __future__ import annotations
import argparse,csv,json,re,sys
import numpy as np
import run_impact_i02i_free_fracture as h
import audit_impact_i02i_table_free as ga
import audit_impact_i02i_fixed_penalty as columns
import reference_impact_i02i_free_fracture as ref
ROOT,OUT=h.ROOT,h.OUT

def elastic():
    dest=OUT/'elastic_verification_r1';assert not dest.exists(),'Keep audits';dest.mkdir()
    cfg=json.loads(h.ELCFG.read_text(encoding='utf-8'));old=json.loads((h.g.OUT/'verification_r1/summary.json').read_text())
    assert h.sha(h.g.OUT/'verification_r1/summary.json')==cfg['saved_G_baseline']['sha256']
    results={};comparison=[];base=old['cases']['FREE_ELASTIC_050NS']
    for c in cfg['cases']:
        prev=ga.OUT,ga.DEST,ga.CFG
        try:ga.OUT,ga.DEST,ga.CFG=OUT,dest,h.ELCFG;v=ga.free_case(cfg,c)
        finally:ga.OUT,ga.DEST,ga.CFG=prev
        v['H_audit_sha256']=h.sha(__file__);h.dump(dest/c['id']/'audit.json',v);results[c['id']]=v
        ratio=c['maximum_dt_ms']/.00005;checks={};metrics={}
        for key,power in [('displacement_fraction',2),('global_momentum_fraction',2),('energy_residual_fraction',2),
                ('nodal_velocity_fraction',1),('raw_initial_momentum_impulse_fraction',1)]:
            measured=v['metrics'][key]/base['metrics'][key];error=abs(measured/ratio**power-1)
            metrics[key]={'H_over_G50':measured,'expected':ratio**power,'relative_scaling_error':error}
            checks[key]=error<=cfg['gates']['elastic_step_scaling_relative_tolerance']
        comparison.append({'case':c['id'],'cached_G_case':'FREE_ELASTIC_050NS','metrics':metrics,'checks':checks,'no_rerun':True})
    passed=all(v['all_checks_pass'] and all(v['strict_raw_1pct_diagnostics'].values()) for v in results.values()) and all(all(v['checks'].values()) for v in comparison)
    summary={'id':'IMPACT-I02I-H-ELASTIC','created_utc':h.NOW(),'cases':results,'comparisons':comparison,'all_checks_pass':passed,
        'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),'case_checks_total':sum(len(v['checks']) for v in results.values()),
        'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparison),'comparison_checks_total':sum(len(v['checks']) for v in comparison),
        'strict_raw_1pct_all_pass':all(all(v['strict_raw_1pct_diagnostics'].values()) for v in results.values()),
        'config_sha256':h.sha(h.ELCFG),'audit_sha256':h.sha(__file__),'old_G_failed_diagnostics_preserved':True,
        'no_time_shift':True,'physical_impact_qualified':False}
    h.dump(dest/'summary.json',summary)
    print(json.dumps({'elastic_pass':passed,'case_gates':[summary['case_checks_passed'],summary['case_checks_total']],
        'comparison_gates':[summary['comparison_checks_passed'],summary['comparison_checks_total']],
        'raw_impulse_fraction':{n:v['metrics']['raw_initial_momentum_impulse_fraction'] for n,v in results.items()}}),flush=True)

def normal_case(cfg,c,dest):
    folder=OUT/c['id'];dest.mkdir();headers,a=h.g.f.inherited.cached.read_history(folder)
    ix={s.strip():i for i,s in enumerate(headers)};get=lambda n:a[:,ix[n]];t=a[:,0]
    ci=columns.columns(headers,'SEAM_HISTORY',6)[1];nodes=columns.columns(headers,'NODES',6);r=cfg['reference'];m=r['moving_mass_g']
    d=a[:,nodes[2][1]]-a[:,nodes[1][1]];v=a[:,nodes[2][3]];fy=a[:,ci[2]];off=a[:,ci[0]]
    j1=a[:,nodes[1][5]];j2=a[:,nodes[2][5]];p=get('Y-MOMENTUM');pn=m*(v+a[:,nodes[1][3]])
    analytic=ref.state(t,r);ie=get('INTERNAL ENERGY')*.001;ke=get('KINETIC ENERGY')*.001;we=get('EXTERNAL WORK')*.001
    E0,P0=r['initial_energy_J'],r['initial_momentum_N_ms'];cap=c['maximum_dt_ms'];peak=lambda x:float(np.max(np.abs(x)))
    jint=np.r_[0,np.cumsum(-.5*(fy[1:]+fy[:-1])*np.diff(t))]
    wforce=np.r_[0,np.cumsum(.5*(fy[1:]+fy[:-1])*np.diff(d)*.001)]
    Wd=ref.work(d,r)*.001;U=np.where(off>=.5,fy*fy/(2*r['k_N_per_mm'])*.001,0)
    breaks=np.flatnonzero(np.diff(off)<-.5)+1;j=int(breaks[0]) if len(breaks) else None
    settled=t>=r['failure_time_ms']+2*cap
    metrics={'displacement_fraction':peak(d-analytic['delta_mm'])/r['deltaf_mm'],
        'velocity_fraction':peak(v-analytic['v_mm_per_ms'])/r['v0_mm_per_ms'],
        'force_fraction':peak(fy-analytic['force_N'])/r['peak_N'],
        'global_momentum_fraction':peak(p-analytic['P_N_ms'])/P0,'nodal_global_momentum_fraction':peak(pn-p)/P0,
        'raw_impulse_fraction':peak(j1+j2+P0-p)/P0,'support_integrated_force_impulse_fraction':peak(j1-jint)/P0,
        'energy_residual_fraction':peak(E0+we-ie-ke)/E0,
        'IE_analytic_at_actual_gap_fraction':peak(ie-Wd)/r['normal_total_work_J'],
        'IE_force_work_quadrature_fraction':peak(ie-wforce)/r['normal_total_work_J'],
        'IE_time_reference_fraction':peak(ie-analytic['work_J'])/r['normal_total_work_J'],
        'KE_time_reference_fraction':peak(ke-analytic['KE_J'])/E0,
        'final_IE_J':float(ie[-1]),'final_KE_J':float(ke[-1]),'final_velocity_mm_per_ms':float(v[-1]),
        'final_global_momentum_N_ms':float(p[-1]),'final_support_impulse_N_ms':float(j1[-1]),
        'initial_velocity_mm_per_ms':float(v[0]),'initial_IE_J':float(ie[0]),'initial_KE_J':float(ke[0]),'initial_P_N_ms':float(p[0]),
        'max_external_work_J':peak(we),'mass_relative_error':peak(get('MASS')-.2)/.2,
        'added_mass_g':peak(get('ADDED MASS')),'maximum_solver_dt_ms':peak(get('TIME STEP')),
        'maximum_recorded_interval_ms':peak(np.diff(t)),'rows':len(t),'end_record_ms':float(t[-1]),
        'minimum_gap_increment_mm':float(np.min(np.diff(d))),
        'OFF_time_ms':None if j is None else float(t[j]),'OFF_time_error_ms':None if j is None else abs(float(t[j])-r['failure_time_ms']),
        'settled_velocity_error_fraction':None if not np.any(settled) else peak(v[settled]-r['post_failure_velocity_mm_per_ms'])/r['post_failure_velocity_mm_per_ms'],
        'settled_momentum_drift_N_ms':None if not np.any(settled) else float(np.ptp(p[settled])),
        'fixed_Y_displacement_peak_mm':peak(a[:,nodes[1][1]]),'moving_Y_reaction_peak_N_ms':peak(j2),
        'other_axis_momentum_peak_N_ms':max(peak(get('X-MOMENTUM')),peak(get('Z-MOMENTUM')))}
    gen=json.loads((folder/'generation.json').read_text());pre=json.loads((folder/'preflight.json').read_text());ex=json.loads((folder/'execution.json').read_text())
    text=(folder/(gen['name']+'_0001.out')).read_text(errors='replace');cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*(?:\.\s*)*[:=]?\s*(\d+)',text).group(1))
    gates=cfg['gates'];checks={'preflight':pre['pass'],'three_successful_jobs':len(ex)==3 and all(r['returncode']==0 for r in ex),
        'normal_termination':'NORMAL TERMINATION' in text,'TH_every_cycle':len(t)==cycles,
        'maximum_solver_dt':metrics['maximum_solver_dt_ms']<=cap*(1+gates['maximum_solver_dt_relative_tolerance']),
        'recorded_dt':metrics['maximum_recorded_interval_ms']<=cap+gates['csv_time_difference_tolerance_ms'],
        'end_covered_without_extrapolation':0<=c['end_ms']-t[-1]<=2*cap+gates['csv_time_difference_tolerance_ms'],
        'no_added_mass':metrics['added_mass_g']<=gates['added_mass_g'],'mass':metrics['mass_relative_error']<=gates['mass_fraction'],
        'fresh_unloaded_IE':abs(ie[0])<=1e-12,'initial_velocity':abs(v[0]-30)/30<=1e-6,
        'initial_momentum':abs(p[0]-P0)/P0<=1e-6,'initial_energy':abs(ke[0]-E0)/E0<=1e-6,
        'no_external_work':metrics['max_external_work_J']<=gates['no_external_work_J'],
        'fixed_node':metrics['fixed_Y_displacement_peak_mm']<=1e-10,'moving_reaction_zero':metrics['moving_Y_reaction_peak_N_ms']<=1e-10,
        'other_axis_momentum_zero':metrics['other_axis_momentum_peak_N_ms']<=gates['other_axis_momentum_N_ms'],
        'no_imposed_motion':gen['no_imposed_moving_X'] and gen['no_imposed_moving_Y'],
        'monotone_gap':metrics['minimum_gap_increment_mm']>=-gates['normal_y_path_monotone_tolerance_mm'],
        'one_irreversible_deactivation':len(breaks)==1 and bool(np.all(np.diff(off)<=0)) and off[-1]==0,
        'OFF_time':j is not None and metrics['OFF_time_error_ms']<=gates['normal_off_time_steps']*cap+gates['csv_time_difference_tolerance_ms'],
        'force_zero_two_rows_after_OFF':j is not None and peak(a[j+2:,ci[1:3]])<=gates['force_zero_N'],
        'post_failure_ballistic':np.any(settled) and metrics['settled_velocity_error_fraction']<=gates['normal_post_failure_velocity_fraction'],
        'post_failure_momentum_constant':np.any(settled) and metrics['settled_momentum_drift_N_ms']/P0<=1e-6,
        'final_IE':abs(ie[-1]-.03)/.03<=gates['normal_final_IE_fraction'],
        'final_KE':abs(ke[-1]-.015)/E0<=gates['normal_energy_fraction']}
    for key,gate in [('displacement_fraction','normal_displacement_fraction'),('velocity_fraction','normal_velocity_fraction'),
        ('force_fraction','normal_force_fraction'),('global_momentum_fraction','normal_momentum_fraction'),
        ('nodal_global_momentum_fraction','normal_momentum_fraction'),('raw_impulse_fraction','normal_impulse_fraction'),
        ('support_integrated_force_impulse_fraction','normal_impulse_fraction'),('energy_residual_fraction','normal_energy_fraction'),
        ('IE_analytic_at_actual_gap_fraction','normal_work_fraction'),('IE_force_work_quadrature_fraction','normal_work_fraction')]:
        checks[key]=metrics[key]<=gates[gate]
    event=None
    if j is not None:
        event={'OFF_row':j,'rows':[{key:float(value[i]) for key,value in [('time_ms',t),('OFF',off),('FY_N',fy),('gap_mm',d),('IE_J',ie),('KE_J',ke),('U_J',U),('nodal_v_mm_ms',v),('global_P_N_ms',p),('support_J_N_ms',j1)]} for i in range(max(0,j-2),min(len(t),j+3))],
            'transition_partition_not_used_as_physical_dissipation':True}
    result={'case':c,'metrics':metrics,'checks':{k:bool(v) for k,v in checks.items()},'all_checks_pass':all(checks.values()),'event':event,
        'cycles':cycles,'raw_history_sha256':h.sha(next(folder.glob('*.csv'))),'audit_sha256':h.sha(__file__),
        'reference_sha256':h.sha(OUT/'reference_verification.json'),'no_time_shift':True,'no_extrapolation':True,
        'physical_fracture_calibrated':False,'mixed_mode_qualified':False,'aircraft_impact_qualified':False}
    h.dump(dest/'audit.json',result)
    arrays=[t,off,d,analytic['delta_mm'],v,analytic['v_mm_per_ms'],fy,analytic['force_N'],ie,ke,we,analytic['work_J'],Wd,wforce,U,ie-U,p,analytic['P_N_ms'],pn,j1,j2,jint,j1+j2+P0-p]
    with (dest/'normal_reference.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.writer(file);writer.writerow(['time_ms','OFF','gap_mm','analytic_gap_mm','v_mm_ms','analytic_v_mm_ms','FY_N','analytic_FY_N','IE_J','KE_J','WE_J','analytic_time_W_J','actual_gap_W_J','force_gap_quadrature_J','recoverable_U_J','unrecovered_numerical_IE_minus_U_J','global_P_N_ms','analytic_P_N_ms','nodal_P_N_ms','support_J_N_ms','moving_J_N_ms','integrated_force_J_N_ms','raw_impulse_residual_N_ms']);writer.writerows(zip(*arrays))
    return result

def fracture():
    dest=OUT/'fracture_verification_r1';assert not dest.exists(),'Keep audits';dest.mkdir()
    cfg=json.loads(h.FRACCFG.read_text(encoding='utf-8'));results={c['id']:normal_case(cfg,c,dest/c['id']) for c in cfg['cases']}
    a,b=results.values();comparisons=[]
    metrics={}
    for key,scale in [('final_IE_J',.03),('final_KE_J',.045),('final_velocity_mm_per_ms',cfg['reference']['post_failure_velocity_mm_per_ms']),('final_support_impulse_N_ms',3.)]:
        metrics[key]=abs(a['metrics'][key]-b['metrics'][key])/scale
    checks={k:v<=cfg['gates']['normal_final_comparison_fraction'] for k,v in metrics.items()}
    comparisons.append({'cases':list(results),'differences':metrics,'checks':checks})
    summary={'id':'IMPACT-I02I-H-FRACTURE','created_utc':h.NOW(),'cases':results,'comparisons':comparisons,
        'all_checks_pass':all(v['all_checks_pass'] for v in results.values()) and all(checks.values()),
        'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),'case_checks_total':sum(len(v['checks']) for v in results.values()),
        'comparison_checks_passed':sum(checks.values()),'comparison_checks_total':len(checks),
        'config_sha256':h.sha(h.FRACCFG),'audit_sha256':h.sha(__file__),'reference_sha256':h.sha(OUT/'reference_verification.json'),
        'software':{'python':sys.version,'numpy':np.__version__,'solver':'OpenRadioss VERS2026; executable SHA-256 and time saved in each execution.json'},
        'physical_fracture_calibrated':False,'aircraft_impact_qualified':False,'mixed_mode_qualified':False,'old_solvers_rerun':False}
    h.dump(dest/'summary.json',summary)
    print(json.dumps({'fracture_pass':summary['all_checks_pass'],'case_gates':[summary['case_checks_passed'],summary['case_checks_total']],
        'comparison_gates':[summary['comparison_checks_passed'],summary['comparison_checks_total']],
        'failed':{n:[k for k,v in a['checks'].items() if not v] for n,a in results.items()},
        'finals':{n:{k:a['metrics'][k] for k in ['OFF_time_ms','final_IE_J','final_KE_J','final_velocity_mm_per_ms','raw_impulse_fraction','energy_residual_fraction']} for n,a in results.items()}}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['elastic','fracture']);a=p.parse_args();globals()[a.action]()
