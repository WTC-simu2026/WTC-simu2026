"""Read cached cases and compare predeclared observables; no solver invocation."""
import json,sys,time
from pathlib import Path
import numpy as np
from audit_impact_i02d import CFG,OUT,audit
from run_impact_i02c import dump
rows={c['id'].replace('_R0','_R5'):audit(c['id'].replace('_R0','_R5')) for c in CFG['cases']}
def hist(n):return json.loads((OUT/(n+'_R5')/'history.json').read_text())
def row(n):return rows[n+'_R5']
g=CFG['gates'];cmp={}
for label,a,b in [('elastic_mesh','LAP_ELASTIC_H05','LAP_ELASTIC_H025'),('fracture_mesh','LAP_SEPARATE_H05','LAP_SEPARATE_H025'),('half_dt','LAP_HALFDT_H025','LAP_SEPARATE_H025')]:
    for key in ('peak_right_force_N','final_joint_work_J'):
        cmp[label+'_'+key+'_fraction']=abs(row(a)[key]-row(b)[key])/max(abs(row(b)[key]),1e-12)
    ha,hb=hist(a),hist(b);ta=min(ha['time_ms'][-1],hb['time_ms'][-1]);ea=np.interp(ta,ha['time_ms'],ha['kinetic_J']);eb=np.interp(ta,hb['time_ms'],hb['kinetic_J'])
    cmp[label+'_common_time_ms']=ta;cmp[label+'_kinetic_relative_diagnostic']=abs(ea-eb)/max(abs(eb),1e-12)
rot=np.load(OUT/'LAP_ROT90_H025_R5/computed_frames.npz');base=np.load(OUT/'LAP_SEPARATE_H025_R5/computed_frames.npz');R=np.array([[0,-1,0],[1,0,0],[0,0,1]])
cmp['rot90_coordinate_max_error_mm']=float(np.max(abs(rot['points_mm']@R-base['points_mm'])))
cmp['rot90_joint_work_fraction']=abs(row('LAP_ROT90_H025')['final_joint_work_J']-row('LAP_SEPARATE_H025')['final_joint_work_J'])/row('LAP_SEPARATE_H025')['final_joint_work_J']
hc,hn=hist('PATCH_CLOSE_CONTACT'),hist('PATCH_CLOSE_NO_CONTACT');tc=np.array(hc['time_ms']);tn=np.array(hn['time_ms'])
fc=np.array(hc['coupon_boundary_force_N']);fn=np.array(hn['coupon_boundary_force_N'])
cmp['closed_contact_mean_compression_N']=float(-fc[(tc>2.05)&(tc<2.15),2].mean())
cmp['closed_no_contact_mean_compression_N']=float(-fn[(tn>2.05)&(tn<2.15),2].mean())
checks={'all_case_gates':all(r['status']=='PASS' for r in rows.values()),
    'elastic_mesh_force':cmp['elastic_mesh_peak_right_force_N_fraction']<g['mesh_force_relative'],
    'fracture_mesh_force':cmp['fracture_mesh_peak_right_force_N_fraction']<g['mesh_force_relative'],
    'fracture_mesh_work':cmp['fracture_mesh_final_joint_work_J_fraction']<g['mesh_energy_relative'],
    'half_dt_force':cmp['half_dt_peak_right_force_N_fraction']<g['half_dt_relative'],
    'half_dt_work':cmp['half_dt_final_joint_work_J_fraction']<g['half_dt_relative'],
    'initial_rotation_work':cmp['rot90_joint_work_fraction']<g['initial_rotation_relative'],
    'initial_rotation_coordinates':cmp['rot90_coordinate_max_error_mm']<g['initial_rotation_relative'],
    'contact_resistance_after_failure':cmp['closed_contact_mean_compression_N']>1 and row('PATCH_CLOSE_CONTACT')['all_separated'],
    'no_contact_control_no_resistance':abs(cmp['closed_no_contact_mean_compression_N'])<g['postfailure_force_N'],
    'normal_pure_energy':abs(row('PATCH_NORMAL')['final_joint_work_J']-2.848)/2.848<g['coupon_energy_relative'],
    'shear_pure_energy':abs(row('PATCH_SHEAR')['final_joint_work_J']-1.632)/1.632<g['coupon_energy_relative'],
    'coupled_full_separation':row('LAP_SEPARATE_H025')['all_separated']}
result={'status':'PASS' if all(checks.values()) else 'FAIL','created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks':checks,'comparisons':cmp,'case_results':rows,
    'accepted_cases':len(rows),'case_checks':sum(len(r['checks']) for r in rows.values()),'seconds':sum(r['seconds'] for r in rows.values()),
    'physical_boeing_joint_qualified':False,'metal_tearing_qualified':False,'full_dynamic_angular_momentum_qualified':False,'full_fracture_wavefield_converged':False,'full_aircraft_impact_qualified':False,
    'scope':'Isolated cohesive law and prescribed-grip eccentric elastic shell lap. Static grip moments checked; dynamic orbital-only angular residual is diagnostic, spin not reconstructed. Two meshes plus half step are bounded observable checks, not asymptotic convergence or physical calibration.'}
dump(OUT/'campaign_audit.json',result)
print(json.dumps({'status':result['status'],'cases':len(rows),'case_checks':result['case_checks'],'seconds':result['seconds'],'failed':[k for k,v in checks.items() if not v],'comparisons':cmp},indent=2));sys.exit(0 if result['status']=='PASS' else 1)
