# Reprise WTC 1 après V11C

Lire AGENTS.md et harness/state.json, puis lancer le contrôle du harnais depuis le dossier actif. V11C est terminée ; prochaine V11D. Ne pas repartir de l'ancien V10J/V8H, relire toute l'histoire ou rescanner l'archive. Les documents manquants ne bloquent pas les prototypes exploratoires explicitement étiquetés demandés par Jeremy.

## Résultat et périmètre

V11C remplace le lien axial parfait de dalle V11A par une ligne de dalle comprimée à déplacement propre et des ressorts de glissement horizontal. Paire symétrique équivalente : 33 nœuds de treillis, 63 barres, 17 déplacements axiaux de dalle, 16 segments de dalle, 17 stations de liaison, 83 degrés de liberté. Le cas roulant comporte 99 termes mécaniques ; le cas retenu 100. Les stations représentent 32 knuckles équivalents supposés, pas un inventaire as-built. La largeur chargée est 80 in, portée 713 in, 16 panneaux Warren supposés, Fy36 ksi et diamètre uniforme1,09 in. Ces hypothèses restent celles de V11A.

22 parcours, 429 états publiés ; 15 premiers seuils (6 attaches, 4 tractions d'appui, 5 membrures supérieures) ; 7 parcours terminent sans franchir les critères vérifiés. Ce sont des comptes de variantes, jamais des probabilités historiques. Six diagnostics de retrait de liaisons sont rééquilibrés au même chargement : tous dépassent ensuite un autre seuil d'attache, donc aucune continuation physique n'est revendiquée.

74/74 contrôles : 32 tests analytiques indépendamment rédigés, 30 régressions d'assemblage, 12 contrôles de parcours/répétition/raffinement. Le pas divisé par deux donne le même premier seuil à moins de2e-7 en paramètre. Dans les parcours/diagnostics, résidus max équilibre9,68376e-13 et identité énergétique4,37966e-12. La dilatation libre analytique complète a séparément un écart d'identité inférieur à1e-9J. Durée CPU10,39s comprenant répétition et raffinement, Python3.14.3/NumPy2.4.6, aucun logiciel installé/GPU/Blender.

## Sources et hypothèses

Lecture bornée NCSTAR1-6C, imprimées61-68 / PDF109-116 local ; tableau5-7 imprimée67 / PDF115 contrôlé visuellement par le principal et un lecteur distinct. Capacité longitudinale PAR knuckle :30/24/19/15kip pour température moyenne BÉTON20-300/450/600/750°C. Ce sont estimations NIST fondées essais/calculs/jugement thermique, pas essais incendie des pièces réelles. Ne pas substituer la température acier ou gaz. Les valeurs d'arrachement vertical sont transcrites mais non activées.

Raideurs1/10/100MN/m par attache équivalente et facteurs de résistance0,05/0,25/1 sont supposés. Le facteur ne réduit pas aussi la raideur et ne représente pas un dommage calculé de l'avion. La densité hypothétique2/(713/16in) est conservée lorsque le nombre de panneaux change ; ressorts pondérés par longueurs tributaires, demi-poids aux extrémités. Les capacités, Ec/fc et détail béton du prototype n'ont pas été calibrés ensemble : dépendance de source et hypothèses restent distinctes.

Sièges hypothétiques intérieur15 / extérieur1013, capacités appliquées une fois à la paire. Raideurs verticales et horizontales100MN/m par paire. Ressort horizontal droit réellement absent pour le rouleau. Les capacités H ne s'appliquent qu'en TRACTION signée ; compression non vérifiée et interactionV-H inconnue. L'extension thermique peut pousser les supports sans franchir leur capacité de traction, mais ce n'est pas une vérification de compression.

La dalle est axialement comprimée seulement : lorsqu'un segment s'ouvre, retirer ensemble sa rigidité et sa force thermique ; effort/énergie en traction nuls. Son déplacement vertical reste celui du treillis. Pas de flexion de dalle, armatures, fissuration détaillée, contact vertical ni arrachement. Le décalage de dalle dans le schéma est uniquement graphique et n'ajoute aucun bras de levier.

Aucun contreventement latéral de membrure supérieure n'est crédité par le seul ressort de glissement. Min(Euler,écrasement) reste un écran nominal ; pas de postflambement, plasticité ou suppression de barre. Géométrie et directions sont fixes ; pas de chaînette, inertie ou fluage. Les températures uniformes dans chaque famille sont imposées20-600°C, sans horloge ni feu. Coefficients constants de dilatation12e-6 acier /10e-6 béton parK supposés.

## Équations et arrêt

Chaque terme utilise N=k(Bu-e0). Pour le béton seul : N=k min(Bu-e0,0). La résolution à ensemble actif vérifie complémentarité et rang, sans pénalité artificielle ; un degré libre déconnecté est signalé comme problème statique non résolu, pas comme effondrement. Énergie U=somme(N²/2k) sur termes actifs. Identité d'état2U=u·f+u_prescrit·réaction−somme(N e0), e0 comprenant dilatation ou position d'ancrage. Ce n'est ni un bilan de chaleur ni une intégration dynamique lorsque E(T) change.

Les parcours s'arrêtent au premier seuil détecté par encadrement puis dichotomie. En température, le raffinement de pas réduit le risque de saut mais n'exclut pas tout pic non échantillonné. Au seuil d'attache, retrait horizontal seulement et diagnostic séparé à même charge. Énergie de ressort retiré, différence d'énergie avant/après et dissipation dynamique sont trois notions distinctes ; la dernière reste null. Tous les diagnostics de retrait livrés dépassent une nouvelle limite d'attache et sont explicitement non admissibles comme continuation.

## Résultats illustratifs, non critères du bâtiment réel

Référence froide K10MN/m, facteur de résistance1, rouleau : flèche47,446mm et glissement2,441mm à80psf ; réaction70,480kN par siège (15,844kip). Les limites Kfaible/Kfort retrouvent les déplacements V11A acier seul/dalle axiale idéale à environ8,85e-6 d'erreur relative, après retrait du tassement d'appui.

À demi-charge : UNIFORM_ROLLER atteint600°C sans franchir les critères vérifiés ; UNIFORM_RESTRAINED atteint un écran de membrure supérieure à122,753°C ; STEEL_HOT_SLAB_COOL l'atteint à108,622°C acier/47,503°C dalle. SUPPORT_OPENING_COLD atteint le seuil de traction intérieure à6,137mm d'ancrage. Les faibles seuils des cas retenus dépendent notamment des appuis supposés et de l'absence de maintien latéral crédité. Ne pas les appeler températures critiques réelles. Un maximum de sollicitation inférieur au seuil n'est pas un seuil atteint : cette erreur de libellé graphique du premier brouillon a été corrigée.

## Livrables et reprise

Dossier wtc1_simulation_v8/output/v11c_floor_panel : rapport_v11c_plancher.md, results_v11c.json, synthese_v11c_plancher.png, panel_inventory.json, path_summaries.csv, path_history.csv, first_events.csv, terminal_component_forces.csv, terminal_displacements.csv, bond_release_diagnostics.json, numerical_audit.json, source_manifest.json, source_table_5_7.png, offline_manifest.json, release_audit.json.

Configuration data/v11c_floor_panel_predeclaration.json. Scripts v11c_panel_model.py, run_v11c_floor_panel.py, test_v11c_independent.py, test_v11c_regression.py dans scripts/. Le runner refuse le dossier existant : essais seulement dans de nouveaux sous-dossiers tmp/v11c_floor_panel/. Deux brouillons conservés attempt01/attempt02. Empreinte numérique commune :5e5aa2c46f754c342e9df7bab9409f24f4631a32439a7ee0ac36407ab88662f4.

13 sorties hachées (hors manifeste lui-même et audit de livraison ajouté ensuite),11 entrées/protégés,5 fichiers code/configuration,13 anciennes entrées V11A vérifiés séparément. La source PDF locale fait8 363 877octets ; l'URL actuelle, trop grande pour le lecteur web, n'a pas remplacé cette copie conservée. La relecture indépendante a fourni les recommandations mécaniques, la vérification source et32tests analytiques ; la revue finale complète de code/exécution a été faite par le principal, pas par un second auditeur complet.

## Prochaine V11D

Ajouter et vérifier la flexion de dalle ainsi que son contact/arrachement vertical dans un panneau borné : appui comprimé et décollement distingués, charges/apports d'armatures hypothétiques explicitement séparés, tests analytiques et limites d'ouverture avant transfert spatial. Ne pas confondre ce contact vertical avec un maintien latéral complet. Puis géométrie non linéaire et réponse après premier seuil, liens avec colonnes/allèges et couplage progressif aux composants spatiaux.

V11A/V11B et le master Blender restent intacts. Aucun V11C n'alimente le calcul global ni le film V10Z. La trajectoire du Boeing767, sa rupture, ses dommages induits, le feu et le champ thermique restent à calculer indépendamment. L'objectif demeure une simulation exploratoire sans effondrement ou non-effondrement imposé.
