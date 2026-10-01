# WTC 1 — V9F, ingestion contrôlée du jeu ouvert S355

## Conclusion courte

V9F valide l'identité, l'intégrité et l'inventaire du petit classeur S355 ouvert. Il contient 14 essais (12 SHPB et 2 quasi-statiques), mais aucune série temporelle force/déformation n'est intégrée au classeur. Une réduction de signal, un ajustement de loi de matériau et toute simulation restent interdits.

La FOIA est conservée en dernier recours. Aucune demande et aucun contact externe n'ont été effectués.

## 1. Faits directement observés ou transcrits

- Le fichier acquis mesure 11191 octets; son MD5 est `1ebdc1413558998a0d25e184e56705c2` et son SHA-256 est `8f0b1e26b8f4db6a6468a24ec580f103f6ba9ff801e9d20401ee852da0688717`.
- Les taille et empreinte correspondent exactement aux métadonnées Zenodo du record 17591440, publié sous licence cc-by-4.0.
- Le classeur comporte une feuille, `S355_TestOverview`, avec 15 lignes utilisées et 11 colonnes.
- Les géométries déclarées sont: no offset, offset.
- Les essais SHPB couvrent des pressions de 0.60 à 2.50 bar et des vitesses de projectile de 8.0 à 27.7 m/s.
- Les deux essais quasi-statiques déclarent une vitesse de traverse de 1.60e-06 m/s.
- Le classeur annonce 9 jeux DIC, 14 jeux de signaux mécaniques, 2 jeux de microdureté et 2 jeux EBSD dans l'archive complémentaire.
- L'archive `FurtherMeasurements.zip` de 954 989 097 octets n'a pas été téléchargée.

## 2. Résultats de modèles ou publications officielles

- Le rapport FDOT/University of Florida déclare une plage globale de 7×10⁻⁵ à 500 s⁻¹ pour les essais A36.
- L'article primaire compagnon déclare huit vitesses et une plage de 7×10⁻⁵ à 250 s⁻¹ pour A36/A1011.
- V9F conserve cette différence de 250 s⁻¹ comme une divergence de périmètre publiée; elle ne moyenne pas les deux valeurs et ne les transforme pas en propriétés WTC.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9F

- Les marqueurs `x` signifient seulement que le dépôt annonce un fichier complémentaire; ils ne prouvent ni la qualité du signal ni son aptitude à une identification constitutive.
- Le couple P4V035/P6V035 est retenu uniquement parce qu'il partage la géométrie `offset` et annonce DIC, signal mécanique, microdureté et EBSD pour les deux régimes.

## 5. Résultats dérivés

- Tous les contrôles d'ingestion et de provenance passent: True.
- Couple cible pour une prochaine inspection sélective: dynamique `P4V035` et quasi-statique `P6V035`.
- Une inspection distante de l'index ZIP et l'acquisition sélective de ces seuls canaux peuvent être préparées; le téléchargement intégral de 955 Mo reste interdit.
- Réduction de signal autorisée: False.
- Ajustement de loi de matériau autorisé: False.
- Solveur analogue autorisé: False.

## 6. Contradictions et informations manquantes

- Le petit classeur ne contient pas les séries temporelles, les dimensions complètes d'éprouvette ni une définition calculable du taux de déformation.
- La différence 250/500 s⁻¹ entre l'article et le rapport demeure source-spécifique tant que les tables par éprouvette n'ont pas été rapprochées.
- Les essais concernent des éprouvettes S355 entaillées en cisaillement; ils ne valident pas la traction WTC M26/C80.
- Aucune propriété de production du CF6-80A2 ou de la nacelle Boeing 767 n'est apportée.

## Interprétation

V9F validates only a small-file provenance and inventory audit. The immutable 11,191-byte S355 workbook matches the Zenodo checksum and lists 12 SHPB plus 2 quasi-static tests, but it contains availability flags rather than the underlying DIC, bar-strain or force-displacement time series. P4V035 and P6V035 form the most completely documented same-geometry dynamic/quasi-static pair for a future selective archive-index audit. The FDOT report and companion article publish upper ranges of 500 and 250 per second respectively; V9F preserves that source-level discrepancy without fitting or substitution. FOIA remains last resort, the 955 MB archive is not downloaded, and no signal reduction, material identification, solver, rupture or facade impact is authorized.
