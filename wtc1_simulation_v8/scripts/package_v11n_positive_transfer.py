"""Repackage unchanged V11N numerical outputs after expanding independent auditing."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--source',required=True); p.add_argument('--output',required=True); args=p.parse_args()
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11n_positive_transfer.json')
    source=(ROOT/args.source).resolve(); out=(ROOT/args.output).resolve()
    scratch=(ROOT/cfg['scratch_directory']).resolve()
    if scratch not in source.parents or scratch not in out.parents or out.exists(): raise ValueError('Use new V11N scratch attempt')
    manifest=read(source/'offline_manifest.json'); before=dict(manifest['input_sha256'])
    audit_path='wtc1_simulation_v8/scripts/audit_v11n_positive_transfer.py'
    snapshot=source/'input_snapshot/audit_v11n_positive_transfer.py'
    for name,h in before.items():
        actual=snapshot if name==audit_path else ROOT/name
        if sha(actual)!=h: raise ValueError('Previous input changed: '+name)
    for name,h in manifest['output_sha256'].items():
        if sha(source/name)!=h: raise ValueError('Previous output changed: '+name)
    if read(source/'results_v11n.json')['status']!='PASS': raise ValueError('Numerical checks failed')
    before[audit_path]=sha(ROOT/audit_path)
    for path in [snapshot,source/'offline_manifest.json',Path(__file__).resolve()]: before[path.relative_to(ROOT).as_posix()]=sha(path)
    out.mkdir(parents=True)
    for name in manifest['output_sha256']:
        if name!='source_manifest.json': shutil.copyfile(source/name,out/name)
    source_doc=read(source/'source_manifest.json'); source_doc['input_sha256']=before
    source_doc['packaging']={'numerical_source':source.relative_to(ROOT).as_posix(),'numerical_payload_unchanged':True,
                             'change':'Independent audit expanded to reconstruct all knots; no solver or coupon rerun.'}
    write(out/'source_manifest.json',source_doc)
    write(out/'offline_manifest.json',{'iteration':'V11N','implementation_status':'PASS','input_sha256':before,
                                      'output_sha256':{f.name:sha(f) for f in sorted(out.iterdir()) if f.is_file()}})
    print(json.dumps({'repackaged':str(out),'numerical_payload_unchanged':True}))
