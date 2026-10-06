"""Read saved native witnesses; distinguish energy, impulse, and effective stress."""
import argparse,re,subprocess
import numpy as np
from run_aircraft_a06 import ROOT,OUT,CFG,RUNTIME,read,dump,sha,rel,now
from audit_aircraft_a05 import vtk,histories
def trap(y,x):return np.sum((y[1:]+y[:-1])*.5*np.diff(x,axis=0),axis=0)
def review(revision):
    dest=OUT/'witness_review.json';assert not dest.exists();cfg=read(CFG);a=cfg['acceptance'];rows=[]
    for case in cfg['witness']['cases']:
        d=OUT/revision/case['id'];n=read(d/'generation.json')['name'];H=histories(d/(n+'T01.csv'));T=H['time'];K=H['KINETIC ENERGY']*.001;IE=H['INTERNAL ENERGY']*.001;EW=H['EXTERNAL WORK']*.001;res=K+IE+H['HOURGLASS ENERGY']*.001-EW
        N=np.column_stack([H[k] for k in H if k.startswith('AFFINE_NODES')]).reshape(len(T),4,6)
        # Canonical order inferred independently from affine nodal positions and velocities.
        eps=np.log1p(N[:,1,0]/case['L_mm']);expected=np.interp(T,cfg['witness']['path_time_ms'],cfg['witness']['path_log_strain'])
        position_error=float(np.max(abs(eps-expected)));ry=np.log1p(N[:,2,1]/case['L_mm']);assert position_error<3e-5 and np.max(abs(ry+.25*eps))<3e-5
        r=N[:,:,4:6];disp=N[:,:,:2];vel=N[:,:,2:4]
        work_force=np.sum(trap(r,disp))*.001
        work_impulse=np.sum((vel[1:]+vel[:-1])*.5*np.diff(r,axis=0))*.001
        norm=max(float(np.max(abs(EW))),1e-9);force_error=abs(work_force-EW[-1])/norm;impulse_error=abs(work_impulse-EW[-1])/norm
        ts=[];dam=[];stress=[];strain=[];positions=[];native=[];erode=[]
        for p in sorted(d.glob(n+'A*')):
            if not re.fullmatch(re.escape(n)+r'A\d{3}',p.name):continue
            q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=90).stdout)
            ts.append(q['time']);dam.append(np.array([q[k] for k in q if 'DAMAGE' in k]));stress.append(q['2DELEM_Stress_(upper)'].reshape(2,3,3));strain.append(q['2DELEM_Strain_(upper)'].reshape(2,3,3));positions.append(q['points'].reshape(4,3));erode.append(q['EROSION_STATUS']);native.append({'path':rel(p),'sha256':sha(p)})
        ts=np.array(ts);dam=np.array(dam);stress=np.array(stress);strain=np.array(strain);assert dam.shape[1:]==(3,2)
        zero_t=.5;ix=np.argmin(abs(ts-zero_t));i1=np.argmin(abs(ts-.25));i2=np.argmin(abs(ts-.75));L=case['L_mm'];le=L/np.sqrt(2);vface=L*L*1.;epsend=float(eps[-1]);ecore=.5*(1/.99)*(epsend**2+(-.25*epsend)**2+.2*epsend*(-.25*epsend))*L*L*8*.001
        energy_per_surface=(IE[-1]-ecore)*1000*le/vface
        np.savez_compressed(d/'saved_witness_SI.npz',history_time_s=T*.001,log_axial_strain=eps,native_node_channels=N,kinetic_J=K,internal_J=IE,external_work_J=EW,energy_residual_J=res,animation_time_s=ts*.001,damage=dam,effective_stress_elemental_MPa=stress,output_strain_elemental=strain,positions_m=np.array(positions)*.001,erosion_status=np.array(erode))
        listing=(d/(n+'_0000.out')).read_text(encoding='utf-8',errors='replace');sl=(d/'starter.log').read_text(encoding='utf-8');warnings=int(re.findall(r'(\d+) WARNING\(S\)',sl)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',sl)[-1])
        checks={'starter_without_errors_warnings':errors==warnings==0,'engine_normal':'NORMAL TERMINATION' in (d/'engine.log').read_text(encoding='utf-8'),'finite':all(np.all(np.isfinite(q)) for q in [N,IE,EW,dam,stress,strain]),'damage_bounds':float(dam.min())>=-a['witness_damage_bounds_tolerance'] and float(dam.max())<=1+a['witness_damage_bounds_tolerance'],'energy_balance':float(np.max(abs(res)))/norm<a['witness_energy_balance_relative'],'reaction_impulse_work_closes':impulse_error<a['witness_energy_balance_relative'],'affine_positions':position_error<3e-5,'no_shell_erosion':bool(np.all(np.array(erode)==1)),'core_damage_zero':bool(np.all(dam[:,1,:]==0))}
        checks={k:bool(v) for k,v in checks.items()}
        row={'case':case,'checks':checks,'integrity_pass':all(checks.values()),'final_time_history_ms':float(T[-1]),'final_time_animation_ms':float(ts[-1]),'final_IE_J':float(IE[-1]),'final_KE_J':float(K[-1]),'final_work_J':float(EW[-1]),'maximum_energy_residual_fraction':float(np.max(abs(res)))/norm,'reaction_as_force_work_J':float(work_force),'reaction_as_impulse_work_J':float(work_impulse),'reaction_force_interpretation_relative_error':float(force_error),'reaction_impulse_interpretation_relative_error':float(impulse_error),'characteristic_length_candidate_mm':le,'candidate_length_not_independently_read_from_native_UVAR':True,'face_damage_at_load_unload_reload':[dam[i,[0,2],:].tolist() for i in [i1,ix,i2]],'IE_at_zero_strain_interpolated_J':float(np.interp(.5,T,IE)),'face_final_energy_per_candidate_area_N_mm':float(energy_per_surface),'not_single_monotone_fracture_measurement':True,'core_energy_subtraction_small_strain_approximation_J':float(ecore),'native_damage_and_effective_tensor_scope':'Layer maxima of failure index; stress animation is not established damaged-force stress. Native impulses/work kept independently.','native_animations':native,'source_snapshot_equivalence_to_binary':False}
        rows.append(row);dump(d/'witness_audit.json',row);print({k:row[k] for k in ['final_IE_J','maximum_energy_residual_fraction','reaction_impulse_interpretation_relative_error','face_final_energy_per_candidate_area_N_mm']},flush=True)
    r1=next(r for r in rows if r['case']['id']=='DAMAGE_L10');r2=next(r for r in rows if r['case']['id']=='DAMAGE_L10_HALF');diff=abs(r1['final_IE_J']-r2['final_IE_J'])/r1['final_IE_J']
    result={'created_utc':now(),'cases':rows,'witness_integrity_pass':all(r['integrity_pass'] for r in rows),'half_dt_final_IE_relative_difference':diff,'half_dt_pass':bool(diff<a['witness_half_dt_final_IE_relative']),'failure_energy_qualified':False,'failure_transfer_authorized':False,'reason':'Cyclic failure parameter energy not identified as dissipated surface energy; native work/irreversibility and effective-stress output require separate interpretation. No claim that G=50N/mm was verified.','whole_elastic_viscosity_controls_can_proceed':True}
    dump(dest,result)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',default='w0');review(p.parse_args().revision)
