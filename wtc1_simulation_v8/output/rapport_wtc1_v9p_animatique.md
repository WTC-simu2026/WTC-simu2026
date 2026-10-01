# WTC 1 — V9P — Animatique 3D illustrative

## Conclusion courte

V9P produit un animatique silencieux de **75 secondes**, en 640 × 360 à 24 images/s. Il montre uniquement l’approche géométrique avant contact, puis une image figée au premier contact et des fiches explicatives. Validation générale : **PASS**.

Ce livrable n’est pas une simulation physique de l’impact sur la façade.

## 1. Faits contrôlés

- Vidéo : `wtc1_3d_v4/renders/v9p/WTC1_V9P_ANIMATIC_75S.mp4` ; durée mesurée **75.000000 s** ; **1800** images ; codec `h264` ; aucune piste audio.
- Le dérivé V9O et le maître V4.2 conservent leurs empreintes ; aucun fichier Blender source n’a été enregistré.
- Les 336 images animées appartiennent aux quatre intervalles pré-contact.
- Les trois échantillons de l’intervalle de contact ont un écart maximal de **0** niveau de canal : l’image est strictement figée.
- Les treize échantillons contiennent le panneau inférieur du bandeau ; couverture horizontale orange minimale : **0.944**, sur au moins **23 lignes** par image.

## 2. Résultats provenant du modèle officiel

Les trois enveloppes de vitesse et d’orientation sont les entrées déjà transcrites et gelées en V8S/V9N. Elles ne sont ni recalculées ni présentées comme des probabilités.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d’archive n’a été introduite. L’archive source n’a été ni lue ni rescannée.

## 4. Exigence utilisateur : trois cages d’escalier

Le futur modèle de tour doit documenter puis intégrer **trois cages d’escalier**. V9P enregistre cette exigence sur la carte finale et dans un fichier dédié. À ce stade, leur position exacte, leur continuité verticale, leur construction, leurs connexions, leur masse et leur état d’endommagement ne sont pas qualifiés.

En conséquence, V9P ne leur attribue **aucune masse, rigidité, résistance ni capacité de chemin de charge**. Leur contribution éventuelle devra être établie par des plans et détails de construction traçables.

## 5. Hypothèses propres à la visualisation

- silhouettes d’avion rigides et schématiques ;
- interpolation géométrique à vitesse constante pour `t < 0` ;
- rendu des mouvements à 12 images/s, dupliqué à 24 images/s pour l’encodage ;
- cadrages, couleurs, éclairage et coupes franches destinés à la lisibilité.

## 6. Résultats dérivés

- 11 plans contigus totalisant 75 s ;
- 4 séquences animées avant contact ;
- 0 séquence 3D mobile après contact ;
- 1 intervalle de contact figé ;
- 3 fiches explicatives après le contact ;
- 0 corps rigide Blender, 0 particule, 0 fluide et 0 monde physique.

## 7. Contradictions, limites et informations manquantes

Ne sont toujours pas qualifiés : le contact déformable-déformable, la rupture du projectile et de la façade, la convergence de l’impulsion, les débris, le carburant, le feu, les dommages du noyau, le rôle mécanique des cages d’escalier et la réponse globale de la tour.

## Décision

V9P valide l’animatique comme média illustratif. V9Q devra effectuer un audit documentaire ciblé des trois cages d’escalier avant toute attribution structurelle ou nouveau calcul global.

## Reproductibilité

- Configuration : `wtc1_simulation_v8/data/v9p_low_resolution_animatic.json`
- Rendu Blender : `wtc1_3d_v4/scripts/render_v9p_motion_sequences.py`
- Encodage et audit : `wtc1_simulation_v8/scripts/run_v9p_animatic_audit.py`
- Manifeste des mouvements : `wtc1_3d_v4/output/v9p_motion_render_manifest.json`
- Manifeste de l’animatique : `wtc1_3d_v4/output/v9p_animatic_manifest.json`
- Planche de contrôle : `wtc1_3d_v4/renders/v9p/wtc1_v9p_audit_contact_sheet.png`
- Graine déclarée : `9122001` ; aucun tirage aléatoire utilisé.
