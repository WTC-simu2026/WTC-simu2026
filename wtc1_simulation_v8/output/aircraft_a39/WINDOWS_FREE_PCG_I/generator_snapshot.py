"""Coherent Windows PCG startup compared with cached mixed-platform A38 controls."""
import probe_aircraft_a37 as native37
from probe_aircraft_a38 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha,build,ff,PARENT_CARDS
from pathlib import Path
import inspect,ast,shutil,argparse,json,time,numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a39'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a39_predeclaration.json'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a38'
CASES=[{'name':'WINDOWS_FREE_PCG_I','scope':'FREE','mode':'I','platform':'Windows','dt_ms':.001,'end_ms':.1,'tolerance':1e-6}, {'name':'WINDOWS_FREE_TIGHT_PCG_I','scope':'FREE','mode':'I','platform':'Windows','dt_ms':.001,'end_ms':.004,'tolerance':1e-11}]

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def cache_audit():
 rows=[]
 for p in sorted((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a*_predeclaration.json')):
  try:i=int(p.name.split('_')[1][1:])
  except ValueError:continue
  if not 28<=i<=38:continue
  c=read(p);cases=c.get('cases',[]);cases=list(cases.values()) if isinstance(cases,dict) else cases
  matches=[x for x in cases if isinstance(x,dict) and x.get('platform')=='Windows' and 'FREE' in x.get('name','').upper() and (x.get('solver_N',0)>0 or x.get('mode')=='I')]
  rows.append({'path':rel(p),'sha256':streamsha(p),'coherent_Windows_implicit_free_cases':matches})
 assert not any(r['coherent_Windows_implicit_free_cases'] for r in rows)
 return {'created_utc':now(),'configs':rows,'same_control_already_present':False,'earlier_A24_free_controls_explicit_not_this_implicit_fixture':True,'A36_Windows_translation_prescribed_explicit_not_free_initial_velocity':True}

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A38';st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_iterations']==['AIRCRAFT-A38'];assert read(PARENT/'publication_verification.json')['pass'];audit=cache_audit();OUT.mkdir();dump(OUT/'harness_before.json',h);dump(OUT/'cache_audit.json',audit)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a38_predeclaration.json');c.update(iteration='AIRCRAFT-A39',declared_utc=now(),seed=1102064,random_draws=0,cases=CASES,purpose='Compare coherent Windows Starter/Engine with cached fresh-Windows-Starter/Linux-Engine PCG A38, without changing physical fixture.',parent_configuration='wtc1_simulation_v8/data/aircraft_a38_predeclaration.json',parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a38_predeclaration.json'))
 c['diagnostic_variants']={'WINDOWS_FREE_PCG_I':'Same PCG/Jacobi/Newmark/time step/nonlinear criteria as cached Linux PCG A38. Both binaries now same Windows release. Platform/compiler/source version change together; differential does not uniquely identify a cause.','WINDOWS_FREE_TIGHT_PCG_I':'Conditional if first witness fails: same Windows PCG, nonlinear tolerances1e-11; .004ms declared diagnostic duration, animation every .001ms. This differs from cached Linux MUMPS tight in linear solver and duration too; do not assert a pure platform cause.'}
 c['conditional_followup']={'if_direct_pass':'Declare half-time-step plus full-state explicit-to-implicit/contact separately before execution.','if_direct_fail':'Run only declared short strict-tolerance witness; no contact or whole extension.','no_route_selected_from_known_damage':True};c['execution'].update(expected_seconds=180,estimated_seconds_max=360,per_process_cap_s=180,new_installation_or_compilation=False)
 c['binaries']=[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in [RUNTIME/'starter_win64.exe',RUNTIME/'engine_win64.exe',build.CAND/'isolated_exec/engine_linux64_gf_ompi']];c['cached_comparisons']=[rel(PARENT/'FREE_PCG_I/review.json'),rel(PARENT/'FREE_TIGHT_I/review.json'),rel(PARENT/'endpoint_addendum.json')]
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True})
 pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PARENT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=PARENT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':['A38 registered157,344newfiles and26488oldfiles verified','Native absolute-stop shortcut evidenced; removing it restores sampled velocity but fails global KE and displacement.'],'same_blocker_without_new_evidence':False});print({'A39_declared':True,'no_install_or_build':True},flush=True)

def cards(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode=='I':
  s=s.replace('/IMPL/SOLVER/2','/IMPL/SOLVER/1');token='0 123 1e-6 1e-6 1e-6';assert token in s
  s=s.replace(token,'0 123 '+' '.join(str(CURRENT['tolerance']) for i in range(3)))
  if CURRENT['tolerance']<1e-10:s=s.replace('/ANIM/DT\n'+ff(0,.01),'/ANIM/DT\n'+ff(0,.001))
  s='/IMPL/PRINT/NONLIN/1\n'+s
 return s

def runner():
 native37.OUT=OUT;native37.CFG=CFG;native37.engine_cards=cards
 s=inspect.getsource(native37.prepare_case);replacements={"n='A37_'":"n='A39_'","'platform':'Linux'":"'platform':case['platform']","end=q['end_ms'] if mode=='I'":"end=case.get('end_ms',q['end_ms']) if mode=='I'"}
 for a,b in replacements.items():assert a in s;s=s.replace(a,b)
 ast.parse(s);dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent':rel(Path(native37.__file__)),'parent_sha256':streamsha(Path(native37.__file__)),'replacement_map':replacements,'derived_prepare_source':s,'physics_unchanged':True});native37.__file__=__file__;exec(compile(s,__file__+'::prepare','exec'),native37.__dict__)

def run():
 global CURRENT
 guard();runner();rows=[]
 for c in CASES:
  CURRENT=c;native37.start_case(c);native37.audit_case(c);r=read(OUT/c['name']/'review.json');rows.append(r)
  if r['pass']:break
 dump(OUT/'native_review.json',{'created_utc':now(),'cases':rows,'passing_variants':[r['case']['name'] for r in rows if r['pass']],'whole_impact_qualified':False});print({'cases':len(rows),'passes':sum(r['pass'] for r in rows)},flush=True)

def preserve():
 from finalize_aircraft_a22 import verify_files
 guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True});print({'preserved_old_files':n},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','preserve']);globals()[p.parse_args().action]()
