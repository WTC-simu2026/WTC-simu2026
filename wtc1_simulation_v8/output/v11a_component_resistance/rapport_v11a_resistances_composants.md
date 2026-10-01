# WTC 1 — V11A : résistances individuelles et travée de plancher

## Résultat utilisable

V11A ajoute une bibliothèque mécanique exécutable pour la zone 93–99 : **329 tronçons de colonnes du noyau** (47 × 7), **553 liaisons candidates de poutres** (79 × 7), **15 familles d'appuis** et **192 variantes d'une travée de plancher**. Chaque composant porte son identifiant, ses unités, sa source ou son statut d'hypothèse. Les calculs portent sur les efforts, rigidités et premiers seuils nominaux, pas sur une simple résistance unique par étage.

Cela ne signifie pas que chaque poutre et chaque plancher réels du WTC1 sont identifiés. Les sections des colonnes proviennent d'une transcription des plans ; toutes les affectations de sections aux poutres restent estimées. Les sept niveaux pointent vers une bibliothèque de travées : ils ne reçoivent pas un nombre inventé de treillis ni une implantation complète supposée exacte.

Les composants sont ici supposés intacts : aucun dommage d'impact ni rupture antérieure d'assemblage ne leur est appliqué. Les températures imposées servent à comparer leurs propriétés, sans représenter une histoire thermique localisée.

La demande récente de Jeremy donne priorité à ce sous-modèle de composants. Les corrections globales V10Y déjà signalées (temps/résistance pendant le premier déplacement, demi-plancher de masse manquant, arrivée au sol avec énergie résiduelle) restent à effectuer ; V11A ne les déclare pas résolues et ne modifie pas V10Y/V10Z.

## 1. Faits directement transcrits ou vérifiés

Les six pages déclarées ont été rendues puis lues visuellement. Les avertissements de substitution de polices du lecteur PDF n'empêchaient pas la lecture des tableaux et dimensions ; les images sont conservées dans `source_pages/`.

- [NIST NCSTAR 1-6C](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6c.pdf), PDF 117–118, pages imprimées 69–70 : description de C32T1 au plancher 96, colonne extérieure 143 ; portée 713 in, bande de dalle 40 in par treillis, double cornière supérieure 2 × 1,5 × 0,25 in, inférieure 3 × 2 × 0,37 in, diagonales rondes 1,09 ou 1,14 in.
- La dimension verticale de 29 in du schéma est utilisée comme distance nodale approximative ; les centres réels des cornières ne sont pas redéterminés. La dalle du modèle détaillé fait 4,35 in équivalents, contre 4,3 in arrondis dans le rapport d'ensemble. La dalle n'est pas confondue avec la seule épaisseur supérieure de béton de 4 in.
- [NIST NCSTAR 1-6](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6.pdf), PDF 156–158, pages 74–76, et PDF 167, page 85 : tableaux d'appuis, géométrie et charge morte + exploitation de référence de 80 psf. La réaction calculée pour une paire de treillis de 713 in est 15,844 kip à chaque appui, proche des 16 kip arrondis dans le texte. La charge inclut déjà le poids propre ; aucun poids propre additionnel n'est ajouté.

Conversions gardées dans le code et les données : 1 in = 0,0254 m ; 1 ft = 0,3048 m ; 1 kip = 4 448,221615 N ; 1 ksi = 6,894757 MPa ; 80 psf = 3,830421 kPa. La portée de 713 in vaut 18,1102 m.

## 2. Résultats de modèles officiels réutilisés

Les capacités d'appui ne sont pas des mesures de résistance de tous les appuis réels : ce sont les résultats calculés du NIST pour des détails types. Les tableaux verticaux intérieurs/extérieurs de V8G sont conservés. V11A ajoute la transcription complète des capacités horizontales extérieures du tableau 4-5 ; l'augmentation de 100 à 138 kip entre 20 et 100 °C du détail 1013 est conservée, sans correction arbitraire.

Les deux directions de sollicitation restent distinctes. Leur interaction n'est pas inventée. Le modèle de travée, avec un appui roulant horizontal, ne mobilise pas les capacités horizontales et ne vérifie pas les poussées thermiques ni l'arrachement par chaînette.

Pour les poutres, 119 liaisons des sept niveaux reprennent le sous-réseau de connexions de moment du modèle NIST. Les 434 autres liaisons proviennent de l'enveloppe orthogonale hypothétique antérieure. L'absence d'une liaison dans le sous-réseau NIST n'est pas interprétée comme l'absence de charpente réelle.

## 3. Informations provenant des archives locales

Les 47 nomenclatures du noyau sont reprises de `core_sections_impact_zone.json` : Drawing Book 3, feuilles 3-A1-2 à 3-A1-48, bandes 95–92, 98–95 et 101–98. Cette transcription manuelle conserve ses pages d'origine et son besoin de seconde lecture indépendante. Les propriétés des profils WF proviennent de la base historique AISC, édition ASD7 utilisée comme proxy ; les caissons sont reconstruits à partir des plaques transcrites. Aucun nouvel examen de l'archive source n'a été lancé.

Les coordonnées du noyau conservent leur incertitude de plan estimée à ±0,30 m. Les hauteurs viennent du calendrier hétérogène existant : le sommet de référence reste 416,9664 m, et non 110 fois une hauteur uniforme. Les raccords de colonnes sont encore alignés aux niveaux dans le prototype ; les vrais décalages de joints restent inconnus.

## 4. Hypothèses propres au modèle

### Colonnes et poutres

Les colonnes ont une rigidité EA/L et des écrans de compression : écrasement A·Fy, Euler, puis courbe nominale de flambement flexionnel déjà employée en V8B (forme E3). K = 0,7 / 1 / 2 est balayé. La forme est traçable dans [AISC 360-16, chapitre E3](https://www.aisc.org/globalassets/aisc/publications/standards/a360-16w-rev-june-2019.pdf), mais son usage ici n'est ni un calcul réglementaire historique ni une vérification incendie. Flambement local/torsionnel, imperfections, interactions flexion-compression et assemblages ne sont pas vérifiés.

Chaque poutre candidate possède sa longueur reconstruite et trois sections alternatives : 12WF65 / 14WF136 / 14WF228. Les moments élastique/plastique, le cisaillement idéal de l'âme et la rigidité relative 12EI/L³ sont calculés séparément. Les facteurs d'assemblage 0,5 / 1, le durcissement 1 % et la rotation de rupture 0,02 rad sont explicitement hypothétiques. Le déversement et la mécanique des boulons/soudures restent absents. Le travail d'un ressort isolé est exporté pour audit mais reçoit **zéro crédit d'énergie de résistance globale**.

Le module d'Young est évalué seulement entre 20 et 600 °C. Toute demande au-delà est rejetée. La réduction de limite d'élasticité est normalisée à 20 °C. Les quatre températures sont imposées, pas calculées par une simulation d'incendie.

### Treillis et dalle

Le solveur est un treillis plan linéaire à barres axiales, appui articulé + rouleau. Il utilise une disposition Warren idéalisée, 12 / 16 / 20 panneaux : c'est une sensibilité à la disposition physique, pas une convergence de maillage du treillis réel. Les panneaux d'extrémité, encastrements et soudures ne sont pas reconstruits exactement. Les deux nuances 36 / 50 ksi sont des hypothèses ; la nuance du matériau des poutres du noyau n'est pas transférée silencieusement aux treillis.

La portée de 433 in est une seconde hypothèse de travée courte issue de V8M ; lui affecter les mêmes cornières que C32T1 n'est pas une transcription du véritable treillis court. Les calculs à 1,09 / 1,14 in utilisent un diamètre uniforme ; la distribution réelle des deux diamètres n'est pas connue.

La dalle est soit absente mécaniquement, soit parfaitement liée, comprimée et supposée maintenir la membrure supérieure contre le flambement. Dans le second cas, seul son EA axial en compression est ajouté à la membrure supérieure. Module, résistance en compression et leur réduction thermique sont des hypothèses déclarées (2 500 ksi et 3 ksi à 20 °C). Aucune résistance en traction, flexion de dalle, poinçonnement, dalle fissurée, armatures, bac acier, goujons ou « knuckles » n'est ajoutée. Le partage acier/béton est vérifié. Le cas idéal est donc une limite de modèle, pas une affirmation que la dalle reste liée après l'impact.

Pour les barres comprimées, le minimum écrasement/Euler est un écran idéal. Il ne reproduit pas le flambement inélastique ou local. Les courbes s'arrêtent au premier seuil nominal sous augmentation proportionnelle de la pesanteur ; aucune solution après ce seuil n'est produite.

## 5. Résultats dérivés

### Exemples de colonnes au niveau 96

À 20 °C, K = 1, écran nominal de flambement uniquement — **pas des charges admissibles réelles** :

| Colonne | Section transcrite | Écran nominal (MN) |
|---|---|---:|
| 501 | 14WF426 | 21.867 |
| 704 | 14WF53 | 2.323 |
| 804 | 12WF79 | 3.314 |
| 1008 | 14WF426 | 21.867 |

La matrice complète contient 3,948 évaluations de colonnes et 13,272 évaluations de poutres. Ces nombres comptent des variantes de paramètres, pas autant de pièces réelles différentes.

### Exemple de travée longue

Portée 713 in, 16 panneaux hypothétiques, Fy supposé 36 ksi, diamètre uniforme 1,09 in. Le tableau emploie les appuis les moins résistants parmi les détails tabulés, à la température considérée :

| Acier (°C) | Dalle | Pression au premier seuil (kPa) | Flèche au seuil (mm) | Famille limitante |
|---:|---|---:|---:|---|
| 20 | acier seul | 3.551 | 66.8 | top_chord |
| 20 | dalle en compression idéale | 6.221 | 49.1 | web |
| 400 | acier seul | 3.097 | 66.8 | top_chord |
| 400 | dalle en compression idéale | 5.425 | 54.9 | web |
| 600 | acier seul | 2.180 | 54.9 | top_chord |
| 600 | dalle en compression idéale | 4.561 | 67.2 | bottom_chord |

Ces valeurs ne sont pas une prédiction de résistance d'un étage réel. Si un treillis sans dalle atteint son écran idéal avant les 80 psf de référence, cela renseigne sur cette hypothèse de contreventement et de liaison, pas sur une faiblesse prouvée du plancher construit. Une grande résistance verticale des appuis ne protège pas automatiquement d'un autre mécanisme : barre comprimée, perte de liaison, poussée horizontale ou instabilité globale.

Sur les 192 variantes, 150 restent sous le premier seuil à la charge de référence et 42 ont un essai élastique au-delà de ce seuil. Ces comptes décrivent seulement la grille déclarée ; ils ne sont **jamais des probabilités historiques**. Chaque variante teste les 56 combinaisons de détails d'appuis, sans en sélectionner une par ressemblance à la chronologie.

### Vérifications numériques

43/43 contrôles passent, dont un treillis triangulaire à solution analytique indépendante, le travail virtuel/énergie élastique, les unités, la charge nulle, les bandes de sections, la connectivité du catalogue, la duplication d'un treillis vers une paire, les réactions et la répétition déterministe exacte.

- Résidu relatif maximal d'équilibre : 6.865e-14.
- Résidu relatif maximal d'énergie élastique : 2.763e-13.
- Durée d'exécution et répétition : 2.36 s. NumPy 2.4.6, Python 3.14.3, calcul CPU ; aucune installation, aucun calcul GPU ou Blender.

Ces contrôles valident l'exécution de ce sous-modèle, pas sa fidélité complète au bâtiment ni la cause historique de l'effondrement.

## 6. Contradictions, limites et suite

Le détail 4,35/4,3 in est une différence de représentation/arrondi dans deux rapports, pas une preuve de deux planchers différents. Les dimensions de profils historiques et les joints de colonnes gardent leurs limites de transcription. Le nombre et l'implantation réelle des travées, les poutres porteuses de rive du noyau, le ferraillage et les ouvertures ne sont pas remplacés par une grille déclarée exacte.

Restent : nomenclature des façades et allèges, assemblages complets, transferts dalle–poutres–colonnes, rupture des soudures/goujons, cisaillement et flexion de dalle, dilatation, gradients thermiques, fluage, flambement non linéaire et redistribution après rupture. La maquette Blender V10Z reste inchangée et ne reçoit aucune de ces capacités comme si le couplage était déjà validé.

Prochaine V11B : corriger explicitement l'initialisation et l'inventaire de masse du calcul global V10Y, sans recalibrer ses scénarios sur la chronologie ; conserver l'arrêt comme issue possible. Ensuite construire un panneau de plancher avec liaisons à raideur/rupture explicites et vérifier son comportement froid avant tout couplage progressif à la tour. Aucune conclusion « effondrement nécessaire » ou « impossible » ne découle de V11A.

## Livrables

- `component_inventory.json` : identifiants, sections, géométrie, sources et statuts.
- `column_capacities.csv` et `core_beam_capacities.csv` : capacités individuelles et variantes.
- `seat_capacities.csv` : appuis verticaux et horizontaux, unités originales et SI.
- `floor_bay_cases.csv`, `floor_bay_members.csv`, `floor_bay_seat_pairs.csv` : solutions et premiers seuils par composant.
- `floor_bay_force_displacement.csv` : courbes de chargement arrêtées au premier seuil.
- `source_manifest.json`, `numerical_audit.json`, `offline_manifest.json` : traçabilité, contrôles et empreintes.
- `synthese_v11a_composants.png` : vue de contrôle, avec hypothèses visibles.
