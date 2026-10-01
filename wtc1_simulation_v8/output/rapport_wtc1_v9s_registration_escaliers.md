# WTC 1 - V9S - inscription qualitative bornee des emprises d'escaliers au niveau 95

**Validation generale : PASS**

> V9S - ENVELOPPES QUALITATIVES - PAS DE COORDONNEES AS-BUILT - PAS DE VALIDATION PHYSIQUE

## Portee

V9S conserve les regressions V8U a V9R et inscrit deux figures NIST sur un canevas commun de 1000 x 1000 pixels, en utilisant uniquement des reperes visibles du contour du noyau. L'operation sert a borner des positions qualitatives; elle ne cree ni plan as-built metrique, ni geometrie solveur, ni propriete mecanique.

## 1. Faits directement observes ou transcrits

- NCSTAR 1-7, Figure 5-2 (page PDF 112, page imprimee 74) montre au niveau 95 trois emprises visibles etiquetees Stairwell A, C et B sur le panneau propre avant superposition des dommages.
- NCSTAR 1-2B, Figure 9-124 (pages PDF 164-165, pages imprimees 346-347) presente la perturbation des escaliers; sur le panneau Floor 95, les boites numerotees 1 et 3 sont recuperables comme contours fermes.
- Le contour ferme du repere 2 / escalier C n'est pas recuperable sur ce panneau Floor 95. Il n'est ni dessine par extrapolation ni remplace par un autre etage.

## 2. Resultats d'un modele officiel

Les deux figures sont des visualisations de modeles NIST. Elles ne constituent pas deux mesures independantes de la geometrie reelle. La Figure 5-2 montre une etendue d'escalier dans un plan modele; la Figure 9-124 montre des reperes numerotes superposes a un etat de dommage modele.

## 3. Affirmations provenant des archives locales

Aucune affirmation documentaire issue de l'archive source n'est employee dans V9S. L'archive n'a ete ni ouverte ni rescanee; seules les deux copies officielles deja presentes dans l'espace de travail ont ete lues en lecture seule.

## 4. Hypotheses propres au modele

- Les rectangles de reference visibles du noyau sont normalises independamment sur les axes X et Y.
- Une erreur de pointage en pixels est declaree pour chaque contour et chaque bord du rectangle de reference. Les extremes de ces intervalles sont propages vers le canevas commun.
- Aucune echelle physique, rotation as-built, masse, rigidite, resistance, connexion ou chemin de charge n'est infere.

## 5. Resultats derives

- Deux escaliers sur trois sont comparables entre figures, conformement au minimum predeclare (2/2).
- Escalier A : ecart entre centroides = 56.830 px communs, seuil qualitatif = 100.0 px, porte franchie = TRUE.
- Escalier B : ecart entre centroides = 65.924 px communs, seuil qualitatif = 100.0 px, porte franchie = TRUE.
- Les enveloppes A et B sont l'union rectangulaire conservative des deux contours normalises, elargie par la pire incertitude de pointage propagee sur chaque axe.
- L'enveloppe C provient uniquement de la Figure 5-2 et porte le statut SINGLE_FIGURE_ONLY_NO_INTERFIGURE_BOUND.

Ces nombres sont des pixels normalises derives. Ils ne sont pas des pieds, des metres, des coordonnees de noeuds ou une validation d'endommagement.

## 6. Contradictions et informations manquantes

- La seconde figure ne permet pas de fermer l'emprise de C au niveau 95.
- Les semantiques graphiques different entre les deux figures; une superposition n'autorise donc pas un indicateur de recouvrement interprete physiquement.
- Aucun plan as-built cote des trois emprises au niveau 95 n'est qualifie par cette iteration.

## Portes de validation

- regression_hashes: PASS
- source_hashes: PASS
- pdf_anchors: PASS
- rendered_pages: PASS
- analysis_crops: PASS
- figure_5_2_visible_count: PASS
- figure_9_124_visible_count: PASS
- cross_figure_count: PASS
- cross_figure_centroid_distances: PASS
- stair_c_missing_not_guessed: PASS
- mechanical_and_blender_gates_closed: PASS
- source_policy_closed: PASS

Toutes les portes de masse, rigidite, resistance, connexion, chemin de charge, dommage composant, solveur global et validation physique Blender restent fermees.

## Livrables

- Manifeste : `wtc1_simulation_v8/output/v9s_stairwell_registration_source_manifest.json`
- Numerisation : `wtc1_simulation_v8/output/v9s_stairwell_digitization.json`
- Enveloppes : `wtc1_simulation_v8/output/v9s_stairwell_qualitative_envelopes.json`
- Mesures : `wtc1_simulation_v8/output/v9s_stairwell_registration_metrics.csv`
- Porte modele : `wtc1_simulation_v8/output/v9s_stairwell_model_gate.json`
- Planche de controle : `wtc1_simulation_v8/output/v9s_stairwell_registration_figures/v9s_contact_sheet.png`

## Etape suivante predeclaree - V9T

Preserve V8U through V9S and construct a geometry-only three-envelope Floor 95 stairwell layer from the V9S normalized envelopes and the separately published landing dimensions. Generate explicitly hypothetical low, base and high placement variants, verify transform reproducibility and topology/non-overlap only, assign zero mass, stiffness, strength, connection or load-path credit, do not modify the Blender master, and do not run a structural solver.
