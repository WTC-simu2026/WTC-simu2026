# WTC 1 — V10X — benchmark indépendant de plasticité cyclique

**Décision : `FAIL_INDEPENDENT_CALCULIX_T3D2_CYCLIC_PLASTICITY_BENCHMARK`**

## Résultat utile

Ce benchmark vérifie uniquement que CalculiX 2.22 reproduit le chargement, la plastification, le déchargement, l'inversion et la dissipation d'un barreau axial générique. Il ne constitue pas encore une simulation du WTC 1.

- Force d'écoulement analytique : 25.000 kN.
- Déplacement d'écoulement analytique : 1.250 mm.
- Dissipation analytique du cycle fermé : 125.000 J.
- Erreur de force maximale : 3.63798e-12 N.
- Erreur relative maximale d'énergie : 100 %.
- Variation d'énergie entre 8 et 32 éléments : 0 %.

## Résultats par maillage

| Éléments | Enregistrements | Travail du cycle (J) | Erreur énergie (%) | Erreur force max. (N) | Verdict |
|---:|---:|---:|---:|---:|:---|
| 1 | 11 | 0.000000 | 100.000000 | 3.63798e-12 | FAIL |
| 2 | 44 | 0.000000 | 100.000000 | 3.63798e-12 | FAIL |
| 8 | 13 | 0.000000 | 100.000000 | 3.63798e-12 | FAIL |
| 32 | 11 | 0.000000 | 100.000000 | 3.63798e-12 | FAIL |

## Statut des preuves

- Faits/sources : syntaxe du solveur et résultats numériques produits par les quatre calculs locaux.
- Hypothèses du modèle : barreau axial générique, petite déformation, plasticité parfaite et indépendante de la vitesse.
- Résultats dérivés : comparaison point par point, équilibre des réactions, aire de la boucle et invariance de maillage.
- Informations manquantes : lois WTC à chaud et à grande vitesse, rupture, assemblages, flambement local et géométrie réelle.

## Limite de conclusion

Aucune des 22 exigences mécaniques documentaires WTC 1 n'est déclarée fermée par V10X. Le prochain modèle exploratoire pourra utiliser des plages hypothétiques clairement signalées, mais pas convertir ce test logiciel en validation historique.
