"""Predeclare and run owned approximate symmetric surface iteration only."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import shutil,json,subprocess,sys,time

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a61'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a61_predeclaration.json'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A60'
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a60';cfg=read(ROOT/'wtc1_simulation_v8/data/aircraft_a60_predeclaration.json')
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    cached=[prior/'material_Jacobian_state_review.json',prior/'mixed_review_terminal_time_interval.json']
    config={'created_utc':now(),'iteration':'AIRCRAFT-A61','seed':1102086,'random_draws':0,'cohesive':cfg['cohesive'],
      'purpose':'Owned symmetric elastic surface iteration matrix with full unchanged material residual; concrete native candidate proposal only, not applied/compiled.',
      'units':{'length':'mm','force':'N','surface_K':'N/mm3','work_Nmm_to_J':.001},
      'surface':{'reference_GP_areas_mm2':[25,25,25,25],'native_HH_order':'SDEF43: dominant node1,2,3,4 in that order','normal_from_current_midface':True,'approximate_geometric_derivative_omitted':True},
      'prototype':{'cap_s':120,'CPU':1,'GPU':False,'maximum_iterations':200,'force_residual_absolute_N':1e-8,'root_tolerance_mm':1e-10,'matrix_relative_tolerance':1e-12,'FD_relative_tolerance':1e-7},
      'cached_sources':[{'path':rel(p),'sha256':sha(p)} for p in cached],
      'software_source':{'archive':'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz','sha256':'d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8','pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a'},
      'new_Starter_or_Engine_runs':0,'new_software_patch_applied_or_compiled':False,
      'future_candidate_scope':{'TYPE43':True,'LAW117':True,'Ismstr':1,'Gauss_points':4,'other_types_preserved':True,'history_and_material_residual_unchanged':True},
      'future_build_requires_distinct_human_approval':True,'future_build_cap_s':3600,'future_build_CPU':6,'future_GPU':False,'future_installation':False,'future_native_cap_s':180,
      'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_prototype':True})
    pins={r['path']:r for r in read(prior/'preservation_before_metadata.json')['files']}
    for r in read(prior/'artifact_manifest.json')['files']:pins[r['path']]=r
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})
    print(json.dumps({'A61_declared':True,'new_native_runs':0}),flush=True)

def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];return read(CFG)

def run():
    c=guard();script=ROOT/'wtc1_simulation_v8/scripts/surface_iteration_aircraft_a61.py';start=time.perf_counter()
    r=subprocess.run([sys.executable,str(script)],capture_output=True,timeout=c['prototype']['cap_s'])
    (OUT/'prototype.log').write_bytes(r.stdout+r.stderr)
    dump(OUT/'prototype_execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':c['prototype']['cap_s'],'CPU':1,'GPU':False,'script_sha256':sha(script)})
    print(r.stdout.decode('utf8',errors='replace'),flush=True);assert r.returncode==0,r.stderr.decode('utf8',errors='replace')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
