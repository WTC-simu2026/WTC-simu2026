# WTC 1 - V9C : méthode officielle de traitement du ringing

## Résultat

L'exécution de V9C est **validée**. La revalidation scientifique est **FAIL**. Au moins une porte pré-déclarée reste en échec ; aucune éprouvette OpenRadioss n est autorisée ou exécutée.

## 1. Faits directement observés ou transcrits

- NCSTAR 1-3D décrit environ 5 000 points acquis par essai : charge, déplacement, déformation de la zone utile, déformation côté mors et temps.
- Le signal de charge corrigé est obtenu en comparant le signal côté mors à la moyenne du capteur piézoélectrique.
- Quand le ringing empêche une lecture visuelle fiable de `Fy`, NIST ajuste un polynôme d'ordre 3 entre 1 % et 5 % de déformation et l'intersecte avec une droite élastique décalée de 1 %.
- NIST définit `TS` comme la charge maximale divisée par l'aire initiale. V9C conserve donc sans filtrage les maxima V9B.
- Les recherches exactes sur M26-C1B1-RF, C80-A-2-2 et C80-A-2-3 n'ont pas localisé les canaux bruts publics. Le dépôt NIST trouvé pour les aciers WTC concerne les courbes à haute température et vitesses quasi statiques, pas ces essais rapides à température ambiante.

## 2. Résultats d'un modèle officiel

La procédure polynomiale est une méthode officielle NIST de réduction de mesure. Son application ici ne recrée pas les signaux corrigés originaux absents.

## 3. Affirmations provenant des archives locales

Aucune affirmation nouvelle n'est tirée des archives. L'archive source n'a pas été rescannée et les sources officielles sont restées en lecture seule.

## 4. Hypothèses propres au modèle

- Les courbes d'ingénieur V9B sont converties en contrainte et déformation vraies avant l'ajustement.
- Le polynôme est ajusté par moindres carrés non pondérés, avec la coordonnée ramenée à `[-1,1]` pour la stabilité numérique.
- Faute de pente élastique individuelle lisible et de canaux bruts, `E` est testé à 28 000, 29 000 et 30 000 ksi. La valeur centrale est 29 000 ksi et la dispersion doit rester sous 5 %.
- Aucun filtre n'est ajouté à `TS` après observation des résultats.

## 5. Résultats dérivés

- Courbes passant toutes les portes : **7 / 9**.
- Erreur médiane `Fy` : **4.24 %** ; maximum : **22.34 %**.
- Erreur médiane `TS` : **0.98 %** ; maximum : **13.38 %**.
- Courbes en échec : **C80_299, C80_401**.

| Courbe | Vitesse (/s) | Points fit | Fy V9C (ksi) | Fy table | Erreur Fy | TS inchangée (ksi) | Erreur TS | Porte |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| M26_QS | 6.06e-05 | 31 | 62.24 | 61.7-63.2 | 0.00 % | 86.60 | 0.58 % | PASS |
| M26_65 | 65 | 49 | 73.06 | 72.2-72.2 | 1.19 % | 101.31 | 1.41 % | PASS |
| M26_100 | 100 | 49 | 75.34 | 75.9-75.9 | 0.73 % | 100.65 | 0.25 % | PASS |
| M26_260 | 260 | 45 | 79.52 | 75.9-75.9 | 4.76 % | 103.41 | 0.59 % | PASS |
| M26_417 | 417 | 48 | 91.31 | 85.0-85.0 | 7.42 % | 107.58 | 0.83 % | PASS |
| C80_QS | 8.75e-05 | 8 | 35.62 | 37.1-37.1 | 3.99 % | 65.72 | 2.34 % | PASS |
| C80_84 | 84 | 32 | 59.73 | 57.3-57.3 | 4.24 % | 84.16 | 0.98 % | PASS |
| C80_299 | 299 | 31 | 67.14 | 62.5-62.5 | 7.43 % | 90.82 | 13.38 % | FAIL (TS) |
| C80_401 | 401 | 32 | 72.79 | 59.5-59.5 | 22.34 % | 91.08 | 2.22 % | FAIL (Fy) |

## 6. Contradictions, limites et informations manquantes

- Le rapport publie la séquence de réduction mais pas les canaux bruts, les fenêtres temporelles `t1/t2`, le module ajusté de chaque essai ni un budget d'incertitude par éprouvette.
- Une concordance avec `Fy` ne suffirait pas à qualifier la courbe plastique complète ; `TS` et la forme pré-striction doivent également franchir leurs portes.
- Une discordance persistante de `TS` ne peut pas être corrigée par le polynôme de `Fy`, car la procédure officielle définit `TS` séparément à partir du maximum de charge.

## Décision de porte

- Éprouvette OpenRadioss autorisée : **non**.
- Éprouvette exécutée : **non**.
- Rupture, suppression d'éléments et impact façade : **non exécutés**.
- Avion complet, tour globale, thermique et Blender : **portes fermées**.
- Aucun mécanisme explosif ou thermite n'est testé.
