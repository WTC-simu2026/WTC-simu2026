# Passation WTC1 — G terminée, H suivante

Lire AGENTS.md puis harness/state.json (prioritaire), ce fichier et data/impact_i02i_h_plan_from_g.json. Contrôle du harnais avant/après ; aucune archive rescannée ni ancien solveur relancé.

G : six états neufs, 18 jobs, 30.114 s, 162/162 critères et 8/8 comparaisons. Résidu X après rupture imposée : F N800 0,192454 % → N1600 0,0962401 % → N3200 0,0481333 %, identique aux caps 100/50 ns ; soutient l'origine tabulée sans établir le code interne. IE finale 0,03 J, forces X post-OFF nulles.

Oscillateur libre élastique sans fracture, m mobile 0,1 g, k=21500 N/mm, v0=1 mm/ms, T=0,0135506659245 ms, E0=0,00005 J, P0=0,1 N ms ; huit périodes. u erreur 0,450436/0,112566 %, bilan énergie 0,0537857/0,0134491 %, à 100/50 ns. Impulsion brute/nodal/global encore 2,319/1,159 % : succès au seuil déclaré 3 %, huit diagnostics stricts 1 % échoués conservés, aucun déphasage corrigé. TH/REACX documentation force vs runtime impulsion toujours contradictoire.

H : pré-déclarer d'abord mêmes témoins neufs à 25 et 12,5 ns, tous champs bruts au seuil 1 %, momentum initial inclus. Si succès, dériver/vérifier référence pièce par pièce d'un témoin neuf de rupture normale libre (m=0,1 g, v0Y=30 mm/ms, E0=0,045 J, travail normal hypothétique 0,03 J, v finale idéale √300 mm/ms), puis seulement déclarer calcul borné. Pas de cisaillement stocké ni de changement de propriété sur état endommagé. Conserver les anciens contrôles et échecs F ; G ne ferme pas les sensibilités/couvertures E ou les deux conventions NASA. Gf15/60 différés.

Rapport/results : wtc1_simulation_v8/output/impact_i02i_table_free/rapport_impact_i02i_table_free.md et verification_r1/summary.json ; 1632 anciens fichiers épinglés. Vérification sans solveur : complete_impact_i02i_table_free.py verify. V11F/V11R/V11S conservés. Boeing complet/feu/effondrement non validés ; flexion post-fracture non validée ; température imposée ≠ incendie ; Blender visualisation.

GitHub : F+G pending 2/2 avant confirmation distante, cadence réelle dans harness/publication_cycle.json. Dernière release E conservée. Après confirmation F+G, H sera 1/2 ; auteur WTC-simu2026 et administration privée exclue. Aucun envoi X autorisé.
