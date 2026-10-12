"""Continue only not-yet-executed refinements after source-based timestamp QA."""
import probe_aircraft_a41 as experiment
from probe_aircraft_a41 import *
from refine_aircraft_a41 import CASES,compare
from read_aircraft_a41_newmark import review

def declare():
 guard();p=OUT/'refinement_continuation_predeclaration.json';assert not p.exists();assert read(OUT/'CONTACT_RREF_DIRECT_EIGHTH/newmark_velocity_time_precision_review.json')['pass'];assert not read(OUT/'cached_quarter_eighth_comparison.json')['pass'];assert all(not (OUT/c['name']).exists() for c in CASES[2:]);dump(p,{'created_utc':now(),'seed':1102066,'before_new_native':True,'cases':CASES[2:],'original_refinement_plan_preserved':True,'reason':'Eighth physical gates pass after documented time-printing QA; cached quarter/eighth component convergence still fails. Continue only the two finer cases already declared, retaining original physical/convergence thresholds.','time_QA_protocol':'Nominal timestamp sequence plus native cycles and actual printed steps, no resampling or time shift applied.','stop':'First converged pair or physical/native failure, at most two processes capped180s each','no_old_solver_replay':True,'no_software_or_physical_input_change':True})

def run():
 guard();assert read(OUT/'refinement_continuation_predeclaration.json')['before_new_native'];native37.OUT=OUT;native37.CFG=CFG;native37.engine_cards=experiment.cards;native37.__file__=__file__;s=read(OUT/'runner_derivation.json')['derived_prepare_source'];exec(compile(s,__file__+'::prepare','exec'),native37.__dict__);rows=[];pairs=[];previous='CONTACT_RREF_DIRECT_EIGHTH'
 for c in CASES[2:]:
  native37.start_case(c);native37.audit_case(c);raw=read(OUT/c['name']/'review.json');row={'case':c['name'],'native_review':raw}
  if raw['checks']['native_completed']:
   physical=review(c,True);row['physical_review']=physical
   if physical['pass']:q=compare(previous,c['name']);row['comparison']=q;pairs.append(q)
  rows.append(row);dump(OUT/'refinement_continuation_progress.json',{'created_utc':now(),'cases':rows,'comparisons':pairs})
  if not row.get('physical_review',{}).get('pass') or row.get('comparison',{}).get('pass'):break
  previous=c['name']
 dump(OUT/'refinement_continuation_review.json',{'created_utc':now(),'cases':rows,'comparisons':pairs,'converged_pair':next((q['cases'] for q in pairs if q['pass']),None),'whole_impact_qualified':False});print({'new_refinements':len(rows),'converged_pair':next((q['cases'] for q in pairs if q['pass']),None)},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
