"""Test paired TYPE2 grouping in the full model only with native binding equivalence checks."""
from probe_aircraft_a51 import ROOT,RUNTIME,CAND,BINARY,WHOLE,read,dump,rel,now,streamsha,harness,parse
from probe_aircraft_a49 import ii,env,win_execute
from pathlib import Path
import argparse,json,re,shutil,subprocess,time,shlex,hashlib
from collections import Counter
import build_aircraft_a35_mumps as bridge
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a52';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a52_predeclaration.json'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256'] and streamsha(BINARY)==read(CFG)['binary_sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();proof=ROOT/'outputs/github_publication/updates_2026-10-13_aircraft_a50_a51/final_remote_verification.json';assert read(proof)['pass'];h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A51';assert read(ROOT/'harness/publication_cycle.json')['pending_count']==0;prev=ROOT/'wtc1_simulation_v8/output/aircraft_a51';assert read(prev/'publication_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
 src=ROOT/'wtc1_simulation_v8/output/aircraft_a49/WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK';n='A49_EQUIVALENT_RIGID_CHAINS';files={'input':src/(n+'_0000.rad'),'state':src/(n+'_0000_0001.rst'),'Engine_card':src/(n+'_0001.rad')};S=parse(files['input']);interfaces={int(k.split('/')[-1]):v for k,v in S.items() if k.startswith('/INTER/TYPE2/')};assert set(interfaces)==set(range(16000,16432))
 for i in range(16000,16432,2):assert interfaces[i]==interfaces[i+1][:1]+[interfaces[i+1][1].replace(str(i+1),str(i)),interfaces[i+1][2]]
 p=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-n',bridge.linux(BINARY)],capture_output=True,timeout=30);assert p.returncode==0;lines=p.stdout.decode().splitlines();offsets=[int(next(l.split()[0] for l in lines if l.endswith(' '+s)),16) for s in ['i2updk0_','i2updk1_']]
 r=read(prev/'verified_printed_node_role_review.json');counts=Counter()
 for pair in r['pairs']:
  if pair['family']!='INTERFACE TYPE 2':continue
  sets=[{int(q['constraint'].split('/')[-1]) for q in roles if q['family']=='TYPE2'} for roles in pair['roles']]
  if sets[0]&sets[1]:kind='same_interface'
  elif {(v-16000)//2 for v in sets[0]}&{(v-16000)//2 for v in sets[1]}:kind='two_faces_same_facet'
  else:kind='different_facets'
  counts[kind]+=pair['messages']
 assert counts=={'two_faces_same_facet':37165,'same_interface':11831}
 c={'created_utc':now(),'iteration':'AIRCRAFT-A52','seed':1102077,'random_draws':0,'purpose':'Native full-model paired TYPE2 grouping with exact native selected-facet/coefficients/offset input comparison. All37165cross-interface warnings link the two faces of the same facet, so pairwise grouping is a more direct full-model test than another incomplete small reproducer.','scope_change_from_handoff':'Use new verified same-facet classification to test all216facet pairs directly. No physical-time or validation credit; reject candidate if native binding changes.','source_files':{k:{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for k,p in files.items()},'source_case_name':n,'binary_sha256':streamsha(BINARY),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_interface_parameters_all_pairwise_identical':True,'message_same_facet_classification':dict(counts),'changes':'Each of216even TYPE2s receives the union of its original disjoint lo/hi secondary groups and two main surface parts. Remove its odd TYPE2definition only; unused original odd groups/surfaces stay. All elements, coordinates, materials, properties, masses, RBE2/RBE3,TYPE25 and boundary/initial conditions retained.','native_measurement':'Own-child hardware entry breakpoints at I2UPDK0/I2UPDK1; read passed arrays NSV/IRTL/IRECT,CRST2orDPARA7,ITAB,X,NDOF. Compare by each original secondary label; actual ordered selected main labels, raw interpolation parameters, coordinates and DOF required equal within declared output-independent tolerances.','function_offsets':offsets,'maximum_nodes':48171,'acceptance':{'native_secondary_labels':3024,'original_calls_expected':432,'paired_calls_expected':216,'selected_main_original_labels_ordered_identical':True,'mode_and_NDOF_identical':True,'raw_parameter_absolute':1e-10,'raw_coordinate_absolute_mm':1e-8,'Starter_mass_relative':1e-6,'Starter_ADMAS_exact':True,'Starter_warnings_strict':0,'Starter_errors':0,'missing_connectivity_clean':0,'CHECK_errors_strict':0,'unsupported_TYPE25_not_hidden':5},'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_s':75,'maximum_total_s':540,'new_installation_or_compilation':False,'source_binary_or_process_data_patch':False,'mass_or_inertia_compensation':False,'new_whole_duration_credit_s':0,'objective1_complete':False};dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_native':True})
 pins={r['path']:r for f in ['preservation_before_metadata.json','artifact_manifest.json'] for r in read(prev/f)['files']}
 for f in ['artifact_manifest.json','publication_verification.json']:
  p=prev/f;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 rows=[]
 for r in pins.values():st=(ROOT/r['path']).stat();assert st.st_size==r['bytes'];rows.append({**r,'mtime_ns_before':st.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'method':'Metadata audit and retained immutable old hashes','source_archives_not_rescanned':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','same_external_blocker':False,'evidence':'A51 registered170, corrected printed label semantics, all37165cross TYPE2 messages now identified as the two sides of the same facet. A50+A51 published and verified. New whole grouping candidate with native binding guard available.'});print({'A52_declared':True,'whole_facet_pairs':216,'native_offsets':offsets},flush=True)

def trace(d,n):
 c=read(CFG);script=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a52_linux.py';config=d/'instrumentation_config.json';dump(config,{'binary':bridge.linux(BINARY),'binary_sha256':streamsha(BINARY),'directory':bridge.linux(d),'Engine_card':n+'_0001.rad','function_offsets':c['function_offsets'],'maximum_nodes':c['maximum_nodes']});q=lambda p:shlex.quote(bridge.linux(p));launch=d/'trace.launch.sh';launch.write_text('set -eu\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexec python3 '+q(script)+' '+q(config)+'\n',encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(launch)];start=time.perf_counter();p=subprocess.run(cmd,capture_output=True,timeout=195);(d/'trace.launcher.log').write_bytes(p.stdout+p.stderr);dump(d/'trace.launcher.execution.json',{'created_utc':now(),'argv':cmd,'parent_exit_code':p.returncode,'wall_s':time.perf_counter()-start,'CPU_threads':1,'GPU':False,'cap_s':180,'trace_script_sha256':streamsha(script),'immutable_helper_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py')});print({'case':d.name,'parent_exit':p.returncode,'trace_saved':(d/'type2_trace_result.json').exists()},flush=True)

def reference():
 guard();c=read(CFG);d=OUT/'WHOLE_ORIGINAL_TYPE2_BINDING_TRACE';assert not d.exists();d.mkdir();n=c['source_case_name']
 for key in ['state','Engine_card']:
  r=c['source_files'][key];p=ROOT/r['path'];assert streamsha(p)==r['sha256'];shutil.copy2(p,d/p.name)
 trace(d,n)

def paired():
 guard();c=read(CFG);src=ROOT/c['source_files']['input']['path'];assert streamsha(src)==c['source_files']['input']['sha256'];S=parse(src);before={k:list(v) for k,v in S.items()};n='A52_TYPE2_FACET_PAIRS';S['/BEGIN'][0]=n;S['/TITLE'][0]=n;changes=[]
 for i in range(16000,16432,2):
  lo='/GRNOD/NODE/'+str(i);hi='/GRNOD/NODE/'+str(i+1);a=[int(v) for row in S[lo][1:] for v in row.split()];b=[int(v) for row in S[hi][1:] for v in row.split()];assert len(a)==len(b)==7 and not(set(a)&set(b));S[lo]=S[lo][:1]+[ii(*(a+b)[j:j+10]) for j in range(0,14,10)];sl='/SURF/PART/'+str(i);sh='/SURF/PART/'+str(i+1);parts=[int(v) for key in [sl,sh] for row in S[key][1:] for v in row.split()];assert len(parts)==2;S[sl]=S[sl][:1]+[ii(*parts)];del S['/INTER/TYPE2/'+str(i+1)];changes.append({'even_interface':i,'removed_odd_interface':i+1,'secondary_union':a+b,'surface_part_union':parts})
 allowed={k for i in range(16000,16432,2) for k in ['/GRNOD/NODE/'+str(i),'/SURF/PART/'+str(i),'/INTER/TYPE2/'+str(i+1)]}|{'/BEGIN','/TITLE'}
 assert all(S.get(k)==v for k,v in before.items() if k not in allowed)
 d=OUT/'WHOLE_PAIRED_TYPE2_BINDING_TRACE';assert not d.exists();d.mkdir();(d/(n+'_0000.rad')).write_text('\n'.join(line for k,v in S.items() for line in [k]+v)+'\n',encoding='utf8');card=(ROOT/c['source_files']['Engine_card']['path']).read_text().replace(c['source_case_name'],n);(d/(n+'_0001.rad')).write_text(card,encoding='utf8');dump(d/'generation.json',{'created_utc':now(),'name':n,'configuration_sha256':streamsha(CFG),'physical_sections_and_all_other_constraints_unchanged':True,'changes':changes,'native_binding_equivalence_not_yet_assumed':True});en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,en);t=(d/'starter.log').read_text();w=int(re.findall(r'(\d+) WARNING\(S\)',t)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',t)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'warnings':w,'errors':e,'strict_pass':ok and w==0 and e==0,'known_original_penetration_warnings_not_hidden':True})
 if ok and e==0:trace(d,n)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','reference','paired']);globals()[p.parse_args().action]()
