# WTC 1 - V11D : flexion de dalle, contact et arrachement

## Résultat utilisable

Le panneau possède maintenant des déplacements et rotations de dalle indépendants du treillis. Le poids passe par des contacts comprimés ou des attaches tendues, et non par un lien vertical parfait. Une attache retirée ne supprime pas le contact comprimé. La dalle est un prédicteur élastique **non fissuré** : une première fissure calculée termine son domaine de validité, sans être déclarée rupture du plancher.

Douze chemins et un contrôle d'attache isolée sont calculés. Premiers seuils : {'slab_first_cracking': 3}. Les autres chemins atteignent simplement leur borne de paramètre. Ni ces comptes ni leurs températures ne donnent des probabilités ou un verdict historique. Aucune sortie V11D n'est transférée à la tour globale ou à Blender.

## 1. Faits directement transcrits ou vérifiés

Les dimensions de référence V11A/V11C sont préservées : paire symétrique, portée713in, largeur80in, épaisseur rectangulaire équivalente4,35in ; charge80psf incluant déjà le poids propre. Le treillis comporte toujours16panneaux Warren supposés et17stations de liaison. Une subdivision de la dalle n'ajoute ni treillis ni attache.

## 2. Résultats d'un modèle officiel réutilisés

Le tableau d'arrachement de [NIST NCSTAR1-6C, tableau5-7 p67](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-6c.pdf), vérifié en V11C, fournit15/12/10/7kip par attache pour les températures moyennes de béton20-300/450/600/750°C. Il est maintenant activé en traction verticale. Ce sont des estimations NIST, pas des essais incendie de toutes les pièces construites. L'interpolation reste une hypothèse. Les capacités de glissement et de siège sont celles déjà utilisées, avec leurs mêmes limites.

## 3. Informations d'archives

Aucune nouvelle inspection de l'archive ou des PDF. Les copies, sources et anciennes versions sont conservées. La disposition réelle des attaches, le ferraillage, le bac et les décalages exacts dalle/cordons ne sont pas établis par V11D.

## 4. Hypothèses et mécanique du prototype

### Dalle et excentricité

La dalle est une bande de poutre Euler-Bernoulli et une ligne axiale bilatérale jusqu'au premier seuil de fissuration/écrasement. Contrairement à V11C, sa traction axiale n'est donc pas supprimée avant que le critère combiné ne soit atteint. Il ne s'agit pas d'une résistance après fissuration. Aucun apport d'armature n'est inventé. E, fc et leurs réductions sont hérités des hypothèses V11A ; ft20=0,5/1/2MPa et sa réduction sont de nouvelles hypothèses déclarées, pas une formule réglementaire ou une mesure WTC.

Le glissement vaut us+e·theta−uacier. L'excentricité e=0 ou t/2 est explicite et la force de liaison transmet son moment e·N. La valeur t/2 suppose une attache sous une dalle rectangulaire équivalente ; le détail réel de bac et de cordon reste inconnu. Les déplacements sont petits, sans chaînette, raideur géométrique, torsion ou postflambement.

### Contact et attache

Le jeu g=wdalle−wtreillis est positif en ouverture. Contact : N=kc·min(g,0), sans adhérence ni traction. Attache : N=kt·max(g,0), limitée par l'arrachement. kc=1000MN/m et kt=10/100/1000MN/m par attache équivalente sont des paramètres non mesurés. Le contact autorise une petite interpénétration de régularisation, mesurée dans les sorties ; elle n'est pas une pénétration physique du béton.

La densité32attaches équivalentes et les poids tributaires sont conservés. Le retrait au premier seuil d'une liaison, s'il intervient avant fissuration/flambement, supprime traction verticale et glissement horizontal de la station, mais garde le contact. Un rééquilibrage éventuel n'est qu'un diagnostic statique ; énergie stockée retirée et dissipation dynamique sont distinctes. Le contrôle d'attache isolée démontre la logique numérique de retrait/recontact, pas la validation expérimentale d'une loi de rupture.

### Charge, température et contraintes

Toute la gravité est appliquée **une seule fois à la dalle**, avec forces et moments nodaux cohérents de charge répartie. Le cas d'abaissement local utilise un déplacement imposé au milieu du treillis après précharge0,25 : sa réaction est incluse dans l'équilibre. Ce n'est ni un dommage d'avion calculé ni un mouvement spontané.

La température moyenne des deux faces de dalle fixe E, résistances et expansion axiale. La différence des faces donne une courbure libre kappa0=−alpha(Tsup−Tinf)/t. Il s'agit d'un gradient prescrit simplifié : pas de section multicouche, de feu, de transfert thermique, de fluage ou de temps réel.

Les contraintes de fibres sont N/A ± M·t/(2I), avec recherche aux extrémités et à l'extremum intérieur de moment de chaque élément. La solution particulière quartique de charge uniforme est ajoutée pour récupérer le moment local ; on ne confond pas la courbure de l'interpolation seule avec le moment physique sous charge répartie. Les flèches exportées sont des maxima **nodaux**, pas une recherche exacte du maximum intérieur entre nœuds.

### Énergie et limites

Deux points de Gauss intègrent exactement la raideur de flexion cubique. Leurs conjugués ne sont pas des forces axiales en newtons : ils ne figurent pas dans le tableau d'efforts physiques. La récupération sous charge répartie ajoute une énergie q²L⁵/(1440EI) et un travail double, séparément consignés. L'identité d'état inclut déformations propres et travail d'appui imposé. Ce n'est pas un bilan de chaleur ou une simulation de fracture dynamique.

Les critères restent séparés : fissuration initiale ou compression de dalle, écrans nominaux de barres, traction des sièges, glissement ou arrachement d'attache. La compression horizontale et l'interactionV-H des sièges restent non vérifiées. Aucune résistance au flambement latéral n'est déduite automatiquement du contact vertical.

## 5. Résultats dérivés

| Chemin | Paramètre final | Acier°C | Dalle sup/inf°C | Flèche nodale mm | Premier critère atteint ou fin |
|---|---:|---:|---:|---:|---|
| COLD_E0_FT05 | 1.250000 | 20.0 | 20.0/20.0 | 58.52 | Fin sans seuil vérifié |
| COLD_E0_FT10 | 1.250000 | 20.0 | 20.0/20.0 | 58.52 | Fin sans seuil vérifié |
| COLD_E0_FT20 | 1.250000 | 20.0 | 20.0/20.0 | 58.52 | Fin sans seuil vérifié |
| COLD_E05_FT05 | 1.250000 | 20.0 | 20.0/20.0 | 54.02 | Fin sans seuil vérifié |
| COLD_E05_FT10 | 1.250000 | 20.0 | 20.0/20.0 | 54.02 | Fin sans seuil vérifié |
| COLD_E05_FT20 | 1.250000 | 20.0 | 20.0/20.0 | 54.02 | Fin sans seuil vérifié |
| COLD_TIE_SOFT | 1.250000 | 20.0 | 20.0/20.0 | 54.02 | Fin sans seuil vérifié |
| COLD_TIE_STIFF | 1.250000 | 20.0 | 20.0/20.0 | 54.02 | Fin sans seuil vérifié |
| HEAT_UNIFORM_ROLLER | 0.452406 | 282.4 | 282.4/282.4 | 28.23 | slab_first_cracking |
| HEAT_UNIFORM_RESTRAINED | 0.107580 | 82.4 | 82.4/82.4 | 28.44 | slab_first_cracking |
| HEAT_FROM_BELOW | 0.039144 | 42.7 | 20.0/31.0 | 18.26 | slab_first_cracking |
| LOCAL_TRUSS_LOWERING_COLD | 1.000000 | 20.0 | 20.0/20.0 | 30.79 | Fin sans seuil vérifié |

Pour les chemins froids, le paramètre est le facteur de charge ; pour les autres il est la fraction de la sollicitation prescrite. Ce n'est jamais un temps. Chaque courbe s'arrête au premier critère et n'est pas prolongée pour atteindre un arrachement après fissuration. Nombre de diagnostics de retrait de panneau :0. Les seuils de fissuration ne préjugent pas de la résistance résiduelle d'une dalle armée réelle.

Différence importante avec V11C : son modèle axial comprimé ne vérifiait pas la fissuration combinant traction et flexion. L'arrêt plus tôt du chemin uniformément chauffé dans V11D traduit ce nouveau domaine de calcul ; ce n'est pas une preuve que le plancher réel tombe à la première fissure, ni une correction rétroactive de la V11C. Les parcours thermiques emploient ici une précharge0,25 et ne doivent pas être confondus avec la précharge0,5 de V11C.

### Contrôles

56/56 contrôles passent : poutres à solutions analytiques, courbure libre/bloquée, contact/traction/recontact, moments récupérés, excentricité, unités, charge et réactions, identité énergétique, répétition déterministe, division du pas de parcours par2 et subdivision de dalle1/2/4 à treillis/attaches fixes. Les comparaisons finales de maillage utilisent2→4 ; elles ne constituent pas une validation des géométries réelles.

Résidus maximaux des parcours :{'equilibrium_residual': 4.7892119461950494e-11, 'energy_identity_residual': 2.2635347420131258e-11, 'recovered_energy_identity_residual': 2.263523997888355e-11}. Temps CPU31.11s avec répétitions/raffinements, Python3.14.3, NumPy2.4.6. Aucun GPU, logiciel nouveau ou Blender. Les contrôles valident l'exécution du prototype, pas toute la chaîne causale historique.

## 6. Limites, contradictions et suite

La dalle équivalente, son excentricité, ses propriétés et les capacités officielles d'attaches ne forment pas encore une calibration matérielle cohérente du plancher construit. Les premiers seuils ne doivent pas être interprétés comme des ruptures complètes. Les valeurs d'attaches peuvent rester inutilisées si la fissuration intervient auparavant : il serait incorrect de sauter cette limite pour afficher un arrachement.

La V11E devra traiter la réponse de dalle après fissuration avec des hypothèses d'armatures déclarées et des vérifications de section/cycle, avant d'utiliser cette résistance dans le panneau ; géométrie non linéaire, postflambement, liaisons avec colonnes/allèges et calcul de l'impact/incendie restent à développer. V11A/V11B/V11C et le film V10Z demeurent inchangés. Aucun effondrement ou non-effondrement n'est imposé.
