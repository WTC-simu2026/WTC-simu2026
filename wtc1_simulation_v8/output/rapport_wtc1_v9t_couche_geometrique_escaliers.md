# WTC 1 - V9T - couche geometrique hypothetique des trois escaliers au niveau 95

**Validation generale : PASS**

> V9T - PLACEMENTS HYPOTHETIQUES - ZERO CREDIT MECANIQUE - PAS DE VALIDATION PHYSIQUE

## Portee

V9T conserve les regressions V8U a V9S et construit neuf rectangles de palier deterministes (trois escaliers x trois placements) dans le canevas qualitatif V9S. Le calcul verifie uniquement la reproduction des transformations, le maintien dans les enveloppes, la topologie et l'absence de chevauchement.

## 1. Faits directement observes ou transcrits

- V9R transcrit des paliers par porte de sortie de 92 x 78 pouces pour A et C, et de 116 x 78 pouces pour B.
- V9S fournit trois enveloppes rectangulaires sur un canevas normalise de 1000 x 1000 pixels, sans echelle physique.
- A et B reposent sur une union qualitative de deux figures; C ne possede qu'une enveloppe issue de la Figure 5-2.

## 2. Resultats d'un modele officiel

Les enveloppes V9S derivent de figures de modeles NIST. Elles ne sont pas des mesures as-built independantes. Les dimensions publiees concernent des paliers par porte de sortie et non l'enveloppe complete de chaque cage.

## 3. Affirmations provenant des archives locales

Aucune. L'archive source n'a ete ni ouverte ni rescanee.

## 4. Hypotheses propres au modele

- A et C conservent le grand cote publie sur l'axe X; B est tourne de 90 degres pour suivre l'enveloppe V9S plus haute que large.
- Une echelle relative commune est le minimum des six capacites enveloppe/dimension. Elle preserve les rapports publies mais n'est pas une conversion physique pixel-pouce.
- LOW place chaque palier au bord inferieur-gauche de l'espace residuel, BASE au centre et HIGH au bord superieur-droit. Ces noms ne sont ni des probabilites, ni des intervalles de confiance, ni une meilleure estimation.

## 5. Resultats derives

- Echelle relative commune : 2.324597826 pixels normalises par pouce publie; controle par C axe x.
- Empreinte deterministe des coordonnees : `eb434c40b98122f1b80e1ccec079439137a2bb201f463fe4283e043200152dcf`.
- Erreur maximale entre deux implementations de la transformation : 0.000e+00 pixel commun.
- Erreur maximale de restitution des dimensions publiees : 2.842e-14 pouce.
- LOW : ecart minimal entre rectangles = 79.207 px; topologie/non-chevauchement = PASS.
- BASE : ecart minimal entre rectangles = 84.157 px; topologie/non-chevauchement = PASS.
- HIGH : ecart minimal entre rectangles = 89.107 px; topologie/non-chevauchement = PASS.

Ces resultats qualifient la coherence interne d'une couche geometrique relative, pas la geometrie reelle des cages ni leur comportement lors de l'impact.

## 6. Contradictions et informations manquantes

- La position metrique exacte et l'orientation as-built ne sont pas disponibles.
- Les rectangles representent uniquement les dimensions publiees de paliers, pas les murs, portes, volees, limons ou connexions.
- La cage C reste fondee sur une seule figure pour son enveloppe qualitative au niveau 95.
- Aucun dommage composant complet des trois cages n'est qualifie.

## Portes de validation

- regression_hashes: PASS
- input_artifact_hashes: PASS
- protected_file_before_after: PASS
- upstream_coordinate_boundary: PASS
- stairway_count: PASS
- variant_count: PASS
- common_scale_rule: PASS
- transform_reproducibility: PASS
- published_dimension_reproduction: PASS
- envelope_containment: PASS
- topology_and_non_overlap: PASS
- positive_pairwise_clearance: PASS
- zero_physical_properties: PASS
- mechanical_and_blender_gates_closed: PASS
- source_policy_closed: PASS
- figures_created: PASS

Masse, rigidite, resistance, connexion, chemin de charge et dommage recoivent explicitement une valeur de credit nulle. Cela signifie absence de credit dans ce modele, pas absence physique dans la tour.

Aucun solveur et aucun processus Blender n'ont ete executes. Le fichier maitre Blender conserve son empreinte initiale.

## Livrables

- Couche : `wtc1_simulation_v8/output/v9t_floor95_stairwell_layer.json`
- Audit des transformations : `wtc1_simulation_v8/output/v9t_stairwell_transform_audit.json`
- Mesures : `wtc1_simulation_v8/output/v9t_stairwell_topology_metrics.csv`
- Porte modele : `wtc1_simulation_v8/output/v9t_stairwell_model_gate.json`
- Planche de controle : `wtc1_simulation_v8/output/v9t_stairwell_geometry_figures/v9t_contact_sheet.png`

## Etape suivante predeclaree - V9U

Preserve V8U through V9T and test whether the geometry-only Floor 95 stairwell layer can be extended across Floors 93-99 using only the published V9R floor-band continuity and transfer topology. Create a categorical seven-floor stack only where continuity is supported, label every repeated placement hypothetical, preserve zero mass, stiffness, strength, connection and load-path credit, do not modify Blender, and do not run a structural solver.
