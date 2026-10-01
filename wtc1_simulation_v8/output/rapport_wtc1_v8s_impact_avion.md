# WTC 1 — V8S : gel de la reconstitution d’impact du vol AA11

## Conclusion de l’itération

V8S fixe une enveloppe d’entrée traçable et vérifie son échelle cinématique, mais **ne constitue pas encore une simulation de rupture de la tour**. Le cas de base transporte 2.523 GJ et 25.475 MN·s. Le temps purement géométrique nécessaire pour que la queue franchisse la façade nord vaut 0.240 s, contre environ 0,25 s dans la sortie NIST : écart 0.010 s. Ce contrôle valide une échelle de temps, pas les dommages.

Le verrou principal est matériel et documentaire : Blender reste une visualisation, CalculiX 2.22 reste utile pour des contrôles de composants, mais aucun solveur explicite à grande vitesse qualifié n’a été trouvé. Le maillage *as-built* des plaques, assemblages, fenêtres, planchers et contenus de la zone d’impact n’est pas non plus complet.

## 1. Faits officiels transcrits

- NIST retient pour AA11 une masse chargée de 283 600 lb, dont 66 100 lb de carburant.
- L’analyse vidéo donne 443 ± 30 mph, une trajectoire descendante de 10,6° ± 3° et un cap latéral de 180,3° ± 4° par rapport au nord structurel.
- Les dimensions publiées utilisées ici sont 155 ft pour le fuselage et 159 ft 2 in pour l’envergure.
- Les trois enveloppes NIST utilisent 414, 443 et 472 mph avec des facteurs de masse de 0,95, 1,00 et 1,05.

## 2. Résultats du modèle officiel réservés pour comparaison

- Le calcul NIST indique que l’appareil est entièrement entré dans le volume vers 0,25 s, avec environ 30 % du moment initial encore porté par ses constituants.
- Dans le cas de base WTC 1, les ailes sont décrites comme fragmentées par la façade; les deux moteurs terminent à moins de 50 mph, l’un dans le noyau et l’autre entre le noyau et la façade sud.
- Le NIST décrit une petite quantité de débris sortant côté sud, pas un avion intact ni un moteur intact traversant entièrement WTC 1.
- Les 17 400 lb de débris et 6 700 lb de carburant annoncés « hors tour » mélangent rebond côté nord et passage côté sud; ce total ne mesure donc pas la seule sortie opposée.

## 3. Résultats dérivés de V8S

| Cas | Masse (t) | Vitesse (m/s) | Énergie (GJ) | Moment (MN·s) | Queue dans la tour (s) |
|---|---:|---:|---:|---:|---:|
| moins sévère | 122.21 | 185.07 | 2.093 | 22.617 | 0.257 |
| base | 128.64 | 198.04 | 2.523 | 25.475 | 0.240 |
| plus sévère | 135.07 | 211.00 | 3.007 | 28.500 | 0.225 |

Avec 25° de roulis, la projection rigide de l’envergure représente environ 43.3 travées de façade et 5.6 hauteurs d’étage entre les saumons. Ce résultat explique seulement l’ordre de grandeur de l’empreinte verticale; il ne décide pas quels poteaux rompent.

La force moyenne équivalente de 71.3 MN jusqu’à 0,25 s est calculée à partir de la courbe de moment NIST. Elle est donc un résumé de sortie officielle, pas une prédiction indépendante de V8S.

## 4. Inventaire des solveurs

| Outil | Présent | Rôle retenu | Solveur global d’impact qualifié |
|---|:---:|---|:---:|
| Blender | oui | visualisation et animation uniquement | non |
| FreeCAD | oui | pré/post-traitement géométrique | non |
| CalculiX | oui | solveur structurel pour contrôles de composants et quasi-statiques | non |
| LS-DYNA | non | solveur explicite non linéaire de référence à grande vitesse | oui |
| Abaqus Explicit | non | solveur explicite non linéaire candidat à grande vitesse | oui |
| OpenRadioss | non | solveur explicite non linéaire candidat à grande vitesse | oui |

## 5. Hypothèses propres à V8S

- Tous les composants de l’avion partagent initialement la même vitesse de translation; leur part d’énergie cinétique suit donc leur part de masse.
- Le diagnostic réduit de silhouette projette une envergure rigide et non déformée selon le roulis; ce n’est pas un calcul de rupture ni de dommages de façade.
- L’estimation du franchissement de la queue projette la longueur du fuselage sur la direction de vitesse et néglige la flexion locale avant impact.
- Aucune sortie NIST de dommage, moment, débris ou pénétration ne règle les calculs cinématiques V8S.

## 6. Affirmations provenant des archives locales

Aucune affirmation de l’archive locale n’est utilisée comme entrée numérique dans V8S. Les originaux n’ont pas été modifiés.

## 7. Contradictions, dépendances et inconnues

- La position, l’orientation du fuselage et le roulis final du jeu NIST ont été raffinés à partir de l’empreinte de dommages observée. Leur réutilisation ne peut donc pas valider indépendamment cette même empreinte.
- L’analyse NIST elle-même signale un maillage plus grossier sur la face opposée, l’absence des fenêtres, des contenus partiels, l’absence de résistance aérodynamique et de mouillage du carburant, et l’absence de déflagration du carburant dans le calcul d’impact.
- La distribution de débris publiée omet environ 18 000 lb d’éléments érodés selon le texte; les totaux arrondis laissent un écart comptable plus grand. V8S conserve cette différence comme incertitude au lieu de la corriger silencieusement.
- L’absence actuelle d’un solveur explicite et d’un maillage de rupture complet empêche de trancher la pénétration, la carte de dommages ou l’hypothèse d’explosifs.

## 8. Métriques préenregistrées

- **M01_energy_balance** — erreur absolue du bilan travail externe + énergie interne + énergie cinétique résiduelle, divisée par l’énergie cinétique initiale ; seuil : inférieure ou égale à 0,05.
- **M02_tail_clearance_time** — écart absolu entre temps prédit et temps rapporté ; seuil : inférieur ou égal à 0,03 s.
- **M03_north_facade_damage** — précision, rappel, F1 et intersection-sur-union à la résolution élément-par-étage ; seuil : F1 supérieur ou égal à 0,80, sans utiliser d’entrée raffinée sur les dommages pour un test indépendant.
- **M04_core_damage** — score de classification pondéré par étage pour les états intact, léger, modéré, lourd et sectionné ; seuil : macro-F1 supérieur ou égal à 0,70; publier chaque cas séparément.
- **M05_momentum_history** — RMSE sur 0,00-0,70 s et fraction résiduelle à 0,25 s ; seuil : RMSE inférieure ou égale à 0,10.
- **M06_debris_by_floor** — distance L1 normalisée et distance de transport sur les étages 92-99 plus l’extérieur ; seuil : diagnostic seulement tant que l’érosion numérique et les fenêtres ne sont pas harmonisées.
- **M07_far_side_categories** — masses et trajectoires séparées pour carburant, moteurs, trains d’atterrissage, fragments d’avion et débris de tour ; seuil : aucune étiquette « avion intact sortant »; tout objet sortant conserve catégorie et provenance.
- **M08_post_impact_stability** — la structure endommagée à froid reprend les charges gravitaires avant couplage thermique ; seuil : obligatoire avant le couplage incendie-effondrement.

## 9. Portes de validation

| Porte | État |
|---|:---:|
| `source_files_present_and_hashed` | PASS |
| `input_integrity_passed` | PASS |
| `tail_clearance_scale_check_passed` | PASS |
| `validation_metrics_predeclared` | PASS |
| `damage_outputs_reserved_from_input_calculation` | PASS |
| `independent_facade_validation_available_with_refined_nist_orientation` | FAIL |
| `as_built_impact_zone_mesh_complete` | FAIL |
| `solver_ready_for_global_high_rate_impact` | FAIL |
| `global_aircraft_impact_replay_ready` | FAIL |
| `thermal_or_blender_coupling_authorized` | FAIL |

**Décision : porte globale V8S fermée.** La prochaine itération doit construire un paquet de solveur explicite indépendant du rendu Blender, en commençant par un sous-assemblage aile/moteur–panneau de façade et une étude de convergence avant toute tour complète.

## 10. Reproductibilité

- Configuration : `wtc1_simulation_v8/data/v8s_wtc1_aircraft_impact_replay.json`
- Script : `wtc1_simulation_v8/scripts/run_v8s_wtc1_aircraft_impact_replay.py`
- Résultats : `wtc1_simulation_v8/output/resultats_wtc1_v8s_impact_avion.json`
- Graphique : `wtc1_simulation_v8/output/synthese_wtc1_v8s_impact_avion.png`
- Graine déclarée : `9112001` (aucun tirage aléatoire dans V8S)
- Durée : 0.051 s
