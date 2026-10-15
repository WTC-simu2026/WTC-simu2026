# Proposition A83 — une observation détaillée du premier essai Newton

A81 a produit un Starter propre, puis un arrêt Engine79/ISTOP−2 avant tout état sauvegardé à temps positif. Les deux processus autorisés sont consommés. Le minimum de pas fixé au pas initial reste conservé, comme tous les critères échoués.

Une seule carte Engine est préparée dans un nouveau dossier. Elle ajoute uniquement /IMPL/PRINT/NONLIN/-1 ; la carte /IMPL/NONLIN/1, son premier paramètre et ses trois tolérances restent exactement identiques, ainsi que chargement, pas initial, minimum/maximum, sorties de champs, conditions physiques, solveur et horizon. Les noms restent A81 pour réutiliser exactement le restart initial, avec un dossier A83 distinct. Le restart vient du Starter réussi, jamais d’une fin dynamique rejetée. Aucun nouveau Starter.

Le lot proposé comporte un seul Engine A73 inchangé, unCPU/plafond180s, estimation5–30s, sans correctif, compilation, GPU, installation ou prolongement d’impact entier. Il doit imprimer les critères et valeurs normalisées/références disponibles du premier refus, le cycle/temps tenté et les messages. Une valeur non finie ou absente est signalée, jamais transformée en convergence. Le même arrêt peut rester attendu ; succès d’observation et réussite de trajectoire sont séparés. Un lancement échoué/expiré consomme sa seule place, sans réessai automatique.

L’analyse source explique le chemin compatible avec le message générique (rollback d’un pas rejeté puis minimum atteint), sans fournir les ratios réellement calculés dans A81. Il faut les mesurer avant de changer les bornes ou les tolérances. Documentation logicielle : [exemple officiel d’impression nonlinéaire](https://2022.help.altair.com/2022.3/hwsolvers/rad/topics/solvers/rad/fan_blade_rotation_initialization_example_r.htm). Le rendu réel de l’option reste à vérifier nativement.

Accord distinct requis pour ce nouveau lot : A81consommé n’autorise aucune autre exécution. Les échecs, avertissements et budgets anciens restent conservés. Aucun contact ou dommage n’est qualifié par cette observation. Dix secondes physiques et vidéo3D incomplètes ; meilleur impact entier0,0200001220703125s.
