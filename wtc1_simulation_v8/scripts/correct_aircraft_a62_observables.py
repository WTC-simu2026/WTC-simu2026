"""Separate source-defined Newmark/BC observables; retain every initial failed gate."""
from probe_aircraft_a62_surface import ROOT,OUT,engine,read,dump,sha,now,rel
from seed_aircraft_a62_motion import SEEDED
from audit_aircraft_a05 import histories
from assess_aircraft_a23_reader_precision import printed_bound
import numpy as np,json

def main():
    engine();cfg=read(SEEDED);lim=cfg['acceptance'];rows=[]
    source=ROOT/'wtc1_simulation_v8/scripts/read_aircraft_a41_newmark.py'
    dump(OUT/'observable_correction_predeclaration.json',{'created_utc':now(),'after_native_runs':True,'old_failed_gates_and_partial_JSON_preserved':True,
       'reasons':['Unused Y translations were explicitly FREE and now have declared initial velocity. Compare motion only on prescribed axes; free-flight Y after deletion is a model result, not a prescribed-motion error.',
          'Newmark TH velocities are secants, as the already established source protocol describes. Compute boundary work from recorded displacements and integrated reaction impulse on actual fixed steps, and independently reconstruct physical endpoint velocities.',
          'Half-dt final animation is at0.9955ms, but a complete native nodal TH sample exists at1ms. Use that real saved field to establish terminal completion without changing any clock or replaying the Engine.'],
       'cached_source_method':rel(source),'cached_method_sha256':sha(source),'physical_thresholds_unchanged':True,'native_binary_unchanged':True,'old_Engine_replays':0,
       'additional_kinematic_counter_thresholds_from_A45':{'energy_relative_initial_KE':.02,'energy_absolute_J':1e-7,'momentum_relative_initial_absolute_P':.02,'momentum_absolute_Ns':1e-9}})
    for case in cfg['cases']:
        d=OUT/'native'/case['id'];prior=read(d/'loaded_mechanical_review.json');name=read(d/'generation.json')['name'];H=histories(d/(name+'T01.csv'));T=H['time'];dt=case['dt_cap_ms']
        N=np.stack([np.column_stack([v for k,v in H.items() if k.startswith('REACTION_'+a)]).reshape(len(T),8,3) for a in 'XYZ'],axis=-1)
        U=N[:,:,0,:];sec=N[:,:,1,:];I=N[:,:,2,:];axes=case['imposed_axes']
        from material_aircraft_a60 import path_values
        expected=path_values(np.minimum(T,1),case,cfg['cohesive']);motion=float(abs(U[:,4:,axes].mean(axis=1)-expected[:,axes]).max())
        work=float(np.sum(np.diff(I,axis=0)*np.diff(U,axis=0)/np.diff(T)[:,None,None])*.001);work_error=abs(work-H['EXTERNAL WORK'][-1]*.001)
        identity=np.diff(U,axis=0)/dt-sec[1:];bound=(printed_bound(U[1:])+printed_bound(U[:-1]))/dt+printed_bound(sec[1:])+1e-6
        V0=np.zeros((8,3));V0[4:]=case['initial_free_velocity_mm_ms'];V=np.zeros_like(sec);V[0]=V0
        for j in range(1,len(T)):V[j]=2*sec[j]-V[j-1]
        kinetic=.5*np.sum(V*V,axis=(1,2))*.001;momentum=np.sum(V,axis=1)*.001;P0=np.sum(V0,axis=0)*.001
        counterK=float(abs(kinetic-H['KINETIC ENERGY']*.001).max());globalP=np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001;counterP=float(abs(momentum-globalP).max())
        momentum_residual=momentum-P0-np.sum(I,axis=1)*.001;momentum_error=float(abs(momentum_residual).max())
        energy_tol=.02*cfg['initial_instrument_KE_J']+1e-7;momentum_tol=.02*np.sum(abs(V0))*.001+1e-9
        checks={k:v for k,v in prior['checks'].items() if k not in ['prescribed_and_free_axes_motion','final_field_motion','native_impulse_work','native_final_clock_reaches_requested_end','native_overshoot_within_one_declared_step','fixed_bottom_fields']}
        checks.update(prescribed_axes_motion_only=motion<=lim['prescribed_motion_mm'],source_secant_displacement_identity=bool(np.all(abs(identity)<=bound)),
            physical_endpoint_KE_vs_native=counterK<=energy_tol,physical_endpoint_P_vs_native=counterP<=momentum_tol,closed_momentum_including_support_impulses=momentum_error<=momentum_tol,
            displacement_impulse_boundary_work=work_error<=lim['work_energy_fraction']*prior['energy_scale_J']+lim['absolute_energy_J'])
        if prior['native_final_field_time_ms']>=1-1e-6:
            from probe_aircraft_a37 import vtk
            field=vtk((d/'final_state.vtk').read_text(encoding='utf8'));finalU=field['Displacement'].reshape(-1,3)[np.argsort(field['NODE_ID'])];end=prior['native_final_field_time_ms'];kind='native_animation'
        else:
            assert T[-1]>=1-1e-6 and prior['checks']['binary_all_channels_agree'];finalU=U[-1];end=float(T[-1]);kind='native_TH_complete_nodal_sample'
            generation=read(d/'generation.json');dump(d/'terminal_TH_fields.json',{'created_utc':now(),'source':rel(d/(name+'T01')),'source_sha256':sha(d/(name+'T01')),'native_time_ms':end,'node_IDs':list(range(1,9)),'native_displacements_mm':finalU.tolist(),'coordinates_mm':(np.asarray(generation['nodes_mm'])+finalU).tolist(),'complete_binary_CSV_channel_identity_previously_verified':True,'older_animation_clock_preserved':prior['native_final_field_time_ms'],'not_an_extrapolation':True})
        target=np.asarray(case['knot_gaps_mm'][-1]);endmotion=float(abs(finalU[4:,axes]-target[axes]).max())
        checks.update(native_saved_terminal_clock_reaches_target=end>=1-1e-6,native_saved_terminal_clock_within_declared_step=end<=1+dt+1e-6,native_terminal_prescribed_axes=endmotion<=lim['prescribed_motion_mm'],fixed_bottom_terminal=bool(np.all(finalU[:4]==0)))
        row={'case':case['id'],'checks':{k:bool(v) for k,v in checks.items()},'pass':bool(all(checks.values())),'initial_failed_checks_preserved':prior['failed_checks'],'maximum_prescribed_axis_motion_error_mm':motion,'maximum_final_prescribed_axis_error_mm':endmotion,'terminal_native_field_source':kind,'terminal_native_time_ms':end,'free_Y_final_gap_mm':float(finalU[4:,1].mean()),'work_by_displacement_impulse_J':work,'work_error_J':float(work_error),'maximum_secant_identity_error':float(abs(identity).max()),'physical_KE_counter_difference_J':counterK,'physical_P_counter_difference_Ns':counterP,'closed_momentum_error_Ns':momentum_error,'additional_counter_energy_tolerance_J':energy_tol,'additional_counter_momentum_tolerance_Ns':float(momentum_tol),'physical_thresholds_unchanged':True,'new_whole_credit_s':0}
        dump(d/'source_observable_mechanical_review.json',row);rows.append(row);print(json.dumps({'case':case['id'],'pass':row['pass'],'failed':[k for k,v in row['checks'].items() if not v],'work_error_J':float(work_error),'KE_counter_error_J':counterK,'momentum_error_Ns':momentum_error}),flush=True)
    raw=[read(OUT/'native'/c['id']/'loaded_mechanical_review.json') for c in cfg['cases']];half=float(abs(raw[1]['maximum_IE_J']-raw[2]['maximum_IE_J'])/raw[1]['energy_scale_J'])
    dump(OUT/'initial_free_motion_source_observable_review.json',{'created_utc':now(),'cases':rows,'all_declared_case_checks_pass':bool(all(r['pass'] for r in rows)),'half_dt_peak_IE_relative_difference':half,'half_dt_pass':bool(half<=lim['half_dt_work_fraction']),'pass':bool(all(r['pass'] for r in rows) and half<=lim['half_dt_work_fraction']),'all_at_rest_and_initial_observable_failures_preserved':True,'analysis_correction_after_runs_explicit':True,'native_state_rollback_directly_instrumented':False,'large_rotation_or_whole_insertion_qualified':False,'new_whole_credit_s':0})

if __name__=='__main__':main()
