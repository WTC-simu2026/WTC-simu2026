"""Read existing A64 outputs; identify sparse TH sampling without rerunning any solver."""
from run_aircraft_a64_step import ROOT,OUT,CFG,read,dump,sha,now,rel
from audit_aircraft_a05 import histories
from assess_aircraft_a23_reader_precision import printed_bound
import numpy as np, re, json

rows=[];cfg=read(CFG);omega=cfg['analytical_reference']['omega_per_ms'];k0=cfg['analytical_reference']['initial_energy_J'];diags=[]
for case in cfg['cases']:
    d=OUT/'native'/case['id'];name=read(d/'generation.json')['name'];H=histories(d/(name+'T01.csv'));T=H['time'];dt=case['dt_cap_ms']
    cycles=np.rint(T/dt).astype(int);nominal=cycles*dt
    clock_error=abs(T-nominal);bound=printed_bound(T)+4*np.finfo(np.float32).eps*abs(T)+1e-12
    q=np.column_stack([v for k,v in H.items() if k.startswith('REACTION_Y')]).reshape(len(T),8,3)[:,4:,0].mean(axis=1)
    phase=cycles*2*np.arctan(omega*dt/2);qref=np.sin(phase)/omega;vref=np.cos(phase)
    kinetic=H['KINETIC ENERGY']*.001;internal=H['INTERNAL ENERGY']*.001
    momentum=np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001
    imp=np.stack([np.column_stack([v for k,v in H.items() if k.startswith('REACTION_'+a)]).reshape(len(T),8,3)[:,:4,2].sum(axis=1) for a in 'XYZ'],axis=1)*.001
    jumps,counts=np.unique(np.diff(cycles),return_counts=True)
    row={'case':case['id'],'source_TH_frequency_ms':float(re.search(r'/TFILE/4\s+([\d.eE+\-]+)',(d/(name+'_0001.rad')).read_text(encoding='utf8')).group(1)),
       'dt_ms':dt,'samples':len(T),'last_TH_ms':float(T[-1]),'recorded_cycle_jump_counts':{str(int(a)):int(b) for a,b in zip(jumps,counts)},
       'all_samples_on_native_dt_grid':bool(np.all(clock_error<=bound)),'missing_steps_before_last_saved_cycle':int(cycles[-1]+1-len(cycles)),
       'maximum_actual_cycle_Newmark_gap_error_mm':float(abs(q-qref).max()),
       'maximum_actual_cycle_native_KE_vs_exact_J':float(abs(kinetic-k0*vref**2).max()),
       'maximum_actual_cycle_native_IE_vs_exact_J':float(abs(internal-k0*np.sin(phase)**2).max()),
       'maximum_native_energy_residual_J':float(abs(kinetic+internal-k0).max()),
       'maximum_native_P_vs_exact_Ns':float(abs(momentum[:,1]-.004*vref).max()),
       'maximum_native_P_support_residual_Ns':float(abs(momentum-np.array([0,.004,0])-imp).max()),
       'terminal_complete_fields_gate_not_overridden':True,'raw_A64_qualification_failure_preserved':True,
       'missing_step_velocity_recursion_invalid_for_sparse_case':bool(np.any(np.diff(cycles)!=1))}
    rows.append(row);diags.append((T,kinetic,internal));print(json.dumps(row),flush=True)
threshold=cfg['acceptance']['half_dt_energy_relative']*k0+cfg['acceptance']['comparison_energy_absolute_J']
compare=[]
for index,key in [(1,'native_KE'),(2,'native_IE')]:
    error=float(abs(diags[0][index]-np.interp(diags[0][0],diags[1][0],diags[1][index])).max())
    compare.append({'channel':key,'maximum_difference_J':error,'unchanged_tolerance_J':threshold,'pass':error<=threshold,'common_recorded_time_only':True})
dump(OUT/'sampling_and_actual_cycle_review.json',{'created_utc':now(),'cases':rows,'native_counter_comparisons':compare,
    'no_solver_replay':True,'no_source_patch':True,'no_extrapolated_missing_fields':True,
    'original_free_composite_pass':read(OUT/'free_cohesive_qualification_review.json')['pass'],
    'qualification_not_promoted':True,'conditional_whole_CHECK_not_authorized_to_override_failed_gate':True,
    'diagnosis':'TFILE=0.0001ms exceeds the fine step0.0000625ms; sparse samples invalidate every-step secant recursion. Last complete saved fields also precede target.'})
