# Passation WTC1 — V11H vers V11I

## État vérifié

- V11H est terminée et validée localement.
- Calcul : `PASS`, 27/27 contrôles, 11 cas, 323 états de référence.
- Audit indépendant des fichiers sauvegardés : `PASS`, 22/22 contrôles.
- Contrôle froid V11F : `PASS`, empreintes conformes, 132/132 contrôles et 14 cas ; aucun recalcul ni changement de sa mécanique.
- Harnais avant V11H : `PASS`, 85 entrées de registre. Exécuter de nouveau `harness/tools/Test-WtcHarness.ps1` après l'enregistrement de cette passation.
- Sortie publiée, copiée octet pour octet depuis `tmp/v11h_thermomechanical/attempt_004` : `wtc1_simulation_v8/output/v11h_thermomechanical/`.

## Ce que V11H établit

Le noyau sectionnel linéaire thermoélastique, à petites déformations et sections planes, reproduit les références fermées de dilatation uniforme libre/empêchée et de gradient linéaire libre. Il suit explicitement `eps_th=alpha*(T-T_ref)`, `eps_m=eps0-y*kappa-eps_th`, les contraintes, N/M, réactions, travail thermoélastique, travail mécanique généralisé, énergie mécanique stockée et enthalpie sensible en J/m.

Les propriétés sont constantes et génériques : température de référence 20 °C, `alpha_c=1.0e-5 K^-1`, `alpha_s=1.2e-5 K^-1`, `rho_c=2400 kg/m3`, `cp_c=900 J/(kg K)`, `rho_s=7850 kg/m3`, `cp_s=600 J/(kg K)`. E, ft, fc et fy restent les hypothèses froides V11E ; aucune propriété d'un matériau endommagé n'est changée.

Résultats de qualification pour le ruban composite symétrique `rho=0.002`, entre 20 et 120 °C :

- uniforme libre : allongement de centroïde 18,192508 mm ; contraintes internes auto-équilibrées dues à `alpha_c != alpha_s` ;
- uniforme, déplacement axial empêché : réaction 3 969,980 kN et énergie stockée 1,995767 kJ/m ;
- gradient libre 20/120 °C : `kappa=-9.087665e-3 m^-1` et flèche cinématique petites pentes 0,372571 m ;
- gradient entièrement empêché : réaction axiale 1 984,990 kN, réaction de moment -36,452156 kN·m et énergie stockée 0,664706 kJ/m ;
- résidu énergétique maximal du calcul : `1.208e-13` ; résidu des résultantes libres : `3.395e-15` ;
- demi-pas : écart maximal normalisé `3.406e-13` ; 160 vers 320 fibres : `2.858e-5` ;
- deux cycles reviennent à l'état de référence sans dissipation ; crédit énergétique global exact : 0 J.

## Limites obligatoires

- Le champ 20–120 °C est imposé. Ce n'est ni un calcul de feu, ni un calcul de transfert thermique, ni une reconstitution des températures du WTC1.
- Les propriétés thermiques sont des hypothèses génériques, non des mesures WTC. Conductivité, convection, rayonnement, flux incident, gaz et état SFRM restent nuls/non renseignés.
- V11H ne couple pas encore la température au panneau V11F. La flèche annoncée est une référence cinématique de section, pas une réponse du panneau.
- Aucune fissuration, plasticité, écrasement, fluage, adhérence, contact évolutif ou non-linéarité géométrique à chaud n'est calculé. Les rapports ft/fc/fy froids sont des écrans d'arrêt, pas des capacités à chaud.
- La localisation en flexion après fracture complète reste non validée. Aucun résultat ne valide le panneau réel, l'impact, l'incendie, l'initiation, l'arrêt ou la propagation d'un effondrement.
- Blender reste inchangé et n'a aucun crédit mécanique.

## Tentatives conservées

- `attempt_001` : arrêt avant calcul, asymétrie numérique relative négligeable de la matrice assemblée ; correction limitée à sa symétrisation analytique explicite.
- `attempt_002` : calcul terminé, arrêt à l'export CSV parce que six diagnostics n'étaient pas déclarés comme colonnes ; les colonnes ont été ajoutées.
- `attempt_003` : 25/27 contrôles ; deux faux échecs provenaient de rapports entre résidus quasi nuls. Des planchers SI explicites ont été pré-déclarés, sans modifier les tolérances relatives des réponses non nulles.
- `attempt_004` : tentative validée et publiée.

## Reprise V11I

1. Lire intégralement `AGENTS.md`, `harness/state.json` puis cette passation, et exécuter le contrôle du harnais.
2. Ne pas rescanner les archives ni relancer V11F/V11G/V11H. Vérifier leurs manifestes sauvegardés.
3. Pré-déclarer un seul panneau V11F élastique borné avec trois contrôles : `DeltaT=0`, température uniforme imposée, puis gradient dans l'épaisseur imposé.
4. Injecter les pré-déformations/courbures V11H dans les sections du panneau ; vérifier équilibre, réactions, travail des appuis et énergie, avec comparaison au contrôle froid.
5. Arrêter avant toute fissuration chauffée, dépassement d'un écran froid ou autre sortie du domaine. Ne pas modifier E/ft/fc/fy d'un matériau endommagé tant qu'une énergie libre dépendant de T et de l'historique, les forces thermodynamiques et l'irréversibilité ne sont pas formulées et testées.
6. Seulement après validation, envisager une V11J pour la loi constitutive à chaud ou un transfert thermique borné ; conserver l'absence de résultat historique prédéterminé.

## Livrables principaux

- Configuration : `wtc1_simulation_v8/data/v11h_thermomechanical_predeclaration.json`
- Noyau : `wtc1_simulation_v8/scripts/v11h_thermomechanical_model.py`
- Pilote : `wtc1_simulation_v8/scripts/run_v11h_thermomechanical.py`
- Tests : `wtc1_simulation_v8/scripts/test_v11h_thermomechanical.py`
- Audit : `wtc1_simulation_v8/scripts/audit_v11h_release.py`
- Rapport : `wtc1_simulation_v8/output/v11h_thermomechanical/rapport_v11h_thermomecanique.md`
- Résultats : `wtc1_simulation_v8/output/v11h_thermomechanical/results_v11h.json`
- Chemins complets : `wtc1_simulation_v8/output/v11h_thermomechanical/section_paths.json`
- Propriétés et formules : `wtc1_simulation_v8/output/v11h_thermomechanical/thermal_material_ledger.json`
- Bilans énergétiques : `wtc1_simulation_v8/output/v11h_thermomechanical/energy_ledger.csv`
- Contrôle V11F : `wtc1_simulation_v8/output/v11h_thermomechanical/cold_v11f_control.json`
- Manifestes : `source_manifest.json`, `offline_manifest.json`, `release_audit.json` dans le dossier V11H.

Empreinte numérique V11H : `a7a39e9a1a4f00709e390da28766c66806b81e9696a25eae1a5b82effa616f8e`.

