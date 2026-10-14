# AIRCRAFT-A76 — audit de l’initialisation et filtrage local proposé

Audit en lecture seule de nouvelles sorties A75, proposition exacte non exécutée. Aucun nouveau Starter/Engine, moteur modifié/compilé ou temps entier simulé.

## 1. Faits directement observés ou transcrits

A75 échoue avec916erreurs/11avertissements dans chaque Starter ; ses deux CHECK conditionnels sont omis. Les deux préparations sont consommées. Le nouvel audit lit la table d’impacts séparée :23520possibles pour l’interface2 et0 pour101–104. Les lignes de coordonnées impossibles précèdent les messages612 : les916numéros concordent avec le message qui les suit. Le premier lecteur A75 avait associé la ligne suivante ; ses données et échecs restent intacts. La lecture réparée rejette toujours les vraies erreurs et avertissements.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Dix fichiers de sources Starter figées sont lus en copie privée AGPL ; aucune identité source/binaire Windows supposée. Le chemin opérationnel de valeurs par défaut normalise1000 en0, séparément du résumé imprimé. Le lecteur d’interface avertit614 puis remet IBAG à zéro sans volume surveillé. La routine de contrôle d’impacts émet612 quand la direction est nulle avec Inacti0 et écrit la ligne de coordonnées avant le message. Ces relations de source sont cohérentes avec A75 mais n’inventent pas un état natif non observé.

La [documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) décrit Irem_gap2 comme un filtrage local des voisins proches du segment, sans retirer le nœud du contact avec les autres segments. Cela justifie une nouvelle hypothèse à tester ; effet sur les faces distinctes reliées TYPE2 et dynamique après rupture restent inconnus.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée ni vidéo source réanalysée. Les lectures concernent seulement des sources logicielles en cache et les nouvelles sorties propres A75. A74+A75 publiées avec anciennes archives et deux CI vérifiées avant déclaration A76.

## 4. Hypothèses propres au modèle

Graine1102101, zéro tirage, unitésg/mm/ms inchangées. IBAG2→0 dans cinq cartes et Irem_gap1→2 uniquement pour l’auto-contact2 constituent la variante. Inacti1000, les autres contacts, paramètres/gaps, géométrie, groupes/surfaces, histoires, masses/matières/inerties restent identiques. Aucune désactivation globale, déplacement de coordonnées ou compensation RKE. Le filtre local est une hypothèse non qualifiée, sans ajustement aux dégâts connus ni preuve d’équivalence TYPE25/TYPE7.

## 5. Résultats dérivés

Les deux différences exactes, noms de cas et entrées futures sont préparés par empreintes. Vingt-deux critères de portée passent ; toutes les autres cartes mécaniques sont identiques. Le lecteur propre futur est vérifié sans écriture sur les deux sorties A75 en cache : il lit les flags et les tables séparées, tout en maintenant le refus916erreurs/11avertissements. Aucun ancien solveur rejoué.

Une préparation de supplément source R0 échoue sur un chemin de helper supposé ; ses trois copies correctes et script sont conservés. Une finition R1 réutilise ces copies, vérifie leurs empreintes et lit le vrai chemin du quatrième fichier. Aucun calcul ou code moteur affecté.

Lot A77 proposé : maximum deux Starter et deux EngineCHECK conditionnels, CPU1/plafond180s chacun, moteur A73 inchangé, sans correctif/compilation/GPU/installation et aucun impact entier prolongé. Avant chaqueCHECK : zéro erreur/avertissement Starter, masse/ADMAS, cinq contacts/gaps/flags et inventaires imprimés lus. Les107391 avertissements de préconditionnement restent bloquants.

## 6. Contradictions et informations manquantes

Aucune variante qualifiée nativement ; l’effet du filtre sur les paires de faces disjointes demeure inconnu. Les listes exactes de paires exclues et la dynamique après rupture ne sont pas établies par un simple compte de candidats. Les avertissements, inerties, matériaux, bilans et intégration entière restent non qualifiés. Nouveau lot soumis à accord distinct : deux Starter A75 épuisés et deux CHECK inutilisés ne peuvent devenir de nouvelles préparations. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

AIRCRAFT-A77 proposée seulement : deux nouveaux Starter et deux CHECK Engine conditionnels sur variantes A76 exactes, unCPU/plafond180s chacun, moteur A73 inchangé. IBAG2→0 dans cinq cartes et Irem_gap1→2 seulement pour l’auto-contact2 ; tous les autres paramètres, groupes/surfaces, gaps0,5/5mm et cartes mécaniques conservés. Pas de désactivation globale de nœuds/contact ni Inacti1/2/3/5/6, coordonnées ou compensation RKE modifiées. Hypothèse de filtrage local de voisins, non qualifiée nativement et non équivalence dynamique TYPE25/TYPE7. Lecteur propre réparé pour tables d’impacts séparées et chronologie des messages, ancien lecteur/échecs A75 conservés. Deux Starter A75 épuisés ; deux CHECK inutilisés conditionnellement ne couvrent pas de nouveaux Starter. Accord distinct requis pour le nouveau lot ; aucun correctif moteur, compilation, GPU ou installation, aucun prolongement d’impact entier. Starter sans erreur/avertissement, masse/ADMAS/gaps/flags/contacts lus avant chaque CHECK ;107391 avertissements de préconditionnement toujours bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
