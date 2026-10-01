# WTC 1 — V8C : validation en coques des profils W

Les âmes et semelles sont modélisées par des coques S4R avec leurs dimensions historiques. Le cas-test est une console de 3,6576 m, encastrée en pied et comprimée par une charge unitaire répartie sur la section supérieure. La référence analytique est donc Euler avec K=2.

| Colonne | Profil | Éléments | ΔIy géom./table | Euler K=2 (MN) | CalculiX (MN) | Écart |
|---:|---:|---:|---:|---:|---:|---:|
| 501 | 14WF500 | 1728 | +0.00 % | 45.5453 | 44.6036 | -2.07 % |
| 605 | 12WF133 | 1728 | -0.03 % | 6.1657 | 6.1085 | -0.93 % |
| 705 | 14WF48 | 1728 | -0.12 % | 0.8103 | 0.8139 | +0.44 % |
| 804 | 12WF92 | 1728 | +0.14 % | 4.0542 | 4.0209 | -0.82 % |

Un écart faible valide la représentation pour le flambement global. Un premier facteur nettement inférieur à Euler doit être examiné comme mode local possible, pas automatiquement classé comme erreur numérique.
