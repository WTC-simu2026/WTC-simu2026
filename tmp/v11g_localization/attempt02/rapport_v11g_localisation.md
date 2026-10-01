# V11G — localisation longitudinale et équilibre local

## Résultat

Le benchmark à une seule zone de fissuration choisie passe sur 16 parcours : deux longueurs, quatre maillages et deux histoires de chargement. 81/81 contrôles numériques passent. Le travail extérieur, l'énergie stockée et la dissipation sont vérifiés séparément. La rupture complète consomme 1.000000 J pour cette section générique de 0,01 m², indépendamment de la largeur numérique de sa bande.

Le diagnostic séparé des efforts locaux du panneau V11F est PASS : 14/14 cas passent au maillage 8 les seuils choisis de 5 % pour N et M aux points de Gauss. Éventuels cas au-dessus : aucun. Ces critères locaux sont nouveaux ; ils ne remplacent pas les comparaisons globales V11F, qui restent enregistrées telles quelles.

Le témoin de déformation uniforme forcée dissipe une énergie proportionnelle au nombre de bandes. Il est rejeté comme représentation d'une seule fissure. Le benchmark ne choisit pas spontanément une fissure, ne valide pas la fracture complète du panneau et ne modifie ni la mécanique V11F ni l'animation.

## 1. Constats et données transcrites

Les résultats V11F, leurs entrées et leurs empreintes sont relus, sans nouvel examen de PDF, photo, vidéo ou archive. Le contrôle porte sur les états terminaux déjà sauvegardés des 14 parcours aux maillages 2, 4 et 8. Les forces de contact et d'attaches et les réactions des actionneurs sont celles de ces calculs, pas de nouvelles mesures.

## 2. Résultats officiels et sources de méthode

Aucun résultat historique officiel supplémentaire n'est introduit. Les héritages NIST du panneau restent dépendants des transcriptions et hypothèses antérieures. Le rapport de l'énergie de traction à la largeur de bande est décrit dans [DIANA — paramètres du modèle](https://manuals.dianafea.com/d110/en/1465843-1466551-model-parameters.html). La distinction entre équilibre intégré et ponctuel des efforts de section est explicite dans [OpenSees — élément à déplacements](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/dispBeamColumn.html). Aucun de ces logiciels n'est exécuté ; les formules et contrôles ci-dessous appartiennent au projet.

## 3. Archives

Aucune nouvelle affirmation d'archive ou identification de mécanisme ne participe à V11G.

## 4. Hypothèses et dérivation du benchmark

Barres génériques de 2 m et 8 m, section 0,01 m² (100 cm²), à 20 °C. Ces dimensions sont des choix d'essai, pas des composants WTC identifiés. E = 2500 ksi, ft = 1 MPa et Gf = 100 J/m² reprennent les hypothèses V11E ; fc = 3 ksi est conservé dans les données, mais aucune compression n'est exercée ici. Les unités originales et leur conversion sont enregistrées dans material_input_ledger.json.

Une seule cellule centrale est autorisée à fissurer ; les autres sont élastiques. Les maillages impairs 9 / 17 / 33 / 65 gardent sa position au milieu de la barre. Sa largeur h = L/n est numérique, pas une largeur physique de fissure mesurée. Ce test vérifie une stratégie à fissure sélectionnée, pas une loi capable d'en découvrir le nombre ou la position.

La loi V11E inchangée est intégrée dans cette bande. Son ouverture inélastique est w = h(ε − σ/E), et sa déformation totale reste ε. Après le pic, on résout cette relation par Newton encadré depuis le dernier état engagé, puis on impose l'équilibre en série : même force dans toutes les cellules. Leurs déplacements sont reconstruits et les résidus nodaux vérifiés. Aucun essai numérique refusé n'est engagé.

Comparateur fermé, dérivé séparément : wc = 2Gf/ft ; σ = ft(1 − w/wc) entre 0 et wc ; P = Aσ ; déplacement total Δ = Lσ/E + w. La décharge/recharge suit une sécante en ouverture jusqu'à l'ouverture maximale déjà atteinte. L'intégrale de la traction sur l'ouverture est Gf. À séparation complète, l'énergie stockée est nulle et le travail extérieur net comme la dissipation valent AGf.

Ici wc = 0.200000 mm. La dérivée dΔ/dw après le pic vaut 1 − L/Lcrit, avec Lcrit = 2EGf/ft² = 3.447378647 m. La barre de 2 m adoucit avec Δ croissant ; celle de 8 m a un retour en déplacement (snapback). L'ouverture est un paramètre de continuation pour suivre les états d'équilibre, pas un vérin intérieur auquel on aurait oublié d'attribuer un travail. Ce parcours ne prouve pas sa stabilité sous un chargement physique libre ni une dynamique de rupture.

Montée élastique jusqu'au pic, puis ouverture monotone 0 / wc / 1,1wc ; cycle 0 / 0,75wc / 0 / 0,75wc / wc / 1,1wc. Les sommets sont inclus explicitement pour le bilan de travail par trapèzes. Le demi-pas et la répétition exacte sont calculés. Pas d'armature, adhérence, flexion, chaleur, vitesse ou paramètres ajustés à l'effondrement.

### Témoin volontairement non localisé

La même déformation est imposée à toutes les cellules. Avec g points identiques par cellule et Lch = L/(n·g), l'énergie finale vaut n·g·AGf. Deux points partageant le même champ axial constant peuvent donc représenter deux bandes dissipatives malgré l'unique cellule ; ils ne constituent pas automatiquement deux fissures physiques. Ce témoin représente une branche homogène forcée, pas une prédiction de fissuration spontanée.

| Cellules | Points par cellule | Bandes simultanées | Dissipation (J) | Une seule fissure ? |
|---:|---:|---:|---:|---|
| 9 | 1 | 9 | 9.000000 | Interprétation rejetée |
| 9 | 2 | 18 | 18.000000 | Interprétation rejetée |
| 17 | 1 | 17 | 17.000000 | Interprétation rejetée |
| 17 | 2 | 34 | 34.000000 | Interprétation rejetée |
| 33 | 1 | 33 | 33.000000 | Interprétation rejetée |
| 33 | 2 | 66 | 66.000000 | Interprétation rejetée |
| 65 | 1 | 65 | 65.000000 | Interprétation rejetée |
| 65 | 2 | 130 | 130.000000 | Interprétation rejetée |

## 5. Résultats dérivés et contrôle du panneau

| Longueur | Cellules | Parcours | États | Dissipation finale (J) | Retour en déplacement au premier adoucissement ? |
|---:|---:|---|---:|---:|---|
| 2 m | 9 | monotonic | 149 | 1.000000000 | Non |
| 2 m | 9 | cyclic | 341 | 1.000000000 | Non |
| 2 m | 17 | monotonic | 149 | 1.000000000 | Non |
| 2 m | 17 | cyclic | 341 | 1.000000000 | Non |
| 2 m | 33 | monotonic | 149 | 1.000000000 | Non |
| 2 m | 33 | cyclic | 341 | 1.000000000 | Non |
| 2 m | 65 | monotonic | 149 | 1.000000000 | Non |
| 2 m | 65 | cyclic | 341 | 1.000000000 | Non |
| 8 m | 9 | monotonic | 149 | 1.000000000 | Oui |
| 8 m | 9 | cyclic | 341 | 1.000000000 | Oui |
| 8 m | 17 | monotonic | 149 | 1.000000000 | Oui |
| 8 m | 17 | cyclic | 341 | 1.000000000 | Oui |
| 8 m | 33 | monotonic | 149 | 1.000000000 | Oui |
| 8 m | 33 | cyclic | 341 | 1.000000000 | Oui |
| 8 m | 65 | monotonic | 149 | 1.000000000 | Oui |
| 8 m | 65 | cyclic | 341 | 1.000000000 | Oui |

Erreur maximale de travail extérieur, divisée par l'énergie physique AGf : 8.438e-15. Écart maximal de force au comparateur, divisé par Aft : 3.783e-16. Ces normalisations sont fixées par le problème, pas par un plancher d'énergie arbitraire.

### Équilibre intégré et efforts locaux V11F

Sur la dalle seule, le contact et les attaches exercent l'opposé de leurs efforts internes enregistrés. Chaque attache horizontale apporte aussi le couple −e·F. On ajoute la gravité répartie et l'actionneur de dalle lorsqu'il existe ; l'actionneur du treillis n'est pas appliqué une seconde fois à la dalle. Les bilans horizontaux, verticaux et de moments sont vérifiés sans mélanger N et N·m.

La reconstruction statique par une coupe à x donne N(x) = −ΣFx à gauche et M(x) = ΣFy(x − xi) − ΣC + qx²/2. Les sauts dus aux actions ponctuelles sont conservés. On compare ce champ équilibré aux N/M constitutifs aux mêmes points de Gauss. Un second calcul assemble les efforts constitutifs aux nœuds avec leurs fonctions de forme et la charge répartie cohérente pour vérifier l'équilibre faible.

Le champ récupéré est seulement un diagnostic. Il n'est pas substitué aux contraintes issues des matériaux et ne fournit aucune énergie, résistance ou redistribution supplémentaire au modèle.

| Cas | Maillage | Écart N max / pic N équilibré (%) | Écart M max / pic M équilibré (%) | Résidu nodal normalisé | Critères locaux |
|---|---:|---:|---:|---:|---|
| COLD_PLAIN | 2 | 0.000000 | 0.000000 | 2.985e-13 | PASS |
| COLD_R02 | 2 | 0.000000 | 0.000000 | 1.521e-13 | PASS |
| BEND_PLAIN | 2 | 0.000000 | 0.000000 | 1.716e-13 | PASS |
| BEND_R01 | 2 | 0.000000 | 0.000000 | 2.664e-13 | PASS |
| BEND_R02 | 2 | 0.000000 | 0.000000 | 2.415e-13 | PASS |
| BEND_R04 | 2 | 0.000000 | 0.000000 | 2.656e-13 | PASS |
| BEND_TOP | 2 | 0.404867 | 0.000000 | 2.172e-13 | PASS |
| CYCLE_R02 | 2 | 0.000000 | 0.000000 | 2.212e-13 | PASS |
| TRUSS_LOWER_R02 | 2 | 1.932677 | 0.000000 | 1.857e-13 | PASS |
| TRUSS_LOWER_PLAIN | 2 | 1.845413 | 0.000000 | 3.273e-13 | PASS |
| TRUSS_LOWER_R01 | 2 | 1.890240 | 0.000000 | 2.915e-13 | PASS |
| TRUSS_LOWER_R04 | 2 | 2.012555 | 0.000000 | 2.541e-13 | PASS |
| TRUSS_LOWER_TOP | 2 | 2.331305 | 0.000000 | 2.835e-13 | PASS |
| TRUSS_CYCLE_R02 | 2 | 0.020447 | 0.000000 | 2.143e-13 | PASS |
| COLD_PLAIN | 4 | 0.000000 | 0.000000 | 4.615e-13 | PASS |
| COLD_R02 | 4 | 0.000000 | 0.000000 | 4.263e-13 | PASS |
| BEND_PLAIN | 4 | 0.000000 | 0.000000 | 4.373e-13 | PASS |
| BEND_R01 | 4 | 0.000000 | 0.000000 | 4.084e-13 | PASS |
| BEND_R02 | 4 | 0.000000 | 0.000000 | 4.870e-13 | PASS |
| BEND_R04 | 4 | 0.000000 | 0.000000 | 4.973e-13 | PASS |
| BEND_TOP | 4 | 0.223629 | 0.000000 | 3.421e-13 | PASS |
| CYCLE_R02 | 4 | 0.000000 | 0.000000 | 3.850e-13 | PASS |
| TRUSS_LOWER_R02 | 4 | 1.288094 | 0.000000 | 4.644e-13 | PASS |
| TRUSS_LOWER_PLAIN | 4 | 1.259460 | 0.000000 | 6.453e-13 | PASS |
| TRUSS_LOWER_R01 | 4 | 1.275023 | 0.000000 | 7.650e-13 | PASS |
| TRUSS_LOWER_R04 | 4 | 1.314754 | 0.000000 | 7.367e-13 | PASS |
| TRUSS_LOWER_TOP | 4 | 1.497616 | 0.000000 | 4.602e-13 | PASS |
| TRUSS_CYCLE_R02 | 4 | 0.039694 | 0.000000 | 4.069e-13 | PASS |
| COLD_PLAIN | 8 | 0.000000 | 0.000000 | 2.968e-12 | PASS |
| COLD_R02 | 8 | 0.000000 | 0.000000 | 1.922e-12 | PASS |
| BEND_PLAIN | 8 | 0.000000 | 0.000000 | 3.610e-12 | PASS |
| BEND_R01 | 8 | 0.000000 | 0.000000 | 4.940e-12 | PASS |
| BEND_R02 | 8 | 0.000000 | 0.000000 | 5.584e-12 | PASS |
| BEND_R04 | 8 | 0.000000 | 0.000000 | 2.736e-12 | PASS |
| BEND_TOP | 8 | 0.117113 | 0.000000 | 3.390e-12 | PASS |
| CYCLE_R02 | 8 | 0.000000 | 0.000000 | 2.564e-12 | PASS |
| TRUSS_LOWER_R02 | 8 | 0.710082 | 0.000000 | 6.953e-12 | PASS |
| TRUSS_LOWER_PLAIN | 8 | 0.700555 | 0.000000 | 4.257e-12 | PASS |
| TRUSS_LOWER_R01 | 8 | 0.703887 | 0.000000 | 2.813e-12 | PASS |
| TRUSS_LOWER_R04 | 8 | 0.716995 | 0.000000 | 6.442e-12 | PASS |
| TRUSS_LOWER_TOP | 8 | 0.813986 | 0.000000 | 7.379e-12 | PASS |
| TRUSS_CYCLE_R02 | 8 | 0.024299 | 0.000000 | 2.048e-12 | PASS |

Normalisation séparée par le pic absolu du champ équilibré de chaque cas/maillage : plancher 1 N pour N et 1 N·m pour M. Les écarts sont évalués seulement aux points de Gauss terminaux, pas partout ni à tous les instants. Chaque maillage a son propre état d'arrêt, généralement très proche mais pas strictement identique ; ne pas confondre ce diagnostic avec une comparaison à déplacement final exactement égal.

**Pourquoi les écarts M affichés sont-ils presque nuls ?** Avec deux points de Gauss, une charge q constante et aucune action ponctuelle à l'intérieur de la cellule, le moment quadratique équilibré et son interpolant linéaire passent par les mêmes valeurs aux deux points. Ce résultat est structurel à l'échantillonnage, pas une validation indépendante de tous les moments de matériau. Aux extrémités de cellule, leur écart vaut |q|·dx²/12, qui n'est pas nul. Un contrôle analytique supplémentaire confirme cet angle mort.

L'écart d'interpolation d'extrémité ainsi calculé atteint au maximum 353.001201 / 88.250300 / 22.062575 N·m sur les maillages 2 / 4 / 8. C'est une comparaison avec l'interpolant linéaire des valeurs de Gauss, PAS une contrainte constitutive postfissurée récupérée entre les points. On ne l'ajoute ni aux énergies ni aux résistances, et les critères initiaux restent inchangés.

Résidu nodal maximal reconstruit : 7.379e-12. Des défauts volontaires (oubli du couple excentré ou de l'actionneur de dalle) sont détectés par les contrôles. Un bon équilibre global ne suffit donc pas à garantir les efforts locaux, et un écart local de formulation faible n'est pas automatiquement une erreur de convergence de Newton.

## 6. Inconnues et suite

La barre démontre une normalisation cohérente de l'énergie pour une seule fissure sélectionnée. Elle ne transfère pas cette validation à la flexion fissurée du panneau V11F : une stratégie de localisation en flexion, les interactions d'armature/adhérence et les fissures multiples restent à vérifier avant d'utiliser sa séparation complète comme résistance globale. Les 42 états de panneau servent à borner les efforts locaux de leurs parcours actuels, pas la propagation d'un effondrement.

V11H : commencer le couplage thermomécanique borné, avec dilatation libre/empêchée et gradient de dalle, propriétés thermiques explicites et bilans adaptés. Préserver le contrôle froid V11F et limiter les revendications au domaine vérifié ; la localisation en flexion après fracture complète reste non validée. Ensuite instabilités géométriques, assemblages, impact calculé et feux spatialement résolus.

Exécution finale : 6.296 s sur CPU ; Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0. Graine 1101007, sans tirage aléatoire. Empreinte numérique : e3c1098f7377909d8bf56471258e6a5f872108282f6f5415342127fef37b4011. Aucune installation, archive modifiée, revue multi-agent ou dynamique Blender exécutée.

## Livrables

results_v11g.json, bar_paths.json, bar_half_step_paths.json, uniform_damage_controls.json, panel_equilibrium_recovery.json, material_input_ledger.json, numerical_audit.json, source_manifest.json, offline_manifest.json et synthese_v11g_localisation.png. L'audit séparé des fichiers sauvegardés est ajouté dans release_audit.json avant publication locale.
