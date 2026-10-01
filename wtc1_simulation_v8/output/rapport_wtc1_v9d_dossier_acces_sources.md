# WTC 1 — V9D : dossier d'accès aux sources manquantes

## Résultat

L'exécution documentaire de V9D est **PASS**. Le dossier de demande est complet selon les portes pré-déclarées, mais les données ne sont pas acquises. La qualification physique des matériaux reste **FAIL** et aucun calcul OpenRadioss ou impact façade n'est autorisé.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D identifie les canaux de temps, charge, déplacement d'actionneur, déformation de la zone utile et déformation côté mors utilisés lors des essais rapides.
- Les identifiants de 12 éprouvettes M26/C80 sont publiés dans les tableaux A-12 et A-14 et sont maintenant explicitement inclus dans le dossier.
- La page FOIA officielle du NIST accepte une demande écrite détaillée par courrier électronique ou postal.
- L'index technique GE identifie `GEK 50460` comme manuel d'installation CF6-80A/A2, mais l'index public ne contient pas de loi matériau ni de données de rupture.

## 2. Résultats d'un modèle officiel

V9D ne recalcule aucun résultat NIST. Les écarts V9C de C80_299 et C80_401 restent inchangés et servent uniquement à expliquer pourquoi les canaux bruts sont nécessaires.

## 3. Affirmations provenant des archives locales

Aucune affirmation nouvelle n'est tirée des archives. L'archive source n'a pas été rescannée et `work/official_sources/` est resté en lecture seule.

## 4. Hypothèses propres au modèle

- La complétude du dossier est définie par 12 identifiants uniques, 10 catégories de dossiers, cinq familles de canaux bruts et une demande explicite du statut des enregistrements absents.
- Ces critères qualifient seulement le dossier administratif ; ils ne préjugent ni de l'existence, ni de la communicabilité, ni de la qualité scientifique des fichiers demandés.

## 5. Résultats dérivés

- Identifiants d'éprouvettes inclus : **12**.
- Catégories de dossiers demandées : **10**.
- Familles de canaux demandées : **5 / 5**.
- Voie officielle documentée : **NIST FOIA Office**.
- Demande envoyée ou publiée : **non**.
- Porte documentaire : **PASS**.

| Porte | Résultat |
|---|---|
| v9c_regressions_unchanged | PASS |
| official_nist_access_route_present | PASS |
| minimum_exact_specimen_identifiers_passed | PASS |
| minimum_record_categories_passed | PASS |
| required_raw_channels_all_named | PASS |
| no_fee_commitment_passed | PASS |
| partial_release_and_record_status_passed | PASS |
| nist_request_remains_unsent | PASS |
| nist_request_remains_unpublished | PASS |
| cf6_requirement_count_is_nine | PASS |
| cf6_available_requirement_count_is_zero | PASS |
| generic_material_substitution_prohibited | PASS |
| ge_or_boeing_request_remains_unsent | PASS |
| no_cf6_source_contact_made | PASS |

### Actualisation CF6-80A2/nacelle

| Source | Classe | Carte matériau/rupture trouvée |
|---|---|---|
| GE_CF6_TECHNICAL_MANUAL_INDEX_2026_02_01 | manufacturer_manual_index | non |
| GE_CF6_ENGINE_FAMILY | manufacturer_product_page | non |
| FAA_AD_2021_26_22 | official_airworthiness_directive | non |
| NASA_CR_165212 | government_sponsored_generic_cf6_size_containment_research | non |
| NASA_19950021857 | government_sponsored_new_generation_nacelle_research | non |

- Exigences disponibles : **0 / 9**.
- Substitution par un matériau générique : **non**.

## 6. Contradictions, limites et informations manquantes

- Une voie de demande identifiée ne prouve pas que les fichiers existent encore ou qu'ils seront communicables.
- Les index publics NIST examinés ne fournissent toujours pas les canaux bruts demandés.
- `GEK 50460`, les directives FAA et les études NASA voisines ne fournissent pas une carte production CF6-80A2/Boeing 767 traçable avec courbes dynamiques, rupture et assemblages.
- Une donnée CF6-générique ou une nacelle de recherche ne peut pas remplacer le composant de production ciblé.

## Décision de porte

- Dossier local et brouillon de demande : **validés**.
- Demande extérieure : **non envoyée**.
- Données NIST brutes acquises : **non**.
- Carte matériau/rupture CF6-80A2/nacelle qualifiée : **non**.
- Éprouvette OpenRadioss, rupture et impact façade : **non autorisés et non exécutés**.
- Avion complet, tour globale, thermique et Blender : **portes fermées**.
- Aucun mécanisme explosif ou thermite n'est testé.
