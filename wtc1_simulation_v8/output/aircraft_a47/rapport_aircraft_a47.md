# AIRCRAFT-A47 — réponse chargée des coques contrôlée ; derniers échantillons manquants conservés

Après correction d’une erreur d’encodage de la nouvelle charge, traction et flexion du panneau isolé concordent avec leurs références indépendantes et entre explicite et implicite dans les histoires enregistrées. Les deux contrôles exigeant un échantillon temporel final exactement12ms restent échoués. Le modèle entier et les dix secondes physiques ne sont pas calculés par ces témoins.

## 1. Faits directement observés ou transcrits

Cinq préparations Starter et neuf processus Engine nouveaux, aucun ancien cas relancé. La première préparation de traction signale trois avertissements DRX/DRY/DRZ, rotations non calculées dans cette sortie. Une nouvelle préparation omet seulement ces trois variables ; les anciennes tentatives restent présentes. Les logs montrent deux threads pour Starter, un pour Engine ; le manifeste et l’addendum corrigent la déclaration générale d’un thread pour les préparations, ainsi que le même libellé antérieur A46, sans réécrire ses fichiers.

La flexion initiale Linux explicite est arrêtée à0,010ms avec valeurs infinies, malgré NORMAL TERMINATION et code0. Le calcul implicite initial s’arrête avant le premier pas accepté. Un nouveau contrôle Windows sur exactement la même reprise et carte explicite reproduit l’arrêt0,010ms ; il ne s’agit pas d’un ancien calcul répété. Les premiers completion.json restent des résultats de processus, pas des preuves de terme physique atteint.

Le contrôle des mouvements montre une erreur du générateur : l’amplitude était écrite dans le facteur de temps Ascale_x, le facteur de déplacement Fscale_y restait1. La correction pré-déclarée place Ascale_x=1 et Fscale_y=amplitude initialement prévue. Les dossiers corrigés sont distincts. Aucun changement de matériau, densité, masse, formulation, appui, charge pré-déclarée ou seuil d’acceptation pour améliorer les résultats.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat officiel historique. La documentation et les sources figées définissent les champs de sortie et leur normalisation, ainsi que l’ordre des facteurs du déplacement imposé. Les formules de référence viennent de l’élasticité isotrope en contrainte plane et de l’intégrale d’épaisseur : tractionU=Eε²Ah/2 ; flexion anticlasteU=Eh³κ²A/24. Elles ne proviennent pas de dégâts observés ou de NIST.

- [Facteurs temps et déplacement IMPDISP](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impdisp_starter_r.htm)
- [Sorties des efforts et moments de coque](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_shel_starter_r.htm)
- [Sorties nodales](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, photographie, vidéo ou PDF inspecté. Sources en lecture seule. Aucun dégât connu n’est une cible de réglage.

## 4. Hypothèses propres au modèle

Graine1102072, zéro tirage. Même extrait A20 de quatre coques de façade et neuf nœuds, huit nœuds de bord à mouvements connus et un intérieur libre. MAT/LAW2/3, PROP/TYPE1/31 et PART/31 inchangés ; densité0,00786g/mm³, E200000MPa,ν0,3,épaisseur7,9375mm,masse8640,489177995g. Ces propriétés de référence ne sont pas des mesures du panneau historique. Déformation de traction1e-5 ; courbure de flexion1e-6/mm avec anticlaste−νκ. Courbe quintique normalisée échantillonnée sur10ms puis maintien jusqu’à12ms ; interpolation native linéaire des mêmes points pour la référence.

Critères pré-déclarés : énergie/efforts2%, plancher énergie1e-7J, déplacement2e-5mm, rotation2e-6rad, masse1e-6relatif, aucune masse ajoutée ou plasticité admise. Aucun critère physique élargi. Pas initial/cap1e-3ms, facteur explicite0,4, impliciteNewmarkγ0,5/β0,25,MUMPS2,tolérances non linéaires1e-11. L’implicite réduit effectivement ses pas ; ce n’est pas une simulation à pas fixe, et aucune reconstruction de vitesse instantanée A41 n’est appliquée à ces séries échantillonnées.

## 5. Résultats dérivés

| Mode | Méthode | IE finale enregistrée(J) | Référence(J) | Écart relatif | Dernière histoire(ms) | Résidu global maximal(J) |
|---|---|---:|---:|---:|---:|---:|
| MEMBRANE | EXPLICIT | 0.01099293 | 0.01099298878 | 5.3467e-06 | 12 | 2.2222e-08 |
| MEMBRANE | IMPLICIT | 0.01099293 | 0.01099298878 | 5.3467e-06 | 11.999 | 1.3232e-08 |
| BENDING | EXPLICIT | 0.0005771698 | 0.0005771676952 | 3.6468e-06 | 12 | 1.38e-09 |
| BENDING | IMPLICIT | 0.0005771698 | 0.0005771676952 | 3.6468e-06 | 11.99925 | 3.3688e-07 |

Les quatre séries corrigées passent finitude, masse, absence de masse ajoutée, déplacements imposés, rotations prescrites en flexion, bilans globaux natifs, absence de travail plastique, épaisseur, absence d’érosion, référence d’énergie et efforts/moments de coque sur leurs échantillons enregistrés. Les erreurs relatives d’énergie sont environ5,35e-6en traction et3,65e-6en flexion. Les comparaisons KE/RKE/IE/travail et déplacements passent sur le support temporel réellement commun jusqu’à11,999ms, sans décalage ni extrapolation.

L’ensemble original n’est pas déclaré intégralement réussi : l’histoire explicite atteint12ms, celles des implicites s’arrêtent à11,999et11,99925ms. Les animations terminales natives donnent12,001ms pour les explicites,12ms pour la traction implicite, mais seulement11,5002ms pour la dernière animation de flexion implicite. Les premières revues de dernier échantillon échouées restent présentes ; la reprise finale de flexion existe mais son contenu terminal n’est pas réétiqueté à partir d’une simple terminaison normale. Les bilans couvrent les temps réellement enregistrés.

L’accord mécanique du panneau chargé empêche d’interpréter les27/21directions de rotation signalées par CHECK A46 comme une preuve d’absence de flexion. Les coques seules ne reproduisent pas l’arrêt d’assemblage entier. Ces résultats orientent la prochaine étape vers les degrés actifs et couplages du graphe entier, avec une famille à la fois.

## 6. Contradictions et informations manquantes

La sortie terminale de flexion implicite, la qualification des reprises chargées et les couplages entiers restent incomplets. Les champs de vitesses implicites ne sont pas des vitesses instantanées supposées ; les réactions brutes sont conservées sans ajouter de terme RKE ou injecter des champs. L’assemblage entier ASSEMC_KIJ A45 n’a pas été réparé. Les cinq TYPE25 ignorés restent une incompatibilité indépendante.

A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués. Le panneau acier n’est pas une validation des peaux composites, d’un assemblage avion, de rupture historique ou du modèle entier. Structure intérieure, gravité et bilans des domaines entiers restent à traiter. Meilleur impact entierA20=0,0200001220703125s ; aucun temps de témoin crédité aux dix secondes demandées. Aucun nouveau fichier vidéo ne prétend couvrir cet objectif.

Les anciennes preuves SHA256 sont conservées et l’audit avant/après des tailles/dates constate aucune modification ancienne. Ce contrôle n’est pas une nouvelle relecture de tous les contenus ; les entrées physiques et le binaire sont revérifiés par SHA256.

AIRCRAFT-A48 : conserver les quatre témoins chargés corrigés A47 en cache, sans les refaire. L’amplitude était écrite dans Ascale_x temps ; la correction vers Fscale_y rétablit exactement les paramètres pré-déclarés, sans ajustement physique. Les contrôles mécaniques traction/flexion et leurs comparaisons passent sur les histoires réellement communes jusqu’à11,999ms ; la demande de dernier échantillon12ms reste échouée pour les deux implicites, dernière animation de flexion11,5002ms. Ne pas réétiqueter ces gates en succès, ni injecter/extrapoler les champs. Les coques seules peuvent répondre mécaniquement en explicite et MUMPS ; les avertissements de rotations CHECK A46 ne démontrent donc pas une absence de flexion. Cibler maintenant le graphe entier qui avorte dans ASSEMC_KIJ : pré-déclarer des petits assemblages coque/solide/RBE3/TYPE2 issus des données entières, en introduisant une seule famille à la fois, puis évaluer la topologie et les degrés actifs avant variante entière. Ne pas modifier silencieusement masse, inertie, résistances, formulation ou TYPE25. Les cinq TYPE25 ignorés restent une incompatibilité indépendante. Les pas implicites A47 se réduisent ; aucune accélération10s ni reprise chargée validée n’en découle. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF restent actives et incomplètes. Publier A46+A47 avec tous les échecs, selon autorisation existante, puis avancer A48.
