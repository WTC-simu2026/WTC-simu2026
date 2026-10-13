# AIRCRAFT-A54 — moteur corrigé compilé, graphe natif contrôlé, impact toujours limité

Le correctif A53 autorisé est appliqué à un troisième moteur isolé. Il supprime les messages de connectivité manquante et permet au candidat regroupé A52 de terminer son CHECK. Les 15 erreurs restantes et les cinq contacts TYPE25 ignorés empêchent encore une qualification de l’impact implicite. Aucun temps physique supplémentaire n’est crédité à l’objectif des dix secondes.

## 1. Faits directement observés ou transcrits

L’accord humain du 13 octobre est enregistré dans software_authorization.json. Le premier contrôle du fichier patché a arrêté la préparation avant compilation : GNU patch produit des fins de ligne LF, le fichier proposé A53 est CRLF. Cette tentative est conservée. R1 vérifie le contenu LF, puis copie le fichier proposé intact et exige son SHA256 exact. La compilation prend 248.771 secondes ; 474,160 secondes depuis le lancement initial, dans le plafond original d’une heure, six CPU, sans GPU ni installation. Aucun ancien moteur n’est remplacé.

Dix nouveaux Engine, un CPU chacun, limite 180 secondes, aucun Starter. Les deux CHECK entiers terminent code0/NORMAL : référence 432 appels TYPE2 et candidat 216, chacun 3024 attaches. Tous les labels de voisins, paramètres natifs, coordonnées et degrés de liberté correspondent exactement à la référence A52 enregistrée. Les 49370 anciens messages de connectivité sont absents dans ces deux sorties corrigées. Chaque CHECK conserve 15 ERRORS, 5 WARNINGS et 624 messages166 sur les éléments60001..60624.

La sonde au symbole auxiliaire générique capture zéro appel, résultat inconclusif conservé. La surveillance matérielle de la ligne48151 observe une nouvelle colonne3011 dans le bon rangement, aucune écriture à la mauvaise colonne surveillée, puis 41 voisins uniques au retour. L’hypothèse de diagnostic « compteur final3 » était trop restrictive : elle ignorait les autres vrais voisins ajoutés ; son échec reste conservé. Une nouvelle déclaration indépendante vise les clones réellement utilisés, dont l’ABI est vérifiée dans le désassemblage du binaire précis. 128 ajouts de dimensionnement et128 de construction passent l’oracle avant/après d’ensembles :140 doublons conservent leur compteur,116 nouveaux voisins l’augmentent correctement. Les quatre régions sont observées :28 principales et100 ordinaires par phase. Cela qualifie les opérations observées, sans total global extrapolé.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel exécuté. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a ; seul ind_glob_k.F porte le correctif exact A53. Les13869 fichiers sources/dépendances sont vérifiés avant modification. L’écart de métadonnées de dépendance71→67 hérité d’A44 reste explicite. Les versions GNU13.3.0, CMake3.28.3 et OpenMPI4.1.6 et les bibliothèques liées sont journalisées. CHECK conserve PCG/IPREC5, ce contrôle ne constitue pas une dynamique MUMPS entière.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou source officielle inspectée. Les archives et work/official_sources restent en lecture seule. Aucun dégât connu ne sert de cible d’ajustement.

## 4. Hypothèses propres au modèle

Graine1102079, aucun tirage. Les états physiques et les cartes Engine des comparaisons sont copiés avec empreintes identiques. Aucune masse, inertie, loi, liaison compensatoire ou RKE n’est ajoutée. Les oracles natifs d’ensembles sont des contrôles logiciels, pas des probabilités historiques. Les propriétés cohésives restent des paramètres de référence, sans mesure nouvelle de fracture réelle.

## 5. Résultats dérivés

Le binaire corrigé SHA256 c4a18b981b9beb461fbb570a12d5ef04aa9a97293c61875c9d458ea99579d3b2 est conservé dans a54_type2_graph_candidate_r1. Les sources complètes, patch et journaux sont conservés séparément sous AGPL ; ils restent exclus du manifeste public MIT courant. Les contrôles de graphe natif et d’équivalence des attaches passent dans leur domaine déclaré ; A52 n’est pas intégré pour autant.

Les quatre témoins cohésifs explicites passent leurs critères de masse, traction, rechargement et travail/énergie, aire et demi-pas. Les deux témoins TYPE7/MUMPS passent les bilans physiques et la comparaison du demi-pas. Les600 champs passent la règle de précision ASCII/float32 déjà utilisée A23/A41/A45 ; leurs échecs littéraux sont conservés. Une première analyse de contact a sauté la conversion faute de completion.json attendu par l’ancien lecteur : le moteur avait terminé normalement. Une passerelle de métadonnées et une analyse distincte réutilisent cette sortie sans rejouer le moteur.

Les624 éléments signalés sont tous LAW117/TYPE43, avec faces d’aire positive et hauteur initiale nulle. Ce constat n’annule pas le CHECK échoué : son traitement géométrique et la réponse cohésive implicite chargée doivent être qualifiés indépendamment. Les anciens fichiers sont vérifiés par métadonnées et manifestes SHA256 conservés, les entrées utilisées et A44 par empreintes fraîches. Harnais PASS avant et après ; intégrité et physique restent distinctes.

## 6. Contradictions et informations manquantes

Le CHECK entier n’est pas propre. Les cinq TYPE25 sont ignorés en implicite ; les témoins TYPE7 ne qualifient pas leur remplacement dans l’impact. Inertie et travaux des attaches, croissance cohésive chargée, peaux, raffinement et bilans locaux restent échoués ou manquants. L’absence de messages de graphe ne valide ni l’impact entier ni la chaîne historique.

La meilleure fenêtre d’impact entier reste0,0200001220703125s. Aucun des diagnostics A54 ne complète les dix secondes, et aucune vidéo de dix secondes physiques n’est fabriquée par extrapolation ou ralenti. La suite A55 examine les cohésifs isolés et leur compatibilité implicite, puis les contacts et autres domaines nécessaires avant extension.

AIRCRAFT-A55 : moteur A54 corrigé compilé et conservé, SHA256 c4a18b981b9beb461fbb570a12d5ef04aa9a97293c61875c9d458ea99579d3b2, dossier a54_type2_graph_candidate_r1. 256 opérations natives passent les ensembles de voisins dans quatre régions ; référence et candidat A52 terminent CHECK, toutes3024attaches identiques, aucun message de connectivité manquante. CHECK entier reste échoué :15erreurs,624messages166 sur60001..60624 cohésifs LAW117/TYPE43 de hauteur nulle, cinqTYPE25 ignorés. Qualifier indépendamment le traitement géométrique des cohésifs et leur réponse chargée implicite avec des cas isolés et des critères inchangés ; confronter un CHECK cohésif à un solide ordinaire et vérifier les bilans avant toute décision. Préserver la sonde auxiliaire sans appel, le critère erroné de compteur final3 et l’analyse contact initiale sans métadonnée completion. Aucun nouveau correctif moteur n’est implicitement autorisé par l’accord A53 ; présenter toute nouvelle modification concrète avant application/compilation. L’accord humain A54 est enregistré ; les contrôles supplémentaires avec ce même binaire et les données de cas sont autorisés pour poursuivre objectif1. A52 reste non intégré : seule équivalence native des attaches passe, inerties/travaux et insertion non qualifiés. Meilleure durée entière A20=0,0200001220703125s, pas de nouveau crédit physique. Aucun impact de dix secondes lancé avec des contacts ignorés ; zéro RKE inventée, budgets et échecs conservés. Prochaine publication A54+A55 vérifiées.
