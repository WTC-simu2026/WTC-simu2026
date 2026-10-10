"""A15 native impact outputs: ledgers, material limits and solver-driven geometry."""
import argparse,json,re,subprocess
from pathlib import Path
import numpy as np
from run_aircraft_a15 import ROOT,OUT,CFG,RUNTIME,read,dump,rel,now,guard,cases,streamsha
from audit_aircraft_a05 import histories,vtk,vm_tensor
from audit_aircraft_a03 import topology
from review_aircraft_a08 import binary_mass
from audit_aircraft_a02 import numbers_after

def segments(H):
    out={}
    for label in ['AIRFRAME','NACELLE','FAN','CORE']:
        k=[k for k in H if k.startswith('CONTACT_RAW_HISTORY_'+label+' ')];assert len(k)==4
        out[label]=np.column_stack([H[z] for z in k[:3]])*.001
    return out

def audit(case):
    guard();d=OUT/'r0'/case['id'];g=read(d/'generation.json');m=read(d/'mesh.json');name=g['name'];cfg=read(CFG);a=cfg['acceptance'];assert not (d/'review.json').exists()
    H=histories(d/(name+'T01.csv'));Ho=histories(d/'observer'/(name+'T02_recovered.csv'));T=H['time'];S=segments(H);J=sum(S.values());J-=J[0]
    P=np.column_stack([H[z+'-MOMENTUM'] for z in 'XYZ'])*.001
    Pf=np.column_stack([sum((H[k] for k in H if k.startswith('FACADE_') and k.strip().endswith(z+'MOM')),np.zeros(len(T))) for z in 'XYZ'])*.001
    Js=np.column_stack([sum((H[k] for k in H if k.startswith('SUPPORT_IMPULSE_'+z)),np.zeros(len(T))) for z in 'XYZ'])*.001;Js-=Js[0]
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(H[k] for k in terms)*.001;E0=float(E[0]);R=E-E0-H['EXTERNAL WORK']*.001
    G=sum(H[k] for k in terms if k!='KINETIC ENERGY')*.001
    finalE=sum(float(Ho[k][0]) for k in terms)*.001;finalR=finalE-E0-float(Ho['EXTERNAL WORK'][0])*.001;finalG=sum(float(Ho[k][0]) for k in terms if k!='KINETIC ENERGY')*.001
    RR=np.r_[R,finalR];GG=np.r_[G,finalG];window=GG>a['local_energy_comparison_minimum_J'];mass=numbers_after((d/(name+'_0000.out')).read_text(errors='replace'),'TOTAL MASS AND MASS CENTER',4)[0]*.001
    jmax=float(np.max(np.linalg.norm(J,axis=1)));mtol=a['momentum_absolute_allowance_Ns']+a['momentum_relative_allowance']*jmax
    ge=float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)));fe=float(np.max(np.linalg.norm(Pf-Pf[0]-J-Js,axis=1)))
    end=float(Ho['time'][0]);step=float(Ho['TIME STEP'][0]);onsets={k:float(T[np.flatnonzero(np.linalg.norm(v-v[0],axis=1)>0)[0]]) if np.any(v-v[0]) else None for k,v in S.items()}
    x0=np.array(m['nodes_mm']);air=np.array(m['aircraft_node_ids'])-1;fa=np.array(g['facade_translated_node_ids'])-1;fix=np.array(m['fixed_node_ids'])-1
    times=[];D=[];V=[];EPS=[];VM=[];rows=[];proofs=[];KE=[];PP=[];nm0=None;cellinfo=None;fixederr=0.;coorderr=0.;unchanged=True;maxeps=0.;maxratio=0.;topcheck=True
    # A priori regular sampling of stored native states; all original animation files retained and hashed.
    available=sorted(p for p in d.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name))
    files=[p for i,p in enumerate(available) if i%5==0 or i==len(available)-1]+sorted(p for p in (d/'observer').glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name))
    for file in files:
        proc=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(file)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=120);q=vtk(proc.stdout);tm=q['time']
        if times and abs(tm-times[-1])<1e-6:continue
        if tm>end+1e-5:continue
        assert not times or tm>times[-1];order=np.argsort(q['NODE_ID']);assert np.array_equal(q['NODE_ID'][order],np.arange(1,len(x0)+1))
        u=q['Displacement'].reshape(-1,3)[order];v=q['Velocity'].reshape(-1,3)[order];nm,pf=binary_mass(file,q);proofs.append({'time_ms':tm,'file':rel(file),**pf})
        if nm0 is None:
            nm0=nm;cells=topology(q);cellinfo={k:q[qk].astype(int) for k,qk in [('element_ids','ELEMENT_ID'),('part_ids','PART_ID'),('cell_types','types')]};index={int(e):i for i,e in enumerate(q['ELEMENT_ID']) if e>0}
            for i,t in enumerate(q['types']):
                if t==5:assert cells[i][-1]==cells[i][-2];cells[i]=cells[i][:3]
            topcheck=all(cells[index[eid]]==el for k,ei in [('original_triangle_node_ids',m['aircraft_triangle_ids']),('original_beam_node_ids',m['aircraft_beam_ids']),('facade_quads_node_ids',range(20001,20001+len(m['facade_quads_node_ids'])))] for eid,el in zip(ei,m[k]))
        else:
            unchanged=unchanged and np.array_equal(nm0,nm);assert np.array_equal(q['ELEMENT_ID'].astype(int),cellinfo['element_ids'])
        assert np.all(q['EROSION_STATUS']==1)
        epkeys=[k for k in q if 'Plast_Strn_Layer_' in k];eps=np.max(np.vstack([q[k] for k in epkeys]),axis=0);rm=cellinfo['part_ids']==21;steel=cellinfo['cell_types']==9;metal=(cellinfo['cell_types']==5)&~rm
        tensors=[q[k].reshape(-1,3,3)[rm] for k in ['2DELEM_Stress_(upper)','2DELEM_Stress_(lower)']];ev=np.concatenate([np.linalg.eigvalsh(t[:,:2,:2]).ravel() for t in tensors]);ratio=max(float(ev.max(initial=0))/cfg['sandwich']['face']['diagnostic_tension_MPa'],float((-ev).max(initial=0))/cfg['sandwich']['face']['diagnostic_compression_MPa'])
        maxratio=max(maxratio,ratio);maxeps=max(maxeps,float(eps.max()));fixederr=max(fixederr,float(np.max(abs(u[fix]))));coorderr=max(coorderr,float(np.max(abs(q['points'].reshape(-1,3)[order]-x0-u))))
        assert all(np.isfinite(z).all() for z in [u,v,eps,q['2DELEM_Von_Mises']]);KE.append(float(.5*np.sum(nm[:,None]*v*v)));PP.append(np.sum(nm[:,None]*v,axis=0))
        rows.append({'time_ms':tm,'max_metal_aircraft_plastic_strain':float(eps[metal].max(initial=0)),'max_facade_plastic_strain':float(eps[steel].max(initial=0)),'max_radome_plastic_strain':float(eps[rm].max(initial=0)),'radome_face_reference_strength_ratio':ratio,'maximum_facade_displacement_mm':float(np.max(np.linalg.norm(u[fa],axis=1))),'maximum_nose_displacement_mm':float(np.max(np.linalg.norm(u[np.array(m['radome_node_ids'])-1],axis=1)))})
        times.append(tm);D.append(u.astype(np.float32)*.001);V.append(v.astype(np.float32));EPS.append(eps.astype(np.float32));VM.append(q['2DELEM_Von_Mises'].astype(np.float32))
        print({'case':case['id'],'review_state_ms':round(tm,4)},flush=True)
    assert len(times)>1 and abs(times[-1]-end)<1e-5
    times=np.array(times);KE=np.array(KE);PP=np.array(PP);kg=np.interp(times,T,H['KINETIC ENERGY']*.001);pg=np.column_stack([np.interp(times,T,P[:,i]) for i in range(3)])
    # The final global values use the observed principal end, but support/contact remain main-history only.
    kg[-1]=float(Ho['KINETIC ENERGY'][0])*.001;pg[-1]=[float(Ho[z+'-MOMENTUM'][0])*.001 for z in 'XYZ'];dk=(KE-KE[0])-(kg-kg[0]);dp=(PP-PP[0])-(pg-pg[0])
    bkeys=[k for k in H if k.startswith('FORWARD_BEAM_DIAGNOSTIC')];B=np.column_stack([H[k] for k in bkeys]).reshape(len(T),len(g['beam_history_ids']),9);beam_eps=float(B[:,:,8].max())
    checks={'native_binary_CSV':read(d/'history_recovery.json')['pass'],'normal_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(),'requested_horizon_reached':end>=case['end_ms'] and end-case['end_ms']<=a['final_timestamp_overshoot_native_step_factor']*step,'original_connectivity':topcheck,'finite_native_states':True,'all_boundary_supports_fixed':fixederr<1e-8,'mass_matches_expected':abs(mass-m['expected_total_mass_kg'])/mass<a['mass_relative_error'],'independent_native_mass_matches':abs(float(nm0.sum())-mass)/mass<a['mass_relative_error'],'native_nodal_mass_unchanged':unchanged,'no_added_mass':float(np.max(abs(H['ADDED MASS'])))/(mass*1000)<a['added_mass_fraction'],'no_erosion':True,'no_external_work':bool(np.all(H['EXTERNAL WORK']==0)),'global_energy':float(np.max(abs(RR)))/E0<a['global_energy_residual_initial_KE_fraction'],'local_energy':bool(np.all(abs(RR[window])<=a['local_energy_residual_generated_energy_fraction']*GG[window]+a['CSV_KE_precision_allowance_J'])),'global_support_momentum':ge<=mtol,'contact_facade_momentum':fe<=mtol,'metal_material_domain':maxeps<=a['metal_plastic_strain_diagnostic_limit'],'beam_material_domain':beam_eps<=a['metal_plastic_strain_diagnostic_limit'],'radome_face_reference_domain':maxratio<=1,'radome_plastic_strain_zero':max(z['max_radome_plastic_strain'] for z in rows)==0,'independent_translation_KE':float(np.max(abs(dk)))<=cfg['acceptance_extra']['independent_nodal_translation_KE_fraction_of_initial']*E0,'independent_momentum':float(np.max(np.linalg.norm(dp,axis=1)))<=cfg['acceptance_extra']['independent_nodal_momentum_absolute_Ns']+cfg['acceptance_extra']['independent_nodal_momentum_relative']*jmax}
    r={'created_utc':now(),'case':case,'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],'all_declared_checks_pass':all(checks.values()),'end_ms':end,'last_main_history_ms':float(T[-1]),'native_animation_states':len(times),'total_mass_kg':mass,'native_aircraft_mass_kg':float(nm0[air].sum()),'initial_KE_J':E0,'final_generated_energy_J':finalG,'final_energy_residual_J':finalR,'maximum_energy_residual_J':float(np.max(abs(RR))),'maximum_local_residual_fraction':float(np.max(abs(RR[window])/GG[window])) if np.any(window) else 0,'contact_onsets_ms':onsets,'contact_onset_sampling_interval_ms':.01,'last_main_contact_impulse_Ns':J[-1].tolist(),'last_main_segment_impulse_Ns':{k:(v[-1]-v[0]).tolist() for k,v in S.items()},'final_plastic_work_J':float(Ho['PLASTIC WORK'][0])*.001,'maximum_facade_displacement_mm':max(z['maximum_facade_displacement_mm'] for z in rows),'maximum_shell_plastic_strain':maxeps,'maximum_beam_plastic_strain':beam_eps,'maximum_radome_face_strength_ratio':maxratio,'momentum_global_support_error_Ns':ge,'momentum_facade_contact_error_Ns':fe,'native_geometry_rounding_error_mm':coorderr,'native_mass_constant':unchanged,'observer_REAC_excluded':True,'observer_contact_impulses_excluded':True,'physical_impact_qualified':False,'spatial_convergence_qualified':False,'fracture_crushing_delamination_modelled':False,'seconds_impact_calculated':False,'state_diagnostics':rows}
    np.savez_compressed(d/'verified_states_SI.npz',time_s=times*.001,node_ids=np.arange(1,len(x0)+1),initial_positions_m=x0*.001,displacement_m=np.array(D),velocity_m_s=np.array(V),shell_max_layer_plastic_strain=np.array(EPS),shell_von_mises_mean_MPa=np.array(VM),native_nodal_mass_kg=nm0,**cellinfo)
    np.savez_compressed(d/'balance_history_SI.npz',time_s=T*.001,contact_impulse_Ns=J,facade_momentum_Ns=Pf,global_momentum_Ns=P,support_Ns=Js,energy_residual_J=R,generated_energy_J=G,plastic_work_J=H['PLASTIC WORK']*.001)
    dump(d/'native_mass_reader_proofs.json',{'samples':proofs});dump(d/'review.json',r);print({k:v for k,v in r.items() if k in ['case','end_ms','failed_checks','maximum_facade_displacement_mm','final_energy_residual_J']},flush=True);return r

def main():
    guard();assert not (OUT/'campaign_review.json').exists();rows=[];rejected=[]
    assert all((OUT/'r0'/c['id']/'history_recovery.json').exists() or list((OUT/'r0'/c['id']).glob('retained_failure_*.json')) for c in cases()),'Wait for both declared attempts to finish'
    for c in cases():
        d=OUT/'r0'/c['id']
        if not (d/'history_recovery.json').exists():rejected.append({'case':c,'retained_failures':[rel(p) for p in d.glob('retained_failure_*.json')]});continue
        rows.append(read(d/'review.json') if (d/'review.json').exists() else audit(c))
    comparison=None
    if len(rows)==2:
        z=[np.load(OUT/'r0'/r['case']['id']/'balance_history_SI.npz') for r in rows];tc=min(float(q['time_s'][-1]) for q in z);J=[np.array([np.interp(tc,q['time_s'],q['contact_impulse_Ns'][:,i]) for i in range(3)]) for q in z];E=[float(np.interp(tc,q['time_s'],q['generated_energy_J'])) for q in z];jd=float(np.linalg.norm(J[1]-J[0])/max(np.linalg.norm(J[0]),1e-30));ed=abs(E[1]-E[0])/max(abs(E[0]),1e-30);a=read(CFG)['acceptance'];comparison={'cases':[r['case']['id'] for r in rows],'common_time_ms':tc*1000,'impulse_difference_fraction':jd,'generated_energy_difference_fraction':ed,'impulse_pass':jd<=a['half_dt_impulse_difference_fraction'],'generated_energy_pass':ed<=a['half_dt_generated_energy_difference_fraction']}
    required=['native_binary_CSV','normal_termination','requested_horizon_reached','original_connectivity','finite_native_states','all_boundary_supports_fixed','mass_matches_expected','independent_native_mass_matches','native_nodal_mass_unchanged','no_added_mass','no_erosion','no_external_work']
    s={'iteration':'AIRCRAFT-A15','created_utc':now(),'cases':rows,'rejected_cases':rejected,'comparison':comparison,'integrity_only_pass':not rejected and all(all(r['checks'][k] for k in required) for r in rows),'all_declared_checks_pass':not rejected and all(r['all_declared_checks_pass'] for r in rows) and bool(comparison and comparison['impulse_pass'] and comparison['generated_energy_pass']),'physical_impact_qualified':False,'whole_aircraft_exploratory_impact_executed':bool(rows),'requested_horizon_ms':10,'seconds_impact_calculated':False,'old_failed_A11_A14_gates_retained':True,'old_solver_reruns':0,'parallel_module_integrated':False,'NIST_outcomes_used_as_target':False}
    dump(OUT/'campaign_review.json',s);print({k:v for k,v in s.items() if k!='cases'},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case');args=p.parse_args()
    audit(next(c for c in cases() if c['id']==args.case)) if args.case else main()
