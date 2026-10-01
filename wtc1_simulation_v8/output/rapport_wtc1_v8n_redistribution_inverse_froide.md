# WTC 1 - V8N : redistribution froide inverse du noyau

## Resultat principal

La V8N ne generalise pas suffisamment les sorties froides NIST laissees hors calibration. Une concordance sur les points ajustes ne peut donc pas reparer le chemin de charge manquant des V8L/V8M.

Le test leave-one-floor-out donne une erreur absolue moyenne de 45 kip et une erreur maximale de 115 kip sur le changement de charge totale du noyau. Sur les 12 poteaux reserves avant la recherche parametrique, l'erreur DCR moyenne est 0.064 et l'erreur maximale 0.331.

## Faits et resultats officiels

- La Table 4-20 publie les charges totales du noyau avant et juste apres impact, etage par etage.
- Les Figures 4-68 et 4-69 publient les DCR axiaux maximaux des poteaux du noyau entre les niveaux 93 et 99.
- Les capacites NIST utilisent AISC LRFD E2-1 avec K=1 et un facteur de resistance egal a 1; NIST signale une incertitude importante sur demandes et capacites.

## Parametres inverses retenus

- Longueur de transfert equivalente : **0.50 travees de noyau**.
- Exposant de biais vers la capacite : **1.75**.
- Fraction de melange global : **0.00**.
- Biais nord-sud : **-0.30**.

Ces valeurs ne sont ni un module de dalle ANSYS retrouve, ni des proprietes mesurees. Elles forment le jeu de parametres du surrogate qui minimise l'erreur sur les seuls poteaux de calibration.
Parametres places sur une borne de recherche : **global_mixing_fraction=minimum**. Une borne active signale une identification incomplete meme si les seuils predictifs sont franchis.

## Test hors echantillon par etage

| Etage exclu | Delta officiel (kip) | Prediction (kip) | Erreur (kip) |
|---:|---:|---:|---:|
| 93 | -555 | -440 | +115 |
| 94 | -352 | -413 | -61 |
| 95 | -53 | -2 | +51 |
| 96 | 261 | 249 | -12 |
| 97 | 399 | 363 | -36 |
| 98 | 400 | 408 | +8 |
| 99 | 398 | 429 | +31 |

## Test hors echantillon par poteau

| Poteau reserve | DCR officiel | DCR predit | Erreur | Etage gouvernant du surrogate |
|---:|---:|---:|---:|---:|
| 502 | 0.60 | 0.589 | -0.011 | 95 |
| 508 | 0.49 | 0.424 | -0.066 | 95 |
| 605 | 1.20 | 1.292 | +0.092 | 95 |
| 608 | 0.66 | 0.601 | -0.059 | 98 |
| 703 | 0.59 | 0.646 | +0.056 | 95 |
| 708 | 0.41 | 0.378 | -0.032 | 98 |
| 804 | 1.15 | 0.819 | -0.331 | 95 |
| 807 | 0.53 | 0.495 | -0.035 | 98 |
| 903 | 0.48 | 0.482 | +0.002 | 95 |
| 908 | 0.64 | 0.613 | -0.027 | 98 |
| 1002 | 0.45 | 0.479 | +0.029 | 98 |
| 1008 | 0.39 | 0.414 | +0.024 | 98 |

## Hypotheses propres a V8N

- Le profil pre-impact utilise les DCR pre-impact comme prior spatial, multiplie par les capacites froides V8B puis renormalise a la charge officielle de chaque etage.
- La charge des segments retires est repartie par un noyau exponentiel de distance; la fraction de melange global approxime l'action membranaire longue portee omise.
- Les charges totales post-impact suivent une transition logistique a quatre parametres. Sa qualite est testee en excluant successivement chacun des sept etages.
- Les douze poteaux reserves, dont 605 et 804 a DCR officiel eleve, ne participent pas au choix des quatre parametres spatiaux.

## Limites et contradictions

- Le jeu de calibration provient du modele NIST lui-meme; un bon accord demontre seulement que ce surrogate peut emuler certains de ses champs froids.
- La carte DCR donne un maximum sur 93-99 et non une charge numerique par poteau et par niveau. L'etage gouvernant predit reste donc non verifie directement.
- Les rigidites de membrane, sections exactes et fichiers d'entree globaux ne sont pas publies dans les pages exploitees. La V8N ne les reconstitue pas de maniere unique.
- Un echec sur un poteau reserve indique un manque de structure dans le surrogate; il ne constitue ni une contradiction du modele global NIST ni un indice d'explosif.

## Decision du gate

**NON VALIDE.** La redistribution interne inverse reste insuffisamment predictive. La prochaine iteration doit enrichir sa topologie ou retrouver des entrees mecaniques supplementaires avant toute thermique.

Temps d'execution : 27.27 s. Cas spatiaux testes : 2100.
