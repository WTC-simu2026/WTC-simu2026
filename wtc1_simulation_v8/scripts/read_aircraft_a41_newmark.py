"""Source-defined endpoint velocity from complete fixed-step secant histories; no solver injection."""
from probe_aircraft_a41 import *
from probe_aircraft_a37 import histories
from assess_aircraft_a23_reader_precision import printed_bound

def review(c, time_precision=False):
 d=OUT/c['name'];g=read(d/'generation.json');p=d/'phase1';H=histories(next(p.glob('*.csv')));T=H['time'];keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];ids=[int(k.split()[1]) for k in keys][::6];F=np.column_stack([H[k] for k in keys]).reshape(len(T),len(ids),6)[:,np.argsort(ids),:];U=F[:,:,:3];sec=F[:,:,3:];V0=np.asarray(g['initial_velocity_mm_ms']);m=np.asarray(g['nodal_masses_g']);dt=c['dt_ms'];grid=bool(T[0]==0 and np.max(abs(np.diff(T)-dt))<dt*1e-6);identity_error=np.diff(U,axis=0)/dt-sec[1:];bounds=(printed_bound(U[1:])+printed_bound(U[:-1]))/dt+printed_bound(sec[1:])+1e-6;kinematic=bool(np.all(abs(identity_error)<=bounds));initial=bool(np.max(abs(sec[0]-V0))<2e-4)
 literal_grid=grid
 if time_precision:
  import re
  log=(p/'engine.log').read_text();cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',log).group(1));printed_dt=[float(x) for x in re.findall(r' NC=.*? DT=\s*([\d.E+\-]+)',log)];nominal=np.arange(len(T))*dt;time_bound=printed_bound(T)+4*np.finfo(np.float32).eps*abs(T)+1e-12
  grid=bool(T[0]==0 and np.all(abs(T-nominal)<=time_bound) and abs(cycles-len(T))<=1 and printed_dt and all(abs(h-dt)<=dt*1e-5 for h in printed_dt))
 true=np.empty_like(sec);true[0]=V0
 for i in range(1,len(T)):true[i]=2*sec[i]-true[i-1]
 K=.5*np.sum(m[None,:,None]*true**2,axis=(1,2))*.001;P=np.sum(m[None,:,None]*true,axis=1)*.001;K0=g['kinetic_energy_J'];P0=np.asarray(g['momentum_Ns']);pt=.02*np.sum(m[:,None]*abs(V0))*.001+1e-9;et=.02*K0+1e-7;other=['ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=K+sum(H[k] for k in other)*.001;res=E-K0-H['EXTERNAL WORK']*.001;globalP=np.column_stack([H[k+'-MOMENTUM'] for k in 'XYZ'])*.001;legacy=read(d/'review.json')
 checks={'native_completed':legacy['checks']['native_completed'],'fixed_step_all_recorded_intervals':grid,'source_secant_displacement_identity':kinematic,'source_initial_velocity':initial,'finite_derived_values':bool(np.isfinite(true).all()),'physical_KE_matches_native_kinetic_counter':bool(abs(K-H['KINETIC ENERGY']*.001).max()<et),'physical_P_matches_native_counter':bool(abs(P-globalP).max()<pt),'physical_energy_balance':bool(abs(res).max()<et),'closed_physical_momentum':bool(np.linalg.norm(P-P0,axis=1).max()<pt),'mass':legacy['histories'][0]['checks']['mass'],'no_added_mass':legacy['histories'][0]['checks']['no_added_mass'],'zero_external_work':legacy['histories'][0]['checks']['zero_external_work'],'no_plastic_work':legacy['histories'][0]['checks']['elastic_no_PW'],'observable_contact':legacy['checks'].get('observable_contact',False)}
 result={'created_utc':now(),'case':c['name'],'history':legacy['histories'][0]['history'],'samples':len(T),'first_ms':float(T[0]),'last_ms':float(T[-1]),'dt_ms':dt,'checks':checks,'pass':all(checks.values()),'maximum_secant_identity_error_mm_ms':float(abs(identity_error).max()),'maximum_kinematic_format_bound_mm_ms':float(bounds.max()),'maximum_physical_KE_vs_native_J':float(abs(K-H['KINETIC ENERGY']*.001).max()),'physical_energy_residual_J':float(abs(res).max()),'energy_tolerance_J':et,'global_momentum_difference_Ns':float(abs(P-globalP).max()),'method':'NDT1, gamma.5 beta.25, initial acceleration0: endpointV[n]=2*publishedSecantV[n]-endpointV[n-1]; independent displacement-increment identity and native kinetic/momentum counters checked. Original raw failures retained.','legacy_raw_review':rel(d/'review.json'),'solver_state_or_inputs_changed':False,'no_new_RKE_term_or_fitted_coefficient':True}
 if time_precision:
  result.update(literal_time_grid_gate_preserved=literal_grid,previous_review_preserved=rel(d/'newmark_velocity_review.json') if (d/'newmark_velocity_review.json').exists() else None,time_format_method='Compare each recorded timestamp with its nominal fixed-step cycle time using documented six-digit/float32 bound; independently require native cycle count within one terminal-cycle convention and all printed actual steps equal requested step.',maximum_time_rounding_error_ms=float(abs(T-nominal).max()),maximum_time_format_bound_ms=float(time_bound.max()),native_cycles=cycles)
  dump(d/'newmark_velocity_time_precision_review.json',result)
 else:dump(d/'newmark_velocity_review.json',result)
 return result

def run():
 guard();rows=[review(c) for c in read(OUT/'native_review.json')['cases'] for c in [c['case']]]
 dump(OUT/'newmark_reader_review.json',{'created_utc':now(),'cases':rows,'source_protocol':read(CFG)['output_velocity_interpretation'],'whole_impact_qualified':False});print([{'case':x['case'],'pass':x['pass'],'energy_residual_J':x['physical_energy_residual_J'],'KE_counter_difference_J':x['maximum_physical_KE_vs_native_J'],'grid':x['checks']['fixed_step_all_recorded_intervals']} for x in rows],flush=True)

if __name__=='__main__':run()
