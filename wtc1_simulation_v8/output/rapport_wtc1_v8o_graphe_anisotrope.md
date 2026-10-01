# WTC 1 - V8O : carte vectorielle et redistribution anisotrope

## Resultat principal

La V8O mesure proprement la carte vectorielle et identifie une redistribution directionnelle, mais celle-ci ne generalise pas suffisamment toutes les sorties DCR laissees hors identification. Le chemin froid reste donc non valide.

La mesure vectorielle retrouve 47 cercles avant impact et 47 apres impact. Sur les blocs de lignes exclus successivement, le noyau anisotrope predit les charges individuelles avec une MAE de 68 kip et une erreur maximale de 305 kip.
Sans reutiliser les DCR pour choisir les parametres, la prediction croisee des 38 DCR donne une MAE de 0.059 et une erreur maximale de 0.359. Pour le poteau 804 : officiel 1.15, predit 0.823.

## Faits et resultats officiels

- Les Figures 4-64 et 4-65 representent les charges axiales des poteaux au niveau 98 avant et apres impact.
- La Table 4-20 fixe les totaux du noyau a 34 029 kip avant impact et 34 429 kip apres impact.
- La Figure 4-69, conservee hors identification du noyau, fournit les DCR maximaux entre les niveaux 93 et 99.

## Controle de la numerisation

La calibration directe par la legende produirait 58204 kip apres impact, contre 34 429 kip dans la table, soit un facteur correctif 0.592. Les diametres relatifs sont coherents, mais l'echelle absolue de la figure et le total publie ne le sont pas. V8O normalise donc les aires relatives au total tabule et ne pretend pas extraire des charges absolues independantes de la table.

## Parametres anisotropes retenus

- Longueur est-ouest Lx : **1.50 travee(s)**.
- Longueur nord-sud Ly : **1.00 travee(s)**.
- Exposant de capacite : **0.50**.
- Biais directionnel est-ouest : **+0.00**.
- Biais nord-sud du gain net : **+0.30**.
- Bornes actives : **capacity_bias_exponent=minimum**.

## Validation spatiale de la carte Floor 98

| Bloc exclu | Poteaux testes | MAE (kip) | Erreur max (kip) |
|---|---:|---:|---:|
| A_rows_5_8 | 10 | 93 | 305 |
| B_rows_6_10 | 15 | 77 | 265 |
| C_rows_7_9 | 13 | 38 | 142 |

## Plus grandes erreurs DCR entre figures

| Poteau | DCR officiel | DCR predit | Erreur | Etage gouvernant |
|---:|---:|---:|---:|---:|
| 705 | 0.67 | 1.029 | +0.359 | 95 |
| 804 | 1.15 | 0.823 | -0.327 | 95 |
| 605 | 1.20 | 0.886 | -0.314 | 95 |
| 603 | 0.95 | 0.730 | -0.220 | 95 |
| 606 | 0.93 | 0.729 | -0.201 | 95 |
| 905 | 0.78 | 0.657 | -0.123 | 95 |
| 703 | 0.59 | 0.668 | +0.078 | 95 |
| 906 | 0.53 | 0.575 | +0.045 | 95 |
| 701 | 0.48 | 0.438 | -0.042 | 95 |
| 806 | 0.50 | 0.540 | +0.040 | 95 |

## Hypotheses propres a V8O

- Les differences de charge des neuf poteaux marques endommages servent de conditions sources pour identifier la direction de redistribution au niveau 98.
- La charge liberee suit un noyau exponentiel anisotrope; les capacites froides V8B biaisent les destinations.
- Les parametres identifies au niveau 98 sont transferes sans recalibration aux retraits de segments par etage et au calcul des DCR 93-99.
- La courbe de charge totale et le prior pre-impact proviennent de V8N; V8O ne constitue donc pas une reconstruction autonome.

## Limites et contradictions

- L'incoherence entre la legende graphique et le total tabule interdit de traiter les rayons comme une mesure absolue sans normalisation.
- Les cartes de bulles et de DCR proviennent du meme modele NIST. Une prediction croisee reussie serait plus exigeante qu'un ajustement direct, mais resterait dependante des memes entrees officielles.
- Le noyau anisotrope reste scalaire : rotations, flexion biaxiale, P-delta, dalle fissuree et assemblages reels ne sont pas resolus.
- Aucun resultat V8O ne constitue une probabilite de l'evenement ou un test distinctif d'explosifs.

## Decision du gate

**NON VALIDE.** La topologie anisotrope issue de la carte Floor 98 ne generalise pas suffisamment la carte DCR 93-99. Il faut davantage de donnees nodales ou un modele de plancher/assemblage explicite.

Temps d'execution : 3.14 s. Jeux de parametres testes : 3600.
