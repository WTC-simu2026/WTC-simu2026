"""Download only the declared open geometry assets, verify Git blobs, never execute source code."""
import json,hashlib,urllib.request,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
cfg=json.loads((ROOT/'wtc1_simulation_v8/data/impact_i02_geom.json').read_text(encoding='utf-8'))
src=ROOT/cfg['source_directory']; src.mkdir(parents=True,exist_ok=True)
def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WTC1-research-geometry-intake'}),timeout=45) as r: return r.read()
tree=json.loads(fetch(f"https://api.github.com/repos/{cfg['repository']}/git/trees/{cfg['commit']}?recursive=1"))
assert tree['sha']==cfg['commit'] and not tree['truncated']
entries={e['path']:e for e in tree['tree']}; records=[]
for rel in cfg['files']:
    url=f"https://raw.githubusercontent.com/{cfg['repository']}/{cfg['commit']}/{rel}"
    p=src/rel; p.parent.mkdir(parents=True,exist_ok=True)
    data=p.read_bytes() if p.exists() else fetch(url)
    git_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert len(data)==entries[rel]['size'] and git_sha==entries[rel]['sha'],rel
    if not p.exists(): p.write_bytes(data)
    records.append({'path':str(p.relative_to(ROOT)),'url':url,'bytes':len(data),'git_blob_sha1':git_sha,'sha256':hashlib.sha256(data).hexdigest()})
with zipfile.ZipFile(src/'source/b762/762.zip') as z:
    zip_inventory=[{'name':i.filename,'size':i.file_size} for i in z.infolist()]
    assert z.testzip() is None
result={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'repository':cfg['repository'],'commit':cfg['commit'],'files':records,'zip_inventory_only_no_execution':zip_inventory}
(src/'intake_manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'files':records,'zip_contents':zip_inventory},indent=2))
