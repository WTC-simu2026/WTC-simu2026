# AIRCRAFT-A63 — dynamique libre exacte, convergence temporelle échouée

Les deux derniers contrôles autorisés du moteur A62 passent séparément les bilans physiques de dynamique libre et la solution Newmark discrète exacte. Leur comparaison demi-pas échoue : le déphasage temporel est encore trop grand. Aucun seuil modifié ni ancien échec effacé, aucun crédit d’impact entier.

## 1. Faits directement observés ou transcrits

Deux nouveaux Starter sans erreur/avertissement, deux Engine A62 CPU1/plafond180s/sansGPU, terminés normalement. La limite autorisée A61 est consommée : A62 dix Engine+A63 deux=12. Aucun ancien Engine rejoué, aucun patch/compilation supplémentaire. Une première préparation propre omettait un import de générateur, échouant avant Starter/Engine ; script/dossier/erreur conservés, dépendances importées, aucune entrée ni critère modifié.

Chaque essai passe22contrôles : canaux binaires/CSV, grille/pas/horloges natives, identité sécante, vitesse physique reconstruite, énergie cinétique et quantité de mouvement comparées aux compteurs natifs, conservation énergétique et impulsion des seuls supports, masse8g, masse ajoutée0, travail externe0, réponse analytique du ressort surfacique, tractions et domaine élastique. Erreur de déplacement analytique≤7,24e-10mm, vitesse≤2,35e-6mm/ms ; résidu énergétique≤8,82e-9J et quantité de mouvement/support≤1,10e-8Ns. Les sorties réelles atteignent1ms ; horloges ANIM/TH distinctes conservées.

Cependant KE et IE diffèrent jusqu’à0,00034846J entre les pas0,001 et0,0005ms, pour une tolérance déclarée1,01e-5J : les deux critères de comparaison échouent. Le composé global est FALSE, malgré les passages par cas.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Le moteur A62 inchangé conserve ses sources figées/correctifs précédemment autorisés. Le protocole Newmark gamma0,5/beta0,25 reconstruit les vitesses physiques depuis les sécantes TH sur les degrés réellement libres ; les compteurs natifs concordent ici, indépendamment des sorties sous mouvements imposés A62. La formule de phase exacte du schéma linéaire est utilisée comme référence mathématique, sans ajustement aux sorties :2atan(omega·dt/2).

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF consulté/modifié. Aucun dégât connu ciblé.

## 4. Hypothèses propres au modèle

Graine1102088, zéro tirage. Face10×10mm, matériau témoin A60/A62 conservé ; quatre nœuds supérieurs de1g libres, quatre inférieurs de1g fixes, vitesse initialeY1mm/ms. Aucun déplacement/vitesse imposé durant le calcul, travail externe nul. Raideur surfacique totale80000N/mm, masse mobile4g, omega=sqrt(80000/4)ms⁻¹. Le maximum de cisaillement reste sous le seuil élastique. Cette masse instrumentale et ces propriétés ne représentent pas l’avion réel et ne déterminent pas son futur pas de calcul.

## 5. Résultats dérivés

La branche native surfacique donne la bonne dynamique libre dans son domaine élastique, avec conservation vérifiée et réponse conforme au schéma discret. Elle ne démontre pas la convergence temporelle au pas courant. La dispersion exacte explique le déphasage cumulé sur1ms ; les seuils de comparaison restent inchangés. Une étude analytique détermine la première paire plus fine dont la borne de différence énergétique respecte cette tolérance :0,000125/0,0000625ms. Aucun matériau/masse/géométrie ajusté, aucune tentative native supplémentaire lancée au-delà de12. Les paramètres, scripts, références et anciennes sorties sont préservés, harnais PASS.

## 6. Contradictions et informations manquantes

Échec demi-pas conservé ; un accord supplémentaire est requis pour dépasser le lot de12contrôles accepté. Démarrage exact au repos et observables prescrits A62 restent échoués/non qualifiés. Retour arrière natif d’état, dommage général et grandes rotations non qualifiés. Aucun nouveau CHECK entier ou insertion A52. Ancien CHECK15erreurs/624volumes/cinqTYPE25 ignorés, budgets et critères locaux/matériaux échoués conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D restent incomplètes.

AIRCRAFT-A64 : douze Engine autorisés A61 consommés au total A62(10)+A63(2). Ne pas dépasser ce budget sans nouvel accord. Préparer puis demander un accord pour deux témoins libres raffinés dt0,000125/0,0000625ms, CPU1/cap180s chacun, sur le moteur A62 inchangé, sans compilation/GPU/installation ; si leurs critères passent, deux CHECK entiers bornés original/paireA53 avec les mêmes entrées, aucune extension dynamique. A63 chaque trajectoire libre concorde avec la solution Newmark discrète exacte et les bilans physiques K/P/support/IE ; maxrésidu énergie8,82e-9J, impulsion1,10e-8Ns. Mais comparaison demi-pas0,001/0,0005ms échoue : différence KE/IE~0,00034846J >tol1,01e-5J. Échec conservé ; dispersion temporelle théorique explique le déphasage, pas de modification du seuil. Le nouveau pas proposé vient de l’erreur du modèle analytique prédeclared, sans ajuster matériau/masse ni dégâts ; ne pas le transposer à l’avion puisque les masses instrumentales sont artificielles. A62 : correctif surfacique compilé, sixième moteur SHAd36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235. Démarrage au repos NaN/Infinity et observables imposés KE/P restent échoués/non qualifiés ; les variantes chargées passent traction/travail, pas une qualification entière. Trois régressions explicites297canaux bits identiques, deux TYPE7/MUMPS source énergie/momentum et demi-pas passent, échecs bruts conservés. CHECK entiercached15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré ; aucun nouveau CHECK ni extension. Budgets/anciennes sorties et critères préservés, aucun RKE compensateur. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. PublicationA62+A63 à vérifier, prochaine cadenceA64+A65. Toute future modification/compilation moteur supplémentaire demande un accord distinct sur une proposition concrète.
