"""Release gate before and after registering IMPACT-I02D."""
import argparse,hashlib,json,re,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];SIM=ROOT/'wtc1_simulation_v8/output/impact_i02d_lap_joint';VIEW=ROOT/'wtc1_3d_v4/output/impact_i02d';MEDIA=ROOT/'wtc1_3d_v4/renders/impact_i02d'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def match(mapping):return bool(mapping) and all((ROOT/p).is_file() and sha(ROOT/p)==v for p,v in mapping.items())
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['pre_state','post_state'],required=True);args=p.parse_args()
campaign=read(SIM/'campaign_audit.json');rows=campaign['case_results'];manifest=read(SIM/'source_manifest.json');checks={};records={}
checks['campaign_pass']=campaign['status']=='PASS' and len(rows)==13 and all(campaign['checks'].values())
checks['226_case_checks_pass']=sum(len(r['checks']) for r in rows.values())==226 and all(all(r['checks'].values()) for r in rows.values())
checks['qualification_limits_retained']=not any(campaign[k] for k in ['physical_boeing_joint_qualified','metal_tearing_qualified','full_dynamic_angular_momentum_qualified','full_fracture_wavefield_converged','full_aircraft_impact_qualified'])
checks['accepted_cases_are_R5']=set(rows)==set(manifest['accepted_cases']) and all(n.endswith('_R5') for n in rows)
checks['accepted_manifest_current']=manifest['file_count']==len(manifest['files']) and match(manifest['files'])
checks['case_config_snapshots']=all(read(SIM/n/'generation.json')['config_snapshot']==read(ROOT/'wtc1_simulation_v8/data/impact_i02d_lap_joint.json') for n in rows)
checks['generator_hashes']=all(read(SIM/n/'generation.json')['generator_sha256']==sha(ROOT/'wtc1_simulation_v8/scripts/run_impact_i02d.py') for n in rows)
checks['executables_and_exit_codes']=all(e['returncode']==0 and sha(Path(e['command'][0]))==e['executable_sha256'] for n in rows for e in read(SIM/n/'execution.json'))
checks['law_force_energy_contact_gates']=all(rows[n]['checks'].get('coupon_force_law',True) and rows[n]['checks'].get('coupon_work',True) and rows[n]['checks'].get('zero_cohesive_force_after_failure',True) for n in rows)
checks['force_and_moment_reference_gates']=all(rows[n]['checks'].get('quasistatic_force_balance',True) and rows[n]['checks'].get('quasistatic_moment_balance',True) for n in rows)
checks['mass_and_energy_all_cases']=all(r['checks']['mass_preserved'] and r['checks']['no_mass_scaling'] and r['checks']['global_energy'] and r['checks']['boundary_work'] for r in rows.values())
checks['contact_control_pair']=campaign['comparisons']['closed_contact_mean_compression_N']>1 and abs(campaign['comparisons']['closed_no_contact_mean_compression_N'])<1
checks['mesh_and_time_checks']=all(campaign['checks'][k] for k in ['elastic_mesh_force','fracture_mesh_force','fracture_mesh_work','half_dt_force','half_dt_work','initial_rotation_work','initial_rotation_coordinates'])
for label,path in [('I02C','wtc1_simulation_v8/output/impact_i02c_deformable_joint/release_audit.json'),('I02B','wtc1_simulation_v8/output/impact_i02b_joint_coupon/release_audit.json'),('I02A','wtc1_simulation_v8/output/impact_i02a_structured_wing/release_audit.json'),('I01','wtc1_simulation_v8/output/impact_i01_first_contact/release_audit.json')]:
    previous=read(ROOT/path);checks[label+'_preserved']=previous['delivery_status']=='PASS' and match(previous['artifact_sha256'])
for name in ('v11f_panel_coupling','v11r_integrated_panel'):
    old=read(ROOT/'wtc1_simulation_v8/output'/name/'offline_manifest.json');kept=[]
    for key,value in old.items():
        if 'sha256' not in key or not isinstance(value,dict):continue
        for path,digest in value.items():
            target=ROOT/'wtc1_simulation_v8/output'/name/path if key=='output_sha256' else ROOT/path
            if name in str(target) or ('v11f_' in str(target) if name.startswith('v11f') else 'v11r_' in str(target)):
                kept.append(target.is_file() and sha(target)==digest)
    checks[name+'_preserved']=bool(kept) and all(kept);records[name+'_hashes']=len(kept)
primary=read(SIM/'references/primary_code.json');checks['primary_code_pinned']=len(primary['files'])==3 and all(sha(ROOT/x['file'])==x['sha256'] for x in primary['files'])
media=read(MEDIA/'presentation_audit.json');cross=read(VIEW/'animation_cross_audit.json');transfer=read(VIEW/'paraview_audit.json')
checks['movie_pass']=media['status']=='PASS' and all(media['checks'].values()) and sha(MEDIA/'I02D_recouvrement_calcule.mp4')==media['video_sha256']
checks['movie_frames_current']=len(media['frames'])==31 and all(sha(MEDIA/'frames'/f"state_{x['state']:03d}.png")==x['sha256'] for x in media['frames'])
checks['movie_source_current']=sha(ROOT/media['source_npz'])==media['source_sha256']
checks['native_animation_cross_pass']=cross['status']=='PASS' and len(cross['states'])==31 and all(all(x['checks'].values()) for x in cross['states'])
checks['native_sources_current']=all(sha(ROOT/x['source'])==x['source_sha256'] and sha(VIEW/'native_cross'/f"state_{x['state']:03d}.vtk")==x['vtk_sha256'] for x in cross['states'])
checks['paraview_roundtrip_pass']=transfer['status']=='PASS' and len(transfer['states'])==31 and all(all(x['checks'].values()) for x in transfer['states'])
checks['vtu_current']=all(sha(VIEW/f"state_{x['state']:03d}.vtu")==x['sha256'] for x in transfer['states'])
datasets=ET.parse(VIEW/'I02D_lap_ms.pvd').findall('./Collection/DataSet')
checks['pvd_times_and_files']=len(datasets)==31 and all(x.attrib['file']==f"state_{r['state']:03d}.vtu" and abs(float(x.attrib['timestep'])-r['time_ms'])<1e-9 for x,r in zip(datasets,transfer['states']))
for n in (0,15,30):
    with Image.open(MEDIA/'frames'/f'state_{n:03d}.png') as im:im.verify();checks[f'frame_{n:03d}_readable']=im.size==(1280,800)
artifacts=[ROOT/'wtc1_simulation_v8/data/impact_i02d_lap_joint.json',
 *[ROOT/'wtc1_simulation_v8/scripts'/f'{n}_impact_i02d.py' for n in ['run','audit','summarize','present','cross','sources','manifest','release']],
 *[SIM/n for n in ['campaign_audit.json','source_manifest.json','rapport_impact_i02d.md','harness_pre_state.log']],
 ROOT/'harness/handoffs/WTC1_IMPACT_I02D_HANDOFF.md',ROOT/'wtc1_3d_v4/scripts/paraview_impact_i02d.py',
 *[VIEW/n for n in ['animation_cross_audit.json','paraview_audit.json','I02D_lap_ms.pvd','README.md']],
 MEDIA/'I02D_recouvrement_calcule.mp4',MEDIA/'presentation_audit.json',MEDIA/'encoding.log',
 *[SIM/'references'/n for n in ['primary_code.json','sigeps117.F90','hm_read_mat117.F90','suser43.F']]]
checks['report_handoff_and_artifacts_exist']=all(x.is_file() for x in artifacts)
proc=subprocess.run([r'C:\Program Files\PowerShell\7\pwsh.exe','-NoProfile','-Command','& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6 -Compress'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
(SIM/f'harness_{args.phase}.log').write_text(proc.stdout+proc.stderr,encoding='utf-8');harness=json.loads(proc.stdout);checks['harness_pass']=proc.returncode==0 and harness['Status']=='PASS'
state=read(ROOT/'harness/state.json');lines=(ROOT/'harness/experiments/registry.jsonl').read_text(encoding='utf-8-sig').splitlines();registry=[json.loads(s) for s in lines if s.strip()]
count=sum(x.get('experiment_id')=='WTC1-IMPACT-I02D' for x in registry);prefix=hashlib.sha256('\n'.join(lines[:102]).encode()).hexdigest()
if args.phase=='pre_state':
    checks['route_before']=state['current_iteration']=='IMPACT-I02C' and state['next_iteration']=='IMPACT-I02D'
    checks['registry_before']=len(registry)==102 and count==0
else:
    pre=read(SIM/'release_audit_pre_state.json');checks['pre_audit_pass']=pre['delivery_status']=='PASS' and match(pre['artifact_sha256'])
    checks['registry_old_lines_unchanged']=prefix==pre['registry_prefix_sha256']
    checks['route_after']=state['current_iteration']=='IMPACT-I02D' and state['next_iteration']=='IMPACT-I02E'
    checks['registry_after']=len(registry)==103 and count==1
    k=state['impact_i02d_key_results'];checks['state_qualification']=k['accepted_cases']==13 and not k['physical_boeing_joint_qualified'] and not k['full_aircraft_impact_qualified']
records.update(accepted_cases=13,case_checks=226,campaign_marks=len(campaign['checks']),accepted_seconds=campaign['seconds'],manifest_files=manifest['file_count'])
result={'phase':args.phase,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'delivery_status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'records':records,'harness':harness,'registry_prefix_sha256':prefix,'meaning':'Mixed-mode numerical law and eccentric prescribed-grip shell-lap verification only; not a calibrated aircraft joint, metal-tearing or aircraft-facade impact result.','artifact_sha256':{str(x.relative_to(ROOT)).replace('\\','/'):sha(x) for x in artifacts}}
target=SIM/('release_audit.json' if args.phase=='post_state' else 'release_audit_pre_state.json');target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['delivery_status'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'records':records,'harness':harness},indent=2));sys.exit(0 if all(checks.values()) else 1)
