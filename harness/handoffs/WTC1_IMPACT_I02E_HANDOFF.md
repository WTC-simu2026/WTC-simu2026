# WTC1 — passation IMPACT-I02E → IMPACT-I02F

## État vérifié

- `IMPACT-I02E` terminé et audité : 8 cas solveur R9, politique d'audit R10, 129 contrôles de cas + 13 contrôles de campagne, `PASS`.
- Modèle : caisson local peau–longerons–nervures–raidisseur de 1,97982 kg contre une colonne fermée représentative, 198,03072 m/s, fenêtre 0–0,35 ms.
- Témoins : vol libre fusionné et cohésif ; impact fusionné, non rompable, rompable, demi-pas, masse numérique /10 et maillage 6,35 mm.
- Impulsion principale : 124,6856 / 124,6892 / 124,6795 N·s pour fusionné / non rompable / rompable.
- Déplacement relatif nodal global maximal : 0,1292 / 0,1602 / 0,3158 mm.
- Aucune cellule cohésive supprimée ; la peau atteint toutefois εp équivalente maximale ≈1,218 avec rupture métallique désactivée. **Ne pas prolonger ni qualifier l'intégrité de l'aile avec cette loi.**
- Raffinement 12,7→6,35 mm : impulsion +2,054 %, travail de liaison +2,525 %, déplacement local 14,092 %. Les grandeurs locales ne sont pas convergées.
- Résidu énergétique maximal 4,467 % sous le seuil 5 %, mais trop grand pour interpréter les écarts d'impulsion <0,01 % entre lois.
- 3 × 30 états natifs exportés ; vidéo comparative 6 s sans interpolation mécanique ni amplification.

## À lire en premier

1. `AGENTS.md`
2. `harness/state.json`
3. ce fichier
4. `wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/rapport_impact_i02e.md`
5. `wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/campaign_audit_r10.json`
6. `wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/source_manifest_r10.json`

Ne pas relancer I02E : les cartes, journaux, historiques, sorties natives et audits sont sauvegardés. Les prévols R0–R8 rejetés restent conservés et sont expliqués dans le rapport.

## Livrables principaux

- Rapport : `wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/rapport_impact_i02e.md`
- Comparaisons : `wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/comparisons_r10.json`
- Audit : `wtc1_simulation_v8/output/impact_i02e_skin_stringer_zone/campaign_audit_r10.json`
- Configuration finale : `wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone_r10.json`
- Export natif : `wtc1_3d_v4/output/impact_i02e/native_export_audit_r10.json`
- Film : `wtc1_3d_v4/renders/impact_i02e/I02E_premier_contact_comparatif.mp4`
- Aperçu : `wtc1_3d_v4/renders/impact_i02e/I02E_apercu_comparatif.png`
- Audit du film : `wtc1_3d_v4/renders/impact_i02e/presentation_audit_r10.json`

## Prochaine étape IMPACT-I02F

Qualifier d'abord un **coupon borné de déchirure de tôle** avant de modifier le caisson :

1. chercher une donnée primaire exploitable pour tôle 2024-T3 mince et, séparément, un contrôle 7075 ; sinon déclarer une plage hypothétique sans la présenter comme Boeing ;
2. définir plasticité, déformation/énergie de rupture et longueur de régularisation avec unités et histoire ;
3. vérifier traction simple et entaille sur au moins deux maillages, travail externe, énergie interne/dissipée, masse et indépendance raisonnable au maillage ;
4. conserver un contrôle élasto-plastique sans rupture et ne jamais changer une propriété après dommage sans traiter l'état et l'énergie ;
5. seulement après passage des coupons, remplacer une seule zone de peau I02E, puis refaire 12,7 et 6,35 mm avec les témoins froids R9/R10.

Ne pas ajouter encore un Boeing complet, du carburant, un moteur ou une durée longue. L'auto-contact/edge contact et l'extension de façade viennent après une rupture métallique minimale crédible.

## Limites permanentes

- Ce sous-modèle ne décide pas si une aile réelle se brise, pénètre ou reste intacte.
- Une image vidéo n'identifie pas un mécanisme ; l'hypothèse holographique n'est ni requise ni testée ici.
- Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète non validée.
- Le B762 3D reste graphique ; la vidéo I02E montre des états solveur locaux, pas un avion complet.
- I01–I02D, V11F froid et V11R thermique doivent rester inchangés.
