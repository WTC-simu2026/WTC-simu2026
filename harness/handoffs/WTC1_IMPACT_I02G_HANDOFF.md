# Passation WTC1 — IMPACT-I02G vers IMPACT-I02H

## État vérifié

- Itération terminée : `IMPACT-I02G`.
- Prochaine étape : `IMPACT-I02H`.
- Harnais avant enregistrement : `PASS` avec 105 entrées.
- Harnais après enregistrement : `PASS` avec 106 entrées, état `IMPACT-I02G -> IMPACT-I02H`.
- Audit de publication I02G : `11/11 PASS`.
- Audit scientifique de campagne : `10/12`; les deux échecs sont conservés et bloquent tout transfert physique.
- Contrôle froid `V11F`, branche thermique `V11R` et résultats d'impact antérieurs préservés.

## Ce qui a été construit

- Éprouvette M(T) 2024-T3 conforme aux dimensions nominales de NASA CR-191523 : 76,2 × 300 × 2,3 mm, fissure centrale totale 25,4 mm, L-T, déplacement imposé.
- Tôle élastique parfaitement plastique : ρ=0,00278 g/mm³, E=73 100 MPa, ν=0,33, Re=360 MPa ; UTS=495 MPa utilisée comme traction maximale de la ligne cohésive.
- Fissure explicite par deux demi-tôles et ligne TYPE8 sans masse hors entaille. Raideurs par aire `Kn=E/h`, `Kt=G/h`; adoucissement triangulaire et `delta_f=2 Gf/495`.
- Plage I02F inchangée : `Gf=15/30/60 N/mm`; aucune valeur ajustée après comparaison NASA.
- Huit cas retenus : deux mailles 5,08/2,54 mm, orientations 0°/5°, contrôle élastique, contrôle fin sans propagation et trois valeurs Gf grossières.

## Résultats à reprendre

- Les huit audits de cas passent masse, terminaison, énergie, quasi-staticité et fermeture du travail de section.
- Écart du pic élastique entre mailles : ~0,99 %, seuil 5 % `PASS`.
- Contrôle fin sans propagation : `delta-a=0`, `PASS`.
- Gf=30, maille fine, orientation 0°/5° : première séparation à 185,081/185,548 MPa, écart ~0,252 %, `PASS`.
- Gf=30, maille 5,08/2,54 mm : première séparation à 147,943/185,081 MPa, écart ~20,07 %, seuil 10 % `ÉCHEC`.
- Extension finale Gf=30 : 2,54 mm grossier, 1,27 mm fin. La maille fine n'atteint pas le domaine déclaré `delta-a>=2,3 mm`; CTOA fin `ÉCHEC/indisponible`.
- Au premier pas grossier, Gf=15/30/60 donne des pics avant/au pas de 147,865/147,943/216,267 MPa et CTOA(B) 2,768°/3,023°/5,796°. La proximité du cas Gf=60 avec ~200/230 MPa et ~6° porte sur un seul saut grossier : ce n'est pas une calibration.
- Résidu énergétique maximal : ~0,1033 % ; erreur maximale travail de section/travail externe : ~0,00129 % ; KE/IE au pic <0,0056 %.
- La somme brute des `REACY` nodaux du grip ne ferme pas le travail et n'est pas utilisée. La réaction publiée est la somme des `FY` de la section cohésive, vérifiée par intégration force-déplacement.

## Tentatives rejetées conservées

- `ELASTIC_H508_A0_R0` : Starter rejeté avant solution, variable `PLAS` invalide dans `/TH/PART`.
- `G30_H254_S20_R2` : arrêt automatique à 600 s ; le mappage 20° comprimait trop les éléments et réduisait le pas explicite. Ne pas augmenter simplement le plafond.

## Décision `/FAIL/TAB2`

La carte officielle a été examinée mais non utilisée. Elle accepte une surface de déformation plastique à rupture dépendant notamment de la triaxialité, de Lode, de la température et de la taille d'élément. Ces entrées 2024-T3 ne sont pas identifiées ; une carte constante aurait caché la lacune. La ligne cohésive I02G identifie directement Gf, mais reste une fissure 2D sur trajet prescrit, sans tunnellisation ni calibration de contrainte de pointe.

## Artefacts principaux

- Configuration : `wtc1_simulation_v8/data/impact_i02g_mt_coupon.json`
- Générateur : `wtc1_simulation_v8/scripts/run_impact_i02g.py`
- Audit de cas : `wtc1_simulation_v8/scripts/audit_impact_i02g.py`
- Synthèse : `wtc1_simulation_v8/scripts/summarize_impact_i02g.py`
- Rapport : `wtc1_simulation_v8/output/impact_i02g_mt_coupon/rapport_impact_i02g.md`
- Résultats : `summary_i02g.json`, `comparisons.json`, `campaign_audit.json`
- Figure : `synthese_impact_i02g.png`
- Manifestes : `source_manifest.json`, `artifact_manifest.json`, `release_audit.json`
- Source primaire en lecture seule : `wtc1_simulation_v8/input/impact_i02f_sources/NASA_CR_191523_2024T3_CTOA.pdf`, SHA-256 `27d91f70b8816927b22f980ae7decb528837abfb19c04335a538ebaa7e6af156`.

## IMPACT-I02H

1. Garder le contrôle sans propagation et les comparateurs NASA strictement indépendants.
2. Remplacer les sauts nodaux par un raffinement local progressif ou une formulation de front de fissure mieux résolue ; éviter le mappage 20° rejeté.
3. Ajouter une troisième résolution locale économiquement bornée et une sensibilité temporelle ; exiger un écart de seuil `<=10 %`.
4. Obtenir au moins deux états d'avance fins au-delà de `delta-a=2,3 mm` avant comparaison au domaine CTOA 5–7°.
5. Chercher une courbe plastique et des données de rupture 2024-T3 compatibles avec 2,3 mm/L-T ; maintenir Gf, triaxialité, Lode, vitesse et longueur interne comme champs séparés.
6. Ne pas relancer I02F, ne pas transférer vers une deuxième zone I02E et ne pas construire l'avion/façade complets tant que les deux portes échouées ne sont pas fermées.

## Limites permanentes

- La localisation en flexion après fracture complète n'est pas validée.
- Une température imposée n'est pas un incendie calculé.
- Des tests numériques réussis ne valident pas l'effondrement réel ni l'impact historique.
- Blender reste une visualisation tant que ses états ne proviennent pas d'une mécanique vérifiée.
