"""Test a documented residual-reference floor, retaining physical data and acceptance gates."""
import probe_aircraft_a40 as experiment
from probe_aircraft_a40 import *
STRICT={'name':'FREE_RREF_ADAPT_I','scope':'FREE','mode':'I','dt_ms':1e-8,'maximum_dt_ms':.001,'end_ms':.1,'platform':'Linux','nonlinear_tolerance':1e-11}
HALF={**STRICT,'name':'FREE_RREF_ADAPT_HALF_I','dt_ms':5e-9,'maximum_dt_ms':.0005}
STANDARD={**STRICT,'name':'FREE_RREF_STANDARD_ADAPT_I','nonlinear_tolerance':1e-6}
STANDARD_HALF={**HALF,'name':'FREE_RREF_STANDARD_ADAPT_HALF_I','nonlinear_tolerance':1e-6}

def declare():
 guard();p=OUT/'reference_floor_predeclaration.json';assert not p.exists();base=read(OUT/'FREE_ADAPT_I/review.json');assert not base['checks']['native_completed'];s=(OUT/'FREE_ADAPT_I/phase1/A40_FREE_ADAPT_I_0001.out').read_text();assert 'TIMESTEP LIMIT' in s and 'Infinity' in s
 files=['engine/source/input/freimpl.F','engine/source/implicit/imp_solv.F','engine/source/implicit/nl_solv.F']
 dump(p,{'created_utc':now(),'seed':1102065,'random_draws':0,'before_new_native':True,'parent_configuration_sha256':streamsha(CFG),'cases':[STRICT,HALF,STANDARD,STANDARD_HALF],'trigger':'Base strict adaptive startup fails before any completed cycle; trace first relative residual grows to9.956e27 with Infinity energy ratio, despite near-zero unforced reference. Source RF_MIN floor is available through /IMPL/RREF/LIMIT, independently of physical loads.','reference_minimum_force':{'original_unit':'g mm/ms^2','value':1.,'SI_force_N':1.,'conversion':'0.001kg*0.001m/(0.001s)^2 =1N','maximum_force':1e30,'reason':'Explicit normalization scale for a force-free exact witness, no applied load. Strict force tolerance1e-11 implies nominal absolute1e-11N; standard relative1e-6 option, if needed, is the original A37 tolerance. All external physical gates remain original.'},'branch_rule':'Strict floor witness first. If it passes, half-step strict witness. If it fails, standard relative tolerance (the original A37 value) at same floor and timestep; if that passes, its half-step. No contact/whole extension from failed free route.','source_files':[{'path':rel(build.CAND/'source'/f),'sha256':streamsha(build.CAND/'source'/f),'url':f'https://github.com/gabrielrussell/OpenRadioss/blob/{build.PIN}/{f}'} for f in files],'documentation':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_rref_limit_engine_r.htm','physical_inputs_changed':False,'physical_gates_changed':False,'new_installation_or_build':False,'no_time_or_position_shift_applied':True,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'maximum_seconds_all_four':720})
 print({'reference_floor_declared':True},flush=True)

def cards(n,index,mode,dt,end,scope,check=False):
 s=experiment.cards(n,index,mode,dt,end,scope,check)
 if mode=='I':
  if CURRENT['nonlinear_tolerance']==1e-6:s=s.replace('0 123 1e-11 1e-11 1e-11','0 123 1e-6 1e-6 1e-6')
  s='/IMPL/RREF/LIMIT\n'+ff(1.,1e30)+'\n'+s
 return s

def run_one(c):
 global CURRENT
 CURRENT=c;experiment.CURRENT=c;native37.start_case(c);native37.audit_case(c);return read(OUT/c['name']/'review.json')

def run():
 guard();assert read(OUT/'reference_floor_predeclaration.json')['before_new_native'];native37.OUT=OUT;native37.CFG=CFG;native37.__file__=__file__;s=read(OUT/'runner_derivation.json')['derived_prepare_source'];exec(compile(s,__file__+'::prepare','exec'),native37.__dict__);native37.engine_cards=cards
 rows=[run_one(STRICT)]
 if rows[-1]['pass']:rows.append(run_one(HALF))
 else:
  rows.append(run_one(STANDARD))
  if rows[-1]['pass']:rows.append(run_one(STANDARD_HALF))
 dump(OUT/'reference_floor_review.json',{'created_utc':now(),'cases':rows,'passing_variants':[r['case']['name'] for r in rows if r['pass']],'whole_impact_qualified':False});print({'reference_cases':len(rows),'passes':sum(r['pass'] for r in rows)},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
