# AIRCRAFT-A25 — raccordement sans décalage et inertie des coques

**Sept nouveaux contrôles natifs**, tous avec bilan énergétique réussi. La mise à zéro du décalage initial ne restaure pas le moment cinétique physique. Les références de coques héritées présentent aussi une énergie initiale de rotation très supérieure à celle de leur seule épaisseur physique. **Aucune insertion entière ni extension temporelle**. L'objectif10secondes physiques3D reste incomplet; A20 couvre20ms.

## 1. Faits directement observés ou transcrits

Graine1102050, aucun tirage aléatoire. Volume4×1×0,5mm et masse0,00556g conservés, mais ruban déplacé de+0,25mm en z. Sa face supérieure z=−4,25mm coïncide avec les surfaces médianes du support et de la peau inférieure. Seuls les nœuds supérieurs x≤−1mm et x≥1mm sont attachés. Deux surfaces de reprise remplacent les deux extrémités décalées. La distance initiale aux surfaces est nulle, contrôlée avant Engine; dsearch1e-5mm, Stfac100 et Visc1e-20 sont effectivement relus. Les témoins libres XYZ, translation et pas réduitY utilisent les références A24 enregistrées avec vitesses angulaires natives. Deux tractions utilisent une nouvelle rigidité3D indépendante aux nœuds réellement attachés. Aucun solveur A20–A24 répété.

La première substitution du centre de masse dans le générateur ne trouve pas son expression conditionnelle et s'arrête avant tout cas natif. Le script est conservé puis la substitution est corrigée; configuration et dimensions inchangées. Les21champs natifs échantillonnés passent finitude, identités bornées par l'impression et absence de suppression. Conservation vérifiée de19927fichiers antérieurs, soit64.881Go. Le harnais passe.

## 2. Résultats d'un modèle officiel

La [théorie primaire des coques](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_mechanical_prop_r.htm) décrit une inertie nodale sphérique régularisée contenant un terme lié à l'aire de l'élément, en plus de l'épaisseur. Elle ne doit pas être identifiée à la seule inertie physique d'épaisseur. [TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm) décrit les limites de la pénalité Spot25. Les propriétés [solid-shell TYPE20](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type20_tshell_starter_r.htm) et [LAW25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law25_compsh_starter_r.htm) sont conservées comme pistes de nouvelle formulation. Leur simple disponibilité ne constitue pas une validation d'une conversion. Aucun dommage officiel n'est une cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou identification historique. Les24racines et144nœuds de peau sont inventoriés depuis la géométrie A20 en lecture seule, avec triangles du fuselage, quads de peau, normales, offsets et épaisseurs2,54/0,5mm. Il s'agit de la géométrie du modèle A20, pas d'une mesure nouvelle de l'attache réelle. Aucun RBE2 du fichier source n'est supprimé à ce stade.

## 4. Hypothèses propres au modèle

Matériau de ruban LAW2 hérité, rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, sans écrouissage ni rupture; résistance historique inconnue. Support et sandwich A20 inchangés, mêmes masses0,3604g sans et0,36596g avec ruban. Le déplacement de géométrie change le centre de masse et le tenseur du ruban; ils ne sont pas compensés. La reprise sur surfaces médianes est une idéalisation qui comporte un recouvrement géométrique de demi-épaisseur avec les coques, explicitement déclaré. Aucune application directe à AA11. Le budget0,80064g pour144rubans plats identiques serait une simple extrapolation: la masse des futurs rubans courbes n'est pas encore définie.

Le moment physique emploie les masses nodales, positions, vitesses et vitesses angulaires natives, avec l'inertie propre d'épaisseur des coques; conversion g·mm²/ms vers kg·m²/s par1e-6. Les huit canaux d'énergie natifs restent tous dans le bilan, y compris RKE. Aucune inertie n'est ajoutée, retirée ou ajustée dans le calcul. Le diagnostic compare une énergie native à une référence physique distincte, sans reconstruire le bilan.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Critères individuels initiaux |
|---|---:|---|
| CONNECTED_FREE_ROTATION_X | 7.273506e-07 | réussi |
| CONNECTED_FREE_ROTATION_Y | 1.089337e-06 | réussi |
| CONNECTED_FREE_ROTATION_Z | 7.112956e-07 | réussi |
| CONNECTED_FREE_TRANSLATION | 0 | réussi |
| CONNECTED_FREE_ROTATION_Y_HALF | 1.120222e-06 | réussi |
| CONNECTED_EXTENSION_N4 | 9.002e-11 | **échoué**: footprint_elastic_reference |
| CONNECTED_EXTENSION_N8 | 5.0848e-11 | **échoué**: footprint_elastic_reference |

| Mouvement | Dérive du moment total(kg·m²/s) | Seuil total | Erreur du moment ajouté | Seuil ajouté | Résultat supplémentaire |
|---|---:|---:|---:|---:|---|
| ROTATION_X | 1.92061455e-06 | 5.00414506e-07 | 1.91189489e-06 | 5.149175e-08 | **échoué** |
| ROTATION_Y | 5.033421e-07 | 4.98118727e-07 | 5.94461656e-07 | 3.58230546e-08 | **échoué** |
| ROTATION_Z | 1.6323974e-06 | 7.29773719e-07 | 1.63240212e-06 | 3.97630604e-08 | **échoué** |
| TRANSLATION | 3.73211946e-12 | 7.76754487e-07 | 3.73211921e-12 | 1.50647945e-07 | réussi |

Le pasY réduit vaut0.23290902fois le pas initial. Les différences entre pas passent, mais le moment physique demeure non conservé: la convergence n'est pas conservation. La translation uniforme et l'énergie cinétique initiale ajoutée passent. Les deux tractions échouent à la référence rigide des surfaces de reprise: la pénalité reste assez souple pour changer la réponse, même àStfac100. L'écart N4/N8 vaut4.7343%, sous5%; ce seuil de maillage ne remplace pas les références échouées.

Dans les trois références A24 à10rad/ms, la RKE initiale native est0,1346221J identique enXYZ. L'énergie propre de l'épaisseur physique des coques métalliques/composites, de masse0,322g et d'épaisseur0,5mm, vaut0,000335416667J enX/Y et zéro pour une rotation normaleZ. L'énergie native transverse est environ401fois cette référence. La masse répartie dans le plan est déjà représentée par les translations nodales. La RKE native reste néanmoins intégralement dans tous les bilans; sa suppression serait une réparation comptable sans justification.

Cette observation montre que le sous-modèle de support n'a pas encore une inertie rotative physique vérifiée. Elle invalide l'attribution exclusive de l'échec de moment au décalage de l'attache. Le tenseur natif par nœud et l'effet du cœur TYPE2 ne sont pas encore lus; ce diagnostic ne prouve pas que la totalité de la dérive ou du déficit local A21 provient des coques.

## 6. Contradictions et informations manquantes

La nouvelle géométrie échoue à son hypothèse suffisante: distance initiale nulle et bon bilan énergétique ne suffisent pas. Le support rotatif doit être vérifié séparément avec inertie physique, rigidité de membrane et de flexion, avant de déclarer une attache valide. Une nouvelle représentation volumique doit conserver volumes, masses, orientations et propriétés, avec contrôles de compatibilité et convergence; aucune conversion implicite. Les144ancres réelles sont préparées mais aucun ruban courbe n'est lancé ou inséré. Résistance, fracture, arrachement, grande vitesse, matériaux A21, gravité, intérieur porteur et contacts de fragments restent ouverts. La vidéo de10secondes physiques n'est pas produite par ce témoin.

AIRCRAFT-A26 : conserver A24/A25 et leurs échecs sans relancer leurs solveurs. Le simple décalage nul ne restaure pas le moment physique. Les références de coques héritées portent0,1346221J de RKE à10rad/ms, contre0,0003354167J physique transverse et zéro drilling: contrôler le modèle de masse rotative du support avant d’accuser exclusivement Spot25. Aucune soustraction ou reconstruction RKE dans les bilans, aucune compensation de densité ou ADMAS. Tester une représentation à translations pour les plaques/peaux, ou un raffinement contrôlé, avec mêmes volumes, densités, matériaux, orientations et capacités annoncées. Les lois orthotropes et la flexion doivent être vérifiées; une conversion de formulation ne qualifie pas automatiquement un matériau. Le noyau A20 reste préservé: toute nouvelle liaison conforme relève d’une déclaration et de témoins distincts. Le fichier root_geometry_preparation.json donne les24racines et144ancres réelles, avec faces principales, normales et épaisseurs. Leur géométrie native et leur budget restent à construire après qualification du raccordement. Ensuite nouveau départ entier intact et bilan local, coût réel avant calcul long. Matériaux A21, gravité, intérieur, fracture et contacts de fragments restent ouverts. Objectif10secondes physiques3D incomplet, meilleur entier A20=20ms; aucun dommage connu comme cible. Publication A24+A25 après intégrité vérifiée.
