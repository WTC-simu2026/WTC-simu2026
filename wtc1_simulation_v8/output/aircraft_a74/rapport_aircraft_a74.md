# AIRCRAFT-A74 — contrat des contacts actuels et variantes de compatibilité

Deux copies TYPE7 sont préparées et non exécutées, avec les autres cartes mécaniques conservées. Aucun moteur modifié/compilé, aucun nouveau Starter/Engine. L’équivalence dynamique n’est pas présumée.

## 1. Faits directement observés ou transcrits

A73 passe six contrôles logiciels et mesure les cinq scalaires natifs dans cinqCHECK. L’erreur de chargement a disparu, mais chaque scène conserve107396 avertissements :107391 de préconditionnement et cinq contacts TYPE25 ignorés. A72+A73 publiées, anciennes archives et deux CI vérifiées avant déclaration A74. Budget A73 sixEngine/zéroStarter entièrement consommé.

Nouvel inventaire des cartes actuelles A49/A52, sans ancien solveur relancé. Les interfaces2/101/102/103/104 sont identiques entre scènes. Les groupes secondaires comptent respectivement3024/1056/480/672/5785nœuds. Tous sont reliés à des coques ; certains le sont aussi à des poutres. Les pièces principales sont des coques. Les groupes/surfaces/identifiants et histoires TH ne changent pas dans les copies préparées.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La [documentation TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) confirme l’absence de ce contact en implicite et sa définition nœuds/surface. Pour Igap5, les épaisseurs déclarées interviennent par demi-épaisseurs ; l’option de stabilité Stfacm n’est active que sous ses flags particuliers, absents ici. La [documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) fournit un gap constant sous Igap1000 et les champs de groupe/surface, raideur, friction et filtrage. Ces formats ne prouvent pas l’équivalence des algorithmes. Le témoin A45 TYPE7 qualifié reste une référence en cache, sans calcul répété.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée, aucune vidéo source réanalysée ni dégât connu ciblé. Les copies de modèles sont des entrées propres, distinctes des sources historiques.

## 4. Hypothèses propres au modèle

Graine1102099, zéro tirage, unitésg/mm/ms conservées. Le contrat géométrique statique permet de proposer Gapmin0,5mm pour2 et5mm pour101–104. Le gap effectivement initialisé reste à mesurer. Les variantes déclarent cinq TYPE7, Istf4/Stfac1, friction0, Igap1000 et Irem_i2=3, avec les groupes et surfaces actuels. Elles changent explicitement le modèle de contact ; comportement près des bords, recherche, pénalité et paires initiales ne sont pas supposés équivalents. Aucun ajustement aux dommages ou résultat attendu, matière/inertie/masse ou RKE ajouté.

## 5. Résultats dérivés

Les deux copies ne changent que les cinq cartes de contact et les noms BEGIN/TITLE/RUN. Vingt-deux critères de portée passent. Toutes les autres cartes mécaniques et TH sont identiques ; paramètres, entrées et empreintes sont enregistrés. Le lot A75 proposé comprend deux Starter et deux EngineCHECK conditionnels, CPU1/plafond180s chacun, moteur A73 inchangé, sans GPU/installation/compilation. Les Starter doivent passer sans erreur/avertissement, masse/ADMAS conservés et références/contacts lus avant lesCHECK. Les erreurs et données de gap/filtrage doivent être relevées ; les107391 avertissements restent bloquants. Aucun impact entier prolongé.

## 6. Contradictions et informations manquantes

Les copies restent non qualifiées par Starter/Engine. Compatibilité de lecture ne vaut pas contact dynamique validé ni objectif dix secondes atteint. Les avertissements de préconditionnement, inerties, domaines matériaux, bilans et intégration A52 restent non qualifiés. Les anciennes TYPE25 et gardeTT0 ratée A71 restent intactes. Un accord distinct est requis pour le nouveau lot car A73 est épuisé. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes, aucun crédit du témoin ou interpolation.

AIRCRAFT-A75 proposée seulement : deux préparations Starter de variantes de contact TYPE7 déclarées puis deux CHECK Engine conditionnels, moteur A73 inchangé. Maximum deux Starter/deux Engine, unCPU/plafond180s chacun, sans correctif moteur, compilation, GPU ni installation. Les cinq cartes TYPE25 sont remplacées explicitement dans deux nouvelles copies, groupes/surfaces/TH et toutes les autres données mécaniques conservés. Ne pas prétendre à une équivalence dynamique de TYPE25/TYPE7 : algorithme, recherche, pénalité et filtrage doivent encore être contrôlés. Aucun impact entier prolongé dans ce lot. Starter propre, mass/ADMAS conservés, cinq TYPE7 lus et aucun contact ignoré requis avant chaqueCHECK. Les107391 avertissements restent bloquants ; zéro erreur de chargement n’est pas qualification physique. A73 six Engine/zéro Starter entièrement consommés ; obtenir un accord distinct sur le nouveau lot. A71 gardeTT0 ratée et toutes anciennes sorties/critères/budgets préservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
