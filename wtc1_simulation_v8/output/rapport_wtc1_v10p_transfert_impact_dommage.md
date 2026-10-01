# WTC 1 — V10P : transfert impact → dommage en trois pistes

Généré le 2026-09-04T07:20:15Z. Aucun solveur, calcul GPU ou lancement Blender n’est effectué.

## Résultat principal

Le transfert impact→dommage est désormais représenté par trois pistes qui ne sont jamais fusionnées :

1. **Contrôle nul** : reprise du scénario sentinelle V10O, utile uniquement pour tester le logiciel.
2. **Référence dépendante du modèle officiel** : cas moins sévère, de base et plus sévère, recopiés sans interpolation. Ces dommages sont des sorties de modèle, pas une observation indépendante du dommage réel.
3. **Dommage physique inconnu** : les bornes cinématiques sont conservées, mais les états de membres, ouvertures, débris et distribution de carburant restent `null`. Cette piste bloque toute libération physique en aval.

## Contrôles obtenus

- Bilans cinématiques scalaires entrants : 3/3 cas reproduits.
- Décomposition de masse/énergie du cas de base : 8 composants, sommes cohérentes avec l’entrée.
- Transcription dommage → V8A : 21/21 couples cas/étage identiques.
- Segments de dommage référencés sur les étages 93–99 : 89 ; dont 57 sévères/lourds à travers les trois cas.
- Cas B final plus sévère : 29 segments, 9 colonnes distinctes.

## Résidus conservés, pas effacés

- Somme des cases carburant : 66080 lb contre 66100 lb annoncées ; résidu 20 lb.
- Somme des cases débris : 195750 lb contre 196000 lb annoncées ; résidu 250 lb.
- Masse non-carburant moins total de débris annoncé : 21500 lb. Ce manque dans le tableau n’est ni supprimé ni interprété comme une destruction de masse.

Les totaux « extérieur de la tour » combinent le rebond côté nord et le passage côté sud. Ils ne constituent donc pas une mesure de masse ayant traversé seule la façade opposée.

## Ce qui reste indéterminé

Aucun bilan complet après impact ne peut être fermé : il manque les vitesses par objet, l’impulsion transmise à la tour, ainsi que les histoires d’énergie élastique, plastique, de rupture, thermique et numérique. Le résultat est donc 0/3 pour la fermeture physique masse–quantité de mouvement–énergie après impact.

## Séparation des preuves

1. **Faits observés dans V10P** : empreintes, sommes, conversions et concordance exacte entre la transcription et la transformation V8A.
2. **Résultats du modèle officiel** : les cartes de dommage et distributions restent explicitement dépendantes de NIST.
3. **Archives locales** : aucune archive source externe au projet n’est lue ; deux PDF officiels locaux sont seulement rehachés.
4. **Hypothèses** : aucune nouvelle carte ou distribution n’est inventée.
5. **Résultats dérivés** : bilans entrants, résidus tabulaires, matrices développées et comparaison V8A.
6. **Inconnues** : dommage physique réel, ouvertures, débris, carburant et bilans complets après impact.

## Décision

La référence officielle peut alimenter des sensibilités portant son étiquette de dépendance ; la piste inconnue doit rester bloquée. Aucun état n’est libéré comme dommage historique validé, et aucune conclusion d’effondrement ou de non-effondrement n’est autorisée.

## Prochaine étape

Build a bounded fire-to-thermal handoff with the same epistemic separation: zero-fire control, cached official-model-dependent fire/temperature envelopes, and UNKNOWN_EVENT_FIRE. Audit fuel-bin rounding, time/temperature units, SFRM uncertainty fields and conservative temporal mapping without running FDS or assigning exact member temperatures.
