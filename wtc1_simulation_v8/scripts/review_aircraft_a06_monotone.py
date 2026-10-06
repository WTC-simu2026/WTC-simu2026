"""Independent energy reference and native reaction work on saved monotone data."""
import re,subprocess
import numpy as np
from run_aircraft_a06 import ROOT,OUT,RUNTIME,read,dump,sha,rel,now
from audit_aircraft_a05 import vtk,histories
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a06_monotone_predeclaration.json'
def main():
    dst=OUT/'monotone_review.json';assert not dst.exists();c=read(CFG);rows=[]
    for case in c['cases']:
        d=OUT/'m1'/case['id'];n='A06_'+case['id'];H=histories(d/(n+'T01.csv'));T=H['time'];N=np.column_stack([H[k] for k in H if k.startswith('AFFINE_NODES')]).reshape(len(T),4,6)
        L=case['L_mm'];ep=np.log1p(N[:,1,0]/L);ey=np.log1p(N[:,2,1]/L);u=T;target=.12*(3*u*u-2*u*u*u);assert np.max(abs(ep-target))<2e-5 and np.max(abs(ey+.25*ep))<2e-5
        K=H['KINETIC ENERGY']*.001;IE=H['INTERNAL ENERGY']*.001;EW=H['EXTERNAL WORK']*.001;res=K+IE+H['HOURGLASS ENERGY']*.001-EW;norm=max(abs(EW));R=N[:,:,4:6];V=N[:,:,2:4];wi=np.sum((V[1:]+V[:-1])*.5*np.diff(R,axis=0))*.001;error=abs(wi-EW[-1])/norm
        ts=[];D=[];S=[];Str=[];eros=[];native=[]
        for p in sorted(d.glob(n+'A*')):
            if not re.fullmatch(re.escape(n)+r'A\d{3}',p.name):continue
            q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=90).stdout);ts.append(q['time']);D.append([q[k] for k in q if 'DAMAGE' in k]);S.append(q['2DELEM_Stress_(upper)'].reshape(2,3,3));Str.append(q['2DELEM_Strain_(upper)'].reshape(2,3,3));eros.append(q['EROSION_STATUS']);native.append({'path':rel(p),'sha256':sha(p)})
        ts=np.array(ts);D=np.array(D);S=np.array(S);Str=np.array(Str);ea=np.interp(ts,T,ep);dm=np.mean(D[:,0,:],axis=1);active=(dm>.02)&(dm<.95);eps0=450/22000;le=L/np.sqrt(2);G=50.;E=22000.;s=450.
        slope=np.mean(np.diff(dm)[active[1:]&active[:-1]]/np.diff(ea)[active[1:]&active[:-1]]) if np.count_nonzero(active)>1 else None
        inferred=slope*2*G/s if slope is not None else None
        ecore=.5*(1/.99)*(ep[-1]**2+ey[-1]**2+.2*ep[-1]*ey[-1])*L*L*8*.001
        g_total=(IE[-1]-ecore)*1000*le/(L*L);g_elastic=le*s*s/(2*E);g_post=G+2*E*G*G/(3*le*s*s);g_ref=g_elastic+g_post;referr=abs(g_total-g_ref)/g_ref
        t0=float(np.interp(eps0,ep,T));ie0=float(np.interp(t0,T,IE));f0=float(np.interp(t0,T,H['EXTERNAL WORK']))*.001
        # Native REACX/REACY are cumulative impulses, established by independent work comparison.
        mtotal=L*L*.002214;mass=np.array([1/3,1/6,1/3,1/6])*mtotal
        reaction_force=np.diff(N[:,:,4],axis=0)/np.diff(T)[:,None];acc=np.diff(N[:,:,2],axis=0)/np.diff(T)[:,None];internal_force= reaction_force-mass[None,:]*acc
        sigma_force=np.sum(internal_force[:,[1,2]],axis=1)/(L*np.exp(.5*(ey[1:]+ey[:-1])))
        # Effective stress output eigenvalue is basis invariant; compare only pre-failure small uniaxial state.
        before=np.flatnonzero((dm>.2)&(dm<.8));ix=int(before[0]) if len(before) else None
        comparison=None
        if ix is not None:
            tm=ts[ix];sf=float(np.interp(tm,(T[1:]+T[:-1])*.5,sigma_force));effective=float(np.max(np.linalg.eigvalsh(S[ix,:,:2,:2])));comparison={'time_ms':float(tm),'damage_max':float(D[ix,0,:].max()),'stress_output_effective_eigenvalue_MPa':effective,'force_equivalent_axial_stress_MPa_approx':sf,'force_equivalent_normalization':'current transverse edge times initial total face thickness1mm; tiny core and thickness change not removed'}
        checks={'normal_engine':'NORMAL TERMINATION' in (d/'engine.log').read_text(encoding='utf-8'),'finite':bool(np.all(np.isfinite(N)) and np.all(np.isfinite(D))),'energy_balance':float(max(abs(res)))/norm<c['acceptance']['energy_balance_fraction'],'reaction_impulse_work':bool(error<c['acceptance']['reaction_impulse_work_fraction']),'no_shell_erosion':bool(np.all(np.array(eros)==1)),'faces_completely_failed':bool(np.all(D[-1,[0,2],:]==1)),'core_not_failed':bool(np.all(D[:,1,:]==0)),'analytic_initial_volume_reference':bool(referr<c['acceptance']['analytic_total_energy_fraction']),'actual_total_G_equals_input':bool(abs(g_total-G)/G<c['acceptance']['actual_G_input_equality_fraction'])}
        checks={k:bool(v) for k,v in checks.items()}
        np.savez_compressed(d/'saved_monotone_SI.npz',time_s=T*.001,log_axial_strain=ep,native_node_channels=N,internal_J=IE,kinetic_J=K,external_work_J=EW,residual_J=res,animation_time_s=ts*.001,damage=D,effective_stress_elemental_MPa=S,output_strain_elemental=Str,force_time_s=(T[1:]+T[:-1])*.0005,force_equivalent_axial_stress_MPa=sigma_force)
        row={'case':case,'checks':checks,'final_IE_J':float(IE[-1]),'final_KE_J':float(K[-1]),'maximum_energy_residual_fraction':float(max(abs(res)))/norm,'reaction_impulse_work_J':float(wi),'reaction_impulse_work_relative_error':float(error),'candidate_Le_mm':le,'inferred_Le_from_damage_slope_mm':float(inferred) if inferred is not None else None,'input_G_N_mm':G,'total_face_work_per_candidate_area_N_mm':float(g_total),'initial_volume_analytic_G_total_N_mm':g_ref,'analytic_G_elastic_N_mm':g_elastic,'analytic_G_post_onset_N_mm':g_post,'initial_volume_analytic_relative_error':float(referr),'energy_at_first_450MPa_reference_J':ie0,'first_reference_time_ms':t0,'face_IE_includes_dissipation_and_storage_until_failure':True,'energy_subtraction_core_approximation_J':float(ecore),'effective_output_vs_force_comparison':comparison,'native_animations':native}
        rows.append(row);dump(d/'audit.json',row);print({k:row[k] for k in ['total_face_work_per_candidate_area_N_mm','initial_volume_analytic_G_total_N_mm','initial_volume_analytic_relative_error','reaction_impulse_work_relative_error','inferred_Le_from_damage_slope_mm']},flush=True)
    checks={'native_execution_and_energy_integrity':all(all(r['checks'][k] for k in ['normal_engine','finite','energy_balance','reaction_impulse_work','no_shell_erosion','faces_completely_failed','core_not_failed']) for r in rows),'all_analytic_references_within_2pct':all(r['checks']['analytic_initial_volume_reference'] for r in rows),'input_G_identified_as_total_fracture_energy':all(r['checks']['actual_total_G_equals_input'] for r in rows)}
    dump(dst,{'created_utc':now(),'cases':rows,'checks':checks,'failure_transfer_authorized':False,'physical_fracture_energy_qualified':False,'reason':'Linear damage evolution generates work containing element-size-dependent elastic energy and rising effective stress. G input is not measured total fracture energy; no NIST fitting and no failure transfer to whole aircraft.'})
if __name__=='__main__':main()
