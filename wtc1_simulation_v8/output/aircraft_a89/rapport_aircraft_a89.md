# AIRCRAFT-A89 — correction imposée non nulle, correction libre nulle

## 1. Faits directement observés ou transcrits

Accord « Oui, exécuter l’observation A89 », receipt request_user_input_async/call_983cb4f571c74eff9c7f88cff44ed49d/0 ; publication A86+A87 vérifiée. Un EngineA87 inchangé,CPU1/plafond180s, zéroStarter/correctif/compilation/GPU/installation. Durée5.404s,19arrêts matériels. Lecteur code0, Engine code2 sans signal ; observation réussie et calcul physique échoué restent distincts.

Second essai réellement observé :NCYCLE2,TT0,00025ms. ModesIDYNA2,IQSTAT0,INSOLV1,NITOL123,ISPRB0,IDTC1,ILAST0,NFXVEL4,NINTER0,IRODDL0,NSPMD1,NTHREAD1,IMCONV0,ICONT0,NDDL8. F libre contient huit zéros exacts,DE0=1e−20,EIMP0,R02=1. NormesU2 etDU2 nativement0. D etDD ne sont non nuls que sur lesZ supérieurs imposés :DD=−1,90288107842e−9mm sur chacun, D=−1,328447181728e−8mm. Au critère2 :URNaN,RR0,ERInfinity ; arrêt79/ISTOP−2. Deux états réels restent sauvegardés, dernier0,000125ms ; le temps tenté0,00025ms n’est pas accepté.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La projection/condensation utilisée parPRODUT_UHP n’est pas une norme de toutes les coordonnées brutes. Les valeurs observées montrent ici un mouvement imposé avec norme libre nulle.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source inspectée/modifiée. Les sources logicielles privées restent épinglées et les deux binaires sont inchangés. Les libellés consoleA85 hérités du lanceur sont cosmétiques ; configuration, autorisation et répertoire réels sontA89, sans ambiguïté de budget.

## 4. Hypothèses propres au modèle

Graine1102112, zéro tirage, unitésg/mm/ms. R2=0 est reconstruit depuisF exactement nul avec la somme source sur un domaine ; la variable localeR2 n’a pas été directement lue. IRIKS=0 est reconstruit depuisIDTC1 selon la source, pas directement lu. Tous les autres paramètres de la garde sont mesurés. Aucun élargissement automatique de garde n’est autorisé.

## 5. Résultats dérivés

La conditionALL(DD brut==0) est fausse à cause des quatre corrections imposées ; les autres conditions sont admissibles et les normes libres restent nulles. Ce résultat explique l’exclusion par la garde actuelle, sans supposer un déséquilibre libre. Il faut tester exactement le vecteur de correction projeté/condensé plutôt que retirer tout contrôleDD : une petite composante libre non nulle peut avoir un carré sous-débordé et doit rester bloquante. Les dix contrôles de transcription/portée passent. Le nouvel observateur lit seulement les données et configure des registres matériels ; les points sont désactivés après le critère2 du second essai, puis le moteur termine selon son propre chemin.

## 6. Contradictions et informations manquantes

La boucle0,65ms, rupture et refermeture ne sont pas parcourues. Le seul EngineA89 est consommé, aucun réessai ; le CHECK conditionnelA87 inutilisé ne couvre aucun autre processus. Aucun nouveau correctif moteur n’est appliqué/compilé. Anciennes sorties, budgets, critères échoués, cinqTYPE25 ignorés et107391avertissements restent conservés. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

AIRCRAFT-A90 : après publication A88+A89 vérifiée, préparer en lecture seule une garde de correction nulle sur coordonnées libres projetées/condensées. A89 observeNCYCLE2/TT0,00025ms, tous modes admissibles, forces libres0,EIMP0,DE0=1e−20,U2=DU2=0 mais quatreDD Z imposés−1,90288107842e−9mm ; ALLDD brut exclut ce cas alors que la projection native est nulle. Ne pas supprimer la garde de correction : vérifier exactement son vecteur projeté pour rejeter un petit non-zéro dont le carré sous-déborde. Aucun nouveau correctif appliqué/compilé ; accord distinct requis. Un EngineA89consommé, aucun réessai, CHECK A87 inutilisé non réaffecté. Conserver toutes sorties, critères échoués, budgets et contacts bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
