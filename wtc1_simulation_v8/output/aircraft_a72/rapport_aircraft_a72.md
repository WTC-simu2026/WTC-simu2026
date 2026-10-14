# AIRCRAFT-A72 — proposition de contexte CHECK explicite

Proposition concrète et vérifiée en lecture seule. Aucun correctif appliqué au moteur, aucune compilation, aucun nouveau Starter/Engine. L’échec de la garde TT0 en A71 est conservé. La proposition utilise le contexte CHECK existant et prépare l’observation native des paramètres manquants.

## 1. Faits directement observés ou transcrits

A71 a consommé ses six Engine et son unique Starter autorisés. Le témoin zéro dynamique et les deux CHECK entiers mesurent R2=0 mais gardent une erreur de chargement et aucun nouveau diagnostic : la nouvelle garde TT0 a échoué. Le témoin statique chargé mesure R2=4, le zéro statique reste refusé, la dynamique libre1ms passe23critères. Ces résultats sont mis en cache, recontrôlés par empreintes, sans répétition de calcul.

La chronologie de la source figée RESOL place l’avance TT ligne8605 avant le contexte IMP_CHK>0 ligne8734 et CALL IMP_CHKM ligne8735, puis MSTOP2 ligne8756. Cette relation est une observation de source. Les valeurs exactes IDYNA/IQSTAT/IMP_CHK/NCYCLE/TT à l’appel n’ont pas encore été lues nativement ; aucune valeur n’est inventée.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat de modèle historique officiel. Le pin logiciel OpenRadioss reste3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Les déclarations communes figées fournissent les types et offsets des cinq scalaires à lire ; elles ne fournissent pas leurs valeurs en exécution. Sources brutes et différence exactes restent en copie privée AGPL, séparées des scripts propres du harnais.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée, modifiée ou réanalysée. Aucune nouvelle vidéo source lue, aucun ajustement à des dégâts connus. Les copies logicielles figées ne sont pas des observations historiques de l’impact.

## 4. Hypothèses propres au modèle

Graine1102097, zéro tirage ; entrées et unitésg/mm/ms conservées. R2 exactement nul devient admissible uniquement dans le CHECK Newmark IDYNA2/IQSTAT0/IMP_CHK>0, avec diagnostic explicite. Cette modification d’admissibilité est annoncée : elle ne qualifie ni les contacts ni la scène entière. Les branches zéro statique, quasi-statique, autres méthodes, valeurs hors plage/non finies et résidus positifs restent inchangées. Aucun terme RKE, chargement entier, budget masse/matière/inertie ou dynamique n’est modifié.

## 5. Résultats dérivés

Quatorze critères de portée passent sur la source proposée : seule IMP_CHKM change, la condition TT==0 est remplacée par IMP_CHK>0 et l’inclusion COM08 ajoutée en A71 devenue inutile est retirée. Les autres routines restent identiques. Les six ensembles d’entrées sont vérifiés par empreintes, avec le Starter positif A71 réutilisé.

Le neuvième moteur isolé A73 est proposé avec toutes les corrections A71 conservées : compilation plafond1h/sixCPU, estimation5–15min, sans GPU ni installation. Maximum six Engine sur unCPU/plafond180s, zéro Starter : zéro dynamique, zéro statique refusé, charge positive R2=4, régression libre1ms aux seuils A67, deux CHECK entiers. Il s’agit de contrôles du nouveau binaire, pas de répétitions de l’ancien lot. Aucun prolongement dynamique entier autorisé dans ce lot.

L’observateur propre est préparé et sa syntaxe passe. Aux mêmes points d’arrêt matériels que les cinq CHECK futurs, il lira directement IDYNA/IQSTAT/IMP_CHK/NCYCLE/TT par mémoire de son enfant en lecture seule. Les symboles et tailles doivent être résolus dans le nouveau binaire et les bornes contrôlées avant lecture ; aucun point d’arrêt, processus ou contrôle natif supplémentaire. Cette observation n’est pas encore qualifiée en exécution.

## 6. Contradictions et informations manquantes

Une revue statique n’est pas une réussite native : A71 a compilé après15critères de portée, puis sa garde a échoué. Les107391 avertissements de coefficients transformés et cinq contacts TYPE25 ignorés par scène restent présents et bloquants. Les inerties, matériaux, contacts et bilans entiers restent non qualifiés. Toute intégration ou simulation entière ultérieure reste conditionnelle aux critères physiques conservés.

L’accord A71 concernait exactement la garde TT0 et son budget épuisé. Le nouveau correctif, sa compilation et six nouveaux contrôles exigent un accord distinct selon AGENTS.md. La publication A70+A71 est vérifiée avant déclaration A72 : empreintes, anciennes archives et deux CI passent. Cette intégrité de publication ne valide pas la physique. Meilleur impact entier0,0200001220703125s ; les dix secondes physiques et leur vidéo3D restent incomplètes. Aucun temps des témoins ou temps interpolé n’est crédité.

AIRCRAFT-A73 proposée seulement : neuvième moteur isolé avec le correctif exact A72, garde CHECK IMP_CHK>0 à la place de TT==0 dans IMP_CHKM, suppression de COM08 devenue inutile. Nouvel accord explicite distinct requis avant application/compilation et six nouveaux Engine. Compilation plafond1h/sixCPU, estimation5–15min ; six Engine au maximum, unCPU/plafond180s chacun, zéro Starter, sans GPU ni installation, aucun prolongement dynamique entier. Starter positif qualifié A71 réutilisé ; entrées et seuils conservés, flags natifs et horloge à mesurer. A71 gardeTT0 échouée et budgets sixEngine/unStarter entièrement consommés, sorties/échecs inchangés. Les107391 avertissements et cinq TYPE25 par scène restent bloquants. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet. Ne pas créditer les témoins, modifier implicitement les budgets, compenser par RKE ou viser des dégâts connus.
