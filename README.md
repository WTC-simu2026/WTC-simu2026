# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **10 octobre 2026** : **AIRCRAFT-A21 terminée**, prochaine étape **AIRCRAFT-A22**. Cette mise à jour rattrape les huit itérations A14 à A21, avec les calculs natifs, configurations, témoins refusés et rapports conservés. Le registre compte 140 entrées.

Le dernier aperçu 3D A20 couvre **20 millisecondes physiques** ; son ralenti MP4/GIF ne constitue pas dix secondes simulées. Le nouvel impact intact A21 atteint **12,000055 ms**, aux mêmes conditions hypothétiques que A20, avec un pas deux fois plus fin. L'impulsion finale varie de **0,9987 %** et l'énergie générée de **0,2580 %**, mais le **bilan énergétique local échoue encore**. Le résidu au contact du fuselage atteint −257,094 kJ à 10,920 ms ; les limites des matériaux métalliques et une énergie de peau négative restent des critères échoués.

Les contrôles isolés du cœur fini et du sandwich Spot5 A20 réussissent. Les témoins des attaches de racine échouent en rotation ; les remplacements TYPE2 testés ne sont pas qualifiés. Leur défaut ne prouve pas la cause complète du bilan entier. Aucun état invalide n'est prolongé vers 10 secondes. La gravité, l'intérieur porteur, la fracture métallique et les contacts des fragments restent à compléter.

Lire les [rapports A14](wtc1_simulation_v8/output/aircraft_a14/rapport_aircraft_a14.md) à [A21](wtc1_simulation_v8/output/aircraft_a21/rapport_aircraft_a21.md), le [rapport A20](wtc1_simulation_v8/output/aircraft_a20/rapport_aircraft_a20.md) et la [passation A21 → A22](harness/handoffs/WTC1_AIRCRAFT_A21_HANDOFF.md). La release fournit l'aperçu A20 et les états mécaniques ; aucune ressemblance visuelle n'identifie un mécanisme historique. Vitesses, attitude, assemblages et lois non mesurées sont des hypothèses déclarées ; aucun résultat de dommage NIST ou observé n'est une cible.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **9,767 fichiers scientifiques dans Git**, **16,299 sorties dans 100 archives**.

Restaurer les 79 anciennes archives des releases précédentes, puis les 21 archives [A14–A21](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-10-aircraft-a14-a21). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

A22 : tester une attache mécanique finie avec masse et inertie explicites, en translation, rotation et dynamique libre, puis seulement envisager un nouveau départ intact. Réutiliser les témoins cœur et sandwich Spot5 A20 réussis. Préparer la fracture métallique et acier à partir de sources et plages déclarées, sans cible de dommage. Le document NASA ATR42 à 9,14 m/s n'est pas une mesure AA11 à 200 m/s. Les contrôles de bilan local et de matériaux doivent passer avant extension. L'objectif reste une vidéo 3D des dix premières secondes physiques ; il est incomplet. Publication suivante après A22 et A23 vérifiées.

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
