# WTC 1 — V8C : sections W composées dans CalculiX

Cette vérification utilise l’âme et les deux semelles réelles comme trois rectangles liés à la même ligne de référence. Les congés de laminage ne sont pas représentés.

| Colonne | Profil | ΔA géométrique | ΔIy géométrique | ΔIx géométrique | CalculiX / Euler(Iy géom.) |
|---:|---:|---:|---:|---:|---:|
| 501 | 14WF500 | -0.28 % | -0.11 % | -0.15 % | +6.24 % |
| 605 | 12WF133 | -0.76 % | -0.04 % | -0.61 % | +8.06 % |
| 705 | 14WF48 | -2.10 % | -0.13 % | -2.46 % | +9.30 % |
| 804 | 12WF92 | -1.28 % | +0.14 % | -1.12 % | +8.15 % |

Les écarts géométriques par rapport à la table AISC proviennent principalement des congés omis et des arrondis de dimensions. Ce modèle n’est accepté pour V8C que si son premier mode est physiquement identifiable et si l’écart avec Euler calculé sur sa propre géométrie reste maîtrisé.
