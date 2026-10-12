# AIRCRAFT-A45 — contrôles natifs réussis ; calcul entier accéléré à corriger

L’accès WSL est rétabli. Le moteur séparé construit A44 passe quatre contrôles de liaisons LAW117 et deux collisions élastiques avec MUMPS. Le modèle entier démarre en explicite avec sa reprise inchangée. Son contrôle implicite avorte pendant l’assemblage de raideur et signale cinq contacts TYPE25 ignorés. Cette réussite logicielle limitée ne prolonge pas encore les20ms de l’impact entier.

## 1. Faits directement observés ou transcrits

Jeremy confirme le rétablissement de WSL ; un contrôle frais retourne0. Huit processus Engine nouveaux utilisent le binaire A44 SHA256871dc6c9f154173eb4148b95cdfeed3e485735d64eb48957722b3588e319730a : quatre LAW117, deux contacts TYPE7, démarrage entier et CHECK entier. Sept terminent normalement avec code0 ; le CHECK termine avec code3. Chaque processus est borné180s, un thread CPU, sans GPU. Aucun nouveau paquet ou compilation, aucun ancien solveur Windows/Linux relancé.

Les états initiaux et cartes Engine des références A17/A41/A37 sont copiés intégralement et vérifiés par SHA256 avant calcul. Aucune injection de CSV ou modification de reprise. Les quatre refus de lancement A44 restent conservés et ne sont pas reclassés en succès.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle officiel historique. Le moteur de calcul est issu de la source figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Les six routines définissant l’intégration et la sortie des vitesses sont byte-identiques aux sources déjà vérifiées A41. La vitesse sécante publiée est donc interprétée avec la même dérivation Newmark, à pas fixe, tous les cycles enregistrés, et contrôles indépendants de déplacement, KE et quantité de mouvement. Aucun facteur ajusté ou nouveau terme RKE.

- [Source LAW117 figée](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/materials/mat/mat117/sigeps117.F)
- [Intégrateur figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/integrator.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle vidéo, photographie ou archive historique analysée. Les documents sources restent en lecture seule. Aucun dégât observé n’est utilisé comme cible de réglage.

## 4. Hypothèses propres au modèle

Graine1102070, zéro tirage. Les quatre témoins LAW117 gardent EN4400N/mm³,ET800N/mm³,TN450MPa,TT100MPa,GIC/GIIC50N/mm ; ces valeurs sont des hypothèses numériques non mesurées pour l’avion. Les8g instrumentaux de ces témoins restent distincts du budget avion. Les collisions TYPE7 reprennent deux cubes élastiques1mm,54nœuds,16briques,masse0,00556g et vitesses±5mm/ms. Leurs pas sont6,25e-6 et3,125e-6ms jusqu’à0,015ms, γ0,5/β0,25, MUMPS2 ; ils ne représentent pas un avion ou une tour.

Les critères A17/A41 sont inchangés. Les écarts littéraux de texte temps/coordonnées restent dans les revues brutes. Une revue distincte applique les bornes float32 et six chiffres significatifs préexistantes A23/A41 ; elle ne modifie ni les champs natifs ni les seuils physiques. Un premier lecteur comparant les noms de colonnes entre versions s’arrête : l’ancien moteur ajoute une colonne non identifiée NO NAME et décale les indices numériques. Script et échec sont conservés. Le lecteur final compare toutes les colonnes physiques nommées, les composantes nodales/contact selon l’ordre des cartes inchangées ; NO NAME reste explicitement non comparée.

## 5. Résultats dérivés

Les quatre LAW117 passent les14contrôles chacun, le demi-pas et la normalisation par aire. Travail final50N/mm, soit5J pour10mm et20J pour20mm. Erreur maximale de traction0,1199% ; résidu énergie maximal1,065e-5J. Les références Windows en cache et les nouveaux calculs Linux passent les mêmes critères analytiques ; aucune identité de leurs trajectoires complètes n’est supposée.

Les deux contacts MUMPS passent les14contrôles physiques interprétés selon la source. Résidus énergétiques4,213e-8 et1,044e-8J, sous le seuil1,49e-6J. Les écarts au demi-pas en KE/IE/énergie de contact restent sous4,475e-7J. Les600champs passent la vérification de format indépendante. Toutes les histoires physiques nommées concordent exactement à la précision sauvegardée avec A41 ; la colonne NO NAME non identifiée reste hors comparaison.

Le modèle entier explicite termine3cycles avec ses624liaisons LAW117 inchangées. Il franchit ainsi l’ancienne panne de lecture A42. La carte demande seulement1e-5ms ; aucun crédit de durée n’est ajouté aux20ms A20. Le CHECK entier affiche cinq avertissements TYPE25 puis avorte avant son compte rendu, avec une trace ASSEMC_KIJ→ASSEM_C4→CBAKE3→IMP_GLOB_K0→IMP_CHKM. L’arrêt d’assemblage et les contacts ignorés sont deux observations distinctes ; leur lien causal n’est pas établi.

## 6. Contradictions et informations manquantes

La cause précise d’assemblage entier reste inconnue. Ignorer cinq contacts ne peut fournir le même impact ; aucune dynamique entière implicite n’est acceptée. Les624liaisons mobiles, autres formulations d’éléments, RBE, réactions, domaines locaux d’énergie, matériaux et assemblages ne sont pas qualifiés par ces témoins uniformes. Rupture mixte, paramètres mesurés, structure intérieure et gravité restent à traiter. A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués.

Le meilleur impact entier reste0,0200001220703125s. Les dix secondes physiques et leur vidéo3D restent incomplètes. Ni un temps de témoin ni une vidéo ralentie ne remplissent cet objectif. L’intégrité des archives n’est pas une validation physique ou historique.

AIRCRAFT-A46 : le moteur antérieur871dc6c9f154173eb4148b95cdfeed3e485735d64eb48957722b3588e319730a est désormais qualifié pour les quatre témoins uniformes LAW117 et le contact direct TYPE7 aux deux pas A41 les plus fins. Ne pas reconstruire ou refaire ces témoins. Le démarrage entier explicite inchangé réussit ; l’incompatibilité de lecture LAW117 A42 est résolue. Le CHECK entier avorte dans ASSEMC_KIJ via ASSEM_C4/CBAKE3/IMP_GLOB_K0/IMP_CHKM, et signale séparément cinq TYPE25 ignorés. Inspecter les routines et les familles d’éléments dans les sources/entrées en cache pour isoler le contrat de raideur qui échoue ; ne pas attribuer automatiquement cet avortement aux contacts. Déclarer un témoin représentatif puis une variante entière portant sur une seule famille, avec bilans et comparaison explicite séparés, avant toute accélération. Aucune substitution silencieuse de TYPE25, matériau, masse, inertie, RBE ou reprise. Conserver toutes les tentatives et critères initiaux échoués. Les contrôles de format coordonnées/temps utilisent les bornes A23/A41 préexistantes, sans injection dans le solveur. A40 reprise chargée/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entier A20=0,0200001220703125s ; aucun crédit du micro-démarrage ou des témoins. Vérifier les domaines entiers, structure intérieure et gravité avant les secondes suivantes. L’objectif dix secondes physiques3D puisMP4/GIF demeure actif et incomplet. Publier A44+A45 avec échecs conservés selon autorisation existante, puis avancer A46.
