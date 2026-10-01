"""Create a separate pseudonymous publication; preserve scientific originals."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,re,shutil,struct,subprocess,time,zipfile
from datetime import datetime,timezone

PUB=pathlib.Path(__file__).resolve().parent
SOURCE=PUB/'repository'
REPO=PUB/'anonymous_repository'
ASSETS=PUB/'anonymous_release_assets'
OWNER='WTC-simu2026/WTC-simu2026'
TAG='snapshot-2026-10-01-impact-i02i-a'
SEVEN=pathlib.Path('C:/Program Files/7-Zip/7z.exe')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def packed_sha(path,entry):
    """Hash the exact encoded payload, without decompression/recompression."""
    with path.open('rb') as f:
        f.seek(entry.header_offset)
        header=f.read(30)
        if header[:4]!=b'PK\x03\x04':raise ValueError('Invalid local ZIP header')
        n,e=struct.unpack_from('<HH',header,26)
        f.seek(n+e,1)
        h=hashlib.sha256();remaining=entry.compress_size
        while remaining:
            b=f.read(min(4*1024**2,remaining))
            if not b:raise ValueError('Truncated ZIP payload')
            remaining-=len(b);h.update(b)
        return h.hexdigest()

def main():
    started=time.perf_counter()
    ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    if REPO.exists() and not args.resume:raise RuntimeError('Preserve existing anonymous attempt; use explicit resume')
    if not SEVEN.is_file():raise RuntimeError('Installed 7-Zip required for lossless metadata update')
    if not REPO.exists():shutil.copytree(SOURCE,REPO,ignore=shutil.ignore_patterns('.git','__pycache__'))
    ASSETS.mkdir(exist_ok=True)
    manifest=json.loads((REPO/'publication/snapshot_manifest.json').read_text(encoding='utf-8'))
    original_assets={a['name']:a for a in json.loads((SOURCE/'publication/snapshot_manifest.json').read_text(encoding='utf-8'))['assets']}
    origins={r.get('published_path',r['path']) for r in manifest['files'] if r['destination']=='git'}
    changed=[]
    for p in REPO.rglob('*'):
        if not p.is_file() or '.git' in p.parts or p.suffix.lower() not in ('.md','.json','.py','.txt') and p.name!='LICENSE':continue
        try:old=p.read_text(encoding='utf-8')
        except UnicodeError:continue
        new=old.replace('OLD_OWNER/WTC-simu2026',OWNER).replace('OLD_AUTHOR','WTC-simu2026 contributors')
        new=re.sub(r'(?i)OLD_OWNER','WTC-simu2026 contributors',new)
        if new!=old:
            rel=p.relative_to(REPO).as_posix()
            if rel in origins:raise RuntimeError('Unexpected identity in immutable scientific file: '+rel)
            p.write_text(new,encoding='utf-8');changed.append(rel)
    license_text=(REPO/'LICENSE').read_text(encoding='utf-8')
    patchroot=PUB/'anonymous_archive_notice'
    patch=(patchroot/'publication/licenses/LICENSE');patch.parent.mkdir(parents=True,exist_ok=True)
    patch.write_text(license_text,encoding='utf-8')
    verified_entries=0
    for a in manifest['assets']:
        old=PUB/'release_assets'/a['name'];new=ASSETS/a['name']
        if sha(old)!=original_assets[a['name']]['sha256']:raise RuntimeError('Original archive hash mismatch')
        if not new.exists():shutil.copy2(old,new)
        with zipfile.ZipFile(new) as probe:
            needs_update=probe.read('publication/licenses/LICENSE').decode('utf-8').replace('\r\n','\n')!=license_text
        if needs_update:
            proc=subprocess.run([str(SEVEN),'u',str(new),'publication/licenses/LICENSE','-y','-bd'],cwd=patchroot,capture_output=True,text=True)
            if proc.returncode:raise RuntimeError('Archive metadata update failed: '+a['name'])
        with zipfile.ZipFile(old) as src,zipfile.ZipFile(new) as dst:
            before={x.filename:x for x in src.infolist()};after={x.filename:x for x in dst.infolist()}
            if len(dst.infolist())!=len(after) or before.keys()!=after.keys():raise RuntimeError('ZIP entries changed')
            for name,item in before.items():
                if name=='publication/licenses/LICENSE':
                    if dst.read(name).decode('utf-8').replace('\r\n','\n')!=license_text:raise RuntimeError('License replacement failed')
                    continue
                target=after[name]
                if (item.CRC,item.file_size,item.compress_type)!=(target.CRC,target.file_size,target.compress_type):raise RuntimeError('Numerical ZIP metadata changed')
                if packed_sha(old,item)!=packed_sha(new,target):raise RuntimeError('Encoded scientific result changed: '+name)
                verified_entries+=1
                if name.lower().endswith(('.md','.txt','.json','.py','.ps1','.mjs','.yaml','.yml','.csv')) and item.file_size<10*1024**2:
                    text=dst.read(name).lower()
                    if b'old_owner' in text or b'old_author@example.invalid' in text:raise RuntimeError('Old identity retained inside ZIP: '+name)
        a.update(bytes=new.stat().st_size,sha256=sha(new),release_tag=TAG,
                 download_url=f'https://github.com/{OWNER}/releases/download/{TAG}/{new.name}')
        print(json.dumps({'archive':new.name,'status':'PASS','bytes':a['bytes']}),flush=True)
    manifest['repository']=OWNER
    manifest['supplement']['release_tag']=TAG
    manifest['supplement']['original_release_unchanged']=False
    manifest['publication_identity']='WTC-simu2026 contributors'
    dump(REPO/'publication/snapshot_manifest.json',manifest)
    sums=''.join(a['sha256']+'  '+a['name']+'\n' for a in manifest['assets'])
    (REPO/'publication/SHA256SUMS.txt').write_text(sums,encoding='utf-8')
    (ASSETS/'SHA256SUMS.txt').write_text(sums,encoding='utf-8')
    readme=(REPO/'README.md').read_text(encoding='utf-8')
    readme=readme.replace('/releases/tag/legacy-diagnostics-2026-10-01','/releases/tag/'+TAG)
    readme=readme.replace('Télécharger les archives des deux releases dans le même dossier pour la restauration complète.',
                          'Les 23 archives sont regroupées dans la même release pour la restauration complète.')
    (REPO/'README.md').write_text(readme,encoding='utf-8')
    legacy=(REPO/'publication/LEGACY_RELEASE_NOTES.md').read_text(encoding='utf-8')
    legacy=legacy.replace('Le manifeste de la branche `main` contient les empreintes et l\'appartenance aux deux releases.',
                          'Le manifeste de la branche `main` contient les empreintes ; les 23 ZIP sont regroupés dans une même release.')
    legacy=legacy.replace('reste inchangé.','inclut désormais ces diagnostics dans une seule release.')
    (REPO/'publication/LEGACY_RELEASE_NOTES.md').write_text(legacy,encoding='utf-8')
    notes=(REPO/'publication/RELEASE_NOTES.md').read_text(encoding='utf-8')
    notes=re.sub(r'Cette préversion de recherche contient [^\n]+',
        f"Cette préversion de recherche contient {manifest['counts']['git']} fichiers scientifiques versionnés et {manifest['counts']['release']} fichiers de résultats bruts, répartis dans {len(manifest['assets'])} archives ZIP. Les sorties représentent {manifest['bytes']['release']/10**9:.2f} Go d'origine, compressés en {sum(a['bytes'] for a in manifest['assets'])/10**9:.2f} Go. Les octets de chaque résultat ont été contrôlés après décompression par SHA-256 ; la republication conserve exactement leurs flux compressés. Les tentatives rejetées et diagnostics historiques sont conservés.",notes,count=1)
    (REPO/'publication/RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
    with (REPO/'.gitignore').open('a',encoding='utf-8') as f:
        f.write('\n# Restored historical numerical diagnostics\n')
        for r in manifest['files']:
            if r['destination']=='release' and r.get('reason')=='historical_scratch_or_failed_numerical_trial':f.write('/'+r['path']+'\n')
    optional=REPO/'requirements-optional.txt'
    if 'pypdfium2' not in optional.read_text(encoding='utf-8'):
        with optional.open('a',encoding='utf-8') as f:f.write('\npypdfium2 # historical PDF rendering helper\n')
    shutil.copy2(pathlib.Path(__file__),REPO/'publication/prepare_anonymous_snapshot.py')
    # This public preparation script uses a neutral account as input only.
    p=REPO/'publication/prepare_anonymous_snapshot.py'
    text=p.read_text(encoding='utf-8').replace("'OLD_OWNER/WTC-simu2026'","'OLD_OWNER/WTC-simu2026'").replace("'OLD_AUTHOR'","'OLD_AUTHOR'").replace("b'old_owner'","b'old_owner'").replace("b'old_author@example.invalid'","b'old_author@example.invalid'").replace('(?i)OLD_OWNER','(?i)OLD_OWNER')
    p.write_text(text,encoding='utf-8')
    leaks=[]
    for p in REPO.rglob('*'):
        if p.is_file() and p.stat().st_size<10*1024**2:
            data=p.read_bytes().lower()
            if b'old_owner' in data or b'old_author@example.invalid' in data:leaks.append(p.relative_to(REPO).as_posix())
    if leaks:raise RuntimeError('Old identity retained: '+str(leaks))
    additions=[]
    for p in sorted(REPO.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(REPO).as_posix()
        if rel in origins or rel=='publication/publication_files.json':continue
        additions.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
    dump(REPO/'publication/publication_files.json',{'files':additions,'self_reference_excluded':True})
    result={'status':'PASS','repository':OWNER,'scientific_originals_modified':False,
            'modified_publication_files':changed,'encoded_zip_entries_preserved':verified_entries,
            'archives':len(manifest['assets']),'compressed_bytes':sum(a['bytes'] for a in manifest['assets']),
            'identity_scan_findings':leaks,'fresh_git_history_required':True,
            'checked_utc':datetime.now(timezone.utc).isoformat(),'seconds':time.perf_counter()-started}
    dump(PUB/'anonymous_preparation_verification.json',result)
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
