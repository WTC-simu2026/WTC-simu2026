# V11I — couplage thermoélastique borné d'un panneau

## Résultat

V11I passe 32/32 contrôles numériques et son audit de fichiers doit être exécuté séparément avant publication. Un seul panneau équivalent V11F R02 reçoit les déformations thermiques V11H de la dalle, à 25 % de la gravité de référence. Trois parcours sont calculés : DeltaT=0, température uniforme et gradient dans l'épaisseur.

Les états acceptés restent sous le garde-fou DCR=0,90. Une tentative qui atteint ce seuil est seulement utilisée pour le borner ; elle n'est pas engagée. Aucune fissuration, plastification, rupture ou propriété dégradée n'est calculée.

## 1. Faits directement observés ou transcrits

Le point COLD_R02 sauvegardé par V11F à un facteur de gravité 0,25 contient une énergie mécanique de 123.542425359 J, une flèche de dalle de 10.793292 mm et une réaction verticale de 35.239800 kN. V11I le relit par empreinte et le reproduit sans relancer le pilote V11F.

Le panneau conserve 33 nœuds de treillis, 63 barres, 65 nœuds de dalle, 64 éléments de dalle, 128 sections de Gauss et 17 stations de contact au maillage de référence. Les anciens fichiers V11F/V11H et le fichier Blender maître sont protégés par empreinte.

## 2. Résultats d'un modèle officiel

Aucun nouveau résultat officiel n'est introduit. Les géométries équivalentes et capacités déjà héritées restent dépendantes de leurs transcriptions et hypothèses antérieures.

## 3. Affirmations provenant des archives locales

Aucune archive, photographie, vidéo ou nouvelle donnée historique n'est examinée dans V11I.

## 4. Hypothèses propres au modèle

La dalle seule reçoit un champ uniforme ou linéaire dans l'épaisseur, identique le long de la portée. Le treillis, les sièges, les contacts et les attaches restent à 20 °C. Les propriétés thermoélastiques constantes sont celles de V11H et le ferraillage R02 reste exploratoire, non as-built.

La déformation de section est eps(y)=eps0-y*kappa ; eps_th=alpha*DeltaT ; sigma=E(eps-eps_th). Les résultantes de section sont intégrées aux deux points de Gauss de chaque élément. Le béton est seulement élastique jusqu'aux écrans froids ft/fc ; l'armature seulement élastique jusqu'à fy. Les composants gardent leurs lois élastiques V11F.

L'énergie mécanique du panneau additionne dalle et ressorts. Le travail mécanique extérieur intègre la gravité ; le travail thermoélastique vaut moins l'intégrale de sigma d eps_th dans la dalle. Leur somme doit égaler l'énergie mécanique stockée. L'enthalpie sensible est enregistrée séparément et n'entre pas dans ce bilan. Les appuis fixes ont un travail nul, même avec réactions non nulles.

## 5. Résultats dérivés

| Parcours | État terminal | Échelle thermique | Faces dalle (°C) | DCR max | Gouvernant | Flèche bas/haut dalle (mm) | Réaction V/H (kN) | U (kJ) | Wthermo (kJ) | H sensible (MJ) |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| COLD_DELTA_T_ZERO | TARGET_REACHED_WITHIN_ELASTIC_GUARD_NOT_SAFETY_PROOF | 1.00000000 | 20.000/20.000 | 0.147129378 | web / STEEL-062 | 10.7933/-0.1780 | 35.2398/-0.0000 | 0.123542 | 0.000000 | 0.000000 |
| SLAB_UNIFORM_100K | TARGET_REACHED_WITHIN_ELASTIC_GUARD_NOT_SAFETY_PROOF | 1.00000000 | 120.000/120.000 | 0.502247419 | slab_concrete_tension_elastic_guard / SLAB-000-END-0-TOP | 0.1809/20.6446 | 35.2398/0.0000 | 1.831685 | 2.422429 | 880.334828 |
| SLAB_GRADIENT_TOP_100K | SAFE_DCR_GUARD_REACHED_BEFORE_NOMINAL_LIMIT | 0.08235463 | 20.000/28.235 | 0.899999873 | slab_concrete_tension_elastic_guard / SLAB-003-END-1-BOTTOM | 9.0358/-0.1811 | 35.2398/-0.0000 | 0.144147 | 0.061586 | 36.249822 |

Résidu d'équilibre maximal : 1.924e-12. Résidu incrémental maximal du bilan énergie : 8.476e-09. Résidu total maximal : 6.346e-11.

Le demi-pas passe 3/3 parcours. Le raffinement 4 vers 8 subdivisions passe 3/3 parcours. Le maillage 2 reste un diagnostic grossier séparé.

## 6. Contradictions, limites et informations manquantes

La température est imposée, non calculée. Il manque une conduction transitoire validée, les échanges de surface, l'état SFRM, l'humidité et une histoire d'incendie. L'arrêt à 0,90 n'est ni une température critique réelle ni une prédiction de rupture : sa valeur dépend des propriétés, capacités et détails hypothétiques du panneau.

La loi V11E endommagée n'est jamais appelée à chaud. Avant toute fissuration chauffée, il faut formuler une énergie libre dépendant de la température et de l'historique, ses forces thermodynamiques et l'irréversibilité. La localisation en flexion après fracture complète reste non validée.

Ce panneau local à petits déplacements ne valide ni la structure spatiale, ni l'impact, ni l'incendie, ni l'initiation, l'arrêt ou la propagation d'un effondrement réel. Blender reste inchangé et sans crédit mécanique.

## Suite bornée

V11J : qualifier un coupon unidimensionnel de conduction transitoire dans l'épaisseur de la dalle équivalente, d'abord avec propriétés constantes et références analytiques, puis bilan flux-enthalpie et raffinement espace-temps. Ne relier aucun flux à un incendie WTC avant de disposer de conditions aux limites sourcées ; ne pas activer de fissuration chaude.

Exécution : 13.746 s sur CPU ; Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0. Graine 1101009, sans tirage aléatoire. Empreinte numérique : f44bf662b31a9d9058125f6fdb7935a28fe8a1a6c30b4f014f0e6df3cbebfa53. Aucun GPU, solveur externe, réseau, rescannage d'archive ou Blender.
