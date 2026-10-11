# AIRCRAFT-A28 — déformations reconstruites et cohérence du cisaillement

**22 nouveaux calculs natifs complets** et lecture de six historiques A27 conservés. La formule ASQBI documentée prédit l'écart de flexion sans ajuster le matériau. Les alternatives testées ne qualifient pas la peau: flexion et cisaillement transverse restent en échec. Aucun nouveau calcul entier ou vidéo10secondes.

## 1. Faits directement observés ou transcrits

Graine1102053, aucun tirage. Plaque10×10×0,5mm, volume50mm³, masse0,0915g. Carte LAW25/4 source inchangée:rho0,00183g/mm³, E11=E22=22000MPa, nu12=0,25, E33=10000MPa, G12=G23=G31=4000MPa. Orientation90° et9subdivisions homogènes régulières. Aucun ajout de masse, RKE ou échelle temporelle. Les anciens solveurs ne sont pas relancés.

w0: sept contrôles HA8 avec /DEF_SOLID Icpre1. Le Starter lit1au défaut global mais **3dans la pièce TYPE22**; le changement n'a pas été appliqué dans la pièce. w1: quinze contrôles HSEPH TYPE22 Isolid15, mêmes matériaux et géométrie, amortissement de stabilisation demandé et lu1e−20. Tous les Starters et Engines terminent normalement sans avertissement. Des corrections de syntaxe/réservation de colonne ont précédé toute exécution et leurs versions sont conservées.

Les66échantillons de champs passent finitude, identités géométriques avec borne d'impression et absence de suppression. Les propriétés natives et positions de couches sont vérifiées. Préservation de21312fichiers antérieurs, 65.216Go. Le dépôt OpenRadioss n'a pas fourni son code courant via l'accès essayé (réponse404); une inspection Git restée en attente est arrêtée. Aucun code source ou logiciel de solveur n'est modifié, aucune compilation ni équivalence source/binaire annoncée.

## 2. Résultats d'un modèle officiel

La [formulation ASQBI](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_assumed_strain_rate.htm) ajoute des termes transverses avec nu/(1−nu) dans les modes de flexion. Ils évitent des verrouillages dans les éléments; ils ne sont pas une mesure de déformation physique indépendante. [TYPE22](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type22_tsh_comp_starter_r.htm) propose HA8 et HSEPH, le second avec stabilisation physique. Les [valeurs globales /DEF_SOLID](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/def_solid_starter_r.htm) peuvent être écrasées: seule la lecture effective de pièce prouve leur application. Ces définitions guident les essais; aucun dommage NIST ou historique n'est ciblé.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation historique ou analyse de vidéo. La carte élastique et le fichier A20 effectivement utilisés sont épinglés par SHA256. Ce matériau est un témoin de référence, pas une identification de rupture de Boeing réel. Inventaire A25 des24racines/144ancres conservé, sans insertion dans l'avion entier.

## 4. Hypothèses propres au modèle

Pour la flexion cylindrique en xz, la composante reconstruite est epsilon_z=−[nu/(1−nu)]epsilon_x. Le bloc constitutif TYPE22 déclaré sépare le plan de E33. Son application donne une rigidité supplémentaire E33[nu/(1−nu)]²=1111,111111MPa, soit4,734848485% de la rigidité plane23466,666667MPa. Les centres de subdivisions intègrent z²; leur déficit de second moment est1/N². Ces coefficients sont issus des entrées et de la formule publiée, sans estimation sur les valeurs natives. Les amplitudes suivent le déplacement effectivement prescrit et l'instant natif.

La référence de matrice3D couplée publiée pour LAW25 reste distincte du bloc observé dans TYPE22. Les neuf sous-couches sont une quadrature d'un milieu homogène, pas un empilement historique. La référence HSEPH utilise IE+HE, la stabilisation physique étant un terme élastique; les canaux natifs restent séparés et le bilan complet inclut tous les termes sans correction. Ici HE vaut zéro dans les valeurs examinées. Les seuils2%+1e−7J élastiques et du bilan complet,0,2% pour les invariants libres, ainsi que les seuils de masse/inertie et raffinements A26 sont conservés.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
| w0 / PATCH_NORMAL_X_N12 | 1.6884e-10 | réussi |
| w0 / PATCH_NORMAL_Y_N12 | 1.6884e-10 | réussi |
| w0 / PATCH_NORMAL_Z_N12 | 1.0212564e-10 | réussi |
| w0 / MEMBRANE_N6 | 1.782e-10 | réussi |
| w0 / MEMBRANE_N12 | 1.9647e-10 | réussi |
| w0 / BENDING_N6 | 2.915e-10 | **échoué**: independent_elastic_reference |
| w0 / BENDING_N12 | 1.79837e-10 | **échoué**: independent_elastic_reference |
| w1 / FREE_ROTATION_X_N12 | 2.37097e-07 | réussi |
| w1 / FREE_ROTATION_Y_N12 | 2.37097e-07 | réussi |
| w1 / FREE_ROTATION_Z_N12 | 9.40219e-07 | réussi |
| w1 / FREE_TRANSLATION_N12 | 0 | réussi |
| w1 / FREE_ROTATION_Y_N12_HALF | 2.54155e-07 | réussi |
| w1 / MEMBRANE_N6 | 1.782e-10 | réussi |
| w1 / MEMBRANE_N12 | 1.9647e-10 | réussi |
| w1 / BENDING_N6 | 4.54539e-10 | **échoué**: independent_elastic_reference |
| w1 / BENDING_N12 | 2.8737e-10 | **échoué**: independent_elastic_reference |
| w1 / PATCH_NORMAL_X_N12 | 1.6884e-10 | réussi |
| w1 / PATCH_NORMAL_Y_N12 | 1.6884e-10 | réussi |
| w1 / PATCH_NORMAL_Z_N12 | 1.0212564e-10 | réussi |
| w1 / PATCH_SHEAR_XY_N12 | 1.0127e-11 | réussi |
| w1 / PATCH_SHEAR_YZ_N12 | 1.3880999e-05 | **échoué**: native_full_balance, independent_elastic_reference |
| w1 / PATCH_SHEAR_XZ_N12 | 1.3880999e-05 | **échoué**: native_full_balance, independent_elastic_reference |

| Historique A27 | IE finale native(J) | Prédiction ASQBI(J) | Ecart maximal sur tout l'historique(J) |
|---|---:|---:|---:|
| w1 / N6 / 3subdivisions | 1.137976e-05 | 1.13721413e-05 | 7.61869951e-09 |
| w1 / N12 / 3subdivisions | 1.137984e-05 | 1.13721413e-05 | 7.69869951e-09 |
| w2 / N6 / 3subdivisions | 1.137976e-05 | 1.13721413e-05 | 7.61869951e-09 |
| w2 / N12 / 3subdivisions | 1.137984e-05 | 1.13721413e-05 | 7.69869951e-09 |
| w3 / N6 / 9subdivisions | 1.264333e-05 | 1.26357126e-05 | 7.6174439e-09 |
| w3 / N12 / 9subdivisions | 1.264341e-05 | 1.26357126e-05 | 7.6974439e-09 |

Les six prédictions passent le seuil initial2%+1e−7J; écart maximal d'environ7,7e−9J. Cette concordance explique une composante numérique de l'écart; les anciens critères de flexion demeurent échoués. Le changement de défaut global w0 n'est pas une perturbation effective de cette composante.

HSEPH conserve les mouvements libres, la traction et les trois modes affines normaux. La flexion demeure environ3,45% au-dessus de la référence et échoue. Les cisaillementsXZ/YZ échouent **également au bilan natif complet**: résidu maximal1,388099897e−5J. IE finale6,940505e−5J est proche du carré de Ashear5/6 multiplié par la référence G; le travail suit un facteur simple. Ce constat ne justifie aucun ajout d'énergie. Le facteur5/6 venait d'une hypothèse de peau/coque; son emploi dans une représentation volumique doit être vérifié séparément.

Le raffinement temporelY vaut0.5fois le pas initial et passe ses critères; les écarts spatiauxN6/N12 passent5%. Ces réussites ne valident pas les critères de flexion ou de cisaillement qui échouent. 20bilans sur22passent, 16ensembles individuels sur22passent.

## 6. Contradictions et informations manquantes

L'hypothèse d'un mécanisme numérique transverse est étayée par la formule et les six historiques, sans preuve de toute la chaîne causale A21. Le réglage Icpre global n'a pas modifié la pièce: ses résultats ne peuvent falsifier les termes ASQBI. La variante HSEPH conserve l'écart de flexion et présente un défaut énergétique transverse; elle n'est pas prête pour le montage entier. Il faut une formulation volumique sans correction de cisaillement héritée et un tenseur3D explicite, vérifiée avant transfert. Aucun matériau n'est ajusté pour réussir un dommage connu. Rupture historique, attaches, cœur, façade, gravité, intérieur porteur et fragments restent ouverts. Meilleur calcul entier A20=20ms; vidéo10secondes physiques incomplète.

AIRCRAFT-A29 : reprendre assumed_strain_diagnostic.json, shear_balance_diagnostic.json et composite_qualification_review.json. Le terme transverse ASQBI E33*(nu/(1-nu))² prédit les6historiques de flexion A27 sans ajustement; il explique une sur-rigidité4,73485% superposée à la quadrature. Le /DEF_SOLID Icpre1 A28 est écrasé par Icpre3 dans la pièce TYPE22: ne pas l’interpréter comme une suppression effective des termes de Poisson. HSEPH source préserve les mouvements libres et la membrane mais échoue en flexion et au bilan du cisaillement transverse avec Ashear5/6; aucun correctif comptable. Tester une branche volumique orthotrope TYPE6 Isolid18 avec même carte LAW25, même volume/densité, orientation90° explicite, tenseur3D documenté et4couches géométriques dans l’épaisseur. Elle représente une nouvelle hypothèse constitutive3D, pas une équivalence automatique de la peau TYPE22. Vérifier d’abord les6modes affines, puis mouvements libres, flexion plane avec contraction transverse issue du tenseur indépendant, bilans et raffinements. Si nécessaire tester une loi3D orthotrope explicitement définie, sans caler propriétés ou densité. Puis cœur/sandwich et24racines/144ancres courbes A25. Nouveau départ entier intact uniquement après bilans et estimation du coût; aucun état A21 prolongé. Objectif vidéo3D10secondes physiques incomplet, meilleur entier20ms. Publication suivante A28+A29 après intégrité; tous les échecs et bilans natifs conservés, aucun dommage connu comme cible.
