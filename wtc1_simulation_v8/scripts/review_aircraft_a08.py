"""A08 native coverage, segmented impulse, nodal and internal-inertia energy review."""
import argparse,re,subprocess
from pathlib import Path
import numpy as np
import audit_aircraft_a05 as inherited
from audit_aircraft_a05 import histories as native_histories,vtk
from audit_aircraft_a02 import numbers_after
from run_aircraft_a08 import ROOT,OUT,PREV,CFG,RUNTIME,read,dump,sha,rel,now,triangle
def binary_mass(file,q):
    # Own prefix reader of documented FASTMAGI10 layout. Validate adjacent data independently against native converter.
    b=file.read_bytes();off=0
    def take(n,dtype):
        nonlocal off
        v=np.frombuffer(b,dtype=dtype,count=n,offset=off).copy();off+=n*np.dtype(dtype).itemsize;return v
    assert take(1,'>i4')[0]==0x542c;tm=take(1,'>f4')[0];off+=243;flags=take(10,'>i4');nn,nf,npart,nfun,nefun,nvec,nten,nsk=take(8,'>i4');assert flags[0]==1 and flags[1]==1
    off+=int(nsk)*12;coords=take(int(nn)*3,'>f4').reshape(-1,3);conn=take(int(nf)*4,'>i4');off+=int(nf)+int(npart)*4+int(npart)*50+int(nn)*6
    off+=int(nfun+nefun)*81;off+=int(nfun*nn+nefun*nf)*4
    labels=[b[off+81*i:off+81*(i+1)].decode('ascii').rstrip('\x00 ') for i in range(int(nvec))];off+=int(nvec)*81;vec=take(int(nvec*nn)*3,'>f4').reshape(nvec,nn,3)
    off+=int(nten)*81+int(nten*nf)*3*4;em=take(int(nf),'>f4');nm=take(int(nn),'>f4');ids=take(int(nn),'>i4');eids=take(int(nf),'>i4');order=np.argsort(ids);vq=q['NODE_ID'].astype(int);qorder=np.argsort(vq)
    assert abs(float(tm)-q['time'])<1e-5 and np.array_equal(ids[order],vq[qorder]);assert np.allclose(coords[order],q['points'].reshape(-1,3)[qorder],rtol=5e-6,atol=1e-6)
    vi=next(i for i,k in enumerate(labels) if k.lower().startswith('velocity'));assert np.allclose(vec[vi][order],q['Velocity'].reshape(-1,3)[qorder],rtol=5e-6,atol=1e-6)
    assert np.all(np.isfinite(nm)) and np.all(nm>=0);assert set(eids[eids>0]).issubset(set(q['ELEMENT_ID'].astype(int)))
    return nm[order].astype(float)*.001,{'magic':int(0x542c),'flags':flags.tolist(),'nodal_mass_offset_bytes':off-int(nf)*4-int(nn)*8,'all_node_ID_coordinates_velocity_checked_against_native_converter':True,'read_only':True}
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
        q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(file)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=60).stdout);order=np.argsort(q['NODE_ID']);nm,proof=binary_mass(file,q)
        vv=q['Velocity'].reshape(-1,3)[order];KE.append(float(.5*np.sum(nm[:,None]*vv**2)));P.append(np.sum(nm[:,None]*vv,axis=0));massrows.append({'time_ms':q['time'],'native_mass_key':'FASTMAGI10 nMassA, present in native ANIM, omitted by installed VTK converter','mass_kg':float(nm.sum()),'reader_validation':proof})
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
def recheck():
    assert not (OUT/'authoritative_review.json').exists();s=read(OUT/'summary.json');rows=[];areas={}
    for r in s['cases']:
        case=r['case']['id'];d=OUT/'r0'/case;g=read(d/'generation.json');x=np.array(read(d/'mesh.json')['nodes_mm']);st=np.load(d/'verified_states_SI.npz');v=st['velocity_m_s'].astype(float);z=np.load(d/'independent_translation_engine_ledger.npz');nm=z['native_nodal_mass_kg'];m=np.zeros(len(nm));meq=np.zeros(len(nm));be=np.zeros(len(nm));area={}
        for _,p,tr in g['added_engine_shells']:
            a,w=triangle(x[np.array(tr)-1]);mass=a*(2*2.78e-6 if p in [22,25] else 5*7.86e-6);m[np.array(tr)-1]+=mass*w;meq[np.array(tr)-1]+=mass/3;area[p]=area.get(p,0.)+a
        for _,_,a,b in g['added_joint_beams']:
            mass=np.linalg.norm(x[a-1]-x[b-1])*400*7.86e-6;be[[a-1,b-1]]+=mass/2
        ids=np.array(g['added_engine_nodes'])-1;redis=np.zeros(len(nm));redis[ids]=nm[ids]-m[ids]-be[ids];expected=sum(16*q['admas_each_kg'] for q in g['engine_mass_ledger']);masserr=float(redis.sum()-expected)
        H=native_histories(d/(g['name']+'T01.csv'));Ho=native_histories(d/'observer'/(g['name']+'T02_recovered.csv'));H={k:np.r_[vv,Ho[k]] for k,vv in H.items()};ts=st['time_s']*1000;sh=sum(vv for k,vv in H.items() if k.startswith('A08_') and not k.startswith('A08_JOINTS ') and k.strip().endswith(' KE'))*.001;beamRKE=next(vv for k,vv in H.items() if k.startswith('A08_JOINTS ') and k.strip().endswith(' RKE'))*.001
        keeq=.5*np.sum(meq[None,:,None]*v*v,axis=(1,2));sherr=float(np.max(abs(keeq-np.interp(ts,H['time'],sh))));hostKE=.5*np.sum(redis[None,:,None]*v*v,axis=(1,2));pointKE=np.interp(st['time_s'],z['time_s'],z['engine_ADMAS_KE_J']);diff=hostKE-pointKE
        checks={'actual_coplanar_area_recomputed_once':True,'engine_dependent_ADMAS_nodes_zero_native_mass':bool(np.max(abs(nm[2860:2892]))==0),'engine_ADMAS_mass_found_on_hosts':abs(masserr)<1e-4,'redistributed_nodal_mass_nonnegative_with_rounding':bool(redis[ids].min()>-1e-5),'native_shell_part_KE_matches_equal_thirds_within_50J':sherr<50,'native_beam_part_RKE_compatible_with_global_initial_rotation':bool(abs(beamRKE[0]-H['ROTATION ENERGY'][0]*.001)<1000)}
        loss=r['largest_dense_saved_loss'];i=np.searchsorted(H['time'],loss['interval_ms'][1]);assert abs(H['time'][i]-loss['interval_ms'][1])<1e-8
        row={'case':case,'checks':checks,'actual_surface_area_mm2_by_part':area,'old_generator_area_metadata_double_counted_coarse':not g['case']['fine'],'engine_ADMAS_expected_mass_kg':expected,'native_redistributed_ADMAS_mass_kg':float(redis.sum()),'redistributed_mass_error_kg':masserr,'native_shell_part_equal_thirds_KE_max_error_J':sherr,'initial_native_beam_part_RKE_J':float(beamRKE[0]),'initial_native_global_rotation_J':float(H['ROTATION ENERGY'][0])*.001,'raw_beam_RKE_semantics_qualified':False,'redistributed_host_minus_original_point_KE_J':diff.tolist(),'largest_loss_interval_global_PW_J':[float(H['PLASTIC WORK'][i-1])*.001,float(H['PLASTIC WORK'][i])*.001],'largest_loss_before_plastic_work':bool(H['PLASTIC WORK'][i]==0),'native_mass_output_initial_CG_mm':(nm@x/nm.sum()).tolist(),'finding':'Native mass is redistributed away from RBE3 dependent ADMAS points onto hosts. Element-based shell PART KE matches equal-third allocation, while native global nodal mass uses angle-weighted allocation; sums are different definitions. Beam PART RKE is inconsistent with zero initial global rotation and cannot be added to a physical ledger. Neither observation alone identifies the cause of the global contact energy deficit.'};rows.append(row);areas[case]=area
        np.savez_compressed(d/'redistributed_engine_inertia_ledger.npz',animation_time_s=st['time_s'],native_redistributed_engine_ADMAS_mass_kg=redis,redistributed_host_KE_J=hostKE,original_point_KE_J=pointKE,host_minus_point_KE_J=diff,equal_third_shell_KE_J=keeq)
    areaerr=max(abs(areas['SPLIT'][p]-areas['FINE'][p]) for p in areas['SPLIT']);checks={'same_engine_piecewise_surface_independently_verified':areaerr<1e-6,'native_inertia_and_shell_reporting_semantics_verified':all(all(v for k,v in r['checks'].items() if k!='native_beam_part_RKE_compatible_with_global_initial_rotation') for r in rows),'suspect_beam_RKE_retained_and_not_used_in_global_energy':all(not r['raw_beam_RKE_semantics_qualified'] for r in rows)}
    checks={k:bool(v) for k,v in checks.items()}
    dump(OUT/'additional_verification.json',{'created_utc':now(),'checks':checks,'pass':all(checks.values()),'cases':rows,'actual_surface_area_max_difference_mm2':areaerr,'old_solver_reruns':0,'first_summary_and_failed_checks_preserved':True,'geometry_and_material_changes':False})
    s['checks']['same_piecewise_engine_surface']=checks['same_engine_piecewise_surface_independently_verified'];s['checks']['independent_native_output_semantics_review']=all(checks.values());s.update(created_utc=now(),integrity_only_pass=all(s['checks'].values()),engine_surface_area_max_error_mm2=areaerr,additional_verification=rel(OUT/'additional_verification.json'),first_summary_preserved=True,beam_part_RKE_semantics_qualified=False,all_declared_checks_pass=False);dump(OUT/'authoritative_review.json',s);print({'additional_checks':checks,'actual_area_error_mm2':areaerr,'shell_part_KE_errors_J':[r['native_shell_part_equal_thirds_KE_max_error_J'] for r in rows],'beam_RKE_initial_J':[r['initial_native_beam_part_RKE_J'] for r in rows],'host_minus_point_KE_final_J':[r['redistributed_host_minus_original_point_KE_J'][-1] for r in rows]},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','summary','recheck']);p.add_argument('--case',default='FREE');a=p.parse_args();audit(a.case) if a.action=='audit' else globals()[a.action]()
