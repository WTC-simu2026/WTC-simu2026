"""Targeted primary-source intake for AIRCRAFT-A01; never edit existing sources."""
from pathlib import Path
import hashlib, json, sys, urllib.request, zipfile
from datetime import datetime, timezone
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'wtc1_simulation_v8/input/aircraft_a01'
OUT.mkdir(exist_ok=False)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
url='https://www.boeing.com/content/dam/boeing/v2/airports/dwgs/7672.zip'
p=OUT/'7672.zip'
with urllib.request.urlopen(url,timeout=60) as response: p.write_bytes(response.read())
with zipfile.ZipFile(p) as z:
    assert z.testzip() is None
    names=z.namelist()
    for n in names:
        if n.lower().endswith('.dxf'):
            # Extract exactly a basename, without trusting ZIP paths.
            q=OUT/Path(n).name
            assert not q.exists()
            q.write_bytes(z.read(n))
pdf=ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing/767_REV_K.pdf'
r=PdfReader(pdf)
for idx in [20,22]:
    (OUT/f'page_{idx+1}_text.txt').write_text(r.pages[idx].extract_text(),encoding='utf-8')
dump(OUT/'source_manifest.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
    'sources':[{'url':url,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'zip_entries':names,
        'copyright':'Boeing; source document excluded from public redistribution',
        'role':'Airport-planning three views; NOT internal production geometry'},
        {'url':'https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf',
         'path':pdf.relative_to(ROOT).as_posix(),'sha256':sha(pdf),'pages_1_based':[21,23,28],
         'role':'OEW definition, 767-200ER nominal configurations, external dimensions'}],
    'extracted_files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in OUT.glob('*.dxf')],
    'full_document_rescan':False,'source_pdf_modified':False})
print(json.dumps({'files':names,'dxf_files':[q.name for q in OUT.glob('*.dxf')],'source_pdf_sha256':sha(pdf)},indent=2))
