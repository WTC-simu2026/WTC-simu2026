"""Copy a bounded, licensed public snapshot; never change scientific originals.

Large results are losslessly zipped for GitHub Releases. Every inventoried file
has a destination or an explicit exclusion; rejected attempts are retained.
"""
from __future__ import annotations
import argparse, collections, concurrent.futures, hashlib, json, pathlib, re
import shutil, subprocess, time, zipfile
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
PUB = pathlib.Path(__file__).resolve().parent
REPO = PUB / 'repository'
ASSETS = PUB / 'release_assets'
ROOTS = ['harness', 'wtc1_simulation_v8', 'wtc1_3d_v4', 'outputs']
TAG = 'snapshot-2026-10-01-impact-i02i-a'
MAX_GIT_FILE = 4 * 1024**2
MAX_ARCHIVE_INPUT = 850 * 1024**2

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''): h.update(b)
    return h.hexdigest()

def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def classify(path, size):
    low = path.lower(); p = pathlib.PurePosixPath(path); ext = p.suffix.lower()
    if low.startswith('outputs/github_publication/'):
        return 'skip', 'publication_workspace', None
    if any(s in p.parts for s in ('__pycache__', '.git', 'node_modules', '.venv', 'venv')):
        return 'exclude', 'generated_dependency_or_cache', None
    if 'openradioss_runtime/' in low:
        return 'exclude', 'external_installed_runtime_obtain_upstream', None
    license_id = 'MIT'
    if '/impact_i02_geom/' in low or path in (
        'wtc1_3d_v4/scripts/build_impact_i02_geom.py',
        'wtc1_3d_v4/scripts/inspect_impact_i02_geom.py'):
        if '/boeing/' not in low: license_id = 'GPL-2.0'
    if '/official_smoke_test/' in low: license_id = 'CC-BY-NC-4.0'
    if low.startswith(('wtc1_simulation_v8/input/v9f_open_sources/',
                       'wtc1_simulation_v8/input/v9h_open_sources/')):
        license_id = 'CC-BY-4.0'
    if low.startswith('wtc1_simulation_v8/input/'):
        allowed = (license_id in ('GPL-2.0', 'CC-BY-4.0')
                   or (ext == '.json' and 'selective_payloads/' not in low)
                   or low.endswith('/boeing/dimensions_page_28.txt'))
        if not allowed: return 'exclude', 'third_party_source_not_relicensed_reference_only', None
    if '/source_snapshots/' in low:
        return 'exclude', 'third_party_reference_snapshot_reference_only', None
    if ext in ('.html', '.torrent'):
        return 'exclude', 'third_party_web_or_archive_reference_only', None
    # These directories contain documentary scans/crops, not model renderings.
    evidence = (low.startswith('outputs/') and p.parts[1] in
                ('analyse_cgi_plane','debris_12_5_audit_v1','video_impact_evidence_20260910','pdf'))
    source_figure = (low.startswith('wtc1_simulation_v8/output/')
                     and len(p.parts)>3 and ('figures' in p.parts[2]
                         or p.parts[2]=='v9b_digitized_curves'))
    if (evidence or source_figure) and ext in ('.png','.jpg','.jpeg','.tif','.gif','.mp4','.pdf'):
        return 'exclude', 'third_party_source_image_or_crop_reference_only', None
    if ext == '.pyc': return 'exclude', 'generated_python_bytecode', None
    raw = (ext in ('.rst','.gz','.npz','.vtk','.vtu','.vtp','.frd','.blend','.blend1','.glb','.zip','.gif','.mp4')
           or (not ext and re.search(r'(?:A\d{3}|T\d{2}|D\d[A-Z0-9])$', p.name))
           or '/renders/' in low or '/frames/' in low
           or (ext == '.csv' and size > 1024**2)
           or (ext == '.png' and not p.name.lower().startswith(('synthese','summary'))))
    if size > MAX_GIT_FILE or raw:
        return 'release', 'large_or_raw_generated_artifact', license_id
    return 'git', 'versioned_code_config_report_or_compact_result', license_id

def inventory():
    names = subprocess.run(['rg','--files',*ROOTS,'-g','!**/__pycache__/**','-g','!**/.git/**'],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    rows=[]
    for name in sorted(names+['AGENTS.md']):
        p=ROOT/name; rel=p.relative_to(ROOT).as_posix(); size=p.stat().st_size
        destination, reason, lic = classify(rel,size)
        if destination=='skip': continue
        rows.append({'path':rel,'bytes':size,'destination':destination,'reason':reason,'license':lic})
    return rows

def fingerprint(row):
    row['sha256']=sha(ROOT/row['path']); return row

def secret_check(rows):
    patterns={
      'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
      'openai_token': re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{30,}\b'),
      'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
      'private_key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
      'credential_url': re.compile(rb'https?://[^\s/:]{2,}:[^\s/@]{4,}@')}
    findings=[]; scanned=0
    for row in rows:
        if row['destination']=='exclude': continue
        p=ROOT/row['path']
        if p.suffix.lower() not in ('.py','.ps1','.cmd','.md','.json','.jsonl','.txt','.yaml','.yml','.toml','.html','.rad','.inp','.log','.out','.xml'): continue
        if row['bytes']>40*1024**2: continue
        data=p.read_bytes(); scanned+=1
        for kind, pattern in patterns.items():
            if pattern.search(data): findings.append({'path':row['path'],'kind':kind})
    result={'files_scanned':scanned,'findings':findings,'pass':not findings,
            'scope':'Known token/key patterns in authored text and published licensed data; no credential values logged.'}
    dump(PUB/'secret_scan.json',result)
    if findings: raise RuntimeError('Potential credentials: inspect listed paths privately before publication')
    return result

def copy_git(row):
    src=ROOT/row['path']; dst=REPO/row['path']; dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():
        if sha(dst)!=row['sha256']: raise RuntimeError('Refuse overwrite: '+str(dst))
    else: shutil.copy2(src,dst)
    if sha(dst)!=row['sha256']: raise RuntimeError('Copy mismatch: '+str(dst))

def make_archive(index, rows):
    name=f'WTC-simu2026-{TAG}-results-{index:02d}.zip'; path=ASSETS/name
    if path.exists(): raise RuntimeError('Preserve existing archive: '+name)
    start=time.perf_counter()
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for row in rows: z.write(ROOT/row['path'],row['path'])
        license_rows={'MIT': REPO/'LICENSE','GPL-2.0': PUB/'LICENSE_GPL2.txt',
                      'CC-BY-4.0':PUB/'LICENSE_CC_BY_4.0.txt','CC-BY-NC-4.0':PUB/'LICENSE_CC_BY_NC_4.0.txt'}
        for lic in sorted(set(r['license'] for r in rows)):
            if license_rows[lic].exists(): z.write(license_rows[lic],'publication/licenses/'+license_rows[lic].name)
        z.writestr('publication/archive_inventory.json',json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
        z.writestr('publication/ARCHIVE_NOTICE.txt',
                   'Lossless scientific outputs. Original relative paths preserved.\n'
                   'Each inventory entry specifies its applicable license.\n'
                   'Tests of limited models do not validate the real WTC1 collapse.\n')
    # Read and hash each restored stream independently; ZIP CRC alone is not enough.
    with zipfile.ZipFile(path) as z:
        for row in rows:
            h=hashlib.sha256()
            with z.open(row['path']) as f:
                for b in iter(lambda:f.read(4*1024**2),b''): h.update(b)
            if h.hexdigest()!=row['sha256']: raise RuntimeError('Archive mismatch: '+row['path'])
    asset={'name':name,'bytes':path.stat().st_size,'sha256':sha(path),'files':len(rows),
           'original_bytes':sum(r['bytes'] for r in rows),'verified_lossless':True,
           'seconds':time.perf_counter()-start,
           'download_url':f'https://github.com/WTC-simu2026/WTC-simu2026/releases/download/{TAG}/{name}'}
    if asset['bytes']>=2*1024**3: raise RuntimeError('GitHub release asset too large')
    print(json.dumps({'archive':name,'bytes':asset['bytes'],'seconds':round(asset['seconds'],2)}),flush=True)
    return asset

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',action='store_true');args=ap.parse_args()
    rows=inventory();counts=collections.Counter();sizes=collections.Counter()
    for r in rows:counts[r['destination']]+=1;sizes[r['destination']]+=r['bytes']
    print(json.dumps({'counts':counts,'bytes':sizes}),flush=True)
    if not args.build:
        dump(PUB/'inventory_plan.json',{'files':rows,'counts':counts,'bytes':sizes});return
    start=time.perf_counter();REPO.mkdir(exist_ok=True);ASSETS.mkdir(exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fingerprint,rows))
    secrets=secret_check(rows)
    for row in rows:
        if row['destination']=='git':copy_git(row)
    # Source-only AGENTS is retained; public instructions are added separately.
    shutil.copy2(REPO/'AGENTS.md',REPO/'publication/AGENTS_original.md')
    for name in ('LICENSE_GPL2.txt','LICENSE_CC_BY_4.0.txt','LICENSE_CC_BY_NC_4.0.txt'):
        dst=REPO/'publication/licenses'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PUB/name,dst)
    batches=[];batch=[];size=0
    for row in rows:
        if row['destination']!='release':continue
        if batch and size+row['bytes']>MAX_ARCHIVE_INPUT:batches.append(batch);batch=[];size=0
        batch.append(row);size+=row['bytes']
    if batch:batches.append(batch)
    for index,batch in enumerate(batches,1):
        for row in batch:row['asset']=f'WTC-simu2026-{TAG}-results-{index:02d}.zip'
    assets=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(make_archive,index,batch) for index,batch in enumerate(batches,1)]
        for f in concurrent.futures.as_completed(futures):assets.append(f.result())
    assets.sort(key=lambda r:r['name'])
    manifest={'schema_version':1,'created_utc':datetime.now(timezone.utc).isoformat(),
              'repository':'WTC-simu2026/WTC-simu2026','release_tag':TAG,
              'current_iteration':'IMPACT-I02I-A','next_iteration':'IMPACT-I02I-B',
              'scientific_originals_modified':False,'counts':dict(counts),'bytes':dict(sizes),
              'secret_scan':secrets,'files':rows,'assets':assets,'seconds':time.perf_counter()-start,
              'not_in_inventory':['.codex/','tmp/','work/official_sources/','external_read_only_archive/','unrelated_root_directories/']}
    dump(REPO/'publication/snapshot_manifest.json',manifest)
    dump(PUB/'snapshot_manifest.json',manifest)
    dump(REPO/'publication/excluded_sources.json',{'files':[r for r in rows if r['destination']=='exclude'],
         'reason':'Third-party sources and installed runtimes retain upstream rights. Numerical project results are not excluded by pass/fail status.'})
    (ASSETS/'SHA256SUMS.txt').write_text(''.join(a['sha256']+'  '+a['name']+'\n' for a in assets),encoding='utf-8')
    print(json.dumps({'status':'PASS','counts':counts,'archive_count':len(assets),
                      'compressed_bytes':sum(a['bytes'] for a in assets),'seconds':time.perf_counter()-start}),flush=True)

if __name__=='__main__':main()
