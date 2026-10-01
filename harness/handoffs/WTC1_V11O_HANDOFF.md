# WTC1 — passation V11O vers V11P

Lire `AGENTS.md`, `harness/state.json`, puis cette passation. L’état local prévaut sur les anciennes reprises. Contrôle `harness/tools/Test-WtcHarness.ps1` avant/après les modifications importantes. Sources, anciens résultats et historiques endommagés en lecture seule.

## Conclusion prioritaire

**Ne pas intégrer le raccord V11O au panneau comme une conduction validée.** Le raccord mécanique peut tendre proprement vers le froid en énergie et en charges, mais son profil reconstruit ne respecte pas le flux thermique : à 256 cellules et fraction 1/65536 du premier pas, il donne environ **502 162 933 W/m²**, contre **8 377,504 W/m²** dans le flux sauvegardé interpolé. C’est un artefact de reconstruction, pas un flux physique établi.

La suite V11P est donc réorientée vers un démarrage thermique cohérent **avant** l’intégration au panneau. L’état local porte `thermal_compatibility_status=NOT_QUALIFIED_FLUX_MISMATCH` et `panel_integration_ready=false`.

## V11O achevée comme vérification bornée

Sorties : `wtc1_simulation_v8/output/v11o_startup_bridge/`. 13 fichiers identiques à `tmp/v11o_startup_bridge/attempt_005`, audit final relu : **41/41 contrôles et 517/517 audits**. Ce PASS concerne les identités, diagnostics et limites déclarés ; il ne valide pas thermiquement le raccord.

- 12 chemins de section, 180 états ; trois sources V11M (64/128/256 cellules), deux raccords, section libre ou entièrement empêchée.
- Premier intervalle sauvegardé uniquement : 0 à 0,140625 s. Fractions 0, 1/65536, 1/4096, 1/256, 1/16, 1/4, 1/2, 1, puis retour synthétique. Les fractions sont des **coordonnées d’interpolation**, pas de nouveaux instants thermiques résolus.
- Contrôle froid V11F et sources V11M/N préservés par empreintes. Aucun ancien pilote complet ni solveur de conduction relancé. Pas de nouveau panneau chargé ou garde-fou global.
- Empreinte numérique : `10d40f93a60f94433f684f55ce8468fedf9a22ff6c4463369982e66b0a7db9a9`.

## Ce qui est qualifié mécaniquement

Le raccord principal conserve les moyennes de cellules et les faces interpolées. À fraction positive il utilise la reconstruction V11N. À zéro, le volume est froid presque partout, tandis que les températures positives de face sont conservées comme sondes de mesure volumique nulle : le champ initial est discontinu et le rejet de reconstruction continue de V11N reste correct. Un témoin proportionnel au premier profil conserve la chaleur, mais pas les températures intermédiaires de face ; il reste un témoin, pas une alternative validée.

La section utilise les intégrales exactes du béton continu et des armatures discrètes :

- `m0=mean(DeltaT)`, `m1=mean((y/h)*DeltaT)`, **`m2=mean(DeltaT²)`** ;
- `f=int(E*alpha*DeltaT*B*dA)`, `S=int(E*alpha²*DeltaT²*dA)`, `B=(1,-y)` ;
- `U=qᵀKq/2-qᵀf+S/2`, `R=Kq-f` ;
- `DeltaWth=-(q_old+q_new)ᵀ*(f_new-f_old)/2+(S_new-S_old)/2` ; `DeltaWext=(R_old+R_new)ᵀ*(q_new-q_old)/2`.

Pour un champ positif borné : `|m1|<=m0/2`, `m2<=Tmax*m0`. Quand la chaleur tend vers zéro, les charges, réactions empêchées, déformations libres et énergies tendent vers le froid ; les contraintes ponctuelles de face ne sont pas nécessairement nulles. Les cycles synthétiques ferment leurs bilans, sans représenter un refroidissement calculé. Ratio maximal aux résistances froides, faces incluses : **0,061617**, sous le garde-fou 0,9.

Résidus maximaux : moyenne 2,29e-16 K ; chaleur 5,17e-11 J/m² ; énergie mécanique relative 2,71e-19. À 256 cellules et fraction 1/65536, section empêchée : énergie du raccord faible 6,8554e-9 J/m, témoin proportionnel 2,3421e-13 J/m, malgré des états finaux identiques.

## Deux conséquences pour le futur transfert

1. **Moyenne et gradient ne suffisent pas à déterminer l’énergie.** Parmi 126 diagnostics de projection, 28 sont rejetés. Même une projection positive supportée sur 640 fibres peut manquer la couche très fine : à 256 cellules et fraction 1/65536, le rapport `mean(Tproj²)/mean(Tcontinu²)` vaut seulement 3,37e-5 ; au premier état sauvegardé complet, 0,879682. Ces projections ne sont pas engagées dans la section V11O. Préserver aussi l’intégrale du carré de la température lors du futur couplage.
2. L’intégration continue retire l’erreur d’inertie des fibres au milieu des bandes : `DeltaK22=Ec*Ac*h²/(12*n²)`. Par rapport à 160 fibres, changement relatif de raideur de flexion environ **0,003826 %**. Anciennes raideurs et histoires inchangées ; le futur panneau devra comparer explicitement son contrôle froid, pas présumer une identité bit à bit avec V11F.

## V11P — prochaine étape

Tester une formulation thermique où la température de surface évolue avec le solide, par exemple un maillage nodal avec **demi-volumes de contrôle aux faces**, à épaisseur, masse et capacité thermique totales inchangées. Aucun ajout de chaleur ou de masse fictive. Vérifier l’état initial, les flux de convection/rayonnement, l’enthalpie, les bilans par pas et les raffinements, puis comparer aux résultats V11M déjà sauvegardés. Ces nouveaux calculs seraient justifiés par le changement de formulation, pas une répétition des anciens pilotes.

Conserver les intégrales exactes V11O comme outil de transfert mécanique futur. N’intégrer au panneau qu’après cette qualification, avec contrôles froids, réactions, énergie et garde-fou. Pas de fissuration chaude à ce stade.

## Fichiers et tentatives

Configuration : `wtc1_simulation_v8/data/v11o_startup_bridge.json`. Scripts dans `wtc1_simulation_v8/scripts/` : `v11o_startup_bridge.py`, `run_v11o_startup_bridge.py`, `audit_v11o_startup_bridge.py`.

Lire d’abord `results_v11o.json`, `rapport_v11o.md`, `flux_mismatch_diagnostics.json`, puis `projection_square_diagnostics.json`, `startup_paths.json`, `section_inventory.json`, `stiffness_comparison.json`. Audit sans écriture : `python wtc1_simulation_v8/scripts/audit_v11o_startup_bridge.py --output wtc1_simulation_v8/output/v11o_startup_bridge --read-only`. Paramètres d’exécution : `OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`.

Tentatives conservées : 001 erreur de conversion liste/tableau avant résultats ; 002 contrôles du petit déficit de raideur trop sensibles à la soustraction de matrices proches ; 003 vérification de l’identité sur l’échelle de K, 40 contrôles/517 audits ; 004 assemblage explicitement symétrique avec sommes compensées, 41/517 ; 005 mêmes résultats numériques que 004, qualification thermique négative et prochaine étape rendues explicites. Entrées des tentatives antérieures figées dans `input_snapshot/`. Production finale environ 0,64 s CPU.

## Limites permanentes

Exposition synthétique non WTC. Pas d’incendie calculé, de premier principe thermo-mécanique couplé fermé, de dommage chaud, de dynamique globale ni d’effondrement validé. Écart de chaleur sensible du composite déclaré séparément. Localisation en flexion après fracture complète non validée. Blender inchangé, visualisation seulement ; crédit énergétique global nul.
