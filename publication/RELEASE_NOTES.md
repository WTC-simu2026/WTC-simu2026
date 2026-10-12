# Instantané AIRCRAFT-A42+AIRCRAFT-A43 — 12 octobre 2026

Instantané du **12 octobre 2026** : **AIRCRAFT-A43 terminée**, prochaine étape **AIRCRAFT-A44**, compilation supplémentaire en attente d’accord explicite. Le registre compte **162 entrées**. A42+A43 localisent une incompatibilité de préparation LAW117 et préparent une voie de compilation séparée. Les anciens résultats, tentatives et critères échoués sont conservés.

A42 teste le modèle entier dès son état initial en explicite. Il avorte aussi avant la première avance ; le problème ne vient donc pas exclusivement du CHECK implicite. Une trace d’avortement installée localise l’arrêt dans **SIGEPS117**, pendant les forces cohésives. La lecture vérifiée des en-têtes natifs montre pour LAW117 **NUPARAM=0, NIPARAM=0, NTABLE=0**, alors que la source du moteur MUMPS A35 attend **14 paramètres réels, 6 entiers et 2 tables**. L’ancien préparateur Windows fournit une autre représentation.

Une nouvelle entrée ajoute deux fonctions de facteur constant1, à résistances450/100MPa et énergies de rupture inchangées. Son équivalence d’entrée est vérifiée ; elle ne corrige pas le format préparé. Le moteur Linux avorte encore, tandis que **le moteur Windows termine normalement sur le même état initial frais et les mêmes cartes**, en3cycles. La préparation garde2avertissements et échoue au critère strict. Aucune extension au-delà des20ms A20, aucune qualification native de cette variante ni modification de reprise.

A43 relève **cinq interfaces Reader absentes** et une interface supplémentaire dont la signature C ne correspond pas à son appel Fortran. Aucune fonction vide n’est ajoutée. La source complète du28juillet, commit **3d75ff13d1946f6d28a43920eac4fa2aae41b27a**, utilise l’ancien tableau LAW117 de21valeurs, présent dans une séquence unique de la reprise. Cette corroboration limitée et les blobs Git vérifiés ne sont ni un parseur complet ni une preuve d’identité avec le binaire Windows.

La [proposition A43](wtc1_simulation_v8/output/aircraft_a43/proposition_compilation_moteur_compatible.md) prépare la compilation du seul moteur antérieur avec MUMPS déjà installé, séparément, au maximum6threads CPU et une heure, sans nouveau paquet ou patch de physique. La dépendance67 en cache est proposée au lieu de71, différence explicitement non qualifiée. Le constructeur est écrit et vérifié par analyse de syntaxe ; **il n’a pas été exécuté** et demande un nouvel accord pour cette source. Comparaisons LAW117, bilans, champs et démarrage entier borné sont requis avant extension.

Les [rapports A42](wtc1_simulation_v8/output/aircraft_a42/rapport_aircraft_a42.md) et [A43](wtc1_simulation_v8/output/aircraft_a43/rapport_aircraft_a43.md) séparent faits, sources, archives, hypothèses, résultats et lacunes. Les binaires, bibliothèques et sources tierces brutes restent exclus de la publication. Compilation A35 terminée39,29min ; aucune nouvelle installation ou compilation. Le contact TYPE7 A41 reste qualifié dans son témoin ; contact chargé et croissance A40, peaux A34 et raffinement A36 restent échoués, et les cinq TYPE25 entiers restent à vérifier.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20millisecondes physiques**. Aucun temps de témoin ou de démarrage n’est crédité à l’extension entière, aucun coût10s extrapolé. Aucun dommage connu comme cible. L’intégrité de publication ne valide pas la physique ou l’événement historique.

Les anciennes archives et les échecs restent conservés.


2 archives complémentaires ; 121 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
