"""Pin native failure implementation for inspection; no archive scan or solver."""
import json, urllib.request, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'wtc1_simulation_v8/input/aircraft_a06_sources'
COMMIT='0168ab344bd743051e996d90c7c8d80728bb04a8'
PATHS=['engine/source/materials/fail/orthenerg/fail_orthenerg_s.F',
       'starter/source/materials/fail/orthenerg/hm_read_fail_orthenerg.F',
       'hm_cfg_files/config/CFG/radioss2024/FAIL/fail_orthenerg.cfg']
def main():
    assert not D.exists(); D.mkdir(parents=True)
    rows=[]
    for path in PATHS:
        url=f'https://raw.githubusercontent.com/OpenCourant/OpenCourant/{COMMIT}/{path}'
        b=urllib.request.urlopen(url,timeout=60).read(); p=D/Path(path).name;p.write_bytes(b)
        rows.append({'url':url,'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),
                     'role':'primary implementation snapshot; not demonstrated identical to installed binary',
                     'redistribution':'exclude third-party code from own-artifact publication'})
    (D/'acquisition.json').write_text(json.dumps({'commit':COMMIT,'sources':rows,'no_software_installation':True},indent=2)+'\n',encoding='utf-8')
    print({'acquired':len(rows)})
if __name__=='__main__':main()
