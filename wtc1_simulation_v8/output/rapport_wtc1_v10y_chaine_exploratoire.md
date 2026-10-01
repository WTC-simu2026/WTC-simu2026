# WTC 1 — V10Y — première chaîne exploratoire intégrée

**Décision d'intégrité : `PASS_EXPLORATORY_MODEL_INTEGRITY_NOT_PHYSICAL_VALIDATION`**

## Réponse bornée à la question

YES_WITHIN_DECLARED_HYPOTHESES: at least one named scenario progresses to ground using impact-selected damage, localized fire weakening and gravity only. This demonstrates numerical possibility in the reduced model, not historical proof.

Le test n'ajoute ni explosif, ni thermite, ni force imposée vers le bas. Après l'initiation, la seule énergie motrice est la gravité. L'impact intervient par la branche de dommages et l'incendie par la réduction de capacité.

## Trois scénarios lisibles

| Scénario | Impact | Quantile thermique | DCR froid max. | Initiation | Étage | Issue du modèle | Arrêt | Durée verticale (s) |
|:---|:---|---:|---:|---:|---:|:---|---:|---:|
| RESISTANT_ENVELOPE | less_severe | 0.25 | 0.542 | — min | — | NO_INITIATION_WITHIN_THERMAL_WINDOW | — | — |
| CENTRAL_EXPLORATORY | base | 0.55 | 0.683 | 28.83 min | 96 | GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL | — | 18.115 |
| VULNERABLE_ENVELOPE | more_severe | 0.80 | 0.905 | 5.33 min | 95 | GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL | — | 13.274 |

## Grille de sensibilité

La grille contient 729 combinaisons déterministes. Les nombres ci-dessous sont des fréquences de grille, pas des probabilités historiques :

- `GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL` : 288/729 (39.5 % de la grille).
- `INITIATED_THEN_ARRESTED` : 144/729 (19.8 % de la grille).
- `NO_INITIATION_WITHIN_THERMAL_WINDOW` : 297/729 (40.7 % de la grille).

## Bilan d'énergie et reproductibilité

- Résidu énergétique normalisé maximal : 1.076e-16.
- Rejeu déterministe exact : OUI (`2be516f5142091e372fae2aff17726424da4e8729781cea2a989060c49a0e5b0`).
- L'énergie cinétique de l'avion est conservée comme référence d'impact mais n'est jamais réinjectée après l'initiation.

## Ce qui est documenté et ce qui est supposé

Les cas d'impact, les états de dommages du noyau et les enveloppes de température proviennent des transcriptions antérieures du modèle officiel. Les réserves de capacité, la répartition verticale noyau/périmètre, le profil de dommages du périmètre, les masses d'étage et les énergies de résistance sont des hypothèses V10Y explicites.

## Limites décisives

Cette version est un modèle vertical réduit, pas une tour 3D en éléments finis. Elle ne calcule ni rupture détaillée de l'avion, ni incendie CFD, ni assemblages réels, ni flambement local, ni fracture, ni basculement asymétrique. Une issue progressive montre seulement qu'une chaîne cohérente existe dans certaines plages déclarées; une issue arrêtée montre que la conclusion dépend fortement de paramètres encore hypothétiques.

Aucune des 22 exigences documentaires mécaniques n'est déclarée satisfaite par cette substitution exploratoire.
