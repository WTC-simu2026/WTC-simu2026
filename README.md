# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A71 terminée**, prochaine **AIRCRAFT-A72**, registre **190 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A70 : proposition exacte de classification du résidu nul.** Le résidu nul A69 est confirmé, mais l’admissibilité proposée doit rester distincte de toute validation physique. La version R4 ajoute la déclaration native COM08 et sélectionne IDYNA2/IQSTAT0/TT0/R2exact0 dans IMP_CHKM. Quinze contrôles de portée passent ; versions de préparation échouées R0–R3 conservées, source privée AGPL hors livrables MIT. La proposition non compilée est ensuite autorisée distinctement par l’humain.

**A71 : huitième moteur isolé appliqué exactement et compilé.** Première compilation sur six CPU, plafond une heure, sans GPU ni installation ; toutes les corrections A67 restent présentes. Six Engine et un Starter sur un CPU/plafond180s sont entièrement consommés. **Le correctif TT0 échoue dans trois contrôles.** Le témoin zéro dynamique et les deux scènes entières affichent encore une erreur de chargement, R2=0, et aucune nouvelle INFO. Compilation/NORMAL ne sont pas un passage du critère.

**Les contrôles de comparaison passent.** Le zéro statique reste refusé comme prévu ; le témoin statique avec1N par nœud supérieur donne R2=4 et CHECK sans erreur ni avertissement, après Starter propre. La dynamique libre du nouveau binaire passe23critères aux seuils A67 conservés et ses TH atteignent1ms. Aucune durée de témoin créditée à l’impact entier. Les cinq observations CHECK sont complètes, y compris l’original manquant en A69 ; son ancien échec n’est pas réécrit.

**Cause mise en évidence en lecture seule : l’horloge TT avance avant CALL IMP_CHKM.** La garde TT exactement zéro ne représente pas le contexte du premier CHECK. Les valeurs précises des flags et de TT à l’appel ne sont pas directement capturées ; aucun scalaire natif supposé. A72 doit préparer une sélection par le contexte CHECK explicite et des observations de ces flags/horloges, sans rejouer le lot A71 ou réinitialiser les budgets.

**Les scènes entières restent bloquées**, chacune avec1ERROR/107396WARNINGS, dont107391 coefficients de préconditionnement signalés et cinq TYPE25 ignorés. Aucun STOPvolume ; A52nonintégrée, aucune extension dynamique entière. Les sources, versions, anciens moteurs, archives, budgets, préparations et critères échoués sont conservés. Aucun chargement artificiel dans la scène entière ni compensation RKE.

Les [rapports A70](wtc1_simulation_v8/output/aircraft_a70/rapport_aircraft_a70.md) et [A71](wtc1_simulation_v8/output/aircraft_a71/rapport_aircraft_a71.md) séparent les six catégories de preuve. Nouvelle modification/compilation du moteur et lot natif soumis à un accord humain distinct. **Meilleur impact entier : 0,0200001220703125 s.** Dix secondes et vidéo 3D ne sont pas produites ; aucune extrapolation visuelle fabriquée. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **18,819 fichiers scientifiques dans Git**, **41,201 sorties dans 140 archives**.

Restaurer les 139 anciennes archives des releases précédentes, puis les 1 archives [A70+A71](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a70-a71). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A72 : audit/proposition en lecture seule de la sélection CHECK, à partir du nouvel échec A71. Le moteur avance TT avant IMP_CHKM ; la garde TT==0 ne correspond pas au contexte du premier contrôle. Préparer une sélection explicite par IMP_CHK>0, sans temps absolu supposé, et des observations des flags/horloges dans les futurs contrôles. A71 huitième moteur compilé exactement après accord ; six Engine et un Starter autorisés consommés, aucun replay ou crédit entier. Dynamique libre1ms et charge positive R2=4 passent ; zéro statique reste refusé comme prévu ; zéro dynamique et deuxCHECK entiers restent échoués avec R2=0. Conserver cette nouvelle garde ratée et toutes les anciennes sorties/critères/budgets. Les 107391 avertissements et cinq TYPE25 par scène sont bloquants. Toute nouvelle modification/compilation et lot natif exigent une proposition concrète et un accord distinct. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.

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
