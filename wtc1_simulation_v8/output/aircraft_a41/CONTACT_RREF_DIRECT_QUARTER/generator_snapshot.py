"""Conditional temporal refinement of the source-consistent direct-contact branch."""
import probe_aircraft_a41 as experiment
from probe_aircraft_a41 import *
from read_aircraft_a41_newmark import review
from probe_aircraft_a37 import histories
CASES=[{'name':'CONTACT_RREF_DIRECT_'+name,'scope':'CONTACT','mode':'I','dt_ms':.000025/(2**k),'platform':'Linux'} for k,name in enumerate(['QUARTER','EIGHTH','SIXTEENTH','THIRTYSECOND'],1)]

def declare():
 guard();p=OUT/'temporal_refinement_predeclaration.json';assert not p.exists();assert read(OUT/'CONTACT_RREF_DIRECT_HALF/newmark_velocity_review.json')['pass']
 dump(p,{'created_utc':now(),'seed':1102066,'random_draws':0,'before_new_native':True,'parent_configuration_sha256':streamsha(CFG),'cases':CASES,'trigger':'Direct contact half-step passes physical gates after source-defined Newmark velocity interpretation; convergence of wave/energy components still required.','branch_rule':'Start quarter, compare with preceding qualified half. Continue halving only if new physical gates pass but original0.5percent+1e-7J component convergence fails. Stop at first converged pair, physical failure, native failure or fourth declared refinement.','original_half_step_energy_gate':{'relative_to_initial_KE':.005,'absolute_J':1e-7,'components':['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']},'physical_inputs_changed':False,'physical_gates_changed':False,'numeric_options_unchanged_except_fixed_step':True,'history_every_actual_requested_step':True,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'maximum_seconds_four':720,'no_software_change':True,'no_historical_damage_target':True})

def compare(a,b):
 def H(n):return histories(next((OUT/n/'phase1').glob('*.csv')))
 x,y=H(a),H(b);lo=max(x['time'][0],y['time'][0]);hi=min(x['time'][-1],y['time'][-1]);T=x['time'][(x['time']>=lo)&(x['time']<=hi)];K0=read(OUT/a/'generation.json')['kinetic_energy_J'];tol=.005*K0+1e-7;items={}
 for key in ['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']:
  err=float(abs(np.interp(T,x['time'],x[key])-np.interp(T,y['time'],y[key])).max())*.001;items[key]={'maximum_J':err,'tolerance_J':tol,'pass':err<tol}
 return {'cases':[a,b],'first_ms':float(T[0]),'last_ms':float(T[-1]),'samples':len(T),'components':items,'pass':all(q['pass'] for q in items.values())}

def run():
 guard();assert read(OUT/'temporal_refinement_predeclaration.json')['before_new_native'];native37.OUT=OUT;native37.CFG=CFG;native37.engine_cards=experiment.cards;native37.__file__=__file__;s=read(OUT/'runner_derivation.json')['derived_prepare_source'];exec(compile(s,__file__+'::prepare','exec'),native37.__dict__);rows=[];comparisons=[];previous='CONTACT_RREF_DIRECT_HALF'
 for c in CASES:
  native37.start_case(c);native37.audit_case(c);raw=read(OUT/c['name']/'review.json');item={'case':c['name'],'native_review':raw}
  if raw['checks']['native_completed']:
   physical=review(c);item['physical_review']=physical
   if physical['pass']:
    comparison=compare(previous,c['name']);comparisons.append(comparison);item['comparison']=comparison
  rows.append(item);dump(OUT/'temporal_refinement_progress.json',{'created_utc':now(),'cases':rows,'comparisons':comparisons})
  if not item.get('physical_review',{}).get('pass') or item.get('comparison',{}).get('pass'):break
  previous=c['name']
 dump(OUT/'temporal_refinement_review.json',{'created_utc':now(),'cases':rows,'comparisons':comparisons,'converged_pair':next((q['cases'] for q in comparisons if q['pass']),None),'whole_impact_qualified':False});print({'refinements':len(rows),'converged_pair':next((q['cases'] for q in comparisons if q['pass']),None)},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
