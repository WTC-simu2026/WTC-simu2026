# IMPACT-I02I-A : traction élémentaire LAW36 et conventions

Date : 1er octobre 2026. Étape A numérique terminée ; convention NASA et propagation physique restent non qualifiées. I02I-B, raideurs cohésives fixes, reste à réaliser. Cette étape suit l'état local IMPACT-I02H et ne rejoue pas l'ancien V11H. Branche thermique conservée : V11R vers V11S ; contrôle froid V11F inchangé.

## 1. Faits directement observés / transcriptions

Dix cas neufs d'un élément de coque ont terminé normalement, sans avertissement du préprocesseur ni du moteur. Sept variantes explicites passent 145/145 contrôles ; ensemble des témoins : 193/203. Les dix échecs appartiennent aux trois témoins legacy/small, ils sont conservés. Huit contrôles de campagne passent ; ce total vérifie la clôture bornée et conserve les échecs des témoins.

333 fichiers antérieurs épinglés par les manifestes I02H sont vérifiés inchangés, dont les références ciblées V11F/V11R/I02G. Aucune relance de ces calculs, aucun examen de vidéo ou nouvelle exploration d'archive. L'archive source n'a pas été parcourue. Les copies sources locales sont lues seulement.

## 2. Sources primaires / résultats de modèles officiels

Les pages PDF 178–182 et 196 du [manuel NASA STAGS](https://ntrs.nasa.gov/api/citations/20060008654/downloads/20060008654.pdf) ont été examinées ; la page 181 a aussi été revue visuellement dans le rendu sauvegardé. Table 15 imprime 0,15/0,4 ; le jeu imprime 0,015/0,04. Aucun texte de ces pages ne spécifie explicitement nominal/vrai. On conserve les valeurs MPa d'I02H et les décimales du jeu ; la différence entre MPa arrondis et psi reste ouverte. Le panneau de ce manuel est distinct du coupon générique utilisé ici. Aucun résultat de modèle officiel du WTC n'est ajouté.

La [caractérisation Altair](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tensile_test_example_law_characterization_r.htm) explique la transformation nominale/vraie et la soustraction de la part élastique. La [définition de coque](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm) distingue QEPH, petites/grandes déformations, épaisseur et plasticité plane. [LAW36](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law36_plas_tab_starter_r.htm) fournit la syntaxe de l'écrouissage tabulé. Ces sources définissent une méthode numérique ; elles n'identifient pas un matériau de production Boeing.

Les explications des développeurs OpenRadioss [discussion 867](https://github.com/orgs/OpenRadioss/discussions/867) et [discussion 2773](https://github.com/orgs/OpenRadioss/discussions/2773) identifient les impulsions stockées dans T01. Un fichier sans /TH/TITLE présente des colonnes génériques et n'entraîne pas leur dérivation automatique. Les réactions brutes de ces essais sont donc J(t) en N·ms. La force moyenne d'intervalle est ΔJ/Δt en N. Ce constat est vérifié numériquement ici, sans extrapoler aveuglément ce diagnostic à tous les types d'éléments.

## 3. Affirmations issues des archives

Aucune nouvelle affirmation d'archive, identification de mécanisme, de composant ou d'alliage du WTC n'est introduite. Les entrées historiques gardent leurs propres réserves.

## 4. Hypothèses, propriétés et unités

Patch homogène générique 10 × 10 × 2,3 mm ; masse 0,6394 g, volume initial 230 mm³. E = 71 400 MPa ; ν = 0,3 ; ρ = 0,00278 g/mm³. Unités du solveur : g–mm–ms, N, MPa, N·mm ; 1 N·mm = 0,001 J. Les cinq couples source sont (0,00483 ; 345), (0,015 ; 390), (0,04 ; 430), (0,1 ; 470), (0,16 ; 491), avec déformation sans unité et contrainte en MPa. Graine 1102009, aucun tirage.

Deux hypothèses neuves restent séparées :

- interprétation nominale : e = ln(1 + εnom), σ = σnom(1 + εnom), p = max(0, e − σ/E) ;
- interprétation vraie totale : e = εsource, σ = σsource, p = max(0, e − σ/E).

Le premier p est légèrement négatif (arrondis et choix de E), puis ramené à zéro explicitement dans `generation.json`. Cela introduit une petite modification au voisinage du premier point ; aucun point postélastique n'est ajusté. Le plateau ajouté à p=1 est une continuation de syntaxe seulement : aucun essai ne dépasse le dernier point source plastique. La formule de conversion nominale/vraie suppose une déformation uniforme et un volume approximativement conservé ; le changement élastique de volume explique une partie du faible écart nominal. Elle ne reconstitue pas la striction d'un essai réel.

Coque QEPH Ishell=24, cinq points en épaisseur. Options explicites : Ismstr=4, Ithick=1, Iplas=1. Témoin hérité : Ismstr=-1, champs épaisseur/plasticité omis ; le listing résout Ismstr=2, ITHK=0, IPLAS=0. Témoin petit déplacement : Ismstr=1, Ithick=2, Iplas=2. Il s'agit d'une comparaison de groupes d'options : elle n'isole pas individuellement Iplas et Ithick. Les essais explicites qualifient seulement la combinaison déclarée dans ce patch homogène.

Appui x nul à gauche ; déplacement x imposé à droite ; un nœud bloque la translation y ; contraction y libre, mouvement hors plan et rotations bloqués. Rampes quintiques à vitesse nulle aux jonctions, segments 2 ms, paliers 0,2 ms ; un témoin à durée double et un à facteur de pas 0,45 au lieu de 0,9. Aucun ajout de masse ni rupture. Cycle élastique 0 → 0,002 → 0 ; cycles plastiques : charge jusqu'au dernier point, décharge visant environ 50 MPa, recharge au même maximum. La loi et son historique ne sont jamais remplacés.

## 5. Résultats dérivés et vérification

La référence uniaxiale résout σ = E(e − p) et σ = f(p) par segments linéaires. p est engagé irréversiblement ; en décharge la réponse est élastique à p constant. Quatre contrôles analytiques indépendants passent : traction/cycle parfaitement plastique, écrouissage linéaire et reproduction des nœuds source pour les deux interprétations.

| Cas | σ finale MPa | épaisseur mm | p finale | Wext finale J | erreur σ / pic référence | marque |
|---|---:|---:|---:|---:|---:|---|
| ENG_LEGACY_R3 | 548.559800 | 2.300000 | 0.1195187 | 16.75733000 | 3.688970 % | échec |
| TRUE_LEGACY_R3 | 483.257600 | 2.300000 | 0.1311197 | 17.00562000 | 1.884965 % | échec |
| ENG_FINITE_R3 | 569.556300 | 2.138908 | 0.1404395 | 16.31273000 | 0.022239 % | pass |
| TRUE_FINITE_R3 | 490.998200 | 2.126092 | 0.1531190 | 16.29417000 | 0.028203 % | pass |
| ENG_SMALL_R3 | 483.261500 | 2.300000 | 0.1311235 | 16.01979000 | 1.884941 % | échec |
| ELASTIC_FINITE_R3 | -0.000304 | 2.300000 | 0.0000000 | 0.00000336 | 0.003430 % | pass |
| ENG_FINITE_DT45_R3 | 569.558200 | 2.138907 | 0.1404412 | 16.31254000 | 0.022074 % | pass |
| ENG_FINITE_SLOW_R3 | 569.558200 | 2.138907 | 0.1404412 | 16.31122000 | 0.011073 % | pass |
| ENG_FINITE_CYCLE_R3 | 569.552300 | 2.138908 | 0.1404395 | 16.31278000 | 0.022239 % | pass |
| TRUE_FINITE_CYCLE_R3 | 490.995300 | 2.126092 | 0.1531190 | 16.29420000 | 0.028203 % | pass |

À même allongement nominal de 10 %, les deux interprétations explicites donnent 516,998 contre 466,934 MPa : sensibilité d'environ 9,7 %, pas choix d'une vérité mesurée. Le témoin ENG_LEGACY atteint 548,560 au lieu d'environ 569,560 MPa, avec p=0,119519 contre 0,140443. Le bilan global ferme pourtant : la fermeture énergétique seule ne qualifie pas la réponse constitutive. Les résultats I02H sont préservés mais leur carte/options héritées ne doivent plus recevoir un crédit de matériau qualifié.

### Travail, réactions et dissipation

Trois calculs indépendants sont confrontés : énergie globale du solveur ; travail intérieur reconstruit depuis les contraintes et les changements du Jacobien du patch ; travail des appuis depuis les seules impulsions nodales et déplacements. Le travail intérieur d'un intervalle utilise la contrainte moyenne, sym(ΔJgéom·Jgéom_moy⁻¹) et le volume courant moyen. En petites déformations, Jacobien et volume initiaux sont utilisés. Les contraintes sont projetées depuis le repère de coque. Le travail des appuis vaut Σn (ΔJn/Δt)·Δun ; les degrés bloqués ont un déplacement nul. Pas de multiplication directe de l'impulsion par le déplacement.

La référence de dissipation plastique est ∫σ(p) V(p) dp, avec V(p) = V0 exp[(1−2ν)σ(p)/E] pour l'état uniaxial explicite, ou V0 dans le témoin small. Cette correction élastique de volume appartient au modèle de référence et n'est pas une mesure réelle. La part stockée sauvegardée vaut IE − travail plastique ; elle n'est pas confondue avec Gf ni une énergie de fissure.

ENG_FINITE : Wext = 16,312730 J, IE = 16,312330 J, travail plastique = 15,786080 J, part stockée par différence = 0,526250 J. Référence plastique = 15,786107 J ; travail des appuis dérivé = 16,313556 J. En recharge, le travail plastique final reste 15,786080 J ; aucun accroissement de p lors de la décharge/recharge sous le maximum. L'essai élastique retourne à p=0 et conserve un petit résidu numérique ; sa normalisation utilise le pic d'énergie du cycle, pas son travail net presque nul.

Maximum des sept cas explicites, normalisé par leur pic de référence ou leur excursion énergétique propre :

- contrainte : 0.028203 % ;
- bilan Wext − IE − KE : 0.002790 % ;
- travail intérieur reconstruit : 0.00007141 % ;
- travail indépendant des appuis : 0.213157 % (cycle élastique, faible énergie) ;
- travail plastique de référence : 0.000299 % ;
- KE/IE dans la fenêtre IE > 1 % du pic : 0.005691 %.

À déformation commune, demi-pas : écart σ/pic 0,002576 % ; durée double : 0,012267 %. L'impulsion brute finale est multipliée par 1.999824 quand la durée double, tandis que contrainte et travail restent proches. Cela confirme son caractère cumulatif. Les réactions dérivées sont des moyennes d'intervalle ; leur précision instantanée reste limitée par l'échantillonnage. Les sorties demandées tous les 0,002 ms sont émises aux cycles du solveur (jusqu'à environ 0,003 ms), et le dernier échantillon précède légèrement la fin demandée. Aucun saut de fracture n'est simulé.

## 6. Contradictions, informations manquantes et prochaine étape

Convention NASA : indéterminée dans la lecture bornée ; la différence Table 15/jeu n'est pas effacée. Le témoin à petites déformations et les deux témoins hérités échouent à la référence constitutive ; ils ne sont pas promus. La combinaison explicite passe dans un élément homogène, sans qualifier torsion, flexion, grandes rotations, localisation ou fracture.

Les préflights ENG_FINITE_R1 et R2 sont conservés avec leurs configurations/générateurs : champs de contrainte par couche non disponibles dans ce runtime isotrope et colonnes réservées/Istrain incompatibles. Aucun moteur lancé. R3 omet Istrain, le listing confirme son défaut actif ; il utilise les contraintes moyennes F1/F2/F12. Leur ordre de stockage canonique est vérifié par les valeurs initiales, l'épaisseur, la cinématique E1 et l'énergie IEM. Les diagnostics de lecture partiels verification_r1/r2 et la sortie r3 avant correction du journal final sont conservés. R4 est l'audit publié, sans relance solveur.

Next : IMPACT-I02I-B. Utiliser des états neufs avec options explicites et deux conventions séparées ; fixer Kn/Kt par unité d'aire indépendamment du maillage et du matériau ; trois résolutions locales, témoin sans propagation. Pré-déclarer domaines communs de déplacement/avance, énergie, inertie, fréquence de sortie, coûts et arrêts. Sensibilités Gf=15/30/60 restent hypothétiques. Examiner les historiques au-delà du seul premier seuil. Vérifier chaque canal force/impulsion avant de l'intégrer ; ne modifier aucune sortie historique.

Une température imposée n'est pas un incendie calculé. Flexion/localisation après fracture complète non validées. Aucun résultat ne démontre pénétration réelle, état d'une aile Boeing, stabilité ou effondrement du WTC1. Blender reste une visualisation ; il n'a pas été exécuté.

## Reproductibilité et livrables

Configuration : `wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json`. Pilote, auditeur, tests de référence et clôture sous `wtc1_simulation_v8/scripts/`, suffixe `impact_i02i_material.py`. Dix dossiers R3 contiennent les jeux, T01, CSV bruts, journaux et temps ; 18,475445 s de solveur/conversion au total (CPU un thread). Python 3.14.3, NumPy 2.4.6, Pillow 12.2.0 ; runtime OpenRadioss local v20260728-win64, empreintes des trois exécutables dans chaque `execution.json`.

L'audit publié est `verification_r4/summary_i02i_material.json`, avec historiques et réactions par intervalle dans les sous-dossiers. Synthèse : `verification_r4/synthese_i02i_material.png`. Les empreintes des entrées, anciens fichiers ciblés et sorties sont dans `artifact_manifest.json` et `publication_verification.json`. Pour revérifier le cache, utiliser le mode `--verify` du script de clôture. Ne relancer aucun solveur ; une réanalyse de CSV doit utiliser un nouveau dossier avec `--output`.
