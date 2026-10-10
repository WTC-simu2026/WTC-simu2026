# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **10 octobre 2026** : **AIRCRAFT-A23 terminée**, prochaine étape **AIRCRAFT-A24**. Le registre compte142entrées. Les deux itérations A22+A23 testent les attaches mécaniques avant toute nouvelle extension de l'impact. Tous les calculs natifs, entrées, scripts, rapports et critères échoués sont conservés.

A22 exécute21contrôles de six poutres finies aux offsets réels d'une racine. Les21bilans énergétiques passent mais l'inertie physique reste échouée, notamment enY; la contribution native RKE est scalaire. A23 exécute26contrôles d'un solide3D et de sa transmission à une peau métallique et au sandwich A20. Les26bilans passent; le solide isolé conserve le tenseur physique en rotation libre. Les neuf témoins corrigés w1 passent leurs critères individuels, mais la comparaison avec/sans connecteur échoue à l'énergie cinétique globale ajoutée surXYZ. Aucun connecteur n'est inséré dans l'avion entier, aucune compensation de masse ou de RKE n'est utilisée.

Le [rapport A23](wtc1_simulation_v8/output/aircraft_a23/rapport_aircraft_a23.md) distingue l'inertie propre correcte du solide et celle du montage encore biaisée. Il conserve les erreurs du témoin de traction initial, les post-traitements corrigés par lecture en cache, les contrôles d'arrondi des champs natifs et les échecs. Le [rapport A22](wtc1_simulation_v8/output/aircraft_a22/rapport_aircraft_a22.md) prépare dix familles d'écrouissage acier sans les adopter; le début de striction n'est pas un seuil de rupture.

L'objectif vidéo3D des **dix premières secondes physiques** demeure incomplet. Le dernier aperçu entier A20 couvre **20millisecondes physiques**. Aucun ancien état invalide n'est prolongé ni ajusté à un dommage observé. Les géométries, capacités, rupture à grand taux, gravité, intérieur porteur et contacts des fragments restent à qualifier. Publication d'intégrité, sans validation historique de l'impact ou de l'effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **10,448 fichiers scientifiques dans Git**, **17,862 sorties dans 109 archives**.

Restaurer les 100 anciennes archives des releases précédentes, puis les 9 archives [A22+A23](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-10-aircraft-a22-a23). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

## Consulter et vérifier sans relancer les solveurs

```powershell
git clone https://github.com/WTC-simu2026/WTC-simu2026.git
cd WTC-simu2026
python tools/verify_public_snapshot.py
```

Ce contrôle vérifie les fichiers présents dans Git, l'état, le registre et les empreintes de l'instantané. Il annonce séparément les fichiers de release qui restent à télécharger. Il vérifie l'intégrité de la publication, pas la physique du WTC.

Pour restaurer et vérifier toutes les sorties brutes, télécharger les ZIP de la release, puis utiliser :

```powershell
python tools/restore_release_assets.py --archives CHEMIN_VERS_LES_ZIP
python tools/verify_public_snapshot.py --full
```

Le restaurateur vérifie chaque archive puis chaque fichier ; il refuse d'écraser un fichier différent. Ces outils utilisent uniquement la bibliothèque standard Python.

## Reproduire ou poursuivre les calculs

Voir [REPRODUCIBILITY.md](REPRODUCIBILITY.md). La base Python utilise NumPy et Pillow ; certains scripts demandent aussi pandas, matplotlib, pypdf ou pdfplumber. OpenRadioss, CalculiX, Blender et ParaView sont des logiciels séparés, à obtenir auprès de leurs projets respectifs.

**La lecture et la vérification des résultats sont portables ; la relance de toutes les itérations ne l'est pas encore.** Des scripts historiques conservent des chemins Windows et des dépendances locales. Les configurations et journaux originaux sont préservés, et cette limite est explicite. Aucun solveur n'est relancé par le contrôle de publication.

## Prochaine étape

A24 : tester une transmission du solide aux peaux sans condensation de masse, avec bilans natifs, tenseur ajouté indépendant, mouvement libre, rigidité et raffinement du pas. Conserver les témoins cœur et sandwich Spot5 A20 réussis. Contrôler ensuite la géométrie réelle inclinée et les capacités/masses des24racines avant un nouvel avion entier intact. Les dimensions4×1×0,5mm, masse0,00556g et seuil162N ne sont qu'un prototype, pas une fixation AA11 identifiée. Les échecs A21/A22/A23 restent disponibles, sans correction artificielle de RKE. Matériaux et contacts restent ouverts avant10secondes. Publication suivante après A24+A25 vérifiées.

## Discipline de preuve

Chaque rapport distingue observations/transcriptions, résultats de modèles officiels, affirmations des archives, hypothèses du projet, résultats dérivés et informations manquantes. Les données NIST utilisées comme entrées ou références ne deviennent pas des observations indépendantes.

- La localisation en flexion après fracture complète n'est pas validée.
- Une température imposée n'est pas un incendie calculé.
- Des tests numériques réussis ne valident pas à eux seuls l'effondrement réel.
- Une fraction de champs synthétiques n'est pas une probabilité de l'événement historique.
- Blender reste une visualisation tant que son animation n'est pas reliée à des états mécaniques vérifiés.

## Licence et contributions

Les travaux propres au projet sont proposés sous [licence MIT](LICENSE). Les composants tiers et leurs dérivés explicitement identifiés gardent leurs licences : notamment GPL-2.0 pour le modèle graphique B762, CC-BY-4.0 pour le jeu SHPB S355 et CC-BY-NC-4.0 pour le cas officiel TWISBEAM. La licence MIT ne remplace aucune de ces licences. Voir [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Les contributions sont bienvenues : corrections de calcul, contrôles indépendants, sources primaires, portabilité ou visualisation. Indiquer la question testée, les unités, les hypothèses, le coût et le critère qui accepterait ou rejetterait le résultat. Conserver les anciennes itérations et publier les échecs utiles. Voir [CONTRIBUTING.md](CONTRIBUTING.md).
