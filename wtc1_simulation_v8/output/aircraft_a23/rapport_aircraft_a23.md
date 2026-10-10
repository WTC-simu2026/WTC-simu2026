# AIRCRAFT-A23 — solide à translations et transmission aux peaux

**26 nouveaux contrôles natifs**, tous avec bilan énergétique réussi. Le solide isolé passe les contrôles de masse, d'inertie physique et de traction. Le montage aux peaux conserve la masse totale mais **échoue à l'énergie cinétique globale ajoutée surXYZ**. Il n'est pas inséré dans l'avion entier. L'objectif vidéo3D des10premières secondes physiques reste incomplet; l'aperçu entier disponible A20 couvre20ms.

## 1. Faits directement observés ou transcrits

Graine1102048, aucun tirage aléatoire. Solide HA8 TYPE14, intégration2×2×2, uniquement trois degrés de liberté de translation par nœud. Dimensions4×1×0,5mm, masse0,00556g. Rotations prescrites90° surXYZ, traction élastique N4 puis N8, rotations libres à10rad/ms sur le maillage12³, puis montage avec et sans connecteur sur une peau métallique et le sandwich A20. Les attaches du cœur restent les Spot5 p3 A20. Un thread CPU, aucun GPU ni mise à l'échelle de masse. Entrées en g/mm/ms, conversions énergétiques en J par facteur0,001.

Le premier témoin de traction w0 déplace par erreur les nœuds18/19 du bord de support àx=0, sélectionnés par x>=0. Le support se déforme, avec0,000328088J d'énergie interne. Le déplacement relatif des extrémités du solide n'est que0,0008mm; ses énergies N4/N8 correspondent alors à la référence adaptée à ces conditions à1,151%/0,528%. Ces calculs et leurs critères échoués sont conservés. La nouvelle déclaration w1 fixe tout le support et déplace uniquement les peaux de0,004mm; elle compare le canal PART du solide à la rigidité3D indépendante.

Les rotations reliées w0 sur1ms échouent à la vitesse rigide de tous les nœuds. Les extrémités restent dans0,005m/s, mais l'intérieur atteint0,06158/0,01421/0,01506m/s d'écart enXYZ. La rotation w1 sur10ms garde angle, masse, matériaux, maillage, interfaces et seuils; les neuf contrôles individuels w1 passent. Ce résultat ne qualifie pas le mouvement rapide w0. Les26bilans passent;21/26ensembles de critères individuels passent. La comparaison indépendante avec/sans connecteur échoue encore.

Deux interruptions de post-traitement sont documentées, sans interruption ni répétition des solveurs: w0 supposait des temps TFILE strictement égaux; w1 conservait un chemin w0 pour la traction. Un nouveau lecteur en cache utilise le support temporel commun et vérifie une borne d'erreur de recalage. Le lecteur de champs initial rechargeait le NPZ pour chaque composante: il a été arrêté puis corrigé pour charger une seule fois les tableaux, en réutilisant les VTK déjà produits. Les78échantillons natifs sont finis et sans suppression d'élément. Le critère textuel initial d'identité des coordonnées2e-5mm échoue sur certains champs imprimés à six chiffres significatifs; cet échec est conservé, avec un addendum fondé sur une borne explicite d'arrondi et de stockage float32. Aucun seuil des calculs mécaniques n'est élargi.

Conservation vérifiée de16471fichiers antérieurs, soit60.134Go; les archives sources ne sont pas rescannées.

## 2. Résultats d'un modèle officiel

La documentation primaire [TYPE14](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type14_solid_starter_r.htm) décrit la formulation volumique. [TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm) décrit Spot5 et Iproj2. La [théorie TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_kinematic_tied_interface_r.htm) décrit le transfert des masses secondaires aux nœuds principaux selon les fonctions de forme, ainsi que les termes d'inertie liés aux offsets. Une telle distribution peut conserver la masse tout en modifiant un tenseur diagonal discrétisé. Cette indication est une piste pour le diagnostic local, pas une preuve de la cause complète du déficit A21. Aucun résultat de dommage NIST n'est utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo ou photographie historique. Réemploi en lecture seule des entrées A20, de l'audit A22 et des sources techniques déjà conservées. Les courbes acier A22 restent non adoptées; leur début de striction n'est pas converti en seuil de rupture.

## 4. Hypothèses propres au modèle

LAW2/1 hérité:rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, écrouissage nul et fracture absente. Capacité axiale de prototype162N. Dimensions, capacité et matériau d'attache non identifiés pour AA11. Aucun ajout à l'avion entier. La masse0,334g du prototype à poutres A22 n'est pas le budget du nouveau solide. Support10×10×0,5mm, sandwich10×10×9mm, solide adjacent à la peau extérieure inférieure et deux attaches d'extrémité Spot5 Iproj2, dsearch0,8mm. Masse de référence0,3604g, avec solide0,36596g; aucune ADMAS ni compensation de densité/inertie.

La rigidité de traction indépendante utilise une élasticité isotrope3D à petits déplacements, des fonctions hexaédriques et huit points de Gauss. Les rotations libres utilisent un tenseur continu indépendant et la masse nodale lumped explicitement assemblée. Le maillage12³ réduit l'erreur d'inertie continue à1,389%, dans le seuil2%. Les maillages prescrits4×2×2/8×4×4 comparent leur propre masse discrète; leur inertie intrinsèque continue ne doit pas être déclarée convergée à partir de ces seuls contrôles.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Critères individuels |
|---|---:|---|
| w0 / ROTATION_X | 1.044419e-12 | réussi |
| w0 / ROTATION_Y | 9.8807494e-12 | réussi |
| w0 / ROTATION_Z | 9.8042153e-12 | réussi |
| w0 / AXIAL_N4 | 1.2624079e-11 | réussi |
| w0 / AXIAL_N8 | 1.264549e-11 | réussi |
| w0 / FREE_ROTATION_X | 7.881229e-12 | réussi |
| w0 / FREE_ROTATION_Y | 7.3514e-11 | réussi |
| w0 / FREE_ROTATION_Z | 8.8073e-11 | réussi |
| w0 / REFERENCE_ROTATION_X | 1.5063218e-08 | réussi |
| w0 / CONNECTED_ROTATION_X | 1.4785879e-08 | **échoué**: all_node_velocity |
| w0 / REFERENCE_ROTATION_Y | 1.5063218e-08 | réussi |
| w0 / CONNECTED_ROTATION_Y | 1.3692615e-08 | **échoué**: all_node_velocity |
| w0 / REFERENCE_ROTATION_Z | 7.6911901e-08 | réussi |
| w0 / CONNECTED_ROTATION_Z | 8.7160808e-08 | **échoué**: all_node_velocity |
| w0 / REFERENCE_EXTENSION | 1.06968e-10 | réussi |
| w0 / CONNECTED_EXTENSION_N4 | 1.097843e-10 | **échoué**: independent_static_IE |
| w0 / CONNECTED_EXTENSION_N8 | 1.0516e-10 | **échoué**: independent_static_IE |
| w1 / REFERENCE_ROTATION_X | 1.4431916e-10 | réussi |
| w1 / CONNECTED_ROTATION_X | 1.2772854e-10 | réussi |
| w1 / REFERENCE_ROTATION_Y | 1.4431916e-10 | réussi |
| w1 / CONNECTED_ROTATION_Y | 1.4458637e-10 | réussi |
| w1 / REFERENCE_ROTATION_Z | 9.7509916e-10 | réussi |
| w1 / CONNECTED_ROTATION_Z | 9.7360784e-10 | réussi |
| w1 / REFERENCE_EXTENSION | 1e-15 | réussi |
| w1 / CONNECTED_EXTENSION_N4 | 1.39418e-11 | réussi |
| w1 / CONNECTED_EXTENSION_N8 | 1.34394e-11 | réussi |

La traction corrigée donne une différence de maillage de2.1993%, sous le seuil5%, et passe les références indépendantes. Les trois rotations libres conservent énergie, quantité de mouvement et moment cinétique, sans canal RKE de solide artificiel.

En rotation lente, la cinématique et le canal cinétique propre au solide retrouvent la référence discrète. Le canal global supplémentaire reste biaisé:

| Axe | Tenseur discret connu(g·mm²) | Tenseur issu du PART solide | Tenseur issu de l'ajout global | Écart global |
|---|---:|---:|---:|---:|
| X | 0.26531625 | 0.26531747 | 0.293957483 | 10.7951% |
| Y | 0.13396125 | 0.133961267 | 0.150280994 | 12.1824% |
| Z | 0.148035 | 0.148034985 | 0.205212915 | 38.6246% |

| Axe | Écart maximal d'énergie ajoutée(J) | Seuil2%+1e-7J | Résultat |
|---|---:|---:|---|
| X | 8.08100652e-07 | 2.47294362e-07 | **échoué** |
| Y | 4.74988463e-07 | 1.74370631e-07 | **échoué** |
| Z | 1.60095306e-06 | 1.82183887e-07 | **échoué** |

Le recalage temporel w1 passe sa borne explicite et ne suffit pas à expliquer ces écarts. Les canaux natifs sont conservés dans inertia_channels_w0/w1.json; aucun terme n'est reconstruit, ajouté ou retiré du bilan. Tous les témoins gardent leur masse totale. L'écart cinétique global rend le montage non qualifié malgré les bilans corrects. La transmission des masses et offsets TYPE2 doit être testée séparément.

## 6. Contradictions et informations manquantes

L'inertie correcte du solide seul ne garantit pas celle du montage. Une énergie interne quasi nulle et un bilan natif correct ne suffisent pas à qualifier la masse dynamique distribuée. L'attache mécanique historique, les propriétés à grand taux de déformation, l'arrachement, le cisaillement, la fracture et la correspondance des nuances restent inconnus. La géométrie inclinée des24racines de l'avion n'a pas été remplacée. Le bilan local entier A21 et ses limites matérielles restent échoués. Gravité, structure intérieure porteuse et contacts de fragments sont à compléter avant extension temporelle. Ni le solide isolé ni son témoin plat n'identifie un mécanisme historique.

AIRCRAFT-A24 : reprendre coupling_summary.json, inertia_channels_w1.json et paired_w1_cached_audit.json, sans relancer A20–A23. Le solide HA8 conserve la masse et le tenseur physique en libre sur le maillage12³; les tractions N4/N8 correspondent à une rigidité3D indépendante. Le montage aux peaux Spot5 Iproj2 conserve les26bilans mais son énergie cinétique globale ajoutée échoue surXYZ, même en rotation lente10ms; le canal PART du solide reste correct. Ne pas transférer ce connecteur à l’avion entier, ni reconstruire une RKE ou compenser la masse. Tester une transmission sans condensation de masse, par maillage conforme ou attache de pénalité contrôlée, en gardant le cœur/Spot5 A20 intact. Si une formulation de pénalité est testée, déclarer sa rigidité et sa viscosité, inclure toutes ses énergies natives, contrôler glissement, bilan, inertie, dynamique libre et sensibilité au pas. La documentation Spot25 la déconseille: résultat à vérifier, pas choix validé. Après réussite des témoins, vérifier la géométrie réelle inclinée, les144points de peau des24racines, les capacités/budgets et la dynamique libre avant départ entier intact. Les dimensions4×1×0,5mm, masse0,00556g et capacité162N sont celles d’un prototype, pas une attache AA11 identifiée; la masse A22 de0,334g ne s’applique pas au nouveau solide. Les matériaux A21, la gravité, l’intérieur porteur et les contacts de fragments restent ouverts. Les courbes acier A22 et la striction ne sont pas des lois de rupture validées. Aucun dommage connu comme cible. Objectif10secondes physiques3D incomplet; dernier aperçu entier A20 de20ms. Publication A22+A23 autorisée par la cadence après intégrité vérifiée.
