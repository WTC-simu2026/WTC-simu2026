# WTC 1 — V10N : ressources locales et gel du couplage

Généré le 2026-09-02T17:34:08Z. Cette itération n’exécute aucun solveur, aucun calcul GPU et aucun lancement Blender.

## Résultat principal

Le poste permet de poursuivre immédiatement la chaîne réduite : les adaptateurs, contrôles d’unités, relectures de sorties en cache et tests d’orchestration sont compatibles avec des exécutions courtes. En revanche, la présence d’un exécutable ne ferme aucun verrou physique. Le modèle d’impact WTC, les entrées FDS de l’événement, les entrées thermomécaniques et les 22 exigences mécaniques restent indisponibles ou non qualifiés.

La chaîne est désormais découpée en neuf modules et neuf interfaces explicites. V10O peut implémenter ces contrats et produire un premier contrôle intégré « aucune propagation », mais ce contrôle vérifiera le logiciel et les transferts de données — pas la réalité historique.

## Ressources observées

- Processeurs physiques/logiques : 6 cœurs / 12 fils.
- Mémoire physique : 15.916 Gio.
- Espace libre sur le volume de travail C: : 265.992 Gio.
- Candidats présents : OPENRADIOSS_STARTER_RUNTIME, OPENRADIOSS_ENGINE_RUNTIME, CALCULIX_CCX, BLENDER, FREECAD_CMD.
- Candidats absents des chemins pré-déclarés : FDS, SMOKEVIEW, LS_DYNA, ANSYS, NVIDIA_SMI.

Ces observations proviennent de l’inventaire Windows, des métadonnées de fichiers et des empreintes SHA-256. Les exécutables de calcul n’ont pas été lancés. Seul l’outil de diagnostic NVIDIA peut avoir été interrogé en lecture seule.

## Qualification réelle des outils

| Outil | Présence | Crédit autorisé | Limite déterminante |
|---|---|---|---|
| OPENRADIOSS_STARTER_RUNTIME | PRESENT | EXECUTABLE_CHAIN_AND_BASIC_SHELL_REGRESSION_ONLY | OpenRadioss is not the NIST production LS-DYNA deck and WTC high-rate material, rupture, contact, mesh and energy gates remain open. |
| OPENRADIOSS_ENGINE_RUNTIME | PRESENT | EXECUTABLE_CHAIN_AND_BASIC_SHELL_REGRESSION_ONLY | Presence does not qualify physical facade impact or aircraft breakup. |
| CALCULIX_CCX | PRESENT | FUTURE_COMPONENT_OR_QUASISTATIC_TESTS_AFTER_CASE_VALIDATION | No validated coupled high-rate or full thermomechanical WTC formulation is assigned. |
| BLENDER | PRESENT | VISUALIZATION_ONLY_NO_MECHANICAL_FEEDBACK | Blender may display only states released by validation gates. |
| FREECAD_CMD | PRESENT | GEOMETRY_PREPOST_ONLY | Geometry tooling is not a physics qualification. |
| FDS | NOT_FOUND_AT_DECLARED_PATHS | NONE_UNTIL_GENERIC_SMOKE_AND_EVENT_INPUT_VALIDATION | The exact NIST FDS event inputs and thermal interface histories are unavailable. |
| SMOKEVIEW | NOT_FOUND_AT_DECLARED_PATHS | POSTPROCESSING_ONLY_IF_FDS_OUTPUT_EXISTS | Postprocessing presence cannot substitute for an FDS model. |
| LS_DYNA | NOT_FOUND_AT_DECLARED_PATHS | NONE | Exact replay also requires the unavailable NIST TrueGrid and LS-DYNA inputs. |
| ANSYS | NOT_FOUND_AT_DECLARED_PATHS | NONE | Exact replay also requires the unavailable translated NIST ANSYS inputs and interfaces. |
| NVIDIA_SMI | NOT_FOUND_AT_DECLARED_PATHS | GPU_IDENTIFICATION_ONLY | No GPU computation is performed in V10N. |

## Chaîne gelée

| Module | État | Crédit physique actuel |
|---|---|---|
| IMPACT_KINEMATICS | READY_FOR_REPLAY_AS_KINEMATIC_ENVELOPE_ONLY | KINEMATICS_ONLY_NO_FORCE_IMPULSE_DAMAGE_OR_BREAKUP |
| IMPACT_DAMAGE_STATE | BLOCKED_FOR_PHYSICAL_PREDICTION_SCHEMA_CAN_BE_IMPLEMENTED | NONE_CURRENTLY |
| FIRE_GAS_PHASE | REDUCED_SURROGATE_ONLY_NOT_EVENT_VALIDATED | NONE_AS_EVENT_RECONSTRUCTION |
| THERMAL_SOLIDS | CACHED_SYNTHETIC_FIELDS_READY_FOR_SOFTWARE_CONTROL_ONLY | SENSITIVITY_ONLY |
| COLD_GRAVITY_REDISTRIBUTION | DIAGNOSTIC_AVAILABLE_SOURCE_GATE_FAILED | NONE_CURRENTLY; REDUCED DIAGNOSTIC ONLY |
| THERMOMECHANICAL_INITIATION | BLOCKED_PENDING_COLD_AND_THERMAL_PHYSICAL_GATES | NONE_CURRENTLY |
| PROPAGATION_OR_ARREST | SCHEMA_ONLY_SEPARATE_MODEL_REQUIRED | NONE_CURRENTLY |
| UNCERTAINTY_ENSEMBLE | READY_FOR_SYNTHETIC_SOFTWARE_CONTROLS_ONLY | ORCHESTRATION_ONLY |
| BLENDER_VISUALIZATION | READY_FOR_VALIDATED_STATE_VISUALIZATION_ONLY | VISUALIZATION_ONLY |

| Interface | Transfert | État | Implémentable en V10O |
|---|---|---|---|
| I01_KINEMATICS_TO_DAMAGE | IMPACT_KINEMATICS → IMPACT_DAMAGE_STATE | SCHEMA_FREEZABLE_PHYSICAL_DAMAGE_BLOCKED | oui |
| I02_DAMAGE_TO_FIRE | IMPACT_DAMAGE_STATE → FIRE_GAS_PHASE | SCHEMA_FREEZABLE_EVENT_INPUT_BLOCKED | oui |
| I03_DAMAGE_TO_COLD_STRUCTURE | IMPACT_DAMAGE_STATE → COLD_GRAVITY_REDISTRIBUTION | SCHEMA_FREEZABLE_PHYSICAL_COLD_GATE_BLOCKED | oui |
| I04_FIRE_TO_THERMAL_SOLIDS | FIRE_GAS_PHASE → THERMAL_SOLIDS | SCHEMA_FREEZABLE_SURROGATE_CONTROL_AVAILABLE | oui |
| I05_THERMAL_TO_INITIATION | THERMAL_SOLIDS → THERMOMECHANICAL_INITIATION | SCHEMA_FREEZABLE_PHYSICAL_INITIATION_BLOCKED | oui |
| I06_COLD_STATE_TO_INITIATION | COLD_GRAVITY_REDISTRIBUTION → THERMOMECHANICAL_INITIATION | SCHEMA_FREEZABLE_COLD_GATE_BLOCKED | oui |
| I07_INITIATION_TO_PROPAGATION | THERMOMECHANICAL_INITIATION → PROPAGATION_OR_ARREST | SCHEMA_FREEZABLE_BOTH_PHYSICS_MODULES_BLOCKED | oui |
| I08_PROPAGATION_TO_ENSEMBLE | PROPAGATION_OR_ARREST → UNCERTAINTY_ENSEMBLE | SCHEMA_FREEZABLE_SOFTWARE_CONTROL_READY | oui |
| I09_ALL_VALIDATED_STATES_TO_BLENDER | VALIDATION_RELEASE_BUS → BLENDER_VISUALIZATION | READY_FOR_RELEASED_STATES_ONLY | oui |

## Séparation des preuves

1. **Faits observés ici** : présence, taille, version déclarée et empreinte des fichiers exécutables ; caractéristiques CIM du poste ; empreintes inchangées des résultats en cache.
2. **Résultats de modèles officiels** : ils restent des entrées dépendantes lorsqu’ils sont repris par les anciens sous-modèles ; V10N ne les rend pas indépendants.
3. **Affirmations d’archives** : aucune nouvelle archive source n’est lue ou promue dans V10N.
4. **Hypothèses du modèle** : les champs thermiques synthétiques, topologies reconstruites, lois proxy et futurs scénarios d’interface restent explicitement hypothétiques.
5. **Résultats dérivés** : disponibilité de la chaîne logicielle courte, graphe de couplage et budget de calcul.
6. **Contradictions et inconnues** : modèle de dommage physique non qualifié, entrées événementielles feu/thermique absentes, 0/22 exigences mécaniques fermées, propagation non implémentée.

## Décision

- **V10O autorisée** : adaptateurs validés par schéma, contrôles d’unités/provenance, relecture des cas en cache et contrôle intégré sans propagation, pour une durée visée inférieure à 15 minutes.
- **Conclusion physique non autorisée** : V10O ne pourra pas conclure que le WTC1 devait s’effondrer ou ne pouvait pas s’effondrer.
- **Calcul long non autorisé sans annonce préalable** : aucun calcul de plusieurs heures ne sera lancé sans estimation, ressources et livrable attendus.
- **3D** : Blender reste en sortie uniquement ; aucune animation ne peut créer ou valider une dynamique absente des modules amont.

## Prochaine étape

Implement schema-validated adapters for the frozen reduced-order coupling interfaces, replay the shortest cached baseline cases, and produce the first integrated no-propagation control without launching a multi-hour solve.
