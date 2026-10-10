# AIRCRAFT-A27 — contrôle volumique de la peau composite

**22 nouveaux calculs natifs complets**, une tentative Starter conservée. Les22bilans complets natifs passent; les mouvements libres conservent la masse et les moments. La traction plane corrigée passe. **La flexion échoue encore**, au critère indépendant conservé: la peau composite et le raccordement entier ne sont pas qualifiés.

## 1. Faits directement observés ou transcrits

Graine1102052, aucun tirage aléatoire. Plaque10×10×0,5mm, volume50mm³. LAW25/4 hérité inchangé:rho0,00183g/mm³, masse0,0915g, E11=E22=22000MPa, nu12=0,25, E33=10000MPa, G12=G23=G31=4000MPa. Le matériau et les paramètres de l'avion entier restent intacts. TYPE22 HA8 à translations, direction d'épaisseur s (Icstr010), angle90°. Aucune rotation nodale indépendante, RKE nulle, aucun ajout de masse, aucune mise à l'échelle.

w0 utilise des positions/poids Gauss proposés comme données de couches: le Starter refuse ces rapports irréguliers (avertissement674). Entrée et sortie conservées, aucun Engine lancé. w1 remplace ces données par3subdivisions homogènes régulières avec positions automatiques; neuf calculs exécutés. w2 conserve3subdivisions et change seulement le déplacement transversal imposé dans quatre contrôles élastiques. w3 utilise9subdivisions et les chargements planes corrigés; neuf nouveaux calculs. Toutes les configurations et critères sont déclarés avant leurs calculs. Les22lectures natives des positions et masses passent. CPU1thread, aucun GPU.

Les66échantillons de champs sont finis, sans suppression d'élément, et passent l'identité coordonnées=données initiales+déplacement avec borne d'impression explicite. Les seuils physiques restent inchangés. Préservation vérifiée de20671fichiers antérieurs, soit65.019Go; aucune archive source rescannée.

## 2. Résultats d'un modèle officiel

[TYPE22](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type22_tsh_comp_starter_r.htm) définit des rapports d'épaisseur et positions de couches, et non une entrée libre de poids Gauss. Les lectures Starter confirment les centres réguliers3/9. [LAW25 Tsai-Wu](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm) distingue la direction transverse élastique des critères de plasticité du plan. La [théorie LAW25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/law25_composite_material_r.htm) montre une matrice de compliance3D avec couplage transverse de Poisson. Sa correspondance complète avec cette réponse TYPE22 n'est pas établie. Documentation et observations natives sont gardées séparément; aucun modèle NIST ou dommage connu n'est ajusté.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou affirmation historique. Le fichier A20 effectivement utilisé et sa carte LAW25 sont identifiés par SHA256 dans material_source_addendum.json. Cette carte est une référence élastique: résistances numériques très élevées et rupture inactive; elle n'est pas une identification de peau Boeing réelle. Les24racines/144ancres A25 restent disponibles, sans insertion d'une nouvelle liaison.

## 4. Hypothèses propres au modèle

Les3/9subdivisions traversent un même milieu homogène, avec même densité, orientation et volume. Elles n'affirment pas un empilement physique mesuré. Les masses nodales sont intégrées avec la densité source; leur changement par rapport au témoin métallique0,139g correspond à un autre matériau explicitement déclaré, sans compensation.

Rotations libres10rad/ms surXYZ pendant0,05ms, translation[-200,5,2]m/s, contrôleY à pas réduit. w1 impose en traction epsilon=[0,001;−0,00025;−0,00025]. La référence initiale ne contient que l'énergie de traction plane. w2/w3 imposent uz=0, avec ux=0,001x, uy=−0,00025y. La flexion utilise ux=−kxz−k²x³/6, uy=0, uz=kx²/2, k=0,001/mm. Le terme z² retiré par rapport à w1 est constant aux deux faces du maillage géométrique à une couche; sa suppression ne corrige donc pas la flexion interpolée dans l'épaisseur.

Références indépendantes conservées: traction0,5E11·epsilon²·volume et flexion0,5D11·k²·aire, D11=E11t³/[12(1−nu12nu21)]. Hypothèse de réponse plane précisée dans les configurations, sans extrapolation à la matrice3D générale. Le choix9subdivisions précède les nouveaux calculs: l'erreur de second moment par centres uniformes vaut théoriquement1/N², soit1/81<2%. Ce calcul est **un composant d'erreur de quadrature**, pas une prédiction suffisante de l'énergie HA8 totale. Aucun nombre intermédiaire n'est recherché pour rejoindre la référence.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
| w1 / FREE_ROTATION_X_N12 | 2.5396e-07 | réussi |
| w1 / FREE_ROTATION_Y_N12 | 2.5396e-07 | réussi |
| w1 / FREE_ROTATION_Z_N12 | 8.80005e-07 | réussi |
| w1 / FREE_TRANSLATION_N12 | 0 | réussi |
| w1 / FREE_ROTATION_Y_N12_HALF | 2.56439e-07 | réussi |
| w1 / MEMBRANE_N6 | 2.0373e-10 | **échoué**: independent_elastic_reference |
| w1 / MEMBRANE_N12 | 2.065e-10 | **échoué**: independent_elastic_reference |
| w1 / BENDING_N6 | 3.72689e-10 | **échoué**: independent_elastic_reference |
| w1 / BENDING_N12 | 2.34532e-10 | **échoué**: independent_elastic_reference |
| w2 / MEMBRANE_N6 | 1.782e-10 | réussi |
| w2 / MEMBRANE_N12 | 1.9647e-10 | réussi |
| w2 / BENDING_N6 | 3.74539e-10 | **échoué**: independent_elastic_reference |
| w2 / BENDING_N12 | 2.3629e-10 | **échoué**: independent_elastic_reference |
| w3 / FREE_ROTATION_X_N12 | 1.83558e-07 | réussi |
| w3 / FREE_ROTATION_Y_N12 | 1.83558e-07 | réussi |
| w3 / FREE_ROTATION_Z_N12 | 6.2396e-07 | réussi |
| w3 / FREE_TRANSLATION_N12 | 0 | réussi |
| w3 / FREE_ROTATION_Y_N12_HALF | 1.8252e-07 | réussi |
| w3 / MEMBRANE_N6 | 1.782e-10 | réussi |
| w3 / MEMBRANE_N12 | 1.9647e-10 | réussi |
| w3 / BENDING_N6 | 2.915e-10 | **échoué**: independent_elastic_reference |
| w3 / BENDING_N12 | 1.79837e-10 | **échoué**: independent_elastic_reference |

| Contrôle élastique | Energie native(J) | Référence plane(J) | Ecart |
|---|---:|---:|---:|
| w1 / MEMBRANE_N6 | 0.0005649465 | 0.00055 | 2.71755% |
| w1 / MEMBRANE_N12 | 0.0005649465 | 0.00055 | 2.71755% |
| w1 / BENDING_N6 | 1.137976e-05 | 1.222222222e-05 | -6.89287% |
| w1 / BENDING_N12 | 1.137984e-05 | 1.222222222e-05 | -6.89222% |
| w2 / MEMBRANE_N6 | 0.0005494129 | 0.00055 | -0.106745% |
| w2 / MEMBRANE_N12 | 0.0005494129 | 0.00055 | -0.106745% |
| w2 / BENDING_N6 | 1.137976e-05 | 1.222222222e-05 | -6.89287% |
| w2 / BENDING_N12 | 1.137984e-05 | 1.222222222e-05 | -6.89222% |
| w3 / MEMBRANE_N6 | 0.0005494129 | 0.00055 | -0.106745% |
| w3 / MEMBRANE_N12 | 0.0005494129 | 0.00055 | -0.106745% |
| w3 / BENDING_N6 | 1.264333e-05 | 1.222222222e-05 | 3.44543% |
| w3 / BENDING_N12 | 1.264341e-05 | 1.222222222e-05 | 3.44608% |

La différence de traction w1−w2 vaut1.55336e-05J, proche de0,5E33·epsilon_z²·volume=1.5625e-05J. Les contraintes natives globales w1 sont proches de[22;0;−2,5]MPa; w2/w3 montrent la suppression de sigma_z. Cela étaye le diagnostic de chargement transverse, sans établir toute une matrice constitutive. Les anciens contrôles w1 et leurs quatre échecs de référence ne sont pas réécrits.

La flexion3subdivisions reste environ6,89% sous la référence; avec9subdivisions elle est environ3,45% au-dessus. Les deux choix échouent au seuil2%+1e−7J. L'écart spatialN6/N12 est faible et passe5%, alors que la sensibilité3/9dans l'épaisseur reste importante. Une convergence spatiale faible ne supprime pas le défaut de référence. Le pas réduitY w3 vaut0.5fois l'initial, avec différence de moment3.056541243e-13kg·m²/s et d'énergie9.5457625e-09J: critères temporels réussis. Aucun terme RKE inventé ou retrait du bilan natif.

## 6. Contradictions et informations manquantes

La peau TYPE22 ne satisfait pas encore la rigidité de flexion de référence. Les effets de cinématique interpolée, intégration volumique et traitement constitutif doivent être séparés. L'interprétation globale de la compliance3D officielle et celle observée dans ce témoin restent à réconcilier; la traction plane réussie ne permet pas d'annoncer une équivalence3D générale. La résistance et la rupture réelles, les liaisons courbes, le cœur, la façade, la gravité, l'intérieur porteur et les contacts de fragments restent ouverts. A26 métal reste qualifié seulement dans son domaine de plaque isolée. Aucun nouvel impact entier n'a été lancé; le meilleur entier reste A20=20ms, avec échecs locaux A21 préservés. Vidéo10secondes physiques incomplète.

AIRCRAFT-A28 : reprendre composite_qualification_review.json et constitutive_observation.json. A26 métal HA8 passe9contrôles isolés; A27 TYPE22 LAW25 conserve masse, énergie, quantité de mouvement et moment physique libresXYZ, mais sa flexion ne passe pas la référence indépendante. Ne pas sélectionner un nombre de couches pour croiser artificiellement la référence. Les3/9couches sont des subdivisions numériques du même matériau homogène; le passageN6/N12 ne résout pas l’écart. Comparer maintenant contraintes et moments de flexion natifs à la cinématique réellement interpolée et aux tenseurs constitutifs explicites, puis tester une alternative volumique orthotrope si nécessaire, sans modifier les paramètres pour obtenir le dommage connu. La matrice3D couplée de la théorie LAW25 et la réponse observée TYPE22 restent à réconcilier; les contrôles planes réussis ne qualifient pas la réponse3D générale ou la rupture historique. Ensuite seulement vérifier le cœur/sandwich et les24racines/144ancres courbes A25. Aucun montage entier d’une liaison non qualifiée, aucune prolongation A21. Objectif vidéo3D10secondes physiques incomplet, meilleur entier A20=20ms. Nouveau départ intact après bilans et mesure du coût. Publication A26+A27 après intégrité; conserver tous les échecs, aucune compensation de masse ou RKE.
