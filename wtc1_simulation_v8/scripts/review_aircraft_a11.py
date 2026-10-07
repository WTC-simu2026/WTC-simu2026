"""A11 native binary-verified energy, momentum, material-domain and saved-state review."""
import argparse,re,subprocess
from pathlib import Path
import numpy as np
from run_aircraft_a11 import ROOT,RUNTIME,CFG,OUT,PREV,read,dump,sha,rel,now,cases,guard
from audit_aircraft_a05 import histories,vtk
from review_aircraft_a08 import binary_mass
import audit_aircraft_a05 as inherited

def segments(H):
    result={}
    for label in ['AIRFRAME','NACELLE','FAN','CORE']:
        keys=[k for k in H if k.startswith('CONTACT_RAW_HISTORY_'+label+' ')]
        if keys:assert len(keys)==4;result[label]=np.column_stack([H[k] for k in keys[:3]])*.001
    return result

def aggregate_histories(p):
    H=histories(p);S=segments(H)
    if not S:return H
    agg=sum(S.values());r={k:v for k,v in H.items() if not k.startswith('CONTACT_RAW_HISTORY_')}
    for i in range(3):r['CONTACT_RAW_HISTORY A11_INTERFACE_SUM '+str(i)]=agg[:,i]*1000
    return r

def audit(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');name=g['name'];assert not (d/'review.json').exists();H=histories(d/(name+'T01.csv'))
    bk=[k for k in H if k.startswith('FORWARD_BEAM_DIAGNOSTIC')];stream=[int(re.search(r'FORWARD_BEAM_DIAGNOSTIC\s+(\d+)\s+B',k).group(1)) for k in bk[::9]];assert len(set(stream))==len(stream) and set(stream)==set(g['beam_history_ids'])
    def adapter(p):
        q=read(p);return {**q,'beam_history_ids':stream} if Path(p)==d/'generation.json' else q
    inherited.OUT=OUT;inherited.CFG=CFG;inherited.PREV=PREV;inherited.read=adapter;inherited.histories=aggregate_histories;r=read(d/'audit.json') if (d/'audit.json').exists() else inherited.audit('r0',caseid)
    Ho=histories(d/'observer'/(name+'T02_recovered.csv'));assert list(H)==list(Ho);H={k:np.r_[v,Ho[k][0]] for k,v in H.items()};T=H['time'];L=np.load(d/'balance_history_SI.npz');z=np.load(d/'verified_states_SI.npz');S=segments(H)
    kk=[k for k in H if k.startswith('AIRCRAFT_NATIVE_VELOCITY_ROTATION')];N=len(g['aircraft_diag_node_ids']);assert len(kk)==6*N;ids=[int(re.search(r'AIRCRAFT_NATIVE_VELOCITY_ROTATION\s+(\d+)\s+N',k).group(1)) for k in kk[::6]];assert set(ids)==set(g['aircraft_diag_node_ids']) and len(set(ids))==N
    for i,n in enumerate(ids):assert all(re.search(r'\s'+str(n)+r'\s+N'+str(n)+r'\s',k) for k in kk[6*i:6*i+6])
    nv=np.column_stack([H[k] for k in kk]).reshape(len(T),N,6);assert np.allclose(nv[0,:,:3],read(CFG)['velocity_m_s']) and np.max(abs(nv[0,:,3:]))==0
    proofs=[];KE=[];P=[];ts=[];masses=[]
    for row in r['native_animations']:
        p=ROOT/row['path'];q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=120).stdout);nm,proof=binary_mass(p,q);order=np.argsort(q['NODE_ID']);v=q['Velocity'].reshape(-1,3)[order];ts.append(q['time']);masses.append(nm);KE.append(.5*np.sum(nm[:,None]*v*v));P.append(np.sum(nm[:,None]*v,axis=0));proofs.append(proof)
    ts=np.array(ts);nm=masses[0];KE=np.array(KE);P=np.array(P);assert np.allclose(ts,z['time_s']*1000,atol=1e-5);assert all(np.array_equal(nm,q) for q in masses)
    Kglob=np.interp(ts,T,H['KINETIC ENERGY']*.001);Pglob=np.column_stack([np.interp(ts,T,H[a+'-MOMENTUM']*.001) for a in 'XYZ']);dk=(KE-KE[0])-(Kglob-Kglob[0]);dp=(P-P[0])-(Pglob-Pglob[0]);extra=read(CFG)['acceptance_extra'];a=read(CFG)['acceptance'];jmax=float(np.max(np.linalg.norm(L['contact_impulse_Ns'],axis=1)));tol=extra['independent_nodal_momentum_absolute_Ns']+extra['independent_nodal_momentum_relative']*jmax
    denseK=.5*np.sum(nm[np.array(ids)-1][None,:,None]*nv[:,:,:3]**2,axis=(1,2));denseP=np.sum(nm[np.array(ids)-1][None,:,None]*nv[:,:,:3],axis=1)
    checks={'native_all_aircraft_velocity_channels_verified':True,'independent_nodal_mass_sum':abs(float(nm.sum())-r['native_total_mass_kg'])<1e-6*r['native_total_mass_kg'],'independent_nodal_translation_energy_change':float(np.max(abs(dk)))<=extra['independent_nodal_translation_KE_fraction_of_initial']*r['initial_KE_J'],'independent_nodal_momentum_change':float(np.max(np.linalg.norm(dp,axis=1)))<=tol,'native_nodal_mass_unchanged':True,'scene_geometry_verified':read(d/'scene_audit.json')['pass'],'CSV_all_native_channels_verified':read(d/'history_recovery.json')['pass']}
    numerical=['starter_zero_errors','starter_zero_warnings','main_engine_normal_termination','observer_normal_termination','observer_did_not_change_main_outputs','mass_preserved','added_mass_within_fraction','native_original_connectivity_preserved','all_exported_states_finite','supports_fixed','native_end_timestamp_observed_within_step','energy_global_within_declared_limit','energy_local_within_declared_limit','momentum_global_support_balance','momentum_contact_facade_balance','global_and_part_plastic_work_nonnegative','no_erosion','no_external_work']
    material=['plastic_strain_below_diagnostic_limit','radome_elastic_reference_stress_below_tension_compression','radome_plastic_strain_zero']
    onset={label:float(T[np.flatnonzero(np.linalg.norm(J-J[0],axis=1)>0)[0]]) if np.any(J-J[0]) else None for label,J in S.items()}
    event={};rr=L['energy_residual_J'];loss=int(np.argmin(np.diff(rr)))+1
    if len(rr)>1:event={'interval_ms':[float(T[loss-1]),float(T[loss])],'residual_increment_J':float(rr[loss]-rr[loss-1]),'global_term_increments_J':{k:float(H[k][loss]-H[k][loss-1])*.001 for k in r['energy_terms_without_double_counting']}}
    r.update(extra_checks=checks,extra_checks_pass=all(checks.values()),all_declared_checks_pass=all(r['checks'].values()) and all(checks.values()),failed_checks=r['failed_checks']+['extra:'+k for k,v in checks.items() if not v],numerical_gates_pass=all(r['checks'][k] for k in numerical) and all(checks.values()),material_domain_pass=all(r['checks'][k] for k in material),numerical_gate_names=numerical,material_gate_names=material,contact_onset_by_segment_ms=onset,final_contact_impulse_by_segment_Ns={k:(J[-1]-J[0]).tolist() for k,J in S.items()},maximum_nodal_translation_energy_change_error_J=float(np.max(abs(dk))),maximum_nodal_momentum_change_error_Ns=float(np.max(np.linalg.norm(dp,axis=1))),native_aircraft_mass_after_RBE3_kg=float(nm[np.array(ids)-1].sum()),native_RKE_ledger='native global counted once; native part/global mismatch and independent angular-inertia ledger unqualified, not used to fill residual',support_units_independently_distinguished=True,support_units='raw cumulative impulse established by A10 source/witness, no force integration',largest_saved_residual_loss=event,full_historical_impact=False,whole_aircraft_exterior_contact=True,whole_aircraft_self_contact=False,material_core_crushing_and_delamination_modeled=False)
    np.savez_compressed(d/'independent_native_mass_diagnostics_SI.npz',native_nodal_mass_kg=nm,animation_time_s=ts*.001,independent_total_translation_KE_J=KE,independent_global_momentum_Ns=P,nodal_translation_KE_change_error_J=dk,nodal_momentum_change_error_Ns=dp,dense_time_s=T*.001,dense_aircraft_translation_KE_J=denseK,dense_aircraft_momentum_Ns=denseP)
    dump(d/'native_mass_reader_proofs.json',{'samples':proofs});dump(d/'review.json',r);print({'case':caseid,'numerical_pass':r['numerical_gates_pass'],'material_pass':r['material_domain_pass'],'failed':r['failed_checks'],'onsets_ms':onset,'end_ms':r['actual_main_end_time_ms'],'J_Ns':r['final_contact_impulse_Ns'],'residual_J':r['final_energy_residual_J'],'generated_J':r['final_generated_energy_J'],'max_radome_strength_ratio':max(q.get('radome_face_strength_ratio',0) for q in r['states'])},flush=True)

def compare(aa,bb):
    za=np.load(OUT/'r0'/aa/'balance_history_SI.npz');zb=np.load(OUT/'r0'/bb/'balance_history_SI.npz');tm=min(za['time_s'][-1],zb['time_s'][-1]);J=[np.array([np.interp(tm,q['time_s'],q['contact_impulse_Ns'][:,i]) for i in range(3)]) for q in [za,zb]];E=[float(np.interp(tm,q['time_s'],q['generated_energy_J'])) for q in [za,zb]];jd=float(np.linalg.norm(J[1]-J[0])/max(np.linalg.norm(J[0]),1e-12));ed=abs(E[1]-E[0])/max(abs(E[0]),1e-12);a=read(CFG)['acceptance'];return {'cases':[aa,bb],'type':'half_dt','common_time_ms':tm*1000,'impulse_difference_fraction':jd,'generated_energy_difference_fraction':ed,'impulse_pass':jd<=a['half_dt_impulse_difference_fraction'],'energy_pass':ed<=a['half_dt_generated_energy_difference_fraction']}

def initial():
    guard();r=[read(p) for p in sorted((OUT/'r0').glob('*/review.json'))];by={q['case']['id']:q for q in r};pair=compare('NOSE_04_DT10','NOSE_04_DT05');best='NOSE_04_DT05';comp=[pair]
    if 'NOSE_04_DT025' in by:best='NOSE_04_DT025';pair=compare('NOSE_04_DT05',best);comp.append(pair)
    s={'created_utc':now(),'iteration':'AIRCRAFT-A11','cases':r,'half_dt_comparisons':comp,'selected_short_case':best,'fallback_allowed':not (pair['impulse_pass'] and pair['energy_pass'] and by[best]['numerical_gates_pass']),'one_ms_extension_numerically_allowed':by['FREE_04']['all_declared_checks_pass'] and by[best]['numerical_gates_pass'] and pair['impulse_pass'] and pair['energy_pass'] and all(by[n]['numerical_gates_pass'] for n in pair['cases']),'initial_material_domain_pass':by[best]['material_domain_pass'],'physical_impact_qualified':False,'spatial_convergence_qualified':False}
    dump(OUT/'initial_stage_review.json',s);print({k:v for k,v in s.items() if k not in ['cases']},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','initial']);p.add_argument('--case',default='FREE_04');a=p.parse_args();audit(a.case) if a.action=='audit' else initial()
