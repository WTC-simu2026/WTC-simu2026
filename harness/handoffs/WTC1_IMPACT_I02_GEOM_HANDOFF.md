# Reprise - IMPACT-I02-GEOM livrée ; IMPACT-I02 mécanique reste à faire

Lire AGENTS.md puis harness/state.json. Jeremy a demandé de trouver et utiliser un modèle 3D d'avion sur Internet. Géométrie intégrée, pas nouveau calcul d'impact. Priorité mécanique toujours premier contact ; thermique V11R terminée/V11S différée. I01 non érodante et ses échecs restent inchangés.

## Modèle disponible

- Source GitHub : Flightradar24/fr24-3d-models, commit dd53267690c6a4ecbb290a3acf0284333a5d68a9. Désigné 767-200, licence GPLv2 du dépôt, notices conservées.
- Sources figées : wtc1_simulation_v8/input/impact_i02_geom/fr24_dd532676/ ; cinq fichiers vérifiés Git blob + SHA256 (GLB1, blend, ZIP, README, LICENSE). Ne pas télécharger à nouveau.
- Livrables **finals** : wtc1_3d_v4/output/impact_i02_geom/final/B762_GEOMETRY_ONLY.blend et .glb, paquet ZIP avec sources/licence/scripts, audits ; planche dans wtc1_3d_v4/renders/impact_i02_geom/final/B762_apercu_annote.png.
- Configuration : wtc1_simulation_v8/data/impact_i02_geom.json. Rapport : wtc1_3d_v4/output/impact_i02_geom/rapport_impact_i02_geom.md.

## Mesures et limites à ne pas oublier

Source GLB assemblée, pas tous les objets non assemblés du blend d'origine. Longueur 50,36791 m et envergure 46,30930 m. Boeing Rev K §2.2.1 p.2-8/PDF28 donne 48,51 m et 47,57 m : écarts +3,830 % et -2,650 %. Aucun étirement correctif. Document constructeur déjà sauvegardé, page rendue et lue ; les cotes sont absentes de la couche texte. Ne pas refaire la recherche documentaire.

138 maxima d'indices erronés dans les métadonnées source, indices réels et buffers contrôlés. Copie dérivée : 126 triangles de surface nulle retirés (liste conservée), 155 ensembles/12521 triangles. Réouverture Blender et GLB2 : tous les triangles conservés vérifiés, erreur max 2,277e-7 m, aucune dynamique. Originaux et brouillons préservés ; utiliser le sous-dossier final.

**Crédit mécanique nul** : ni masse, ni rigidité, ni résistance, ni jonction, ni rupture justifiées par ces surfaces. Pas longerons/nervures/épaisseurs de fabrication ni distribution carburant validés. Ne pas utiliser l'intégrité d'un maillage graphique comme résultat d'impact.

## Suite opérationnelle

Poursuivre IMPACT-I02 prévu dans WTC1_IMPACT_I01_HANDOFF.md : section d'aile structurée et contact instrumenté, hypothèses explicites, énergie et rupture contrôlées. Le modèle trouvé sert de contexte/enveloppe visuelle après correction documentée de ses dimensions ; ne pas le brancher tel quel sur le solveur. Préserver le témoin I01, les réserves maillage/contact/plasticité tardive, V11F froid et V11R. Ni nouvelle lecture vidéo ni nouvelle animation de pénétration prescrite requise.

Scripts acquis : intake_impact_i02_geom.py, decode_i02_glb1.py, read_i02_boeing_dimensions.py (simulation/scripts) ; inspect/build/verify/present_impact_i02_geom.py (3d/scripts). Dernier audit release_impact_i02_geom.py ; harnais avant/après et registre à jour uniquement après vérification.
