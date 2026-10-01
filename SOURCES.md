# Sources externes et provenance

L'instantané publie les modèles et calculs propres au projet. Les références sont conservées dans les configurations `wtc1_simulation_v8/data/`, les fichiers `source_manifest.json`, le registre et les rapports. Les empreintes permettent de retrouver la version effectivement utilisée.

- [NIST, investigation World Trade Center](https://www.nist.gov/world-trade-center-investigation) : rapports NCSTAR, géométrie et résultats officiels. Les résultats NIST réutilisés ne constituent pas une validation indépendante.
- [NASA Technical Reports Server](https://ntrs.nasa.gov/) : propriétés et essais de matériaux, fracture et CTOA. La dernière étude utilise notamment [NASA CR-2006-214281](https://ntrs.nasa.gov/citations/20060008654), avec pages bornées et convention de déformation toujours indéterminée.
- [OpenRadioss](https://github.com/OpenRadioss/OpenRadioss) et [documentation Altair Radioss](https://help.altair.com/hwsolvers/rad/index.htm) : solveur, formulation des coques, lois et signification des sorties. Les pages sauvegardées servent de références et ne sont pas replacées sous MIT.
- [Jeu SHPB S355, Zenodo](https://doi.org/10.5281/zenodo.17591440), CC-BY-4.0 : échantillon sélectif inclus avec attribution.
- [Modèles graphiques Flightradar24](https://github.com/Flightradar24/fr24-3d-models), GPL-2.0 : package B762 original et dérivés identifiés. Un modèle graphique ne fournit pas les propriétés mécaniques d'un Boeing réel.
- [Boeing, airport planning](https://www.boeing.com/commercial/airports/plan_manuals.page) : références dimensionnelles. Le manuel est externe ; la petite transcription dimensionnelle utilisée est conservée.

Le dossier local `work/official_sources/` et l'archive documentaire personnelle ne sont pas publiés. Des fichiers des rapports peuvent encore citer leurs anciens chemins Windows. Ces chemins sont historiques et n'impliquent pas qu'ils existent dans un clone.

`publication/excluded_sources.json` décrit les fichiers inventorés mais non redistribués, leurs tailles, empreintes et raisons. Les sources extérieures à l'inventaire restent représentées par `harness/sources.json`, `harness/snapshots/source_hashes.json` et les manifestes des itérations. Aucun rescannage de l'archive personnelle n'a été effectué pour cette publication.

Pour reproduire une étape dépendant d'un fichier absent, utiliser son URL/identifiant primaire et comparer l'empreinte du téléchargement. Ne pas substituer une édition différente sans le noter. Les sources sans accès public établi peuvent empêcher une reproduction complète ; le rapport conserve cette limite.
