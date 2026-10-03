# IMPACT-I02I-C — travail des connecteurs et échantillonnage

Huit calculs neufs : six connecteurs TYPE8 et deux répliques M(T) de B. C isole la fréquence d’enregistrement, sans changer géométrie, matériau, aire initiale, pénalités, Gf, vitesse, pas mécanique ou limites du domaine des éprouvettes. Les calculs B ne sont pas relancés. Coût des trois exécutables par cas : 335.032 s (5.584 min), hors lecture des résultats, audit et empaquetage. Plafond pré-déclaré : 30 minutes de solveur.

**Résultat borné : l’écart entre travail trapézoïdal et IE des connecteurs est un effet de sous-échantillonnage sur les deux cas médians testés.** Les enregistrements denses abaissent cet écart sous 0,00001 %. Les mêmes trajectoires, sous-échantillonnées à 0,004 ms, reproduisent les écarts B. Ce résultat ne qualifie ni Gf comme propriété réelle, ni la propagation physique. C conserve 84/85 critères scalaires, 29/30 critères d’éprouvette et 6/8 critères de comparaison B/C. Les échecs et non-évaluations sont conservés.

## 1. Faits observés ou transcrits

Il s’agit d’observations numériques, sans nouvelle observation du WTC. Les listings donnent QEPH Ishell24, Ismstr4, NPT5, ITHK1, IPLAS1 et Idril2 résolu par défaut. Le nombre de lignes denses égale le nombre de cycles moteur : 58523 ENG et 82611 TRUE_TOTAL. Les temps CSV ont sept chiffres significatifs : un incrément arrondi peut dépasser légèrement le pas mécanique. Le diagnostic R1 basé sur ce seul rapport était insuffisant ; R1 et son script sont conservés, R2 vérifie les cycles et les lignes. Il n’y a pas de nouveau calcul entre ces deux audits.

Toutes les lignes B retrouvent un temps exactement enregistré dans C. Les différences maximales sont documentées dans `cached_B_exact_timestamp_matches` : forces, travail externe, avance et CTOA. Ce contrôle distingue la trajectoire calculée de son observation plus ou moins fréquente.

Dans MIXED, OFF devient nul à 0,8145134 ms, avec FX=409,6267 N encore présent sur cette ligne ; FX est nul à la ligne suivante 0,8149292 ms. Le critère indépendant « FX=Kt·x tant qu’actif, zéro dès OFF=0 » échoue. Le décalage est conservé ; aucun filtrage ne transforme cet échec en réussite.

## 2. Résultats de modèles officiels et documentation primaire

Aucun nouveau résultat NIST ou modèle officiel de l’événement n’est importé. La source NASA et ses deux interprétations restent celles de B. La convention de la courbe n’est pas déterminée.

[TYPE8 Altair](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm) décrit les modes indépendants et les raideurs de décharge. [La documentation H2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stiffness_formulation_spring_hardening_r.htm) décrit un chargement sur fonction, une décharge linéaire et une plage sans force après son annulation en déplacement positif. [TH/SPRING](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) fournit OFF, forces, allongements et énergie. Le contrôle utilise ces définitions ; elles ne calibrent pas une loi cohésive multiaxiale.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation des archives n’est évaluée. Les archives et copies de sources demeurent en lecture seule. Les documents NASA bornés et les manifests de B sont réutilisés ; la seule nouvelle copie documentaire est la page primaire H2, enregistrée avec URL, date et SHA-256 et exclue de la redistribution scientifique.

## 4. Hypothèses, propriétés, unités et références indépendantes

Unités solveur : g, mm, ms ; N, MPa=N/mm² ; énergie N·mm=mJ, conversion J=0,001 N·mm ; réaction nodale brute = impulsion N·ms. Force moyenne d’appui=ΔJ/Δt et travail d’appui=Σ(ΔJ/Δt)Δu. IE globale inclut déjà l’énergie des connecteurs : elle n’est pas additionnée une seconde fois.

Sur les éprouvettes : Kn=56000 et Kt=21500 N/mm³, aire initiale Ai fixe, kn=Kn·Ai et kt=Kt·Ai en N/mm. Traction maximale 495 MPa ; Gf=30 N/mm hypothétique. Maillage local 1,27 mm, domaine et arrêt sur capteurs inchangés. Les options explicites, la loi LAW36, les deux conversions de la courbe et les contrôles froids sont conservés. Aucun état endommagé n’est importé ni modifié.

Sur le connecteur isolé : aire 1 mm² ; masse de connecteur 0,2 g, inertie rotationnelle 0,001 g·mm² ; rotations et z bloqués, nœud1 fixe, x/y du nœud2 imposés. Ces inerties positives sont propres à ces nouveaux contrôles, sans modification des ressorts B. Aucun ajout automatique de masse. Déplacement lissé par quintique, 800 subdivisions par segment de 1 ms ; échelle mécanique 0,2, puis 0,1 pour les deux témoins de demi-pas.

δ0=495/56000=0.00883928571429 mm ; δf=2·30/495=0.121212121212 mm. Traction monotone : aire du triangle ½·495·δf=30 N·mm=0,03 J. Cisaillement seul : ½·21500·0,02²=4,3 N·mm=0,0043 J. Référence H2 positive : m=max historique de δ ; force sur enveloppe à m, puis F=max(0,F(m)+kn(δ−m)) sur décharge/recharge en dessous de m. Pas de compression testée. Le cycle 0→0,6δf→0,2δf→0,6δf→1,05δf conserve cet historique ; la boucle de retour ne rajoute pas de nouvelle aire à la traction finale.

Le cas mixte n’a pas de référence Gf multiaxiale calibrée : un travail tangent positif précède la désactivation. IE finale ne distingue pas automatiquement énergie encore stockable et énergie irréversiblement dissipée. Aucun bilan thermique ou incendie n’est déduit de cette IE.

## 5. Résultats dérivés et bilans

| Contrôle isolé | Critères réussis | Travail intégré final (J) | Échec |
|---|---:|---:|---|
| NORMAL | 14/14 | 0.0299999939 | aucun |
| NORMAL_HALF_DT | 14/14 | 0.0299999975 | aucun |
| CYCLE | 15/15 | 0.0299999947 | aucun |
| CYCLE_HALF_DT | 15/15 | 0.0299999981 | aucun |
| SHEAR | 14/14 | 0.00430000003 | aucun |
| MIXED | 12/13 | 0.0339033462 | shear_force |

Les essais purs retrouvent 0,03 J normal et 0,0043 J tangent, avec une erreur de quadrature inférieure à 0,0001 %. La décharge H2 retrouve sa plage sans force ; le demi-pas conserve le résultat. MIXED conserve 0,03390335 J dans IE et le travail, tout en échouant au critère de force au passage OFF. Tous les bilans scalaires globaux, masses et travaux des appuis passent leurs seuils pré-déclarés.

Quadrature indépendante : Σ½(Fᵢ+Fᵢ₋₁)·(uᵢ−uᵢ₋₁), deux composantes, convertie en J. Écart maximum rapporté au maximum de |ΣIE ressorts|. Sous-échantillonnage : premier état, première ligne à/après chaque cible temporelle uniforme, dernier état ; aucun événement de rupture ajouté spécialement.

| Branche | Enregistrement de la même trajectoire | Erreur maximum de travail |
|---|---|---:|
| ENG | Dense : 58523 lignes | 9.33971424e-06 % |
| ENG | 0.004 ms : 2126 lignes | 1.32934293 % |
| ENG | 0.002 ms : 4251 lignes | 0.26961416 % |
| ENG | 0.001 ms : 8501 lignes | 0.08822993 % |
| ENG | 0.0005 ms : 17001 lignes | 0.0124532941 % |
| TRUE_TOTAL | Dense : 82611 lignes | 8.73802426e-06 % |
| TRUE_TOTAL | 0.004 ms : 3001 lignes | 0.283295613 % |
| TRUE_TOTAL | 0.002 ms : 6001 lignes | 0.0928431656 % |
| TRUE_TOTAL | 0.001 ms : 12001 lignes | 0.0252160514 % |
| TRUE_TOTAL | 0.0005 ms : 24001 lignes | 0.00573753134 % |

L’ENG dense réduit l’écart B de 1.32934 % à 9.33971424e-06 %. TRUE_TOTAL passe de 0.283296 % à 8.73802426e-06 %. Les autres maillages B ne sont pas réexécutés : le maximum 3,04655 % de la campagne entière n’est pas directement résolu cas par cas dans C.

ENG : travail externe final 20.15278 J, travail d’appui indépendant 20.15339532 J, erreur d’énergie globale 0.0427837 %, max KE/IE=2.12247 % dans la fenêtre IE≥1 % du pic. Le seuil inertiel 1 % échoue. TRUE_TOTAL : travail externe 27.38288 J, travail indépendant 27.38551352 J, erreur d’énergie 0.00106497 %, max KE/IE=0.246601 %, seuil inertiel réussi. Masse nominale 146,16684 g ; écart maximum relatif 2.7366e-05 %. Les impulsions signées des deux appuis sont comparées à PY, séparément du travail et de la force de section.

B/C aux déplacements communs : ENG 7/16 points, dont 4 après première séparation dans les deux historiques ; TRUE_TOTAL 16/16, dont 13. Pas d’extrapolation après l’arrêt ENG. Différence maximale de force normalisée par pic : ENG 0.338513 %, TRUE_TOTAL 0.00582755 %. Les trajectoires aux mêmes temps sont comparées séparément : la différence due à interpolation/échantillonnage n’est pas une nouvelle sensibilité matérielle.

Avances nodales communes 2,54/5,08/7,62 mm : ENG 3/3 disponibles, mais différence CTOA maximale B/C 10.7926 % > seuil10 %. L’événement dense et le premier événement enregistré grossièrement ne sont pas au même instant. TRUE_TOTAL 1/3 seulement ; 5,08 et 7,62 mm ne sont pas atteints par ce calcul borné. Les états de fissure ne sont pas interpolés pour inventer les deux valeurs absentes.

## 6. Contradictions, manques et étape suivante

L’énergie de connecteurs pure normale est vérifiée numériquement sur cette loi et ces cas ; ce n’est pas une identification de Gf réel. Le statut/force tangent à la désactivation mixte, la distinction stockage/dissipation, l’inertie ENG, la couverture des avances et la convergence des angles restent ouverts. Les maxima plastiques portent uniquement sur les coques sélectionnées ; ils ne bornent pas toute l’éprouvette. La source reste indéterminée et aucune propagation physique avion/façade n’est qualifiée.

I02I-D : partir de ces sorties sauvegardées. Clarifier le décalage OFF/FX par une étude ciblée de l’algorithme TYPE8 ou de nouveaux témoins mixtes pré-déclarés ; séparer le travail normal, le travail tangent et le statut. Pour les éprouvettes, annoncer une campagne bornée de vitesse/pénalité/domaine avec histories denses avant Gf15/60 ; comparer forces/travaux à déplacements communs et angles à événements définis précisément. Une extension du domaine doit être un nouvel état et ne doit pas prolonger un coupon déjà endommagé. Pas de reprise de V11F ou V11R pour relecture.

La localisation en flexion après fracture complète demeure non validée. Température imposée ≠ incendie calculé. Succès numérique ≠ validation de l’effondrement historique. Blender reste visualisation. Source NASA et résultats NIST, lorsqu’ils servent d’entrée, ne deviennent pas observations indépendantes.

## Reproduction et artefacts

Configuration : `wtc1_simulation_v8/data/impact_i02i_sampling_predeclaration.json` ; seed1102011, aucun tirage aléatoire. Scripts run/audit/complete `impact_i02i_sampling.py` ; les dépendances B sont épinglées par SHA-256. OpenRadioss win64 v20260728, /VERS2026, un thread ; exécutables épinglés dans chaque execution.json. Python/NumPy et durées dans summary.json. Les decks, sorties brutes T01/CSV/listings, préflights, journaux, génération, bilans, diagnostics R1 et audit R2 sont conservés.

Les scripts de génération de B sont réutilisés en lecture seule ; leurs anciens champs config/générateur sont conservés dans `predecessor_metadata_hashes`, et les empreintes C sont ajoutées explicitement. Aucune animation, GPU ou branche thermique exécutée. Les 896 fichiers précédemment épinglés sont vérifiés avant/après ; aucun scan intégral de l’archive.

La vérification d’intégrité `publication_verification.json` contrôle les octets, registre et état, sans relancer de solveur. La cadence GitHub conserve B+C en attente jusqu’à confirmation distante du commit, des archives et du contrôle CI ; cette intégrité ne transforme pas les critères scientifiques échoués en réussite.
