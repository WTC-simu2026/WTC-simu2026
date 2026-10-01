# WTC 1 — V10Q : transfert feu → thermique en trois pistes

Généré le 2026-09-04T07:30:16Z. Aucun FDS, solveur thermique, GPU ou Blender n’est lancé.

## Résultat principal

Le transfert feu→thermique conserve trois pistes non fusionnées : contrôle sans feu, référence dépendante du modèle officiel, et incendie réel inconnu. La référence officielle fournit 105 plages de température structurelle aux cinq instants publiés ; elle ne fournit pas, dans les entrées sélectionnées, les histoires de température des gaz, de flux thermique, de convection, ni les températures exactes élément par élément nécessaires à un nouveau calcul thermique.

## Vérifications numériques

- Plages : 105 = 3 familles × 7 étages × 5 instants.
- Conversions °C→K : 210/210 extrémités exactes.
- Ordre min≤max : 105/105.
- Comparaison aux extrêmes du noyau V8A à 100 min : 7/7.
- Contrôles d’identité V8E : 6/6.
- Domaine total transcrit : 23 à 938 °C (296.15 à 1211.15 K).

## Deux alertes quantitatives

La charge combustible est donnée à la fois comme 25 kg/m² et 5 lb/ft². La conversion exacte de 5 lb/ft² vaut 24.412138 kg/m², soit un écart conservé de 0.587862 kg/m² (2.351 %). Les deux valeurs sont donc traitées comme des valeurs sources parallèles arrondies, pas forcées à l’égalité.

Le polynôme du module d’Young sélectionné dans la transcription n’est déclaré valable que jusqu’à 600 °C, tandis que 47/105 maxima de plage dépassent 600 °C. V10Q interdit toute extrapolation silencieuse ; ces points devront être bloqués ou traités comme hypothèses séparées en V10R.

Le résidu de 20 lb entre la somme des cases de carburant et le total publié, identifié en V10P, est conservé. Il n’est attribué à aucun étage.

## SFRM et support spatial

La phrase indiquant que le dommage de protection incendie suit le trajet d’impact est conservée comme contexte de modèle. Elle ne fournit aucune des huit entrées nécessaires : épaisseur, densité, conductivité, chaleur spécifique, émissivité, fraction endommagée, carte spatiale et loi d’adhésion/rupture. Les huit champs restent donc `null`.

Les cinq nœuds temporels 20, 40, 60, 80 et 100 minutes sont convertis exactement en 1200, 2400, 3600, 4800 et 6000 secondes. Aucune interpolation ni extrapolation n’est effectuée, car les maxima eux-mêmes ne sont pas nécessairement monotones.

## Séparation des preuves

1. **Faits observés ici** : empreintes, structure des tableaux, conversions, comptages et comparaisons V8A/V8E.
2. **Résultats du modèle officiel** : les 105 plages et la distribution de carburant restent dépendantes des calculs NIST.
3. **Archives** : aucune archive source externe n’est lue ; trois PDF officiels locaux sont seulement rehachés.
4. **Hypothèses** : les champs spatiaux V8E sont synthétiques ; aucune valeur SFRM ou température de membre n’est ajoutée.
5. **Résultats dérivés** : conversions SI, écart de double unité, domaine thermique et dépassements de validité.
6. **Inconnues** : feu réel, ouvertures, ventilation, flux, SFRM et températures élémentaires.

## Décision

La piste officielle peut alimenter uniquement une sensibilité portant ses étiquettes de dépendance et de champ synthétique. La piste physique reste bloquée. Zéro état thermique physique est libéré en aval et aucune conclusion d’effondrement ou de non-effondrement n’est autorisée.

## Prochaine étape

Build a three-track thermal-to-initiation preprocessor. Preserve the zero control, evaluate only labelled cached official-dependent/synthetic temperature envelopes through the already documented reduced laws inside their validity domains, and keep the physical branch unknown. Quantify every >600 C modulus-law exceedance, forbid silent extrapolation, join with the failed cold gate as INDETERMINATE, and run no structural solver.
