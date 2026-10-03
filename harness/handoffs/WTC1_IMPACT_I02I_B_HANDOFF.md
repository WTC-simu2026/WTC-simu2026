# WTC1 : IMPACT-I02I-B terminée, prochaine IMPACT-I02I-C

Lire AGENTS.md, harness/state.json, ce fichier, puis wtc1_simulation_v8/output/impact_i02i_fixed_penalty/publication_verification.json. L'état local fait autorité ; V8H/V11H sont historiques. V11F froid et branche thermique V11R → V11S préservés. Pas de reprise thermique dans B.

## Acquis à réutiliser

12 cas neufs, deux conventions engineering/true_total, trois pas locaux 2,54/1,27/0,635 mm ; Kn=56000 et Kt=21500 N/mm³ identiques, aire initiale fixe. Options QEPH explicites Ismstr4/Ithick1/Iplas1. Gf30 hypothétique. Témoins élastiques 28/28 et contrôles 5/5 ; capteur d'arrêt réel vérifié. Réactions REACY brutes = impulsions N·ms ; forces ΔJ/Δt, travail indépendant ΣFΔu. Mors inférieur ajouté pour le bilan d'impulsion. Aucun état ancien modifié, 583 empreintes anciennes protégées.

Campagne : 175/180 contrôles de cas ; 16/24 de comparaison. Voir les échecs et non-évaluations dans summary.json. Source convention et propagation physique non qualifiées. Maxima plastiques échantillonnés, prolongement numérique constant signalé lorsqu'utilisé. Sensibilité demi-pas/durée double uniquement ENG médian.

## Suite bornée

IMPACT-I02I-C : lire les historiques sauvegardés et traiter les critères échoués / avances communes manquantes avant de choisir une nouvelle campagne. Quadrature du travail des ressorts : écart max 3.04655 %, diagnostic à borner avant de qualifier Gf comme dissipation effective. Demi-pas : 4/4 critères dans le recouvrement, inertie toujours >1 % ; durée double : angle hors seuil et inertie persistante. Comparer pénalités, domaine et échantillonnage sans dépendance au maillage ; Gf15/30/60 reste une hypothèse à explorer lorsque les contrôles le permettent. Pré-déclarer durée/coût et états neufs ; ne pas remplacer une loi sur un état déjà endommagé. Ne pas relancer B, A, I02H, V11F ou V11R pour relecture.

Cadence GitHub : voir harness/publication_cycle.json ; baseline publiée A, B compte 1/2. Après C auditée et vérifiée, publier la paire sur https://github.com/WTC-simu2026/WTC-simu2026 avec paramètres, résultats, échecs et limites. Cette autorisation est acquise ; pas de publication X autorisée.

## Chemins et vérification

wtc1_simulation_v8/data/impact_i02i_fixed_penalty_predeclaration_r3.json
wtc1_simulation_v8/output/impact_i02i_fixed_penalty/rapport_impact_i02i_fixed_penalty.md
wtc1_simulation_v8/output/impact_i02i_fixed_penalty/verification_r1/summary.json
wtc1_simulation_v8/output/impact_i02i_fixed_penalty/artifact_manifest.json
wtc1_simulation_v8/output/impact_i02i_fixed_penalty/publication_verification.json

`harness/tools/Test-WtcHarness.ps1` puis `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_fixed_penalty.py --verify` : contrôles du cache, aucun solveur lancé. Une réanalyse des CSV utilise un nouveau dossier. Préflights R1/R2 et diagnostics partiels restent conservés. Archives/sources en lecture seule ; aucun nouveau scan. 29.061 minutes pour les 12 cas.

Température imposée ≠ incendie ; flexion après fracture complète non validée ; éprouvette générique ≠ événement réel ; Blender reste visualisation.
