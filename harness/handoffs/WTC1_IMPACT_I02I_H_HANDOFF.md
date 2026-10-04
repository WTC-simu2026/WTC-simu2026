# Passation WTC1 — H terminée, I suivante

Lire AGENTS.md, harness/state.json (prioritaire), ce fichier et data/impact_i02i_i_plan_from_h.json. Vérifier le harnais avant/après. G reste réutilisée, aucune archive rescannée ni ancien solveur relancé.

H : quatre états neufs, 12 jobs, 4.643 s ; 122/122 critères de cas, 14/14 comparaisons et 9/9 contrôles de référence. Élastique libre à 25/12,5 ns : impulsion brute 0,579655/0,289821 %, tous champs bruts ≤1 %. Les huit anciens diagnostics G échoués restent conservés.

Témoin neuf de séparation normale libre TYPE8 dans cette série I02I : Y libre, m mobile 0,1 g, v0=30 mm/ms, Kn=56000 N/mm, pic495 N, aire1 mm², Gf30 hypothétique ; E0=0,045 J, Wséparation≈0,03 J, KE finale≈0,015 J. Référence propre vérifiée par quadrature et équations avant déclaration du moteur : tf=0,00561201925604 ms, vf=√300≈17,320508 mm/ms. Cas 50/25 ns : OFF0,00565/0,005625 ms, vf17,32244/17,32142, résidu impulsion0,412173/0,206106 %, bilan énergie0,001698/0,000429 %. Après OFF : forces nulles, mouvement libre calculé, momentum constant. Ce témoin ne calibre pas la fracture physique ni le mode mixte.

I : états neufs d'arrêt/retour sans séparation ; proposition énergie0,02 J/v0Y20 mm/ms dans l'adoucissement et retour sous pic0,001 J. Dériver puis vérifier référence de décharge H2 avec maximum historique, temps de retournement/force nulle et bilans. Vérifier la fenêtre de gap positif, arrêter avant compression. Pré-déclarer critères bruts1 %, énergie/travail0,5 %, pas/couverture et budget90 s/cas600 s total. Ne jamais modifier une propriété sur état endommagé.

Sorties : wtc1_simulation_v8/output/impact_i02i_free_fracture/rapport_impact_i02i_free_fracture.md et verification_r1/summary.json ; référence reference_verification.json, audits elastic_verification_r1 et fracture_verification_r1. 1765 anciens fichiers épinglés. Vérification sans moteur : complete_impact_i02i_free_fracture.py verify.

Conserver les cinq échecs OFF/FX F, REACX/REACY et centrage exact non établis, toutes sensibilités et couvertures E, deux conventions NASA, Gf15/60 différés. Aucun transfert vers avion/façade ou Blender dynamique ; flexion post-fracture non validée, température imposée ≠ incendie, effondrement non validé. V11F/V11R/V11S conservés.

GitHub : F+G publiée/vérifiée, H seule pending1/2 ; publier H+I après I vérifiée selon harness/publication_cycle.json. Aucun post X.
