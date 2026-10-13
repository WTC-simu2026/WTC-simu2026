# AIRCRAFT-A60 — modes mixtes et limite de l’assemblage implicite

Six nouveaux témoins explicites chargés concordent avec le contrat propre de la branche mixte LAW117 déclarée. La dérivée exacte mixte est généralement non symétrique, incompatible avec son insertion directe dans l’assemblage symétrique inspecté. Aucun correctif moteur appliqué ou compilé ; aucune seconde d’impact entier supplémentaire.

## 1. Faits directement observés ou transcrits

Six Starter sans erreur/avertissement puis six Engine A57 normaux, un CPU/sans GPU, plafonds180s chacun. Historiques natifs binaires et CSV concordants ; trois axes de déplacements, vitesses et impulsions de réaction contrôlés. Tractions, travail externe, énergie interne, bilan global, masse instrumentale8g et absence de masse ajoutée passent les seuils A17 inchangés. Erreur maximale relative de traction0,000891. Demi-pas et aire×4 concordent. Deux ratios mixtes, azimuts distincts, décharge/recharge, trajet non proportionnel et compression après endommagement constituent de nouvelles questions ; aucun ancien témoin rejoué.

L’historique termine à0,9999ms, et échoue au contrôle initial de fin1ms. Les champs finaux sauvegardés indiquent1,0ms dans cinq cas,1,00001ms pour le demi-pas. Le premier contrôle d’égalité stricte échoue dans ce dernier cas. Ces analyses initiales restent intactes. Une analyse séparée, après calcul, compare la fin réelle à[1ms,1ms+pas déclaré], avec1e-6ms de lecture : six fins atteignent la cible dans un pas. Le script reproduit exactement cette correction d’observable ; ni horloge ni pas ni seuil mécanique ni horizon demandé n’est modifié. Aucun temps de témoin crédité à l’impact entier.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Sources primaires du logiciel figé3d75ff13d1946f6d28a43920eac4fa2aae41b27a lues en cache, empreintes et lignes consignées. SIGEPS117 décrit la branche mixte testée. Dans les répertoires implicites inspectés, IMP_MUMPS1 initialise SYM1 et IMP_BUCK SYM2. ASSEMC_KIJ utilise un triangle et une transposition de bloc ; la matrice non symétrique entière n’y est pas conservée. Cette constatation ne revendique pas une inspection de tous les chemins solveur. Les sources AGPL ne sont pas copiées dans les livrables publics MIT.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF consulté/modifié. Aucun ajustement aux dégâts connus.

## 4. Hypothèses propres au modèle

Graine1102085, zéro tirage, unités g/mm/ms, travail Nmm vers J×0,001. EN4400N/mm³,ET800N/mm³,TN450MPa,TT100MPa,GI/GII50N/mm conservés ; paramètres témoins sans fracture historique mesurée. Contrat propre limité au critère en déplacement, évolution linéaire, mélange en puissance d’exposant2 et compression asymétrique. Aucune qualification des autres branches LAW117. La différentiation automatique dérive les trois composantes avec l’état validé gelé pendant un essai. Repère matériel fixe, pas de dérivée géométrique native.

## 5. Résultats dérivés

Vingt-deux contrôles propres passent : différences finies des neuf dérivées, monotonicité des états, abandon d’essai sans pollution, pentes pures indépendantes, trois résolutions Newton revenant au même équilibre. Un contrôle négatif qui valide le dommage à chaque essai donne un mauvais équilibre et reste archivé. Ces contrôles qualifient le contrat propre, pas le retour arrière du moteur. La dérivée exacte non symétrique nécessite une autre méthode d’itération ou un assemblage différent ; changer uniquement SYM ne suffit pas. Une matrice surfacique symétrique d’itération peut être étudiée en conservant le résidu natif complet et en exigeant sa convergence.

Préservation des anciennes sorties/critères par métadonnées et manifestes ; configuration figée, rapports et empreintes propres enregistrés, harnais PASS. Aucun budget avion/façade, matériau ou RKE modifié.

## 6. Contradictions et informations manquantes

Convergence implicite native, validation/retour arrière des états et repères mobiles non qualifiés. Les fins d’historique/égalité stricte initialement échouées restent visibles ; le nouveau critère d’intervalle est une correction analytique postérieure explicitement déclarée. CHECK entier15erreurs/624volumes/cinq TYPE25 ignorés, A52 non intégré et critères locaux/matériaux entiers échoués conservés. A20 reste0,0200001220703125s et hors domaine pour une prolongation ; dix secondes physiques et leur vidéo3D restent incomplètes. Toute nouvelle modification/compilation du moteur exigera un accord distinct sur une proposition concrète.

AIRCRAFT-A61 : préparer une matrice surfacique symétrique d’itération avec forces natives LAW117 conservées, puis une différence moteur concrète et bornée. A60 six nouveaux témoins explicites mixtes/nonproportionnels/compression passent traction, travail et énergie ; 22 contrôles de dérivée complète et état d’essai passent. La dérivée mixte est généralement non symétrique ; ASSEMC_KIJ stocke un triangle, IMP_MUMPS1 appelle SYM1, IMP_BUCK appelle SYM2 dans les répertoires implicites inspectés. Ne pas assimiler une matrice symétrique d’itération à la dérivée exacte, ni modifier seulement le drapeau MUMPS. État d’essai natif/retour arrière, repères mobiles et convergence native restent à qualifier. Toute nouvelle modification/compilation moteur exige un accord humain distinct sur une proposition concrète. Moteur A57 SHA256 34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528 inchangé. Fin native des témoins1ms à un pas près, historique0,9999ms inchangé ; anciens échecs d’égalité temporelle préservés et correction d’observable séparée après calcul. CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré, bilans locaux et domaines matériaux échoués conservés. Meilleur impact entierA20 0,0200001220703125s, aucun crédit des témoins ; objectif dix secondes physiques puis vidéo3D incomplet. Pas de prolongation A20 hors domaine ni de répétition des diagnostics acquis. Publication après paireA60+A61 vérifiée.
