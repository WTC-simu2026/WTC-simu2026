# AIRCRAFT-A33 — peau à intérieur libre, relaxation aux bords non qualifiée

Huit nouveaux calculs natifs complets : trois ensembles individuels passent, cinq échouent, huit bilans énergétiques passent. Une peau à quatre cellules dans l’épaisseur passe la comparaison énergétique mais échoue au champ intérieur. Aucun ancien critère n’est réécrit et aucun nouvel impact entier n’est exécuté.

## 1. Faits directement observés ou transcrits

Graine 1102058, aucun tirage. Même plaque 10×10×0,5 mm, volume 50 mm³, densité 0,00183 g/mm³, masse 0,0915 g. TYPE6/Isolid24, Ismstr4, Icpre3, Iframe2, axes Y,−X,Z et carte LAW12 source inchangés. Une, deux ou quatre cellules géométriques dans l’épaisseur; maillage 12/24 dans le plan. Les flexions prescrivent uniquement les deux faces extérieures; les autres nœuds sont effectivement libres. Le contrôle affine transverse prescrit tous les nœuds et reste un témoin distinct. Aucun transfert dans les fichiers de l’avion entier.

Les 24 échantillons de champs natifs passent : identifiants, finitude, identité coordonnées−déplacements avec borne d’impression, absence de suppression. Cartes, formulations et masses vérifiées. 24117 anciens fichiers conservés par empreintes (68.469 Go); aucun ancien solveur relancé, aucune archive source balayée.

## 2. Résultats d’un modèle officiel

[TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) documente Isolid24 à stabilisation physique; cela ne qualifie pas automatiquement son champ intérieur. Le protocole de réaction hérité de A31 distingue les impulsions effectivement sorties par ce binaire du libellé force de [TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm). Pour chaque flexion, la somme des réactions brutes suit la variation de quantité de mouvement; leur interprétation en forces intégrées échoue. Pour le patch affine symétrique à quantité de mouvement nette nulle, seule la cohérence de somme et le travail aux limites sont contrôlés; aucune interprétation autonome non ambiguë n’est annoncée.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation historique ou analyse vidéo. Les sources matérielles, budgets et cartographie des 24 racines/144 ancres courbes restent ceux des sorties conservées. Aucun dégât connu, observation vidéo ou résultat NIST utilisé comme cible. Les propriétés historiques de rupture restent non identifiées.

## 4. Hypothèses propres au modèle

LAW12 est le témoin 3D élastique A29 : E=[22000,22000,10000] MPa, G=[4000,4000,4000] MPa, coefficients transverses explicites 0,25. Ses seuils géants ne sont pas une loi physique de rupture de l’avion. Rampe 0,1 ms, κ=0,001/mm et champ aux faces ux=−κxz−κ²x³/6, uy=0, uz=κx²/2, multiplié par s=3u²−2u³. Mouvements libres ΩY=10 rad/ms et translation [−200,5,2] m/s pendant 0,05 ms. Les maillages supplémentaires partagent les mêmes volumes et densités; aucune masse ou inertie compensée.

Référence indépendante fixée avant les sorties A33 : calcul conventionnel 192×192×16 A32, énergie 1,18892058968×10⁻⁵ J, contrôles de Jacobien, symétrie, équilibre, travail virtuel et énergie, raffinements XY/Z 0,65%/0,34%. Les nœuds A33 coïncident avec ceux de cette grille imbriquée; les déplacements correspondants sont lus directement, sans ajustement. Les faces physiques ont les mêmes conditions et l’intérieur est libre.

Seuils déclarés : comparaison élastique 2%+10⁻⁷ J, bilan complet 2%+10⁻⁷ J, raffinement spatial 5%, temporel 0,2%, rapport de pas <0,6, KE finale 1% de la référence+10⁻⁷ J, travail plastique <10⁻⁷ J. La tolérance du champ intérieur est 2% de la relaxation indépendante par rapport au prolongement du champ imposé aux faces, plus 2×10⁻⁶ mm. Ce contrôle distingue la petite relaxation de la courbure globale prescrite; aucun seuil élargi après les résultats.

## 5. Résultats dérivés

| Contrôle | IE+HE natif (J) | Référence au temps natif (J) | Résidu bilan maximal (J) | Ensemble original |
|---|---:|---:|---:|---|
| PATCH_NORMAL_Z_N12_Z2 | 0.0003162848 | 0.0003163904092168612 | 1.5736243e-10 | réussi |
| FREE_ROTATION_Y_N12_Z2 | 1.091509e-05 | sans objet | 1.256624e-07 | réussi |
| FREE_TRANSLATION_N12_Z2 | 0 | sans objet | 0 | réussi |
| FACE_BENDING_N12_Z1 | 1.226754e-05 | 1.1882671087634038e-05 | 1.775e-11 | **échoué** : independent_elastic_energy |
| FACE_BENDING_N12_Z2 | 1.223521e-05 | 1.188239214959724e-05 | 3.0715e-10 | **échoué** : independent_elastic_energy, independent_interior_relaxation |
| FACE_BENDING_N24_Z2 | 1.223527e-05 | 1.1882392011104071e-05 | 1.958531e-10 | **échoué** : independent_elastic_energy, independent_interior_relaxation |
| FACE_BENDING_N24_Z4 | 1.197319e-05 | 1.1882232519609158e-05 | 2.100398e-10 | **échoué** : independent_interior_relaxation |
| FACE_BENDING_N24_Z2_HALF | 1.223511e-05 | 1.1882225232841337e-05 | 1.9657e-10 | **échoué** : independent_elastic_energy, independent_interior_relaxation |

Le témoin à une seule cellule est déclaré comme contrôle négatif séparé et échoue encore à l’énergie; son résultat A32 n’est pas remplacé. Avec deux cellules, l’énergie et le champ intérieur échouent. Avec quatre cellules, l’écart énergétique est 0.765492%, mais l’erreur maximale du champ intérieur vaut 8.21543643e-06 mm pour une tolérance 2.74166951e-06 mm. Tous les travaux aux faces, bilans et contrôles de KE finale passent, avec travail plastique nul. L’accord énergétique seul ne suffit donc pas.

| Contrôle | Coordonnée de l’erreur maximale (mm) | Composante | Erreur (mm) |
|---|---|---|---:|
| FACE_BENDING_N12_Z2 | [5.0, 2.5, 0.0] | Z | 7.85322275e-06 |
| FACE_BENDING_N24_Z2 | [5.0, 2.5, 0.0] | Z | 7.85329545e-06 |
| FACE_BENDING_N24_Z4 | [5.0, -4.583333333333333, 0.0] | Z | 8.21543643e-06 |

Les plus grands écarts se situent à x=5 mm, sur un bord libre dans l’épaisseur. Cette localisation est une observation du cache, pas une cause démontrée. Les maillages et opérateurs discrets peuvent encore influencer cette relaxation. Le rapport de pas demi/initial est 0.5; la différence énergétique temporelle vaut 8.10013225e-11 J. Les variations énergétiques XY/Z passent les seuils spatiaux, mais les critères individuels échoués restent contraignants.

Une inspection logicielle en lecture seule trouve Ubuntu 24.04.4 WSL avec CMake/GCC/Make, sans GFortran ou MPI sur PATH et sans paquet MUMPS inventorié. Les documents du miroir OpenRadioss figé au commit bad6688602d770e019b75773d2d5a48b4f9bd918 sont contrôlés par empreintes de blobs Git. Sa licence AGPL-3.0 est conservée; identité avec le binaire Windows non démontrée. La construction MUMPS documentée demande double précision et MPI. Une proposition séparée décrit outils manquants, espace, limite de calcul, empreintes et nouveaux témoins. Aucune installation, compilation, modification ou publication de binaire réalisée.

## 6. Contradictions et informations manquantes

Quatre cellules améliorent l’énergie sans satisfaire le déplacement intérieur aux bords. Deux cellules plus efficaces ne passent pas; cette piste n’est pas qualifiée pour l’impact entier. Résistance, décollement, rupture, prises courbes, façade et contacts de fragments restent ouverts. Aucun ajout RKE, densité modifiée, masse inventée ou prolongation balistique non calculée.

Le binaire actuel refuse l’implicite avec MUMPSrequired dans les sondes A31 conservées. Installer et compiler un solveur séparé nécessite une demande explicite de Jeremy selon AGENTS.md; la proposition existe, l’autorisation supplémentaire n’est pas présumée. Sa réussite ne garantirait ni l’accélération ni la qualification du modèle entier. Un nouveau binaire doit être contrôlé séparément, et aucun restart Windows n’est présumé compatible.

Meilleur impact entier A20 : 20 ms physiques. La vidéo de dix secondes physiques reste à produire; les aperçus ralentis ne remplissent pas cet objectif.

AIRCRAFT-A34 : conserver les défauts de relaxation aux bords A33, étudier leur raffinement géométrique et l’opérateur discret avant une prise courbe ou insertion entière. La référence indépendante A32 à faces prescrites et intérieur libre passe ses contrôles; A33Z4passe l’énergie mais pas le champ intérieur. Une compilation séparée avec MUMPS est proposée dans aircraft_a33/native_build_preflight, soumise à accord explicite Jeremy pour installation/compilation; ne pas l’exécuter sans cet accord. Après accord, déclarer configuration/source/version et contrôles avant construction et nouveaux calculs; aucune compatibilité de reprise Windows/Linux présumée. Sans cet accord, les diagnostics et contrôles mécaniques du binaire actuel peuvent continuer. Aucun ajout de masse/densité, RKE inventé ou dommage connu comme cible. Capacités, décollement et rupture historiques non identifiés; LAW12reste un témoin élastique hypothétique. Meilleur entier A20=20ms; vidéo3D10secondes physiques incomplète. Publication A32+A33 après vérification; cadence suivante A34+A35.
