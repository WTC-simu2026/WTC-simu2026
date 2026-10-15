# AIRCRAFT-A80 — vérifier la cohésion avant de changer le contact

Préparation en lecture seule, zéro calcul natif et aucun correctif appliqué. La politique d’attente jusqu’à sortie du gap n’est pas retenue : une rupture cohésive peut la précéder. Un témoin concret A81 est préparé, non exécuté, non autorisé. Les analyses exploratoires conservées précèdent la déclaration de cette synthèse ; elles ne sont pas présentées comme des exécutions natives préenregistrées.

## 1. Faits directement observés ou transcrits

Les4430paires A79 sont reliées aux assemblages du modèle courant :2910sur des facettes de même peau partageant une arête et un joint direct, dont les916erreurs ;1520partagent seulement un sommet d’origine. Pour ces dernières,1108chemins de longueur2 et412de longueur3 existent autour du sommet. Les624joints et chemins RBE2 vers leurs coins sont présents. Le contrôle R0 d’identité avec A20 échoue sur144hôtes réaffectés ; il reste conservé. R1 vérifie les raccords écrits actuellement vers les racines, sans conclure équivalence mécanique. Aucune exclusion de contact n’est ainsi qualifiée.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La documentation logicielle [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) décrit une réduction de gap pour Inacti5/6 ; ces options ne satisfont pas ici la conservation du gap exigée. La sémantique [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) d’ignorance initiale puis réentrée n’est pas transférée par la seule valeur1000. Des sources logicielles ciblées en cache expliquent stockage/tri/effort/matrice ; elles ne prouvent pas l’identité du Starter Windows avec ces sources.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source inspectée ou modifiée. Les seuls membres copiés proviennent du cache logiciel épinglé, avec empreintes conservées séparément ; leurs sources brutes ne sont pas incluses dans le manifeste public propre. Aucun dégât connu ciblé.

## 4. Hypothèses propres au modèle

Graine1102104 pour la synthèse, zéro tirage. Les nœuds distincts et les joints séparables restent conservés. Une table persistante par paire demanderait une nouvelle fonction transversale Starter/Engine, engagement au pas accepté, annulation des essais Newton et reprise/tri cohérents. Ce n’est pas un petit correctif prêt à compiler. Surtout, sous les hypothèses de modeI pur et d’évolution linéaire, les paramètres actuels EN4400,TN450,GI50 donnent450/4400=0,10227mm d’initiation et2×50/450=0,22222mm de rupture, avant le gap0,5mm. La rupture native et la compression résiduelle ne sont pas déduites de cette formule seule.

## 5. Résultats dérivés

Un témoin A81 conserve les cartes numériques LAW117/TYPE43 et la géométrie validée A67 : huit nœuds, carré100mm²,8g de masses instrumentales, sans contact général. Il impose en Z une compression−0,05mm, une ouverture0,3mm et une refermeture−0,05mm sur0,65ms. Les translationsXY restent libres comme la trame dynamique ; dériveXY, cisaillement, uniformité, aire et orientation doivent être contrôlés nativement avant d’invoquer le modeI. Les21contrôles indépendants de préparation et20contrôles du générateur passent, sans qualification native. Les10417échantillons de chargement sont vérifiés, erreur maximale5,01e−13mm. Un Starter puis un Engine uniquement si la préparation passe, unCPU/plafond180s chacun ; logiciels A73/Starter inchangés, zéro compilation/GPU/installation ou extension entière.

Les sorties demandent tous les pas acceptés, état final réel, OFF/contraintes/énergie et variables utilisateur. Leur peuplement natif n’est pas présumé. Les réactions de nœuds du précédent témoin sont des impulsions cumulées ; la pente de l’impulsion du support bas sur les plateaux de compression doit être comparée avant/après, référence conditionnelle22000N et tolérance2% héritée A67. Ne pas lire une impulsion comme une force. L’absence de contact dans le coupon sert uniquement à isoler la cohésion.

Six contrôles supplémentaires relient la configuration finale aux cartes inchangées. Le critère énergétique A67 conservé est0,02×K0+1e−7J ; ici K0=0, donc1e−7J. Il n’est remplacé ni par1e−5J ni par2%du travail de rupture après consultation des résultats. Une éventuelle qualification complémentaire du travail imposé devra être déclarée séparément avant ses résultats. Un échec de ce critère reste distinct du succès de la mesure.

## 6. Contradictions et informations manquantes

La compression après suppression éventuelle de l’élément n’est pas qualifiée ; une branche constitutive compressive ne garantit pas qu’un élément supprimé la transmette. Confirmer la rupture par statut natif/événements des quatre points, jamais par le déplacement0,3mm seul. USR absents ou nuls ne prouvent pas un dommage nul ; les champs manquants après suppression ne sont pas une guérison. Un essai complet peut réfuter la politique d’attente géométrique sans qualifier un futur contact. L’échec d’observation reste conservé sans réessai automatique. L’unique Starter A79 est consommé et n’autorise aucun nouveau Starter/Engine. Aucun nouveau correctif proposé à compiler. A75/A77/A79,107391avertissements A73, budgets et limites restent conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

AIRCRAFT-A81 proposée, non exécutée : un Starter puis un Engine conditionnel CPU1/plafond180s chacun, moteur A73 inchangé, zéro correctif, compilation, GPU, installation ou prolongement de l’impact entier. Témoin cohésif LAW117/TYPE43 exact,8nœuds/100mm²/8g instrumentaux, aucun contact général : compression−0,05mm, ouverture0,3mm puis refermeture−0,05mm, horizon0,65ms. Mesurer impulsions/réactions, contraintes, énergie, OFF et défaillance des quatre points ; USR absents ou nuls ne prouvent pas un dommage nul. Une rupture avant le gap nominal0,5mm rend insuffisante la simple attente jusqu’à sortie complète ; cette politique n’est pas retenue sans ce contrôle. Modes purs, aire constante et compressions avant/après à qualifier nativement. Accord distinct requis : unique Starter A79 consommé, aucun Engine prévu dans ce lot précédent. Conserver analyses R0/R1, anciennes sorties, budgets et critères échoués. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
