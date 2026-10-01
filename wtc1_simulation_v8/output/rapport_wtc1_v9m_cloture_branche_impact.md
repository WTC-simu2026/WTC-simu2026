# WTC 1 — V9M — Clôture de la branche impact

## Conclusion courte

V9M est validée comme synthèse en cache, sans nouvelle source, sans solveur et sans Blender. La chaîne sait exécuter des cas bornés, conserver un projectile déformable stable en vol libre et obtenir un contrôle de contact convergent lorsque l’érosion est supprimée. En revanche, la rupture physique du projectile, l’objectivité de la rupture et la convergence de l’impulsion avec érosion ne sont pas qualifiées. Une simulation physique de l’impact de l’avion sur la façade n’est donc pas autorisée.

Ce n’est pas l’échec d’un lancement logiciel : c’est une limite de validation physique liée aux données et à l’objectivité de la rupture.

## 1. Faits directement observés dans les résultats locaux

- Les huit artefacts V9L préservés correspondent à leurs empreintes SHA-256 enregistrées.
- Les douze lignes de la matrice reproduisent leurs valeurs attendues depuis les résultats V8S à V9L.
- V9M n’a lu que ces artefacts locaux déjà validés. Aucune archive source n’a été relue ou rescannée.
- Aucun accès réseau, téléchargement, contact externe, FOIA, solveur ou Blender n’a été exécuté.

## 2. Résultats de modèles officiels conservés comme comparateurs

- V8S conserve l’échelle officielle d’environ 0,25 s pour le dégagement de la queue. Son calcul réduit donne 0,239975469 s, soit 0,010024531 s d’écart.
- V8T conserve le passage du cas officiel de vérification d’installation OpenRadioss.

Ces deux comparaisons portent respectivement sur une échelle cinématique et sur l’exécution du logiciel. Elles ne valident pas l’impact physique du WTC 1.

## 3. Affirmations provenant de l’archive locale

Aucune nouvelle affirmation d’archive n’est introduite en V9M. L’archive source est restée en lecture seule et n’a pas été consultée.

## 4. Hypothèses du modèle

- Le seuil numérique de 10 % reste inchangé pour les écarts d’impulsion et de sensibilité à la longueur de rupture.
- Les catégories de la matrice distinguent un contrôle numérique, une réussite conditionnelle et une qualification physique.
- La voie physique ne peut être rouverte que si tous les déclencheurs de preuve primaire sont satisfaits ; aucune substitution générique n’est admise.

## 5. Résultats dérivés

| Groupe | Nombre |
|---|---:|
| Contrôles ou entrées qualifiés numériquement | 4 |
| Réussite numérique conditionnelle, non physique | 1 |
| Échecs de seuil ou qualifications physiques manquantes | 6 |
| Visualisation seulement | 1 |

### Matrice de qualification

| Domaine | Itération | Classement | Résultat conservé | Usage permis |
|---|---:|---|---|---|
| kinematics | V8S | `NUMERICALLY_QUALIFIED_INPUT_ENVELOPE` | The frozen base case gives 25.475462528 MN-s total momentum and a 0.239975469 s tail-clearance estimate, within 0.010024531 s of the approximately 0.25 s official scale. | Scene timing, trajectory envelope and uncertainty storyboard inputs. |
| solver_chain | V8T | `NUMERICALLY_QUALIFIED_BOUNDED_EXECUTION` | The official OpenRadioss installation smoke case and source-hash gate passed. | Confirm that a bounded Radioss deck can be launched and checked locally. |
| projectile_free_flight | V8W | `NUMERICALLY_QUALIFIED_FREE_FLIGHT` | All three free-flight meshes passed the pre-impact stability, momentum, mass and zero-erosion checks after the V8V self-contact defect was corrected. | Preserve the minimal deformable projectile's pre-contact numerical stability as a regression. |
| contact_control | V8X | `NUMERICALLY_QUALIFIED_CONTROL_ONLY` | With element erosion disabled, the diagonal contact impulse changes by 1.95062 percent from 50 to 25 mm. | Localize the dominant sensitivity to the unregularized deletion law rather than to basic contact execution alone. |
| eroding_impulse_convergence | V8U | `FAILED_NUMERICAL_GATE` | The rigid-sphere surrogate executes, but its 50-to-25 mm impulse difference is 20.9001 percent and fails the fixed 10 percent gate. | Immutable regression and execution diagnostic. |
| eroding_impulse_convergence | V8W | `FAILED_NUMERICAL_GATE` | After free-flight stabilization, the deformable eroding case still has a 32.8659 percent 50-to-25 mm impulse difference. | Diagnose the remaining post-contact mesh sensitivity. |
| conditional_regularized_rupture | V8Y | `CONDITIONAL_NUMERICAL_PASS_PHYSICALLY_UNQUALIFIED` | The 50-to-25 mm impulse difference falls to 8.3414 percent with LeMAX=100 mm, while the 100-to-50 mm step remains 33.4297 percent and the length is not measured. | Show that a regularized deletion formulation can improve one tested numerical step. |
| fracture_length_objectivity | V8Z | `FAILED_PHYSICAL_OBJECTIVITY_GATE` | At fixed 50 mm mesh, LeMAX=50, 100 and 200 mm changes facade impulse from 134.731 to 153.224 to 216.738 kN-s; the maximum difference is 37.8369 percent. | Demonstrate that fracture length or energy must be independently bounded before physical use. |
| material_and_joint_evidence | V9A | `PHYSICALLY_UNQUALIFIED_MISSING_PRIMARY_DATA` | Only 2 of 9 minimum WTC fracture-card requirements and 0 of 9 production CF6-80A2/cowling requirements are available. | Document the exact-data gap and retain published strength-rate observations as limited comparators. |
| analogue_measurement | V9J | `DESCRIPTIVE_ANALOGUE_ONLY` | Two of five documentary requirements are complete; the S355 dataset remains a no-imputation descriptive comparator without absolute bar-DIC alignment. | Method and data-quality comparator only. |
| external_impact_benchmark | V9L | `SEARCH_CLOSED_NO_QUALIFIED_BENCHMARK` | Neither the Altair rigid-sphere deck nor FAA AR-08/36 combines measured validation, deformable-projectile rupture, objective regularization, convergence and a reusable bounded deck. | Retain both sources as method comparators and stop the bounded search. |
| three_dimensional_visualization | V9M | `VISUALIZATION_ONLY_NOT_EXECUTED` | A future 3D storyboard may illustrate frozen kinematics and uncertainties, but no Blender run or physical interpretation occurs in V9M. | Illustrative scene planning with explicit uncertainty overlays and permanent non-validation labels. |

## 6. Contradictions et informations manquantes

- Le contrôle sans érosion converge à 1,95062 %, mais il retire précisément la rupture que l’on cherche à qualifier.
- Le cas V8Y passe le pas de maillage 50→25 mm à 8,3414 %, mais dépend d’une longueur LeMAX=100 mm non mesurée et garde un écart 100→50 mm de 33,4297 %.
- La sensibilité V8Z atteint 37,8369 % lorsque LeMAX varie de 50 à 200 mm.
- Seulement 2 exigences sur 9 sont disponibles pour la carte de rupture WTC, contre 0 sur 9 pour le CF6-80A2 et sa coiffe/liaisons.
- Aucun benchmark inspecté ne réunit à la fois des mesures, un projectile déformable pouvant rompre, une rupture objectivée, trois maillages convergents et un modèle réutilisable localement.
- La fermeture de la recherche bornée ne signifie pas qu’aucun benchmark adéquat n’existe ailleurs.

## Deux voies futures strictement séparées

### A — Storyboard 3D illustratif

État : **préparation permise, non exécutée**. Une future spécification pourra montrer les trois enveloppes cinématiques V8S avec des bandes d’incertitude et la mention permanente « VISUALISATION ILLUSTRATIVE — NON VALIDÉE PHYSIQUEMENT ». Elle ne devra produire ni force, ni impulsion, ni rupture, ni trajectoire de débris présentée comme prédiction.

### B — Solveur physique dormant

État : **bloqué en attente de nouvelles preuves primaires**. Conditions cumulatives de réouverture :

- [ ] **exact_wtc_facade_material_and_joint_data** — Traceable impact-zone plate, weld, bolt, window and floor-attachment definitions with relevant rate and failure data.
- [ ] **production_cf6_80a2_material_and_attachment_data** — Traceable CF6-80A2 core, cowling and attachment material/failure definitions at relevant rates.
- [ ] **objective_fracture_energy_or_length** — A physical fracture-energy or internal-length bound identified independently of facade impulse.
- [ ] **measured_open_deformable_projectile_benchmark** — A lawful deck or deterministic reconstruction with measured outputs, deformable-projectile rupture and an objective failure treatment.
- [ ] **three_level_convergence** — A common measured observable on three comparable meshes with medium-to-fine eroding impulse difference no greater than 10 percent and a bounded fracture-length sensitivity no greater than 10 percent.

La FOIA reste un dernier recours non envoyé. Une nouvelle recherche générale sur le web n’est pas prévue ; seule une nouvelle source primaire précisément identifiée pourra être testée contre les seuils inchangés.

## Décision et suite

La branche impact physique est gelée proprement. Les portes façade, avion complet, tour globale, thermique, explosifs et thermite restent fermées. Blender reste un outil d’illustration et non de validation physique.

La prochaine itération est **V9N** : préparer uniquement la spécification du storyboard 3D illustratif, sans exécuter Blender ni aucun solveur.
