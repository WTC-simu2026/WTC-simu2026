# WTC 1 — V10I — réception locale des cinq documents

## Résultat

**PASS** pour la réception locale bornée V10I. Les cinq fichiers fournis correspondent octet pour octet aux tailles, MD5 et SHA-1 des objets marqués `original` dans les métadonnées Archive.org observées avant V10I. Leurs SHA-256 locaux sont enregistrés et cinq copies de travail vérifiées ont été créées dans `wtc1_simulation_v8/input/v10i_structural_sources`.

| Document | Octets | MD5/SHA-1 Archive.org | Pages conteneur | Registre |
|---|---:|---|---:|---:|
| WTCI-000024-L | 9427468 | MATCH | 276 | 276 |
| WTCI-000014-L | 10760417 | MATCH | 300 | 300 |
| WTCI-000016-L | 11095821 | MATCH | 280 | 280 |
| WTCI-000021-L | 7904080 | MATCH | 282 | 282 |
| WTCI-000030-L | 12330703 | MATCH | 298 | 298 |

Discordances éventuelles entre le nombre de pages du conteneur et le registre : **aucune**. Une concordance de nombre de pages ne prouve ni la révision ni l'applicabilité.

## Faits directement observés

Les cinq chemins explicites existent dans `WTC1_HARNESS`. Leur nom, taille, MD5 et SHA-1 correspondent aux métadonnées figées des cinq objets Archive.org originaux. Chaque fichier possède une signature PDF, un marqueur EOF et un arbre de pages lisible. Aucune page n'est lue ou rendue et aucun texte n'est extrait.

## Résultats de modèles officiels

Aucun résultat de modèle officiel n'est produit ou validé dans V10I.

## Affirmations d'archives et de l'utilisateur

Archive.org marque ces cinq objets comme `original` dans ses conteneurs. L'utilisateur les considère authentiques et indique qu'une chaîne complète est facultative. Ces affirmations autorisent ici une réception documentaire bornée, mais ne prouvent pas à elles seules un dépôt officiel NIST, la révision gouvernante ou un état as-built.

## Hypothèses propres au modèle

Les cinq identifiants restent des candidats de recherche issus du lot minimal V10H. Leur contenu n'est pas présumé suffisant et les documents d'un même livre ne sont pas présumés interchangeables.

## Résultats dérivés

L'identité binaire aux objets Archive.org est établie pour 5/5 fichiers et les copies de travail reproduisent exactement les SHA-256 sources. Ce résultat qualifie uniquement le conteneur documentaire local.

## Contradictions et informations manquantes

- La chaîne officielle NIST n'est pas vérifiée ; elle n'est pas exigée pour cette réception bornée.
- Aucune page de titre, révision, index ou dessin n'est encore inspectée.
- L'applicabilité au WTC 1 et aux étages 93–99, la révision gouvernante et le statut as-built restent inconnus.
- L'anomalie de registre `2 - C/2` pour WTCI-000024-L reste non résolue.
- Les 22 exigences demeurent bloquantes.

## Portes physiques

V10I attribue zéro coordonnée, section, matériau, masse, rigidité, résistance, loi de connexion, dommage ou crédit de chemin de charge. Aucun accès réseau n'a lieu pendant V10I, `work/official_sources/` n'est pas lu, et aucun solveur, calcul thermique ou Blender n'est lancé. Les cinq sources de l'archive restent inchangées.

## Prochaine itération

V10J pourra inspecter au maximum cinq pages de front-matter/index par document, soit 25 pages au total, après pré-déclaration immuable des pages exactes et uniquement pour des champs de localisation, de tour, d'étage et de révision.
