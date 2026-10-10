# AIRCRAFT-A24 — transmission par pénalité et moment cinétique physique

**45 nouveaux contrôles natifs**, tous avec bilan énergétique réussi. La masse et l'énergie cinétique initiale ajoutée sont correctes. La traction de prototype converge avec Stfac100. **Le moment cinétique libre du montage décalé échoue surXYZ**, et cet échec demeure à pas réduit. La liaison n'est pas montée sur l'avion. L'objectif de vidéo3D des10premières secondes physiques reste incomplet; A20 couvre20ms.

## 1. Faits directement observés ou transcrits

Graine1102049, aucun tirage aléatoire. Campagnes w0:19calculs, w1:10, w2:6, w3:10. Chaque calcul conserve entrée Starter/Engine, sorties natives, journaux, code générateur, masses, bilan complet et critères. Aucun nouveau calcul entier, aucun calcul A20–A23 répété. Quatre références A24 sont recalculées sous une déclaration d'observation nouvelle pour obtenir VRX/VRY/VRZ, indisponibles dans l'observation initiale. Les autres références et les six tractions w2 sont réemployées.

Visc=0 est lu par le Starter comme le défaut0,05, avec dissipation native: les échecs du critère de dissipation≤1e-12J sont conservés. w1 utilise une valeur positive1e-20, effectivement relue avant Engine; elle représente une viscosité négligeable, sans prétendre être exactement nulle. Les matériaux, masses et seuils de bilan ne changent pas. w2 fait varier Stfac1/10/100 et contrôle sa relecture. Après ses six tractions, son générateur échoue sur le suffixe S100_X avant tout lancement natif libre. Cette tentative est gardée; w3 déclare une correction explicite de lecture de l'axe et ajoute les vitesses angulaires natives.

Les135champs natifs échantillonnés sont finis, conservent les éléments et passent une identité coordonnées/déplacements bornée par le stockage float32 et l'impression à six chiffres. Cette borne de lecture ne modifie aucun seuil mécanique. Un booléen NumPy empêche la première écriture JSON de l'audit angulaire; le lecteur initial est conservé, puis sa conversion en booléen Python permet l'écriture. Aucun solveur ni résultat antérieur n'est changé. Conservation vérifiée de18044fichiers antérieurs, soit64.337Go.

## 2. Résultats d'un modèle officiel

La documentation primaire [TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm) définit Spot25 comme une pénalité, décrit la rigidité issue des raideurs nodales, et signale ses limites de transmission des moments. Le solide secondaire n'a ici que des translations. Cela ne garantit toutefois pas la conservation du moment physique du montage, qui est mesurée séparément. Le [TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) fournit les vitesses angulaires VRX/VRY/VRZ. Aucun résultat officiel de dommage n'est pris comme cible. Ces documents décrivent le solveur, pas une attache historique.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo, photographie ou dommage historique. Réemploi en lecture seule de la géométrie A20 et des sources techniques sauvegardées. Les courbes acier A22 restent non adoptées et leur début de striction n'est pas un seuil de rupture.

## 4. Hypothèses propres au modèle

Solide HA8 TYPE14 à translations,4×1×0,5mm, masse0,00556g, LAW2 hérité rho0,00278g/mm³, E73100MPa, nu0,33, seuil324MPa, sans écrouissage ni rupture. Prototype de capacité axiale162N, sans identification AA11. Support10×10×0,5mm et sandwich A20, masses0,3604g sans et0,36596g avec solide. Les attaches du cœur Spot5 p3 sont inchangées. Seules les deux attaches d'extrémité301/302 utilisent Spot25, Istf2, dsearch0,8mm. Stfac est un paramètre de pénalité, pas une résistance matérielle ajustée. Les zéros hérités des coefficients de viscosité volumique sont des demandes de défaut natif, pas des suppressions affirmées.

Toutes les huit énergies natives sont incluses: cinétique de translation, rotation, interne, hourglass, ressort, contact élastique, contact de frottement et contact amorti. Résidu E(t)−E(0)−travail extérieur; g/mm/ms convertis en J par0,001. Aucune reconstruction RKE, ADMAS, mise à l'échelle ou compensation de densité.

Le moment physique est calculé par Σm r×v et l'inertie propre de l'épaisseur des coques avec leurs vitesses angulaires réellement enregistrées. Le tenseur d'épaisseur est m t²/12(I−n⊗n), sans compter deux fois la distribution dans le plan. Conversion g·mm²/ms vers kg·m²/s par1e-6. Aucun moment n'est déduit d'une énergie RKE scalaire. Ce calcul est un contrôle du modèle discret, pas une validation de l'événement historique.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Critères individuels |
|---|---:|---|
| w0 / CONNECTED_EXTENSION_N4 | 1.2575267e-11 | **échoué**: no_undeclared_contact_damping, stiff_clip_traction_reference |
| w0 / CONNECTED_EXTENSION_N8 | 1.190173e-11 | **échoué**: no_undeclared_contact_damping, stiff_clip_traction_reference |
| w0 / CONNECTED_FREE_ROTATION_X | 6.2793894e-06 | **échoué**: no_undeclared_contact_damping |
| w0 / CONNECTED_FREE_ROTATION_Y | 2.914326e-05 | **échoué**: no_undeclared_contact_damping |
| w0 / CONNECTED_FREE_ROTATION_Z | 8.9474325e-06 | **échoué**: no_undeclared_contact_damping |
| w0 / CONNECTED_FREE_TRANSLATION | 0 | réussi |
| w0 / CONNECTED_ROTATION_X | 1.3225559e-10 | **échoué**: no_undeclared_contact_damping |
| w0 / CONNECTED_ROTATION_Y | 1.3110269e-10 | **échoué**: no_undeclared_contact_damping |
| w0 / CONNECTED_ROTATION_Z | 8.9493863e-10 | **échoué**: no_undeclared_contact_damping |
| w0 / CONNECTED_ROTATION_Z_HALF | 9.2838636e-10 | **échoué**: no_undeclared_contact_damping |
| w0 / REFERENCE_EXTENSION | 1e-15 | réussi |
| w0 / REFERENCE_FREE_ROTATION_X | 7.439e-07 | réussi |
| w0 / REFERENCE_FREE_ROTATION_Y | 7.41e-07 | réussi |
| w0 / REFERENCE_FREE_ROTATION_Z | 5.284e-07 | réussi |
| w0 / REFERENCE_FREE_TRANSLATION | 0 | réussi |
| w0 / REFERENCE_ROTATION_X | 1.4431916e-10 | réussi |
| w0 / REFERENCE_ROTATION_Y | 1.4431916e-10 | réussi |
| w0 / REFERENCE_ROTATION_Z | 9.7509916e-10 | réussi |
| w0 / REFERENCE_ROTATION_Z_HALF | 5.7585324e-10 | réussi |
| w1 / CONNECTED_EXTENSION_N4 | 1.18157e-11 | **échoué**: stiff_clip_traction_reference |
| w1 / CONNECTED_EXTENSION_N8 | 1.32398e-11 | **échoué**: stiff_clip_traction_reference |
| w1 / CONNECTED_FREE_ROTATION_X | 6.5193e-06 | réussi |
| w1 / CONNECTED_FREE_ROTATION_Y | 2.93289e-05 | réussi |
| w1 / CONNECTED_FREE_ROTATION_Z | 8.2768e-06 | réussi |
| w1 / CONNECTED_FREE_TRANSLATION | 0 | réussi |
| w1 / CONNECTED_ROTATION_X | 1.2895354e-10 | réussi |
| w1 / CONNECTED_ROTATION_Y | 1.1978159e-10 | réussi |
| w1 / CONNECTED_ROTATION_Z | 9.4593317e-10 | réussi |
| w1 / CONNECTED_ROTATION_Z_HALF | 9.5839806e-10 | réussi |
| w2 / CONNECTED_EXTENSION_S100_N4 | 1.281e-11 | réussi |
| w2 / CONNECTED_EXTENSION_S100_N8 | 1.028e-11 | réussi |
| w2 / CONNECTED_EXTENSION_S10_N4 | 1.4055e-11 | **échoué**: stiff_clip_traction_reference |
| w2 / CONNECTED_EXTENSION_S10_N8 | 1.309e-11 | réussi |
| w2 / CONNECTED_EXTENSION_S1_N4 | 1.82e-11 | **échoué**: stiff_clip_traction_reference |
| w2 / CONNECTED_EXTENSION_S1_N8 | 9.9e-12 | **échoué**: stiff_clip_traction_reference |
| w3 / CONNECTED_FREE_ROTATION_S100_X | 8.4087e-07 | réussi |
| w3 / CONNECTED_FREE_ROTATION_S100_Y | 1.54481e-06 | réussi |
| w3 / CONNECTED_FREE_ROTATION_S100_Y_HALF | 1.48512e-06 | réussi |
| w3 / CONNECTED_FREE_ROTATION_S100_Z | 6.535955e-07 | réussi |
| w3 / CONNECTED_FREE_TRANSLATION_S100 | 0 | réussi |
| w3 / REFERENCE_FREE_ROTATION_S100_X | 7.439e-07 | réussi |
| w3 / REFERENCE_FREE_ROTATION_S100_Y | 7.41e-07 | réussi |
| w3 / REFERENCE_FREE_ROTATION_S100_Y_HALF | 7.44e-07 | réussi |
| w3 / REFERENCE_FREE_ROTATION_S100_Z | 5.284e-07 | réussi |
| w3 / REFERENCE_FREE_TRANSLATION_S100 | 0 | réussi |

Les45bilans passent, et31/45ensembles individuels passent. Ces ensembles initiaux n'incluent pas encore le moment physique: l'audit angulaire supplémentaire conserve donc un échec malgré les dix réussites individuelles w3.

| Axe, rotation prescrite w1 | Inertie ajoutée native(g·mm²) | Inertie discrète connue | Critères cinétiques |
|---|---:|---:|---|
| X | 0.265292083 | 0.26531625 | réussi |
| Y | 0.133938686 | 0.13396125 | réussi |
| Z | 0.147994862 | 0.148035 | réussi |

La pénalité élimine le biais cinétique ajouté constaté dans A23 sur les trois axes. Les paires initiales libres passent aussi. Cela ne qualifie pas la transmission des couples. La rotation prescrite w1 à pas réduit passe l'inertie individuelle mais échoue à la convergence de l'énergie ajoutée: écart2,38738149e-7J, seuil1,41149857e-7J. La traction Stfac1 reste trop souple; les deux maillages Stfac100 passent la référence3D rigide et leur écart de maillage est1.9933%, sous5%. L'échec initial de traction est conservé.

| Mouvement libre Stfac100 | Dérive du moment total(kg·m²/s) | Seuil total | Erreur du moment ajouté | Seuil ajouté | Résultat |
|---|---:|---:|---:|---:|---|
| ROTATION_S100_X | 9.57836977e-07 | 5.00668969e-07 | 9.5910971e-07 | 5.406325e-08 | **échoué** |
| ROTATION_S100_Y | 8.71747998e-07 | 4.98390234e-07 | 9.41947419e-07 | 3.86206427e-08 | **échoué** |
| ROTATION_S100_Z | 1.92444952e-06 | 7.29785477e-07 | 1.9244544e-06 | 4.06744571e-08 | **échoué** |
| TRANSLATION_S100 | 3.73211923e-12 | 7.76930261e-07 | 3.73211949e-12 | 1.54425339e-07 | réussi |

Les trois références sans solide passent le contrôle de moment total. Le montage échoue enXYZ; la translation uniforme passe. Le pas effectif réduit enY vaut0.241331377fois le pas initial. La différence entre moments des deux pas vaut7.85256823e-11kg·m²/s, très inférieure à la dérive: celle-ci ne disparaît pas avec le raffinement temporel testé. La convergence du bilan natif et du moment calculé ne signifie pas conservation physique.

## 6. Contradictions et informations manquantes

Une masse correcte, une énergie correcte et une traction convergée ne garantissent pas les couples transmis. Le décalage entre les extrémités solides et la surface principale est une hypothèse de diagnostic; sa responsabilité n'est pas prouvée par le seul échec. Une nouvelle géométrie de reprise des efforts doit être déclarée et testée. La courbure réelle des24racines et les144ancres ne sont pas qualifiées par ce témoin plat. Résistance historique, rupture, arrachement, cisaillement et propriétés à grande vitesse restent inconnus. L'échec local A21 n'est pas expliqué en totalité. Gravité, structure intérieure porteuse et contacts de fragments restent à traiter avant extension aux10secondes. Les anciens calculs et aperçus sont préservés; aucune continuation d'un état invalide.

AIRCRAFT-A25 : réemployer les45contrôles A24 et leurs échecs, sans relancer A20–A24. Spot25 conserve les masses et retrouve l’énergie cinétique initiale ajoutée; Stfac100 retrouve la traction N4/N8, mais le moment cinétique physique libre échoue surXYZ, même au pas réduit. Ne pas monter cette attache décalée sur l’avion. Tester une transmission des efforts aux points de raccordement, avec surfaces de reprise explicites et aucun bras de levier caché. Déclarer tout changement de géométrie, de masse nodale et de capacité. Le solide4×1×0,5mm et LAW2 hérité restent des hypothèses de prototype, pas une attache AA11 identifiée. Vérifier libreXYZ, translation, rigidité3D indépendante, pas et géométrie courbe des24racines/144ancres avant un nouveau départ entier intact. Garder le sandwich et les Spot5 A20 validés. Si l’on raffine une surface principale, vérifier sa masse, son tenseur et sa rigidité; aucune compensation de densité, ADMAS ou RKE. Le bilan local A21 reste échoué; matériaux, gravité, intérieur porteur, fracture et contacts des fragments restent ouverts. Objectif10secondes physiques3D incomplet; meilleur calcul entier20ms A20. Estimer le coût réel du prochain entier avant tout lancement de plusieurs heures. Publication suivante A24+A25 après intégrité vérifiée; aucun dommage connu comme cible.
