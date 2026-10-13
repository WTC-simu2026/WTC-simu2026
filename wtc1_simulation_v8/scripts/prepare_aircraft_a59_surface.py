"""Predeclare and execute only the owned bounded surface prototype, no Engine patch."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,shutil,subprocess,time,sys

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a59'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a59_predeclaration.json'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A58'
    a17=read(ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json');prior=ROOT/'wtc1_simulation_v8/output/aircraft_a58';native=ROOT/'wtc1_simulation_v8/output/aircraft_a57/cohesive_controls/cohesive_review.json';v=read(native);assert v['mechanical_implementation_gate_pass']
    rows=[]
    for row in v['cases']:
        p=native.parent/'w0'/row['case']['id']/'cohesive_diagnostics.npz';rows.append({'case':row['case'],'path':rel(p),'sha256':sha(p)})
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={'created_utc':now(),'iteration':'AIRCRAFT-A59','seed':1102084,'random_draws':0,'workspace':str(ROOT),'purpose':'Independent area surface residual and active pure-mode tangent prototype. Verify actual equilibrium/closed integral/FD/cached native witnesses before considering a source patch.','cohesive':a17['cohesive'],'acceptance':a17['acceptance'],'cached_native_diagnostics':rows,'units':{'length':'mm','force':'N','traction':'N/mm2','surface_K':'N/mm3','work_to_J':.001},'CPU':1,'GPU':False,'cap_s':120,'expected_seconds':[1,30],'native_Engine_executions':0,'Starter_runs':0,'new_Engine_software_patch_or_compile':False,'mixed_mode_or_native_transfer_not_qualified':True,'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_prototype':True})
    pins={r['path']:r for r in read(prior/'preservation_before_metadata.json')['files']}
    for r in read(prior/'artifact_manifest.json')['files']:pins[r['path']]=r
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})
    print('A59 surface prototype declared; cached native output only, no solver replay.',flush=True)

def run():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    script=ROOT/'wtc1_simulation_v8/scripts/surface_aircraft_a59.py';argv=[sys.executable,str(script),str(CFG),str(OUT/'surface_prototype_review.json')];start=time.perf_counter()
    p=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=120);(OUT/'prototype.log').write_bytes(p.stdout+p.stderr)
    dump(OUT/'prototype_execution.json',{'created_utc':now(),'argv':argv,'exit_code':p.returncode,'wall_s':time.perf_counter()-start,'cap_s':120,'CPU':1,'GPU':False,'script_sha256':sha(script),'native_Engine_replays':0})
    print(p.stdout.decode('utf8',errors='replace'),flush=True);assert p.returncode==0,p.stderr.decode('utf8',errors='replace')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
