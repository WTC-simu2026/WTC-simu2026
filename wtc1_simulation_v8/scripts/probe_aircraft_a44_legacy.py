"""Bounded native controls for the newly authorized legacy-format MUMPS Engine."""
from preflight_aircraft_a43 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha
from pathlib import Path
import subprocess,shutil,time,shlex,argparse
import build_aircraft_a35_mumps as bridge
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a44'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a44_predeclaration.json'
CAND=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate'
BINARY=CAND/'isolated_exec/engine_linux64_gf_ompi'

def guard():
 assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256'];assert read(OUT/'build_finished.json')['build_success'];assert streamsha(BINARY)==read(OUT/'build_finished.json')['binary_sha256']

def execute(d,n,label='engine'):
 guard();q=lambda p:shlex.quote(bridge.linux(p));script=d/(label+'.launch.sh');assert not script.exists();script.write_text('set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexport OMPI_MCA_mpi_abort_print_stack=1\nexec '+q(BINARY)+' -i '+shlex.quote(n+'_0001.rad')+' > '+shlex.quote(label+'.log')+' 2>&1\n',encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(script)];t=time.perf_counter();r=subprocess.run(cmd,capture_output=True,timeout=195);(d/(label+'.launcher.log')).write_bytes(r.stdout+r.stderr);dump(d/(label+'.log.execution.json'),{'created_utc':now(),'exe':rel(BINARY),'sha256':streamsha(BINARY),'source_pin':read(CFG)['build']['complete_source_pin'],'exit_code':r.returncode,'wall_s':time.perf_counter()-t,'CPU_threads':1,'GPU':False,'cap_s':180,'argv':cmd});log=(d/(label+'.log')).read_text(errors='replace') if (d/(label+'.log')).exists() else '';ok=r.returncode==0 and 'NORMAL TERMINATION' in log;dump(d/'completion.json',{'created_utc':now(),'exit_code':r.returncode,'normal_termination':'NORMAL TERMINATION' in log,'pass':ok});return ok

def coupons():
 guard();baseline=read(OUT/'cached_Windows_LAW117_reference_review.json');assert baseline['pass'];rows=[]
 for row in baseline['cached_cases']:
  case=row['case'];d=OUT/'w0'/case['id'];assert not d.exists();d.mkdir(parents=True);n=row['cached_generation']['name'];transfers=[]
  for entry in [row['initial_state'],row['Engine_cards']]:
   src=ROOT/entry['path'];assert streamsha(src)==entry['sha256'];dest=d/src.name;shutil.copy2(src,dest);assert streamsha(dest)==entry['sha256'];transfers.append({'source':entry['path'],'target':rel(dest),'sha256':entry['sha256'],'bytes':entry['bytes']})
  dump(d/'generation.json',row['cached_generation']);dump(d/'restart_transfer.json',{'created_utc':now(),'files':transfers,'full_native_state_copy':True,'no_physical_state_modified':True});ok=execute(d,n);converted=False
  if ok:
   t=time.perf_counter();r=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),n+'T01'],cwd=d,capture_output=True,timeout=120);(d/'converter.log').write_bytes(r.stdout+r.stderr);dump(d/'converter.log.execution.json',{'created_utc':now(),'exe':rel(RUNTIME/'th_to_csv_win64.exe'),'sha256':streamsha(RUNTIME/'th_to_csv_win64.exe'),'exit_code':r.returncode,'wall_s':time.perf_counter()-t,'cap_s':120});converted=r.returncode==0 and (d/(n+'T01.csv')).exists()
  rows.append({'case':case,'native_completed':ok,'history_converted':converted,'Windows_reference':rel(ROOT/row['initial_state']['path'].rsplit('/',1)[0])});print({'case':case['id'],'new_Engine_completed':ok,'history_converted':converted},flush=True)
 dump(OUT/'native_coupon_execution_review.json',{'created_utc':now(),'cases':rows,'all_native_completed':all(r['native_completed'] and r['history_converted'] for r in rows),'fresh_Starter_executions':0,'old_Windows_solver_replays':0,'whole_insertion_ready':False})

def review():
 guard();assert read(OUT/'native_coupon_execution_review.json')['all_native_completed'];import review_aircraft_a17 as auditor;auditor.OUT=OUT;auditor.main();print({'new_Engine_cohesive_gate_pass':read(OUT/'cohesive_review.json')['mechanical_implementation_gate_pass']},flush=True)

def whole():
 guard();assert read(OUT/'cohesive_review.json')['mechanical_implementation_gate_pass'];source=ROOT/'wtc1_simulation_v8/output/aircraft_a37/whole_compatibility';g=read(source/'generation.json');n=g['name'];state=source/(n+'_0000_0001.rst');assert streamsha(state)==read(ROOT/'wtc1_simulation_v8/data/aircraft_a42_predeclaration.json')['source_state_sha256'];d=OUT/'WHOLE_EXPLICIT_STARTUP';assert not d.exists();d.mkdir();shutil.copy2(state,d/state.name);card=ROOT/'wtc1_simulation_v8/output/aircraft_a42/WHOLE_EXPLICIT_READ'/f'{n}_0001.rad';shutil.copy2(card,d/card.name);dump(d/'generation.json',g);ok=execute(d,n);dump(d/'review.json',{'created_utc':now(),'native_completed':ok,'unchanged_initial_state_sha256':streamsha(d/state.name),'unchanged_whole_physics':True,'new_physical_duration_credit_s':0,'whole_impact_qualified':False});print({'whole_explicit_startup_completed':ok},flush=True)
 if ok:
  from probe_aircraft_a41 import PARENT_CARDS,ff
  import probe_aircraft_a37 as helper
  helper.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json';q=OUT/'WHOLE_IMPLICIT_CHECK';q.mkdir();shutil.copy2(state,q/state.name);dump(q/'generation.json',g);text='/IMPL/RREF/LIMIT\n'+ff(1,1e30)+'\n'+PARENT_CARDS(n,1,'I',.001,.001,'FREE',True);(q/(n+'_0001.rad')).write_text(text,encoding='utf8');finished=execute(q,n);log=(q/'engine.log').read_text(errors='replace');dump(q/'review.json',{'created_utc':now(),'native_completed':finished,'check_report_begins':'BEGIN IMPLICIT MODEL CHECKING' in log,'check_report_ends':'END IMPLICIT MODEL CHECKING' in log,'same_initial_state_sha256':streamsha(q/state.name),'whole_impact_qualified':False});print({'whole_CHECK_completed':finished},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['coupons','review','whole']);globals()[p.parse_args().action]()
