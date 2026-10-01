# V9Q — Audit sourcé des trois cages d'escalier du WTC 1

## Conclusion

V9Q est **PASS** comme audit documentaire reproductible. Les trois cages doivent être conservées dans le futur modèle pour la cohérence géométrique du noyau : vides de plancher, obstacles non structuraux, interfaces avec le plancher, masse globale et topologie des dommages. En revanche, les sources auditées ne qualifient ni leur géométrie métrique complète, ni leurs assemblages, ni leur masse discrète, ni une contribution porteuse. Aucun crédit de rigidité, résistance ou chemin de charge n'est donc attribué.

## 1. Faits directement observés ou transcrits

- Le WTC 1 comportait trois cages centrales, avec les correspondances 1/A/FS-F3, 2/C/FS-F2 et 3/B/FS-F1.
- A et C avaient une largeur libre publiée de 44 in (1117.6 mm) ; B, 56 in (1422.4 mm).
- A et C reliaient le 110e étage à la mezzanine surélevée ; B reliait le 107e étage au niveau B6.
- Deux plages de déviation sont rapportées pour A et C : étages 42–48 et 76–82. Leur décalage métrique exact n'est pas donné.
- L'enveloppe générique des gaines/cages était un assemblage non structural en panneaux de gypse moulé, maintenus par des profils métalliques aux dalles, avec parements en plaques de gypse.

## 2. Résultats et choix du modèle officiel

- NIST a classé ces parois comme non structurales et n'a pas effectué d'essais matériaux propres aux matériaux non structuraux pour son modèle d'impact.
- Le modèle NIST a utilisé une loi approchée à 500 psi et 60 % de déformation de rupture ; ce choix de calcul n'est pas une validation du composant réel.
- Dans le modèle global WTC 1, les cloisons du noyau n'étaient explicites qu'aux étages 94 à 97. La base des parois était fusionnée à la dalle ; leur sommet n'était pas contraint.
- Le passage audité indique que les dommages ou débris du cas de base rendaient les trois cages apparemment impraticables aux étages 94 à 96. Les témoignages transcrits pour l'étage 92 et la synthèse générale NIST restent des classes de preuve distinctes.

## 3. Source gouvernementale indexée, distincte d'un plan de structure

Le texte mis en cache du rapport de la Commission du 11-Septembre fournit la continuité verticale et les plages de déviation, en renvoyant à une réponse de la Port Authority. Il ne constitue ni un plan métrique d'exécution ni une validation structurale NIST. Le PDF externe mentionné par l'index n'a pas été ouvert.

## 4. Exigence utilisateur

Le futur modèle de tour doit représenter explicitement trois cages d'escalier. V9Q traduit cette exigence en champs vérifiables et en garde-fous, sans inventer les données manquantes.

## 5. Résultats dérivés

- 330 lignes ont été produites : 110 étages × 3 cages.
- Couverture des sept champs nécessaires : 0 complet, 6 partiels, 1 manquant.
- La position relative des trois cages aux étages 93–97 est seulement qualitative, dérivée de la figure 9-124 avec le nord en haut : 1/A au nord-est, 2/C au nord-ouest, 3/B au sud-centre.
- Les conversions d'unités sont calculées séparément ; les charges globales du noyau publiées par NIST ne sont pas converties en masses discrètes de cages.

## 6. Hypothèses propres au modèle

Aucune géométrie métrique ou propriété mécanique nouvelle n'est admise en V9Q. Une future esquisse qualitative pourra représenter les trois vides/obstacles, mais toute coordonnée au-delà de la topologie relative documentée restera une hypothèse affichée comme telle.

## 7. Contradictions, limites et informations manquantes

- coordonnées et orientations métriques par étage ;
- géométrie exacte des deux transferts de A et C ;
- volées, paliers, limons, marches et attaches ;
- connexions réelles aux dalles et à l'ossature du noyau ;
- masses discrètes et détails de construction par étage ;
- dommages composant par composant sur toute la zone d'impact.

La masse globale du noyau déjà intégrée par NIST impose un contrôle de double comptage avant l'ajout futur d'éléments discrets.

## 8. Contrôles de reproductibilité et périmètre

- Régressions V9P : **PASS**.
- Empreintes des sources mises en cache : **PASS**.
- Ancrages de pages PDF : **PASS** (12 contrôles).
- Rapport gouvernemental indexé : **PASS**.
- Archive source externe : non ouverte et non rescannée.
- Réseau, solveur, Blender et calcul physique global : non utilisés.

Blender reste un outil de visualisation. Il ne constitue pas une validation physique de l'impact, des cages d'escalier ou du comportement global de la tour.

## 9. Décision et suite

Le seul niveau autorisé est une couche topologique qualitative à trois cages. Tous les crédits de masse discrète, rigidité, résistance, connexion porteuse, dommage quantifié, solveur global et validation physique restent fermés.

**V9R :** Preserve V8U through V9Q and perform a bounded primary-plan gap closure for the three WTC 1 stairways. Search first for NIST NCSTAR 1-7 and traceable PANYNJ or architectural drawings that expose metric floor plans, the exact 42-48 and 76-82 transfer geometry, stair flights, landings, stringers and connections. Digitize only source-visible geometry with scale or fixed landmarks. Keep all mass, stiffness, strength, damage and solver gates closed if the primary geometry remains incomplete.
