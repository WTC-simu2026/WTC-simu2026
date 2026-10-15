# Voie de recherche contact A80 — lecture seule

Ce dossier ne contient aucun correctif appliqué, aucune compilation et aucun calcul natif. Onze membres ciblés du cache logiciel épinglé ont été copiés sans modification. Leur manifeste conserve leurs empreintes. Il ne s'agit pas de l'archive historique et aucune identité entre source épinglée et Starter Windows n'est supposée.

## 1. Faits directement observés
Le parent a transmis que A79 imprime les 916 tuples ERROR612. La qualification complète des paires par les liaisons cohésives reste nécessaire; coïncidence géométrique seule insuffisante.

## 2. Résultats d'un modèle officiel
Aucun résultat physique officiel exploité. La documentation logicielle Altair TYPE25 indique une absence de prise en charge implicite et décrit Inacti1000 comme une attente jusqu'à sortie puis rentrée en contact. Cela motive une spécification, sans démontrer l'équivalence TYPE7/TYPE25.

## 3. Affirmations d'archives locales
Aucune archive historique inspectée.

## 4. Hypothèse propre et voie unique recommandée
Préparer une fonction explicite d'attente puis d'armement par paire dans TYPE7 implicite, limitée aux jointures cohésives initiales certifiées. Conserver le gap nominal, les nœuds distincts et les lois cohésives. Une paire initialement recouvrante attend sa première sortie complète du domaine de contact; après celle-ci elle redevient une paire TYPE7 normale, à jamais armée. Toute paire initialement propre et toute autre facette du même nœud restent actives.

Ce serait une nouvelle fonction du solveur et une hypothèse du modèle, non une simple réparation de lecture. Il faut une table persistante, un transfert Starter/Engine explicite et une décision commune aux efforts et à la matrice. Ne pas redéfinir silencieusement Inacti1000, ne pas coder en dur les identifiants d'avion. N'adopter un nouvel indicateur qu'après audit des champs disponibles.

## 5. Résultats dérivés de l'audit logiciel
Inacti1/2 supprime des raideurs entières de nœud/segment. Inacti5/6 réduit le gap effectif: la source I7FOR3 soustrait explicitement CAND_P à GAPV (722–758) et I7PWR3 annonce cette réduction (245–259). Pour les jointures coïncidentes où la pénétration approche le gap, cette correction est d'ordre du gap entier. Elle n'est donc pas compatible avec sa conservation exigée.

Le simple réemploi du tampon 5/6 est insuffisant: I7DSTR3 remet CAND_P à zéro dans la sélection implicite (391–399), et I7STO initialise les nouveaux candidats à zéro. Les mises à jour d'état doivent aussi être annulables pendant les essais Newton et engagées seulement sur un pas accepté.

## 6. Contradictions et manques
Les 916 erreurs fatales ne représentent pas à elles seules les 4430 pénétrations initiales. Une exemption basée seulement sur ces erreurs masquerait peut-être des recouvrements non cohésifs. Avant patch: classifier la totalité des paires initiales candidates, tracer stockage/tri/reprise, certifier la compression avant armement et préparer les témoins du JSON joint.

Le risque physique est réel: avant sortie complète du domaine, une paire en attente ne porte pas de contact; si les éléments cohésifs ne couvrent pas correctement la compression ou la rupture avant armement, cette voie doit être abandonnée. L'absence de 612 ne suffira jamais à valider le modèle. Aucun correctif n'est prêt à compiler et les échecs A75/A77/A79 restent conservés.

Sources primaires: [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm), [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm).
