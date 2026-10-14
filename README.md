# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A75 terminée**, prochaine **AIRCRAFT-A76**, registre **194 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A74 : contrat de cinq contacts actuels et deux variantes TYPE7 préparées, non exécutées.** Les deux scènes A49/A52 portent les mêmes interfaces2/101/102/103/104, groupes secondaires3024/1056/480/672/5785nœuds et surfaces principales en coques. L’inventaire statique propose gap0,5mm pour2 et5mm pour101–104. Vingt-deux critères de portée passent ; toutes les cartes mécaniques et TH restent identiques hors cinq cartes de contact et noms BEGIN/TITLE/RUN. Une variante de modèle de contact est déclarée explicitement, sans présumer l’équivalence dynamique TYPE25/TYPE7.

**A75 : les deux Starter autorisés échouent ; aucun Engine CHECK exécuté.** CPU1/plafond180s chacun, moteur A73 inchangé, sans correctif, compilation, GPU ni installation. Chaque cas retourne2, sans dépassement de temps, avec **916erreurs et11avertissements**. La condition de préparation propre interdit les deux CHECK : leurs places restent conditionnellement inutilisées, non réaffectées ; aucun nouveau crédit Starter. Les deux Starter autorisés sont entièrement consommés.

**Cause native précise, conservée avec les sorties.** Les916erreurs612 par cas concernent seulement l’auto-contact2 du radôme : nœuds sur la surface principale et impossibilité de calcul de nouvelles coordonnées. L’entrée et le résumé impriment Inacti1000, mais les erreurs impriment INACTI=0. Aucun domaine de nombres de nœuds ou état initial valide n’est supposé. Les11avertissements sont10messages614 (IBAG activé sans volume surveillé puis remis à zéro, deux passages pour cinq interfaces) et1message343 :4430pénétrations initiales concernant1968nœuds. La valeur1000 ne porte pas le même contrat initial entreTYPE25 etTYPE7 ; une revue statique et le résumé de paramètres ne qualifient pas l’initialisation.

**Les totaux de masse sont conservés, pas la compatibilité validée.** Les cinq TYPE7 et gaps déclarés sont imprimés. Masse191273837,9425g, ADMAS100368522,1367g et centres imprimés correspondent aux références ; aucun tenseur redistribué ou inertie native inférés. Aucun restart initial propre n’est produit, aucun impact entier prolongé. La liste des paires initiales n’est pas qualifiée par ces sorties avortées.

**Les blocages restent visibles.** Anciennes TYPE25 ignorées,107391 avertissements de préconditionnement A73, gardeTT0 ratée A71, budgets, configurations et critères échoués sont conservés. Aucun contact entier supprimé, déplacement de nœuds d’entrée, RKE de compensation, modification masse/matière/inertie ou ajustement aux dégâts connus. A76 doit auditer le filtrage de voisinage et IBAG à partir de ces nouvelles données, préparer une différence exacte puis demander un accord distinct pour de nouvelles préparations.

Les [rapports A74](wtc1_simulation_v8/output/aircraft_a74/rapport_aircraft_a74.md) et [A75](wtc1_simulation_v8/output/aircraft_a75/rapport_aircraft_a75.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Dix secondes et vidéo 3D restent incomplètes. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **19,113 fichiers scientifiques dans Git**, **41,428 sorties dans 142 archives**.

Restaurer les 141 anciennes archives des releases précédentes, puis les 1 archives [A74+A75](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a74-a75). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A76 : audit en lecture seule du nouvel échec d’initialisation TYPE7 A75 et proposition ciblée après publication A74+A75 vérifiée. Les deux Starter autorisés ont échoué avec916erreurs612 sur l’interface2 et11avertissements (10IBAG614 +1pénétrations343) ; aucun Engine exécuté. Les deux places CHECK restent conditionnellement inutilisées, non réaffectées et sans nouveau crédit Starter. Les cinq TYPE7/gaps0,5/5mm sont imprimés et masse/ADMAS conservés, mais aucun restart initial qualifié. La valeur Inacti1000 ne porte pas le même contrat entreTYPE25 etTYPE7 : ne pas désactiver globalement des contacts ni déplacer des nœuds pour forcer un passage. Inspecter le filtrage de voisinage/paires initiales et IBAG sans volume surveillé, préparer une différence exacte et un nouveau lot borné avec accord distinct. Moteur A73 conservé, zéro correctif/compilation/GPU/installation ; critères et anciens échecs inchangés. Les107391 avertissements et budgets physiques entiers restent bloquants. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.

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
