"""Refine the implicit startup step, then grow it while retaining exact free-motion gates."""
import probe_aircraft_a37 as native37
from probe_aircraft_a39 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha,build,ff,PARENT_CARDS
from pathlib import Path
import inspect,ast,shutil,argparse,time,json,numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a40'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a40_predeclaration.json'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a39'
CASES=[{'name':'FREE_ADAPT_I','scope':'FREE','mode':'I','dt_ms':1e-8,'maximum_dt_ms':.001,'end_ms':.1,'platform':'Linux'}, {'name':'FREE_ADAPT_HALF_I','scope':'FREE','mode':'I','dt_ms':5e-9,'maximum_dt_ms':.0005,'end_ms':.1,'platform':'Linux'}]

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A39';cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A39';assert read(PARENT/'publication_verification.json')['pass'];remote=ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a38_a39/final_remote_verification.json';assert read(remote)['pass'];partial=read(PARENT/'cached_partial_history_review.json');assert partial['checks']['full_native_energy_balance'] and not partial['checks']['physical_displacement'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a38_predeclaration.json');c.update(iteration='AIRCRAFT-A40',declared_utc=now(),seed=1102065,random_draws=0,cases=CASES,purpose='Test startup-step refinement with controlled subsequent growth against exact free translation, using frozen Linux MUMPS binary and unchanged physical gates.')
 c['parent_configuration']='wtc1_simulation_v8/data/aircraft_a38_predeclaration.json';c['parent_configuration_sha256']=streamsha(ROOT/c['parent_configuration']);c['diagnostic_variants']={'FREE_ADAPT_I':'Newmark/MUMPS unchanged; all nonlinear tolerances1e-11. Initial step1e-8ms, max .001ms; It_w4, growth1.5, maximum iterations30, decrease .5.','FREE_ADAPT_HALF_I':'Half both initial and maximum step, same growth and all physical data. Only if base normal completion and conserved sampled physical/global KE/P permit it.'}
 c['startup_accuracy_rationale']={'largest_initial_speed_mm_ms':200.,'base_initial_displacement_scale_mm':2e-6,'declared_free_displacement_tolerance_mm':c['acceptance']['free_displacement_mm'],'reason':'Initial displacement scale smaller than unchanged accuracy threshold; previously observed offset suggests startup-time refinement. No position/time offset correction is applied.'}
 c['numeric_options']={'nonlinear_tolerances':[1e-11]*3,'linear_tolerance':1e-8,'minimum_dt_ms':1e-12,'growth_target_iterations':4,'growth_factor':1.5,'maximum_nonlinear_iterations':30,'decrease_factor':.5,'Newmark_gamma_beta':[.5,.25],'actual_time_grid_must_be_reported':True};c['free'].update(animation_dt_ms=.001,history_dt_ms=.001)
 c['conditional_followup']={'half_case_only_if':'Base finishes normally and physical/global KE/P satisfy the original checks; no half case after an unphysical/aborted base.','transition_contact':'Only after complete free and half-step qualification; separately predeclare before any new execution.','no_whole_extension_from_cube':True};c['execution'].update(CPU_threads=1,GPU=False,expected_seconds=180,estimated_seconds_max=360,per_process_cap_s=180,new_installation_or_compilation=False)
 c['primary_documentation']={'startup':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dtini_engine_r.htm','adaptive_step':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_1_engine_r.htm','bounds':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_stop_engine_r.htm'};c['cached_evidence']=[{'path':rel(p),'sha256':streamsha(p)} for p in [PARENT/'cached_partial_history_review.json',PARENT/'capability_source_review.json']]
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True})
 pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PARENT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=PARENT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':['A39 registered158 and A38+A39 published with remote integrity verification','Cached native TH confirms KE/P/full balance while displacement remains shifted. Next action narrowed to startup-step refinement.'],'same_blocker_without_new_evidence':False});print({'A40_declared':True,'no_physics_patch':True},flush=True)

def cards(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode=='I':
  s=s.replace('0 123 1e-6 1e-6 1e-6','0 123 1e-11 1e-11 1e-11')
  old='/IMPL/DT/1\n'+native37.ii(2)+ff(1)+native37.ii(30)+ff(.5);assert old in s;s=s.replace(old,'/IMPL/DT/1\n'+native37.ii(4)+ff(1.5)+native37.ii(30)+ff(.5))
  old='/IMPL/DT/STOP\n'+ff(1e-8,dt);assert old in s;s=s.replace(old,'/IMPL/DT/STOP\n'+ff(1e-12,CURRENT['maximum_dt_ms']));s='/IMPL/PRINT/NONLIN/1\n'+s
 return s

def runner():
 native37.OUT=OUT;native37.CFG=CFG;native37.engine_cards=cards;s=inspect.getsource(native37.prepare_case);assert "n='A37_'" in s;s=s.replace("n='A37_'","n='A40_'");ast.parse(s);dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent':rel(Path(native37.__file__)),'parent_sha256':streamsha(Path(native37.__file__)),'derived_prepare_source':s,'changes':['A40 root and configuration only; physical fixture unchanged','Predeclared nonlinear tolerance and adaptive timestep controls'],'compiled_solver_modified':False});native37.__file__=__file__;exec(compile(s,__file__+'::prepare','exec'),native37.__dict__)

def run():
 global CURRENT
 guard();runner();rows=[]
 for c in CASES:
  CURRENT=c;native37.start_case(c);native37.audit_case(c);r=read(OUT/c['name']/'review.json');rows.append(r)
  needed=['full_native_energy_balance','physical_nodal_KE_matches_global','physical_nodal_P_matches_global','closed_momentum']
  if not r['checks']['native_completed'] or not r['histories'] or not all(all(h['checks'][k] for k in needed) for h in r['histories']):break
 dump(OUT/'native_review.json',{'created_utc':now(),'cases':rows,'passing_variants':[r['case']['name'] for r in rows if r['pass']],'whole_impact_qualified':False});print({'cases':len(rows),'passes':sum(r['pass'] for r in rows)},flush=True)

def preserve():
 from finalize_aircraft_a22 import verify_files
 guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True});print({'preserved_old_files':n},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','preserve']);globals()[p.parse_args().action]()
