"""Verify release archives and restore declared result files without overwriting."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, shutil, sys, zipfile
from verify_public_snapshot import ROOT, digest, safe_path

def restore(archives):
    manifest=json.loads((ROOT/'publication/snapshot_manifest.json').read_text(encoding='utf-8'))
    rows={r['path']:r for r in manifest['files'] if r['destination']=='release'}
    restored=0;existing=0
    # Verify all archive hashes before any extraction.
    for asset in manifest['assets']:
        path=archives/asset['name']
        if not path.is_file() or path.stat().st_size!=asset['bytes'] or digest(path)!=asset['sha256']:
            raise ValueError('Archive missing or hash mismatch: '+asset['name'])
    for asset in manifest['assets']:
        with zipfile.ZipFile(archives/asset['name']) as z:
            expected={name:r for name,r in rows.items() if r['asset']==asset['name']}
            for name,row in expected.items():
                info=z.getinfo(name)
                if info.file_size!=row['bytes']:raise ValueError('Wrong archive entry size: '+name)
                dst=safe_path(name)
                if dst.exists():
                    if not dst.is_file() or digest(dst)!=row['sha256']:
                        raise ValueError('Refuse to overwrite a different file: '+name)
                    existing+=1;continue
                dst.parent.mkdir(parents=True,exist_ok=True)
                temp=dst.with_name(dst.name+'.public-restore-part')
                if temp.exists():raise ValueError('Existing partial file: '+str(temp))
                h=hashlib.sha256()
                try:
                    with z.open(info) as src,temp.open('xb') as out:
                        for block in iter(lambda:src.read(4*1024**2),b''):
                            h.update(block);out.write(block)
                    if h.hexdigest()!=row['sha256']:raise ValueError('Restored SHA mismatch: '+name)
                    temp.rename(dst);restored+=1
                except Exception:
                    if temp.exists():temp.unlink()
                    raise
        print(json.dumps({'archive':asset['name'],'status':'PASS'}),flush=True)
    print(json.dumps({'status':'PASS','files_restored':restored,'identical_existing_files':existing}))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archives',type=pathlib.Path,required=True);args=ap.parse_args()
    restore(args.archives.resolve())

if __name__=='__main__':main()
