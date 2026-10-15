# AIRCRAFT-A78 — coïncidences de surface et paires initiales à observer

Nouvel audit statique depuis les sorties A77, sans solveur rejoué. Une observation Starter avec sortie détaillée est préparée, non exécutée. Aucun contact ou paramètre mécanique changé.

## 1. Faits directement observés ou transcrits

A77 conserve916erreurs612/1avertissement ; les deux Starter sont consommés et ses deuxCHECK omis. Les numéros des676nœuds distincts sont présents dans les groupes et surfaces d’entrée. L’auto-contact possède432pièces,1296facettes et3024nœuds. Le graphe des facettes par identités de nœuds contient432composantes ;340groupes de coordonnées écrites identiques traversent ces composantes. Tous les676numéros fautifs apparaissent dans ces groupes. Les deux variantes donnent les mêmes mesures statiques. Cela ne prouve pas le segment réellement choisi par le Starter.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La [documentation IOFLAG](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm) décrit la sortie Starter détaillée Ipri5 avec coordonnées, connectivités et pénétrations initiales. Les sources et configuration figées en cache confirment l’ordre des champs, Ipri0 et Idrot0 par défaut. Leur identité avec le binaire Windows n’est pas revendiquée ; l’observation native proposée devra vérifier le résultat.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée, aucune vidéo source réanalysée ni dégâts connus ciblés. Les sources logicielles et données propres restent distinctes de l’histoire de l’impact. A76+A77 publiées avec anciennes archives et deux CI vérifiées avant déclaration A78.

## 4. Hypothèses propres au modèle

Graine1102103, zéro tirage ; unitésg/mm/ms. Des morceaux de surface distincts partageant les mêmes positions sont compatibles avec les erreurs d’auto-contact et l’inefficacité du filtre par voisinage. Cette relation reste une hypothèse tant que les paires effectivement sélectionnées sont absentes. Les contraintes TYPE2 ne sont pas incluses dans le graphe de surface ; aucune déconnexion mécanique ou rang structurel inférés. Coordonnées identiques écrites ne sont pas une observation de coordonnées internes natives.

## 5. Résultats dérivés

Une seule copie originale A77 est préparée avec ajout /IOFLAG Ipri5 et noms BEGIN/TITLE changés. Toutes les cartes physiques et contacts restent exactement identiques ; aucun Engine préparé/exécuté. Neuf critères de portée passent. Lot A79 proposé : un Starter CPU1/plafond180s, sans correctif/compilation/GPU/installation ni impact entier prolongé, estimation20–90s. Objectif : tuples réels secondaire/quatre nœuds du segment, vérifiés contre coordonnées/connectivités natives imprimées et modèle déclaré. Les masses/ADMAS et erreurs sont enregistrées. Le succès d’observation ne valide pas l’initialisation.

## 6. Contradictions et informations manquantes

Les paires fautives réelles restent manquantes. Le nouveau changement porte sur la sortie, jamais sur un filtre destiné à forcer le passage ; les erreurs916/1 restent attendues et échouées. Les107391 avertissements, inerties, matériaux, contacts dynamiques, bilans et intégration entière restent bloquants. Les budgets A77 sont conservés et aucun nouveau Starter n’est couvert par ses CHECK inutilisés. Accord distinct requis pour l’observation proposée. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

AIRCRAFT-A79 proposée : une seule nouvelle observation Starter détaillée, IPRI5 ajouté par /IOFLAG et nom de cas changé, toutes les cartes physiques A77 originales exactes. UnCPU/plafond180s, zéro Engine, correctif logiciel, compilation, GPU ou installation, aucun impact entier prolongé. Mesurer les tuples réels nœud secondaire/quatre nœuds de segment et les relier à la géométrie, avant une nouvelle politique de contact. Les916erreurs/1avertissement A77 sont attendus et restent échoués ; réussite d’observation ne vaut pas préparation propre. Hypothèse de fragments de surface coïncidents : 432composantes par identités de nœuds,340groupes de coordonnées identiques entre composantes, 676numéros fautifs tous sur ces coïncidences, sans preuve de déconnexion mécanique ni paire native encore identifiée. Les deux Starter A77 sont consommés, CHECK inutilisés non réaffectés : accord distinct requis pour cette observation. Conserver anciens moteurs/sorties, A75/A77 échoués, budgets et critères.107391avertissements physiques bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
