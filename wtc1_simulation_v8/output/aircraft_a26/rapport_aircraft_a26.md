# AIRCRAFT-A26 — plaques sans inertie nodale de rotation

**18 nouveaux calculs natifs complets**, avec une tentative Starter conservée. Les **neuf témoins métal volumique TYPE20 HA8 passent tous leurs contrôles**, dont inertie physique, moment libreXYZ, énergie, traction et flexion indépendantes, raffinement spatial et temporel. Les neuf témoins triangulaires DKT_S3 et leurs cinq échecs sont conservés. Qualification limitée à la plaque métallique isolée; aucun transfert entier ni vidéo10secondes physiques.

## 1. Faits directement observés ou transcrits

Graine1102051, aucun tirage aléatoire. Plaque10×10×0,5mm, volume50mm³, masse0,139g. DKT_S3 w0: triangles à translations, rotation calculée via les voisins. TYPE20 w2: hexaèdres HA8 à translations, maillages6×6×1 et12×12×1. Aucun matériau de l'avion entier n'est remplacé. CPU1thread, aucun GPU, ADMAS ou mise à l'échelle. Entrées, sorties, scripts générateurs, vitesses, masses, temps d'exécution et critères sont conservés.

TYPE20 w1 s'arrête sur l'avertissement100214: des colonnes réservées contiennent des zéros au lieu d'espaces. Aucun Engine w1 lancé. Une nouvelle déclaration w2 conserve géométrie, matériau et seuils, corrige seulement ces champs et passe le Starter sans avertissement. Aucun ancien solveur répété. Les54échantillons de champs w0/w2 sont finis, sans suppression, et passent les identités de coordonnées avec borne explicite d'impression. Préservation de20151fichiers antérieurs, soit64.908Go.

La publication A24+A25 est vérifiée pendant la déclaration A26: elle met à jour la cadence et les métadonnées de publication, sans changer les résultats scientifiques ou le registre. Les snapshots initiaux A26 sont gardés, et une nouvelle référence de registre après publication est vérifiée séparément.

## 2. Résultats d'un modèle officiel

La [théorie DKT_S3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_3_node_triangle_without_rot_dof_r.htm) décrit la flexion dérivée des translations de voisins. [TYPE20](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type20_tshell_starter_r.htm) décrit HA8 et le choix de direction d'épaisseur. Les témoins vérifient ces formulations avec références indépendantes; leurs intitulés ne suffisent pas à la qualification. Aucun dommage connu ou résultat NIST n'est une cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo ou photographie historique. Matériau LAW2 repris en lecture seule du fichier source A20 identifié dans material_source_addendum.json. Les24racines/144ancres réelles inventoriées A25 restent disponibles pour la suite. La plaque d'essai n'est pas une nouvelle identification de la structure AA11.

## 4. Hypothèses propres au modèle

LAW2 métallique hérité:rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, écrouissage nul, rupture absente. DKT et HA8 conservent volume et densité; leurs masses nodales diffèrent et sont calculées explicitement par intégration des aires/volumes. Aucun réajustement des inerties. Pour HA8, le tenseur discret tient compte des deux faces d'épaisseur; il est confronté au tenseur continu du même parallélépipède, au seuil2%, sans déclaration d'exactitude continue.

Rotations libres10rad/ms pendant0,05ms surXYZ, translation[-200,5,2]m/s, pasY réduit. Traction affine epsilon_x0,001 avec contractions de Poisson. Flexion cylindrique de courbure0,001/mm, déplacements volumétriques cohérents avec sigma_z=0 au premier ordre et courbure_y=0. Référence de flexion D=Et³/[12(1−nu²)], sans calage à un résultat natif. Une couche géométrique d'épaisseur et huit points d'intégration pour HA8; direction s bottom-to-top suivant la convention native. Le matériau composite et les attaches ne sont pas concernés par cette qualification.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
| w0 / FREE_ROTATION_X_N12 | 5.662142e-06 | **échoué**: free_linear_momentum |
| w0 / FREE_ROTATION_Y_N12 | 5.851951e-06 | **échoué**: free_linear_momentum |
| w0 / FREE_ROTATION_Z_N12 | 7.69671e-08 | réussi |
| w0 / FREE_TRANSLATION_N12 | 0 | réussi |
| w0 / FREE_ROTATION_Y_N12_HALF | 5.855218e-06 | **échoué**: free_linear_momentum |
| w0 / MEMBRANE_N6 | 1.06537e-09 | réussi |
| w0 / MEMBRANE_N12 | 1.04729e-09 | réussi |
| w0 / BENDING_N6 | 0.000126773749 | **échoué**: native_full_balance |
| w0 / BENDING_N12 | 0.000545413144 | **échoué**: native_full_balance |
| w2 / FREE_ROTATION_X_N12 | 6.877e-09 | réussi |
| w2 / FREE_ROTATION_Y_N12 | 6.877e-09 | réussi |
| w2 / FREE_ROTATION_Z_N12 | 7.91302e-08 | réussi |
| w2 / FREE_TRANSLATION_N12 | 0 | réussi |
| w2 / FREE_ROTATION_Y_N12_HALF | 5.94e-09 | réussi |
| w2 / MEMBRANE_N6 | 1.38886e-09 | réussi |
| w2 / MEMBRANE_N12 | 1.43724e-09 | réussi |
| w2 / BENDING_N6 | 9e-12 | réussi |
| w2 / BENDING_N12 | 9.1e-12 | réussi |

Les deux formulations ne produisent aucune RKE nodale indépendante. DKT passe le moment physique libre mais échoue au critère absolu strict de quantité de mouvement dans les rotationsX/Y etY à pas réduit. L'historique natif confirme une dérive maximaleY d'environ1,637529e-8N·s; cet échec n'est pas seulement celui d'une somme de valeurs de vitesse imprimées. Ses flexions retrouvent la rigidité intérieure de référence mais échouent au bilan global natif; enN12 le résidu maximal vaut0,000545413144J, avec travail extérieur final négatif. Aucun correctif comptable n'est appliqué.

Les neuf témoins HA8 passent les critères de masse, énergie complète, quantité de mouvement, moment physique, énergie initiale discrète/continue, traction et flexion. Leur pas réduit est0.5fois le pas initial, différence de moment3.41946608e-13kg·m²/s et d'énergie1.27454375e-08J; les seuils initialement déclarés passent. L'écart N6/N12 de traction est0% et celui de flexion0.00815709299%, sous5%. Ces réussites sont propres à la plaque isolée et aux sollicitations déclarées.

## 6. Contradictions et informations manquantes

La suppression des rotations nodales indépendantes ne garantit pas à elle seule un bilan correct: les échecs DKT en témoignent. HA8 réussit sur métal, mais ne qualifie pas la peau orthotrope LAW25, la jonction au cœur, les attachés réels ou les matériaux à rupture. Une nouvelle formulation composite nécessite mêmes volumes, orientation, densité et quadrature documentés, avec contrôles propres. La référence LAW25/4 utilisée dans les témoins précédents est élastique, pas une loi de rupture historique validée. L'avion, la façade, la gravité, l'intérieur porteur et les contacts de fragments restent à qualifier. Le meilleur calcul entier demeure A20=20ms, avec les échecs locaux A21 préservés. Aucun état invalide n'est prolongé pour fabriquer une vidéo10secondes.

AIRCRAFT-A27 : reprendre metal_qualification_review.json. Les9témoins métal TYPE20 HA8 passent masse, inertie discrète/continue, libreXYZ, translation, moment physique, bilan natif, membrane/flexion indépendantes et raffinements. DKT_S3 élimine RKE mais son bilan de flexion et son critère strict de quantité de mouvement échouent; conserver ces9calculs. La tentative TYPE20 w1 s’arrête au Starter sur des champs réservés non blancs; w2 corrige uniquement le format et réussit. Qualifier maintenant la peau orthotrope LAW25 héritée en TYPE22 HA8 avec volumes/densité/orientation/quadrature explicites, sans supposer une équivalence matérielle. LAW25/4 est une référence élastique, pas la rupture historique qualifiée. Puis vérifier le sandwich/cœur et les24racines/144ancres réelles inventoriées A25, sans montage entier d’une liaison non qualifiée, ni prolongation d’un état A21 invalide. Les paramètres de rupture, matériaux, gravité, intérieur porteur et contacts des fragments restent ouverts. Nouveau départ entier intact seulement après bilans; mesurer le coût avant tout calcul long. Objectif vidéo3D10secondes physiques incomplet, meilleur entier A20=20ms. Publication suivante A26+A27 après intégrité. Aucun dommage connu comme cible, aucune compensation de masse ou RKE.
