# WTC1 — passation IMPACT-I02F → IMPACT-I02G

## État vérifié

- `IMPACT-I02F` terminé : 15 cellules de bande R3, audit final R5, 281 contrôles de cas + 24 contrôles de campagne, `PASS`.
- Deux témoins 2024-T3 sans rupture sont conservés. Les bandes 2024 utilisent `Gf = 15/30/60 N/mm` (hypothèses) ; le contrôle 7075 utilise `30,007/44,069/54,520 N/mm`, équivalents élastiques dérivés de `Kc²/E`, pas des énergies ductiles mesurées.
- Mailles 4/2 mm : écart maximal force de plateau 0,636 %, travail plastique 1,392 %, travail total à suppression 9,942 %. Erreur maximale travail plastique/cible 3,188 %. Demi-pas : écart maximal 0,00123 %.
- Une seule zone I02E 6,35 mm a ensuite reçu le cas central `Gf = 30 N/mm`, en conservant la carte de plasticité I02E (`Rp = 310,264 MPa`) et son historique.
- Dans cette zone : première érosion peau 0,226032 ms ; 336/3072 coques de peau supprimées (10,9375 %, 95,668 g) ; liaison cohésive intacte ; impulsion 107,8992 N·s, soit -15,236 % face au témoin I02E identique sans rupture métal.
- Résidu énergétique maximal de zone 4,856 % sous le portail 5 %, mais trop proche de la limite pour étendre le modèle.

## À lire en premier

1. `AGENTS.md`
2. `harness/state.json`
3. ce fichier
4. `wtc1_simulation_v8/output/impact_i02f_tear_coupon/rapport_impact_i02f_r1.md`
5. `wtc1_simulation_v8/output/impact_i02f_tear_coupon/campaign_audit_r5.json`
6. `wtc1_simulation_v8/output/impact_i02f_tear_coupon/ZONE_AA2024_G30_H0635_R0/zone_audit_r0.json`

Ne pas relancer I02F : entrées, cartes, journaux, historiques, sorties et audits sont sauvegardés. R0–R2 et les audits R3/R4 rejetés restent conservés.

## Sources primaires locales en lecture seule

- `wtc1_simulation_v8/input/impact_i02f_sources/NASA_CR_191523_2024T3_CTOA.pdf`
- `wtc1_simulation_v8/input/impact_i02f_sources/NASA_19990028733_wide_stiffened_panels.pdf`
- `wtc1_simulation_v8/input/impact_i02f_sources/NASA_19730023698_7075T6_fracture.pdf`
- `NASA_19740003601_2024T3_1p02mm_fracture.pdf` est conservé mais non sélectionné : compilation générale ne correspondant pas à la description du résultat de recherche.

## Prochaine étape IMPACT-I02G

Construire une éprouvette 2024-T3 M(T) entaillée d'après NASA CR-191523 avant tout second transfert dans l'aile :

1. géométrie 76,2 × 300 × 2,3 mm et fissure totale initiale 25,4 mm ; chargement en déplacement, orientation L-T ;
2. au moins deux maillages et deux orientations de maille, contrôle sans propagation, réactions, travail externe, énergie interne/plastique et masse ;
3. mesurer extension, charge distante et CTOA à partir des états solveur ; comparer seulement aux domaines publiés (début stable vers 200/230 MPa, CTOA final voisin de 6°), sans ajustement caché ;
4. tester `/FAIL/TAB2` ou une formulation de fissure explicite plus appropriée ; documenter comment `Gf`, triaxialité, Lode et longueur caractéristique sont identifiés ou restent hypothétiques ;
5. resserrer le résidu énergétique avant une sensibilité 12,7/6,35 mm dans la zone I02E.

## Limites permanentes

- La cellule I02F vérifie une objectivité numérique de travail dans une bande prescrite ; elle ne reproduit pas l'initiation, le tunneling ou le CTOA d'une fissure réelle.
- Le transfert local emploie une longueur nominale unique pour des coques irrégulières et une déformation critique constante avec triaxialité, Lode, vitesse et température.
- La variation d'impulsion démontre la sensibilité au choix de rupture ; elle ne prouve ni la rupture ni l'intégrité d'une aile réelle, et ne tranche pas la pénétration historique ou une hypothèse de projection.
- Le modèle reste une baie locale de 1,98 kg contre une colonne représentative, pas un Boeing 767 ni une façade WTC1 complète.
- V11F froid, V11R thermique, I01–I02E et le B762 graphique doivent rester inchangés. Blender demeure une visualisation tant que les états de rupture ne sont pas exportés et vérifiés.
