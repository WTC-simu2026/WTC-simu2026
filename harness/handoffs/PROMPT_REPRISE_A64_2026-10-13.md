# Reprise WTC1 — A63 terminée, A64 préparée

Continuer l’objectif1 : dix secondes physiques d’impact avion–façade, puis visualisation3D et MP4/GIF. Conditions réalistes documentées, résultats observés sans viser les dégâts connus. Aucun temps de témoin ajouté à l’impact ; ne pas inventer une seconde manquante. État local actuel prioritaire sur ce document.

Lire intégralement AGENTS.md, harness/state.json, harness/handoffs/WTC1_AIRCRAFT_A63_HANDOFF.md et les fichiers suivants :

- wtc1_simulation_v8/output/aircraft_a63/rapport_aircraft_a63.md
- wtc1_simulation_v8/output/aircraft_a63/composite_qualification_review.json
- wtc1_simulation_v8/output/aircraft_a63/dispersion_and_next_step_review.json
- wtc1_simulation_v8/output/aircraft_a62/rapport_aircraft_a62.md
- wtc1_simulation_v8/output/aircraft_a62/composite_qualification_review.json
- wtc1_simulation_v8/output/aircraft_a62/build_finished.json
- wtc1_simulation_v8/data/aircraft_a62_authorization.json
- wtc1_simulation_v8/output/aircraft_a64_preparation/proposition_etape_a64.md
- wtc1_simulation_v8/data/aircraft_a64_proposal.json
- wtc1_simulation_v8/output/aircraft_a64_preparation/preparation_review.json
- harness/publication_cycle.json
- outputs/github_publication/updates_2026-10-13_aircraft_a62_a63/final_remote_verification.json s’il existe ; sinon publication encore en vérification, ne pas la déclarer terminée.

État attendu à la rédaction : A63, registre182, A64 suivante, aucun Engine en cours. A62 a appliqué le correctif surfacique A61 explicitement autorisé dans le sixième moteur isolé. Exacte différence approuvée d’abord appliquée ; R0/R1 échecs de compilation conservés, R2 corrige seulement l’interface/type natif des déclarations, équations du helper inchangées. Binaire d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235. Sources/anciens moteurs, archives, budgets et échecs préservés ; images ext4 démontées.

A62 dix nouveaux Engine : au repos, NaN/Infinity des rapports de convergence àT0, puis code2/limite de pas, sans STOP volumique. Avec petite vitesse initiale Y libre, trois témoins terminent à1ms et concordent sur traction/travail/G/recharge. Les contrôles KE/P/somme de REAC sous mouvements imposés échouent, ne pas inventer de compensation pour les fermer. Trois régressions explicites297canaux bit à bit identiques, deux TYPE7/MUMPS et demi-pas source énergie/momentum passent. Vieilles vérifications brutes de champs restent échouées.

A63 deux nouveaux Engine, oscillateur cohésif LIBRE élastique :22contrôles par cas (44 au total) passent, solution Newmark discrète exacte et bilans physiques énergie/momentum/support qualifiés dans ce domaine. Résidus énergie≤8,82e-9J, impulsion≤1,10e-8Ns. MAIS les pas0,001/0,0005ms diffèrent de0,00034846J, au-dessus du seuil1,01e-5J. Échec temporel conservé. La dispersion exacte propose0,000125/0,0000625ms ; pas choisi par erreur analytique, aucune propriété ajustée, ne pas le transposer aux masses de l’avion.

Les12Engine du lot A61 sont consommés au total A62(10)+A63(2). A64 est prête pour un NOUVEAU lot de quatre maximum : deux libres raffinés puis, uniquement si le composé local passe, deux CHECK entiers originaux/paireA53 exacts. CPU1,180s chacun, sansGPU/compilation/installation ni extension dynamique. Accord supplémentaire demandé dans le chat ; vérifier s’il a été reçu dans wtc1_simulation_v8/data/aircraft_a64_authorization.json et/ou la conversation courante. Ne pas redemander s’il existe effectivement, ni dépasser l’ancien lot avant accord. Lanceur prêt : wtc1_simulation_v8/scripts/run_aircraft_a64_step.py ; il impose l’accord exact et une publication précédente complètement vérifiée.

Les modèles entiers gardent leurs anciens échecs : CHECKcached15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré ; bilans locaux/domaines matériaux/inerties et grandes rotations restent ouverts. Pas de nouvel impact entier exécuté. Meilleure fenêtre entière0,0200001220703125s, objectif1 incomplet. Toute nouvelle modification/compilation moteur supplémentaire exige une proposition concrète et un accord distinct ; les corrections déjà exécutées ne l’autorisent pas.

Ne pas rejouer les diagnostics acquis ou rescanner les archives. Harnais avant/après changements importants, rapports/sorties réels avant état/registre, publication toutes les deux itérations vérifiées, anciennes releases conservées. Nouvelles courtes en français.
