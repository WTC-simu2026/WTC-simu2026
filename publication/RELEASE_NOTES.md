# Instantané AIRCRAFT-A64+AIRCRAFT-A65 — 14 octobre 2026

Instantané du **14 octobre 2026** : **AIRCRAFT-A65 terminée**, prochaine **AIRCRAFT-A66**, registre **184 entrées**. Objectif dix secondes physiques puis vidéo3D incomplet.

**A64 : deux essais plus fins terminés, composé initial échoué.** La fréquence de sortie0,0001ms omettait6000pas intermédiaires du second essai0,0000625ms et invalidait la reconstruction de vitesse cycle par cycle. Les champs terminaux sauvegardés du second cas précédaient1ms. Échecs/lecteur initial préservés. Une analyse indépendante aux cycles réellement enregistrés concorde avec la solution exacte et les compteurs natifs, sans inventer les champs manquants. Les deux CHECK conditionnels n’ont pas été lancés.

**A65 : nouveau lot humain explicite, quatre Engine exécutés**, deux Starter propres, CPU1/cap180s, moteurA62 inchangé, sansGPU/compilation/installation. TFILEdt/2 et arrêt1+dt/2 enregistrent chaque cycle et la frontière cible1ms ; paramètres physiques et seuils conservés. **22contrôles par essai libre,44au total, passent**, avec comparaison temporelle KE5,47015e-6J/IE5,49140e-6J sous le seuil inchangé1,01e-5J. Résidu énergie≤4,48e-8J, impulsion/support≤4,81e-8Ns. Les sorties natives TH atteignent1ms ; dernière animation du second cas0,995062ms conservée, champ terminal complet issu des huit nœudsTH.

**Les deux CHECK entiers échouent.** Anciennes initialisations/cartes identiques vérifiées par empreintes. Chaque scène affiche15ERRORS/5WARNINGS et624messagesSTOPvolume, et ignore cinqTYPE25. Code0/NORMAL n’est pas un passage ; premier lecteur étroit null/false conservé puis corrigé par une nouvelle analyse des messages réels. A52nonintégré, aucun impact entier prolongé.

**A66 préparée, aucun patch appliqué ni compilé.** Les624éléments utilisentTYPE43/LAW117/Ismstr4, tandis que le helperA62 traiteIsmstr1. L’aire de référenceVOL n’est stockée que pourIsmstr1 ; Ismstr4 utilise l’aire couranteAREAP. Les quatre aires des624surfaces sont positives. Prototype courant52contrôles PASS ; proposition/source exacte dans une copie privéeAGPL, hors archivesMIT. La future modification/compilation du septième moteur nécessite un accord distinct ; les cinq contactsTYPE25 restent bloquants. Les tentatives de préparation R0–R3 échouées sont conservées, analyse/prototype réussi R1 réutilisé sans replay.

Les [rapports A64](wtc1_simulation_v8/output/aircraft_a64/rapport_aircraft_a64.md) et [A65](wtc1_simulation_v8/output/aircraft_a65/rapport_aircraft_a65.md) séparent les six catégories de preuve. Budgets, anciennes sorties, échecs au repos/imposésA62 et temporels grossiersA63 préservés. Domaine libre élastique uniquement ; dommage général, grandes rotations et bilans entiers restent non qualifiés. **Meilleur impact entier0,0200001220703125s**, aucune durée de témoin créditée à l’objectif et aucune vidéo fabriquant les secondes manquantes. Intégrité de publication distincte de validation physique.


1 archives complémentaires ; 136 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
