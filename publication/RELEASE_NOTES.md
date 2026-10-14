# Instantané AIRCRAFT-A70+AIRCRAFT-A71 — 14 octobre 2026

Instantané du **14 octobre 2026** : **AIRCRAFT-A71 terminée**, prochaine **AIRCRAFT-A72**, registre **190 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A70 : proposition exacte de classification du résidu nul.** Le résidu nul A69 est confirmé, mais l’admissibilité proposée doit rester distincte de toute validation physique. La version R4 ajoute la déclaration native COM08 et sélectionne IDYNA2/IQSTAT0/TT0/R2exact0 dans IMP_CHKM. Quinze contrôles de portée passent ; versions de préparation échouées R0–R3 conservées, source privée AGPL hors livrables MIT. La proposition non compilée est ensuite autorisée distinctement par l’humain.

**A71 : huitième moteur isolé appliqué exactement et compilé.** Première compilation sur six CPU, plafond une heure, sans GPU ni installation ; toutes les corrections A67 restent présentes. Six Engine et un Starter sur un CPU/plafond180s sont entièrement consommés. **Le correctif TT0 échoue dans trois contrôles.** Le témoin zéro dynamique et les deux scènes entières affichent encore une erreur de chargement, R2=0, et aucune nouvelle INFO. Compilation/NORMAL ne sont pas un passage du critère.

**Les contrôles de comparaison passent.** Le zéro statique reste refusé comme prévu ; le témoin statique avec1N par nœud supérieur donne R2=4 et CHECK sans erreur ni avertissement, après Starter propre. La dynamique libre du nouveau binaire passe23critères aux seuils A67 conservés et ses TH atteignent1ms. Aucune durée de témoin créditée à l’impact entier. Les cinq observations CHECK sont complètes, y compris l’original manquant en A69 ; son ancien échec n’est pas réécrit.

**Cause mise en évidence en lecture seule : l’horloge TT avance avant CALL IMP_CHKM.** La garde TT exactement zéro ne représente pas le contexte du premier CHECK. Les valeurs précises des flags et de TT à l’appel ne sont pas directement capturées ; aucun scalaire natif supposé. A72 doit préparer une sélection par le contexte CHECK explicite et des observations de ces flags/horloges, sans rejouer le lot A71 ou réinitialiser les budgets.

**Les scènes entières restent bloquées**, chacune avec1ERROR/107396WARNINGS, dont107391 coefficients de préconditionnement signalés et cinq TYPE25 ignorés. Aucun STOPvolume ; A52nonintégrée, aucune extension dynamique entière. Les sources, versions, anciens moteurs, archives, budgets, préparations et critères échoués sont conservés. Aucun chargement artificiel dans la scène entière ni compensation RKE.

Les [rapports A70](wtc1_simulation_v8/output/aircraft_a70/rapport_aircraft_a70.md) et [A71](wtc1_simulation_v8/output/aircraft_a71/rapport_aircraft_a71.md) séparent les six catégories de preuve. Nouvelle modification/compilation du moteur et lot natif soumis à un accord humain distinct. **Meilleur impact entier : 0,0200001220703125 s.** Dix secondes et vidéo 3D ne sont pas produites ; aucune extrapolation visuelle fabriquée. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


1 archives complémentaires ; 139 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
