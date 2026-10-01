# IMPACT-I02-GEOM - modèle 3D d'avion acquis et intégré

10 septembre 2026. Demande de Jeremy : chercher et utiliser un modèle 3D d'avion disponible sur Internet, GitHub notamment. Cette étape complète l'acquisition géométrique ; elle ne prétend pas achever les contrôles de contact et la section d'aile mécanique prévus pour IMPACT-I02. I01 reste inchangée, V11F et V11R préservées, V11S thermique toujours différée.

## 1. Faits directement vérifiés

Un modèle désigné **Boeing 767-200** est publié dans [Flightradar24/fr24-3d-models](https://github.com/Flightradar24/fr24-3d-models), dossier source/b762 et modèle models/b762.glb. Le README crédite FlightGear/FGMEMBERS et déclare GPLv2 pour ces modèles d'avion. Cinq fichiers ont été récupérés à la révision figée `dd53267690c6a4ecbb290a3acf0284333a5d68a9` : README, LICENSE, GLB, source Blender et ZIP source. Taille et empreinte Git SHA1 vérifiées contre l'arbre GitHub ; SHA256 locales sauvegardées. Aucun logiciel téléchargé exécuté, aucun script embarqué activé, aucun changement d'installation.

Le modèle GLB source est en glTF binaire **1.0**, avec sept nœuds, 156 primitives graphiques, 9719 sommets référencés et 12647 triangles. Il ne contient pas d'animation ni de skinning graphique : cette dernière observation concerne l'animation des maillages, pas les peaux structurelles de l'avion. Le fichier Blender original contient aussi des objets supplémentaires non assemblés dont les coordonnées brutes ne décrivent pas un avion complet ; ils ne sont pas amalgamés au modèle livré. C'est la scène GLB publiée, avec ses transformations hiérarchiques, qui définit la copie dérivée.

L'enveloppe visuelle comporte fuselage, ailes, empennages, moteurs et surfaces mobiles. Elle ne fournit pas de cartes de matériau mécanique, d'épaisseurs de tôles résistantes, de lois de jonctions ou de rupture utilisables ici. Ses primitives ne sont pas identifiées comme des poutres ou des nervures de structure.

## 2. Données constructeur et résultats officiels

La référence dimensionnelle est **Boeing D6-58328 Rev K, décembre 2024, §2.2.1, page imprimée 2-8 / page PDF 28**, modèles 767-200 et -200ER. [Document constructeur](https://www.boeing.com/content/dam/boeing/v2/airports/acaps/767_REV_K.pdf). La page entière a été rendue avec Poppler puis lue visuellement : les cotes du dessin ne figurent pas dans la couche texte, qui contient seulement le titre et les mentions de page.

| Dimension | Cote Boeing d'origine | Conversion exacte pieds/pouces | Valeur métrique imprimée | Étendue GLB mesurée | Écart à la cote métrique imprimée |
|---|---|---:|---:|---:|---:|
| Longueur hors tout | 159 ft 2 in | 48,514 m | 48,51 m | 50,36791 m | +3,830 % |
| Envergure | 156 ft 1 in | 47,5742 m | 47,57 m | 46,30930 m | -2,650 % |

Conversions : 1 ft = 0,3048 m ; 1 in = 0,0254 m. Ce sont des dimensions générales d'aménagement aéroportuaire, pas des plans de fabrication ni un modèle d'impact. Aucune résistance mécanique n'est tirée de ce document et aucun résultat de modèle NIST n'est utilisé pour ajuster la forme importée. Les écarts géométriques ci-dessus sont conservés ; ni mise à l'échelle anisotrope ni calibration par l'image de l'impact.

## 3. Affirmations des archives locales

Aucune nouvelle source d'archive ou vidéo consultée. Aucune affirmation de projection holographique ou de comportement réel des ailes n'est utilisée comme entrée ou comme conclusion. Le fait qu'une enveloppe graphique reste entière ne teste pas une rupture physique.

## 4. Hypothèses et transformations propres à cette intégration

Les mètres définis par glTF sont conservés. Transformation des axes : (x, y, z) glTF vers (z, x, y) d'analyse, soit une permutation cyclique sans changement d'échelle. Convention d'analyse : x vers l'arrière de l'avion, y transversal, z vertical. Matériaux remplacés par un affichage gris neutre sans identification d'alliage. Les textures et shaders de l'original ne sont pas exécutés ni utilisés comme données de résistance.

**Crédit mécanique nul** : masse, rigidité, résistance, connexions et rupture ne sont pas ajoutées au solveur par ce modèle. Cela ne signifie pas qu'un avion réel a une masse nulle ; cela signifie qu'aucune propriété mécanique n'est justifiée par cet actif graphique. Aucune collision, température ou physique Blender activée. Les dimensions doivent être corrigées à partir de références traçables avant d'employer la forme pour une mesure précise de contact.

## 5. Résultats dérivés et vérifications

Le lecteur restreint GLB1 contrôle les bornes des buffers, les indices de triangles, les matrices et la scène active. Il a détecté **138 bornes max d'indices incohérentes dans les métadonnées du fichier source**, toutes de type SCALAR : les indices réels sont valides pour leurs sommets, mais certains maxima déclarés ne correspondent pas aux données. Exemple accessor_21 : maximum déclaré 233, maximum réel 91. Le fichier source reste inchangé, et la conversion utilise les buffers vérifiés. Les bornes de positions ne présentent pas ces incohérences.

**126 triangles de surface inférieure à 1e-12 m²** ont été retirés de la copie dérivée, avec liste de leurs indices conservée. Une primitive devient vide ; restent **155 ensembles et 12521 triangles**. Ce nettoyage n'invente ni matière ni résistance. Le brouillon initial, qui provoquait une omission automatique par l'exporteur, est conservé hors du sous-dossier final ; utiliser uniquement les fichiers final/B762_GEOMETRY_ONLY.blend et final/B762_GEOMETRY_ONLY.glb.

Les deux formats finaux ont été rouverts indépendamment. Chaque triangle conservé est comparé à la géométrie source transformée, sans dépendre de l'ordre des indices. Écart maximal des coordonnées **2,277e-7 m**, sous 1e-5 m ; nombre de triangles et ensembles identiques. Aucun corps rigide, modificateur ou contrainte dans les objets livrés. Les trois vues (perspective, dessus, face) et la planche annotée ont été inspectées. Le message de miniature de cache Blender non écrite n'affecte pas les fichiers sauvegardés et rouverts ; aucune modification de cache système n'a été tentée.

## 6. Informations manquantes et portée

Le modèle est accepté comme **référence visuelle**, pas comme géométrie exacte ni maillage de calcul de l'appareil historique. La topologie de surface, même transférée correctement, n'est pas une topologie structurelle. Manquent notamment : peaux résistantes variables, longerons, nervures, raidisseurs, attaches, propriétés et endommagement, masse et carburant distribués. Les moteurs sont ici des enveloppes graphiques, pas des moteurs mécaniques.

Concernant les ailes : I01 désactive leur rupture par construction, et ce nouveau modèle graphique ne la calcule pas non plus. Ni intégrité ni rupture d'une aile réelle ne peuvent donc être inférées de ces deux livrables. La suite doit définir des prédictions mécaniques testables, sans supposer les ailes intactes ou nécessairement détachées avant toute pénétration.

## Livraison et prochaine étape

Dans `wtc1_3d_v4/output/impact_i02_geom/final/` : scène Blender, GLB2 portable, audits d'intégration et de réimportation, notice de modifications, licence et paquet ZIP avec sources. Dans `wtc1_3d_v4/renders/impact_i02_geom/final/` : trois vues et B762_apercu_annote.png. Les données originales sont conservées sous `wtc1_simulation_v8/input/impact_i02_geom/` ; ne plus les modifier.

La procédure de reprise du harnais a conduit à isoler cet apport graphique et à préserver I01/V11F/V11R par empreintes, sans crédit mécanique indu. La procédure PDF a conduit à lire les cotes directement sur la page rendue plutôt qu'à inventer une extraction textuelle. La validation de livraison porte sur provenance, conversion et traçabilité ; les critères physiques I01 restés en échec ne changent pas de statut.

Prochaine étape toujours **IMPACT-I02 mécanique** : section d'aile avec peaux/longerons/nervures, données primaires et plages explicites, corrections de précision des decks et des avertissements de contact, réactions enregistrées, puis contrôle de rupture et d'énergie. Employer ce modèle pour l'enveloppe et le contexte visuel après traitement de ses écarts, pas comme substitution à ces données. Ne relancer ni I01 ni les anciennes campagnes pour retrouver leurs résultats.
