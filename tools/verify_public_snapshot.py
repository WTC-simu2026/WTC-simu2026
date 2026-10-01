"""Verify only the declared public snapshot; never run solvers or change files."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()

def safe_path(name):
    p=(ROOT/name).resolve()
    if not p.is_relative_to(ROOT.resolve()):raise ValueError('Path outside repository: '+name)
    return p

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args()
    manifest=json.loads((ROOT/'publication/snapshot_manifest.json').read_text(encoding='utf-8-sig'))
    failures=[];checked=0;pending=0;excluded=0
    for row in manifest['files']:
        dest=row['destination']
        if dest=='exclude':excluded+=1;continue
        p=safe_path(row.get('published_path',row['path']))
        if dest=='release' and not args.full:pending+=1;continue
        if not p.is_file():failures.append({'path':row['path'],'reason':'missing'});continue
        if p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:
            failures.append({'path':row['path'],'reason':'hash_or_size_mismatch'});continue
        checked+=1
    # Publication additions are pinned separately to avoid a self-hashing manifest.
    additions=ROOT/'publication/publication_files.json'
    added=0
    if additions.is_file():
        for row in json.loads(additions.read_text(encoding='utf-8'))['files']:
            p=safe_path(row['path'])
            if not p.is_file() or digest(p)!=row['sha256']:
                failures.append({'path':row['path'],'reason':'publication_file_mismatch'})
            else:added+=1
    state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8-sig'))
    entries=[json.loads(line) for line in (ROOT/'harness/experiments/registry.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if state['current_iteration']!=manifest['current_iteration'] or state['next_iteration']!=manifest['next_iteration']:
        failures.append({'path':'harness/state.json','reason':'iteration_mismatch'})
    result={'status':'PASS' if not failures else 'FAIL','mode':'full' if args.full else 'git',
            'scientific_files_verified':checked,'publication_files_verified':added,
            'release_files_not_checked_in_git_mode':pending,'external_files_documented':excluded,
            'registry_entries':len(entries),'current_iteration':state['current_iteration'],
            'next_iteration':state['next_iteration'],'failures':failures,
            'meaning':'Publication integrity only; no solver execution or physical validation.'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if not failures else 1

if __name__=='__main__':sys.exit(main())
