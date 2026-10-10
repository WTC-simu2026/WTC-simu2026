# AIRCRAFT-A17 — séparation énergétique native et premier export vidéo 3D

**L'export MP4 et GIF fonctionne. Il présente les états A16 sur 10 ms physiques, ralentis sur 6,3 s de lecture. L'objectif utilisateur de 10 secondes physiques reste actif et incomplet.** A17 prépare le prolongement : quatre témoins natifs de liaison cohésive passent le bilan, l'énergie par surface, la recharge au même maximum, le demi-pas et le changement d'aire. Aucun ancien impact relancé.

## 1. Faits directement observés ou transcrits

Pré-déclaration immutable, graine 1102042, zéro tirage. Quatre Starter sans erreur ni avertissement ; quatre Engines natifs normaux. Histoire binaire/CSV intégrale contrôlée sur 10000 lignes par cas, tous les canaux. Les messages natifs déclarent la rupture des quatre points d'intégration et la suppression de l'élément de connexion. Statut final d'érosion égal à zéro, lu via le convertisseur natif.

Le film présente 21 états géométriques A16 enregistrés, deux caméras, 42 rendus natifs Blender. Les coordonnées exportées en mètres ont un écart absolu maximal de 1.90734863e-06 m à la précision flottante du rendu. Déplacements ×1, aucune interpolation de déformation et aucun solveur Blender. Les couleurs du nez proviennent des indices de dommage A16 ; elles ne créent ni trou ni fragment. La façade est représentée par ses arêtes rendues de 8 mm d'épaisseur visuelle ; cette épaisseur ne modifie pas le calcul.

MP4 H.264 2560×720, 30 images/s, 189 images, 6,3 s de lecture ; GIF 1280×360, 21 images de 300 ms. Décodeur vidéo et métadonnées contrôlés. Images décodées initiale, médiane et finale inspectées : légendes lisibles, temps simulé présent, deux vues. Lecture interactive GUI non certifiée. L'état final est 0.010000175476 s physique. Il ne représente pas les 10 premières secondes demandées.

## 2. Résultats d'un modèle officiel et sources primaires

Le solveur est OpenRadioss v20260728-win64 conservé. Aucun résultat NIST de dégâts n'est une cible. La façade nominale A16 garde sa dépendance d'entrée NIST signalée ; ce film ne constitue pas une reconstruction officielle.

La [loi LAW117](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm) est une relation cohésive à deux modes utilisant rigidité d'interface, traction maximale et énergie surfacique. Elle permet de relier ouverture et réduction des efforts. Elle emploie des briques [TYPE43](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm), dont la hauteur peut être nulle et dont la stabilité dépend des masses nodales. Ces sources décrivent une implémentation ; elles n'identifient pas les propriétés du radôme Boeing.

## 3. Affirmations des archives locales

Aucune nouvelle vidéo/photographie d'archive ni nouveau PDF source analysé. Archive et sources officielles en lecture seule. **10242 fichiers antérieurs, 44.920 Go**, recontrôlés entièrement par SHA-256 sans différence. Les états, rapports, limites et critères échoués A06–A16 restent intacts. Le contrat analytique A07 est réutilisé ; ORTHENERG rejetée ne reçoit aucune nouvelle qualification.

Les premiers rendus et l'encodage ont réussi à créer leurs sorties, puis leur wrapper de journalisation a échoué : il exigeait un exécutable situé sous le workspace, contrairement à Blender/FFmpeg installés. Journaux et ancien encodeur conservés. Le helper A17 accepte maintenant ces chemins ; les rendus/MP4 existants sont vérifiés sans écrasement ni relance inutile. Les codes natifs et durées exactes de ces deux premières commandes n'ont pas été journalisés ; cette lacune reste explicite. Durée interne de rendu enregistrée : 40.873 s. L'avertissement d'écriture d'une miniature Blender hors workspace n'a pas empêché les PNG et le fichier blend sous A17. Aucun logiciel installé/modifié et aucune publication externe nouvelle.

## 4. Hypothèses propres au modèle et protocole

Référence cohésive numérique issue du contrat A07 : EN=22000/5=4400 N/mm³, ET=4000/5=800 N/mm³ ; pic normal 450 MPa, pic tangent 100 MPa ; GI=GII=50 N/mm=50 kJ/m². **G et le pic de cisaillement ne sont pas mesurés pour le radôme réel.** Le pic normal reprend une résistance uniaxiale d'un tissu de référence, pas une résistance d'adhésif identifiée. La longueur 5 mm choisie sert seulement à la rigidité du témoin, indépendamment de son aire. Aucun paramètre adapté à la perforation ou aux dégâts observés.

Un élément cohésif carré de côté 10 ou 20 mm, huit nœuds distincts, hauteur initiale nulle. Ismstr=1, aire initiale, Imass=1, Idel=4, Irupt=1. Densité surfacique numérique 1e−20 g/mm² ; masses instrumentales de 1 g par nœud, aucune masse ajoutée automatiquement. Face inférieure fixe ; face supérieure imposée en traction Z ou cisaillement X, autres directions bloquées. Ces masses et déplacements appartiennent au contrôle de la loi et ne deviennent pas des paramètres de l'avion.

Trajet d'ouverture : 0→(δdébut+δfin)/2→0→même pic→1,1δfin aux temps 0/0,25/0,5/0,75/1 ms ; interpolation cubique lisse sur chaque branche. δdébut=T/K, δfin=2G/T. Déformation irréversible fondée sur l'ouverture maximale ; contrainte résistante (1−D)Kδ. Énergie stockée ψ=½(1−D)Kδ² ; dissipation référencée comme travail de l'enveloppe jusqu'au maximum moins ψ à ce maximum. Comparaison séparée avec IE native. PW n'est pas ajouté à IE. Réactions lues comme impulsions : travail Σv·ΔR ; leur dérivée sur les appuis donne l'effort, sans inertie d'appui mobile.

Critères avant calcul : bilan/référence IE ≤1% du travail cible +0,001 J ; travail surfacique/G ≤2% ; recharge au même pic ≤0,5% ; effort/référence ≤2% du pic ; position ≤0,0001 mm ; demi-pas et normalisation d'aire ≤0,5%. Pas maximum 25 ns, cas demi-pas 12,5 ns ; TH 0,1 µs ; images 5 µs. Deux threads CPU, plafond 180 s par Engine. Il n'y a pas de nouveau calcul de l'avion entier dans A17.

## 5. Résultats dérivés

| Cas | Travail final / aire N/mm | Écart IE à même pic (fraction) | Max résidu J | Max écart effort / pic | Critères échoués |
|---|---:|---:|---:|---:|---|
| NORMAL_L10 | 50.000000 | 4.99999999e-08 | 1.42182e-06 | 0.055123% | aucun |
| NORMAL_L10_HALF | 50.000000 | 0 | 1.360363e-06 | 0.050803% | aucun |
| NORMAL_L20 | 50.000000 | 5e-07 | 1.06499e-05 | 0.119811% | aucun |
| SHEAR_L10 | 50.000000 | 5.00000001e-08 | 1.33e-06 | 0.047200% | aucun |

Le travail final par aire vaut 50 N/mm dans les quatre cas. Écart final demi-pas et normalisation d'aire : 0 et 0. Les éléments de connexion se séparent réellement dans ces témoins, avec énergie de rupture incluse dans le bilan ; pas de perte inventée ni de RKE reconstruit. Cette réussite contrôle une interface uniforme et une implémentation, **pas la convergence spatiale de l'avion ou la ténacité réelle de son radôme**. Mode mixte, compression et effets de rotation encore ouverts.

Le MP4 et le GIF sont des aperçus des sorties A16 mises en cache. Sélection du premier cas déclaré R20, sans classement selon une ressemblance historique. Les 21 poses tiennent chacune neuf images à 30 Hz ; ralentissement de lecture seul. Le fichier blend contient ces poses natives à interpolation constante, ouvert sur la pose finale. Les couleurs finales y sont sauvegardées ; pour les actualiser avec le temps, réutiliser le script de rendu, car elles ne sont pas un nouveau champ mécanique Blender.

Coût mesuré du solveur A16 : 509.197 et 493.404 s pour 10 ms. Projection linéaire jusqu'à 10 s : **5.802 jours sur deux threads**, avant nouvelles interactions et modifications du modèle. Ce n'est pas une ETA fiable. Réduire la fréquence des sorties peut réduire stockage/I/O ; cela ne justifie pas d'augmenter le pas ou la masse pour masquer un défaut mécanique.

## 6. Contradictions, données manquantes et suite

Le premier export fonctionne ; l'objectif de 10 secondes physiques n'est pas réalisé. L'horizon couplé reste A16≈0,01 s. La nouvelle liaison n'est pas encore intégrée au radôme, aux métaux ou à la façade. Sa géométrie de séparation, ses propriétés réelles, le mode mixte, la compression, les rotations, l'autocontact des fragments et l'effet sur les masses/assemblages restent à contrôler. Le cœur, l'intérieur de la tour, les planchers/noyau, la gravité, le carburant et les conditions historiques ne sont pas ajoutés par une animation.

Les limites A16 et ses critères matériels ne sont pas transformés en réussite. Une reprise native intacte avec topologie déclarée est nécessaire ; aucune transformation arbitraire du dernier état en fragments. La suite vise un impact couplé de 20 ms, continuable puis prolongé selon le domaine atteint, avec temps/coût/conditions toujours explicites.

AIRCRAFT-A18 : objectif utilisateur prioritaire = vidéo 3D des10 premières secondes physiques. L'export MP4/GIF A17 existe mais couvre seulement10ms issus d'A16. Passer maintenant de la liaison cohésive native contrôlée à une séparation dans le contact couplé avion/façade ; aucun ancien Engine relancé. Déclarer avant calcul une topologie adaptée et vérifier masses/CG/inertie, interface/rotations/contacts et travail des connexions ; la LAW117 est vérifiée en traction/cisaillement uniformes, pas en mode mixte, compression ou dans le radôme réel. Les50N/mm sont un essai numérique non mesuré. Ne pas ajouter un G pour compenser le maillage, ni reprendre ORTHENERG rejetée. Partir intact, conserver toutes limites A16, viser un premier20ms borné et continuable, puis100ms/1s/10s suivant le domaine atteint. Étendre la structure intérieure et la gravité avant de présenter les secondes suivantes comme des conditions réalistes. Sauvegarder les checkpoints et réduire la cadence de sorties sans changer les équations pour permettre les calculs longs. Coût observé10ms≈8,3min/2threads, projection linéaire10s≈5,8jours, pas une ETA fiable. Rendu Blender de données natives à échelle1, aucun mouvement extrapolé ni cinématique choisie pour une perforation. Histoire énergétique globale/locale, masse, quantité de mouvement et fragments doivent être auditables. L'objectif10s reste actif et incomplet. Publication A14+A15 toujours due, A16+A17 également en attente ; intégrité de publication distincte de qualification physique.
