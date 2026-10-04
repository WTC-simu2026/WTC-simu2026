# WTC1 — IMPACT-I02I-G : résolution des trajectoires et témoin élastique libre

## 1. Faits directement observés ou transcrits

Six états neufs, 18 exécutables, terminaison normale et aucune alerte starter : 30.114386 s au total, limites 90 s/cas et 600 s/campagne. Pas global sauvegardé plafonné à 100 ou 50 ns, une ligne TH par cycle ; aucune masse ajoutée, aucune extrapolation terminale. Les deux fonctions imposées des cas N1600 comptent 3201 points chacune, celles des cas N3200 6401 points chacune. Le script historique avait 800 subdivisions codées en dur : le nouveau générateur utilise réellement N et contrôle les fonctions sérialisées, sans modifier les anciens scripts.

Les définitions primaires consultées sont [/INIVEL](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inivel_starter_r.htm), [/TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) et la [théorie dynamique Radioss 2017](https://2017.help.altair.com/2017/hwsolvers/theory_dynamic_analysis.pdf). /INIVEL/TRA définit une vitesse initiale sur un groupe de nœuds. La théorie emploie des vitesses à demi-pas. La documentation TH nomme REACX « réaction », avec unité de force, alors que les essais sauvegardés de cette version sont compatibles avec une impulsion cumulative N ms. Le témoin libre compare de nouveau cette colonne à l'intégrale de −FX et à P−P0. Cette contradiction est conservée ; ni le code exact ni le centrage temporel de toutes les sorties 2026 ne sont établis par ces pages. Les copies locales datées et leurs SHA-256 sont dans source_manifest.json ; documents sous copyright exclus de redistribution.

## 2. Résultats d'un modèle officiel

Aucun résultat NIST ni modèle officiel du WTC1 ajouté. La documentation d'un solveur sert à définir les entrées et la référence numérique. Les deux conventions NASA antérieures restent non identifiées ; aucune branche de matériau avion n'est choisie par ces contrôles.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d'archive testée, aucune vidéo relue ni archive rescannée. 1632 fichiers anciens contrôlés à partir des inventaires sauvegardés, dont F et ses prédécesseurs. Les anciens solveurs ne sont pas relancés. Le contrôle froid V11F, V11R et V11S différée restent inchangés.

## 4. Hypothèses propres au modèle, unités et références

Cas imposés : même liaison TYPE8 à deux nœuds coïncidents, aire initiale 1 mm², masse totale 0,2 g (0,1 g/nœud), inertie 0,001 g mm², Kn=56000 N/mm, Kt=21500 N/mm, pic normal hypothétique 495 N, Gf=30 N/mm. δ0=495/56000 mm, δf=60/495 mm ; loi normale H2 et désactivation complète identiques à F. Rupture normale pendant 0–1 ms puis déplacement X 0→0,02 mm pendant 1–2 ms, quintique tabulée à 1600 ou 3200 subdivisions par segment. Historiques neufs, aucune substitution de propriété sur matériau endommagé.

Cas libres : même masse 0,1 g mobile et 0,1 g fixe, X libre, Y/Z et rotations bloqués, Kt=21500 N/mm, liaison linéaire symétrique sans rupture. u0=0, v0=1 mm/ms, aucun déplacement imposé, amortissement nul et aucun travail externe. Référence : ω=√(k/m)=463.680924775 rad/ms, T=2π/ω=0.0135506659245 ms, u=v0 sin(ωt)/ω, v=v0 cos(ωt), F=ku. Amplitude=0.00215665546407 mm, force amplitude=46.3680924775 N. P0=mv0=0,1 N ms, E0=mv0²/2=0,05 N mm=0,00005 J ; bilan brut J1+J2+P0−P et E0+WE−IE−KE. Énergie élastique U=ku²/2 ; période évaluée sur les passages croissants par zéro sans ajuster la phase.

Unités : g, mm, ms, N ; N=g mm/ms², N ms=g mm/ms et N mm=mJ. 0,0001 ms=100 ns ; les huit périodes demandées couvrent 0.108405327396 ms. Dernières lignes à 0,1084 ms, conservées sans extrapolation.

Tous les seuils sont déclarés avant moteur dans le JSON : 1 % en déplacement et momentum global ; 3 % pour vitesse nodale, force et impulsion brute, 0,5 % en énergie et période. Le seuil 3 % repose sur la borne prudente de demi-pas ωh/2≈0,023184 rad plus dispersion sur huit périodes ≈0,004505 rad à 100 ns. Il ne constitue pas une qualification à 1 %. Des diagnostics bruts plus stricts à 1 % sont enregistrés et restent échoués. Pour la tabulation, hypothèse testée de résidu proportionnel à 1/N, ratio à ±10 %. Aucun seuil modifié après exécution, aucun décalage des séries.

## 5. Résultats dérivés

Tous les 162 critères déclarés de cas et 8 critères de comparaison passent. Ils ne ferment pas les échecs stricts de F ni les sensibilités E.

### Trajectoires imposées après désactivation

F N800 : résidu X brut maximal / impulsion de bord maximale = 0,192454154 %. Les nouveaux résultats sont :

| Cas | Résidu brut (%) | Ratio G/F | Ratio 800/N attendu | Écart relatif du ratio (%) |
|---|---:|---:|---:|---:|
| AFTER_N1600_100NS | 0.0962401027 | 0.500067681 | 0.5 | 0.0135361 |
| AFTER_N1600_050NS | 0.0962401027 | 0.500067681 | 0.5 | 0.0135361 |
| AFTER_N3200_100NS | 0.0481333462 | 0.250102921 | 0.25 | 0.0411684 |
| AFTER_N3200_050NS | 0.0481333462 | 0.250102921 | 0.25 | 0.0411684 |

Le résidu diminue quasiment comme 1/N, indépendamment du passage 100→50 ns aux résolutions testées. Cette observation soutient une erreur liée aux points de la trajectoire imposée ; elle ne prouve pas le détail de l'implémentation interne. Les bilans IE finaux restent 0,03 J et les forces X restent nulles après désactivation : aucune réapparition de liaison. Le résidu n'est pas nul, et ces mouvements demeurent imposés.

### Oscillations libres, erreurs brutes normalisées

| Cas | u (%) | vitesse nodale (%) | momentum global (%) | J+P0−P (%) | bilan énergie (%) | période (%) |
|---|---:|---:|---:|---:|---:|---:|
| FREE_ELASTIC_100NS | 0.450436 | 2.304862 | 0.4363151 | 2.319017 | 0.05378572 | 0.008974839 |
| FREE_ELASTIC_050NS | 0.1125658 | 1.15573 | 0.1090825 | 1.159313 | 0.01344906 | 0.002239491 |

Le déplacement et momentum global convergent approximativement en h² ; vitesse nodale et résidu d'impulsion environ en h. E0 est conservée à 0,0537857 % à 100 ns et 0,0134491 % à 50 ns ; WE=0, masse inchangée. IE suit ku²/2 à moins de 0,000065 % de E0. La période analytique est retrouvée à 0,008975 % puis 0,0022395 %. Les colonnes nodales et impulsions dépassent encore 1 % : environ 2,319 % puis 1,159 %, compatible avec un décalage de demi-pas, sans prouver ni corriger son origine. Les huit diagnostics à 1 % échoués (quatre par cas) figurent dans retained_limitations.json. Aucun succès uniforme à 1 % n'est affirmé.

Ces résultats vérifient un oscillateur élastique libre limité aux conditions testées et aux tolérances déclarées. Ils ne qualifient pas l'inertie libre après fracture, la dissipation mixte ni la pénétration d'un avion.

## 6. Contradictions et informations manquantes

Restent ouverts : le phasage exact TH, la désignation REACX force/impulsion, les cinq échecs stricts OFF/FX de F, la conservation numérique du réservoir tangentiel lors de désactivation complète, les échecs d'inertie et angles et les points non couverts de E. Réutiliser son review sauvegardé plutôt que recalculer. Gf30 est une hypothèse, Gf15/60 différés ; convention nominale/vraie NASA non identifiée.

H resserrera d'abord le témoin libre élastique à 25 et 12,5 ns, avec critères bruts à 1 %, puis pourra déclarer un témoin neuf de rupture normale libre seulement si ce contrôle passe et si sa référence analytique travail/impulsion/énergie est vérifiée. Aucun calcul de fracture libre exécuté en G. Impact Boeing/façade complet, feu et effondrement ne sont pas atteints. Localisation en flexion après fracture complète non validée ; température imposée ≠ incendie calculé ; Blender reste une visualisation.

## Reproduction, contrôle et publication

Configuration JSON, graines sans tirage aléatoire, fonctions sérialisées, scripts générateurs et d'audit, journaux, empreintes des exécutables, CSV bruts et comparaisons analytiques sont conservés. Summary : verification_r1/summary.json. Vérification sans moteur : `C:/Python314/python.exe -X utf8 wtc1_simulation_v8/scripts/complete_impact_i02i_table_free.py verify`. Le manifeste épingle les artefacts ; le harnais et les anciens fichiers sont contrôlés avant/après. La vérification d'intégrité ne valide pas la physique du WTC1.

F+G atteint la cadence de deux itérations. Publication autorisée sur WTC-simu2026 ; ancienne release E et ses archives conservées. La cadence reste pending 2/2 jusqu'à vérification du dépôt distant, des archives et des deux CI. Aucun post sur X.
