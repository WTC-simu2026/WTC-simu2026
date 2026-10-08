# AIRCRAFT-A12 — premier contact du nez, énergie et maillage

A12 est terminée comme campagne de diagnostic reproductible : 12 nouveaux calculs principaux, dont un premier essai libre conservé avec instrumentation rejetée, puis 11 cas instrumentés et 12 observations de fin séparées. Aucun ancien solveur relancé. Les contrôles d'intégrité passent ; l'ensemble des critères numériques ne passe pas. La fenêtre reste environ **0,4 ms = 0,0004 s**. Les premières secondes de l'impact réel ne sont pas calculées.

Le défaut énergétique se reproduit sans le reste de l'avion, sans RBE3 et avec un témoin LAW1 simple. Le sandwich LAW25 et la redistribution RBE3 ne sont donc pas nécessaires à ce défaut dans cette famille de témoins. Cela ne démontre pas leur innocuité dans l'avion couplé ni une cause unique. Les déficits diminuent au raffinement, mais l'impulsion varie encore de **44.34 %** entre les deux maillages les plus fins : le contact n'est pas convergé.

## 1. Faits directement observés ou transcrits

Onze Starter sans erreur ni avertissement et onze terminaisons Engine normales dans la révision instrumentée r1. Les terminaisons du premier essai r0 restent conservées. Toutes les valeurs CSV acceptées sont comparées aux records binaires T01 ; la première ligne native T02 fournit l'instant final réel. Les déplacements, connectivités, vitesses et masses nodales des animations sont lus indépendamment, puis archivés en SI. Aucun ajout de masse, aucune érosion, aucun travail externe ni travail plastique dans ces témoins.

Le radôme isolé a une masse 41.062723785 kg ; aucun appoint ne remplace les réserves de l'avion retiré. Son premier contact survient autour de 0,225 ms. Les instants sauvegardés suivent les pas effectifs du solveur : demander 0,0005 ms de sortie ne crée pas des états sous le pas natif. Chaque horizon est un départ neuf intact.

Réactions d'appui : les historiques principaux REAC sont des impulsions cumulées. À la reprise observateur, leur cumul se réinitialise. Les premiers bilans r1 utilisaient cette dernière ligne et restent conservés dans review.json ; authoritative_review.json contrôle les réactions sur **l'historique principal seulement**, indique sa borne temporelle et conserve le saut observé. Aucun cumul de fin n'est inventé ; aucun REAC n'est réintégré comme une force. Les erreurs restantes des cas grossiers restent échouées.

## 2. Résultats d'un modèle officiel

La portion de façade et l'acier héritent des entrées nominales NIST utilisées dans A11 ; dépendance des entrées maintenue, aucun résultat de dommages NIST employé comme cible. La portion présente est découpée puis immobilisée : les résultats de ce témoin ne sont ni les résultats NIST ni une validation du WTC réel. Les sorties sont celles d'OpenRadioss v20260728 installé ; les exécutables, arguments, durées, versions et empreintes sont consignés dans les journaux d'exécution.

## 3. Affirmations provenant des archives locales

Aucune nouvelle inspection vidéo/photo, aucun scan d'archive et aucune modification de source. 6598 fichiers antérieurs, sources et livraisons parallèles sont vérifiés par SHA-256. Le premier scan complet de 31,36 Go a révélé deux références héritées du manifeste parallèle r0 : integration_ready.json et finalize_r0.log. Le manifeste r1 déjà présent donne les empreintes exactes des deux fichiers, modifiés le 7 octobre avant la déclaration A12. Leur contenu n'a pas été changé : preservation_initial_conflicts.json et preservation_baseline_correction.json conservent le premier échec et la correction de sélection du manifeste, puis les deux SHA-256 canoniques sont revérifiés. Les 6596 autres résultats du scan complet sont réutilisés. V11F/V11R conservées ; branches V11S et I02I-M différées. Manifestes A11, sources c3inmas.F déjà sauvegardées et données Boeing parallèles réutilisés en lecture seule.

Le module Boeing parallèle v2 est effectivement livré : douze ports aile–pylône–moteur, six témoins constitutifs / 96 contrôles, trois candidats natifs. Son Starter avion conserve douze avertissements d'inertie ; le contrat d'inertie zéro et la dynamique libre restent bloqués. Revue enregistrée dans parallel_module_review.json ; aucune intégration, aucun changement implicite de matériaux ou budgets de masse.

## 4. Hypothèses propres au modèle

Déclaration aircraft_a12_predeclaration.json, graine 1102037, zéro tirage. Extraction exacte des 216 triangles du radôme A11, racine libre. Aucun fuselage, RBE3, ADMAS, poutre ou moteur dans ce témoin. Façade : seuls les segments frontaux x=-50 mm dont les centroïdes satisfont |Y|,|Z|≤3000 mm sont retenus ; 540 quadrilatères, tous leurs nœuds fixés. Ce retrait change les conditions mécaniques et ne donne aucun droit d'extrapoler à l'avion.

Sandwich LAW25 / TYPE51 / TYPE19 conservé avec peaux de 0,5 mm et cœur de 8 mm ; rupture, écrasement de cœur, délamination et auto-contact absents. Vitesse hypothétique [-200,5,2] m/s. Le témoin LAW1 à E=22000 MPa, nu=0,25 et épaisseur 9 mm conserve la masse surfacique, avec rho=(0,00183×1+0,000048×8)/9 g/mm³. Il ne conserve pas les raideurs de membrane, flexion et cisaillement du sandwich et n'est pas un substitut matériau Boeing.

Contact TYPE7 : gap constant 5 mm, Stfac=1, friction=0, VIS_s=1e-20 ; Istf=4 ou 5 testés séparément. [La documentation primaire TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) distingue la raideur minimale et la mise en série ; aucune variante n'est sélectionnée sur un dégât historique. Iform=2 concerne la formulation du frottement, ici nul. Les coefficients de viscosité ne sont pas modifiés pour faire passer un budget.

Chaque subdivision coupe les trois côtés en deux et crée quatre triangles coplanaires. Les niveaux 216/864/3456/13824 triangles conservent aire, forme plane par morceau, matériau et masse surfacique ; le partage nodal et les inerties numériques changent et sont contrôlés. Aucune projection sur une nouvelle forme lissée. Les quatre essais supplémentaires ont été déclarés avant exécution dans spatial_extension.json après les échecs r1.

Énergie globale = KE + RKE global + IE + hourglass + spring + contact élastique/friction/amortissement - travail externe. Chaque terme est compté une fois ; spring=0 dans les témoins. Le travail plastique est déjà dans IE. RKE par pièce et reconstruction indépendante ne comblent jamais le résidu. Les seuils A11 sont conservés séparément. Le témoin A12 utilise un contrôle plus précis : |résidu|≤5 % énergie générée+1 J dès énergie générée>100 J, global≤0,5 % KE initiale ; impulsion/appuis≤0,01 N·s+2 % impulsion. Demi-pas : 5 % impulsion / 10 % énergie ; maillage : 10 % / 10 %. Ni tolérance ni matériau modifiés après calcul.

## 5. Résultats dérivés

| Cas | Fin native ms | Masse radôme kg | Jx façade N·s | Énergie générée J | Résidu final J | Critères échoués après contrôle de reprise |
|---|---:|---:|---:|---:|---:|---|
| FREE | 0.401100338 | 41.062724 | 0.000000 | 0.000 | -0.044 | aucun |
| SAND | 0.402292520 | 41.062724 | -100.284008 | 8611.210 | -5928.354 | energy_global, energy_local, momentum_contact_support, independent_translation_KE_change, independent_momentum_change |
| SAND_HALF | 0.400642931 | 41.062724 | -98.743906 | 8492.840 | -5927.364 | energy_global, energy_local, momentum_contact_support, independent_translation_KE_change |
| SAND_FINE | 0.400425941 | 41.062724 | -56.122906 | 6512.997 | -1469.767 | energy_local |
| SAND_SERIES | 0.400177389 | 41.062724 | -98.629016 | 8442.170 | -5935.730 | energy_global, energy_local, momentum_contact_support, independent_translation_KE_change |
| SIMPLE | 0.400310755 | 41.062722 | -420.830000 | 51946.031 | -4737.021 | energy_global, energy_local |
| SIMPLE_FINE | 0.400052458 | 41.062722 | -229.310250 | 27838.527 | -902.381 | energy_local |
| SAND_FINE2 | 0.400048524 | 41.062724 | -32.121734 | 4328.405 | -292.951 | energy_local |
| SAND_FINE2_HALF | 0.400002152 | 41.062724 | -32.115867 | 4327.281 | -292.475 | energy_local |
| SAND_FINE3 | 0.400153250 | 41.062724 | -17.748859 | 2065.549 | -53.599 | energy_local |
| SIMPLE_FINE2 | 0.400081992 | 41.062722 | -84.716578 | 15021.568 | -151.660 | energy_local |

| Comparaison | Nature | Temps commun ms | Δimpulsion % | Δénergie % | Critères impulsion/énergie |
|---|---|---:|---:|---:|---|
| SAND / SAND_HALF | half_dt | 0.3996810 | 1.43125 | 0.04952 | True/True |
| SAND_HALF / SAND_FINE | mesh | 0.3996810 | 43.27717 | 23.29782 | False/False |
| SAND_FINE / SAND_FINE2 | mesh | 0.3997297 | 42.53026 | 33.15036 | False/False |
| SAND_FINE2 / SAND_FINE3 | mesh | 0.3995990 | 44.34107 | 52.32262 | False/False |
| SAND_FINE2 / SAND_FINE2_HALF | half_dt | 0.3995247 | 0.01686 | 0.00201 | True/True |
| SIMPLE / SIMPLE_FINE | mesh | 0.3995632 | 45.05693 | 46.38629 | False/False |
| SIMPLE_FINE / SIMPLE_FINE2 | mesh | 0.3995486 | 62.87365 | 46.07811 | False/False |
| SAND_HALF / SAND_SERIES | contact_stiffness_formulation | 0.3992122 | 0.10033 | 0.18681 | None/None |

Les comparaisons utilisent le plus petit instant commun des historiques principaux, borné à 0,4 ms ; les réactions de reprise sont exclues. À 3456 triangles, le demi-pas donne Δimpulsion=0.01686 % et Δénergie=0.00201 %. Les contrôles temporels passent, les contrôles spatiaux restent échoués. Le changement Istf minimal/série est faible dans cette configuration et ne ferme pas le déficit.

Le résidu final sandwich passe d'environ -5927 à -1470, -293 puis -53.599 J au raffinement. Au niveau le plus fin, le ratio final vaut 2.595 %, mais le maximum dans la fenêtre d'énergie générée>100 J vaut 38.576 % : **un ratio final seul masquerait le contrôle local échoué**. Certaines variantes fines passent le seuil A11 moins strict dans le témoin isolé ; cela ne qualifie ni le contact spatial ni l'avion couplé.

Inerties initiales : masses lumpées pondérées par les angles, centres de gravité et tenseurs Starter sont vérifiés indépendamment. L'algorithme sauvegardé c3inmas.F ajoute aux inerties de levier la contribution scalaire des triangles et des couches intégrées ; aucune inertie physique n'est assimilée à cette inertie numérique. Erreur relative maximale de tenseur=4.412e-09, inférieure à 1e-6 dans tous les témoins. Exemple libre : CG natif [1.05383601, 1.06314783e-17, -3.66786003e-17] m et diagonale du tenseur natif [74.0463793, 53.4185068, 49.1885026] kg·m². [TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm) décrit l'empilement ; l'algorithme de masse/inertie propre au binaire est confronté à ses valeurs sauvegardées, sans équivalence complète source/binaire démontrée. L'accord initial ne qualifie pas la reconstruction dynamique RKE ; les écarts et les vitesses rotationnelles restent sauvegardés.

Durée native cumulée de tous les essais, observateurs et convertisseurs=142.774 s, deux threads CPU, aucun GPU. Les étapes Python de construction et revue sont distinctes et leurs produits/scripts conservés. Il n'y a eu aucun calcul susceptible de durer des heures. Cette campagne courte ne fournit pas une estimation fiable d'un impact déformant de plusieurs secondes.

Visualisation : visualisation/premier_contact.html utilise les états natifs SAND_FINE2_HALF avec déplacements ×1, temps physique ms et lecture ralentie. visualisation/bilans_maillage.svg compare les quatre maillages sandwich. Données finies, indices, temps et syntaxe JavaScript contrôlés ; le rendu graphique interactif n'est pas encore certifié. La vue ne représente pas un avion complet ni une validation physique. États/bilans et inerties dans r1/*/*.npz ; rapports initiaux et corrigés conservés côte à côte.

## 6. Contradictions, informations manquantes et suite

La cause unique du déficit n'est pas identifiée. Une dépendance au maillage de la pénalité de contact, la formulation triangulaire, les inerties rotationnelles et le décalage temporel des sorties restent à départager. La perte existe aussi avec LAW1 : l'accuser exclusivement du sandwich serait injustifié. Les petits écarts indépendants KE/quantité de mouvement des mailles grossières restent échoués, sans recalage a posteriori.

Erreurs conservées : r0 libre terminé mais nombre de records mal décrit ; deux tentatives de lecture rejetées, réactions Y/Z dépassant les dix colonnes demandées. output_schema_extension.json déclare r1 avec deux groupes de nœuds séparés ; aucun ancien fichier ni résultat natif écrasé. Les premiers reviews r1 ont utilisé les réactions réinitialisées de l'observateur ; la revue corrigée les sépare explicitement et préserve tous les échecs physiques. Le premier contrôle de préservation contre le manifeste parallèle r0 obsolète est conservé et corrigé par sélection du manifeste r1 existant, sans réécriture du module. Les sources héritées ne sont pas réinterprétées comme matériaux historiques.

AIRCRAFT-A13 : repartir des sorties A12, sans relance ancienne. Discriminer la dépendance à la maille du contact TYPE7 et de la formulation triangulaire du radôme : témoin de contact à grande vitesse, option de contact alternative documentée et contrôle de formulation déclaré séparément. Contrôler le décalage temporel des vitesses/énergies et les inerties rotationnelles sans ajouter de terme au ledger. Garder les réactions REAC principales séparées du redémarrage observateur. Aucun allongement avion complet avant fermeture locale et convergence spatiale. Module Boeing parallèle v2 reçu mais contrat inertiel/dynamique libre bloqué ; ne pas l’intégrer silencieusement. Premières secondes, écrasement, rupture et impact historiques non qualifiés.

Le cycle local de publication reste A12 seule en attente de la paire A12+A13. A10+A11 déjà enregistrées comme publiées dans le cycle ; aucune republication, aucun envoi externe, aucun X/Yoremi. L'impact et l'effondrement historiques restent non qualifiés ; température imposée distincte d'un incendie calculé ; Blender demeure une visualisation.
