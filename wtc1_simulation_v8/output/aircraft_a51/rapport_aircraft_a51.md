# AIRCRAFT-A51 — labels vérifiés et piste des interfaces croisées

Les messages CHECK identifient déjà les labels d’entrée : leur interprétation initiale comme indices internes est rejetée. Leur classement corrigé situe37165messages entre ensembles TYPE2distincts. La source laisseNMC2à zéro ; cette piste demande un reproducer avec deux interfaces sur le même noyau. Aucun solveur relancé et aucun temps d’impact supplémentaire.

## 1. Faits directement observés ou transcrits

Réemploi du fichier natif à temps zéro A50, produit depuis exactement le même état initial que CHECK A49, vérifié par SHA256. Pour un domaineSPMD, XYZNOD écrit X(:,I) dans l’ordre interne et GENANI écritITAB dans le même ordre. Les48171labels sont uniques et couvrent toute l’entrée. Les302correspondances IXC/X directement capturées en A49 confirment cet ordre.

Le texte VTK échoue au seuil0,003mm : arrondi maximal0,05mm. L’échec et le lecteur original sont conservés. Un lecteur propre, limité au fichier natifv44figé, lit les coordonnées float32 avant cet arrondi ; erreur maximale0,0016741500003263354mm, sous le même seuil. Format vérifié depuis les écrivains de la source figée : en-tête, titres81octets, compteurs, repères six entiers16bits puis coordonnées. Aucun convertisseur, moteur ou fichier natif modifié.

Deux corrections de lecteurs sont aussi conservées dans des versions distinctes : clés de métadonnées native_element/source_nodes, puis exclusion des directions réelles de poutres du lecteur des surfaces coque/solide. Aucun critère physique ajusté et aucun calcul relancé.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les appels TYPE2/RBE2 à PRINT_WKIJ passentITAB(NI)/ITAB(NJ). Le diagnostic de raideur imprimeITAB(I). Les nombres du listing sont donc déjà les labels originaux ; observer seulement le sous-programme d’impression ne suffisait pas. L’ancienne classification entière en indices internes est conservée comme interprétation rejetée, séparément du vrai tableau d’indices/labels qui reste valide.

IND_KINE_K traite chaque TYPE2 et ses couples secondaires internes, puisRBE2. Son seul affectateurNMC2estNMC2=0, sous un commentaire de couplage entre interfaces. Cela suggère une piste de fermeture du graphe, sans établir à lui seul la cause des blocs manquants.

- [Appels TYPE2, source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/interfaces/interf/i2_imp1.F)
- [Appels RBE2, source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/constraints/general/rbe2/rbe2_imp0.F)
- [Graphe des contraintes, source figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/ind_glob_k.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, photographie, vidéo ou PDF inspecté. Archives en lecture seule ; aucun dégât connu utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine1102076, zéro tirage. Lire seulement l’entrée A49, ses listings et les états/captures existants. RôlesRBE2exacts ; pourTYPE2, l’ensemble des nœuds de surface est un ensemble potentiel de parents. PourRBE3, le groupe support ne remplace pas la matrice interpolatoire native. Une appartenance de surface ne prouve pas une facette ou un coefficient réellement choisi. Ces graphes ne prouvent ni conflit mécanique ni mécanisme historique.

Hypothèse suivante : une partie des blocs manquants concerne les interactions entre deux TYPE2opposés liés au même noyau3D, interaction absente des petits cas A49. Un test de la dernière facette216doit copier ses deux peaux, noyau, cellules cohésives, RBE2déportés et TYPE2originaux16430/16431. Un regroupement éventuel est seulement une variante diagnostique ; ses facettes, coefficients et déports natifs doivent être comparés avant tout transfert entier.

## 5. Résultats dérivés

Les49370messages correspondent à20483paires ordonnées en comptant les familles séparément. TYPE2 :37165messages relient des ensembles déclarés distincts,11831ont au moins une interface commune. Les374messagesRBE2relient des nœuds de peau principaux RBE2et des secondaires de racines rigides. Le classement corrigé ne relie aucun message directement à RBE3.

Les15directions suspectes appartiennent aux labels originaux99,103,107,109,111,119, références de racines rigides. L’ancienne conversion erronée les attribuait à des nœuds de noyau428xx ; cette attribution est explicitement rejetée. Les valeurs négatives parfois extrêmes restent un diagnostic d’assemblage non qualifié, pas une preuve d’instabilité physique.

Les3024nœuds secondairesTYPE2 et5136secondairesRBE2 sont uniques et disjoints ; aucun ne partage le rôle de référence dépendanteRBE3. Aucune double contrainte secondaire déclarée. Au total96TYPE2ont des parents de surface potentiellement déjà secondairesRBE2. Leur interpolation exacte et leur fermeture native restent à vérifier.

## 6. Contradictions et informations manquantes

La cause complète n’est pas prouvée. Le défaut de graphe reste réel : PUT_KIJretourne sans ajouter un bloc absent. Les cinq petits reproducer A49 ne contenaient pas cette interaction complète à deuxTYPE2. Ils ne réfutent pas la piste actuelle. Changer /IMPL/SOLVERseul pendantCHECKest neutralisé par les contrôles forcés établis enA50 ; aucune variante inutile exécutée.

A49 :15erreurs mécaniques et cinqTYPE25ignorés en implicite. A50 : bilans et mouvements initiaux identiques à la référence, mais seulement20ns, sans qualification sous charge ou en rotation. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF toujours incomplètes. Aucune suppression de contrainte, compensation de masse/inertie, modification de moteur ou impact implicite avec contacts ignorés.

Toutes les interprétations rejetées et les tentatives de lecteurs sont conservées. Sorties antérieures intactes, audit tailles/dates et manifestes existants ; empreintes des entrées utilisées recontrôlées, sans nouvelle lecture complète des anciens résultats. Rapport, sorties et harnaisPASSprécèdent l’enregistrement.

AIRCRAFT-A52 : créer un reproducer complet de la dernière facette216, à partir de l’entrée réelle A20/A49 : deux faces de peau, noyau3D, cellules cohésives et RBE2déportés, deux TYPE2originaux16430/16431. A51 corrige les labels du listing : les appels PRINT_WKIJ reçoiventITAB(N), donc les nombres imprimés sont déjà des labels originaux ; les anciennes classifications inverses sont rejetées et conservées. Les15directions suspectes appartiennent aux racines99/103/107/109/111/119. Les49370messages sont répartis en20483paires ordonnées ;37165TYPE2 relient des ensembles TYPE2distincts,11831ontau moins un TYPE2commun ;374sontRBE2. Aucune double contrainte secondaire,96interfaces ont des parents potentiellement dépendants. La sourceIND_KINE_K laisseNMC2=0 et construit les couples secondaires à l’intérieur de chaque TYPE2 avantRBE2. Tester l’interaction réelle de deux TYPE2au travers du même noyau, absente des petits reproducer A49. Comparer ensuite une variante groupée seulement si les facettes principales, coefficients natifs et déports restent équivalents ; ne pas assimiler un groupe de surface potentiel aux vrais poids. Aucun changement entier implicite, ajout de masse/inertie, patch logiciel ou ajustement historique. Coordonnées natives48171nœuds vérifiées au seuil0,003mm : erreur0,00167415mm ; la sortie texte arrondie0,05mm reste rejetée. Les302correspondances natives sont confirmées ; aucun nouveau Engine enA51. CHECKforcéPCG/IPREC5, contactsTYPE25ignorés et15erreurs restent ouverts. A40 chargé/croissance, A34 peaux et A36 raffinement échoués. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF actives et incomplètes. Publier A50+A51 puis poursuivre A52.
