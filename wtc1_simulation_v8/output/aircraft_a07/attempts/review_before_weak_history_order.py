"""Read saved native A06 fields; audit new A07 states without rerunning predecessors."""
import argparse,re,json
from pathlib import Path
import numpy as np
import audit_aircraft_a05 as inherited
from run_aircraft_a07 import ROOT,OUT,PREV,CFG,read,dump,sha,rel,now
from audit_aircraft_a05 import histories
def cached():
    d=PREV/'r1/ZERO_DM';z=np.load(d/'balance_history_SI.npz');H=histories(d/'A06_ZERO_DMT01.csv');T=H['time'];nr=len(T);r=z['energy_residual_J'][:nr];step=np.diff(r);j=int(np.argmin(step))+1
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY','HOURGLASS ENERGY','SPRING ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    nearby=np.flatnonzero((T>1.56)&(T<1.76));partkeys=[k for k in H if k.strip().endswith('KE')]
    event={'interval_ms':[float(T[j-1]),float(T[j])],'residual_increment_J':float(step[j-1]),'global_term_increments_J':{k:float(H[k][j]-H[k][j-1])*.001 for k in terms},'part_KE_increment_J':{k:float(H[k][j]-H[k][j-1])*.001 for k in partkeys},'contact_impulse_increment_Ns':(z['contact_impulse_Ns'][j]-z['contact_impulse_Ns'][j-1]).tolist()}
    table=[{'time_ms':float(T[i]),'residual_J':float(r[i]),'generated_J':float(z['generated_energy_J'][i]),'elastic_contact_J':float(H['ELASTIC CONTACT ENERGY'][i])*.001,'radome_KE_J':float(next(H[k] for k in H if k.startswith('REFERENCE_RADOME') and k.strip().endswith('KE'))[i])*.001} for i in nearby]
    S=np.load(d/'verified_states_SI.npz');samples=[];radome=np.array(read(d/'mesh.json')['radome_node_ids'])-1
    for i,t in enumerate(S['time_s']*1000):
        if 1.4<=t<=1.9:
            v=S['velocity_m_s'][i,radome];samples.append({'time_ms':float(t),'radome_velocity_x_range_m_s':[float(v[:,0].min()),float(v[:,0].max())],'radome_velocity_yz_max_m_s':float(np.linalg.norm(v[:,1:],axis=1).max()),'radome_nodes':len(radome),'nodal_mass_weighted_work_not_available':True})
    dump(OUT/'cached_A06_energy_diagnosis.json',{'created_utc':now(),'old_solver_reruns':0,'inputs':[{'path':rel(d/p),'sha256':sha(d/p)} for p in ['balance_history_SI.npz','verified_states_SI.npz','A06_ZERO_DMT01.csv']],'largest_saved_loss_interval':event,'nearby_history':table,'native_animation_samples':samples,'part_history_does_not_include_all_unassigned_ADMAS_KE':True,'no_added_mass':float(np.max(abs(H['ADDED MASS'])))==0,'external_work_zero':bool(np.all(H['EXTERNAL WORK']==0)),'cause_identified':False,'finding':'Loss concentrated in one saved20us interval; global/part KE and penalty contact energy change abruptly. Incomplete independent nodal/rotational energy attribution prevents identifying a contact-algorithm or constraint cause. No element erosion in retained states. Temporal coincidence is not causal proof.'})
    # Analytical candidate only: fixed total work per fracture area, max-opening unloading.
    f=read(CFG)['energy_contract_for_future_fracture'];E=f['E_MPa'];sig=f['sigma_MPa'];G=f['G_N_mm'];Lcrit=2*E*G/sig**2;L=5.;w0=sig*L/E;wf=2*G/sig;w=np.linspace(0,wf,100001);tr=np.where(w<=w0,E*w/L,sig*(wf-w)/(wf-w0));area=float(np.trapezoid(tr,w))
    def damage(peak):return 0. if peak<=w0 else 1. if peak>=wf else wf*(peak-w0)/(peak*(wf-w0))
    path=[0,w0,(w0+wf)/2,0,(w0+wf)/2,wf];peak=0.;rows=[]
    for q in path:peak=max(peak,q);D=damage(peak);rows.append({'opening_mm':q,'maximum_opening_history_mm':peak,'damage':D,'traction_MPa':(1-D)*E*q/L,'stored_energy_N_mm':.5*(1-D)*E*q*q/L})
    checks={'total_surface_work_matches_G':bool(abs(area-G)/G<1e-8),'same_peak_reload_no_new_damage':rows[2]['damage']==rows[4]['damage'],'complete_failure_zero_traction':rows[-1]['traction_MPa']==0,'candidate_length_admissible':w0<wf}
    dump(OUT/'future_fracture_energy_contract.json',{'created_utc':now(),'scope':'Analytical energy/history contract only, NOT a qualified native material or whole-radome transfer','properties':f,'maximum_admissible_Le_mm':Lcrit,'example_Le_mm':L,'opening_initiation_mm':w0,'opening_complete_mm':wf,'integrated_total_work_N_mm':area,'checks':checks,'path':rows,'elastic_storage_and_irreversible_work_must_be_tracked':True,'Le_and_actual_G_need_identification':True,'native_implementation_verified':False,'failure_transfer_enabled':False})
    print({'cached_A06_largest_loss':event['residual_increment_J'],'time':event['interval_ms'],'candidate_contract':checks})
def audit(caseid,revision):
    d=OUT/revision/caseid;g=read(d/'generation.json')
    def adapter(p):
        value=read(p)
        if Path(p)==d/'generation.json':value={**value,'beam_history_ids':sorted(value['beam_history_ids'])}
        return value
    inherited.OUT=OUT;inherited.CFG=CFG;inherited.PREV=PREV;inherited.read=adapter;r=inherited.audit(revision,caseid);z=np.load(d/'verified_states_SI.npz');H=histories(d/(g['name']+'T01.csv'));mesh=read(d/'mesh.json')
    engine=np.isin(z['part_ids'],range(22,28));nac=np.isin(z['part_ids'],[22,25]);cas=np.isin(z['part_ids'],[23,24,26,27]);history=np.load(d/'balance_history_SI.npz');nativeids=history['beam_element_ids'].tolist();pylon=np.array([nativeids.index(i) for i in range(11135,11139)]);B=history['beam_history_native'];js=np.array([nativeids.index(b[0]) for b in g['added_joint_beams']]);stress=np.maximum(z['shell_von_mises_upper_MPa'],z['shell_von_mises_lower_MPa']);engine_ids=np.array(g['added_engine_nodes'])-1
    native_listing=(d/(g['name']+'_0000.out')).read_text(encoding='utf-8',errors='replace');cg=re.search(r'TOTAL MASS AND MASS CENTER',native_listing)
    r.update(beam_history_scope=g['beam_history_scope'],engine_mass_budget_kg=9000.,engine_mass_ledger=g['engine_mass_ledger'],engine_shell_count=len(g['added_engine_shells']),engine_joint_count=len(g['added_joint_beams']),engine_inertial_hosts_do_not_include_wing_nodes=all(all(n in set(g['added_engine_nodes']) for n in ids) for ids in g['RBE3_engine_hosts'].values()),
        maximum_engine_shell_plastic_strain=float(z['shell_max_layer_plastic_strain'][:,engine].max()),maximum_nacelle_fiber_von_mises_MPa=float(stress[:,nac].max()),maximum_case_fiber_von_mises_MPa=float(stress[:,cas].max()),
        maximum_new_joint_force_N=float(np.linalg.norm(B[:,js,:3],axis=2).max()),maximum_pylon_force_N=float(np.linalg.norm(B[:,pylon,:3],axis=2).max()),maximum_pylon_moment_Nmm=float(np.linalg.norm(B[:,pylon,3:6],axis=2).max()),
        expected_aircraft_CG_mm=g['expected_aircraft_CG_mm'],contact_domain=g['case']['domain'],local_control_not_full_impact=g['local_contact_control_not_full_impact'],engine_fracture_or_crushing_qualified=False,engine_self_contact_enabled=False)
    r['checks']['engine_inertia_hosts_in_engine_only']=r['engine_inertial_hosts_do_not_include_wing_nodes'];r['checks']['engine_mass_partition_exact']=all(abs(q['assembly_total_kg']-4500)<1e-9 and q['dry_residual_kg']>=0 and q['external_residual_kg']>=0 for q in g['engine_mass_ledger']);r['checks']['engine_and_old_beam_history_retained']=B.shape[1]==len(g['beam_history_ids'])
    r['all_declared_checks_pass']=all(r['checks'].values());r['failed_checks']=[k for k,v in r['checks'].items() if not v]
    dump(d/'review.json',r);print({'case':caseid,'mass':r['native_total_mass_kg'],'Jx':r['final_contact_impulse_Ns'][0],'residual_J':r['final_energy_residual_J'],'failed':r['failed_checks'],'pylon_N':r['maximum_pylon_force_N']},flush=True)
def summary(revision):
    cfg=read(CFG);rs=[read(OUT/revision/c['id']/'review.json') for c in cfg['execution']['cases']];zz=[np.load(OUT/revision/c/'balance_history_SI.npz') for c in ['ENGINE_LOCAL','ENGINE_HALF']];t=min(z['time_s'][-1] for z in zz);J=[np.array([np.interp(t,z['time_s'],z['contact_impulse_Ns'][:,i]) for i in range(3)]) for z in zz];En=[float(np.interp(t,z['time_s'],z['generated_energy_J'])) for z in zz];jd=float(np.linalg.norm(J[1]-J[0])/max(np.linalg.norm(J[0]),1e-12));ed=abs(En[1]-En[0])/max(En[0],1e-12);limit=cfg['comparison_limits']
    comparisons={'common_time_ms':t*1000,'impulse_difference_fraction':jd,'generated_energy_difference_fraction':ed,'impulse_pass':jd<=limit['half_dt_impulse_fraction'],'energy_pass':ed<=limit['half_dt_generated_energy_fraction']}
    essential=['starter_zero_errors','starter_zero_warnings','main_engine_normal_termination','observer_normal_termination','observer_did_not_change_main_outputs','mass_preserved','native_original_connectivity_preserved','all_exported_states_finite','supports_fixed','no_erosion','no_external_work','engine_inertia_hosts_in_engine_only','engine_mass_partition_exact','engine_and_old_beam_history_retained']
    checks={'native_saved_integrity':all(all(r['checks'][k] for k in essential) for r in rs),'all_horizons_observed':all(r['requested_horizon_reached'] for r in rs),'cached_energy_diagnosis_preserved':(OUT/'cached_A06_energy_diagnosis.json').exists(),'failure_not_transferred':not cfg['failure_transfer_enabled']}
    dump(OUT/'case_selection.json',{'case_directories':{c['id']:revision+'/'+c['id'] for c in cfg['execution']['cases']}})
    s={'created_utc':now(),'cases':rs,'checks':checks,'integrity_only_pass':all(checks.values()),'all_declared_checks_pass':all(r['all_declared_checks_pass'] for r in rs) and comparisons['impulse_pass'] and comparisons['energy_pass'],'engine_local_half_dt_comparison':comparisons,'physical_impact_qualified':False,'engine_crush_or_fracture_qualified':False,'local_energy_ledger_fully_qualified':all(r['checks']['energy_local_within_declared_limit'] for r in rs),'spatial_convergence_qualified':False,'engine_spatial_sensitivity_tested':False,'old_solver_reruns':0,'NIST_outcomes_used_as_target':False,'failure_transfer_enabled':False};dump(OUT/'summary.json',s);print({k:s[k] for k in ['checks','all_declared_checks_pass','engine_local_half_dt_comparison']})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['cached','audit','summary']);p.add_argument('--case',default='FREE');p.add_argument('--revision',default='r0');a=p.parse_args()
    if a.action=='cached':cached()
    elif a.action=='audit':audit(a.case,a.revision)
    else:summary(a.revision)
