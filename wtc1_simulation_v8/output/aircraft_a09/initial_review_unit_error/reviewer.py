"""Saved native A09 onset diagnostics. No solver rerun or outcome fitting."""
import argparse,re,subprocess
from pathlib import Path
import numpy as np
import audit_aircraft_a05 as inherited
from audit_aircraft_a05 import histories,vtk
from audit_aircraft_a02 import numbers_after
from review_aircraft_a08 import audit_histories,segment_history,binary_mass
from run_aircraft_a08 import triangle
from run_aircraft_a09 import ROOT,RUNTIME,OUT,PREV,CFG,EXT,read,dump,sha,rel,now,cases,guard

def audit(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');name=g['name'];assert not (d/'review.json').exists()
    H=histories(d/(name+'T01.csv'));bk=[k for k in H if k.startswith('FORWARD_BEAM_DIAGNOSTIC')]
    stream=[int(re.search(r'FORWARD_BEAM_DIAGNOSTIC\s+(\d+)\s+B',k).group(1)) for k in bk[::9]]
    assert len(stream)==len(set(stream)) and set(stream)==set(g['beam_history_ids'])
    def adapter(p):
        q=read(p);return {**q,'beam_history_ids':stream} if Path(p)==d/'generation.json' else q
    inherited.OUT=OUT;inherited.CFG=CFG;inherited.PREV=PREV;inherited.read=adapter;inherited.histories=audit_histories
    r=read(d/'audit.json') if (d/'audit.json').exists() else inherited.audit('r0',caseid)
    Ho=histories(d/'observer'/(name+'T02_recovered.csv'));assert list(H)==list(Ho)
    H={k:np.r_[v,Ho[k][0]] for k,v in H.items()};T=H['time'];z=np.load(d/'verified_states_SI.npz');ledger=np.load(d/'balance_history_SI.npz')
    nk=[k for k in H if k.startswith('ENGINE_NATIVE_VELOCITY_ROTATION')];N=len(g['dense_engine_diag_node_ids']);assert len(nk)==6*N
    ids=[int(re.search(r'ENGINE_NATIVE_VELOCITY_ROTATION\s+(\d+)\s+N',k).group(1)) for k in nk[::6]]
    assert len(ids)==len(set(ids)) and set(ids)==set(g['dense_engine_diag_node_ids'])
    for i,n in enumerate(ids):assert all(re.search(r'\s'+str(n)+r'\s+N'+str(n)+r'\s',k) for k in nk[i*6:i*6+6])
    nv=np.column_stack([H[k] for k in nk]).reshape(len(T),N,6);assert np.allclose(nv[0,:,:3],[-200,5,2]) and np.max(abs(nv[0,:,3:]))==0
    part={}
    for pid,title in g['part_titles'].items():
        found=[k for k in H if k.startswith(title+' ')];assert len(found)==9;part[int(pid)]={k.split()[-1]:H[k] for k in found}
        assert set(part[int(pid)])==set(['IE','KE','HE','PW','RKE','XMOM','YMOM','ZMOM','MASS'])
    # Kinetic translation uses actual native nodal masses, including redistribution by constraints.
    Ke=[];Ps=[];mass=[];proofs=[];ts=[]
    for row in r['native_animations']:
        p=ROOT/row['path'];q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=60).stdout)
        nm,proof=binary_mass(p,q);order=np.argsort(q['NODE_ID']);v=q['Velocity'].reshape(-1,3)[order];ts.append(q['time']);Ke.append(.5*np.sum(nm[:,None]*v*v));Ps.append(np.sum(nm[:,None]*v,axis=0));mass.append(nm);proofs.append(proof)
    ts=np.array(ts);nm=mass[0];assert np.allclose(ts,z['time_s']*1000,atol=1e-5)
    Kglobal=np.interp(ts,T,H['KINETIC ENERGY']*.001);Ke=np.array(Ke);Pglobal=np.column_stack([np.interp(ts,T,H[a+'-MOMENTUM']*.001) for a in 'XYZ']);Ps=np.array(Ps)
    dk=(Ke-Ke[0])-(Kglobal-Kglobal[0]);dp=(Ps-Ps[0])-(Pglobal-Pglobal[0])
    # Published theory page154, equations571-574: isotropic shell nodal inertia, angle/pi allocation.
    x=np.array(read(d/'mesh.json')['nodes_mm']);inertia=np.zeros(len(nm));shellmass=np.zeros(len(nm));beam_mass=np.zeros(len(nm));area={}
    for _,pid,tr in g['added_engine_shells']:
        idx=np.array(tr)-1;A,w=triangle(x[idx]);t=2 if pid in [22,25] else 5;rho=2.78e-6 if pid in [22,25] else 7.86e-6;m_g=rho*t*A
        inertia[idx]+=m_g*(2*A/6+t*t/12)*w;shellmass[idx]+=m_g*.001*w;area[pid]=area.get(pid,0.)+A
    for _,_,a,b in g['added_joint_beams']:
        m=np.linalg.norm(x[a-1]-x[b-1])*400*7.86e-6;beam_mass[[a-1,b-1]]+=m/2
    inertia_diag=inertia[np.array(ids)-1];Krot=.5*np.sum(inertia_diag[None,:,None]*nv[:,:,3:]**2,axis=(1,2))*.001
    shellR=sum(p['RKE'] for pid,p in part.items() if pid in range(22,28))*.001
    rot_error=float(np.max(abs(Krot-shellR)));extra=read(CFG)['acceptance_extra'];rot_limit=extra['native_shell_rotation_absolute_allowance_J']+extra['native_shell_rotation_relative_fraction']*abs(shellR)
    dep=[k for k in H if k.startswith('ENGINE_ADMAS_VELOCITY')];assert len(dep)==96
    depids=[int(re.search(r'ENGINE_ADMAS_VELOCITY\s+(\d+)\s',k).group(1)) for k in dep[::3]];depv=np.column_stack([H[k] for k in dep]).reshape(len(T),32,3)
    assert set(depids)==set(range(2861,2893));denseK=.5*np.sum(nm[np.array(ids)-1][None,:,None]*nv[:,:,:3]**2,axis=(1,2))+.5*np.sum(nm[np.array(depids)-1][None,:,None]*depv**2,axis=(1,2))
    redis=np.zeros(len(nm));ei=np.array(g['added_engine_nodes'])-1;redis[ei]=nm[ei]-shellmass[ei]-beam_mass[ei];expected=sum(16*p['admas_each_kg'] for p in g['engine_mass_ledger'])
    shellpartK=sum(p['KE'] for pid,p in part.items() if pid in range(22,28))*.001
    rawbeamR=part[28]['RKE']*.001
    PWh=H['PLASTIC WORK']*.001;rr=ledger['energy_residual_J'];loss=int(np.argmin(np.diff(rr)))+1;terms=r['energy_terms_without_double_counting']
    event={'interval_ms':[float(T[loss-1]),float(T[loss])],'residual_increment_J':float(rr[loss]-rr[loss-1]),'native_global_term_increments_J':{k:float(H[k][loss]-H[k][loss-1])*.001 for k in terms},'global_PW_J':[float(PWh[loss-1]),float(PWh[loss])],'engine_dense_translation_KE_increment_J':float(denseK[loss]-denseK[loss-1]),'engine_independent_shell_rotation_increment_J':float(Krot[loss]-Krot[loss-1]),'engine_shell_part_translation_increment_J':float(shellpartK[loss]-shellpartK[loss-1])}
    # /TH/NODE REAC is a force: use force integral for this new review; retain the inherited ambiguous diagnostic.
    js=ledger['support_as_force_integral_Ns'];p=ledger['global_momentum_Ns'];pf=ledger['facade_momentum_Ns'];j=ledger['contact_impulse_Ns'];mtol=r['momentum_allowance_Ns'];gp=float(np.max(np.linalg.norm(p-p[0]-js,axis=1)));fp=float(np.max(np.linalg.norm(pf-pf[0]-j-js,axis=1)))
    listing=(d/(name+'_0000.out')).read_text(errors='replace');penalty_count=re.findall(r'(\d+)\s+OF RBE3 HAVE BEEN SWITCHED TO PENALTY METHOD',listing)
    cg=np.array(numbers_after(listing,'TOTAL MASS AND MASS CENTER',4))[1:]
    parent=PREV/'r0'/g['case']['parent'];pn=read(parent/'generation.json')['name'];pcg=np.array(numbers_after((parent/(pn+'_0000.out')).read_text(errors='replace'),'TOTAL MASS AND MASS CENTER',4))[1:]
    # Compare native double-precision Starter CG to parent Starter, not float32 ANIM mass centroid.
    checks={'dense_node_ids_and_6_requested_channels':True,'initial_angular_velocity_zero':True,'native_nodal_mass_total':bool(abs(nm.sum()-r['native_total_mass_kg'])/r['native_total_mass_kg']<1e-6),'native_nodal_mass_constant':all(bool(np.allclose(m,nm,rtol=1e-6,atol=1e-8)) for m in mass),'independent_delta_translation_KE':bool(np.all(abs(dk)<=1000+.01*np.interp(ts,T,ledger['generated_energy_J']))),'independent_delta_momentum':bool(np.max(np.linalg.norm(dp,axis=1))<20+1e-6*np.linalg.norm(Pglobal[0])),'independent_shell_rotation_matches_native':bool(np.all(abs(Krot-shellR)<=rot_limit)),'redistributed_engine_mass_sum':bool(abs(redis.sum()-expected)<1e-4),'support_force_integral_global':gp<mtol,'support_force_integral_facade':fp<mtol,'penalty_option_confirmed_by_Starter':g['case']['engine_RBE3_Iform']!=3 or penalty_count==['32'],'native_CG_unchanged_vs_parent':bool(np.max(abs(cg-pcg))<extra['native_historical_CG_error_mm'])}
    engine=np.isin(z['part_ids'],range(22,28));eps=float(z['shell_max_layer_plastic_strain'][:,engine].max());S=segment_history(H)
    r.update(extra_checks=checks,extra_checks_pass=all(checks.values()),maximum_engine_shell_plastic_strain=eps,engine_shell_count=len(g['added_engine_shells']),largest_dense_saved_loss=event,independent_translation_delta_KE_error_J=float(np.max(abs(dk))),independent_momentum_delta_error_Ns=float(np.max(np.linalg.norm(dp,axis=1))),independent_shell_rotation_max_error_J=rot_error,independent_shell_rotation_final_J=float(Krot[-1]),native_shell_rotation_final_J=float(shellR[-1]),native_global_rotation_final_J=float(H['ROTATION ENERGY'][-1])*.001,initial_raw_beam_part_RKE_J=float(rawbeamR[0]),raw_beam_part_RKE_semantics_qualified=False,shell_rotation_formula='I=m_g*(2*A_mm2/6+t_mm^2/12), nodal angle/pi; omega rad/ms, .5Iomega^2*0.001 J. Engine triangle shells only, beams excluded.',dense_translation_scope='New engine shell/hub and32 dependent nodes, actual native masses; not a closed subdomain work ledger.',support_units_independently_distinguished=True,support_channel_units='N, integrate time_ms then multiply0.001 for Ns',support_force_global_error_Ns=gp,support_force_facade_error_Ns=fp,maximum_native_angular_velocity_rad_ms=float(np.max(abs(nv[:,:,3:]))),native_penalty_RBE3_count=penalty_count,contact_segment_final_impulses_Ns={k:(v[-1]-v[0]).tolist() for k,v in S.items()},actual_surface_area_mm2_by_part=area,energy_cause_identified=False,physical_impact_qualified=False)
    r['all_declared_checks_pass']=r['all_declared_checks_pass'] and all(checks.values());r['failed_checks']+=['extra:'+k for k,v in checks.items() if not v]
    np.savez_compressed(d/'independent_engine_diagnostic.npz',time_s=T*.001,diag_node_ids=np.array(ids),native_velocity_m_s=nv[:,:,:3],native_angular_velocity_rad_s=nv[:,:,3:]*1000,native_engine_nodal_translation_J=denseK,independent_engine_shell_rotation_J=Krot,native_engine_shell_part_rotation_J=shellR,native_beam_part_rotation_raw_unqualified_J=rawbeamR,native_nodal_mass_kg=nm,native_engine_redistributed_mass_kg=redis,engine_shell_nodal_inertia_kg_m2=inertia*1e-9,animation_time_s=ts*.001,independent_global_translation_J=Ke,independent_global_momentum_Ns=Ps)
    dump(d/'native_mass_reader_proofs.json',{'samples':proofs});dump(d/'review.json',r);print({'case':caseid,'failed':r['failed_checks'],'Jx_Ns':r['final_contact_impulse_Ns'][0],'residual_J':r['final_energy_residual_J'],'generated_J':r['final_generated_energy_J'],'shell_rotation_error_J':rot_error,'largest_loss_J':event['residual_increment_J']},flush=True)

def summary():
    rows=[read(OUT/'r0'/c['id']/'review.json') for c in cases()];cfg=read(CFG);cmp=[]
    def compare(a,b,label,old=False):
        zz=[np.load((PREV/'r0'/a if old else OUT/'r0'/a)/'balance_history_SI.npz'),np.load(OUT/'r0'/b/'balance_history_SI.npz')];tc=min(q['time_s'][-1] for q in zz);J=[np.array([np.interp(tc,q['time_s'],q['contact_impulse_Ns'][:,i]) for i in range(3)]) for q in zz];G=[float(np.interp(tc,q['time_s'],q['generated_energy_J'])) for q in zz];jd=float(np.linalg.norm(J[1]-J[0])/max(np.linalg.norm(J[0]),1e-12));ed=abs(G[1]-G[0])/max(G[0],1e-12)
        limits=cfg['comparison_limits'];gated=label in ['instrument','mesh'];cmp.append({'comparison':label,'cases':[('A08/' if old else '')+a,b],'common_time_ms':tc*1000,'impulse_difference_fraction':jd,'generated_energy_difference_fraction':ed,'declared_acceptance_comparison':gated,'impulse_pass':jd<=limits[label+'_impulse_fraction'] if gated else None,'generated_energy_pass':ed<=limits[label+'_generated_energy_fraction'] if gated else None})
    compare('FINE','BASE_FINE','instrument',True)
    for b in ['SERIES_FINE','SOFT_FINE','PENALTY_FINE','EFFECTIVE_FINE_01','EFFECTIVE_FINE_001']:compare('BASE_FINE',b,b)
    compare('EFFECTIVE_COARSE_001','EFFECTIVE_FINE_001','mesh')
    def raw_pair(a,b):
        out=[]
        for c in [a,b]:
            d=OUT/'r0'/c;name=read(d/'generation.json')['name'];H=histories(d/(name+'T01.csv'));Ho=histories(d/'observer'/(name+'T02_recovered.csv'));out.append({k:np.r_[v,Ho[k]] for k,v in H.items()})
        assert list(out[0])==list(out[1]);return [k for k in out[0] if not np.array_equal(out[0][k],out[1][k])]
    identical={'Stfac0.1_vs1_fine':raw_pair('BASE_FINE','SOFT_FINE'),'penalty_vs_kinematic_fine':raw_pair('BASE_FINE','PENALTY_FINE')}
    essential=['starter_zero_errors','starter_zero_warnings','main_engine_normal_termination','observer_normal_termination','observer_did_not_change_main_outputs','mass_preserved','native_original_connectivity_preserved','all_exported_states_finite','supports_fixed','no_erosion','no_external_work','native_end_timestamp_observed_within_step']
    robust=['dense_node_ids_and_6_requested_channels','initial_angular_velocity_zero','native_nodal_mass_total','native_nodal_mass_constant','penalty_option_confirmed_by_Starter','native_CG_unchanged_vs_parent']
    integrity=all(all(r['checks'][k] for k in essential) and all(r['extra_checks'][k] for k in robust) for r in rows)
    source_note={'TYPE7_formula':'Km=Stfac*Em*tm; Ks=Es*ts for attached secondary shell. Istf4 min(Km,Ks), Istf5 Km*Ks/(Km+Ks), then clamping/2. Thus Stfac scales main stiffness only. Exact spatial active contact stiffness is not assumed equal across triangles.','RBE3':'Iform3 changes32 engine constraints to penalty, native Starter explicitly confirms32. Lack of measured response before fan contact is not evidence the flag was ignored.','TH_NODE':'REAC is force; new balance integrates it. In this short interval reaction output is zero, so it cannot distinguish the old two interpretations by observation. VR channels rad/ms, no claim that each angular-axis order is independently calibrated; isotropic norm unaffected by permutation.','extension':'Effective factors0.01/0.001 separately predeclared after0.1 was observed inactive, no material/gate changes, all initial controls retained.','whole_chain_qualified':False}
    dump(OUT/'source_interpretation.json',source_note);dump(OUT/'case_selection.json',{'case_directories':{c['id']:'r0/'+c['id'] for c in cases()}})
    s={'created_utc':now(),'iteration':'AIRCRAFT-A09','cases':rows,'comparisons':cmp,'exact_saved_native_history_pair_different_channels':identical,'integrity_only_pass':integrity,'all_declared_checks_pass':all(r['all_declared_checks_pass'] for r in rows) and all(q['impulse_pass'] and q['generated_energy_pass'] for q in cmp if q['declared_acceptance_comparison']),'local_energy_ledger_fully_qualified':all(r['checks']['energy_local_within_declared_limit'] for r in rows),'spatial_convergence_qualified':False,'physical_impact_qualified':False,'engine_crushing_qualified':False,'energy_cause_identified':False,'NIST_outcomes_used_as_target':False,'failure_transfer_enabled':False,'old_solver_reruns':0,'initial_controls_retained':True}
    dump(OUT/'authoritative_review.json',s);print({'integrity':integrity,'comparisons':cmp,'different_channels':identical,'all_declared_pass':s['all_declared_checks_pass']},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['audit','summary']);p.add_argument('--case',default='BASE_FINE');a=p.parse_args();audit(a.case) if a.action=='audit' else summary()
