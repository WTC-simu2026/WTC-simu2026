# WTC1 : IMPACT-I02I-A terminée, prochaine IMPACT-I02I-B

Lire AGENTS.md puis harness/state.json, ce fichier et la publication_verification.json indiquée ci-dessous. L'état local fait autorité. V8H/V11H sont historiques ; branche thermique préservée V11R → V11S, contrôle froid V11F inchangé. Pas de reprise du feu ici.

## Acquis bornés à réutiliser

- Dix tractions neuves homogènes d'une coque QEPH ; 7 variantes explicites, 145/145 critères pass ; 193/203 avec les trois témoins rejetés. Campagne 8/8. Quatre contrôles analytiques de référence passent. Pas de fracture, avion ou façade.
- Options explicites vérifiées : Ishell=24, Ismstr=4, Ithick=1, Iplas=1, cinq points en épaisseur. Déformation vraie, contraction/épaisseur variables. Ce groupe d'options est qualifié uniquement pour la traction homogène testée ; les contributions individuelles des options ne sont pas isolées.
- Erreur σ max 0,028203 % ; énergie globale 0,002790 % ; travail intérieur 0,00007141 % ; travail indépendant des appuis 0,213157 % (cycle élastique à faible énergie). Demi-pas σ 0,002576 % ; durée double 0,012267 %.
- ENG_LEGACY hérite des champs I02H : σ finale 548,560 vs 569,560 MPa ; p 0,119519 vs 0,140443. Bilan énergétique fermé mais réponse constitutive non qualifiée. Préserver I02H, ne pas le promouvoir.
- Convention NASA toujours indéterminée. Hypothèses nominale et vraie totale testées séparément ; à 10 % nominal, σ=516,998 / 466,934 MPa. Ne choisir aucune branche par ressemblance au comparateur. Décimales .015/.04 du jeu retenues, différence MPa/psi ouverte.
- Les REAC bruts de ces CSV sans TH/TITLE sont des impulsions N·ms. Force d'intervalle = ΔJ/Δt ; travail = Σ(ΔJ/Δt)·Δu, bilans vérifiés indépendamment. L'impulsion double avec la durée. Ne pas appliquer aveuglément cette correction à tout canal/type d'élément : vérifier chaque sortie.

## Prochaine IMPACT-I02I-B

1. États entièrement neufs, options explicites et deux interprétations séparées. Ne changer ni E ni la loi dans un état endommagé.
2. Fixer Kn/Kt par unité d'aire indépendamment de h et du matériau ; trois maillages locaux + témoin sans propagation. Pré-déclarer domaines communs de déplacement/avance, critères d'énergie/inertie, fréquence de sortie et arrêt à la frontière raffinée.
3. Comparer forces, travail et CTOA à déplacement/avance communs, puis pas/vitesse au-delà du premier seuil. Gf15/30/60 restent des sensibilités, aucune calibration cachée.
4. Déclarer le coût avant une campagne longue. Pas de transfert physique à l'avion/façade tant que matériau et propagation restent non qualifiés.

## Chemins et contrôle rapide

Dossier : wtc1_simulation_v8/output/impact_i02i_material/.
Rapport : rapport_impact_i02i_material.md. Audit final : verification_r4/summary_i02i_material.json ; historiques/forces d'intervalle sous verification_r4/<cas>/ ; source_manifest.json ; artifact_manifest.json ; publication_verification.json.
Configuration : wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json.
Scripts : run_impact_i02i_material.py, audit_impact_i02i_material.py, test_impact_i02i_material.py, complete_impact_i02i_material.py.

```powershell
./harness/tools/Test-WtcHarness.ps1
$env:PYTHONDONTWRITEBYTECODE='1'
& C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_material.py --verify
```

333 anciens fichiers ciblés conservés, aucune relance I02H/V11F/V11R. Préflights R1/R2 rejetés et diagnostics d'audit conservés ; R3 accepté, audit R4 publié. Solveur/conversion : 18,475445 s. Archives/sources en lecture seule. Température imposée ≠ incendie calculé ; flexion/localisation après fracture complète non validées ; tests numériques ≠ événement réel ; Blender reste visualisation.
