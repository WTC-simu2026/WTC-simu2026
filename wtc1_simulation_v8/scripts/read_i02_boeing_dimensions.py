"""Read-only source acquisition and targeted dimension-page extraction; no structural inference."""
from pathlib import Path
import urllib.request,json,hashlib
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2]; out=ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing'; out.mkdir(parents=True,exist_ok=True)
url='https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf'; p=out/'767_REV_K.pdf'
if not p.exists():
    with urllib.request.urlopen(url,timeout=60) as r: p.write_bytes(r.read())
reader=PdfReader(p); found=[]
# Page located from Section 2 pagination and visually rendered. Drawing dimensions
# are image/vector artwork absent from the text layer, so do not claim extraction.
for i in [27]:
    t=reader.pages[i].extract_text()
    found.append({'page_index':i,'text':t,'dimensions_require_visual_transcription':True})
    (out/f'dimensions_page_{i+1}.txt').write_text(t,encoding='utf-8')
meta={'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'page_count':len(reader.pages),'dimension_pages':found}
(out/'source_manifest.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
print(json.dumps(meta,indent=2))
