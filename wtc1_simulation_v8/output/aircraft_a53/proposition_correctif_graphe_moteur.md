# Proposition A53 : correction du rangement du graphe, moteur isolé

La mesure sur le moteur actuel non modifié montre un défaut précis. Pour le nœud48151, ligne9891dans la région principale, NNMAX24etNKMAX119donnent deux adresses différentes. Le moteur écrit le voisin48154dans le tableau calculé avec le mauvais pas24, puis augmente le compteur de la bonne ligne de3à4. Le voisin figurait déjà dans ses trois colonnes correctes. La quatrième colonne correcte reste0pendant que le compteur monte ensuite jusqu’à14. Cela explique des lignes contaminées ; la cause de toutes les autres erreurs n’est pas déclarée prouvée.

Le correctif proposé concerne un seul fichier, ind_glob_k.F, dans la source figée du28juillet. Il sélectionne le tableau et le pas corrects pour les opérations TYPE2de dimensionnement et de construction : ajout de colonne, lecture de voisin, test d’appartenance. La phase de dimensionnement conserve ses indices globaux avec padding, conformément à l’allocation existante ; la phase de construction utilise row-INKpour les principales. Les matériaux, géométrie, masses, liaisons physiques, charges, pas de temps et critères restent inchangés. Aucun bloc n’est ignoré pour éviter un arrêt.

Huit contrôles de graphes indépendants passent une référence dictionnaire/ensembles, y compris domaines sans région principale ou ordinaire. Le cas observé reproduit l’ajout erroné d’un voisin déjà présent. Ces contrôles ne sont pas une compilation ou qualification du moteur proposé.

Le fichier proposé et le patch exact sont dans tmp/aircraft_a53_graph_patch_proposal/, sous la licenceAGPLdu moteur. Les empreintes et la liste des changements sont enregistrées dans engine_patch_proposal_review.json. Aucun fichier du logiciel actuel n’a été modifié, aucun nouveau binaire compilé.

## Exécution proposée après accord explicite

Créer un troisième moteur séparé depuis le même code3d75ff13d1946f6d28a43920eac4fa2aae41b27a, avec uniquement ce correctif. Utiliser les compilateurs et bibliothèques déjà installés, les dépendances en cache, aucune nouvelle installation, aucun GPU. Compilation limitée à une heure, sixCPUmaximum. Conserver source/patch/empreintes, paramètres de compilation, journaux, version et nouveau binaire ; ne remplacer aucun ancien moteur.

Puis vérifier la syntaxe compilée, les cas indépendants de masse/lois cohésives/contact et la destination native des écritures de graphe. Comparer les CHECKentiers original et candidat, sans toucher les entrées physiques. Chaque contrôle natif reste borné180s. Les critères échoués restent explicites : cela n’autorise pas un impact implicite avec TYPE25ignorés. Le moteur ne sera intégré à l’impact qu’après bilans et contrôles nécessaires ; les dix secondes3D restent l’objectif, pas la simple compilation.

## Autorisation requise

AGENTS.md impose : « Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy. » L’accord A43 concernait le moteur non modifié du28juillet. Cette proposition modifie son code de rangement du graphe ; elle nécessite donc un accord supplémentaire. La publicationA52+A53est déjà autorisée et peut continuer indépendamment.
