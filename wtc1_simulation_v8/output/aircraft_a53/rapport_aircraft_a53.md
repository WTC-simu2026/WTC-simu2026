# AIRCRAFT-A53 — vrai bloc fautif identifié et écriture de graphe incorrecte observée

Le bloc arrêté appartient à la peau triangulaire du fuselage. Une mesure séparée du moteur inchangé montre une écriture dans le mauvais tableau de connexions, suivie d’une augmentation du compteur de la ligne correcte. Un correctif limité est préparé ; il n’est ni appliqué ni compilé. A53 termine le diagnostic et prépare la décision suivante, sans prolonger l’impact.

## 1. Faits directement observés ou transcrits

Quatre Engine nouveaux, aucun Starter, un CPU chacun, limite180s, aucun GPU. Les durées internes des observations sont respectivement8,500s,8,134s,7,154s et7,786s ; les journaux conservent séparément les durées des lanceurs. Les trois premières exécutions terminent code3 au signal natif ; le lanceur d’observation peut terminer0 sans que le moteur réussisse. La référence non regroupée termine code0/NORMAL mais conserve ses erreurs mécaniques connues.

La première capture observe263ASSEM_C4 et1579ASSEMC. Son dernier bloc de quadrangles ne correspond toujours pas au bloc fautif ; tentative conservée et contexte rejeté. La capture suivante ajouteASSEM_C3 : un appel, bloc courantNEL128, connectivitéIXTG de largeur6. Chaque couple NI/NJ correspond à son élément courant. Les128éléments193..320 correspondent exactement à SH3N/1,fuselage_skin, propriété1, matériau1/LAW2 ; leurs89nœuds ont un écart de coordonnées nul. Premier élément193 :[97,121,122]. La faute ASSEMC_KIJ+0x664 concerne24pairesNDOF[6,6] et144lignes absentes, IKPAT1. Premier couple interne[42833,42834] : labels[97,121]. Le nœud97 est principal de septRBE2 ;121n’a aucun rôleRBE2 déclaré. La vérification ne dépend plus des huit peaux du contexte périmé A52.

Un contrôle d’entréeREORDER_A capture zéro appel, résultat inconclusif conservé : une optimisation/inlining peut expliquer l’absence, mais elle n’est pas prouvée uniquement par cette capture. Le défaut est ensuite observé par surveillance matérielle de trois adresses de données dans notre propre processus fils, sur l’entrée originale A49 non regroupée.

Au début IND_KINE_K :NNMAX24,NKMAX119,NKINE11064,INK9888. Le nœud d’entrée48151 correspond à l’indice42826, ligne9891>INK, compteur3 ; colonnes correctes[42827,42828,42829]. L’adresse correcte est0x616470c6d7c0 ; le calcul avec le pas ordinaire24 donne0x616470c6d4c8. Une écriture à l’adresse incorrecte ajoute42827(label48154), déjà présent dans la ligne correcte. L’instruction suivante est à l’offset0xbfe7be. Puis le compteur de la ligne correcte augmente3→4 à0xbfe7c2, alors que sa quatrième colonne reste0. Les douze événements bornés montrent le compteur monter jusqu’à14, une écriture dans la colonne incorrecte et aucune dans la colonne correcte observée. Aucun total global de mauvaises écritures n’est inféré de ces douze événements.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel exécuté. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, binaireA44 intact. Les symboles et signatures sont vérifiés dans cette source et les adresses lues dans le processus exécuté. Les observateurs changent les registres matériels de débogage, aucune instruction, tableau mécanique, donnée de reprise ou binaire.

La source distingue deux rangements. Dans IND_KINE_K, les lignes ordinaires utilisent ICOK avec le pasNNMAX ; les principales utilisent ICOKM avec le pasNKMAX et l’indice row-INK. Dans DIM_KINE_T, les principales précèdent les ordinaires. Le tableau ordinaire de dimensionnement garde les indices globaux avec padding, selon l’allocation existante ; il ne faut pas y appliquer row-INK. Les branchesRBE2/RBE3 choisissent déjà ces tableaux, alors que les branchesTYPE2 emploient directement ICOK. Les écritures mesurées confirment un cas concret de mauvais rangement.

- [Assemblage triangulaire](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/assem_c3.F)
- [Dimensionnement et construction du graphe](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/ind_glob_k.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo, photographie ou source officielle inspectée. Les archives restent en lecture seule. Les dégâts historiques et les résultatsNIST ne servent pas de cible d’ajustement.

## 4. Hypothèses propres au modèle

Graine1102078 et configurations JSON fixées avant leurs mesures natives, aucun tirage dans ces quatre mesures. Les huit contrôles indépendants Python de rangement utilisent séparément cette graine pour des graphes synthétiques : ils vérifient des ensembles de voisins, aucune probabilité de l’événement réel. Les hypothèses physiques héritées restent celles des entrées ; aucune masse, inertie, loi de matériau, charge ou liaison mécanique compensatoire n’est ajoutée.

Le correctif proposé touche un fichier ind_glob_k.F : cinq ajouts, une lecture et un test d’appartenance dans chacun des deux blocs TYPE2, avec trois fonctions auxiliaires de sélection du rangement. Le dimensionnement garde son padding ; la construction utilise row-INK pour les principales. Les anciennes routines hors de ces deux blocs et déclarations restent identiques. Le contrôle statique vérifie la portée de la différence et la limite72colonnes des nouvelles lignes ; il ne compile pas le Fortran.

## 5. Résultats dérivés

L’attribution aux128triangles/89nœuds passe la connectivité et les coordonnées natives exactes. La surveillance prouve une écriture de colonne dans le mauvais tableau et une inflation du compteur correct pour un voisin déjà présent. C’est un défaut de stockage observé, sans preuve que sa correction résoudra toutes les15erreurs et49370messages de la référence ni l’ensemble des arrêts de variantes.

Les huit contrôles dictionnaire/ensembles passent, y compris les domaines sans principales ou sans ordinaires. Le cas natif observé montre compteur attendu3 contre4 après l’ajout erroné. Les sources complètes proposées et le patch AGPL restent dans tmp/aircraft_a53_graph_patch_proposal/, exclus du manifeste public ; leurs empreintes et la proposition sont conservées. Aucun moteur installé modifié, aucun nouveau binaire produit, aucun effet natif du correctif qualifié.

Les sorties anciennes sont conservées : métadonnées comparées avec manifestes SHA256 existants, sans nouvelle relecture intégrale. Entrées effectivement utilisées, source moteur figée, binaire et original entier sont recontrôlés. Les harnais PASS et empreintes vérifient la traçabilité ; ils ne valident pas la physique.

## 6. Contradictions et informations manquantes

Le regroupement A52 reste rejeté : équivalence des attaches native indisponible. Les erreurs initiales, la captureC4périmée et le contrôleREORDERsans appel restent archivés. La compilation et les essais du correctif ne sont pas autorisés par l’ancien accord A43 portant sur la source non modifiée. AGENTS.md exige une demande explicite pour les modifications de logiciels ; la proposition séparée prépare un troisième moteur isolé, compilation≤1h/sixCPU, dépendances existantes, sans nouvelle installation ni GPU, puis contrôles natifs≤180s.

CHECK force la voiePCG/IPREC5 et n’est pas une dynamiqueMUMPS qualifiée. Les cinqTYPE25 ignorés en implicite restent bloquants pour un impact avec ces contacts. Les lois cohésives chargées/croissanceA40, peauxA34, raffinementA36, travaux locaux/énergie et autres critères restent échoués ou manquants. Les essais sans charge et le défaut de logiciel ne qualifient pas l’initiation ou l’effondrement historique.

Meilleur impact entier A20 :0,0200001220703125seconde. Aucun temps des diagnostics A53 n’est crédité. L’objectif dix secondes physiques simulées, visualisation3D puisMP4/GIF, reste incomplet. Jeremy demande de finir cette sous-tâche et de préparer une nouvelle session : A54 ne commence pas ici. Publication A52+A53 selon l’autorisation existante, puis prompt de reprise daté avec preuve distante finale.

AIRCRAFT-A54 : demander l’accord explicite de Jeremy pour la proposition wtc1_simulation_v8/output/aircraft_a53/proposition_correctif_graphe_moteur.md avant toute application ou compilation. A53 identifie le vrai bloc fautif : 128 triangles SH3N du fuselage, éléments193..320,89nœuds, coordonnées exactes ; 24paires6/6 et144lignes manquantes. Une observation séparée du modèle entier A49 non regroupé montre une écriture TYPE2 dans ICOK au mauvais pas24 pour une ligne principale exigeant ICOKM au pas119, puis inflation du compteur de3à4 alors que le voisin existe déjà ; colonne correcte toujours0. Correctif d’un fichier préparé mais non appliqué et non compilé, huit contrôles Python de graphes réussis sans qualification native du correctif. Après autorisation seulement : troisième moteur isolé depuis la source 3d75ff13d1946f6d28a43920eac4fa2aae41b27a, patch exact conservé, dépendances existantes, aucune installation/GPU, compilation≤1h et sixCPUmaximum ; contrôles natifs≤180s, destination des écritures puis CHECK original/candidat et lois/contacts/bilans. Ne pas déplacer les entrées physiques ni traiter les TYPE25 ignorés comme des contacts qualifiés. En dimensionnement, conserver le padding et les indices globaux ordinaires ; en construction, principales row-INK. A52 groupée reste rejetée, anciennes erreurs conservées. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques 3D puisMP4/GIF incomplet. Jeremy demande de terminer A53 et sa publication puis de reprendre dans une nouvelle session ; ne pas commencer A54 ici.
