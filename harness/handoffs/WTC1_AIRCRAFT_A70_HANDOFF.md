# Reprise AIRCRAFT-A70 → AIRCRAFT-A71

Rapport : wtc1_simulation_v8/output/aircraft_a70/rapport_aircraft_a70.md
Proposition : wtc1_simulation_v8/output/aircraft_a70_preparation_r4/proposition_controle_residu_initial_nul.md
Plan : wtc1_simulation_v8/data/aircraft_a70_proposal_r4.json

AIRCRAFT-A71 proposée, non appliquée/non compilée : huitième moteur isolé avec le correctif exact A70 de CHECK initial à résidu nul. Nouvel accord humain distinct requis avant toute modification/compilation, conformément à AGENTS.md. Ajout limité à quatre lignes dans IMP_CHKM (déclaration COM08 et garde) : IDYNA2, IQSTAT0, TT0, R2 exactement0 ; diagnostic explicite, aucun chargement entier artificiel. Les anciennes erreurs restent conservées ; les 107391 avertissements et cinq TYPE25 restent présents et bloquants. Plafond compilation1h/CPU6 ; maximum six Engine et un Starter sur CPU1/cap180s chacun, sans GPU ni installation, aucune dynamique entière prolongée. Témoins zéro dynamique, zéro statique refusé, charge positive instrumentale, régression libre1ms puis deuxCHECK entiers. Budget A69 trois entièrement consommé (deux observations complètes, première originale échouée), jamais réinitialisé. Préserver budgets, sorties, critères échoués et RKE sans compensation. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.
