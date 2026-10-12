# Instantané AIRCRAFT-A44+AIRCRAFT-A45 — 12 octobre 2026

Instantané du **12 octobre 2026** : **AIRCRAFT-A45 terminée**, prochaine étape **AIRCRAFT-A46**. Le registre compte **164 entrées**. Le second moteur MUMPS est construit et ses contrôles natifs passent. Le modèle entier démarre en explicite ; son contrôle implicite échoue encore. Les anciens résultats et échecs sont conservés.

A44 construit le moteur antérieur figé **3d75ff13d1946f6d28a43920eac4fa2aae41b27a** en **5min11s**, six threads CPU, dans l’heure autorisée, sans installation ni patch de physique. Sources et dépendances : **13869blobs vérifiés**. Les quatre premières tentatives A44 sont refusées par WSL avant Engine ; ces refus restent conservés. La différence de dépendance67/71 déclarée reste non qualifiée physiquement.

Après rétablissement de WSL, A45 exécute **huit processus natifs nouveaux**, dont sept terminent normalement. Les **quatre contrôles LAW117** passent les critères de mouvement, force, réaction, travail, énergie, recharge et rupture, avec demi-pas et normalisation par aire. Les **deux collisions élastiques TYPE7 calculées avec MUMPS** passent masse, énergie, quantité de mouvement et convergence temporelle. Les **600champs** passent la vérification de format float32/six chiffres préexistante ; les contrôles littéraux échoués restent visibles. Les histoires physiques nommées des collisions concordent avec les références A41 à la précision sauvegardée ; une ancienne colonne NO NAME non identifiée reste explicitement non comparée.

Le **modèle entier explicite inchangé démarre et termine trois cycles** : l’ancienne incompatibilité de lecture LAW117 A42 est résolue. Ce micro-démarrage ne prolonge pas les20ms de l’impact entier. Le **CHECK entier avorte pendant l’assemblage de raideur** (ASSEMC_KIJ/ASSEM_C4/CBAKE3) et signale séparément **cinq contacts TYPE25 ignorés**. Aucun lien causal unique n’est affirmé, aucune substitution silencieuse de contact ou modification de reprise n’est faite. L’implicite entier reste non qualifié.

Les [rapports A44](wtc1_simulation_v8/output/aircraft_a44/rapport_aircraft_a44.md) et [A45](wtc1_simulation_v8/output/aircraft_a45/rapport_aircraft_a45.md) séparent faits, sources, archives, hypothèses, résultats et lacunes. Les binaires, bibliothèques et sources tierces brutes sont exclus. Aucun ancien solveur relancé pour publication. A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués. Les paramètres physiques de rupture, modes mixtes, domaines locaux, structure intérieure et gravité restent à traiter.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Aucun temps de témoin ou de démarrage n’est crédité à l’extension entière. Aucun dégât connu comme cible. L’intégrité de publication ne valide pas la physique ou l’événement historique.

Archives précédentes et échecs conservés.


1 archives complémentaires ; 123 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
