# WTC1 — I02I-F terminée, prochaine I02I-G

Lire AGENTS.md, harness/state.json, cette passation puis `wtc1_simulation_v8/output/impact_i02i_dtcap/publication_verification.json`. État local prioritaire. Rapport `wtc1_simulation_v8/output/impact_i02i_dtcap/rapport_impact_i02i_dtcap.md`, résultats `wtc1_simulation_v8/output/impact_i02i_dtcap/verification_r1/summary.json`, configuration `wtc1_simulation_v8/data/impact_i02i_dtcap_predeclaration.json`, plan G `wtc1_simulation_v8/data/impact_i02i_g_plan_from_f.json`.

F : 8 témoins neufs, 24 jobs normaux, 32.190 s ; 217/222 critères et 10/10 comparaisons. /DTIX vérifié dans TIME STEP : 200/100/50 ns, TH chaque cycle, aucune masse ajoutée. Critère strict OFF/FX échoué dans cinq cas ; retard d'un cycle conservé. IE sous cisaillement fixé reste 0,0343 J, sans restitution de 0,0043 J tangent dans KE observée. Travail non récupéré numérique, aucune dissipation mixte physique calibrée.

Cisaillement imposé après rupture : résidu impulsion X D≈14,205 % → F≈0,192454 % à 100 et 50 ns ; plateau non nul. Maximum à 1,7875 ms sur un point tabulé, momentum global compatible avec moyenne des vitesses adjacentes ; diagnostic ajouté après déclaration, pas preuve du code interne ni correction d'un critère. Les grandes impulsions opposées ont aussi une limite float32. Réutiliser `residual_plateau_diagnostic.json`, `plateau_point_inference.json` et les CSV sauvegardés.

G : trajectoires 1600/3200 subdivisions à états neufs, puis témoin élastique libre analytique avec momentum initial ; documenter les mots-clés avant solveur et déclarer les critères. Toutes les sensibilités/angles/couvertures E restent ouverts (`cached_E_sensitivity_review.json`), Gf15/60 différés, deux conventions NASA conservées. Pas de propriété remplacée sur état endommagé, aucun impact libre avec fracture qualifié.

1453 anciens fichiers épinglés, aucune archive rescannée ni ancien solveur relancé. Vérification sans solveur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_dtcap.py verify`. V11F/V11R/V11S préservés ; température imposée ≠ incendie, flexion post-fracture non validée, Blender visualisation.

Publication : cadence dans harness/publication_cycle.json ; F pending 1/2, envoi après G vérifiée. Dernière publication D+E du 3 octobre 2026 conservée. Compte/identité WTC-simu2026 ; administration privée exclue, aucun post sur X autorisé.
