# AIRCRAFT-A04 — plasticité du Boeing entier et de la façade

Le modèle complet possède maintenant des lois élastoplastiques pour les peaux, les structures internes et l’acier de façade. Huit cas nouveaux r1 sont sauvegardés : trois contrôles et cinq variantes plastiques. Le contrôle sans contact conserve une translation uniforme et une énergie plastique nulle. **Le premier travail plastique non négligeable apparaît vers 0,2401 ms.** Les quatre variantes sans écrouissage n’atteignent pas les 2 ms prévues : un écrasement du maillage du nez réduit considérablement le pas de temps. La variante H=0,02E termine à 2.0001510 ms en 40.54 s d’Engine.

Cela établit une sensibilité du modèle à sa loi de comportement, sans sélectionner la variante qui atteint le plus loin comme représentation vraie du 767. Les grandes déformations, le radôme, la rupture et le bilan énergétique local restent non qualifiés. Aucun résultat de dégâts ou d’effondrement n’est imposé ou utilisé comme cible NIST. A04 est une itération complète de recherche avec des essais arrêtés et des critères échoués explicitement conservés.

## 1. Faits directement observés ou transcrits

Le graphe A03 est conservé : 35 020 nœuds, dont 3 228 pour l’avion (2 860 structuraux et 368 références de masses/RBE3), 6 538 triangles d’avion, 4 600 poutres équivalentes et 31 986 quadrilatères de façade. Les cartes de géométrie, masses, inerties géométriques de section, appuis, RBE3 et vitesse initiale sont identiques à celles d’A03. Les huit Starter r1 signalent chacun zéro erreur et zéro avertissement. Les huit ensembles d’états sauvegardés sont finis et leurs connectivités sont contrôlées avec les identifiants natifs, indépendamment de leur ordre dans VTK.

La fiche [Kaiser 2024, page 1](https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1012/Kaiser_Aluminum_2024_Sheet_Coil_and_Plate.pdf) donne une limite typique de 47 ksi, imprimée 324 MPa, pour T4/T351 et une éprouvette de diamètre 0,500 in. Ce n’est pas une nomenclature de peaux 767 en T3. La fiche [Kaiser 7075, page 1](https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1017/Kaiser_Aluminum_7075_Sheet_Coil_and_Plate.pdf) donne 73 ksi, imprimé 503 MPa, pour T651 ; sa table scannée est inspectée visuellement. Sa valeur d’allongement 11 % n’est employée ni comme déformation à la résistance maximale ni comme seuil d’effacement d’éléments. La source [Boeing ARFF 767, page PDF 6](https://www.boeing.com/content/dam/boeing/v2/airports/arff/arff767.pdf) répertorie le radôme parmi les emplacements de matériaux composites ; sa feuille porte la date du 29 avril 2022. Elle ne fournit ni stratification, ni épaisseur, ni loi d’écrasement, et ne constitue pas une description d’AA11 en 2001.

Les trois copies PDF nouvelles sont épinglées par SHA-256 et conservées dans input/aircraft_a04_sources. Elles restent des sources externes en lecture seule, exclues des livrables propres au modèle à republier. Les JSON d’acquisition, les conversions et un script de réacquisition uniquement si un fichier manque rendent leur provenance traçable.

## 2. Résultats d’un modèle officiel

Aucun résultat officiel nouveau n’est adopté comme résultat attendu. La façade nominale héritée de V8V/I02A dépend d’entrées NIST déjà transcrites : 59 colonnes et 3 étages, largeur 14 in, pas 40 in et traverses de 52 in. Les épaisseurs de référence et la hauteur d’étage restent représentatives. Cette dépendance à des données nominales est explicite ; les sorties de dégâts NIST ne servent pas à identifier les lois, la vitesse, le contact ou les seuils. OpenRadioss calcule ici notre modèle exploratoire.

## 3. Affirmations des archives locales

Aucune vidéo n’est analysée, aucun parcours de l’archive n’est relancé. Les 2464 fichiers antérieurs épinglés, dont les résultats A01–A03 et leurs échecs, sont identiques. V11F froid, V11R et la branche V11S différée restent conservés ; IMPACT-I02I-M demeure différée selon l’orientation vers l’avion entier. Aucune affirmation des archives n’est transformée en propriété de matériau ou en condition initiale de cette itération.

## 4. Hypothèses, propriétés, unités et historique

Chaque cas r1 repart intact à t=0. Aucun matériau déjà endommagé d’A03 n’est relu avec une loi modifiée. Les reprises utilisées pour observer les fins et les libellés conservent strictement les mêmes matériaux et leur historique propre à A04 ; elles ne prolongent pas la fenêtre physique publiée.

| Attribution hypothétique | Masse volumique (kg/m³) | E (GPa) | ν | Limite a (MPa) |
|---|---:|---:|---:|---:|
| Peaux et nez, aluminium de référence 2024 | 2780 | 73,1 | 0,33 | 324 |
| Cadres, longerons et poutres internes, référence 7075 | 2810 | 71,7 | 0,33 | 503 |
| Acier représentatif de façade | 7860 | 200 | 0,30 | 427,656 |

Les deux attributions aluminium sont des hypothèses, pas des nuances et traitements identifiés sur chaque pièce du 767. La densité 2780 kg/m³ est héritée d’A01 tandis que Kaiser indique 2770 ; E=71,7 GPa du 7075 est hérité tandis que la fiche indique 71,0. Elles sont conservées pour isoler la modification de loi. L’acier 62 ksi converti antérieurement à 427,656 MPa reste une référence non attribuée à chaque plaque impactée ; il n’est pas présenté comme une reconstruction des grades exacts.

La loi native [LAW2, Iflag=0](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law2_plas_johns_starter_r.htm) emploie σécoulement = a + b·εp^n, n=1. Le cas nominal a b=0 : élasticité puis plasticité parfaite. Les variantes a×0,8 et a×1,2 concernent tous les métaux. La variante H=b=0,02E a H=1462/1434/4000 MPa selon les trois matériaux. Ces lois et sensibilités sont déclarées avant calcul. Elles ne sont pas des courbes dynamiques identifiées. c=0 désactive le terme de vitesse de déformation ; l’absence d’identification dynamique reste une limite à l’impact. Aucun adoucissement thermique, aucune rupture, aucune érosion ni mass scaling ne sont activés. Les champs de température de référence du format LAW2 n’imposent aucune montée en température ou incendie ; le modèle reste mécanique sans couplage thermique.

Les coques plastiques et le contrôle à limite fictivement très haute utilisent N=5 points dans l’épaisseur. Les tenseurs UPPER/LOWER sont ceux des points extrêmes d’intégration, selon [ANIM/SHELL/TENS](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_tens_engine_r.htm), sans extrapolation d’une contrainte extérieure. VONM est conservé séparément. Les poutres TYPE3 utilisent toujours leurs sections équivalentes, avec dm=0 et df=10⁻²⁰ pour éviter le défaut df=0,01. Ce choix explore l’amortissement numérique ; il ne mesure pas un amortissement physique. TYPE3 ne résout pas une plastification progressive de fibres de section. Les historiques de 696 poutres sont sélectionnés avant calcul par max(X des extrémités)≤8 m ; SX est axial, pas une contrainte maximale de flexion. Cette sélection n’est pas un maximum global sur les 4 600 poutres.

Le nez demeure le substitut métallique d’A01, alors que la source Boeing situe un composite au radôme. Il n’est pas renommé composite. Construction interne, épaisseurs, assemblages et distributions de masses restent hypothétiques. Les moteurs de 4500 kg chacun ont des attaches équivalentes et aucune surface de contact déformable. La réserve de masse vide non résolue de 53,187 t n’a pas de raideur ajoutée pour la dissimuler. L’avion a 122 159,1859781 kg, la façade 69 310,977272 kg ; le total reste 191 470,163250 kg, et le décalage de CG natif d’A02 de 1,204527 mm est conservé.

Conditions A03 : v=(-200,5,2) m/s, attitude nulle, alignement propre au test, pas des conditions AA11 identifiées. Façade haute/basse fixée sur 944 nœuds ; pas de noyau, planchers, coins, gravité ou précharge. Distance nez-plan initial 50 mm, gap de contact TYPE7 5 mm, friction nulle, amortissement normal presque nul, aucune correction de position initiale. Pas d’autocontact ni de contact entre arêtes. La trajectoire évolue à partir de v0, sans déplacement forcé après l’initialisation.

Unités natives : g, mm, ms, MPa, N et N·mm. 1 g=0,001 kg ; 1 mm=0,001 m ; 1 ms=0,001 s ; 1 N·mm=0,001 J ; 1 N·ms=0,001 N·s ; 1 mm/ms=1 m/s. εp est une déformation plastique équivalente sans dimension, et ne signifie pas un allongement d’éprouvette à rupture. K0=½Mavion|v0|²=2,444955028 GJ. Les graines et paramètres sont dans le JSON ; le calcul est déterministe, aucun tirage aléatoire n’est effectué.

## 5. Résultats dérivés, réactions et bilans

| Cas | Dernière histoire (ms) | Dernier état (ms) | Sortie principale | PW (kJ) | εp max coques | εp max poutres échantillonnées |
|---|---:|---:|---|---:|---:|---:|
| ELASTIC_N0_DFMIN | 0.6004377 | 0.600438 | terminé | 0.000 | 0 | 0 |
| ELASTIC_HIGHY_N5 | 0.6004377 | 0.600438 | terminé | 0.000 | 0 | 1.97601e-25 |
| FREE_PLASTIC_N5 | 0.6004502 | 0.600450 | terminé | 0.000 | 0 | 0 |
| PLASTIC_NOMINAL | 1.6200010 | 1.600030 | plafond 300 s | 561.388 | 3.72617 | 5.40752 |
| PLASTIC_HALF_DT | 1.6200010 | 1.600010 | plafond 300 s | 561.468 | 3.70718 | 5.34914 |
| PLASTIC_Y080 | 1.6300020 | 1.600020 | plafond 300 s | 484.966 | 3.41 | 5.11241 |
| PLASTIC_Y120 | 1.6300000 | 1.600020 | plafond 300 s | 641.698 | 3.46174 | 8.03282 |
| PLASTIC_H002 | 2.0001510 | 2.000150 | terminé | 1166.090 | 0.870888 | 0.738445 |

Les dernières histoires des cas plafonnés sont des sauvegardes antérieures à l’interruption, pas des horodatages de terminaison vérifiés. L’Engine nominal est interrompu à environ 1,628 ms d’après sa ligne de cycle arrondie, avec Δt≈6,001×10⁻⁸ ms et le triangle 4050 limitant. Ce triangle est identifié dans fuselage_caps, au nez initial X=0 ; son aire initiale est 0,0001980619225 m². À l’état 1.60003 ms, son aire n’est plus que 1.669 % de l’aire initiale. Cela démontre une dégénérescence géométrique calculée, pas une fracture physique. Le cas de résistance basse devient également limité par un triangle proche du nez. Ajouter du temps de calcul n’est pas considéré comme une solution physique à cette dégénérescence.

Le travail plastique nominal dépasse le seuil de lecture 10⁻⁶ J à 0.2401098 ms ; le premier état spatial non nul sauvé est à 0.300254 ms. Ces cadences ne donnent pas l’instant exact de premier écoulement. Le diagnostic déclaré εp≤0,1 est dépassé dès l’état de coque proche de 0,6 ms ; il ne supprime aucun élément et n’est pas un seuil de fracture réel. Le nominal atteint εp≈3,73 en coque et 5,41 dans les poutres échantillonnées. La variante écrouissante atteint encore 0,871/0,738. Le fait qu’elle termine ne rend donc pas ses grandes déformations qualifiées.

À l’instant commun 1.6200010 ms des deux cas nominaux, réduire le pas par deux donne un écart vectoriel d’impulsion de 0.05772 % et un écart d’énergies générées de 0.02587 %. Les limites préalables 5 % et 10 % passent sur cette fenêtre. Cela ne valide pas une convergence spatiale, la rupture, les composites, les assemblages ou la partie d’impact non calculée. Les ailes n’ont pas encore atteint la façade dans ces états.

### Quantité de mouvement et réactions

La colonne de contact est testée à nouveau contre Pfaçade. Elle se comporte comme une impulsion cumulée N·ms : J=0,001·(colonne−colonneinitiale), sans intégration supplémentaire. Nominal, dernier Jx=-5189.161 N·s, Pfaçade,x=-5183.536 N·s ; l’erreur vectorielle maximale est 38.014 N·s pour une tolérance 10+2 % de |J|≈113.803 N·s. Interpréter la même colonne comme une force puis l’intégrer donne une erreur maximale d’environ 1941 N·s. Les deux interprétations sont conservées dans la relecture. Les appuis sont immobiles et leur travail est nul ; leurs petites sorties de réaction ne suffisent toujours pas à distinguer indépendamment leurs unités par rapport à la quantification de Pglobal. Les deux interprétations de réactions sont conservées, sans fabriquer une force ou une puissance. Pavion=Pglobal−Pfaçade inclut les masses additionnelles, absentes des PART structuraux.

### Énergie

Ecomptée=Ktranslation+Krotation+Uinterne+hourglass+ressorts+contactélastique+friction+dissipationcontact. Le résidu est ΔEcomptée−Wextérieur. CONTACT ENERGY n’est pas additionnée une seconde fois à ses composantes. **PW est un sous-ensemble de Uinterne, jamais une énergie additionnelle** ; cette inclusion est contrôlée sur toutes les histoires principales sauvées. Hourglass, ressorts, friction, damping contact et travail extérieur sont nuls dans ces cas. L’origine du résidu n’est pas attribuée à une dissipation physique manquante sans preuve.

| Cas plastique | Jx dernier (N·s) | Résidu E dernier (kJ) | Énergie générée dernière (kJ) |
|---|---:|---:|---:|
| PLASTIC_NOMINAL | -5189.161 | -64.879 | 823.121 |
| PLASTIC_HALF_DT | -5186.180 | -64.091 | 822.909 |
| PLASTIC_Y080 | -4476.216 | -64.401 | 702.599 |
| PLASTIC_Y120 | -5968.318 | -65.959 | 957.041 |
| PLASTIC_H002 | -10160.490 | -65.691 | 1576.309 |

Nominal : PW=561.388 kJ, Uinterne=784.251 kJ, Krotation=37.383 kJ, contactélastique=1.487 kJ. Résidu dernier -64.879 kJ, soit environ 7.88 % de l’énergie générée. Les écarts restent petits par rapport aux 2,445 GJ initiaux et tous les critères globaux 0,5 % passent. Mais **les critères locaux 5 % de l’énergie générée +1000 J, au-delà de 1000 J générés, échouent pour tous les contacts**. Le maximum relatif précoce nominal vaut 2,671 ; les courbes de résidu sont sauvegardées, et ce nombre n’est pas une probabilité. L’arrondi CSV à sept chiffres est explicitement pris en compte par les 1000 J préalablement déclarés.

La comparaison avec les résultats A03 sauvegardés est faite à 0,4955922 ms, sans relancer A03. Son résidu à cet instant vaut −49,288 kJ ; le maximum A03 sur toute sa fenêtre était 49,624 kJ.

| Cas A04 | Résidu à l’instant commun (kJ) | Différence signée avec A03 (kJ) |
|---|---:|---:|
| ELASTIC_N0_DFMIN | -47.775 | 1.512 |
| ELASTIC_HIGHY_N5 | -47.775 | 1.512 |
| PLASTIC_NOMINAL | -45.744 | 3.544 |

Le remplacement du seul amortissement df dans le contrôle élastique ne retire qu’environ 1,51 kJ du déficit à cet instant commun. Il ne résout pas le bilan local A03. Le contrôle LAW2 à haute limite et N=5 produit presque la même réponse élastique ; le nominal change aussi l’écoulement plastique. Aucun écart n’est corrigé en modifiant artificiellement l’énergie ou les propriétés.

### Horodatage et erreurs d’outillage conservées

Une première tentative r0 ELASTIC_N0_DFMIN a terminé, mais son observateur dans le même dossier a remplacé son animation A007. Cette frame r0 n’a pas été récupérée et la tentative n’est pas acceptée comme série intacte ; son anomalie, ses sorties restantes et son script sont conservés. **Les anciennes itérations A01–A03 n’ont pas été touchées.** r1 corrige l’observateur en copiant la reprise nouvelle dans un dossier isolé et en vérifiant tous les fichiers principaux par hash. Les quatre cas r1 terminés possèdent ainsi un premier enregistrement T02 et une animation correspondant à la vraie fin principale. Le cycle additionnel de l’observateur reste exclu de la fenêtre physique. Les quatre cas plafonnés n’ont pas d’observateur de fin et leurs critères de terminaison restent false.

Les cinq premiers audits interprétaient les neuf canaux de poutre dans l’ordre demandé du deck. Le moteur les écrit dans l’ordre canonique **F1,F2,F3,M1,M2,M3,IE,SX,EPSP**. Une observation isolée à matériaux inchangés avec /TH/TITLE établit cet ordre pour les 696 poutres. Les premiers audits et tableaux bruts demeurent inchangés ; cached_review/review.json porte l’interprétation corrigée. Les différences restantes de cette relecture sont l’arrondi du conteneur float32. Les libellés d’unité parasites du convertisseur sont ignorés, les unités viennent de la déclaration native. SX nominal maximal corrigé 503 MPa ne doit pas être confondu avec une énergie de poutre en N·mm ni une contrainte de fibre de flexion.

Le premier PNG a montré un défaut de découpe graphique du zoom et une borne verticale trop basse ; il est conservé. **A04_contact_plastique_v2.png** est le rendu retenu, inspecté visuellement : états enregistrés, projection XY, déplacement ×1, lignes du nez découpées au panneau, aucune trajectoire d’animation imposée. Le trait vertical représente le plan INITIAL de façade ; sa déformation n’est pas dessinée. Il s’agit d’une projection de calcul, pas d’une validation visuelle du mécanisme réel.

## 6. Contradictions, critères échoués et données manquantes

- **ELASTIC_N0_DFMIN** : energy_local_within_declared_limit.
- **ELASTIC_HIGHY_N5** : energy_local_within_declared_limit, high_yield_or_elastic_plastic_work_zero.
- **FREE_PLASTIC_N5** : aucun échec dans les critères déclarés.
- **PLASTIC_NOMINAL** : main_engine_normal_termination, observer_normal_termination, observer_did_not_change_main_outputs, native_end_timestamp_observed_within_step, energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit.
- **PLASTIC_HALF_DT** : main_engine_normal_termination, observer_normal_termination, observer_did_not_change_main_outputs, native_end_timestamp_observed_within_step, energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit.
- **PLASTIC_Y080** : main_engine_normal_termination, observer_normal_termination, observer_did_not_change_main_outputs, native_end_timestamp_observed_within_step, energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit.
- **PLASTIC_Y120** : main_engine_normal_termination, observer_normal_termination, observer_did_not_change_main_outputs, native_end_timestamp_observed_within_step, energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit.
- **PLASTIC_H002** : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit.

Le critère strict PW=0 du contrôle à haute limite échoue littéralement avec seulement 8,55×10⁻¹⁹ J ; εp coque est nul et εp poutre corrigé est d’environ 2×10⁻²⁵. Ce résidu microscopique n’est pas présenté comme une plasticité mesurable. Le critère ne reçoit pas une tolérance modifiée après observation.

Les contraintes VONM moyennes et les tenseurs des points extrêmes sont des sorties séparées. Dans le nominal, le VONM acier maximal vaut environ 499 MPa tandis que les tenseurs extrêmes sont proches de 427,657 MPa. Le VONM aluminium dépasse également 324 MPa alors que les points extrêmes sont proches de cette référence. La [documentation de post-traitement](https://2021.help.altair.com/2021/hwsolvers/rad/topics/solvers/rad/faq_rad_post_processing_r.htm) décrit VONM à partir des contraintes moyennes. La différence observée n’est pas expliquée ni utilisée pour revendiquer un écoulement exact partout ; sorties intermédiaires, cisaillement transversal, formulations et synchronisation restent à examiner. Le maximum dans toutes les fibres d’une poutre n’est pas obtenu.

Il manque une construction du radôme et de ses fixations, les propriétés et épaisseurs propres aux différentes pièces, la dépendance à la vitesse de déformation, des lois de rupture identifiées, l’autocontact et le contact des moteurs, une convergence spatiale et la réponse des planchers/noyau. La dégénérescence du nez doit être traitée par une représentation et une méthode défendables, pas par un seuil d’érosion choisi pour prolonger ou rapprocher le résultat attendu. Les fractions ou sensibilités de cas ne sont pas des probabilités de l’événement réel.

La localisation en flexion après fracture complète reste non validée. Une température imposée n’est pas un incendie calculé. La réussite de tests numériques ne valide pas l’effondrement réel. Blender reste visualisation tant qu’il n’est pas relié à des états mécaniques vérifiés. A04 ne calcule aucun incendie ni effondrement.

## Reproductibilité et reprise

OpenRadioss v20260728-win64, Engine marqué /VERS/2026, deux threads par cas, versions et hashes des exécutables dans chaque journal. Histoires toutes les 0,01 ms, animations toutes les 0,1 ms, timeout principal 300 s. Il y a 9 nouveaux départs principaux au total (la tentative r0 incluse), 6 observations auxiliaires à matériaux inchangés, 9 Starter et **zéro ancien calcul relancé**. Quatre des huit cas r1 atteignent leur horizon demandé, dont un des cinq cas plastiques avec contact. Les autres sont des résultats partiels explicitement bornés.

Les paramètres restent dans aircraft_a04_predeclaration.json ; decks, scripts, journaux, animations binaires, reprises, CSV, NPZ, premières interprétations et relecture corrigée sont conservés. La source des résultats à reprendre est **cached_review/review.json**. complete_aircraft_a04.py verify relit les hashes et le harnais sans calcul de dynamique.

AIRCRAFT-A05 : améliorer le nez/radôme dans le modèle d’avion entier à partir de sources primaires et de variantes explicites, puis reprendre un départ intact. Traiter la dégénérescence du maillage et le besoin d’autocontact sans érosion ni mass scaling arbitraires ; conserver les comparaisons A03/A04 et le bilan local ouvert. Ne pas choisir H=0,02E simplement pour atteindre 2 ms et ne pas forcer un résultat NIST. Préserver V11F et la branche thermique différée.

Après enregistrement, le registre contient 123 itérations historiques, dont A01–A04 pour l’avion entier ; ce compteur ne mesure pas une fidélité physique. Publication GitHub : A02+A03 déjà vérifiée, A04 première itération en attente (1/2), prochaine paire A04+A05. Aucune écriture GitHub n’est requise pour A04 seule.
