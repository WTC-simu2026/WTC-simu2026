# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **8 octobre 2026** : **AIRCRAFT-A13 terminée**, prochaine étape **AIRCRAFT-A14**. Le registre contient 132 expériences. Les anciennes mentions V8H/V11H sont historiques.

A12 isole le radôme, vérifie l'inertie initiale et conserve les échecs de fermeture énergétique et de convergence sur quatre maillages. A13 ajoute treize témoins : le contact TYPE25 ferme l'énergie du radôme, mais l'impulsion varie encore de **23,53 %** entre 3456 et 13824 triangles (seuil 10 %). Le demi-pas ne change cette impulsion que de 0,093 %. Le témoin de rebond à 200 m/s passe avec TYPE25 ; TYPE7 perd environ 20,8 % de son énergie initiale. Le contrôle DKT18/TYPE7 conserve un déficit. La correction temporelle v+dt·a/2 reste un diagnostic sans requalification rétroactive.

Lire le [rapport A12](wtc1_simulation_v8/output/aircraft_a12/rapport_aircraft_a12.md), le [rapport A13](wtc1_simulation_v8/output/aircraft_a13/rapport_aircraft_a13.md), les [résultats définitifs A13](wtc1_simulation_v8/output/aircraft_a13/campaign_review.json) et la [passation A14](harness/handoffs/WTC1_AIRCRAFT_A13_HANDOFF.md). L'agrégat intermédiaire A13 est conservé comme tentative incomplète et remplacé scientifiquement par campaign_review.json.

Le temps radôme reste **0,4 milliseconde**, soit **0,0004 seconde**. Premières secondes, rupture, écrasement, pénétration historique et effondrement ne sont pas qualifiés. Le module Boeing parallèle v2 reste séparé ; le contrat d'inertie et la dynamique libre demeurent bloqués. V11F/V11R et les branches différées sont conservées.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **7,858 fichiers scientifiques dans Git**, **10,314 sorties dans 79 archives**.

Restaurer les 69 anciennes archives des releases précédentes, puis les 10 archives [A12+A13](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-08-aircraft-a12-a13). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

**AIRCRAFT-A14** : contrôler la dépendance spatiale de la pénalité de contact sur une plaque plane à 200 m/s, avec aire, masse et gap fixes. Examiner le nombre de nœuds actifs et l'aire tributaire, puis déclarer séparément tout contact pondéré par aire. Aucun Stfac choisi sur les dégâts NIST. Qualifier d'abord les bilans et le demi-pas du témoin analytique, puis réessayer le radôme si ces contrôles passent. Vérifier la convention temporelle native à partir des sorties et de la source exacte. Aucun allongement à l'avion complet avant fermeture locale et convergence spatiale ; premières secondes non calculées.


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
