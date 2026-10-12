# AIRCRAFT-A43 — source antérieure et compilation ciblée préparées

A43 vérifie une voie concrète après l’incompatibilité LAW117 localisée A42 : un moteur compilé depuis la source complète du28juillet utilise les21paramètres antérieurs présents dans la reprise Windows. Ce candidat reste à compiler et qualifier. Aucun solveur, compilation ou installation exécuté pendant A43.

## 1. Faits directement observés ou transcrits

La construction Starter A35 a cinq symboles non résolus : cpp_create_rbodies_from_rigid_parts_, cpp_evaluate_rbodies_number_from_rigid_parts_, cpp_is_part_with_elements_, cpp_sale_mesh_create_ et cpp_get_include_file_by_index. Les appels sont présents dans le préparateur figé ; les implementations correspondantes ne figurent pas dans son lecteur ouvert. Une sixième interface, cpp_get_number_of_include_files, reçoit deux arguments côté Fortran bindC, alors que le C++ fourni en reçoit un. Une simple résolution des noms ne suffirait pas à prouver la compatibilité d’appel.

Les métadonnées publiques interrogées renvoient deux miroirs de dépendances, versions59et37. Elles ne fournissent pas la dépendance82 du candidat A35 ni la71 du candidat de juillet. Cela ne prouve pas leur inexistence. La dépendance67 déjà conservée et vérifiée A35 reste disponible localement.

La requête d’historique avant le29juillet renvoie le commit3d75ff13d1946f6d28a43920eac4fa2aae41b27a, daté28juillet2026à15:06:41UTC. L’arbre récursif est complet, et cinq fichiers de revue concordent exactement avec leurs blobs Git : les deux routines LAW117, les configurations moteur et sa licence. Une assertion initiale de revue qui exigeait PARMAT directement dans le moteur est conservée comme erreur de script ; la source reçoit en réalité un tableau utilisateur UPARAM de21entrées. La revue corrigée utilise ce contrat explicite sans modifier la source.

Le constructeur futur est écrit, sa syntaxe analysée et son empreinte enregistrée. Il n’est pas lancé. Il exige un enregistrement d’accord humain précis avant toute écriture dans le nouveau candidat logiciel. Les anciens moteurs, sources, archives et image de travail sont conservés.

## 2. Résultats d’un modèle officiel

Aucun nouveau calcul d’un modèle officiel. La source publiée dans le miroir montre une refonte de LAW117 le5août2026, postérieure au paquet Windows actuel du28juillet. Ce contexte explique le changement d’interface ; il ne prouve pas l’identité exacte entre une source du même jour et un binaire distribué.

- [Source moteur LAW117 antérieure, commit figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/materials/mat/mat117/sigeps117.F)
- [Source préparateur LAW117 antérieure](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/starter/source/materials/mat/mat117/hm_read_mat117.F)

Le moteur antérieur reçoit21paramètres utilisateur et deux fonctions par son ancien chemin, sans accéder aux nouvelles tables MATPARAM de SIGEPS117_A35. Les options de construction MUMPS existent dans la configuration figée. Ni cette inspection ni la compilation proposée ne constituent une validation mécanique.

## 3. Affirmations provenant des archives locales

Aucune nouvelle inspection d’archive historique, vidéo, image ou PDF. Aucun résultat utilisé pour ajuster une empreinte connue. Les données scientifiques A20–A42 et les critères échoués sont conservés.

## 4. Hypothèses propres au modèle

Graine1102068, zéro tirage. A43 ne change aucune donnée physique. La source candidate doit être utilisée intégralement, sans recopier seulement l’ancienne loi dans un moteur plus récent. Le nouveau moteur resterait séparé ; le préparateur Windows et A35 seraient conservés.

Compilation proposée : double précision, GNU13/OpenMPI4.1.6/MUMPS5.6.2 installés, six threads CPU au maximum, aucun GPU, une heure de construction puis démontage. Nouvelle image indépendante8Gio. Aucun nouveau paquet ou mise à niveau. Dépendance67 déjà contrôlée par Git et empreinte au lieu de71 : différence explicitement non qualifiée, seule métadonnée de construction EXTLIB_VERSION.json remplacée et original conservé. Les sources mécaniques restent celles du commit complet. Aucun faux symbole Reader ou patch de reprise.

Un contrôle après construction doit comparer force, déplacement, énergie, momentum, masse et champs entre les deux moteurs, sur LAW117 déclaré puis sur un démarrage entier borné. Les critères ne sont pas relâchés pour obtenir un calcul. Les limites de compatibilité des cinq TYPE25 restent indépendantes.

## 5. Résultats dérivés

Une séquence unique de21réels big-endian dans la reprise A37 concorde avec l’ordre et les valeurs de l’ancienne source LAW117 :4400,800,1,450,100,1,50,50,4,2,2,1,450/4400,100/800,100/450,1,1,1,1,3,0. Cette corroboration limitée n’est pas un parseur complet de la reprise. Elle distingue les anciens paramètres utilisateur des nouveaux compteurs MATPARAM tous nuls observés A42 ; ces deux stockages ne doivent pas être confondus.

La piste choisie évite une réparation partielle du Reader : compiler uniquement le moteur antérieur complet avec MUMPS, puis tester sa lecture des mêmes états Windows. La proposition, configuration, preuve de source et script futur sont réellement enregistrés avant demande d’accord. L’accord précédent portait sur une autre source et une construction A35 terminée39,29minutes.

## 6. Contradictions et informations manquantes

La compilation du nouveau candidat n’est pas autorisée ni exécutée dans A43. La disponibilité des dépendances originales est non confirmée. La dépendance67 n’est pas présumée équivalente à71. Le code de construction exact du binaire Windows reste inconnu. Les autres lois, conditions, champs, contacts et trajectoires demandent des contrôles natifs ; aucune interopérabilité générale inférée d’une séquence de21valeurs.

Le démarrage Windows A42 n’étend pas A20. Le meilleur impact entier reste≈20ms. A41contact direct qualifié seulement dans son témoin ; A40chargé/croissance, A34peaux et A36raffinement restent échoués. Dix secondes physiques3D puisMP4/GIF demeurent incomplètes. Aucun coût10s annoncé depuis le cube ou cette revue.

AIRCRAFT-A44 : après accord humain explicite demandé sur la proposition A43, construire uniquement un moteur MUMPS séparé depuis la source complète3d75ff13d1946f6d28a43920eac4fa2aae41b27a(28juillet2026), sans patch de physique, installation ou remplacement des moteurs. Six threads, plafond1h, dépendance67en cache au lieu de71 explicitement non qualifiée. Le constructeur préparé est figé dans A43. A42 localise l’incompatibilité du nouveau SIGEPS117 avec la préparation Windows; A43 corrobore les21anciens paramètres natifs et identifie cinq interfaces manquantes plus une signature discordante du Reader. Ne créer aucune fonction vide. Après construction, vérifier versions/bibliothèques, LAW117 natif et bilans/comparaisons Windows/Linux, puis démarrage entier explicite et CHECK conditionnel. Toute incompatibilité persistante reste échouée. Ne modifier ni reprise binaire ni masse/matériau/contact pour la contourner. Contact direct A41 qualifié seulement dans son témoin; A40chargé/croissance, A34peaux et A36raffinement restent échoués. Meilleur impact entierA20≈20ms; objectif10sphysiques3D puisMP4/GIF incomplet. Publier la paire A42+A43 avec les échecs et cette proposition, selon autorisation déjà donnée. Pas de nouvelle compilation avant réponse à la question A43.
