# AIRCRAFT-A14 — objectivité spatiale du contact sur une plaque

**17 nouveaux calculs principaux et 17 observations de fin terminés.** Le contrôle d'intégrité passe ; la qualification scientifique globale reste échouée. Aucun ancien solveur relancé. Les conditions et les seuils ont été déclarés avant calcul. Aucun dommage, trajectoire finale ou résultat NIST n'a servi de cible.

À surface et masse identiques, la pénalité nodale uniforme change la raideur totale quand on raffine le maillage. Une pondération déclarée par la surface tributaire conserve cette raideur et passe toutes les comparaisons spatiales et de demi-pas de la plaque pondérée : entre les deux maillages fins, Δimpulsion **0.001720 %**, Δdurée **0.1896 %**, Δcourbe énergétique **0.7544 %** de KE initiale. La comparaison uniforme échoue, avec Δimpulsion **2.0923 %**, Δdurée **46.60 %** et Δcourbe **84.31 %**.

Des critères ponctuels d'impulsion et de pénétration sur les plaques grossières restent échoués. La condition annoncée pour tester ensuite le radôme n'est donc pas remplie. **Aucun essai de radôme ajouté dans A14 ; aucun allongement du calcul de l'avion.**

## 1. Faits directement observés ou transcrits

17 Starter sans erreur ni avertissement ; tous les principaux et observateurs terminent normalement. Les historiques CSV sont vérifiés contre chacun des records binaires natifs. Le premier record observateur donne la fin réelle et l'énergie finale ; ses REAC sont exclus, car les reprises remettent leur cumul à zéro. Contact FNX/FNY/FNZ et REAC principal sont des impulsions cumulatives, converties en N·s sans nouvelle intégration.

Masse mobile native = 0,001112 kg, erreur relative environ 1,03×10⁻⁸ ; masses nodales décodées indépendamment dans la première animation et comparées aux surfaces tributaires. Masse constante, aucune masse ajoutée, appuis fixes, rotations nulles, travail externe et plastique nuls dans tous les cas. Le vol libre reste uniforme. Ces observations concernent les sorties du solveur, aucune observation historique nouvelle.

**Correction de description A13 :** ses cartes TYPE25 portaient les IDs de surfaces [3,0] avec un groupe secondaire supplémentaire ; le Starter enregistrait le mode 1. A14 utilise explicitement [0,3] pour les contacts nœuds/surface, mode natif 3. Le témoin LEGACY_N1 reproduit séparément la déclaration antérieure et son départ. Il retrouve l'entrée effective vers −0,499838 mm. Le cas canonique grossier donne environ −0,986727 mm, puis les cas fins tendent vers −1 mm. Ces plans sont des diagnostics tirés des sorties ; le gap d'entrée n'a jamais été ajusté. L'ancienne description était inexacte. Rapport et résultats A13 sont conservés intégralement, avec cette correction nouvelle dans A14 ; aucun crédit rétroactif.

## 2. Résultats d'un modèle officiel

A14 n'utilise aucun résultat NIST comme paramètre ou cible. Les sorties nouvelles viennent de l'exécutable OpenRadioss local v20260728-win64 ; elles ne sont pas des résultats NIST. Le solveur, ses empreintes, les arguments, durées et codes de sortie sont enregistrés pour chaque processus dans execution_summary.json. Les hypothèses de façade NIST héritées d'A12/A13 ne sont pas nécessaires à ce contrôle plan.

La [documentation primaire TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) distingue les déclarations de surfaces, groupe nodal et raideur. Le calcul analytique de la plaque ci-dessous est une référence mécanique propre au témoin, sans assimilation à l'avion.

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou archive inspectée. Nouveau scan SHA-256 complet de **7876 fichiers antérieurs**, soit **39.11 Go**, sans différence. Les sources officielles locales et archives restent en lecture seule. Le module Boeing parallèle v2 reste séparé ; ses limites d'inertie et de dynamique libre ne sont pas résolues par A14. V11F/V11R et les branches différées sont conservées.

La publication A12+A13 vérifiée reste le dernier point distant. Le cycle ne reçoit que A14, en attente d'A15 pour la cadence de deux itérations ; aucune publication externe nouvelle dans A14.

## 4. Hypothèses propres au modèle

Configuration aircraft_a14_predeclaration.json, graine 1102039, zéro tirage. Plaque 20×20×1 mm, mur 40×40×1 mm immobilisé, départ X=−5 mm, vitesse +200 m/s, horizon **0,04 ms = 0,00004 s**. Seul X est libre sur la plaque ; Y, Z et toutes les rotations sont bloqués. LAW1 synthétique : rho=0,00278 g/mm³, E=70000 MPa, nu=0,3 ; ces valeurs vérifient un mécanisme numérique et n'identifient pas un matériau Boeing. Aucun RBE3, rupture, érosion, ressort ou masse artificielle.

TYPE25 : Istf=4, gap déclaré 1 mm, épaisseurs de contact de 1 mm pour chaque côté avec demi-contribution, Ishape=2, Iedge=1000, Ipstif=0, Inacti=1000, frottement nul, amortissement VIS_s=1e−20. Les IDs de surfaces canoniques restent [0,3]. Les quatre niveaux mobiles ont 1/4/16/64 quadrilatères et 4/9/25/81 nœuds, même surface 400 mm² et même masse. Le mur a séparément 1, 9 ou 16 mailles.

Pénalité uniforme : Stfac=1, raideur nodale théorique 35000 N/mm, donc raideur totale 140000/315000/875000/2835000 N/mm. Pénalité pondérée : **Stfacᵢ = facteur × Aᵢ / 100 mm²**, Aᵢ étant la somme des quarts d'aire des quadrilatères incidents. Les groupes nodaux sont disjoints et couvrent chaque nœud secondaire une seule fois. La raideur totale nominale reste **140000 N/mm**. L'aire de référence correspond au témoin grossier A13 et a été déclarée avant exécution ; elle n'est pas choisie à partir du résultat A14. Les facteurs 0,25 et 4 sont conservés comme sensibilités. Cette raideur est une pénalité numérique, pas une loi de contact physique identifiée.

Pour une translation uniforme conservatrice : masse 1,112 g, KE₀=22,24 J, P₀=0,2224 N·s, impulsion de rebond=0,4448 N·s ; durée π√(M/K)=0,008853974 ms et pénétration 200√(M/K)=0,5636615 mm au facteur nominal. Les références de durée/pénétration ne sont pas créditées aux maillages uniformes nodaux supérieurs, dont les masses et raideurs locales ne sont pas proportionnelles.

Seuils inchangés : énergie ≤1 % de KE₀ ; quantité de mouvement/contact ≤1 % de P₀ ; appuis ≤2 % de P₀ ; rebond ≤1 % ; durée et pénétration ≤2 % ; reconstruction de l'énergie de contact ≤1 % de KE₀ ; comparaisons de maillage/demi-pas ≤1 % d'impulsion, ≤2 % de durée et de courbe énergétique. Les diagnostics de phase ont leurs propres limites de 0,1 %. Ils ne reclassent pas les cas.

Ledger : KE + rotation globale + IE + hourglass + spring + contact élastique/frottement/amortissement − travail externe, chaque terme une fois. Aucun RKE par pièce ou reconstruit ajouté ; aucun décalage des canaux d'énergie. Unités d'origine g/mm/ms, conversions SI enregistrées, N·mm→0,001 J et N·ms→0,001 N·s.

## 5. Résultats dérivés

| Cas | Impulsion finale X N·s | Max résidu / KE₀ % | Durée du contact ms | Critères échoués |
|---|---:|---:|---:|---|
| FREE_N8 | 0.0000000 | 0.000000 | 0.00000000 | aucun |
| RAW_N1 | 0.4451910 | 0.037249 | 0.00878879 | momentum_contact, analytic_peak_penetration, contact_energy_law |
| RAW_N2 | 0.4204096 | 0.082212 | 0.00668122 | momentum_contact, complete_rebound_impulse, rebound_velocity |
| RAW_N4 | 0.4249692 | 0.028957 | 0.00410645 | momentum_contact, complete_rebound_impulse, rebound_velocity |
| RAW_N8 | 0.4338610 | 0.013433 | 0.00219273 | momentum_contact, complete_rebound_impulse, rebound_velocity |
| AREA_N1 | 0.4451910 | 0.037249 | 0.00878879 | momentum_contact, analytic_peak_penetration, contact_energy_law |
| AREA_N2 | 0.4448600 | 0.016705 | 0.00880891 | momentum_contact, analytic_peak_penetration, contact_energy_law |
| AREA_N4 | 0.4448090 | 0.005216 | 0.00883223 | contact_energy_law |
| AREA_N8 | 0.4448013 | 0.001416 | 0.00884898 | aucun |
| AREA_N8_HALF | 0.4448004 | 0.000367 | 0.00884898 | aucun |
| AREA_N4_MAIN3 | 0.4448090 | 0.005216 | 0.00883223 | contact_energy_law |
| AREA_N4_MAIN4 | 0.4448090 | 0.005216 | 0.00883223 | contact_energy_law |
| AREA_SOFT_N4 | 0.4448013 | 0.001416 | 0.01769795 | aucun |
| AREA_SOFT_N8 | 0.4448004 | 0.000375 | 0.01769911 | aucun |
| AREA_STIFF_N4 | 0.4448600 | 0.016705 | 0.00440446 | momentum_contact, contact_energy_law |
| AREA_STIFF_N8 | 0.4448090 | 0.005216 | 0.00441611 | aucun |
| LEGACY_N1 | 0.4449062 | 0.009294 | 0.00878880 | momentum_contact |

La durée est mesurée sur les lignes où l'énergie de contact dépasse 10⁻⁶ J, avec un pas médian ajouté. Elle reste une mesure discrète. Le vol libre a une durée de contact nulle dans la table. Les impulsions viennent de l'historique principal ; le résidu inclut le record de fin observé. Les 17 budgets énergétiques passent ; cette fermeture ne fait pas passer les autres critères.

| Comparaison | Nature | Δimpulsion % | Δdurée % | Δcourbe contact / KE₀ % | Passe J/durée/courbe |
|---|---|---:|---:|---:|---|
| RAW_N1 / RAW_N2 | secondary_mesh | 5.566465 | 23.980218 | 72.781676 | False/False/False |
| RAW_N2 / RAW_N4 | secondary_mesh | 1.084561 | 38.537500 | 75.052461 | False/False/False |
| RAW_N4 / RAW_N8 | secondary_mesh | 2.092340 | 46.602658 | 84.307203 | False/False/False |
| AREA_N1 / AREA_N2 | secondary_mesh | 0.074350 | 0.228897 | 0.036334 | True/True/True |
| AREA_N2 / AREA_N4 | secondary_mesh | 0.011473 | 0.264739 | 1.509322 | True/True/True |
| AREA_N4 / AREA_N8 | secondary_mesh | 0.001720 | 0.189617 | 0.754381 | True/True/True |
| AREA_N8 / AREA_N8_HALF | half_dt | 0.000205 | 0.000006 | 0.001303 | True/True/True |
| AREA_N4 / AREA_N4_MAIN3 | main_mesh | 0.000000 | 0.000000 | 0.000000 | True/True/True |
| AREA_N4 / AREA_N4_MAIN4 | main_mesh | 0.000000 | 0.000000 | 0.000000 | True/True/True |
| AREA_SOFT_N4 / AREA_SOFT_N8 | secondary_mesh_sensitivity | 0.000199 | 0.006547 | 0.377244 | True/True/True |
| AREA_STIFF_N4 / AREA_STIFF_N8 | secondary_mesh_sensitivity | 0.011453 | 0.264511 | 1.509322 | True/True/True |

Le maillage principal 1/9/16 donne les mêmes historiques pertinents dans la plaque nominale à 16 mailles. La comparaison de demi-pas fin donne Δimpulsion 0.0002053 %. Les sensibilités 0,25 et 4 passent aussi leur comparaison spatiale ; leur durée et pénétration diffèrent physiquement dans ce modèle puisqu'on change la raideur déclarée. Aucune sensibilité n'est sélectionnée pour obtenir un dommage attendu.

**Convention temporelle, diagnostic conservé :** AREA_N1 donne une différence maximale de variation KE nodale/globale de 0.432338 J pour v brut, 0.873025 J pour v−dt·a/2 et 0.029266 J pour v+dt·a/2. Le dernier diagnostic échoue encore sa limite KE de 0,02224 J sur ce cas grossier, tandis que son diagnostic quantité de mouvement passe. Le bilan natif global/contact garde 0.00466812 N·s d'écart maximal, soit 2.0990 % de P₀ : son seuil de 1 % reste échoué.

L'audit fige 12 fichiers de [la source publique au commit 0168ab344bd7](https://github.com/OpenCourant/OpenCourant/tree/0168ab344bd743051e996d90c7c8d80728bb04a8). [THNOD](https://github.com/OpenCourant/OpenCourant/blob/0168ab344bd743051e996d90c7c8d80728bb04a8/engine/source/output/th/thnod.F) écrit directement les tableaux V/A ; HIST2 écrit séparément KE et quantité de mouvement globale. [REACTION_FORCES_TH](https://github.com/OpenCourant/OpenCourant/blob/0168ab344bd743051e996d90c7c8d80728bb04a8/engine/source/output/reaction_forces_th.F) accumule les contributions avec DT12. VELOCITY met V à jour avec DT12·A, et RESOL note les sorties avant intégration. Cela soutient des phases de sortie distinctes. **La chaîne temporelle complète et l'équivalence avec le binaire installé ne sont pas établies.** Le ledger et tous les critères échoués restent intacts.

## 6. Contradictions et informations manquantes

Les comparaisons spatiales pondérées passent et l'énergie se ferme, mais le critère global de transfert échoue sur les maillages grossiers. La pondération constitue une réponse vérifiée à la dépendance du contact au nombre de nœuds dans ce témoin ; elle ne démontre pas une loi de contact réaliste. La pénétration et le plan effectif grossiers peuvent dépendre du démarrage discret ; la cause unique de leurs différences n'est pas prouvée. Corriger la description des surfaces A13 change aussi l'entrée en contact : une future comparaison de radôme devra séparer déclaration géométrique et pondération.

Il manque encore des matériaux et propriétés de sandwich documentés, masse/inertie et assemblages qualifiés, rupture/délamination/écrasement, carburant et conditions mécaniques de façade. Une plaque contrainte contre un mur fixe ne reproduit pas l'avion en impact. Les premières secondes de l'événement restent non calculées. Aucun seuil ne sera élargi pour retrouver un résultat connu.

AIRCRAFT-A15 : reprendre les sorties A14 sans relancer les anciens cas. Déclarer des contrôles neufs de pas temporel et de démarrage du contact sur les plaques grossières pondérées, avec géométrie, masse, vitesse et loi de contact inchangées. Retracer la phase des historiques TH/NODE, quantité de mouvement globale, impulsion TYPE25 et REAC, notamment DT12/DT2 et l'ordre des sorties dans le code. Garder séparément les bilans natifs, les diagnostics v±dt·a/2 et les références analytiques ; aucune correction a posteriori du ledger. La qualification globale A14 reste échouée malgré les comparaisons spatiales pondérées réussies. Si une nouvelle famille passe les critères déclarés avant calcul, tester ensuite le radôme isolé avec TYPE25 explicitement nœuds/surface et pondération par aire, niveaux indépendants et sensibilité de pénalité conservée. Ne pas attribuer à la seule pondération les différences avec A13, dont la déclaration était surface + nœuds supplémentaires. Aucun coefficient choisi pour retrouver les dommages connus. Définir matériaux, masse/inertie, assemblages et conditions de façade à partir des sources avant tout crédit physique. Aucun allongement avion complet sans fermeture locale et convergence. Module Boeing parallèle v2 séparé, inertie/dynamique libre encore bloquées. Premières secondes, rupture, écrasement et impact historiques non qualifiés.

Livrables : campaign_review.json, scientific_assessment.json, timing_audit.json, execution_summary.json, configurations/scripts, manifeste et handoff. Comparaison scientifique SVG/PNG inspectée visuellement ; visualisation HTML issue des déplacements natifs ×1, syntaxe/données vérifiées, rendu interactif non certifié. L'intégrité du harnais et de la publication est distincte de la qualification physique.
