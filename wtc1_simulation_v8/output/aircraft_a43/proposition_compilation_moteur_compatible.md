# Proposition A44 — moteur MUMPS séparé utilisant le format matériau antérieur

A42 localise une incompatibilité précise : le préparateur Windows utilise les anciens paramètres LAW117, alors que le moteur A35 attend de nouveaux tableaux. A43 vérifie que la source du28juillet utilise21paramètres utilisateur et que leurs21valeurs attendues sont présentes, dans une séquence unique, dans la reprise initiale entière. Ce contrôle limité ne prouve pas toute l’interopérabilité.

Le Starter Linux actuel manque cinq interfaces de son lecteur ouvert. Une interface supplémentaire porte le même nom avec une signature différente. Ajouter cinq fonctions vides ne fournirait donc pas un préparateur correct.

Action proposée après nouvel accord explicite : compiler uniquement le moteur depuis le commit complet **3d75ff13d1946f6d28a43920eac4fa2aae41b27a**, daté du28juillet2026, dans un nouveau dossier séparé. Conserver le préparateur Windows actuel et le moteur MUMPS A35. Aucun changement de physique dans la source, aucun remplacement de matériau ou contact, aucune modification de reprise.

Le script préparé télécharge cette source figée, vérifie ses blobs Git et ceux de la dépendance en cache, puis compile en double précision avec les outils et MUMPS déjà installés. Aucun paquet supplémentaire ni mise à niveau. Six threads CPU maximum, sans GPU ; estimation15–60minutes, plafond strict une heure pour la construction, puis démontage de l’espace temporaire. Nouvelle image de travail indépendante8Gio ; ancienne image conservée.

La source demande la dépendance71, dont la disponibilité n’est pas confirmée. La dépendance67 déjà vérifiée et utilisée lors d’A35 est explicitement proposée, avec les bibliothèques Ubuntu déjà présentes. Seule la métadonnée de construction EXTLIB_VERSION.json est remplacée, original conservé. Cette différence n’est pas supposée équivalente et doit apparaître dans les contrôles. La source du même jour que le paquet Windows ne prouve pas l’identité de son code de construction.

Livrables : source et licence figées, versions, empreintes, journaux, configuration, nouveau binaire si la construction réussit ; contrôles natifs déclarés sur LAW117 et démarrage entier sans changement des données physiques. Bilans, force, masse, momentum, champs et comparaisons au moteur Windows précèdent toute extension. Les dix secondes ne sont pas garanties par une compilation réussie.

Le constructeur préparé n’a pas été exécuté. Il exige un enregistrement d’accord humain explicite pour cette source et ce plafond. L’accord précédent concernait la source bad6688602d770e019b75773d2d5a48b4f9bd918 et la construction A35, terminée en39,29minutes.

Accord supplémentaire requis par AGENTS.md : « Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy. » La publication GitHub A42+A43 est déjà autorisée et continue indépendamment.
