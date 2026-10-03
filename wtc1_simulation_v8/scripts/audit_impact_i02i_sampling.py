"""Read saved I02I-C histories. Independent scalar references, no solver launch."""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
import numpy as np
import audit_impact_i02i_fixed_penalty as previous
from run_impact_i02i_sampling import ROOT,CFG,OUT,B,NOW,dump,sha,rel,read_history

def work(headers,data):
    mapping=previous.columns(headers,'SEAM_HISTORY',6); t=data[:,0]; ie=np.zeros(len(t)); normal=np.zeros(len(t)); shear=np.zeros(len(t)); breaks=[]
    for eid,ci in mapping.items():
        f=data[:,ci[1:3]]; u=data[:,ci[3:5]]
        increments=.5*(f[:-1]+f[1:])*np.diff(u,axis=0)*.001
        wx=np.r_[0,np.cumsum(increments[:,0])]; wy=np.r_[0,np.cumsum(increments[:,1])]
        shear+=wx; normal+=wy; ie+=data[:,ci[5]]*.001
        for j in np.flatnonzero(np.diff(data[:,ci[0]])<-.5)+1:
            breaks.append({'element_id':eid,'time_ms':float(t[j]),'previous_time_ms':float(t[j-1]),'normal_gap_before_mm':float(u[j-1,1]),'normal_gap_after_mm':float(u[j,1]),'normal_force_before_N':float(f[j-1,1]),'normal_force_after_N':float(f[j,1]),'IE_jump_J':float((data[j,ci[5]]-data[j-1,ci[5]])*.001),'trapezoid_increment_J':float(np.sum(increments[j-1]))})
    total=normal+shear; scale=max(float(np.max(np.abs(ie))),1e-15)
    return {'rows':len(t),'min_output_dt_ms':float(np.min(np.diff(t))),'max_output_dt_ms':float(np.max(np.diff(t))),'spring_work_error_fraction':float(np.max(np.abs(total-ie))/scale),'final_IE_J':float(ie[-1]),'final_trapezoid_work_J':float(total[-1]),'final_normal_trapezoid_work_J':float(normal[-1]),'final_shear_trapezoid_work_J':float(shear[-1]),'max_absolute_work_discrepancy_J':float(np.max(np.abs(total-ie))),'deactivation_events':sorted(breaks,key=lambda e:e['time_ms'])}

def control_audit(cfg,case,destination):
    folder=OUT/case['id']; m=json.loads((folder/'generation.json').read_text()); headers,data=read_history(folder); ci=previous.columns(headers,'SEAM_HISTORY',6)[1]; nodes=previous.columns(headers,'NODES',6)
    idx={v.strip():i for i,v in enumerate(headers)}; c=lambda key:data[:,idx[key]]
    t=data[:,0]; off=data[:,ci[0]]; active=off>=.5; x=data[:,ci[3]]; y=data[:,ci[4]]; fx=data[:,ci[1]]; fy=data[:,ci[2]]; d0=m['delta0_mm']; df=m['deltaf_mm']; kn=m['kn_N_per_mm']; kt=m['kt_N_per_mm']; peak=m['peak_N']
    maximum=0.; reference=np.zeros(len(t))
    for i,delta in enumerate(y):
        maximum=max(maximum,float(delta)); envelope=kn*maximum if maximum<=d0 else max(0.,peak*(df-maximum)/(df-d0))
        reference[i]=max(0.,envelope+kn*(float(delta)-maximum)) if active[i] else 0.
    reference_x=np.where(active,kt*x,0.)
    w=work(headers,data); ie=c('INTERNAL ENERGY')*.001; ke=c('KINETIC ENERGY')*.001; we=c('EXTERNAL WORK')*.001; energy_scale=max(float(np.max(np.abs(we))),1e-15)
    actuator=np.zeros(len(t)-1)
    for ids in nodes.values():
        for displacement,impulse in [(ids[0],ids[4]),(ids[1],ids[5])]:
            actuator+=np.diff(data[:,impulse])/np.diff(t)*np.diff(data[:,displacement])*.001
    wa=np.r_[0,np.cumsum(actuator)]
    expected=.5*kt*.02**2*.001 if case['kind']=='shear' else .03 if case['kind'] in ['normal','cycle'] else None
    free_plateau=(t>1.05)&(t<2.95)&(y<.9*(.6*df)) if case['kind']=='cycle' else np.zeros(len(t),dtype=bool)
    gap=float(np.max(np.abs(y[active]-(data[active,nodes[2][1]]-data[active,nodes[1][1]]))))
    metrics={'normal_force_error_fraction_of_peak':float(np.max(np.abs(fy-reference))/peak),'shear_force_error_fraction_of_reference_peak':float(np.max(np.abs(fx-reference_x))/max(kt*.02,1.)),'energy_residual_fraction':float(np.max(np.abs(we-ie-ke))/energy_scale),'actuator_work_error_fraction':float(np.max(np.abs(wa-we))/energy_scale),'mass_error_fraction':float(np.max(np.abs(c('MASS')-m['expected_mass_g']))/m['expected_mass_g']),'spring_IE_sum_error_fraction':float(np.max(np.abs(data[:,ci[5]]*.001-c('SPRING ENERGY')*.001))/energy_scale),'active_normal_gap_error_mm':gap,'final_external_work_J':float(we[-1]),'final_IE_J':float(ie[-1]),'final_KE_J':float(ke[-1]),'max_KE_J':float(np.max(ke)),'expected_scalar_work_J':expected,'scalar_work_error_fraction':None if expected is None else abs(w['final_trapezoid_work_J']-expected)/expected,'free_plateau_max_force_N':None if not np.any(free_plateau) else float(np.max(np.abs(fy[free_plateau])))}
    engine=(folder/(m['name']+'_0001.out')).read_text(errors='replace')
    checks={'three_jobs':len(json.loads((folder/'execution.json').read_text()))==3,'preflight':json.loads((folder/'preflight.json').read_text())['pass'],'normal_termination':'NORMAL TERMINATION' in engine,'mass':metrics['mass_error_fraction']<=1e-5,'normal_force_H2':metrics['normal_force_error_fraction_of_peak']<=.005,'shear_force':metrics['shear_force_error_fraction_of_reference_peak']<=.005,'energy_balance':metrics['energy_residual_fraction']<=.005,'boundary_work':metrics['actuator_work_error_fraction']<=.005,'spring_IE_sum':metrics['spring_IE_sum_error_fraction']<=.001,'active_gap':gap<=1e-5,'irreversible_OFF':bool(np.all(np.diff(off)<=1e-7)),'expected_final_status':bool(off[-1]==(1 if case['kind']=='shear' else 0)),'work_quadrature':w['spring_work_error_fraction']<=.005}
    if expected is not None: checks['analytic_scalar_work']=metrics['scalar_work_error_fraction']<=.005
    if case['kind']=='cycle': checks['H2_zero_force_plateau']=metrics['free_plateau_max_force_N'] is not None and metrics['free_plateau_max_force_N']<=.005*peak
    checks={k:bool(v) for k,v in checks.items()}; destination.mkdir()
    result={'case':case,'metrics':metrics,'work_diagnostic':w,'checks':checks,'pass':all(checks.values()),'config_sha256':sha(CFG),'raw_csv_sha256':sha(next(folder.glob('*.csv'))),'reference':'Independent H2 positive-history scalar envelope + linear unloading Ku; no compression exercised. Mixed-mode total work is diagnostic, not a calibrated fracture energy.'}
    dump(destination/'audit.json',result)
    with (destination/'force_work_history.csv').open('w',encoding='utf-8',newline='') as f:
        import csv
        writer=csv.writer(f);writer.writerow(['time_ms','OFF','x_mm','y_mm','fx_N','fy_N','reference_fx_N','reference_fy_N','IE_J','KE_J','external_work_J','actuator_work_J']);writer.writerows(zip(t,off,x,y,fx,fy,reference_x,reference,ie,ke,we,wa))
    return result

def downsample(t,dt):
    return np.unique(np.r_[0,np.searchsorted(t,np.arange(t[0]+dt,t[-1],dt),side='left'),len(t)-1])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--controls-only',action='store_true');args=parser.parse_args()
    destination=Path(args.output).resolve();destination.relative_to(OUT);destination.mkdir(exist_ok=False)
    cfg=json.loads(CFG.read_text()); controls={c['id']:control_audit(cfg,c,destination/c['id']) for c in cfg['controls']}; results={}; comparisons={}; sampling={}
    for case in ([] if args.controls_only else cfg['cases']):
        folder=OUT/case['id']
        # Only the CSV reader is adapted in this process to avoid Python-list duplication.
        # B's immutable equations, flags and gates run unchanged into a new C directory.
        original_reader=previous.read
        try:
            previous.read=read_history
            result,states=previous.audit_case(folder,destination/case['id'],cfg)
        finally: previous.read=original_reader
        cachedfolder=B/'verification_r1'/case['cached_B_case']; old_result=json.loads((cachedfolder/'case_audit.json').read_text()); old_states=json.loads((cachedfolder/'history.json').read_text())
        comparison=previous.compare(case['id']+'_VS_CACHED_B',(old_result,old_states),(result,states),cfg,'time')
        for key,limit in [('force_at_common_displacement',.005),('work_at_common_displacement',.005)]:
            metric='maximum_force_difference_fraction' if key.startswith('force') else 'maximum_work_difference_fraction'
            comparison['checks'][key]=comparison[metric] is not None and comparison[metric]<=limit
        comparison['all_comparison_checks_pass']=all(comparison['checks'].values()); comparisons[case['id']]=comparison
        headers,data=read_history(folder); full=work(headers,data); coarse={}
        for dt in cfg['diagnostics']['output_downsample_dt_ms']:
            selection=downsample(data[:,0],dt);coarse[str(dt)]=work(headers,data[selection])
        full['cached_B_error_fraction']=old_result['metrics']['spring_work_quadrature_error_fraction']; full['downsampled_same_trajectory']=coarse
        full['relative_reduction_against_B']=None if full['cached_B_error_fraction']==0 else 1-full['spring_work_error_fraction']/full['cached_B_error_fraction']
        full['dense_work_gate_pass']=full['spring_work_error_fraction']<=.005
        full['raw_max_timestamp_increment_over_max_solver_dt']=full['max_output_dt_ms']/max(float(np.max(data[:,headers.index('TIME STEP')])),1e-15)
        text=(folder/(json.loads((folder/'generation.json').read_text())['name']+'_0001.out')).read_text(errors='replace')
        match=re.search(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',text); assert match
        full['reported_solver_cycles']=int(match.group(1))
        full['dense_output_covers_each_solver_step']=len(data)==int(match.group(1))
        full['timing_note']='CSV timestamps rounded to seven significant digits. A maximum timestamp difference ratio alone is not a cycle-coverage test. Compare engine cycle count with history row count.'
        times=np.array([s['time_ms'] for s in states]); old_times=np.array([s['time_ms'] for s in old_states]); ids=np.searchsorted(times,old_times)
        valid=ids<len(times); valid[valid]&=np.abs(times[ids[valid]]-old_times[valid])<1e-10
        matched=[(old_states[i],states[int(ids[i])]) for i in np.flatnonzero(valid)]
        full['cached_B_exact_timestamp_matches']={'matched_rows':len(matched),'requested_rows':len(old_states),'all_rows_matched':len(matched)==len(old_states),'max_section_force_difference_N':max(abs(a['section_force_N']-b['section_force_N']) for a,b in matched),'max_external_work_difference_J':max(abs(a['external_work_J']-b['external_work_J']) for a,b in matched),'max_area_advance_difference_mm':max(abs(a['area_advance_mm']-b['area_advance_mm']) for a,b in matched),'max_CTOA_B_difference_deg':max(abs(a['CTOA_B_deg']-b['CTOA_B_deg']) for a,b in matched)}
        dump(destination/case['id']/'sampling_audit.json',full);sampling[case['id']]=full;results[case['id']]=result
        print(json.dumps({'audited':case['id'],'rows':full['rows'],'work_error_fraction':full['spring_work_error_fraction']}),flush=True)
    summary={'created_utc':NOW(),'iteration':'IMPACT-I02I-C','controls':controls,'all_controls_pass':all(v['pass'] for v in controls.values()),'control_checks_passed':sum(sum(v['checks'].values()) for v in controls.values()),'control_checks_total':sum(len(v['checks']) for v in controls.values()),'cases':results,'sampling':sampling,'comparisons':comparisons,'case_checks_passed':sum(sum(v['gates'].values()) for v in results.values()),'case_checks_total':sum(len(v['gates']) for v in results.values()),'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparisons.values()),'comparison_checks_total':sum(len(v['checks']) for v in comparisons.values()),'all_dense_work_gates_pass':all(v['dense_work_gate_pass'] for v in sampling.values()) if sampling else None,'source_convention_verified':False,'physical_propagation_qualified':False,'runtime_seconds':sum(r['seconds'] for f in OUT.glob('*/execution.json') for r in json.loads(f.read_text())),'software':{'python':__import__('sys').version,'numpy':np.__version__,'solver':'OpenRadioss 20260728 win64, engine /VERS2026, one thread'},'config_sha256':sha(CFG),'audit_script_sha256':sha(__file__),'dependency_audit_sha256':sha(previous.__file__),'no_old_calculation_rerun':True}
    dump(destination/'summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['all_controls_pass','control_checks_passed','control_checks_total','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds']}),flush=True)

if __name__=='__main__':main()
