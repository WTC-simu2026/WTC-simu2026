# WTC 1 — V8X : origine de la sensibilité de maille de l'impulsion

## Résultat

Le diagnostic V8X est **PASS** comme expérience de localisation. Le projectile/façade déformable reste **NON QUALIFIÉ**, car le cas érodant V8W conserve un écart d'impulsion 50–25 mm de **32.866%**, supérieur au seuil inchangé de 10 %.

Le contrôle sans érosion donne un écart 50–25 mm de **1.951%** et son portail est **PASS**. La classification dérivée est : **unregularized_strain_to_failure_erosion**. C'est une inférence limitée à ces sous-modèles, pas un fait sur l'impact réel.

## 1. Faits directement documentés

- La documentation officielle Radioss indique que LAW2 possède un critère intégré de déformation plastique maximale et que sa valeur par défaut est `1e20`. Les cas `N_`/`NC_` utilisent `EPSmax=0`, qui appelle ce défaut et désactive donc pratiquement l'érosion sur la durée testée.
- V8W et ses résultats sont inchangés selon les empreintes et métriques gelées : **PASS**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats d'un modèle officiel

- Aucun nouveau résultat NIST n'est utilisé comme cible. V8X compare seulement des variantes du même sous-modèle OpenRadioss.

## 3. Hypothèses propres au modèle

- La façade trois colonnes par trois étages, le noyau/capotage carrés, les matériaux et les deux contacts pairwise restent ceux de V8W.
- Le contrôle sans érosion n'est pas une loi de rupture réelle ; c'est un cas limite numérique destiné à séparer l'effet de suppression d'éléments de celui de la discrétisation du contact.
- Les seuils ne sont pas recalés sur les résultats : le portail d'impulsion reste fixé à 10 %.

## 4. Résultats dérivés

| Cas exécuté | Maille façade (mm) | Maille projectile (mm) | Mode | Impulsion façade (kN·s) | Éléments érodés | Erreur énergie (%) |
|---|---:|---:|---|---:|---:|---:|
| E_F100_P050 | 100 | 50 | v8w_enabled | 160.927 | 2431 | -1.448 |
| E_F025_P050 | 25 | 50 | v8w_enabled | 63.137 | 4198 | -1.363 |
| E_F050_P100 | 50 | 100 | v8w_enabled | 76.032 | 1362 | -1.555 |
| E_F050_P025 | 50 | 25 | v8w_enabled | 114.600 | 7132 | -1.274 |
| N_F100_P100 | 100 | 100 | law2_default_non_eroding | 357.920 | 0 | -1.356 |
| N_F050_P050 | 50 | 50 | law2_default_non_eroding | 363.524 | 0 | -0.900 |
| N_F025_P025 | 25 | 25 | law2_default_non_eroding | 356.569 | 0 | -0.689 |

### Matrice érodante, variable isolée

- Façade 100/50/25 mm avec projectile 50 mm : **160.927 / 87.608 / 63.137 kN·s** ; écart 50–25 mm **38.759%**.
- Projectile 100/50/25 mm avec façade 50 mm : **76.032 / 87.608 / 114.600 kN·s** ; écart 50–25 mm **23.554%**.

### Contrôle sans érosion

- Diagonale 100/50/25 mm : **357.920 / 363.524 / 356.569 kN·s** ; écart 50–25 mm **1.951%**.
- Matrice croisée conditionnelle : **non requise, car la diagonale sans érosion passe le portail de 10 %**.

## 5. Contradictions, inconnues et décision

- La géométrie et la rupture réelles du JT9D, le bordereau exact du panneau 124, le contact arête-arête, les ailes, le carburant et le fuselage restent inconnus ou non qualifiés.
- Supprimer l'érosion peut améliorer la convergence tout en supprimant une physique importante ; un résultat convergé sans rupture n'est donc pas une validation physique de l'impact.
- Une formulation de rupture régularisée par taille d'élément exige des données ou bornes de fracture explicites. Elle ne doit pas être inventée ni ajustée pour reproduire une impulsion souhaitée.
- Le portail global WTC 1, le thermique et Blender restent fermés. Blender demeure une visualisation seulement.

La prochaine itération doit conserver ces diagnostics et tester uniquement une rupture régularisée sourcée ou explicitement bornée, puis répéter le seuil de convergence de 10 % et l'ordre de rupture avant toute extension globale.
