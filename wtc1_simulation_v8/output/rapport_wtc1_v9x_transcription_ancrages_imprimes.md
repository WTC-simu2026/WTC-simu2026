# WTC 1 - V9X - provenance et transcription bornee des ancrages imprimes des escaliers

**Validation generale : PASS**

> PASS DOCUMENTAIRE CONSERVATEUR - ZERO CHAINE COTEE ACCEPTEE - ZERO ANCRAGE NUMERIQUE FERME - PAS AS-BUILT - ZERO CREDIT PHYSIQUE

## Conclusion

V9X est PASS comme audit documentaire reproductible, mais la porte geometrique reste fermee. Les dix TIFF cibles sont identiques aux fichiers distribues par le ZIP nistreview archive et par l'item Internet Archive actuel. Les sept vues d'ensemble Marsh des niveaux 93 a 99 portent visiblement un cachet RECORD DRAWING et corroborent une topologie a trois escaliers. En revanche, aucune des douze tentatives feuille-escalier ne fournit une chaine complete dont les chiffres et les extremites de cote soient a la fois lisibles et reproductibles. Aucune valeur n'est devinee, aucune coordonnee n'est creee et aucune geometrie V9T/V9U n'est modifiee.

## 1. Faits directement observes ou transcrits

- A-A-148, A-A-150, A-A-151 et A-A-153 affichent Stair 1, Stair 2 et Stair 3 ainsi que des bulles numerotees de colonnes du noyau.
- A-A-125 porte le titre Stair Sections - Stair 1 and 2; A-A-126 porte Stair Sections - Stair 2 and 3. Ces sections ne recoivent aucun credit de localisation horizontale.
- Une photographie d'ensemble ciblee pour chacun des niveaux 93 a 99 affiche l'identifiant du niveau, un cachet RECORD DRAWING et trois cages ou symboles d'escaliers.
- Les photographies sont prises en perspective; aucune echelle pixel n'est exploitee.

## 2. Resultats ou contexte officiel NIST

- NIST indique avoir recu des plans de conception originaux et des plans originaux de fabrication/construction des tours.
- NIST indique aussi qu'un jeu complet de plans as-built n'etait pas disponible et distingue les plans contractuels originaux et leurs revisions.
- Ces declarations generales ne constituent pas un recu NIST au niveau fichier pour les dix TIFF locaux et ne valident aucune coordonnee as-built.

## 3. Affirmations provenant des archives

- L'utilisateur a decrit les plans comme recuperes depuis des ressources NIST via nistreview.org/Internet Archive.
- La chaine binaire locale vers le ZIP nistreview archive et vers l'item Internet Archive actuel est verifiee pour les dix fichiers cibles.
- La page nistreview archivee qualifie explicitement le lot Marsh de diffusion FOIA, mais n'applique pas cette mention a la ligne du ZIP de plans originaux.
- Le PDF Douglas est une critique externe de la simulation NIST, Greening une analyse externe simplifiee, et WTCI-008-S un rapport externe de risque immobilier; aucun n'est une sortie officielle NIST ni une entree geometrique V9X.

### Sources publiques de provenance

- [Item Internet Archive des plans](https://archive.org/details/WTC_Architectural_Drawings_Dated_Aug_31_1967)
- [Page nistreview archivee](https://web.archive.org/web/20110717062822/http://nistreview.org/)
- [Etat de la collecte NIST](https://www.nist.gov/news-events/news/2004/07/status-data-collection-efforts)
- [Limite du jeu as-built dans le document NIST](https://www.nist.gov/system/files/documents/2017/05/09/SunderWTCMediaHandout050703.pdf)

## 4. Hypotheses propres au modele

- Les relations A=upper east, C=upper west et B=lower central restent purement categorielles et servent seulement a la continuite documentaire.
- LOW, BASE et HIGH restent trois placements V9T/V9U separes, explicitement hypothetiques et inchanges.
- Aucune repetition d'un niveau, aucun alignement apparent et aucun cachet RECORD DRAWING ne sont transformes en coordonnee as-built.

## 5. Resultats derives

- Fichiers de plans verifies : 10.
- Vues Marsh ciblees et verifiees : 7.
- Candidats feuille-escalier controles : 12.
- Chaines de cotes numeriques acceptees : 0.
- Jeux d'ancrages de grille fermes acceptes : 0.
- Coordonnees issues des pixels : 0; geometries de modele promues : 0.
- Empreinte de transcription : `c6d8afb9c54daaade606711074fde1089db50b89b2c27fb0540c2926c9fb911e`.

## 6. Contradictions et informations manquantes

- Les superpositions d'annotations, le bruit du scan et l'ambiguite de certaines extremites de lignes de cote empechent un calage numerique unique.
- Une bulle de colonne visible n'est pas, a elle seule, une chaine fermee entre une grille et le contour d'une cage.
- Il manque un recu NIST/FOIA au niveau fichier, une source vectorielle ou lossless plus lisible et une trace de verification de chantier.
- Aucun fait de dommage, aucune masse, rigidite, resistance, connexion ou capacite de chemin de charge n'est deduit de ces plans.

## Portes de validation

- v9w_regression_hashes: PASS
- plan_sources_hashes_and_dimensions: PASS
- plan_sources_unchanged: PASS
- marsh_overviews_hashes_and_dimensions: PASS
- marsh_overviews_unchanged: PASS
- supplemental_pdfs_hashes: PASS
- supplemental_pdfs_unchanged: PASS
- protected_blender_master_unchanged: PASS
- core_transcription_sheet_count: PASS
- supporting_section_sheet_count: PASS
- transcription_candidate_count: PASS
- all_ambiguous_candidates_rejected: PASS
- categorical_stair_relation_count: PASS
- marsh_floor_topology_count: PASS
- record_drawing_stamp_count: PASS
- no_accepted_numeric_dimension_chain: PASS
- no_accepted_closed_grid_anchor_set: PASS
- no_scan_pixel_coordinates: PASS
- no_model_geometry_promotion: PASS
- wayback_plan_distribution_match: PASS
- current_internet_archive_distribution_match: PASS
- wayback_marsh_distribution_match: PASS
- upstream_nist_file_level_provenance_not_overclaimed: PASS
- as_built_status_not_verified: PASS
- variant_separation_retained: PASS
- zero_physical_properties: PASS
- solver_and_blender_prohibited: PASS
- supplemental_pdfs_not_used_for_geometry: PASS

Le Blender maitre conserve son empreinte protegee. Aucun processus Blender et aucun solveur structurel n'ont ete executes.

## Livrables

- Audit de provenance : `wtc1_simulation_v8/output/v9x_plan_provenance_audit.json`
- Transcription bornee : `wtc1_simulation_v8/output/v9x_printed_anchor_transcription.json`
- Matrice CSV : `wtc1_simulation_v8/output/v9x_stairwell_anchor_matrix.csv`
- Porte modele : `wtc1_simulation_v8/output/v9x_stairwell_model_gate.json`
- Planche de controle : `wtc1_simulation_v8/output/v9x_stairwell_anchor_figures/v9x_contact_sheet.png`

## Etape suivante pre-declaree - V9Y

Preserve V8U through V9X and seek only a higher-quality vector or lossless dimensioned record-plan source plus a file-level NIST/FOIA receipt capable of resolving one complete printed grid-to-stair dimension chain for each of Stair 1, Stair 2 and Stair 3. Promote no coordinate unless every digit and endpoint is independently reproducible; otherwise retain only the seven-floor categorical topology. Keep low, base and high separate and hypothetical, assign zero mass, stiffness, strength, connection, damage and load-path credit, do not modify the Blender master, and run neither Blender nor a structural solver.
