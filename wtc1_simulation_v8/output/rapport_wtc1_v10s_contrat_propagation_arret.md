# WTC 1 — V10S : contrat initiation → propagation/arrêt

Généré le 2026-09-04T07:57:44Z. Aucun solveur de propagation, GPU ou Blender n’est lancé.

## Résultat principal

La chaîne logicielle possède désormais un contrat explicite pour séparer l’initiation de la propagation ou de l’arrêt. Ce contrat ne simule pas l’effondrement : la piste dépendante du modèle officiel s’arrête avant propagation, et la piste physique conserve un résultat entièrement inconnu.

Le contrôle nul reproduit exactement les enregistrements V10O et termine par `CONTROL_NO_PROPAGATION`. Cette étiquette décrit uniquement un scénario logiciel sans masse, vitesse, énergie ni rupture ; elle n’est pas un résultat historique de non-effondrement.

## Deux lacunes de contrat détectées

La comparaison exacte des interfaces I07/I08 trouve 12/14 champs présents et deux écarts :

- `boundary_state` est exigé par le graphe I07 mais absent du payload I07 V10O ;
- `conservation_residuals` est exigé par I08, alors que V10O ne conserve que deux scalaires séparés, sans bilan de masse ni vecteur de quantité de mouvement.

Le schéma V2 ajoute ces informations et distingue explicitement masse, quantité de mouvement vectorielle et énergie. Cela ferme une lacune de spécification, pas une lacune de données physiques.

## Entrées physiques minimales

Les 32 exigences restent bloquantes : 12 pour l’état initial, 10 pour la résistance et les interactions, 8 pour la validation numérique, et 2 pour les sorties/critères. Zéro exigence est physiquement prête.

Elles couvrent notamment les champs de déplacement et de vitesse, la masse participante par étage, les états d’effort, les lois d’assemblage et de contact, le flambement/post-flambement, la rupture objectivée au maillage, l’entraînement des débris, les frontières de la tour basse, puis les convergences en temps et en espace.

## Bilans de conservation

Le gabarit contient 17 termes par piste, soit 51 lignes. Les 17 valeurs égales à zéro du contrôle satisfont les trois identités masse/quantité de mouvement/énergie. Les 34 cellules des deux pistes non contrôles restent vides ; aucune tolérance physique n’est fabriquée.

## Séparation des preuves

1. **Faits observés ici** : empreintes, champs exacts des interfaces, deux écarts de schéma, comptages et identités nulles.
2. **Résultats du modèle officiel** : aucun résultat officiel de propagation globale n’est importé ou supposé.
3. **Archives** : aucune archive externe n’est lue ; un PDF officiel local est seulement rehaché.
4. **Hypothèses du modèle** : le schéma V2 et la liste minimale sont des exigences de conception, pas des propriétés du WTC 1.
5. **Résultats dérivés** : couverture de schéma, matrice des blocages et gabarit de conservation.
6. **Inconnues** : l’état d’initiation, la propagation, l’arrêt et tous leurs bilans physiques.

## Décision

V10S ferme la chaîne de statuts sans fermer la question physique. Zéro simulation de propagation est exécutée, zéro résultat physique est libéré et aucune conclusion historique d’effondrement ou de non-effondrement n’est autorisée.

## Prochaine étape

Construire un paquet de visualisation 3D à trois pistes, strictement dérivé des états libérés : contrôle logiciel, références dépendantes du modèle officiel clairement étiquetées et cartes d’inconnues pour les étapes bloquées. Produire un fichier Blender dérivé et quelques images fixes avec bannière permanente, sans modifier le master, inventer de mouvement d’effondrement, réinjecter Blender dans les calculs ni présenter la visualisation comme une prédiction physique.
