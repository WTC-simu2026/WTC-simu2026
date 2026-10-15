# AIRCRAFT-A84 — audit des normalisations et mesure brute préparée

Travail en lecture seule, zéro Engine/Starter ; aucun correctif du moteur. Les deux divisions non protégées sont localisées, mais leurs opérandes réels ne sont pas encore mesurés.

## 1. Faits directement observés ou transcrits

A83 imprimeInfinity sur le critère énergie dès1 etNaN sur le déplacement dès2 ; arrêt au maximum30 puis79/ISTOP−2. Une seule ligneTH réelle à0ms. Deux fichiers logiciels sont copiés sans modification depuis le cache épinglé3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Le binaire actuel conserve les trois symboles nécessaires ; aucune exécution Engine pour les inspecter.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La source logicielle de NL_SOLV calcule RE=DE0/EIMP, puis à partir d’IT2, RU=LS(3)*sqrt(DU2/U2), sans garde locale de ces dénominateurs. Après une itération non négative, DE0 est ramené à une constante positive si sa valeur absolue est trop petite. PRODUT_UHP projette/condense les déplacements avant de former la norme sur les inconnues libres. NITOL123 combine les trois critères normalisés.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée ou modifiée. Les sources AGPL brutes demeurent dans le répertoire logiciel privé, exclues du manifeste propre public. Le précédent cache A34 a servi au repérage ; les conclusions sont liées aux copies exactes du cache épinglé vérifié.

## 4. Hypothèses propres au modèle

Graine1102107, zéro tirage, unitésg/mm/ms. Des mouvements libres nuls et une énergie cumulée nulle sont compatibles avec ce témoin dont les mouvements normaux sont imposés. Le plancher deDE0 pourrait alors produireInfinity, et une normeDU2/U2 nulle sur nulleNaN. Ce mécanisme reste une hypothèse à mesurer, pas un constat de valeurs internes natives. Un mouvement imposé non nul ne garantit pas une norme libre non nulle. Aucun remplacement arbitraire des non-finis ni changement de tolérances proposé.

## 5. Résultats dérivés

Addendum d’interprétation A83 : la ligne d’itération0 utilise le même en-tête visuel que les suivantes, mais la source imprime sqrt(U2),sqrt(R02),EIMP à0, puis RU,RR,RE pourIT>0. Les chaînes et nombres A83 restent exacts ; l’appellation générale de ratios dans son rapport est trop large pour0. Le rapport initial est conservé, cette correction est ajoutée explicitement ici. Les observationsInfinity/NaN aux itérations positives restent valides.

Une observation nouvelle du moteur inchangé est préparée. Les signatures et indices d’arguments sont comparés à la source épinglée, les trois symboles au binaire exact. Le lecteur utilise quatre points matériels maximum, lectures de données seules et désactivation à l’itération2, puis laisse le calcul terminer. Un seul EngineCPU1/plafond180s est proposé, zéro Starter/correctif/compilation/GPU/installation. Les données et le restart propre sont identiques à A83 ; aucun ancien diagnostic n’est rejoué pour sa question déjà résolue : les nouvelles valeurs demandées sont les références brutes absentes.

## 6. Contradictions et informations manquantes

Les valeurs exactes deDE0,EIMP,U2,DU2 et le vecteur libre restent inconnus. Le lecteur est vérifié statiquement, pas encore au fonctionnement natif ; une observation manquée ne sera pas remplacée automatiquement. Aucun temps/cycle global n’est promis par cette capture. Le seul EngineA83 est consommé ; nouvel accord requis pour A85. Toute proposition future de changement du moteur restera distincte. Compression, rupture, refermeture, contacts et dix secondes physiques non qualifiés ; meilleur impact entier0,0200001220703125s. Anciennes sorties, budgets, échecs et107391avertissements conservés.

AIRCRAFT-A85 proposée non exécutée : une mesure nouvelle des références Newton brutes, un seul Engine A73 inchangé sous observateur en lecture seule, CPU1/plafond180s ; restart initial propre A81 et carte exacte A83 réutilisés, zéro Starter/correctif/compilation/GPU/installation. Observer DE0,EIMP,R02,F libre et normes natives U2/DU2 aux premières itérations0à2, puis laisser le moteur terminer sans changer les données, critères ou bornes de pas. Quatre points matériels, aucune écriture de code ou données numériques. Accord distinct requis : le seul Engine A83 est consommé. Une observation manquée consomme sa place sans réessai. L’hypothèse de dénominateurs nuls n’est pas encore une mesure ; aucun correctif ne doit masquer les non-finis. Compression, rupture, refermeture et contacts restent non qualifiés. Anciennes sorties, budgets,107391avertissements et critères échoués conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
