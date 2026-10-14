# A65 proposée — enregistrer les pas et la frontière cible

A64 : deux nouveaux calculs terminent normalement, mais la sortieTH0,0001ms omet6000pas intermédiaires du second essai au pas0,0000625ms. Le lecteur exige chaque pas ; son premier résultat et l’absence du champ terminal à1ms restent des échecs conservés. Aux cycles effectivement enregistrés, les déplacements et compteurs natifs concordent avec la solution analytique ; cela ne suffit pas pour qualifier le composé.

Proposition : deux essais sur le même moteur A62, avec les mêmes matériaux, surface, masses8g, vitesse initiale, supports, pas et seuils. Seuls deux réglages de sortie changent : fréquenceTH=dt/2 pour ne manquer aucun cycle ; arrêt1+dt/2 afin de sauvegarder la frontière cible1ms, au plus un pas supplémentaire réel. Le seuil d’overshoot préexistant reste inchangé. Les champs proviendront du moteur ; aucun état manquant extrapolé.

Si tous les critères locaux passent, deux CHECK entiers sur les mêmes anciennes entrées originales/appariées vérifiées par empreintes. Aucun impact entier prolongé, aucune qualification entière inférée du témoin. Les blocsTYPE25, budgets, bilans locaux et autres critères échoués restent ouverts.

Nouveau lot demandé : maximum4Engine, CPU1, plafond180s chacun, estimation2–5minutes. Sans nouvelle modification du moteur, compilation, installation ouGPU. A64 a utilisé2contrôles ; ses deux CHECK conditionnels n’ont pas été lancés et ne sont pas convertis en essais de remplacement. L’ancien lotA61 de12 reste consommé.

Les cartes exactes, différences et lanceur sont prêts. Dix secondes physiques d’impact puis vidéo3D restent l’objectif ; meilleur impact entier0,0200001220703125s.
