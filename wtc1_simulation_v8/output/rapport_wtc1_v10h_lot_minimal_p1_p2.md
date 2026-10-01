# WTC 1 — V10H — lot minimal P1/P2

## Résultat

**PASS** pour la pré-déclaration hors ligne V10H. L'optimisation exacte couvre nominalement les **16** exigences atteignables par P1/P2 avec **4 documents**, puis conserve T02 sur un cinquième document Book 9 séparé. Aucune combinaison de un à trois documents ne couvre ces 16 exigences.

Le lot principal exact est : `WTCI-000016-L, WTCI-000021-L, WTCI-000024-L, WTCI-000014-L`. La piste T02 sélectionne `WTCI-000030-L` avec `WTCI-000031-L` comme repli.

## Faits observés ou transcrits

La matrice V10B contient 53 identifiants : 9 P0, 23 P1 et 21 P2. V10G conserve 22 exigences toutes bloquantes. V10H ne lit que ces matrices et leurs artefacts de validation ; aucun payload ou contenu de page n'est consulté.

## Résultats de modèles officiels

Aucun nouveau résultat de modèle officiel n'est produit. Une couverture documentaire nominale ne valide aucun résultat officiel ni mécanisme physique.

## Affirmations d'archives

Les titres, numéros de livres, résumés de contenu et plages de dessins restent des affirmations du registre d'archive. Ils ne prouvent ni l'applicabilité WTC 1/étages 93–99, ni la révision gouvernante, ni le statut as-built.

## Hypothèses propres au modèle

Le problème de couverture suppose seulement qu'un document candidat peut contribuer aux exigences auxquelles V10B l'a relié. Les documents d'un même groupe ne sont pas déclarés équivalents et le document sélectionné n'est pas déclaré suffisant.

## Résultats dérivés

| Ordre | Document | Groupe | Couverture nominale | Gain marginal |
|---:|---|---|---|---|
| 1 | WTCI-000024-L | OFFICE_FLOOR_BOOK7 | N02|N03|E03|O01|O02|O03|O04|O05|T01|M01 | N02|N03|E03|O01|O02|O03|O04|O05|T01|M01 |
| 2 | WTCI-000014-L | PERIMETER_PANEL_BOOK4 | N02|O05|P01|P02|P03|T01|M01 | P01|P02|P03 |
| 3 | WTCI-000016-L | CORE_BEAM_BOOK5 | N02|E02|E03|E04|M01 | E02|E04 |
| 4 | WTCI-000021-L | CONNECTION_BOOK6 | N03|C01|O04|O05|T01 | C01 |
| 5 | WTCI-000030-L | HAT_TRUSS_BOOK9 | T02 | T02 |

Le gain marginal sert à ordonner la recherche au sein du lot optimal. Il ne représente ni une probabilité de succès ni une quantité physique.

## Pistes séparées et informations manquantes

- N01 et E01 restent P0 seulement, liés à `WTCI-000013-L` ; aucun nouveau candidat P1/P2 ne les couvre.
- Pour `WTCI-000024-L`, la fin de plage `2 - C/2` est une anomalie du registre conservée telle quelle, non une localisation Book 7 validée.
- D01 exige des données de dommage propres à l'événement, non des plans de conception.
- T02 demeure une piste Book 9 séparée.
- B01 exige un modèle numérique de conditions aux limites.
- S01 exige des données quantitatives distinctives ; V9U reste hypothétique et sans crédit mécanique.

## Portes maintenues

Zéro exigence est fermée et les 22 restent bloquantes. V10H n'attribue aucune coordonnée, section, propriété de matériau, masse, rigidité, résistance, loi de connexion, dommage ou crédit de chemin de charge. Aucun réseau, contact externe, accès à l'archive source ou à `work/official_sources/`, solveur, continuation thermique ou lancement Blender n'a eu lieu. Le fichier Blender maître reste inchangé.

## Suite conditionnelle

V10I pourra vérifier uniquement les chemins locaux explicitement fournis par l'utilisateur pour les cinq identifiants pré-déclarés. Sans chemin fourni, aucune recherche de répertoire ne sera lancée.
