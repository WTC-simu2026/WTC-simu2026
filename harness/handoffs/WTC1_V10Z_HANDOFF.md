# Reprise WTC 1 après V10Z

État autoritatif : `harness/state.json`, V10Z terminée, V11A suivante. Reprendre dans le dossier actif ; lire AGENTS.md et l'état, puis exécuter `harness/tools/Test-WtcHarness.ps1`.

V10Y : première chaîne réduite impact/dommages, température, capacité, initiation puis propagation verticale. 729 cas : 288 progressions au sol, 144 arrêts, 297 sans initiation. Les fréquences de grille ne sont pas des probabilités. Les paramètres structuraux restent exploratoires et les dommages/températures dépendent d'enveloppes issues des modèles officiels.

V10Z : scénario GRID-0119 rejoué exactement (35 champs), 96 événements, 220 images enregistrées dans Blender. Vidéo 768×432, 12 images/s, durée 18,33 s. Cinq vues et planche de contrôle. Master V4.2 intact. La scène WTC1_MASTER est une référence distincte de la scène animée V10Z_GRID0119_ANIMATION ; cette dernière ne contient pas de physique Blender.

Livrables :

- `wtc1_3d_v4/output/WTC1_V10Z_EXPLORATORY_GRID0119.blend`
- `wtc1_3d_v4/renders/v10z/wtc1_v10z_grid0119_exploratory.mp4`
- `wtc1_3d_v4/renders/v10z/wtc1_v10z_grid0119_proof_sheet.png`
- `wtc1_simulation_v8/output/rapport_wtc1_v10z_visualisation_3d_exploratoire.md`
- `wtc1_simulation_v8/output/v10z_grid0119_visualization_driver.json`

Le scénario initie au niveau 96 à 5810 s, 304 s avant la référence chronologique. Il appartient à 18 cas progressants ex aequo ; le choix a été fait après observation de la grille. Sa progression est de 14,1263386663 s après une chute initiale supposée de 1,8288 m.

Priorité V11A :

1. Le temps initial de chute est absent : V10Y attribue déjà déplacement et vitesse à son temps relatif zéro. Intégrer le mouvement depuis le repos, avec la résistance active dès le premier déplacement.
2. V10Y termine à 109,5 étages équivalents de masse : le demi-étage d'initiation restant est absent. Fermer l'inventaire initial, mobile, accré­té et immobile.
3. Le dernier état garde 326,16 GJ d'énergie cinétique ; ne pas confondre arrivée au dernier niveau et débris stabilisés. Rendre l'état terminal explicite.
4. Recalculer les mêmes scénarios avec paramètres hérités, sans réglage pour rapprocher la chronologie observée. Expliquer les changements de régime. Ensuite seulement étendre les chemins d'efforts spatiaux.

Les géométries diffèrent explicitement : V10Y/V10Z ont 110 niveaux uniformes de 3,6576 m, soit 402,336 m ; le master V4.2 garde 416,9664 m. Les façades animées sont échantillonnées pour le dessin. Les étages masqués restent dans la masse du calcul ; aucun volume de débris n'est calculé.

Exécutions conservées : `tmp/v10z_attempt_01` (cadrage rejeté), `tmp/v10z_attempt_02` (aperçu et rendu acceptés), `tmp/v10z_attempt_02/rejected_render_01` (sélection du format vidéo interrompue). Blender 5.2 requiert `image_settings.media_type='VIDEO'` avant FFMPEG. Aucune installation requise. Le rendu vidéo accepté a pris environ 49 s.

Ne pas relancer V10Y complet pour reconstruire le pilote : il est déjà vérifié et conservé. Ne pas modifier les itérations finalisées. Les archives sources et `work/official_sources/` restent en lecture seule.
