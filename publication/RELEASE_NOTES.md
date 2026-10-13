# Instantané AIRCRAFT-A60+AIRCRAFT-A61 — 13 octobre 2026

Instantané du **13 octobre 2026** : **AIRCRAFT-A61 terminée**, prochaine étape **AIRCRAFT-A62**. Registre **180 entrées**. Les dix secondes physiques d’impact et leur vidéo3D restent incomplètes.

**A60 : six nouveaux témoins explicites** mixtes, non proportionnels et compression après dommage, CPU1/sansGPU, chacun plafonné180s, Starter sans erreur/avertissement puis Engine A57 normal. Traction dans les trois directions, travail/énergie, demi-pas et aire×4 passent les seuils A17 conservés. Erreur maximale relative de traction0,000891.22contrôles propres de dérivée complète et état d’essai passent ; dérivée mixte généralement non symétrique, incompatible avec l’insertion directe dans un assemblage triangulaire symétrique.

L’historique natif0,9999ms reste inchangé. Ses contrôles de fin initialement échoués et l’égalité stricte échouée du champ à1,00001ms sont conservés. Une analyse séparée après calcul vérifie la fin effective à1ms dans un pas déclaré, avec les champs sauvegardés, sans modifier durée/pas ni seuil mécanique. Aucun temps de témoin ajouté à la couverture entière.

**A61 : aucun nouveau Starter/Engine**,44contrôles propres d’une matrice surfacique symétrique d’itération : équilibre, aires uniformes/nonuniformes, rang12, translations nulles, rotation3D, reconstruction triangulaire, neuf équilibres à résidu mixte complet avec états validés gelés. L’échec R0 bit à bit reste archivé ; R1 utilise la tolérance matricielle1e-12 déjà déclarée. Une différence exacte de s8zke3.F est préparée : branche TYPE43+LAW117+Ismstr1, quatre aires natives de référence, normale courante ; les forces et états SUSER43/SIGEPS117 restent calculés nativement. Cette matrice est une approximation d’itération, pas une tangente cohérente.

**Correctif non appliqué/non compilé dans cette paire.** [Proposition A61](wtc1_simulation_v8/output/aircraft_a61/proposition_correctif_surface_implicite.md). Accord distinct reçu pour la future A62 : sixième moteur isolé, plafond compilation1h/CPU6/sansGPU/sansinstallation, jusqu’à12contrôles CPU1/plafond180s chacun. Les cinq moteurs antérieurs et trois correctifs déjà autorisés sont conservés. Grande rotation, convergence implicite native et restauration des états Newton restent non qualifiées ; un échec bloquera l’intégration entière. Source/différence bruteAGPL hors des archives publiques MIT.

Les [rapports A60](wtc1_simulation_v8/output/aircraft_a60/rapport_aircraft_a60.md) et [A61](wtc1_simulation_v8/output/aircraft_a61/rapport_aircraft_a61.md) séparent les six catégories de preuve. Aucun budget de masse/matériau, termeRKE ou seuil physique changé, aucun dégât connu ciblé. Archives/anciennes sorties/échecs conservés ; aucun ancien solver rejoué.

CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés ; A52 non intégré, domaines matériaux/bilans locaux échoués conservés. **Meilleur impact entier :0,0200001220703125s**, sans prolongation de l’ancien état hors domaine. Aucune vidéo obtenue par interpolation des secondes manquantes. Intégrité de publication et validation physique restent distinctes.


1 archives complémentaires ; 134 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
