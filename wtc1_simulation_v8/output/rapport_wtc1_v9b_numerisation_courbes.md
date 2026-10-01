# WTC 1 - V9B : numérisation des courbes M26 et C80

## Résultat

L'exécution de V9B est **validée comme résultat négatif**. La numérisation complète est **FAIL** selon les portes déclarées avant calcul. Les neuf tracés sont extraits et les axes sont calibrés, mais trois courbes C80 échouent au moins un critère individuel. L'éprouvette OpenRadioss conditionnelle est donc **non autorisée et non exécutée**.

Ce résultat ne dit pas que l'impact de l'avion sur la façade échoue physiquement. Il dit seulement que les figures publiques utilisées ici ne suffisent pas, sans filtrage ou hypothèse ajoutée après coup, à construire et valider la réponse plastique/rate demandée pour l'étape suivante.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D Figure A-28 publie cinq courbes longitudinales M26 à 6.06E-5, 65, 100, 260 et 417 /s.
- NCSTAR 1-3D Figure A-48 publie quatre courbes longitudinales C80 à 8.75E-5, 84, 299 et 401 /s.
- Les Tables A-12 et A-14 donnent les limites à 1 % et résistances maximales employées comme références.
- Le rapport avertit que des oscillations de charge subsistent dans les essais rapides et qu'aucun filtrage mathématique n'a été appliqué.
- Les pages source ont été rendues à 300 dpi et contrôlées visuellement. Les données numériques proviennent néanmoins des chemins vectoriels du PDF, non des pixels rendus.

## 2. Résultats d'un modèle officiel

Aucun résultat global NIST n'est recalculé dans V9B. Les figures et tables NIST servent seulement de mesures publiées à numériser et comparer.

## 3. Affirmations provenant des archives locales

Aucune affirmation nouvelle n'est tirée des archives locales. L'archive source n'a pas été rescannée et les PDF officiels n'ont pas été modifiés.

## 4. Hypothèses propres au modèle

- Une droite d'offset à 1 % avec `E = 29 000 ksi` est utilisée uniquement pour relire la limite d'élasticité sur les courbes.
- Aucun lissage ni filtrage n'est appliqué après observation des résultats.
- Le court segment orange terminal de C80-401/s est rattaché au tracé vert uniquement parce que son écart vectoriel de 0.630 point reste sous la limite pré-déclarée de 1.5 point.
- Aucune partie après striction n'est convertie en loi de rupture.

## 5. Résultats dérivés

- Résidu maximal de calibration des axes : **0.202 point PDF**, sous la limite de 0.25.
- Erreur médiane Fy : **4.18 %**, sous la limite de 5 %.
- Erreur médiane TS : **0.98 %**, sous la limite de 5 %.
- Erreur individuelle maximale Fy : **28.76 %**.
- Erreur individuelle maximale TS : **13.38 %**.
- Six courbes passent tous leurs critères et trois échouent : **C80_QS, C80_299, C80_401**.

| Courbe | Vitesse (/s) | Points | Fy num. (ksi) | Fy table (ksi) | Erreur Fy | TS num. (ksi) | TS table (ksi) | Erreur TS | Porte |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| M26_QS | 6.06e-05 | 71 | 61.32 | 61.7-63.2 | 0.61 % | 86.60 | 85.5-86.1 | 0.58 % | PASS |
| M26_65 | 65 | 308 | 72.38 | 72.2-72.2 | 0.25 % | 101.31 | 99.9-99.9 | 1.41 % | PASS |
| M26_100 | 100 | 398 | 72.80 | 75.9-75.9 | 4.09 % | 100.65 | 100.4-100.4 | 0.25 % | PASS |
| M26_260 | 260 | 333 | 79.02 | 75.9-75.9 | 4.12 % | 103.41 | 102.8-102.8 | 0.59 % | PASS |
| M26_417 | 417 | 329 | 92.76 | 85.0-85.0 | 9.13 % | 107.58 | 106.7-106.7 | 0.83 % | PASS |
| C80_QS | 8.75e-05 | 25 | 35.55 | 37.1-37.1 | 4.18 % | 65.72 | 67.3-67.3 | 2.34 % | FAIL (points) |
| C80_84 | 84 | 314 | 61.05 | 57.3-57.3 | 6.55 % | 84.16 | 85.0-85.0 | 0.98 % | PASS |
| C80_299 | 299 | 348 | 69.61 | 62.5-62.5 | 11.38 % | 90.82 | 80.1-80.1 | 13.38 % | FAIL (Fy, TS) |
| C80_401 | 401 | 294 | 76.61 | 59.5-59.5 | 28.76 % | 91.08 | 89.1-89.1 | 2.22 % | FAIL (Fy) |

## 6. Contradictions, limites et informations manquantes

- **C80_QS** contient 25 points centraux uniques, sous le minimum de 30. Ses résistances sont proches de la table, mais la complétude vectorielle échoue.
- **C80_299** dépasse les limites individuelles pour Fy (11.38 %) et TS (13.38 %).
- **C80_401** dépasse la limite individuelle Fy (28.76 %).
- Les oscillations visibles sont cohérentes avec l'avertissement NIST, mais les données brutes et la procédure exacte de réduction utilisées pour les valeurs tabulées ne sont pas publiques ici. On ne peut donc pas attribuer toute la différence au seul ringing.
- La recherche publique ciblée GE/FAA/NASA fournit des dimensions, des actions de navigabilité et des concepts adjacents de nacelle ou de confinement. Elle ne fournit toujours **aucune des 9 exigences** d'une carte matériau/rupture assignable au CF6-80A2 ou à son capotage de production.
- Aucune nuance générique, aucun concept composite expérimental et aucun modèle de moteur voisin n'est substitué au CF6-80A2.

## Décision de porte

La porte de numérisation V9B reste fermée. Conformément au protocole pré-déclaré :

- pas d'éprouvette OpenRadioss ;
- pas de suppression d'éléments ni calibration de rupture ;
- pas d'impact façade ;
- pas de simulation avion complet, tour globale, thermique ou Blender ;
- aucune conclusion sur explosif ou thermite.

## Suite recommandée

Conserver V9B comme cas de régression négatif. Pour V9C, rechercher d'abord soit les données numériques brutes des essais NIST M26/C80, soit une méthode officielle documentée reliant les tracés oscillants aux valeurs Fy/TS tabulées. À défaut, ne pas construire de carte plastique haute vitesse à partir de ces figures. La recherche CF6-80A2 doit rester limitée à des composants et matériaux explicitement identifiés, sans substitution générique.
