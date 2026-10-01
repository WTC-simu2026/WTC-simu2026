# WTC 1 — V10R : préprocesseur thermique → initiation

Généré le 2026-09-04T07:46:12Z. Aucun solveur structurel ou thermique, GPU ou Blender n’est lancé.

## Résultat principal

Le préprocesseur conserve trois pistes non fusionnées. Il transforme les plages thermiques dépendantes du modèle officiel en facteurs mécaniques réduits uniquement là où le domaine sélectionné est déclaré exploitable. Il ne crée ni température de membre, ni capacité de membre, ni état d’initiation physique.

Sur 105 plages, 58 ont leurs deux extrémités dans le domaine conservateur 0–600 °C. Les 47 autres ne conservent que leur extrémité froide calculable ; leur extrémité chaude et l’intervalle mécanique complet restent `null`. Aucun des deux prolongements V8B au-delà de 600 °C n’est invoqué.

## Domaine et comptages

- Extrémités évaluées dans le domaine : 163/210.
- Extrémités bloquées : 47/210.
- Plages bloquées par famille : noyau 19, périmètre 8, treillis 20.
- Plages bloquées aux temps 20/40/60/80/100 min : 7/9/10/10/11.
- Le rapport de limite d’élasticité à 20 °C issu de l’équation vaut 0,982493, pas exactement 1 ; une seconde colonne normalisée à la valeur de 20 °C évite de confondre les deux conventions.
- Les deux lois sont décroissantes sur les 600 intervalles de la grille 0–600 °C.

## Audit rétrospectif V8E

V8E contient 70 lignes déterministes : 20 restent entièrement dans 0–600 °C et 50 utilisent un prolongement. Les 25/25 paires hors domaine donnent des résultats différents selon le prolongement choisi.

Les 40 agrégats de champs lisses atteignent au moins une température supérieure à 600 °C. Parmi leurs 20 paires, 11 divergent et 9 coïncident. Une coïncidence d’agrégat ne valide pas le prolongement ; toutes ces fractions restent des sensibilités de champs synthétiques, jamais des probabilités de l’événement réel.

## Jonction avec le gate froid

Le gate V8J reste `NOT_VALIDATED_MISSING_FORCE_DISPLACEMENT_PATH` : un composant chargé demeure déconnecté et la topologie survivante, la raideur, la ductilité et l’affectation des assemblages ne sont pas établies. Même les 58 plages arithmétiquement complètes ne peuvent donc pas produire une initiation physique. La jonction correcte est `INDETERMINATE_BLOCKED`, et non « effondrement » ou « non-effondrement ».

## Séparation des preuves

1. **Faits observés ici** : empreintes, comptes, domaine déclaré, valeurs nulles et divergence des paires V8E.
2. **Résultats du modèle officiel** : les plages thermiques restent des sorties NIST dépendantes de leurs entrées.
3. **Archives** : aucune archive externe n’est lue ; deux PDF officiels locaux sont seulement rehachés.
4. **Hypothèses du modèle** : le domaine conjoint 0–600 °C est une restriction conservatrice ; les champs V8E sont synthétiques.
5. **Résultats dérivés** : facteurs de réduction, contrôles de monotonie et audit des prolongements.
6. **Inconnues** : températures, sections, charges, assemblages, défauts et critères de rupture membre par membre.

## Décision

Le paquet logiciel V10R est valide comme préprocesseur et comme audit de domaine. La piste physique reste fermée : zéro état d’initiation est libéré, et aucune conclusion historique d’effondrement ou de non-effondrement n’est autorisée.

## Prochaine étape

Construire un contrat d’état à trois pistes pour le transfert initiation → propagation/arrêt. Conserver le contrôle logiciel à entrée nulle, transmettre la piste dépendante du modèle officiel uniquement comme INDETERMINATE_BLOCKED et garder la piste physique inconnue. Énumérer les entrées minimales et les contrôles de conservation nécessaires à la propagation et à l’arrêt, sans inventer de valeur, exécuter de solveur, lancer Blender ni conclure historiquement à l’effondrement ou au non-effondrement.
