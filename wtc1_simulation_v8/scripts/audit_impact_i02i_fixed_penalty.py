"""Saved-history audits for fresh fixed-penalty coupons; never launch a solver."""
from __future__ import annotations
import argparse, csv, json, math, re
from pathlib import Path
import numpy as np
import audit_impact_i02g as old
from run_impact_i02i_fixed_penalty import ROOT, CFG, OUTPUT, dump, sha


def columns(headers,title,n):
    mapping=old.entity_columns(headers,title,n)
    assert mapping,'Missing channel '+title
    return {k:[headers.index(x) for x in v] for k,v in mapping.items()}


def read(folder):
    with next(folder.glob('*.csv')).open(newline='',encoding='utf-8') as f:
        r=csv.reader(f); headers=next(r); data=np.array([[float(x) for x in row] for row in r],dtype=float)
    assert len(data)>1 and np.all(np.isfinite(data)) and np.all(np.diff(data[:,0])>0)
    return headers,data


def sensor_check():
    p=OUTPUT/'SENSOR_STOP_R2'; m=json.loads((p/'generation.json').read_text()); headers,d=read(p)
    status=columns(headers,'DOMAIN_STOP_STATUS',1)[501][0]
    nodes=columns(headers,'NODES',6)
    # Canonical order DX,DY,VX,VY,REACX,REACY verified by I02I-A.
    dx=10+d[:,nodes[2][0]]-d[:,nodes[1][0]]; dy=d[:,nodes[2][1]]-d[:,nodes[1][1]]
    dist=np.hypot(dx,dy); text=(p/(m['name']+'_0001.out')).read_text(errors='replace')
    checks={'normal_user_stop':'NORMAL TERMINATION' in text and 'USER BREAK' in text,'status_activated':d[-1,status]==1,'stopped_before_requested_end':d[-1,0]<m['configured_end_ms']*.5,'threshold_reached':10.01<=dist[-1]<=10.0102,'completed_three_jobs':len(json.loads((p/'execution.json').read_text()))==3}
    checks={k:bool(v) for k,v in checks.items()}
    result={'pass':all(checks.values()),'checks':checks,'end_ms':float(d[-1,0]),'end_distance_mm':float(dist[-1]),'requested_end_ms':m['configured_end_ms']}
    return result


def audit_case(folder,destination,cfg):
    m=json.loads((folder/'generation.json').read_text()); executions=json.loads((folder/'execution.json').read_text())
    headers,d=read(folder); idx={v.strip():i for i,v in enumerate(headers)}
    t=d[:,0]; seam=columns(headers,'SEAM_HISTORY',6); upper=columns(headers,'UPPER_GRIP_HISTORY',3); lower=columns(headers,'LOWER_GRIP_HISTORY',3); nodes=columns(headers,'SEAM_NODE_HISTORY',2); plastic=columns(headers,'TIP_PLASTIC_HISTORY',1)
    c=lambda name:d[:,idx[name]]
    pairs=m['seam_pairs']; n=len(t); u=np.mean(d[:,[v[0] for v in upper.values()]],axis=1)
    ju=np.sum(d[:,[v[2] for v in upper.values()]],axis=1); jl=np.sum(d[:,[v[2] for v in lower.values()]],axis=1)
    work_increments=np.zeros(n-1)
    for mapping in [upper,lower]:
        for ci in mapping.values(): work_increments += np.diff(d[:,ci[2]])/np.diff(t)*np.diff(d[:,ci[0]])*.001
    actuator=np.r_[0,np.cumsum(work_increments)]
    actuator_force=np.diff(ju)/np.diff(t); bottom_force=np.diff(jl)/np.diff(t)
    force=np.sum(d[:,[v[2] for v in seam.values()]],axis=1)
    spring_ie=np.sum(d[:,[v[5] for v in seam.values()]],axis=1)*.001
    ie=c('INTERNAL ENERGY')*.001; ke=c('KINETIC ENERGY')*.001; we=c('EXTERNAL WORK')*.001
    energy_scale=max(np.max(np.abs(we)),np.max(np.abs(ie)),1e-15)
    significant=ie>=.01*np.max(ie)
    opens=d[:,[nodes[x][1] for x in m['upper_seam_nodes']]]-d[:,[nodes[x][1] for x in m['lower_seam_nodes']]]
    slip=d[:,[nodes[x][0] for x in m['upper_seam_nodes']]]-d[:,[nodes[x][0] for x in m['lower_seam_nodes']]]
    xs=np.array(m['mesh']['x_coordinates_mm']); half=cfg['geometry']['initial_total_crack_length_mm']/2; b=cfg['geometry']['thickness_mm']
    ext=np.zeros((n,2)); nodal=np.zeros((n,2)); broken=np.zeros(n,dtype=int); max_gap_error=0.; law_error=0.; seam_quadrature=np.zeros(n)
    for p in pairs:
        ci=seam[p['element_id']]; j=int(np.argmin(np.abs(xs-p['x_mm']))); active=d[:,ci[0]]>=.5
        assert d[0,ci[0]]==1 and abs(p['normal_stiffness_N_per_mm']/p['area_mm2']-cfg['seam']['normal_penalty_N_per_mm3'])<1e-8
        assert abs(p['tangent_stiffness_N_per_mm']/p['area_mm2']-cfg['seam']['tangent_penalty_N_per_mm3'])<1e-8
        assert np.all(np.diff(d[:,ci[0]])<=1e-7),'Connector reactivation'
        broken += (~active)
        if np.any(active): max_gap_error=max(max_gap_error,float(np.max(np.abs(d[active,ci[4]]-opens[active,j]))))
        elastic=active & (np.abs(d[:,ci[4]])<=.95*p['delta0_mm'])
        if np.any(elastic): law_error=max(law_error,float(np.max(np.abs(d[elastic,ci[2]]-p['normal_stiffness_N_per_mm']*d[elastic,ci[4]])))/max(p['peak_force_N'],1))
        increments=(.5*(d[:-1,ci[1]]+d[1:,ci[1]])*np.diff(d[:,ci[3]])+.5*(d[:-1,ci[2]]+d[1:,ci[2]])*np.diff(d[:,ci[4]]))*.001
        seam_quadrature += np.r_[0,np.cumsum(increments)]
    for side,label in enumerate(['left','right']):
        ordered=sorted([p for p in pairs if p['side']==label],key=lambda p:abs(p['x_mm']))
        contiguous=np.ones(n,dtype=bool)
        for p in ordered:
            contiguous &= d[:,seam[p['element_id']][0]]<.5
            ext[:,side] += contiguous*p['tributary_width_mm']
            nodal[contiguous,side]=abs(p['x_mm'])-half
    meanext=ext.mean(axis=1); meannodal=nodal.mean(axis=1)
    angles=[]
    for i in range(n):
        row=[]
        for offset in [b,2*b]:
            xx=[-half-ext[i,0]+offset,half+ext[i,1]-offset]
            assert all(xs[0]<=x<=xs[-1] for x in xx)
            gaps=[max(0,float(np.interp(x,xs,opens[i]))) for x in xx]
            row.append(sum(math.degrees(2*math.atan2(g,2*offset)) for g in gaps)/2)
        angles.append(row)
    angles=np.array(angles); pmax=float(np.max(d[:,[v[0] for v in plastic.values()]])); lastsource=m['conversion_ledger'][-1]['plastic_strain']
    states=[{'time_ms':float(t[i]),'displacement_mm':float(u[i]),'section_force_N':float(force[i]),'remote_initial_area_stress_MPa':float(force[i]/(cfg['geometry']['width_mm']*b)),'external_work_J':float(we[i]),'internal_energy_J':float(ie[i]),'kinetic_energy_J':float(ke[i]),'actuator_work_J':float(actuator[i]),'area_advance_mm':float(meanext[i]),'left_area_advance_mm':float(ext[i,0]),'right_area_advance_mm':float(ext[i,1]),'nodal_advance_mm':float(meannodal[i]),'left_nodal_advance_mm':float(nodal[i,0]),'right_nodal_advance_mm':float(nodal[i,1]),'CTOA_B_deg':float(angles[i,0]),'CTOA_2B_deg':float(angles[i,1])} for i in range(n)]
    events=[states[i] for i in range(1,n) if meanext[i]>meanext[i-1]+1e-8]
    status={}; guards_safe=True; maxdistance=0.
    if m['guards']:
        statuses=columns(headers,'DOMAIN_STOP_STATUS',1)
        for guard in m['guards']:
            sid=guard['sensor_id']; j=int(np.argmin(np.abs(xs-guard['x_mm'])))
            status[str(sid)]=float(d[-1,statuses[sid][0]])
            maxdistance=max(maxdistance,float(np.max(np.hypot(opens[:,j],slip[:,j]))))
            p=next(p for p in pairs if abs(p['x_mm']-guard['x_mm'])<1e-9)
            guards_safe &= bool(np.all(d[:,seam[p['element_id']][0]]>=.5))
    stopped=any(v==1 for v in status.values())
    starter=(folder/(m['name']+'_0000.out')).read_text(errors='replace'); engine=(folder/(m['name']+'_0001.out')).read_text(errors='replace')
    match=re.search(r'Ishell\s+Ismstr\s+Idril\s+NPT\s+ITHK\s+IPLAS\s+IPOS\s*\n\s*([\d\s-]+)\n',starter)
    assert match,'Resolved shell flags missing from listing'
    resolved=list(map(int,match.group(1).split()))
    # Idril=0 requests the runtime default (resolved 2 for QEPH); verify the explicit constitutive fields.
    assert resolved[:2]==[24,4] and resolved[3:6]==[5,1,1],resolved
    metrics={'mass_error_fraction':float(np.max(np.abs(c('MASS')-m['expected_mass_g']))/m['expected_mass_g']),'energy_residual_fraction':float(np.max(np.abs(we-ie-ke))/energy_scale),'independent_actuator_work_error_fraction':float(np.max(np.abs(actuator-we))/energy_scale),'momentum_residual_N_ms':float(np.max(np.abs(ju+jl-c('Y-MOMENTUM')))),'momentum_residual_fraction_of_boundary_impulse':float(np.max(np.abs(ju+jl-c('Y-MOMENTUM')))/max(np.max(np.abs(ju)),np.max(np.abs(jl)),1e-15)),'spring_energy_sum_error_fraction':float(np.max(np.abs(spring_ie-c('SPRING ENERGY')*.001))/max(np.max(np.abs(spring_ie)),1e-15)),'spring_geometry_gap_error_mm':max_gap_error,'elastic_spring_force_error_fraction_of_peak':law_error,'maximum_kinetic_to_internal_significant_window':float(np.max(ke[significant]/ie[significant])),'spring_work_quadrature_error_fraction':float(np.max(np.abs(seam_quadrature-spring_ie))/max(np.max(np.abs(spring_ie)),1e-15)),'raw_upper_impulse_final_N_ms':float(ju[-1]),'max_sampled_tip_plastic_strain':pmax,'last_source_plastic_strain':lastsource,'max_guard_distance_mm':maxdistance,'maximum_area_advance_mm':float(np.max(ext)),'peak_section_force_N':float(np.max(force)),'final_external_work_J':float(we[-1]),'final_actuator_work_J':float(actuator[-1]),'final_spring_energy_J':float(spring_ie[-1]),'final_spring_integrated_work_J':float(seam_quadrature[-1]),'minimum_solver_dt_ms':float(np.min(c('TIME STEP')))}
    gates={'three_completed_jobs':len(executions)==3 and all(x['returncode']==0 for x in executions),'normal_termination':'NORMAL TERMINATION' in engine and 'ERROR TERMINATION' not in engine,'preflight_and_no_unreviewed_engine_warnings':json.loads((folder/'preflight.json').read_text())['pass'] and not re.search(r'(?:WARNING|ERROR) ID',engine),'fixed_penalty_verified':True,'mass':metrics['mass_error_fraction']<=cfg['gates']['maximum_mass_error_fraction'],'global_energy':metrics['energy_residual_fraction']<=cfg['gates']['maximum_global_energy_residual_fraction'],'independent_actuator_work':metrics['independent_actuator_work_error_fraction']<=cfg['gates']['maximum_independent_boundary_work_error_fraction'],'momentum_impulse_balance':metrics['momentum_residual_fraction_of_boundary_impulse']<=cfg['gates']['maximum_momentum_residual_fraction'],'spring_IE_sum':metrics['spring_energy_sum_error_fraction']<=cfg['gates']['maximum_spring_energy_sum_error_fraction'],'spring_gap_mapping':max_gap_error<=cfg['gates']['maximum_spring_geometry_gap_error_mm'],'inertia_significant_window':metrics['maximum_kinetic_to_internal_significant_window']<=cfg['gates']['maximum_kinetic_to_internal_significant_window'],'control_no_failure':m['case']['mode']=='fracture' or int(broken[-1])==0,'refined_domain_retained':bool(guards_safe) and metrics['maximum_area_advance_mm']<=cfg['comparison']['refined_domain_maximum_area_advance_mm']+1e-8,'end_reason_verified':stopped or t[-1]>=m['run_end_ms']-.02}
    gates={k:bool(v) for k,v in gates.items()}
    gates['resolved_explicit_shell_flags']=True
    destination.mkdir(exist_ok=False)
    dump(destination/'history.json',states)
    with (destination/'boundary_intervals.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['start_ms','end_ms','upper_force_N','lower_force_N','increment_actuator_work_J']); w.writerows(zip(t[:-1],t[1:],actuator_force,bottom_force,work_increments))
    result={'case':m['case'],'metrics':metrics,'gates':gates,'all_case_gates_pass':all(gates.values()),'events':events,'final_state':states[-1],'source_constitutive_domain_exceeded_in_sampled_tip_shells':pmax>lastsource,'plastic_sampling':'Selected shells with abs(y_center)<=2h and a0-h<=abs(x_center)<=outer refined break; not a global upper bound.','domain_stop_activated':stopped,'sensor_final_status':status,'broken_springs_final':int(broken[-1]),'runtime_seconds':sum(x['seconds'] for x in executions),'raw_csv_sha256':sha(next(folder.glob('*.csv'))),'maximum_csv_output_dt_ms':float(np.max(np.diff(t))),'reaction_sign_convention':'Positive upper differentiated impulse gives positive actuator work. Signed sum of upper/lower impulses checked against global PY; residual normalized by largest boundary impulse, absolute residual also recorded.','spring_work_note':'Trapezoidal connector-work diagnostic; deactivation and hysteresis jumps are not interpolated as calibrated dissipation.'}
    result['resolved_shell_flags']=dict(zip(['Ishell','Ismstr','Idril','NPT','ITHK','IPLAS','IPOS'],resolved))
    result['additional_energy_diagnostics']={'max_added_mass_g':float(np.max(c('ADDED MASS'))),'max_hourglass_energy_J':float(np.max(np.abs(c('HOURGLASS ENERGY')))*.001),'max_rotation_energy_J':float(np.max(np.abs(c('ROTATION ENERGY')))*.001),'max_contact_energy_J':float(np.max(np.abs(c('CONTACT ENERGY')))*.001)}
    dump(destination/'case_audit.json',result); return result,states


def interpolate_state(states,u):
    xs=[s['displacement_mm'] for s in states]
    # Permit only floating summation roundoff at a recorded endpoint, never a physical extrapolation.
    if not xs[0]-1e-12<=u<=xs[-1]+1e-12: return None
    # Force and work interpolation at prescribed displacement, never interpolate a crack state.
    return {k:float(np.interp(u,xs,[s[k] for s in states])) for k in ['section_force_N','external_work_J']}


def compare(name,a,b,cfg,kind):
    force_scale=max(a[0]['metrics']['peak_section_force_N'],b[0]['metrics']['peak_section_force_N'])
    work_scale=max(a[0]['metrics']['final_external_work_J'],b[0]['metrics']['final_external_work_J'])
    points=[]
    for u in cfg['comparison']['common_displacements_mm']:
        x=interpolate_state(a[1],u); y=interpolate_state(b[1],u)
        points.append({'displacement_mm':u,'assessed':x is not None and y is not None,'a':x,'b':y,'force_difference_fraction_of_peak':None if x is None or y is None else abs(x['section_force_N']-y['section_force_N'])/force_scale,'work_difference_fraction_of_max_final':None if x is None or y is None else abs(x['external_work_J']-y['external_work_J'])/work_scale})
    advances=[]
    for v in cfg['comparison']['common_nodal_advances_mm']:
        def event(r):
            return next((e for e in r['events'] if abs(e['left_nodal_advance_mm']-v)<1e-8 and abs(e['right_nodal_advance_mm']-v)<1e-8),None)
        x=event(a[0]); y=event(b[0]); assessed=x is not None and y is not None
        advances.append({'nodal_advance_mm':v,'assessed':assessed,'a':x,'b':y,'CTOA_B_difference_fraction':None if not assessed else abs(x['CTOA_B_deg']-y['CTOA_B_deg'])/max(abs(x['CTOA_B_deg']),abs(y['CTOA_B_deg']),1e-15),'CTOA_2B_difference_fraction':None if not assessed else abs(x['CTOA_2B_deg']-y['CTOA_2B_deg'])/max(abs(x['CTOA_2B_deg']),abs(y['CTOA_2B_deg']),1e-15)})
    force=max([p['force_difference_fraction_of_peak'] for p in points if p['assessed']],default=None)
    work=max([p['work_difference_fraction_of_max_final'] for p in points if p['assessed']],default=None)
    ctoa=max([max(p['CTOA_B_difference_fraction'],p['CTOA_2B_difference_fraction']) for p in advances if p['assessed']],default=None)
    limits=cfg['gates']; checks={'force_at_common_displacement':force is not None and force<=limits['maximum_'+kind+'_force_difference_fraction'],'work_at_common_displacement':work is not None and work<=limits['maximum_mesh_work_difference_fraction'],'ctoa_at_exact_common_advance':ctoa is not None and ctoa<=limits['maximum_'+kind+'_ctoa_difference_fraction'],'all_requested_common_advances_assessed':all(p['assessed'] for p in advances)}
    onset_u=max(a[0]['events'][0]['displacement_mm'],b[0]['events'][0]['displacement_mm']) if a[0]['events'] and b[0]['events'] else None
    coverage={'displacement_points_assessed':sum(p['assessed'] for p in points),'displacement_points_requested':len(points),'displacement_points_after_first_complete_separation_in_both':sum(p['assessed'] and onset_u is not None and p['displacement_mm']>=onset_u for p in points),'advance_points_assessed':sum(p['assessed'] for p in advances),'advance_points_requested':len(advances)}
    return {'name':name,'common_displacements':points,'common_advances':advances,'coverage':coverage,'maximum_force_difference_fraction':force,'maximum_work_difference_fraction':work,'maximum_ctoa_difference_fraction':ctoa,'checks':checks,'all_comparison_checks_pass':all(checks.values()),'unassessed_is_not_pass':True,'force_work_checks_apply_only_to_assessed_points':True}


def main():
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--controls',action='store_true'); args=p.parse_args()
    destination=Path(args.output).resolve(); destination.relative_to(OUTPUT); destination.mkdir(exist_ok=False)
    cfg=json.loads(CFG.read_text()); results={}; histories={}
    cases=[c for c in cfg['cases'] if c['mode']=='elastic'] if args.controls else cfg['cases']
    for case in cases:
        result,history=audit_case(OUTPUT/case['id'],destination/case['id'],cfg); results[case['id']]=result; histories[case['id']]=history
    sensor=sensor_check(); x=results['ELASTIC_R3']; y=results['ELASTIC_SLOW_R3']; ratio=y['metrics']['raw_upper_impulse_final_N_ms']/x['metrics']['raw_upper_impulse_final_N_ms']; workdiff=abs(y['metrics']['final_external_work_J']-x['metrics']['final_external_work_J'])/x['metrics']['final_external_work_J']
    controls={'sensor_stop':sensor['pass'],'elastic_case_gates':x['all_case_gates_pass'] and y['all_case_gates_pass'],'duration_impulse_scaling':abs(ratio/2-1)<=cfg['gates']['maximum_elastic_duration_impulse_ratio_error_fraction'],'duration_work_invariance':workdiff<=cfg['gates']['maximum_elastic_duration_work_difference_fraction'],'spring_linear_force_mapping':max(x['metrics']['elastic_spring_force_error_fraction_of_peak'],y['metrics']['elastic_spring_force_error_fraction_of_peak'])<.001}
    comparisons={}
    if not args.controls:
        for branch in ['ENG','TRUE']:
            for lo,hi in [('L254','L127'),('L127','L0635')]:
                name=branch+'_'+lo+'_'+hi; ca=branch+'_'+lo+'_R3'; cb=branch+'_'+hi+'_R3'; comparisons[name]=compare(name,(results[ca],histories[ca]),(results[cb],histories[cb]),cfg,'mesh')
        for variant in ['DT45','SLOW']:
            name='ENG_L127_'+variant; ca='ENG_L127_R3'; cb=name+'_R3'; comparisons[name]=compare(name,(results[ca],histories[ca]),(results[cb],histories[cb]),cfg,'time')
    summary={'controls':controls,'control_pass':all(controls.values()),'sensor':sensor,'duration_impulse_ratio':ratio,'duration_work_difference_fraction':workdiff,'cases':results,'case_checks_passed':sum(sum(r['gates'].values()) for r in results.values()),'case_checks_total':sum(len(r['gates']) for r in results.values()),'comparisons':comparisons,'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparisons.values()),'comparison_checks_total':sum(len(v['checks']) for v in comparisons.values()),'all_case_gates_pass':all(r['all_case_gates_pass'] for r in results.values()),'all_comparison_gates_pass':bool(comparisons) and all(v['all_comparison_checks_pass'] for v in comparisons.values()),'runtime_seconds':sum(r['runtime_seconds'] for r in results.values()),'source_convention_verified':False,'physical_propagation_qualified':False,'audit_script_sha256':sha(__file__),'config_sha256':sha(CFG)}
    dump(destination/'summary.json',summary)
    if args.controls:
        target=OUTPUT/'control_checks.json'; assert not target.exists(); dump(target,{'pass':all(controls.values()),'checks':controls,'audit':str((destination/'summary.json').relative_to(ROOT)),'impulse_ratio':ratio,'sensor':sensor})
    print(json.dumps({k:summary[k] for k in ['control_pass','case_checks_passed','case_checks_total','comparison_checks_passed','comparison_checks_total','runtime_seconds']},indent=2))


if __name__=='__main__': main()
