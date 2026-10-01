"""Verify saved deliverables and invariants before/after state registration."""
import argparse,hashlib,json,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];SIM=ROOT/'wtc1_simulation_v8/output/impact_i02c_deformable_joint';VIEW=ROOT/'wtc1_3d_v4/output/impact_i02c';MEDIA=ROOT/'wtc1_3d_v4/renders/impact_i02c'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def match(mapping):return bool(mapping) and all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in mapping.items())
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['pre_state','post_state'],required=True);args=p.parse_args()
campaign=read(SIM/'campaign_audit.json');rows=campaign['case_results'];checks={};records={}
checks['campaign_pass']=campaign['status']=='PASS' and len(rows)==15 and all(campaign['checks'].values())
checks['293_case_checks_pass']=sum(len(r['checks']) for r in rows.values())==293 and all(all(r['checks'].values()) for r in rows.values())
checks['qualification_limits_retained']=not any(campaign[k] for k in ['physical_boeing_joint_qualified','mixed_mode_qualified','normal_fracture_qualified','large_rotation_objectivity_qualified','post_fracture_wave_field_converged'])
checks['unconverged_vibration_disclosed']=campaign['comparisons']['post_separation_kinetic_base_to_fine_fraction_not_qualified']>.1
checks['accepted_domains_positive']=all(r['min_signed_slip_mm']>=-1e-5 for r in rows.values())
checks['bounded_low_and_high_G']=rows['DYN_LOW_H025_R3']['time_end_ms']<.0332 and rows['DYN_G_HIGH_H025_R3']['time_end_ms']<.22055
manifest=read(SIM/'source_manifest.json');checks['source_manifest_current']=match(manifest['files']);records['manifest_hashes']=len(manifest['files'])
checks['executables_and_exit_codes']=all(e['returncode']==0 and sha(Path(e['command'][0]))==e['executable_sha256'] for name in rows for e in read(SIM/name/'execution.json'))
for label,path in [('I02B','wtc1_simulation_v8/output/impact_i02b_joint_coupon/release_audit.json'),('I02A','wtc1_simulation_v8/output/impact_i02a_structured_wing/release_audit.json'),('I01','wtc1_simulation_v8/output/impact_i01_first_contact/release_audit.json'),('B762_GEOM','wtc1_3d_v4/output/impact_i02_geom/final/release_audit.json')]:
    previous=read(ROOT/path);checks[label+'_preserved']=previous['delivery_status']=='PASS' and match(previous['artifact_sha256'])
oldcfg=read(ROOT/'wtc1_simulation_v8/data/impact_i02b_joint_coupon.json')
checks['nist_source_preserved']=sha(ROOT/oldcfg['source_envelope']['source_path'])==oldcfg['source_envelope']['source_sha256']
for name in ('v11f_panel_coupling','v11r_integrated_panel'):
    old=read(ROOT/'wtc1_simulation_v8/output'/name/'offline_manifest.json');preserved=[]
    for key,value in old.items():
        if 'sha256' not in key or not isinstance(value,dict):continue
        for path,digest in value.items():
            target=ROOT/'wtc1_simulation_v8/output'/name/path if key=='output_sha256' else ROOT/path
            if name in str(target) or ('v11f_' in str(target) if name.startswith('v11f') else 'v11r_' in str(target)):
                preserved.append(target.is_file() and sha(target)==digest)
    checks[name+'_preserved']=bool(preserved) and all(preserved);records[name+'_hashes']=len(preserved)
cross=read(VIEW/'animation_cross_audit.json');transfer=read(VIEW/'paraview_audit.json');media=read(MEDIA/'presentation_audit.json')
checks['animation_cross_audit_pass']=cross['status']=='PASS' and len(cross['states'])==31 and all(all(s['checks'].values()) for s in cross['states'])
checks['native_and_converted_animation_current']=all(sha(ROOT/s['source'])==s['source_sha256'] and sha(VIEW/'vtk_raw'/f"state_{s['state']:03d}.vtk")==s['vtk_sha256'] for s in cross['states'])
checks['paraview_roundtrip_pass']=transfer['status']=='PASS' and len(transfer['states'])==31 and all(all(s['checks'].values()) for s in transfer['states'])
checks['vtu_current']=all(sha(VIEW/f"state_{s['state']:03d}.vtu")==s['sha256'] for s in transfer['states'])
checks['paraview_cross_source_current']=sha(VIEW/'animation_cross_audit.json')==transfer['source_cross_audit_sha256']
datasets=ET.parse(VIEW/'I02C_coupled_joint_ms.pvd').findall('./Collection/DataSet')
checks['pvd_times_and_files']=len(datasets)==31 and all(d.attrib['file']==f"state_{s['state']:03d}.vtu" and abs(float(d.attrib['timestep'])-s['time_ms'])<1e-8 for d,s in zip(datasets,cross['states']))
checks['movie_pass']=media['status']=='PASS' and all(media['checks'].values())
checks['movie_and_frames_current']=sha(MEDIA/'I02C_liaison_couplee.mp4')==media['video_sha256'] and all(sha(MEDIA/'frames'/f"state_{s['state']:03d}.png")==s['sha256'] for s in media['frames'])
checks['movie_source_current']=sha(ROOT/media['source_npz'])==media['source_sha256']==cross['nodal_frames_npz_sha256']
with Image.open(SIM/'synthese_impact_i02c.png') as im:
    checks['summary_image_size']=im.size==(1520,1040);im.verify()
for n in (0,15,30):
    with Image.open(MEDIA/'frames'/f'state_{n:03d}.png') as im:im.verify()

artifacts=[ROOT/'wtc1_simulation_v8/data/impact_i02c_deformable_joint.json',
    *[ROOT/'wtc1_simulation_v8/scripts'/f'{n}_impact_i02c.py' for n in ['run','audit','summarize','export','present','release']],
    *[SIM/n for n in ['campaign_audit.json','source_manifest.json','rapport_impact_i02c.md','synthese_impact_i02c.png']],
    ROOT/'harness/handoffs/WTC1_IMPACT_I02C_HANDOFF.md',ROOT/'wtc1_3d_v4/scripts/paraview_impact_i02c.py',
    *[VIEW/n for n in ['animation_cross_audit.json','paraview_audit.json','I02C_coupled_joint_ms.pvd','README.md']],
    MEDIA/'I02C_liaison_couplee.mp4',MEDIA/'presentation_audit.json',MEDIA/'encoding.log',
    ROOT/'wtc1_simulation_v8/scripts/export_impact_i02a.py']
checks['report_handoff_and_artifacts_exist']=all(p.is_file() for p in artifacts)
process=subprocess.run([r'C:\Program Files\PowerShell\7\pwsh.exe','-NoProfile','-Command','& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6 -Compress'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
(SIM/f'harness_{args.phase}.log').write_text(process.stdout+process.stderr,encoding='utf-8');harness=json.loads(process.stdout)
checks['harness_pass']=process.returncode==0 and harness['Status']=='PASS'
state=read(ROOT/'harness/state.json');lines=(ROOT/'harness/experiments/registry.jsonl').read_text(encoding='utf-8-sig').splitlines();registry=[json.loads(s) for s in lines if s.strip()]
count=sum(r.get('experiment_id')=='WTC1-IMPACT-I02C' for r in registry)
prefix=hashlib.sha256('\n'.join(lines[:101]).encode()).hexdigest()
if args.phase=='pre_state':
    checks['route_before']=state['current_iteration']=='IMPACT-I02B' and state['next_iteration']=='IMPACT-I02C'
    checks['registry_before']=len(registry)==101 and count==0
else:
    pre=read(SIM/'release_audit_pre_state.json')
    checks['pre_audit_pass']=pre['delivery_status']=='PASS' and match(pre['artifact_sha256'])
    checks['registry_old_lines_unchanged']=prefix==pre['registry_prefix_sha256']
    checks['route_after']=state['current_iteration']=='IMPACT-I02C' and state['next_iteration']=='IMPACT-I02D'
    checks['registry_after']=len(registry)==102 and count==1
    checks['state_qualification']=state['impact_i02c_key_results']['accepted_cases']==15 and not state['impact_i02c_key_results']['physical_boeing_joint_qualified']
records.update(accepted_cases=15,case_checks=293,accepted_seconds=campaign['seconds'])
result={'phase':args.phase,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'delivery_status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'records':records,'harness':harness,
        'registry_prefix_sha256':prefix,'meaning':'Constrained coplanar shell-joint verification only; not a mixed-mode riveted aircraft model or converged post-fracture wave field.',
        'artifact_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in artifacts}}
target=SIM/('release_audit.json' if args.phase=='post_state' else 'release_audit_pre_state.json');target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['delivery_status'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'records':records,'harness':harness},indent=2))
sys.exit(0 if all(checks.values()) else 1)
