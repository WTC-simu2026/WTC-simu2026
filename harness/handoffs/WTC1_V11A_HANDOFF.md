# Reprise WTC 1 après V11A

Lire intégralement AGENTS.md et l'état autoritatif `harness/state.json`, puis lancer `harness/tools/Test-WtcHarness.ps1` depuis le dossier actif. Ne pas reprendre à partir de l'ancien point V8H ou V10J et ne pas relire toute l'histoire.

## Demande et périmètre

Jeremy a demandé si les résistances de chaque poutre et plancher étaient présentes et a autorisé la poursuite vers une structure plus réaliste. Réponse exacte : V10Y/V10Z restaient agrégées ; des bibliothèques V8 existaient mais n'alimentaient pas l'animation. V11A a priorisé une bibliothèque de composants et une travée calculable, avec hypothèses admises par Jeremy. Ne pas transformer à nouveau les documents manquants en condition empêchant tout prototype.

V11A est terminée. Prochaine V11B : corriger le raccord global V10Y (masse, début du déplacement avec résistance et temps, état terminal), sans recalibrage sur la chronologie. Le passage à V11A composant a été explicitement déclaré dans sa configuration ; il n'a pas effacé ces corrections.

## Livrables de V11A

Dossier : `wtc1_simulation_v8/output/v11a_component_resistance/`.

- `rapport_v11a_resistances_composants.md` et `results_v11a.json` : résultat et limites.
- `component_inventory.json` : 376 nœuds, 329 tronçons de colonnes (47 × 7, F93→F94 jusqu'à F99→F100), 553 poutres candidates (79 × 7).
- `column_capacities.csv` : 3 948 évaluations (températures 20/200/400/600 °C, K 0,7/1/2).
- `core_beam_capacities.csv` : 13 272 évaluations ; trois profils et deux facteurs d'assemblage ; aucune section de poutre n'est une affectation as-built.
- `seat_capacities.csv` : 15 détails × 11 températures ; valeurs verticales/horizontales pour une paire de treillis, pas un seul.
- `floor_bay_cases.csv`, `floor_bay_members.csv`, `floor_bay_seat_pairs.csv`, `floor_bay_force_displacement.csv` : 192 variantes, 12 096 évaluations de barres et 10 752 comparaisons de paires d'appuis.
- `synthese_v11a_composants.png`, `source_pages/`, `source_manifest.json`, `numerical_audit.json`, `offline_manifest.json`, `release_audit.json`.

Code : `wtc1_simulation_v8/scripts/v11a_component_model.py` et `run_v11a_component_resistance.py`. Configuration : `data/v11a_component_resistance_predeclaration.json`. Python 3.14.3 à `C:/Python314/python.exe`, NumPy 2.4.6 et Pillow. L'exécution complète et sa répétition déterministe prennent environ 2,4 secondes ; aucun solveur externe/GPU/Blender. Le script refuse un dossier de sortie déjà existant : pour un test utiliser un nouveau sous-dossier de `tmp/v11a_component_resistance/`, ne jamais écraser la version livrée.

## Sources et statuts à préserver

Les 47 sections du noyau sont des transcriptions manuelles du Drawing Book 3 (seconde vérification indépendante encore manquante), propriétés historiques AISC avec proxy ASD7, coordonnées reconstituées ±0,30 m. La convention de bandes suit V8B : F93/94 → 95–92 ; F95/96/97 → 98–95 ; F98/99 → 101–98. Les joints ne sont pas localisés dans les étages. Le sommet de référence de la géométrie hétérogène reste 416,9664 m.

119 liaisons de poutres reprennent le sous-réseau de connexions de moment du modèle NIST ; 434 sont l'enveloppe orthogonale hypothétique. Les profils 12WF65 / 14WF136 / 14WF228, coefficients 0,5/1 et rotation de rupture 0,02 rad restent des hypothèses. Capacité d'une force et travail d'un ressort isolé ne donnent aucune énergie de résistance d'étage : zéro crédit global explicite.

Six pages de copies officielles ont été rendues et vérifiées : NCSTAR1-6 PDF156/157/158/167 et NCSTAR1-6C PDF117/118. La dernière confirme C32T1, portée 713 in, 40 in de dalle par treillis, double L supérieur 2×1,5×0,25 in, inférieur 3×2×0,37 in, diagonales Ø1,09/1,14 in. La dimension de schéma 29 in est utilisée comme séparation nodale approximative, pas comme relevé exact des centres de profils. Dalle équivalente 4,35 in dans 1-6C versus 4,3 dans l'aperçu 1-6.

Le tableau 4-5 des capacités horizontales extérieures a été ajouté intégralement. Son détail 1013 passe de 100 à 138 kip entre 20 et 100 °C : conserver cette non-monotonie publiée. Aucune loi mixte V-H n'est disponible. Ne pas appliquer une résistance en traction à une poussée de compression.

## Modèle de travée et vérifications

Treillis plan linéaire à appuis articulé/roulant ; barres axiales, Warren idéal. 713/433 in × 12/16/20 panneaux × quatre températures × Fy hypothétique 36/50 ksi × diamètre uniforme 1,09/1,14 in × acier seul/dalle comprimée parfaitement liée = 192 cas. Affecter C32T1 à la portée courte est une extrapolation explicite. Le nombre de panneaux change la structure physique ; ce n'est pas une étude de convergence de maillage.

La dalle idéale ajoute son EA à la membrure supérieure, partage sa compression et la maintient contre le flambement. Ec, fc et réductions thermiques sont hypothétiques. Pas de résistance ajoutée en flexion/traction de dalle, armatures, poinçonnement, bac, soudures, knuckles, goujons. Pas d'impact appliqué, pas de fluage, dilatation ou déplacement d'appui. Composants intacts de référence ; l'histoire thermique réelle reste à coupler.

La charge de référence de 80 psf inclut déjà le poids propre. Pour 713 in, une paire reprend 31,689 kip, soit 15,844 kip par siège, comparés aux capacités de siège COMPLET. Ne pas diviser par deux une seconde fois ni doubler le poids propre. La solution s'arrête au premier écran nominal sous charge proportionnelle. Le minimum Euler/écrasement des barres comprimées est un écran idéal, pas du flambement non linéaire. Une sortie « service trial exceeds first limit » n'est pas une simulation de la réponse après rupture.

43/43 contrôles passent, dont triangle analytique, énergie, unités, invariance des efforts du treillis isostatique, connexité/topologie, massification d'une paire et répétition exacte. Résidus max : équilibre 6,8651e-14, énergie 2,7633e-13. Parmi ces variantes seulement, 150 sont sous leur premier seuil à 80 psf et 42 au-delà ; aucune fréquence n'est une probabilité historique.

Référence longue, 16 panneaux, Fy36, Ø1,09 : premiers seuils (kPa) acier seul/dalle idéale = 3,551/6,221 à 20 °C ; 3,097/5,425 à 400 °C ; 2,180/4,561 à 600 °C. Ce ne sont pas des résistances réelles d'étages. Au froid le cas nu manque de contreventement par dalle ; ne pas en déduire que le plancher construit ne pouvait porter son poids.

Le polynôme E(T) est bloqué au-dessus de 600 °C. Le modèle de colonnes reprend la forme nominale E3 mais ne vérifie ni éléments minces, torsion, joints, imperfections ni conformité incendie.

## Raccord global encore nécessaire (V11B)

V10Y/V10Z sont intacts et restent une chaîne agrégée + sa visualisation. Aucun résultat V11A n'a été transféré au film. Points hérités du handoff V10Z :

1. Le pilote GRID-0119 initie à 5 810 s, niveau 96, et commence déjà après 1,8288 m de déplacement avec vitesse. Le temps de ce premier déplacement est absent. Repartir du repos avec résistance active, sans vitesse imposée cachée.
2. Masse finale V10Y = 109,5 étages équivalents : fermer l'inventaire du demi-étage d'initiation restant.
3. Fin à l'arrivée au sol avec 326,16 GJ d'énergie cinétique, pas des débris stabilisés ; expliciter l'état terminal.
4. Recalculer les scénarios inchangés pour comparaison ; ne pas régler pour obtenir l'effondrement ou 102 minutes. Les 729 anciens cas étaient 288 progressants, 144 arrêts, 297 sans initiation.
5. Après ces corrections, panneau structurel avec liaisons réellement déformables/rupturables et validation froide, puis chemins d'efforts spatiaux. Les façades, allèges, poutres porteuses de rive du noyau et disposition réelle de tous les planchers restent à construire.

Empreinte numérique V11A : `4e0ff28266f0d36c135ab6a1307a70731bb895e8d1ef43ccb758265d256b8d7d`. Les manifestes contiennent les empreintes des 21 sorties, 13 entrées/protégés et trois fichiers de code/configuration. Les deux brouillons sont conservés dans `tmp/v11a_component_resistance/attempt01` et `attempt02` ; seule la métadonnée « intact » et six contrôles ont été enrichis après attempt01, les résultats mécaniques n'ont pas changé.
