# IMPACT-I02E — premier contact local peau–raidisseur contre une colonne

14 septembre 2026. **Lot numérique borné terminé : 8 cas R9, audités sous la politique R10, 129 contrôles de cas et 13 contrôles de campagne, PASS.** Les huit calculs acceptés cumulent 91,687 s. Les essais préparatoires R0 à R8 sont conservés mais ne sont pas promus.

Le résultat utile est circonscrit. Entre 0 et 0,35 ms, un petit caisson d'aile idéalisé de 1,980 kg heurte à 198,03072 m/s une courte colonne fermée représentative. Les références fusionnée, cohésive non rompable et cohésive rompable reçoivent pratiquement la même impulsion globale, environ 124,68 N·s. En revanche, la liaison rompable atteint un déplacement relatif nodal global maximal de 0,316 mm contre 0,160 mm pour la liaison non rompable. Aucune cellule cohésive n'est supprimée dans cette fenêtre.

**Ce résultat ne montre pas qu'une aile réelle reste intacte.** La rupture des coques métalliques est désactivée et la peau atteint localement une déformation plastique équivalente maximale d'environ 1,22. Le calcul s'arrête avant toute réponse tardive qualifiée. Il ne contient ni Boeing 767 complet, ni carburant, ni moteur, ni façade multi-colonnes, ni étage, ni rupture métallique calibrée.

## 1. Faits directement observés ou transcrits

- Les huit cas acceptés terminent normalement dans OpenRadioss. Les deux vols libres conservent exactement la vitesse uniforme, sans énergie interne, force de liaison ni force de contact.
- Le modèle 12,7 mm compte 6 229 nœuds et 6 096 coques ; les interfaces cohésives ont 32 cellules. Le raffinement 6,35 mm compte 24 489 nœuds, 24 224 coques et 128 cellules cohésives.
- La masse globale de référence est 47 061,15 g, dont 1 979,8195 g de coques du caisson et 0,516128 g de masse numérique déclarée pour l'interface. Aucun mass scaling dynamique n'est appliqué et la masse reste constante.
- L'énergie cinétique initiale mesurée est 38 830,58 J, contre 38 830,5859 J calculés à partir de la masse et de la vitesse.
- Trente états natifs par variante ont été exportés. Les coordonnées, déplacements, topologies et positions des nœuds de liaison ont été recoupés avec les historiques. Aucun élément de coque n'est érodé, puisque ce mécanisme est désactivé.
- Au maillage 6,35 mm, l'avertissement 477 du contact est conservé. Il est accepté uniquement après vérification que les ensembles de nœuds aile et façade sont disjoints ; il signale une réserve d'auto-contact, pas une validation du contact tardif.

Documentation primaire du solveur : [LAW117](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm), [TYPE43](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm), [liaison TYPE2](https://help.altair.com/2022/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r_2.htm) et [masse ajoutée ADMAS](https://2023.help.altair.com/2023/hwsolvers/rad/topics/solvers/rad/admas_starter_r.htm). Elles décrivent les cartes numériques employées, pas la construction exacte d'un Boeing 767.

## 2. Résultat provenant d'un modèle officiel

La seule donnée officielle directement réutilisée ici est la vitesse de 443 mph, soit 198,03072 m/s, mise en cache depuis le tableau 7-3 de NIST NCSTAR 1-2B pour AA11. Elle n'est pas estimée à partir d'une vidéo. Aucune forme de dommage NIST, trajectoire postérieure, carte de rupture ni quantité de débris n'est utilisée comme cible d'ajustement.

La section de colonne et les matériaux sont hérités des approximations I01/I02A. Ils ne sont pas présentés comme la plaque exacte de la colonne effectivement heurtée, et le caisson ne reproduit pas les stations de nervures ou les joints de production de l'avion.

## 3. Affirmations provenant des archives locales

Aucune nouvelle affirmation historique ou visuelle n'est introduite. Les vidéos de l'utilisateur ne servent ni à régler le contact, ni à décider à l'avance qu'une aile doit se rompre ou rester entière. Une apparence vidéo et une réponse de ce petit sous-modèle ne permettent pas d'identifier un mécanisme historique.

## 4. Hypothèses propres au modèle

### Unités, géométrie et conditions aux limites

Unités du solveur : g, mm, ms, N et MPa. Ainsi, 1 mm/ms = 1 m/s, 1 N·mm = 0,001 J et 1 N·ms = 0,001 N·s.

| Élément | Définition I02E |
|---|---|
| Colonne de façade | caisson fermé 355,6 × 355,6 × 508,0 mm ; coque de 7,9375 mm |
| Appuis de colonne | extrémités haute et basse fixes ; aucun panneau voisin, allège, plancher ou compliance globale |
| Caisson d'aile | 203,2 mm de portée × 304,8 mm de corde × 101,6 mm de hauteur |
| Structure du caisson | deux peaux de 2,54 mm ; deux longerons et deux nervures de 3,175 mm ; un raidisseur supérieur en Z de 3,175 mm |
| Position initiale | nez local à z = 50 mm de la face idéale ; vitesse normale −198,03072 mm/ms |
| Contact | TYPE7 unidirectionnel, sans frottement ; nœuds de l'aile contre coques de colonne |
| Fenêtre | 0,35 ms ; historique de 0,001 ms ; 30 états natifs effectivement écrits |

Le temps géométrique idéal pour parcourir 50 mm est 0,252486 ms. Le contact échantillonné commence vers 0,221034 ms au maillage 12,7 mm et 0,225014 ms au maillage 6,35 mm, car l'algorithme agit à travers son intervalle de contact et les épaisseurs de coque. Cet instant n'est pas une preuve de pénétration physique anticipée.

### Matériaux

| Pièce | ρ (g/mm³) | E (MPa) | ν | Plasticité employée |
|---|---:|---:|---:|---|
| Colonne, acier représentatif | 0,00786 | 200 000 | 0,30 | limite 427,656 MPa ; référence LAW2, rupture désactivée |
| Peaux, référence 2024-T3 | 0,00278 | 73 100 | 0,33 | élastique parfaitement plastique à 310,264 MPa |
| Longerons, nervures, raidisseur, référence 7075-T6 | 0,00281 | 71 700 | 0,33 | élastique parfaitement plastique à 503,32 MPa |

Ces affectations n'ont ni écrouissage, ni dépendance à la vitesse, ni courbe de rupture, ni régularisation énergétique du métal. Elles ne sont pas des allowables de production ni une carte matériau Boeing qualifiée.

### Liaison peau–raidisseur

La bande fait 203,2 × 25,4 = 5 161,28 mm². Le proxy I02D de référence est défini sur 254 mm² ; I02E répartit donc **20,32 aires de référence** sur la bande. Cela donne, avant tout endommagement, des capacités nominales agrégées de 231 485 N en normal et 132 649 N en tangentiel. Ce facteur est un étalement surfacique, **pas un nombre de rivets** et pas une identification de joint Boeing.

- déplacement d'initiation supposé : 0,02 mm ; séparation complète supposée : 0,5 mm ;
- décalage entre surfaces moyennes : (2,54 + 3,175)/2 = 2,8575 mm ;
- formulation rompable : LAW117 / TYPE43, Imass=1, Idel=4, Irupt=2, exposants B=2 et BK=1, γ=1 ;
- référence non rompable : même rigidité initiale, mais initiation à 10 mm et séparation à 100 mm, donc hors fenêtre ;
- référence fusionnée : liaison cinématique TYPE2 ; la même masse numérique est réintroduite par deux demi-masses ADMAS afin de comparer des masses égales.

La masse surfacique numérique de base vaut 10⁻⁴ g/mm², soit 0,516128 g pour la bande ou 0,0261 % de la masse des coques d'aile. Un témoin à 10⁻⁵ g/mm² est calculé. Cette masse stabilise le pas de temps ; elle n'a aucun crédit matériel.

## 5. Résultats dérivés et contrôles

### Comparaison principale à 12,7 mm

| Variante | Impulsion finale (N·s) | Travail de liaison maximal (J) | Déplacement relatif nodal global maximal (mm) | Fraction active minimale |
|---|---:|---:|---:|---:|
| Fusionnée | 124,6856 | 0 | 0,1292 | sans objet |
| Cohésive non rompable | 124,6892 | 2,2467 | 0,1602 | 100 % |
| Cohésive rompable | 124,6795 | 4,8881 | 0,3158 | 100 % |

Les écarts d'impulsion rompable/fusionnée et rompable/non rompable sont respectivement −0,0049 % et −0,0078 %. Ils sont très inférieurs au résidu énergétique maximal d'environ 4,36 % de ces cas : **I02E ne distingue donc pas les trois lois par l'impulsion globale pendant cette fenêtre**. La différence locale de déplacement est visible, mais le champ local n'est pas convergé et la rupture métallique absente empêche d'en faire une conclusion d'intégrité.

Le « déplacement relatif nodal global » est la distance relative complète entre lignes de nœuds opposées ; il comprend translation, rotation et offset. Ce n'est pas une ouverture cohésive pure. Le travail de liaison est issu de l'énergie interne de la pièce cohésive. Le champ d'animation nommé dommage reste nul, mais il n'est pas traité comme qualifié sans réconciliation constitutive indépendante.

### Bilans et sensibilités

- Résidu énergétique maximal accepté : 4,4672 % sur le demi-pas ; 4,3582 % sur les trois comparaisons principales ; seuil préalable 5 %. Cette proximité impose de ne pas lire les petites différences comme précises.
- Énergie hourglass maximale : 0,0975 % de l'énergie cinétique initiale, sous le seuil de 2 %.
- Les bilans impulsion contact/aile et appuis/système passent les tolérances de 3 % et 5 % pour chaque cas.
- Demi-pas : écart d'impulsion 0,2483 %, de travail 0,1949 %, de déplacement relatif maximal 0,4704 %.
- Masse numérique divisée par dix : écart d'impulsion 0,000321 %, de travail 0,3242 %, de déplacement 0,0446 %.
- Raffinement 12,7 → 6,35 mm : écart d'impulsion 2,0542 %, de travail 2,5245 %, mais **14,0924 %** sur le déplacement relatif maximal. Un seul raffinement qui passe les deux critères globaux ne démontre pas une convergence asymptotique.
- Aucune cellule cohésive n'est supprimée à 12,7 ou 6,35 mm avant 0,35 ms. Cela signifie seulement que ce proxy de liaison ne franchit pas son critère de suppression dans cette fenêtre.

### Diagnostic des révisions conservées

- R0/R1 : modèles d'une hauteur d'étage, avec hauteur cohésive nulle puis finie ; tous deux trop lents. Aucune causalité n'est attribuée à la hauteur nulle.
- R2 à R4 : réduction progressive du diagnostic ; vitesse nulle sans disparition du très petit pas.
- R5 : impression à chaque cycle ; pas constant mesuré de 3,3674×10⁻⁹ ms, causé par l'ancienne masse surfacique numérique de 10⁻¹² g/mm².
- R6 : première masse stabilisée, rejetée parce que la pièce de connexion n'avait pas reçu la vitesse initiale et vibrait avant contact.
- R7 : rejetée parce qu'une rangée intermédiaire de nœuds cohésifs n'appartenait pas aux coques de peau.
- R8 : topologie corrigée. Le maillage 25,4 mm termine mais dépasse le seuil énergétique de 5 % ; le demi-pas confirme une origine spatiale. Le cas 12,7 mm passe et devient la base R9.
- R9 : huit calculs finaux. R10 ne change aucun calcul ; il documente seulement l'acceptation conditionnelle de l'avertissement 477 lorsque les ensembles de contact sont disjoints.

### Visualisation 3D vérifiée

Le film comparatif de 6,0 s juxtapose les trois variantes principales. Il encode 30 états natifs par variante en répétant les images à 30 images/s ; il n'interpole aucun état mécanique. Les temps correspondants diffèrent au maximum de 0,003 µs entre solveurs. La projection est orthonormale, l'amplification des déplacements vaut 1 et la caméra reste fixe.

Les fichiers VTK/PVD conservent les coordonnées en mm et les temps en ms. Les repères verts sont les cellules d'interface distribuées, pas des rivets géométriques. Le rendu montre les surfaces moyennes des coques ; il n'ajoute ni rupture, ni trajectoire, ni mouvement postérieur. Blender n'est pas employé dans I02E.

## 6. Ce que le calcul permet — et ne permet pas — de dire

I02E établit qu'un premier contact explicite peut être calculé de manière stable sur une petite zone structurée, avec trois traitements de liaison, des masses comparables, des vols libres, des bilans de quantité de mouvement, un suivi énergétique et deux niveaux de maillage. Dans ce problème précis, l'impulsion initiale est contrôlée surtout par le contact et la déformation globale locale, pas par la suppression de la liaison, qui n'arrive pas avant l'arrêt du calcul.

I02E **ne reproduit pas l'observation d'un avion entrant « en entier »**, ne teste pas la rupture d'une aile complète et ne permet pas de choisir entre récit officiel, anomalie vidéo ou hypothèse holographique. Une aile réelle peut se fragmenter, se déformer et continuer à transporter de la quantité de mouvement ; les termes « intacte » et « disparue » exigent des critères mesurables, un modèle de rupture et des données vidéo analysées séparément. L'absence de suppression d'une liaison dans un caisson de 1,98 kg n'est ni une validation ni une réfutation de la pénétration historique.

La forme finale affichée est déjà hors domaine de confiance du métal simplifié : εp équivalente maximale ≈1,22 dans la peau, ≈0,294 dans les longerons et ≈0,991 dans les nervures. Sans critère de déchirure régularisé, prolonger le film fabriquerait une « aile intacte » numériquement artificielle.

## 7. Suite proposée : IMPACT-I02F

Avant d'allonger la séquence ou d'ajouter une aile entière, construire un coupon borné de déchirure de tôle 2024-T3 et un contrôle 7075, avec : données primaires ou plage explicitement hypothétique, histoire de plasticité, travail externe, énergie de fracture, dépendance au maillage et longueur de régularisation. Aucune déformation de rupture arbitraire ne doit être injectée directement dans I02E.

Après qualification minimale, remplacer **une seule zone de peau** du même caisson par cette loi, conserver les témoins froids R9/R10 et recalculer 12,7 puis 6,35 mm. Ce n'est qu'ensuite qu'une fenêtre plus longue, l'auto-contact/edge contact et une géométrie plus large pourront être étudiés.

Les branches I01 à I02D, V11F froid et V11R thermique restent inchangées. Température imposée ≠ incendie calculé ; localisation en flexion après fracture complète toujours non validée ; visualisation 3D ≠ validation mécanique du Boeing ou de l'effondrement réel.
