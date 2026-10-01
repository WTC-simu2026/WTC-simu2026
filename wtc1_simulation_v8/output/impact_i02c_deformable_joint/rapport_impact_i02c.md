# IMPACT-I02C — Deux bandes déformables avec liaisons séparables

13 septembre 2026. Configuration `wtc1_simulation_v8/data/impact_i02c_deformable_joint.json`. Calculs déterministes, graine déclarée 9112001 sans tirage. Ce lot prolonge I02B sans modifier ses sorties.

## Résultat utile

La liaison rompable n'est plus isolée entre deux masses ponctuelles : elle transmet maintenant un effort entre deux bandes métalliques élastiques maillées. Quinze cas retenus passent 293 contrôles booléens, avec 21 marques de campagne incluant les agrégations des cas. Ces nombres décrivent des contrôles de code et de cohérence, pas des validations expérimentales indépendantes.

Le glissement tangent aux bandes mène à une séparation effective ; leur énergie élastique et leur inertie sont suivies séparément de la dissipation des liaisons. L'ouverture normale est vérifiée seulement à faible charge, en flexion élastique. La nouvelle vidéo contient des états I02C, et non les anciennes images I02A.

Les efforts maximaux et l'énergie de séparation sont stables sur trois maillages. Les petites vibrations résiduelles ne sont pas encore convergées. Deux essais dynamiques ont été arrêtés avant de sortir du domaine à glissement positif ; leurs longues trajectoires exploratoires sont conservées mais rejetées comme solutions qualifiées.

## 1. Faits directement observés ou transcrits

Le harnais initial a répondu PASS : 101 entrées, état IMPACT-I02B, suite IMPACT-I02C. Aucun ancien calcul n'a été relancé. Les nouveaux calculs utilisent OpenRadioss `v20260728-win64`, un fil chacun. Leurs commandes, empreintes d'exécutables, codes retour et temps sont dans les `execution.json`. Les quinze séquences acceptées totalisent 174,604 s, hors prévols, audits et présentation ; aucune exécution de plusieurs heures.

Les propriétés de liaison proviennent des entrées sauvegardées I02B. Ce lot ne relit pas les PDF ni l'archive. Il conserve donc leur statut : capacité issue d'une lecture approximative de la figure 4-21 du NIST, extrapolation D² propre au projet, travail post-pic non mesuré. Aucune nouvelle donnée Boeing n'est revendiquée.

La documentation primaire [TYPE8](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm) définit des composantes indépendantes dans un repère local et préconise notamment une longueur initiale nulle pour éviter les problèmes de moments d'un ressort général de longueur finie. [LAW1](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law1_elast_starter_r.htm) fournit la référence élastique. Les axes sont définis suivant [SKEW/FIX](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/skew_fix_starter_r.htm), les sorties suivant [TH/SPRING](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm). La forme de décharge H2 a été vérifiée numériquement, sans supposer qu'elle décrit un rivet réel.

## 2. Résultats ou choix d'un modèle officiel

Aucun résultat d'impact officiel n'est importé comme objectif ou condition finale. Les capacités centrales héritées d'I02B restent dépendantes de la reproduction documentaire NIST ; leur provenance n'est pas remplacée par le succès de ce nouveau calcul. Ni le diamètre cible ni une résistance maximale ne déterminent l'énergie de séparation, les effets de vitesse ou le comportement en chargement combiné.

## 3. Affirmations provenant des archives locales

Aucune affirmation supplémentaire d'archive n'est utilisée comme propriété. Aucune vidéo source n'est analysée, modifiée ou prise comme cible visuelle. Les discontinuités de la nouvelle animation résultent du connecteur numérique choisi et ne sont pas une identification du mécanisme du WTC1.

## 4. Hypothèses propres au modèle

### Géométrie, matériaux, unités

Deux bandes coplanaires se rejoignent au bord x=0, avec des nœuds distincts liés par une rangée de ressorts de longueur initiale nulle. Chacune mesure 40 mm de long et 25,4 mm de large. Épaisseurs : peau 2 mm, bande de semelle 3 mm. Il n'y a ni recouvrement réel, ni excentricité des surfaces moyennes, ni trous, ni contact entre plaques. « Peau » et « semelle » décrivent les rôles du sous-ensemble, pas un détail Boeing reconstruit.

Matériau générique constant : E=70 000 MPa, ν=0,33, ρ=0,0027 g/mm³. Il est élastique, sans limite d'écoulement, écrouissage, vitesse, température ou fracture de coque. Masse issue de la géométrie : 5,4864 g + 8,2296 g = 13,716 g. Les ressorts n'ajoutent aucune masse ni inertie de rotation ; les inerties des coques subsistent.

Unités natives g–mm–ms–N ; 1 mm/ms = 1 m/s, 1 N·mm = 0,001 J et 1 N·ms = 0,001 N·s. Les grilles visées 5 / 2,5 / 1,25 mm donnent respectivement 96 / 352 / 1 344 coques, et 126 / 408 / 1 452 nœuds. La largeur est divisée uniformément avec un nombre entier de cellules ; les pas transversaux réels sont consignés par les coordonnées.

La rangée utilise des poids de largeur tributaire h/25,4, avec demi-poids aux bords. Leur somme vaut un rivet équivalent, réparti en 7, 12 ou 22 connecteurs. Les points colorés de la vidéo ne sont donc pas autant de rivets physiques.

### Liaison et conditions aux limites

Tangentiel : Fp=6 528 N, d0=0,02 mm, df=0,2 / 0,5 / 1 mm, soit G=Fp·df/2 = 0,6528 / 1,632 / 3,264 J pour toute la rangée. Normal : Fp=11 392 N, d0=0,02 mm, df=0,5 mm, mais le test normal reste très loin du pic. d0, df, la loi de décharge et les propriétés des plaques sont des hypothèses non calibrées.

Une seule composante du ressort est active par essai ; les autres translations et toutes ses raideurs de rotation sont nulles. Un repère fixe définit x tangent et z normal à la surface. En glissement, les nœuds ne se déplacent que longitudinalement et toutes les rotations sont bloquées. En ouverture, seuls les déplacements normaux et rotations de flexion sont libres, sauf aux prises éloignées où les rotations sont bloquées. La déformation transversale est empêchée dans les deux essais. Les prises imposent ou libèrent le mouvement déclaré ; le reste de la plaque est réellement déformable.

Ce guidage donne une référence contrôlable, pas un assemblage libre de se tordre. Le test tourné de 90° vérifie une transformation initiale du repère, pas l'objectivité sous grandes rotations en cours de mouvement. Les moments de réaction des prises ne sont pas audités séparément dans ce lot.

### Historique et énergie

Enveloppe triangulaire positive ; pente initiale K=Fp/d0 ; décharge de pente K avec glissement permanent p. La référence indépendante calcule F=min(max(K(δ−p),0),max(Fenv(δ),0)) puis p←max(p,δ−F/K). Une fois δ≥df, l'indicateur de séparation reste inactif et la force n'est pas recréée. G est une énergie de liaison en J, non une ténacité en J/m².

Les révisions R2/R3 augmentent la seule pente de décharge de 10⁻⁸ en relatif afin d'éviter une correction automatique causée par l'arrondi des poids ; ni Fp ni G ne changent. L'énergie récupérable est Uj=ΣFj²/(2Kj), et Dj=IEj−Uj. Le travail ∫ΣFj dδj est intégré séparément. Le bilan vérifie Δ(Ecin+IEplaques+IEj+Econtact)−Wext, avec Econtact=0. L'énergie ne disparaît pas lorsqu'un ressort est supprimé.

La quantité de mouvement est recalculée avec les masses nodales déduites des aires et épaisseurs. La somme des canaux REAC est déjà une impulsion cumulée : elle n'est pas intégrée une seconde fois. Elle est comparée à ΔP. Pour le glissement, l'énergie cinétique est aussi recalculée à partir des vitesses nodales ; en flexion, cette vérification translationnelle n'inclut pas les rotations et n'est pas utilisée comme égalité complète.

## 5. Résultats dérivés

### Références élastiques et raffinement

Avec E*=E/(1−ν²), la compliance tangentielle attendue est L/(E*b)(1/t1+1/t2)+1/Kj. Pour 0,01 mm imposé : F attendu 505,823 N ; mesuré environ 505,800 N. Erreur de raideur inférieure à 0,005 %.

La référence normale utilise deux porte-à-faux en série avec rotation libre à la jonction : compliance 4L³/(E*b)(1/t1³+1/t2³), complétée par le cisaillement transverse (coefficient 5/6) et 1/Kj. Force attendue 0,479586 N pour 0,01 mm ; maillage fin 0,479532 N, erreur 0,01114 %. La valeur grossière a une erreur de 0,4245 %. Il ne s'agit pas d'un essai de rupture normale. Les très petits jeux négatifs numériques (jusqu'à 2,60×10⁻⁶ mm) restent sous le seuil de domaine de 10⁻⁵ mm ; aucune résistance en compression n'en est déduite. Les contraintes de flexion ne sont pas extraites : elles sont indiquées indisponibles, et non nulles.

| Maillage cible des bandes | Pic tangent | Travail final de séparation |
| --- | ---: | ---: |
| 5 mm | 6 526,4458 N | 1,63200000 J |
| 2,5 mm | 6 526,3264 N | 1,63199964 J |
| 1,25 mm | 6 526,4136 N | 1,63200008 J |

Étendue relative : 0,001829 % sur le pic, 0,00002696 % sur le travail. Demi-pas : pic modifié de 0,001296 %, travail identique à la précision de sortie. Rotation initiale de 90° : coordonnées rétablies exactement par la transformation inverse et énergie identique. Translation uniforme libre : aucune déformation ni force parasite détectée.

Ces contrôles ne ferment pas toutes les questions de convergence : à l'instant commun 1,199 ms, l'énergie cinétique résiduelle du chargement monotone vaut 0,0009271 / 0,0012800 / 0,0014955 J. L'écart moyen–fin est de 14,4 %, bien que très petit par rapport au travail de séparation. Le champ d'ondes et les vibrations post-fracture restent non convergés. La géométrie guidée charge aussi la rangée presque uniformément ; elle ne teste pas une propagation spatiale complexe de décollement.

### Essais dynamiques libres

Seule la bande de droite reçoit la vitesse initiale ; aucune pénétration n'est imposée ensuite. À 2,5 J elle vaut environ 24,649 m/s pour 8,2296 g. Les valeurs suivantes sont prises aux fins de fenêtres différentes, explicitement indiquées :

| Énergie initiale | G supposé | Fin sauvegardée | Séparation complète | Ecin finale | IE plaques finale | IE liaison finale |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 0,4 J | 1,632 J | 0,0319 ms | Non | 0,328180 J | 0,063130 J | 0,008691 J |
| 2,5 J | 0,6528 J | 0,39995 ms | Oui | 1,541401 J | 0,305809 J | 0,652797 J |
| 2,5 J | 1,632 J | 0,39995 ms | Oui | 0,597773 J | 0,270240 J | 1,631993 J |
| 2,5 J | 3,264 J | 0,20995 ms | Non | 0,055008 J | 0,050554 J | 2,394439 J |

Dans le premier cas, le travail de liaison est presque entièrement récupérable ; la dissipation ne doit pas être confondue avec IE. Dans les cas séparés, les oscillations échangent ensuite de l'énergie entre les plaques et leur mouvement. Les contraintes longitudinales élastiques estimées atteignent environ 286 MPa dans la campagne : ce n'est pas un contrôle de plasticité d'un alliage réel, dont la carte n'est pas qualifiée.

Le cycle retenu charge la prise à 0,30 mm, la relâche à +0,05 mm dans la zone sans force, recharge, puis sépare complètement avant un nouveau cycle. L'historique persiste ; les forces après suppression restent nulles.

### Contrôles, corrections et domaines exclus

Résidu énergétique global maximal : 0,001795 % de l'énergie propre au cas, sans normalisation artificielle par G pour la flexion minuscule. Écart impulsion–quantité de mouvement maximal : 0,356 %, contre le seuil de 2 %. La différence énergie cinétique nodale–globale atteint 0,219 %, sous le seuil configuré de 1 %. Écart maximal force/loi indépendante : 0,0323 % ; une partie des variations d'historique se produit entre deux sauvegardes.

Le cumul de dissipation peut présenter des écarts négatifs de quelques microjoules, inférieurs au seuil absolu 10⁻⁵ J ; aucune monotonie arithmétique exacte n'est revendiquée. La masse globale reste 13,716 g. Le « supplément de masse » maximal enregistré est 1,78×10⁻¹⁵ g, arrondi flottant et non masse volontairement ajoutée.

Les corrections sont conservées dans la configuration et les révisions de cas : R0 laissait le solveur changer l'intégration de LAW1 ; R1 explicite N=0. L'avertissement 445 « inertie nulle » des ressorts sans masse et sans raideur de rotation est attendu et limité à ces propriétés ; il ne signifie pas que les coques n'ont pas d'inertie. L'avertissement 506 de pente due à l'arrondi est refusé et corrigé en R2 par la marge 10⁻⁸. Deux premiers audits contenaient des critères additionnels non configurés de 10⁻⁵ pour P et Ecin ; leurs résultats initiaux sont préservés, puis les seuils préalablement configurés de 2 % et 1 % ont été appliqués. Aucun seuil déclaré ni paramètre de rupture n'a été ajusté pour obtenir un résultat attendu.

Les longues trajectoires R2 à faible énergie et G élevé atteignaient le glissement négatif à 0,0332 et 0,22055 ms. Leur continuation ne décrit pas le cisaillement inverse d'un rivet : la loi n'en possède pas. Les nouveaux R3 s'arrêtent à 0,032 et 0,21 ms. Le cycle R2 descendait à −0,001045 mm ; sa nouvelle consigne R3 reste positive. Les anciennes sorties restent sauvegardées et ne sont pas promues.

### Vidéo et données 3D

Vidéo `wtc1_3d_v4/renders/impact_i02c/I02C_liaison_couplee.mp4` : 6,2 s, H.264, 1 280×800, 31 états nodaux réellement sauvegardés du cas dynamique central. Aucune amplification des déplacements ; les images à 30 Hz sont obtenues par répétition, pas par interpolation mécanique. La projection représente les surfaces moyennes des coques, pas leur épaisseur géométrique ni un calcul de Blender.

Un second chemin compare les fichiers d'animation natifs aux historiques nodaux : 31 états, connectivités vérifiées, erreur maximale position–déplacement 5,032×10⁻⁵ mm compatible avec les arrondis de position ET déplacement et la simple précision de l'animation. Le premier contrôle ne budgétait que l'arrondi de position ; il est conservé. Écart maximal entre animation et historique 0,000695 mm, y compris le dernier instant situé légèrement après la dernière sauvegarde nodale, sous la borne explicitement fondée sur précision et vitesse×intervalle.

Les fichiers VTU ont été relus par ParaView : coordonnées, connectivités, types et tableaux identiques aux fichiers convertis. Ouvrir `wtc1_3d_v4/output/impact_i02c/I02C_coupled_joint_ms.pvd`, unités mm et ms. La vidéo et ParaView échantillonnent la même solution à des instants légèrement différents ; ne pas confondre leurs numéros d'image. Aucun état interpolé de rupture n'est validé.

## 6. Informations manquantes et suite

La qualification reste limitée au sous-ensemble coplanaire, guidé et en modes séparés. Il manque un recouvrement avec excentricité, les rotations libres, une loi cohérente en cisaillement inverse et en mode mixte, le contact après séparation, les propriétés dynamiques des assemblages réels et la déchirure des tôles. La réponse complète de l'aile et de la façade n'est pas obtenue dans ce lot.

I02D : construire un petit recouvrement peau–semelle avec bras de levier et degrés de liberté libérés ; vérifier réactions et moments, couplage normal/tangent et bilan énergétique, puis contact après séparation. Définir la dissipation mixte et le sens inverse avant leur emploi. Conserver I02C comme référence coplanaire ; comparer les observables de rupture et les vibrations avec raffinement spatial/temporel. Seulement ensuite autoriser un transfert borné dans la section d'aile I02A, en gardant le témoin à assemblages fusionnés.

Les contrôles froid V11F, thermique V11R et d'impact I01/I02A/I02B sont préservés par empreintes. V11S demeure différée. Le B762 graphique ne reçoit aucun crédit mécanique. La localisation en flexion après fracture complète reste non validée ; une température imposée n'est pas un incendie calculé. Aucune de ces vérifications ne prouve un événement historique ni un effondrement réel.

## Reprise

Utiliser `campaign_audit.json`, `source_manifest.json`, `release_audit.json` et la passation `harness/handoffs/WTC1_IMPACT_I02C_HANDOFF.md`. Le contrôle de livraison doit être PASS avant de considérer I02C enregistrée. Ne pas relancer les quinze cas ni rescanner les archives pour la reprise ; consulter seulement les sorties nécessaires à I02D.
