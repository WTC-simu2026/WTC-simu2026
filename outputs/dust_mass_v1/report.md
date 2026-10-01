# DUST-V1 - Audit de la masse et de la granulométrie des poussières du WTC

Date : 25 août 2026  
Statut : branche documentaire et calcul réduit ; aucune modification de V8W, de l'état du harnais ou des archives sources.

## Conclusion courte

L'affirmation « les deux tours ont été réduites pour moitié en poussière fine de 100 µm » n'est pas établie par les documents inspectés.

- Les trois échantillons Lioy mesurent **30 à 38 % de leur masse sous 75 µm**, et **42 à 49 % entre 75 et 300 µm**. Le seuil 100 µm n'a pas été mesuré.
- Une interpolation conditionnelle place la moyenne sous 100 µm vers **40,1 %** (uniforme en diamètre) ou **44,5 %** (uniforme en logarithme du diamètre). Ce ne sont pas des observations.
- Ces pourcentages décrivent trois dépôts de poussière protégés de la pluie, recueillis à l'est du WTC cinq à six jours après l'événement. Ils ne donnent pas la fraction de la masse initiale des tours devenue poussière.
- En terminologie des aérosols, 100 µm n'est pas de la « particule fine » au sens PM2,5. Dans les trois échantillons, la fraction <2,5 µm représente seulement **0,88 à 1,30 % de la masse** du tableau 1.

La piste poussière reste importante, mais la première question testable n'est pas encore « quel mécanisme ? ». C'est : **quelle masse totale a réellement été produite dans chaque classe granulométrique, avec quelles incertitudes de dépôt et de collecte ?**

## 1. Données directement documentées

### FAIT_ARCHIVE - distribution granulométrique de Lioy et al. (2002)

Trois dépôts protégés ont été recueillis les 16 et 17 septembre 2001 : un sur une corniche de Cortlandt Street, deux sur des automobiles à environ 0,7 km du site. Le tableau 1 donne :

| Échantillon | <2,5 µm | 2,5-10 µm | 10-53 µm | >53 µm | <75 µm | 75-300 µm | >300 µm |
|---|---:|---:|---:|---:|---:|---:|---:|
| Cortlandt | 1,12 % | 0,35 % | 37,03 % | 61,50 % | 38 % | 46 % | 16 % |
| Cherry | 0,88 % | 0,30 % | 46,61 % | 52,21 % | 30 % | 49 % | 23 % |
| Market | 1,30 % | 0,40 % | 34,69 % | 63,60 % | 37 % | 42 % | 21 % |

Contrôles internes à conserver :

- l'abstract annonce 0,88-1,98 % sous 2,5 µm, alors que le tableau 1 donne 0,88-1,30 % ;
- l'introduction imprime une masse de matériaux « >10 × 10^6 tons », manifestement incompatible avec les bilans de déblaiement officiels. Cette valeur ne doit pas être reprise comme masse des tours ;
- la somme des trois classes tamisées de Cherry vaut 102 %, probablement en raison des valeurs rapportées/arrondies. Les valeurs sont conservées telles que publiées.

### FAIT_OFFICIEL - USGS OFR 01-0429

L'USGS a collecté 33 échantillons de poussière, principalement les 17 et 18 septembre. L'étude de réflectance indique des grains allant de fragments centimétriques à des fibres submicroniques. Cela établit une forte hétérogénéité, mais pas une distribution massique représentative de l'ensemble du site. Les objectifs étaient surtout minéralogiques, chimiques et environnementaux.

### FAIT_ARCHIVE - McGee et al. (2003)

Le corpus Judy Wood contient une copie HTML de l'article sur la PM2,5. Les auteurs ont tamisé, aérosolisé puis séparé en taille la poussière retombée avant d'isoler PM2,5. Le résultat chimique de cette fraction ne mesure donc pas sa proportion massique naturelle dans la poussière initiale.

### AFFIRMATION_ARCHIVE - Judy Wood

Les pages `dirt4.html` et `dirt6.html` citent un ordre de grandeur de 1,176 million de tonnes de débris, parlent de poussière visuellement uniforme et reproduisent des cartes USGS. Elles ne fournissent ni prélèvement représentatif, ni intégration volume-épaisseur-densité, ni histogramme massique au seuil 100 µm, ni dosimétrie énergétique. Les photographies documentent un nuage et des dépôts ; elles ne mesurent pas la masse pulvérisée et n'identifient pas un mécanisme.

## 2. Ce que l'on peut et ne peut pas calculer à 100 µm

Le seuil 100 µm coupe la classe publiée 75-300 µm. Sans distribution interne à cette classe :

| Échantillon | borne stricte basse <100 µm | borne stricte haute <100 µm | interpolation linéaire | interpolation log-uniforme |
|---|---:|---:|---:|---:|
| Cortlandt | 38 % | 84 % | 43,11 % | 47,54 % |
| Cherry | 30 % | 79 % | 35,44 % | 40,17 % |
| Market | 37 % | 79 % | 41,67 % | 45,72 % |

### INFERENCE

« Environ la moitié de la poussière retombée sous 100 µm » est compatible avec certaines formes possibles de la distribution, mais la valeur n'a pas été mesurée.

### INCONNU

La masse totale de poussière retombée et aéroportée, séparée de la masse des gros débris restés au site ou transportés, n'est pas fournie par ces études. On ne peut donc pas transformer la fraction d'un échantillon de poussière en fraction de la masse des tours.

## 3. Pourquoi les tonnages de déblaiement ne ferment pas le bilan

Les chiffres officiels décrivent des périmètres opérationnels différents : environ 1,2 million de tonnes traitées à Fresh Kills, 1 642 116 tonnes de débris et acier enlevées selon un rapport au Congrès, et 1,8 million de tonnes « cleared » selon la rétrospective DDC. Ils incluent le complexe WTC, les bâtiments 3 à 7, leur démolition ultérieure et d'autres matériaux du site.

Multiplier 1,2 million de tonnes par les fractions granulométriques de trois dépôts revient à supposer simultanément que :

1. ce tonnage est la masse initiale des deux tours ;
2. toute cette masse est passée dans le nuage ;
3. les trois dépôts ont échantillonné ce nuage sans biais de taille ni de distance ;
4. le matériau transporté à Fresh Kills conserve la même distribution que la poussière déposée à l'est.

Ces quatre hypothèses sont fausses ou non démontrées. Le calcul populaire donnant environ 11 000 tonnes de PM2,5 provient vraisemblablement de `1,2 million × ~0,9 %`; c'est un exercice de mise à l'échelle, pas une pesée de PM2,5.

## 4. Test de cohérence de la piste thermitique

### FAIT_ARCHIVE

Harrit et al. rapportent :

- 1,74 mg de fragments rouges/gris extraits d'un échantillon de 1,6 g après retrait manuel de fragments de verre et de béton, soit environ 0,1 % de la poussière **séparée** ;
- des exothermes DSC estimés à 1,5, 3, 6 et 7,5 kJ/g de fragments ;
- l'aveu explicite que la masse totale du nuage de poussière est difficile à établir.

### INFERENCE CONDITIONNELLE

Si l'on applique littéralement 0,1 % à un kilogramme de poussière séparée, il y aurait 1 g de fragments, donc **1,5 à 7,5 kJ de chaleur par kilogramme de poussière**. Ce calcul ne prouve pas que cette fraction soit représentative, ne donne pas la masse initiale avant réaction et ne fournit aucun coefficient de conversion chaleur-fracturation.

### HYPOTHESE DE CALCUL - surface de fracture

Pour des sphères idéales, la surface par masse vaut `6/(rho d)`. Avec `rho = 1 800-2 400 kg/m3`, `d = 75-100 µm` et une énergie de fracture testée de `100-200 J/m2`, le proxy donne environ **2,5 à 8,9 kJ/kg** de matériau fragmenté. Ce n'est pas une loi validée de broyage : formes réelles, fines <75 µm, frottement, compactage, écrasement répété et rendement de couplage manquent.

Les deux plages se chevauchent uniquement sous des hypothèses idéalisées. Le résultat correct est donc :

- la publication thermitique ne constitue pas une explication quantitative de la poussière ;
- le simple bilan énergétique ne suffit pas non plus à exclure mathématiquement toute contribution chimique ;
- il faut un modèle distribué de masse, placement, chronologie, pression/couplage mécanique et résidus prédits.

## 5. Comparaison des mécanismes à tester

| Mécanisme | Ce qu'il peut expliquer en principe | Prédictions distinctives requises | État actuel |
|---|---|---|---|
| Chute gravitaire et impacts répétés | fragmentation du béton léger, plâtre, fibres et contenus ; éjection pneumatique | bilan énergie-masse, distribution par matériau et par taille, évolution temporelle | plausible mais non quantifié à l'échelle de la poussière |
| Explosifs distribués | fragmentation rapide et vitesses radiales | surpressions, signatures acoustiques, résidus, géométrie de charges, chronologie | hypothèse non confirmée par la granulométrie seule |
| Thermite/nanothermite | apport thermique local, coupe ou réaction énergique selon formulation | masse initiale, implantation, rendement pression-fracture, produits attendus et bilan de chaleur | publication des fragments insuffisante pour le bilan global |
| Énergie dirigée selon Judy Wood | disparition/fragmentation alléguée | source de puissance, champ et dose, loi de couplage, gradients matériels, témoins contrôlés | aucune quantification correspondante dans le dossier inspecté |

## 6. Prochaine étape recommandée : DUST-V2

Construire un bilan massique spatial avant toute attribution causale :

1. recenser les mesures d'épaisseur de dépôt avec date, lieu, protection contre pluie et méthode ;
2. numériser chaque distribution granulométrique par masse, sans fusionner nombre, volume et masse ;
3. séparer béton, gypse, laine minérale, cellulose, verre, acier et suies ;
4. modéliser la sélection aérodynamique avec distance et direction du vent ;
5. borner la masse totale par intégration surface × épaisseur × densité apparente, puis comparer aux flux de déblaiement ;
6. seulement ensuite, comparer énergie gravitaire, fracture, broyage industriel et contributions chimiques avec des rendements explicites.

## Fichiers reproductibles

- `inputs.json` : données publiées et plages de sensibilité ;
- `calculate.py` : calculs déterministes ;
- `results.json` et `particle_size_results.csv` : sorties ;
- `source_matrix.csv` : statut probatoire et limites de chaque source.

## Sources principales

- Lioy et al., 2002, DOI 10.1289/ehp.02110703.
- USGS Open-File Report 01-0429.
- McGee et al., 2003, Environmental Health Perspectives 111:972-980.
- Harrit et al., 2009, The Open Chemical Physics Journal 2:7-31.
- Lee et Lopez, 2014, test expérimental de l'énergie de fracture du béton ordinaire (valeurs moyennes 185-189 N/m), utilisé ici uniquement comme plage de sensibilité non-WTC.
