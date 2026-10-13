# Instantané AIRCRAFT-A58+AIRCRAFT-A59 — 13 octobre 2026

Instantané du **13 octobre 2026** : **AIRCRAFT-A59 terminée**, prochaine étape **AIRCRAFT-A60**. Le registre compte **178 entrées**. A58 précise la chaîne native du blocage géométrique ; A59 prépare un prototype propre de résidu/rigidité surfacique. **La vidéo des dix secondes physiques reste incomplète.**

Le moteur A57 précédemment publié conserve ses corrections autorisées et le passage du témoin mémoire : capacité21 et pointeurSAV exact, en-têteNODREAC intact. **Aucun nouveau correctif, installation ou compilation A58/A59.** A58 lance un seul nouveau Engine instrumenté, CPU1/cap180s, sansGPU. Ordre observé : **SUSER43**, puis **S8ZKE3(TYPE43/LAW117,NEL1,ISMSTR1,JHBE0)**, **S8ZDERICT3**, **SCHKJAB3(DET0,OFF1,élément1)**. La face possède100mm² et hauteur0. L'hypothèse « volume avant toute surface » est rejetée et conservée. Code0/NORMAL suivi deUSER BREAK etSTOP volume nul àT=0 : aucune réponse chargée.

Sept routines sources figées sont auditées en lecture seule, avec empreintes et lignes ; sources brutesAGPL exclues. DansMMATS inspecté, pas de branche spécifique117, sans extrapoler cette absence à tout le programme. SIGEPS117 n'est pas directement instrumentée ; son appel est appuyé par la brancheSUSER43 et le matériau du cas. Retirer le contrôle de volume ne constituerait pas un traitement cohésif correct.

A59 n'exécute **aucun Engine/Starter**. Un prototype propre passe **112contrôles** : équilibre, intégrale surfacique fermée, rang12 et translations nulles, tangente active par différences finies, adoucissement négatif, covariance3D des forces/matrices, traction/travail/rechargement sur les quatre témoins natifsA57 réutilisés avec empreintes, sans les rejouer. CPU1, sansGPU, plafond120s, résultats en moins d'une seconde. Seuils physiquesA17 inchangés, aucune masse, matériau ouRKE compensatoire.

**Domaine limité** : plans rectangulaires en repère de référence fixe, matrice élastique3axes et tangente active en modes purs à adoucissement linéaire. Les directions passives gardent le dommage gelé. Modes mixtesLAW117, repères mobiles, tangente géométrique, état d'essai/retour arrièreNewton et connexion au moteur **non qualifiés**. STIFM deSUSER43 est une surestimation pour le pas explicite, pas une tangente implicite cohérente. Le prototype n'est pas prêt à être intégré à l'impact entier.

Les [rapports A58](wtc1_simulation_v8/output/aircraft_a58/rapport_aircraft_a58.md) et [A59](wtc1_simulation_v8/output/aircraft_a59/rapport_aircraft_a59.md) séparent les six catégories de preuve. Archives, anciennes sorties et hypothèses rejetées conservées. CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, A52 non intégré, couverture locale et domaines de matériau restent échoués ou manquants. Aucun dégât connu utilisé comme cible.

Meilleur impact entierA20 : **0,0200001220703125seconde**. L'ancienne projection linéaire6,89479jours pour10s est un ordre de grandeur historique, pas une ETA actuelle. Aucune prolongation de l'ancien état hors domaine ; aucun temps des témoins/prototype crédité comme impact. Aucune vidéo fabriquée par extrapolation ou ralenti. Intégrité de publication et physique restent distinctes.


1 archives complémentaires ; 133 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
