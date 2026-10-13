"""Explain preserved half-step failure from exact Newmark dispersion, no fitting."""
from free_aircraft_a63_cohesive import ROOT,OUT,CFG,engine,read,dump,now
import numpy as np,json

def main():
    engine();c=read(CFG);r=read(OUT/'free_cohesive_qualification_review.json');assert all(x['pass'] for x in r['cases']) and not r['pass']
    omega=c['analytical_reference']['omega_per_ms'];K0=c['analytical_reference']['initial_energy_J'];limit=r['half_dt_energy_comparisons'][0]['tolerance_J'];grid=np.linspace(0,1,200001);cases=[]
    for dt in [.001,.0005,.00025,.000125,.0000625]:
        w1=2*np.arctan(omega*dt/2)/dt;w2=2*np.arctan(omega*dt/4)/(dt/2);delta=abs(w1-w2);bound=K0*abs(np.sin(delta))
        exact=float(abs(K0*np.cos(w1*grid)**2-K0*np.cos(w2*grid)**2).max());cases.append({'dt_ms':dt,'half_dt_ms':dt/2,'frequency_per_ms':float(w1),'phase_lag_at1ms_rad':float(omega-w1),'half_dt_phase_difference_at1ms_rad':float(delta),'half_dt_energy_difference_bound_J':float(bound),'dense_exact_linear_energy_difference_J':exact,'same_predeclared_tolerance_J':limit,'bound_pass':bool(bound<=limit)})
    next_pair=next(x for x in cases if x['bound_pass'])
    dump(OUT/'dispersion_and_next_step_review.json',{'created_utc':now(),'source_model':'Exact average-acceleration Newmark linear oscillator; all parameters taken from predeclared area/ET/mass. No native parameter fit, no damage/history target.',
      'each_native_run_matches_its_exact_discrete_solution':True,'overall_half_dt_failed_gate_preserved':True,'observed_native_max_difference_J':max(x['maximum_difference_J'] for x in r['half_dt_energy_comparisons']),
      'declared_tolerance_J':limit,'candidates':cases,'proposed_next_pair_dt_ms':[next_pair['dt_ms'],next_pair['half_dt_ms']],
      'A62_A63_authorized_Engine_runs_consumed':12,'new_Engine_runs':0,'new_software_or_compilation':False,'coupled_impact_dt_not_inferred_from_instrument_mass':True,'whole_credit_s':0})
    print(json.dumps({'half_dt_failure_preserved':True,'proposed_pair_ms':[next_pair['dt_ms'],next_pair['half_dt_ms']],'new_native_runs':0}),flush=True)

if __name__=='__main__':main()
