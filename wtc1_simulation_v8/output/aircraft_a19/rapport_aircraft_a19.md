# AIRCRAFT-A19 — localisation du défaut du nez et comparaison native20ms

Un nouveau calcul couplé et son MP4/GIF couvrent **20.000217400ms physiques**. La formulation alternative réduit fortement le défaut mais ne le résout pas. **L'objectif des10 premières secondes physiques reste actif et incomplet.** Le bilan local, certains bilans par facette et les domaines matériels échouent encore.

## 1. Faits directement observés ou transcrits

Graine1102044, zéro tirage. Quatre déclarations complémentaires immuables précèdent les nouveaux contrôles, l'observateur et l'impact; la déclaration générale A19 précède l'analyse des sorties conservées. Aucun ancien impact relancé.101 états natifs A18 lus puis101 états du nouvel impact. Lecture indépendante des coordonnées, masses, vitesses, contraintes/déformations et énergie spécifique confrontée au convertisseur natif. Un observateur isolé de l'ancien checkpoint final fournit les neuf points de ply41/42/43 sans changer ce checkpoint ni les sorties principales.

La facette174 A18 porte-41,656353MJ à20ms, s'étire56,50fois et atteint152,40fois son aire initiale. Les12 facettes les plus négatives portent99,75% de l'énergie négative finale. Le champ legacy «layer2» nul ne pouvait pas être identifié comme le cœur: la demande explicite **ply42, point2** donne des déformations natives[3,982207;-1,101313;11,694304] et des contraintes[4,320553;-1,119560;10,704959]MPa. Les deux peaux ont dommage1 et le cœur dommage0. Les anciens zéros sont conservés avec une correction de leur interprétation, sans écraser l'analyse originale.

Un nouvel impact entier dure1042.308s sur2threads CPU, fin normale43187cycles. Géométrie, matériau, masse, épaisseur, résistances, G cohésif, contacts, appuis et vitesse[-200;5;2]m/s identiques àA18. Une seule carte mécanique change: TYPE51/21, Ish3n2→31. Les masses et moments initiaux passent les contrôles natifs et indépendants. Starter conserve les deux avertissements1166/343 associés aux576 coins d'autocontact initialement coïncidents; le critère zéro avertissement reste échoué.

La fiche locale Hexcel HRH10 p4 donne pour le produit de référence3.2-48: densité48kg/m³, E33=138MPa, G31=41/G23=24MPa, cisaillement1,21/0,69MPa, compression nue2,07MPa. Ces valeurs typiques sont mesurées avec une épaisseur12,7mm à température ambiante. Elles n'identifient pas le radôme historique ni une courbe dynamique de rupture.

## 2. Résultats d'un modèle officiel

Aucune sortie de dommages NIST n'est utilisée pour sélectionner les paramètres, les facettes ou le film. Les références Altair décrivent les commandes du solveur: [TYPE51](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm), [sorties explicites par ply](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_shell_idply_restype_engine_r.htm), [LAW25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm). Ce sont des spécifications et non des résultats de l'impact réel.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo ou photographie n'a été analysée. Le diagnostic s'appuie sur les fichiers natifs conservés, la fiche matériau déjà acquise et une inspection ciblée du code public. Les sources restent en lecture seule. La vérification SHA256 porte sur11476anciens fichiers, 46.970Go, sans modification constatée.

## 4. Hypothèses propres au modèle

Le sandwich0,5/8/0,5mm, ses orientations, le cœur élastique à faibles rigidités dans son plan et la fracture des peaux restent des hypothèses. G des arêtes50N/mm n'est pas mesuré. La façade couvre trois niveaux représentatifs, sans intérieur de tour, gravité, carburant résolu ni identification complète des conditions historiques. Les fissures suivent les arêtes de triangles et l'autocontact initial n'est pas qualifié.

Les témoins de cisaillement testent un cœur8mm seul, avec rayon de déclenchement min(1,21/41;0,69/24)=0,02875 et deux phases de dégradation de2% et20%: ce dernier choix est hypothétique, sans G mesuré. Ils ne sont pas transférés au modèle complet.

## 5. Résultats dérivés

Les quatre témoins de triangle réussissent: rotation rigide90° à énergie interne quasi nulle et traction biaxiale0,001 à énergie1,320832J, référence analytique1,320392J, pour Ish3n2 et31. Ces contrôles couvrent une rotation rigide et une petite déformation; ils ne qualifient pas un cœur écrasé ou étiré à plusieurs centaines de pour cent.

| Grandeur à20ms | A18 conservé | A19 neuf |
|---|---:|---:|
| IE totale radôme (J) | -42148524 | 328236.096 |
| Facette la plus négative à la fin (J) | -41656353 | -34174.477 |
| Résidu global final (J) | -1568571.248 | -415788.352 |
| Erreur maximale d'offset(mm) | 0.001194894 | 0.000378371 |
| Groupes radôme détachés |168|168|

La somme native des énergies de216facettes vaut328236,100009J; la part vaut328236,096J, écart0,004009J. **Une somme positive ne masque pas les16facettes encore négatives**: minimum sur tout le parcours-49669.425J. L'étirement maximal atteint10,305fois la longueur initiale. La facette162 la plus négative en fin de calcul a encore ses deux peaux rompues et son cœur intact. Les624liaisons ne sont pas toutes rompues:620supprimées,168groupes détachés. Tous les éléments porteurs de masse restent présents.

Les témoins de cœur reproduisent le cisaillement élastique attendu(1,38375J à0,015rad), mais **les deux seuils finis lus correctement par Starter ne déclenchent aucune dégradation ni suppression**:

| Témoin |IE finale(J)|Coque encore présente|Contrôle complet|
|---|---:|---|---|
| UNBOUNDED | 22.140000 | True | réussi |
| FINITE_R20 | 22.140000 | True | **échoué** |
| FINITE_R02 | 22.140000 | True | **échoué** |

Le code public épinglé contient un appel de délaminage hérité conditionné par igmat0, cohérent avec cette absence d'effet dans la branche à plies distinctes: [mulawc.F90](https://github.com/OpenCourant/OpenCourant/blob/0168ab344bd743051e996d90c7c8d80728bb04a8/engine/source/materials/mat_share/mulawc.F90). **L'équivalence du code avec le binaire local n'est pas établie**, et aucun logiciel n'a été modifié. Le comportement observé du binaire fait foi pour ces témoins.

| Contrôle impact A19 | Résultat |
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
| offset_rotation_distance_tolerance | réussi |
| zero_warning_gate | **échoué** |
| cohesive_part_history_present | réussi |
| zero_initial_cohesive_IE | réussi |
| cohesive_IE_nonnegative | réussi |
| cohesive_expected_four_channels | réussi |
| no_generated_energy_before_external_contact | réussi |

Le contrôle séparé de non-négativité des facettes échoue aussi. Le résidu local maximal normalisé vaut0.702883; le seuil et la tolérance de précision sont hérités et restent inchangés. Aucune correction par une RKE inventée, changement de masse ou sélection d'une ressemblance historique.

Le MP4 et le GIF montrent21poses natives à échelle1, sans extrapolation, interpolateur de trajectoire ni physique Blender. **0.020000217s physiques** sont ralenties en6.3s de lecture. Les images portent la durée, le défaut énergétique et la qualification exploratoire. Contrôles d'encodage, décodage première/milieu/dernière et inspection visuelle enregistrés; lecture GUI non certifiée.

## 6. Contradictions et informations manquantes

Le changement de triangle contribue nettement au défaut mais ne démontre pas sa cause unique. Le cœur substitut non fissuré autorise encore des distorsions hors domaine, et la commande de rupture essayée n'agit pas dans cette configuration. La couverture legacy layer2 s'est révélée ambiguë; les sorties nouvelles utilisent explicitement ply42. La non-négativité par facette, le bilan local, le domaine métal/poutres et la référence de résistance des peaux restent échoués. Les anciens critères échoués A18, y compris la couverture annoncée de9canaux, sont intacts; A19 déclare correctement les4canaux natifs disponibles.

La prochaine étape doit représenter le cœur en3D avec un comportement compatible vérifié, traiter son couplage aux peaux et conserver les budgets de masse et d'énergie. Les données de rupture et de compression après le pic restent manquantes et devront apparaître comme plages déclarées, jamais comme paramètres ajustés au dommage connu. [LAW28](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm) constitue une piste à vérifier, sans intégration déjà qualifiée.

AIRCRAFT-A20 : objectif vidéo3D10 secondes physiques actif/incomplet. A19 a localisé99,75% de l'IE négative A18 dans12 facettes, vérifié les vrais champs ply42 (le legacy layer2 nul ne représente pas le cœur), effectué4 contrôles de triangle réussis et un nouveau départ intact20ms Ish3n31. IE totale radôme devenue positive328236J mais16 facettes négatives à la fin, minimum transitoire-49669J; local_energy échoué et domaines métal/façade dépassés. La rupture de cisaillement LAW25 gamma_ini/gamma_max lue par Starter ne s'active pas dans les2 témoins TYPE51: conserver ces échecs, ne pas l'intégrer comme correction. Lire source_inspection.json: appel m25delam limité àigmat0 dans le code public épinglé; équivalence avec le binaire non prouvée. Prochaine modification : traiter explicitement le cœur en3D (LAW28 ou loi compatible vérifiée) et le couplage aux peaux, avec cisaillement/crushing fini, pas seulement changer Ish3n. Fiche HRH10 p4 fournitrho48,E33=138,G31=41,G23=24MPa,tau31=1.21,tau23=.69MPa,compression nue2.07MPa, essais12.7mm; épaisseur8mm et branches postpic/G sont hypothèses, pas valeurs mesurées AA11. Déclarer les plages avant calcul, garder masse/CG/inertie/énergie et fragments/contact contrôlés; aucun retrait de cœur ou RKE inventé. Une modification mécanique exige un nouveau départ intact. Ne prolonger les20ms invalides vers100ms sans correction des déficits matériels/énergétiques. Ensuite100ms,1s,10s avec gravité/intérieur réellement modélisé, checkpoints, cadence de sorties réduite, coût annoncé et pas de mass scaling. Réutiliser les sorties et les contrôles A19 sans les relancer. Publication A12+A13 intacte; A14 àA19 en attente.
