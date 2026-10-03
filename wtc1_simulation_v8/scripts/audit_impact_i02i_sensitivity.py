"""Saved dense-history I02I-E audits. Old B/C solvers are never launched.

The inherited equations audit each new effective configuration. Comparison
events require the exact requested advance on both sides, with no invented
topology. Missing displacement/advance coverage remains a failed coverage gate.
"""
from __future__ import annotations
import argparse, gc, json, re, sys
from pathlib import Path
import numpy as np
import audit_impact_i02i_fixed_penalty as previous
import audit_impact_i02i_sampling as spring_work
from run_impact_i02i_sensitivity import ROOT,CFG,OUT,C,NOW,sha,dump,rel
from run_impact_i02i_sampling import read_history

VERIFY=OUT/'verification_r1'

def audit_case(case):
    destination=VERIFY/case['id']
    if destination.exists():
        assert (destination/'sensitivity_audit.json').exists(),'Incomplete saved audit retained; use a new revision rather than overwrite'
        print(json.dumps({'cached_audit':case['id'],'no_solver':True}),flush=True);return
    folder=OUT/case['id'];cfg=json.loads((folder/'effective_configuration.json').read_text(encoding='utf-8'));meta=json.loads((folder/'generation.json').read_text(encoding='utf-8'))
    saved_reader=previous.read
    try:
        previous.read=read_history
        result,states=previous.audit_case(folder,destination,cfg)
    finally:previous.read=saved_reader
    headers,data=read_history(folder);work=spring_work.work(headers,data)
    text=(folder/(meta['name']+'_0001.out')).read_text(errors='replace');match=re.search(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',text);assert match
    cycles=int(match.group(1));min_dt=float(np.min(data[:,headers.index('TIME STEP')]))
    base_folder=C/'verification_r2'/case['cached_C_case'];base_result=json.loads((base_folder/'case_audit.json').read_text(encoding='utf-8'));base_states=json.loads((base_folder/'history.json').read_text(encoding='utf-8'))
    comparison=previous.compare(case['id']+'_VS_C',(base_result,base_states),(result,states),cfg,'time')
    comparison['checks']['all_requested_common_displacements_assessed']=all(p['assessed'] for p in comparison['common_displacements'])
    comparison['all_comparison_checks_pass']=all(comparison['checks'].values())
    comparison['baseline_case']=case['cached_C_case'];comparison['factor']=case['factor'];comparison['declared_force_work_ctoa_limits']={'force':.05,'work':.05,'ctoa':.1}
    guards=result['sensor_final_status'];first=lambda r:r['events'][0] if r['events'] else None
    onset_a=first(base_result);onset_b=first(result)
    onset={'baseline':onset_a,'variant':onset_b,'relative_onset_displacement_difference':None if onset_a is None or onset_b is None else (onset_b['displacement_mm']-onset_a['displacement_mm'])/onset_a['displacement_mm'],'relative_onset_section_force_difference':None if onset_a is None or onset_b is None else (onset_b['section_force_N']-onset_a['section_force_N'])/onset_a['section_force_N'],'interpretation':'first recorded contiguous complete separation; diagnostic only, independent of requested later advances'}
    result['gates'].update(dense_history_every_cycle=len(data)==cycles,requested_history_interval_below_minimum_solver_dt=meta['history_interval_ms']<=min_dt,declared_dense_spring_work=work['spring_work_error_fraction']<=.005,zero_added_mass=result['additional_energy_diagnostics']['max_added_mass_g']==0.,generation_invariants=all(meta['generation_checks'].values()))
    result['all_case_gates_pass']=all(result['gates'].values())
    info={'created_utc':NOW(),'case':case,'case_audit':result,'comparison':comparison,'onset_diagnostic':onset,'spring_work':work,'sampling':{'rows':len(data),'engine_cycles':cycles,'requested_interval_ms':meta['history_interval_ms'],'minimum_solver_dt_ms':min_dt,'last_saved_time_ms':float(data[-1,0]),'requested_run_end_ms':meta['run_end_ms'],'maximum_saved_timestamp_increment_ms':float(np.max(np.diff(data[:,0]))),'note':'CSV times rounded. Row/cycle equality verifies coverage; last saved row is not extrapolated to requested end.'},'config_sha256':sha(CFG),'effective_configuration_sha256':sha(folder/'effective_configuration.json'),'audit_script_sha256':sha(__file__),'predecessor_audit_sha256':sha(previous.__file__),'C_baseline_case_audit_sha256':sha(base_folder/'case_audit.json'),'C_baseline_history_sha256':sha(base_folder/'history.json'),'mixed_mode_dissipation_calibrated':False,'physical_propagation_qualified':False,'historical_penetration_conclusion_authorized':False}
    dump(destination/'sensitivity_audit.json',info)
    print(json.dumps({'audited':case['id'],'gates_passed':sum(result['gates'].values()),'gates_total':len(result['gates']),'inertia_fraction':result['metrics']['maximum_kinetic_to_internal_significant_window'],'max_force_difference_fraction':comparison['maximum_force_difference_fraction'],'common_advances':comparison['coverage']['advance_points_assessed'],'sampling_rows_cycles':[len(data),cycles]}),flush=True)
    del data,states,base_states;gc.collect()

def summarize():
    target=VERIFY/'summary.json';assert not target.exists(),'Never overwrite an audit revision'
    cfg=json.loads(CFG.read_text(encoding='utf-8'));results={}
    for case in cfg['cases']:
        p=VERIFY/case['id']/'sensitivity_audit.json'
        if p.exists():results[case['id']]=json.loads(p.read_text(encoding='utf-8'))
    assert results,'No completed, audited case'
    missing=[c['id'] for c in cfg['cases'] if c['id'] not in results]
    comparisons={name:v['comparison'] for name,v in results.items()}
    summary={'created_utc':NOW(),'iteration':'IMPACT-I02I-E','completed_audited_cases':len(results),'planned_cases':len(cfg['cases']),'missing_cases':missing,'cases':results,'case_checks_passed':sum(sum(v['case_audit']['gates'].values()) for v in results.values()),'case_checks_total':sum(len(v['case_audit']['gates']) for v in results.values()),'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparisons.values()),'comparison_checks_total':sum(len(v['checks']) for v in comparisons.values()),'all_case_gates_pass':all(v['case_audit']['all_case_gates_pass'] for v in results.values()),'all_comparison_gates_pass':all(v['all_comparison_checks_pass'] for v in comparisons.values()),'runtime_seconds':sum(r['seconds'] for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text(encoding='utf-8'))),'config_sha256':sha(CFG),'plan_sha256':sha(ROOT/cfg['plan_path']),'audit_script_sha256':sha(__file__),'software':{'python':sys.version,'numpy':np.__version__,'solver':'OpenRadioss 20260728 win64, one thread, engine VERS2026'},'source_convention_verified':False,'physical_propagation_qualified':False,'mixed_mode_dissipation_calibrated':False,'post_deactivation_inertia_qualified':False,'no_old_solver_rerun':True,'temperature_prescribed_is_not_fire':True,'blender_executed':False}
    dump(target,summary)
    print(json.dumps({k:summary[k] for k in ['completed_audited_cases','missing_cases','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds']}),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--case');p.add_argument('--campaign',action='store_true');p.add_argument('--summary',action='store_true');a=p.parse_args()
    VERIFY.mkdir(exist_ok=True)
    if a.summary:summarize();return
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    for case in cfg['cases']:
        if a.campaign or a.case==case['id']:audit_case(case)
    if a.campaign:summarize()

if __name__=='__main__':main()
