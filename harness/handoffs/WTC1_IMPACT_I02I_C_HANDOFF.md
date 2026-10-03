# WTC1 — IMPACT-I02I-C terminée, prochaine I02I-D

Lire AGENTS.md, harness/state.json, cette passation, puis `wtc1_simulation_v8/output/impact_i02i_sampling/publication_verification.json`. L’état local fait autorité. V8H/V11H sont historiques ; V11F froid et V11R → V11S sont préservés.

## À réutiliser

C : six connecteurs TYPE8 neufs et deux éprouvettes médianes ENG/TRUE_TOTAL neuves, identiques à B sauf fréquence TH. 5.584 min de calcul. Rapport `wtc1_simulation_v8/output/impact_i02i_sampling/rapport_impact_i02i_sampling.md`, résultats `wtc1_simulation_v8/output/impact_i02i_sampling/verification_r2/summary.json`, config `wtc1_simulation_v8/data/impact_i02i_sampling_predeclaration.json`. 84/85 contrôles scalaires ; 29/30 critères éprouvettes ; 6/8 comparaisons B/C. Les échecs restent des échecs.

Travail de ressorts : dense ENG 9.33971424e-06 %, TRUE_TOTAL 8.73802426e-06 % d’erreur ; sous-échantillonner les mêmes lignes à 0,004 ms reproduit B (1.32934/0.283296 %). 58523/82611 lignes = cycles moteur ; toutes les lignes B correspondent à des temps denses. R1 et script conservés ; R2 corrige le diagnostic de cadence basé sur les incréments CSV arrondis. Aucun solveur relancé pour cette correction.

Références : normale 0,03 J, cisaillement0,0043 J, cycle H2 conserve l’historique et retrouve la plage sans force ; demi-pas concordant. MIXED : OFF nul une ligne avant FX nul, critère de force échoué, travail/IE ≈0,03390335 J ; ne pas assimiler l’énergie tangentielle à une dissipation calibrée.

ENG conserve max KE/IE=2.12247 % >1 %, CTOA B/C jusqu’à 10.7926 % aux premières observations d’un même niveau d’avance. TRUE_TOTAL n’atteint que 2,54 mm parmi les avances2,54/5,08/7,62 ; les deux absences restent non évaluées. Kn56000/Kt21500 N/mm³, Gf30 hypothétique, deux conventions séparées, QEPH explicite et aire initiale fixe. Source et propagation physique non qualifiées.

## I02I-D

Analyser OFF/FX et stockage/dissipation en mixte ; pré-déclarer des témoins supplémentaires ou une lecture ciblée du code primaire TYPE8. Pré-déclarer une extension bornée vitesse/pénalité/domaine à états neufs et histoires denses avant Gf15/60. Garder comparaisons à déplacements communs et événements de fissure précisément définis ; ne pas interpoler une topologie absente. Préserver V11F/V11R et les anciens résultats. Ne pas relancer B/C pour une relecture ; réanalyse CSV uniquement dans un nouveau dossier si nécessaire.

## GitHub et contrôles

`harness/publication_cycle.json` fait autorité : après C la paire B+C est due. La publication est autorisée toutes les deux itérations ; confirmer commit distant, empreintes d’archives et CI avant d’effacer l’attente. L’authentification doit être WTC-simu2026, identité Git pseudonyme. Aucun post X autorisé. Préparation privée : outputs/github_publication/update_i02i_bc.py, réutiliser son plan sauvegardé. Ne jamais reconstruire les 23 archives A ni publier le dossier privé d’administration.

`harness/tools/Test-WtcHarness.ps1`, puis `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_sampling.py --verify` : aucun solveur. Archives/sources en lecture seule ; 896 fichiers anciens épinglés. Température imposée ≠ incendie, coupon ≠ événement réel, flexion après fracture complète non validée, Blender visualisation.
