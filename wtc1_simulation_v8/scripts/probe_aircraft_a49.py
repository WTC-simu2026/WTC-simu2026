"""Declare a stronger native observation and map actual element IDs to the immutable input."""
from probe_aircraft_a48 import ROOT,RUNTIME,CAND,BINARY,WHOLE,read,dump,rel,now,streamsha,harness,sections,ii,ff,group,env,win_execute
from pathlib import Path
import argparse,shutil,json,re,hashlib,tarfile,subprocess,time,shlex
import build_aircraft_a35_mumps as bridge
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a49'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a49_predeclaration.json'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256'];assert streamsha(BINARY)==read(CFG)['binary_sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A48';prev=ROOT/'wtc1_simulation_v8/output/aircraft_a48';assert read(prev/'publication_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
 archive=CAND/'source.tar.gz';assert streamsha(archive)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256'];source_rows=[]
 with tarfile.open(archive,'r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for suffix in ['engine/source/elements/shell/coqueba/cbake3.F','engine/source/elements/shell/coqueba/cbacoork.F','common_source/modules/elements/element_mod.F90']:
   data=tar.extractfile(members[suffix]).read();source_rows.append({'path':suffix,'sha256':hashlib.sha256(data).hexdigest(),'raw_source_redistributed':False})
   if suffix.endswith('element_mod.F90'):assert 'nixc = 7' in data.decode().lower()
 p=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-n',bridge.linux(BINARY)],capture_output=True,timeout=30);assert p.returncode==0;symbol=next(l for l in p.stdout.decode().splitlines() if l.endswith(' cbake3_'));shell_offset=int(symbol.split()[0],16);source=prev/'WHOLE_NO_RBE3_CHECK';n=read(source/'generation.json')['name'];files=[source/(n+'_0000_0001.rst'),source/(n+'_0001.rad')]
 dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A49','seed':1102074,'random_draws':0,'purpose':'Observe native CBAKE3 IXC/X at the same sparse assembly fault, validate original element IDs and node coordinate correspondence, then build targeted reproducer.','source':rel(source),'name':n,'files':[{'path':rel(f),'sha256':streamsha(f),'bytes':f.stat().st_size} for f in files],'binary_sha256':streamsha(BINARY),'source_mechanics':source_rows,'source_schema':{'IXC_dimension':7,'IXC_material_row':1,'IXC_nodes_rows':[2,3,4,5],'IXC_property_row':6,'IXC_user_element_row':7,'X':'X(3,*) double precision, runtime internal indices','CBAKE3_X_argument_1based':27,'CBAKE3_IXC_argument_1based':12,'fact':'CBACOORK assigns NGL(I)=IXC(7,I), documented users element ID; coordinate matches required before node-label mapping.'},'function_offset':0xb9d0a0,'shell_function_offset':shell_offset,'pattern_symbol_offset':0x8447bd8,'maximum_nodes':48171,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_s':30,'new_installation_or_compilation':False,'no_physical_state_or_instruction_memory_patch':True,'prior_failed_cases_retained':True,'source_pin':read(ROOT/'wtc1_simulation_v8/data/aircraft_a45_predeclaration.json')['build']['complete_source_pin'],'whole_input_sha256':streamsha(WHOLE),'source_coordinate_tolerance_mm':1e-8,'new_whole_duration_credit_s':0,'objective1_complete':False});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_native':True});pins={r['path']:r for f in ['preservation_before_metadata.json','artifact_manifest.json'] for r in read(prev/f)['files']}
 for f in ['artifact_manifest.json','publication_verification.json']:
  p=prev/f;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 rows=[]
 for r in pins.values():
  st=(ROOT/r['path']).stat();assert st.st_size==r['bytes'];rows.append({**r,'mtime_ns_before':st.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'method':'Immutable hashes retained, before/after metadata audit, not full old-content rehash.','source_archives_not_rescanned':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':'A48 registered167, captured real sparse graph at SIGSEGV using unmodified native child;26pairs/156missing rows, active6/3DOF. Mapping incomplete, stronger coordinate observation now available.','same_external_blocker':False});print({'A49_declared':True,'shell_symbol':hex(shell_offset),'source_IXC_dimension':7},flush=True)

def run():
 guard();c=read(CFG);d=OUT/'WHOLE_NATIVE_ELEMENT_MAP';assert not d.exists();d.mkdir();n=c['name']
 for row in c['files']:
  f=ROOT/row['path'];assert streamsha(f)==row['sha256'];shutil.copy2(f,d/f.name);assert streamsha(d/f.name)==row['sha256']
 dump(d/'instrumentation_config.json',{'binary':bridge.linux(BINARY),'binary_sha256':streamsha(BINARY),'directory':bridge.linux(d),'Engine_card':n+'_0001.rad',**{k:c[k] for k in ['function_offset','shell_function_offset','pattern_symbol_offset','maximum_nodes']}});q=lambda p:shlex.quote(bridge.linux(p));s='set -eu\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexport OMPI_MCA_mpi_abort_print_stack=1\nexec python3 '+q(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a49_linux.py')+' '+q(d/'instrumentation_config.json')+'\n';script=d/'trace.launch.sh';script.write_text(s,encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(script)];t=time.perf_counter();r=subprocess.run(cmd,capture_output=True,timeout=195);(d/'trace.launcher.log').write_bytes(r.stdout+r.stderr);dump(d/'trace.launcher.execution.json',{'created_utc':now(),'argv':cmd,'exit_code':r.returncode,'wall_s':time.perf_counter()-t,'cap_s':180,'CPU_threads':1,'GPU':False,'binary_sha256':streamsha(BINARY),'trace_script_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a49_linux.py'),'immutable_helper_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py')});print({'trace_launcher_exit':r.returncode,'result_saved':(d/'trace_result.json').exists()},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
