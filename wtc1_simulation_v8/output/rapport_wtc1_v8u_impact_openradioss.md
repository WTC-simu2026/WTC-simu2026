# WTC 1 — V8U : sous-modèle d’impact OpenRadioss

## Résultat

La matrice V8U s’est exécutée sans modifier `C:\OpenRadioss` ni `System32`. Le verdict du portail numérique pré-déclaré est **FAIL: medium_to_fine_impulse**.

Ce verdict concerne uniquement un projectile sphérique rigide et un petit panneau de coques. Il ne constitue ni une reproduction de l’impact du vol AA11, ni une validation de l’état d’endommagement global NIST, ni un test de la chaîne incendie-initiation-propagation, ni un test d’une hypothèse de démolition.

## 1. Faits directement documentés

- NIST décrit 59 colonnes caisson par façade, nominalement carrées de 14 pouces, espacées de 40 pouces, avec des allèges de 52 pouces.
- Un élément récupéré voisin de la zone d’impact, N8, provient du WTC 1 vers les étages 97–100 ; une plaque de semelle de 5/16 pouce est documentée, ainsi qu’un acier spécifié à 60 ksi.
- Pour ce groupe d’acier, NIST rapporte un coefficient longitudinal de sensibilité au taux d’environ 0,016 pour la limite d’élasticité.
- Dans ses sous-modèles de moteur, NIST rapporte des pertes de vitesse de 56 à 74 mph selon la position et le traitement des assemblages. Ce sont des résultats de modèle officiel, pas des mesures directes de l’événement.

## 2. Hypothèses propres à V8U

- Trois colonnes caisson carrées fermées sont reliées par une allège d’un étage. Les soudures sont remplacées par des nœuds partagés ; planchers, boulons, sièges de fermes et plaques d’assemblage sont absents.
- L’épaisseur de 5/16 pouce est appliquée à toutes les faces des colonnes et 3/8 pouce à l’allège. Ces valeurs sont représentatives de pièces voisines ; elles ne constituent pas le bordereau exact du panneau 124 au niveau 96.
- Le projectile est une sphère rigide de 1,0 m et 4 558,6 kg à 443 mph. Sa masse dérive d’une moitié de la masse des deux moteurs avec capotages, mais son diamètre, sa rigidité et sa forme sont des choix de qualification.
- La déformation plastique de rupture 0,20 est entourée par 0,10 et 0,30. Cette suppression d’éléments est dépendante du maillage.

## 3. Résultats dérivés

| Cas | Maille (mm) | Rupture | Fils | Coques | Coques rompues | Vitesse résiduelle (m/s) | Perte (mph) | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M100_E020_T1 | 100 | 0.20 | 1 | 2272 | 144 | 192.820 | 11.655 | -1.748 |
| M050_E020_T1 | 50 | 0.20 | 1 | 8874 | 372 | 193.462 | 10.220 | -1.760 |
| M025_E020_T1 | 25 | 0.20 | 1 | 32926 | 1069 | 194.252 | 8.454 | -1.727 |
| M050_E010_T1 | 50 | 0.10 | 1 | 8874 | 608 | 193.830 | 9.396 | -1.768 |
| M050_E030_T1 | 50 | 0.30 | 1 | 8874 | 300 | 192.019 | 13.448 | -1.741 |
| M050_E020_T4 | 50 | 0.20 | 4 | 8874 | 372 | 193.462 | 10.220 | -1.760 |

- Écart moyen-fin sur l’impulsion : **20.900%**.
- Écart moyen-fin sur la vitesse résiduelle : **0.407%**.
- Répétabilité 1/4 fils sur l’impulsion : **0.000%**.
- Répétabilité 1/4 fils sur la vitesse : **0.000%**.

## 4. Comparaison au modèle officiel

La bande NIST de 56–74 mph est affichée comme repère diagnostique uniquement. Une différence avec V8U n’est pas une contradiction physique : NIST utilisait une représentation détaillée et déformable du moteur et plusieurs panneaux, alors que V8U emploie une sphère rigide et un panneau tronqué. L’intérêt de V8U est de révéler la sensibilité au maillage, à la rupture et au parallélisme avant d’engager un modèle plus coûteux.

## 5. Contradictions, inconnues et décision

- Bordereau exact des plaques du panneau 124 au niveau 96 : **inconnu dans le jeu local gelé**.
- Courbe matériau complète à grande vitesse et loi de rupture multiaxiale de cette plaque précise : **inconnues**.
- Géométrie et propriétés détaillées du moteur JT9D, capotage et assemblages : **non modélisées**.
- Contact déformable-déformable `/INTER/TYPE7`, rupture du projectile, aile et carburant : **non qualifiés par V8U**.
- Le portail global WTC-impact demeure **bloqué** même si le portail numérique du substitut passe.

La prochaine itération doit conserver ce cas comme test de régression, puis remplacer la sphère par un projectile déformable minimal et qualifier `/INTER/TYPE7` sur une géométrie de panneau plus étendue. Aucun transfert vers Blender ou vers un calcul global n’est justifié par V8U seul.
