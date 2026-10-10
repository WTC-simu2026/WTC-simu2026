# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **10 octobre2026** : **AIRCRAFT-A25 terminée**, prochaine étape **AIRCRAFT-A26**. Le registre compte144entrées. A24+A25 ajoutent52contrôles natifs pour qualifier une attache mécanique avant nouvelle extension de l'impact. Tous les calculs, scripts, entrées, rapports et critères échoués sont conservés.

A24 exécute45contrôles de transmission par pénalité. Les45bilans énergétiques passent; l'énergie cinétique initiale ajoutée est correcte et la traction converge avec une pénalité raide. Le moment cinétique physique du montage échoue enXYZ, même à pas réduit. A25 exécute sept nouveaux contrôles avec des surfaces de reprise sans décalage initial. Les sept bilans passent, mais le moment physique échoue encore. Le témoin révèle aussi une inertie de rotation des coques héritées bien supérieure à leur inertie physique d'épaisseur. Aucun terme RKE n'est retiré, ajouté ou compensé dans les bilans. Aucun connecteur n'est inséré dans l'avion entier.

Les [rapports A24](wtc1_simulation_v8/output/aircraft_a24/rapport_aircraft_a24.md) et [A25](wtc1_simulation_v8/output/aircraft_a25/rapport_aircraft_a25.md) conservent les viscosités natives par défaut, les sensibilités de rigidité et de pas, les échecs et les contrôles de précision des champs. La géométrie source des24racines et144ancres de peau est inventoriée pour la suite; ses capacités et son implantation ne sont pas encore qualifiées. La seule suppression du décalage géométrique ne suffit pas et n'identifie pas la cause complète du déficit A21.

L'objectif vidéo3D des **dix premières secondes physiques** reste incomplet. Le meilleur calcul entier A20 couvre **20millisecondes physiques**. Les prochains travaux doivent vérifier l'inertie et la rigidité des plaques/peaux puis les raccordements réels, avant un nouveau départ entier intact. Matériaux, fracture à grande vitesse, gravité, intérieur porteur et contacts des fragments restent ouverts. Aucun dommage connu n'est une cible. Cette publication confirme l'intégrité des fichiers, sans validation historique de l'impact ou de l'effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **11,321 fichiers scientifiques dans Git**, **19,090 sorties dans 110 archives**.

Restaurer les 109 anciennes archives des releases précédentes, puis les 1 archives [A24+A25](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-10-aircraft-a24-a25). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

A26 : tester une représentation à translations des plaques/peaux, ou un raffinement contrôlé, avec volumes, densités, orientations et propriétés conservés et déclarés. Vérifier masse, tenseur physique, mouvement libre, membrane et flexion. Conserver les bilans RKE natifs et les échecs A21–A25; aucune compensation de masse ou d'inertie. Utiliser ensuite l'inventaire réel des24racines/144ancres et vérifier les raccordements courbes avant un nouvel avion entier intact. Estimer le coût effectif avant tout calcul long. L'objectif10secondes physiques demeure incomplet. Prochaine publication après A26+A27 vérifiées.

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
