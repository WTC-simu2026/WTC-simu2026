# WTC 1 — V10V : benchmark indépendant de flambement non linéaire

## Décision

**PASS — `PASS_INDEPENDENT_B32R_NONLINEAR_BUCKLING_BENCHMARK`.**

La décision qualifie uniquement ce cas générique CalculiX B32R : extraction de charge critique, colonne initialement courbe, grandes déformations et raccourcissement imposé. Elle ne représente aucune colonne du WTC 1.

## Flambement propre

Référence de Timoshenko : 105167.831929 N ; Euler : 105275.780278 N.

| Éléments | Première charge propre (N) | Écart (%) | Code retour | Statut |
|---:|---:|---:|---:|---|
| 8 | 105158.200000 | 0.00915863 | 0 | PASS |
| 16 | 105144.900000 | 0.0218051 | 0 | PASS |
| 32 | 105146.200000 | 0.020569 | 0 | PASS |
| 64 | 105146.200000 | 0.020569 | 0 | PASS |

Variation du couple de maillages le plus fin (32→64) : 0 %.

## Réponse après la charge critique

Imperfection initiale : 2.000 mm (L/1000) ; raccourcissement cible : 8.000 mm ; seuil de fenêtre postcritique : 1.314598 mm.

| Éléments | Points | Points postcritiques | Raccourcissement final (mm) | Réaction finale / Pcr | Amplitude finale (mm) | Amplification | Résidu d'équilibre max | Erreur médiane analytique (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 104 | 85 | 8.000000 | 0.975641 | 77.102090 | 38.551 | 0.000e+00 | 0.0736528 |
| 32 | 104 | 85 | 8.000000 | 0.975621 | 77.058670 | 38.529 | 0.000e+00 | 0.0737231 |
| 64 | 104 | 85 | 8.000000 | 0.975601 | 76.994880 | 38.497 | 0.000e+00 | 0.0765229 |

Convergence 32→64 : réaction finale 0.00204675 %, amplitude finale 0.0828497 %.

Le travail externe est intégré sous chaque courbe réaction–raccourcissement. C’est un résultat dérivé ; aucune égalité avec une énergie interne de solveur non extraite n’est revendiquée.

## Discipline de preuve

### 1. Faits directement observés ou transcrits

Le binaire local haché annonce CalculiX 2.22. Sept jeux d’entrée ont été exécutés. Leurs fichiers d’entrée et sorties sont hachés, les réactions des deux appuis sont parsées à chaque incrément convergé et le maître Blender reste inchangé.

### 2. Résultats d’un modèle officiel

Aucun résultat officiel NIST n’est utilisé.

### 3. Affirmations provenant des archives locales

Aucune affirmation des archives WTC n’est utilisée. Un exemple FreeCAD installé sert seulement de précédent syntaxique pour B32R.

### 4. Hypothèses propres au modèle

Colonne générique bi-articulée de 2 000 mm, section carrée 40 × 40 mm, élasticité isotrope, imperfection sinusoïdale de 2 mm, appuis idéaux, sans contact, plasticité, température, endommagement ni rupture.

### 5. Résultats dérivés

Les charges critiques d’Euler et de Timoshenko, la relation approchée de colonne imparfaite, les résidus d’équilibre, les convergences de maillage et les travaux externes proviennent des entrées déclarées et des sorties CalculiX parsées.

### 6. Contradictions et informations manquantes

La relation postcritique analytique est une approximation à faibles pentes, non une solution exacte à rotations finies. Le benchmark ne contient aucune section, liaison, charge, imperfection, température ou rupture propre au WTC 1. Il ferme donc 0/22 exigences mécaniques et ne permet aucune conclusion d’effondrement ou de non-effondrement.

## Étape suivante

V10W — Qualifier un benchmark thermo-mécanique indépendant et borné : dilatation libre, dilatation empêchée et gradient thermique simple, avec solutions analytiques et bilans. Ne transférer ensuite vers le WTC 1 que des capacités logicielles, jamais des états physiques sans données sources suffisantes.
