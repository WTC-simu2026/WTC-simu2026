"""Freeze every accepted R5 input/output plus the source code used by I02D."""
import hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02d_lap_joint'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02d_lap_joint.json'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
cfg=json.loads(CFG.read_text())
cases=[c['id'].replace('_R0','_R5') for c in cfg['cases']]
paths=[CFG]
paths += [ROOT/'wtc1_simulation_v8/scripts'/f'{name}_impact_i02d.py' for name in ['run','audit','summarize','present','cross','sources','manifest']]
paths += sorted((OUT/'references').glob('*'))
for name in cases:
    paths += sorted(p for p in (OUT/name).rglob('*') if p.is_file())
missing=[str(p) for p in paths if not p.is_file()]
if missing:raise RuntimeError('Missing accepted artifacts: '+repr(missing))
files={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in paths}
result={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'iteration':'IMPACT-I02D','accepted_revision':'R5','accepted_cases':cases,'file_count':len(files),'files':files,'scope':'Every accepted R5 deck, log, raw history, native animation, parsed result, saved frame state and the scripts/configuration that produced or audited them. Rejected R0-R4 are retained but deliberately excluded.'}
(OUT/'source_manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','files':len(files),'cases':len(cases)}))
