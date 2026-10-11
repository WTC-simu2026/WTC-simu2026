# AIRCRAFT-A32 — formulations volumiques efficaces, flexion non qualifiée

Trente nouveaux calculs natifs complets, vingt-six ensembles individuels réussis, quatre flexions échouées et trente bilans énergétiques réussis. Les quatre échecs originaux restent inchangés. Le diagnostic indépendant révèle une référence initiale incompatible avec une relaxation transverse admissible, mais ne démontre pas l’équivalence des formulations natives à un continuum à intérieur libre. L’objectif de dix secondes physiques reste incomplet.

## 1. Faits directement observés ou transcrits

Graine 1102057, aucun tirage. Plaque 10×10×0,5 mm, volume 50 mm³, densité 0,00183 g/mm³, masse 0,0915 g. Une cellule géométrique dans l’épaisseur et maillages 6/12 dans le plan. w0 emploie TYPE21/HSEPH15, neuf points dans l’épaisseur; w1 TYPE6/HEPH24. Les deux conservent LAW12, ses constantes, ses axes Y,−X,Z et le budget physique. Aucun ADMAS, aucun RKE ajouté ou compensé. Les cartes et paramètres sont contrôlés dans les sorties Starter réelles avant Engine.

90 échantillons natifs passent les contrôles d’identifiants, finitude, coordonnées−déplacements avec borne d’impression et absence d’élément supprimé. Les raffinements temporels et spatiaux passent dans leur périmètre; une convergence entre deux calculs ne remplace pas l’accord avec une référence indépendante. Conservation vérifiée de 23227 fichiers antérieurs (68.064 Go), sans nouveau balayage des archives ni ancien solveur relancé.

La première lecture w0 s’est arrêtée avant Engine parce que le lecteur attendait le tableau TYPE6 à neuf colonnes. TYPE21 imprime cinq colonnes Isolid/Ismstr/Icpre/NPT/ICONTROL, valeurs 15/4/3/9/0. La version erronée et l’échec sont conservés. La reprise corrige seulement cette lecture, utilise les mêmes entrées et achève les calculs w0 encore non exécutés, sans répéter w1. NPT n’est pas Iframe. Le résumé après reprise est l’autorité; l’ancien résumé reste une trace historique.

## 2. Résultats d’un modèle officiel

La documentation primaire [TYPE21](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type21_tsh_orth_starter_r.htm) décrit HSEPH15 et les points dans l’épaisseur; [TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) décrit HEPH24 à stabilisation physique. Ces descriptions ne prouvent pas leur équivalence à une discrétisation conventionnelle pour les conditions imposées ici. Aucun résultat NIST ni dégât observé n’entre dans la référence ou les seuils.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse vidéo ou affirmation historique. Sources matérielles et budgets hérités de A20/A29, géométrie des 24 racines et 144 ancres conservée dans A31. Aucun assemblage AA11 réel n’est identifié par ces plaques. Les inventaires et sources sont réutilisés en lecture seule.

## 4. Hypothèses propres au modèle

LAW12 reste un témoin élastique explicite : E=[22000,22000,10000] MPa, G=[4000,4000,4000] MPa, coefficients transverses 0,25. Ses seuils géants ne constituent pas une résistance physique ou une loi de rupture historique. Rotation libre Ω=10 rad/ms, translation [−200,5,2] m/s; durée 0,05 ms. Champs affines et membrane/bending : rampe s=3u²−2u³ sur 0,1 ms. Les déplacements des nœuds de flexion sont ux=−κxz−κ²x³/6, uy=0, uz=κx²/2, κ=0,001/mm. Avec une seule cellule dans l’épaisseur, tous les nœuds appartiennent aux faces externes; leur contrainte n’impose pas nécessairement εzz en chaque point intérieur d’une formulation enrichie.

Les seuils originaux sont conservés : énergie élastique 2%+10⁻⁷ J, bilan complet 2%+10⁻⁷ J, raffinements spatial 5% et temporel 0,2%, rapport de pas réduit <0,6. IE et HE restent séparés dans le bilan; leur somme est la comparaison élastique déclarée. Aucun terme énergétique inventé.

Après les résultats originaux, un diagnostic séparé prescrit les deux faces physiques sur un continuum 3D conventionnel, avec tous les nœuds intérieurs libres. Le champ admissible uz=κx²/2+(Czx/Czz)κ(z²−t²/4)/2 conserve uz aux deux faces mais autorise εzz=(Czx/Czz)κz et σzz=0. Il démontre une possibilité mathématique, sans identifier l’opérateur interne natif. La référence analytique condensée vaut 1,22222222×10⁻⁵ J, contre 1,33490023×10⁻⁵ J pour Cxx plein, à amplitude finale de premier ordre. Les bords libres et la correction du second ordre sont traités par la référence 3D indépendante, sans ajustement de module.

Le sixième calcul indépendant initial s’est arrêté au travail virtuel. Les cinq références acceptées sont conservées. Une déclaration distincte resserre uniquement la résolution CG de 10⁻¹⁰ relatif+10⁻¹¹ N à 10⁻¹³ relatif+10⁻¹⁴ N, sans modifier les contrôles de symétrie, équilibre, travail virtuel ou somme des énergies. Le raffinement XY 48→96 échoue au seuil diagnostic 2% (2,442014%). Une extension séparée 192×192×8/16 est déclarée avant ses résultats; aucun ancien critère n’est remplacé rétrospectivement.

## 5. Résultats dérivés

| Branche | Contrôle | Résidu énergétique maximal (J) | Ensemble original |
|---|---|---:|---|
| w0 | CONSTRAINED_BENDING_N12 | 2.951e-10 | **échoué** : independent_elastic_energy |
| w0 | CONSTRAINED_BENDING_N6 | 4.730609e-10 | **échoué** : independent_elastic_energy |
| w0 | FREE_ROTATION_X_N12 | 2.3799e-08 | réussi |
| w0 | FREE_ROTATION_Y_N12 | 1.626e-08 | réussi |
| w0 | FREE_ROTATION_Y_N12_HALF | 4.0205e-08 | réussi |
| w0 | FREE_ROTATION_Z_N12 | 2.200812e-07 | réussi |
| w0 | FREE_TRANSLATION_N12 | 0 | réussi |
| w0 | MEMBRANE_N12 | 3.58077e-10 | réussi |
| w0 | MEMBRANE_N6 | 3.40624e-10 | réussi |
| w0 | PATCH_NORMAL_X_N12 | 6.352271e-10 | réussi |
| w0 | PATCH_NORMAL_Y_N12 | 7.352271e-10 | réussi |
| w0 | PATCH_NORMAL_Z_N12 | 3.0099815e-10 | réussi |
| w0 | PATCH_SHEAR_XY_N12 | 1.2761353e-10 | réussi |
| w0 | PATCH_SHEAR_XZ_N12 | 1.240578e-10 | réussi |
| w0 | PATCH_SHEAR_YZ_N12 | 1.340578e-10 | réussi |
| w1 | CONSTRAINED_BENDING_N12 | 1.775e-11 | **échoué** : independent_elastic_energy |
| w1 | CONSTRAINED_BENDING_N6 | 1.274e-11 | **échoué** : independent_elastic_energy |
| w1 | FREE_ROTATION_X_N12 | 1.67176e-07 | réussi |
| w1 | FREE_ROTATION_Y_N12 | 1.60405e-07 | réussi |
| w1 | FREE_ROTATION_Y_N12_HALF | 1.57789e-07 | réussi |
| w1 | FREE_ROTATION_Z_N12 | 5.1071e-07 | réussi |
| w1 | FREE_TRANSLATION_N12 | 0 | réussi |
| w1 | MEMBRANE_N12 | 3.58077e-10 | réussi |
| w1 | MEMBRANE_N6 | 4.15146e-10 | réussi |
| w1 | PATCH_NORMAL_X_N12 | 6.352271e-10 | réussi |
| w1 | PATCH_NORMAL_Y_N12 | 7.352271e-10 | réussi |
| w1 | PATCH_NORMAL_Z_N12 | 3.0099815e-10 | réussi |
| w1 | PATCH_SHEAR_XY_N12 | 1.2761353e-10 | réussi |
| w1 | PATCH_SHEAR_XZ_N12 | 1.340578e-10 | réussi |
| w1 | PATCH_SHEAR_YZ_N12 | 1.340578e-10 | réussi |

La référence exacte aux faces atteint 1,18892058968×10⁻⁵ J avec 192×192×16 éléments. Variation XY 96→192 à Z8 : 0.65016%; variation Z8→16 à XY192 : 0.335184%. Les deux critères diagnostics 2% passent, avec les contrôles indépendants inchangés. Les références grossières étaient sensibles au cisaillement induit par leur interpolation du déplacement quadratique; raffiner uniquement Z ne suffisait pas.

| Branche | Maillage XY natif | IE+HE natif (J) | Référence raffinée au temps natif (J) | Écart diagnostic |
|---|---:|---:|---:|---:|
| w0 | 6 | 1.226688e-05 | 1.1882671e-05 | 3.23336% |
| w0 | 12 | 1.226733e-05 | 1.1882671e-05 | 3.23714% |
| w1 | 6 | 1.226732e-05 | 1.18826712e-05 | 3.23706% |
| w1 | 12 | 1.226754e-05 | 1.18826711e-05 | 3.23891% |

Ces écarts restent un diagnostic après exécution. Les quatre échecs à la référence Cxx originale sont conservés et aucune qualification de flexion n’est accordée. Le fait que les deux formulations donnent presque la même énergie ne prouve pas leur équivalence au continuum à intérieur libre. Les pas natifs d’environ 4,79×10⁻⁵ ms sont environ quatre fois ceux du témoin A31 fin; cela ne permet pas d’estimer directement le coût d’un avion entier avec contacts.

## 6. Contradictions et informations manquantes

La référence Cxx supposait une contrainte transverse point par point absente des conditions nodales réellement imposées à une peau d’une cellule. Sa correction analytique ne ferme cependant pas l’écart avec le continuum à bords et intérieur libres. La prochaine étape doit permettre ces degrés de liberté physiques et contrôler leur effet avant une insertion entière. Champs de contraintes moyens aux points natifs archivés, mais opérateurs de déformation enrichie non directement observés.

Masse, matériaux, capacités des prises courbes, plasticité, décollement, rupture, façade et contacts de fragments restent à traiter dans leurs périmètres. Les seuils géants LAW12 ne sont pas transférables comme résistance physique. Le binaire implicite installé échoue avec MUMPSrequired; aucun logiciel installé, compilé ou modifié. A20 reste le meilleur impact entier à 20 ms, et son coût ne garantit pas celui de dix secondes. Aucune prolongation balistique ou animation inventée ne remplace les états calculés.

AIRCRAFT-A33 : tester une peau TYPE6/Isolid24 à plusieurs cellules physiques dans l’épaisseur, faces seules chargées et intérieur libre, avec la référence continuum indépendante A32 désormais raffinée. Déclarer avant les sorties les contrôles de flexion, inertie libre, affine transverse et raffinements; conserver les quatre échecs A32. Puis tester la transmission du sandwich et les prises courbes avant insertion entière. Aucun ajout de masse, changement de densité ou terme RKE artificiel. LAW12 et ses coefficients transverses restent des hypothèses élastiques; résistance, décollement et rupture historiques non identifiés. L’implicite du binaire installé réclame MUMPS; aucune installation ou modification de solveur autorisée ou effectuée. Meilleur impact entier A20=20ms, objectif vidéo3D10secondes physiques incomplet. Publication suivante A32+A33 après vérification.
