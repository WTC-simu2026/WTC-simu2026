# WTC 1 — V9I, cohérence descriptive des mesures analogues S355

## Conclusion courte

V9I valide une réduction descriptive sans interpolation des 55 fichiers V9H. Les deux axes de temps DIC diffèrent d'un décalage moyen de 2.245000 ms, avec une dispersion de 0.001000 ms, compatible avec la tolérance de résolution pré-déclarée. Cela démontre une relation numérique stable, pas une synchronisation physique absolue.

Les données peuvent désormais servir de benchmark analogique de mesure et de cinématique. Elles ne suffisent toujours pas à identifier une loi de contrainte-déformation ou de rupture, ni à valider un impact de façade.

## 1. Faits directement observés ou transcrits

- Le dépôt relie les temps des noms de fichiers DIC à un déclencheur virtuel placé à l'extrémité gauche d'une barre incidente raccourcie à 300 mm.
- `BC_Inc` et `BC_Trans` sont des déplacements de bord calculés depuis les jauges de déformation, en référence à l'équation 12, avec une vitesse acoustique de 4 639 m/s et un facteur de correction.
- La valeur numérique du facteur de correction et le texte intégral de l'équation 12 n'ont pas été acquis.
- La courbe quasi statique utilise le déplacement relatif du spécimen évalué par DIC.
- L'image de coordonnées montre `y` vers le haut, `z` vers la droite et l'onde incidente vers la gauche. Les CSV utilisent toutefois `x,y,z`, avec `z=0`; la correspondance entre le `x` CSV et le `z` affiché reste non résolue.

## 2. Résultats de modèles officiels

- Aucun modèle officiel ni solveur physique n'est exécuté dans V9I.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9I

- L'intervalle descriptif au-dessus du seuil arbitraire pré-déclaré de 5 % du déplacement absolu maximal est mesuré uniquement dans la fenêtre enregistrée. Comme les deux signaux dépassent encore ce seuil à la dernière valeur, cet intervalle ne constitue pas une durée complète d'impulsion.
- Les quantiles utilisent une interpolation linéaire à l'indice `(n-1)p`.
- Les valeurs DIC vides sont exclues uniquement du calcul de leur propre champ; elles ne sont ni nulles ni interpolées.
- Le chevauchement numérique des temps de barre et DIC n'est pas traité comme une preuve de synchronisation.

## 5. Résultats dérivés

- Barre incidente: pic absolu observé 0.542379605 mm à 0.2 ms; étendue temporelle entre la première et la dernière valeur au-dessus du seuil 5 %: 0.172 ms, tronquée par la fin de l'enregistrement.
- Barre transmise: pic absolu observé 0.00273380166 mm à 0.199 ms; étendue temporelle entre la première et la dernière valeur au-dessus du seuil 5 %: 0.188 ms, tronquée par la fin de l'enregistrement.
- Fenêtre numérique commune barre/DIC: 0.003 à 0.2 ms, soit 0.197 ms et 42 trames DIC.
- DIC: 51 trames, 19169 lignes, 7070 cellules de mesure vides conservées sans imputation.
- Coordonnées CSV: `x=[-1.6872, 1.6906]`, `y=[-1.3996, 1.4034]`, `z=[0.0, 0.0]` mm.
- Quasi statique: force maximale 19.021234 kN à 0.09825 mm; travail trapézoïdal signé le long du chemin enregistré 1.16984069 J.
- Le déplacement quasi statique contient 267 incréments négatifs; le travail est donc un intégral de chemin enregistré, pas une énergie de rupture.

## 6. Contradictions et informations manquantes

- Le repère dessiné `y-z` et les colonnes CSV `x-y` ne sont pas explicitement mis en correspondance par la documentation acquise.
- Le facteur de correction des déplacements de bord n'est pas chiffré dans la métadonnée locale et l'équation 12 complète n'est pas reproduite.
- L'alignement absolu entre les temps de barre et les temps DIC n'est pas démontré, malgré leur chevauchement et le décalage interne stable des deux horloges DIC.
- La géométrie reste incomplète et aucun effort dynamique n'est fourni avec `BC_Inc`/`BC_Trans`; aucune contrainte, courbe matériau, énergie de rupture ou longueur de régularisation n'est donc identifiée.
- Le S355 à éprouvette entaillée reste un analogue et ne remplace ni les aciers WTC M26/C80 ni les matériaux/assemblages du CF6-80A2.

## Interprétation

V9I validates a no-imputation descriptive measurement benchmark for the selected S355 analogue pair. The cached payload identities remain exact; source metadata documents the virtual DIC trigger, processed bar-displacement boundary conditions and quasi-static relative displacement. The two DIC time axes have a stable 2.245000 ms mean offset within the predeclared rounding tolerance, but absolute bar/DIC synchronization is not asserted. All 7070 DIC blanks remain missing. The quasi-static force-displacement integral is reported only along its recorded path. Because equation 12, its correction-factor value, complete specimen geometry, dynamic force and the coordinate-axis mapping remain incomplete, V9I does not identify stress, constitutive response, fracture energy or regularization length. S355 remains an analogue and no WTC, CF6, rupture or facade-impact solver gate is opened.
