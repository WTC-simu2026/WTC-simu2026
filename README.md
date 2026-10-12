# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **12 octobre 2026** : **AIRCRAFT-A45 terminée**, prochaine étape **AIRCRAFT-A46**. Le registre compte **164 entrées**. Le second moteur MUMPS est construit et ses contrôles natifs passent. Le modèle entier démarre en explicite ; son contrôle implicite échoue encore. Les anciens résultats et échecs sont conservés.

A44 construit le moteur antérieur figé **3d75ff13d1946f6d28a43920eac4fa2aae41b27a** en **5min11s**, six threads CPU, dans l’heure autorisée, sans installation ni patch de physique. Sources et dépendances : **13869blobs vérifiés**. Les quatre premières tentatives A44 sont refusées par WSL avant Engine ; ces refus restent conservés. La différence de dépendance67/71 déclarée reste non qualifiée physiquement.

Après rétablissement de WSL, A45 exécute **huit processus natifs nouveaux**, dont sept terminent normalement. Les **quatre contrôles LAW117** passent les critères de mouvement, force, réaction, travail, énergie, recharge et rupture, avec demi-pas et normalisation par aire. Les **deux collisions élastiques TYPE7 calculées avec MUMPS** passent masse, énergie, quantité de mouvement et convergence temporelle. Les **600champs** passent la vérification de format float32/six chiffres préexistante ; les contrôles littéraux échoués restent visibles. Les histoires physiques nommées des collisions concordent avec les références A41 à la précision sauvegardée ; une ancienne colonne NO NAME non identifiée reste explicitement non comparée.

Le **modèle entier explicite inchangé démarre et termine trois cycles** : l’ancienne incompatibilité de lecture LAW117 A42 est résolue. Ce micro-démarrage ne prolonge pas les20ms de l’impact entier. Le **CHECK entier avorte pendant l’assemblage de raideur** (ASSEMC_KIJ/ASSEM_C4/CBAKE3) et signale séparément **cinq contacts TYPE25 ignorés**. Aucun lien causal unique n’est affirmé, aucune substitution silencieuse de contact ou modification de reprise n’est faite. L’implicite entier reste non qualifié.

Les [rapports A44](wtc1_simulation_v8/output/aircraft_a44/rapport_aircraft_a44.md) et [A45](wtc1_simulation_v8/output/aircraft_a45/rapport_aircraft_a45.md) séparent faits, sources, archives, hypothèses, résultats et lacunes. Les binaires, bibliothèques et sources tierces brutes sont exclus. Aucun ancien solveur relancé pour publication. A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués. Les paramètres physiques de rupture, modes mixtes, domaines locaux, structure intérieure et gravité restent à traiter.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Aucun temps de témoin ou de démarrage n’est crédité à l’extension entière. Aucun dégât connu comme cible. L’intégrité de publication ne valide pas la physique ou l’événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **15,823 fichiers scientifiques dans Git**, **28,279 sorties dans 124 archives**.

Restaurer les 123 anciennes archives des releases précédentes, puis les 1 archives [A44+A45](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-12-aircraft-a44-a45). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A46 : le moteur antérieur871dc6c9f154173eb4148b95cdfeed3e485735d64eb48957722b3588e319730a est désormais qualifié pour les quatre témoins uniformes LAW117 et le contact direct TYPE7 aux deux pas A41 les plus fins. Ne pas reconstruire ou refaire ces témoins. Le démarrage entier explicite inchangé réussit ; l’incompatibilité de lecture LAW117 A42 est résolue. Le CHECK entier avorte dans ASSEMC_KIJ via ASSEM_C4/CBAKE3/IMP_GLOB_K0/IMP_CHKM, et signale séparément cinq TYPE25 ignorés. Inspecter les routines et les familles d’éléments dans les sources/entrées en cache pour isoler le contrat de raideur qui échoue ; ne pas attribuer automatiquement cet avortement aux contacts. Déclarer un témoin représentatif puis une variante entière portant sur une seule famille, avec bilans et comparaison explicite séparés, avant toute accélération. Aucune substitution silencieuse de TYPE25, matériau, masse, inertie, RBE ou reprise. Conserver toutes les tentatives et critères initiaux échoués. Les contrôles de format coordonnées/temps utilisent les bornes A23/A41 préexistantes, sans injection dans le solveur. A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entier A20=0,0200001220703125s ; aucun crédit du micro-démarrage ou des témoins. Vérifier les domaines entiers, structure intérieure et gravité avant les secondes suivantes. L’objectif dix secondes physiques3D puisMP4/GIF demeure actif et incomplet. Publier A44+A45 avec échecs conservés selon autorisation existante, puis avancer A46.

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
