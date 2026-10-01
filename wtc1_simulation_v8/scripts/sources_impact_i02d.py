"""Pin only the primary code needed to interpret the new law; no archive scan."""
import json,urllib.request,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/impact_i02d_lap_joint/references'
OUT.mkdir(parents=True,exist_ok=True)
manifest=OUT/'primary_code.json'
if manifest.exists():raise RuntimeError('Pinned references already exist; preserve them')
commit=json.load(urllib.request.urlopen('https://api.github.com/repos/OpenRadioss/OpenRadioss/commits/main'))['sha']
paths=['engine/source/materials/mat/mat117/sigeps117.F90','starter/source/materials/mat/mat117/hm_read_mat117.F90','engine/source/elements/solid/sconnect/suser43.F']
records=[]
for p in paths:
    url=f'https://raw.githubusercontent.com/OpenRadioss/OpenRadioss/{commit}/{p}';blob=urllib.request.urlopen(url).read();target=OUT/Path(p).name;target.write_bytes(blob)
    records.append({'url':url,'repo_path':p,'file':str(target.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(blob).hexdigest()})
manifest.write_text(json.dumps({'retrieved_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'commit':commit,'files':records,'scope':'Primary implementation reference for independently reproduced equations. This upstream commit is not asserted to be the exact source build of the installed executable; executable hashes and observed deck output are retained separately.'},indent=2)+'\n')
print(json.dumps({'commit':commit,'files':len(records)}))
