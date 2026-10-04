# WTC1 — IMPACT-I02I-J : précision des sorties sauvegardées

## 1. Faits directement observés ou transcrits

Analyse de quatre T01 et de leurs CSV de I, sans moteur, starter ou convertisseur relancé. Lecture indépendante : 1203 lignes × 41 colonnes = **49323 valeurs**. Toutes reproduisent exactement les jetons .6e de l'export sauvegardé, y compris les temps, forces, vitesses, impulsions et énergies. Deux lecteurs propres distincts (blocs contrôlés avec struct ; accès NumPy à pas constant après validation) donnent les mêmes valeurs. Les trois sorties IE globale, SPRING ENERGY et IE de la liaison sont bit pour bit identiques sur chaque ligne.

Le diagnostic brut J passe 53/56 critères ; les trois échecs concernent uniquement la condition exacte temps_final_binaire≤temps_demandé, sans marge d'arrondi. Ils restent échoués. Six contrôles de lecteur passent, dont rejet de marqueur corrompu, version inconnue, code variable incorrect, troncature et ajout d'octet, plus cinq états élastiques synthétiques pour le calcul exact d'intervalle. Un diagnostic de temps **distinct**, pré-déclaré après ces échecs, passe 8/8 contrôles d'intervalle. Il ne remplace aucun critère brut.

La [documentation /TFILE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tfile_engine_r.htm) associe le type 4 au format binaire IEEE32 ; les cartes I demandent /TFILE/4. L'accès aux sources officielles du convertisseur a renvoyé 404 via API et chemins raw testés, après les mêmes difficultés historiques. Les liens présents dans les résultats de recherche ne constituent pas une lecture du code. Les six essais d'accès sont consignés ; aucun algorithme interne n'est inféré de ce code indisponible.

## 2. Résultats d'un modèle officiel

Aucun nouveau résultat NIST ou modèle historique. Les pages Altair documentent les champs demandés : [IE/FY/OFF de liaison](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) et [sorties nodales](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm). L'égalité constatée dans ces quatre fichiers ne valide ni le logiciel entier ni un phénomène réel. La documentation continue d'appeler REACX/REACY une force alors que les valeurs sauvegardées se comportent comme une impulsion cumulative ; le centrage exact TH et le chemin interne du convertisseur ne sont pas établis.

## 3. Affirmations des archives locales

Aucune nouvelle assertion d'archive ni vidéo inspectée. 1967 fichiers antérieurs vérifiés depuis les inventaires sauvegardés ; aucun rescan d'archive ou ancien solveur relancé. Les quatre échecs IE−U de I restent inchangés. Tous les états E/F/G/H/I et V11F/V11R/V11S sont conservés. H+I publiée reste la base publique ; J seule constitue une itération sur deux avant prochaine publication J+K.

## 4. Hypothèses propres au diagnostic, propriétés et unités

Aucune propriété physique ajoutée. Dans le témoin I : masse mobile 0,1 g, Kn=56000 N/mm, Kt=21500 N/mm, force normale maximale hypothétique 495 N, aire 1 mm², Gf=30 N/mm hypothétique. X/Z et rotations bloqués, pas de cisaillement actif ; U=Fy²/(2Kn). Les sorties d'énergie sont en N mm=mJ, converties en J par ×0,001 ; temps ms, force N, impulsion N ms. IE−U est nommé travail numérique non récupéré, sans assimilation à une chaleur ou fissuration physique.

Schéma **observé localement**, limité à ces quatre fichiers : version entière 3040, entiers et flottants en big-endian, marqueur entier 32 bits donnant la longueur de chaque bloc puis répété après le contenu. Les 16 blocs d'en-tête occupent 916 octets ; titres de calcul, groupes SEAM_HISTORY/NODES, IDs de nœuds 1/2 et codes variables sont contrôlés. À chaque ligne : quatre blocs de 4/88/24/48 octets, soit temps, 22 champs globaux, six champs de liaison et 12 champs nodaux. Toute autre signature, octet final résiduel ou bloc incorrect est refusé. Certains entiers annexes d'en-tête restent opaques, simplement contrôlés ; aucune généralité du lecteur ou validation de schéma officiel n'est revendiquée. Les noms de variables sont reliés aux cartes /TH originales et confrontés à l'export déjà sauvegardé.

Diagnostic de représentation pré-déclaré avant analyse : hypothèse d'arrondi au plus proche binaire32. Pour un flottant x sauvegardé, cellule fermée [(prev32(x)+x)/2,(x+next32(x))/2] ; les deux milieux sont calculés exactement comme fractions dyadiques. Pour F dans [fl,fh], calculer les extrema exacts de F², incluant zéro si l'intervalle change de signe ; puis D_min=0,001(IE_min−U_max), D_max=0,001(IE_max−U_min). Kn et la conversion 0,001 sont des rationnels exacts, sans tolérance ajustée. Pour le CSV, ajouter un demi-pas décimal lu dans chaque jeton .6e. Les décisions d'inclusion de zéro utilisent les fractions exactes ; les bornes en CSV sont arrondies vers l'extérieur pour leur affichage. Aucun clipping de D, changement de phase ou correction d'énergie.

L'hypothèse d'arrondi ne révèle pas la vraie valeur interne du moteur. Un intervalle contenant zéro rend le signe non observable à cette précision ; ce n'est pas la preuve de D=0. Les deux nœuds, loi H2 et références I restent ceux d'origine ; aucun restart ou matériau endommagé modifié.

## 5. Résultats dérivés

| Cas I réutilisé | Lignes | Valeurs | Minimum D CSV (J) | Minimum D binaire (J) | Lignes binaires D<0 |
|---|---:|---:|---:|---:|---:|
| NORMAL_ARREST_RETURN_050NS | 241 | 9881 | -1.9406036e-10 | -1.0508632e-10 | 5 |
| NORMAL_ARREST_RETURN_025NS | 480 | 19680 | -3.3157143e-10 | -8.9276881e-11 | 10 |
| NORMAL_SUBPEAK_RETURN_025NS | 161 | 6601 | -3.6647223e-10 | -9.6511927e-11 | 89 |
| NORMAL_SUBPEAK_RETURN_012P5NS | 321 | 13161 | -4.5080143e-10 | -1.2751256e-10 | 163 |

L'export décimal ajoute une perte de précision mesurée directement. Lire le binaire réduit les minima négatifs en amplitude, mais ne les élimine pas. Même le seuil original −1e−10 J resterait dépassé dans deux séries binaires ; cette remarque est descriptive et ne réévalue pas les critères de I. Tous les cas à D binaire négatif dans la branche historiquement élastique admettent zéro dans leur intervalle exact. Toutes les lignes négatives CSV admettent aussi zéro après prise en compte des deux représentations. **Le signe près de zéro est donc indécidable avec ces seules sorties et sous l'hypothèse déclarée.** Les quatre échecs de I sont conservés.

Après décharge de l'arrêt endommagé, IE binaire finale ≈0,0192134418488 J et 0,0192133502960 J, avec force normale/U nulles ; cette énergie positive est largement supérieure à l'incertitude. Les contrôles sous pic ont D binaire final ≈−4,02e−13 J et +2,05e−12 J : toujours rapportés tels quels. Les bilans globaux binaires restent au-dessous de 0,008755 % de E0, sans correction de phase ou physique ; leur seuil 0,5 % passe.

| Cas | Temps final binaire (ms) | Temps demandé (ms) | Différence (ms) | Critère brut J |
|---|---:|---:|---:|---|
| NORMAL_ARREST_RETURN_050NS | 0.012000000104308128 | 0.012 | 1.0430813e-10 | échoue |
| NORMAL_ARREST_RETURN_025NS | 0.01197499968111515 | 0.012 | -2.5000319e-05 | passe |
| NORMAL_SUBPEAK_RETURN_025NS | 0.0040000001899898052 | 0.004 | 1.8998981e-10 | échoue |
| NORMAL_SUBPEAK_RETURN_012P5NS | 0.0040000001899898052 | 0.004 | 1.8998981e-10 | échoue |

Les trois dépassements sont 1,04e−10 ou 1,90e−10 ms. La série arrêt 25 ns se termine une ligne plus tôt, à ≈0,0119749996811 ms, comme son CSV original, sans extrapolation. Le diagnostic supplémentaire teste exactement l'intersection de la cellule binaire du temps final avec [fin−2pas,fin] : les quatre cellules sont compatibles et contiennent aussi leur temps final CSV. L'ordre, le nombre et les valeurs des lignes correspondent entièrement ; aucun octet n'est perdu. Cette compatibilité ne change pas les trois échecs de condition brute.

## 6. Contradictions et informations manquantes

La précision interne et l'arrondi réel du moteur, la source exacte du convertisseur et le schéma binaire officiel ne sont pas établis. J vérifie une lecture propre de quatre fichiers bornés ; son audit brut reste 53/56 et le champ all_declared_raw_checks_pass reste false. Les petits signes IE−U demeurent non résolus ; aucune énergie négative réelle ne peut être identifiée ou exclue par une telle quantification seule.

Conserver les quatre échecs I, les trois critères bruts de fin J, les cinq OFF/FX mixtes F, les huit diagnostics historiques G, les sensibilités et couvertures E, la définition REACX/REACY et le centrage TH. Les conventions NASA restent non identifiées ; Gf30 hypothétique et Gf15/60 différés. J ne ferme pas le réservoir tangentiel perdu lors d'une désactivation complète.

K proposera quatre états neufs libres sur X et Y avec Y sous la séparation : contrôle élastique et arrêt normal H2 avec réserve de cisaillement élastique. Dériver d'abord la référence séparable, Ux+Uy+Dy et les deux impulsions initiales, avant cartes, critères puis moteur. C'est un témoin de modes indépendants simultanés, pas un assemblage réel ou une rupture mixte qualifiée. Rien n'est calculé en K ici.

Impact complet Boeing/façade, incendie et effondrement réel non qualifiés. Localisation en flexion après fracture complète non validée ; température imposée ≠ incendie calculé ; Blender visualisation uniquement. V11F/V11R/V11S préservés.

## Reproduction et reprise

Graines 1102018 sans tirage. Pré-déclaration J, source /TFILE en snapshot non redistribué, six accès sources échoués consignés, lecteur, deux audits distincts, CSV binaires à 17 décimales, intervalles rationnels et journaux de contrôle conservés. Analyse principale : 0.285708 s, budget 120 s respecté ; aucun executable scientifique ou convertisseur lancé. Actions : initialize, declare, audit, terminal declare/diagnose, prepare, register. Pré/post-harnais, empreintes et état contrôlés. Vérifier sans solveur avec complete_impact_i02i_output_precision.py verify. Prochaine étape K dans impact_i02i_k_plan_from_j.json ; prochaine publication J+K après K vérifiée, aucun post X.
