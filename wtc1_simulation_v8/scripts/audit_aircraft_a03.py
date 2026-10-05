"""Audit cached whole-aircraft first contact; preserve elasticity failures and units."""
import argparse,csv,re,subprocess,time
import numpy as np
from run_aircraft_a03 import ROOT,CFG,OUT,PREV,RUNTIME,read,dump,sha,rel,now
from audit_aircraft_a02 import numbers_after
from export_impact_i02a import parse_vtk

def topology(q):
    cells=[];i=0
    while i<len(q['cells']):
        n=int(q['cells'][i]);cells.append(q['NODE_ID'][q['cells'][i+1:i+n+1].astype(int)].astype(int).tolist());i+=n+1
    assert len(cells)==len(q['types'])
    return cells

def integrate(y,t):
    return np.vstack([np.zeros(y.shape[1]),np.cumsum((y[1:]+y[:-1])*.5*np.diff(t)[:,None],axis=0)])

def audit_case(revision,case):
    cfg=read(CFG);a=cfg['acceptance'];d=OUT/revision/case['id'];name=read(d/'generation.json')['name'];mesh=read(OUT/revision/'mesh.json')
    assert not (d/'audit.json').exists()
    rows=list(csv.DictReader((d/(name+'T01.csv')).open(encoding='utf-8-sig')));keys=list(rows[0]);H={k:np.array([float(r[k]) for r in rows]) for k in keys}
    T=H['time'];P=np.column_stack([H[k+'-MOMENTUM'] for k in 'XYZ'])*.001
    Pf=np.column_stack([sum((H[k] for k in keys if k.startswith('FACADE_') and k.strip().endswith(axis+'MOM')),np.zeros(len(T))) for axis in 'XYZ'])*.001
    Pa=P-Pf;support=np.column_stack([sum((H[k] for k in keys if k.startswith('SUPPORT_IMPULSE_'+axis)),np.zeros(len(T))) for axis in 'XYZ'])
    Js=(support-support[0])*.001;Js_force=integrate(support,T)*.001
    cs=[k for k in keys if k.startswith('CONTACT_RAW_HISTORY')]
    C=np.column_stack([H[k] for k in cs[:3]]) if cs else np.zeros((len(T),3))
    J=(C-C[0])*.001;J_force=integrate(C,T)*.001
    error_impulse=float(np.max(np.linalg.norm(Pf-Pf[0]-J-Js,axis=1)))
    error_force=float(np.max(np.linalg.norm(Pf-Pf[0]-J_force-Js_force,axis=1)))
    peakJ=float(np.max(np.linalg.norm(J,axis=1)));tol=a['momentum_CSV_absolute_precision_allowance_Ns']+a['momentum_balance_fraction']*peakJ
    energy_names=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    E=sum(H[k] for k in energy_names)*.001;E0=float(E[0]);EW=H['EXTERNAL WORK']*.001;residual=E-E[0]-EW
    listed=(d/(name+'_0000.out')).read_text(errors='replace');native=numbers_after(listed,'TOTAL MASS AND MASS CENTER',4)
    starter=(d/'starter.log').read_text();engine=(d/'engine.log').read_text();warnings=int(re.findall(r'(\d+) WARNING\(S\)',starter)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',starter)[-1])
    x0=np.array(mesh['nodes_mm']);na=mesh['aircraft_node_count'];vel=np.array(cfg['aircraft']['velocity_m_s']);expectedD=lambda tm: np.vstack([np.tile(tm*vel,(na,1)),np.zeros((len(x0)-na,3))])
    edges=set()
    for el in mesh['original_triangle_node_ids']:
        edges.update(tuple(sorted((el[j]-1,el[(j+1)%3]-1))) for j in range(3))
    for el in mesh['original_beam_node_ids']:edges.add(tuple(sorted((el[0]-1,el[1]-1))))
    edge=np.array(sorted(edges));L0=np.linalg.norm(x0[edge[:,1]]-x0[edge[:,0]],axis=1)
    times=[];D=[];V=[];S=[];samples=[];nodeids=None;cellinfo=None;maxD=0.;maxV=0.;maxfixed=0.;maxround=0.;maxstrain=0.;first_diag=None;peakstress={'skin':0.,'internals':0.,'steel':0.};topcheck=False
    # Original shell/beam IDs preserved by construction; check actual native connectivity too.
    original=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json')
    external_names={'fuselage_skin','fuselage_caps','wing_skin','horizontal_tail','horizontal_tail_caps','vertical_tail','vertical_tail_caps'}
    skin_element_ids={i+1 for i,e in enumerate(original['triangular_shells']) if e['part'] in external_names}
    for anim in sorted(d.glob(name+'A*')):
        if not re.fullmatch(re.escape(name)+r'A\d{3}',anim.name):continue
        start=time.perf_counter();proc=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(anim)],capture_output=True,text=True,encoding='utf-8',timeout=cfg['execution']['converter_timeout_s']);assert proc.returncode==0,proc.stderr
        q=parse_vtk(proc.stdout);raw_ids=q['NODE_ID'].astype(int);order=np.argsort(raw_ids);ids=raw_ids[order];assert np.array_equal(ids,np.arange(1,len(x0)+1))
        disp=q['Displacement'].reshape(-1,3)[order];v=q['Velocity'].reshape(-1,3)[order];tm=q['time'];stress=q['2DELEM_Von_Mises'];parts=q['PART_ID'].astype(int)
        if nodeids is None:
            nodeids=ids;cells=topology(q);cellinfo={'element_ids':q['ELEMENT_ID'].astype(int),'part_ids':parts,'cell_types':q['types'].astype(int)}
            nc=len(mesh['original_triangle_node_ids']);nb=len(mesh['original_beam_node_ids'])
            index={int(e):i for i,e in enumerate(cellinfo['element_ids']) if e>0}
            topcheck=all(cells[index[i+1]]==el for i,el in enumerate(mesh['original_triangle_node_ids'])) and all(cells[index[nc+i+1]]==el for i,el in enumerate(mesh['original_beam_node_ids'])) and all(cells[index[20001+i]]==el for i,el in enumerate(mesh['facade_quads_node_ids']))
        else:assert np.array_equal(ids,nodeids) and np.array_equal(q['ELEMENT_ID'].astype(int),cellinfo['element_ids'])
        maxD=max(maxD,float(np.max(abs(disp-expectedD(tm)))));targetV=expectedD(1.);maxV=max(maxV,float(np.max(abs(v-targetV))))
        maxfixed=max(maxfixed,float(np.max(abs(disp[np.array(mesh['fixed_node_ids'])-1]))));maxround=max(maxround,float(np.max(abs(q['points'].reshape(-1,3)[order]-x0-disp))))
        current=x0+disp;eps=np.linalg.norm(current[edge[:,1]]-current[edge[:,0]],axis=1)/L0-1;emax=float(np.max(abs(eps)));maxstrain=max(maxstrain,emax)
        skinmask=np.isin(cellinfo['element_ids'],list(skin_element_ids));internalmask=(cellinfo['cell_types']==5)&~skinmask;steelmask=cellinfo['cell_types']==9
        vals={'skin':float(np.max(stress[skinmask],initial=0)), 'internals':float(np.max(stress[internalmask],initial=0)), 'steel':float(np.max(stress[steelmask],initial=0))}
        limits=cfg['elastic_diagnostics'];exceeded=emax>limits['triangle_or_beam_edge_extension_absolute_limit'] or vals['skin']>limits['skin_midplane_von_mises_limit_MPa'] or vals['internals']>limits['internal_alloy_midplane_von_mises_limit_MPa'] or vals['steel']>limits['steel_midplane_von_mises_limit_MPa']
        if exceeded and first_diag is None:first_diag=tm
        for k in vals:peakstress[k]=max(peakstress[k],vals[k])
        samples.append({'time_ms':tm,'maximum_aircraft_edge_extension_fraction':emax,'midplane_shell_von_mises_MPa':vals,'elastic_diagnostic_exceeded':exceeded,'converter_seconds':time.perf_counter()-start})
        times.append(tm);D.append(disp*.001);V.append(v);S.append(stress);assert np.all(q['EROSION_STATUS']==1), 'Unexpected element erosion'
    assert times
    np.savez_compressed(d/'verified_states_SI.npz',time_s=np.array(times)*.001,node_ids=nodeids,initial_positions_m=x0*.001,displacement_m=np.array(D),velocity_m_s=np.array(V),shell_midplane_von_mises_MPa=np.array(S),**cellinfo)
    np.savez_compressed(d/'balance_history_SI.npz',time_s=T*.001,global_momentum_Ns=P,facade_momentum_Ns=Pf,aircraft_momentum_Ns=Pa,contact_raw=C,contact_as_cumulative_impulse_Ns=J,contact_as_integrated_force_Ns=J_force,support_raw=support,support_as_cumulative_impulse_Ns=Js,support_as_integrated_force_Ns=Js_force,total_accounted_energy_J=E,energy_residual_J=residual)
    onset=float(T[np.flatnonzero(np.linalg.norm(C,axis=1)>0)[0]]) if np.any(C) else None
    AM=float(np.max(abs(H['ADDED MASS'])));mass=native[0]*.001;lastdt=float(H['TIME STEP'][-1]);overshoot=times[-1]-cfg['execution']['end_ms']
    initialKE=.5*read(PREV/'r1/translation_dt080/audit.json')['native_mass_kg']*float(vel@vel)
    checks={'starter_zero_errors':errors==0,'starter_zero_warnings':warnings==0,'engine_normal_termination':'NORMAL TERMINATION' in engine,
        'native_total_mass_within_predeclared_fraction':abs(mass-mesh['expected_total_mass_kg'])/mesh['expected_total_mass_kg']<a['mass_relative_error'],
        'initial_KE_matches_flying_aircraft_only':abs(E0-initialKE)/initialKE<a['mass_relative_error'],
        'added_mass_fraction_below_declared_limit':AM/(mass*1000)<a['added_mass_fraction'],
        'global_energy_residual_within_declared_limit':float(np.max(abs(residual)))/E0<a['max_global_energy_residual_fraction'],
        'hourglass_below_declared_fraction':float(np.max(abs(H['HOURGLASS ENERGY'])))*.001/E0<a['hourglass_initial_KE_fraction'],
        'fixed_support_displacements_zero':maxfixed<1e-8,'all_nodes_and_finite_states':len(nodeids)==len(x0) and all(np.all(np.isfinite(v)) for v in [D,V,S]),
        'original_aircraft_and_new_facade_connectivity_preserved':topcheck,
        'global_momentum_support_balance_with_CSV_allowance':float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)))<tol,
        'end_overshoot_within_one_native_step':0<=overshoot<=a['end_overshoot_maximum_native_step_factor']*lastdt,
        'zero_external_work':bool(np.all(EW==0))}
    if case['contact']:checks.update(contact_cumulative_impulse_balances_facade=error_impulse<tol,contact_cumulative_interpretation_distinguished=error_force>10*max(error_impulse,1e-12))
    else:checks.update(free_whole_scene_displacement=maxD<a['free_node_displacement_error_mm'],free_whole_scene_velocity=maxV<a['free_node_velocity_error_m_s'],free_internal_energy_zero=bool(np.all(H['INTERNAL ENERGY']==0)))
    checks={k:bool(v) for k,v in checks.items()}
    result={'created_utc':now(),'case':case,'revision':revision,'checks':checks,'numerical_checks_pass':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],
        'native_total_mass_kg':mass,'initial_KE_J':E0,'energy_terms_without_double_counting':energy_names,'energy_residual_max_J':float(np.max(abs(residual))), 'energy_residual_max_initial_KE_fraction':float(np.max(abs(residual)))/E0,
        'last_history_energy_J':{k:float(H[k][-1])*.001 for k in energy_names},'last_history_time_ms':float(T[-1]),'final_state_time_ms':times[-1],'end_overshoot_ms':overshoot,'last_native_dt_ms':lastdt,
        'last_contact_impulse_Ns':J[-1].tolist(),'last_facade_momentum_Ns':Pf[-1].tolist(),'last_aircraft_delta_momentum_Ns':(Pa[-1]-Pa[0]).tolist(),
        'contact_raw_cumulative_impulse_balance_max_error_Ns':error_impulse,'contact_raw_as_force_integral_balance_max_error_Ns':error_force,'momentum_declared_absolute_and_relative_allowance_Ns':tol,
        'last_contact_raw':C[-1].tolist(),'last_contact_raw_as_force_integral_Ns':J_force[-1].tolist(),'contact_onset_history_ms':onset,
        'support_raw_max_abs':float(np.max(abs(support))),'support_unit_interpretation':'Both cumulative and force-integrated forms retained. Support signals nearly zero on this short window, so their units are NOT independently distinguished here.',
        'contact_unit_interpretation':'Native TH FNX/FNY/FNZ behaves as cumulative Nms on this build, demonstrated against facade momentum; documented force name is insufficient. Raw columns and competing N-force integration preserved.',
        'maximum_added_mass_g':AM,'maximum_added_mass_fraction':AM/(mass*1000),'free_reference_max_displacement_difference_mm':maxD,'free_reference_max_velocity_difference_m_s':maxV,
        'coordinate_serialization_max_identity_error_mm':maxround,'maximum_aircraft_edge_extension_fraction':maxstrain,'maximum_shell_midplane_stress_MPa':peakstress,
        'beam_stress_not_exported':True,'first_saved_elastic_diagnostic_exceedance_ms':first_diag,'elastic_diagnostics_pass':first_diag is None,'physical_impact_qualified':False,'states':samples,'runtime':[read(d/(n+'.execution.json')) for n in ['starter.log','engine.log','converter.log']]}
    dump(d/'audit.json',result);print(case['id'],result['failed_checks'],peakstress,first_diag);return result

def main(revision):
    cfg=read(CFG);cases=[read(OUT/revision/c['id']/'audit.json') if (OUT/revision/c['id']/'audit.json').exists() else audit_case(revision,c) for c in cfg['execution']['cases']]
    x,y=[np.load(OUT/revision/c['case']['id']/'balance_history_SI.npz') for c in cases[1:]];t=min(x['time_s'][-1],y['time_s'][-1]);j=[]
    for z in [x,y]:j.append(np.array([np.interp(t,z['time_s'],z['contact_as_cumulative_impulse_Ns'][:,i]) for i in range(3)]))
    diff=float(np.linalg.norm(j[1]-j[0])/max(np.linalg.norm(j[0]),1e-30));onset=abs(cases[1]['contact_onset_history_ms']-cases[2]['contact_onset_history_ms'])
    checks={'all_three_numerical_case_checks':all(c['numerical_checks_pass'] for c in cases),'contact_impulse_half_dt':diff<cfg['acceptance']['half_dt_contact_impulse_difference_fraction'],'contact_onset_half_dt':onset<cfg['acceptance']['half_dt_onset_difference_ms']}
    r={'created_utc':now(),'revision':revision,'cases':cases,'checks':checks,'numerical_checks_pass':all(checks.values()),'half_dt_comparison_common_time_ms':t*1000,'half_dt_common_time_contact_impulses_Ns':[v.tolist() for v in j],'half_dt_impulse_relative_difference':diff,'half_dt_onset_difference_ms':onset,
        'all_elastic_diagnostics_pass':all(c['elastic_diagnostics_pass'] for c in cases),'physical_impact_qualified':False,'A02_strict_failures_retained':True,'NIST_damage_outputs_used_as_target':False}
    assert not (OUT/revision/'summary.json').exists();dump(OUT/revision/'summary.json',r);print({k:r[k] for k in ['checks','numerical_checks_pass','half_dt_impulse_relative_difference','all_elastic_diagnostics_pass']})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',default='r0');main(p.parse_args().revision)
