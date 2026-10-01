# WTC 1 - V9A : éprouvettes et identification des matériaux

## Résultat

La reproduction limitée des lois de vitesse sur la résistance est **PASS**. Les quatre pentes publiées pour les éprouvettes M26 et C80 sont retrouvées à partir des valeurs tabulées.

L'identification d'une carte de rupture physique WTC est **FAIL**. L'identification d'une carte moteur/capotage CF6-80A2 est **FAIL**. Aucun calcul OpenRadioss de rupture n'est autorisé ou exécuté dans V9A.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D publie des valeurs individuelles de vitesse de déformation, limite à 1 %, résistance maximale, allongement total et réduction de section pour des éprouvettes WTC identifiées.
- La série périphérique M26 provient de la colonne 130/131, niveaux 90-93 ; la série de noyau C80 provient de la colonne 603, niveaux 92-95.
- Les essais couvrent plusieurs vitesses, mais les géométries et rapports `sqrt(A)/L` changent. NIST précise que l'allongement à rupture n'est comparable que pour des éprouvettes géométriquement similaires.
- AA11, qui a frappé le WTC 1, utilisait des moteurs **General Electric CF6-80A2**. Le JT9D-7R4D concernait UA175 et le WTC 2.
- Les empreintes des PDF officiels et des fichiers V8Z gelés sont inchangées.

## 2. Résultats et choix d'un modèle officiel

- NIST a utilisé un modèle détaillé de PW4000 comme substitut des moteurs des deux avions, à partir de manuels propriétaires Pratt & Whitney.
- NIST n'a pas testé les matériaux structuraux de l'avion. Les courbes 2024/7075 provenaient de la littérature et aucun effet de vitesse n'a été inclus faute de données suffisantes.
- Le modèle de moteur NIST a augmenté les densités de 20 % pour répartir la masse de composants non représentés. Ce choix n'est pas une mesure de matériau.

## 3. Affirmations des archives locales

- Aucune nouvelle affirmation de l'archive locale n'est utilisée. L'archive source n'a pas été rescannée.

## 4. Hypothèses propres au modèle

- La seule opération de V9A est une régression de `ln(résistance)` sur `ln(vitesse de déformation)`, conforme à l'équation 4-9 de NCSTAR 1-3D.
- La tolérance de 0,0001 sur la pente couvre uniquement l'arrondi des tableaux. Elle ne mesure pas une fidélité physique.
- Les résidus d'ajustement et de validation croisée sont rapportés sans portail prédictif, car le jeu est petit et les essais ne sont pas uniformément répliqués.

## 5. Résultats dérivés

| Série | Observable | Points | Pente publiée | Pente reproduite | Écart absolu | Portail |
|---|---|---:|---:|---:|---:|---|
| M26_PERIMETER_LONGITUDINAL | yield_1_percent_offset | 7 | 0.012100 | 0.012097 | 0.000003 | PASS |
| M26_PERIMETER_LONGITUDINAL | tensile_strength | 7 | 0.011800 | 0.011844 | 0.000044 | PASS |
| C80_CORE_LONGITUDINAL | yield_1_percent_offset | 5 | 0.031700 | 0.031731 | 0.000031 | PASS |
| C80_CORE_LONGITUDINAL | tensile_strength | 5 | 0.017500 | 0.017521 | 0.000021 | PASS |

- L'erreur relative maximale en retrait d'un point est **25.189%**, contrôlée par `C80_CORE_LONGITUDINAL / yield_1_percent_offset`. C'est un diagnostic sans portail, qui interdit d'interpréter le simple `PASS` des pentes comme une validation prédictive.
- Complétude WTC pour une carte de rupture : **2/9** exigences disponibles.
- Éléments WTC manquants : `numeric_true_stress_plastic_strain_curves, geometry_consistent_fracture_strain, triaxiality_coverage, lode_and_shear_coverage, fracture_energy, regularization_length, joint_and_attachment_failure`.
- Complétude CF6-80A2/capotage : **0/9** exigences disponibles.
- Éléments moteur/capotage manquants : `specific_material_and_product_form, rate_strength_coverage, numeric_true_stress_plastic_strain_curves, geometry_consistent_fracture_strain, triaxiality_coverage, lode_and_shear_coverage, fracture_energy, regularization_length, joint_and_attachment_failure`.

## 6. Contradictions et informations manquantes

- Les itérations précédentes ont parfois nommé le JT9D comme cible WTC 1 ; NCSTAR 1-2B l'attribue au vol UA175/WTC 2. La cible correcte pour AA11/WTC 1 est CF6-80A2.
- Les tableaux NIST identifient la sensibilité de résistance de certains aciers WTC, mais pas une surface de rupture dépendant de la triaxialité et de l'angle de Lode.
- Ils ne donnent pas l'énergie de fracture, la largeur de localisation ou une longueur interne physique permettant d'identifier `/NONLOCAL/MAT`.
- L'index public GE confirme l'existence des manuels CF6-80A/A2, mais ne fournit pas les cartes matériau/rupture des composants et les qualifie de propriétaires.
- Faute de ces données, aucun alliage générique n'est substitué au CF6-80A2. L'impact façade, l'avion complet, le modèle global, le thermique et Blender restent fermés. Blender demeure une visualisation seulement.
