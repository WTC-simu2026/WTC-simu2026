# WTC 1 - V8P : etats nodaux et graphe vertical

## Resultat principal

V8P ajoute les donnees nodales verticales absentes des iterations precedentes, mais le chemin froid reste non valide sur les criteres declares.

Les Figures 4-60 et 4-61 fournissent 329 etats avant impact et 329 etats apres impact. Chaque valeur reste un intervalle de contour; aucune fausse precision ponctuelle n'est introduite.
Le controle independant au niveau 98 avec la carte de bulles V8O place 97.9% des charges dans l'intervalle de contour correspondant.

## Faits officiels utilises

- Figures 4-60 et 4-61 : contours de charge axiale le long des 47 lignes de poteaux du noyau avant et apres impact.
- Table 4-20 : totaux de charge du noyau a chaque niveau 93-99.
- Figure 4-69 : DCR axial maximal 93-99, utilise seulement apres le choix des parametres.

## Controle de la numerisation

| Etat | Segments absents affiches |
|---|---:|
| Avant impact | 0 |
| Apres impact | 23 |

Les totaux officiels appartiennent a tous les intervalles agreges : **oui**.

## Graphe vertical

La variation de charge de chaque poteau est decomposee en innovations entre niveaux consecutifs. La sommation descendante reconstruit exactement l'etat du poteau et impose la continuite verticale par construction.

- Longueur est-ouest : **0.50 travee(s)**.
- Longueur nord-sud : **1.50 travee(s)**.
- Longueur verticale : **4.00 etage(s)**.
- Exposant de similarite de capacite : **1.00**.
- Jeux de parametres testes : **648**.
- Cas quasi equivalents : **101**.
- Parametres en butee de grille : **transfer_length_x_bays=minimum, vertical_length_floors=maximum, capacity_similarity_exponent=maximum**.

## Validation reservee 705 / 804 / 605

- Couverture des 21 intervalles : **14.3%**.
- Distance moyenne hors intervalle : **385.5 kip**.
- MAE par rapport aux milieux de classe : **474.3 kip**.
- Erreur ponctuelle maximale : **1203.5 kip**.
- Dispersion maximale des predictions quasi equivalentes : **388.2 kip**.

| Poteau | Couverture des 7 intervalles | MAE milieu (kip) | Biais (kip) |
|---:|---:|---:|---:|
| 705 | 28.6% | 169.4 | -164.8 |
| 804 | 14.3% | 387.6 | -387.6 |
| 605 | 0.0% | 865.9 | -865.9 |

| Poteau | DCR officiel | DCR predit | Erreur |
|---:|---:|---:|---:|
| 705 | 0.67 | 0.478 | -0.192 |
| 804 | 1.15 | 0.497 | -0.653 |
| 605 | 1.20 | 0.405 | -0.795 |

## Hypotheses propres a V8P

- Un pixel couleur a un niveau donne represente seulement l'intervalle de sa classe ANSYS.
- L'absence locale de segment colore est convertie en charge nulle et conservee comme drapeau distinct.
- Le champ d'innovation est interpole; aucune rigidite de dalle, loi d'assemblage ou rotation nodale reelle n'est identifiee.
- Les poteaux endommages restent des conditions de bord connues. Les trois poteaux reserves ne participent jamais au choix des parametres.

## Limites et identifiabilite

- 101 combinaisons restent quasi equivalentes sur les seules donnees d'apprentissage.
- Les contours sont larges et les panneaux de chaque serie utilisent une echelle differente; les milieux de classe ne sont pas des mesures exactes.
- Toutes les cibles proviennent du meme modele global NIST. Une bonne prediction est une coherence entre sorties, pas une validation independante.
- Aucun resultat ne constitue une probabilite de l'evenement ou un test distinctif d'explosifs.

## Decision du gate

**NON VALIDE.** Le graphe vertical ne satisfait pas tous les seuils reserves ou les controles de numerisation.

Temps d'execution : 49.23 s.
