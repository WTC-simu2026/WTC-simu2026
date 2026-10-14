# Reprise AIRCRAFT-A72 → AIRCRAFT-A73

Rapport : wtc1_simulation_v8/output/aircraft_a72/rapport_aircraft_a72.md
Proposition : wtc1_simulation_v8/output/aircraft_a72_preparation/proposition_contexte_CHECK_explicite.md
Plan : wtc1_simulation_v8/data/aircraft_a72_proposal.json
Observateur : wtc1_simulation_v8/data/aircraft_a72_observer_plan.json

AIRCRAFT-A73 proposée seulement : neuvième moteur isolé avec le correctif exact A72, garde CHECK IMP_CHK>0 à la place de TT==0 dans IMP_CHKM, suppression de COM08 devenue inutile. Nouvel accord explicite distinct requis avant application/compilation et six nouveaux Engine. Compilation plafond1h/sixCPU, estimation5–15min ; six Engine au maximum, unCPU/plafond180s chacun, zéro Starter, sans GPU ni installation, aucun prolongement dynamique entier. Starter positif qualifié A71 réutilisé ; entrées et seuils conservés, flags natifs et horloge à mesurer. A71 gardeTT0 échouée et budgets sixEngine/unStarter entièrement consommés, sorties/échecs inchangés. Les107391 avertissements et cinq TYPE25 par scène restent bloquants. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. Ne pas créditer les témoins, modifier implicitement les budgets, compenser par RKE ou viser des dégâts connus.
