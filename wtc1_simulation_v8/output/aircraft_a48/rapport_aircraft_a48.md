# AIRCRAFT-A48 — panne capturée dans le graphe d’assemblage entier

Quatre petits assemblages coque/solide terminent leur diagnostic, sans reproduire l’arrêt. Une variante entière retire seulement les368liaisons RBE3 dans une copie distincte ; l’arrêt persiste. Une observation locale du processus natif inchangé capture alors des colonnes attendues absentes de la matrice et un accès invalide K_LT au moment de SIGSEGV. La correspondance entre indices internes et pièces d’entrée reste à établir avant correction. Aucune extension physique de l’impact.

## 1. Faits directement observés ou transcrits

Cinq préparations Starter nouvelles et six Engine nouveaux, un thread CPU, bornés180s, sans GPU. Quatre assemblages à mêmes géométrie/matériaux/masses : aucun lien, TYPE2/Spot5, RBE2translatoire, RBE3interpolatoire. Chaque petite préparation a0erreur/avertissement, chaque Engine atteint BEGIN/END CHECK et sortie0/NORMAL. Les compte rendus portent1erreur de chargement et27avertissements de rotation ; aucune qualification mécanique propre n’est revendiquée.

La copie entière sans RBE3 conserve toutes les autres sections de l’entrée, avec seulement deux titres renommés. Les368sections retirées sont listées. Les1320RBE2 et les autres contraintes ne sont pas réécrits ou remplacés. La préparation conserve les2avertissements originaux et0erreur. Engine signale les5TYPE25ignorés puis s’arrête de nouveau dans ASSEMC_KIJ, avant le compte rendu CHECK.

La trace observe seulement notre propre processus fils. La permission kernelTRACEME, GETREGS et breakpoint matériel est vérifiée avec un processus de contrôle /bin/true. Aucun nouvel outil installé, compilation, patch d’instructions, écriture de tableau mécanique ou modification du binaire. Le signal original est transmis au moteur, qui conserve son arrêt avec code3. Les paramètres et scripts d’observation sont enregistrés avant ce calcul instrumenté distinct.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle officiel historique. La source figée du moteur utilise ASSEM_C4→ASSEMC_KIJ pour les blocs de coques. ASSEMC_KIJ cherche une colonne JDIK, puis utilise JDL sans branche explicite de colonne absente. Le désassemblage situe l’instruction observée à+0x664, une lecture vectorielle lors de l’accumulation du bloc. Ces éléments de code sont rapprochés de la capture native ; aucun correctif logiciel n’est appliqué.

- [Assemblage global figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/imp_glob_k.F)
- [Assemblage des coques figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/assem_c4.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie, vidéo ou PDF historique inspecté. Les sources restent en lecture seule. Aucun dégât historique n’est une cible de réglage.

## 4. Hypothèses propres au modèle

Graine1102073, zéro tirage. Même extrait de quatre coques de façade A20, neuf nœuds, acier de référence et épaisseur7,9375mm. Un petit bloc métallique10×20×20mm, huit nœuds et une brique HA8, est un instrument de couplage déclaré : MAT/LAW2/1,TYPE14/Isolid14. Il ne représente pas le noyau composite entier. Masse du panneau8640,489177995g, bloc11,12g, total8651,609177995g. Chargement nul et aucun appui ; les modes libres et absence de chargement sont conservés dans CHECK.

TYPE2 utilise quatre nœuds solides secondaires et les quatre facettes principales. RBE2 utilise le centre du panneau comme référence et les nœuds solides secondaires ; RBE3 utilise un nœud solide comme référence et neuf nœuds du panneau. Ces choix testent une seule famille à la fois ; le sens main/secondaire et le comportement des DOF partiels de l’assemblage entier ne sont pas supposés reproduits automatiquement. La redistribution RBE3 est évaluée sur la masse des deux corps réunis.

La variante entière sans RBE3 est strictement diagnostique : contraintes et redistribution d’inertie sont explicitement modifiées. Ce n’est pas un candidat d’impact. Les matériaux, propriétés, éléments, coordonnées, masses prescrites, groupes et autres liaisons sont conservés. Aucune compensation de masse ou inertie et aucune substitution de TYPE25.

## 5. Résultats dérivés

Les quatre petits assemblages passent les contrôles de complétion et de masse ; ils ne prouvent pas la mécanique chargée des assemblages entiers. Le retrait des RBE3 ne supprime pas l’arrêt : cette famille seule ne suffit pas à l’expliquer.

La masse totale préparée reste191273837,9425g, le centre reste[14245,90260656;−0,00031019191109262;−211,2460794408]mm. Les masses non structurelles prescrites ADMAS restent100368522,1367g, identiques à la référence. Un premier lecteur assimile à tort le libellé Starter TOTAL ADDED MASS à une masse artificielle de mise à l’échelle : son échec est conservé. Un addendum distingue les ADMAS existantes du compteur Engine ADDED MASS. Aucun nouvel ajout de masse. L’histoire native initiale entière n’est pas exploitable après l’arrêt ; le compteur de mise à l’échelle n’est donc pas déclaré observé égal à zéro.

La capture native, après1531appels d’assemblage, révèle NEL128, ND6 et IKPAT1. Parmi les128paires du bloc,26paires à NDOF[6,3] présentent156lignes sans la colonne attendue. Première paire interne[41005,41002], IDDL[250824,224517] ; colonne224518absente des lignes examinées. L’instruction arrêtée tente une lecture K_LT à l’indice1082239911 ; son adresse correspond à l’adresse signalée par SIGSEGV. Ce rapprochement localise une incohérence réelle de graphe/assemblage. Il ne démontre pas encore sa construction amont ni que toutes les lignes manquantes ont été visitées avant l’arrêt.

NI/NJ sont des indices internes. Leur assimilation directe aux labels /NODE n’est pas validée : retrouver le même entier dans une brique de l’entrée ne suffit pas à identifier la pièce fautive. Coordonnées, connectivité et labels doivent être capturés au même bloc avant un reproducer minimal ou une correction.

## 6. Contradictions et informations manquantes

La panne logicielle est localisée, sa cause amont et la correspondance aux pièces ne sont pas encore prouvées. Le petit RBE2 utilise une coque principale et un solide secondaire ; il n’exclut pas un problème avec une coque secondaire partiellement contrainte. Aucun branchement n’est ignoré dans le moteur pour obtenir une terminaison. Les cinq TYPE25 ignorés restent une incompatibilité indépendante.

A47 montre une réponse des coques chargées concordante sur les histoires communes11,999ms, avec deux sorties finales implicites encore échouées. A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués. Structure intérieure, gravité, matériaux/rupture et bilans des domaines entiers restent ouverts. Meilleur impact entierA20=0,0200001220703125s ; aucun temps de diagnostic crédité aux dix secondes physiques ni nouvelle vidéo présentée comme cet objectif.

Anciennes empreintes conservées, audit tailles/dates avant/après sans modification ancienne ; ce n’est pas une nouvelle relecture de tous leurs contenus. Original physique et binaire revérifiés par SHA256. Registre et état sont mis à jour seulement après existence des sorties, rapport et validation du harnais.

AIRCRAFT-A49 : exploiter la capture A48 du graphe au moment de SIGSEGV, pas une nouvelle supposition sur TYPE25 ou RBE3. Les quatre petits assemblages terminent CHECK. Retirer les368RBE3 du modèle entier conserve masse totale/centre/ADMAS prescrites, mais reproduit ASSEMC_KIJ+0x664. La lecture locale du processus fils non modifié capture après1531appels un bloc128éléments, ND6, IKPAT1 :26paires NDOF6/3 ont156lignes sans colonne attendue ; accès K_LT à l’indice1082239911, SIGSEGV puis sortie3. NI/NJ sont des indices internes, pas encore identifiés aux labels originaux. Pré-déclarer une observation supplémentaire de CBAKE3 pour lire coordonnées/connectivité/identifiants au même bloc, établir la correspondance avec l’entrée puis créer un petit reproducer respectant le rôle main/secondaire et les DOF partiels. Aucun patch binaire/source, remplacement silencieux de liaisons, ajout de masse/inertie ou relaxation physique pour contourner la panne. Instrumentation propre TRACEME et breakpoint matériel disponibles ; aucun outil à installer. Les deux avertissements Starter et cinq TYPE25 ignorés restent explicites. Histoires initiales entières non exploitables après l’arrêt, aucun bilans de temps avancé inféré. A47 champs chargés concordent dans les histoires communes11,999ms, sorties terminales implicites encore échouées. A40 chargé/croissance, A34 peaux, A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF restent actives et incomplètes. A46+A47 publiées/vérifiées ; A48 en attente deA48+A49.
