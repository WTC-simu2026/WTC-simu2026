# AIRCRAFT-A70 — correctif de classification CHECK initial, proposé seulement

Le correctif exact ajoute quatre lignes dans IMP_CHKM et préserve toutes les autres routines. Aucun code moteur appliqué ou compilé, aucun nouveau Starter/Engine. Son admissibilité numérique modifiée est annoncée explicitement ; elle ne valide pas les contacts ni la scène entière.

## 1. Faits directement observés ou transcrits

A69 mesure R2=0/LB nul dans deux cas, dont le témoin dont la dynamique libre A67 passe. L’observation originale A69 reste échouée et non répétée. Source proposée et différence exactes en copie privée AGPL. La revue indépendante passe 15 critères de portée, garde, entrées et conservation des autres routines. En retirant seulement les quatre lignes ajoutées, on retrouve exactement la source de base. TT est déclaré par COM08, ajoutée uniquement dans cette routine ; la proposition TIME antérieure, non déclarée, est refusée.

Les préparations R0 (espacement d’inclusion), R1 (ancien identifiant INIVEL supposé1 au lieu de500) et R2 (comparaison du TITLE volontairement renommé) échouent avant toute application. Toutes sont conservées. Les cartes R2 correctes sont réutilisées sans régénération. La proposition utilisant TIME est refusée par la revue indépendante avant application ; R4 utilise TT et la déclaration COM08 native. Tous les champs mécaniques sont identiques sauf la suppression déclarée de vitesse initiale dans le coupon statique chargé, et sa charge de contrôle explicite ; BEGIN/TITLE sont renommés. A68+A69 publiées, hashes et deux CI vérifiés avant déclaration A70.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Le pin OpenRadioss et la base IMP_CHKM sont identiques à A67/A68. La modification porte sur la classification du résidu, sans modifier force, matériau, histoire, raideur ou intégration. Le format de charge du coupon est vérifié dans la [documentation officielle CLOAD](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/cload_starter_r.htm), qui applique la force individuellement à chaque nœud du groupe, et dans [FUNCT](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/funct_starter_r.htm). Le Starter natif n’est pas encore exécuté.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée ; aucun dégât connu ciblé. Les références logicielles de contrôle sont séparées des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102095, zéro tirage. Une vitesse initiale peut donner un résidu initial nul ; les bilans, paramètres physiques et contacts doivent être vérifiés séparément. La proposition autorise seulement R2 exactement zéro pour IDYNA2, IQSTAT0, TT0, avec diagnostic explicite. Les autres méthodes, temps non nul, zéro statique, valeurs hors plage/non finies gardent leur ancienne branche. Cette règle est une nouvelle admissibilité de CHECK, pas une relaxation cachée d’un critère physique ni une réussite rétroactive.

## 5. Résultats dérivés

Huitième moteur isolé A71 proposé avec toutes les corrections A67 conservées, compilation plafond1h/CPU6, sans GPU ni installation. Maximum six Engine et un Starter CPU1/cap180s chacun : zéro dynamique accepté avec message ; zéro statique toujours refusé ; charge statique positive ; régression libre élastique1ms avec seuils A67 conservés ; deux CHECK entiers avec cartes/restarts inchangés. Le coupon positif applique1N à chacun des quatre nœuds libres, total4N ; aucune force ajoutée aux scènes entières. Sources, entrées, graines, empreintes et résultats attendus dans le plan ; aucun contrôle natif présumé passé.

## 6. Contradictions et informations manquantes

Patch non appliqué, moteur non compilé, cartes nouvelles non qualifiées par Starter. Accord A69 limité aux trois observations moteur inchangé et épuisé : nouveau consentement requis avant toute modification/compilation ou calcul proposé. Les 107391 avertissements et cinq contacts TYPE25 restent présents et bloquants. A52nonintégrée, inerties, domaines matériaux et bilans entiers non qualifiés. Tous les refus antérieurs restent inchangés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes, aucun temps manquant fabriqué.

AIRCRAFT-A71 proposée, non appliquée/non compilée : huitième moteur isolé avec le correctif exact A70 de CHECK initial à résidu nul. Nouvel accord humain distinct requis avant toute modification/compilation, conformément à AGENTS.md. Ajout limité à quatre lignes dans IMP_CHKM (déclaration COM08 et garde) : IDYNA2, IQSTAT0, TT0, R2 exactement0 ; diagnostic explicite, aucun chargement entier artificiel. Les anciennes erreurs restent conservées ; les 107391 avertissements et cinq TYPE25 restent présents et bloquants. Plafond compilation1h/CPU6 ; maximum six Engine et un Starter sur CPU1/cap180s chacun, sans GPU ni installation, aucune dynamique entière prolongée. Témoins zéro dynamique, zéro statique refusé, charge positive instrumentale, régression libre1ms puis deuxCHECK entiers. Budget A69 trois entièrement consommé (deux observations complètes, première originale échouée), jamais réinitialisé. Préserver budgets, sorties, critères échoués et RKE sans compensation. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.
