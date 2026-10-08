"""Saved-output A12 review: main histories and restart-reset reactions kept separate."""
import json,re,sys
import numpy as np
from run_aircraft_a12 import ROOT,OUT,CFG,REV,allcases,guard,read,dump,rel,sha,now,triangle,histories

def main():
    guard();assert not (OUT/'authoritative_review.json').exists();a=read(CFG)['acceptance'];rows=[]
    for c in allcases():
        d=OUT/REV/c['id'];g=read(d/'generation.json');r=read(d/'review.json');H=histories(d/(g['name']+'T01.csv'));L=np.load(d/'balance_history_SI.npz');z=np.load(d/'verified_states_SI.npz');T=H['time'];nn=len(g['nodes_mm']);wn=np.array(g['fixed_nodes'])-1;rn=np.array(g['radome_nodes'])-1
        keys=[k for k in H if k.startswith('NATIVE_NODES')];ids=[int(re.search(r'NATIVE_NODES\s+(\d+)\s+N',k).group(1)) for k in keys[::9]]
        nodes=np.column_stack([H[k] for k in keys]).reshape(len(T),nn,9)[:,np.argsort(ids),:]
        sk=[k for k in H if k.startswith('SUPPORT_NATIVE')];sids=[int(re.search(r'SUPPORT_NATIVE\s+(\d+)\s+S',k).group(1)) for k in sk[::3]];assert sids==g['fixed_nodes']
        for j,n in enumerate(sids):assert all(re.search(r'\s'+str(n)+r'\s+S'+str(n)+r'\s',k) for k in sk[3*j:3*j+3])
        Js=np.column_stack([H[k] for k in sk]).reshape(len(T),len(wn),3).sum(1)*.001;Js-=Js[0]
        J=L['impulse_Ns'][:-1];P=L['momentum_Ns'][:-1];ptol=a['momentum_absolute_Ns']+a['momentum_relative']*float(np.max(np.linalg.norm(J,axis=1)))
        supporterr=float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)));contacterr=float(np.max(np.linalg.norm(J+Js,axis=1)))
        m=z['nodal_mass_kg'];K=.5*np.sum(m[None,:,None]*nodes[:,:,3:6]**2,axis=(1,2));PN=np.sum(m[None,:,None]*nodes[:,:,3:6],axis=1)
        Kerr=(K-K[0])-(L['native_kinetic_J'][:-1]-L['native_kinetic_J'][0]);Perr=(PN-PN[0])-(P-P[0]);cg=(m[rn,None]*z['initial_position_m'][rn]).sum(0)/m[rn].sum();rx=z['initial_position_m'][rn]-cg
        lever=sum(mass*(float(v@v)*np.eye(3)-np.outer(v,v)) for mass,v in zip(m[rn],rx));rotI=np.zeros(nn)
        # c3inmas.F: XI = sum m_slice*(area/4.5+slice_thickness^2/12+slice_z^2).
        # For Ipos=0, Iint=2, slice centres are the cumulative Gauss-weight slices.
        for tr in g['triangles']:
            ix=np.array(tr)-1;ar,w=triangle(np.array(g['nodes_mm'])[ix]);mf=0.
            if c['simple']:
                sm=read(CFG)['simple_elastic_control'];mf=sm['rho_g_mm3']*sm['thickness_mm']*(ar/4.5+sm['thickness_mm']**2/12)
            else:
                position=-4.5
                for th,rho in [(.5,.00183),(8,.000048),(.5,.00183)]:
                    for weight in [5/9,8/9,5/9]:
                        dt=th*weight/2;zz=position+dt/2;mf+=rho*dt*(ar/4.5+dt*dt/12+zz*zz);position+=dt
            rotI[ix]+=ar*mf*w*1e-9
        pred=lever+np.eye(3)*rotI.sum()
        text=(d/(g['name']+'_0000.out')).read_text(errors='replace');match=re.search(r'PART\s*:\s*21,.*?\n\s*Mass.*?\n([^\n]+)\n\s*X.*?\n([^\n]+)',text,re.S);assert match
        native=np.fromstring(match.group(1),sep=' ');second=np.fromstring(match.group(2),sep=' ');assert len(native)==7 and len(second)==7
        values=native[1:]*1e-9;nat=np.array([[values[0],values[3],values[5]],[values[3],values[1],values[4]],[values[5],values[4],values[2]]]);err=float(np.max(abs(pred-nat)))/float(np.max(abs(nat)));cgerr=float(np.max(abs(cg-second[:3]*.001)))
        reconstructedR=.5*np.sum(rotI[None,:,None]*(nodes[:,:,6:9]*1000)**2,axis=(1,2));nativeR=L['native_rotation_J'][:-1];Rerr=float(np.max(abs(reconstructedR-nativeR)))
        checks=r['checks'].copy();checks['momentum_support']=supporterr<=ptol;checks['momentum_contact_support']=contacterr<=ptol
        # Keep the original failed observer-end checks separately; no synthetic continuation of REAC.
        inheritedA=read(CFG)['inherited_A11_gates_unchanged'];fullG=L['generated_J'];fullR=L['residual_J'];active=fullG>inheritedA['local_energy_comparison_minimum_J'];A11pass=bool(np.all(abs(fullR[active])<=inheritedA['local_energy_residual_generated_energy_fraction']*fullG[active]+inheritedA['CSV_KE_precision_allowance_J']))
        rr={**r,'checks':checks,'all_checks_pass':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'first_review_preserved':{'path':rel(d/'review.json'),'sha256':sha(d/'review.json'),'failed_checks':r['failed_checks']},'support_comparison_window_ms':[float(T[0]),float(T[-1])],'observer_reaction_reset_detected':bool(np.linalg.norm(L['support_Ns'][-1]-Js[-1])>ptol),'observer_REAC_endpoint_used_for_acceptance':False,'main_support_residual_Ns':supporterr,'main_contact_support_residual_Ns':contacterr,'observer_support_Ns':L['support_Ns'][-1].tolist(),'main_last_support_Ns':Js[-1].tolist(),'max_dense_KE_change_error_J':float(np.max(abs(Kerr))),'max_dense_momentum_error_Ns':float(np.max(np.linalg.norm(Perr,axis=1))),'A11_local_gate_pass_in_isolated_witness':A11pass,'no_A11_extension_credit':True,'native_initial_inertia_audit':{'native_radome_mass_kg':float(native[0]*.001),'native_CG_m':(second[:3]*.001).tolist(),'native_tensor_kg_m2':nat.tolist(),'angle_lumped_lever_tensor_kg_m2':lever.tolist(),'scalar_rotational_inertia_sum_kg_m2':float(rotI.sum()),'predicted_tensor_kg_m2':pred.tolist(),'maximum_relative_tensor_error':err,'maximum_CG_error_m':cgerr,'initial_inertia_consistent_with_saved_c3inmas_algorithm':err<=1e-6 and cgerr<=1e-6,'source_binary_equivalence_established':False,'not_a_physical_inertia_validation':True},'dynamic_inertia_diagnostic':{'maximum_reconstructed_global_RKE_error_J':Rerr,'native_global_RKE_final_main_J':float(nativeR[-1]),'reconstructed_global_RKE_final_main_J':float(reconstructedR[-1]),'qualified':False,'energy_ledger_changed':False,'missing_energy_filled':False}}
        np.savez_compressed(d/'authoritative_main_history_SI.npz',time_ms=T,residual_J=L['residual_J'][:-1],generated_J=L['generated_J'][:-1],impulse_Ns=J,support_Ns=Js,momentum_Ns=P,dense_KE_J=K,dense_momentum_Ns=PN,nodal_rotation_inertia_kg_m2=rotI,reconstructed_RKE_J=reconstructedR,native_RKE_J=nativeR,KE_change_error_J=Kerr)
        dump(d/'authoritative_review.json',rr);rows.append(rr)
    by={q['case']['id']:q for q in rows};comparisons=[]
    def compare(aa,bb,kind,accept=True):
        za=np.load(OUT/REV/aa/'authoritative_main_history_SI.npz');zb=np.load(OUT/REV/bb/'authoritative_main_history_SI.npz');tm=min(.4,float(za['time_ms'][-1]),float(zb['time_ms'][-1]));js=[np.array([np.interp(tm,q['time_ms'],q['impulse_Ns'][:,i]) for i in range(3)]) for q in [za,zb]];es=[float(np.interp(tm,q['time_ms'],q['generated_J'])) for q in [za,zb]];jd=float(np.linalg.norm(js[1]-js[0])/max(np.linalg.norm(js[0]),1e-12));ed=abs(es[1]-es[0])/max(abs(es[0]),1e-12)
        limit='half_dt' if kind=='half_dt' else 'mesh';q={'cases':[aa,bb],'type':kind,'common_time_ms':tm,'impulse_difference_fraction':jd,'generated_difference_fraction':ed,'impulses_Ns':[v.tolist() for v in js],'generated_J':es,'declared_acceptance':accept,'impulse_pass':jd<=a[limit+'_impulse_relative'] if accept else None,'generated_pass':ed<=a[limit+'_generated_relative'] if accept else None};comparisons.append(q)
    for aa,bb,kind in [('SAND','SAND_HALF','half_dt'),('SAND_HALF','SAND_FINE','mesh'),('SAND_FINE','SAND_FINE2','mesh'),('SAND_FINE2','SAND_FINE3','mesh'),('SAND_FINE2','SAND_FINE2_HALF','half_dt'),('SIMPLE','SIMPLE_FINE','mesh'),('SIMPLE_FINE','SIMPLE_FINE2','mesh')]:compare(aa,bb,kind)
    compare('SAND_HALF','SAND_SERIES','contact_stiffness_formulation',False)
    required=['native_CSV_all_channels_verified','starter_zero_errors_warnings','normal_engine_termination','observer_outputs_preserved','finite_monotone_history','native_mass_preserved','analytic_radome_mass','native_nodal_mass_lumping','zero_added_mass','connectivity_preserved','supports_fixed','no_external_work','no_plastic_work']
    integrity=all(all(r['checks'][k] for k in required) for r in rows)
    runtime=[read(p) for p in OUT.rglob('*.execution.json')];mainjobs=[q for q in runtime if q['exe'].endswith('engine_win64.exe') and q['args'][1].endswith('_0001.rad')]
    peer=ROOT/'wtc1_simulation_v8/output/aircraft_a11_boeing_parallel';pr=read(peer/'integration_ready.json');pr2=read(peer/'native_adapter_v2/integration_ready.json')
    dump(OUT/'parallel_module_review.json',{'created_utc':now(),'delivered':True,'static_module':pr,'native_v2_module':pr2,'main_agent_review':'12 ports and six constitutive witnesses exist. Strict inertia contract and free dynamics remain blocked; no integration into A12. Initial witness matrix pass cannot qualify aircraft collision.','integrated':False,'materials_or_mass_budgets_changed':False})
    summary={'iteration':'AIRCRAFT-A12','created_utc':now(),'cases':rows,'comparisons':comparisons,'integrity_only_pass':integrity,'all_declared_checks_pass':all(q['all_checks_pass'] for q in rows) and all(q['impulse_pass'] and q['generated_pass'] for q in comparisons if q['declared_acceptance']),'native_initial_inertia_consistent_in_all_witnesses':all(q['native_initial_inertia_audit']['initial_inertia_consistent_with_saved_c3inmas_algorithm'] for q in rows),'local_energy_qualified':False,'spatial_convergence_qualified':False,'physical_impact_qualified':False,'seconds_impact_calculated':False,'whole_aircraft_extension_allowed':False,'main_engine_jobs':len(mainjobs),'accepted_instrumented_cases':len(rows),'retained_instrumentation_cases':1,'observer_jobs':len([q for q in runtime if q['exe'].endswith('engine_win64.exe')])-len(mainjobs),'old_solver_reruns':0,'native_wall_seconds':sum(q['seconds'] for q in runtime),'parallel_module_integrated':False,'causal_findings':{'RBE3_required_to_reproduce_deficit':False,'LAW25_sandwich_required_to_reproduce_deficit':False,'half_dt_closes_coarse_energy_deficit':False,'spatial_refinement_decreases_deficit':True,'unique_energy_cause_identified':False},'reaction_restart_semantics':'Cumulative main REAC resets in observer restart; no observer endpoint used for support/momentum acceptance. Previous reviews retained.'}
    assert integrity,summary
    dump(OUT/'authoritative_review.json',summary)
    print({k:v for k,v in summary.items() if k not in ['cases','comparisons','reaction_restart_semantics']},flush=True)
    print(json.dumps(comparisons,indent=2),flush=True)

if __name__=='__main__':main()
