"""Preserve historical scratch calculations in a separate supplemental release."""
from __future__ import annotations
import collections,concurrent.futures,hashlib,json,pathlib,re,shutil,time
import build_public_snapshot as build

PUB=pathlib.Path(__file__).resolve().parent
ROOT=PUB.parents[1]
REPO=PUB/'repository'
LEGACY_TAG='legacy-diagnostics-2026-10-01'

def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    started=time.perf_counter()
    manifest=json.loads((REPO/'publication/snapshot_manifest.json').read_text(encoding='utf-8'))
    selected=json.loads((PUB/'supplement_selection.json').read_text(encoding='utf-8'))
    rows=[]
    for name in sorted(selected['files']):
        path=ROOT/name;size=path.stat().st_size;ext=path.suffix.lower();lic='MIT'
        if ext=='.rad' and b'CC BY-NC' in path.read_bytes()[:12000]:lic='CC-BY-NC-4.0'
        versioned=(ext in ('.py','.ps1','.mjs','.md')
                   or (ext=='.json' and 'config' in path.name.lower())) and size<4*1024**2
        rows.append({'path':name,'bytes':size,'destination':'git' if versioned else 'release',
                     'reason':'historical_scratch_or_failed_numerical_trial' if name.startswith('tmp/') else 'historical_source_acquisition_helper',
                     'license':lic,'qualification':'historical_scratch_not_promoted_to_final_validation'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(build.fingerprint,rows))
    scan=build.secret_check(rows)
    dump(PUB/'secret_scan_supplement.json',scan)
    for row in rows:
        if row['destination']=='git':build.copy_git(row)
    batches=[];batch=[];size=0
    for row in rows:
        if row['destination']!='release':continue
        if batch and size+row['bytes']>build.MAX_ARCHIVE_INPUT:batches.append(batch);batch=[];size=0
        batch.append(row);size+=row['bytes']
    if batch:batches.append(batch)
    assets=[]
    for idx,batch in enumerate(batches,22):
        for row in batch:row['asset']=f'WTC-simu2026-{build.TAG}-results-{idx:02d}.zip'
        asset=build.make_archive(idx,batch);asset['release_tag']=LEGACY_TAG
        asset['download_url']=f'https://github.com/WTC-simu2026/WTC-simu2026/releases/download/{LEGACY_TAG}/{asset["name"]}'
        assets.append(asset)
    manifest['files'].extend(rows);manifest['assets'].extend(assets)
    for row in rows:
        manifest['counts'][row['destination']]+=1;manifest['bytes'][row['destination']]+=row['bytes']
    manifest['supplement']={'release_tag':LEGACY_TAG,'files':len(rows),'bytes':sum(r['bytes'] for r in rows),
          'qualification':selected['qualification'],'secret_scan':scan,'seconds':time.perf_counter()-started,
          'original_release_unchanged':True}
    manifest['not_in_inventory']=[s for s in manifest['not_in_inventory'] if s!='tmp/']
    manifest['not_in_inventory'].extend(['tmp/documentary_sources_media_extraction_cache_outside_selected_numerical_history/',
                                       'work/except_four_historical_source_acquisition_helpers/'])
    dump(REPO/'publication/snapshot_manifest.json',manifest);dump(PUB/'snapshot_manifest.json',manifest)
    readme=(REPO/'README.md').read_text(encoding='utf-8')
    total=sum(manifest['bytes'][k] for k in ('git','release'))
    compressed=sum(a['bytes'] for a in manifest['assets'])
    inventory=(f"Inventaire : **{manifest['counts']['git']:,} fichiers scientifiques dans Git**, "
               f"**{manifest['counts']['release']:,} fichiers en {len(manifest['assets'])} archives**. "
               f"Ensemble : {total/10**9:.2f} Go originaux ; archives compressées : {compressed/10**9:.2f} Go.")
    readme=re.sub(r'Inventaire : [^\n]+',inventory,readme,count=1)
    marker='Les documents sources'
    link=f'https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/{LEGACY_TAG}'
    insertion=(f'Les [archives complémentaires de diagnostics historiques]({link}) ajoutent les préflights, '
               'essais interrompus et brouillons numériques conservés sous `tmp/`, ainsi que quatre anciens helpers de sources sous `work/`. '
               '**Ces brouillons ne remplacent pas les rapports finaux.** Télécharger les archives des deux releases '
               'dans le même dossier pour la restauration complète.\n\n')
    readme=readme.replace('Les exécutables installés,',insertion+'Les exécutables installés,',1)
    (REPO/'README.md').write_text(readme,encoding='utf-8')
    notes=f'''# Diagnostics numériques historiques et helpers

Complément de l'instantané IMPACT-I02I-A, sans changement de l'état scientifique. Le [premier instantané](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/{build.TAG}) reste inchangé.

{len(rows)} fichiers supplémentaires ({sum(r['bytes'] for r in rows)/10**9:.2f} Go originaux) sont conservés : anciens préflights, essais interrompus, tentatives rejetées et brouillons des étapes V8/V10/V11. Les scripts, configurations et rapports courts sont dans Git ; les autres fichiers sont dans {len(assets)} ZIP supplémentaires. Il peut y avoir des copies identiques de résultats finaux : leurs chemins historiques et leurs octets sont conservés.

Ces sorties temporaires ne sont pas promues en calculs validés. Les rapports finaux, le registre et `harness/state.json` restent les points de référence. Aucun ancien calcul n'a été relancé.

Télécharger aussi les 21 ZIP du premier instantané dans le même dossier, puis exécuter `python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP` et `python tools/verify_public_snapshot.py --full`. Le manifeste de la branche `main` contient les empreintes et l'appartenance aux deux releases.

Le code propre au projet reste MIT ; les licences amont déjà indiquées sont conservées. Les sources documentaires, vidéos, images d'archive et caches d'extraction ne sont pas intégrés à ce complément. Les helpers historiques conservent leurs prérequis locaux et ne doivent pas être exécutés sans adapter leurs chemins et respecter la lecture seule des sources.
'''
    (REPO/'publication/LEGACY_RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
    sums=''.join(a['sha256']+'  '+a['name']+'\n' for a in manifest['assets'])
    (REPO/'publication/SHA256SUMS.txt').write_text(sums,encoding='utf-8')
    (PUB/'release_assets/SHA256SUMS-legacy.txt').write_text(''.join(a['sha256']+'  '+a['name']+'\n' for a in assets),encoding='utf-8')
    shutil.copy2(pathlib.Path(__file__),REPO/'publication/supplement_public_snapshot.py')
    origins={r.get('published_path',r['path']) for r in manifest['files'] if r['destination']=='git'}
    additions=[]
    for p in sorted(REPO.rglob('*')):
        if not p.is_file() or '.git' in p.parts:continue
        rel=p.relative_to(REPO).as_posix()
        if rel in origins or rel=='publication/publication_files.json':continue
        additions.append({'path':rel,'bytes':p.stat().st_size,'sha256':build.sha(p)})
    dump(REPO/'publication/publication_files.json',{'files':additions,'self_reference_excluded':True})
    dump(PUB/'supplement_export_verification.json',{'status':'PASS','files':len(rows),'archives':len(assets),
           'original_bytes':sum(r['bytes'] for r in rows),'compressed_bytes':sum(a['bytes'] for a in assets),
           'seconds':time.perf_counter()-started})
    print(json.dumps({'status':'PASS','files':len(rows),'archives':len(assets),'compressed_bytes':sum(a['bytes'] for a in assets)}))

if __name__=='__main__':main()
