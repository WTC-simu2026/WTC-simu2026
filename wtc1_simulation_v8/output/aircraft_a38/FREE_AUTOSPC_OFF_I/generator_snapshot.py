"""One-factor native startup diagnoses; no rebuild or physical input fitting."""
import probe_aircraft_a37 as native37
from probe_aircraft_a37 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha,build,ff
from pathlib import Path
import inspect,ast,shutil,argparse,time,json
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a38'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a38_predeclaration.json'
CASES=[{'name':'FREE_'+v+'_I','scope':'FREE','mode':'I','dt_ms':.001,'variant':v} for v in ['AUTOSPC_OFF','PCG','HHT']]
DOCS={'autospc':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_autospc_engine_r.htm','solver':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_solver_engine_r.htm','HHT':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_1_engine_r.htm'}
PARENT_OUT=native37.OUT;PARENT_CFG=native37.CFG;PARENT_CARDS=native37.engine_cards

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A37';s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_count']==0 and cy['last_published_iteration']=='AIRCRAFT-A37'
 publication=ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a36_a37/final_remote_verification.json';assert read(publication)['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 c=read(PARENT_CFG);c.update(iteration='AIRCRAFT-A38',declared_utc=now(),seed=1102063,random_draws=0,cases=CASES,purpose='Isolate startup failure by changing only one algorithmic option per fresh free witness, then conditional full native transition/contact of a passing route.',parent_configuration=rel(PARENT_CFG),parent_configuration_sha256=streamsha(PARENT_CFG),parent_source=rel(Path(native37.__file__)),parent_source_sha256=streamsha(Path(native37.__file__)),primary_documentation=DOCS)
 c['diagnostic_variants']={'AUTOSPC_OFF':'Newmark/MUMPS unchanged; only /IMPL/AUTOSPC/OFF','PCG':'Newmark unchanged; only /IMPL/SOLVER/1 with same Jacobi2, tolerance1e-8','HHT':'MUMPS unchanged; only /IMPL/DYNA/1 alpha=-.05, documented HHT default; algorithmic damping acknowledged, exact free IE/P/KE still required'}
 c['baseline']={'cached_case':rel(PARENT_OUT/'FREE_I'),'expected':'Exact unforced translation X=X0+tV0, V=V0, KE=.05564031J, Pconstant, IEzero','successful_native_rerun':False}
 c['conditional_followup']={'only_if_direct_free_pass':'Same option half dt, then same-option EE/EI free and active-contact transition with both original time steps; fresh states only','winner_order':['AUTOSPC_OFF','PCG','HHT'],'no_route_selected_from_known_damage':True,'failed_branch_stopped':True}
 c['execution'].update(expected_seconds=180,estimated_seconds_max=2700,per_process_cap_s=180,new_installation_or_compilation=False)
 source_files=['engine/source/input/freimpl.F','engine/source/implicit/imp_dyna.F','engine/source/implicit/imp_solv.F','engine/source/implicit/integrator.F']
 c['source_inspection']=[{'path':rel(build.CAND/'source'/f),'sha256':streamsha(build.CAND/'source'/f),'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{f}','raw_source_redistributed':False} for f in source_files]
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native':True})
 pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PARENT_OUT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=PARENT_OUT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':['A37 sealed and registered156 entries','A36+A37 release and two successful CI, final_remote_verification PASS'],'same_blocker_without_new_evidence':False});print({'A38_declared':True,'cases':len(CASES),'no_rebuild':True},flush=True)

def cards(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode!='I':return s
 v=VARIANT
 if v=='AUTOSPC_OFF':s='/IMPL/AUTOSPC/OFF\n'+s
 elif v=='PCG':assert '/IMPL/SOLVER/2' in s;s=s.replace('/IMPL/SOLVER/2','/IMPL/SOLVER/1')
 elif v=='HHT':a='/IMPL/DYNA/2\n'+ff(.5,.25);assert a in s;s=s.replace(a,'/IMPL/DYNA/1\n'+ff(-.05))
 else:raise ValueError(v)
 return s

def install_runner():
 native37.OUT=OUT;native37.CFG=CFG
 s=inspect.getsource(native37.prepare_case);assert "n='A37_'" in s;s=s.replace("n='A37_'","n='A38_'");ast.parse(s)
 dump(OUT/'runner_derivation.json',{'created_utc':now(),'parent_source':read(CFG)['parent_source'],'parent_sha256':read(CFG)['parent_source_sha256'],'changes':['New A38 output root/configuration','native root A37_ to A38_ only','One declared Engine option per case; physics fixture retained'],'derived_prepare_source':s,'compiled_solver_modified':False})
 native37.__file__=__file__;exec(compile(s,__file__+'::prepare','exec'),native37.__dict__);native37.engine_cards=cards

def run():
 global VARIANT
 guard();install_runner();rows=[]
 for c in CASES:
  VARIANT=c['variant'];native37.start_case(c);native37.audit_case(c);r=read(OUT/c['name']/'review.json');rows.append(r)
  print({'variant':VARIANT,'pass':r['pass']},flush=True)
 dump(OUT/'startup_review.json',{'created_utc':now(),'cases':rows,'cached_baseline':rel(PARENT_OUT/'FREE_I/review.json'),'passing_variants':[r['case']['variant'] for r in rows if r['pass']],'same_physical_fixture':True,'full_transition_qualified':False,'whole_qualified':False})

def preserve():
 from finalize_aircraft_a22 import verify_files
 guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True});print({'preserved_old_files':n},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','preserve']);globals()[p.parse_args().action]()
