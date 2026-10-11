# AIRCRAFT-A39 — Windows indisponible ; énergie Linux relue, défaut de déplacement isolé

Deux préparations Windows fraîches passent sans erreur ni avertissement. Leurs moteurs s’arrêtent avant le premier pas avec MUMPSrequired, malgré PCG sélectionné : aucune comparaison de dynamique Windows–Linux obtenue. La relecture séparée de douze échantillons du calcul Linux strict A38 apporte le résultat utile : KE globale du fichier TH, KE nodale, momentum et bilan énergétique complet concordent. Le journal−75% ne représente pas la KE enregistrée. Le déplacement garde environ0,000293mm de décalage, et le calcul partiel ne termine pas. La prochaine action cible le raffinement des premiers pas et leur croissance adaptative, sans patch de physique ni ajustement à un résultat historique.

## 1. Faits directement observés ou transcrits

Deux cas PCG Windows utilisent le même cube physique A37/A38, sans charge ou contact : tolérances10⁻⁶ jusqu’à0,1ms, puis10⁻¹¹ jusqu’à0,004ms. Les préparateurs terminent sans avertissement ni erreur. Les deux moteurs lisent le mode implicite, écrivent seulement l’animationt0 puis s’arrêtent avec code2, MUMPSrequired et ERROR TERMINATION. Temps moteur d’environ0,2s chacun. Cette limitation était déjà relevée dans la proposition de compilation A33 sur d’autres sondes implicites ; elle est confirmée ici sur le témoin libre. Aucun succès de dynamique ni cause unique du défaut Linux n’en est déduit.

Les journaux Windows affichent2processus HMPP alors que la configuration déclare1. Cet écart d’exécution est conservé comme critère échoué. Les deux cas ne progressent pas physiquement ; tout futur calcul Windows devra imposer et vérifier explicitement le nombre de threads avant utilisation.

Le fichier d’historique partiel A38 est copié bit pour bit dans un nouveau dossier A39, puis décodé par l’outil natif conservé. L’empreinte du fichier original reste identique. Aucun solveur ancien relancé, aucune modification des sorties A38. Les douze temps enregistrés vont de0 à0,011ms ; la source reste un calcul arrêté, prévu jusqu’à0,1ms, et n’est pas créditée à l’impact entier.

## 2. Résultats d’un modèle officiel

La source OpenRadioss figée bad6688602d770e019b75773d2d5a48b4f9bd918 encadre l’appel implicite IMP_SOLV par la condition de compilation MUMPS5 ; sinon RESOL termine avec MUMPSrequired. Ce garde-fou est distinct du choix PCG/MUMPS dans les cartes d’entrée. Les liens et empreintes RESOL/prec_solv sont enregistrés. L’identité exacte de cette source avec le binaire Windows conservé n’est pas démontrée : le journal natif Windows fournit directement la limitation observée.

La documentation prévoit un pas initial et l’augmentation du pas après convergence en un nombre choisi d’itérations. Cette possibilité sera testée séparément ; elle ne qualifie pas déjà la dynamique ni une accélération entière.

- [Pas initial /IMPL/DTINI](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dtini_engine_r.htm)
- [Croissance adaptative /IMPL/DT/1](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_1_engine_r.htm)

## 3. Affirmations provenant des archives locales

Aucune nouvelle consultation d’archive, photographie, vidéo ou PDF historique. Aucun nouveau fait AA11 transcrit. Les cubes numériques ne constituent pas une observation historique.

## 4. Hypothèses propres au modèle

Graine1102064, zéro tirage. Cube1mm N2,27nœuds,8HA8 ; masse0,00278g ; LAW2 E73100MPa,ν0,33,densité0,00278g/mm³,yield324MPa ; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Vitesse initiale[-200,5,2]mm/ms, KE0,05564031J. Newmarkγ0,5/β0,25, PCG avec Jacobi et tolérance linéaire10⁻⁸. Pas initial0,001ms, mêmes données physiques et mêmes critères de conservation que le Linux PCG A38 mis en cache. Le cas strict court change aussi la durée et le solveur linéaire par rapport au Linux MUMPS strict : aucune comparaison à facteur unique revendiquée pour cette paire.

Critères physiques inchangés : KE/bilan2%+10⁻⁷J ; vitesse2×10⁻⁴mm/ms ; déplacement2×10⁻⁵mm ; momentum2%+10⁻⁹Ns ; vérification de masse, absence d’ADMAS et travail externe nul. Aucune correction empirique du temps, de la position, de KE ou de RKE, aucune modification de densité, de matériau ou de fichier de reprise. Les échantillons partiels sont testés, sans prétendre couvrir chaque incrément intermédiaire ou la durée complète.

## 5. Résultats dérivés

| Contrôle | Résultat |
|---|---|
| Windows libre PCG10⁻⁶ | préparateur réussi, moteur indisponible àt0 |
| Windows libre PCG10⁻¹¹ | préparateur réussi, moteur indisponible àt0 |
| Douze vitesses Linux strictes | conformes à[-200,5,2]mm/ms |
| KE nodale et globale enregistrées | conformes à0,05564031J |
| Bilan énergétique complet enregistré | résidu0J à la précision publiée |
| Momentum physique et global enregistré | conformes à la valeur initiale |
| Masse, ADMAS et travail externe | critères réussis aux échantillons |
| Déplacement exact | échoué, décalage maximal0,000293mm |
| Terme complet0,1ms | absent, calcul arrêté |

Le bilan utilise toutes les composantes natives déjà déclarées : KE, rotation, énergie interne, hourglass, ressorts, contact élastique, friction et dissipation, moins travail externe et énergie initiale. Aucun terme nouveau ou facteur ajusté ne referme le budget. Énergie interne maximale environ4,878×10⁻²⁶J, autres composantes non cinétiques nulles à la précision des sorties.

Les affichages A38−75% contredisent donc les valeurs globales d’historique et les champs échantillonnés. A38 est conservée intégralement ; cette nouvelle lecture précise l’interprétation, sans transformer son calcul interrompu en réussite. La prochaine piste est le décalage initial, avec raffinement temporel puis croissance contrôlée. Il faut une nouvelle configuration avant toute exécution.

## 6. Contradictions et informations manquantes

L’origine exacte du−75% imprimé reste inconnue ; ni une perte physique réelle ni un facteur correctif sur la KE enregistrée n’est démontré. Le mécanisme du décalage initial et sa dépendance au premier pas restent à tester. La compatibilité complète Windows–Linux n’est pas prouvée, mais les champs et budgets partiels conservés contraignent les hypothèses. Le moteur Windows sans MUMPS ne permet pas la comparaison cohérente visée ; le préparateur Linux A35 reste incomplet.

Aucun nouveau calcul entier. Les peaux A34, raffinement A36, transition/contact implicites A37 et défauts de démarrage A38 restent distincts et non qualifiés. Le meilleur impact entier reste A20≈20ms. Ni ce cube ni une vidéo ralentie ne fournit dix secondes physiques. Installation et compilation A35 restent terminées en39,29min ; aucun prolongement de compilation ni modification de logiciel.

AIRCRAFT-A40 : reprendre les douze historiques partiels Linux stricts A38 relus en A39 sans répétition. Vitesse, KE nodale et globale, bilan énergétique complet, momentum physique/global, masse et travail passent aux instants enregistrés; seul le déplacement garde environ0,000293mm de décalage et la terminaison complète manque. Le -75% est une ligne de journal, pas la KE globale du fichier TH; sa cause d’affichage reste inconnue. Déclarer un raffinement du tout premier pas, avec tolérances1e-11 et croissance adaptative vers le pas maximal initial, selon /IMPL/DTINI et /IMPL/DT/1. Garder les seuils physiques, masses, matériaux, vitesses et état initial; ne pas appliquer un décalage artificiel de temps/position ou facteur de KE. Tester le mouvement libre exact jusqu’au terme puis au demi-pas; seulement après succès, déclarer transition complète et contact actif. Aucun calcul entier ni coût10s extrapolé depuis ce cube. Le contrôle Windows PCG est indisponible : MUMPS requis avant avance, limitation connue A33 confirmée en A39. Ses départs affichent2HMPP malgré1déclaré; vérifier explicitement -nt1 avant tout nouveau calcul Windows. Compilation A35 terminée39,29min, aucune nouvelle compilation ou installation. Peaux A34, raffinement A36 et compatibilité implicite entière restent échoués/incomplets. Meilleur impact entier A20=20ms, objectif10s physiques 3D puis vidéo/GIF incomplet. Publier A38+A39 maintenant après vérification, selon autorisation et cadence.
