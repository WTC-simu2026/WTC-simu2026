# Passation — IMPACT-I02C → IMPACT-I02D

13 septembre 2026. Lire AGENTS.md, l'état local `harness/state.json`, puis cette passation. Le vieux label V8H n'est pas l'avancement. Harnais avant/après ; archives et anciennes itérations en lecture seule.

## Livré

I02C a couplé la liaison à deux bandes déformables, pas encore à l'aile. Quinze cas acceptés, 293 contrôles booléens, 21 marques de campagne incluant agrégations. 174,604 s cumulées de séquences acceptées. Aucun ancien solveur relancé. Vérifier `release_audit.json` PASS à la reprise.

- Géométrie propre au projet : deux bandes coplanaires 40×25,4 mm, épaisseurs 2/3 mm. Masse totale 13,716 g, E=70 000 MPa, ν=0,33, ρ=0,0027 g/mm³. Coques élastiques, pas de fracture de tôle.
- TYPE8 H2 de longueur nulle, repère fixe, raideurs de rotation nulles, une seule translation active par essai. Poids tributaires de bord/demi-bord, somme d'un rivet équivalent ; ce ne sont pas 12 rivets physiques. Guidage bloque déformation transversale et degrés de liberté hors mode ; pas de recouvrement/excentricité/contact.
- Tangentiel : Fp=6 528 N, d0=0,02 mm, df=0,2/0,5/1 mm, G=0,6528/1,632/3,264 J. Capacités héritées d'I02B ; énergie et décharge hypothétiques. Normal limité à flexion faible charge, F≈0,48 N ; rupture normale non testée.
- Maillages 5/2,5/1,25 mm : 96/352/1 344 coques. Étendue pic 1,82949e-5 en fraction ; énergie 2,69608e-7. Erreur de raideur normale fine 1,11444e-4. Rotation initiale90° reproduite exactement, pas un test de corotation dynamique.
- À 2,5 J et G central : séparation ; à0,39995 ms Ecin=0,5977734 J, Eplaques=0,27023979 J, Eliaison=1,631993 J. La géométrie se sépare réellement. Pas de ressemblance vidéo utilisée comme cible.
- Résidu énergie max1,79497e-5, erreur impulsion max0,0035543. Pas de masse ajoutée, hors arrondi1,78e-15 g.

## Limites ouvertes / révisions à ne pas oublier

- Énergie cinétique résiduelle du chargement monotone, à1,199 ms : moyen0,001279955 J, fin0,001495540 J ; écart14,415 %. Pics et G stables ne rendent pas le champ vibratoire convergé.
- Loi à glissement positif seulement. Les longues R2 faible énergie/Ghaut traversent δ<0 : elles sont rejetées. R3 s'arrête avant, à0,032/0,21 ms. Aucun cisaillement inverse ou contact validé. CycleR3 relâche à+0,05 mm au lieu de0 pour rester dans le domaine.
- R0/R1 et premiers audits rejetés conservés. N=0 explicite pour LAW1 ; marge relative1e-8 sur K de décharge pour éviter correction automatique506, Fp/G inchangés. Avertissement445 NULL INERTIA attendu seulement pour ressorts sans masse/inertie/raideur de rotation ; coques gardent leur inertie.
- Audits initiaux P/Ecin avaient une limite supplémentaire non configurée1e-5 : corrigée vers les seuils configurés2%/1%, résultats initiaux conservés. Pas de réglage des seuils configurés ni de G après observations.
- REAC T01 est une impulsion Nms : ne pas réintégrer. Masse nodale par aires, énergie récupérable F²/(2K), dissipation IE−U. Ne pas effacer IE/masses après suppression.
- Corps élastiques, contraintes longitudinales estimées jusqu'à≈286 MPa, pas de qualification d'alliage Boeing. Contraintes de flexion indisponibles, pas nulles. Réactions en moments non auditées séparément.

## Livrables à réutiliser

Config : `wtc1_simulation_v8/data/impact_i02c_deformable_joint.json` ; sélection des révisions dans `accepted_case_overrides` (défautR2, deux grossiersR1, troiscasR3).

Dossier : `wtc1_simulation_v8/output/impact_i02c_deformable_joint/` : `rapport_impact_i02c.md`, `campaign_audit.json`, `source_manifest.json`, `release_audit.json`, `synthese_impact_i02c.png`. Chaque cas contient cartes, logs, T01, `generation.json`, `results.json`, `history.json`, `computed_frames.npz`.

Scripts : `run_impact_i02c.py`, `audit_impact_i02c.py`, `summarize_impact_i02c.py`, `export_impact_i02c.py`, `present_impact_i02c.py`, `release_impact_i02c.py` dans `wtc1_simulation_v8/scripts/`. Pas de rerun inutile ; auditer les caches.

Nouvelle vidéo : `wtc1_3d_v4/renders/impact_i02c/I02C_liaison_couplee.mp4`, 6,2 s, 31 états nodaux sauvegardés, aucun facteur d'amplification, répétition des images sans interpolation mécanique. Vues de surfaces moyennes, pas de volume 3D Boeing.

ParaView : `wtc1_3d_v4/output/impact_i02c/I02C_coupled_joint_ms.pvd`,31 états natifs d'animation en mm/ms, réouverture VTU vérifiée. Temps légèrement différents de ceux du film nodal. Vérification croisée `animation_cross_audit.json` ; borne d'arrondi position ET déplacement explicitée. Ne pas interpoler la rupture.

## I02D réalisable

Passer à un petit recouvrement peau–semelle avec excentricité et rotations libérées. Définir une loi normale/tangentielle énergétique et irréversible, dont le sens inverse, avant le chargement combiné. Vérifier forces ET moments aux prises, travail, contact après rupture et convergence des observables. Conserver le témoin I02C coplanaire. Après ces tests seulement, brancher une petite zone à la section I02A et comparer au témoin fusionné. Ne pas annoncer une aile physiquement qualifiée.

I01/I02A/I02B, V11F froid et V11R thermique restent inchangés ; V11S différée. Le B762 graphique conserve zéro crédit mécanique. Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète non validée ; aucune conclusion historique ni preuve d'effondrement tirée d'un sous-modèle. Actualiser registre/état uniquement après outputs, rapport et audits vérifiés.
