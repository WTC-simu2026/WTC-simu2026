"""Declare and execute a direct mapping of the current faulting full-model assembly block."""
from probe_aircraft_a52 import ROOT,RUNTIME,CAND,BINARY,WHOLE,read,dump,rel,now,streamsha,harness,parse
from pathlib import Path
import argparse,tarfile,hashlib,subprocess,time,shlex,shutil,re,json
import build_aircraft_a35_mumps as bridge
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a53';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a53_predeclaration.json'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256'] and streamsha(BINARY)==read(CFG)['binary_sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A52';prev=ROOT/'wtc1_simulation_v8/output/aircraft_a52';assert read(prev/'publication_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
 archive=CAND/'source.tar.gz';assert streamsha(archive)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256'];sources=[];signature=None
 with tarfile.open(archive,'r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for path in ['engine/source/implicit/imp_solv.F','engine/source/implicit/assem_c4.F','common_source/modules/elements/element_mod.F90']:
   b=tar.extractfile(members[path]).read();sources.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'raw_source_redistributed':False})
   if path.endswith('imp_solv.F'):
    lines=b.decode().splitlines();i=next(i for i,s in enumerate(lines) if 'SUBROUTINE IMP_CHKM(' in s);parts=[lines[i].split('(',1)[1]];j=i+1
    while ')' not in parts[-1]:parts.append(lines[j][6:].strip());j+=1
    signature=[x.strip() for x in ''.join(parts).split(')',1)[0].split(',')];assert signature.index('ITAB')+1==15 and signature.index('X')+1==46
   elif path.endswith('assem_c4.F'):assert 'IXC(NIXC,*)' in b.decode()
   else:assert 'nixc = 7' in b.decode().lower()
 p=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-n',bridge.linux(BINARY)],capture_output=True,timeout=30);assert p.returncode==0;lines=p.stdout.decode().splitlines();offsets={s:int(next(l.split()[0] for l in lines if l.endswith(' '+s)),16) for s in ['assem_c4_','imp_chkm_']};prior=read(ROOT/'wtc1_simulation_v8/data/aircraft_a52_sparse_fault_predeclaration.json');case=prev/'WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1';name='A52_TYPE2_FACET_PAIRS_R1';files=[case/(name+'_0000_0001.rst'),case/(name+'_0001.rad'),case/(name+'_0000.rad')]
 c={'created_utc':now(),'iteration':'AIRCRAFT-A53','seed':1102078,'random_draws':0,'purpose':'Capture actual ASSEM_C4 connectivity and global CHECK labels/coordinates at the known fault. Reject stale context unless every current NI/NJ pair belongs to its current IXC element.','files':[{'path':rel(f),'sha256':streamsha(f),'bytes':f.stat().st_size} for f in files],'name':name,'binary_sha256':streamsha(BINARY),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_review':sources,'IMP_CHKM_argument_names':signature,'ITAB_argument_1based':15,'X_argument_1based':46,'function_offset':prior['function_offset'],'pattern_symbol_offset':prior['pattern_symbol_offset'],'ASSEM_C4_offset':offsets['assem_c4_'],'IMP_CHKM_offset':offsets['imp_chkm_'],'maximum_nodes':48171,'acceptance':{'all_current_NI_NJ_in_corresponding_IXC_element':True,'all_element_user_IDs_and_original_labels_match_input':True,'maximum_coordinate_error_mm':1e-8},'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_s':20,'new_installation_or_compilation':False,'source_binary_or_process_mechanics_patch':False,'grouped_candidate_remains_rejected':True,'new_whole_duration_credit_s':0,'objective1_complete':False};dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_native':True})
 pins={r['path']:r for f in ['preservation_before_metadata.json','artifact_manifest.json'] for r in read(prev/f)['files']}
 for f in ['artifact_manifest.json','publication_verification.json']:
  p=prev/f;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 rows=[]
 for r in pins.values():st=(ROOT/r['path']).stat();assert st.st_size==r['bytes'];rows.append({**r,'mtime_ns_before':st.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'method':'Metadata audit plus immutable old hash manifests','source_archives_not_rescanned':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','same_external_blocker':False,'evidence':'A52 registered171, tested paired whole TYPE2 candidate, rejected unavailable binding equivalence, captured new24pairs/144missing rows and disproved correspondence with stale8element CBAKE3 context. Direct ASSEM_C4 observation and CHECK ITAB/X signature now verified.'});print({'A53_declared':True,'ITAB_argument':15,'X_argument':46,'ASSEM_C4_offset':offsets['assem_c4_'],'IMP_CHKM_offset':offsets['imp_chkm_']},flush=True)

def run():
 guard();c=read(CFG);d=OUT/'WHOLE_ACTUAL_ASSEMBLY_BLOCK_TRACE';assert not d.exists();d.mkdir()
 for r in c['files'][:2]:
  p=ROOT/r['path'];assert streamsha(p)==r['sha256'];shutil.copy2(p,d/p.name)
 config=d/'instrumentation_config.json';dump(config,{'binary':bridge.linux(BINARY),'binary_sha256':streamsha(BINARY),'directory':bridge.linux(d),'Engine_card':c['name']+'_0001.rad',**{k:c[k] for k in ['function_offset','ASSEM_C4_offset','IMP_CHKM_offset','ITAB_argument_1based','X_argument_1based','pattern_symbol_offset','maximum_nodes']}});script=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a53_linux.py';q=lambda p:shlex.quote(bridge.linux(p));launch=d/'trace.launch.sh';launch.write_text('set -eu\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexec python3 '+q(script)+' '+q(config)+'\n',encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(launch)];t=time.perf_counter();p=subprocess.run(cmd,capture_output=True,timeout=195);(d/'trace.launcher.log').write_bytes(p.stdout+p.stderr);dump(d/'trace.launcher.execution.json',{'created_utc':now(),'argv':cmd,'parent_exit':p.returncode,'wall_s':time.perf_counter()-t,'CPU_threads':1,'GPU':False,'cap_s':180,'script_sha256':streamsha(script),'immutable_helper_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py')});print({'trace_saved':(d/'trace_result.json').exists(),'parent_exit':p.returncode},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
