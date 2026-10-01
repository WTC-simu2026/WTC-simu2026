# WTC 1 — V8D : pilote force–déplacement de la colonne 705 au niveau 95

## Portée

Le profil 14WF43 est modélisé en coques, bi-articulé, avec une imperfection sinusoïdale. Cette étape mesure la réponse d’un membre isolé; elle ne représente pas encore le noyau, les planchers ou la tour entière.

| Température | Statut | Imperfection | E (GPa) | Fy (MPa) | Maximum convergé (MN) | Dernier déplacement (mm) | Énergie (MJ) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 52.0 °C | NIST Case B Floor 95 100-min minimum | L/1000 | 203.6 | 296.4 | 1.672 | 3.8 | 0.003 |
| 406.5 °C | arithmetic midpoint sensitivity; not a NIST mean/median | L/1000 | 178.2 | 215.6 | 1.360 | 3.9 | 0.003 |
| 761.0 °C | NIST Case B Floor 95 100-min maximum | L/1000 | 95.7 | 39.2 | 0.291 | 1.9 | 0.000 |
| 406.5 °C | arithmetic midpoint sensitivity; not a NIST mean/median | L/500 | 178.2 | 215.6 | 1.226 | 3.8 | 0.003 |

## Contrôle croisé avec V8B/AISC

Pour `K = 1`, la courbe de résistance de colonne utilisée dans V8B donne respectivement 1,684 MN à 52 °C, 1,301 MN à 406,5 °C et 0,288 MN à 761 °C. Les maxima convergés du modèle en coques avec imperfection L/1000 valent 1,672 MN, 1,360 MN et 0,291 MN, soit des écarts de -0,7 %, +4,5 % et +1,2 %. À 52 °C, la courbe croît encore au dernier point : 1,672 MN est donc une borne atteinte, pas un pic établi. Avec l’imperfection L/500, le maximum médian baisse à 1,226 MN.

Cet accord contrôle le niveau du premier pic; il ne valide pas la branche descendante ni l’énergie totale d’écrasement. Les énergies du tableau ne couvrent que les quelques millimètres calculés avant la perte de convergence.

## Limites de décision

La valeur à 406,5 °C n’est qu’une interpolation de sensibilité entre le minimum et le maximum spatial publiés par NIST. Au-dessus de 600 °C, le module suit une extrapolation explicite et non une donnée NIST. Aucun résultat de ce pilote ne peut être additionné 47 fois sans carte spatiale des températures, charges individuelles et liaisons de planchers.
