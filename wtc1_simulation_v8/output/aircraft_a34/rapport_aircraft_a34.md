# AIRCRAFT-A34 — défaut du champ intérieur après raffinement

Quatre nouveaux calculs natifs terminés. Un ensemble individuel passe, trois échouent au champ intérieur. Les quatre bilans et les douze échantillons natifs passent. Conservation vérifiée de 24383 fichiers antérieurs (68.729 Go). Les trois critères échoués sont conservés; aucun ancien solveur relancé.

## 1. Faits directement observés ou transcrits

Graine1102059, aucun tirage. Même plaque 10×10×0,5 mm, densité0,00183g/mm³, masse0,0915g, TYPE6/Isolid24, Ismstr4, Icpre3, Iframe2, source LAW12 et axesY,−X,Z inchangés. Maillage48 dans le plan, quatre/huit cellules physiques dans l’épaisseur. Faces seules prescrites en flexion, intérieur libre. Rotation libreY, flexionZ4/Z8 et flexionZ4à demi-pas. Quatre nouvelles exécutions, aucune ancienne relancée. Douze champs natifs: identifiants, finitude, coordonnées/déplacements avec borne d’impression, absence de suppression.

## 2. Résultats d’un modèle officiel

Formulation HEPH24 à stabilisation physique selon la documentation TYPE6 déjà conservée. La présence de cette formulation ne démontre pas l’équivalence de son opérateur à la référence conventionnelle. Même binaire Windows20260728, empreinte et journaux dans runtime_manifest_live.json. Aucun résultatNIST utilisé comme référence.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse d’archive, photographie ou vidéo. Les budgets/materials et inventaires des prises courbes hérités restent inchangés. Aucun résultat du coupon identifié comme propriété d’un assemblage réel d’AA11.

## 4. Hypothèses propres au modèle

Témoin LAW12élastique A29, E/G/coefficientstransverses conservés; seuils géants sans qualification historique de résistance ou rupture. κ=0,001/mm, rampe0,1ms, champ exact aux deux faces identique A33; ΩY=10rad/ms durant0,05ms. Référence3D indépendante192×192×16A32 avec mêmes faces et intérieur libre. Ses changements de champs Z8→16etXY96→192 sont vérifiés aux nœuds correspondants avant calcul natif. Tolérances originelles conservées: énergie2%+10⁻⁷J, déplacement intérieur2%de la relaxation+2×10⁻⁶mm, raffinements5%spatial/0,2%temporel, rapport de pas<0,6. Aucun seuil élargi après résultat, aucune densité/massescaleouRKEinventé.

## 5. Résultats dérivés

| Contrôle | IE+HE(J) | Référence au temps natif(J) | Résidu maximal(J) | Ensemble original |
|---|---:|---:|---:|---|
| FREE_ROTATION_Y_N48_Z4 | 1.131681e-05 | sans objet | 3.93e-08 | réussi |
| FACE_BENDING_N48_Z4 | 1.196883e-05 | 1.1882222289037267e-05 | 1.333393e-10 | **échoué** : independent_interior_relaxation |
| FACE_BENDING_N48_Z8 | 1.188664e-05 | 1.1882148775553845e-05 | 1.535854e-10 | **échoué** : independent_interior_relaxation |
| FACE_BENDING_N48_Z4_HALF | 1.196875e-05 | 1.188213820213908e-05 | 1.346779e-10 | **échoué** : independent_interior_relaxation |

Z8 atteint un écart énergétique d’environ0,038%, mais échoue au champ intérieur. Erreurs de déplacements d’environ7,8×10⁻⁶mm face à une tolérance2,74×10⁻⁶mm. Les deux contrôles du champ de référence passent au seuil déclaré. Rapport de pas demi/initial=0.500000084; différence énergétique=3.38804417e-11J. Les variations énergétiques XY/Z passent5%, sans remplacer les critères individuels échoués. Bilans, impulsions et travail aux faces passent; les détails sont conservés.

## 6. Contradictions et informations manquantes

L’accord énergétique se rapproche mais le défaut du champ intérieur persiste après raffinement XY/Z/temps. Sa cause n’est pas identifiée: ne pas l’attribuer à un opérateur précis sans contrôle distinct. Comparaison avec une formulation pleinement intégrée et examen des opérateurs stabilisés possibles avant toute prise courbe. Propriétés historiques, rupture, décollement et modèle entier restent ouverts.

A32+A33 publiées et vérifiées. Le présent rapport et les résultats sont scellés avant inscription A34 au registre et mise à jour de l’état. Aucun processus natif restant. La proposition de compilation séparée MUMPS A33 a reçu ensuite l’accord explicite de Jeremy : « Oui, installer et compiler le solveur séparé ». Les calculs A34 ont utilisé le solveur Windows inchangé; la tentative de construction séparée sera journalisée dans A35. Meilleur impact entierA20=20ms; vidéo3D10secondes physiques incomplète.


AIRCRAFT-A35 : priorité à la compilation séparée MUMPS autorisée explicitement par Jeremy le 11 octobre 2026, selon la proposition A33, limitée à une heure. Installer les dépendances minimales dans Ubuntu WSL, conserver le solveur Windows, les sources épinglées, les licences et tous les journaux. Vérifier ensuite une sonde implicite fraîche et des témoins explicites de même version avant toute extension entière. La comparaison mécanique préparée reste différée : TYPE6/Isolid18/Ismstr0→2 déjà exécuté dans A29/A31 et TYPE6/Isolid24/Ismstr2, en gardant la géométrie, LAW12, ses axes, densité, masse, conditions aux faces, référence indépendante et seuils A34. Le TYPE6/Isolid24/Ismstr4 reste une référence en cache, sans ancien solveur relancé. Lire les paramètres réellement acceptés par Starter; arrêter une branche à la première erreur ou au premier échec affine, conserver les tentatives et leurs différences. Contrôler objectivité/inertie libre, flexion, champs, bilans, travail et raffinements avant prise courbe puis insertion entière. Une meilleure énergie seule ne qualifie pas le mécanisme. Accord humain reçu : « Oui, installer et compiler le solveur séparé ». Une compilation réussie ne qualifie pas encore la dynamique implicite. Aucun changement de masse/densité, RKE inventé ou cible de dommage connu. Propriétés de rupture, décollement et prises historiques non identifiées; LAW12 reste un témoin élastique. Meilleur impact entierA20=20ms; vidéo3D10secondes physiques incomplète. Publication suivanteA34+A35après scellage.
