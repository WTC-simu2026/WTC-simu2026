# Notices et portée des licences

La licence MIT à la racine couvre les travaux propres de WTC-simu2026 contributors dans ce projet. Les documents sources, données et logiciels tiers ne sont pas réattribués à WTC-simu2026 contributors.

| Composant publié | Provenance et licence | Portée |
| --- | --- | --- |
| B762 graphique et conversions | [Flightradar24/fr24-3d-models](https://github.com/Flightradar24/fr24-3d-models/tree/dd53267690c6a4ecbb290a3acf0284333a5d68a9), révision `dd53267690c6a4ecbb290a3acf0284333a5d68a9`, GPL-2.0 ; ascendance FlightGear/FGMEMBERS créditée par le diffuseur. | `wtc1_simulation_v8/input/impact_i02_geom/fr24_dd532676/`, `wtc1_3d_v4/output/impact_i02_geom/`, rendus correspondants, scripts `build_impact_i02_geom.py` et `inspect_impact_i02_geom.py`. Les sources modifiables, licence et notices sont conservées. |
| Données SHPB S355 | Stefan Jentzsch, Daniel Stock, Ralf Höcker, Birgit Skrotzki, Reza Darvishi Kamachali, Dietmar Klingbeil et Vitaliy Kindrachuk, [DOI 10.5281/zenodo.17591440](https://doi.org/10.5281/zenodo.17591440), CC-BY-4.0 selon les métadonnées enregistrées. | `input/v9f_open_sources/` et `input/v9h_open_sources/` sous `wtc1_simulation_v8/` : classeur et extractions sélectives inchangés, empreintes conservées. |
| TWISBEAM officiel | Copyright 2026 **SISW Siemens Industry Software Inc.**, titulaire indiqué dans le deck ; diffusé par [OpenRadioss, commit 18707be39cd8b6385a04d698709c540f288ea95c](https://github.com/OpenRadioss/OpenRadioss/tree/18707be39cd8b6385a04d698709c540f288ea95c/qa-tests/miniqa/SMOKE_TEST), **CC-BY-NC-4.0 déclaré dans le deck**. | `wtc1_simulation_v8/openradioss_benchmarks/official_smoke_test/`. Cet exemple tiers comporte une restriction non commerciale ; il n'est pas proposé comme code MIT. Les sorties produites à partir de cet exemple sont conservées avec cette attribution. |

Les licences complètes accompagnent le dépôt sous `publication/licenses/` et les archives concernées. Le champ `license` du manifeste précise la portée par fichier. Pour les contenus tiers, il indique la licence amont conservée, pas une nouvelle concession de droits. Les anciennes notices du modèle graphique sont conservées verbatim.

Les solveurs ne sont pas redistribués : [OpenRadioss](https://github.com/OpenRadioss/OpenRadioss) annonce AGPL-3.0, [CalculiX](https://www.calculix.de/) et [Blender](https://www.blender.org/) disposent de leurs propres licences. Les bibliothèques Python et ParaView restent sous leurs licences amont. Utiliser leurs distributions officielles.

Les PDF NASA/NIST/FAA/Boeing, dessins d'archives, images, vidéos et copies de pages web restent des références externes. L'accès public à un document ne lui attribue pas automatiquement la licence MIT. Les fichiers non redistribués sont identifiés dans `publication/excluded_sources.json`.

Aucune approbation du projet par ces organismes, éditeurs ou auteurs n'est impliquée.

Les métadonnées JSON brutes de références tierces sans licence explicite conservent le statut `NOASSERTION-reference-metadata` dans le manifeste ; la MIT ne leur est pas attribuée.
