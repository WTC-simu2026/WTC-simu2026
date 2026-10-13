"""Observe the new grouped-input failure at CBAKE3/ASSEMC, without changing the Engine or physics."""
from probe_aircraft_a52 import *
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a52_sparse_fault_predeclaration.json'

def declare():
 guard();assert not DEC.exists();d=OUT/'WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1';r=read(d/'type2_trace_result.json');assert r['Engine_exit_code']==3 and len(r['calls'])==0 and r['faults'][0]['instruction_offset']=='0xb9d704';n='A52_TYPE2_FACET_PAIRS_R1';old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a49_predeclaration.json');files=[d/(n+'_0000_0001.rst'),d/(n+'_0001.rad')]
 dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A52','seed':1102077,'random_draws':0,'source_case':rel(d),'files':[{'path':rel(f),'sha256':streamsha(f),'bytes':f.stat().st_size} for f in files],'name':n,'binary_sha256':streamsha(BINARY),'function_offset':old['function_offset'],'shell_function_offset':old['shell_function_offset'],'pattern_symbol_offset':old['pattern_symbol_offset'],'maximum_nodes':48171,'purpose':'Grouped whole candidate failed in ASSEMC+0x664 before any TYPE2binding callback. Capture actual missing rows and source element labels to classify that failed candidate. No equivalent-binding claim and no impact.','CPU_threads':1,'GPU':False,'expected_s':15,'per_process_cap_s':180,'software_or_physical_data_patched':False,'new_physical_duration_credit_s':0})
 dump(OUT/'sparse_fault_guard.json',{'created_utc':now(),'sha256':streamsha(DEC),'before_new_native_measurement':True});print('New sparse-fault observation declared; grouped candidate remains rejected.',flush=True)

def run():
 guard();assert streamsha(DEC)==read(OUT/'sparse_fault_guard.json')['sha256'];c=read(DEC);d=OUT/'WHOLE_PAIRED_SPARSE_FAULT_TRACE';assert not d.exists();d.mkdir()
 for r in c['files']:
  p=ROOT/r['path'];assert streamsha(p)==r['sha256'];shutil.copy2(p,d/p.name)
 config=d/'instrumentation_config.json';dump(config,{'binary':bridge.linux(BINARY),'binary_sha256':streamsha(BINARY),'directory':bridge.linux(d),'Engine_card':c['name']+'_0001.rad',**{k:c[k] for k in ['function_offset','shell_function_offset','pattern_symbol_offset','maximum_nodes']}});script=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a49_linux.py';q=lambda p:shlex.quote(bridge.linux(p));launch=d/'trace.launch.sh';launch.write_text('set -eu\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexec python3 '+q(script)+' '+q(config)+'\n',encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(launch)];start=time.perf_counter();p=subprocess.run(cmd,capture_output=True,timeout=195);(d/'trace.launcher.log').write_bytes(p.stdout+p.stderr);dump(d/'trace.launcher.execution.json',{'created_utc':now(),'argv':cmd,'parent_exit_code':p.returncode,'wall_s':time.perf_counter()-start,'cap_s':180,'CPU_threads':1,'GPU':False,'immutable_observer_sha256':streamsha(script)});print({'new_sparse_observation_saved':(d/'trace_result.json').exists(),'parent_exit':p.returncode},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
