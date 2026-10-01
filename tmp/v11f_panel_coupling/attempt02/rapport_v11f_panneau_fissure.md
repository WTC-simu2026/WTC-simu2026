# V11F — couplage à froid de la dalle fissurable au panneau

## Résultat et niveau de vérification

La dalle postfissurée V11E est assemblée au treillis et aux liaisons V11D : N et M sont calculés ensemble à chaque section ; contact et attaches réagissent aux déplacements indépendants. 14 parcours et 713 états de référence ; 132/132 contrôles de calcul passent, dont 62 régressions constitutives V11E. Ce nombre n'est pas une validation expérimentale ou historique.

Le contrôle SPATIAL séparé est **PASS** : 14/14 cas passent toutes les exigences de comparaison 4→8. Cas concernés par un échec : aucun. Contrôle de demi-pas : PASS ; cas concernés : aucun. Un calcul dont l'équilibre est correct peut encore être dépendant du maillage ; ces deux résultats ne sont pas fusionnés.

Aucun calcul d'avion, d'incendie, de propagation globale ou de dynamique Blender n'est modifié. Un seuil de membrure dans ce prototype ne signifie pas un effondrement du plancher.

## 1. Faits transcrits et constats directs

Les entrées conservées décrivent la paire équivalente de treillis de 713 in de portée, 80 in de largeur tributaire et dalle de 4,35 in. Les hypothèses géométriques de V11D sont reprises : 16 panneaux idéaux, 63 barres, 17 stations de liaison et 32 knuckles équivalents. La résistance et le ferraillage réels de chaque plancher ne sont pas documentés par cet ajout. Aucun PDF ni média d'archive n'est réanalysé ; empreintes des entrées et anciennes sorties conservées.

## 2. Résultats officiels et sources de méthode

Les tables déjà transcrites de sièges et de knuckles NIST sont des écrans de capacités hérités, pas de nouvelles observations ni des essais incendie reproduits. Le module E acier antérieur à 20 °C est conservé. Aucune chronologie NIST de dommage ou d'effondrement n'est imposée.

Le principe d'une section à chaque point d'intégration et de fonctions d'interpolation des déplacements est décrit par [OpenSees — élément à déplacements](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/633.htm). Les efforts de section y satisfont un équilibre faible, au sens intégré, et pas forcément l'équilibre ponctuel exact à l'intérieur de chaque élément : [documentation actuelle](https://opensees.github.io/OpenSeesDocumentation/user/manual/model/elements/dispBeamColumn.html). L'aire de loi de traction Gf/largeur de bande est décrite dans [DIANA — paramètres du modèle](https://manuals.dianafea.com/d110/en/1465843-1466551-model-parameters.html). Le code ici est propre au projet ; ni OpenSees ni DIANA n'est exécuté, et notre choix Lch=poids de quadrature n'est pas présenté comme un réglage certifié par ces logiciels.

## 3. Affirmations d'archives

Aucune affirmation nouvelle d'archive, identification vidéo ou mécanisme supplémentaire n'entre dans cette itération.

## 4. Hypothèses, discrétisation et limites de loi

Tout est à 20 °C, en petits déplacements. Béton et armatures reprennent exactement les lois V11E : dommage de traction avec adoucissement, fermeture élastique en compression, acier parfaitement plastique ; Ec = 2500 ksi, fc = 3 ksi, ft = 1 MPa, Gf = 100 J/m² et acier E = 200 GPa / fy = 400 MPa sont des hypothèses. Les ratios d'acier total 0 / 0,1 / 0,2 / 0,4 % et les nappes symétriques/supérieure sont hypothétiques, parfaitement adhérents au béton. Pas d'écrasement, géométrie non linéaire, flambement postcritique, fluage, cisaillement de dalle, bac acier ou rupture d'armature.

Chaque nœud de dalle porte ux,w,theta. L'axial est linéaire et la déformée verticale est cubique : eps0 constant et kappa linéaire dans un élément. Deux points de Gauss le long de chaque élément et 160 fibres au milieu de bandes à travers l'épaisseur. En référence 4 subdivisions par panneau acier : 65 nœuds de dalle, 64 éléments, 128 sections et 261 degrés de liberté au total. Les subdivisions 2/8 ne changent ni le treillis, ni les stations, ni la densité d'attaches, ni la position physique du dispositif.

Lch est le poids LONGITUDINAL du point de Gauss, soit la demi-longueur de l'élément : 0,282971875 / 0,1414859375 / 0,07074296875 m pour 2/4/8 subdivisions. Une bande entièrement fissurée dissipe bien AcGf indépendamment de sa longueur. Mais faire fissurer toutes les bandes double le nombre de bandes et l'énergie totale quand leur nombre double. Ce test isolé ne prouve donc pas l'objectivité de la localisation ou du nombre de fissures du panneau. Les dissipations calculées sont comparées séparément des flèches et des forces.

La section fournit [N,M] et sa matrice tangente couplée, sans imposer artificiellement N=0 comme dans l'essai de section V11E. L'assemblage utilise l'intégrale de Bᵀ[N,M] et de BᵀKsectionB. La charge 80 psf, poids propre compris, est appliquée une fois à la dalle par le vecteur réparti cohérent. Aucun ajout de masse ou de charge fictive de renfort. La bulle de charge élastique exacte de V11D n'est PAS superposée aux contraintes ni à l'énergie non linéaires ; les contraintes récupérées sont celles du champ FE approché.

La compression est vérifiée aux faces de la dalle aux extrémités des éléments, où la déformation linéaire de section peut être extrême, et non seulement aux points de Gauss intérieurs. La déformation maximale d'acier est aussi vérifiée aux extrémités. En traction, l'histoire de fissuration reste discrète aux points d'intégration.

Contact en compression et attaches tendues restent distincts ; le glissement horizontal inclut le décalage t/2 et le moment conjugué. Les capacités de membrures, sièges et attaches sont des premiers écrans nominaux : à leur franchissement, arrêt, sans suppression de barre ni propagation dynamique. Les compressions horizontales et soulèvements d'appuis non vérifiés sont signalés s'ils apparaissent.

Newton et recherche linéaire partent toujours du dernier état engagé. Les essais refusés sont annulés, puis le pas est réduit ; aucun ressort stabilisateur n'est ajouté. Une tangente non positive sous les déplacements imposés ou l'absence de convergence termine le parcours comme diagnostic, pas comme chute. La tangente est celle de ce modèle à petites déformations, sans raideur géométrique : sa positivité n'est pas la stabilité réelle de la tour.

### Chargements imposés

Deux montées de gravité : béton sans armature jusqu'à 125 % et hypothèse 0,2 % jusqu'à 250 %, avec arrêt au premier écran. Les autres essais partent de 25 % de la gravité de référence. Un déplacement de 2 mm est imposé à la dalle entre deux stations ; un autre dispositif abaisse le nœud8 du treillis jusqu'à 100 mm ou au premier écran. Ces mouvements sont des tests imposés, pas des dommages calculés d'avion. Tous leurs efforts et travaux sont inclus.

Un cycle de dalle va successivement 0, −2, 0, +2, 0 mm. Le cycle de treillis va 0, −60, 0 mm ; son amplitude a été choisie après un premier essai monotone atteignant un écran près de 68 mm, afin de tester la recharge/décharge dans un domaine déjà exploré. Ce choix de test est divulgué : ce n'est ni un paramètre historique ni une prédiction aveugle d'une amplitude réelle.

## 5. Résultats dérivés

| Cas | Fin | Gravité / référence | Déplacement imposé (mm) | Sections fissurées | Dissipation béton (J) |
|---|---|---:|---:|---:|---:|
| COLD_PLAIN | Borne du parcours | 1.25000 | 0.000 | 0 | 0.00000 |
| COLD_R02 | web | 1.69919 | 0.000 | 0 | 0.00000 |
| BEND_PLAIN | Borne du parcours | 0.25000 | -2.000 | 0 | 0.00000 |
| BEND_R01 | Borne du parcours | 0.25000 | -2.000 | 0 | 0.00000 |
| BEND_R02 | Borne du parcours | 0.25000 | -2.000 | 0 | 0.00000 |
| BEND_R04 | Borne du parcours | 0.25000 | -2.000 | 0 | 0.00000 |
| BEND_TOP | Borne du parcours | 0.25000 | -2.000 | 0 | 0.00000 |
| CYCLE_R02 | Borne du parcours | 0.25000 | 0.000 | 0 | 0.00000 |
| TRUSS_LOWER_R02 | top_chord | 0.25000 | -68.126 | 8 | 0.36190 |
| TRUSS_LOWER_PLAIN | top_chord | 0.25000 | -68.064 | 8 | 0.33231 |
| TRUSS_LOWER_R01 | top_chord | 0.25000 | -68.095 | 8 | 0.34714 |
| TRUSS_LOWER_R04 | top_chord | 0.25000 | -68.185 | 8 | 0.39184 |
| TRUSS_LOWER_TOP | top_chord | 0.25000 | -68.158 | 8 | 0.41062 |
| TRUSS_CYCLE_R02 | Borne du parcours | 0.25000 | 0.000 | 8 | 0.21714 |

Le panneau sans armature retrouve la réponse élastique V11D avant fissuration. Le cas TRUSS_LOWER_R02 finit à déplacement imposé -68.125763mm, flèche nodale maximale de dalle 78.850305mm et 8sections fissurées. La somme des réactions de sièges (171492.594366N) et de l'actionneur (-136252.794236N) équilibre la gravité (35239.800130N). Oublier l'actionneur inventerait un déséquilibre et une charge supplémentaire.

Les nombres de sections fissurées sont des points d'intégration, pas un nombre observé de fissures, une fraction réelle endommagée ou une probabilité. Une fin de cycle avec déplacement imposé revenu à zéro peut conserver une réaction : ce n'est pas un déchargement libre, et encore moins une flèche résiduelle de tour calculée.

### Bilans et contrôles

Sur référence, répétition, raffinements et demi-pas : résidu d'équilibre maximal 2.810e-11, identité d'énergie exacte 2.201e-16, écart de travail extérieur par trapèzes 0.000012%. Chaque incrément fait aussi l'objet d'un contrôle de travail pouvant réduire le pas. Les forces et moments sont normalisés équation par équation, sans les additionner comme des unités identiques.

Le travail matériau intègre les lois V11E exactement le long de l'incrément engagé ; on ajoute l'énergie élastique des barres/sièges/liaisons. L'intégration longitudinale multiplie les J/m par des poids en m pour obtenir des J du panneau. Le travail extérieur est calculé indépendamment avec les forces de gravité et réactions imposées, y compris les moments nodaux des charges réparties. Ce bilan isotherme ne contient ni chaleur ni chute dynamique et n'apporte aucune énergie de résistance au calcul global.

Contrôles analytiques : reproduction des champs axial/flexion et mouvements rigides ; section vectorisée identique à V11E ; inertie et solution élastique V11D avec défaut de quadrature milieu connu ; tangente globale par différences finies ; travail virtuel ; contact/recontact ; retour d'état sur échec ; conservation de la charge, de la géométrie et des unités. Il n'y a pas de revue multi-agent ni de comparaison à un solveur externe dans cette itération.

### Sensibilité spatiale 4→8 — critères déclarés, pas ajustés après les résultats

| Cas | Même arrêt | Écart flèche normalisé (%) | Écart actionneur normalisé (%) | Écart béton normalisé, plancher 1 J (%) | Tous critères |
|---|---|---:|---:|---:|---|
| COLD_PLAIN | True | 0.00000 | 0.00000 | 0.00000 | PASS |
| COLD_R02 | True | 0.00000 | 0.00000 | 0.00000 | PASS |
| BEND_PLAIN | True | 0.02677 | 0.00000 | 0.00000 | PASS |
| BEND_R01 | True | 0.02652 | 0.00000 | 0.00000 | PASS |
| BEND_R02 | True | 0.02649 | 0.00000 | 0.00000 | PASS |
| BEND_R04 | True | 0.02706 | 0.00000 | 0.00000 | PASS |
| BEND_TOP | True | 0.02639 | 0.00003 | 0.00000 | PASS |
| CYCLE_R02 | True | 0.02659 | 0.00000 | 0.00000 | PASS |
| TRUSS_LOWER_R02 | True | 0.00010 | 0.00020 | 0.64377 | PASS |
| TRUSS_LOWER_PLAIN | True | 0.00009 | 0.00018 | 0.57462 | PASS |
| TRUSS_LOWER_R01 | True | 0.00009 | 0.00019 | 0.61213 | PASS |
| TRUSS_LOWER_R04 | True | 0.00011 | 0.00023 | 0.71364 | PASS |
| TRUSS_LOWER_TOP | True | 0.00009 | 0.00021 | 0.68994 | PASS |
| TRUSS_CYCLE_R02 | True | 0.00007 | 0.00014 | 0.37066 | PASS |

Comparaisons sur paramètres communs, séparées par phase/cycle, sans extrapolation après arrêt. Flèches normalisées par le maximum de la phase de référence (plancher 1 µm), forces par leur maximum (plancher 1 N), dissipation par son maximum (plancher 1 J). Pour les dissipations inférieures à 1 J, la dernière colonne numérique n'est donc PAS le pourcentage de la dissipation physique calculée. Le critère béton autorise alors un écart absolu de 0,1 J ; il ne faut pas le présenter comme une convergence relative de 10 % d'une très petite énergie.

Exemple TRUSS_LOWER_R02 : dissipation finale 0.361900535 J pour 4 subdivisions, contre 0.355471611 J pour 8, soit 1.776 % de la valeur de référence. Ce diagnostic compare leurs états terminaux propres, très proches mais pas strictement identiques. La figure de dommage emploie également les états terminaux propres à chaque maillage. Le contrôle sur paramètres communs reste celui déclaré dans le tableau.

## 6. Inconnues et suite

Ferraillage réel, paramètres béton/adhérence et détail de bac restent inconnus. La fissuration peut demeurer étalée entre plusieurs bandes et sensible au maillage malgré la bonne énergie d'une bande isolée. Les cas qui échouent au contrôle spatial ne doivent pas être présentés comme prédictions convergées de fissuration, d'énergie dissipée ou de résistance du plancher réel. Leurs données restent des diagnostics reproductibles, pas des résultats supprimés ou validés artificiellement.

V11G : résoudre d'abord les éventuelles dépendances du maillage/localisation mises en évidence, avec un test longitudinal indépendant et une stratégie de fissuration explicitement vérifiée, avant d'étendre le chauffage et les instabilités géométriques. Si tous les critères présents passent, compléter quand même le contrôle longitudinal de localisation/équilibre fort avant de créditer une fracture structurale. Puis couplage thermique, postflambement, assemblages avec colonnes/allèges, avion calculé et incendies spatialement résolus.

Exécution CPU 100.019s ; Python3.14.3, NumPy2.4.6, Pillow12.2.0. Empreinte numérique : 14c653db4392244bc377a41705597d40adbc687fbd4afc92ffb33389d1c3ccff. Aucun logiciel installé, GPU ou Blender lancé. Les sorties antérieures sont protégées par empreinte.

## Livrables

results_v11f.json, panel_inventory.json, path_summaries.csv, path_history.csv, section_states.csv, physical_component_forces.csv, slab_displacements.csv, rejected_trials.json, regularization_coupons.csv, convergence_comparison.json, numerical_audit.json, source_manifest.json, offline_manifest.json et synthese_v11f_panneau_fissure.png. Les historiques complets de tous les raffinements et du demi-pas sont conservés dans verification_runs.json pour permettre une vérification indépendante sans refaire le calcul.
