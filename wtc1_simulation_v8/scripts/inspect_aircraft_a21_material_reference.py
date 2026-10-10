"""Read and render relevant pages of one acquired primary NASA drop-test model reference."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a21';D=OUT/'sources';PDF=D/'nasa_metal_reference_1.pdf'
assert hashlib.sha256(PDF.read_bytes()).hexdigest()=='6c6e401d3ced0c8697fec98dcbec4b5f7855869c5b16e36187268372db694f2e'
dst=D/'material_pdf_inspection.json';assert not dst.exists();reader=PdfReader(PDF);pages=[]
for i,p in enumerate(reader.pages):
    t=p.extract_text() or ''
    if i<2 or ('14.63' in t and '4.49' in t):pages.append({'pdf_page_1based':i+1,'text':t})
table=[r for r in pages if '14.63' in r['text'] and '4.49' in r['text']];assert len(table)==1
result={'inspected_utc':datetime.now(timezone.utc).isoformat(),'source_url':'https://ntrs.nasa.gov/api/citations/20040086484/downloads/20040086484.pdf','source_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'total_pdf_pages':len(reader.pages),'relevant_pages':pages,'table_page_pdf_1based':table[0]['pdf_page_1based'],'source_is_different_aircraft_drop_test_model':True,'not_adopted_as_AA11_high_rate_fracture_measurement':True}
dst.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');render=D/'material_table';exe=Path(r'C:\Users\jeuxpc\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe');assert exe.is_file();page=table[0]['pdf_page_1based'];subprocess.run([str(exe),'-f',str(page),'-l',str(page),'-r','110','-singlefile','-png',str(PDF),str(render)],check=True,timeout=60);print(json.dumps(result,ensure_ascii=False),flush=True)
