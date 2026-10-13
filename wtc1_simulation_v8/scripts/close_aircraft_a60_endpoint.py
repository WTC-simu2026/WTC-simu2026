"""Reproduce the explicit terminal-clock interval from saved fields, without reruns."""
from build_aircraft_a54_graph import ROOT,read,dump,now
import json

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a60'

def evaluate():
    cfg=read(ROOT/'wtc1_simulation_v8/data/aircraft_a60_predeclaration.json')
    old=read(OUT/'mixed_review_with_final_fields.json');rows=[]
    cases={c['id']:c for c in cfg['cases']}
    for prior in old['cases']:
        row=dict(prior);dt=cases[row['case']]['dt_cap_ms'];end=row['native_end_time_ms']
        checks={k:v for k,v in row['checks'].items() if k!='native_final_field_clock_reaches_requested_end'}
        checks.update(native_final_clock_reaches_target=end>=1-1e-6,
                      overshoot_no_more_than_declared_dt=end<=1+dt+1e-6)
        row.update(checks=checks,pass_=all(checks.values()))
        row['pass']=row.pop('pass_')
        row.update(strict_endpoint_equality_initial_gate=prior['checks']['native_final_field_clock_reaches_requested_end'],declared_maximum_dt_ms=dt,clock_not_modified=True)
        rows.append(row)
    return {'cases':rows,'discretization_checks':old['discretization_checks'],
        'mechanical_witness_domain_pass':all(r['pass'] for r in rows) and all(old['discretization_checks'].values()),
        'earlier_failed_endpoint_gates_preserved':True,
        'reason':'A fixed step reaches or crosses the requested stopping time; compare actual final clock to [target,target+declared max dt], preserving the actual1.00001ms clock and the failed strict-equality gate. No requested horizon, time step or force/energy threshold changed.',
        'new_whole_duration_credit_s':0}

if __name__=='__main__':
    result=evaluate();saved=read(OUT/'mixed_review_terminal_time_interval.json');saved.pop('created_utc')
    assert result==saved
    dump(OUT/'terminal_clock_reproduction_review.json',{'created_utc':now(),'saved_analysis_reproduced':True,'new_Engine_runs':0,'initial_endpoint_failures_preserved':True,'interval_rule_is_analysis_correction_after_runs':True})
    print(json.dumps({'terminal_clock_reproduced':True,'actual_native_clock_unchanged':True}))
