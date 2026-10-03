# WTC1 — IMPACT-I02I-E : sensibilités bornées sur éprouvettes

## 1. Faits observés ou transcrits

8/8 nouveaux cas ont leurs trois exécutables terminés et leur audit sauvegardé. Temps des exécutables des cas acceptés : 1751.892 s (29.198 min), plus 0.852 s de précontrôle rejeté. Cas non audités : aucun. Configuration `wtc1_simulation_v8/data/impact_i02i_sensitivity_predeclaration.json`, plan antérieur de D `wtc1_simulation_v8/data/impact_i02i_sensitivity_plan.json`, résultats `wtc1_simulation_v8/output/impact_i02i_sensitivity/verification_r1/summary.json`. Les coordonnées et la topologie sont conservées pour vitesse et pénalité ; l'extension du domaine raffiné est déclarée séparément. Deux préparations avant solveur ont été rejetées pour une comparaison tuples/listes ; les decks et scripts sont conservés dans `rejected_generation/`. Aucune physique n'a été calculée dans ces tentatives.

Un premier précontrôle de pénalité doublée a aussi été rejeté : arrondir δ0 à 12 chiffres significatifs vers le bas faisait dépasser à la pente de la fonction la raideur déclarée d'environ 6×10⁻¹³ relatif ; le starter tentait d'augmenter automatiquement K (avertissement 506). Ce starter et son script sont conservés dans `rejected_preflight/`. Les nouveaux états neufs écrivent δ0=peak sérialisé/K sérialisé, arrondi décimal vers le haut à 14 chiffres ; variation relative maximale d'ouverture 6.56161616e-13, sous la borne pré-déclarée 10⁻¹⁰. Kn, peak, Gf et aire initiale restent déclarés identiques. Aucun état endommagé n'est réutilisé et l'avertissement n'est pas autorisé pour masquer un changement de propriété.

Cette **vitesse est celle du chargement d'une éprouvette**, pas celle du Boeing. Les anciens impacts locaux à 198,03072 m/s ne sont ni modifiés ni relancés. Un succès sur ce coupon ne qualifie pas un avion contre une façade.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle NIST ou résultat officiel de l'événement n'est importé. Les fenêtres NASA bornées et leurs conversions sont celles des itérations A/B/C. Les deux interprétations engineering et true_total restent conservées ; aucune n'est déclarée être la convention expérimentale certaine. Les valeurs de courbe, unités initiales et conversions stress/déformation sont enregistrées dans chaque `generation.json`.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation des archives n'est testée. 1247 fichiers antérieurs épinglés sont vérifiés par SHA-256 ; aucune archive source ni tout l'historique n'est rescanné. Les résultats B/C/D servent de références sauvegardées ; aucun ancien solveur ne tourne. La copie source NASA, les documents primaires et les anciens rendus restent en lecture seule.

## 4. Hypothèses propres au modèle, unités et critères

Éprouvette M(T) nominale : largeur 76,2 mm, longueur 300 mm, épaisseur 2,3 mm, fissure centrale initiale totale 25,4 mm. Coques QEPH24 avec Ismstr4, Ithick1, Iplas1, cinq points d'intégration, z et rotations bloqués ; bord inférieur y fixé et déplacement y supérieur quintique 0→1,2 mm. Matériau LAW36 : densité 0,00278 g/mm³, E=71400 MPa, ν=0,3 ; courbe NASA avec deux conventions conservées, sans remplacement d'un historique endommagé.

Unités : g/mm/ms/N, MPa=N/mm², énergie solveur N mm=mJ, énergie rapport J=0,001 N mm. Pénalités par aire initiale Kn=56000 et Kt=21500 N/mm³ en référence ; chaque connecteur reçoit K=penalité×aire initiale fixe (épaisseur initiale×largeur tributaire). Traction normale maximale hypothétique 495 MPa, Gf=30 N/mm maintenu ; δ0=traction/Kn, δf=2Gf/traction. Avec cette aire, l'intégrale normale est Gf×aire ; ce n'est pas une identification de fracture mixte. D montre que la suppression d'un effort tangent peut conserver du travail numérique dans IE.

Facteurs : durée 12→24 ms (vitesse moitié), Kn/Kt ×0,5 ou ×2 à géométrie identique, domaine raffiné ±22,86→±30,48 mm avec garde déplacée et largeur physique 76,2 mm inchangée. Aucun facteur n'est cumulé avec un autre dans un cas. h local=1,27 mm, Gf15/60 différés. Histoire demandée fixe 0,00001 ms, indépendante de la durée de chargement ; vérifier intervalle inférieur au pas minimum et nombre de lignes égal aux cycles. Aucun ajout de masse. Plafonds : 900 s/cas, 2400 s cumulées pour les exécutables.

Critères déclarés : max KE/IE ≤1 % sur toute fenêtre IE≥1 % du pic, résidu global énergie ≤0,5 %, travail indépendant des appuis ≤1 %, impulsion signée comparée au momentum ≤1 % des grandes impulsions d'appuis (résidu absolu aussi conservé), somme IE ressort ≤0,1 %, quadrature dense ressort ≤0,5 %. Comparaisons à déplacements communs : force ≤5 % du maximum des pics, travail ≤5 % du maximum des travaux finaux, angles à avances nodales exactes ≤10 %. Absence d'une avance ou d'un déplacement demandé demeure une absence ; le nouveau contrôle de couverture les rend visibles.

## 5. Résultats dérivés

Critères de cas : 156/160. Comparaisons : 30/40. Les échecs et non-évaluations sont conservés dans `wtc1_simulation_v8/output/impact_i02i_sensitivity/retained_failed_and_unassessed_gates.json`.

| Cas | Max KE/IE % | Résidu énergie % | Travail appuis erreur % | Dernier déplacement mm | Avance nodale moyenne mm | Critères de cas échoués |
|---|---:|---:|---:|---:|---:|---|
| ENG_SPEED_R1 | 1.9921 | 0.037151 | 0.099755 | 1.011949 | 8.89 | inertia_significant_window |
| TRUE_SPEED_R1 | 0.21832 | 0.00098477 | 0.10497 | 1.2 | 2.54 | aucun |
| ENG_PENALTY_HALF_R1 | 1.8374 | 0.046475 | 0.0025629 | 1.095718 | 8.89 | inertia_significant_window |
| TRUE_PENALTY_HALF_R1 | 0.29987 | 0.0013024 | 0.0069381 | 1.2 | 2.54 | aucun |
| ENG_PENALTY_DOUBLE_R1 | 2.1611 | 0.034846 | 0.0028514 | 1.006728 | 8.89 | inertia_significant_window |
| TRUE_PENALTY_DOUBLE_R1 | 0.22129 | 0.00083296 | 0.0088586 | 1.2 | 2.54 | aucun |
| ENG_DOMAIN_R1 | 10.958 | 0.045539 | 0.0029104 | 1.113935 | 16.51 | inertia_significant_window |
| TRUE_DOMAIN_R1 | 0.24841 | 0.00078397 | 0.0095328 | 1.2 | 2.54 | aucun |

| Variante / référence C | Écart force % | Écart travail % | Écart CTOA % | Déplacements couverts | Avances couvertes | Critères de comparaison échoués |
|---|---:|---:|---:|---:|---:|---|
| ENG_SPEED_R1 | 4.0146 | 0.014807 | 1.0736 | 5/11 | 3/3 | all_requested_common_displacements_assessed |
| TRUE_SPEED_R1 | 0.79099 | 0.0072673 | 0.17423 | 11/11 | 1/3 | all_requested_common_advances_assessed |
| ENG_PENALTY_HALF_R1 | 3.5854 | 0.48002 | 10.707 | 5/11 | 3/3 | ctoa_at_exact_common_advance, all_requested_common_displacements_assessed |
| TRUE_PENALTY_HALF_R1 | 1.5512 | 0.49595 | 0.75263 | 11/11 | 1/3 | all_requested_common_advances_assessed |
| ENG_PENALTY_DOUBLE_R1 | 3.2464 | 0.24708 | 3.3239 | 4/11 | 3/3 | all_requested_common_displacements_assessed |
| TRUE_PENALTY_DOUBLE_R1 | 0.97706 | 0.24818 | 0.48882 | 11/11 | 1/3 | all_requested_common_advances_assessed |
| ENG_DOMAIN_R1 | 0.39609 | 0.028309 | 19.68 | 5/11 | 3/3 | ctoa_at_exact_common_advance, all_requested_common_displacements_assessed |
| TRUE_DOMAIN_R1 | 0.51955 | 0.080306 | 0.44818 | 11/11 | 1/3 | all_requested_common_advances_assessed |

- engineering : max KE/IE passe de 2.12247 % à 1.99212 %, avec seuil déclaré 1 %. Comparaison valable sur les déplacements et événements effectivement couverts, sans extrapolation.
- true_total : max KE/IE passe de 0.246601 % à 0.218319 %, avec seuil déclaré 1 %. Comparaison valable sur les déplacements et événements effectivement couverts, sans extrapolation.

- engineering : domaine étendu, dernière ouverture/distance de garde maximale 0.1206435 mm pour seuil 0.0969697 mm ; max KE/IE 10.9577 %, déplacement terminal enregistré 1.113935 mm, avance nodale 16.51 mm. La garde est un arrêt numérique avec dépassement échantillonné, pas une limite physique exacte.
- true_total : domaine étendu, dernière ouverture/distance de garde maximale 0.0064743 mm pour seuil 0.0969697 mm ; max KE/IE 0.248413 %, déplacement terminal enregistré 1.2 mm, avance nodale 2.54 mm. La garde est un arrêt numérique avec dépassement échantillonné, pas une limite physique exacte.

Les tableaux de comparaison donnent le maximum sur les seuls points réellement disponibles. Leur faible écart ne remplace pas une couverture manquante. Les événements de départ sont les premières lignes d'avance contiguë, conservées comme diagnostic distinct. Les derniers états sont les derniers enregistrements, pas une extrapolation à la fin demandée. Les CTOA sont des angles géométriques du chemin de fissure imposé, pas une mesure indépendante de tunnel de fissure 3D.

## 6. Contradictions, informations manquantes et suite

La convention de source, Gf réel, la dissipation mixte et la propagation physique restent non identifiés. Les maxima plastiques portent sur un sous-ensemble de coques près de la pointe ; leur borne ne vaut pas pour toute l'éprouvette. Une sensibilité de pénalité ou de domaine reflète une dépendance du modèle, pas une probabilité de l'événement. Le témoin D conserve une limite d'impulsion après suppression quand le pas augmente ; E ne remplace pas le témoin neuf à pas post-rupture contrôlé nécessaire avant un impact libre.

I02I-F devra traiter les sensibilités ou domaines encore ouverts à partir de ces résultats, puis vérifier le phasage force/état/impulsion et la libération d'énergie avant transfert à un sous-modèle d'impact libre. Réutiliser les courbes E ; ne pas relancer huit cas pour relire leurs résultats. Si une portion de campagne a été différée par le plafond, elle reste explicitement à exécuter depuis le plan initial. Gf15/60 restent différés tant que leurs dépendances sont ouvertes.

V11F froid et V11R/V11S préservés. Température imposée ≠ incendie calculé ; flexion après fracture complète non validée ; tests numériques ≠ validation de l'effondrement réel ; Blender reste une visualisation. D+E constituent la paire GitHub suivante, après vérification d'intégrité ; la confirmation administrative B+C déjà préparée doit être incluse. Aucun post sur X autorisé.
