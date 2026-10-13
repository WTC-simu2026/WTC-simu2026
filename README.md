# WTC-simu2026

**Construction progressive d'une simulation exploratoire du WTC 1 : impact d'un Boeing 767, incendies et réponse structurelle, jusqu'à un éventuel effondrement ou son arrêt.**

Le projet teste des mécanismes, des hypothèses explicites et des plages de paramètres. Aucun résultat final n'est présupposé. Il s'agit d'une recherche personnelle reproductible, assistée par Codex, dont les modèles, calculs, essais rejetés et limites sont publiés pour être examinés et améliorés.

*English: an open, incremental WTC 1 research harness. Current results concern limited verification models; they do not establish the cause or reproduce the full historical collapse.*

## Où en est la simulation ?

Instantané du **13 octobre 2026** : **AIRCRAFT-A53 terminée**, prochaine étape **AIRCRAFT-A54 après autorisation explicite du correctif logiciel**. Le registre compte **172 entrées**. A52 teste un regroupement de contraintes entier et le rejette ; A53 identifie le vrai bloc arrêté, puis observe une écriture de graphe dans le mauvais tableau du moteur inchangé.

A52 conserve la référence complète et teste432→216TYPE2 par facette. Une première tentative sans en-tête échoue ; sa réparationR1 dans un autre dossier donne un Starter avec deux avertissements et zéro erreur. Masse, centre et ADMAS prescrites sont identiques à la référence. Les éléments, matériaux et autres contraintes sont conservés. L’Engine regroupé s’arrête avant tout contrôle natif de ses attaches ; leur équivalence n’est donc pas vérifiée, et le candidat reste rejeté. Trois Engine et deux Starter nouveaux sont journalisés, caps180s/unCPU, aucun GPU.

A53 exécute quatre Engine instrumentés, aucun Starter, aucune installation ou compilation. La première capture de quadrangles reste périmée et conservée. L’observation des triangles identifie exactement **128éléments193..320 de la peau du fuselage**, **89nœuds**, écart de coordonnées **0mm**. Connectivité et couples réellement assemblés sont vérifiés. L’arrêt ASSEMC_KIJ+0x664 concerne **24paires6/6 et144lignes absentes** après1579appels ; il n’est pas attribué aux huit peaux du contexte périmé.

La sonde d’entréeREORDER_A n’observe aucun appel, résultat inconclusif conservé. Une surveillance séparée d’adresses de données dans le processus de la référence A49 non regroupée montre le défaut : ligne principale9891>INK9888, pas ordinaireNNMAX24 contre pas principalNKMAX119. Le moteur écrit le voisin48154 dans le mauvais tableau, alors qu’il figurait déjà dans les trois colonnes correctes du nœud48151. Le compteur correct augmente3→4, puis jusqu’à14 dans douze événements bornés, tandis que la quatrième colonne correcte reste0. Une écriture incorrecte est observée ; aucun total global ni explication de toutes les autres erreurs n’est inféré. Le moteur, les instructions et les tableaux mécaniques ne sont pas modifiés par l’observation.

Un correctif limité à **ind_glob_k.F** est préparé : choisir les tableaux corrects pour ajout, lecture et appartenance dans les deux blocsTYPE2. Le dimensionnement garde ses indices ordinaires globaux avec padding ; la construction utilise row-INK pour les principales. **Huit contrôles Python indépendants** passent une référence dictionnaire/ensembles. La portée de la différence et la limite72colonnes sont vérifiées. **Aucun correctif appliqué, aucune compilation ni qualification native du moteur corrigé.** Le patch et la source dérivée AGPL restent hors du manifeste public ; empreintes, scripts propres et proposition sont conservés.

La proposition prévoit un troisième moteur isolé, même source figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, une heure de compilation maximum, sixCPU, dépendances déjà installées, aucun GPU ni nouvelle installation, puis contrôles natifs bornés180s. Elle **nécessite un nouvel accord explicite** : l’ancien accord concernait le moteur non modifié. Aucun travail A54 commencé ; prompt de reprise demandé pour une nouvelle session.

Les [rapports A52](wtc1_simulation_v8/output/aircraft_a52/rapport_aircraft_a52.md) et [A53](wtc1_simulation_v8/output/aircraft_a53/rapport_aircraft_a53.md) séparent les six catégories de preuve. Les anciennes tentatives, quinze erreurs mécaniques de la référence et49370messages restent conservés. CHECK forcePCG/IPREC5 et ne qualifie pas une dynamiqueMUMPS. Les cinqTYPE25 ignorés en implicite empêchent de créditer un tel impact ; A40 chargé/croissance, A34 peaux, A36 raffinement et bilans locaux restent échoués ou manquants. Aucun matériau ajusté, masse compensatoire ou cible de dégâtsNIST.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entierA20 = **0,0200001220703125seconde**. Aucun temps des diagnostics n’est crédité. L’intégrité de publication ne valide pas la physique ni l’événement historique.


## Ce qui est publié

- `harness/` : état scientifique, registre des expériences, références, contrôles et passations.
- `wtc1_simulation_v8/scripts/` et `data/` : code des calculs et configurations numériques.
- `wtc1_simulation_v8/output/`, dossiers CalculiX et OpenRadioss : résultats, rapports, bilans et diagnostics, y compris essais rejetés.
- `wtc1_3d_v4/` : scripts de visualisation, paramètres, audits et modèles/rendus dans les archives de résultats.
- `outputs/` : calculs exploratoires antérieurs et audits complémentaires. Leurs affirmations se lisent avec leurs propres limites ; leur présence n'est pas une validation.
- `publication/` : inventaire complet, empreintes SHA-256, règles de publication, licences tierces et liste motivée des fichiers externes non redistribués.

Inventaire courant : **16,562 fichiers scientifiques dans Git**, **28,565 sorties dans 130 archives**.

Restaurer les 128 anciennes archives des releases précédentes, puis les 2 archives [A52+A53](https://github.com/WTC-simu2026/WTC-simu2026/releases/tag/snapshot-2026-10-13-aircraft-a52-a53). Manifestes, SHA-256 et URL conservés ; aucune ancienne archive reconstruite ou remplacée.

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

AIRCRAFT-A54 : demander l’accord explicite de Jeremy pour la proposition wtc1_simulation_v8/output/aircraft_a53/proposition_correctif_graphe_moteur.md avant toute application ou compilation. A53 identifie le vrai bloc fautif : 128 triangles SH3N du fuselage, éléments193..320,89nœuds, coordonnées exactes ; 24paires6/6 et144lignes manquantes. Une observation séparée du modèle entier A49 non regroupé montre une écriture TYPE2 dans ICOK au mauvais pas24 pour une ligne principale exigeant ICOKM au pas119, puis inflation du compteur de3à4 alors que le voisin existe déjà ; colonne correcte toujours0. Correctif d’un fichier préparé mais non appliqué et non compilé, huit contrôles Python de graphes réussis sans qualification native du correctif. Après autorisation seulement : troisième moteur isolé depuis la source 3d75ff13d1946f6d28a43920eac4fa2aae41b27a, patch exact conservé, dépendances existantes, aucune installation/GPU, compilation≤1h et sixCPUmaximum ; contrôles natifs≤180s, destination des écritures puis CHECK original/candidat et lois/contacts/bilans. Ne pas déplacer les entrées physiques ni traiter les TYPE25 ignorés comme des contacts qualifiés. En dimensionnement, conserver le padding et les indices globaux ordinaires ; en construction, principales row-INK. A52 groupée reste rejetée, anciennes erreurs conservées. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques 3D puisMP4/GIF incomplet. Jeremy demande de terminer A53 et sa publication puis de reprendre dans une nouvelle session ; ne pas commencer A54 ici.

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
