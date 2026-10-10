# AIRCRAFT-A18 — impact couplé20ms avec séparation du radôme et vidéo3D

Un nouvel impact natif couvre **20.000261300 ms physiques**, à partir d'un avion intact. Les facettes du nez peuvent maintenant se détacher par rupture de liaisons natives ; leur masse n'est pas retirée. Le MP4/GIF rend ces sorties à échelle1. **L'objectif utilisateur de10 secondes physiques reste actif et incomplet.** Le modèle demeure exploratoire et ses critères échoués sont conservés.

## 1. Faits directement observés ou transcrits

Configuration immutable, graine1102043, zéro tirage. Géométrie générée :42699 nœuds,600 contraintes d'offset RBE2,624 liaisons cohésives sur les arêtes internes de216 triangles de radôme. Les944 appuis aux bords de la façade déformable sont conservés. Un seul nouvel impact entier, aucun ancien Engine relancé. Fin normale, 1090.437 s de calcul sur deux threads CPU. Plafond2700s annoncé avant lancement ; aucun calcul GPU.

Starter : zéro erreur et deux avertissements1166/343, tous deux pour l'interface d'autocontact2,576 coins non racinaires coïncidents. **Le critère initial zéro avertissement a échoué et reste faux.** Un contrôle séparé avant Engine a confirmé leur périmètre déclaré et autorisé seulement le diagnostic borné ; il ne remplace pas une qualification physique du contact. Deck et paramètres non modifiés après Starter. Les sources et anciens résultats sont restés intacts :11225 fichiers, 45.077Go vérifiés par SHA-256.

Les enregistrements de tous les canaux d'histoire CSV ont été comparés au binaire natif ; le redémarrage observateur isolé donne le temps et l'énergie de fin. Ses réactions et impulsions de contact ne sont pas mélangées avec l'histoire principale. 21 poses contrôlées et rendues ; 189 images MP4 H.2642560×720,30Hz,6.300s de lecture ; GIF1280×360. Le film indique le temps physique, les ruptures et groupes détachés. Trois images décodées inspectées. La lecture interactive GUI n'est pas certifiée.

## 2. Résultats d'un modèle officiel et sources primaires

Solveur OpenRadioss v20260728-win64 déjà conservé. Aucun résultat officiel de dégâts n'est choisi comme cible. Les entrées nominales de la façade restent dépendantes de sources NIST comme dans A16 ; cette dépendance d'entrée ne rend pas les résultats indépendants de toute source officielle.

La documentation [RBE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm) définit une translation dépendante comprenant l'offset lié à la rotation de son nœud indépendant avec Iflag0. La [TYPE43](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm) admet des faces coïncidentes ; Ismstr4 est ici employé pour la géométrie mobile. La [LAW117](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm) fournit la cohésion et la suppression native. Ces définitions ne constituent pas des mesures du Boeing.

Avec [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm), Inacti1000 ignore les paires initialement pénétrantes et peut les réactiver après sortie puis retour. Ce traitement évite d'inventer une énergie initiale, mais ne garantit pas le contact d'un fragment qui s'est rompu tout en restant dans le jeu initial.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive vidéo, photographie ou PDF analysée. Les affirmations historiques des archives ne sont pas ajoutées au résultat mécanique. Les contrôles A17 de traction/cisaillement, de travail surfacique, recharge au même pic, aire et demi-pas sont réutilisés sans relance. Ils avaient qualifié une implémentation uniforme Ismstr1, pas le mode mixte, les rotations ou les propriétés du vrai radôme. Leurs limites restent présentes après le changement Ismstr4.

La première procédure Starter a arrêté son wrapper sur les deux avertissements attendus ; son journal et son gate faux sont conservés. Le contrôle complémentaire a été écrit avant tout Engine. Une erreur de sélection des sections d'avertissements dans le listing puis une conversion booléenne NumPy pour le rapport initial ont été corrigées dans les nouveaux scripts d'analyse. Après la fin normale de l'Engine, le premier lecteur a supposé15 blocs par état ; l'ajout d'une part ne créait pas de nouvelle famille de blocs. Les14 blocs réellement présents ont été lus et tous leurs canaux comparés au CSV, sans relance du solveur. Cet échec de récupération est conservé. La carte héritée TH/PART ne sélectionnait que IE/KE/HE/PW pour la cohésion, au lieu des neuf canaux annoncés ; **le critère de couverture à neuf reste échoué** et la configuration effective distincte documente l'écart. Aucune sortie solveur antérieure n'a été corrigée ou effacée.

## 4. Hypothèses propres au modèle

Chaque triangle du radôme possède ses coins de surface distincts, sauf la racine x2000mm qui reste liée au corps. Deux bandes de cohésion, chacune de largeur0,5mm, relient chaque arête interne aux peaux situées à±4..4,5mm. Aire par bande = longueur initiale d'arête×0,5mm. Les coins de bande sont liés à leur propre coin de facette avec RBE2, Iflag0 et translations111000. Densité cohésive1e−20g/mm² ; aucune masse instrumentale de témoin ni mass scaling ajouté. Surface, volume des couches, matériaux, masses et liaisons RBE3 d'origine conservés. La masse, le centre de gravité et l'inertie initiaux natifs sont comparés séparément au parent.

LAW117 : EN4400N/mm³, ET800N/mm³, TN450MPa, TT100MPa, GI=GII50N/mm ; Imass1,Idel4,Irupt1. **Énergies et résistance tangentielle non mesurées pour l'avion.** Ce sont des hypothèses déclarées reprises d'A17, sans adaptation au résultat. ORTHSTRAIN R20 demeure dans les peaux à l'intérieur des facettes ; travail de cohésion suivi à part mais déjà inclus une seule fois dans IE globale. Ce cumul de deux mécanismes n'est pas calibré comme un modèle réel de rupture du sandwich.

Le cœur8mm reste dans chaque facette ; **la traction entre arêtes de cœur n'est pas modélisée**. Fissures limitées aux arêtes initiales, effet du maillage non qualifié. Métaux/façade sans rupture physique identifiée ; pas de structure intérieure, gravité ou carburant résolu. Vitesse initiale[-200,5,2]m/s, propre au prototype et non déterminée pour l'AA11 historique. Les quatre contacts extérieurs TYPE25 gardent le jeu5mm et la rigidité hérités. L'autocontact du radôme devient TYPE25, jeu9mm, Inacti1000 ; pas d'autocontact de tout l'avion.

Pas de déplacement imposé au couplage. Facteur de pas0,5 hérité, TH0,01ms, animation0,2ms, revue géométrique toutes5 images plus dernière et fin observée. Les critères d'énergie/matériaux/quantité de mouvement A16 sont hérités ; tolérance nouvelle d'offset0,001mm déclarée avant exécution. Aucun critère élargi après réception du résultat.

## 5. Résultats dérivés

Masse totale native :191273.837942800kg. Le contrôle de masse nodale donne un écart parent de-5.52972779e-08kg ; écart d'inertie relative3.26136211e-09. Énergie cohésive et contrainte nulles dans le premier état. Énergie générée avant premier contact extérieur (0.230344ms) :4.801559e-24J. Erreur maximale de rayon d'offset, calculée sur les coordonnées **binaires** :0.00119489397mm. Les coordonnées VTK arrondies auraient artificiellement dégradé ce contrôle ; elles ne sont pas prises comme référence exacte.

À la fin :**624/624 bandes rompues**, 169 composantes du radôme dont **168 sans connexion à la racine**, comprenant168 facettes. Le graphe conserve une arête tant qu'au moins une de ses deux peaux reste liée ; les coins de racine partagés sont aussi reliés. Ces nombres sont des résultats du maillage et de la loi d'essai, pas un dénombrement de vrais débris. Toutes les coques porteuses de masse demeurent présentes ; seules les connexions de masse négligeable sont supprimées.

Somme finale des termes énergétiques autres que KE-19.683711MJ ; résidu global final-1568571.248000J, maximum2715669.900000J. **Cette somme est négative : ce n'est pas une énergie produite physiquement acceptable.** Le diagnostic natif isolé retrouve une IE du radôme négative à partir de12.970320ms, finissant à-42.148524MJ ; l'IE globale finale vaut-20.290988MJ tandis que KE augmente. Le défaut réside dans l'IE de la part radôme, sa cause exacte restant inconnue ; la cohésion a une IE positive. Cet examen de cohérence physique est ajouté comme diagnostic distinct, sans prétendre qu'il était un critère pré-déclaré. Le critère global normalisé par l'énorme KE initiale peut réussir et ne compense pas l'échec du bilan local ni l'IE négative.

IE du seul groupe cohésif final6804.502500J. Cette IE comprend stockage et dissipation ; elle n'est pas ajoutée à l'IE globale. PW et une RKE inventée ne compensent aucun déficit. Déplacement maximal échantillonné de façade742.435585mm. Impulsion principale finale de contact[-153295.4, 7567.901, -921.3503000000001]N·s.

| Critère déclaré | Résultat |
|---|---|
| native_binary_CSV | réussi |
| normal_termination | réussi |
| requested_horizon_reached | réussi |
| declared_connectivity | réussi |
| finite_states | réussi |
| all_supports_fixed | réussi |
| native_mass_expected | réussi |
| independent_native_mass_matches | réussi |
| native_nodal_mass_unchanged | réussi |
| no_added_mass | réussi |
| mass_bearing_shells_not_deleted | réussi |
| no_external_work | réussi |
| global_energy | réussi |
| local_energy | **échoué** |
| global_support_momentum | réussi |
| contact_facade_momentum | réussi |
| metal_material_domain | **échoué** |
| beam_material_domain | **échoué** |
| radome_face_reference_domain | **échoué** |
| independent_translation_delta_KE | réussi |
| independent_momentum | réussi |
| initial_native_gate | réussi |
| offset_rotation_distance_tolerance | **échoué** |
| zero_warning_gate | **échoué** |
| cohesive_part_history_present | réussi |
| zero_initial_cohesive_IE | réussi |
| cohesive_IE_nonnegative | réussi |
| cohesive_expected_nine_channels | **échoué** |
| no_generated_energy_before_external_contact | réussi |

Écart maximal de coordonnées Blender1.90734863e-06m ; aucune interpolation de géométrie, pas de physique Blender ou de déplacement amplifié. Chaque pose physique est tenue neuf images pour ralentir la lecture. Temps physique0.020000261307s, objectif10s. Projection linéaire du coût jusqu'à10s :6.310jours sur deux threads ; pas une ETA fiable, car contacts, ruptures et domaine structurel peuvent changer fortement.

## 6. Contradictions et informations manquantes

Critères échoués :local_energy; metal_material_domain; beam_material_domain; radome_face_reference_domain; offset_rotation_distance_tolerance; zero_warning_gate; cohesive_expected_nine_channels. Leur conservation interdit de présenter cet essai comme l'impact WTC1 validé. L'IE négative impose de diagnostiquer la déformation, la formulation des couches/cœur et les rotations/contraintes avant extension ; elle n'est pas attribuée sans preuve à une cause unique. La tolérance d'offset native échoue à0.00119489397mm et reste0,001mm. Les paramètres cohésifs et le cœur entre facettes manquent de mesures ; rotation/mode mixte ne sont pas qualifiés par les seuls anciens témoins. Le traitement d'initiale coïncidence ne certifie pas le contact des morceaux après rupture, et l'autocontact de l'ensemble avion est absent. Une ressemblance de l'image ne remplace aucun de ces contrôles.

L'horizon20ms est bien calculé, mais il ne couvre que0,02s sur les10s demandées. Avant les secondes suivantes, les limites métal/façade, les contacts des fragments, les planchers et le noyau, la gravité et les conditions historiques doivent être traités explicitement. Les sorties ne sont ni interpolées ni extrapolées pour remplir une durée absente. AIRCRAFT-A19 : objectif vidéo3D des10 premières secondes physiques actif/incomplet. A18 a intégré624 liaisons cohésives dans le radôme et effectué un impact20ms avec fragments natifs et MP4/GIF, mais l'IE native du radôme devient négative dès12,97032ms et finit à-42,148524MJ. Priorité immédiate : expliquer/corriger ce défaut avant prolongement. Lire negative_energy_diagnostic.json et les états/bilans déjà conservés ; séparer déformation de LAW25/TYPE51/cœur, cinématique de rotation et travail de contraintes, sans relancer A17/A18 ni inventer RKE ou G pour fermer un déficit. Le domaine métal/façade, l'autocontact et les interfaces restent également non qualifiés. Modifier la mécanique impose un nouveau départ intact et déclaré ; seuls des continuations inchangées peuvent réutiliser un checkpoint. Ensuite viser100ms,1s,10s selon le domaine atteint ; ajouter gravité/intérieur réellement modélisé avant les secondes, annoncer le coût avant calcul long, sauver des checkpoints et réduire les sorties sans mass scaling. Aucune cible historique. G50N/mm non mesuré, cœur aux arêtes absent, fissures restreintes aux triangles, contact initial Inacti1000 non qualifié, critère d'offset0,001mm échoué à0,001195mm et quatre canaux de part au lieu de neuf annoncés : conserver toutes ces limites. La vidéo est explicitement marquée bilan énergétique échoué, poses natives à échelle1. Publication A12+A13 intacte ; A14 à A18 en attente.
