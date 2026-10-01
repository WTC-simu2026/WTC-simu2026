# Passation WTC1 — V11I vers V11J

## État vérifié

- V11I est terminée et validée localement.
- Calcul : `PASS`, 32/32 contrôles, 3 parcours et 54 états de référence.
- Audit indépendant des fichiers sauvegardés, sans importer le noyau mécanique : `PASS`, 26/26 contrôles.
- Contrôles hérités : V11F `PASS` (132/132, 14 cas) et V11H `PASS` (27/27, 11 cas), avec empreintes conformes ; leurs anciens pilotes n'ont pas été relancés.
- Harnais avant enregistrement : `PASS`, 86 entrées de registre. Exécuter de nouveau `harness/tools/Test-WtcHarness.ps1` après la mise à jour de l'état et du registre.
- Sortie publiée, copiée octet pour octet depuis `tmp/v11i_thermoelastic_panel/attempt_001` : `wtc1_simulation_v8/output/v11i_thermoelastic_panel/`.

## Ce que V11I établit

V11I injecte les déformations thermiques V11H dans la dalle d'un seul panneau élastique V11F R02, à 25 % de la gravité de référence. La dalle équivalente reçoit un champ uniforme ou linéaire dans son épaisseur et constant le long de la portée ; le treillis, les sièges, les contacts et les attaches restent froids. Le calcul est réversible, à petits déplacements et propriétés constantes.

Le contrôle `DeltaT=0` reproduit le point froid V11F sauvegardé : énergie mécanique 123,542425 J, flèche de dalle 10,793292 mm, réaction verticale 35,239800 kN et DCR maximal 0,147129. La topologie reste 33 nœuds de treillis, 63 barres, 65 nœuds de dalle, 64 éléments de dalle, 128 sections de Gauss et 17 stations de contact.

Résultats terminaux :

- dalle uniforme à 120 °C : cible complète atteinte, DCR maximal 0,502247 sur l'écran élastique de traction du béton, déplacement maximal vers le haut 20,644553 mm, travail thermoélastique 2,422429 kJ, énergie mécanique stockée 1,831685 kJ et enthalpie sensible 880,334828 MJ ;
- gradient imposé : arrêt borné à l'échelle 0,082354625, soit 20/28,235 °C aux faces, juste sous DCR 0,90 sur l'écran élastique de traction du béton en face inférieure ; la tentative supérieure est seulement enregistrée comme borne et n'est pas engagée ; travail thermoélastique 61,585867 J, énergie mécanique stockée 144,146967 J et enthalpie sensible 36,249822 MJ.

Le résidu d'équilibre maximal vaut `1.924e-12`, le résidu incrémental énergétique `8.476e-9` et le résidu énergétique total recomposé `6.346e-11`. Le demi-pas passe 3/3 parcours. Le maillage de référence à 4 subdivisions comparé à 8 passe 3/3 parcours ; les écarts maximaux sont 0,293 % sur l'échelle terminale, `2.566e-11` sur les déplacements, `4.839e-7` sur les réactions et `1.139e-5` sur les énergies. Le maillage 2 est conservé comme diagnostic grossier séparé.

Les unités sont SI : déplacements en m, forces en N, moments en N·m, contraintes en Pa, énergie mécanique et travail en J par panneau, enthalpie sensible en J. Le bilan vérifié est `Delta U = W_gravite + W_thermoelastique`; l'enthalpie sensible reste séparée, les appuis fixes ont un travail nul et le crédit énergétique global est exactement 0 J.

## Limites obligatoires

- Les températures sont imposées, non calculées. V11I n'est ni un feu, ni une conduction, ni une histoire thermique du WTC1.
- Le seuil atteint par le gradient est un garde-fou numérique basé sur des propriétés et écrans froids génériques ; 28,235 °C n'est pas une température critique réelle du panneau.
- Les propriétés constantes héritées de V11H (`alpha`, `rho`, `cp`) et les E/ft/fc/fy froids hérités de V11E sont exploratoires ; le ferraillage R02 n'est pas une disposition as-built.
- Aucune fissuration chauffée, plasticité, rupture, écrasement, fluage, adhérence, suppression d'assemblage, postflambement, dynamique ou non-linéarité géométrique n'est calculé. Aucun matériau endommagé ne change de propriété ou d'historique.
- La localisation en flexion après fracture complète reste non validée. Ce panneau local ne valide ni l'impact, ni l'incendie, ni l'initiation, l'arrêt ou la propagation d'un effondrement réel.
- Blender reste inchangé et sans crédit mécanique.

## Reprise V11J

1. Lire intégralement `AGENTS.md`, `harness/state.json` puis cette passation, et exécuter le contrôle du harnais.
2. Ne pas rescanner l'archive ni relancer V11F/V11H/V11I ; vérifier les manifestes sauvegardés.
3. Pré-déclarer un coupon unidimensionnel de conduction transitoire dans l'épaisseur de la dalle équivalente, avec propriétés constantes et conditions aux limites synthétiques clairement étiquetées.
4. Vérifier d'abord des références analytiques simples, puis le bilan flux entrant moins flux sortant égale variation d'enthalpie, la conservation et le raffinement espace-temps.
5. Conserver l'histoire thermique du coupon séparée du panneau V11I jusqu'à qualification. Aucun flux ou scénario ne doit être attribué à un incendie WTC sans conditions aux limites primaires sourcées.
6. Ne pas activer de fissuration chaude ni modifier une propriété endommagée. Une future loi devra expliciter énergie libre dépendant de la température et de l'historique, forces thermodynamiques, dissipation et irréversibilité.

## Livrables principaux

- Configuration : `wtc1_simulation_v8/data/v11i_thermoelastic_panel_predeclaration.json`
- Noyau : `wtc1_simulation_v8/scripts/v11i_thermoelastic_panel_model.py`
- Pilote : `wtc1_simulation_v8/scripts/run_v11i_thermoelastic_panel.py`
- Tests : `wtc1_simulation_v8/scripts/test_v11i_thermoelastic_panel.py`
- Audit : `wtc1_simulation_v8/scripts/audit_v11i_release.py`
- Rapport : `wtc1_simulation_v8/output/v11i_thermoelastic_panel/rapport_v11i_panneau_thermoelastique.md`
- Résultats : `wtc1_simulation_v8/output/v11i_thermoelastic_panel/results_v11i.json`
- Parcours et états : `panel_paths.json`, `path_history.csv`, `panel_section_states.csv`, `critical_fiber_states.csv`, `connection_forces.csv`, `slab_nodes.csv` dans le dossier V11I.
- Bilans et sensibilités : `energy_ledger.csv`, `discretization_comparison.json`, `mesh_runs.json`, `half_step_paths.json`.
- Contrôles et manifestes : `cold_and_thermoelastic_controls.json`, `material_and_scope_ledger.json`, `source_manifest.json`, `offline_manifest.json`, `release_audit.json`.

Empreinte numérique V11I : `f44bf662b31a9d9058125f6fdb7935a28fe8a1a6c30b4f014f0e6df3cbebfa53`.
