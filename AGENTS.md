# Harnais public de recherche technique WTC 1

## Mission et état

Construire progressivement une simulation exploratoire reproductible de l'impact, des incendies et de la réponse structurelle du WTC 1, jusqu'à un éventuel effondrement ou son arrêt. Ne présupposer aucun résultat et ne présenter aucun sous-modèle comme une expertise exhaustive.

Lire dans l'ordre ce fichier, `harness/state.json`, la passation dédiée à l'itération courante et sa vérification finale. L'état local fait autorité sur les anciens points de reprise. Au premier instantané public : IMPACT-I02I-A terminée, prochaine IMPACT-I02I-B ; branche thermique V11R → V11S, contrôle froid V11F préservé. V8H et V11H sont historiques.

L'original des instructions locales est conservé dans `publication/AGENTS_original.md`. Il cite des chemins et prérequis privés qui n'existent pas nécessairement dans un clone public. Pour la portée exacte de cette publication, lire README.md et REPRODUCIBILITY.md.

## Sources, historique et écritures

- Sources et archives en lecture seule, y compris `work/official_sources/` si ce dossier est reconstitué. Ne jamais modifier, renommer, déplacer ni supprimer un document source.
- Conserver toutes les anciennes itérations et les essais rejetés. Écrire une nouvelle configuration et de nouvelles sorties ; ne pas relancer une campagne historique par défaut.
- Écrire les calculs uniquement dans `wtc1_simulation_v8/`, `wtc1_3d_v4/`, `harness/`, `outputs/` ou `tmp/`. Les documents publics à la racine, `tools/`, `.github/` et `publication/` peuvent être actualisés pour maintenir le dépôt public, sans altérer les résultats anciens.
- Aucun PDF, média ou logiciel tiers ne reçoit la licence MIT du projet. Conserver les licences et notices indiquées dans THIRD_PARTY_NOTICES.md. N'ajouter des sources redistribuées qu'après vérification de leur licence applicable.
- Ne commencer une analyse vidéo que pour une question précise.

## Discipline de preuve

Séparer dans chaque rapport : faits observés ou transcrits ; résultats d'un modèle officiel ; affirmations des archives ; hypothèses propres ; résultats dérivés ; contradictions et informations manquantes.

Une fraction de champs synthétiques n'est pas une probabilité de l'événement réel. Une ressemblance visuelle n'identifie pas un mécanisme. Toute hypothèse doit produire des prédictions distinctives confrontées à des données fiables.

## Calculs et contrôles

1. Lire l'état avant une nouvelle itération longue. Donner à chaque itération identifiant, configuration JSON, graines, unités d'origine, conversions, sources et critères pré-déclarés.
2. Vérifier avant et après une modification importante. Dans le poste local complet, utiliser `harness/tools/Test-WtcHarness.ps1`. Pour l'instantané public, utiliser `python tools/verify_public_snapshot.py`, et `--full` après restauration de toutes les archives. Ces contrôles ont des portées distinctes ; ne pas présenter l'intégrité des fichiers comme un contrôle physique.
3. Conserver scripts, version des logiciels, durée, journaux, bilans et rapport. Préférer les résultats sauvegardés vérifiés aux répétitions inutiles.
4. Enregistrer une expérience dans le registre après vérification. Mettre à jour l'état et la passation seulement quand les livrables existent réellement. Actualiser ensuite les manifestes publics avec une trace de la nouvelle publication, sans remplacer l'ancien instantané/release.
5. Ne pas modifier les propriétés d'un matériau endommagé sans traiter son historique et son énergie. Commencer les couplages nouveaux par des cas limités et des références vérifiables.
6. Chercher des sources primaires lorsqu'une donnée précise le nécessite. Énoncer les paramètres heuristiques et les dépendances aux résultats officiels.
7. Annoncer le coût estimé et le livrable avant tout calcul susceptible de durer plusieurs heures.

## Limites obligatoires

La localisation en flexion après fracture complète n'est pas validée. Une température imposée n'est pas un incendie calculé. Des tests numériques réussis ne valident pas à eux seuls l'effondrement réel. Blender reste une visualisation tant que son animation n'est pas liée à des états mécaniques vérifiés.

Les publications, envois, modifications de logiciels et autres écritures externes exigent l'autorisation explicite du propriétaire. L'autorisation de publier le premier instantané GitHub ne vaut pas autorisation de publier des messages sur X ni de promouvoir des résultats scientifiques futurs sans vérification.
