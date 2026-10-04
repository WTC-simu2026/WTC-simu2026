"""Separate J endpoint-interval diagnostic; preserve three raw-time failures."""
from __future__ import annotations
import argparse,csv,json
from fractions import Fraction as Q
import run_impact_i02i_output_precision as j
import audit_impact_i02i_output_precision as a
h=j.h
CFG=j.ROOT/'wtc1_simulation_v8/data/impact_i02i_j_terminal_interval_predeclaration.json'
OUT=j.OUT/'terminal_time_diagnostic_r1.json'

def declare():
    assert not CFG.exists() and not OUT.exists()
    s=j.read(j.OUT/'verification_r1/summary.json')
    assert s['case_checks_passed']==53 and s['case_checks_total']==56
    h.dump(CFG,{'id':'IMPACT-I02I-J-TERMINAL-INTERVAL','declared_utc':h.NOW(),'seed':1102018,'random_draws':0,
        'parent_config_sha256':h.sha(j.CFG),'raw_audit_sha256':h.sha(j.OUT/'verification_r1/summary.json'),
        'scope':'Separate conditional endpoint rounding diagnostic; does not reassess or override J raw timing gates',
        'gates':{'endpoint_rule':'Closed exact nearest float32 time cell intersects [declared_end-2*cap,declared_end]',
            'old_raw_failures_retained':True,'CSV_endpoint_in_binary_cell':True,'no_new_time_shift':True},
        'rounding_assumption':'nearest binary32, not proven engine internal time precision',
        'inputs':'Only J decoded_binary.csv and immutable J parent config',
        'no_solver_or_converter':True,'no_fit_or_new_empirical_tolerance':True})
    print(json.dumps({'terminal_interval_declared':True,'raw_failures_retained':3}),flush=True)

def diagnose():
    assert not OUT.exists();cfg=j.read(CFG);parent=j.read(j.CFG)
    assert h.sha(j.OUT/'verification_r1/summary.json')==cfg['raw_audit_sha256']
    cases={};checks={}
    for c in parent['cases']:
        p=j.OUT/'verification_r1'/c['id']/'decoded_binary.csv'
        with p.open(encoding='utf-8',newline='') as f:rows=list(csv.reader(f))
        time=float(rows[-1][0]);lo,hi=a.rounding_interval32(time)
        end=Q(str(c['saved_case']['end_ms']));cap=Q(str(c['saved_case']['maximum_dt_ms']))
        with (j.ROOT/c['inputs']['csv']['path']).open(encoding='utf-8',newline='') as f:old=list(csv.reader(f))
        csv_end=Q(old[-1][0]);overlap=max(lo,end-2*cap)<=min(hi,end)
        raw=j.read(j.OUT/'verification_r1'/c['id']/'audit.json')['checks']['no_truncation_or_extrapolation']
        cases[c['id']]={'binary_end_ms':time,'declared_end_ms':float(end),'binary_minus_declared_ms':float(a.qfloat(time)-end),
            'lower_exact_ms':str(lo),'upper_exact_ms':str(hi),'lower_ms':float(lo),'upper_ms':float(hi),
            'endpoint_window_compatible':bool(overlap),'CSV_end_inside_binary_cell':bool(lo<=csv_end<=hi),
            'raw_time_gate_still_passes':raw,'raw_gate_not_overridden':True}
        checks[c['id']+'_interval']=bool(overlap);checks[c['id']+'_CSV']=bool(lo<=csv_end<=hi)
    h.dump(OUT,{'created_utc':h.NOW(),'pass':all(checks.values()),'checks':checks,'cases':cases,
        'config_sha256':h.sha(CFG),'script_sha256':h.sha(__file__),'parent_raw_gates_unchanged':True,
        'raw_failures_preserved':sum(not c['raw_time_gate_still_passes'] for c in cases.values()),
        'interpretation':'Endpoint compatibility only under quantization assumption; no missing CSV row, no extrapolation used; three raw binary-end tests stay failed.'})
    print(json.dumps({'time_interval_pass':all(checks.values()),'checks':len(checks),'raw_failures_retained':3,
        'binary_end_errors_ms':{name:c['binary_minus_declared_ms'] for name,c in cases.items()}}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','diagnose']);args=p.parse_args();globals()[args.action]()
