# WTC 1 — V10O : premier contrôle intégré des interfaces

Généré le 2026-09-02T17:46:19Z en 900 secondes maximales autorisées.

## Résultat

Les neuf interfaces gelées en V10N disposent maintenant d’un contrat typé exécutable. Pour chacune, un enregistrement valide est accepté et une copie où manque un champ obligatoire est rejetée. Deux exécutions indépendantes du contrôle donnent le même condensat canonique.

Le scénario sentinelle traverse la branche impact, se sépare vers incendie et structure froide, rejoint l’initiation, puis atteint la propagation, l’ensemble et la sortie de visualisation. Son résultat terminal est `CONTROL_NO_PROPAGATION`. Ce libellé signifie uniquement qu’une entrée algébrique nulle produit une sortie nulle dans le logiciel. Il ne signifie ni « le WTC1 ne s’effondre pas », ni « l’effondrement est impossible ».

## Vérifications

- Interfaces valides : 9/9.
- Enregistrements invalides correctement rejetés : 9/9.
- Relectures de références en cache : 5/5.
- Contrôles inter-interfaces : 10/10.
- Interfaces physiquement prêtes : 0/9.
- Solveur, GPU, Blender : 0 exécution.

## Ce que les relectures en cache prouvent

- V8S : la masse et la vitesse du cas de base reproduisent exactement son énergie cinétique et sa quantité de mouvement enregistrées.
- V8E : les nombres de champs synthétiques, graines et paramètres sont retrouvés, avec l’interdiction explicite d’y voir des probabilités.
- V8J et V8L : leurs portes froides restent non validées ; V10O ne les transforme pas en résultats physiques.
- V9M : la branche d’impact physique reste fermée, avec zéro déclencheur de réouverture satisfait.

## Séparation des preuves

1. **Faits observés** : empreintes des cinq fichiers en cache, valeurs relues, résultats des tests de contrat.
2. **Résultats officiels dépendants** : aucune donnée NIST n’est promue ici ; les anciennes dépendances gardent leur statut.
3. **Archives** : aucune archive source n’est lue.
4. **Hypothèses** : la température de référence et les zéros sont des sentinelles logicielles, pas des propriétés du WTC1.
5. **Résultats dérivés** : cohérence arithmétique, validation des neuf contrats, déterminisme du parcours.
6. **Inconnues** : dommage réel, incendie, thermique des éléments, état froid, initiation et propagation physiques.

## Portes maintenues fermées

Les 22 exigences mécaniques restent ouvertes. Aucun modèle de dommage n’est qualifié, aucune entrée événementielle FDS/thermique n’est disponible et aucune loi de propagation globale n’est validée. Une sortie 3D éventuelle restera strictement en aval des états libérés et sans rétroaction mécanique.

## Prochaine étape

Instantiate a bounded three-track impact-to-damage handoff using only a zero-input software control, official-model-dependent damage references and an explicit UNKNOWN_PHYSICAL_DAMAGE branch. Verify available mass, energy and momentum ledgers without reopening the unqualified explicit physical solver branch or presenting an official-model damage mask as independent evidence.
