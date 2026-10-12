# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **12 octobre 2026** : **AIRCRAFT-A49 terminée**, prochaine étape **AIRCRAFT-A50**. Le registre compte **168 entrées**. La panne d’assemblage est reliée aux peaux inférieures du radôme ; une représentation équivalente des chaînes rigides permet au modèle entier de terminer son diagnostic.

A48 teste quatre petits assemblages puis une copie entière sans les368RBE3. Leur retrait conserve masse totale, centre et ADMAS prescrites, mais ne supprime pas SIGSEGV. Une observation du processus fils inchangé capture26paires/156lignes sans colonne attendue dans ASSEMC_KIJ. Les labels originaux restent alors inconnus.

A49 observe aussi les tableaux de coques et coordonnées : **128éléments et302nœuds internes correspondent exactement à l’entrée**, erreur0mm. Les26paires manquantes ont un nœud de peau secondaire d’une racine entièrement rigide et principal d’une liaison cohésive déportée. **Cinq petits reproducer ne reproduisent pas la panne**. L’option numérique Idrill1, vérifiée réellement reçue par le moteur, ne la corrige pas non plus ; le défaut persiste avec des DOF6/6.

Une copie distincte compose **144chaînes déjà entièrement rigides**, sans supprimer leurs déports ou bras de levier. Les3072contrôles indépendants de pose, vitesse et moments passent les seuils pré-déclarés. Coordonnées, matériaux, propriétés, masses, groupes, contacts et RBE3 sont conservés. **Le modèle entier termine maintenant CHECK sans planter**, code0/NORMAL, en7,39s natives. Masse191273837,9425g, centre et ADMAS100368522,1367g restent identiques à la référence.

**Le contrôle mécanique entier reste échoué** :15directions de raideur suspectes,5avertissements récapitulatifs et **49370messages de connectivité** dans le listing, dont48996TYPE2 et374RBE2. Les valeurs négatives extrêmes ne sont pas interprétées comme un mécanisme physique. Deux avertissements Starter originaux et cinq TYPE25 ignorés en implicite restent explicites. L’histoire initiale CHECK n’est pas convertible ; l’inertie redistribuée et le travail natifs ne sont pas supposés qualifiés. Un addendum distingue mat_ID4 et Npt_ply3 dans TYPE19, sans modifier l’entrée.

A49 comprend sept préparations Starter et neuf Engine nouveaux, un thread CPU chacun, caps180s, sans GPU. Aucun patch logiciel ou de données mécaniques, installation, compilation ou ancien calcul réussi relancé. Les [rapports A48](wtc1_simulation_v8/output/aircraft_a48/rapport_aircraft_a48.md) et [A49](wtc1_simulation_v8/output/aircraft_a49/rapport_aircraft_a49.md) séparent les six catégories de preuve. Les bilans natifs de la copie composée et les connexions TYPE2/RBE2 sont la suite, avec contacts originaux conservés. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Aucun temps de diagnostic ou de panneau n’est crédité à l’impact entier. L’intégrité de publication ne valide pas la physique ni l’événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **16,339 fichiers scientifiques dans Git**, **28,519 sorties dans 127 archives**.

Restaurer les 125 anciennes archives des releases précédentes, puis les 2 archives [A48+A49](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-12-aircraft-a48-a49). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A50 : partir de la copie A49 à chaînes rigides composées, qui termine désormais CHECK sans SIGSEGV. Les144références internes sont redirigées vers leur racine entièrement rigide, sans perdre offsets, bras de levier, masses ou matériaux. Les cinq petits reproducer ne reproduisent pas la panne ; Idrill1 reçu par le moteur ne la corrige pas. La copie entière conserve RBE3 et TYPE25, mais CHECK reste échoué :15directions de raideur suspectes et49370messages de connectivité, dont48996TYPE2 et374RBE2. Vérifier dans un lancement explicite entier très court et borné les masses/inerties/énergies natives après redistribution, avec les TYPE25 conservés, par comparaison aux sorties A45 déjà en cache ; aucun ancien calcul réussi à relancer. Identifier ensuite les nœuds et contraintes des messages TYPE2/RBE2 et leur construction du graphe depuis la source figée. Ne pas lancer un impact implicite avec contacts ignorés, supprimer des contraintes, ajouter des masses, ajuster les matériaux ou contourner une panne logicielle. Les équations rigides composées sont vérifiées, leur implémentation native chargée reste à qualifier. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF actif et incomplet. Publier A48+A49 avec tous les échecs puis continuer A50.

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
