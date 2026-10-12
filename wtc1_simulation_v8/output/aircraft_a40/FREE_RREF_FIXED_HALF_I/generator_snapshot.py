"""Separate variable-step predictor lag from the reference-floor correction."""
import probe_aircraft_a40_reference as reference
import probe_aircraft_a40 as experiment
from probe_aircraft_a40 import *
CASES=[{'name':'FREE_RREF_FIXED_I','scope':'FREE','mode':'I','dt_ms':.001,'maximum_dt_ms':.001,'end_ms':.1,'platform':'Linux','nonlinear_tolerance':1e-11}, {'name':'FREE_RREF_FIXED_HALF_I','scope':'FREE','mode':'I','dt_ms':.0005,'maximum_dt_ms':.0005,'end_ms':.1,'platform':'Linux','nonlinear_tolerance':1e-11}]

def declare():
 guard();p=OUT/'fixed_step_predeclaration.json';assert not p.exists();r=read(OUT/'reference_floor_review.json');assert len(r['cases'])==2 and all(x['checks']['native_completed'] and not x['pass'] for x in r['cases'])
 dump(p,{'created_utc':now(),'seed':1102065,'random_draws':0,'before_new_native':True,'parent_configuration_sha256':streamsha(CFG),'cases':CASES,'trigger':'Both floor/adaptive calculations complete and preserve reported energy, but during growth1.5 their nodal velocity becomesV0/1.5 then returns toV0 after reaching maximum dt; displacement offset persists. Test whether fixed time step with the same reference floor removes that lag.','change_from_floor_adaptive':'Set initial step equal to maximum step, factor of increase1. No applied loads, altered states, time shift, materials, masses or physical acceptance changes.','nonlinear_tolerances':[1e-11]*3,'reference_floor_force_N':1.,'reference_max':1e30,'minimum_dt_ms':1e-12,'branch_rule':'Fixed baseline first, half-time-step only if baseline passes complete original physical gates. No transition/contact from failed free route.','CPU_threads':1,'GPU':False,'per_process_cap_s':180,'maximum_seconds_both':360,'no_solver_source_or_binary_change':True})

def cards(n,index,mode,dt,end,scope,check=False):
 s=reference.cards(n,index,mode,dt,end,scope,check)
 if mode=='I':
  old='/IMPL/DT/1\n'+native37.ii(4)+ff(1.5)+native37.ii(30)+ff(.5);assert old in s;s=s.replace(old,'/IMPL/DT/1\n'+native37.ii(4)+ff(1.)+native37.ii(30)+ff(.5))
 return s

def run():
 guard();assert read(OUT/'fixed_step_predeclaration.json')['before_new_native'];native37.OUT=OUT;native37.CFG=CFG;native37.__file__=__file__;s=read(OUT/'runner_derivation.json')['derived_prepare_source'];exec(compile(s,__file__+'::prepare','exec'),native37.__dict__);native37.engine_cards=cards;rows=[]
 for c in CASES:
  reference.CURRENT=c;experiment.CURRENT=c;native37.start_case(c);native37.audit_case(c);r=read(OUT/c['name']/'review.json');rows.append(r)
  if not r['pass']:break
 dump(OUT/'fixed_step_review.json',{'created_utc':now(),'cases':rows,'passing_variants':[r['case']['name'] for r in rows if r['pass']],'whole_impact_qualified':False});print({'fixed_cases':len(rows),'passes':sum(r['pass'] for r in rows)},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
