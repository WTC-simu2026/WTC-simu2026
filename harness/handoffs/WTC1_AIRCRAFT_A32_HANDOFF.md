# Reprise AIRCRAFT-A32 → AIRCRAFT-A33

Rapport : wtc1_simulation_v8/output/aircraft_a32/rapport_aircraft_a32.md
Résultats : wtc1_simulation_v8/output/aircraft_a32/composite_qualification_review.json
Diagnostic : wtc1_simulation_v8/output/aircraft_a32/surface_bending_extended_diagnostic.json

AIRCRAFT-A33 : tester une peau TYPE6/Isolid24 à plusieurs cellules physiques dans l’épaisseur, faces seules chargées et intérieur libre, avec la référence continuum indépendante A32 désormais raffinée. Déclarer avant les sorties les contrôles de flexion, inertie libre, affine transverse et raffinements; conserver les quatre échecs A32. Puis tester la transmission du sandwich et les prises courbes avant insertion entière. Aucun ajout de masse, changement de densité ou terme RKE artificiel. LAW12 et ses coefficients transverses restent des hypothèses élastiques; résistance, décollement et rupture historiques non identifiés. L’implicite du binaire installé réclame MUMPS; aucune installation ou modification de solveur autorisée ou effectuée. Meilleur impact entier A20=20ms, objectif vidéo3D10secondes physiques incomplet. Publication suivante A32+A33 après vérification.
