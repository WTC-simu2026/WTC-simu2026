"""Create a deterministic GPL delivery bundle; downloaded sources remain unmodified."""
import json,hashlib,zipfile,shutil,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; cfg=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json').read_text()); src=ROOT/cfg['source_directory']; out=ROOT/cfg['output_directory']/'final'
shutil.copy2(src/'LICENSE',out/'LICENSE_GPL2.txt'); shutil.copy2(src/'README.md',out/'ORIGINAL_REPOSITORY_README.md')
items={
  'derived/B762_GEOMETRY_ONLY.blend':out/'B762_GEOMETRY_ONLY.blend',
  'derived/B762_GEOMETRY_ONLY.glb':out/'B762_GEOMETRY_ONLY.glb',
  'derived/integration_audit.json':out/'integration_audit.json',
  'derived/roundtrip_audit.json':out/'roundtrip_audit.json',
  'derived/retained_triangle_indices.npz':out/'retained_triangle_indices.npz',
  'derived/THIRD_PARTY_NOTICES.md':out/'THIRD_PARTY_NOTICES.md',
  'derived/rapport_impact_i02_geom.md':ROOT/'wtc1_3d_v4/output/impact_i02_geom/rapport_impact_i02_geom.md',
  'render/B762_apercu_annote.png':ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final/B762_apercu_annote.png',
  'render/perspective.png':ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final/perspective.png',
  'render/plan.png':ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final/plan.png',
  'render/front.png':ROOT/'wtc1_3d_v4/renders/impact_i02_geom/final/front.png',
  'provenance/LICENSE_GPL2.txt':out/'LICENSE_GPL2.txt',
  'provenance/ORIGINAL_REPOSITORY_README.md':out/'ORIGINAL_REPOSITORY_README.md',
  'provenance/intake_manifest.json':src/'intake_manifest.json',
  'provenance/geometry_audit.json':ROOT/'wtc1_3d_v4/output/impact_i02_geom/geometry_audit.json',
  'provenance/boeing_source_manifest.json':ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing/source_manifest.json',
  'source/fr24/README.md':src/'README.md','source/fr24/LICENSE':src/'LICENSE','source/fr24/models/b762.glb':src/'models/b762.glb','source/fr24/source/b762/767-200.blend':src/'source/b762/767-200.blend','source/fr24/source/b762/762.zip':src/'source/b762/762.zip',
  'config/impact_i02_geom.json':ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json',
  'handoff/WTC1_IMPACT_I02_GEOM_HANDOFF.md':ROOT/'harness/handoffs/WTC1_IMPACT_I02_GEOM_HANDOFF.md'
}
for name in ['intake_impact_i02_geom.py','decode_i02_glb1.py','read_i02_boeing_dimensions.py','package_impact_i02_geom.py','release_impact_i02_geom.py']:
    items['scripts/simulation/'+name]=ROOT/'wtc1_simulation_v8/scripts'/name
for name in ['inspect_impact_i02_geom.py','build_impact_i02_geom.py','verify_impact_i02_geom.py','present_impact_i02_geom.py']:
    items['scripts/3d/'+name]=ROOT/'wtc1_3d_v4/scripts'/name
assert all(p.is_file() for p in items.values())
manifest={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'license':'GPL-2.0 for third-party model and derived model/scripts; see notices and full license','source_commit':cfg['commit'],'entries':{k:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in sorted(items.items())},'boeing_pdf_packaged':False,'boeing_reference':'Official external reference retained by URL and local read-only source manifest; not relicensed in this GPL bundle'}
mbytes=json.dumps(manifest,indent=2,ensure_ascii=False).encode('utf-8')
zip_path=out/'B762_GEOMETRY_ONLY_GPL_SOURCE_PACKAGE.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,p in sorted(items.items()):
        zi=zipfile.ZipInfo(name,(2026,9,10,0,0,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=0o100644<<16; z.writestr(zi,p.read_bytes())
    zi=zipfile.ZipInfo('package_manifest.json',(2026,9,10,0,0,0)); zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=0o100644<<16; z.writestr(zi,mbytes)
(out/'package_manifest.json').write_bytes(mbytes)
print(json.dumps({'package':str(zip_path.relative_to(ROOT)),'files':len(items)+1,'bytes':zip_path.stat().st_size,'sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest()},indent=2))
