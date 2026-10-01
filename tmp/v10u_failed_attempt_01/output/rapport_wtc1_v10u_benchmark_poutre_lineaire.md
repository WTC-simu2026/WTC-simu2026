# WTC 1 — V10U : benchmark CalculiX indépendant d’une poutre linéaire

## Décision

**ÉCHEC — `FAIL_INDEPENDENT_LINEAR_B32R_BENCHMARK`.**

Cette décision qualifie uniquement la chaîne locale CalculiX 2.22 pour ce porte-à-faux générique en éléments B32R. Elle ne valide aucun membre, assemblage, chemin de charge ou mécanisme du WTC 1.

## Résultats numériques

- Exécutions structurelles : 9 ; codes retour acceptés : 9/9.
- Fermetures charge-réaction : 9/9.
- Comparaisons analytiques acceptées : 5/9.
- Déplacement de référence de Timoshenko à 10 000 N : 16.0312000 mm.
- Écart maximal solveur/référence : 10.013 %.
- Écart relatif entre 16 et 32 éléments : 0.343125 %.
- Linéarité charge-déplacement : R² = 1.000000000000 ; erreur de pente = 0.430865 % ; intercept = -6e-07 mm.

| Éléments | Déplacement (mm) | Référence (mm) | Écart (%) | Réaction Z (N) | Fermeture relative | Statut |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 14.425990000 | 16.031200000 | 10.013 | 10000.000000 | 0.000e+00 | ÉCHEC |
| 2 | 15.111240000 | 16.031200000 | 5.73856 | 10000.000000 | 0.000e+00 | ÉCHEC |
| 4 | 15.563360000 | 16.031200000 | 2.91831 | 10000.000000 | 0.000e+00 | ÉCHEC |
| 8 | 15.793480000 | 16.031200000 | 1.48286 | 10000.000000 | 0.000e+00 | ÉCHEC |
| 16 | 15.907360000 | 16.031200000 | 0.772494 | 10000.000000 | 0.000e+00 | PASS |
| 32 | 15.962130000 | 16.031200000 | 0.430847 | 10000.000000 | 0.000e+00 | PASS |

## Discipline de preuve

### 1. Faits directement observés ou transcrits

Le binaire local vérifié par empreinte annonce CalculiX 2.22. Neuf jeux d’entrée ont été exécutés ; leurs fichiers d’entrée et sorties ont été inventoriés et hachés. Le fichier maître Blender est resté inchangé.

### 2. Résultats d’un modèle officiel

Aucun résultat officiel NIST n’est utilisé dans ce benchmark.

### 3. Affirmations provenant des archives locales

Aucune affirmation des archives WTC n’est utilisée. Le seul exemple installé consulté sert de précédent syntaxique B32R et n’obtient aucun crédit physique.

### 4. Hypothèses propres au modèle

Porte-à-faux rectangulaire générique de 2 000 mm, section 100 × 100 mm, matériau élastique isotrope E = 200 000 MPa et ν = 0,3, encastrement idéal, force nodale en bout, petites déformations, sans imperfection, contact ni non-linéarité.

### 5. Résultats dérivés

Les références d’Euler–Bernoulli et de Timoshenko, la conformité charge-réaction, la convergence 16→32 éléments, la régression charge-déplacement et le travail externe linéaire sont calculés à partir des entrées déclarées et des sorties numériques parsées.

### 6. Contradictions et informations manquantes

Aucune donnée mécanique manquante du WTC 1 n’est fermée : 0/22 exigences restent satisfaites. Les sections réelles, assemblages, redistributions, dommages d’impact, températures, ruptures et conditions de propagation demeurent absents. Il est donc interdit de transformer ce PASS logiciel en conclusion d’effondrement ou de non-effondrement.

## Étape suivante

V10V — Qualifier un second benchmark mécanique indépendant avec non-linéarité géométrique, flambement et réponse post-critique contrôlée en déplacement. Vérifier la convergence et les bilans sans attribuer le modèle au WTC 1 ni rouvrir les portes physiques tant que les données réelles restent absentes.
