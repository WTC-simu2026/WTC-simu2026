# AIRCRAFT-A59 — prototype de surface et tangente active en modes purs

Un prototype propre utilisant l'aire de la surface passe112contrôles dans son domaine limité et concorde avec les quatre témoins explicites natifsA57 réutilisés. Il n'est ni une implémentation complète deLAW117 ni un correctif intégré au moteur. Aucun nouveau calcul Engine, aucune compilation, aucun temps physique d'impact entier supplémentaire.

## 1. Faits directement observés ou transcrits

Exécution Python propre, CPU1/sansGPU, plafond120s, résultats en moins d'une seconde.92contrôles initiaux passent, puis20contrôles additionnels répondent aux questions de rotation arbitraire3D et de courbe entière de travail/rechargement. Les quatre fichiers natifs en cache sont vérifiés par empreintes, aucun solver rejoué. Vérifications :équilibre nodal, translations nulles, matrice élastique d'intégrale fermée, rang12, spectre élastique non négatif, pente active négative en adoucissement, différences finies de la tangente active, covariance des forces/matrices sous rotation, traction native, travail de séparation, dommage irréversible et retour au même pic.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel ou solveur tiers exécuté. Les sources figéesSIGEPS117/SUSER43 indiquent une loi de traction surfacique et ses états internes ; SUSER43 décritSTIFM comme une surestimation destinée au pas de temps explicite. Il ne s'agit pas de sa tangente cohérente. Les branches mixtes et variablesUVAR deSIGEPS117 restent à transférer avec un traitement d'état correct avant tout patch natif.

## 3. Affirmations provenant des archives locales

Aucune archive historique, image, vidéo ouPDF consulté ou modifié. Aucun objectif de dégâts connus.

## 4. Hypothèses propres au modèle

Graine1102084, aucun tirage. Deux faces planes rectangulaires à hauteur nulle, quadrature2×2, repère de référence fixe. Le résidu est l'intégrale surfacique des tractions, la matrice active leur dérivée. Paramètres témoinsA17 conservés :EN4400N/mm³,ET800N/mm³,TN450MPa,TT100MPa,GI/GII50N/mm ; valeurs de référence sans fracture historique mesurée. Les modes purs normaux/cisaillement utilisent une enveloppe bilinéaire et un maximum irréversible. Les directions passives gardent ce dommage gelé : aucun couplage mixteLAW117 n'est qualifié. Les quatre points de Gauss partagent une histoire uniforme seulement dans les témoins en cache.

## 5. Résultats dérivés

Le noyau surfacique possède une rigidité non nulle sans volume fictif, avec équilibre et travail contrôlés dans ce domaine. Les différences finies actives et la matrice analytique donnent des références indépendantes pour une future connexion au moteur. Les seuils de traction, travail et rechargement sont ceux d'A17, inchangés. Aucun budget mécanique, masse, matériau ouRKE n'est modifié.

Un rappel ciblé de sortiesA20 déjà vérifiées conserve ses limites :1191,4197075s pour20ms, projection linéaire ancienne6,89479jours pour10s, explicitement pas une ETA actuelle. Cette ancienne scène ne modélisait ni gravité ni intérieur porteur et restait hors domaine sur plusieurs critères. Son fichier de route interdisait sa prolongation ; aucune prolongation ou répétition exécutée et aucune lacune déduite pour une scène plus récente non inspectée. Préservation par métadonnées/manifestes antérieurs, empreintes des fichiers natifs utilisés, harnaisPASS.

## 6. Contradictions et informations manquantes

Modes mixtes, repères mobiles, tangente géométrique, état d'essai/retour arrièreNewton et assemblage natif ne sont pas qualifiés. Le prototype passe ses propres contrôles mais ne valide pas l'impact entier. Les critèresA57/A58 restentéchoués : cohésion implicite àT=0, CHECK entier15erreurs/624volumes et cinqTYPE25 ignorés. A52 non intégré ; bilans locaux, domaines de matériau et autres travaux/inerties entiers restent ouverts. Meilleure fenêtre entière0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. Tout futur correctif logiciel demandera une proposition concrète et un accord explicite distinct avant application/compilation.

AIRCRAFT-A60 : prototype propre de surface A59 disponible dans surface_aircraft_a59.py,112contrôles passent dans le domaine déclaré. Compléter et qualifier les modes mixtes selon SIGEPS117, états d’essai et validation/retour arrière de Newton, repères mobiles et tangente géométrique avant une différence moteur concrète. Le noyau A59 couvre plans rectangulaires, matrice élastique3axes et tangente ACTIVE de modes purs normaux/cisaillement à adoucissementlinéaire. Les directions passives gardent le dommage gelé ; cela ne qualifie pas le couplage mixte de LAW117. 112tests :équilibre,intégralefermée, rang12 et translationsnulles, différencesfinies de tangente, adoucissement négatif, rotations de repère3D, quatre témoinsnatifsA57 réutilisés sans rerun, travail et rechargement. SUSER43 décritSTIFM comme surestimation pour le pas explicite ; ne pas l’assimiler à une tangente implicite cohérente. Aucun patch moteur proposé/appliqué ou compilationA59, zéro nouveau Engine/Starter ; toute future modification/compilation moteur exige un accord explicite distinct après proposition concrète. Moteur A57 conservé34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528 ; mémoire du témoin corrigée, mais STOP de jacobienvolumiqueTYPE43 reste. A58ordre natif surface puis rigidité volumique connu, ne pas le rejouer. CHECKentier15erreurs/624volumes/cinqTYPE25 ignorés, A52nonintégré, budgets/critèreséchoués conservés. Meilleur impact entierA20=0,0200001220703125s ; ne pas prolonger cet état horsdomaine vers10s. Coût historiqueA20=1191,4197075s pour20ms, projection linéaire6,89479jours pour10s est seulement un ordre de grandeur ancien, pas une ETA ni une autorisation d’extension. A20 ne modélisait pas gravité/intérieurporteur et ses critèreslocaux/matériaux échouaient ; aucune extrapolation de ces lacunes à une nouvelle scène sans inspection. Objectif1 dix secondes physiques puis vidéo3D incomplet, aucun crédit des témoins ou prototype. PublicationA58+A59 à vérifier, ensuite cadenceA60+A61. Aucun ancien solver rejoué.
