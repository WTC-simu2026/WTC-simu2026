# AIRCRAFT-A75 — deux préparations TYPE7 échouées, CHECK omis

Les deux Starter autorisés sont terminés avec erreur. Aucun Engine lancé, conformément à la condition stricte de la proposition A74. Sources, erreurs, critères et budgets conservés ; aucun impact entier prolongé.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, exécuter les deux préparations et CHECK conditionnels A75 », lié aux empreintes avant lancement. Deux nouveaux Starter CPU1/plafond180s, sans délai dépassé, moteur A73 inchangé et aucun correctif/compilation/GPU/installation. Les entrées sont les copies A74 exactes, vérifiées avant lancement.

| Cas | Durée(s) | Erreurs | Avertissements | CHECK |
|---|---:|---:|---:|---|
| WHOLE_ORIGINAL_TYPE7_CHECK | 22.913 | 916 | 11 | omis |
| WHOLE_PAIRED_TYPE7_CHECK | 13.400 | 916 | 11 | omis |

Chaque cas imprime cinq TYPE7 et les paramètres déclarés, dont les gaps0,5mm/5mm. Masse191273837,9425g et ADMAS100368522,1367g égales aux totaux de référence, ainsi que les centres imprimés ; ce résultat ne qualifie pas le tenseur redistribué ni les inerties. Aucun restart initial propre produit.

Les916erreurs612 concernent uniquement l’interface2, auto-contact de la peau du radôme. Elles signalent des nœuds secondaires sur la surface principale et une impossibilité de calcul de nouvelles coordonnées, avec INACTI=0 dans le message. L’entrée et le résumé de paramètres impriment pourtant1000 : le résumé seul n’est donc pas le contrat effectif d’initialisation. Les deux nombres de nœuds imprimés dans chaque message sont conservés sans supposer leur domaine ou leur égalité.

Les11avertissements se décomposent en dix614 (IBAG activé sans volume surveillé puis remis à zéro, deux passages pour les cinq interfaces) et un343, qui compte4430pénétrations initiales sur1968nœuds de l’interface2. Le lecteur ne dispose pas d’un inventaire de paires initiales achevé dans ces sorties ; ce critère reste échoué.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les [définitions TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) et [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) montrent que Inacti1000 ne signifie pas le même traitement des pénétrations initiales entre les deux familles. A74 avait conservé la valeur sans présumer d’équivalence dynamique ; A75 établit nativement que cette variante d’initialisation échoue. Aucun résultat de documentation n’est substitué aux messages natifs.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée, aucune vidéo source réanalysée ni dégâts connus ciblés. Les copies de modèle et logiciels sont distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102100, zéro tirage ; unitésg/mm/ms et cartes mécaniques A74 conservées. La variante de contact est explicite et rejetée par ses critères. Les valeurs de gap imprimées ne suffisent pas à valider les paires, recherche, pénalité ou transfert d’efforts. Aucun nœud d’entrée déplacé, contact entier désactivé, matière/masse/inertie ou RKE ajouté pour forcer un passage. Les tentatives natives de coordonnées rapportées par le Starter ne sont pas un état initial validé.

## 5. Résultats dérivés

Les deux portes Starter sont échouées. Les deux CHECK autorisés seulement sous condition sont omis, leurs places ne sont ni consommées comme Engine ni réaffectées à de nouvelles préparations. Deux Starter consommés, zéro restant ; deux places CHECK conditionnellement inutilisées. La nouvelle cause concerne le filtrage initial de l’auto-contact2 et l’option IBAG sans volume surveillé. Il faut une proposition ciblée fondée sur ces données et le contrat de voisinage, sans nouvelle exécution dans le lotA75.

## 6. Contradictions et informations manquantes

Aucune compatibilité entière ou équivalence dynamique validée. Les paramètres natifs effectifs d’initialisation et le domaine des nombres de nœuds restent à tracer par source ; aucun domaine inventé. Les107391 avertissements de préconditionnement A73 restent bloquants, ainsi que inerties, matériaux, bilans et intégration A52. Les échecs TYPE25 antérieurs, gardeTT0 ratée A71 et variante A75 restent conservés. Nouveau lot Starter requiert un accord distinct ; les places CHECK inutilisées ne l’autorisent pas. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.

AIRCRAFT-A76 : audit en lecture seule du nouvel échec d’initialisation TYPE7 A75 et proposition ciblée après publication A74+A75 vérifiée. Les deux Starter autorisés ont échoué avec916erreurs612 sur l’interface2 et11avertissements (10IBAG614 +1pénétrations343) ; aucun Engine exécuté. Les deux places CHECK restent conditionnellement inutilisées, non réaffectées et sans nouveau crédit Starter. Les cinq TYPE7/gaps0,5/5mm sont imprimés et masse/ADMAS conservés, mais aucun restart initial qualifié. La valeur Inacti1000 ne porte pas le même contrat entreTYPE25 etTYPE7 : ne pas désactiver globalement des contacts ni déplacer des nœuds pour forcer un passage. Inspecter le filtrage de voisinage/paires initiales et IBAG sans volume surveillé, préparer une différence exacte et un nouveau lot borné avec accord distinct. Moteur A73 conservé, zéro correctif/compilation/GPU/installation ; critères et anciens échecs inchangés. Les107391 avertissements et budgets physiques entiers restent bloquants. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.
