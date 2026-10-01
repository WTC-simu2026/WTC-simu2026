# IMPACT-I02D — recouvrement, modes combinés et contact après séparation

13 septembre 2026. **Lot numérique borné terminé : 13 cas R5, 226 contrôles de cas, 13 marques de campagne, PASS.** Les marques incluent des agrégations, pas autant de validations expérimentales indépendantes. Les séquences acceptées cumulent 320,970 s ; les exécutions et diagnostics enregistrés cumulent 603,999 s, hors travail interactif et processus interrompus non chronométrés jusqu'au bout.

L'avancée est mécanique : un recouvrement à excentricité réelle, des coques déformables sans guidage intérieur, une liaison dont l'histoire persiste lors du changement de sens, et un contact distinct qui subsiste après sa rupture. **Le film n'est toujours pas un Boeing contre la façade.** Il montre un assemblage de vérification sollicité aux prises, sans rupture des tôles.

## 1. Faits directement observés ou transcrits

- Treize séquences R5 terminent normalement dans OpenRadioss installé. Configurations, cartes d'entrée, journaux, historiques, états nodaux, révisions rejetées et empreintes sont conservés. Aucune ancienne simulation n'a été relancée.
- Les archives, vidéos de l'utilisateur, copies NIST et anciennes itérations n'ont pas été modifiées. Aucune analyse vidéo supplémentaire n'était nécessaire à cette question.
- Le convertisseur écrit les historiques de solide dans l'ordre **OFF, IE, LSX, LSY, LSZ, LSXY, LSYZ, LSXZ**, même lorsque les mots-clés sont demandés dans un autre ordre. La somme des IE élémentaires est recoupée avec celle de la pièce cohésive.
- Les sorties nodales REAC sont des **impulsions cumulées**, non des forces instantanées. Les différences de ces sorties retrouvent les bilans de quantité de mouvement et le travail des prises. Les moments REACXX/YY/ZZ sont également conservés.
- `primary_code.json` épingle trois fichiers du dépôt OpenRadioss au commit `6803d02ed72fdaeea6898b725358bb3e382062c0`. Ce code primaire sert à reconstruire les équations ; ce commit n'est pas présenté comme le commit exact de compilation des exécutables installés, dont les empreintes sont enregistrées séparément.

Documentation primaire consultée : [LAW117](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm), [équations publiées de LAW117](https://2023.help.altair.com/2023/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm), [TYPE43](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm), [contact TYPE7](https://2025.help.altair.com/2025/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm), [historiques nodaux](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm). Ce sont des descriptions de calcul, pas des essais physiques de rivets Boeing.

## 2. Résultats d'un modèle officiel

Aucun résultat officiel de pénétration, d'endommagement de façade ou de rupture d'aile n'est utilisé comme cible d'ajustement. Le lien NIST reste celui d'I02B : enveloppe de charges d'un essai de connexion et contexte de rivets. Les pics 11 392 N / 6 528 N héritent notamment de notre extrapolation en carré du diamètre ; ce ne sont pas deux capacités mesurées sur une connexion précisément localisée du Boeing étudié. Les calculs I02D ne reproduisent pas le modèle d'impact NIST.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation historique tirée d'une archive n'est ajoutée. Ni la disparition visuelle d'une aile ni une apparence de pénétration ne servent de condition aux limites. Le résultat de ce sous-modèle ne tranche aucune hypothèse historique, officielle ou alternative.

## 4. Hypothèses propres au modèle

### Géométrie, propriétés et unités

Unités du solveur : g, mm, ms, N, MPa. Une vitesse de 1 mm/ms vaut 1 m/s. Un travail de 1 N·mm vaut 0,001 J ; 1 N·ms vaut 0,001 N·s ; 1 N·mm·ms vaut 10⁻⁶ N·m·s.

| Paramètre | Valeur / interprétation |
|---|---|
| Bande inférieure | x = −40 à +5 mm, largeur 25,4 mm, épaisseur 2 mm |
| Bande supérieure | x = −5 à +40 mm, même largeur, épaisseur 3 mm |
| Écart initial des surfaces moyennes | 2,5 mm : les faces physiques idéales se touchent |
| Recouvrement | 10 × 25,4 = 254 mm² |
| Matériau des coques | E = 70 000 MPa, ν = 0,33, ρ = 0,0027 g/mm³ ; élastique constant |
| Masse des deux bandes | 15,4305 g ; 3,429 g pour les seuls petits coupons de 10 mm |
| Maillages des bandes | cible 5 / 2,5 mm : 108 / 396 coques, 140 / 456 nœuds |
| Zone cohésive | 12 / 44 éléments ; répartition d'une connexion équivalente, pas autant de rivets |
| Masse cohésive numérique | Imass=1, masse surfacique 10⁻¹² g/mm² ; total 2,54×10⁻¹⁰ g, sans crédit physique |

Le champ hérité `joint.rho_g_mm3` a un nom impropre pour Imass=1 : il est expressément interprété ici comme **masse surfacique** et expliqué dans `cohesive_mass_definition`. La masse volumique de l'aluminium n'est pas remplacée par cette valeur. Le témoin Imass=2 donnait aussi une masse proportionnelle à l'aire dans l'exécutable installé ; nous ne lui attribuons pas une couche matérielle physique.

Les coques TYPE24 ont une intégration élastique déclarée N=0. Dans les petits coupons, les deux surfaces sont pilotées uniformément. Dans les recouvrements, **les six degrés de liberté des nœuds intérieurs sont libres** ; les orientations et translations aux prises sont contrôlées. Ce ne sont donc ni des plaques libres de toute condition aux limites, ni un essai balistique.

La prise gauche est fixe ; la droite suit un déplacement lissé : 0,002 mm suivant x et z en 4 ms pour les essais élastiques ; 1,2 mm suivant x et 4 mm suivant z en 4 ms pour la séparation, puis maintien jusqu'à 5 ms. Pas de vitesse d'impact historique imposée à ces coupons, de masse ajoutée pour agrandir le pas, de plasticité ou de déchirure des tôles.

### Loi énergétique avec historique

LAW117 / TYPE43, formulation géométrique non linéaire, mélange BK d'exposant 1, γ=1, suppression lorsque les quatre points sont rompus. `True_thickness=0` laisse la géométrie courante définir le bras de levier : imposer une épaisseur constante à cet endroit a produit des moments incorrects dans les contre-essais.

Pour la connexion équivalente entière : Kn=569 600 N/mm ; Kt=326 400 N/mm ; début d'endommagement d0=0,02 mm ; séparation pure df=0,5 mm. Les énergies supposées sont Gn=2,848 J et Gt=1,632 J. Les rigidités surfaciques sont obtenues en divisant par 254 mm². Les aires élémentaires assurent la même capacité totale lors du raffinement.

La reconstruction indépendante utilise :

- δm = √(〈δn〉₊² + ‖δt‖²), puis κ(t)=max historique de δm ;
- un ratio énergétique instantané r=Kt‖δt‖²/(Kn〈δn〉₊²+Kt‖δt‖²), et Gm=Gn+(Gt−Gn)r ;
- Km=(Kn〈δn〉₊²+Kt‖δt‖²)/δm², df,m=2Gm/(d0 Km), en unités cohérentes N·mm ;
- d(t)=max(d passé, valeur bornée entre 0 et 1 de df,m(κ−d0)/[κ(df,m−d0)]) ;
- F=(1−d)Kδ en traction et cisaillement signé. Avant suppression complète, la compression cohésive reste élastique. Après suppression, cette connexion ne transmet plus de force.

Dans les coupons homogènes, U est également recalculée directement à partir des tractions sauvegardées : U=½ F·δ ; D=IE−U. On vérifie force, travail, non-décroissance de D à l'arrondi déclaré et absence de guérison. **Conserver seulement d mais oublier κ dans une reconstruction non proportionnelle donne une autre loi.** L'erreur initiale de reconstruction est gardée dans les diagnostics, pas interprétée comme une violation physique du solveur.

Le contact TYPE7 indépendant reste actif après suppression cohésive. Il est sans frottement, avec amortissement réglé à 10⁻²⁰ pour éviter une valeur automatique non nulle ; son intervalle d'activation vaut 2,5 mm. Avant rupture, les raideurs de compression cohésive et de contact peuvent agir en parallèle : cela reste une hypothèse du proxy, pas une calibration du matage d'un rivet.

## 5. Résultats dérivés et vérifications

### Loi et contact

| Essai homogène | Travail final de liaison |
|---|---:|
| Arrachement pur | 2,848000 J |
| Cisaillement pur | 1,632000 J |
| Cisaillement inversé puis séparation | 1,632000 J |
| Mode combiné proportionnel à 45° | 2,405029 J |
| Chemin combiné changeant de direction | 2,575413 J |

La différence entre les deux chemins combinés est un effet de la loi historique choisie, pas une erreur automatiquement identifiable en comparant au seul G du mode final. Les valeurs de Gm ne constituent pas une énergie universelle de rivet pour tous les chemins.

Après arrachement complet, une fermeture **imposée** de 0,02 mm dans l'enveloppe de contact donne environ 67 741,9 N de compression. Sans contact, le même contrôle donne environ 0 N. La liaison rompue reste sans traction et ne se reconstitue pas ; l'énergie maximale de contact vaut 0,675606 J puis est rendue lors de la réouverture. Cette forte force vérifie une pénalité numérique sous déplacement prescrit : **elle ne prédit pas une force de matage réelle et ne démontre pas un rebond libre sans pénétration.**

### Recouvrement déformable

Cas fin central : premières suppressions observées à 1,598 ms, toutes à 1,602 ms, avec un historique de 0,002 ms. Ce sont des instants échantillonnés propres au chargement imposé, pas des temps d'impact historique.

- Pic de réaction résultante : **6 371,269 N**.
- À 4,99805 ms : travail de liaison **1,651691 J**, énergie des tôles **0,00904575 J**, énergie cinétique **0,03118305 J**, énergie de contact nulle.
- 5 → 2,5 mm : écart de pic **0,4236 %**, travail de liaison **0,09318 %**, énergie cinétique au temps commun **0,9377 %**.
- Demi-pas : écart de pic **0,002309 %**, même travail à la précision de sortie ; comparaison cinétique au temps commun **0,001457 %**.
- Rotation initiale de 90° : écart maximal après transformation inverse **10⁻⁶ mm**, travail identique à la précision conservée. Ce contrôle n'est pas un test autonome de rotation rigide dynamique imposée.

Le recouvrement élastique donne un écart de pic de **1,9945 %** entre les deux maillages. Sur le maillage fin, le moment moyen à la prise droite autour de l'origine vaut 73,0743 N·mm selon y ; les déséquilibres moyens totaux sont 0,000160 N et 0,003240 N·mm. Le contrôle quasi statique des forces **et** moments passe. L'écart relatif de 39,8 % entre de minuscules énergies cinétiques élastiques, ≈3,4/5,7×10⁻¹⁰ J, reste affiché ; il n'est pas un critère de convergence d'un champ vibratoire.

### Bilans et portée

Maximum sur les 13 cas : résidu global énergétique **0,01144 %**, erreur de travail indépendant des prises **0,24665 %**, erreur de bilan d'impulsion **0,33943 %**. L'énergie globale inclut séparément énergie interne, cinétique de translation, cinétique de rotation et contact. La masse globale est conservée ; l'ajout maximal relatif, 2,3×10⁻¹⁵, est un arrondi, pas un mass scaling imposé.

Les moments des réactions sont présents. Le contrôle angulaire dynamique reconstruit seulement la partie **orbitale** du moment cinétique : le spin nodal n'est pas reconstruit. Son résidu maximal de 0,05284 % reste un diagnostic, **pas un bilan angulaire dynamique complet validé**. Après séparation les bandes vibrent : pour le cas fin, le déséquilibre moyen des réactions terminales est encore 84,8 N. Ce n'est pas un état d'équilibre statique final, et il n'est pas traité comme tel.

### Révisions et livrables

- R0/R1 : pilotes, ambiguïté de masse numérique et premier ordre de colonnes mal interprété ; conservés.
- R2 : épaisseur imposée 1 mm, incorrecte pour le bras de levier ; le coupon de cisaillement donne ≈74,95 % de résidu angulaire. La série en cours a été interrompue. Certaines cartes diagnostiques R2 ont été générées pendant des révisions du générateur ; leur contenu conservé fait foi, **aucune R2 n'est promue**.
- R3/R4 : clarifications de masse puis bras constant 2,5 mm ; ce dernier est encore incorrect si l'ouverture normale change. Deuxième série interrompue. R4 non proportionnelle conserve aussi l'ancien audit de reconstruction erronée.
- R5 : Imass=1 explicite, bras géométrique courant, état historique κ et d, aucune modification des pics, G ou tolérances. Chaque cas possède une copie complète de la configuration et l'empreinte du générateur.
- Avertissement 94 conservé et autorisé uniquement pour deux ensembles de coques disjoints : l'intervalle de contact dépasse une demi-arête ; la mise en garde concerne l'auto-contact. Il n'a pas été caché en réduisant artificiellement l'épaisseur. Aucun autre avertissement de solveur accepté.

Le MP4 de 6,2 s montre 31 états nodaux sauvegardés sans amplification, interpolations mécaniques ni images générées ; l'encodage répète ces images. Les repères verts/rouges sont des connexions distribuées, pas des rivets géométriques. Le PVD conserve les mêmes temps en ms et coordonnées en mm ; les fichiers VTU sont relus et comparés exactement. Les 31 animations natives, à des instants légèrement différents, sont recoupées avec les historiques (écart maximal 0,006688 mm dans la borne d'échantillonnage). Les images initiale, médiane, finale et une image décodée du film ont été inspectées.

Reproduction : configuration `impact_i02d_lap_joint.json`, scripts `run_impact_i02d.py` avec `--case <id_R0> --revision R5`, puis `summarize_impact_i02d.py`. Les dossiers existants sont protégés ; privilégier les audits des caches. Les scripts de présentation, transfert ParaView et vérification native sont également conservés. `release_audit.json` atteste la livraison et la préservation des contrôles antérieurs après inscription.

## 6. Informations manquantes, limites et suite

**Pas encore de validation physique des rivets, de fissuration du métal, de cisaillement de boulons explicites, de matage de trous ou de rupture de panneaux WTC.** La zone cohésive répartie est un choix de réduction. Les tôles restent élastiques même lorsque la liaison rompt ; le champ de contraintes n'a pas été qualifié comme champ d'un alliage Boeing. La loi de vitesse de déformation et les données expérimentales de travail de séparation restent absentes. Deux maillages ne prouvent pas une convergence asymptotique ; le bilan angulaire dynamique complet et le rebond libre après fermeture restent à vérifier.

I02E : brancher **une seule zone de liaison remplaçable** sur un petit tronçon peau–raidisseur extrait de la topologie I02A, comparer au témoin fusionné et à une référence sans rupture, vérifier la conservation masse/énergie/efforts et les offsets. Commencer par une courte fenêtre et arrêter si l'énergie supprimée ou le domaine des matériaux n'est pas maîtrisé. Une représentation distribuée ne doit pas multiplier la capacité d'un rivet par le nombre de cellules. L'impact de cette zone sur la façade vient ensuite, pas une animation d'avion entier présupposant son état.

I01/I02A/I02B/I02C, V11F froid et V11R thermique sont préservés par empreintes. La réserve I02C sur les vibrations ne disparaît pas. V11S reste différée. Le B762 graphique n'a aucun crédit mécanique. Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète toujours non validée ; aucune conclusion sur l'effondrement réel n'est tirée de ce lot.
