# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **12 octobre 2026** : **AIRCRAFT-A43 terminée**, prochaine étape **AIRCRAFT-A44**, compilation supplémentaire en attente d’accord explicite. Le registre compte **162 entrées**. A42+A43 localisent une incompatibilité de préparation LAW117 et préparent une voie de compilation séparée. Les anciens résultats, tentatives et critères échoués sont conservés.

A42 teste le modèle entier dès son état initial en explicite. Il avorte aussi avant la première avance ; le problème ne vient donc pas exclusivement du CHECK implicite. Une trace d’avortement installée localise l’arrêt dans **SIGEPS117**, pendant les forces cohésives. La lecture vérifiée des en-têtes natifs montre pour LAW117 **NUPARAM=0, NIPARAM=0, NTABLE=0**, alors que la source du moteur MUMPS A35 attend **14 paramètres réels, 6 entiers et 2 tables**. L’ancien préparateur Windows fournit une autre représentation.

Une nouvelle entrée ajoute deux fonctions de facteur constant1, à résistances450/100MPa et énergies de rupture inchangées. Son équivalence d’entrée est vérifiée ; elle ne corrige pas le format préparé. Le moteur Linux avorte encore, tandis que **le moteur Windows termine normalement sur le même état initial frais et les mêmes cartes**, en3cycles. La préparation garde2avertissements et échoue au critère strict. Aucune extension au-delà des20ms A20, aucune qualification native de cette variante ni modification de reprise.

A43 relève **cinq interfaces Reader absentes** et une interface supplémentaire dont la signature C ne correspond pas à son appel Fortran. Aucune fonction vide n’est ajoutée. La source complète du28juillet, commit **3d75ff13d1946f6d28a43920eac4fa2aae41b27a**, utilise l’ancien tableau LAW117 de21valeurs, présent dans une séquence unique de la reprise. Cette corroboration limitée et les blobs Git vérifiés ne sont ni un parseur complet ni une preuve d’identité avec le binaire Windows.

La [proposition A43](wtc1_simulation_v8/output/aircraft_a43/proposition_compilation_moteur_compatible.md) prépare la compilation du seul moteur antérieur avec MUMPS déjà installé, séparément, au maximum6threads CPU et une heure, sans nouveau paquet ou patch de physique. La dépendance67 en cache est proposée au lieu de71, différence explicitement non qualifiée. Le constructeur est écrit et vérifié par analyse de syntaxe ; **il n’a pas été exécuté** et demande un nouvel accord pour cette source. Comparaisons LAW117, bilans, champs et démarrage entier borné sont requis avant extension.

Les [rapports A42](wtc1_simulation_v8/output/aircraft_a42/rapport_aircraft_a42.md) et [A43](wtc1_simulation_v8/output/aircraft_a43/rapport_aircraft_a43.md) séparent faits, sources, archives, hypothèses, résultats et lacunes. Les binaires, bibliothèques et sources tierces brutes restent exclus de la publication. Compilation A35 terminée39,29min ; aucune nouvelle installation ou compilation. Le contact TYPE7 A41 reste qualifié dans son témoin ; contact chargé et croissance A40, peaux A34 et raffinement A36 restent échoués, et les cinq TYPE25 entiers restent à vérifier.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20millisecondes physiques**. Aucun temps de témoin ou de démarrage n’est crédité à l’extension entière, aucun coût10s extrapolé. Aucun dommage connu comme cible. L’intégrité de publication ne valide pas la physique ou l’événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **15,598 fichiers scientifiques dans Git**, **26,233 sorties dans 123 archives**.

Restaurer les 121 anciennes archives des releases précédentes, puis les 2 archives [A42+A43](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-12-aircraft-a42-a43). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A44 : après accord humain explicite demandé sur la proposition A43, construire uniquement un moteur MUMPS séparé depuis la source complète3d75ff13d1946f6d28a43920eac4fa2aae41b27a(28juillet2026), sans patch de physique, installation ou remplacement des moteurs. Six threads, plafond1h, dépendance67en cache au lieu de71 explicitement non qualifiée. Le constructeur préparé est figé dans A43. A42 localise l’incompatibilité du nouveau SIGEPS117 avec la préparation Windows; A43 corrobore les21anciens paramètres natifs et identifie cinq interfaces manquantes plus une signature discordante du Reader. Ne créer aucune fonction vide. Après construction, vérifier versions/bibliothèques, LAW117 natif et bilans/comparaisons Windows/Linux, puis démarrage entier explicite et CHECK conditionnel. Toute incompatibilité persistante reste échouée. Ne modifier ni reprise binaire ni masse/matériau/contact pour la contourner. Contact direct A41 qualifié seulement dans son témoin; A40chargé/croissance, A34peaux et A36raffinement restent échoués. Meilleur impact entierA20≈20ms; objectif10sphysiques3D puisMP4/GIF incomplet. Publier la paire A42+A43 avec les échecs et cette proposition, selon autorisation déjà donnée. Pas de nouvelle compilation avant réponse à la question A43.

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
