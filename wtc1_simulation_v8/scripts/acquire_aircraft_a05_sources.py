"""Targeted primary material sheets, never overwriting acquired source bytes."""
import urllib.request,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'wtc1_simulation_v8/input/aircraft_a05_sources'
SOURCES={'hexply913.pdf':'https://www.hexcel.com/wp-content/uploads/2026/01/HexPly_913_us_DataSheet.pdf','hrh10_eu.pdf':'https://www.hexcel.com/wp-content/uploads/2025/12/HexWeb_HRH10_DataSheet_eu1.pdf'}
if __name__=='__main__':
    BASE.mkdir(exist_ok=True);manifest=BASE/'acquisition.json'
    if manifest.exists():
        for r in json.loads(manifest.read_text()):assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
        print({'cached_sources_verified':2})
    else:
        rows=[]
        for name,url in SOURCES.items():
            p=BASE/name;assert not p.exists()
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WTC-simu2026 primary-source research'}),timeout=60) as f:b=f.read()
            assert b.startswith(b'%PDF')
            with p.open('xb') as f:f.write(b)
            rows.append({'path':p.relative_to(ROOT).as_posix(),'url':url,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'acquired_utc':datetime.now(timezone.utc).isoformat(),'external_source_exclude_from_publication':True,'read_only_after_acquisition':True})
        manifest.write_text(json.dumps(rows,indent=2)+'\n');print({'primary_pdfs_acquired':len(rows)})
