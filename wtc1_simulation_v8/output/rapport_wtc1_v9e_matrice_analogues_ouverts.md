# WTC 1 — V9E, matrice de données analogues ouvertes

## Conclusion courte

V9E est une itération documentaire validée. Elle confirme que des données et essais analogues ouverts peuvent soutenir une prochaine vérification de **méthode** à petite échelle. Elle ne trouve aucune source de niveau A réunissant le matériau/composant exact, le régime d'impact pertinent et des enregistrements numériques traçables. La simulation physique de l'impact du Boeing 767/CF6-80A2 sur la façade reste donc bloquée.

## 1. Faits directement observés ou transcrits

- Le DOJ indique qu'une personne non américaine peut déposer une demande FOIA; la citoyenneté américaine n'est pas une condition de recevabilité.
- Le manuel GEK 50460, le bulletin GE CF6-80A 72-0869 R03 et les familles Boeing AMM/IPC/SRM/service bulletins ont des identifiants et des voies légales d'accès.
- Aucun de ces accès propriétaires n'a été sollicité et aucune donnée propriétaire n'a été acquise.
- 13 sources analogues publiques ont été classées.
- Niveau A: 0 source(s)
- Niveau B: 6 source(s)
- Niveau C: 5 source(s)
- Niveau D: 2 source(s)
- 4 sources annoncent des fichiers lisibles par machine; 1 fournit publiquement un modèle éléments finis.
- Le jeu Zenodo S355 contient un petit classeur d'inventaire et un complément d'environ 955 Mo; ce complément n'a pas été téléchargé.

## 2. Résultats de modèles officiels ou publics

- Le rapport FAA générique de perte d'aube compare un modèle de ventilateur complet à des essais de confinement, mais il ne représente pas un CF6-80A2 installé.
- Les rapports NASA de confinement comparent des calculs transitoires à des impacts de projectiles ou d'aubes sur panneaux et tissus génériques.
- Le rapport Fokker F28 et le modèle ouvert EMST fournissent des méthodes de construction et de vérification de modèles d'aéronefs, dans des régimes différents de l'impact WTC.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source n'a pas été rescannée.

## 4. Hypothèses propres à V9E

- Les niveaux A à D mesurent la proximité documentaire et physique; ils ne sont ni des probabilités ni des coefficients de confiance sur l'événement réel.
- Une source B, C ou D peut vérifier une chaîne numérique limitée mais ne peut pas remplacer les propriétés exactes WTC/CF6.

## 5. Résultats dérivés

- Tous les contrôles documentaires V9E passent: True.
- Sources exactes de niveau A acquises: 0.
- La prochaine étape peut ingérer un petit jeu ouvert et tester la réduction des signaux/lois de matériau comme exercice analogue explicitement non-WTC.
- Le coupon WTC, la rupture du projectile, l'impact façade, l'aéronef complet, la tour globale, le thermique et Blender comme validation physique restent interdits.

## 6. Contradictions et informations manquantes

- Le rapport FDOT annonce une plage maximale de 500 s⁻¹ tandis que l'abstract de l'article compagnon annonce 250 s⁻¹; cette différence devra être résolue avant tout ajustement quantitatif.
- Le jeu S355 SHPB concerne surtout le cisaillement localisé d'éprouvettes entaillées, pas la traction uniaxiale WTC.
- Les données brutes NIST M26/C80 à température ambiante et grande vitesse restent absentes.
- Les matériaux, assemblages, joints et lois de rupture du CF6-80A2 et de la nacelle Boeing 767 restent à 0/9 exigences.
- Aucun modèle ouvert trouvé ne réunit la géométrie Boeing 767-200/CF6-80A2, les matériaux de production, la rupture et un essai d'impact façade comparable.

## Matrice des sources propriétaires

- **NIST_NCSTAR_1_3D_ROOM_TEMPERATURE_HIGH_RATE_CHANNELS** — Twelve specimen identifiers and five raw channel families are defined in V9D. Voie: NIST FOIA Office; use the unsent V9D draft only after explicit authorization. Limite: The route is confirmed but record existence, retention and release status are unknown.
- **GEK_50460** — The current GE technical-manual index identifies GEK 50460 as the CF6-80A/A2 Installation Manual, revision 2 dated 1983-09-01. Voie: GE Fleet Support, as identified by the manufacturer manual index. Limite: An installation-manual identifier is not a component alloy, layup, dynamic constitutive law or fracture card.
- **GE_CF6_80A_SB_72_0869_R03** — FAA AD 2021-26-22 identifies GE CF6-80A SB 72-0869 R03 dated 2021-03-19 for specified HPT disk inspections. Voie: GE normal service-information channel; the public FAA AD remains an identifier and regulatory description. Limite: The bulletin concerns HPT disk inspection and does not supply a reusable cowling, attachment or complete impact-fracture model.
- **BOEING_767_AMM_IPC_SRM_AND_SERVICE_BULLETINS** — Boeing publicly identifies AMM, IPC, SRM and service bulletins as controlled technical-publication families in its Toolbox Library. Voie: Boeing Maintenance Performance Toolbox Library or Boeing Service Bulletin Center for authorized customers. Limite: No public tail-specific 767-200 CF6-80A2 nacelle/cowling manual, vendor mapping, joint card or failure dataset was located.
- **BOEING_DATA_AND_SERVICES_MARKETPLACE** — Boeing describes a secure catalog for authorized customers to discover, request and buy technical publications, drawings and engineering data. Voie: Boeing Data & Services Marketplace through MyBoeingFleet. Limite: A commercial access route does not establish that the requested legacy 767 records are available or licensable for this investigation.

Résumé: 5 identifiants/voies documentés, 0 jeu de données acquis, 0 contact externe.

## Sources analogues et usage autorisé

- **NIST_WTC_HIGH_TEMPERATURE_STEEL_CSV** — niveau B — usage permis: Exact-material provenance and data-schema cross-check only. Limite: Cannot identify the missing room-temperature 65-417 per second response or high-rate fracture/localization parameters.
- **FDOT_BDK75_977_31_A36_A1011** — niveau B — usage permis: Rate-law fitting, stress-strain reduction and LS-DYNA implementation benchmark. Limite: The official report describes rates through 500 per second while the companion journal abstract states through 250 per second; published curves/parameters are not the missing WTC raw channels.
- **MSU_CAVS_A572_A992_INTERMEDIATE_RATE** — niveau B — usage permis: Intermediate-rate trend and correction-method benchmark. Limite: The published range reaches 2 per second, far below the 65-417 per second WTC channels.
- **SUPSI_S355_TENSION_COMPRESSION_WIDE_RATE** — niveau B — usage permis: Cowper-Symonds and Johnson-Cook rate-law comparison benchmark. Limite: The publication record does not provide the required WTC raw channels or a production-engine material mapping.
- **ZENODO_17591440_S355_SHPB** — niveau B — usage permis: Signal-chain, shear-localization and nonlocal-regularization benchmark after a separate data-ingestion gate. Limite: The data emphasize adiabatic shear localization rather than uniaxial tensile fracture. The 955 MB supplementary archive was not downloaded in V9E.
- **ZENODO_6965147_STRUCTURAL_METALLIC_COUPONS** — niveau B — usage permis: Open coupon-data ingestion and true-stress/true-strain processing benchmark. Limite: Does not cover the target WTC high-rate regime.
- **FAA_DOT_TC_14_43_GENERIC_FAN_BLADE_OUT** — niveau C — usage permis: Released-blade contact, containment, energy-balance and post-containment method benchmark. Limite: The public report was located but no public LS-DYNA input deck or production component card was found.
- **NASA_TRANSIENT_FE_FAN_CONTAINMENT** — niveau C — usage permis: Contact and containment FE/test comparison method benchmark. Limite: Not traceable to a production CF6-80A2/Boeing 767 component.
- **NASA_METAL_FAN_CONTAINMENT_IMPACT** — niveau C — usage permis: Generic metal-panel impact and deformation benchmark. Limite: No production CF6-80A2 component mapping or public reusable input deck was identified.
- **NASA_KEVLAR_ZYLON_CONTAINMENT** — niveau C — usage permis: Fabric-containment constitutive and validation-workflow benchmark. Limite: Cannot establish the production cowling construction or its attachments.
- **NASA_CR_165212_GENERIC_CF6_SIZE** — niveau C — usage permis: Containment-concept geometry and mass sensitivity only. Limite: Size similarity is not production material or joint traceability.
- **NASA_FAA_FOKKER_F28_CRASH_MODEL** — niveau D — usage permis: Full-scale aircraft crash-model verification workflow only. Limite: Wrong aircraft, geometry, materials and velocity regime.
- **FAA_EMST_PANEL_1_OPEN_FE_MODEL** — niveau D — usage permis: Open aircraft-panel mesh, joint, file-provenance and reproducibility workflow benchmark. Limite: Not a high-speed impact validation case and not physically transferable to the WTC target.

## Interprétation

V9E validates a bounded evidence and access matrix, not WTC impact physics. Official DOJ sources confirm that non-U.S. citizenship does not bar a FOIA request, while the NIST, GE and Boeing routes remain unsent and no proprietary record is acquired. Public sources provide comparable structural-steel rate data, S355 shear-localization data, generic fan-containment experiments and open aircraft-panel workflows, but no source satisfies the exact target gate. These sources may support a separately gated analogue data-ingestion and numerical-method benchmark only. They cannot supply the missing WTC M26/C80 high-rate channels or the production CF6-80A2/Boeing 767 material, joint and fracture card, which remains 0 of 9. No solver or impact is run.
