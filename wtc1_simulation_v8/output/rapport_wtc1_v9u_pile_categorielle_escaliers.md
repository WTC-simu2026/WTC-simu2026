# WTC 1 - V9U - pile catégorielle hypothétique des escaliers, niveaux 93 à 99

**Validation générale : PASS**

> PILE CATÉGORIELLE HYPOTHÉTIQUE — AUCUNE GÉOMÉTRIE AS-BUILT — ZÉRO CRÉDIT MÉCANIQUE — PAS DE VALIDATION PHYSIQUE

## Conclusion

La continuité documentaire V9R autorise une pile catégorielle de sept niveaux pour A, C et B : les 21 lignes étage/cage indiquent que les cages sont présentes, qu'elles continuent et qu'aucun transfert n'est listé entre 93 et 99. Cette décision ne qualifie pas une répétition géométrique réelle. Les variantes LOW, BASE et HIGH restent trois hypothèses séparées.

## 1. Faits directement observés ou transcrits

- V9R contient 21 lignes pertinentes : sept niveaux multipliés par trois cages.
- Toutes portent `CONTINUES`, `present_in_reported_vertical_extent=true` et `transfer_event=NONE`.
- Deux bandes documentaires couvrent la cible : 83-95 et 96-102; dans V9U elles apparaissent respectivement sur 93-95 et 96-99.
- La seule superposition étiquetée par étage dans ce jeu est celle du niveau 95; aucune ligne des six autres niveaux n'en revendique une.

## 2. Résultats d'un modèle officiel

Les bandes proviennent de panneaux schématiques NIST et la superposition du niveau 95 d'une figure du modèle officiel. Ce ne sont ni des relevés indépendants ni des plans d'exécution cotés. Le changement de bande entre 95 et 96 est conservé explicitement.

## 3. Affirmations provenant des archives locales

Aucune. L'archive source n'a été ni ouverte ni rescannée.

## 4. Hypothèses propres au modèle

- Pour chaque variante, les coordonnées normalisées V9T du niveau 95 sont répétées comme marqueurs catégoriels aux niveaux 93 à 99.
- Même au niveau 95, LOW, BASE et HIGH restent des ajustements relatifs hypothétiques, pas une géométrie observée.
- L'espacement vertical des planches est seulement graphique. Aucun z, aucune hauteur d'étage et aucune échelle verticale physique ne sont attribués.
- L'absence de transfert listé permet la continuité catégorielle, mais ne prouve pas une identité de plan entre étages.

## 5. Résultats dérivés

- Trois piles séparées de 21 instances chacune; 63 instances hypothétiques au total.
- Frontières de bandes dans la cible : 1; événements de transfert listés : 0.
- Répétitions hors niveau 95 : 54.
- Empreinte déterministe de la pile : `6c97dd0f5315832e7783638d06d85db237b98d6026fb30d2569676b9d3c811c4`.
- Échelle relative héritée : 2.324597826 pixels normalisés par pouce publié; elle n'est pas une conversion physique.

## 6. Contradictions et informations manquantes

- Aucun contour spécifique aux niveaux 93, 94, 96, 97, 98 ou 99 n'est publié dans les artefacts V9R utilisés.
- La frontière 95-96 ne documente pas la transformation exacte entre les deux bandes.
- Les positions, orientations, murs, portes, volées, limons, connexions et hauteurs d'étage as-built restent inconnus.
- Les indications de dommage de la matrice V9R ne sont ni propagées ni converties en dommage de composant dans V9U.

## Portes de validation

- v8u_through_v9t_chained_regression_hashes: PASS
- direct_input_artifact_hashes: PASS
- protected_blender_master_before_after: PASS
- v9t_geometry_layer_pass_and_fingerprint: PASS
- floor_count: PASS
- stairway_count: PASS
- variant_count_and_separation: PASS
- floor_stair_documentary_coverage: PASS
- two_documented_floor_bands_preserved: PASS
- all_three_stairs_documented_continuous: PASS
- no_transfer_event_93_99: PASS
- adjacent_transition_coverage: PASS
- band_boundary_preserved_without_geometry_inference: PASS
- floor95_overlay_not_extrapolated: PASS
- published_landing_dimensions_consistent: PASS
- upstream_metric_and_mechanical_qualifications_closed: PASS
- categorical_stack_instance_count: PASS
- all_placements_explicitly_hypothetical: PASS
- no_physical_vertical_coordinate_or_scale: PASS
- relative_scale_not_physical_conversion: PASS
- zero_physical_properties_and_credit: PASS
- mechanical_solver_blender_gates_closed: PASS
- source_policy_closed: PASS
- figures_created: PASS

Masse, rigidité, résistance, connexion, chemin de charge et crédit de dommage valent explicitement zéro dans V9U. Ces zéros signifient qu'aucun crédit n'est attribué par le modèle; ils ne décrivent pas une absence physique dans la tour.

Aucun solveur et aucun processus Blender n'ont été exécutés. Le fichier Blender maître conserve son empreinte protégée.

## Livrables

- Pile catégorielle : `wtc1_simulation_v8/output/v9u_floor93_99_stairwell_stack.json`
- Audit de continuité : `wtc1_simulation_v8/output/v9u_stairwell_continuity_audit.json`
- Mesures : `wtc1_simulation_v8/output/v9u_stairwell_stack_metrics.csv`
- Porte modèle : `wtc1_simulation_v8/output/v9u_stairwell_model_gate.json`
- Planche de contrôle : `wtc1_simulation_v8/output/v9u_stairwell_stack_figures/v9u_contact_sheet.png`

## Étape suivante pré-déclarée - V9V

Preserve V8U through V9U and perform a cached-source-only sufficiency audit for any floor-specific stairwell plan or offset evidence on Floors 93-99 before any geometry is promoted beyond categorical placeholders. Keep low/base/high separate, retain zero mechanical and damage credit, and do not run Blender or a structural solver unless a later explicitly authorized objective changes those gates.
