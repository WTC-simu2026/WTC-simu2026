# WTC 1 — V8Y : rupture non-locale et convergence de l'impulsion

## Résultat

Le portail diagonal V8Y est **PASS**. La matrice auxiliaire est **PASS**. La qualification numérique limitée du sous-ensemble est **PASS**.

L'écart d'impulsion 50–25 mm vaut **8.341%**, pour un seuil inchangé de 10 %. La longueur `LeMAX=100 mm` est un bornage numérique déclaré, pas une longueur de fracture mesurée.

## 1. Faits directement documentés

- La documentation officielle Radioss décrit `/NONLOCAL/MAT` comme une régularisation de la déformation plastique visant la convergence en taille et orientation de maille pour `Le <= LeMAX`.
- La documentation liste `/FAIL/JOHNSON` parmi les critères compatibles et définit l'endommagement accumulé par incréments de déformation plastique.
- Les empreintes et métriques V8W/V8X sont inchangées : **PASS**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats d'un modèle officiel

- Aucun nouveau résultat NIST n'est utilisé comme cible. V8Y compare uniquement des variantes du sous-modèle OpenRadioss.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation d'archive n'est introduite dans cette itération.

## 4. Hypothèses propres au modèle

- La façade réduite, le noyau/capotage équivalent et leurs courbes de contrainte restent ceux de V8W.
- Les déformations de rupture 0,20/0,20/0,12 sont des hypothèses héritées. Elles sont déplacées de LAW2 vers un critère JOHNSON constant, sans recalage sur l'impulsion.
- `LeMAX=100 mm` borne les trois maillages testés mais n'est pas identifié par essais de matériau.

## 5. Résultats dérivés

| Cas | Maille façade (mm) | Maille projectile (mm) | Impulsion (kN·s) | Érosion projectile | Ruptures façade | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|
| NL_M100_P100_DT090_T1 | 100 | 100 | 204.446 | 112 | 345 | -1.275 |
| NL_M050_P050_DT090_T1 | 50 | 50 | 153.224 | 439 | 945 | -0.809 |
| NL_M025_P025_DT090_T1 | 25 | 25 | 141.427 | 1755 | 2913 | -0.636 |
| NL_M050_P050_DT045_T1 | 50 | 50 | 153.302 | 441 | 939 | -0.796 |
| NL_M050_P050_DT090_T4 | 50 | 50 | 153.224 | 439 | 945 | -0.809 |
| NL_M050_P050_DT090_FLO_T1 | 50 | 50 | 151.595 | 711 | 872 | -0.822 |
| NL_M050_P050_DT090_FHI_T1 | 50 | 50 | 161.383 | 158 | 951 | -0.786 |

- Écart impulsion 100–50 mm : **33.430%**.
- Écart impulsion 50–25 mm : **8.341%**.
- Écart moment final 50–25 mm : **1.549%**.
- Portails diagonaux en échec : **aucun**.
- Portails auxiliaires en échec : **aucun**.

## 6. Contradictions et informations manquantes

- Une convergence numérique avec une longueur non-locale heuristique ne valide pas la rupture réelle d'un JT9D, du capotage ou du panneau 124.
- Les courbes de rupture à grande vitesse, la longueur interne physique, le contact arête-arête, les ailes, le carburant, le fuselage et la façade globale restent inconnus ou non qualifiés.
- Le portail global WTC 1, le thermique et Blender restent fermés. Blender demeure une visualisation seulement.
