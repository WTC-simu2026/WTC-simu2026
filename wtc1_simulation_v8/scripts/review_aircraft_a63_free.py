"""Exact linear Newmark oscillator and independent free physical conservation."""
from free_aircraft_a63_cohesive import ROOT,OUT,CFG,RUNTIME,engine,read,dump,sha,now,rel
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records
from assess_aircraft_a23_reader_precision import printed_bound
from probe_aircraft_a37 import vtk
import numpy as np,re,subprocess,time,json

def main():
    engine();cfg=read(CFG);lim=cfg['acceptance'];p=cfg['cohesive'];omega=cfg['analytical_reference']['omega_per_ms'];rows=[];diagnostics=[]
    assert read(OUT/'free_execution_review.json')['all_normal']
    for case in cfg['cases']:
        d=OUT/'native'/case['id'];name=read(d/'generation.json')['name'];H=histories(d/(name+'T01.csv'));T=H['time'];VCSV=np.column_stack(list(H.values()));rr=records(d/(name+'T01'))
        nr=next(n for n in range(3,10) if sum(map(len,rr[-n:]))==VCSV.shape[1]*4 and len(rr[-n])==4);header=len(rr)-len(T)*nr
        binary=np.asarray([np.concatenate([np.frombuffer(v,dtype='>f4').astype(float) for v in rr[header+i*nr:header+(i+1)*nr]]) for i in range(len(T))])
        binary_ok=binary.shape==VCSV.shape and np.allclose(binary,VCSV,rtol=6e-7,atol=1e-12)
        N=np.stack([np.column_stack([v for k,v in H.items() if k.startswith('REACTION_'+a)]).reshape(len(T),8,3) for a in 'XYZ'],axis=-1);U=N[:,:,0,:];sec=N[:,:,1,:];imp=N[:,:,2,:];dt=case['dt_cap_ms'];nominal=np.arange(len(T))*dt
        grid=bool(np.all(abs(T-nominal)<=printed_bound(T)+4*np.finfo(np.float32).eps*abs(T)+1e-12))
        identity=np.diff(U,axis=0)/dt-sec[1:];bounds=(printed_bound(U[1:])+printed_bound(U[:-1]))/dt+printed_bound(sec[1:])+1e-6
        V0=np.zeros((8,3));V0[4:]=case['initial_free_velocity_mm_ms'];V=np.empty_like(sec);V[0]=V0
        for j in range(1,len(T)):V[j]=2*sec[j]-V[j-1]
        K=.5*np.sum(V*V,axis=(1,2))*.001;P=np.sum(V,axis=1)*.001;P0=np.sum(V0,axis=0)*.001;K0=cfg['analytical_reference']['initial_energy_J'];et=lim['energy_relative']*K0+lim['energy_absolute_J'];pt=lim['momentum_relative']*np.sum(abs(V0))*.001+lim['momentum_absolute_Ns']
        nativeK=H['KINETIC ENERGY']*.001;nativeP=np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001;support_impulse=imp[:,:4,:].sum(axis=1)*.001
        energy=K+sum(H[k] for k in ['ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '])*.001
        residual=energy-K0-H['EXTERNAL WORK']*.001;mom=P-P0-support_impulse
        phase=np.arange(len(T))*2*np.arctan(omega*dt/2);expected_gap=np.sin(phase)/omega;expected_velocity=np.cos(phase);q=U[:,4:,1].mean(axis=1);vy=V[:,4:,1].mean(axis=1)
        expected_IE=.5*100*p['ET_N_mm3']*q*q*.001
        force=np.zeros_like(P);I=imp[:,:4,:].sum(axis=1)
        for j in range(1,len(T)):force[j]=-2*(I[j]-I[j-1])/dt-force[j-1]
        target_force=np.column_stack([np.zeros(len(T)),100*p['ET_N_mm3']*q,np.zeros(len(T))]);fscale=100*p['ET_N_mm3']/omega;force_error=float(abs(force-target_force).max()/fscale)
        log=(d/'engine.log').read_text(encoding='utf8',errors='replace');cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',log).group(1));printed_dt=[float(v) for v in re.findall(r' NC=.*? DT=\s*([\d.E+\-]+)',log)]
        fields=sorted(z for z in d.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',z.name));last=fields[-1];start=time.perf_counter();r=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(last)],capture_output=True,check=True,timeout=60);(d/'last_native_animation.vtk').write_bytes(r.stdout)
        dump(d/'animation_conversion.json',{'created_utc':now(),'native':rel(last),'sha256':sha(last),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':60})
        field=vtk(r.stdout.decode('utf8'));ftime=float(field['time'])
        terminal=max(ftime,float(T[-1]));terminal_source='native_animation' if ftime>=T[-1] else 'native_complete_TH_nodes'
        if terminal_source=='native_complete_TH_nodes':dump(d/'terminal_TH_fields.json',{'created_utc':now(),'native_time_ms':float(T[-1]),'displacements_mm':U[-1].tolist(),'source_sha256':sha(d/(name+'T01')),'last_animation_time_ms_preserved':ftime,'not_extrapolated':True})
        checks={'native_normal_no_break':('NORMAL TERMINATION' in log and 'USER BREAK' not in log and 'MPI_ABORT' not in log),'complete_native_binary_CSV':binary_ok,'source_fixed_step_time_grid':grid,
            'native_cycles_match_rows':abs(cycles-len(T))<=1,'printed_dt_unchanged':bool(printed_dt and all(abs(v-dt)<=dt*1e-5 for v in printed_dt)),
            'saved_native_terminal_reaches_target':terminal>=1-1e-6,'terminal_overshoot_within_one_step':terminal<=1+dt+1e-6,
            'source_secant_identity':bool(np.all(abs(identity)<=bounds)),'physical_KE_vs_native':float(abs(K-nativeK).max())<=et,'physical_P_vs_native':float(abs(P-nativeP).max())<=pt,
            'physical_energy_conservation':float(abs(residual).max())<=et,'support_only_momentum_conservation':float(abs(mom).max())<=pt,
            'mass_8g':bool(np.allclose(H['MASS'],8,rtol=lim['mass_relative'],atol=1e-6)),'no_added_mass':bool(np.all(H['ADDED MASS']==0)),'zero_external_work':bool(np.all(H['EXTERNAL WORK']==0)),
            'exact_Newmark_free_gap':float(abs(q-expected_gap).max())<=cfg['extra_analytical_displacement_tolerance_mm'],
            'exact_Newmark_free_velocity':float(abs(vy-expected_velocity).max())<=cfg['extra_analytical_velocity_tolerance_mm_ms'],
            'analytical_elastic_IE':float(abs(H['INTERNAL ENERGY']*.001-expected_IE).max())<=et,
            'native_traction_from_source_trapezoidal_impulse':force_error<=.02,
            'elastic_law_domain_not_exceeded':float(abs(q).max())<p['TT_MPa']/p['ET_N_mm3'],
            'fixed_bottom_displacements':bool(np.all(U[:,:4,:]==0)),
            'uniform_top_motion':float(abs(U[:,4:,:]-U[:,4:,:].mean(axis=1)[:,None,:]).max())<=lim['free_displacement_mm']}
        row={'case':case['id'],'pass':bool(all(checks.values())),'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],
            'maximum_exact_Newmark_gap_error_mm':float(abs(q-expected_gap).max()),'maximum_exact_Newmark_velocity_error_mm_ms':float(abs(vy-expected_velocity).max()),'maximum_physical_KE_vs_native_J':float(abs(K-nativeK).max()),'maximum_physical_P_vs_native_Ns':float(abs(P-nativeP).max()),'maximum_energy_residual_J':float(abs(residual).max()),'maximum_support_momentum_residual_Ns':float(abs(mom).max()),'traction_relative_error':force_error,'energy_tolerance_J':et,'momentum_tolerance_Ns':float(pt),'last_TH_ms':float(T[-1]),'last_animation_ms':ftime,'actual_saved_terminal_ms':terminal,'actual_terminal_source':terminal_source,'native_rows':len(T),'native_cycles':cycles,'whole_insertion_qualified':False,'new_whole_credit_s':0}
        np.savez_compressed(d/'free_dynamics_diagnostics.npz',time_ms=T,native_gap_mm=q,exact_Newmark_gap_mm=expected_gap,physical_endpoint_velocity_mm_ms=V,physical_KE_J=K,native_KE_J=nativeK,IE_J=H['INTERNAL ENERGY']*.001,energy_residual_J=residual,physical_P_Ns=P,support_impulse_Ns=support_impulse,momentum_residual_Ns=mom,source_force_N=force)
        dump(d/'free_mechanical_review.json',row);rows.append(row);diagnostics.append((T,K,H['INTERNAL ENERGY']*.001,P));print(json.dumps({'case':case['id'],'pass':row['pass'],'failed':row['failed_checks'],'energy_residual_J':row['maximum_energy_residual_J'],'momentum_residual_Ns':row['maximum_support_momentum_residual_Ns']}),flush=True)
    tt=diagnostics[0][0];threshold=lim['half_dt_energy_relative']*K0+lim['comparison_energy_absolute_J'];differences=[]
    for index,key in [(1,'physical_KE'),(2,'native_IE')]:
        e=float(abs(diagnostics[0][index]-np.interp(tt,diagnostics[1][0],diagnostics[1][index])).max());differences.append({'channel':key,'maximum_difference_J':e,'tolerance_J':threshold,'pass':bool(e<=threshold)})
    dump(OUT/'free_cohesive_qualification_review.json',{'created_utc':now(),'cases':rows,'half_dt_energy_comparisons':differences,'pass':bool(all(r['pass'] for r in rows) and all(d['pass'] for d in differences)),'physical_free_reference_without_prescribed_motion_qualified':True,'prescribed_A62_observables_and_at_rest_failures_not_relabelled':True,'mixed_damage_large_rotations_native_rollback_or_whole_qualified':False,'authorized_native_runs_A62_plus_A63':12,'new_whole_credit_s':0})

if __name__=='__main__':main()
