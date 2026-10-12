"""Localize whole-data startup failure using the sealed cached initial preparation."""
from probe_aircraft_a41 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha,build,ff,PARENT_CARDS
import probe_aircraft_a37 as native37
from pathlib import Path
import shutil,argparse,time,json
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a42'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a42_predeclaration.json'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a41'
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a37/whole_compatibility'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A41';c=read(ROOT/'harness/publication_cycle.json');assert c['pending_count']==0 and c['last_published_iteration']=='AIRCRAFT-A41';assert read(PARENT/'publication_verification.json')['pass'];assert read(ROOT/'outputs/github_publication/updates_2026-10-12_aircraft_a40_a41/final_remote_verification.json')['pass'];g=read(SOURCE/'generation.json');state=SOURCE/(g['name']+'_0000_0001.rst');assert streamsha(state)==next(r['sha256'] for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a37/artifact_manifest.json')['files'] if r['path']==rel(state));OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 config={'iteration':'AIRCRAFT-A42','declared_utc':now(),'seed':1102067,'random_draws':0,'purpose':'Separate cached whole-model restart reading/complexity from implicit CHECK initialization. Same whole physical model and binary; no new preparation or substitutions.','source_generation':rel(SOURCE/'generation.json'),'source_generation_sha256':streamsha(SOURCE/'generation.json'),'source_initial_native_state':rel(state),'source_state_sha256':streamsha(state),'source_state_bytes':state.stat().st_size,'cases':[{'name':'WHOLE_EXPLICIT_READ','mode':'E','maximum_dt_ms':1e-5,'requested_end_ms':1e-5,'purpose':'Tiny explicit diagnostic with unchanged cached initial whole state; isolates read/initialization from implicit capability. It is not a10s run or extension beyond A20.'},{'name':'WHOLE_RREF_CHECK','mode':'CHECK','only_if_explicit_read_completes':True,'purpose':'Same physical state, qualified numeric reference floor; CHECK only. If explicit also fails, skip identical reread and localize shared read failure from source instead.'}],'execution':{'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_seconds':30,'estimated_seconds_max':360,'new_installation_or_compilation':False},'whole_physical_data_unchanged':True,'no_history_or_state_injection':True,'no_old_successful_solver_reruns':True,'failed_A37_CHECK_retained':True,'no_whole_qualification_inferred_from_diagnostic':True,'source_code_commit':build.PIN,'Linux_engine_sha256':streamsha(build.CAND/'isolated_exec/engine_linux64_gf_ompi')};dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True})
 pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PARENT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=PARENT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':['A41 registered160 with direct contact and temporal convergence qualified','A40+A41 published with both CI successful and120oldarchives verified.'],'same_blocker_without_new_evidence':False});print({'A42_declared':True,'whole_physical_inputs_unchanged':True},flush=True)

def one(case):
 guard();d=OUT/case['name'];assert not d.exists();d.mkdir();g=read(SOURCE/'generation.json');n=g['name'];src=ROOT/read(CFG)['source_initial_native_state'];shutil.copy2(src,d/src.name);assert streamsha(d/src.name)==read(CFG)['source_state_sha256'];g.update(diagnostic_case=case,configuration_sha256=streamsha(CFG),cached_preparation=True);dump(d/'generation.json',g)
 if case['mode']=='E':s='\n'.join(['/DT',ff(.4,0),'/DTIX',ff(1e-5,1e-5),'/ANIM/DT',ff(0,1e-5),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/PRINT/-1/1',f'/RUN/{n}/1',ff(1e-5),'/TFILE/4',ff(1e-5),'/VERS/2026'])+'\n'
 else:
  native37.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json';s=PARENT_CARDS(n,1,'I',.001,.001,'FREE',True);s='/IMPL/RREF/LIMIT\n'+ff(1.,1e30)+'\n'+s
 (d/(n+'_0001.rad')).write_text(s,encoding='utf8');ok=native37.native(d,n,1);assert streamsha(src)==read(CFG)['source_state_sha256'];dump(d/'review.json',{'created_utc':now(),'case':case,'native_completed':ok,'execution':read(d/'engine.log.execution.json'),'source_initial_state_unchanged':True,'whole_physical_inputs_unchanged':True,'whole_impact_qualified':False});print({'case':case['name'],'completed':ok},flush=True);return read(d/'review.json')

def run():
 guard();rows=[one(read(CFG)['cases'][0])]
 if rows[0]['native_completed']:rows.append(one(read(CFG)['cases'][1]))
 dump(OUT/'startup_review.json',{'created_utc':now(),'cases':rows,'whole_impact_qualified':False})

def preserve():
 from finalize_aircraft_a22 import verify_files
 guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True});print({'preserved_old_files':n},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','preserve']);globals()[p.parse_args().action]()
