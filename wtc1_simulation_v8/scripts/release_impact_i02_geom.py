"""Audit saved geometry delivery only; no solver, source download, or 3D rebuild."""
import argparse,json,hashlib,zipfile,subprocess,time,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]; cfg=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json').read_text()); src=ROOT/cfg['source_directory']; base=ROOT/cfg['output_directory']; out=base/'final'; render=ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final'
arg=argparse.ArgumentParser(); arg.add_argument('--phase',choices=['pre_state','post_state'],required=True); args=arg.parse_args()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={}; records={}
intake=json.loads((src/'intake_manifest.json').read_text()); current={str((ROOT/f['path']).resolve()):sha(ROOT/f['path']) for f in intake['files']}
checks['five_source_sha256_unchanged']=len(current)==5 and all(current[str((ROOT/f['path']).resolve())]==f['sha256'] for f in intake['files'])
checks['pinned_commit']=intake['commit']==cfg['commit']=='dd53267690c6a4ecbb290a3acf0284333a5d68a9'
checks['license_and_readme_copied']=sha(src/'LICENSE')==sha(out/'LICENSE_GPL2.txt') and sha(src/'README.md')==sha(out/'ORIGINAL_REPOSITORY_README.md')
boeing=json.loads((ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing/source_manifest.json').read_text()); pdf=ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing/767_REV_K.pdf'
checks['boeing_pdf_hash_and_target_page']=sha(pdf)==boeing['sha256'] and boeing['page_count']==282 and boeing['dimension_pages'][0]['page_index']==27
checks['boeing_page_rendered']=Image.open(ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing/dimensions_page_28.png').size[0]>=1000
geom=json.loads((base/'geometry_audit.json').read_text()); integ=json.loads((out/'integration_audit.json').read_text()); roundtrip=json.loads((out/'roundtrip_audit.json').read_text())
checks['source_geometry_counts']=geom['vertices']==9719 and geom['triangles']==12647 and geom['node_count']==7
checks['source_geometry_restricted']=geom['no_animations'] and geom['no_skins'] and geom['all_buffer_bounds_checked'] and len(geom['accessor_metadata_mismatches'])==138
checks['zero_mechanical_credit']=all(v==0 for v in geom['mechanical_credit'].values()) and not integ['physics_enabled']
checks['dimensions_disclosed_unscaled']=integ['source_scale_unchanged'] and abs(integ['relative_length_difference']-.038299494491511155)<1e-12 and abs(integ['relative_span_difference']+.026501968123969433)<1e-12
checks['derived_cleanup_traceable']=integ['source_original_preserved'] and integ['removed_zero_area_triangles']==126 and integ['original_triangles']-integ['triangles']==126
checks['roundtrip_blend']=roundtrip['blend']['primitive_count']==155 and roundtrip['blend']['triangles']==12521 and roundtrip['blend']['max_triangle_vertex_error_m']<1e-5 and roundtrip['blend']['no_rigid_bodies_modifiers_or_constraints']
checks['roundtrip_glb']=roundtrip['glb']['primitive_count']==155 and roundtrip['glb']['triangles']==12521 and roundtrip['glb']['max_triangle_vertex_error_m']<1e-5 and roundtrip['glb']['no_rigid_bodies_modifiers_or_constraints']
for name,size in [('perspective.png',(1200,800)),('plan.png',(1200,800)),('front.png',(1200,800)),('B762_apercu_annote.png',(1440,1000))]:
    with Image.open(render/name) as im: im.verify(); checks['image_'+name]=im.size==size
checks['report_handoff_notices']=all(p.is_file() for p in [base/'rapport_impact_i02_geom.md',ROOT/'harness/handoffs/WTC1_IMPACT_I02_GEOM_HANDOFF.md',out/'THIRD_PARTY_NOTICES.md'])
package=json.loads((out/'package_manifest.json').read_text()); zpath=out/'B762_GEOMETRY_ONLY_GPL_SOURCE_PACKAGE.zip'
with zipfile.ZipFile(zpath) as z:
    checks['package_crc']=z.testzip() is None
    checks['package_exact_entries']=set(z.namelist())==set(package['entries'])|{'package_manifest.json'}
    checks['package_embedded_hashes']=all(hashlib.sha256(z.read(k)).hexdigest()==v['sha256'] for k,v in package['entries'].items()) and json.loads(z.read('package_manifest.json'))==package
records['package']={'files':len(z.namelist()),'bytes':zpath.stat().st_size,'sha256':sha(zpath)}
i01=json.loads((ROOT/'wtc1_simulation_v8/output/impact_i01_first_contact/release_audit.json').read_text()); i01_checks=[]
for p,h in i01['artifact_sha256'].items(): i01_checks.append((ROOT/p).is_file() and sha(ROOT/p)==h)
checks['impact_i01_all_recorded_artifacts_preserved']=i01['delivery_status']=='PASS' and all(i01_checks)
for name in ['v11f_panel_coupling','v11r_integrated_panel']:
    m=json.loads((ROOT/'wtc1_simulation_v8/output'/name/'offline_manifest.json').read_text()); vals=[]
    for key,value in m.items():
        if not ('sha256' in key and isinstance(value,dict)): continue
        for p,h in value.items():
            target=ROOT/'wtc1_simulation_v8/output'/name/p if key=='output_sha256' else ROOT/p
            if name in str(target) or ('v11f_' in str(target) if name.startswith('v11f') else 'v11r_' in str(target)): vals.append(target.is_file() and sha(target)==h)
    checks[name+'_preserved']=bool(vals) and all(vals); records[name+'_hash_count']=len(vals)
pwsh=r'C:\Program Files\PowerShell\7\pwsh.exe'; r=subprocess.run([pwsh,'-NoProfile','-Command','& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
(out/('harness_'+args.phase+'.log')).write_text(r.stdout+r.stderr,encoding='utf-8'); harness=json.loads(r.stdout) if r.returncode==0 else {'Status':'FAIL'}; checks['harness_pass']=harness['Status']=='PASS'
if args.phase=='post_state':
    state=json.loads((ROOT/'harness/state.json').read_text()); registry=[json.loads(s) for s in (ROOT/'harness/experiments/registry.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    checks['state_route']=state['current_iteration']=='IMPACT-I02-GEOM' and state['next_iteration']=='IMPACT-I02'
    checks['registry_once']=sum(r.get('experiment_id')=='WTC1-IMPACT-I02-GEOM' for r in registry)==1
result={'phase':args.phase,'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'delivery_status':'PASS' if all(checks.values()) else 'FAIL','meaning':'Source provenance and graphics-geometry delivery consistency only; zero mechanical or real-impact validation','checks':checks,'records':records,'harness':harness,'artifact_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json',base/'rapport_impact_i02_geom.md',out/'B762_GEOMETRY_ONLY.blend',out/'B762_GEOMETRY_ONLY.glb',out/'integration_audit.json',out/'roundtrip_audit.json',out/'THIRD_PARTY_NOTICES.md',out/'package_manifest.json',zpath,render/'B762_apercu_annote.png',ROOT/'harness/handoffs/WTC1_IMPACT_I02_GEOM_HANDOFF.md']}}
(out/('release_audit.json' if args.phase=='post_state' else 'release_audit_pre_state.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'status':result['delivery_status'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'records':records,'harness':harness},indent=2)); sys.exit(0 if all(checks.values()) else 1)
