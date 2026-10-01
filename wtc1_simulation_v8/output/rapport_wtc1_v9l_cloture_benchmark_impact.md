# WTC 1 - V9L, clôture du benchmark ouvert d'impact rapide

## Conclusion courte

V9L est validée comme **résultat négatif de clôture**. Le ZIP Altair a bien été récupéré et inspecté, et le rapport FAA DOT/FAA/AR-08/36 a été contrôlé sur ses pages techniques utiles. Aucun des deux cas ne réunit simultanément mesures physiques, rupture objectivement régularisée, convergence à trois niveaux, modèle réutilisable et exécution locale bornée. Aucun solveur n'a donc été lancé et la recherche externe de benchmark est close sans assouplir les critères.

## 1. Faits directement observés ou transcrits

- Le ZIP Altair mesure exactement 77 961 octets et contient 20 fichiers RAD : 10 Starter et 10 Engine. Les sept cas de plaque utilisent une sphère rigide `/RWALL/SPHER`; il n'existe ni projectile déformable, ni carte `/NONLOCAL`, ni données d'essai mesurées, ni licence embarquée.
- Les cartes BIQUAD ont une longueur élémentaire de référence nulle et les cartes TAB1 n'activent aucune fonction de longueur d'élément. Les variantes partagent une géométrie de plaque unique : ce ne sont pas trois maillages de convergence.
- Le rapport FAA est un rapport final public de 48 pages. Le lien FAA historique ne répond plus; la copie inspectée provient de la capture 2014 de cette URL, avec identité vérifiée sur la couverture et la fiche documentaire du rapport.
- Les essais FAA/UCB concernent des plaques d'aluminium 2024-T3/T351 de 1/16, 1/8 et 1/4 pouce, frappées par une sphère d'acier de 1/2 pouce. Les graphes donnent les vitesses initiales et résiduelles mesurées, avec des limites balistiques d'environ 400, 700 et 1350 ft/s.
- Le projectile FAA est maillé et peut se déformer élastiquement, mais le modèle interdit sa plasticité et les essais n'ont montré aucun écoulement du projectile. Ce cas ne qualifie donc pas la rupture du projectile.

## 2. Résultats de modèles officiels

- La FAA compare trois configurations de maillage et plusieurs jeux Johnson-Cook. Elle conclut elle-même que les paramètres accordés à une taille d'élément sont plus précis et qu'augmenter la densité du maillage n'améliore pas nécessairement la prédiction.
- L'option non locale testée par la FAA n'a ni amélioré l'exactitude ni diminué la dépendance au maillage dans cette étude.
- Les contacts SOFT=1 et SOFT=2 ont donné des résultats proches avec des maillages de densités similaires; SOFT=2 coûtait davantage en calcul.
- Altair compare des formulations numériques de rupture. L'exemple n'est pas accompagné d'une validation expérimentale.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive WTC en lecture seule n'a pas été rescannée.

## 4. Hypothèses propres à V9L

- Les sept portes V9K restent obligatoires et ne sont pas pondérées.
- Trois maillages différents ne constituent une convergence que si un observable commun tend vers une valeur stable ou si une incertitude numérique est explicitement bornée.
- Une comparaison mesure/calcul de plaque ne peut pas être substituée aux aciers de façade WTC ni à un projectile moteur/capotage sans qualification distincte.

## 5. Résultats dérivés

| Candidat | Portes franchies | Décision | Premier motif de rejet |
| --- | ---: | --- | --- |
| ALTAIR_RD_E_2602_INPUT_ARCHIVE | 3/7 | REJETE | Public download is verified, but no reusable model-file license is embedded; the official documentation page carries an All Rights Reserved notice. |
| FAA_DOT_FAA_AR_08_36_FLAT_PANEL_IMPACT | 2/7 | REJETE | The report is public, but no solver deck or explicit model-file reuse license is supplied; report access alone does not license a benchmark deck. |

- Candidats retenus : **0**.
- ZIP Altair : complet et exécutable en principe, mais sphère rigide, aucune mesure, aucune convergence et aucune régularisation objective active.
- Rapport FAA : excellent comparateur descriptif de perforation de plaque, avec mesures et contact déformable, mais projectile sans plasticité, rupture dépendante du maillage, absence de convergence établie et absence de deck public.
- Le critère de clôture est satisfait : aucun cas ne combine les éléments requis. La recherche externe de benchmark est désormais gelée.

## 6. Contradictions et informations manquantes

- La FAA publie trois maillages, mais le troisième modifie aussi la topologie dans le plan; les résultats montrent une sensibilité, pas une suite convergée.
- Les graphes FAA fournissent des mesures quantitatives, mais aucune barre d'incertitude ni table brute.
- Le rapport décrit une option non locale, sans publier la valeur numérique de longueur utilisée; sa conclusion ne montre aucun gain de convergence.
- Le ZIP Altair est publiquement téléchargeable, mais aucune licence de réutilisation explicite n'y est embarquée.

## Décision

V9L n'autorise ni ajustement de loi de rupture, ni conversion LS-DYNA, ni simulation du projectile, de la façade ou de l'impact global. Le verrou physique reste la rupture objectivée et convergée d'un projectile déformable. Blender demeure un outil de visualisation, jamais une validation physique.
