# WTC 1 — V9G, audit sélectif de l'index ZIP S355

## Conclusion courte

Le serveur accepte les lectures partielles. V9G a transféré 366686 octets, soit 0.038397 % du ZIP déclaré.

Téléchargement complet du ZIP: **non**. Extraction de signaux: **non**. Solveur ou impact: **non**.

## 1. Faits directement observés ou transcrits

- `Fig1.jpg` mesure 59578 octets et correspond au MD5 Zenodo `f82e31db6ab9799b18c76fd05d57cece`.
- La figure indique des dimensions globales 17 × 10 × 12,2 mm, une séparation verticale cotée 2 mm et un décalage de géométrie `x = 0,35 mm`.
- Ces cotes ne constituent pas encore une définition géométrique complète: rayons, profondeurs de toutes les entailles et tolérances ne sont pas tous spécifiés dans la petite figure.
- Statut de la requête partielle initiale: 206.
- Statut de la requête du répertoire central: 206.
- Octets réellement lus: 366686 sous un plafond de 20971520.

## 2. Résultats de modèles officiels

- Aucun modèle officiel ou calcul physique n'est exécuté dans V9G.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9G

- Une correspondance de chemin contenant exactement `P4V035` ou `P6V035` identifie seulement un fichier candidat; elle ne valide ni ses unités ni sa qualité.
- La classification DIC, force-déplacement ou signal de barre est dérivée du nom de chemin et devra être confirmée par le contenu et la documentation avant toute réduction.

## 5. Résultats dérivés

- Répertoire central accessible: True.
- Entrées ZIP annoncées/parsées: 1931 / 1931.
- Fichiers P4V035: 60.
- Fichiers P6V035: 881.
- Une prochaine acquisition sélective peut être pré-déclarée: True.
- Sélection minimale proposée pour V9H: 55 fichier(s), 563657 octets compressés.
- La série DIC quasi-statique P6V035 reste différée: 875 fichier(s), 567110013 octets compressés.
- Un ZIP local fourni par Jeremy est nécessaire: False.

## 6. Contradictions et informations manquantes

- Les fichiers de mesure n'ont pas été extraits; leurs unités, fréquences d'échantillonnage, synchronisation et qualité restent inconnues.
- La géométrie de la petite figure reste incomplète pour un maillage constitutif fidèle.
- Le jeu S355 reste un analogue en cisaillement et ne fournit aucune propriété WTC ou CF6 de production.

## Entrées candidates exactes

### P4V035 — 60 fichier(s), 1959880 octets compressés
- Famille `DIC`: 53 fichier(s), 559221 octets compressés.
- Famille `EBSD`: 5 fichier(s), 1393898 octets compressés.
- Famille `bar_strain_or_bar_displacement_boundary_condition`: 2 fichier(s), 6761 octets compressés.
- Entrée mécanique exacte: `FurtherMeasurements/BarDisplBCs/BC_Inc_P4V035.txt` — compressé 3361 octets; décompressé 10211 octets; CRC32 `7140bb75`; famille(s): bar_strain_or_bar_displacement_boundary_condition.
- Entrée mécanique exacte: `FurtherMeasurements/BarDisplBCs/BC_Trans_P4V035.txt` — compressé 3400 octets; décompressé 10211 octets; CRC32 `517f5d1e`; famille(s): bar_strain_or_bar_displacement_boundary_condition.
- Série DIC: 53 fichier(s), 559221 octets compressés; la liste exacte reste dans le manifeste machine.
### P6V035 — 881 fichier(s), 568712305 octets compressés
- Famille `DIC`: 875 fichier(s), 567110013 octets compressés.
- Famille `EBSD`: 5 fichier(s), 1594812 octets compressés.
- Famille `force_displacement`: 1 fichier(s), 7480 octets compressés.
- Entrée mécanique exacte: `FurtherMeasurements/Fu_curves/P6V035.csv` — compressé 7480 octets; décompressé 27070 octets; CRC32 `14ec40a4`; famille(s): force_displacement.
- Série DIC: 875 fichier(s), 567110013 octets compressés; la liste exacte reste dans le manifeste machine.

## Interprétation

V9G validates a bounded remote ZIP-index audit only. Zenodo honored HTTP Range requests; 366686 bytes were read and the central directory exposes 60 P4V035 plus 881 P6V035 file entries. Their exact paths, sizes and CRC32 values can now support a separately predeclared selective-download iteration. The 955 MB ZIP and all measurement payloads remain undownloaded. Fig1 confirms several millimetre-scale dimensions but is incomplete for a constitutive mesh. No material law, WTC or CF6 property, solver, rupture or facade impact is authorized.
