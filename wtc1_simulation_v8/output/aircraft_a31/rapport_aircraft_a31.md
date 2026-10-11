# AIRCRAFT-A31 — transmission dans un sandwich à intérieur libre

Neuf nouveaux calculs natifs complets. Périmètre élastique aux faces, intérieur libre et raffinements: réussi. Les essais implicites séparés échouent sur le binaire installé. L'impact entier et sa vidéo de dix secondes restent à réaliser.

## 1. Faits directement observés ou transcrits

Graine1102056, aucun tirage. Géométrie et matériaux A30 conservés:10×10mm, peaux0,5mm, cœur8mm; volumes50+800+50mm³, densités0,00183et0,000048g/mm³, masse0,2214g. Maillages6/12dans le plan, quatre éléments dans chaque peau et douze dans le cœur. Faces internes partagées par identité des nœuds, sans interface massive ou déport rigide. Seules les faces extérieuresz=−4,5et4,5mm contraignentXYZ; tous les autres nœuds restent libres. Le contrôle des cartes confirme LAW12et LAW28, formulations et repères natifs avant Engine. 27échantillons natifs: finitude, coordonnées/déplacements avec borne d'impression et absence de suppression.

Conservation vérifiée de22768fichiers antérieurs (66.385Go). Aucun ancien calcul relancé. Une erreur de métadonnées avant Starter, puis une erreur de sélection des titres de pièces après le premier calcul, sont conservées avec leurs versions originales. Les reprises complètent les métadonnées puis relisent le calcul déjà terminé; ses entrées et sorties natives ne sont pas réécrites.

## 2. Résultats d'un modèle officiel

[TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) décrit REAC comme des forces. Dans ce binaire et ces calculs, les sorties brutes vérifient au contraire l'impulsion: sommeQ−Qinitial=variation de quantité de mouvement. L'interprétation alternative par intégration temporelle échoue. Les deux comparaisons et seuils déclarés sont gardés; la réaction est alors dQ/dt, avec retrait explicite de l'inertie des seuls nœuds prescrits pour la comparaison statique. Le travail nodal est comparé au travail externe natif. Le moment cinétique issu des impulsions est un diagnostic séparé, sans critère ajouté après calcul.

La documentation [Newmark](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_2_engine_r.htm) et [solveur implicite](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_solver_engine_r.htm) définit les options des sondes séparées. Leur présence dans la documentation n'établit pas leur disponibilité dans l'exécutable: les nouvelles tentatives PCGet MUMPS échouent effectivement.

## 3. Affirmations provenant des archives locales

Aucune nouvelle analyse vidéo ou affirmation historique. Sources cœur/peaux réutilisées avec les lacunes A20/A29. Aucune identification d'un matériau, assemblage ou décollement historique d'AA11annoncée. Les24racines/144ancres courbes A25sont mappées sur les faces physiques candidates: épaisseurs2,54mm du corps et0,5mm des peaux, points proches, coordonnées barycentriques et repères orthonormés directs. Les distances minimales sont2.44897..2.72694mm. Tous les candidats sont gardés. Cette sélection géométrique ne définit ni empreinte, ni volume, ni masse d'attache; le budget de la prise plate n'est pas reporté. Aucun dommage connu ou résultat NIST comme cible.

Une préparation en cache transforme les1296quads de peau des216facettes réelles en volumes0,5mm, avec faces du cœur intactes et repères matériauxW,−L,nissus de l'orientation source90°. Masse de peau33.9407326kg, identique au budget source à1e−8relatif; tous les jacobiens de Gauss positifs, erreur de plan moyen maximal2.27373675e-13mm. Centre de masse et tenseurs physiques sont archivés. Les IDs de facettes ne sont pas contigus: une erreur de recherche par position, sans exécution native, est conservée et reprise par dictionnaire d'IDoriginal. Aucun ancien fichier modifié. Ce maillage candidat n'est pas inséré dans l'avion ni qualifié mécaniquement par cette préparation géométrique.

## 4. Hypothèses propres au modèle

LAW12des peaux garde E=[22000,22000,10000]MPa, G=[4000,4000,4000]MPa; nu23=nu31=0,25restent des hypothèses transverses explicites. Les seuils géants maintiennent ce témoin élastique, sans qualifier une rupture historique. Le cœur LAW28source garde E=[1,1,138]et G=[0,5,24,41]MPa, plateaux et seuils précédents; paramètres dans le plan et rupture encore non mesurés. Le collage parfait est une hypothèse A30distincte des anciennes interfaces Spot5.

Rampe0,5ms, déplacement0,009mm, s=3u²−2u³; face inférieure fixe, supérieure mobile dans une seule direction. CisaillementsXZ/YZ, traction et compression normales. Durée et amplitude déclarées avant résultats pour un régime élastique et une faible énergie cinétique finale, adequation contrôlée. Référence3D indépendante hétérogène: hexaèdres8nœuds,2×2×2Gauss, tenseurs des sources, géométrie et conditions aux faces identiques. Matrice symétrique, jacobiens positifs, équilibre intérieur, travail virtuel et somme des énergies par pièce contrôlés. Résolution CG préconditionnée, tolérance1e−10relative+1e−11N, sans opérateur natif ou ajustement de module.

Critères avant exécution: bilans, énergie et réactions2%avec bornes absolues; déplacement intérieur2%de l'amplitude+2e−6mm, KEfinale1%de la référence+1e−7J; travail plastique<1e−7J; convergence spatiale5%, temporelle0,2%, rapport de pas<0,6. Tous les canaux natifs, dont RKEet HE, restent séparés dans le bilan complet. Aucun terme artificiel ajouté.

## 5. Résultats dérivés

| Contrôle | Résidu énergétique max(J) | Erreur réaction tardive max(N) | Erreur déplacement intérieur max(mm) | Résultat |
|---|---:|---:|---:|---|
| SHEAR_XZ_N6 | 9.28e-12 | 0.031705938 | 0.00012800206 | réussi |
| SHEAR_XZ_N12 | 8.8e-12 | 0.0264678 | 6.5316205e-05 | réussi |
| SHEAR_YZ_N6 | 6.70245e-12 | 0.024839884 | 0.00010528234 | réussi |
| SHEAR_YZ_N12 | 1.57e-12 | 0.022988517 | 5.5106923e-05 | réussi |
| NORMAL_TENSION_N6 | 1.101e-11 | 0.030463258 | 6.7150051e-07 | réussi |
| NORMAL_TENSION_N12 | 1.4773e-11 | 0.029777406 | 4.0940245e-07 | réussi |
| NORMAL_COMPRESSION_N6 | 1.2666e-11 | 0.012796605 | 6.7412275e-07 | réussi |
| NORMAL_COMPRESSION_N12 | 1.1581e-11 | 0.01215801 | 4.1172176e-07 | réussi |
| SHEAR_XZ_N12_HALF | 9.32e-12 | 0.026316128 | 6.5315205e-05 | réussi |

9/9ensembles individuels et9/9bilans complets passent. Les critères originaux des essais grossiers restent gardés séparément. Qualification fine: réussi.

| Mode | Variation énergétique native6→12 | Variation référence indépendante6→12 | Raffinement |
|---|---:|---:|---|
| SHEAR_XZ | 1.59393% | 1.6655% | réussi |
| SHEAR_YZ | 1.7723% | 1.82142% | réussi |
| NORMAL_TENSION | 0.000229438% | 0.000765722% | réussi |
| NORMAL_COMPRESSION | 0.00345313% | 0.000765722% | réussi |

Rapport de pas demi/initial=0.499999833; écart maximal d'énergie=1.0090018e-11J et réaction=0.000221172122N. Valeurs, historiques SI et paramètres effectivement lus sont archivés.

Un addendum relit les27canaux plastiques A30en cache: maximum du travail plastique total=0J. Le diagnostic initial A30avait des dictionnaires vides parce qu'il cherchait le nom de groupe au lieu des titres réels; sa qualification n'avait pas de critère plastique. L'addendum fournit l'observation manquante sans modifier le rapport ou les fichiers A30scellés.

Quatre sondes implicites nouvelles, sur un cube métallique1mm³ à masse0,00278g et intérieur libre: les deux premières s'arrêtent lors de la lecture d'un enregistrement NONLIN de80caractères. Le code amont conservé montre une chaîne TITLEde72caractères, sans preuve d'identité avec ce binaire. La branche distincte à nombres identiques en format compact franchit la lecture, puis les deux modes terminent avec **MUMPSrequired** (8684et2404). Aucun calcul implicite n'est réussi. Aucun composant installé ou exécutable modifié.

## 6. Contradictions et informations manquantes

La transmission élastique dans ce témoin, même réussie, ne qualifie ni les prises courbes réelles, ni la plasticité du nez à grande vitesse, ni le décollement ou la rupture. Les contradictions de libellé REACet les erreurs de préparation/lecture restent documentées. Échecs A21–A30conservés. Façade, gravité, intérieur porteur, contacts de fragments et propriétés historiques restent ouverts.

Le calcul entier A20de20ms a coûté1191,42s; extrapolation linéaire indicative10s≈6,90jours, sans garantie pour une autre discrétisation ou un contact tardif. La voie implicite du binaire actuel n'est pas disponible; une formulation ou résolution spatiale efficace doit conserver masse, tenseur physique et réponse mécanique vérifiée. Meilleur entier20ms, objectif vidéo3D10secondes physiques incomplet.

AIRCRAFT-A32 : le périmètre élastique du sandwich à intérieur libre passe; préparer les24racines/144ancres courbes réellement inventoriées dans A25, leurs repères, prises et budgets physiques avant un contrôle natif représentatif. Le coût de10secondes doit être évalué sur la discrétisation réelle; tester une formulation efficace à masse physique inchangée avec référence indépendante si nécessaire. Le binaire installé échoue aux deux sondes implicites avec MUMPSrequired; aucune installation ni modification du solveur effectuée. Les cartes LAW12, coefficients transverses et collage parfait restent des hypothèses explicites; résistances, décollement et rupture historiques non identifiés. Aucun faux ajout de RKE, correction de densité ou ajustement aux dégâts connus. Nouveau départ entier après critères locaux, bilans et estimation du coût. Meilleur entierA20=20ms; objectif vidéo3D10secondes physiques incomplet. Publication A30+A31 après vérification, déjà autorisée; cadence suivante A32+A33.
