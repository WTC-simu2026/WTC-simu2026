# AIRCRAFT-A64 — raffinement libre et contrôles entiers conditionnels

Composé local PASS=False. physical_KE : 3.563132993e-05 J, seuil 1.01e-05 J, PASS=False; native_IE : 5.4925e-06 J, seuil 1.01e-05 J, PASS=True. CHECK entier propre=False. Aucun crédit de temps physique pour l’impact entier.

## 1. Faits directement observés ou transcrits

2 nouveaux Engine sur le moteur A62 inchangé, un CPU, plafond180s chacun, sansGPU, installation ou compilation. Accord distinct «continue» du14octobre2026 sur la proposition de quatre contrôles maximum ; les douze anciens restent consommés. Deux Starter locaux propres ; sorties et messages natifs conservés. Chaque cas libre garde les22contrôles A63 et les mêmes seuils. physical_KE : 3.563132993e-05 J, seuil 1.01e-05 J, PASS=False; native_IE : 5.4925e-06 J, seuil 1.01e-05 J, PASS=True.

Le lecteur initial est inapplicable au second cas : TFILE0,0001ms dépasse le pas0,0000625ms, et6000pas intermédiaires manquent. Les calculs dérivés qui supposent une ligne par cycle restent sauvegardés comme échecs initiaux, sans les confondre avec une divergence physique. Une analyse séparée des cycles réellement enregistrés trouve déplacement analytique≤7,31e-10mm, compteurs KE/IE≤5,58e-10J d’écart à la solution exacte, conservation native≤6,01e-10J et impulsion/support≤2,21e-9Ns. Les différences des compteurs KE/IE entre pas, aux temps sauvegardés communs, passent le seuil inchangé. Cela ne répare pas l’absence du champ terminal complet à1ms et ne promeut pas la qualification globale.

Les CHECK entiers conditionnels ne sont pas exécutés car le composé local échoue.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Moteur OpenRadioss A62 figé SHA256 d36015d6238b5216ae7c5c4cbd909abb5c3cd7b25f724e6ef2faebc4814a4235, schéma Newmark gamma0,5/beta0,25 et reconstruction de vitesse sur degrés libres selon les sources déjà vérifiées. Aucun ancien diagnostic natif rejoué. Intégrité logicielle et publication ne prouvent pas la simulation physique entière.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo, photographie ou PDF consulté/modifié. Aucun dégât historique utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine1102089, zéro tirage ; oscillateur surfacique élastique10×10mm, masse instrumentale8g, quatre nœuds mobiles, vitesse initialeY1mm/ms et travail extérieur nul. Matériau, géométrie et masse identiques à A63. Seul le pas devient0,000125/0,0000625ms selon la borne de dispersion analytique. Ni masse ni propriété ajustée ; les masses instrumentales ne fixent pas le pas du futur avion entier.

## 5. Résultats dérivés

Les analyses libres suivent les canaux natifs binaires et CSV, la réponse Newmark discrète exacte, l’énergie physique et l’impulsion des seuls supports. Les différences temporelles sont évaluées avec le seuil préexistant, sans assouplissement. Les CHECK entiers, lorsqu’exécutés, vérifient les mêmes scènes originales et appariées sur le nouveau moteur ; ils ne sont pas une extension dynamique. Scripts, paramètres, messages et sorties sauvegardés ; budgets et anciens échecs préservés.

## 6. Contradictions et informations manquantes

Composé local=False, CHECK entier propre=False. Les échecs au repos et sous mouvements prescrits A62, l’échec temporel aux anciens pas A63, les domaines matériaux, inerties, grandes rotations, retour arrière natif et bilans locaux entiers restent ouverts. A52 non intégré. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes. Aucune seconde manquante fabriquée, aucun RKE compensateur.

AIRCRAFT-A65 : préparer les sorties TH à chaque pas et sauvegarder la frontière1ms, sans changement moteur, mécanique ou de seuil. Nouveau lot à autoriser : deux témoins puis deux CHECK entiers seulement si les critères passent. A64 deux Engine exécutés ; ses deux CHECK conditionnels non utilisés car le composé initial échoue. Préserver les défauts au repos et sous mouvements imposés A62, le critère temporel échoué A63, les budgets, anciennes sorties et tous les critères entiers ouverts. Objectif dix secondes physiques puis vidéo3D incomplet ; meilleur impact entier0,0200001220703125s. Une nouvelle modification ou compilation moteur exige un accord distinct sur une proposition prête.
