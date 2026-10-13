"""Bounded explicit startup of the equivalent rigid-chain model, using an immutable cached reference."""
from probe_aircraft_a49 import ROOT,RUNTIME,CAND,BINARY,WHOLE,read,dump,rel,now,streamsha,harness,sections,env,win_execute
from audit_aircraft_a05 import histories,vtk
from pathlib import Path
import argparse,json,shutil,subprocess,time,re,tarfile,hashlib
import numpy as np
import probe_aircraft_a45 as launcher
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a50';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a50_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a49'
SOURCE=PREV/'WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK'
REFERENCE=ROOT/'wtc1_simulation_v8/output/aircraft_a45/WHOLE_EXPLICIT_STARTUP'

def guard():
 assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']
 assert streamsha(BINARY)==read(CFG)['binary_sha256']

def declare():
 assert not OUT.exists() and not CFG.exists()
 publication=ROOT/'outputs/github_publication/updates_2026-10-12_aircraft_a48_a49/final_remote_verification.json'
 assert read(publication)['pass']
 h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A49'
 assert read(ROOT/'harness/publication_cycle.json')['pending_count']==0
 assert read(PREV/'publication_verification.json')['pass']
 OUT.mkdir();dump(OUT/'harness_before.json',h)
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
 name='A49_EQUIVALENT_RIGID_CHAINS';refname='A37_WHOLE_CHECK'
 sources=[SOURCE/(name+'_0000_0001.rst'),SOURCE/(name+'_0000.rad'),REFERENCE/(refname+'_0001.rad'),REFERENCE/(refname+'T01')]+[REFERENCE/(refname+f'A{k:03}') for k in [1,2,3]]
 c={'created_utc':now(),'iteration':'AIRCRAFT-A50','seed':1102075,'random_draws':0,'purpose':'Native explicit startup budgets and saved fields after exact rigid-chain composition; then readonly interpretation of remaining sparse-condensation warnings.','units':{'native':['g','mm','ms'],'g_to_kg':.001,'Nmm_to_J':.001,'g_mm_ms_to_Ns':.001},'name':name,'reference_name':refname,'sources':[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in sources],'binary_sha256':streamsha(BINARY),'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','reference_cached_no_Engine_replay':True,'native_restart_reused_without_state_injection':True,'same_explicit_controls_as_A45':{'DTIX_ms':1e-5,'RUN_end_ms':1e-5,'expected_saved_last_ms':2e-5,'expected_cycles':3,'TFILE_ms':1e-5,'no_implicit':True,'TYPE25_preserved':5,'mass_scaling':False},'acceptance':{'finite':True,'NORMAL_exit0_no_kill':True,'cycles':3,'sample_time_absolute_ms':1e-11,'mass_relative':1e-6,'mass_scaling_relative':1e-9,'energy_relative':1e-6,'energy_absolute_J':1e-7,'momentum_relative':1e-6,'momentum_absolute_Ns':1e-9,'coordinate_difference_mm':.002,'displacement_difference_mm':2e-5,'velocity_difference_mm_ms':2e-4,'no_erosion':True,'identical_node_ids_and_topology':True},'expected_mass_g':191273837.9425,'redistributed_nodal_mass_not_assumed_pointwise_identical':True,'rotational_inertia_tensor_not_exported':True,'native_loaded_or_rotating_equivalence_requires_separate_test':True,'original_failed_A49_CHECK_remains_failed':True,'source_review':['engine/source/implicit/imp_glob_k.F','engine/source/interfaces/interf/i2_imp1.F','engine/source/constraints/general/rbe2/rbe2_imp0.F'],'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_s':40,'maximum_total_s':360,'new_installation_or_compilation':False,'source_binary_or_process_data_patch':False,'known_damage_used_as_target':False,'new_whole_duration_credit_s':0,'objective1_complete':False}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_native':True})
 pins={r['path']:r for f in ['preservation_before_metadata.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
 for f in ['artifact_manifest.json','publication_verification.json']:
  p=PREV/f;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 rows=[]
 for r in pins.values():
  st=(ROOT/r['path']).stat();assert st.st_size==r['bytes'];rows.append({**r,'mtime_ns_before':st.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'method':'Before/after metadata plus immutable old hash manifests; not new all-old-content rehash.','source_archives_not_rescanned':True})
 dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','same_external_blocker':False,'evidence':'A49 mapping complete and algebraic rigid-chain composition removed whole CHECK SIGSEGV, with15mechanical errors and49370missing-connectivity messages retained. A48+A49 published, hashes/CI checked. Native startup budget test is new and bounded.'})
 print({'A50_declared':True,'expected_native_seconds':40,'cap_seconds':180},flush=True)

def run():
 guard();c=read(CFG);d=OUT/'WHOLE_EQUIVALENT_CHAIN_EXPLICIT_STARTUP';assert not d.exists();d.mkdir();n=c['name']
 state=ROOT/c['sources'][0]['path'];assert streamsha(state)==c['sources'][0]['sha256'];target=d/state.name;shutil.copy2(state,target);assert streamsha(target)==streamsha(state)
 card=ROOT/c['sources'][2]['path'];assert streamsha(card)==c['sources'][2]['sha256'];s=card.read_text();assert s.count('/RUN/'+c['reference_name']+'/1')==1
 s=s.replace('/RUN/'+c['reference_name']+'/1','/RUN/'+n+'/1');assert '/IMPL/' not in s;(d/(n+'_0001.rad')).write_text(s,encoding='utf8')
 dump(d/'generation.json',{'created_utc':now(),'name':n,'configuration_sha256':streamsha(CFG),'whole_initial_state':rel(state),'whole_initial_state_sha256':streamsha(state),'only_Engine_card_change':'Root name in RUN','TYPE25_preserved':True,'new_physical_duration_credit_s':0})
 ok=launcher.execute(d,n);t=(d/'engine.log').read_text(errors='replace');cycles=re.search(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',t)
 dump(d/'startup_execution_review.json',{'created_utc':now(),'NORMAL_exit0':ok,'cycles':int(cycles.group(1)) if cycles else None,'no_implicit_TYPE25_ignored': 'INTERFACE TYPE 25 IS NOT AVAILABLE' not in t,'kill_or_Userbreak_seen':bool(re.search(r'USERBREAK|KILL|SIGSEGV|ABORT',t,re.I)),'whole_impact_qualified':False})
 print(read(d/'startup_execution_review.json'),flush=True)

def convert(d,n):
 en=env();en.update(OMP_NUM_THREADS='1')
 for p in sorted(d.glob(n+'T[0-9][0-9]')):
  assert not p.with_suffix('.csv').exists();win_execute(RUNTIME/'th_to_csv_win64.exe',[p.name],d,p.name+'.converter.log',60,en)
 for p in sorted(d.glob(n+'A[0-9][0-9][0-9]')):
  dest=p.with_suffix('.vtk');assert not dest.exists();t=time.perf_counter();r=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,timeout=60,env=en)
  (d/(p.name+'.converter.stderr.log')).write_bytes(r.stderr)
  dump(d/(p.name+'.converter.execution.json'),{'created_utc':now(),'exe':rel(RUNTIME/'anim_to_vtk_win64.exe'),'sha256':streamsha(RUNTIME/'anim_to_vtk_win64.exe'),'exit_code':r.returncode,'seconds':time.perf_counter()-t,'cap_s':60})
  assert r.returncode==0;dest.write_bytes(r.stdout)

def audit():
 guard();c=read(CFG);ref=OUT/'CACHED_A45_REFERENCE';assert not ref.exists();ref.mkdir()
 for r in c['sources'][3:]:
  p=ROOT/r['path'];assert streamsha(p)==r['sha256'];shutil.copy2(p,ref/p.name)
 d=OUT/'WHOLE_EQUIVALENT_CHAIN_EXPLICIT_STARTUP';convert(ref,c['reference_name']);convert(d,c['name']);a=c['acceptance'];rr=read(d/'startup_execution_review.json');checks={'native_completed_no_kill':rr['NORMAL_exit0'] and not rr['kill_or_Userbreak_seen'],'three_cycles':rr['cycles']==3,'TYPE25_not_ignored':rr['no_implicit_TYPE25_ignored']}
 p1=ref/(c['reference_name']+'T01.csv');p2=d/(c['name']+'T01.csv');hr=[];fields=[]
 if p1.exists() and p2.exists():
  H=[histories(p) for p in [p1,p2]];keys=list(H[0]);checks['same_history_channels']=keys==list(H[1]);checks['finite_histories']=all(np.isfinite(v).all() for h in H for v in h.values());checks['same_history_samples']=len(H[0]['time'])==len(H[1]['time']) and len(H[0]['time'])>0
  if checks['same_history_channels'] and checks['same_history_samples']:
   h0,h1=H;checks['same_history_times']=float(abs(h0['time']-h1['time']).max())<=a['sample_time_absolute_ms']
   mass=float(h0['MASS'][0]);scale=max(1,float(abs(h0['KINETIC ENERGY']).max())*.001);pt=max(1,float(np.linalg.norm(np.column_stack([h0[x+'-MOMENTUM'] for x in 'XYZ'])*.001,axis=1).max()))
   for key in ['MASS','ADDED MASS','KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','EXTERNAL WORK','X-MOMENTUM','Y-MOMENTUM','Z-MOMENTUM']:
    fac=.001 if key not in ['MASS','ADDED MASS'] else 1;err=float(abs(h0[key]-h1[key]).max())*fac
    tol=a['mass_relative']*mass if key=='MASS' else a['mass_scaling_relative']*mass if key=='ADDED MASS' else a['momentum_absolute_Ns']+a['momentum_relative']*pt if 'MOMENTUM' in key else a['energy_absolute_J']+a['energy_relative']*scale
    hr.append({'channel':key,'maximum_difference':err,'tolerance':tol,'pass':err<=tol});checks['history_'+key]=err<=tol
   checks['mass_budget']=float(abs(h1['MASS']-c['expected_mass_g']).max())<=a['mass_relative']*c['expected_mass_g'];checks['no_new_artificial_mass']=float(abs(h1['ADDED MASS']).max())<=a['mass_scaling_relative']*mass
 else:checks['history_conversion_available']=False
 files1=sorted(ref.glob(c['reference_name']+'A[0-9][0-9][0-9].vtk'));files2=sorted(d.glob(c['name']+'A[0-9][0-9][0-9].vtk'));checks['three_fields_each']=len(files1)==len(files2)==3
 for p,q in zip(files1,files2):
  A,B=vtk(p.read_text()),vtk(q.read_text());ids1=A['NODE_ID'].astype(int);ids2=B['NODE_ID'].astype(int);o1=np.argsort(ids1);o2=np.argsort(ids2);ck={'same_nodes':np.array_equal(ids1[o1],ids2[o2]),'finite':all(np.isfinite(v).all() for r in [A,B] for v in r.values()),'same_time':abs(A['time']-B['time'])<=a['sample_time_absolute_ms'],'same_topology':np.array_equal(A['cells'],B['cells']) and np.array_equal(A['types'],B['types'])};diffs={}
  for key,tol in [('points',a['coordinate_difference_mm']),('Displacement',a['displacement_difference_mm']),('Velocity',a['velocity_difference_mm_ms'])]:
   err=float(abs(A[key].reshape(-1,3)[o1]-B[key].reshape(-1,3)[o2]).max());ck[key]=err<=tol;diffs[key]={'maximum_difference':err,'tolerance':tol}
  ck['no_erosion']=bool(np.all(B['EROSION_STATUS']>0));masskey=next((k for k in B if k.lower()=='mass'),None)
  fields.append({'cached':rel(p),'candidate':rel(q),'time_ms':B['time'],'checks':ck,'differences':diffs,'native_nodal_mass_field':masskey,'pass':all(ck.values())})
 checks['saved_fields']=bool(fields) and all(r['pass'] for r in fields)
 result={'created_utc':now(),'checks':checks,'startup_budget_and_field_comparison_pass':all(checks.values()),'history_differences':hr,'fields':fields,'native_nodal_masses_not_assumed_pointwise_identical':True,'rotation_inertia_tensor_observed':False,'loaded_or_rotating_native_equivalence_qualified':False,'whole_impact_qualified':False,'new_whole_duration_credit_s':0}
 dump(OUT/'explicit_startup_budget_review.json',result);print({'startup_budget_and_fields_pass':result['startup_budget_and_field_comparison_pass'],'checks':checks},flush=True)

def source_review():
 guard();c=read(CFG);arc=CAND/'source.tar.gz';assert streamsha(arc)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256'];rows=[]
 with tarfile.open(arc,'r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for name in c['source_review']:
   data=tar.extractfile(members[name]).read();t=data.decode();lines=t.splitlines();rows.append({'path':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'PRINT_WKIJ_calls':[{'line':i+1,'call':s.strip()} for i,s in enumerate(lines) if 'CALL PRINT_WKIJ' in s],'raw_source_redistributed':False})
   if name.endswith('imp_glob_k.F'):
    start=t.index('      SUBROUTINE PUT_KIJ(');stop=t.index('      SUBROUTINE PRINT_WKIJ(',start);body=t[start:stop];assert body.count('IERR = 1')==2 and body.count('RETURN')>=3
    rows[-1]['missing_column_behavior']='PUT_KIJ sets IERR=1 and returns before adding the corresponding KIJ block. A missing block is not assembled as a valid zero stiffness.'
    rows[-1]['reported_node_indices']='PRINT_WKIJ prints passed NI/NJ without a label mapping; do not identify them with original /NODE labels without independent evidence.'
 dump(OUT/'remaining_condensation_source_review.json',{'created_utc':now(),'source_pin':c['source_pin'],'files':rows,'conclusion':'Completed CHECK with missing connectivity does not certify the stiffness: PUT_KIJ explicitly returns without adding a missing block. Original labels of printed indices still need mapping. No physical instability or material conclusion follows.','raw_source_redistributed':False,'software_changed':False})
 print({'remaining_condensation_source_review_saved':True,'software_patch':False},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','audit','source_review']);globals()[p.parse_args().action]()
