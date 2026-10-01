# WTC 1 — V10Z : première animation pilotée par V10Y

Statut : **visualisation exploratoire opérationnelle**, contrôlée contre le calcul réduit. Le résultat ne constitue pas une validation historique.

Le fichier Blender contient une scène animée de 110 niveaux schématiques et conserve séparément la scène de référence V4.2. La vidéo dure 18.33 s (220 images à 12 images/s) : les quatre premières secondes accélèrent l'évolution thermique, puis le mouvement suit le temps de propagation du modèle. Les cinq vues de contrôle et la planche permettent une lecture rapide.

## Résultat du scénario

GRID-0119 initie au niveau 96 après 5810 s, soit 96 min 50 s après l'impact. Il est 304 s en avance sur les 6114 s de la chronologie de comparaison. Il appartient à un groupe de 18 cas progressants ayant cet écart minimal : ce choix a été effectué après observation de la grille, et n'est ni unique, ni une validation indépendante.

La progression atteint le dernier niveau du modèle après 14.126339 s. La vitesse atteint 43.544 m/s et la masse mobile finale vaut 350.4 millions de kg. Cette progression utilise l'énergie gravitationnelle après initiation et les résistances V10Y déclarées. Les autres résultats de la grille restent présents : 288 progressions, 144 arrêts après initiation et 297 cas sans initiation. Ces nombres ne sont pas des probabilités de l'événement réel.

## Ce que représente l'image

La maquette reprend les niveaux uniformes de 3,6576 m de V10Y, soit 402,336 m, tandis que le master V4.2 conserve sa hauteur de référence de 416,9664 m. Le bloc supérieur suit la translation calculée. Les niveaux inférieurs sont masqués au passage des événements de rupture ; leur masse reste dans le bilan d'accrétion du calcul. Leur disparition n'est donc pas une prévision de poussière ou de volume de débris. La couleur de la zone 93–99 code une température d'enveloppe par niveau : la répartition locale des flammes n'est pas calculée.

Les positions entre deux événements sont reconstruites avec l'accélération constante de l'intervalle V10Y. Les pertes de vitesse aux événements suivent l'accrétion inélastique du même calcul. Les positions ont été enregistrées à chacune des 220 images ; l'interpolation à des instants intermédiaires dans Blender sert uniquement à l'affichage. Le fichier fonctionne sans script automatique à son ouverture.

## Limites mises en évidence pendant le transfert

- La première ligne V10Y contient déjà une chute de 1,8288 m et une vitesse non nulle à son temps relatif zéro. Les 14,1263 s excluent donc la durée de cette chute supposée. Son équivalent en chute libre serait 0.6107 s ; ce diagnostic ne la rend pas mécaniquement justifiée.
- La masse initiale plus les étages accré­tés totalise 109.5 étages équivalents. Un demi-étage du niveau d'initiation n'est pas compté dans V10Y. L'animation conserve cette limite et ne corrige pas silencieusement le calcul.
- L'état final conserve une énergie cinétique élevée (326.16 GJ). Il marque l'arrivée au dernier événement, pas la stabilisation des débris au sol. L'arrêt de la vidéo n'est pas un arrêt mécanique.
- L'impact est représenté par des dommages d'entrée, l'échauffement par des plages dépendantes des calculs officiels, et la propagation par un mécanisme vertical unique. La chaîne n'est pas encore une simulation 3D complète de l'avion, des incendies, des assemblages et de l'effondrement.

## Statut des informations

1. **Faits observés ou transcrits** : identités et empreintes des fichiers, dimensions des médias, chronologie et géométrie héritées des dossiers locaux vérifiés.
2. **Résultats de modèle officiel** : branches de dommages et plages de températures NIST reprises par V10Y.
3. **Affirmations des archives locales** : aucune nouvelle archive inspectée, aucune nouvelle affirmation ajoutée.
4. **Hypothèses propres** : réserve à froid 1,8, quantile thermique 0,55, masse 3,2 millions de kg par étage, résistance de référence 1,2 GJ, demi-hauteur de chute initiale ; autres hypothèses inchangées dans la configuration V10Y.
5. **Résultats dérivés** : rejeu exact de 35 champs, 96 événements, 220 poses, animation, vidéo et vues fixes.
6. **Contradictions et inconnues** : avance de 304 s, durée initiale omise, demi-étage manquant, bilan de débris et dynamique latérale non résolus.

## Vérification et reprise

Les contrôles de reproduction, de conservation des sources, des 220 poses, d'ouverture et de métadonnées vidéo et de revue visuelle des cinq vues passent. L'erreur maximale de position enregistrée est 1.46e-05 m. La maquette ne contient aucun objet de physique Blender. Le master conserve son SHA-256. Le rendu ne renvoie aucune donnée au calcul. Le rapport demande/capacité est arrondi à l'écran : l'affichage 1,0000 juste avant initiation ne remplace pas la valeur exacte du pilote.

Exécution conservée : Python 3.14.3, Blender 5.2.0 LTS, deux passages Blender acceptés, durée cumulée 66.2 s. Un aperçu au cadrage insuffisant et une tentative de réglage vidéo interrompue sont conservés dans les dossiers de travail. Deux interrogations locales de l'API ont servi à corriger le format vidéo, dont le changement de sélection est documenté dans les [notes officielles Blender](https://developer.blender.org/docs/release_notes/4.5/pipeline_assets_io/). Configuration, scripts, pilote, manifestes, revue et bilans sont conservés.

Prochaine priorité : corriger le raccord initiation–propagation, fermer l'inventaire de masse et traiter les forces résistantes dès le premier déplacement ; ensuite introduire les chemins d'efforts spatiaux noyau/façades/planchers. Ce transfert fournit un premier résultat visible et révèle les simplifications qui influencent le verdict.
