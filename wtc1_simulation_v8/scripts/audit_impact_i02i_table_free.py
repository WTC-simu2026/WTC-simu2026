"""G raw histories against declared table and free-oscillator references."""
from __future__ import annotations
import csv,json,sys
from pathlib import Path
import numpy as np
import run_impact_i02i_table_free as g
import audit_impact_i02i_dtcap as fa
import audit_impact_i02i_fixed_penalty as columns
ROOT,OUT,CFG=g.ROOT,g.OUT,g.CFG
DEST=OUT/'verification_r1'

def free_case(cfg,c):
    folder=OUT/c['id'];dest=DEST/c['id'];dest.mkdir()
    h,a=g.f.inherited.cached.read_history(folder);ix={s.strip():i for i,s in enumerate(h)}
    get=lambda name:a[:,ix[name]];t=a[:,0];ci=columns.columns(h,'SEAM_HISTORY',6)[1];nodes=columns.columns(h,'NODES',6)
    r=cfg['free_reference'];m,k,w=r['moving_mass_g'],r['k_N_per_mm'],r['omega_rad_per_ms']
    amp,E0,P0=r['amplitude_mm'],r['initial_energy_J'],r['initial_momentum_N_ms'];cap=c['maximum_dt_ms']
    u=a[:,nodes[2][0]]-a[:,nodes[1][0]];v=a[:,nodes[2][2]];force=a[:,ci[1]];off=a[:,ci[0]]
    ua=amp*np.sin(w*t);va=np.cos(w*t);pa=m*va;fa_ref=k*ua
    j1=a[:,nodes[1][4]];j2=a[:,nodes[2][4]];p=get('X-MOMENTUM');pn=m*(a[:,nodes[1][2]]+v)
    ie=get('INTERNAL ENERGY')*.001;ke=get('KINETIC ENERGY')*.001;we=get('EXTERNAL WORK')*.001
    U=.5*k*u*u*.001;Ua=.5*k*ua*ua*.001;Ka=.5*m*va*va*.001
    jint=np.r_[0,np.cumsum(-.5*(force[1:]+force[:-1])*np.diff(t))]
    peak=lambda x:float(np.max(np.abs(x)))
    metrics={'displacement_fraction':peak(u-ua)/amp,'nodal_velocity_fraction':peak(v-va),
        'force_fraction':peak(force-fa_ref)/r['force_amplitude_N'],
        'global_momentum_fraction':peak(p-pa)/P0,'nodal_global_momentum_fraction':peak(pn-p)/P0,
        'raw_initial_momentum_impulse_fraction':peak(j1+j2+P0-p)/P0,
        'support_integrated_force_impulse_fraction':peak(j1-jint)/P0,
        'moving_X_reaction_peak_N_ms':peak(j2),'energy_residual_fraction':peak(E0+we-ie-ke)/E0,
        'recoverable_energy_fraction':peak(ie-U)/E0,'analytic_IE_fraction':peak(ie-Ua)/E0,
        'analytic_KE_fraction':peak(ke-Ka)/E0,'maximum_external_work_J':peak(we),
        'fixed_displacement_peak_mm':peak(a[:,nodes[1][0]]),'initial_velocity_mm_per_ms':float(v[0]),
        'maximum_added_mass_g':peak(get('ADDED MASS')),'mass_relative_error':peak(get('MASS')-.2)/.2,
        'maximum_solver_dt_ms':peak(get('TIME STEP')),'maximum_recorded_interval_ms':peak(np.diff(t)),
        'rows':len(t),'end_record_ms':float(t[-1]),'declared_end_ms':c['end_ms'],
        'initial_IE_J':float(ie[0]),'initial_KE_J':float(ke[0]),'initial_global_P_N_ms':float(p[0])}
    # Period from positive-going zero crossings, no phase fitting or extrapolation.
    crossings=[]
    for i in np.flatnonzero((u[:-1]<0)&(u[1:]>=0)):
        crossings.append(float(t[i]-u[i]*(t[i+1]-t[i])/(u[i+1]-u[i])))
    periods=np.diff(crossings)
    metrics.update(positive_zero_crossings_ms=crossings,measured_periods_ms=periods.tolist(),
        period_fraction=None if len(periods)==0 else peak(periods/r['period_ms']-1))
    ex=json.loads((folder/'execution.json').read_text());pre=json.loads((folder/'preflight.json').read_text());gen=json.loads((folder/'generation.json').read_text())
    text=(folder/(gen['name']+'_0001.out')).read_text(errors='replace')
    import re
    cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*(?:\.\s*)*[:=]?\s*(\d+)',text).group(1))
    gates=cfg['gates'];checks={
        'preflight':pre['pass'],'normal_termination':all(x['returncode']==0 for x in ex) and 'NORMAL TERMINATION' in text,
        'TH_every_cycle':len(t)==cycles,'maximum_saved_solver_dt':metrics['maximum_solver_dt_ms']<=cap*(1+gates['maximum_solver_dt_relative_tolerance']),
        'maximum_recorded_dt_with_CSV_roundoff':metrics['maximum_recorded_interval_ms']<=cap+gates['csv_time_difference_tolerance_ms'],
        'end_covered_without_extrapolation':c['end_ms']-t[-1]<=2*cap+gates['csv_time_difference_tolerance_ms'],
        'mass':metrics['mass_relative_error']<=gates['mass_fraction'],'no_added_mass':metrics['maximum_added_mass_g']<=gates['added_mass_g'],
        'no_deactivation':bool(np.all(off==1)),'no_imposed_moving_X':gen['no_imposed_moving_X'],
        'fixed_node':metrics['fixed_displacement_peak_mm']<=gates['free_fixed_displacement_mm'],
        'initial_velocity':abs(v[0]-1)<=gates['free_initial_velocity_fraction'],
        'initial_momentum':abs(p[0]-P0)/P0<=gates['free_initial_velocity_fraction'],
        'initial_energy':abs(ke[0]-E0)/E0<=gates['free_initial_velocity_fraction'],
        'moving_X_reaction_zero':peak(j2)<=1e-10,
        'energy':metrics['energy_residual_fraction']<=gates['free_energy_fraction'],
        'recoverable_energy':metrics['recoverable_energy_fraction']<=gates['free_recoverable_energy_fraction'],
        'period':len(periods)>=6 and metrics['period_fraction']<=gates['free_period_fraction']}
    for metric,gate in [('displacement_fraction','free_displacement_fraction'),('nodal_velocity_fraction','free_nodal_velocity_fraction'),
            ('force_fraction','free_force_fraction'),('global_momentum_fraction','free_global_momentum_fraction'),
            ('nodal_global_momentum_fraction','free_nodal_global_momentum_fraction'),('raw_initial_momentum_impulse_fraction','free_impulse_fraction'),
            ('support_integrated_force_impulse_fraction','free_impulse_fraction')]:checks[metric]=metrics[metric]<=gates[gate]
    strict={name:metrics[name]<=.01 for name in ['nodal_velocity_fraction','force_fraction','nodal_global_momentum_fraction','raw_initial_momentum_impulse_fraction','support_integrated_force_impulse_fraction']}
    result={'case':c,'metrics':metrics,'checks':{k:bool(v) for k,v in checks.items()},'all_checks_pass':all(checks.values()),
        'strict_raw_1pct_diagnostics':strict,'analytic_reference':r,'cycles':cycles,
        'raw_history_sha256':g.sha(next(folder.glob('*.csv'))),'audit_script_sha256':g.sha(__file__),
        'no_time_shift':True,'no_extrapolation':True,'free_fracture_qualified':False,
        'REACX_units_test':'Saved support REACX compared to integral(-FX dt) and P-P0 in N ms; software documentation labels force, discrepancy not erased'}
    g.dump(dest/'audit.json',result)
    arrays=[t,u,ua,v,va,force,fa_ref,p,pa,pn,j1,j2,jint,j1+j2+P0-p,ie,ke,we,U,Ua,Ka]
    with (dest/'analytic_comparison.csv').open('w',encoding='utf-8',newline='') as file:
        writer=csv.writer(file);writer.writerow(['time_ms','u_mm','analytic_u_mm','v_mm_ms','analytic_v_mm_ms','FX_N','analytic_FX_N','global_P_N_ms','analytic_P_N_ms','nodal_P_N_ms','support_J_N_ms','moving_J_N_ms','integral_support_force_N_ms','raw_J_plus_P0_minus_P_N_ms','IE_J','KE_J','WE_J','elastic_U_J','analytic_U_J','analytic_K_J']);writer.writerows(zip(*arrays))
    return result

def audit():
    assert not DEST.exists(),'Preserve audit revisions';DEST.mkdir()
    cfg=json.loads(CFG.read_text(encoding='utf-8'));results={}
    baseline=json.loads((g.f.OUT/'verification_r1/summary.json').read_text(encoding='utf-8'))
    assert g.sha(g.f.OUT/'verification_r1/summary.json')==cfg['saved_F_baseline']['sha256']
    comparisons=[]
    for c in cfg['cases']:
        if c['stage']=='table':
            prev=fa.OUT,fa.DEST,fa.CFG
            try:fa.OUT,fa.DEST,fa.CFG=OUT,DEST,CFG;value,_=fa.audit_case(cfg,c)
            finally:fa.OUT,fa.DEST,fa.CFG=prev
            value['G_audit_script_sha256']=g.sha(__file__);value['table_points']=json.loads((OUT/c['id']/'generation.json').read_text())['serialized_function_points']
            results[c['id']]=value;old=baseline['cases']['AFTER_CAP100NS' if c['maximum_dt_ms']==.0001 else 'AFTER_CAP050NS']
            new=value['momentum']['X']['raw_boundary_residual_fraction'];ref=old['momentum']['X']['raw_boundary_residual_fraction']
            ratio=new/ref;expect=800/c['subdivisions'];err=abs(ratio/expect-1)
            energy=abs(value['metrics']['final_IE_J']-old['metrics']['final_IE_J'])/.03
            comparisons.append({'case':c['id'],'cached_F_case':old['case']['id'],'subdivisions':c['subdivisions'],
                'F_raw_residual_fraction':ref,'G_raw_residual_fraction':new,'ratio_G_to_F':ratio,'expected_ratio':expect,
                'ratio_relative_error':err,'final_IE_difference_fraction':energy,
                'checks':{'linear_table_scaling':err<=cfg['gates']['table_residual_ratio_relative_tolerance'],
                    'normal_work_preserved':energy<=cfg['gates']['table_energy_difference_fraction']},'no_rerun':True,'no_time_shift':True})
            g.dump(DEST/c['id']/'audit.json',value)
        else:results[c['id']]=free_case(cfg,c)
    summary={'iteration':cfg['id'],'created_utc':g.NOW(),'cases':results,'comparisons':comparisons,
        'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),'case_checks_total':sum(len(v['checks']) for v in results.values()),
        'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparisons),'comparison_checks_total':sum(len(v['checks']) for v in comparisons),
        'all_scientific_checks_pass':all(v['all_checks_pass'] for v in results.values()) and all(all(v['checks'].values()) for v in comparisons),
        'runtime_seconds':json.loads((OUT/'execution_complete.json').read_text())['runtime_seconds'],
        'physical_propagation_qualified':False,'free_fracture_qualified':False,'post_deactivation_free_inertia_qualified':False,
        'E_sensitivities_resolved':False,'source_convention_verified':False,'mixed_mode_dissipation_calibrated':False,
        'old_solvers_rerun':False,'config_sha256':g.sha(CFG),'audit_script_sha256':g.sha(__file__),
        'software':{'python':sys.version,'numpy':np.__version__,'solver':'OpenRadioss VERS2026, executable hashes in saved execution.json'},
        'cached_E_review_path':g.rel(g.f.OUT/'cached_E_sensitivity_review.json'),'cached_E_review_sha256':g.sha(g.f.OUT/'cached_E_sensitivity_review.json'),
        'F_same_row_OFF_FX_failures_still_open':baseline['strict_same_row_OFF_FX_failed_cases']}
    g.dump(DEST/'summary.json',summary)
    print(json.dumps({'case_gates':[summary['case_checks_passed'],summary['case_checks_total']],
        'comparison_gates':[summary['comparison_checks_passed'],summary['comparison_checks_total']],
        'failed':{n:[k for k,v in r['checks'].items() if not v] for n,r in results.items()},
        'table_residuals':[(r['case'],r['G_raw_residual_fraction'],r['ratio_relative_error']) for r in comparisons]},ensure_ascii=False),flush=True)

if __name__=='__main__':audit()
