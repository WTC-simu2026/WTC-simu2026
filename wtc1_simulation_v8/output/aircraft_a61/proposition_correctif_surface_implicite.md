# Proposition A61 — rigidité surfacique d’itération, sixième moteur isolé

Statut : préparé, non appliqué et non compilé. Cette modification n’est couverte par aucun accord moteur antérieur.

## Problème concret et modification

Le témoin TYPE43/LAW117 à hauteur nulle appelle correctement les forces surfaciques natives, puis échoue à T=0 dans la rigidité volumique S8ZKE3. Les nouveaux témoins explicites A60 qualifient la branche mixte déclarée, mais sa dérivée exacte est généralement non symétrique et l’assemblage natif ASSEM_KII/ASSEM_KIJ stocke un triangle. Insérer cette dérivée directement ou changer seulement le drapeau MUMPS serait incorrect.

Une seule nouvelle différence porte sur engine/source/elements/solid/solide8z/s8zke3.F : avant SRCOORK et les dérivées volumiques, TYPE43 + LAW117 + Ismstr1 appelle une nouvelle routine ajoutée au même fichier. Elle forme une matrice surfacique symétrique d’itération avec EN/ET natifs, les quatre aires de référence déjà conservées par SUSER43, les fonctions SDEF43 et la normale du plan moyen courant. Les points supprimés n’ajoutent plus de matrice. Les blocs suivent ASSEM_KII/KIJ ; les autres branches conservent leur code.

Cette matrice élastique est une approximation d’itération, pas la tangente cohérente d’adoucissement ou de géométrie. Le résidu de force, la loi, les états de dommage et l’énergie restent calculés par SUSER43/SIGEPS117. Aucune épaisseur fictive, modification de masse/matériau, terme RKE ou assouplissement d’un seuil physique. Les trois corrections déjà autorisées restent présentes dans le nouveau moteur ; les cinq anciens moteurs restent conservés.

## Préparation vérifiée et limites

44contrôles propres passent : aire uniforme/nonuniforme, reconstruction triangulaire, équilibre et translations nulles, rang12, spectre non négatif, changement de repère courant, exclusion des points supprimés, géométries invalides rejetées ; neuf résolutions à résidu mixte complet convergent au même équilibre avec états validés gelés. Une égalité bit à bit échouée reste archivée ; R1 utilise la tolérance matricielle1e-12 déjà déclarée, sans changement de seuil. Aucune compilation Fortran ni convergence native n’est revendiquée. Sources, lignes, empreintes, différence exacte et script de production sont sauvegardés. Le code source/différence AGPL reste hors des archives publiques MIT.

L’ordre natif de restauration des états Newton et l’objectivité des grandes rotations ne sont pas qualifiés. Le candidat n’altère pas les routines d’état existantes : les futurs témoins doivent vérifier leur comportement, et un échec bloque l’intégration. Les branches Ismstr autres que1 ne sont pas prises en charge par cette proposition. Un arrêt fermé code61 est prévu pour un agencement/une aire/un matériau non admissible ; il ne peut constituer un essai mécanique réussi.

## Exécution soumise à accord distinct

Appliquer exactement cette différence dans un sixième moteur isolé AIRCRAFT-A62, sources figées et trois anciens correctifs conservés. Estimation compilation5–15minutes, plafond absolu1heure, six CPU au maximum, sans GPU ni installation. Puis au maximum12 nouveaux contrôles Engine à un CPU et180s chacun : d’abord élastique implicite chargé, puis dommage/cycles/états, enfin régressions du nouveau binaire. Estimation des contrôles5–20minutes. Aucun impact de plusieurs heures lancé par cet accord.

Les critères initiaux et anciens échecs restent visibles. La meilleure fenêtre entière reste0,0200001220703125s ; la vidéo des dix premières secondes physiques n’existe pas encore. Après les contrôles natifs, l’intégration avion/façade restera conditionnée aux autres critères entiers déjà ouverts.
