# IMPACT-I02B — Liaison séparable : force, historique et énergie

Date : 12 septembre 2026. Configuration : `wtc1_simulation_v8/data/impact_i02b_joint_coupon.json`. Graine 9112001, calcul déterministe, aucun tirage utilisé.

## Résultat et portée

Treize cas OpenRadioss satisfont leurs 231 contrôles numériques élémentaires. L'audit de campagne comporte 17 marques PASS, dont 13 agrégations des cas ; il ne s'agit pas de 248 validations indépendantes. Une liaison uniaxiale équivalente peut désormais plastifier, conserver un glissement permanent, se décharger, se recharger et se séparer sans recréer de force après rupture. L'énergie interne est conservée dans le bilan après suppression de la liaison.

À masse mobile de 100 g, vitesse de 10 m/s et force maximale de 11,392 kN identiques, les hypothèses d'énergie de séparation 1,1392 J et 2,848 J conduisent à la séparation ; l'hypothèse 5,696 J conduit à l'arrêt de l'ouverture puis à un retour partiel pendant la fenêtre calculée. Ce résultat est conditionnel à la loi choisie, pas une prédiction du comportement d'un rivet Boeing réel.

Ce lot vérifie un connecteur, pas encore des plaques rivetées déformables. Le nom de travail « coupon » désigne cette éprouvette numérique élémentaire. Aucune nouvelle simulation avion-façade n'a été lancée. Le contrôle non érodant I02A, les références I01, le contrôle froid V11F et le dernier lot thermique V11R restent inchangés.

## 1. Faits directement observés ou transcrits

Lecture ciblée du document primaire [NIST NCSTAR 1-2B, volume 1](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2bv1.pdf), pages PDF 176–179 ; figure 4-21 vérifiée visuellement page PDF 177, page imprimée 79. Copie locale en lecture seule : `work/official_sources/ncstar1-2bv1.pdf`, SHA-256 `1504c598adcd9e492bc126530b593b2d467b7c01a7324913b221a5cb9e128ab4`.

La figure reproduit une enveloppe expérimentale de rupture de rivets attribuée à Langrand et al. Ses étiquettes indiquent un rivet fraisé 7050 de diamètre 4 mm et des plaques 2024-T351 d'épaisseur 1,6 mm. Le texte utilise 5/32 pouce et 0,063 pouce ; les écarts d'arrondi sont conservés. Lecture approximative des intersections avec les axes : effort normal central 4,45 kN, encadrement de lecture 4,3–4,6 kN ; effort de cisaillement central 2,55 kN, encadrement 2,4–2,7 kN. Ces plages ne sont ni des intervalles statistiques ni des valeurs admissibles Boeing.

Le document consulté ici est la reproduction NIST, pas le fichier expérimental original de Langrand. Aucune trace force-déplacement ni énergie de séparation mesurée n'a été obtenue par cette lecture. Aucun nouvel examen des vidéos de l'utilisateur n'était nécessaire pour la question précise de ce lot.

Outils réellement exécutés : OpenRadioss Windows `v20260728-win64` déjà présent ; Python 3.14 et NumPy/Pillow ; FFmpeg `9.0.1-full_build-www.gyan.dev` ; ParaView installé sous « 6.2.0 », dont `pvpython --version` annonce `6.2.0-RC1`. Gmsh n'a pas été trouvé dans les emplacements ciblés ; ce constat n'est pas un inventaire exhaustif du système. Aucune installation ni modification de logiciel par cette session.

## 2. Résultats ou choix d'un modèle officiel

La page imprimée 78 présente le critère quadratique normal/cisaillement. Le texte NIST évoque le changement de diamètre vers 1/4 pouce et un pas de quatre diamètres, soit 1 pouce. Il indique une hypothèse de mode de rupture identique. L'exposant de mise à l'échelle n'est pas explicité dans les pages inspectées.

Nous n'importons pas une histoire d'impact officielle, ni une énergie de rupture ajustée par NIST, ni une perforation attendue. La transcription d'une enveloppe expérimentale reproduite par NIST reste dépendante de cette source ; elle ne rend pas cette branche entièrement indépendante du NIST. L'enveloppe quadratique d'initiation ne détermine pas à elle seule une loi post-pic en mode mixte.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation d'archive n'est employée comme propriété mécanique. Pas de rescan de l'archive, pas d'écriture dans les sources. Les déformations I02A utilisées pour la vidéo et ParaView sont des résultats numériques du projet, et non une observation du 11 septembre. L'apparence d'une aile intacte dans une vidéo ne fournit pas l'énergie de séparation d'un assemblage.

## 4. Hypothèses propres au modèle

### Propriétés et unités

Unités natives : gramme, millimètre, milliseconde, newton. Ainsi 1 mm/ms = 1 m/s ; 1 N·mm = 0,001 J ; 1 N·ms = 0,001 N·s. Les historiques dérivés conservent mm et ms explicitement et convertissent énergies et impulsions en J et N·s.

Mise à l'échelle propre au projet : capacité proportionnelle à D², facteur (0,25/0,15625)² = 2,56. Diamètre cible 6,35 mm ; pas 25,4 mm. Il en résulte une force normale centrale de 11 392 N et une force de cisaillement de 6 528 N. Cette extrapolation n'est pas une mesure de l'assemblage réel.

Une liaison TYPE4 relie deux nœuds initialement distants de 10 mm. Sa masse totale de 200 g est partagée entre les extrémités ; l'extrémité mobile porte 100 g. Cette masse et la longueur initiale sont des paramètres d'éprouvette numérique, pas la masse ou la géométrie d'un rivet. Un nœud est fixe, l'autre possède le seul mouvement axial X libre ou imposé ; les autres degrés de liberté sont bloqués. Pas d'amortissement, pas d'ajout artificiel de masse, pas de dépendance à la vitesse, pas de température.

| Paramètre | Normal | Substitut « cisaillement » |
| --- | ---: | ---: |
| Force maximale Fp | 11 392 N | 6 528 N |
| Ouverture au pic d0, hypothèse | 0,02 mm | 0,02 mm |
| Raideur K = Fp/d0 | 569 600 N/mm | 326 400 N/mm |
| Ouverture finale df, hypothèses | 0,2 / 0,5 / 1 mm | 0,5 mm |
| Travail de séparation G = Fp·df/2 | 1,1392 / 2,848 / 5,696 J | 1,632 J |

G est ici une énergie par connecteur équivalent, pas une ténacité surfacique en J/m². Le cas nommé SHEAR ne fait que remplacer la capacité dans le même test axial : il ne vérifie ni une géométrie de cisaillement ni un changement de repère ni une interaction normale-tangentielle.

### Loi et historique irréversible

L'enveloppe monotone en traction est triangulaire : Fenv = Kδ avant d0 ; Fenv = Fp(df−δ)/(df−d0) entre d0 et df ; zéro après df. La formulation TYPE4 H2 utilise une décharge élastique de pente K avec glissement permanent. La référence indépendante ne réutilise pas le générateur de cartes :

- F = min(max(K(δ−p), 0), max(Fenv(δ), 0)).
- p ← max(p, δ−F/K) tant que la liaison n'est pas séparée.
- Une fois δ ≥ df, le drapeau de séparation reste vrai, F = 0, y compris après fermeture et réouverture.
- Énergie récupérable U = F²/(2K), convertie de N·mm vers J.
- Dissipation D = IE−U, où IE est le travail interne cumulé du connecteur.

Les trajets acceptés restent à δ ≥ 0 ; la compression et le contact après refermeture sont hors domaine. Il s'agit d'une loi de glissement plastique avec adoucissement, pas d'une loi cohésive à décharge vers l'origine. Aucun matériau déjà endommagé n'a vu ses propriétés réinitialisées. Les réglages H2, les variables d'historique et le plafonnement temporel ont été confrontés aux documentations primaires [TYPE4](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type4_spring_starter_r.htm), [décharge des ressorts](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stiffness_formulation_spring_hardening_r.htm), [historiques de ressort](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm) et [DTIX](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/dtix_engine_r.htm).

### Travail, réactions et masse

L'audit intègre séparément W = ∫F dδ par trapèzes, compare W à IE, puis vérifie Δ(Ecin + IE + énergie de contact) − Wext. Le nœud fixe a un travail nul ; en mouvement imposé, Wext alimente l'énergie interne et l'inertie de la masse mobile. En essai libre, Wext = 0 et Ecin,0 = Ecin + U + D à l'erreur numérique près.

Le canal REACX du convertisseur T01 contient ici une impulsion cumulée en N·ms, pas une force instantanée à intégrer une seconde fois. La somme des impulsions aux frontières est comparée à la variation de quantité de mouvement globale. Les nœuds sont réordonnés par leurs identifiants, le convertisseur ne conservant pas l'ordre des groupes du générateur. `column_map.json` documente les correspondances ; force du ressort et déplacement sont vérifiés indépendamment.

Après suppression du ressort, le compteur de masse de la pièce peut passer à zéro, alors que la masse nodale globale reste à 200 g pour le connecteur isolé. Le bilan utilise la masse et l'énergie cinétique globales, sans effacer la dissipation accumulée. L'audit vérifie cette conservation et l'absence d'ajout de masse.

## 5. Résultats dérivés et vérifications

### Cas acceptés

Neuf cas à déplacement imposé R2 : NORMAL_BASE_MONO, NORMAL_BASE_CYCLE, NORMAL_LOW_MONO, NORMAL_HIGH_MONO, SHEAR_BASE_MONO, NORMAL_BASE_HALFDT, ROW_H050, ROW_H025, ROW_H0125. Quatre cas dynamiques R1 : DYNAMIC_LOW_ENERGY, DYNAMIC_HIGH_ENERGY, DYNAMIC_G_LOW_V10, DYNAMIC_G_HIGH_V10. Les noms complets avec suffixe sont consignés dans `campaign_audit.json`.

| Cas dynamique | Vitesse initiale | Ecin,0 | G supposé | Réponse dans la fenêtre | Ecin finale | Vitesse finale |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Faible énergie, G central | 5 m/s | 1,25 J | 2,848 J | Arrêt puis retour, sans séparation | 0,066582 J | −1,153965 m/s |
| Énergie haute, G central | 10 m/s | 5 J | 2,848 J | Séparation | 2,152020 J | 6,560517 m/s |
| Même énergie, G bas | 10 m/s | 5 J | 1,1392 J | Séparation | 3,860818 J | 8,787284 m/s |
| Même énergie, G haut | 10 m/s | 5 J | 5,696 J | Arrêt puis retour, sans séparation | 0,014204 J | −0,532985 m/s |

Dernier état sauvegardé : 0,1198 ms pour le premier cas, 0,1999 ms pour les trois autres. « Arrêt » signifie inversion du mouvement d'ouverture dans cette fenêtre, pas immobilisation permanente. Les maxima d'ouverture sans séparation sont respectivement 0,1330374 et 0,6539598 mm. Pour les cas séparés, vfinal = sqrt(2(Ecin,0−G)/m) est vérifiée ; on ne déduit pas une vitesse d'avion de ces masses de 100 g.

Dans le cycle partiel, la montée jusqu'à δ = 0,2 mm conduit à F ≈ 7 120 N, puis la décharge à un glissement conservé p ≈ 0,1875 mm. La décharge-recharge sous le maximum précédent ne crée pas de dissipation supplémentaire dans cette loi idéale ; la dissipation déjà acquise subsiste. La poursuite jusqu'à la séparation complète dissipe 2,848 J, également après fermeture/réouverture sans cicatrisation.

### Précision numérique dans ce domaine limité

- Treize terminaisons normales, aucun avertissement de démarrage dans les cas acceptés, aucune masse ajoutée.
- Écart maximal force/référence : 0,001178 % de la capacité correspondante ; seuil fixé 1 %.
- Résidu énergétique global maximal : 0,0000871 % de max(G, Ecin,0) ; seuil 1 %.
- Écart maximal impulsion/quantité de mouvement : 0,468 % de l'échelle d'impulsion définie dans l'audit ; seuil 1 %.
- Plus petite variation de dissipation sauvegardée : −1,306 × 10⁻⁶ J, compatible avec la quantification des sorties et le seuil −10⁻⁵ J. La monotonie n'est pas revendiquée à précision arithmétique exacte.
- Division par deux du pas temporel maximal : travail final identique à la précision des sorties, et non une erreur mathématique strictement nulle du solveur.

La rangée de 200 mm est répartie en 4, 8 ou 16 connecteurs pondérés par h/25,4. Elle représente 7,874 rivets équivalents sous ouverture uniforme. Énergie totale attendue ≈ 22,4252 J ; étendue relative des trois valeurs calculées 0,0000357 %, contre un seuil de 0,1 %. C'est un test de conservation des poids sous partition, pas une convergence spatiale d'un assemblage déformable ni une preuve d'objectivité de localisation.

### Prévols rejetés et exécution

Deux prévols R0 sont conservés mais rejetés : champ fixe TYPE4 mal positionné et mouvement X simultanément imposé et bloqué. Les neuf mouvements imposés R1 sont conservés mais remplacés : les angles de leurs déplacements linéaires par morceaux introduisaient des sauts de vitesse et un décalage des historiques impulsion/inertie. R2 lisse chaque segment avec 3u²−2u³, échantillonné en 1 000 subdivisions. Les essais libres gardent R1. Aucun seuil n'a été assoupli pour faire accepter ces calculs.

Pas maximal 0,0001 ms, ou 0,00005 ms pour le témoin demi-pas ; sauvegarde historique 0,0002 ms. Le plafond DTIX reste actif après suppression. Un seul fil d'exécution, plafond de 60 s par lancement. Les treize séquences acceptées (préparation solveur, moteur et conversion) ont pris ensemble 21,217 s, hors prévols, audits et présentation. Pas de calcul de plusieurs heures. Versions, commandes, codes retour, temps et empreintes des exécutables sont conservés dans chaque `execution.json`.

### Livrables visuels et conservation

`synthese_impact_i02b.png` présente les nouvelles courbes calculées. Sa lisibilité a été vérifiée après correction de deux superpositions de légendes.

`wtc1_3d_v4/renders/impact_i02b/I02A_etats_verifies.mp4` est un nouvel encodage des 25 images annotées I02A existantes : H.264, 960 × 620, 5 s, 150 images à 30 Hz par répétition, sans interpolation. Il ne représente pas la rupture I02B. Le bandeau prévient que la rupture I02A est désactivée et que les grandes déformations tardives ne sont pas physiquement qualifiées. Métadonnées et image à 2,5 s inspectées ; les 25 images sources sont inchangées.

`wtc1_3d_v4/output/impact_i02b/paraview_i02a/I02A_solver_states_ms.pvd` ouvre les 25 états I02A avec coordonnées en mm, temps en ms, identifiant de pièce et déformation plastique équivalente. Réouverture des 25 fichiers VTP : coordonnées, connectivité, pièces et déformations identiques aux tableaux sauvegardés. Ne pas activer d'interpolation temporelle. Ce transfert ne relance pas OpenRadioss. Un avertissement de ParaView sur la sauvegarde des préférences hors espace autorisé n'affecte pas les fichiers dérivés vérifiés.

## 6. Contradictions, manques et prochaine étape

Le blocage principal ne vient plus de l'affichage 3D : il manque toujours une loi post-pic documentée pour les assemblages réels, leurs positions, dimensions, matériaux et effets de vitesse. Les trois énergies sont des essais de sensibilité, pas des probabilités ni une calibration. Le succès numérique du connecteur n'en fait pas un rivet 767 qualifié.

IMPACT-I02C doit coupler cette liaison à un petit sous-ensemble peau–raidisseur/longeron déformable. Commencer élastique, séparer ouverture normale et véritable cisaillement, vérifier rotations/repères, absence de liaison parasite, réaction et bilan d'énergie, puis l'histoire de rupture. Comparer plusieurs maillages de plaques avec force et énergie par longueur constantes. Ne pas présenter le partitionnement I02B comme cette convergence. La généralisation en mode mixte doit préciser initiation, dissipation et contact après rupture avant emploi dans l'aile.

L'intégration ultérieure dans la section I02A conservera le témoin à assemblages fusionnés ; comparer impulsion, énergie absorbée, ouvertures et fragments sur une même fenêtre. Le balayage 5/10 raidisseurs et épaisseurs basses/centrales/hautes, ainsi que le raffinement spatial 50 vers 25 mm de la section d'aile, restent à faire. Le B762 graphique ne reçoit toujours aucun crédit mécanique.

Ni une température imposée ni Blender ne calculent un incendie. La localisation en flexion après fracture complète reste non validée. Une éventuelle réussite ou difficulté de notre sous-modèle ne démontre pas à elle seule le mécanisme historique, l'intégrité d'une aile réelle ou l'effondrement du WTC1. Aucun résultat visuel n'a servi de cible d'ajustement.

## Reprise et contrôle

Les configurations, cartes solveur, historiques bruts, références indépendantes et résultats sont sauvegardés. Réutiliser les audits et sorties acceptés ; ne pas relancer les cas ni relire les archives sans question précise. Le contrôle de livraison `release_audit.json` doit être PASS avant de considérer cette itération enregistrée. Il contrôle les empreintes, la préservation des témoins et le harnais avant/après la mise à jour de l'état. La passation compacte est `harness/handoffs/WTC1_IMPACT_I02B_HANDOFF.md`.
