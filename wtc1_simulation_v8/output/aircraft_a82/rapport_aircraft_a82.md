# AIRCRAFT-A82 — rendre visible le premier refus de convergence

Préparation en lecture seule d’une observation nouvelle ; zéro exécution native, aucun correctif logiciel. Le prochain lot ne modifie que l’impression, pas les critères physiques ou numériques.

## 1. Faits directement observés ou transcrits

A81 : Starter propre, zéro erreur/zéro avertissement, Engine arrêté avec MESSAGE79/ISTOP−2. Un unique état natif sauvegardé à0ms, pas de compression ou rupture mesurée. La sortie confirme les deux bornes0,000125ms et une fréquence d’impression nonlinéaire0. Les valeurs ayant provoqué le premier refus ne figurent pas dans ce fichier.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Un [exemple logiciel officiel](https://2022.help.altair.com/2022.3/hwsolvers/rad/topics/solvers/rad/fan_blade_rotation_initialization_example_r.htm) documente l’impression des itérations nonlinéaires par /IMPL/PRINT/NONL/-1. Le parseur source épinglé accepte le préfixe NONL, lit la dernière composante dans NPRINT et le défaut vaut0. L’option NONLIN complète est préparée ; son rendu réel reste à vérifier.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source inspectée/modifiée. Trois fichiers logiciels sont copiés en privé depuis le cache épinglé, avec empreintes. La copie brute .F exploratoire dans la préparation est exclue explicitement du manifeste propre, avec les autres sources AGPL brutes.

## 4. Hypothèses propres au modèle

Graine1102105, zéro tirage ; unités g/mm/ms conservées. Le chemin source compatible rejette un pas, restaure temps/cycle, ajuste DT puis s’arrête lorsque DT égale le minimum. Cette lecture ne fournit pas la cause initiale du refus et ne permet pas d’accuser un résidu nul, un pivot ou la loi cohésive. Les sources éclairent une hypothèse de chemin ; seuls les critères nativement imprimés doivent la préciser.

## 5. Résultats dérivés

Une carte ajoute exactement /IMPL/PRINT/NONLIN/-1. Tous les blocs préexistants restent identiques, notamment /IMPL/NONLIN/1 (son premier champ n’est pas une fréquence d’impression), tolérances, /IMPL/DT/STOP, pas initial, chargement et horizon. Le restart initial du Starter A81 est copié à l’identique, sans Starter supplémentaire. Dix contrôles statiques de portée passent. Un EngineCPU1/plafond180s seulement est proposé, logiciel A73 inchangé, sans compilation/GPU/installation ou extension entière. La question porte sur les premières valeurs de convergence manquantes, pas sur un ancien diagnostic déjà vérifié.

## 6. Contradictions et informations manquantes

Aucun nouveau résultat natif. La trajectoire0,65ms du coupon, ses sortiesUSR peuplées, dommage, compression après rupture et retour de contact restent inconnus. L’arrêt79 peut être reproduit tout en réussissant une observation, mais ne sera jamais rebaptisé convergence. Une seule place nouvelle nécessite un accord explicite ; A81estconsommé. Toutes les anciennes sorties, bornes et tolérances restent conservées. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

AIRCRAFT-A83 proposée non exécutée : une nouvelle observation Engine seulement, CPU1/plafond180s, restart initial propre A81 réutilisé, zéro Starter, correctif, compilation, GPU ou installation. Ajouter uniquement /IMPL/PRINT/NONLIN/-1 à la carte Engine A81 ; noms conservés dans un nouveau dossier isolé. Mesurer les critères du premier refus Newton et ses valeurs de référence avant tout changement de tolérance, pas, chargement ou physique. Le message79/ISTOP−2 peut rester attendu ; une observation ne devient pas trajectoire réussie. Un nouvel accord explicite est requis :1Starter+1Engine A81consommés. Ne pas redémarrer depuis une fin non convergée, ne pas abaisser silencieusement le minimum de pas. Anciennes sorties, critères échoués, budgets et107391avertissements conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
