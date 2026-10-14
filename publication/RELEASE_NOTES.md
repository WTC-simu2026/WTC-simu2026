# Instantané AIRCRAFT-A62+AIRCRAFT-A63 — 13 octobre 2026

Instantané du **13 octobre 2026** : **AIRCRAFT-A63 terminée**, prochaine étape **AIRCRAFT-A64**, registre **182entrées**. Les dix secondes physiques d’impact et leur vidéo3D restent incomplètes.

**A62 : sixième moteur isolé compilé**, autorisation humaine A61 sauvegardée. Différence approuvée appliquée exactement, puis déclarations d’interface Fortran réparées seulement ; équations exécutables du helper inchangées. Échecs R0/R1 conservés, R2 réussit dans le même plafond initial1h/CPU6/sansGPU/installation. Binaire **d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235**. Sources/caches/anciens moteurs préservés ; sources/différences/binaireAGPL hors des archives MIT.

Dix nouveaux Engine A62 CPU1/plafond180s : au repos, témoin normal et journal Newton échouent àT0 par rapports NaN/Infinity, résidu de force0 puis limite de pas. Le STOP volume nul est franchi. Trois variantes avec petite vitesseY libre initiale terminent à1ms, tractions/travail/G/rechargement/demi-pas concordants. Les conventions KE/P et somme de toutes les REAC sous mouvements imposés restent **non qualifiées**, leurs critères échoués et analyses initiales conservés ; aucune compensation de masse/RKE. Trois régressions explicites : **297canaux égaux bit à bit** aux A60 ; deux TYPE7/MUMPS et demi-pas passent le lecteur source/énergie/momentum A45, avec les échecs bruts antérieurs archivés.

**A63 : deux derniers Engine du lot autorisé**, sans compilation ou patch. Oscillateur surfacique élastique libre, aucune trajectoire imposée, deux Starter propres, CPU1/plafond180s. **22contrôles par cas (44 au total) passent** : solution Newmark discrète exacte, énergie physique, quantité de mouvement/impulsion des seuls supports, canaux natifs, masse8g et masse ajoutée0. Maximum résidu énergie8,82e-9J, impulsion1,10e-8Ns ; erreur de déplacement analytique7,24e-10mm.

**La comparaison demi-pas échoue** : KE/IE diffèrent jusqu’à0,00034846J, tolérance conservée1,01e-5J. Le composé global resteFALSE. Conservation algébrique et solution discrète exacte ne prouvent pas la convergence en temps. La dispersion analytique propose0,000125/0,0000625ms pour les futurs témoins ; matériau/masse/géométrie inchangés, aucune adaptation aux dégâts historiques. Ce pas instrumental n’est pas transposé à l’avion.

**Les12contrôles autorisés sont consommés.** [A64 préparée](wtc1_simulation_v8/output/aircraft_a64_preparation/proposition_etape_a64.md), non exécutée à cet instantané : deux essais plus fins puis, si tous les critères passent, deux CHECK entiers avec les anciennes entrées exactes. Nouveau budget maximum4/CPU1/cap180s, sanscompilation/GPU/installation, soumis à un accord distinct. Aucun impact entier prolongé.

Les [rapports A62](wtc1_simulation_v8/output/aircraft_a62/rapport_aircraft_a62.md) et [A63](wtc1_simulation_v8/output/aircraft_a63/rapport_aircraft_a63.md) séparent les six catégories de preuve. Archives/anciennes sorties/critères échoués préservés. Ancien CHECK15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré ; domaines matériaux et bilans locaux entiers restent ouverts. **Meilleur impact entier :0,0200001220703125s**, aucun temps de témoin crédité à l’impact. Aucune vidéo produite en inventant les secondes manquantes. Intégrité de publication distincte de la validation physique.


1 archives complémentaires ; 135 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
