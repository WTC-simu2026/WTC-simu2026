# WTC 1 — V8C : validation CalculiX du flambement élastique

## Portée

Cette étape vérifie uniquement que la chaîne CalculiX reproduit la charge critique d’Euler d’une colonne bi-articulée. Elle ne constitue ni une simulation d’impact, ni une simulation d’effondrement.

La section rectangulaire équivalente est construite pour reproduire exactement `Iy` de chaque profil historique. Son aire n’est pas celle du profil W : elle ne peut donc servir qu’à cette vérification élastique de solveur.

## Résultats

| Colonne | Profil | Euler (MN) | Timoshenko (MN) | CalculiX (MN) | Écart vs Timoshenko |
|---:|---:|---:|---:|---:|---:|
| 501 | 14WF500 | 182.1805 | 178.0836 | 177.8142 | -0.151 % |
| 605 | 12WF133 | 24.6703 | 24.4632 | 24.4771 | +0.057 % |
| 705 | 14WF48 | 3.2451 | 3.2352 | 3.2390 | +0.120 % |
| 804 | 12WF92 | 16.1938 | 16.0835 | 16.0938 | +0.064 % |

## Décision

La chaîne est acceptée pour le sous-modèle V8C si les quatre erreurs absolues par rapport à la solution de colonne de Timoshenko restent inférieures à 1 %. La comparaison à Euler est conservée comme contrôle secondaire. L’étape suivante devra utiliser de vraies géométries de sections ou une composition de rectangles, avec imperfections, liaisons et comportement matériel dépendant de la température.
