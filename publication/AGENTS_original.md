# Harnais de recherche technique WTC 1

## Mission

Poursuivre une investigation technique reproductible de l'impact, de l'incendie, de l'initiation et de la propagation de l'effondrement du WTC 1. Le but est de tester des mécanismes et des plages de paramètres, pas de défendre à l'avance une conclusion officielle ou alternative.

## Limites des sources

- Traiter `C:\Users\jeuxpc\Desktop\ARCH\11 septembre 2001` comme une archive source en lecture seule.
- Traiter `work/official_sources/` comme une copie locale de documents sources en lecture seule.
- Ne jamais renommer, déplacer, supprimer ou modifier une archive, une vidéo, une photographie ou un PDF source.
- Écrire les calculs et livrables uniquement dans `wtc1_simulation_v8/`, `wtc1_3d_v4/`, `harness/`, `outputs/` ou `tmp/`.
- Ne commencer l'analyse des vidéos que lorsqu'une question précise l'exige ou qu'un document technique y renvoie.

## Discipline de preuve

Séparer explicitement dans chaque rapport :

1. faits directement observés ou transcrits ;
2. résultats d'un modèle officiel ;
3. affirmations provenant des archives locales ;
4. hypothèses propres au modèle ;
5. résultats dérivés ;
6. contradictions et informations manquantes.

Une fraction issue de champs synthétiques n'est jamais une probabilité de l'événement réel. Une ressemblance visuelle n'est pas une identification de mécanisme. Une hypothèse d'explosif, de thermite ou de démolition doit rester une hypothèse tant qu'un ensemble de prédictions distinctives n'est pas confirmé par des données fiables.

## Processus de simulation

1. Lire `harness/state.json` avant une nouvelle itération longue.
2. Donner à chaque nouvelle itération un identifiant, une configuration, des graines aléatoires et une liste de sources.
3. Conserver les unités d'origine et les conversions dans les données d'entrée.
4. Ne jamais écraser une ancienne itération ; créer V8H, V8I, etc.
5. Exécuter `harness/tools/Test-WtcHarness.ps1` avant et après une modification importante.
6. Ajouter une ligne dans `harness/experiments/registry.jsonl` après une exécution validée.
7. Mettre à jour `harness/state.json` uniquement lorsque le rapport et les sorties correspondantes existent réellement.
8. Comparer séparément le calcul réduit, le solveur structurel et l'animation Blender. Blender est une visualisation tant que sa dynamique n'est pas liée à un solveur validé.

## Reproductibilité

- Conserver les paramètres numériques dans des fichiers JSON plutôt que dans le texte de conversation.
- Conserver les scripts qui ont produit chaque résultat.
- Journaliser le temps d'exécution, le logiciel, la version, les entrées et les sorties importantes.
- Préférer un calcul mis en cache et vérifié à une répétition inutile.
- Signaler les paramètres encore heuristiques et les analyses qui dépendent d'une sortie NIST, donc non indépendantes.

## Sécurité et autorisations

- Les inspections de sources sont en lecture seule.
- Les écritures externes, publications, envois ou modifications de logiciels exigent une demande explicite de Jeremy.
- Ne pas lancer de calcul GPU ou solveur susceptible de durer plusieurs heures sans annoncer l'estimation et le livrable attendu.
- Ne pas présenter l'absence de contradiction dans un sous-modèle comme la preuve de toute une chaîne causale.

## Point de reprise

La V8G est terminée. La prochaine étape est V8H : remplacer la redistribution heuristique entre colonnes du noyau par des capacités mécaniques de poutres et d'assemblages, puis seulement transférer les états validés vers Blender.
