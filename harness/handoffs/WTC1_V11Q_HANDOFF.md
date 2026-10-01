# WTC1 — passation V11Q vers V11R

Lire `AGENTS.md`, `harness/state.json`, puis cette passation ; l’état local prévaut. Contrôle `harness/tools/Test-WtcHarness.ps1` avant/après les modifications importantes. Sources et anciennes itérations en lecture seule ; pas de relance des anciens pilotes complets.

## État vérifié

V11Q terminée : **7406/7406 contrôles, 22463/22463 audits**, 14 chemins, 7357 états engagés et 7 premiers essais refusés. L’audit réintègre indépendamment 7364 états par quadrature de Gauss, sans importer le noyau de section testé. Production 3,69 s, Python 3.14.3, NumPy 2.4.6, graine 11017 sans tirage. Sorties : `wtc1_simulation_v8/output/v11q_nodal_section/`, 11 fichiers identiques à `tmp/v11q_nodal_section/attempt_001`.

Empreinte numérique : `abf5abadec18870d15d1c701aed4a07dbe887da9a5f639000f27fb3567d82404`.

## Ce qui a été fait

Transfert **direct** des sept profils nodaux V11P vers la section continue V11O : N64/128/256/512 à 640 pas ; N256 à 160/320/1280 pas. Pas de conduction relancée, pas de raccord thermique V11O, pas d’interpolation temporelle. Les températures des deux couches d’armatures sont interpolées spatialement dans les profils linéaires par morceaux.

Section symétrique 2,032 m × 0,11049 m, fraction d’armatures 0,002. Béton E=2500 ksi, alpha=1e-5/K, ft20=1 MPa, fc20=3 ksi ; armatures E=200 GPa, alpha=1,2e-5/K, fy=400 MPa, couches à 25 mm des faces. Propriétés constantes, non qualifiées comme loi à chaud. Pas de charge de gravité, de panneau ou d’historique endommagé dans V11Q.

Intégrales exactes `m0=mean(DeltaT)`, `m1=mean((y/h)*DeltaT)`, `m2=mean(DeltaT²)` ; section plane `eps=eps0-y*kappa`. Libre : `q=K^-1*f` ; entièrement empêchée : `q=0`. Résultants `R=Kq-f`, réactions conventionnelles de blocage `-R`, en N et N·m. Énergie `U=qᵀKq/2-qᵀf+S/2`, J/m. Le travail thermique incrémental `-(q_old+q_new)ᵀ*(f_new-f_old)/2+(S_new-S_old)/2` ferme l’identité énergétique à K constant ; ce n’est pas une qualification du chemin thermique entre deux pas.

Bilans de chaleur sensible du coupon homogène et du composite conservés séparément. Résidu maximal de transfert 3,49e-10 J/m² ; résidu d’énergie mécanique relatif 1,20e-15 (audit indépendant du travail : 2,26e-15). Le contrôle froid est nul ; V11F est préservé par empreintes, sans relance de son panneau. Correction de raideur de flexion continue par rapport à 160 fibres : +0,00382625 %, sans remplacer l’ancienne matrice.

## Garde-fou et résultats décisifs

Maximum des ratios traction béton/ft20, compression béton/fc20 et acier/fy20 limité à **0,9**. Tous les nœuds thermiques et les faces sont contrôlés : les contraintes sont linéaires sur chaque segment, donc leurs extrema y sont couverts. Premier essai dépassant le seuil sauvegardé séparément et **non engagé** ; arrêt du chemin, sans fissuration ni prolongement artificiel.

- Les sept chemins libres atteignent le garde-fou de **traction du béton** vers 63 s du scénario synthétique. À 640 pas, intervalle de franchissement [63 ; 63,140625] s pour les quatre maillages. À 1280 pas, [62,9296875 ; 63] s. Aucun instant exact interpolé n’est revendiqué.
- Les sept chemins entièrement empêchés restent sous le garde-fou jusqu’à 90 s. À N256/S640, ratio de compression 0,434938 ; traction nulle. Ce contraste provient des contraintes autoéquilibrées de la section libre sous gradient non linéaire, pas d’une erreur assimilant libre à zéro contrainte partout.
- Ratio maximal engagé sur l’ensemble : 0,899773599. Ces seuils froids ne valident ni résistance à chaud, ni rupture du panneau, ni chronologie réelle.

Exemples N256/S640 : libre à 63 s, eps0=1,93765556e-5, kappa=-9,75885461e-4 1/m, réactions nulles, U=6,86932481 J/m, surface haute 64,8061453 °C. Empêchée à 90 s : réaction conventionnelle [107071,378 N ; -5384,989 N·m], U=15,5158447 J/m. Écart de chaleur composite−coupon : respectivement -1903,72 et -2543,38 J/m ; ne pas le confondre avec le travail mécanique.

Raffinements comparés aux temps sauvegardés communs : **62,4375 s libre**, **90 s empêchée**. À 62,4375 s, N256→512 donne un changement relatif d’énergie libre de 0,0109591 %. Conserver les comparaisons de q, réactions, énergie, m2 et ratios ; une petite variation d’énergie ne borne pas automatiquement un instant de franchissement.

## V11R — suite limitée

Préparer l’intégration des profils nodaux sauvegardés dans un **panneau élastique borné** avec intégrales exactes, contrôle froid comparé, conventions de signes et travail vérifiés. Examiner les noyaux de panneau V11I/L/M seulement dans la mesure nécessaire, sans réexécuter leurs pilotes complets.

Pré-déclarer une fenêtre et des charges mécaniques ; vérifier d’abord la charge froide puis chaque essai avant engagement. **62,4375 s est un temps commun sûr pour ces sections sans gravité, pas une fenêtre garantie pour le panneau chargé.** La gravité, les conditions d’appui et la compatibilité peuvent atteindre le garde-fou plus tôt, voire au contrôle froid. S’arrêter et diagnostiquer si cela arrive ; ne pas abaisser la charge ou modifier les résistances après coup pour obtenir un résultat désiré.

Préserver m2 et les températures des armatures. Chaleur et travail thermoélastique restent séparés ; premier principe couplé non fermé. Pas de fissuration chaude ni changement des propriétés d’un matériau endommagé sans nouvelle formulation de son historique et de son énergie. Aucun transfert vers l’animation Blender à ce stade.

## Lecture minimale et reproduction

Configuration `wtc1_simulation_v8/data/v11q_nodal_section.json`. Pilote et audit : `wtc1_simulation_v8/scripts/run_v11q_nodal_section.py`, `audit_v11q_nodal_section.py`. Noyau de section inchangé : `v11o_startup_bridge.py`, classe `ContinuousSection` uniquement, **pas** fonction `bridge`.

Lire `results_v11q.json`, `rapport_v11q.md`, `comparisons.json`, `cold_comparison.json`, puis les états utiles de `section_paths.json`. Chaque chemin contient `history` engagée, `rejected_trial` éventuel, `last_committed_time_s` et `first_rejected_time_s`. Les profils thermiques sources restent dans V11P, référencés par job et pas.

Audit sans écriture : `python wtc1_simulation_v8/scripts/audit_v11q_nodal_section.py --output wtc1_simulation_v8/output/v11q_nodal_section --read-only`. Variables : `OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`.

## Modélisation 3D disponible — question de l’utilisateur

La maquette de référence existe : `wtc1_3d_v4/output/WTC1_V4_2_MASTER.blend` ; aperçu `wtc1_3d_v4/renders/wtc1_v4_2_structure_89_103.png`. Son README décrit 110 niveaux, 47 poteaux du noyau, 236 poteaux périphériques, et des détails accrus autour de la zone d’impact. Des sections sont représentées par des carrés d’aire équivalente ; assemblages et variations complètes de façade ne sont pas modélisés.

Une animation exploratoire V10Z existe aussi : `wtc1_3d_v4/output/WTC1_V10Z_EXPLORATORY_GRID0119.blend` et `wtc1_3d_v4/renders/v10z/wtc1_v10z_grid0119_exploratory.mp4`, 18,33 s selon sa passation. Elle illustre un ancien scénario réduit sélectionné dans une grille, sans physique Blender. Ses limites connues (initialisation de chute, inventaire de masse, état terminal, géométrie de niveaux différente du master) sont décrites dans `harness/handoffs/WTC1_V10Z_HANDOFF.md`. Des corrections V11 ultérieures ne lui ont pas été appliquées. Elle n’est pas le résultat thermomécanique actuel. Fichiers inspectés en lecture seule, aucun rendu ni Blender relancé.

## Limites permanentes

Exposition synthétique, pas incendie calculé. Pas de validation de l’effondrement réel ; localisation en flexion après fracture complète non validée. Pas de dynamique globale ni de dommage chaud ; Blender reste une visualisation et le crédit énergétique global reste nul.
