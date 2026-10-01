# WTC 1 — V10G — clôture de la branche P0 et état des exigences

## Résultat

**PASS** pour l'audit de synthèse V10G. La branche de lecture de pages ouverte en V10E/V10F est fermée : V10F n'a documenté aucun couple exact « étage 93–99 + page ou dessin ». Les neuf documents P0 disposent d'une identité locale chaînée par manifeste et d'un audit borné de localisateurs, mais cela ne ferme aucune exigence mécanique.

- documents candidats V10B : **53** (P0 : 9, P1 : 23, P2 : 21) ;
- documents P0 locaux enregistrés : **9** ;
- exigences liées à au moins un P0 : **18** ;
- exigences sans candidat P0 : **4** (D01, T02, B01, S01) ;
- exigences fermées : **0/22** ;
- exigences encore bloquantes pour un solveur : **22/22**.

## Faits observés ou transcrits antérieurement

V10D enregistre neuf copies de travail avec taille et SHA-256. V10E enregistre 29 transcriptions bornées de pages d'index. V10F enregistre zéro localisateur exact pour les étages 93 à 99 et ferme explicitement l'expansion de contenu. V10G ne relit aucune page de dessin : il ne lit que les matrices, manifestes et portes déjà validés.

## Résultats de modèles officiels

Aucun nouveau résultat de modèle officiel n'est produit. Les références V10A restent des dépendances documentaires et ne sont pas converties en validation indépendante.

## Affirmations d'archives

Les intitulés, numéros de livres, étiquettes de tour et plages de dessins viennent du registre d'archive déjà audité. V10G ne confirme ni leur autorité de révision, ni leur statut as-built, ni leur applicabilité exacte au WTC 1 et aux étages 93–99.

## Hypothèses propres au modèle

Le lien entre une famille documentaire et une exigence est une priorité de recherche, pas une preuve que le document contient la donnée requise. Les priorités P0/P1/P2 ne sont ni des probabilités ni des niveaux d'authenticité.

## Résultats dérivés

Les neuf P0 couvrent au moins nominalement 18 exigences, mais seulement au niveau identité de contenant et localisateurs bornés. D01 exige des données de dommage liées à l'événement, T02 suit une piste séparée Book 9, B01 exige un modèle de frontières et S01 conserve zéro crédit mécanique. Ainsi, **0/22** exigence est fermée et le solveur reste interdit.

## Matrice des 22 exigences

| Exigence | Sous-système | Champ | Statut V10G | P0 liés | Blocage |
|---|---|---|---|---:|---|
| N01 | core_nodes | column_identifiers | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| N02 | all_nodes | as_built_coordinates_xyz | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 5 | OUI |
| N03 | all_nodes | floor_elevations_and_story_heights | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 3 | OUI |
| E01 | core_vertical | column_continuity | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| E02 | core_inplane | moment_subnetwork_topology | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| E03 | core_inplane | nonmoment_and_slab_topology | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 3 | OUI |
| E04 | core_elements | book5_member_schedule | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| C01 | core_connections | book6_connection_schedule | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| D01 | all_structural_elements | physical_damage_state | EVENT_DAMAGE_REQUIRES_EVENT_SPECIFIC_EVIDENCE_NOT_DESIGN_DRAWINGS | 0 | OUI |
| O01 | office_floor | generic_geometry | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 3 | OUI |
| O02 | office_floor | member_level_topology | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 2 | OUI |
| O03 | office_floor | equivalent_membrane_stiffness | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| O04 | office_floor_connections | interior_seat_behavior | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 3 | OUI |
| O05 | office_floor_connections | exterior_seat_behavior | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 4 | OUI |
| P01 | perimeter | official_floor98_load_reference | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 3 | OUI |
| P02 | perimeter | member_sections_and_vertical_topology | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 3 | OUI |
| P03 | perimeter | connections_and_damage | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 1 | OUI |
| T01 | core_office_perimeter_transfer | transfer_topology_and_compatibility | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 4 | OUI |
| T02 | hat_truss | separate_upper_transfer_path | HAT_TRUSS_REQUIRES_SEPARATE_P1_BOOK9_SOURCE_PATH | 0 | OUI |
| B01 | boundary_conditions | above_F99_and_below_F93 | TRUNCATED_MODEL_BOUNDARIES_REQUIRE_A_SEPARATE_BOUNDARY_MODEL | 0 | OUI |
| M01 | materials_and_sections | mass_stiffness_strength_and_failure | UNRESOLVED_P0_IDENTITY_AND_BOUNDED_LOCATOR_ONLY | 8 | OUI |
| S01 | stairwells | mechanical_exclusion | STAIRWELLS_REMAIN_CATEGORICAL_HYPOTHESES_WITH_ZERO_MECHANICAL_CREDIT | 0 | OUI |

## Contradictions et informations manquantes

- Une copie locale hachée ne prouve pas l'identité WTC 1, l'applicabilité aux étages 93–99, la révision gouvernante ou le statut as-built.
- Les localisateurs bornés ne fournissent ni coordonnées, ni sections, ni propriétés de matériau, ni lois de connexion.
- Les plans de conception ne peuvent pas établir seuls le dommage physique du 11 septembre 2001.
- Les conditions aux limites du modèle tronqué 93–99 restent indéfinies.
- La couche d'escaliers V9U reste catégorielle, hypothétique et sans crédit mécanique.

## Interdictions maintenues

V10G attribue zéro coordonnée as-built, section, matériau, masse, rigidité, résistance, loi de connexion, dommage ou crédit de chemin de charge. Aucun accès réseau, contact externe, lecture de l'archive source ou de `work/official_sources/`, solveur, continuation thermique ou lancement Blender n'a eu lieu. Le fichier Blender maître reste inchangé.

## Prochaine itération

V10H pourra seulement pré-déclarer hors ligne le plus petit lot exact P1/P2 maximisant la couverture marginale des exigences dépendantes de dessins, tout en maintenant D01, B01 et S01 sur des pistes de preuve séparées et T02 sur la piste Book 9. Aucun payload ou page ne devra être ouvert pendant cette pré-déclaration.
