# IMPACT-I02I-B : éprouvette à raideurs cohésives fixes

Date : 2026-10-02T08:56:57.771431+00:00. Campagne bornée terminée et auditée. La qualification de propagation physique reste ouverte ; les critères échoués ou non évalués sont conservés. Cette étape suit IMPACT-I02I-A. Contrôle froid V11F et branche thermique V11R → V11S préservés. Aucun calcul historique relancé.

## 1. Faits directement observés ou transcrits

Douze essais neufs ont terminé normalement. Les contrôles élastiques passent 28/28 critères, avec 5/5 contrôles de campagne et un test de capteur. Ensemble : 175/180 critères de cas ; comparaisons : 16/24. Ces totaux ne sont pas une validation de l'événement réel. 583 anciens fichiers épinglés ont été vérifiés inchangés, sans rescanner les archives.

Le test de capteur s'arrête à t=1.001758 ms, distance=10.01003296 mm, pour un seuil 10,01 mm et une fin demandée 4,4 ms. Son historique est clôturé et converti. Les éprouvettes fissurantes emploient le même mécanisme d'arrêt, aux deux limites x=±22,86 mm ; il arrête réellement le moteur si la distance des nœuds de couture atteint 0,8 δf. Il ne s'agit pas d'un recadrage des résultats.

## 2. Sources primaires et résultats de modèles officiels

Les données matériau et leurs deux conversions réutilisent exclusivement le manifeste borné de [I02I-A](../impact_i02i_material/rapport_impact_i02i_material.md), fondé sur les pages 178–182 et 196 du [document NASA STAGS](https://ntrs.nasa.gov/api/citations/20060008654/downloads/20060008654.pdf). La convention nominale/vraie et la contradiction décimale restent ouvertes. Aucune nouvelle lecture globale de ce PDF, aucune donnée Boeing nouvellement identifiée, aucun résultat de modèle officiel du WTC.

La géométrie est reprise de la configuration I02H et de sa source NASA CR-191523 sauvegardée, dont l'empreinte est revérifiée dans `source_provenance_supplement.json`. La liste initiale de sources B décrivait le matériau et les nouvelles cartes ; ce supplément rend explicite l'origine distincte de la géométrie, sans nouvelle inspection du PDF ni utilisation de ses comparateurs de déchirure stable.

Les pages primaires [TYPE8](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm), [historiques de ressort](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm), [capteur de distance](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/sensor_dist_starter_r.htm) et [arrêt par capteur](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stop_lsensor_engine_r.htm) ont été consultées et sauvegardées. TYPE8 décrit des modes indépendants et des options d'écrouissage ; H=2 est ici conservé. La carte n'est pas une loi cohésive mixte calibrée, et l'intégrale triangulaire en ouverture monotone ne suffit pas à prouver sa dissipation lors de retours ou de glissement.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation issue de vidéo, photographie ou archive n'est ajoutée. L'identification d'un mécanisme historique, l'applicabilité aux composants d'un avion et la chaîne d'effondrement ne sont pas déduites de ces essais numériques.

## 4. Hypothèses propres au modèle, propriétés et unités

Éprouvette générique plane 76,2 × 300 × 2,3 mm ; fissure centrale initiale de longueur totale 25,4 mm. E=71 400 MPa, ν=0,3, ρ=0,00278 g/mm³, masse initiale 146.166840 g. QEPH : Ishell24, Ismstr4, Ithick1, Iplas1, N5 ; états initiaux neufs, sans remplacement de matériau ni de son historique. Aucun calcul thermique. Options homogènes vérifiées en A ; leur usage près d'une fissure reste à évaluer.

Unités : g–mm–ms ; N ; MPa=N/mm² ; énergie brute N·mm, convertie par 0,001 en J ; impulsion N·ms. Interprétation ENG : e=ln(1+εsource), σ=σsource(1+εsource), p=max(0,e−σ/E). Interprétation TRUE : e=εsource, σ=σsource, p=max(0,e−σ/E). Cinq points source inchangés ; clipping du premier p et prolongement constant final explicités dans chaque `conversion_ledger`. La source n'est pas choisie comme une vérité mesurée.

Kn=56 000 N/mm³ et Kt=21 500 N/mm³, indépendants du pas et de la branche matériau. Le connecteur i reçoit ki=K Ai en N/mm, Ai=2,3 mm × largeur tributaire initiale. Cette aire reste fixe lorsque la coque s'amincit : il s'agit d'une loi définie sur l'aire de référence, pas d'une traction recalculée sur l'aire courante. Ces pénalités sont des choix numériques. Pic normal 495 MPa, Gf=30 N/mm hypothétique, δ0=495/56000=0.008839285714 mm, δf=60/495=0.121212121212 mm. L'intégrale d'une charge normale monotone jusqu'à δf vaut Gf Ai ; somme sur le ligament entier : 3,5052 J. Dix vérifications indépendantes de partition, dimensions et invariance de δ0 passent, sans lancer le solveur des jeux de référence.

Pas locaux h=2,54 ; 1,27 ; 0,635 mm, même domaine raffiné et même éloignement des mors. Géométrie hors zone raffinée héritée d'I02H. Ressorts sans masse de translation ; inertie de rotation 10⁻²⁰ g·mm², égale au remplacement du solveur, rotations contraintes. Le précontrôle accepte uniquement l'avertissement 445 « NULL INERTIA » attendu une fois par ressort et documenté ; tout autre avertissement ou erreur bloque le moteur. R1 et R2 rejetés avant moteur restent sauvegardés. Le contrôle de masse vérifie ensuite l'absence d'ajout de masse.

Mors inférieur fixe y ; mors supérieur déplacé y ; un nœud supprime la translation x, z et rotations bloqués. Charge quintique u=u_max(10s³−15s⁴+6s⁵), 800 subdivisions ; contrôles 0,02 mm en 6/12 ms ; autres essais 1,2 mm en 12 ms, témoin lent 24 ms. Facteur de pas 0,9 et témoin 0,45, sans mass scaling, un thread CPU. Historiques demandés tous les 0,004 ms, multipliés par le facteur de durée ; temps réellement émis enregistrés. Aucun amortissement ajouté, aucune animation Blender.

Arrêt de domaine : ouverture-distance aux nœuds x=±22,86 mm. Distance euclidienne inclut le glissement et peut déclencher plus tôt que le seuil en ouverture normale. Le contrôle est discret au pas moteur ; les distances finales peuvent dépasser légèrement le seuil d'activation, leurs maxima sont sauvegardés. L'avance maximale admissible par côté est 10,16 mm ; les connecteurs de garde doivent rester actifs. Un arrêt de domaine borne l'essai numérique et n'est pas un arrêt physique de fissure.

## 5. Résultats dérivés, réactions, énergies et comparaisons

Le fichier brut sans titres contient REACY cumulatif J(t), confirmé par les deux durées élastiques : ratio d'impulsion 1.99992350, écart de travail 0.000278 %. Force moyenne d'intervalle = ΔJ/Δt ; travail indépendant des mors = Σn,i(ΔJn/Δt) Δun × 0,001 J. Les déplacements du mors inférieur sont nuls. Les forces d'intervalle et incréments de travail sont sauvegardés, sans traiter J comme une force instantanée.

Bilan global contrôlé : Wext−IE−KE, normalisé par le pic énergétique propre. IE inclut déjà les ressorts ; leur énergie n'est pas ajoutée une deuxième fois. Somme des IE des ressorts confrontée au canal global SPRING ENERGY, puis quadrature Σ½(Fi+Fi-1)ΔLi sur les composantes x/y enregistrée comme diagnostic distinct. Elle n'est pas assimilée d'office à une énergie de fracture. Impulsions signées des deux mors confrontées au quantité de mouvement globale PY ; résidu absolu et résidu divisé par l'impulsion maximale d'un mors sont tous deux conservés. Cette normalisation ne mesure pas une petite erreur relative sur le quantité de mouvement nette lorsque les réactions se compensent.

Le rapport d'inertie KE/IE utilise toute la fenêtre IE≥1 % de son pic, y compris les pointes de fracture. Critère ≤1 %. Bilan global ≤0,5 %, travail indépendant ≤1 %, masse ≤10⁻⁵ ; critères complets dans la configuration, sans ajustement après calcul.

Écarts maximaux : bilan global 0.042784 %, travail indépendant des appuis 0.003514 %. La quadrature du travail des ressorts diffère jusqu'à 3.046550 % de leur IE enregistrée, tandis que la somme des IE rejoint son canal global. Ce diagnostic n'avait pas de critère de réussite pré-déclaré ; il doit être résolu ou borné avant de qualifier Gf comme une énergie dissipée effective. Une sortie plus fine, les sauts de désactivation et la définition de IE sous H=2 sont des pistes à vérifier, pas une cause déjà démontrée.

| Cas | pic de force de section kN | u final mm | avance maximale par côté mm | Wext final J | max KE/IE fenêtre | critères échoués |
|---|---:|---:|---:|---:|---:|---|
| ELASTIC_R3 | 0.7912 | 0.02000 | 0.0000 | 0.007912 | 0.3723 % | aucun |
| ELASTIC_SLOW_R3 | 0.7912 | 0.02000 | 0.0000 | 0.007912 | 0.0932 % | aucun |
| ENG_NOPROP_R3 | 44.5971 | 1.20000 | 0.0000 | 28.069040 | 0.0937 % | aucun |
| ENG_L254_R3 | 41.6008 | 1.20000 | 6.3500 | 27.175370 | 0.4422 % | aucun |
| ENG_L127_R3 | 37.7796 | 1.01731 | 9.5250 | 20.152780 | 2.1225 % | inertia_significant_window |
| ENG_L0635_R3 | 36.6455 | 0.98819 | 9.8425 | 19.038160 | 1.8163 % | inertia_significant_window |
| TRUE_NOPROP_R3 | 44.3103 | 1.20000 | 0.0000 | 28.041040 | 0.0937 % | aucun |
| TRUE_L254_R3 | 41.9889 | 1.20000 | 1.2700 | 27.500440 | 0.0944 % | aucun |
| TRUE_L127_R3 | 41.3892 | 1.20000 | 3.1750 | 27.382880 | 0.2443 % | aucun |
| TRUE_L0635_R3 | 37.6493 | 1.03744 | 9.8425 | 20.902530 | 1.8629 % | inertia_significant_window |
| ENG_L127_DT45_R3 | 37.7811 | 1.01716 | 9.5250 | 20.147210 | 2.1170 % | inertia_significant_window |
| ENG_L127_SLOW_R3 | 37.7738 | 1.01195 | 9.5250 | 19.953870 | 1.9921 % | inertia_significant_window |

La force de section est ΣFY des ressorts ; la contrainte nominale associée emploie l'aire initiale 76,2×2,3 mm². Elle est distincte de la réaction moyenne des mors pendant les transitoires.

À u=1,2 mm dans les deux cas grossiers, l'avance d'aire moyenne est 6.3500 mm en ENG contre 1.2700 mm en TRUE. Cette différence illustre la sensibilité couplée à la convention source, dans ces cas neufs identiquement discrétisés ; elle n'identifie pas la bonne convention ni un mécanisme historique. Les cas arrêtés avant 1,2 mm ne sont pas extrapolés pour produire cette comparaison.

Deux proxys d'avance restent distincts : somme des largeurs tributaires rompues contiguës (première cellule h/2), et dernier nœud rompu contigu moins la pointe initiale (première rupture : 0). Les angles CTOA sont des indicateurs géométriques calculés derrière la pointe issue du proxy d'aire, à distances B=2,3 mm et 2B ; ils ne constituent pas un critère matériau identifié.

Comparaisons à u=0,2 ; 0,5 ; 0,8 ; 1 ; 1,2 mm dans le recouvrement réel seulement. Forces/travail interpolés en u ; aucun prolongement hors domaine. Comparaisons CTOA aux avances nodales exactes 2,54 ; 5,08 ; 7,62 mm, lorsque les deux côtés atteignent cette valeur dans un événement sauvegardé. Un saut qui omet une valeur ou un arrêt avant celle-ci donne « non évalué », jamais « réussi ». L'indicateur d'aire diffère de h/2 à avance nodale identique ; cette incertitude de localisation est conservée. Les différences de force sont divisées par le pic commun, celles de travail par le maximum des travaux finaux et celles d'angle par la valeur maximale des deux angles.

| Comparaison | max Δforce / pic | max Δtravail / échelle | max ΔCTOA relatif | déplacements évalués (après rupture) | avances exactes évaluées | critères échoués / non évalués |
|---|---:|---:|---:|---:|---:|---|
| ENG_L254_L127 | 0.4522 % | 0.2182 % | 29.7133 % | 4/5 (1 après rupture) | 2/3 | ctoa_at_exact_common_advance, all_requested_common_advances_assessed |
| ENG_L127_L0635 | 0.0962 % | 0.0189 % | 8.2683 % | 3/5 (0 après rupture) | 2/3 | all_requested_common_advances_assessed |
| TRUE_L254_L127 | 7.7056 % | 0.4276 % | non évalué | 5/5 (2 après rupture) | 0/3 | ctoa_at_exact_common_advance, all_requested_common_advances_assessed |
| TRUE_L127_L0635 | 1.4628 % | 0.0238 % | 13.5976 % | 4/5 (1 après rupture) | 1/3 | ctoa_at_exact_common_advance, all_requested_common_advances_assessed |
| ENG_L127_DT45 | 0.0037 % | 0.0000 % | 5.4765 % | 4/5 (1 après rupture) | 3/3 | aucun |
| ENG_L127_SLOW | 0.0167 % | 0.0032 % | 11.3235 % | 4/5 (1 après rupture) | 3/3 | ctoa_at_exact_common_advance |

Les critères force/travail se limitent aux points réellement évalués ; leur réussite ne vaut pas une couverture de tous les déplacements demandés. Lorsque les arrêts précèdent les premiers déplacements communs après séparation complète, ces critères décrivent essentiellement l'état avant propagation. Le nombre de points après rupture est explicité pour empêcher une promotion indue en convergence de propagation.

## 6. Contradictions, informations manquantes et suite

Critères de cas non satisfaits : `{"ENG_L127_R3": ["inertia_significant_window"], "ENG_L0635_R3": ["inertia_significant_window"], "TRUE_L0635_R3": ["inertia_significant_window"], "ENG_L127_DT45_R3": ["inertia_significant_window"], "ENG_L127_SLOW_R3": ["inertia_significant_window"]}`. Tous les essais restent conservés. Critères de comparaison entièrement satisfaits : 1/6. Une comparaison partielle ou non évaluée n'est pas déclarée convergée.

Le dépassement KE/IE retire le crédit quasi statique déclaré pour ces cas ; il ne démontre pas à lui seul une erreur du solveur. Le demi-pas satisfait les quatre critères de comparaison temporelle dans le recouvrement disponible, mais le cas reste au-dessus du seuil d'inertie. La durée doublée ne supprime pas ce dépassement et échoue au critère d'angle. Aucune qualification complète de propagation n'en est tirée.

Cas dépassant le dernier point source de déformation plastique dans les coques échantillonnées près des pointes : `[]`. Le prolongement numérique constant prévu dans la configuration n’est pas sollicité dans cet échantillon. L'échantillonnage couvre les coques dont |ycentre|≤2h et a0−h≤|xcentre|≤22,86 ; son maximum n'est pas une borne du maillage entier. La convention source demeure indéterminée, les décimales et arrondis MPa/psi ne sont pas résolus.

IMPACT-I02I-C doit partir des résultats sauvegardés : examiner en priorité les critères échoués, l'écart de travail des ressorts et les états communs manquants, choisir une extension bornée de qualification de pénalité/domaine/vitesse ou d'échantillonnage, puis seulement comparer Gf=15/30/60 sans modification d'un état endommagé. La sensibilité temporelle est effectuée uniquement pour ENG au pas médian ; TRUE ne reçoit pas de qualification temporelle par analogie. Le domaine d'arrêt et le proxy de pointe peuvent limiter les comparaisons ; la convention matériau reste une sensibilité distincte.

Une température imposée n'est pas un incendie calculé. Localisation en flexion après fracture complète non validée. Aucun résultat ne valide l'impact historique d'un Boeing, une aile réelle, la façade ou l'effondrement du WTC1. Blender reste une visualisation.

## Reproductibilité, coût et publication

Configuration R1, R2 et R3 conservées ; R3 effective : `wtc1_simulation_v8/data/impact_i02i_fixed_penalty_predeclaration_r3.json`. Scripts `run_impact_i02i_fixed_penalty.py`, `audit_impact_i02i_fixed_penalty.py`, `test_impact_i02i_fixed_penalty.py` et `complete_impact_i02i_fixed_penalty.py`. Graine 1102010 ; aucun tirage. Python 3.14.3, NumPy 2.4.6, OpenRadioss v20260728-win64 ; empreintes des exécutables et durées par travail dans chaque `execution.json`. Douze cas : 1743.670248 s ; estimation annoncée 30–60 minutes, plafonds 30 minutes par cas et 90 minutes pour la campagne, sans calcul GPU. Préflights et capteur séparés dans le bilan administratif.

Audit effectif : `verification_r1/summary.json`, historiques JSON et forces d'intervalle CSV par cas. Diagnostics élastiques intermédiaires conservés ; r1 interrompu à la sérialisation d'un booléen NumPy, r2 lit les mêmes CSV sans relancer de solveur. Le test de capteur R1 est un échec de préparation Python avant solveur, R2 est réussi. Manifeste source, références, protection antérieure, empreintes et vérification finale dans ce dossier. Revérifier avec le mode `--verify` du script de clôture ; une nouvelle réanalyse doit créer un nouveau dossier.

Publication autorisée sur [WTC-simu2026](https://github.com/WTC-simu2026/WTC-simu2026) après chaque paire d'itérations auditée. Baseline publiée : IMPACT-I02I-A. Après clôture vérifiée de B : compteur 1/2 ; prochaine mise à jour après C vérifiée. Aucun envoi GitHub n'est effectué pour B seule. Les vérifications d'intégrité du dépôt restent distinctes de la validation scientifique.
