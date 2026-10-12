"""Direct implicit contact and source-defined distinction between secant and Newmark velocities."""
import probe_aircraft_a37 as native37
from probe_aircraft_a40 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha,build,ff,PARENT_CARDS
from pathlib import Path
import inspect,ast,shutil,argparse,json,time,numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a41'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a40'
CASES=[{'name':'CONTACT_RREF_DIRECT_BASE','scope':'CONTACT','mode':'I','dt_ms':.00005,'platform':'Linux'}, {'name':'CONTACT_RREF_DIRECT_HALF','scope':'CONTACT','mode':'I','dt_ms':.000025,'platform':'Linux'}]

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A40';cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_iterations']==['AIRCRAFT-A40'];assert read(PARENT/'publication_verification.json')['pass'];a=read(PARENT/'scientific_assessment.json');assert a['fixed_free_qualified_in_declared_scope'] and not a['active_contact_restart_qualified'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a40_predeclaration.json');c.update(iteration='AIRCRAFT-A41',declared_utc=now(),seed=1102066,random_draws=0,cases=CASES,purpose='Compare contact begun directly implicit with cached active-contact E-to-I A40; interpret output velocities from pinned code, without modifying software or physical inputs.',parent_configuration=rel(ROOT/'wtc1_simulation_v8/data/aircraft_a40_predeclaration.json'),parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a40_predeclaration.json'))
 c['numeric_options']={'nonlinear_tolerances':[1e-11]*3,'linear_tolerance':1e-8,'minimum_dt_ms':1e-12,'growth_factor':1.,'force_reference_min_N':1.,'force_reference_max':1e30,'Newmark_gamma_beta':[.5,.25],'no_adaptive_growth':True,'NEXP_default_from_pinned_input':1,'NDT_source_assignment':'NDT=NEXP in IMP_SOLV; no mixed explicit partition in this fixture'}
 c['output_velocity_interpretation']={'direct_source_fact':'INTEGRATOR calls INTE_DYNA, then overwrites V with D/(DT2*NDT); THNOD publishes V. ECRIT derives kinetic velocity DY_V-DT05*DY_A.','legacy_tests_preserved':'Original raw instantaneous-velocity KE/P checks remain as separate diagnostics; they must not define field semantics contrary to pinned source.','derived_fixed_Newmark_velocity':'For gamma=.5,beta=.25, fixed dt, all cycles sampled, NDT1 and source initial acceleration0: trueV[n]=2*secantV[n]-trueV[n-1]. Independently check displacement increments/times, native global KE/P and contact-force impulse conventions. No corrected fields are injected into solver or restart.','conditions_required':['initial geometry separated, no applied force/contact at t0','record every actual native cycle','fixed timestep, NDT1','source-defined temporal derivation, original physical thresholds','fail reconstruction if grid/kinematic conditions do not hold']}
 c['contact'].update(animation_dt_ms=.00005,history_dt_ms=.00005);c['execution'].update(CPU_threads=1,GPU=False,expected_seconds=180,estimated_seconds_max=360,per_process_cap_s=180,new_installation_or_compilation=False)
 c['conditional_followup']={'both_direct_steps':'Base and half assess conservation and convergence; no whole extension unless source-consistent physical gates pass.','model_check':'Separate cached-state free /IMPL/CHECK capability test before attributing prior whole-check abort to TYPE25.','old_successful_native_reruns':False};c['primary_documentation']={'Newmark':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_2_engine_r.htm','model_check':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_check_engine_r.htm'}
 source_files=['engine/source/implicit/integrator.F','engine/source/implicit/imp_dyna.F','engine/source/implicit/imp_solv.F','engine/source/output/th/thnod.F','engine/source/output/ecrit.F','engine/source/output/restart/wrrest.F'];c['source_inspection']=[{'path':rel(build.CAND/'source'/f),'sha256':streamsha(build.CAND/'source'/f),'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{f}','raw_source_redistributed':False} for f in source_files]
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True});pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PARENT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=PARENT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':['A40 registered159 and four fixed free/direct or restart sets passed','Source INTEGRATOR/THNOD/ECRIT distinguishes output secant velocity and true Newmark kinetic velocity.'],'same_blocker_without_new_evidence':False});print({'A41_declared':True,'source_velocity_convention_recorded':True},flush=True)

def cards(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode=='I':
  s=s.replace('0 123 1e-6 1e-6 1e-6','0 123 1e-11 1e-11 1e-11').replace('/IMPL/DT/STOP\n'+ff(1e-8,dt),'/IMPL/DT/STOP\n'+ff(1e-12,dt));s='/IMPL/RREF/LIMIT\n'+ff(1.,1e30)+'\n/IMPL/PRINT/NONLIN/1\n'+s
  if not check:s=s.replace('/TFILE/4\n'+ff(read(CFG)[scope.lower()]['history_dt_ms']),'/TFILE/4\n'+ff(dt))
 return s

def runner():
 native37.OUT=OUT;native37.CFG=CFG;native37.engine_cards=cards;s=inspect.getsource(native37.prepare_case);assert "n='A37_'" in s;s=s.replace("n='A37_'","n='A41_'");ast.parse(s);dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent':rel(Path(native37.__file__)),'parent_sha256':streamsha(Path(native37.__file__)),'derived_prepare_source':s,'physical_fixture_unchanged':True,'source_or_binary_patch':False});native37.__file__=__file__;exec(compile(s,__file__+'::prepare','exec'),native37.__dict__)

def run():
 guard();runner();rows=[]
 for c in CASES:
  native37.start_case(c);native37.audit_case(c);rows.append(read(OUT/c['name']/'review.json'))
 dump(OUT/'native_review.json',{'created_utc':now(),'cases':rows,'raw_instantaneous_velocity_assumption_preserved':True,'whole_impact_qualified':False});print({'A41_direct_cases':len(rows),'legacy_passes':sum(r['pass'] for r in rows)},flush=True)

def preserve():
 from finalize_aircraft_a22 import verify_files
 guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True});print({'preserved_old_files':n},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','preserve']);globals()[p.parse_args().action]()
