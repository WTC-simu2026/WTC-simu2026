"""Audit saved artifacts and preserve explicit scientific failures; no solver rerun."""
import argparse,json,subprocess,time,sys
from pathlib import Path
from PIL import Image
from run_impact_i01 import ROOT,CFG,sha,write_json

arg=argparse.ArgumentParser(); arg.add_argument('--phase',choices=['pre_state','post_state'],required=True); args=arg.parse_args()
cfg=json.loads(CFG.read_text(encoding='utf-8')); out=ROOT/cfg['output_root']; media=ROOT/'wtc1_3d_v4/renders/impact_i01/final'
campaign=json.loads((out/'campaign_audit.json').read_text()); export=json.loads((out/'animation_export_audit.json').read_text()); render=json.loads((media/'render_audit.json').read_text())
checks={}; records={}; checked_hashes={}
for name in ['v11f_panel_coupling','v11r_integrated_panel']:
    manifest=json.loads((ROOT/'wtc1_simulation_v8/output'/name/'offline_manifest.json').read_text(encoding='utf-8'))
    targets={}
    # Verify only explicitly listed files of these two iterations, no archive scan.
    for key,value in manifest.items():
        if 'sha256' in key and isinstance(value,dict):
            for p,h in value.items():
                if key=='output_sha256':
                    target=str(Path('wtc1_simulation_v8/output')/name/p)
                    targets[target]=h
                elif name in p or ('v11f_' in p if name.startswith('v11f') else 'v11r_' in p): targets[p]=h
    assert targets, name
    for p,h in targets.items(): checked_hashes[p]=sha(ROOT/p)==h
    checks[name+'_saved_files_preserved']=all(checked_hashes[p] for p in targets)
    records[name+'_preserved_count']=len(targets)
for case in cfg['cases']:
    key=case['id']; d=out/key; gen=json.loads((d/'generation.json').read_text()); c=campaign['cases'][key]['checks']
    checks[key+'_normal']=c['normal_termination']; checks[key+'_deck_ke']=c['initial_KE_matches_actual_rounded_deck_speed']
    checks[key+'_known_config_ke_failure_retained']=not c['initial_KE_matches_geometry_and_speed']
    checks[key+'_numerical_checks']=all(v for k,v in c.items() if k not in ['physical_fracture_validation','initial_KE_matches_geometry_and_speed'])
    checks[key+'_not_physical']=not c['physical_fracture_validation']
    checks[key+'_inherited_inputs_unchanged']=all(sha(ROOT/p)==h for p,h in gen['source_sha256'].items())
    states=export['cases'][key]['states']
    checks[key+'_export_identity']=all(s['displacement_identity_error_mm']<=.05 and s['min_erosion_status']==s['max_erosion_status']==1 for s in states)
checks['initial_mesh_failure_retained']=not campaign['comparisons']['M050_M025']['passes_10pct_gate']
checks['additional_mesh_scalar_pass_recorded']=campaign['comparisons']['M025_M0125']['passes_10pct_gate']
checks['fine_gap_warning_recorded']='477' in campaign['cases']['M0125']['warning_ids']
checks['not_physical_campaign']=not campaign['physical_WTC1_impact_qualified']
checks['render_from_current_export']=render['source_sha256']==sha(out/'M050/computed_frames.npz')
checks['render_24_exact_states']=len(render['states'])==24 and max(s['max_position_error_m'] for s in render['states'])<1e-5 and render['interpolation']=='CONSTANT' and not render['physics_engine']
gif=media/'impact_i01_contact_final.gif'
with Image.open(gif) as im:
    durations=[]
    for i in range(im.n_frames): im.seek(i); im.load(); durations.append(im.info['duration'])
    checks['gif_24_frames_6_seconds']=im.n_frames==24 and sum(durations)==6000
    records['gif']={'frames':im.n_frames,'duration_ms':sum(durations),'size':im.size}
for p in sorted(media.glob('labelled_*.png')):
    with Image.open(p) as im: im.verify()
checks['24_labelled_images']=len(list(media.glob('labelled_*.png')))==24
ffmpeg=r'C:\Program Files\Wondershare\UniConverter 15\ffmpeg.exe'
cmd=[ffmpeg,'-hide_banner','-i',str(media/'impact_i01_contact_final.mp4'),'-c:v','libx264','-preset','ultrafast','-f','null','-']
r=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=60)
(out/('media_decode_'+args.phase+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
checks['mp4_full_decode']=r.returncode==0 and '1400x860' in r.stderr and 'Duration: 00:00:06.00' in r.stderr
blend=ROOT/'wtc1_3d_v4/output/IMPACT_I01_CONTACT_DIAGNOSTIC_FINAL.blend'
blender=r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
expr="import bpy; print('I01_REOPEN_OK', bpy.context.scene.frame_start, bpy.context.scene.frame_end, len(bpy.data.objects['NUMERICAL_ONLY_GENERIC_BOX_AND_COLUMNS'].data.shape_keys.key_blocks))"
br=subprocess.run([blender,'--background',str(blend),'--python-expr',expr],capture_output=True,text=True,errors='replace',timeout=60)
(out/('blend_reopen_'+args.phase+'.log')).write_text(br.stdout+br.stderr,encoding='utf-8')
# Blender 5.2 saves this file with a Zstandard header, not uncompressed BLENDER magic.
checks['blend_reopen_24_states']=br.returncode==0 and 'I01_REOPEN_OK 1 24 24' in br.stdout
checks['report_and_handoff']=(out/'rapport_impact_i01.md').is_file() and (ROOT/'harness/handoffs/WTC1_IMPACT_I01_HANDOFF.md').is_file()
pwsh=r'C:\Program Files\PowerShell\7\pwsh.exe'
r=subprocess.run([pwsh,'-NoProfile','-Command','& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
(out/('harness_'+args.phase+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
harness=json.loads(r.stdout) if r.returncode==0 else {'Status':'FAIL','stderr':r.stderr}
checks['harness_pass']=harness['Status']=='PASS'
if args.phase=='post_state':
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    registry=[json.loads(s) for s in (ROOT/'harness/experiments/registry.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    checks['state_branch']=state['current_iteration']=='IMPACT-I01' and state['next_iteration']=='IMPACT-I02'
    checks['registry_once']=sum(r.get('experiment_id')=='WTC1-IMPACT-I01' for r in registry)==1
paths=[CFG,out/'campaign_audit.json',out/'history_comparisons.json',out/'animation_export_audit.json',out/'rapport_impact_i01.md',ROOT/'harness/handoffs/WTC1_IMPACT_I01_HANDOFF.md',blend,gif,media/'impact_i01_contact_final.mp4',media/'impact_i01_apercu_final.png',media/'render_audit.json',media/'presentation.json',Path(__file__)]
paths += [ROOT/'wtc1_simulation_v8/scripts'/s for s in ['run_impact_i01.py','audit_impact_i01.py','export_impact_i01.py']]
paths += [ROOT/'wtc1_3d_v4/scripts'/s for s in ['build_impact_i01.py','present_impact_i01.py']]
result={'phase':args.phase,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'delivery_status':'PASS' if all(checks.values()) else 'FAIL','meaning':'Saved-artifact consistency and explicit failure disclosure, NOT physical or complete numerical qualification','checks':checks,'records':records,'harness':harness,'preserved_hash_checks':checked_hashes,'artifact_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'python':sys.version}
write_json(out/('release_audit.json' if args.phase=='post_state' else 'release_audit_pre_state.json'),result)
print(json.dumps({'status':result['delivery_status'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'harness':harness,'records':records},indent=2))
sys.exit(0 if all(checks.values()) else 1)
