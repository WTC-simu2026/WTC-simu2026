# Instantané AIRCRAFT-A90+AIRCRAFT-A91 — 15 octobre 2026

Instantané du **15 octobre 2026** : **AIRCRAFT-A91 terminée**, prochaine **AIRCRAFT-A92**, registre **210 entrées**. **Les dix secondes physiques d’impact entier et la vidéo 3D restent à produire.**

**A90 prépare une garde de correction libre exactement nulle.** La projection reprend IMP_SETB puis CONDENS_B ; chaque composante projetée doit être exactement nulle, avec rejet des D/DD non finis. Les restrictions A86, les tolérances et le traitement non dégénéré restent conservés. Les 105 contrôles mathématiques et la revue de portée sont statiques ; l’application et la compilation sont réalisées uniquement par A91 après son accord explicite distinct. La première dérivation du lanceur, rejetée avant toute exécution, reste archivée.

**A91 compile le onzième moteur isolé en 320,630 s, six CPU, dans le plafond d’une heure.** Zéro Starter, GPU, installation ou prolongement dynamique entier. Les dix anciens moteurs, sorties et critères échoués sont conservés. Le lot utilise trois Engine sur quatre maximum, un CPU et 180 s chacun. Les deux régressions reproduisent exactement les canaux binaires sauvegardés et passent leurs contrôles mécaniques aux seuils d’origine : mouvement libre et aire courante avec Y libre, dans leurs portées respectives.

**Le témoin original de compression–rupture–refermeture termine normalement et sauvegarde 5 201 états jusqu’à 0,65 ms.** Le blocage numérique au second essai est levé : 5 200 marqueurs de garde. Cette durée locale n’est pas une durée d’impact entier. Un problème de sérialisation JSON d’un booléen NumPy a interrompu le premier export d’analyse ; le fichier partiel et l’exception sont conservés, puis l’analyse est récupérée sur les mêmes sorties sans aucun calcul natif supplémentaire ni changement des formules ou seuils.

**La qualification physique reste échouée.** Le plateau initial de compression donne environ 22 000,007 N en valeur absolue, mais celui après rupture et refermeture donne 0 N. Le résidu énergétique calculé vaut au maximum 6,15396457e−5 J pour le seuil inchangé 1e−7 J ; la différence entre énergie cinétique nodale reconstruite et native atteint 3,86075989e−5 J. La précision des sorties et la reconstruction doivent être examinées avant d’attribuer cet écart à la mécanique. La population/sémantique des champs USR et la fermeture indépendante par travail des réactions restent non certifiées. Aucun RKE inventé et aucun seuil relâché.

**Le CHECK entier conditionnel reste inutilisé**, sans réaffectation de sa place. Aucun impact entier prolongé ; cinq contacts TYPE25 ignorés et 107 391 avertissements restent bloquants. A92 doit lire les nouveaux états et les sources exactes pour expliquer la perte de compression après rupture, puis examiner les champs et le bilan indépendant. Une nouvelle modification du moteur ou un autre lot natif exigera une proposition et un accord distinct. Aucune archive historique ni vidéo réanalysée, aucune adaptation aux dégâts connus.

Les [rapports A90](wtc1_simulation_v8/output/aircraft_a90/rapport_aircraft_a90.md) et [A91](wtc1_simulation_v8/output/aircraft_a91/rapport_aircraft_a91.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Publication et CI vérifient l’intégrité des fichiers, pas la physique de l’impact réel.


1 archives complémentaires ; 149 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
