# AIRCRAFT-A79 — paires initiales mesurées, initialisation toujours échouée

L’unique observation autorisée est terminée en32.601s, sur unCPU, sous plafond180s. Les paires réellement imprimées et leur domaine géométrique sont contrôlés. Le Starter reste échoué avec916erreurs et2avertissements ; aucun Engine ou impact entier prolongé.

## 1. Faits directement observés ou transcrits

L’accord humain « bien, on reprends et on continue » répond à la proposition A79 et au rappel de sa portée. La déclaration conserve cette réponse et les empreintes exactes avant lancement. Une entrée A78 immuable est copiée ; ajout /IOFLAG Ipri5 et noms de cas constituent les seuls changements. Le binaire Starter Windows est inchangé et le moteur A73 n’est pas lancé. Code retour2, aucun dépassement du plafond. Les cinq paramètres TYPE7, gaps0,5/5mm et filtres sont toujours lus ; aucun restart initial propre.

Le détail d’observation est dans pair_listing_review.json et ses fichiers de paires référencés : coordonnées et connectivités natives imprimées, groupe secondaire et facettes déclarées sont comparés séparément. Premier exemple : secondaire50, segment37327/43926/43928/43925, puis pénétration0,5mm et ERROR612. La ligne de tuple précède la ligne de coordonnées impossibles puis l’erreur ; elle n’est pas associée au nœud suivant. Le numéro d’élément n’est pas confondu avec son indice interne.

Les4430tuples ont chacun un segment natif et une facette déclarée uniques, avec ordre exact des quatre sommets. Les48171coordonnées imprimées concordent avec l’entrée, écart absolu maximal0mm à cette précision. Les1296segments et3024nœuds secondaires sont contrôlés. Les916erreurs, portant676secondaires distincts, ont toutes une coïncidence exacte avec un sommet principal portant un autre numéro. Leurs916quads ne sont pas dégénérés ; aire triangulée de12686,35à36969,36mm², distance point–surface triangulée nulle. Les3514autres paires comportent aussi8coïncidences exactes sans ERROR612 : une règle causale fondée uniquement sur l’égalité des coordonnées serait excessive. Les432TYPE2 ont des groupes et surfaces imprimés, présence seulement.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat d’un modèle historique officiel. La documentation [IOFLAG](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm) définit l’impression détaillée ; la sortie réelle confirme IPRI5. Les sources logicielles figées éclairent l’ordre d’impression, sans revendication d’identité avec le binaire Windows. La documentation [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) et [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) n’attribue pas le même traitement initial à Inacti1000 : sa valeur numérique seule n’établit pas l’équivalence.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée et aucune vidéo source réanalysée. Aucun dégât connu utilisé comme cible. Les données propres, les sources logicielles et les observations natives restent distinctes de l’histoire réelle.

## 4. Hypothèses propres au modèle

Graine1102103, zéro tirage, unitésg/mm/ms. Les peaux des fragments du radôme ont été séparées pour autoriser la rupture via les joints existants ; une fusion de coordonnées identiques changerait ce mécanisme. Le graphe de surface n’est ni un rang de matrice ni une preuve de déconnexion mécanique. La présence de liaisons TYPE2 n’établit pas leur qualification dynamique. La norme de la direction de repositionnement dans la source liée ne constitue pas à elle seule une aire de facette.

## 5. Résultats dérivés

La réussite de l’observation est enregistrée séparément de l’échec de la préparation physique. Les données géométriques et tous les contrôles sont dans le JSON détaillé conservé, sans crédit de durée. Masse191273837,9425g, ADMAS100368522,1367g et centre identiques aux références ; cela ne valide pas le tenseur redistribué ou l’inertie native. Un Starter autorisé consommé, zéro restant ; aucun Engine autorisé, entrée Engine créée ou lancement.

## 6. Contradictions et informations manquantes

Le plan A78 prévoyait1avertissement. La sortie détaillée en émet2 : WARNING1164 liste3514pénétrations à direction calculable, en plus de WARNING343 qui compte4430pénétrations concernant1968nœuds. Avec916erreurs612,3514+916=4430. Le supplément diagnostique reste enregistré ; la prévision antérieure n’est pas réécrite. Les916erreurs, les2avertissements et la porte stricte restent échoués, même si les paires sont correctement observées. Les107391avertissements A73, contacts après séparation/refermeture, inerties, matériaux et bilans restent bloquants. Aucune nouvelle durée d’impact ; meilleur calcul entier0,0200001220703125s, dix secondes puis vidéo3D incomplètes.

AIRCRAFT-A80 : après publication A78+A79 vérifiée, préparer en lecture seule une stratégie de contact pour les jointures cohésives initialement coïncidentes, à partir des paires réelles A79. Préserver les nœuds séparés voulus pour la rupture et les contacts après ouverture/refermeture ; ne pas fusionner les nœuds, réduire le gap, déplacer les coordonnées ou désactiver globalement le contact pour forcer une préparation propre. Écarter toute simple copie Inacti1000 entre TYPE25 et TYPE7. Définir des témoins distinctifs et vérifier les chemins sources avant de présenter un correctif concret. A79 consomme son unique Starter ; zéro Engine autorisé ou exécuté. Aucun autre lot natif/correctif logiciel ou compilation couvert par cet accord. Les916erreurs et deux avertissements A79 restent échoués, dont1164 supplémentaire dû à la sortie détaillée, sans modifier la prévision originale d’un avertissement. Conserver moteurs, sorties, budgets, critères échoués et107391avertissements A73. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.
