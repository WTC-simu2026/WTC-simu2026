"""Independent closed-form/history/energy audits of saved joint coupon outputs.

Does not import the deck generator and never runs a mechanics solver.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
import sys
import time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/impact_i02b_joint_coupon.json'
CFG=json.loads(CONFIG.read_text())
OUT=ROOT/CFG['output_root']


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=lambda v:v.item())+'\n',encoding='utf-8')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda:stream.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def reference(displacements, peak, d0, df):
    """Elastic unloading with irreversible slip, independently from Radioss.

    Monotonic triangular envelope F(x) is a parameterized tensile test, not a
    measured rivet law. p is permanent slip. Failed connectors cannot heal.
    """
    stiffness=peak/d0; slip=0.; failed=False; values=[]; slips=[]
    for x in displacements:
        if x>=df: failed=True
        if failed:
            force=0.
        else:
            env=stiffness*x if x<=d0 else peak*(df-x)/(df-d0)
            trial=max(0.,stiffness*(x-slip))
            force=min(trial,max(0.,env))
            slip=max(slip,x-force/stiffness)
        values.append(force); slips.append(slip)
    return np.array(values),np.array(slips)


def work_closed_form(x,peak,d0,df):
    x=np.clip(x,0,df)
    return np.where(x<=d0,0.5*(peak/d0)*x*x,
                    0.5*peak*d0+peak*((x-d0)-(x-d0)**2/(2*(df-d0))))*.001


def audit_case(directory):
    meta=json.loads((directory/'generation.json').read_text())
    p=meta['parameters']; case=meta['case']; count=p['count']; k=p['K_N_mm']
    with (directory/(meta['name']+'T01.csv')).open() as stream:
        headers=next(csv.reader(stream))
        a=np.loadtxt(stream,delimiter=',')
    # Converter emits generic var IDs for nodal/spring channels; preserve an
    # explicit mapping from the authored TH order and check geometry and K*d.
    assert a.shape[1]==27+11*count, (a.shape[1],count)
    spring=a[:,27:27+5*count].reshape(len(a),count,5)
    nodes=a[:,27+5*count:].reshape(len(a),2*count,3)
    node_ids=[int(re.search(r'BOUNDARY_HISTORY\s+(\d+)',headers[27+5*count+3*i]).group(1)) for i in range(2*count)]
    order=[node_ids.index(node) for node in meta['fixed_nodes']+meta['moving_nodes']]
    nodes=nodes[:,order,:]
    t=a[:,0]; off=spring[:,:,0]; F=spring[:,:,1]; d=spring[:,:,2]
    IE=spring[:,:,3]*.001
    U=np.sum(F*F/(2*k),axis=1)*.001
    W=np.concatenate(([0.],np.cumsum(np.sum(.5*(F[1:]+F[:-1])*(d[1:]-d[:-1]),axis=1)*.001)))
    totalIE=np.sum(IE,axis=1); D=totalIE-U
    ref,slip=reference(d[:,0],p['peak_N'],p['d0_mm'],p['df_mm'])
    source=CFG['source_envelope']
    peak_from_input=source[case['mode']+'_capacity_kN_approx'][1]*1000*(source['target_diameter_in']/source['rivet_diameter_in'])**source['capacity_scale_exponent']*case['weight']
    G=p['energy_J']*count
    totalF=np.sum(F,axis=1)
    energy_scale=max(G,a[0,2]*.001)
    residual=(a[:,1]+a[:,2]+a[:,8]-a[0,1]-a[0,2]-a[0,8]-a[:,9])*.001
    supportImpulse=np.sum(nodes[:,:count,2],axis=1)*.001
    allImpulse=np.sum(nodes[:,:,2],axis=1)*.001
    deltaMomentum=(a[:,3]-a[0,3])*.001
    momentum_scale=max(np.max(abs(allImpulse)),np.max(abs(deltaMomentum)),1e-9)
    normal='NORMAL TERMINATION' in (directory/'engine.log').read_text(errors='replace')
    starter=(directory/(meta['name']+'_0000.out')).read_text(errors='replace')
    warnings=re.findall(r'^WARNING ID\s*:\s*(\d+)',starter,re.M)
    failed=np.any(off==0,axis=1)
    hist={
        'time_ms':t.tolist(),'separation_mm':d[:,0].tolist(),'total_force_N':totalF.tolist(),
        'reference_force_N':(ref*count).tolist(),'permanent_slip_mm':slip.tolist(),
        'active_fraction':np.mean(off,axis=1).tolist(),'internal_work_J':totalIE.tolist(),
        'force_displacement_work_J':W.tolist(),'recoverable_J':U.tolist(),'dissipated_J':D.tolist(),
        'global_kinetic_J':(a[:,2]*.001).tolist(),'external_work_J':(a[:,9]*.001).tolist(),
        'energy_residual_J':residual.tolist(),'moving_velocity_m_s':nodes[:,count,1].tolist(),
        'support_impulse_Ns':supportImpulse.tolist(),'all_boundary_impulse_Ns':allImpulse.tolist(),
        'total_delta_momentum_Ns':deltaMomentum.tolist()
    }
    stats={
        'case':case['id'],'loading':case['loading'],'normal_termination':normal,'warning_ids':warnings,
        'rows':len(a),'time_end_ms':float(t[-1]),'peak_capacity_N':p['peak_N']*count,
        'peak_recorded_N':float(np.max(totalF)),'expected_full_separation_energy_J':G,
        'final_internal_work_J':float(totalIE[-1]),'final_dissipation_J':float(D[-1]),
        'minimum_dissipation_J':float(np.min(D)),
        'minimum_dissipation_increment_J':float(np.min(np.diff(D))),
        'max_force_reference_error_fraction':float(np.max(abs(F[:,0]-ref))/p['peak_N']),
        'max_work_internal_energy_error_fraction':float(np.max(abs(W-totalIE))/G),
        'max_global_energy_residual_fraction':float(np.max(abs(residual))/energy_scale),
        'boundary_impulse_momentum_error_fraction':float(np.max(abs(allImpulse-deltaMomentum))/momentum_scale),
        'initial_kinetic_J':float(a[0,2]*.001),'final_kinetic_J':float(a[-1,2]*.001),
        'final_moving_velocity_m_s':float(nodes[-1,count,1]),
        'maximum_separation_mm':float(np.max(d)),'minimum_separation_mm':float(np.min(d)),
        'any_complete_separation':bool(np.any(failed)),
        'failure_time_ms':float(t[np.argmax(failed)]) if np.any(failed) else None,
        'after_failure_max_force_N':float(np.max(abs(totalF[failed]))) if np.any(failed) else None,
        'global_mass_initial_g':float(a[0,6]),'global_mass_final_g':float(a[-1,6]),
        'max_added_mass_g':float(np.max(abs(a[:,17]))),
        'max_node_spring_separation_error_mm':float(np.max(abs(nodes[:,count:,0]-nodes[:,:count,0]-d))),
        'spring_ie_equals_global_ie_max_J':float(np.max(abs(totalIE-a[:,1]*.001))),
        'seconds':sum(item['seconds'] for item in json.loads((directory/'execution.json').read_text())),
    }
    gates=CFG['predeclared_checks']
    checks={
        'normal_termination':normal,'zero_starter_warnings':not warnings,
        'input_capacity_reproduced':abs(peak_from_input-p['peak_N'])<1e-8,
        'force_history_matches_independent_law':stats['max_force_reference_error_fraction']<gates['force_envelope_relative_error'],
        'force_work_matches_connector_energy':stats['max_work_internal_energy_error_fraction']<gates['work_energy_relative_error'],
        'energy_balance':stats['max_global_energy_residual_fraction']<gates['dynamic_energy_relative_error'],
        'dissipation_nonnegative':stats['minimum_dissipation_J']>=gates['minimum_dissipation_J'],
        'dissipation_irreversible':stats['minimum_dissipation_increment_J']>=gates['minimum_dissipation_J'],
        'boundary_impulse_matches_total_momentum':stats['boundary_impulse_momentum_error_fraction']<gates['dynamic_momentum_relative_error'],
        'node_displacement_matches_spring_extension':stats['max_node_spring_separation_error_mm']<1e-5,
        'total_nodal_mass_retained':abs(a[-1,6]-a[0,6])<1e-6,
        'no_added_mass':stats['max_added_mass_g']<1e-6,
        'nonnegative_opening_scope':stats['minimum_separation_mm']>=-1e-6,
        'sampled_to_end':meta['end_ms']-t[-1]<2.1*CFG['execution']['history_dt_ms'],
    }
    if case['loading']=='monotonic':
        closed=work_closed_form(d[:,0],p['peak_N'],p['d0_mm'],p['df_mm'])*count
        stats['max_closed_form_energy_error_fraction']=float(np.max(abs(closed-totalIE))/G)
        checks['closed_form_monotonic_work']=stats['max_closed_form_energy_error_fraction']<gates['work_energy_relative_error']
        checks['complete_separation_energy']=abs(totalIE[-1]-G)/G<gates['work_energy_relative_error']
    if np.any(failed):
        checks['no_force_after_failure']=stats['after_failure_max_force_N']/(p['peak_N']*count)<gates['post_failure_force_fraction']
        checks['no_healing_after_failure']=bool(np.all(off[np.argmax(failed):]==0))
    if case['loading']=='cycle':
        # Compare pre-failure closed loop endpoints independently of final break.
        i1=np.argmin(abs(t-1)); i2=np.argmin(abs(t-2)); i3=np.argmin(abs(t-3))
        stats['partial_cycle_loop_dissipation_J']=float(totalIE[i3]-totalIE[i1])
        stats['partial_cycle_unloaded_force_N']=float(totalF[i2])
        stats['partial_cycle_slip_mm']=float(slip[i2])
        checks['pre_failure_cycle_dissipation_constant']=abs(stats['partial_cycle_loop_dissipation_J'])/G<gates['work_energy_relative_error']
        checks['zero_force_after_partial_unloading']=abs(totalF[i2])/(p['peak_N']*count)<gates['post_failure_force_fraction']
        checks['complete_cycle_work_equals_separation_energy']=abs(totalIE[-1]-G)/G<gates['work_energy_relative_error']
    if case['loading']=='dynamic':
        E0=stats['initial_kinetic_J']; m=meta['moving_mass_g']*.001
        if E0>G:
            v_expected=np.sqrt(2*(E0-G)/m)
            stats['expected_post_failure_velocity_m_s']=float(v_expected)
            checks['high_energy_causes_complete_separation']=bool(np.any(failed))
            checks['residual_velocity_matches_energy']=abs(stats['final_moving_velocity_m_s']-v_expected)/v_expected<gates['dynamic_energy_relative_error']
        else:
            checks['low_energy_stops_before_complete_separation']=not np.any(failed) and stats['maximum_separation_mm']<p['df_mm']
            checks['low_energy_turns_back']=stats['final_moving_velocity_m_s']<0
    stats['checks']=checks; stats['status']='PASS' if all(checks.values()) else 'FAIL'
    dump(directory/'history_si.json',hist);dump(directory/'results.json',stats)
    dump(directory/'column_map.json',{'raw_headers':headers,'global_count':23,'part_columns':[23,24,25,26],
        'spring_start':27,'spring_order':['OFF','FX_N','LX_mm','IE_N_mm','LENGTH_mm'],
        'node_order':['DX_mm','VX_mm_ms','REACX_N_ms'],
        'reaction_note':'REACX is cumulative boundary impulse in raw T01 conversion; do not integrate it again.'})
    return stats,hist


def main():
    results={};history={}
    for declared in CFG['cases']:
        suffix='_R1' if declared['loading']=='dynamic' else '_R2'
        name=declared['id'].replace('_R0',suffix)
        results[name],history[name]=audit_case(OUT/name)
    checks={name:row['status']=='PASS' for name,row in results.items()}
    nominal=results['NORMAL_BASE_MONO_R2']; half=results['NORMAL_BASE_HALFDT_R2']
    half_error=abs(nominal['final_internal_work_J']-half['final_internal_work_J'])/half['expected_full_separation_energy_J']
    checks['half_dt_energy']=half_error<CFG['predeclared_checks']['half_dt_relative_error']
    rows=[results[name] for name in ['ROW_H050_R2','ROW_H025_R2','ROW_H0125_R2']]
    row_error=(max(row['final_internal_work_J'] for row in rows)-min(row['final_internal_work_J'] for row in rows))/rows[0]['expected_full_separation_energy_J']
    checks['uniform_partition_energy_invariant']=row_error<CFG['predeclared_checks']['uniform_row_partition_relative_error']
    nsrc=ROOT/CFG['source_envelope']['source_path']
    checks['primary_source_unchanged']=sha(nsrc)==CFG['source_envelope']['source_sha256']
    prior=ROOT/'wtc1_simulation_v8/output/impact_i02a_structured_wing/release_audit.json'
    prior_record=json.loads(prior.read_text())
    checks['all_i02a_release_artifacts_unchanged']=all(sha(ROOT/path)==h for path,h in prior_record['artifact_sha256'].items())
    result={
        'id':'IMPACT-I02B','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
        'accepted_cases':len(results),'case_results':results,
        'comparisons':{'half_dt_energy_difference_fraction':half_error,'row_partition_energy_difference_fraction':row_error},
        'rejected_preflights':['NORMAL_BASE_MONO_R0','NORMAL_BASE_CYCLE_R0'],
        'superseded_imposed_motion_R1':'Abrupt velocity changes at piecewise-linear displacement corners cause staggered momentum-history mismatch; smoothed R2 motions are accepted instead. R1 raw results retained.',
        'physical_boeing_joint_qualification':False,'spatial_joint_convergence':False,
        'mixed_mode_postpeak_qualification':False,
        'scope':'Uniaxial law and dynamic energy verification plus uniform row weighting; no plate deformation or aircraft impact.'
    }
    dump(OUT/'campaign_audit.json',result)
    files=[CONFIG,Path(__file__),ROOT/'wtc1_simulation_v8/scripts/run_impact_i02b.py',nsrc,prior]
    for name in results:
        directory=OUT/name; meta=json.loads((directory/'generation.json').read_text())
        files += [directory/'generation.json',directory/'execution.json',directory/'results.json',
                  directory/'history_si.json',directory/(meta['name']+'_0000.rad'),directory/(meta['name']+'_0001.rad'),
                  directory/(meta['name']+'T01.csv')]
    dump(OUT/'source_manifest.json',{'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},'remote_sources':CFG['sources']})
    print(json.dumps({'status':result['status'],'cases':len(results),'comparisons':result['comparisons'],
        'failed':{name:[k for k,v in row['checks'].items() if not v] for name,row in results.items() if row['status']!='PASS'},
        'max_energy_residual_fraction':max(row['max_global_energy_residual_fraction'] for row in results.values()),
        'max_force_reference_error_fraction':max(row['max_force_reference_error_fraction'] for row in results.values())},indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__': sys.exit(main())
