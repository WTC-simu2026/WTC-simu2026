"""Consolidate cached case audits and compare only declared observables."""
import json,hashlib,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'wtc1_simulation_v8/data/impact_i02c_deformable_joint.json'
cfg=json.loads(CONFIG.read_text());OUT=ROOT/cfg['output_root']
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
names=[c['id'].replace('_R0','_'+cfg['accepted_case_overrides'].get(c['id'],'R2')) for c in cfg['cases']]
rows={n:read(OUT/n/'results.json') for n in names}
coarse=rows['SHEAR_MONO_H05_R1'];base=rows['SHEAR_MONO_H025_R2'];fine=rows['SHEAR_MONO_H0125_R2'];half=rows['SHEAR_HALFDT_H025_R2'];rot=rows['SHEAR_ROT90_H025_R2']
def relative(a,b):return abs(a-b)/max(abs(b),1e-15)
meshes=[coarse,base,fine]
common_time=min(r['time_end_ms'] for r in meshes)
common_ke=[]
for r in meshes:
    h=read(OUT/r['case']/'history.json');common_ke.append(float(np.interp(common_time,h['time_ms'],h['kinetic_J'])))
b=np.load(OUT/base['case']/'computed_frames.npz');r=np.load(OUT/rot['case']/'computed_frames.npz')
rotation=np.array(read(OUT/rot['case']/'generation.json')['rotation'])
rotation_error=float(np.max(abs(b['points_mm']-r['points_mm']@rotation)))
comparisons={
    'mesh_peak_force_spread_fraction':(max(r['peak_force_N'] for r in meshes)-min(r['peak_force_N'] for r in meshes))/fine['peak_force_N'],
    'mesh_joint_energy_spread_fraction':(max(r['joint_energy_J'] for r in meshes)-min(r['joint_energy_J'] for r in meshes))/fine['expected_full_joint_energy_J'],
    'half_dt_joint_energy_fraction':relative(base['joint_energy_J'],half['joint_energy_J']),
    'half_dt_peak_force_fraction':relative(base['peak_force_N'],half['peak_force_N']),
    'rotation_joint_energy_fraction':relative(base['joint_energy_J'],rot['joint_energy_J']),
    'rotation_coordinate_error_mm':rotation_error,
    'normal_fine_compliance_error_fraction':rows['NORMAL_ELASTIC_H025_R2']['elastic_compliance_error_fraction'],
    'post_separation_common_time_ms':common_time,'post_separation_kinetic_J_coarse_base_fine':common_ke,
    'post_separation_kinetic_base_to_fine_fraction_not_qualified':relative(common_ke[1],common_ke[2])}
g=cfg['gates'];checks={n:row['status']=='PASS' and all(row['checks'].values()) for n,row in rows.items()}
checks.update(mesh_peak_force=comparisons['mesh_peak_force_spread_fraction']<g['mesh_peak_force_relative'],
              mesh_joint_energy=comparisons['mesh_joint_energy_spread_fraction']<g['mesh_joint_energy_relative'],
              half_dt_energy=comparisons['half_dt_joint_energy_fraction']<g['half_dt_energy_relative'],
              rotation_energy=comparisons['rotation_joint_energy_fraction']<g['rotation_energy_relative'],
              rotation_coordinates=rotation_error<1e-9)
source=ROOT/'wtc1_simulation_v8/output/impact_i02b_joint_coupon/release_audit.json';prior=read(source)
checks['i02b_release_artifacts_preserved']=all(sha(ROOT/p)==h for p,h in prior['artifact_sha256'].items())
accepted_checks=sum(len(row['checks']) for row in rows.values())
result={'id':'IMPACT-I02C','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'case_results':rows,'comparisons':comparisons,
        'accepted_cases':len(rows),'accepted_case_checks':accepted_checks,'seconds':sum(r['seconds'] for r in rows.values()),
        'physical_boeing_joint_qualified':False,'mixed_mode_qualified':False,'normal_fracture_qualified':False,'large_rotation_objectivity_qualified':False,
        'post_fracture_wave_field_converged':False,'qualification':'Pure-mode constrained-strip numerical verification. Stable peak force and separation energy do not establish convergence of residual vibration or a physical riveted assembly.',
        'rejected_or_superseded':['SHEAR_ELASTIC_H05_R0','SHEAR_ELASTIC_H025_R1','NORMAL_ELASTIC_H05_R1','NORMAL_ELASTIC_H025_R1','DYN_LOW_H025_R2','DYN_G_HIGH_H025_R2','SHEAR_CYCLE_H025_R2']}
dump(OUT/'campaign_audit.json',result)
files=[CONFIG,Path(__file__),ROOT/'wtc1_simulation_v8/scripts/run_impact_i02c.py',ROOT/'wtc1_simulation_v8/scripts/audit_impact_i02c.py',source]
for n in names:
    d=OUT/n;m=read(d/'generation.json')
    files += [d/p for p in ['generation.json','execution.json','results.json','history.json','computed_frames.npz','column_map.json',m['name']+'_0000.rad',m['name']+'_0001.rad',m['name']+'T01.csv','starter.log','engine.log']]
dump(OUT/'source_manifest.json',{'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files},'remote_sources':[s for s in cfg['sources'] if s.startswith('https:')]})
print(json.dumps({'status':result['status'],'cases':len(rows),'case_checks':accepted_checks,'campaign_marks':len(checks),'failed':[k for k,v in checks.items() if not v],'comparisons':comparisons,'seconds':result['seconds']},indent=2))
