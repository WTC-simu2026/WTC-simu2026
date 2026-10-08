# AIRCRAFT-A13 — énergie, contact alternatif et formulation triangulaire

Treize nouveaux calculs principaux et treize reprises observateur se terminent normalement, sans avertissement Starter. Aucun ancien calcul relancé. L'intégrité du harnais et des fichiers passe ; la qualification scientifique globale reste échouée. La fenêtre du radôme reste **0,4 ms = 0,0004 s**.

Le contact TYPE25 ferme le bilan énergétique sur quatre maillages et un demi-pas du nez isolé. Entre les deux maillages les plus fins, l'impulsion varie encore de **23.53 %** et l'énergie générée de **38.30 %** : seuils de 10 % échoués. TYPE25 n'est donc pas encore transférable à l'avion complet. Le remplacement C0 par DKT18 en gardant TYPE7 conserve un déficit local. L'amélioration énergétique est une discrimination numérique, pas une sélection de contact pour l'événement historique.

## 1. Faits directement observés ou transcrits

13 Starter sans erreur ni avertissement, 13 terminaisons principales normales, 13 reprises de fin isolées. Les CSV sont vérifiés contre tous les records binaires natifs T01. Le premier record T02 donne la fin principale réelle, mais les réactions de cette reprise sont exclues des critères d'appui : le cumul REAC s'y réinitialise. REAC principal et FNX/FNY/FNZ sont traités comme impulsions cumulées, sans réintégration. L'observation ici concerne les fichiers solveur, aucun film historique.

Les masses nodales sont décodées indépendamment des animations ; positions, vitesses, identifiants et connectivité sont contrôlés. Pas d'ajout de masse, érosion, travail externe, travail plastique ou ressort dans ces témoins. Le premier agrégat authoritative_review.json a été produit pendant que le reste de la campagne tournait : il est conservé comme tentative incomplète et n'a jamais servi au registre. **campaign_review.json** est l'agrégat final des 13 cas, avec garde exigeant leur terminaison ; aucune qualification n'est tirée du premier agrégat.

## 2. Résultats d'un modèle officiel

Les dimensions et les entrées acier de la façade restent celles héritées de la chaîne NIST utilisée par A11. La façade tronquée et immobilisée n'est pas le bâtiment historique. Aucun dommage NIST ne sert de cible. Les résultats nouveaux sont ceux d'OpenRadioss installé v20260728, avec empreintes exécutables, durées et arguments dans les journaux ; ce ne sont pas des résultats d'impact NIST.

## 3. Affirmations provenant des archives locales

Aucune vidéo, photographie ou nouvelle source d'archive inspectée. Les **7240 fichiers antérieurs**, soit 34.64 Go, ont fait l'objet d'un nouveau contrôle SHA-256 complet en flux : zéro différence. La correction de sélection du manifeste parallèle déjà documentée en A12 est appliquée explicitement au point de départ, sans modifier le premier échec ni les sources. Le module Boeing parallèle v2 reste séparé ; inertie et dynamique libre encore bloquées. V11F/V11R et les branches différées sont conservées.

## 4. Hypothèses propres au modèle

Déclaration aircraft_a13_predeclaration.json, graine 1102038, zéro tirage. Radôme libre sans RBE3, restes d'avion, moteurs ni ADMAS. Les 216/864/3456/13824 triangles conservent la surface plane par morceau, les matériaux et la masse de 41,062724 kg. La façade conserve les 540 quadrilatères fixes d'A12. Vitesse [-200,5,2] m/s, gap 5 mm, sans frottement ; rupture, cœur écrasable, délamination et auto-contact absents.

TYPE25 est déclaré comme alternative à pénalité constante, avec groupe nodal secondaire, surface principale, Istf=4, Stfac=1, Igap=5, épaisseurs de contact secondaire/principale de 5 mm chacune à facteur 1, soit gap total 5 mm. Bord rond Ishape=2, Iedge=1000, Ipstif=0 et VIS_s=1e-20. Sa raideur, son traitement des bords et son algorithme diffèrent de TYPE7 : la comparaison ne distingue pas une cause unique. Ces choix viennent de [la documentation primaire TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm), sans ajustement sur des dégâts historiques.

Le contrôle coque remplace seulement Ish3n=2 par Ish3n=30 (DKT18) dans TYPE51 ; mêmes couches, orientation, géométrie, contact TYPE7 et amortissement déclaré. [La documentation TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm) décrit ces deux formulations. L'inertie numérique peut changer ; la formule c3inmas C0 n'est pas créditée à DKT18 sans preuve propre.

Témoin rapide : plaque LAW1 20×20×1 mm, masse 0,001112 kg, surface fixe 40×40 mm ; mouvement X seul et rotations bloquées. Départ x=-1,01 mm, gap 1 mm, vx=200 m/s. KE initiale 22,24 J, impulsion de rebond conservatif 0,4448 N·s. Horizon 0,02 ms. TYPE7 et TYPE25 aux facteurs de pas 0,05/0,025 ; pas libre distinct. Matériau E=70000 MPa, rho=0,00278 g/mm³, nu=0,3 synthétique, aucun crédit Boeing.

Ledger inchangé : KE + rotation globale + IE + hourglass + spring + contact élastique/frottement/amortissement − travail externe. Chaque terme une fois ; RKE par pièce ou reconstruit jamais ajouté. Critères radôme hérités A12 : résidu≤5 % énergie générée+1 J dès >100 J, global≤0,5 % initial, maillage≤10 % impulsion/énergie, demi-pas≤5 %/10 %. Témoin rapide : énergie et vitesse de rebond à 1 %, impulsion à 1 %, appuis à 2 %. Aucun seuil élargi.

## 5. Résultats dérivés

| Cas | Fin native ms | Impulsion X native N·s | Énergie générée J | Résidu final J | Critères échoués |
|---|---:|---:|---:|---:|---|
| WFREE | 0.02014394 | 0.000000 | 0.000 | 0.0000 | aucun |
| W7_DT050 | 0.02016439 | 0.422110 | 0.000 | -4.5576 | energy_global, rebound_or_free_velocity |
| W7_DT025 | 0.02003728 | 0.420936 | 0.000 | -4.6262 | energy_global, rebound_or_free_velocity |
| W25_DT050 | 0.02005611 | 0.445191 | 0.000 | 0.0009 | aucun |
| W25_DT025 | 0.02003423 | 0.444906 | 0.000 | 0.0019 | aucun |
| T25_L0 | 0.40015015 | -28.467640 | 4780.990 | 0.0177 | independent_translation_KE_change |
| T25_L1 | 0.40053213 | -23.997100 | 3502.315 | -0.0011 | aucun |
| T25_L2 | 0.40033016 | -16.891440 | 2965.401 | 0.0448 | aucun |
| T25_L3 | 0.40001148 | -12.922170 | 1822.796 | 0.0317 | aucun |
| T25_L2_HALF | 0.40014055 | -16.875470 | 2960.157 | -0.0152 | aucun |
| DKT7_L0 | 0.40109119 | -95.594750 | 3676.835 | -5892.4250 | energy_global, energy_local, momentum_contact_support, independent_translation_KE_change |
| DKT7_L1 | 0.40043467 | -26.937750 | 2469.752 | -1228.4680 | energy_local, independent_translation_KE_change |
| DKT7_L2 | 0.40001237 | -14.365470 | 1836.613 | -263.4625 | energy_local |

FNX est de signe positif pour la plaque allant en +X et négatif pour le radôme allant en −X : impulsion sur la surface principale, opposée au changement de quantité de mouvement du secondaire. Les appuis sont testés sur le seul historique principal. La fin de la table utilise l'observation de fin pour l'énergie, pas ses REAC.

| Comparaison | Nature | Δimpulsion % | Δénergie % | Critères impulsion/énergie |
|---|---|---:|---:|---|
| T25_L0 / T25_L1 | mesh | 16.59704 | 27.12815 | False/False |
| T25_L1 / T25_L2 | mesh | 29.46948 | 15.06493 | False/False |
| T25_L2 / T25_L3 | mesh | 23.53376 | 38.29693 | False/False |
| DKT7_L0 / DKT7_L1 | mesh | 71.65477 | 32.17513 | False/False |
| DKT7_L1 / DKT7_L2 | mesh | 46.36293 | 25.55957 | False/False |
| T25_L2 / T25_L2_HALF | half_dt | 0.09276 | 0.00186 | True/True |
| W7_DT050 / W7_DT025 | witness_half_dt | 0.27803 | 0.30851 | True/True |
| W25_DT050 / W25_DT025 | witness_half_dt | 0.06397 | 0.02795 | True/True |

Pour les témoins rapides, la dernière colonne énergie est la variation du maximum de résidu divisée par KE initiale, avec seuil 0,5 % ; elle n'est pas la variation d'énergie générée quasi nulle. TYPE7 peut passer la comparaison de demi-pas tout en échouant le budget absolu : au demi-pas, résidu -4.6262 J, soit 20.80 % de KE initiale. TYPE25 passe le rebond aux deux pas ; au demi-pas, résidu final 0.001920 J.

Sur TYPE25 radôme, tous les bilans locaux passent. Le maximum |résidu|/énergie générée dans la fenêtre >100 J reste inférieur à 0.0647 %. T25_L0 échoue encore la comparaison brute de KE nodale, conservée sans correction. Le demi-pas T25_L2 change l'impulsion de 0.09276 %, mais le raffinement spatial de 23.53 % : stabilité temporelle et spatiale sont distinctes.

Décalage temporel, diagnostic pré-déclaré : enregistrer [les accélérations natives TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm), puis comparer séparément v, v−dt·a/2 et v+dt·a/2, avec le TIME STEP natif de chaque ligne. Pour T25_L0, erreur maximale de variation KE 33.929401 J brute → 0.130717 J avec +demi-pas ; différence de rotation globale 0.091417 J → 0.000000556 J. Les autres cas et les deux signes restent dans les JSON. Ce résultat soutient un décalage natif ; il n'est pas une preuve d'équivalence entre source c3inmas sauvegardée et binaire installé. Aucun critère raté n'est reclassé, aucune énergie n'est ajoutée, la dynamique RKE reste non qualifiée.

DKT18 + TYPE7 garde un résidu final -263.463 J au niveau 3456 et échoue le critère local. Changer de triangle ne suffit donc pas à fermer le budget dans cette famille de témoins. La cause énergétique unique n'est pas établie, et la convergence TYPE25 reste à traiter.

## 6. Contradictions et informations manquantes

Énergie TYPE25 fermée, convergence spatiale échouée : ces deux constats sont conservés ensemble. La raideur de pénalité et le nombre de nœuds actifs varient avec le maillage ; leur relation à l'aire tributaire reste à tester sur une plaque analytique. Les formulations et traitements de bord différents empêchent d'attribuer le gain à un seul paramètre. Les coefficients de contact ne sont pas identifiés comme paramètres physiques réels.

Géométrie graphique, matériaux sandwich hypothétiques, racine libre et façade fixée ne représentent pas l'avion en impact réel. Rupture, écrasement, délamination, carburant et dynamique complète ne sont pas calculés. Une fermeture d'énergie sur ce témoin ne valide ni pénétration historique, ni feu, ni effondrement. L'animation utilise les états natifs ×1 et affiche les millisecondes ; sa lecture est ralentie, sans valeur dynamique propre. Syntaxe et données vérifiées, rendu interactif non certifié.

AIRCRAFT-A14 : réutiliser A12/A13 sans relance ancienne. Tester l'objectivité spatiale du contact sur une plaque élastique plane à 200 m/s, avec masse/aire/gap fixes et raffinements indépendants : contrôler le nombre de nœuds actifs, la raideur de pénalité nodale et sa relation à l'aire tributaire. Déclarer séparément tout contact pondéré par aire, sans choisir Stfac sur un dommage NIST. Qualifier les bilans énergie/impulsion et le demi-pas avant de réessayer le radôme. Vérifier la convention temporelle v + dt*a/2 à partir des sorties natives et de la source exacte, sans décaler le ledger ni crédit rétroactif. TYPE25 ferme l'énergie mais sa variation spatiale de 23,53 % reste échouée ; DKT18/TYPE7 ne ferme pas l'énergie. Aucun allongement avion complet avant fermeture locale et convergence spatiale. Module Boeing parallèle v2 séparé, inertie/dynamique libre bloquées. Premières secondes, écrasement, rupture et impact historiques non qualifiés.

Reprise : campaign_review.json, scientific_assessment.json, scripts conservés, manifeste et handoff. Publication A12+A13 selon cadence déjà autorisée, avec échecs et anciennes archives conservés ; l'intégrité de publication reste distincte de la physique.
