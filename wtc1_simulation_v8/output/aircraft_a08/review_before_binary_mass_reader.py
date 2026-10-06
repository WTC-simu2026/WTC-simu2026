"""A08 native coverage, segmented impulse, nodal and internal-inertia energy review."""
import argparse,re,subprocess
from pathlib import Path
import numpy as np
import audit_aircraft_a05 as inherited
from audit_aircraft_a05 import histories as native_histories,vtk
from audit_aircraft_a02 import numbers_after
from run_aircraft_a08 import ROOT,OUT,PREV,CFG,RUNTIME,read,dump,sha,rel,now,triangle
def segment_history(H):
    result={}
    for label in ['NACELLE','FAN','CORE']:
        k=[k for k in H if k.startswith('CONTACT_RAW_HISTORY_'+label)]
        if k:
            assert len(k)==4;result[label]=np.column_stack([H[q] for q in k[:3]])*.001
    return result
def audit_histories(p):
    H=native_histories(p);S=segment_history(H)
    if not S:return H
    # Explicit audit-only aggregate of disjoint native interfaces. Native CSV is untouched.
    agg=sum(S.values());result={k:v for k,v in H.items() if not k.startswith('CONTACT_RAW_HISTORY_')}
    for i in range(3):result['CONTACT_RAW_HISTORY A08_VERIFIED_INTERFACE_SUM '+str(i)]=agg[:,i]*1000
    return result
def audit(caseid):
    d=OUT/'r0'/caseid;g=read(d/'generation.json');n=g['name'];H=native_histories(d/(n+'T01.csv'));beamkeys=[k for k in H if k.startswith('FORWARD_BEAM_DIAGNOSTIC')];stream=[int(re.search(r'FORWARD_BEAM_DIAGNOSTIC\s+(\d+)\s+B',k).group(1)) for k in beamkeys[::9]];assert set(stream)==set(g['beam_history_ids']) and len(stream)==len(set(stream))
    def adapter(p):
        q=read(p)
        if Path(p)==d/'generation.json':q={**q,'beam_history_ids':stream}
        return q
    inherited.OUT=OUT;inherited.CFG=CFG;inherited.PREV=PREV;inherited.read=adapter;inherited.histories=audit_histories
    r=read(d/'audit.json') if (d/'audit.json').exists() else inherited.audit('r0',caseid)
    Ho=native_histories(d/'observer'/(n+'T02_recovered.csv'));assert list(H)==list(Ho);H={k:np.r_[v,Ho[k][0]] for k,v in H.items()};T=H['time'];S=segment_history(H)
    cov={};part={}
    for pid,title in g['part_titles'].items():
        found=[k for k in H if k.startswith(title+' ')];assert len(found)==9,(title,found)
        vals={k.strip().split()[-1]:H[k] for k in found};assert set(vals)==set(read(CFG)['output_contract']['part_channels']);cov[title]=list(vals);part[title]=vals
    nodkeys=[k for k in H if k.startswith('ENGINE_ADMAS_VELOCITY')];assert len(nodkeys)==96
    node_ids=[int(re.search(r'ENGINE_ADMAS_VELOCITY\s+(\d+)\s',k).group(1)) for k in nodkeys[::3]];assert set(node_ids)==set(range(2861,2893))
    nv=np.column_stack([H[k] for k in nodkeys]).reshape(len(T),32,3);m=np.array([g['engine_mass_ledger'][(ni-2861)//16]['admas_each_kg'] for ni in node_ids]);adKE=.5*np.sum(m[None,:,None]*nv**2,axis=(1,2));adP=np.sum(m[None,:,None]*nv,axis=1)
    partKE=sum(p['KE'] for p in part.values())*.001;partRKE=sum(p['RKE'] for p in part.values())*.001;partIE=sum(p['IE'] for p in part.values())*.001;partPW=sum(p['PW'] for p in part.values())*.001;partP=sum(np.column_stack([p[a+'MOM'] for a in 'XYZ']) for p in part.values())*.001
    z=np.load(d/'verified_states_SI.npz');animations=[ROOT/q['path'] for q in r['native_animations']];massrows=[];KE=[];P=[];native_m=None
    for file in animations:
        q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(file)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=60).stdout);order=np.argsort(q['NODE_ID']);keys=[k for k in q if 'mass' in k.lower() and len(q[k])==len(order)];assert len(keys)==1,keys
        nm=q[keys[0]][order]*.001;vv=q['Velocity'].reshape(-1,3)[order];KE.append(float(.5*np.sum(nm[:,None]*vv**2)));P.append(np.sum(nm[:,None]*vv,axis=0));massrows.append({'time_ms':q['time'],'native_mass_key':keys[0],'mass_kg':float(nm.sum())})
        if native_m is None:native_m=nm
        else:assert np.allclose(nm,native_m,rtol=1e-6,atol=1e-8)
    ts=z['time_s']*1000;assert np.allclose(ts,[q['time_ms'] for q in massrows],atol=1e-5)
    Ksaved=np.interp(ts,T,H['KINETIC ENERGY']*.001);KE=np.array(KE);P=np.array(P);Pglobal=np.column_stack([np.interp(ts,T,H[a+'-MOMENTUM']*.001) for a in 'XYZ']);dKE=(KE-KE[0])-(Ksaved-Ksaved[0]);dP=(P-P[0])-(Pglobal-Pglobal[0])
    local=read(CFG)['acceptance'];checks={'all_added_engine_part_native_channels':True,'all_32_engine_ADMAS_velocity_channels':True,'native_nodal_mass_matches_total':bool(abs(native_m.sum()-r['native_total_mass_kg'])/r['native_total_mass_kg']<1e-6),'native_nodal_mass_unchanged':True,'native_translational_KE_absolute_match_1e_6':bool(np.max(abs(KE-Ksaved))/Ksaved[0]<1e-6),'native_translational_delta_KE_match_1kJ_plus_1percent_generated':bool(np.all(abs(dKE)<=1000+.01*np.interp(ts,T,np.load(d/'balance_history_SI.npz')['generated_energy_J']))),'native_nodal_momentum_match_20Ns_plus_float32':bool(np.max(np.linalg.norm(dP,axis=1))<20+1e-6*np.linalg.norm(Pglobal[0])),'sum_engine_part_PW_nonnegative':bool(np.min(partPW)>-1e-3)}
    # Native masses for all nodes provide a global translation ledger. Engine component allocation below remains a separate element-based ledger.
    am=np.zeros((3,len(native_m)));x=np.array(read(d/'mesh.json')['nodes_mm'])
    for _,pid,tr in g['added_engine_shells']:
        v=x[np.array(tr)-1];area,w=triangle(v);mass=area*(2*2.78e-6 if pid in [22,25] else 5*7.86e-6);comp=0 if pid in [22,25] else 1 if pid in [23,26] else 2
        am[comp,np.array(tr)-1]+=mass*w
    engine_shell_K=np.array([.5*np.sum(am[None,:,:,None]*z['velocity_m_s'][:,None,:,:].astype(float)**2,axis=(2,3))])[0]
    bw=np.zeros(len(native_m))
    for _,_,a,b in g['added_joint_beams']:
        mass=np.linalg.norm(x[a-1]-x[b-1])*400*7.86e-6;bw[[a-1,b-1]]+=mass/2
    engine_beam_K=.5*np.sum(bw[None,:,None]*z['velocity_m_s'].astype(float)**2,axis=(1,2));localK=engine_shell_K.sum(axis=1)+engine_beam_K+np.interp(ts,T,adKE)
    native_engineK=np.interp(ts,T,partKE+adKE);localerr=float(np.max(abs(localK-native_engineK)))
    checks['engine_element_plus_ADMAS_translation_matches_native_parts_1kJ']=localerr<=1000
    Jtotal=np.load(d/'balance_history_SI.npz')['contact_impulse_Ns'];segment_end={k:(v[-1]-v[0]).tolist() for k,v in S.items()};segcheck=not S or np.allclose(sum((v-v[0] for v in S.values())),Jtotal,rtol=1e-8,atol=1e-9);checks['disjoint_contact_interface_sum_verified']=bool(segcheck)
    ledger=np.load(d/'balance_history_SI.npz');rr=ledger['energy_residual_J'];loss=int(np.argmin(np.diff(rr)))+1;terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY','HOURGLASS ENERGY','SPRING ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    event={'interval_ms':[float(T[loss-1]),float(T[loss])],'residual_increment_J':float(rr[loss]-rr[loss-1]),'native_global_term_increments_J':{k:float(H[k][loss]-H[k][loss-1])*.001 for k in terms},'engine_ADMAS_KE_increment_J':float(adKE[loss]-adKE[loss-1]),'engine_part_translation_KE_increment_J':float(partKE[loss]-partKE[loss-1]),'engine_part_rotation_KE_increment_J':float(partRKE[loss]-partRKE[loss-1]),'engine_part_IE_increment_J':float(partIE[loss]-partIE[loss-1]),'engine_part_PW_increment_J':float(partPW[loss]-partPW[loss-1])}
    listing=(d/(n+'_0000.out')).read_text(errors='replace');cg=np.array(numbers_after(listing,'TOTAL MASS AND MASS CENTER',4))[1:];oldcg=np.array(read(PREV/'additional_verification.json')['cases'][2]['native_total_CG_mm']);pred=oldcg+np.array(g['native_nodal_CG_moment_shift_kg_mm'])/r['native_total_mass_kg'];cgerr=float(np.max(abs(cg-pred)));checks['native_CG_refinement_predicted_1e_5_mm']=cgerr<1e-5
    engine=np.isin(z['part_ids'],range(22,28));ep=float(z['shell_max_layer_plastic_strain'][:,engine].max());checks={k:bool(v) for k,v in checks.items()}
    r.update(beam_history_scope='504 inherited forward beams,56 engine joints,4 pylons; IDs and9 canonical native channels individually matched',extra_checks=checks,part_channel_coverage=cov,contact_segment_final_impulses_Ns=segment_end,native_nodal_translation_KE_max_absolute_error_J=float(np.max(abs(KE-Ksaved))),native_nodal_translation_delta_KE_max_error_J=float(np.max(abs(dKE))),native_nodal_momentum_delta_max_error_Ns=float(np.max(np.linalg.norm(dP,axis=1))),engine_translation_KE_max_error_J=localerr,native_CG_refinement_error_mm=cgerr,maximum_engine_shell_plastic_strain=ep,largest_dense_saved_loss=event,native_mass_samples=massrows,energy_cause_identified=False,physical_impact_qualified=False,engine_crushing_qualified=False,engine_shell_count=len(g['added_engine_shells']),local_contact_control_not_full_impact=True)
    r['extra_checks_pass']=all(checks.values());r['all_declared_checks_pass']=r['all_declared_checks_pass'] and r['extra_checks_pass'];r['failed_checks']+=['extra:'+k for k,v in checks.items() if not v]
    np.savez_compressed(d/'independent_translation_engine_ledger.npz',time_s=T*.001,engine_ADMAS_KE_J=adKE,engine_ADMAS_momentum_Ns=adP,engine_part_KE_J=partKE,engine_part_RKE_J=partRKE,engine_part_IE_J=partIE,engine_part_PW_J=partPW,engine_part_momentum_Ns=partP,animation_time_s=z['time_s'],native_nodal_mass_kg=native_m,native_nodal_KE_J=KE,native_nodal_momentum_Ns=P,engine_shell_component_KE_J=engine_shell_K,engine_joint_KE_J=engine_beam_K,engine_local_translation_KE_J=localK)
    dump(d/'review.json',r);print({'case':caseid,'extra_checks':checks,'Jx':r['final_contact_impulse_Ns'][0],'residual_J':r['final_energy_residual_J'],'engine_plastic':ep,'dense_loss_J':event['residual_increment_J']},flush=True)
def summary():
    cfg=read(CFG);rows=[read(OUT/'r0'/c['id']/'review.json') for c in cfg['execution']['cases']];cmp=[]
    for a,b,label in [('DENSE','SPLIT','instrument'),('SPLIT','FINE','mesh'),('FINE','FINE_HALF','half_dt')]:
        z=[np.load(OUT/'r0'/v/'balance_history_SI.npz') for v in [a,b]];tc=min(q['time_s'][-1] for q in z);j=[np.array([np.interp(tc,q['time_s'],q['contact_impulse_Ns'][:,i]) for i in range(3)]) for q in z];e=[float(np.interp(tc,q['time_s'],q['generated_energy_J'])) for q in z];jd=float(np.linalg.norm(j[1]-j[0])/np.linalg.norm(j[0]));ed=abs(e[1]-e[0])/e[0];cmp.append({'comparison':label,'cases':[a,b],'common_time_ms':tc*1000,'impulse_difference_fraction':jd,'generated_energy_difference_fraction':ed,'impulse_pass':jd<=cfg['comparison_limits'][label+'_impulse_fraction'],'generated_energy_pass':ed<=cfg['comparison_limits'][label+'_generated_energy_fraction']})
    a=read(OUT/'r0/SPLIT/generation.json');b=read(OUT/'r0/FINE/generation.json');areaerr=max(abs(a['piecewise_surface_area_mm2_by_part'][p]-b['piecewise_surface_area_mm2_by_part'][p]) for p in a['piecewise_surface_area_mm2_by_part']);ess=['starter_zero_errors','starter_zero_warnings','main_engine_normal_termination','observer_normal_termination','observer_did_not_change_main_outputs','mass_preserved','native_original_connectivity_preserved','all_exported_states_finite','supports_fixed','no_erosion','no_external_work'];critical=['all_added_engine_part_native_channels','all_32_engine_ADMAS_velocity_channels','native_nodal_mass_matches_total','native_nodal_mass_unchanged','sum_engine_part_PW_nonnegative','disjoint_contact_interface_sum_verified','native_CG_refinement_predicted_1e_5_mm']
    checks={'saved_native_integrity':all(all(r['checks'][k] for k in ess) and all(r['extra_checks'][k] for k in critical) for r in rows),'all_horizons_observed':all(r['requested_horizon_reached'] for r in rows),'same_piecewise_engine_surface':areaerr<1e-6,'unchanged_RBE3_engine_hosts_and_joints':a['RBE3_engine_hosts']==b['RBE3_engine_hosts'] and a['added_joint_beams']==b['added_joint_beams'],'cached_A07_CG_resolved_without_model_change':read(OUT/'cached_A07_mass_output_review.json')['all_corrected_CG_gates_pass']}
    dump(OUT/'case_selection.json',{'case_directories':{c['id']:'r0/'+c['id'] for c in cfg['execution']['cases']}});s={'created_utc':now(),'cases':rows,'checks':checks,'integrity_only_pass':all(checks.values()),'comparisons':cmp,'engine_surface_area_max_error_mm2':areaerr,'all_declared_checks_pass':all(r['all_declared_checks_pass'] for r in rows) and all(c['impulse_pass'] and c['generated_energy_pass'] for c in cmp),'local_energy_ledger_fully_qualified':all(r['checks']['energy_local_within_declared_limit'] for r in rows),'engine_spatial_sensitivity_tested':True,'spatial_convergence_qualified':False,'physical_impact_qualified':False,'engine_crushing_qualified':False,'energy_cause_identified':False,'NIST_outcomes_used_as_target':False,'failure_transfer_enabled':False,'old_solver_reruns':0};dump(OUT/'summary.json',s);print({'summary_checks':checks,'comparisons':cmp,'all_declared_checks_pass':s['all_declared_checks_pass']},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','summary']);p.add_argument('--case',default='FREE');a=p.parse_args();audit(a.case) if a.action=='audit' else summary()
