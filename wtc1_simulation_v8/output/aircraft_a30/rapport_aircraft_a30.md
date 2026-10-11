# AIRCRAFT-A30 — sandwich volumique conformal

**Neuf nouveaux calculs natifs complets** sur deux peaux et leur cœur. Périmètre des invariants libres et champs élastiques imposés: réussi. La transmission dans un intérieur libre, les attaches courbes et l'impact entier restent à vérifier.

## 1. Faits directement observés ou transcrits

Graine1102055, aucun tirage. Géométrie10×10mm; peau inférieurez=−4,5..−4mm, cœur−4..4mm, peau supérieure4..4,5mm. Volumes50+800+50mm³, densités0,00183et0,000048g/mm³, masse0,2214g. Les maillages6/12dans le plan comprennent4éléments par peau et12dans le cœur. Les facesz±4partagent les mêmes nœuds; aucune coordonnée dupliquée, masse d'interface, rotation indépendante ou déport rigide ajouté. Les anciennes entrées Spot5et l'avion entier restent conservés.

Les peaux utilisent la branche LAW12/TYPE6 Isolid18A29, avec axesY,−X,Z. Le cœur garde sa carte LAW28/28source et ses six courbes plateau; TYPE6 Isolid14, axesXYZ. Avant chaque Engine, le Starter confirme repères et formulations effectifs. Les27échantillons natifs contrôlent finitude, identité géométrique avec borne d'impression et absence de suppression. Les cartes effectives et les faces partagées sont vérifiées séparément. Conservation de22498fichiers antérieurs, 65.804Go. Aucun ancien calcul relancé. Publication A28+A29effectivement confirmée avant cette déclaration.

## 2. Résultats d'un modèle officiel

[LAW12](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law12_3d_comp_starter_r.htm) définit l'orthotropie3D des peaux; sa conformité numérique locale a été vérifiée dans A29. [LAW28](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm) décrit un cœur orthotrope à réponses directionnelles. Les contrôles de matériau A20en cache sont réutilisés, avec leurs limites et leurs anciens critères échoués. Aucune forme de dommage NIST ou connue n'est utilisée comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse de vidéo ou affirmation historique. Les propriétés de référence du cœur HRH10et leurs paramètres non mesurés restent celles documentées dans A20. Aucune identification du matériau d'AA11ou de son décollement n'est annoncée. L'inventaire A25des24racines/144ancres est conservé; aucune racine fictive n'est insérée.

## 4. Hypothèses propres au modèle

La liaison peau/cœur par faces communes est une **nouvelle hypothèse de collage parfait**, distincte des anciennes interfaces Spot5. Elle ne donne pas de résistance de décollement. Les modules,densitéetnu12source des peaux sont conservés; nu23=nu31=0,25restent les hypothèses transverses explicites d'A29. Les seuils géants de LAW12maintiennent les témoins élastiques, sans capacité historique de rupture. Le cœur garde E=[1,1,138]MPa et G=[0,5,24,41]MPa; ses faibles propriétés dans le plan et ses seuils de rupture restent hypothétiques.

La rotation libre commence avec omega1rad/ms sur0,05ms: amplitude déclarée pour garder le cœur faible dans un régime élastique, différente des témoins de peau A29à10rad/ms. La translation−200,5,2m/s teste l'invariance. Les champs élastiques prescrivent tous les nœuds sur0,1ms: extensionepsilon_x=0,001, epsilon_y=epsilon_z=0; flexion cylindriqueκ=0,0001/mm, extension transverse contrainte. Cette courbure fixe une déformation de peau maximale4,5e−4, choisie avant calcul pour rester dans le même ordre élastique. Ces champs ne sont pas un test d'intérieur libre ou de flexion plane libre.

Référence d'extension:0,5epsilon_x²ΣCxx·volume. Référence de flexion:0,5κ²·aire·Σ[Cxx·intégrale(z²dz)]. Cdes peaux provient de la compliance A29, Cdu cœur est diagonal. Chaque région garde son volume,densitéetposition réels. Le tenseur d'inertie continu est la somme analytique de ses prismes avec déport physique; masse nodale issue des volumes, tensor discret séparé. Aucun module n'est ajusté à une sortie. Les seuils énergétiques/élastiques2%+1e−7J, invariants libres0,2%, inertie continue2%, raffinement spatial5% et rapport de pas<0,6sont conservés.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique maximal(J) | Résultat |
|---|---:|---|
| FREE_ROTATION_X_N12 | 5.7326e-10 | réussi |
| FREE_ROTATION_Y_N12 | 5.1233e-10 | réussi |
| FREE_ROTATION_Z_N12 | 5.29565e-10 | réussi |
| FREE_TRANSLATION_N12 | 0 | réussi |
| FREE_ROTATION_Y_N12_HALF | 5.09932e-10 | réussi |
| AFFINE_EXTENSION_N6 | 9.3352e-10 | réussi |
| AFFINE_EXTENSION_N12 | 8.61193e-10 | réussi |
| CONSTRAINED_BENDING_N6 | 1.3882804e-08 | réussi |
| CONSTRAINED_BENDING_N12 | 8.7548194e-09 | réussi |

9ensembles individuels sur9et9bilans natifs sur9passent. Les RKE natives restent séparées dans tous les bilans; aucun terme inventé. Pas médian demi-pas/initial=0.500000167; différence de moment cinétique=5.35168164e-14kg·m²/s, énergie=1.43365969e-10J. Les références et écarts6/12sont conservés dans sandwich_qualification_review.json. Le travail plastique natif par pièce est enregistré comme diagnostic, sans seuil ajouté après exécution.

## 6. Contradictions et informations manquantes

Les essais vérifient les invariants physiques du montage libre et sa réponse à des champs imposés. Ils ne démontrent pas le transfert des charges par des nœuds intérieurs libres: cette question est l'étape suivante. La liaison parfaite ignore le décollement; coefficients transverses, faible plan du cœur, rupture et assemblage réel restent à identifier. La réussite du témoin n'autorise pas encore un remplacement dans l'avion entier. Les échecs antérieurs restent conservés. Gravité, façade, intérieur porteur et contacts de fragments restent ouverts. Meilleur entierA20=20ms, vidéo10secondes physiques incomplète.

AIRCRAFT-A31 : les champs imposés A30 et invariants libres ne qualifient pas encore le transfert par un intérieur libre. Si le périmètre A30 passe, imposer seulement les faces/prises sur le même sandwich conformal et comparer réaction, travail et déplacements internes à une référence3D indépendante hétérogène, construite à partir des tenseurs et volumes déclarés. Au minimum cisaillementsXZ/YZ et traction/pression normales, amplitudes restant élastiques et raffinements. Conserver les nouvelles hypothèses LAW12 et liaison parfaite, tous les défauts A21–A30, sans correction RKE ou de masse. Puis mapper24racines/144ancres courbes A25avec leurs orientations et budget physique réels; aucune racine plate fictive substituée. Nouveau départ entier intact après bilans, critères locaux et estimation de coût. Meilleur entier20ms; objectif vidéo3D10secondes physiques incomplet. Publication suivante après A30+A31 vérifiées, autorisation déjà donnée. Aucun dommage connu comme cible.
