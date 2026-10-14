# Instantané AIRCRAFT-A68+AIRCRAFT-A69 — 14 octobre 2026

Instantané du **14 octobre 2026** : **AIRCRAFT-A69 terminée**, prochaine **AIRCRAFT-A70**, registre **188 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A68 : audit en lecture seule des nouveaux CHECK A67.** Huit sources logicielles figées expliquent la chaîne : le contrôle de connexion porte sur un tableau réutilisé comme préconditionneur après LIN_SOLV, avec des coefficients issus d’inverses approchés. Ses faibles valeurs ne sont pas, à elles seules, une preuve de déconnexion. Les 75 nœuds de translation signalés ont tous des incidences d’éléments : 74 au fuselage, un à l’aile. Cela ne démontre pas le rang complet des contraintes. Les cinq TYPE25 restent ignorés et bloquants. Aucun Engine, Starter, correctif ou compilation en A68.

**A69 : trois Engine sur un CPU/plafond 180 s, après accord humain distinct.** Moteur A67 inchangé, sans Starter, GPU, installation ni compilation. **La première observation originale échoue** : le lecteur propre tentait de lire l’adresse inutilisée d’un tableau de taille zéro. Échec compté et conservé, aucune valeur native R2 attribuée à l’original. Une version R1 du lecteur traite correctement un tableau vide ; seules les deux observations restantes sont exécutées, sans répétition ni remise à zéro du budget.

**Deux observations complètes : R2 vaut exactement zéro**, et LB est entièrement nul, dans la scène appariée et le témoin libre CHECK. Ce témoin conserve sa dynamique libre A67 qualifiée jusqu’à 1 ms. Il affiche pourtant l’erreur native de chargement, car le contrôle exige un résidu strictement positif. Dans la scène appariée, la diagonale assemblée dynamique/contraintes est positive, comprise entre 1,13727e7 et 1,14438e18 ; les coefficients après préconditionnement vont de 8,73833e-19 à 8,79297e-8. Les 107391 valeurs signalées concordent avec ce tableau transformé. La positivité dynamique ne prouve pas la validité des seules liaisons statiques. La correspondance complète entre équations libres réduites et les deux diagonales n’est pas reconstruite sans IKC ; aucune correspondance inventée.

**La scène entière reste refusée** : une erreur de chargement, 107391 avertissements de connexion possible et cinq TYPE25 ignorés. L’observation originale reste incomplète ; deux mesures réussies ne deviennent pas trois réussites. Tous les anciens critères, sorties et budgets restent conservés. A52 non intégrée, aucun impact entier prolongé, aucune force fictive ou compensation RKE.

**A70 : préparer le correctif limité au contrôle du résidu initial dynamique nul**, en préservant les anciens CHECK refusés et la distinction entre admissibilité numérique et qualification physique. Toute nouvelle modification/compilation du moteur nécessite un accord humain distinct. Les cinq contacts requièrent encore une variante déclarée et contrôlée, sans substitution silencieuse.

Les [rapports A68](wtc1_simulation_v8/output/aircraft_a68/rapport_aircraft_a68.md) et [A69](wtc1_simulation_v8/output/aircraft_a69/rapport_aircraft_a69.md) séparent les six catégories de preuve. Sources privées AGPL et binaires exclus des livrables MIT. **Meilleur impact entier : 0,0200001220703125 s.** Aucune seconde manquante fabriquée dans une vidéo. Publication et CI attestent l’intégrité, pas la validité physique de l’impact réel.


1 archives complémentaires ; 138 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
