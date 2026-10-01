# WTC 1 — V9H, ingestion sélective des signaux analogues S355

## Conclusion courte

V9H a vérifié et conservé 55 fichiers pré-déclarés, pour 1443163 octets décompressés. Le ZIP complet n'a pas été téléchargé. Le serveur a transféré 0 octets par lectures partielles lors de cette exécution; 55 fichier(s) provenaient d'un cache local vérifié.

Le reçu durable de l'acquisition distante initiale conserve 569802 octets transférés et les plages HTTP exactes.

Cette étape qualifie l'identité et le format des petits fichiers analogues. Elle ne constitue ni un ajustement de loi matériau, ni une validation de rupture, ni une simulation d'impact de façade.

## 1. Faits directement observés ou transcrits

- Fichiers attendus/vérifiés: 55 / 55.
- Taille compressée annoncée des entrées: 563657 octets.
- Taille décompressée vérifiée: 1443163 octets.
- CRC32, taille et chemin ZIP conformes pour chaque fichier: True.
- En-têtes des deux fichiers de barre P4V035: `[['t[s]', 'u[mm]'], ['t[s]', 'u[mm]']]`.
- Série DIC dynamique: 51 trames CSV nommées de 0.003 à 0.241 ms; pas nominal observé entre 0.004 et 0.005 ms.
- Unités explicitement déclarées dans chaque export DIC: `['{"angle": "deg", "length": "mm", "strain": "%", "time": "ms"}']`.
- Temps relatif interne des étapes DIC: `[2.2476, 2.4857]`; il s'agit d'un second repère à documenter avant toute synchronisation avec les signaux de barre.
- En-tête de la courbe quasi statique P6V035: `['t[s]', 'u[mm]', 'F[kN]']`.
- Cellules manquantes détectées dans les tableaux texte: 7070.
- Répartition des valeurs DIC absentes par colonne: `{'displacement_x': {'missing_count': 1414, 'numeric_count': 17755, 'missing_fraction': 0.07376493296468256}, 'displacement_y': {'missing_count': 1414, 'numeric_count': 17755, 'missing_fraction': 0.07376493296468256}, 'epsilon_x': {'missing_count': 1414, 'numeric_count': 17755, 'missing_fraction': 0.07376493296468256}, 'epsilon_xy': {'missing_count': 1414, 'numeric_count': 17755, 'missing_fraction': 0.07376493296468256}, 'epsilon_y': {'missing_count': 1414, 'numeric_count': 17755, 'missing_fraction': 0.07376493296468256}, 'id': {'missing_count': 0, 'numeric_count': 19169, 'missing_fraction': 0.0}, 'x': {'missing_count': 0, 'numeric_count': 19169, 'missing_fraction': 0.0}, 'y': {'missing_count': 0, 'numeric_count': 19169, 'missing_fraction': 0.0}, 'z': {'missing_count': 0, 'numeric_count': 19169, 'missing_fraction': 0.0}}`. Les identifiants et coordonnées restent complets; les cinq champs de déplacement/déformation présentent chacun 1 414 valeurs vides.
- Cellules non numériques dans les lignes de données: 0.

## 2. Résultats de modèles officiels

- Aucun modèle officiel ou calcul physique n'est exécuté dans V9H.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9H

- P4V035 et P6V035 sont traités comme un couple analogue de même catégorie géométrique d'après le classeur V9F; cela ne les transforme pas en matériau WTC ou CF6.
- Le séparateur, la ligne d'en-tête et les colonnes numériques sont détectés par des règles déterministes et restent à confronter à la documentation expérimentale.

## 5. Résultats dérivés

- Les temps DIC tirés des noms sont strictement croissants et uniques: True.
- Tous les fichiers texte sont décodables: True.
- Tous les tableaux texte gardent un nombre de colonnes constant: True.
- La série DIC quasi statique P6V035 reste différée: 875 fichiers, 567110013 octets compressés.

## 6. Contradictions et informations manquantes

- Les libellés présents dans les fichiers doivent être interprétés avec la documentation du dépôt; une unité absente ne sera pas inventée.
- La petite figure géométrique ne fournit toujours pas toutes les dimensions, tolérances et rayons nécessaires à un maillage constitutif fidèle.
- Les données S355 concernent un essai analogue en cisaillement localisé et ne déterminent ni la loi de rupture des aciers WTC M26/C80, ni les matériaux et assemblages du CF6-80A2.
- Aucun ajustement de loi, régularisation de rupture, coupon OpenRadioss, projectile ou impact de façade n'est autorisé par V9H.

## Interprétation

V9H validates exact bounded ingestion and structural format auditing of the selected open S355 analogue payloads. All 55 acquired or cache-verified entries match their central-directory paths, uncompressed sizes and CRC32 values. The dynamic DIC filenames expose 51 ordered time points and the two bar files plus one quasi-static force-displacement comparator are present. This establishes traceable input identity and machine readability only. Units and sign conventions must be taken from explicit headers or repository documentation; no absent definition is inferred. The S355 notched shear data cannot identify WTC M26/C80 tensile fracture or production CF6-80A2 materials. No material fit, regularized failure law, solver, rupture or facade impact is authorized.
