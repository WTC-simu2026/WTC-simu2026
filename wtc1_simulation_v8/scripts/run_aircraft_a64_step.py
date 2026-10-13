"""Ready bounded runner; every native launch requires the exact separate budget approval."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a64_step import PREP,PLAN
from pathlib import Path
from material_aircraft_a60 import path_values
import probe_aircraft_a54 as launcher
import numpy as np,subprocess,shutil,time,ast,json,re,argparse

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a64'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a64_predeclaration.json'
CONTROL=CFG
RUNTIME=launcher.RUNTIME

def guard():
    c=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a64_authorization.json')
    assert auth['explicit_human_authorization'] and auth['plan_sha256']==sha(PLAN) and auth['maximum_native_runs']==4
    return c

def engine():
    c=guard();old=read(ROOT/'wtc1_simulation_v8/output/aircraft_a62/build_finished.json');p=ROOT/old['candidate_directory'];b=p/'isolated_exec/engine_linux64_gf_ompi';assert sha(b)==c['binary_sha256'];return p,b

def declare():
    assert not OUT.exists() and not CFG.exists();auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a64_authorization.json');plan=read(PLAN)
    assert auth['explicit_human_authorization'] and auth['plan_sha256']==sha(PLAN) and auth['maximum_native_runs']==4
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A63' and read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(CFG,{**plan,'iteration':'AIRCRAFT-A64','created_utc':now(),'authorization':auth});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_native_execution':True})
    old=ROOT/'wtc1_simulation_v8/output/aircraft_a63';pins={r['path']:r for r in read(old/'preservation_before_metadata.json')['files']}
    for r in read(old/'artifact_manifest.json')['files']:pins[r['path']]=r
    for p in [old/'artifact_manifest.json',old/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})

source=(ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a62_surface.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='generate');s=ast.get_source_segment(source,node).replace("name='A62_'","name='A64_'")
exec(compile(s,__file__,'exec'))

def native(d,name):
    engine();ordinal=len(list(OUT.rglob('engine.execution.json')))+1;assert ordinal<=4
    dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':ordinal,'maximum_native':4,'cap_s':180,'CPU':1,'GPU':False,'authorized_plan_sha256':sha(PLAN)})
    launcher.engine=engine;return launcher.run_native(d,name)

def free():
    rows=[]
    for case in guard()['cases']:
        d,name=generate(case);r=native(d,name)
        if r['parent_exit_code']==0 and r['normal_termination']:
            conversion=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60);(d/'converter.log').write_bytes(conversion.stdout+conversion.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':conversion.returncode,'cap_s':60})
        rows.append({'case':case['id'],**r});print(json.dumps(rows[-1]),flush=True)
    dump(OUT/'free_execution_review.json',{'created_utc':now(),'cases':rows,'all_normal':all(r['parent_exit_code']==0 and r['normal_termination'] for r in rows)})

def review_free():
    import review_aircraft_a63_free as reviewer
    reviewer.OUT=OUT;reviewer.CFG=CFG;reviewer.engine=engine;reviewer.main()

def whole():
    c=guard();local=read(OUT/'free_cohesive_qualification_review.json');assert local['pass'],'Conditional whole CHECK prohibited: refined local gate failed'
    rows=[]
    for case in c['whole_CHECK_cases']:
        d=OUT/case['id'];assert not d.exists();d.mkdir()
        for entry in case['files']:
            p=ROOT/entry['path'];assert sha(p)==entry['sha256'];shutil.copy2(p,d/p.name)
        dump(d/'generation.json',{'created_utc':now(),'configuration_sha256':sha(CFG),'case':case,'unchanged_inputs_and_cards':True,'CHECK_only_no_dynamic_extension':True})
        r=native(d,case['name']);log=(d/'engine.log').read_text(encoding='utf8',errors='replace');r.update(zero_volume_messages=log.lower().count('zero or negative volume'),stop_or_USER_BREAK=bool(re.search(r'USER\s*BREAK|STOP\s+61|STOP\s+zero',log,re.I)))
        rows.append({'case':case['id'],**r});print(json.dumps(rows[-1]),flush=True)
    dump(OUT/'whole_CHECK_review.json',{'created_utc':now(),'cases':rows,'all_clean':all(r['parent_exit_code']==0 and r['CHECK_ended'] and r['CHECK_errors']==0 and r['TYPE25_ignored']==0 and not r['stop_or_USER_BREAK'] for r in rows),'whole_impact_qualification_not_inferred':True,'whole_credit_s':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','free','review_free','whole']);globals()[p.parse_args().action]()
