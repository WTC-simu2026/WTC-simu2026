"""Read only the six declared pages of the cached NASA source; no archive scan."""
from pathlib import Path
import hashlib
import json
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'wtc1_simulation_v8/input/impact_i02h_sources/NASA_CR_2006_214281_STAGS.pdf'
dest=ROOT/'wtc1_simulation_v8/output/impact_i02i_material/source_snapshots/NASA_bounded_pages.json'
expected='aef6bef6327dd7038ea4bd78e232403bc2cffda94e8012df15e1fc10369abb80'
actual=hashlib.sha256(source.read_bytes()).hexdigest()
assert actual==expected
if dest.exists(): raise RuntimeError('Previous extraction preserved')
reader=PdfReader(source); pages=[178,179,180,181,182,196]
dest.write_text(json.dumps({'source':str(source),'source_sha256':actual,'pages':{str(n):reader.pages[n-1].extract_text() for n in pages},'interpretation':'bounded pages do not explicitly specify nominal/true; table/deck decimal discrepancy retained; visual table read from preserved tmp/i02h_nasa_table15.png'},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'pages_extracted':pages,'source_unchanged':hashlib.sha256(source.read_bytes()).hexdigest()==expected}))
