"""I saved histories: raw fields, initial momentum, history and energy.

No time shift, fit, extrapolation, or solver call. Failures retained.
"""
from __future__ import annotations
import csv,json,re
import numpy as np
import run_impact_i02i_free_return as i
import reference_impact_i02i_free_return as ref
import audit_impact_i02i_fixed_penalty as cols
h=i.h;ROOT,OUT,CFG=i.ROOT,i.OUT,i.CFG

def case(cfg,c,dest):
    dest.mkdir();folder=OUT/c['id'];headers,a=h.g.f.inherited.cached.read_history(folder)
    ix={s.strip():j for j,s in enumerate(headers)};get=lambda n:a[:,ix[n]];t=a[:,0]
    ci=cols.columns(headers,'SEAM_HISTORY',6)[1];nodes=cols.columns(headers,'NODES',6)
    p=cfg['references'][c['family']];m=p['moving_mass_g'];e0=p['initial_energy_J'];p0=p['initial_momentum_N_ms'];cap=c['maximum_dt_ms']
    d=a[:,nodes[2][1]]-a[:,nodes[1][1]];dm=np.maximum.accumulate(d);v=a[:,nodes[2][3]];fy=a[:,ci[2]];off=a[:,ci[0]]
    j1=a[:,nodes[1][5]];j2=a[:,nodes[2][5]];pg=get('Y-MOMENTUM');pn=m*(v+a[:,nodes[1][3]])
    ie=get('INTERNAL ENERGY')*.001;ke=get('KINETIC ENERGY')*.001;we=get('EXTERNAL WORK')*.001
    exact=ref.state(t,p);hist=ref.history_state(d,dm,p);u=fy*fy/(2*p['k_N_per_mm'])*.001;retained=ie-u
    integral=np.r_[0,np.cumsum(-.5*(fy[1:]+fy[:-1])*np.diff(t))]
    work=np.r_[0,np.cumsum(.5*(fy[1:]+fy[:-1])*np.diff(d)*.001)]
    peak=lambda x:float(np.max(np.abs(x)))
    frac={'gap':peak(d-exact['delta_mm'])/p['turning_gap_mm'],
        'velocity':peak(v-exact['v_mm_per_ms'])/p['v0_mm_per_ms'],
        'force':peak(fy-exact['force_N'])/p['force_amplitude_N'],
        'P':peak(pg-exact['P_N_ms'])/p0,'nodal_P':peak(pn-pg)/p0,
        'initial_P_impulse':peak(j1+j2+p0-pg)/p0,'force_integral_impulse':peak(j1-integral)/p0,
        'history_force':peak(fy-hist['force_N'])/p['force_amplitude_N'],
        'energy_balance':peak(e0+we-ie-ke)/e0,'history_IE':peak(ie-hist['IE_J'])/e0,
        'force_work':peak(ie-work)/e0,'time_IE':peak(ie-exact['IE_J'])/e0,'time_KE':peak(ke-exact['KE_J'])/e0,
        'recoverable':peak(u-exact['recoverable_J'])/e0,'retained':peak(retained-exact['retained_J'])/e0}
    crossings=np.flatnonzero((v[:-1]>=0)&(v[1:]<0));tc=None
    if len(crossings)==1:
        j=int(crossings[0]);tc=float(t[j]+(t[j+1]-t[j])*v[j]/(v[j]-v[j+1]))
    gen=json.loads((folder/'generation.json').read_text());pre=json.loads((folder/'preflight.json').read_text());jobs=json.loads((folder/'execution.json').read_text())
    text=(folder/(gen['name']+'_0001.out')).read_text(errors='replace')
    cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*(?:\.\s*)*[:=]?\s*(\d+)',text).group(1))
    metrics={'fractions':frac,'rows':len(t),'cycles':cycles,'end_record_ms':float(t[-1]),'turn_time_ms':tc,
        'turn_time_error_ms':None if tc is None else abs(tc-p['turn_time_ms']),
        'maximum_gap_mm':float(d.max()),'final_gap_mm':float(d[-1]),'minimum_gap_after_initial_mm':float(d[1:].min()),
        'final_IE_J':float(ie[-1]),'final_KE_J':float(ke[-1]),'final_recoverable_J':float(u[-1]),
        'final_retained_J':float(retained[-1]),'minimum_retained_J':float(retained.min()),
        'final_v_mm_per_ms':float(v[-1]),'final_P_N_ms':float(pg[-1]),'final_J_support_N_ms':float(j1[-1]),
        'initial_P_N_ms':float(pg[0]),'initial_KE_J':float(ke[0]),'initial_IE_J':float(ie[0]),
        'max_WE_J':peak(we),'maximum_solver_dt_ms':peak(get('TIME STEP')),
        'maximum_record_interval_ms':peak(np.diff(t)),'mass_fraction':peak(get('MASS')-.2)/.2,
        'added_mass_g':peak(get('ADDED MASS')),'fixed_gap_mm':peak(a[:,nodes[1][1]]),
        'moving_reaction_N_ms':peak(j2),'other_axis_P_N_ms':max(peak(get('X-MOMENTUM')),peak(get('Z-MOMENTUM'))),
        'OFF_min':float(off.min()),'OFF_max':float(off.max()),'seconds':sum(r['seconds'] for r in jobs)}
    gates=cfg['gates'];checks={}
    for key in ['gap','velocity','force','P','nodal_P','initial_P_impulse','force_integral_impulse','history_force']:
        checks[key]=frac[key]<=gates['raw_amplitude_fraction']
    for key in ['energy_balance','history_IE','force_work','time_IE','time_KE','recoverable','retained']:
        checks[key]=frac[key]<=gates['work_fraction'] if key=='force_work' else frac[key]<=gates['energy_fraction']
    checks.update(preflight=pre['pass'],three_jobs=len(jobs)==3 and all(r['returncode']==0 for r in jobs),
        normal_termination='NORMAL TERMINATION' in text,one_TH_per_cycle=len(t)==cycles,
        cap=metrics['maximum_solver_dt_ms']<=cap*(1+gates['maximum_solver_dt_relative_tolerance']),
        record_cap=metrics['maximum_record_interval_ms']<=cap+gates['csv_time_difference_tolerance_ms'],
        end_coverage=0<=c['end_ms']-t[-1]<=gates['end_coverage_steps']*cap+gates['csv_time_difference_tolerance_ms'],
        no_OFF=np.all(off==1),positive_gap=np.all(d[1:]>0) and d[0]==0,
        before_failure=d.max()<p['deltaf_mm'],one_turn=len(crossings)==1,
        turn_time=tc is not None and abs(tc-p['turn_time_ms'])<=gates['turn_time_steps']*cap+gates['csv_time_difference_tolerance_ms'],
        peak_gap=abs(d.max()-p['turning_gap_mm'])/p['turning_gap_mm']<=gates['raw_amplitude_fraction'],
        no_external_work=peak(we)<=gates['no_external_work_J'],mass=metrics['mass_fraction']<=gates['mass_fraction'],
        no_added_mass=metrics['added_mass_g']<=gates['added_mass_g'],fixed_support=metrics['fixed_gap_mm']<=gates['fixed_gap_mm'],
        no_moving_reaction=peak(j2)<=gates['other_axis_momentum_N_ms'],no_other_axis_P=metrics['other_axis_P_N_ms']<=gates['other_axis_momentum_N_ms'],
        initial_IE=abs(ie[0])<=gates['no_external_work_J'],initial_KE=abs(ke[0]-e0)/e0<=gates['initial_fraction'],
        initial_P=abs(pg[0]-p0)/p0<=gates['initial_fraction'],initial_v=abs(v[0]-p['v0_mm_per_ms'])/p['v0_mm_per_ms']<=gates['initial_fraction'],
        retained_nonnegative=retained.min()>=-gates['retained_negative_tolerance_J'],fresh=gen['fresh_state'] and gen['no_restart'],
        unchanged_history=gen['history_properties_unchanged'],case_budget=metrics['seconds']<=cfg['execution']['maximum_case_wall_seconds'])
    if c['family']=='NORMAL_ARREST_RETURN':
        settled=t>=p['zero_force_time_ms']+2*cap
        metrics.update(settled_force_N=peak(fy[settled]),settled_P_range_N_ms=float(np.ptp(pg[settled])),
            settled_v_error_fraction=peak(v[settled]-p['release_velocity_mm_per_ms'])/p['v0_mm_per_ms'])
        checks.update(force_zero_after_unload=np.any(settled) and metrics['settled_force_N']<=gates['force_zero_N'],
            free_return_velocity=metrics['settled_v_error_fraction']<=gates['raw_amplitude_fraction'],
            retained_after_unload=peak(ie[settled]-p['retained_work_J'])/e0<=gates['energy_fraction'])
    checks={key:bool(value) for key,value in checks.items()}
    data=np.column_stack([t,d,dm,v,fy,off,pg,j1,j2,ie,ke,we,u,retained,integral,work,
        exact['delta_mm'],exact['v_mm_per_ms'],exact['force_N'],exact['IE_J'],exact['KE_J'],hist['IE_J']])
    with (dest/'comparison.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['t_ms','gap_mm','history_gap_mm','v_mm_ms','Fy_N','OFF','P_N_ms',
            'J1_N_ms','J2_N_ms','IE_J','KE_J','WE_J','U_J','retained_J','force_impulse_N_ms','force_work_J',
            'exact_gap_mm','exact_v_mm_ms','exact_F_N','exact_IE_J','exact_KE_J','history_IE_J']);writer.writerows(data)
    result={'case':c,'metrics':metrics,'checks':checks,'all_checks_pass':all(checks.values()),
        'history_csv_sha256':h.sha(next(folder.glob('*.csv'))),'audit_sha256':h.sha(__file__),
        'no_time_shift':True,'no_extrapolation':True,'physical_calibration':False}
    h.dump(dest/'audit.json',result)
    return result,(t,{'gap':d,'v':v,'P':pg,'IE':ie,'KE':ke,'J_support':j1,'force':fy})

def audit():
    dest=OUT/'verification_r1';assert not dest.exists(),'Keep audits';dest.mkdir()
    cfg=json.loads(CFG.read_text());assert h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256']
    results={};series={};comp=[]
    for c in cfg['cases']:
        results[c['id']],series[c['id']]=case(cfg,c,dest/c['id'])
    for family,query in cfg['comparison_times_ms'].items():
        members=[c for c in cfg['cases'] if c['family']==family];c1,c2=members;p=cfg['references'][family]
        t1,a=series[c1['id']];t2,b=series[c2['id']];coverage=all(min(t1[-1],t2[-1])>=q>=max(t1[0],t2[0]) for q in query)
        scales={'gap':p['turning_gap_mm'],'v':p['v0_mm_per_ms'],'P':p['initial_momentum_N_ms'],
            'IE':p['initial_energy_J'],'KE':p['initial_energy_J'],'J_support':p['initial_momentum_N_ms'],'force':p['force_amplitude_N']}
        metrics={key:float(np.max(abs(np.interp(query,t1,a[key])-np.interp(query,t2,b[key]))))/scale for key,scale in scales.items()}
        checks={key:value<=cfg['gates']['comparison_fraction'] for key,value in metrics.items()};checks['coverage']=bool(coverage)
        comp.append({'family':family,'cases':[c1['id'],c2['id']],'times_ms':query,'fractions':metrics,'checks':checks})
    r=json.loads((OUT/'reference_verification.json').read_text());ex=json.loads((OUT/'execution_complete.json').read_text())
    summary={'iteration':'IMPACT-I02I-I','created_utc':h.NOW(),'cases':results,'comparisons':comp,
        'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),'case_checks_total':sum(len(v['checks']) for v in results.values()),
        'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comp),'comparison_checks_total':sum(len(v['checks']) for v in comp),
        'reference_checks_passed':sum(r['checks'].values()),'reference_checks_total':len(r['checks']),
        'all_declared_checks_pass':all(v['all_checks_pass'] for v in results.values()) and all(all(v['checks'].values()) for v in comp) and r['pass'],
        'runtime_seconds':ex['runtime_seconds'],'config_sha256':h.sha(CFG),'audit_sha256':h.sha(__file__),
        'numerical_normal_unload_verified':all(v['all_checks_pass'] for v in results.values()),
        'physical_fracture_calibrated':False,'physical_propagation_qualified':False,'mixed_mode_qualified':False,
        'aircraft_impact_qualified':False,'source_convention_verified':False,'E_sensitivities_resolved':False,
        'old_solvers_rerun':False,'cached_F_same_row_OFF_FX_failures_preserved':5,'cached_G_strict_failures_preserved':8}
    h.dump(dest/'summary.json',summary)
    print(json.dumps({'pass':summary['all_declared_checks_pass'],'case_checks':[summary['case_checks_passed'],summary['case_checks_total']],
        'comparisons':[summary['comparison_checks_passed'],summary['comparison_checks_total']],
        'failures':{n:[k for k,v in r['checks'].items() if not v] for n,r in results.items()},
        'fractions':{n:r['metrics']['fractions'] for n,r in results.items()}}),flush=True)

if __name__=='__main__':audit()
