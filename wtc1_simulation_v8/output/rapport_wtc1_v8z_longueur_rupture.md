# WTC 1 — V8Z : identifiabilité de la rupture et sensibilité numérique de LeMAX

## Résultat

Le portail à maille 50 mm est **FAIL**. La matrice à 25 mm est **NON EXÉCUTÉE**. La robustesse numérique sur `LeMAX=50/100/200 mm` est **FAIL**.

Ce résultat ne constitue pas une identification physique : le portail des paramètres de rupture réels reste **FAIL** et la simulation globale reste fermée.

## 1. Faits directement observés ou transcrits

- NIST NCSTAR 1-3D rapporte des essais mécaniques rapides sur une sélection d'aciers du WTC, avec des essais de traction à 50–500 s⁻¹ et certains essais de compression à des taux supérieurs.
- La documentation Radioss définit `Rlen` comme longueur interne non locale et `LeMAX` comme cible de convergence de maille ; avec `LeMAX`, le solveur calcule automatiquement `Rlen`.
- Les trois PDF officiels contrôlés ont conservé leurs empreintes SHA-256 déclarées : **PASS**.
- Les résultats et scripts V8W, V8X et V8Y gelés sont inchangés : **PASS**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats et choix d'un modèle officiel

- NIST NCSTAR 1-2B décrit des déformations critiques ajustées selon la taille de maille dans ses essais de composants ; il s'agit d'un choix de modèle dépendant de la résolution.
- NIST indique ne pas avoir testé les matériaux structuraux du Boeing 767 et avoir utilisé des propriétés de littérature ouverte, avec des variations de déformation de rupture dans l'étude d'incertitude.
- Ces réglages NIST ne sont pas des mesures directes d'une longueur interne physique transférable au projectile équivalent V8Y.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation provenant de l'archive locale n'est utilisée dans V8Z.

## 4. Hypothèses propres au modèle

- Les longueurs `LeMAX=50/100/200 mm` forment une plage numérique factorielle déclarée avant calcul. Elles ne sont ni des bornes physiques ni ajustées sur l'impulsion.
- La géométrie équivalente, les courbes matériaux et les déformations de rupture 0,20/0,20/0,12 sont héritées de V8Y.
- Le cas V8Y à `LeMAX=100 mm` est réutilisé sans recalcul ni modification.

## 5. Résultats dérivés

| Cas | Source | Maille (mm) | LeMAX (mm) | Rlen solveur (mm) | Impulsion (kN·s) | Érosion projectile | Masse restante | Erreur énergie (%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| LM200_M050_P050_DT090_T1 | V8Z | 50 | 200 | 338.514 | 216.738 | 425 | 0.988 | -0.887 |
| LM100_M050_P050_DT090_T1 | V8Y | 50 | 100 | 169.257 | 153.224 | 439 | 0.988 | -0.809 |
| LM050_M050_P050_DT090_T1 | V8Z | 50 | 50 | 84.628 | 134.731 | 484 | 0.987 | -0.874 |
| LM100_M025_P025_DT090_T1 | V8Y | 25 | 100 | 169.257 | 141.427 | 1755 | 0.988 | -0.636 |

- Écart maximal d'impulsion entre longueurs à 50 mm : **37.837%**.
- Écart maximal de quantité de mouvement finale entre longueurs à 50 mm : **11.954%**.
- Portails moyens en échec : **medium_across_lemax_contact_impulse, medium_across_lemax_projectile_final_momentum**.
- Portails fins en échec : **non évalués**.
- Portails de convergence 50–25 mm en échec : **non évalués**.

## 6. Contradictions et informations manquantes

- Les sources examinées ne fournissent pas de surface de rupture à grande vitesse et triaxialité représentative pour les aciers WTC, le moteur ou le capotage équivalent.
- Elles ne fournissent pas non plus de longueur interne physique utilisable pour identifier `Rlen` ou `LeMAX` dans ce modèle.
- Une éventuelle convergence numérique ne valide donc ni le JT9D, ni l'avion complet, ni l'impact global sur le WTC 1.
- Les portails global, thermique et Blender restent fermés. Blender demeure uniquement une visualisation. Aucun résultat V8Z ne teste un mécanisme explosif ou thermitique.
