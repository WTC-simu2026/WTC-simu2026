# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **14 octobre 2026** : **AIRCRAFT-A65 terminée**, prochaine **AIRCRAFT-A66**, registre **184 entrées**. Objectif dix secondes physiques puis vidéo3D incomplet.

**A64 : deux essais plus fins terminés, composé initial échoué.** La fréquence de sortie0,0001ms omettait6000pas intermédiaires du second essai0,0000625ms et invalidait la reconstruction de vitesse cycle par cycle. Les champs terminaux sauvegardés du second cas précédaient1ms. Échecs/lecteur initial préservés. Une analyse indépendante aux cycles réellement enregistrés concorde avec la solution exacte et les compteurs natifs, sans inventer les champs manquants. Les deux CHECK conditionnels n’ont pas été lancés.

**A65 : nouveau lot humain explicite, quatre Engine exécutés**, deux Starter propres, CPU1/cap180s, moteurA62 inchangé, sansGPU/compilation/installation. TFILEdt/2 et arrêt1+dt/2 enregistrent chaque cycle et la frontière cible1ms ; paramètres physiques et seuils conservés. **22contrôles par essai libre,44au total, passent**, avec comparaison temporelle KE5,47015e-6J/IE5,49140e-6J sous le seuil inchangé1,01e-5J. Résidu énergie≤4,48e-8J, impulsion/support≤4,81e-8Ns. Les sorties natives TH atteignent1ms ; dernière animation du second cas0,995062ms conservée, champ terminal complet issu des huit nœudsTH.

**Les deux CHECK entiers échouent.** Anciennes initialisations/cartes identiques vérifiées par empreintes. Chaque scène affiche15ERRORS/5WARNINGS et624messagesSTOPvolume, et ignore cinqTYPE25. Code0/NORMAL n’est pas un passage ; premier lecteur étroit null/false conservé puis corrigé par une nouvelle analyse des messages réels. A52nonintégré, aucun impact entier prolongé.

**A66 préparée, aucun patch appliqué ni compilé.** Les624éléments utilisentTYPE43/LAW117/Ismstr4, tandis que le helperA62 traiteIsmstr1. L’aire de référenceVOL n’est stockée que pourIsmstr1 ; Ismstr4 utilise l’aire couranteAREAP. Les quatre aires des624surfaces sont positives. Prototype courant52contrôles PASS ; proposition/source exacte dans une copie privéeAGPL, hors archivesMIT. La future modification/compilation du septième moteur nécessite un accord distinct ; les cinq contactsTYPE25 restent bloquants. Les tentatives de préparation R0–R3 échouées sont conservées, analyse/prototype réussi R1 réutilisé sans replay.

Les [rapports A64](wtc1_simulation_v8/output/aircraft_a64/rapport_aircraft_a64.md) et [A65](wtc1_simulation_v8/output/aircraft_a65/rapport_aircraft_a65.md) séparent les six catégories de preuve. Budgets, anciennes sorties, échecs au repos/imposésA62 et temporels grossiersA63 préservés. Domaine libre élastique uniquement ; dommage général, grandes rotations et bilans entiers restent non qualifiés. **Meilleur impact entier0,0200001220703125s**, aucune durée de témoin créditée à l’objectif et aucune vidéo fabriquant les secondes manquantes. Intégrité de publication distincte de validation physique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **18,255 fichiers scientifiques dans Git**, **39,723 sorties dans 137 archives**.

Restaurer les 136 anciennes archives des releases précédentes, puis les 1 archives [A64+A65](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-14-aircraft-a64-a65). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A66 : audit borné en lecture seule des nouveaux messages CHECK A65, des624éléments60001–60624 et des cinq contacts TYPE25, puis de leurs branches sources natives. Réutiliser les sorties A65 sans nouveau Starter/Engine, sans patch/compilation ni modification des budgets. Distinguer un contrôle volumique appliqué à une surface valide d’une géométrie réellement invalide ; ne pas supprimer les messages ou substituer silencieusement les contacts. Préparer ensuite la proposition concrète nécessaire. A65 quatre contrôles autorisés exécutés : local libre raffiné PASS, scènes entières quinze erreurs affichées/624STOPvolume/cinqTYPE25 ignorés chacune. Les échecs au repos/imposés A62, temporels grossiers A63 et lecteur incomplet A64 restent préservés. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes. Toute nouvelle modification/compilation du moteur exige un accord explicite distinct.

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
