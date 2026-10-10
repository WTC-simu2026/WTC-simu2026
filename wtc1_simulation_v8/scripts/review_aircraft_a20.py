"""Independent native balances and actual 3D-core/skin erosion, no extrapolation."""
from run_aircraft_a20_whole import *
from audit_aircraft_a03 import topology
from review_aircraft_a15 import segments

PROTOCOL=OUT/'whole_review_protocol.json'

def declare():
    whole_guard();assert not PROTOCOL.exists()
    dump(PROTOCOL,{'declared_utc':now(),'iteration':'AIRCRAFT-A20','geometry_review_stride':5,
        'shell_energy_review':'Every retained animation including observer; prefix reader checked against converter at first, middle and final sampled states.',
        '3D_review':'Core and cohesive element IDs, cells and erosion checked in native converter at every sampled state. Initial core mass derived from same native-confirmed material volume; specific energy compared to native core part history.',
        'negative_IE_allowance_J':.001,'part_element_final_energy_relative_allowance':1e-4,
        'geometric_moment_reference_addendum':rel(D/'geometric_moment_addendum.json'),'old_parent_CG_gate_retained':True,
        'native_animation_mass_discrepancy':'Sum independently; do not subtract an assumed constraint mass or create RKE to close the balance.',
        'same_A19_energy_and_momentum_thresholds':True,'no_new_solver':True,'physical_qualification':False,
        'source_states':'Use true binary time and node coordinates; remove only native-eroded geometry; no interpolation or dynamics beyond the native horizon.'})

def values(H,Ho,k):return np.r_[H[k],Ho[k][0]]

def main():
    whole_guard();assert PROTOCOL.exists();assert not (D/'review.json').exists()
    cfg=read(WCFG);a=cfg['acceptance'];proto=read(PROTOCOL);m=read(D/'mesh.json');g=read(D/'generation.json')
    H=histories(D/(N+'T01.csv'));Ho=histories(D/'observer'/(N+'T02_recovered.csv'));T=values(H,Ho,'time')
    assert read(D/'history_recovery.json')['pass'];end=float(T[-1]);step=float(Ho['TIME STEP'][0]);terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(values(H,Ho,k) for k in terms)*.001;E0=float(E[0]);EW=values(H,Ho,'EXTERNAL WORK')*.001;R=E-E0-EW;G=sum(values(H,Ho,k) for k in terms if k!='KINETIC ENERGY')*.001
    window=G>a['local_energy_comparison_minimum_J'];mass=numbers_after((D/(N+'_0000.out')).read_text(errors='replace'),'TOTAL MASS AND MASS CENTER',4)[0]*.001
    S=segments(H);J=sum(S.values());J-=J[0];P=np.column_stack([H[z+'-MOMENTUM'] for z in 'XYZ'])*.001
    Pf=np.column_stack([sum((H[k] for k in H if k.startswith('FACADE_') and k.strip().endswith(z+'MOM')),np.zeros(len(H['time']))) for z in 'XYZ'])*.001
    Js=np.column_stack([sum((H[k] for k in H if k.startswith('SUPPORT_IMPULSE_'+z)),np.zeros(len(H['time']))) for z in 'XYZ'])*.001;Js-=Js[0]
    jmax=float(np.linalg.norm(J,axis=1).max());mtol=a['momentum_absolute_allowance_Ns']+a['momentum_relative_allowance']*jmax
    ge=float(np.linalg.norm(P-P[0]-Js,axis=1).max());fe=float(np.linalg.norm(Pf-Pf[0]-J-Js,axis=1).max())
    def pk(prefix,channel):
        keys=[k for k in H if k.startswith(prefix) and k.strip().endswith(' '+channel)];assert len(keys)==1,(prefix,channel,keys);return keys[0]
    corekeys=[k for k in H if k.startswith('RADOME_CORE_FACET_') and k.strip().endswith(' IE')]
    skinkeys=[k for k in H if k.startswith(('RADOME_LOWER_FACET_','RADOME_UPPER_FACET_')) and k.strip().endswith(' IE')]
    assert len(corekeys)==216 and len(skinkeys)==432,(len(corekeys),len(skinkeys))
    coreparts=np.column_stack([values(H,Ho,k) for k in corekeys])*.001;skinparts=np.column_stack([values(H,Ho,k) for k in skinkeys])*.001
    coreIE=coreparts.sum(axis=1);skinIE=skinparts.sum(axis=1);cohIE=values(H,Ho,pk('RADOME_EDGE_COHESIVE','IE'))*.001
    shell_ids=[r['id'] for r in m['radome_skin_quads']];core_ids=[r[0] for r in m['radome_core_bricks']];coh_ids=[s['element_id'] for s in m['cohesive_seams']]
    cm={72001+k*3+j:f['core_volume_mm3']*4.8e-5/3 for k,f in enumerate(m['radome_facets']) for j in range(3)}
    coremass=np.array([cm[e] for e in core_ids]);x0=np.array(m['nodes_mm']);fix=np.array(m['fixed_node_ids'])-1;fa=np.array(g['facade_translated_node_ids'])-1
    available=sorted(p for p in D.glob(N+'A*') if re.fullmatch(re.escape(N)+r'A\d{3}',p.name));available+=sorted(p for p in (D/'observer').glob(N+'A*') if re.fullmatch(re.escape(N)+r'A\d{3}',p.name))
    sampled=[p for i,p in enumerate(available) if i%proto['geometry_review_stride']==0 or i==len(available)-1]
    times=[];poses=[];vels=[];SK=[];CO=[];SE=[];epss=[];rows=[];proofs=[];ke=[];pp=[];nm0=None;cellinfo=None;fixederr=0.;coorderr=0.;topcheck=True;unchanged=True;maxmetal=0.;maxfacade=0.;minskin=0.;mincore=0.;ie_err=[];all_shell_rows=[]
    # Every saved shell energy field, even where geometry is sampled more sparsely.
    for p in available:
        z=fast(p);ix={int(e):j for j,e in enumerate(z['eid'])};si=np.array([ix[e] for e in shell_ids]);e=z['scalar']['Specific Energy'][si]*z['element_mass_g'][si]*.001
        all_shell_rows.append({'time_ms':z['time_ms'],'skin_IE_J':float(e.sum()),'minimum_skin_element_IE_J':float(e.min(initial=0)),'negative_skin_elements':int(np.sum(e<-.001))});minskin=min(minskin,float(e.min(initial=0)))
    for p in sampled:
        z=fast(p);tm=z['time_ms']
        if times and abs(tm-times[-1])<1e-6:continue
        q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,check=True,timeout=120).stdout)
        assert abs(q['time']-tm)<max(1e-6,tm*5e-6)
        order=np.argsort(q['NODE_ID']);assert np.array_equal(q['NODE_ID'][order],np.arange(1,len(x0)+1));zo=np.argsort(z['nid']);assert np.array_equal(z['nid'][zo],np.arange(1,len(x0)+1))
        X=z['x'][zo];V=z['vector']['Velocity'][zo];U=q['Displacement'].reshape(-1,3)[order];nm=z['node_mass_g'][zo]*.001
        assert np.allclose(X,q['points'].reshape(-1,3)[order],rtol=5e-6,atol=1e-6);assert np.allclose(V,q['Velocity'].reshape(-1,3)[order],rtol=5e-6,atol=1e-6)
        ix={int(e):j for j,e in enumerate(q['ELEMENT_ID']) if e>0};ci=np.array([ix[e] for e in core_ids]);si=np.array([ix[e] for e in shell_ids]);ei=np.array([ix[e] for e in coh_ids])
        if nm0 is None:
            nm0=nm;cells=topology(q);cellinfo={k:q[v].astype(int) for k,v in [('element_ids','ELEMENT_ID'),('part_ids','PART_ID'),('cell_types','types')]}
            for j,t in enumerate(q['types']):
                if t==5:assert cells[j][-1]==cells[j][-2];cells[j]=cells[j][:3]
            topcheck=all(cells[ix[e]]==f for e,f in zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids'])) and all(cells[ix[r['id']]]==r['nodes'] for r in m['radome_skin_quads']) and all(cells[ix[r[0]]]==r[1:] for r in m['radome_core_bricks']+m['cohesive_connectivity'])
        else:unchanged=unchanged and np.array_equal(nm0,nm);assert np.array_equal(q['ELEMENT_ID'].astype(int),cellinfo['element_ids'])
        core_alive=q['EROSION_STATUS'][ci].astype(int);skin_alive=q['EROSION_STATUS'][si].astype(int);seam_alive=q['EROSION_STATUS'][ei].astype(int)
        core_e=q['3DELEM_Specific_Energy'][ci]*coremass*.001;mincore=min(mincore,float(core_e.min(initial=0)));part=np.interp(tm,T,coreIE);ie_err.append(float(core_e.sum()-part))
        epskeys=[k for k in q if 'Plast_Strn_Layer_' in k];eps=np.vstack([q[k] for k in epskeys]).max(axis=0);metal=cellinfo['cell_types']==5;facade=cellinfo['cell_types']==9
        maxmetal=max(maxmetal,float(eps[metal].max(initial=0)));maxfacade=max(maxfacade,float(eps[facade].max(initial=0)));fixederr=max(fixederr,float(abs(U[fix]).max()));coorderr=max(coorderr,float(abs(X-x0-U).max()))
        assert all(np.isfinite(v).all() for v in [X,V,U,eps,core_e]);ke.append(float(.5*np.sum(nm[:,None]*V*V)));pp.append(np.sum(nm[:,None]*V,axis=0))
        # The true binary coordinates are the rendering source; displacement only remains a cross-check.
        poses.append(X.astype(np.float32)*.001);vels.append(V.astype(np.float32));times.append(tm);SK.append(skin_alive);CO.append(core_alive);SE.append(seam_alive);epss.append(eps.astype(np.float32))
        row={'time_ms':tm,'deleted_skin_quads':int(np.sum(skin_alive==0)),'deleted_core_bricks':int(np.sum(core_alive==0)),'deleted_cohesive_strips':int(np.sum(seam_alive==0)),
            'maximum_metal_plastic_strain':float(eps[metal].max(initial=0)),'maximum_facade_plastic_strain':float(eps[facade].max(initial=0)),
            'maximum_facade_displacement_mm':float(np.linalg.norm(U[fa],axis=1).max()),'core_element_IE_sum_J':float(core_e.sum()),'core_part_IE_interpolated_J':float(part),'core_element_part_IE_difference_J':float(core_e.sum()-part)}
        rows.append(row);proofs.append({'path':rel(p),'time_ms':tm,'binary_VTK_coordinates_and_velocity_agree':True,'binary_timestamp_used':True});print(row,flush=True)
    times=np.array(times);ke=np.array(ke);pp=np.array(pp);assert len(times)>1 and abs(times[-1]-end)<1e-5
    kg=np.interp(times,T,values(H,Ho,'KINETIC ENERGY')*.001);pg=np.column_stack([np.interp(times,T,values(H,Ho,z+'-MOMENTUM')*.001) for z in 'XYZ']);dk=(ke-ke[0])-(kg-kg[0]);dp=(pp-pp[0])-(pg-pg[0])
    bk=[k for k in H if k.startswith('FORWARD_BEAM_DIAGNOSTIC')];beam=np.column_stack([H[k] for k in bk]).reshape(len(H['time']),len(g['beam_history_ids']),9);beps=float(beam[:,:,8].max())
    contact_active=np.linalg.norm(J,axis=1)>0;first=int(np.flatnonzero(contact_active)[0]) if contact_active.any() else len(J);pre=float(abs(G[:first]-G[0]).max(initial=0))
    checks={'native_binary_CSV':True,'normal_termination':'NORMAL TERMINATION' in (D/'engine.log').read_text(),'requested_horizon_reached':end>=20 and end-20<=a['final_timestamp_overshoot_native_step_factor']*step,
        'declared_connectivity':topcheck,'finite_states':True,'supports_fixed':fixederr<1e-8,'native_global_mass_expected':abs(mass-m['expected_total_mass_kg'])/mass<a['mass_relative_error'],
        'animation_mass_matches_native_global_mass':abs(nm0.sum()-mass)/mass<a['mass_relative_error'],'animation_nodal_mass_unchanged':unchanged,'no_added_or_scaled_mass':float(abs(values(H,Ho,'ADDED MASS')).max())/(mass*1000)<a['added_mass_fraction'],
        'no_external_work':bool(np.all(EW==0)),'global_energy':float(abs(R).max())/E0<a['global_energy_residual_initial_KE_fraction'],
        'local_energy':bool(window.any() and np.all(abs(R[window])<=a['local_energy_residual_generated_energy_fraction']*G[window]+a['CSV_KE_precision_allowance_J'])),
        'global_support_momentum':ge<=mtol,'contact_facade_momentum':fe<=mtol,'metal_material_domain':maxmetal<=a['metal_plastic_strain_diagnostic_limit'],'facade_material_domain':maxfacade<=a['metal_plastic_strain_diagnostic_limit'],'beam_material_domain':beps<=a['metal_plastic_strain_diagnostic_limit'],
        'core_part_IE_nonnegative':float(coreIE.min())>-.001,'all_core_facets_IE_nonnegative':float(coreparts.min())>-.001,'skin_part_IE_nonnegative':float(skinIE.min())>-.001,'all_skin_facets_IE_nonnegative':float(skinparts.min())>-.001,'cohesive_part_IE_nonnegative':float(cohIE.min())>-.001,'saved_skin_elements_IE_nonnegative':minskin>-.001,'sampled_core_elements_IE_nonnegative':mincore>-.001,
        'core_final_element_part_IE_agree':abs(ie_err[-1])<=proto['part_element_final_energy_relative_allowance']*abs(coreIE[-1])+.001,
        'zero_initial_IE':abs(coreIE[0])+abs(skinIE[0])+abs(cohIE[0])<cfg['insertion_acceptance']['initial_no_contact_IE_J'],
        'no_generated_energy_before_contact':pre<cfg['insertion_acceptance']['initial_no_contact_IE_J'],
        'geometric_insertion_addendum_pass':read(D/'geometric_moment_addendum.json')['geometric_reference_addendum_pass'],
        'initial_constraint_mass_duplicate_reconciled':read(D/'constraint_mass_listing/constraint_mass_interpretation.json')['pass'],
        'original_parent_CG_gate':read(D/'native_insertion_gate.json')['checks']['CG_preserved'],'zero_warning_gate':read(D/'starter_gate.json')['strict_pass'],
        'independent_translation_delta_KE':float(abs(dk).max())<=.005*E0,'independent_delta_momentum':float(np.linalg.norm(dp,axis=1).max())<=mtol}
    checks={k:bool(v) for k,v in checks.items()};r={'created_utc':now(),'iteration':'AIRCRAFT-A20','case':CASE,'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'all_declared_checks_pass':all(checks.values()),
        'end_ms':end,'total_mass_kg':mass,'animation_mass_kg':float(nm0.sum()),'animation_mass_difference_kg':float(nm0.sum()-mass),'initial_KE_J':E0,
        'maximum_energy_residual_J':float(abs(R).max()),'final_energy_residual_J':float(R[-1]),'final_generated_energy_J':float(G[-1]),'maximum_local_residual_fraction':float((abs(R[window])/G[window]).max()) if window.any() else None,
        'final_core_IE_J':float(coreIE[-1]),'final_skins_IE_J':float(skinIE[-1]),'final_cohesive_IE_J':float(cohIE[-1]),'minimum_saved_skin_element_IE_J':minskin,'minimum_sampled_core_element_IE_J':mincore,
        'maximum_metal_plastic_strain':maxmetal,'maximum_facade_plastic_strain':maxfacade,'maximum_beam_plastic_strain':beps,'global_support_momentum_error_Ns':ge,'facade_contact_momentum_error_Ns':fe,
        'first_external_contact_history_ms':float(H['time'][first]) if first<len(J) else None,'precontact_maximum_generated_energy_J':pre,'coordinate_crosscheck_max_mm':coorderr,
        'independent_delta_KE_max_error_J':float(abs(dk).max()),'independent_delta_momentum_max_error_Ns':float(np.linalg.norm(dp,axis=1).max()),'native_history_rows':len(T),'verified_geometry_states':len(times),
        'state_diagnostics':rows,'final_deleted_geometry':rows[-1],'animation_nodal_mass_physical_interpretation_qualified':False,'RKE_not_invented_or_added':True,'old_failed_gates_retained':True,
        'physical_impact_qualified':False,'physical_G_measured':False,'metal_rupture_modelled':False,'core_skin_debonding_modelled':False,'spatial_convergence_qualified':False,'objective1_complete':False,'seconds_extension_allowed':False,'NIST_damage_fitted':False,'observer_impulses_excluded':True}
    np.savez_compressed(D/'verified_states_SI.npz',time_s=times*.001,node_ids=np.arange(1,len(x0)+1),initial_positions_m=x0*.001,positions_m=np.array(poses),velocity_m_s=np.array(vels),native_nodal_mass_kg=nm0,
        shell_max_layer_plastic_strain=np.array(epss),skin_element_ids=shell_ids,skin_alive=np.array(SK),core_element_ids=core_ids,core_alive=np.array(CO),cohesive_element_ids=coh_ids,cohesive_alive=np.array(SE),**cellinfo)
    np.savez_compressed(D/'balance_history_SI.npz',time_s=T*.001,energy_residual_J=R,generated_energy_J=G,core_part_IE_J=coreIE,skin_part_IE_J=skinIE,cohesive_part_IE_J=cohIE)
    dump(D/'native_geometry_proofs.json',{'samples':proofs});dump(D/'native_part_IE_mapping.json',{'core_IE_channels':corekeys,'skin_IE_channels':skinkeys,'native_individual_part_titles_used':True,'aggregation_includes_each_part_once':True,'minimum_core_facet_IE_J':float(coreparts.min()),'minimum_skin_facet_IE_J':float(skinparts.min())});dump(D/'every_saved_skin_energy.json',{'frames':all_shell_rows});dump(D/'review.json',r)
    dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':[r],'all_declared_checks_pass':False,'physical_impact_qualified':False,'objective1_complete':False,'old_failed_gates_retained':True,'old_solver_reruns':0})
    print({k:r[k] for k in ['end_ms','failed_checks','final_energy_residual_J','final_core_IE_J','final_skins_IE_J','animation_mass_difference_kg']},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','main']);globals()[p.parse_args().action]()
