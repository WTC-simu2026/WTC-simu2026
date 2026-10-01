# WTC 1 - V9Y - audit borne des sources alternatives et des recus de plans d'escaliers

**Validation generale : PASS**

> PASS DOCUMENTAIRE CONSERVATEUR - AUCUNE SOURCE CIBLE QUALIFIEE - AUCUN RECU FICHIER EXACT - ZERO CHAINE COTEE - PAS AS-BUILT - ZERO CREDIT PHYSIQUE

## Conclusion

V9Y est PASS comme audit reproductible de sources alternatives, mais la porte geometrique reste fermee. Les manifestes publics de 1984 et 2009 contiennent bien A-A-148, A-A-150, A-A-151 et A-A-153. V9Y a extrait uniquement 27 petits fichiers par plages HTTP, sans telecharger les trois archives completes. Aucun candidat ne fournit simultanement une information de plan cible demonstrablement superieure et un recu NIST/FOIA nommant le lot de 175 TIFF ou les quatre feuilles cibles.

## 1. Faits directement observes ou transcrits

- Les quatre TIFF deja conserves sont des images binaires 1 bit, compressees LZW sans perte, de 4 896 pixels de large et declarees a 200 dpi. Le tag DocumentName contient `buzzsaw.com`.
- Le torrent LERA 1984 inventorie 284 fichiers, dont 261 TIFF, 2 DWG et 4 DXF; les quatre feuilles cibles y sont nommees.
- Le torrent mai 2009 inventorie 901 fichiers, dont 895 PNG; les suffixes `_0` a `_3` forment une pyramide de quatre resolutions pour chacune des quatre feuilles cibles, et non quatre tuiles spatiales.
- Les deux petits DXF ont ete lus uniquement pour leurs calques, entites et textes. Hits textuels `STAIR`: 0; hits textuels explicites pour les niveaux 93-99: 25. Aucune coordonnee DXF n'a ete extraite ou utilisee.
- Le journal FOIA reproduit une reponse NIST du 28 janvier 2013 et la ligne abregee `DOC-NIST-2012-000501 / 12-178 / WTCI-120 / WTC Architectural Drawings 1 - 65`. La correspondance du dossier, datee des 12 juillet et 1er novembre 2012, designe explicitement `WTC 7 Architectural Drawings 1 through 65` et annonce la remise de 64 pages.

## 2. Resultats et contexte officiels

- Le dossier FOIA 12-178 est un fait documentaire NIST, mais il concerne explicitement le WTC 7. Il ne constitue donc pas un recu des plans WTC 1 et ne nomme ni le lot de 175 TIFF, ni A-A-148, A-A-150, A-A-151 ou A-A-153.
- V9Y ne cree aucun resultat de dommage officiel et ne transforme pas une distribution publique en certification as-built.

## 3. Affirmations provenant des archives publiques

- Les titres `WTC1 Architectural Drawings Dated May 9 1984` et `WTC1 Architectural and Engineering Drawings Released May 2009` sont des libelles de distribution 911datasets.
- La page 1984 renvoie a `LERA - PLANS-022102`, 911blogger et 911research; la page 2009 renvoie a 911blogger. Ces pages ne sont pas des recus d'agence.
- Le champ `source` de l'item Internet Archive 1967 reste absent. Le texte `source=original` applique aux fichiers par Internet Archive decrit leur statut dans l'item, pas leur provenance NIST.

### Sources publiques auditees

- [Metadonnees Internet Archive du lot 1967](https://archive.org/metadata/WTC_Architectural_Drawings_Dated_Aug_31_1967)
- [Page 911datasets 1984 archivee](https://web.archive.org/web/20170424103333/http://www.911datasets.org/index.php/WTC1_Architectural_Drawings_Dated_May_9_1984)
- [Page 911datasets 2009 archivee](https://web.archive.org/web/20170424103325/http://www.911datasets.org/index.php/WTC1_Architectural_and_Engineering_Drawings_Released_May_2009)
- [Contexte officiel de collecte NIST](https://www.nist.gov/news-events/news/2004/07/status-data-collection-efforts)

## 4. Hypotheses propres au modele

- LOW, BASE et HIGH restent trois placements separes, explicitement hypothetiques et inchanges.
- Une compression sans perte ne restaure pas les details absents du scan original; un PNG ou TIFF sans perte n'est donc pas automatiquement une source plus informative.
- Les PNG 2009 sont traites comme une pyramide de resolutions. Les niveaux `_0` sont des transcodages sans perte, pixel-identiques aux TIFF 1967 normalises; les niveaux `_1` a `_3` sont des reductions et ne constituent pas de nouvelles donnees de plan.

## 5. Resultats derives

- Fichiers distants selectionnes et verifies : 27.
- TIFF cibles LZW/200 dpi deja conserves : 4/4.
- TIFF LERA Group 4 sans perte/200 dpi : 4/4.
- TIFF LERA apportant davantage de pixels : 0/4.
- Correspondances exactes de pixels entre les deux series TIFF : 0/4.
- Niveaux PNG 2009 `_0` exactement identiques aux TIFF 1967 apres normalisation 1 bit : 4/4.
- Sources cibles de qualite superieure qualifiees : 0.
- Recus NIST/FOIA exacts pour le lot cible : 0.
- Chaines cotees completes acceptees : 0; ancrages numeriques fermes : 0.
- Coordonnees creees : 0; geometries promues : 0.
- Empreinte de matrice : `d27e04e5e33c4e053f893cc1097d08647e632174245f5e49d0dc03e04c8388de`.

## 6. Contradictions et informations manquantes

- Un format TIFF ou PNG sans perte garantit seulement l'absence de perte supplementaire lors de l'encodage; il ne garantit ni la resolution du document papier, ni son autorite de revision.
- Les petits DXF ne sont pas qualifies comme plans d'escaliers des niveaux 93-99. Les gros DWG/DXF du torrent ne sont pas acquis dans V9Y et leur nom ne suffit pas a leur attribuer une semantique as-built.
- Il manque toujours un registre de dessins, un recu fichier par fichier NIST ou PANYNJ, une version native ou de resolution superieure des quatre feuilles cibles et une chaine cotee complete avec extremites non ambigues.
- Aucun fait de dommage, aucune masse, rigidite, resistance, connexion ou capacite de chemin de charge n'est deduit.

## Portes de validation

- v9x_regression_hashes: PASS
- small_source_hashes: PASS
- protected_blender_master_unchanged: PASS
- torrent_descriptor_count: PASS
- torrent_file_counts: PASS
- all_remote_selected_entries_verified: PASS
- cached_core_tiff_count: PASS
- four_target_sheets_in_each_alternate_raster_set: PASS
- may_2009_full_resolution_levels_match_cached_pixels: PASS
- source_quality_audit_completed: PASS
- foia_log_relevant_record_found: PASS
- foia_12_178_release_disambiguated_as_wtc7: PASS
- foia_target_mismatch_not_overclaimed: PASS
- no_qualified_higher_quality_target_source: PASS
- no_accepted_numeric_dimension_chain: PASS
- no_accepted_closed_grid_anchor_set: PASS
- no_scan_pixel_coordinates: PASS
- no_model_geometry_promotion: PASS
- variant_separation_retained: PASS
- zero_physical_properties: PASS
- solver_and_blender_prohibited: PASS
- full_alternate_datasets_not_downloaded: PASS

Le Blender maitre conserve son empreinte protegee. Aucun processus Blender et aucun solveur structurel n'ont ete executes.

## Livrables

- Manifeste : `wtc1_simulation_v8/output/v9y_alternate_source_manifest.json`
- Inventaire distant : `wtc1_simulation_v8/output/v9y_remote_dataset_inventory.json`
- Audit FOIA : `wtc1_simulation_v8/output/v9y_foia_receipt_audit.json`
- Audit qualite : `wtc1_simulation_v8/output/v9y_source_quality_audit.json`
- Matrice : `wtc1_simulation_v8/output/v9y_alternate_source_candidate_matrix.csv`
- Porte modele : `wtc1_simulation_v8/output/v9y_stairwell_geometry_gate.json`
- Planche de controle : `wtc1_simulation_v8/output/v9y_alternate_source_figures/v9y_contact_sheet.png`

## Etape suivante pre-declaree - V9Z

Preserve V8U through V9Y and formulate a precise, unsent record request to NIST and/or PANYNJ for the native or highest-resolution versions and release documentation of A-A-148, A-A-150, A-A-151 and A-A-153, including revision and drawing-register context. Do not send the request without explicit user authorization. Preserve categorical topology and all zero-credit gates.
