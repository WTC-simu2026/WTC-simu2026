# V11J — coupon de conduction transitoire 1D

## Résultat

V11J passe 31/31 contrôles numériques. Le coupon conservatif calcule la conduction transitoire dans 4,35 in (0.11049 m) d'épaisseur équivalente, sur 1 m², avec propriétés constantes. Les cinq cas incluent deux contrôles stationnaires, deux champs transitoires à solution analytique et un contrôle à flux imposé avec solution analytique de température moyenne.

La température calculée reste séparée du panneau V11I. Aucun résultat de cette itération n'est une température de gaz, une exposition d'incendie, une température historique du WTC1, une contrainte, une rupture ou une validation d'effondrement.

## 1. Faits directement observés ou transcrits

NIST NCSTAR 1-5G indique, dans son modèle officiel, une épaisseur équivalente de dalle de 4,35 in et décrit un maillage thermique d'environ 16 éléments dans l'épaisseur afin de résoudre l'onde thermique et les forts gradients de surface. Cette information borne la géométrie et motive le premier niveau de raffinement ; elle ne transforme pas le coupon V11J en reproduction du modèle NIST.

NIST NCSTAR 1-5F emploie k=1,0 W/(m·K), rho=2 000 kg/m³ et cp=0,88 kJ/(kg·K) pour représenter la dalle comme condition de bord du calcul de gaz, tout en renvoyant le calcul détaillé de pénétration à une analyse séparée. NIST TN 1681 donne, pour des estimations constantes simples, 0,5 W/(m·K) pour un béton léger et 1,3 W/(m·K) pour un béton courant, avec des réserves sur densité, granulats, humidité et essais à petite échelle.

## 2. Résultats d'un modèle officiel

Les valeurs et choix NIST ci-dessus sont des entrées ou pratiques de modèles officiels, pas des mesures individualisées de la dalle modélisée ici. Aucun champ de température NIST n'est importé dans V11J.

## 3. Affirmations provenant des archives locales

Aucune archive locale, photographie ou vidéo n'est analysée. Les trois références primaires ont été consultées par leurs publications NIST en ligne et sont enregistrées dans le manifeste de sources.

## 4. Hypothèses propres au modèle

La masse volumique rho=2400 kg/m³ et la chaleur massique cp=900 J/(kg·K) sont reprises telles quelles des hypothèses génériques V11H. La conductivité de référence k=1.0 W/(m·K) est constante ; la sensibilité couvre 0,5, 1,0 et 1,3 W/(m·K). Cette combinaison n'est pas un matériau WTC calibré.

Le domaine est homogène, unidimensionnel, sans tôle de deck, armature, humidité, chaleur latente, contact, convection, rayonnement ou SFRM. Euler implicite avance les volumes finis centrés. La convention est q entrant positif à chaque face. Par unité de surface, H=rho·cp·Σ(Ti−Tref)·dx et chaque pas vérifie ΔH=dt(qbas,entrant+qhaut,entrant).

## 5. Résultats dérivés

| Cas | Cellules × pas | Fo final | T moyenne finale (°C) | Min / max (°C) | Erreur L∞ analytique (K) | ΔH (MJ/m²) | ∫q dt (MJ/m²) | Résidu énergie relatif |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UNIFORM_ADIABATIC_CONTROL | 64 × 1600 | 0.136522 | 60.000000 | 60.0000 / 60.0000 | 1.42109e-14 | 0.000000 | 0.000000 | 0.000e+00 |
| LINEAR_DIRICHLET_STEADY_CONTROL | 64 × 1600 | 0.136522 | 70.000000 | 20.7812 / 119.2187 | 2.84217e-14 | 0.000000 | 0.000000 | 7.408e-08 |
| SINE_DIRICHLET_TRANSIENT | 64 × 1600 | 0.068261 | 45.974415 | 21.0012 / 60.7841 | 0.0112961 | -5.956981 | -5.956981 | 7.172e-14 |
| CONSTANT_TOP_FLUX_BOTTOM_ADIABATIC | 64 × 1600 | 0.068261 | 27.542161 | 20.1716 / 51.7150 | — | 1.800000 | 1.800000 | 2.057e-13 |
| TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC | 64 × 1600 | 0.068261 | 49.472051 | 21.3691 / 118.3122 | 0.0201686 | 7.033753 | 7.033753 | 3.396e-14 |

Le résidu incrémental absolu maximal est 4.103e-09 J/m². Le résidu total absolu maximal est 2.524e-07 J/m² et le maximum relatif hors bilan nul 2.057e-13.

Le contrôle uniforme adiabatique reste à 60 °C et échange exactement 0 J/m². Le profil linéaire 20–120 °C reste stationnaire ; ses flux de face, opposés, valent ±k·100/L. Le flux supérieur constant de 1 000 W/m² pendant 1 800 s apporte 1,800000 MJ/m² et élève la moyenne à la valeur analytique.

### Raffinement

| Diagnostic | Ordres observés successifs | Attendu |
|---|---|---|
| Opérateur spatial, mode sinus, temps exact | 1.994554 / 1.998641 / 1.999660 | 2 |
| Euler implicite, SINE_DIRICHLET_TRANSIENT | 0.992242 / 0.988160 / 0.978365 | 1 |
| Euler implicite, TOP_STEP_DIRICHLET_BOTTOM_ADIABATIC | 0.992618 / 0.985131 / 0.970631 | 1 |

Le contrôle spatial emploie la valeur propre exacte de l'opérateur volumes finis pour isoler l'erreur spatiale de l'erreur temporelle. Les contrôles temporels utilisent 256 cellules et 100, 200, 400 puis 800 pas.

### Sensibilité à la conductivité — même palier synthétique de 1 800 s

| k (W/m·K) | Diffusivité (m²/s) | T moyenne (°C) | Cellule basse (°C) | Profondeur du centroïde thermique depuis le haut (mm) | ΔH (MJ/m²) |
|---:|---:|---:|---:|---:|---:|
| 0.500 | 2.314815e-07 | 40.835222 | 20.027082 | 18.0990 | 4.972501 |
| 1.000 | 4.629630e-07 | 49.472051 | 21.369131 | 25.5295 | 7.033753 |
| 1.300 | 6.018519e-07 | 53.605009 | 23.532776 | 28.9627 | 8.020118 |

Ces trois réponses sont une sensibilité paramétrique conditionnelle, pas des probabilités ni trois scénarios d'incendie.

## 6. Contradictions, limites et informations manquantes

Une température prescrite de face ou un flux imposé ne calcule pas un incendie. Il manque les températures de gaz et flux nets sourcés, les coefficients convectifs, l'émissivité et les facteurs de vue, le rayonnement, l'état du SFRM, la tôle, l'humidité et les propriétés dépendantes de la température. Les valeurs constantes ne sont valides que comme vérification bornée.

Aucune température V11J n'est appliquée au panneau V11I. Aucune propriété mécanique ou endommagée n'est changée ; aucune énergie mécanique, fissuration chaude, localisation complète, rupture, impact, initiation, arrêt ou propagation d'effondrement n'est calculée. Blender reste une visualisation inchangée.

## Suite bornée

V11K : qualifier séparément des conditions de surface convectives et radiatives sur le coupon, d'abord avec cas synthétiques et références analytiques ou manufacturées, puis bilan de puissance et sensibilité. Conserver les propriétés constantes de V11J comme contrôle, ne rattacher aucune courbe à un incendie WTC sans flux net ou température de gaz primaire sourcé, et ne coupler au panneau qu'après qualification.

## Sources primaires utilisées

- [NIST_NCSTAR_1_5G](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-5g.pdf) — Chapter 6 p.98 and Appendix A p.274 of the report pagination; Primary official model report: 4.35 in equivalent slab thickness; approximately 16 through-depth thermal elements were used to resolve thermal waves and steep surface gradients; lightweight-concrete conductivity was temperature dependent in the official thermal model. V11J does not reproduce that model.
- [NIST_NCSTAR_1_5F](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-5f.pdf) — Chapter 5 p.52; Primary official fire-model report: the exposed slab underside used k=1.0 W/(m K), rho=2000 kg/m3 and cp=0.88 kJ/(kg K) as gas-phase boundary properties, while detailed member penetration was calculated separately. Only k=1.0 is used here as a numerical anchor, not as an as-built calibration.
- [NIST_TN_1681](https://doi.org/10.6028/NIST.TN.1681) — Section 4.2.1.1.1 p.64; Primary NIST design guidance: simple averaged constant conductivity estimates of 1.3 W/(m K) for normal-weight and 0.5 W/(m K) for lightweight normal-strength concrete, with cautions about density, aggregate, moisture and small-scale data. Used only to bracket conductivity sensitivity.

Exécution : 3.588 s sur CPU ; Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0. Graine 1101010, sans tirage. Empreinte numérique : e5a62e868a1448268eb389512a5ca90015d662316636c11342924122775513a4. Aucun GPU, solveur externe, Blender ou rescannage d'archive.
