# Proposition : solveur séparé avec MUMPS

Le binaire Windows actuel s’arrête avec **MUMPSrequired** sur les sondes implicites A31. Ubuntu 24.04.4 WSL dispose de CMake, GCC et Make, mais pas de GFortran ou MPI sur PATH; aucun paquet MUMPS n’apparaît dans l’inventaire. Aucune installation ou compilation n’a été effectuée.

Action proposée après accord explicite : installer dans cet Ubuntu les seuls outils manquants GFortran, OpenMPI, MUMPS, ScaLAPACK et LAPACK ainsi que leurs dépendances indispensables; compiler une version séparée dans `wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate`. Aucun remplacement du solveur Windows ni modification de son code. Pas de mise à niveau générale. Compilation limitée à six threads processeur et une heure; estimation 15–60 minutes, espace 2–8 Go.

Source candidate figée : miroir gabrielrussell/OpenRadioss, commit **bad6688602d770e019b75773d2d5a48b4f9bd918**. Documentation et scripts de construction contrôlés par empreintes de blobs Git; licence AGPL-3.0 conservée. Ce n’est pas une preuve d’identité avec le binaire installé. Les instructions de compilation indiquent MUMPS en double précision avec MPI; les chemins de bibliothèques effectivement présents seront vérifiés avant construction. Toute erreur, option et dépendance sera journalisée. Aucun patch de physique proposé.

Livrables : binaires séparés si la construction réussit, empreintes, versions et journaux; nouvelles sondes implicites déclarées sur un cube physique à intérieur libre, bilans, travail, masse et champs. Les échecs restent conservés. Aucun fichier de reprise Windows n’est supposé compatible. Des témoins explicite/implicite de cette même nouvelle version seront nécessaires avant transfert à un modèle entier.

La construction peut échouer et ne garantit ni une accélération ni dix secondes d’impact. Elle permettrait de tester une voie actuellement indisponible. Les propriétés matérielles, prises, contacts et défauts A32/A33 restent à résoudre.

Accord requis par `AGENTS.md` : « Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy. » La publication GitHub est déjà autorisée; cette installation et compilation constituent une action supplémentaire.
