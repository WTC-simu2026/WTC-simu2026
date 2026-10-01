# WTC 1 — V10W : benchmark mécanique à température prescrite

## Décision

**PASS — `PASS_INDEPENDENT_PRESCRIBED_TEMPERATURE_MECHANICAL_BENCHMARK`.**

Cette décision qualifie uniquement la conversion locale d’un champ de température imposé en dilatation ou effort axial dans un barreau de treillis T3D2 générique. Aucun transfert de chaleur, incendie ou champ thermique WTC 1 n’est calculé.

## Références analytiques

- Dilatation uniforme libre : 1.200000 mm.
- Effort uniforme totalement empêché : 24000.000000 N, soit 240.000000 MPa dérivés.
- Gradient axial linéaire libre : 0.600000 mm.

| Cas | Éléments | Déplacement (mm) | Réaction base (N) | Réaction extrémité (N) | Erreur déplacement | Erreur effort | Statut |
|---|---:|---:|---:|---:|---:|---:|---|
| UNIFORM_FREE | 1 | 1.200000000 | 0.000000 | -0.000000 | 0.000e+00 | — | PASS |
| UNIFORM_FREE | 2 | 1.200000000 | -0.000000 | -0.000000 | 0.000e+00 | — | PASS |
| UNIFORM_FREE | 8 | 1.200000000 | 0.000000 | 0.000000 | 0.000e+00 | — | PASS |
| UNIFORM_FREE | 32 | 1.200000000 | 0.000000 | -0.000000 | 0.000e+00 | — | PASS |
| UNIFORM_RESTRAINED | 1 | -0.000000000 | 24000.000000 | -24000.000000 | 6.163e-33 | 0.000e+00 | PASS |
| UNIFORM_RESTRAINED | 2 | 0.000000000 | 24000.000000 | -24000.000000 | 4.622e-33 | 0.000e+00 | PASS |
| UNIFORM_RESTRAINED | 8 | -0.000000000 | 24000.000000 | -24000.000000 | 7.704e-34 | 0.000e+00 | PASS |
| UNIFORM_RESTRAINED | 32 | 0.000000000 | 24000.000000 | -24000.000000 | 0.000e+00 | 0.000e+00 | PASS |
| AXIAL_LINEAR_GRADIENT_FREE | 1 | 0.600000000 | 0.000000 | -0.000000 | 0.000e+00 | — | PASS |
| AXIAL_LINEAR_GRADIENT_FREE | 2 | 0.600000000 | -0.000000 | -0.000000 | 0.000e+00 | — | PASS |
| AXIAL_LINEAR_GRADIENT_FREE | 8 | 0.600000000 | -0.000000 | 0.000000 | 0.000e+00 | — | PASS |
| AXIAL_LINEAR_GRADIENT_FREE | 32 | 0.600000000 | 0.000000 | -0.000000 | 0.000e+00 | — | PASS |

## Convergence des maillages les plus fins

- Dilatation uniforme libre : 0 %.
- Effort uniforme empêché : 0 %.
- Gradient axial libre : 0 %.

## Discipline de preuve

### 1. Faits directement observés ou transcrits

Le binaire local haché annonce CalculiX 2.22. Douze jeux d’entrée sont exécutés, chaque nœud original reçoit explicitement une température, toutes les sorties sont inventoriées et le maître Blender reste inchangé.

### 2. Résultats d’un modèle officiel

Aucun résultat officiel NIST n’est utilisé.

### 3. Affirmations provenant des archives locales

Aucune affirmation des archives WTC n’est utilisée. La documentation CalculiX sert uniquement à distinguer température prescrite en étape mécanique et analyse thermique couplée.

### 4. Hypothèses propres au modèle

Barreau générique de 1 000 mm et 10 × 10 mm, E = 200 000 MPa, ν = 0,3, coefficient de dilatation constant 12×10⁻⁶ /°C, température initiale et de référence 0 °C, élévation synthétique maximale 100 °C, comportement linéaire et petites déformations.

### 5. Résultats dérivés

Les déplacements, l’effort empêché, la contrainte axiale dérivée, les erreurs analytiques, les équilibres de réactions et les variations de maillage proviennent des paramètres déclarés et des sorties CalculiX parsées.

### 6. Contradictions et informations manquantes

Aucun flux thermique, convection, rayonnement, feu de compartiment, SFRM, historique température-temps ou loi matériau dépendante de la température n’est résolu. Le benchmark ferme 0/22 exigences mécaniques WTC et ne permet aucune conclusion d’effondrement ou de non-effondrement.

## Étape suivante

V10X — Qualifier un benchmark de réponse matériau non linéaire indépendant avec plasticité et déchargement cyclique contrôlé, puis vérifier la dissipation et l'indépendance de maillage avant toute attribution WTC 1.
