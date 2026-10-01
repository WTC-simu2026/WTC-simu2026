# WTC 1 - V9J, suffisance documentaire de l'analogue S355

## Conclusion courte

V9J récupère légalement le texte intégral primaire et documente deux éléments jusque-là manquants : l'équation 12 et le facteur correctif numérique `b = 1,02`. Le verdict global reste **INSUFFISANT** : 2 définition(s) sur 5 satisfont entièrement les critères pré-déclarés, 2 restent partielles et 1 reste inconnue.

Aucune reconstruction contrainte-déformation, identification de matériau, loi de rupture ou simulation d'impact n'est donc autorisée.

## 1. Faits directement observés ou transcrits

- Le dépôt institutionnel BAM fournit le PDF primaire de 14 pages, lié au DOI `10.1016/j.ijmecsci.2024.109749`, sous licence CC BY 4.0. Son identité locale est vérifiée par SHA-256.
- À la page 4, l'équation 12 impose le déplacement longitudinal du bord extérieur de la barre incidente comme le produit de `b`, de la vitesse acoustique `c_B` et de l'intégrale temporelle de la déformation longitudinale mesurée `epsilon_zz`.
- La vitesse acoustique publiée est `c_B = 4 639 m/s`. La page 5 précise une intégration par différences centrales et un facteur sans dimension `b = 1,02`, conservé pour toutes les simulations rapportées.
- La publication exprime le déplacement longitudinal en `u_z`; l'image de coordonnées P4V035 affiche `+z` vers la droite, `+y` vers le haut et l'onde incidente vers la gauche.
- La figure 5 publie notamment les dimensions 17, 10, 12,2, 2 et 0,35 mm ainsi qu'un rayon d'entaille moyen de 0,1741 mm. Le texte de cette figure concerne toutefois la géométrie `x = 0`, alors que P4V035/P6V035 est classée `x = 0,35 mm` dans la description du jeu de données.

## 2. Résultats de modèles officiels

- Aucun modèle officiel WTC ni solveur physique n'est exécuté dans V9J.
- Les résultats Abaqus de l'article sont des résultats du modèle publié par ses auteurs pour l'éprouvette S355; V9J ne les reproduit pas et ne les transpose pas au WTC ou au CF6.

## 3. Affirmations provenant des archives locales

- Aucune. L'archive source WTC n'a pas été rescannée.

## 4. Hypothèses propres à V9J

- Le portail documentaire n'est déclaré franchi que si les cinq familles d'informations pré-déclarées sont toutes explicites dans une source primaire localisée par page, équation, figure ou métadonnée.
- Une convention SHPB générique ne peut pas remplacer une définition absente du jeu P4V035/P6V035.

## 5. Résultats dérivés

- Forme mathématique complète de l'équation 12 : **documentée**.
- Valeur et application du facteur correctif : **documentées**, `b = 1,02`.
- Repères et signes barre/spécimen : **partiels**; `u_z`, le sens physique de l'onde et le repère affiché sont documentés, mais la correspondance CSV `x/displacement_x` vers le `z/u_z` physique et le signe séparé de `BC_Trans` ne le sont pas.
- Dimensions nécessaires à une réduction nominale de P4V035 : **partielles**; plusieurs dimensions sont publiées, mais la figure de l'article traite `x = 0` et aucune réduction nominale complète de la variante décalée n'est définie.
- Alignement temporel absolu barre/DIC : **inconnu**; les deux caméras sont synchronisées entre elles et un déclencheur DIC virtuel est décrit, sans relation explicite avec les colonnes temporelles `BC_Inc`/`BC_Trans`.

## 6. Contradictions et informations manquantes

- La publication emploie le repère physique `y-z`, tandis que les CSV exposent `x-y-z` et `displacement_x/displacement_y`; l'équivalence numérique apparente entre CSV `x` et le `z` affiché reste une inférence interdite.
- L'équation 12 est explicitée pour le bord de la barre incidente. La documentation acquise ne donne pas séparément le signe et la convention appliqués au fichier `BC_Trans`.
- La variante publiée dans la figure 5 et la paire de données sélectionnée ne partagent pas la même valeur déclarée de l'offset `x`.
- Le décalage temporel stable mesuré en V9I n'établit toujours pas une synchronisation physique absolue.

## Décision

Le portail de suffisance documentaire V9J échoue de manière informative. L'équation et son facteur sont récupérés, mais la reconstruction contrainte-déformation demeure interdite. Cette conclusion ne porte ni sur les matériaux WTC M26/C80, ni sur le CF6-80A2, ni sur la rupture du projectile, ni sur l'impact de façade réel.
