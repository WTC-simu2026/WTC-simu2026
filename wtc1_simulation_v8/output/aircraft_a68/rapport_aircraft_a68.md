# AIRCRAFT-A68 — audit du résidu et de la sémantique CHECK

L’audit en lecture seule précise les deux blocages numériques nouveaux, sans modifier leur statut échoué. Il prépare trois mesures natives directes, non exécutées, nécessaires pour attribuer précisément les valeurs manquantes.

## 1. Faits directement observés ou transcrits

Les deux nouvelles sorties A67 emploient le gradient conjugué et des inverses approchés factorisés. IMP_CHKM appelle IMP_CHECK0, puis le contrôle de norme de LB, LIN_SOLV et enfin IMP_CHECM0. IMP_CHECK0 copie DIAG_K et ajoute DIAG_I dans DIAG_M ; LIN_SOLV réutilise ce tableau comme espace de préconditionnement. FSA_SOLV y écrit la dernière composante obtenue en résolvant un sous-système avec second membre unité. IMP_CHECM0 teste ces valeurs avec les bornes fixes 1e-12 et 1e10. Les 107391 directions imprimées sont entièrement relues depuis les sorties A67 ; les 75 nœuds de translation sont reliés aux cartes d’entrée.

- A49_EQUIVALENT_RIGID_CHAINS_0000.rad : 75 nœuds de translation signalés ; 75 ont des incidences d’éléments ; rôles : {"fuselage_skin": 74, "fuselage_stringers": 74, "fuselage_frames": 74, "wing_ribs": 1, "wing_stringers": 1, "wing_skin": 1}.
- A52_TYPE2_FACET_PAIRS_R1_0000.rad : 75 nœuds de translation signalés ; 75 ont des incidences d’éléments ; rôles : {"fuselage_skin": 74, "fuselage_stringers": 74, "fuselage_frames": 74, "wing_ribs": 1, "wing_stringers": 1, "wing_skin": 1}.

Les cinq contacts TYPE25 gardent leurs cartes et noms exacts. Aucun chargement de force ou mouvement imposé détecté dans les familles de mots-clés examinées ; la carte INIVEL de translation est conservée. /IMPL/DYNA/2 était déjà présent. La valeur R2 effective n’est pas disponible dans ces listings. Le binaire A67 possède les cinq symboles nécessaires à l’observation. gdb est absent : aucune installation effectuée ; la méthode locale déjà disponible de points d’arrêt matériels est utilisée dans la proposition, sans rejouer ses anciens diagnostics.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Huit fichiers du même pin OpenRadioss sont lus depuis le cache logiciel vérifié, copies privées sous AGPL, hors publication MIT. La routine PRODUT_W calcule pour un seul processus la norme carrée ordinaire de LB ; W_DDL ne filtre que la branche multi-processus. La chaîne dynamique soustrait masse × accélération ; une vitesse initiale ne garantit pas une force résiduelle initiale non nulle. La branche d’amortissement est distincte.

## 3. Affirmations provenant des archives locales

Aucune archive historique consultée ou modifiée ; aucune nouvelle analyse vidéo. Aucun ajustement aux dégâts connus.

## 4. Hypothèses propres au modèle

Graine 1102093, zéro tirage. La cause exacte des valeurs natives reste inconnue : l’audit n’assimile pas un coefficient d’inverse à une raideur ou une masse brute. L’incidence d’un élément ne démontre pas le rang complet des contraintes. Un exemple algébrique connecté positif à échelle 1e14 illustre seulement la dépendance d’échelle du test d’inverse, sans attribuer cette matrice à la scène entière.

## 5. Résultats dérivés

Les faibles valeurs signalées ne suffisent pas à prouver des déconnexions. Le résidu initial nul d’un problème à vitesse initiale pourrait expliquer l’erreur de chargement, mais R2 doit être mesuré pour confirmer ou rejeter cette hypothèse. Trois mesures préparées lisent R2/LB et les diagonales avant/après transformation dans deux CHECK entiers et un témoin libre CHECK. Le moteur et les cartes entières restent exactement identiques. L’observation n’exige ni patch ni compilation ; les valeurs nouvelles recherchées n’existent pas dans les sorties vérifiées précédemment.

## 6. Contradictions et informations manquantes

Aucun nouvel Engine ni Starter exécuté ; les mesures proposées sont non qualifiées en exécution. Une erreur de chargement, 107391 directions signalées et cinq TYPE25 ignorés par scène restent des critères échoués, intégration entière refusée. Aucun changement de RREF, seuil, force, masse, matériau, inertie ou RKE. Préconditionnement et résidu demandent des valeurs natives avant tout correctif éventuel. Les cinq contacts exigent ensuite une variante mécanique déclarée, des contrôles distincts et une preuve d’équivalence, sans substitution silencieuse. Meilleur impact entier 0,0200001220703125 s ; objectif dix secondes puis vidéo 3D incomplet. A66+A67 publiées et vérifiées avant déclaration A68, intégrité distincte de validation physique.

AIRCRAFT-A69 proposée : trois nouvelles observations natives bornées, non exécutées, moteur A67 inchangé. Mesurer directement R2/LB et les diagonales avant/après préconditionnement dans les deux CHECK entiers et un témoin libre CHECK. Observer par points d’arrêt matériels et lectures mémoire du seul enfant propre, sans gdb, installation, patch ni compilation. Un CPU, plafond 180 s chacun, maximum trois Engine, aucun Starter ni prolongement entier. Attendre un accord humain distinct sur ce lot, car les huit Engine A67 sont consommés. Ces mesures nouvelles ne répètent pas les anciens diagnostics de volume ou de graphe. Les cinq contacts TYPE25 restent ignorés et bloquants ; aucune substitution ou modification de seuils. Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D incomplètes.
