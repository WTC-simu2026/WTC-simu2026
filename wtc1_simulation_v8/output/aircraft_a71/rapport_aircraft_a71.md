# AIRCRAFT-A71 — moteur compilé, garde TT initial échouée

Le huitième moteur applique exactement le correctif A70 R4 autorisé et compile. Les six contrôles sont terminés ; la garde de résidu initial échoue dans trois cas. La dynamique libre et le contrôle chargé positif passent. Aucun prolongement d’impact entier.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, appliquer et compiler le correctif A70 et exécuter le lot A71 » lié aux empreintes avant application. Premier build en 284.626s, six CPU/plafond1h, sans GPU ni installation ; Starter non recompilé. Binaire SHA256 61b9b1d613267ad24ad8bde41e00496399ba5ba5e0808f8e3bead9b161c99a7e. Toutes les corrections A67 conservées ; source appliquée égale exactement à la proposition R4, patch fuzz0, workspace distinct puis démonté. Six Engine CPU1/cap180s et un Starter CPU1/cap180s, propres, budgets entièrement consommés.

| Contrôle | R2 natif | Erreurs de chargement | Nouveau INFO | Critères attendus |
|---|---:|---:|---:|---|
| FREE_INITIAL_ZERO_CHECK | 0.0 | 1 | 0 | False |
| STATIC_INITIAL_ZERO_CHECK | 0.0 | 1 | 0 | True |
| STATIC_POSITIVE_LOAD_CHECK | 4.0 | 0 | 0 | True |
| FREE_DYNAMIC_REGRESSION | dynamique | 0 | 0 | True |
| WHOLE_ORIGINAL_CHECK | 0.0 | 1 | 0 | False |
| WHOLE_PAIRED_CHECK | 0.0 | 1 | 0 | False |

Le Starter du témoin positif passe sans erreur ni avertissement. Sa charge déclarée1N sur chacun des quatre nœuds supérieurs donne R2=4, et aucune erreur CHECK. Le zéro statique reste refusé, comme demandé. Les cinq observations CHECK sont complètes, y compris l’original jusque-là manquant en A69 ; R2=0 dans original/appairé et témoin libre. Le premier échec A69 n’est pas réécrit. Aucune nouvelle INFO dans ces trois cas : l’exception proposée n’est pas atteinte. Chaque scène entière garde1ERROR/107396WARNINGS et cinq TYPE25 ignorés ; pas de STOPvolume.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La chronologie native du pin déclaré est lue après le nouvel échec : RESOL incrémente son horloge TT avant CALL IMP_CHKM, sous IF(IMP_CHK>0), puis fixe MSTOP2. Le contexte d’un CHECK initial ne correspond donc pas à TT exactement zéro. Cette relation est directement vérifiée dans la source, mais les flags et la valeur précise de TT à l’appel ne sont pas directement capturés ici. Aucune valeur scalaire native supposée à partir du seul affichage de départ.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée, aucune analyse vidéo ni ajustement aux dégâts connus. Source logicielle figée et entrées de modèle distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102096, zéro tirage. Unitésg/mm/ms, coupon instrumental8g conservé. L’idée de résidu nul admissible pour un problème dynamique reste appuyée par le témoin libre, mais le critère de sélection TT0 proposé est incorrect pour le contexte observé. Aucun remplacement silencieux de contact ni force ajoutée aux scènes entières. Matrice surfacique toujours d’itération, pas jacobien exact ; domaine libre élastique uniquement.

## 5. Résultats dérivés

La régression libre du nouveau binaire passe 23critères, avec TH terminal 1.0ms, résidu énergie 2.378543902e-08J et résidu impulsion/support 2.715480001e-08Ns, aux seuils A67 inchangés. Charge positive et refus statique préviennent une acceptation universelle de zéro. Le critère neuf zéro dynamique reste échoué, ainsi que les deux CHECK entiers. Il faut préparer une sélection par le contexte CHECK explicite et mesurer les flags/horloges dans la prochaine variante, sans rejouer l’ancien lot ni réinitialiser son budget.

## 6. Contradictions et informations manquantes

Compilation/NORMAL ne sont pas réussite de la garde ou de l’impact. La proposition A70 TT0 reste conservée comme nouvelle tentative ratée ; source audit15contrôles et compilation ne l’avaient pas qualifiée nativement. Les107391 avertissements de coefficients transformés et cinq TYPE25 restent bloquants. Les flags IDYNA/IQSTAT/IMP_CHK/TT/NCYCLE à l’appel manquent encore ; pas de valeur inventée. A52nonintégrée, inerties, matériaux, contacts et bilans locaux entiers non qualifiés. A71 six Engine/un Starter entièrement consommés. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet, aucun temps de témoin crédité.

AIRCRAFT-A72 : audit/proposition en lecture seule de la sélection CHECK, à partir du nouvel échec A71. Le moteur avance TT avant IMP_CHKM ; la garde TT==0 ne correspond pas au contexte du premier contrôle. Préparer une sélection explicite par IMP_CHK>0, sans temps absolu supposé, et des observations des flags/horloges dans les futurs contrôles. A71 huitième moteur compilé exactement après accord ; six Engine et un Starter autorisés consommés, aucun replay ou crédit entier. Dynamique libre1ms et charge positive R2=4 passent ; zéro statique reste refusé comme prévu ; zéro dynamique et deuxCHECK entiers restent échoués avec R2=0. Conserver cette nouvelle garde ratée et toutes les anciennes sorties/critères/budgets. Les 107391 avertissements et cinq TYPE25 par scène sont bloquants. Toute nouvelle modification/compilation et lot natif exigent une proposition concrète et un accord distinct. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.
