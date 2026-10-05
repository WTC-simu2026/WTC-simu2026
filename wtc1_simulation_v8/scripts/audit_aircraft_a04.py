"""Saved-state and energy audit for whole-aircraft plasticity, no acceptance fitting."""
import argparse,csv,re,subprocess,time
import numpy as np
from run_aircraft_a04 import ROOT,CFG,OUT,PREV,RUNTIME,read,dump,sha,rel,now
from audit_aircraft_a02 import numbers_after
from audit_aircraft_a03 import integrate,topology

def vtk(text):
    lines=text.splitlines();i=0;count=0;q={}
    while i<len(lines):
        w=lines[i].split();i+=1
        if not w:continue
        if w[0]=='TIME':
            while not lines[i].strip():i+=1
            q['time']=float(lines[i]);i+=1;continue
        if w[0] in ['POINT_DATA','CELL_DATA']:count=int(w[1]);continue
        if w[0] not in ['POINTS','CELLS','CELL_TYPES','SCALARS','VECTORS','TENSORS']:continue
        if w[0]=='POINTS':key,n='points',int(w[1])*3
        elif w[0]=='CELLS':key,n='cells',int(w[2])
        elif w[0]=='CELL_TYPES':key,n='types',int(w[1])
        else:
            key=w[1];n=count*(9 if w[0]=='TENSORS' else 3 if w[0]=='VECTORS' else int(w[3]) if len(w)>3 else 1)
            if w[0]=='SCALARS':
                while not lines[i].strip():i+=1
                assert lines[i].startswith('LOOKUP_TABLE');i+=1
        start=i;k=0
        while k<n:k+=len(lines[i].split());i+=1
        values=np.fromstring(' '.join(lines[start:i]),sep=' ');assert len(values)==n,(key,len(values),n);q[key]=values
    return q

def vm_tensor(v):
    s=v.reshape(-1,3,3);return np.sqrt(.5*((s[:,0,0]-s[:,1,1])**2+(s[:,1,1]-s[:,2,2])**2+(s[:,2,2]-s[:,0,0])**2)+3*(s[:,0,1]**2+s[:,1,2]**2+s[:,2,0]**2))

def histories(p):
    with p.open(encoding='utf-8-sig') as f:
        r=csv.reader(f);keys=next(r);rows=list(r)
        # Native converter leaves a trailing empty field; it is not a physical channel.
        while keys and (not keys[-1].strip() or keys[-1].startswith('(null)')):
            keys.pop();assert all(not row[-1].strip() for row in rows);rows=[row[:-1] for row in rows]
        v=np.array([[float(x) for x in row] for row in rows]);assert v.ndim==2 and v.shape[1]==len(keys)
    return {k:v[:,i] for i,k in enumerate(keys)}

def audit(revision,case_id):
    cfg=read(CFG);d=OUT/revision/case_id;meta=read(d/'generation.json');case=meta['case'];name=meta['name'];mesh=read(OUT/revision/'mesh.json');a=cfg['acceptance'];assert not (d/'audit.json').exists()
    H=histories(d/(name+'T01.csv'));has_observer=(d/'observer'/(name+'T02.csv')).exists()
    # T02 initial row is the start of the observer, i.e. physical-main end; subsequent step excluded.
    keys=list(H)
    if has_observer:
        Ho=histories(d/'observer'/(name+'T02.csv'));assert len(Ho['time'])==1 and keys==list(Ho);H={k:np.r_[H[k],Ho[k][0]] for k in keys}
    T=H['time'];assert np.all(np.diff(T)>0)
    Eterms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in Eterms)*.001;E0=E[0];EW=H['EXTERNAL WORK']*.001;residual=E-E0-EW
    generated=(H['ROTATION ENERGY']+H['INTERNAL ENERGY']+H['HOURGLASS ENERGY']+H['SPRING ENERGY']+H['ELASTIC CONTACT ENERGY'])*.001
    window=generated>a['local_energy_comparison_minimum_J'];ratio=np.abs(residual[window])/generated[window] if np.any(window) else np.array([0.])
    P=np.column_stack([H[ax+'-MOMENTUM'] for ax in 'XYZ'])*.001;Pf=np.column_stack([sum((H[k] for k in keys if k.startswith('FACADE_') and k.strip().endswith(ax+'MOM')),np.zeros(len(T))) for ax in 'XYZ'])*.001
    raw=np.column_stack([H[k] for k in keys if k.startswith('CONTACT_RAW_HISTORY')][:3]) if case['contact'] else np.zeros((len(T),3));J=(raw-raw[0])*.001
    support=np.column_stack([sum((H[k] for k in keys if k.startswith('SUPPORT_IMPULSE_'+ax)),np.zeros(len(T))) for ax in 'XYZ']);Js=(support-support[0])*.001;Js_force=integrate(support,T)*.001
    momtol=a['momentum_absolute_allowance_Ns']+a['momentum_relative_allowance']*float(np.max(np.linalg.norm(J,axis=1)));facadeerr=float(np.max(np.linalg.norm(Pf-Pf[0]-J-Js,axis=1)));gerr=float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)))
    PW=H['PLASTIC WORK']*.001;partpw=sum((H[k] for k in keys if k.strip().endswith('PW')),np.zeros(len(T)))*.001
    beamkeys=[k for k in keys if k.startswith('FORWARD_BEAM_DIAGNOSTIC')];bs=[H[k] for k in beamkeys if re.search(r'var ',k)]
    # Native /TH/TITLE probe confirms canonical order, NOT the variable order in the deck.
    assert len(beamkeys)==9*meta['beam_history_count'];B=np.column_stack([H[k] for k in beamkeys]).reshape(len(T),meta['beam_history_count'],9)
    beam_ids=read(OUT/revision/'beam_selection.json')['element_ids'];assert all(all(re.search(r'\s'+str(e)+r'\s+B'+str(e)+r'\s',k) for k in beamkeys[9*i:9*i+9]) for i,e in enumerate(beam_ids))
    beameps=B[:,:,8];beamSX=B[:,:,7];beammom=B[:,:,3:6];beamIE=B[:,:,6]*.001
    listing=(d/(name+'_0000.out')).read_text(errors='replace');mass=numbers_after(listing,'TOTAL MASS AND MASS CENTER',4)[0]*.001
    warnings=int(re.findall(r'(\d+) WARNING\(S\)',(d/'starter.log').read_text())[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',(d/'starter.log').read_text())[-1])
    x0=np.array(mesh['nodes_mm']);na=mesh['aircraft_node_count'];vel=np.array(cfg['velocity_m_s']);edges=set()
    for el in mesh['original_triangle_node_ids']:
        edges.update(tuple(sorted((el[j]-1,el[(j+1)%3]-1))) for j in range(3))
    for el in mesh['original_beam_node_ids']:edges.add(tuple(sorted((el[0]-1,el[1]-1))))
    edge=np.array(sorted(edges));L0=np.linalg.norm(x0[edge[:,1]]-x0[edge[:,0]],axis=1)
    original=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json');parts_by_id={i+1:e['part'] for i,e in enumerate(original['triangular_shells'])};extern={'fuselage_skin','fuselage_caps','wing_skin','horizontal_tail','horizontal_tail_caps','vertical_tail','vertical_tail_caps'}
    animations=[p for p in d.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name)]+[p for p in (d/'observer').glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name)]
    times=[];D=[];V=[];EPS=[];VMU=[];VML=[];VMM=[];samples=[];native_audit=[];topcheck=True;fixederr=0.;freeD=0.;freeV=0.;maxcoord=0.;finalcapdisplacement=0.;ids=None;info=None;maxeps=0.;epsfirst=None
    for p in animations:
        start=time.perf_counter();proc=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=cfg['execution']['converter_timeout_s']);q=vtk(proc.stdout);tm=q['time']
        if times and abs(tm-times[-1])<1e-6:continue
        if tm>T[-1]+1e-5:continue
        order=np.argsort(q['NODE_ID']);nid=q['NODE_ID'].astype(int)[order];assert np.array_equal(nid,np.arange(1,len(x0)+1));disp=q['Displacement'].reshape(-1,3)[order];v=q['Velocity'].reshape(-1,3)[order]
        if ids is None:
            ids=nid;info={k:q[qk].astype(int) for k,qk in [('element_ids','ELEMENT_ID'),('part_ids','PART_ID'),('cell_types','types')]};cells=topology(q);index={int(e):i for i,e in enumerate(q['ELEMENT_ID']) if e>0};nc=len(mesh['original_triangle_node_ids'])
            for i,t in enumerate(q['types']):
                if t==5:assert len(cells[i])==4 and cells[i][-1]==cells[i][-2];cells[i]=cells[i][:3]
            topcheck=all(cells[index[startid+i]]==el for k,startid in [('original_triangle_node_ids',1),('original_beam_node_ids',nc+1),('facade_quads_node_ids',20001)] for i,el in enumerate(mesh[k]))
            smask=np.array([parts_by_id.get(int(e)) in extern for e in info['element_ids']]);fmask=info['cell_types']==9;imask=(info['cell_types']==5)&~smask
        else:assert np.array_equal(nid,ids) and np.array_equal(q['ELEMENT_ID'].astype(int),info['element_ids'])
        epkeys=[k for k in q if 'Plast_Strn_Layer_' in k];eps=np.max(np.vstack([q[k] for k in epkeys]),axis=0) if epkeys else np.zeros(len(q['types']));mvm=q['2DELEM_Von_Mises']
        upper=vm_tensor(q['2DELEM_Stress_(upper)']) if '2DELEM_Stress_(upper)' in q else mvm;lower=vm_tensor(q['2DELEM_Stress_(lower)']) if '2DELEM_Stress_(lower)' in q else mvm;fiber=np.maximum(upper,lower)
        maxeps=max(maxeps,float(np.max(eps)));eps_active=float(np.max(eps))>1e-8
        if eps_active and epsfirst is None:epsfirst=tm
        normcoord=float(np.max(abs(q['points'].reshape(-1,3)[order]-x0-disp)));maxcoord=max(maxcoord,normcoord)
        fixederr=max(fixederr,float(np.max(abs(disp[np.array(mesh['fixed_node_ids'])-1]))));target=np.vstack([np.tile(tm*vel,(na,1)),np.zeros((len(x0)-na,3))]);targetv=np.vstack([np.tile(vel,(na,1)),np.zeros((len(x0)-na,3))]);freeD=max(freeD,float(np.max(abs(disp-target))));freeV=max(freeV,float(np.max(abs(v-targetv))))
        def vmax(s,m):return float(np.max(s[m],initial=0))
        samples.append({'time_ms':tm,'maximum_plastic_strain':float(np.max(eps)),'skin_plastic_strain':vmax(eps,smask),'steel_plastic_strain':vmax(eps,fmask),'internal_shell_plastic_strain':vmax(eps,imask),
            'skin_mean_von_mises_MPa':vmax(mvm,smask),'steel_mean_von_mises_MPa':vmax(mvm,fmask),'skin_outermost_point_von_mises_MPa':vmax(fiber,smask),'steel_outermost_point_von_mises_MPa':vmax(fiber,fmask),
            'maximum_aircraft_geometric_edge_extension_fraction':float(np.max(abs(np.linalg.norm((x0+disp)[edge[:,1]]-(x0+disp)[edge[:,0]],axis=1)/L0-1))),
            'maximum_free_flight_relative_X_mm':float(np.max(abs(disp[:na,0]-tm*vel[0]))),'converter_seconds':time.perf_counter()-start})
        assert np.all(q['EROSION_STATUS']==1);times.append(tm);D.append(disp.astype(np.float32)*.001);V.append(v.astype(np.float32));EPS.append(eps.astype(np.float32));VMU.append(upper.astype(np.float32));VML.append(lower.astype(np.float32));VMM.append(mvm.astype(np.float32));native_audit.append({'path':rel(p),'sha256':sha(p)})
    assert times and np.all(np.diff(times)>0)
    if has_observer:assert abs(times[-1]-T[-1])<1e-5
    np.savez_compressed(d/'verified_states_SI.npz',time_s=np.array(times)*.001,node_ids=ids,initial_positions_m=x0*.001,displacement_m=np.array(D),velocity_m_s=np.array(V),shell_max_layer_plastic_strain=np.array(EPS),shell_von_mises_mean_MPa=np.array(VMM),shell_von_mises_upper_MPa=np.array(VMU),shell_von_mises_lower_MPa=np.array(VML),**info)
    np.savez_compressed(d/'balance_history_SI.npz',time_s=T*.001,global_momentum_Ns=P,facade_momentum_Ns=Pf,contact_impulse_Ns=J,support_as_cumulative_impulse_Ns=Js,support_as_force_integral_Ns=Js_force,energy_total_J=E,energy_residual_J=residual,generated_energy_J=generated,global_plastic_work_J=PW,part_plastic_work_J=partpw,beam_history_native=B.astype(np.float32),beam_element_ids=np.array(read(OUT/revision/'beam_selection.json')['element_ids']))
    actualend=float(T[-1]);dt=float(H['TIME STEP'][-1]);localpass=bool(np.all(np.abs(residual[window])<=a['local_energy_residual_generated_energy_fraction']*generated[window]+a['CSV_KE_precision_allowance_J']))
    checks={'starter_zero_errors':errors==0,'starter_zero_warnings':warnings==0,'main_engine_normal_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(),'observer_normal_termination':has_observer and 'NORMAL TERMINATION' in (d/'observer/observer.log').read_text(),'observer_did_not_change_main_outputs':has_observer and read(d/'observer_preservation.json')['main_outputs_unchanged'],
        'mass_preserved':abs(mass-mesh['expected_total_mass_kg'])/mass<a['mass_relative_error'],'added_mass_within_fraction':float(np.max(abs(H['ADDED MASS'])))/(mass*1000)<a['added_mass_fraction'],
        'native_original_connectivity_preserved':topcheck,'all_exported_states_finite':all(np.all(np.isfinite(q)) for q in [D,V,EPS,VMU,VML,VMM]),'supports_fixed':fixederr<1e-8,
        'native_end_timestamp_observed_within_step':has_observer and 0<=actualend-case['end_ms']<=a['final_timestamp_overshoot_native_step_factor']*dt,
        'energy_global_within_declared_limit':float(np.max(abs(residual)))/E0<a['global_energy_residual_initial_KE_fraction'],'energy_local_within_declared_limit':localpass,
        'momentum_global_support_balance':gerr<momtol,'momentum_contact_facade_balance':facadeerr<momtol,
        'global_and_part_plastic_work_nonnegative':float(np.min(PW))>=-a['negative_plastic_work_allowance_J'] and float(np.min(partpw))>=-a['negative_plastic_work_allowance_J'],
        'plastic_strain_below_diagnostic_limit':maxeps<=a['plastic_strain_diagnostic_limit'],'no_erosion':True,'no_external_work':bool(np.all(EW==0))}
    if not case['contact']:checks.update(free_displacement_uniform=freeD<a['free_displacement_error_mm'],free_velocity_uniform=freeV<a['free_velocity_error_m_s'],free_plastic_strain_zero=maxeps==0,free_energies_zero=bool(np.all(generated==0) and np.all(PW==0)))
    if case['law']!='plastic':checks['high_yield_or_elastic_plastic_work_zero']=bool(np.all(PW==0) and maxeps==0)
    checks={k:bool(v) for k,v in checks.items()}
    core=[k for k in checks if k not in ['energy_local_within_declared_limit','plastic_strain_below_diagnostic_limit']]
    onset=float(T[np.flatnonzero(np.linalg.norm(J,axis=1)>0)[0]]) if np.any(J) else None;pwtime=float(T[np.flatnonzero(PW>1e-6)[0]]) if np.any(PW>1e-6) else None
    result={'created_utc':now(),'case':case,'checks':checks,'all_declared_checks_pass':all(checks.values()),'core_execution_and_transfer_checks_pass':all(checks[k] for k in core),'failed_checks':[k for k,v in checks.items() if not v],
        'native_total_mass_kg':mass,'actual_main_end_time_ms':actualend if has_observer else None,'last_history_time_ms':actualend,'last_animation_time_ms':times[-1],'main_end_observed':has_observer,'requested_horizon_reached':has_observer and actualend>=case['end_ms'],'observer_timestamp_role':'T02 initial saved history plus first observer animation; continuation step excluded. No observer for a timed-out run; last saved history is not a verified end timestamp.',
        'initial_KE_J':float(E0),'energy_terms_without_double_counting':Eterms,'global_plastic_work_is_subset_of_IE_not_added_again':True,'maximum_energy_residual_J':float(np.max(abs(residual))),
        'maximum_energy_residual_initial_KE_fraction':float(np.max(abs(residual)))/E0,'maximum_local_energy_residual_fraction_above_1kJ':float(np.max(ratio)),
        'final_energy_residual_J':float(residual[-1]),'final_generated_energy_J':float(generated[-1]),'final_energy_terms_J':{k:float(H[k][-1])*.001 for k in Eterms},'final_global_plastic_work_J':float(PW[-1]),'final_sum_part_plastic_work_J':float(partpw[-1]),
        'contact_onset_history_ms':onset,'plastic_work_onset_history_ms':pwtime,'first_saved_plastic_strain_ms':epsfirst,'maximum_shell_plastic_strain':maxeps,'maximum_sampled_beam_plastic_strain':float(np.max(beameps)),
        'maximum_sampled_beam_abs_SX_MPa':float(np.max(abs(beamSX))),'maximum_sampled_beam_bending_moment_Nmm':float(np.max(np.linalg.norm(beammom[:,:,1:],axis=2))),
        'beam_history_native_order':['F1','F2','F3','M1','M2','M3','IE','SX','EPSP'],'beam_history_scope':'696 forward beams with max endpoint X<=8m; SX is native axial stress, not an outer-fiber bending maximum. Native resultants are preserved; section resolved yielding unknown.',
        'final_contact_impulse_Ns':J[-1].tolist(),'final_facade_momentum_Ns':Pf[-1].tolist(),'contact_balance_max_error_Ns':facadeerr,'global_support_balance_max_error_Ns':gerr,'momentum_allowance_Ns':momtol,'maximum_support_raw':float(np.max(abs(support))),
        'support_units_independently_distinguished':False,'contact_impulse_interpretation_inherited_and_balance_checked':True,'maximum_added_mass_g':float(np.max(abs(H['ADDED MASS']))),'maximum_export_coordinate_rounding_mm':maxcoord,
        'free_reference_max_displacement_difference_mm':freeD,'states':samples,'native_animations':native_audit,'physical_impact_qualified':False,'radome_reconstructed':False,'no_fracture':True,
        'runtime':[read(p) for p in [d/'starter.log.execution.json',d/'engine.log.execution.json',d/'observer/observer.log.execution.json',d/'converter_T01.log.execution.json',d/'observer/converter_T02.log.execution.json'] if p.exists()]}
    dump(d/'audit.json',result);print(json_summary(result),flush=True);return result

def json_summary(r):return {'case':r['case']['id'],'core_pass':r['core_execution_and_transfer_checks_pass'],'failed':r['failed_checks'],'end_ms':r['actual_main_end_time_ms'],'PW_J':r['final_global_plastic_work_J'],'epsp_max':r['maximum_shell_plastic_strain'],'E_local_max_fraction':r['maximum_local_energy_residual_fraction_above_1kJ']}

def main(revision,case):
    if case:return audit(revision,case)
    cfg=read(CFG);cases=[read(OUT/revision/c['id']/'audit.json') for c in cfg['execution']['cases']];nom,half=cases[3],cases[4];z=[np.load(OUT/revision/r['case']['id']/'balance_history_SI.npz') for r in [nom,half]];tc=min(q['time_s'][-1] for q in z)
    J=[np.array([np.interp(tc,q['time_s'],q['contact_impulse_Ns'][:,i]) for i in range(3)]) for q in z];gen=[float(np.interp(tc,q['time_s'],q['generated_energy_J'])) for q in z]
    jd=float(np.linalg.norm(J[1]-J[0])/np.linalg.norm(J[0]));ed=abs(gen[1]-gen[0])/max(gen[0],1e-12);checks={'all_final_cases_core_pass':all(r['core_execution_and_transfer_checks_pass'] for r in cases),'half_dt_impulse':jd<cfg['acceptance']['half_dt_impulse_difference_fraction'],'half_dt_generated_energy':ed<cfg['acceptance']['half_dt_generated_energy_difference_fraction']}
    comparison=[]
    # Reuse A03 native histories, never rerun its engines. Compare at common actual time.
    old=np.load(PREV/'r0/CONTACT_F200_DT080/balance_history_SI.npz');told=old['time_s'][-1]
    for r in cases[:2]+[nom]:
        q=np.load(OUT/revision/r['case']['id']/'balance_history_SI.npz');tc2=min(told,q['time_s'][-1]);res=float(np.interp(tc2,q['time_s'],q['energy_residual_J']));resold=float(np.interp(tc2,old['time_s'],old['energy_residual_J']));comparison.append({'case':r['case']['id'],'common_time_ms':tc2*1000,'A03_energy_residual_J':resold,'A04_energy_residual_J':res,'difference_J':res-resold,'change_scope':'N0 elastic differs only beam df; high-yield N5 also changes material implementation/integration; nominal also enables yielding. Not all are pure single-parameter comparisons.'})
    target=OUT/revision/'summary.json';assert not target.exists();r={'created_utc':now(),'revision':revision,'cases':cases,'checks':checks,'core_and_timestep_checks_pass':all(checks.values()),'all_declared_checks_pass':all(checks.values()) and all(c['all_declared_checks_pass'] for c in cases),'half_dt_common_time_ms':tc*1000,'half_dt_impulse_relative_difference':jd,'half_dt_generated_energy_relative_difference':ed,'A03_cached_comparison':comparison,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':all(c['checks']['energy_local_within_declared_limit'] for c in cases),'old_A03_elastic_failures_retained':True,'radome_reconstructed':False,'NIST_outcomes_used_as_target':False};dump(target,r);print({k:r[k] for k in ['checks','all_declared_checks_pass','local_energy_ledger_fully_qualified','half_dt_impulse_relative_difference']},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',default='r1');p.add_argument('--case');a=p.parse_args();main(a.revision,a.case)
