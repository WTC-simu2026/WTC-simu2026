# WTC 1 — V9O — Aperçu Blender du storyboard

## Conclusion courte

V9O est validée comme **visualisation 3D illustrative à basse résolution**, et uniquement comme cela. Le fichier produit montre trois silhouettes rigides pendant l’approche, puis les fige au premier contact. Il ne calcule ni l’impact, ni la rupture, ni les débris, ni le feu, ni la réponse de la tour.

Validation générale : **PASS**.

## 1. Faits contrôlés

- Le fichier maître V4.2 conserve son empreinte SHA-256 : `1322d1a216f99d99872aa2d6fc16ec40d71f8ee476b11fd89d074e313bb3a6b1`.
- Un nouveau fichier dérivé existe : `wtc1_3d_v4/output/WTC1_V9O_STORYBOARD_PREVIEW.blend` (596413 octets).
- Onze vues PNG de 640 × 360 et une planche de contrôle de 1280 × 540 existent et correspondent au manifeste.
- Le fichier dérivé a été rouvert par Blender 5.2.0 LTS pour un audit indépendant en lecture seule.
- Les trois scènes V9O, les trois caméras et les onze repères temporels sont effectivement enregistrés.

## 2. Résultats provenant du modèle officiel

Les trois enveloppes d’approche, leurs vitesses et leurs orientations restent celles déjà transcrites et gelées en V9N. V9O ne les requalifie pas et ne les transforme pas en probabilités.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d’archive n’a été introduite. L’archive source n’a été ni lue ni rescannée en V9O.

## 4. Hypothèses propres au modèle visuel

- silhouette d’avion rigide et simplifiée ;
- interpolation à vitesse constante avant contact ;
- couleurs, éclairage, cadrages et décalages latéraux destinés à la lisibilité ;
- géométrie de façade partiellement reconstruite déjà documentée en V4.2/V9N.

Ces choix sont graphiques. Ils ne constituent pas une validation physique.

## 5. Résultats dérivés

| Branche | Image de contact | Images-clés de position | Immobilité après contact |
|---|---:|---|---|
| less_severe | 865 | [481, 721, 865, 1801] | PASS |
| base | 1009 | [481, 721, 1009, 1801] | PASS |
| more_severe | 1153 | [481, 721, 1153, 1801] | PASS |

- Corps rigides Blender : **0**.
- Systèmes de particules : **0**.
- Modificateurs fluides : **0**.
- Monde de corps rigides : **0**.
- Solveur structurel exécuté : **non**.
- Physique Blender exécutée : **non**.

## 6. Contradictions, limites et informations manquantes

Restent non qualifiés : le contact déformable-déformable à l’échelle pertinente, la rupture du projectile et de la façade, la convergence de l’impulsion, les débris, le carburant, le feu, les dommages du noyau et la réponse globale. Par conséquent, V9O ne permet pas de dire qu’une simulation physique de l’impact de l’avion sur la façade a réussi.

## Décision

V9O ferme l’étape de **prévisualisation fixe**. Elle autorise V9P à fabriquer un animatique de 75 secondes à partir du seul fichier dérivé validé, avec le bandeau permanent et l’arrêt au contact. Elle n’autorise toujours aucune simulation physique globale.

## Reproductibilité

- Configuration : `wtc1_simulation_v8/data/v9o_blender_storyboard_preview.json`
- Constructeur Blender : `wtc1_3d_v4/scripts/build_v9o_storyboard_preview.py`
- Audit Blender : `wtc1_3d_v4/scripts/audit_v9o_storyboard_preview.py`
- Manifeste : `wtc1_3d_v4/output/v9o_visualization_manifest.json`
- Planche de contrôle : `wtc1_3d_v4/renders/v9o/wtc1_v9o_proof_sheet.png`
- Graine déclarée : `9122001` (exécution déterministe, sans tirage aléatoire utilisé)
