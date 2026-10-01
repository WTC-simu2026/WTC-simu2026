# WTC 1 - V11C : dalle, treillis et liaisons déformables

## Résultat utilisable

V11C construit une paire symétrique de treillis de 713 in (18,1102 m) avec une dalle axiale distincte, 17 stations de glissement horizontal et des appuis déformables. Les 17 stations représentent **32 attaches équivalentes supposées**, pas un nombre de knuckles réels relevé sur plans. Les sollicitations de la dalle, des barres et des liaisons sont calculées séparément. Aucune résistance V11C n'est ajoutée à V11B ni au film Blender.

22 chemins pré-déclarés sont exécutés : 18 chargements froids et quatre sollicitations thermiques/d'appui. 7 arrivent à la limite de chargement sans dépasser les seuils vérifiés ; les autres atteignent un premier seuil nominal ({'top_chord': 5, 'seat_h': 4, 'bond': 6}). Ces comptes décrivent les cas choisis, pas des probabilités historiques. La réponse s'arrête au premier seuil : aucune barre qui flambe ou plastifie n'est prolongée artificiellement dans son régime élastique.

## 1. Faits directement transcrits ou vérifiés

La géométrie de référence C32T1, les sections de cornières, le diamètre uniforme de diagonale, la dalle équivalente de 4,35 in et la largeur de 40 in par treillis sont repris de V11A avec leurs limites. Les 16 panneaux Warren et l'affectation de cette géométrie à la paire restent idéalisés.

Le chapitre knuckle de [NIST NCSTAR 1-6C](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6c.pdf), pages imprimées 61-68, a fait l'objet d'une lecture bornée. Le tableau 5-7 (page 67, PDF 115 local) a été contrôlé visuellement. Les unités sont conservées dans la configuration : 1 kip = 4448,221615 N ; 1 in = 0,0254 m. La copie source n'est pas modifiée.

## 2. Résultats et hypothèses d'un modèle officiel réutilisés

Les capacités longitudinales d'une attache reprises du tableau sont 30/24/19/15 kip aux températures moyennes du **béton** 20-300/450/600/750 °C. Le NIST les estime à partir d'essais, de calculs et de jugement thermique ; ce ne sont pas des essais incendie de chaque attache construite. Le modèle interpole les valeurs sans les indexer sur la température de l'acier. Les données d'arrachement vertical sont conservées comme référence mais **non activées** ici.

Les graphiques publiés concernent des modèles de deux attaches. Ils ne donnent pas à V11C une loi individuelle as-built vérifiée : raideur et rupture fragile restent des hypothèses. Les capacités des sièges viennent des tableaux déjà transcrits en V11A, appliquées une seule fois à la paire ; les valeurs horizontales ne sont utilisées qu'en traction. Aucun domaine d'interaction traction verticale/horizontale n'est validé.

## 3. Informations provenant des archives locales

Aucune nouvelle lecture de l'archive source. La nomenclature complète de chaque plancher, les positions réelles d'attaches et les assemblages de rive restent non reconstruits. Les détails de siège intérieur 15 / extérieur 1013 sont des alternatives déclarées, non une identification du siège réel associé à C32T1.

## 4. Hypothèses propres au modèle

### Structure et liaisons

Une paire de treillis identiques est condensée en un treillis plan avec EA, aire, inertie et charge doublés. La largeur chargée est 80 in. La référence 80 psf contient déjà le poids propre : aucun second poids propre n'est ajouté. La symétrie impose une même réponse aux deux treillis ; torsion, transfert transversal et ouverture de plancher sont absents.

La dalle possède un déplacement axial indépendant à chaque nœud supérieur. Elle ne travaille qu'en compression ; en traction son effort, sa rigidité et sa charge thermique sont nuls. Aucun béton tendu ni armature n'est crédité. La dalle est ramenée à l'axe supérieur du treillis : excentricité, flexion et cisaillement de dalle ne sont pas résolus. Son lien vertical reste parfait, même dans le diagnostic de rupture horizontale. Cela limite fortement ce diagnostic après dommage.

Les ressorts de cisaillement transmettent un effort selon le glissement entre dalle et acier. Leur raideur et leur capacité sont pondérées par longueur tributaire, demi-poids aux extrémités. Le pas d'attaches équivalent est supposé 713/16 in et reste fixe si le nombre de panneaux de test change. La somme de raideur et de capacité ne varie donc pas artificiellement avec ce nombre. Changer les panneaux Warren change néanmoins la structure physique : ce n'est pas une convergence du maillage réel.

Raideurs testées : 1/10/100 MN/m par attache équivalente ; facteurs de résistance 0,05/0,25/1. Ces facteurs ne représentent pas des dommages calculés de l'avion. Le facteur réduit seulement la résistance, pas aussi la raideur. Le modèle n'est pas ajusté pour retrouver une durée ou un effondrement.

Les appuis verticaux et horizontaux retenus valent 100 MN/m par paire. Le cas roulant ne possède aucun ressort horizontal à droite. Aucun contreventement latéral du cordon n'est automatiquement déduit des attaches : les barres comprimées sont contrôlées par le minimum Euler/écrasement, sans postflambement. Le mode de contreventement idéal sert seulement à comparer V11A dans les tests.

### Température, limites et rupture

Acier, dalle et siège peuvent recevoir trois températures prescrites différentes, dans le domaine 20-600 °C. Les coefficients constants de dilatation supposés sont 12 et 10 micromètres par mètre et kelvin pour acier et béton. Ec, fc et réductions thermiques du béton restent ceux des hypothèses V11A. Pas de gradients dans chaque barre, de feu, de transfert thermique, de fluage ni d'horloge réelle.

Les quatre chemins commencent après une charge froide de 0,5 fois la référence, vérifiée avant chauffage/déplacement. Le premier franchissement est encadré par pas puis affiné par dichotomie. Une répétition avec pas divisé par deux contrôle le premier seuil détecté ; ce n'est pas une preuve contre tout maximum non échantillonné. La traction horizontale et la compression aux sièges sont distinguées : la résistance horizontale en compression est inconnue, donc une poussée élastique calculée n'est pas une capacité vérifiée.

À un premier seuil d'attache, les ressorts horizontaux concernés peuvent être supprimés et le même chargement rééquilibré dans un **diagnostic statique séparé**. Si un autre seuil est dépassé, le résultat est marqué non admissible comme continuation. Aucune suppression de barre, boucle de ruine ou trajectoire dynamique n'est appliquée. Les énergies avant/après et l'énergie stockée dans le ressort retiré sont distinctes ; aucune différence n'est baptisée énergie dissipée de rupture.

L'identité vérifiée est 2U = u·f + u_prescrit·réaction - somme(N·extension_propre). Elle inclut les extensions thermiques et les positions d'ancrage dans extension_propre. C'est une identité d'état élastique, **pas un bilan de chaleur ou d'énergie dynamique** ; E varie avec la température sans intégration du travail thermique.

## 5. Résultats dérivés

### Trois raideurs de liaison, résistance de référence entière, appui roulant

Les valeurs ci-dessous correspondent à la fin du chemin autorisé (jusqu'à 1,25 fois 80 psf), ou à son premier seuil. Elles ne sont pas toutes mesurées au même effort si l'un des chemins s'arrête avant.

| K par attache (MN/m) | Facteur de charge final | Flèche finale (mm) | Glissement max (mm) | État |
|---:|---:|---:|---:|---|
| 1 | 1.055867 | 70.95 | 5.561 | FIRST_NOMINAL_LIMIT_NO_POST_MEMBER_CONTINUATION |
| 10 | 1.250000 | 59.31 | 3.051 | PARAMETER_END_BELOW_CHECKED_LIMITS_NOT_PROOF_OF_SAFETY |
| 100 | 1.250000 | 41.85 | 0.503 | PARAMETER_END_BELOW_CHECKED_LIMITS_NOT_PROOF_OF_SAFETY |

### Chemins thermiques et déplacement imposé

Valeurs à la fin du chemin ou au premier écran nominal ; aucune température critique de la tour réelle n'est identifiée.

| Chemin | Acier (°C) | Dalle (°C) | Déplacement d'ancrage (mm) | Flèche (mm) | État final du modèle |
|---|---:|---:|---:|---:|---|
| UNIFORM_ROLLER | 600.00 | 600.00 | 0.000 | 53.54 | Fin sans seuil vérifié franchi |
| UNIFORM_RESTRAINED | 122.75 | 122.75 | 0.000 | 55.53 | Premier seuil : top_chord |
| STEEL_HOT_SLAB_COOL | 108.62 | 47.50 | 0.000 | 62.62 | Premier seuil : top_chord |
| SUPPORT_OPENING_COLD | 20.00 | 20.00 | 6.137 | 10.84 | Premier seuil : seat_h |

Le cas roulant chauffé atteint la borne de 600 °C **sans franchissement** : la membrure la plus sollicitée n'est donc pas présentée comme rompue à cette température. Les seuils plus bas des cas retenus dépendent notamment des ressorts d'appui supposés et du cordon supérieur sans maintien latéral crédité ; ils ne constituent pas des températures critiques mesurées ou établies du plancher réel.

Les pertes de liaison donnent 6 diagnostics de retrait de ressorts. Les sorties composant par composant permettent de distinguer une rupture d'attache d'un seuil de barre. Une absence de dépassement parmi les critères implementés n'est pas une preuve de résistance d'un plancher réel.

### Vérification

**74/74 contrôles passent.** Résidu relatif maximal d'équilibre 9.684e-13 ; identité d'énergie d'état 4.380e-12. Tests analytiques indépendants, limites de liaison, charge doublée, signes de traction/compression, index thermique, pondération des attaches, répétition exacte et pas de parcours divisé par deux sont inclus. Exécution CPU, répétition et raffinement : 9.83 s, Python 3.14.3, NumPy 2.4.6. Aucun logiciel installé, aucun GPU ou Blender lancé.

## 6. Contradictions, informations manquantes et suite

V11C fait progresser le transfert d'efforts local, pas encore le bâtiment entier. Les capacités NIST des attaches et les propriétés de dalle du prototype n'ont pas la même base matérielle : les conserver comme dépendance/hypothèse distinctes, pas comme calibration cohérente du béton réel. Les rigidités de liaison ne sont pas une extraction des courbes d'essai. Aucune conclusion « effondrement nécessaire » ou « impossible » n'en découle.

Restent prioritaires : liaison verticale et décollement, flexion/fissuration de dalle et armatures ; géométrie non linéaire et réponse après premier flambement ; assemblages de rive et appuis fournis par colonnes/allèges ; couplage aux composants spatiaux. **V11D : ajouter et tester la flexion de dalle et son contact/arrachement vertical dans un panneau borné, avant toute propagation globale.** Les entrées de l'impact 767 et des incendies doivent ensuite être calculées, sans issue prédéfinie. V11B reste inchangée ; le film V10Z conserve son ancien pilote.

## Livrables

Configuration et scripts V11C ; synthèse graphique ; résumés des 22 parcours, histories, premiers événements, efforts terminaux et déplacements ; diagnostics de rupture horizontale ; tests numériques ; manifestes des sources et sorties. Toute reprise utilise le handoff V11C et le nouvel état, sans réexécuter les anciennes itérations.
