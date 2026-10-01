# WTC 1 — V10T : visualisation 3D des statuts à trois pistes

Généré : `2026-09-04T08:16:54Z`

Statut : **PENDING_MANUAL_VISUAL_QA**

## Résultat

Le paquet crée un nouveau dérivé Blender statique (`wtc1_3d_v4/output/WTC1_V10T_THREE_TRACK_STATUS.blend`), 6 vues fixes et une planche de contrôle. Le master V4.2 conserve son empreinte SHA-256. Toutes les scènes V10T sont limitées à l’image 1, sans image clé, corps rigide, particule, fluide, collision, fracture ou solveur physique.

Les trois pistes restent séparées :

- **contrôle logiciel zéro** : test de chaîne uniquement, jamais un non-effondrement historique ;
- **références dépendantes du modèle officiel** : statuts et plages transcrits, jamais promus en état physique indépendant ;
- **événement physique** : indéterminé de l’impact jusqu’à la propagation ou l’arrêt.

## Mesures représentées

- impact/dommages : 89 segments de référence sur les trois cas officiels dépendants ;
- feu/thermique : 105 plages, 47 extrémités chaudes hors domaine commun, et 0/8 champs SFRM disponibles ;
- initiation : 58 plages entièrement évaluables dans le domaine déclaré, 47 partielles, aucune initiation physique ;
- propagation/arrêt : 0/32 entrées physiques prêtes, donc aucun calcul de propagation.

## Contrôles

- rendu technique : 17/17 contrôles passés ;
- inspection visuelle : **PENDING_MANUAL_VISUAL_QA** ;
- états physiques libérés vers Blender : 0 ;
- issue historique assignée : 0.

## Discipline de preuve

1. **Faits observés** : identités de fichiers, dimensions et empreintes des rendus, scènes statiques, compteurs nuls de physique Blender.
2. **Résultats du modèle officiel** : les nombres affichés sont uniquement les références déjà transcrites dans V10P–V10R et restent dépendants de ce modèle.
3. **Affirmations des archives** : aucune archive externe n’est lue dans V10T ; un PDF officiel local est seulement rehaché.
4. **Hypothèses du modèle** : couleurs, cadrages, cartes et cadre des étages 93–99 sont des choix de présentation sans crédit mécanique.
5. **Résultats dérivés** : matrice 3 pistes × 4 étapes, paquet Blender, six vues et planche de contrôle.
6. **Contradictions et inconnues** : dommages physiques, feu réel, historiques thermiques par membre, initiation, propagation, arrêt et issue finale restent inconnus.

## Décision

V10T fournit la visualisation 3D auditée de l’état du programme, pas une animation de l’événement. L’absence de mouvement d’effondrement est une contrainte de preuve, pas un résultat de non-effondrement.

## Prochaine étape

Qualifier un premier cas mécanique borné et indépendant dans CalculiX avec solution analytique, convergence de maillage et bilan force-déplacement. Le cas doit rester un benchmark logiciel de composant sans attribution au WTC 1 tant que les plans, sections, assemblages et chemins d’efforts réels manquent.
