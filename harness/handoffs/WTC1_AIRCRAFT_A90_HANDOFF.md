# Reprise AIRCRAFT-A90 → AIRCRAFT-A91

Rapport : wtc1_simulation_v8/output/aircraft_a90/rapport_aircraft_a90.md
Proposition : wtc1_simulation_v8/output/aircraft_a90_preparation/proposition_correction_libre_projetee_A91.md
Plan : wtc1_simulation_v8/data/aircraft_a90_proposal.json

AIRCRAFT-A91 proposée non exécutée : appliquer le correctifA90 de correction exactement nulle après projection/condensation native, puis compiler un onzième moteur isolé, seulement après accord distinct. Plafond1h/6CPU, puis au maximum4EngineCPU1/180s, zéroStarter/GPU/installation : deux régressions, boucleA81 conditionnelle, CHECK entier conditionnel à toutes les qualifications locales. Aucun impact entier prolongé. Le vecteur libre exact doit être nul ; les non-zéros sous-normaux et les D/DD non finis restent exclus. Les mouvements imposés finis ne sont plus confondus avec une correction libre. Toutes les autres gardesA86, tolérances et budgets physiques conservés. Correctif préparé nonappliqué noncompilé ; A89consommé ne couvre aucune modification. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

Constructeur préparé R1 à utiliser : wtc1_simulation_v8/scripts/build_aircraft_a91_projected_null_r1.py. Le refus de chemin R0 est conservé ; aucun calcul ni correctif appliqué pendant ce refus.
