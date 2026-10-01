# WTC 1 — V8W : vol libre et contacts pairwise du projectile déformable

## Résultat

Le contrôle en vol libre est **PASS**. La matrice d'impact façade a été **exécutée** et son portail est **FAIL**. Le portail V8W complet est donc **FAIL**.

Échecs du vol libre : aucun. Échecs de l'impact : medium_to_fine_contact_impulse.

Ce verdict porte seulement sur le projectile équivalent à deux coques et sur la petite façade V8V. Il ne valide ni un JT9D réel, ni l'avion complet, ni l'impact global du WTC 1, ni l'incendie ou l'effondrement, ni Blender comme validation physique, ni une hypothèse de démolition.

## 1. Faits directement documentés

- La documentation officielle Radioss définit TYPE7 comme un contact entre une surface principale et un groupe de nœuds secondaires. Un nœud n'est exclu que du segment auquel il est directement connecté ; TYPE7 ne traite pas le contact arête-arête.
- Avec `Igap=2`, le jeu variable des deux coques est calculé à partir de leurs demi-épaisseurs lorsque cette somme dépasse le jeu minimal.
- V8U et V8V sont restés inchangés selon les empreintes et métriques gelées : **PASS**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats d'un modèle officiel

- Aucun nouveau résultat NIST n'est utilisé comme cible de V8W. Les données de façade, masse et vitesse restent celles déjà gelées dans V8V ; elles ne constituent pas une validation indépendante de l'impact réel.

## 3. Hypothèses propres au modèle

- Le noyau et le capotage carrés restent des équivalents de masse, pas une géométrie JT9D.
- L'auto-contact V8V entre tous les nœuds et toutes les coques du projectile est supprimé. Il est remplacé par deux contacts directionnels : noyau vers capotage, puis capotage vers noyau.
- L'ouverture frontale du capotage passe de 1 000 à 1 200 mm. Le jeu radial de surfaces moyennes est de 150 mm ; après les demi-épaisseurs équivalentes, la marge initiale calculée est d'environ 114.731 mm, soit 3.253 fois le jeu d'activation TYPE7.
- Les matériaux, ruptures, façade tronquée et absence de contact arête-arête restent des hypothèses ou limites V8V.

## 4. Résultats dérivés — vol libre

| Cas | Maille projectile (mm) | Énergie de contact max. | Variation relative qdm Z | Éléments érodés | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|
| FF_P100_DT090_T1 | 100 | 0 | 0.000e+00 | 0 | 0.000000 |
| FF_P050_DT090_T1 | 50 | 0 | 0.000e+00 | 0 | 0.000000 |
| FF_P025_DT090_T1 | 25 | 0 | 0.000e+00 | 0 | 0.000000 |

Le vol libre exigeait simultanément : aucune croissance d'énergie de contact, aucune érosion, conservation de la quantité de mouvement et de la masse, aucune masse ajoutée et une erreur d'énergie inférieure à 0,1 % aux trois maillages.

## 5. Résultats dérivés — impact sur la façade simplifiée

| Cas | Maille façade (mm) | Maille projectile (mm) | Impulsion façade (kN·s) | Éléments projectile érodés | Masse projectile restante | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|
| IM_M100_P100_DT090_T1 | 100 | 100 | 134.657 | 268 | 97.046% | -1.748 |
| IM_M050_P050_DT090_T1 | 50 | 50 | 87.608 | 874 | 97.592% | -1.188 |
| IM_M025_P025_DT090_T1 | 25 | 25 | 65.937 | 1397 | 99.038% | -1.077 |
| IM_M050_P050_DT045_T1 | 50 | 50 | 88.555 | 919 | 97.468% | -1.166 |
| IM_M050_P050_DT090_T4 | 50 | 50 | 87.608 | 874 | 97.592% | -1.188 |
| IM_M050_P050_DT090_FLO_T1 | 50 | 50 | 89.533 | 1090 | 96.997% | -1.275 |
| IM_M050_P050_DT090_FHI_T1 | 50 | 50 | 82.901 | 376 | 98.964% | -1.072 |

Écart d'impulsion moyen-fin : **32.866%** (seuil inchangé 10 %). Répétabilité 1/4 fils : **0.000%**. Ordre de rupture basse / nominale / haute : **1090 / 874 / 376**.

## 6. Contradictions, inconnues et décision

- Le bordereau exact du panneau 124, la géométrie et les liaisons JT9D, le contact arête-arête, les ailes, le carburant et le fuselage restent inconnus ou non qualifiés.
- Une terminaison normale du solveur signifie seulement que le calcul s'est achevé ; elle ne prouve pas que le modèle physique réel est correct.
- Le portail global WTC 1, le couplage thermique et la dynamique Blender restent fermés, même si V8W passe.

La prochaine itération doit traiter seulement les portails V8W encore en échec. Une simulation globale n'est autorisée que lorsque l'énergie, la masse, la quantité de mouvement, la répétabilité, la rupture et la convergence d'impulsion passent ensemble.
