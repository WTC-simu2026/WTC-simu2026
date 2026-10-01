# WTC 1 — V9N — Storyboard 3D illustratif

## Conclusion courte

V9N est une **spécification visuelle**, pas une simulation physique. Elle définit une présentation de 75 secondes et 11 plans. Le mouvement 3D est limité à l’approche avant contact. À `t = 0`, l’image se fige et toute la suite utilise uniquement des fiches explicatives.

Le bandeau « **VISUALISATION ILLUSTRATIVE — NON VALIDÉE PHYSIQUEMENT** » est obligatoire sur chaque plan. Aucun processus Blender n’a été lancé en V9N.

## 1. Faits directement observés ou transcrits

- Les huit fichiers de régression V8S/V9M correspondent à leurs empreintes enregistrées.
- V8S contient trois enveloppes d’entrée : basse, base et haute.
- La façade de référence est la face nord ; la largeur et la profondeur de tour gelées valent 63,1444 m.
- Les détails locaux de plaques, soudures, boulons, vitrages et assemblages restent incomplets.
- V9M maintient à `false` la qualification physique de l’impact façade, de la rupture, de la convergence avec érosion et de la réponse globale.

## 2. Résultats du modèle officiel utilisés

Les vitesses, angles, facteurs de masse et positions raffinées sont des entrées ou résultats officiels déjà transcrits dans V8S. Ils sont montrés avec leur provenance NIST. Les positions raffinées contre les dégâts de façade sont explicitement signalées comme **non indépendantes** du motif qu’elles ont servi à reproduire.

Le repère d’environ 0,25 s pour le dégagement de la queue est affiché sur une fiche de temps. Il ne déclenche aucun mouvement après contact.

## 3. Affirmations provenant de l’archive locale

Aucune nouvelle affirmation n’est introduite. L’archive source n’a été ni lue ni rescannée.

## 4. Hypothèses propres au storyboard

- Avant le contact seulement, la silhouette est rigide et se déplace à vitesse constante.
- Les couleurs, cadrages, durées et dispositions sont des choix de présentation.
- Les trois branches sont des enveloppes d’entrée, pas des probabilités de l’événement réel.
- Le photoréalisme éventuel ne devra jamais être présenté comme une précision physique.

## 5. Résultats dérivés

Les décalages avant contact sont calculés directement à partir des composantes de vitesse V8S. Exemple à `t = -0,25 s` :

| Branche | Masse (kg) | Vitesse (mph) | Pente | Distance avant façade (m) | Hauteur au-dessus du contact (m) | Repère de dégagement de queue (s, fiche seulement) |
|---|---:|---:|---:|---:|---:|---:|
| Enveloppe basse | 122206.9 | 414 | 13.6° | 44.97 | 10.88 | 0.257273 |
| Cas de base | 128638.8 | 443 | 10.6° | 48.66 | 9.11 | 0.239975 |
| Enveloppe haute | 135070.7 | 472 | 7.6° | 52.29 | 6.98 | 0.224811 |

Ces distances sont des positions géométriques avant contact. Aucune position positive après `t = 0` n’est produite.

### Découpage prévu

| Plan | Temps de présentation | Vue | Mode | Fonction |
|---|---:|---|---|---|
| S01_TITLE_AND_SCOPE | 0–5 s | CAM_DATA_CARD | `data_card` | State the visualization-only scope and permanent non-validation banner. |
| S02_PROVENANCE_MAP | 5–12 s | CAM_DATA_CARD | `data_card` | Separate official transcriptions, derived pre-contact geometry, assumptions and unknown post-contact physics. |
| S03_GEOMETRY_AND_UNCERTAINTY | 12–20 s | CAM_NORTH_ORTHO | `static_geometry_overlay` | Show tower envelope, north facade plane, floor range and incomplete local-geometry warning. |
| S04_THREE_BRANCH_APPROACH | 20–30 s | CAM_THREE_BRANCH_SPLIT | `precontact_motion` | Compare the three constant-velocity pre-contact branches at common negative event times. |
| S05_LESS_SEVERE_BRANCH | 30–36 s | CAM_SIDE_PROFILE_SCHEMATIC | `precontact_motion` | Show only the low-envelope approach geometry and stop at first contact. |
| S06_BASE_BRANCH | 36–42 s | CAM_NORTHWEST_OBLIQUE | `precontact_motion` | Show only the base approach geometry and stop at first contact. |
| S07_MORE_SEVERE_BRANCH | 42–48 s | CAM_SIDE_PROFILE_SCHEMATIC | `precontact_motion` | Show only the high-envelope approach geometry and stop at first contact. |
| S08_CONTACT_BOUNDARY | 48–54 s | CAM_NORTH_ORTHO | `frozen_contact_frame` | Freeze all branches at the first-contact plane and display the contact-stop banner. |
| S09_TIMING_SCALE_CARD | 54–61 s | CAM_DATA_CARD | `postcontact_data_card_no_motion` | Display the 0.224811–0.257273 s rigid geometric tail-clearance range as a timing scale only. |
| S10_UNQUALIFIED_PHYSICS | 61–68 s | CAM_DATA_CARD | `data_card` | List rupture, facade impulse, debris, fuel, fire and global response as unknown or unqualified. |
| S11_TWO_TRACKS_AND_CLOSE | 68–75 s | CAM_DATA_CARD | `data_card` | Separate the visualization-only track from the dormant physical-solver track. |

## 6. Contradictions et informations manquantes

Les éléments suivants restent inconnus ou physiquement non qualifiés :

- rupture du projectile, des moteurs, des ailes ou du fuselage
- force, impulsion et pression sur la façade
- endommagement des colonnes, allèges, planchers et noyau
- trajectoires de débris et dispersion du carburant
- incendie, stabilité post-impact et réponse globale de la tour

La valeur visuelle d’une scène ne résout aucun de ces manques. En particulier, aucun avion intact ne doit être animé au-delà du plan de contact nord.

## Règles de réalisation pour V9O

- Créer un nouveau fichier Blender ; ne pas modifier le master existant.
- Désactiver toute dynamique de corps rigide, collision, fracture, particules, carburant, feu ou structure.
- Animer uniquement les positions à temps négatif puis figer à `t = 0`.
- Remplacer les temps post-contact par des fiches graphiques.
- Afficher le bandeau de non-validation sur chaque image.
- Produire d’abord une planche-contact basse résolution, pas une animation finale coûteuse.

## Décision

La spécification est complète et contrôlée : 11 plans, 5 vues définies, 8 éléments de provenance et zéro plan de mouvement post-contact. La voie physique demeure dormante.
