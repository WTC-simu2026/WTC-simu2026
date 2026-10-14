# Instantané AIRCRAFT-A74+AIRCRAFT-A75 — 14 octobre 2026

Instantané du **14 octobre 2026** : **AIRCRAFT-A75 terminée**, prochaine **AIRCRAFT-A76**, registre **194 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A74 : contrat de cinq contacts actuels et deux variantes TYPE7 préparées, non exécutées.** Les deux scènes A49/A52 portent les mêmes interfaces2/101/102/103/104, groupes secondaires3024/1056/480/672/5785nœuds et surfaces principales en coques. L’inventaire statique propose gap0,5mm pour2 et5mm pour101–104. Vingt-deux critères de portée passent ; toutes les cartes mécaniques et TH restent identiques hors cinq cartes de contact et noms BEGIN/TITLE/RUN. Une variante de modèle de contact est déclarée explicitement, sans présumer l’équivalence dynamique TYPE25/TYPE7.

**A75 : les deux Starter autorisés échouent ; aucun Engine CHECK exécuté.** CPU1/plafond180s chacun, moteur A73 inchangé, sans correctif, compilation, GPU ni installation. Chaque cas retourne2, sans dépassement de temps, avec **916erreurs et11avertissements**. La condition de préparation propre interdit les deux CHECK : leurs places restent conditionnellement inutilisées, non réaffectées ; aucun nouveau crédit Starter. Les deux Starter autorisés sont entièrement consommés.

**Cause native précise, conservée avec les sorties.** Les916erreurs612 par cas concernent seulement l’auto-contact2 du radôme : nœuds sur la surface principale et impossibilité de calcul de nouvelles coordonnées. L’entrée et le résumé impriment Inacti1000, mais les erreurs impriment INACTI=0. Aucun domaine de nombres de nœuds ou état initial valide n’est supposé. Les11avertissements sont10messages614 (IBAG activé sans volume surveillé puis remis à zéro, deux passages pour cinq interfaces) et1message343 :4430pénétrations initiales concernant1968nœuds. La valeur1000 ne porte pas le même contrat initial entreTYPE25 etTYPE7 ; une revue statique et le résumé de paramètres ne qualifient pas l’initialisation.

**Les totaux de masse sont conservés, pas la compatibilité validée.** Les cinq TYPE7 et gaps déclarés sont imprimés. Masse191273837,9425g, ADMAS100368522,1367g et centres imprimés correspondent aux références ; aucun tenseur redistribué ou inertie native inférés. Aucun restart initial propre n’est produit, aucun impact entier prolongé. La liste des paires initiales n’est pas qualifiée par ces sorties avortées.

**Les blocages restent visibles.** Anciennes TYPE25 ignorées,107391 avertissements de préconditionnement A73, gardeTT0 ratée A71, budgets, configurations et critères échoués sont conservés. Aucun contact entier supprimé, déplacement de nœuds d’entrée, RKE de compensation, modification masse/matière/inertie ou ajustement aux dégâts connus. A76 doit auditer le filtrage de voisinage et IBAG à partir de ces nouvelles données, préparer une différence exacte puis demander un accord distinct pour de nouvelles préparations.

Les [rapports A74](wtc1_simulation_v8/output/aircraft_a74/rapport_aircraft_a74.md) et [A75](wtc1_simulation_v8/output/aircraft_a75/rapport_aircraft_a75.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Dix secondes et vidéo 3D restent incomplètes. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


1 archives complémentaires ; 141 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
