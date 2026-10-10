# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **10 octobre2026** : **AIRCRAFT-A27 terminée**, prochaine étape **AIRCRAFT-A28**. Le registre compte146entrées. A26+A27 ajoutent40calculs natifs complets sur des plaques isolées, avant un nouveau départ de l'impact entier. Les configurations, sorties, scripts, rapports et critères échoués restent disponibles.

A26 qualifie les neuf témoins de plaque métallique volumique HA8: masse, énergie complète, inertie physique, mouvements libres, moment cinétique, traction et flexion, raffinements spatial et temporel. Les neuf essais triangulaires DKT et leurs cinq échecs sont conservés. Aucun matériau ou raccordement de l'avion entier n'est remplacé.

A27 exécute22contrôles de peau composite avec la même carte LAW25 source. Les22bilans complets passent, ainsi que les mouvements libres et la traction plane corrigée. **La flexion échoue encore à sa référence indépendante**, avec3ou9subdivisions numériques dans l'épaisseur. Aucun nombre de couches intermédiaire n'est choisi pour rejoindre la référence. La réponse3D complète, la rupture réelle et les attaches courbes restent à qualifier. Deux tentatives arrêtées au Starter sont conservées sur la paire; aucun Engine correspondant n'a été lancé.

Les [rapports A26](wtc1_simulation_v8/output/aircraft_a26/rapport_aircraft_a26.md) et [A27](wtc1_simulation_v8/output/aircraft_a27/rapport_aircraft_a27.md) séparent les observations natives, références mécaniques, hypothèses et limites. Les RKE natives sont gardées dans tous les bilans; aucun terme inventé ni compensation de masse ou d'inertie. Les24racines/144ancres géométriques A25 restent disponibles pour la suite.

L'objectif vidéo3D des **dix premières secondes physiques** demeure incomplet. Le meilleur calcul entier A20 couvre **20millisecondes physiques**. La prochaine étape confronte la flexion composite aux contraintes, moments et cinématiques réellement interpolées, puis vérifie cœur et attaches avant un nouveau départ entier intact. Matériaux, rupture, gravité, intérieur porteur et contacts de fragments restent ouverts. Aucun dommage connu n'est une cible. Cette publication vérifie l'intégrité, sans validation historique de l'impact ou de l'effondrement.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **12,006 fichiers scientifiques dans Git**, **19,560 sorties dans 111 archives**.

Restaurer les 110 anciennes archives des releases précédentes, puis les 1 archives [A26+A27](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-10-aircraft-a26-a27). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

A28 : comparer la flexion composite native à la cinématique interpolée et aux tenseurs constitutifs explicitement documentés; réconcilier la réponse TYPE22 avec la matrice3D officielle. Tester une alternative volumique orthotrope si nécessaire, avec même volume, densité et propriétés déclarées, sans calage de rigidité sur une sortie. Conserver tous les échecs A21–A27 et les bilans natifs. Ensuite vérifier cœur/sandwich et24racines/144ancres réelles avant un nouveau départ entier intact; mesurer son coût avant tout calcul long. L'objectif10secondes physiques reste incomplet. Prochaine publication après A28+A29 vérifiées.

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
