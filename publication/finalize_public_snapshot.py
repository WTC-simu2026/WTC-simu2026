"""Add public-only metadata after the immutable scientific copy is verified."""
from __future__ import annotations
import hashlib,json,pathlib,shutil,subprocess

PUB=pathlib.Path(__file__).resolve().parent
ROOT=PUB.parents[1]
REPO=PUB/'repository'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    manifest=json.loads((REPO/'publication/snapshot_manifest.json').read_text(encoding='utf-8'))
    for row in manifest['files']:
        if row['path']=='AGENTS.md':
            row['published_path']='publication/AGENTS_original.md'
            assert sha(REPO/row['published_path'])==row['sha256']
        if row['path'].startswith('wtc1_simulation_v8/input/') and row['license']=='MIT':
            if not row['path'].endswith('/boeing/dimensions_page_28.txt'):
                row['license']='NOASSERTION-reference-metadata'
    manifest['public_only_changes']={'AGENTS.md':'Portable public instructions; original retained with original SHA-256 under publication/AGENTS_original.md.',
          'scientific_state':'Original state, registry, configurations, scripts and result bytes preserved.',
          'reference_metadata':'Raw third-party JSON metadata is attributed as reference metadata, not relicensed as MIT.'}
    shutil.copy2(PUB/'AGENTS_public.md',REPO/'AGENTS.md')
    base=(REPO/'.gitignore').read_text(encoding='utf-8').split('# Restored release results')[0]
    escaped=lambda s:s.replace('[','\\[').replace(']','\\]').replace('*','\\*').replace('?','\\?')
    (REPO/'.gitignore').write_text(base+'\n# Restored release results stay outside Git history.\n'+
        ''.join('/'+escaped(r['path'])+'\n' for r in manifest['files'] if r['destination']=='release'),encoding='utf-8')
    git_bytes=manifest['bytes']['git']; raw_bytes=manifest['bytes']['release']; zipped=sum(a['bytes'] for a in manifest['assets'])
    readme=(REPO/'README.md').read_text(encoding='utf-8')
    readme=readme.replace('**Les sorties lourdes sont dans les [archives de la release]',
      f"Inventaire : **{manifest['counts']['git']:,} fichiers scientifiques dans Git**, "
      f"**{manifest['counts']['release']:,} fichiers en {len(manifest['assets'])} archives**. "
      f"Ensemble : {(git_bytes+raw_bytes)/10**9:.2f} Go originaux ; archives compressées : {zipped/10**9:.2f} Go.\n\n"
      '**Les sorties lourdes sont dans les [archives de la release]')
    (REPO/'README.md').write_text(readme,encoding='utf-8')
    notice=(REPO/'THIRD_PARTY_NOTICES.md').read_text(encoding='utf-8')
    notice+='\nLes métadonnées JSON brutes de références tierces sans licence explicite conservent le statut `NOASSERTION-reference-metadata` dans le manifeste ; la MIT ne leur est pas attribuée.\n'
    (REPO/'THIRD_PARTY_NOTICES.md').write_text(notice,encoding='utf-8')
    notes=f'''# Instantané public du 1er octobre 2026

IMPACT-I02I-A terminée ; prochaine IMPACT-I02I-B. Branche thermique V11R/V11S et contrôle froid V11F préservés.

Cette préversion de recherche contient {manifest['counts']['git']} fichiers scientifiques versionnés et {manifest['counts']['release']} fichiers de résultats bruts, répartis dans {len(manifest['assets'])} archives ZIP. Les archives représentent {raw_bytes/10**9:.2f} Go d'origine, compressés en {zipped/10**9:.2f} Go. Les octets de chaque résultat ont été contrôlés après décompression par SHA-256. Les tentatives rejetées sont conservées.

Lire le README et les rapports avant d'interpréter les figures. Les tests de traction homogène ne qualifient pas la propagation de fracture ni l'événement réel. Une température imposée n'est pas un incendie calculé ; Blender garde sa portée de visualisation.

## Restaurer les résultats

Télécharger tous les fichiers `results-*.zip` de cette release et, si souhaité, `SHA256SUMS.txt`, puis cloner le dépôt et exécuter :

```powershell
python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP
python tools/verify_public_snapshot.py --full
```

Les ZIP conservent leurs chemins relatifs. Le restaurateur vérifie les empreintes et refuse d'écraser des fichiers différents. Le manifeste `publication/snapshot_manifest.json` fournit les tailles et SHA-256 de chaque fichier et de chaque archive. Le contrôle automatique GitHub vérifie les fichiers versionnés, sans télécharger les archives et sans lancer de solveur.

Code propre au projet : MIT. Modèle B762 et conversions : GPL-2.0. Données SHPB S355 : CC-BY-4.0. Exemple officiel TWISBEAM : CC-BY-NC-4.0 ; sa restriction non commerciale est conservée. Les licences complètes accompagnent le dépôt et les archives concernées. Les exécutables et documents/médias tiers hors périmètre de redistribution restent externes, avec références et exclusions documentées.

La relance générale de toutes les anciennes itérations reste partiellement dépendante de chemins Windows et de sources externes ; elle n'est pas présentée comme vérifiée dans un environnement propre.
'''
    (REPO/'publication/RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
    # Publish the actual export generator; it expects the original complete local workspace.
    shutil.copy2(PUB/'build_public_snapshot.py',REPO/'publication/build_public_snapshot.py')
    shutil.copy2(pathlib.Path(__file__),REPO/'publication/finalize_public_snapshot.py')
    dump(REPO/'publication/snapshot_manifest.json',manifest)
    dump(PUB/'snapshot_manifest.json',manifest)
    originals={r.get('published_path',r['path']) for r in manifest['files'] if r['destination']=='git'}
    additions=[]
    for p in sorted(REPO.rglob('*')):
        if not p.is_file() or '.git' in p.parts:continue
        rel=p.relative_to(REPO).as_posix()
        if rel in originals or rel=='publication/publication_files.json':continue
        additions.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
    dump(REPO/'publication/publication_files.json',{'files':additions,'self_reference_excluded':True})
    check=subprocess.run(['python','-X','utf8','tools/verify_public_snapshot.py'],cwd=REPO,capture_output=True,text=True,check=True)
    report=json.loads(check.stdout);dump(PUB/'public_snapshot_verification.json',report)
    print(check.stdout)

if __name__=='__main__':main()
