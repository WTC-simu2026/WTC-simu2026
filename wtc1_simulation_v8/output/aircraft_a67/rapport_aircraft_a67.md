# AIRCRAFT-A67 — aire courante compilée, contrôle entier toujours refusé

Le septième moteur isolé applique exactement le correctif A66 autorisé. Six témoins locaux passent dans leur domaine déclaré ; les deux CHECK entiers ne signalent plus les 624 volumes nuls, mais restent échoués. Aucun prolongement d’impact entier.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, appliquer et compiler ce correctif A66 » et empreintes du plan, de la proposition, de la différence et de la source enregistrés avant exécution. Première compilation réussie en 291.077 s, plafond 3600 s, six CPU, sans GPU ni installation ; Starter non recompilé. Source pin 3d75ff13d1946f6d28a43920eac4fa2aae41b27a, binaire SHA256 89a87631eb2e7f87db29e03247717556818567e41feb7fa2e768a10e03b642f8. Anciennes corrections autorisées conservées ; ancienne branche Ismstr1 byte à byte préservée. Huit Engine sur un CPU avec plafond 180 s chacun, six Starter propres : budget entièrement consommé, aucun replay.

| Témoin | Critères locaux | Dernier TH ms | Résidu énergie dans le domaine J | Résidu impulsion/support Ns |
|---|---:|---:|---:|---:|
| FREE_Ismstr4 | 23 | 1.0 | 2.3785439e-08 | 2.71548e-08 |
| FREE_Ismstr4_HALF | 23 | 1.0 | 4.4794855e-08 | 4.808432e-08 |
| RIGID_ROTATED_FREE | 23 | 1.0 | 1.3629603e-08 | 5.187022e-08 |
| AREA_x4_FREE | 23 | 1.0 | 2.3785439e-08 | 2.71548e-08 |
| NONUNIFORM_AREA_FREE | 22 | 1.0 | 3.1440992e-12 | 3.213922e-10 |
| AREA_EVOLUTION_FREE_Y | 23 | 1.0 | 7.5163635e-08 | 6.75896e-08 |

Les 137 critères locaux passent, ainsi que les deux comparaisons demi-pas au seuil inchangé 1,01e-5 J : KE 5,47014241452e-6 J, IE 5,49140000000e-6 J. Chaque TH atteint réellement 1 ms. Les cinq cas à translations supérieures libres qualifient leurs bilans globaux ; le sixième prescrit X commun et qualifie seulement Y libre. Son aire évolue de 100 à 110 mm². Les anciens indicateurs génériques « all_top_translations_free » ne décrivent pas ce sixième cas ; les métadonnées initiales restent conservées et une clarification explicite accompagne les cartes réelles.

Dans chaque CHECK entier : code 0, NORMAL et fin du CHECK, mais une erreur « IMPLICIT LOADING DATA », 107391 avertissements de connexion possible et cinq TYPE25 ignorés, soit 107396 avertissements. Zéro avertissement de raideur nulle, zéro STOPvolume et aucun STOP66. Les 107391 directions sont 35722 de chaque rotation et 75 de chaque translation. La valeur native R2 du chargement n’est pas imprimée. Les cartes contiennent déjà /IMPL/DYNA/2. Les anciennes initialisations et cartes entières sont identiques, empreintes vérifiées. Le premier champ CHECK_errors=null est conservé ; les messages détaillés et décomptes affichés déterminent l’échec.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les routines natives du pin déclaré servent à distinguer construction de matrice, forces/histoires de matériau et règles CHECK. La matrice ajoutée utilise les quatre aires Gauss projetées de la face médiane courante pour TYPE43/LAW117/Ismstr4. Elle ne lit pas VOL de référence. Le message générique ISOLID0 reste présent ; sa présence n’annule pas la sélection particulière vérifiée. Ces résultats logiciels ne valident pas une reconstruction historique de l’impact.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF consulté ou modifié. Aucun dommage connu n’est ciblé. Les surfaces et matériaux instrumentaux sont distincts de mesures réelles d’une jonction Boeing/façade.

## 4. Hypothèses propres au modèle

Graine 1102092, zéro tirage. Unités g/mm/ms, force N, énergie native N·mm convertie en J. Masse instrumentale 8 g sans masse ajoutée. Les variantes testent demi-pas, orientation initiale rigide, aire multipliée par quatre, trapèze à petite amplitude et aire évolutive prescrite. La matrice reste symétrique EN/ET, sans dérivée d’aire, de repère ou de dommage : matrice d’itération, pas jacobien exact. Aucun seuil physique assoupli, volume fictif, force de chargement ajoutée ou terme RKE compensateur.

## 5. Résultats dérivés

Les sorties binaires/CSV et tous les pas sont vérifiés. Les vitesses physiques libres sont reconstruites par la relation Newmark, confrontées aux bilans natifs et à la référence indépendante. Le trapèze est comparé à la limite de petite amplitude, sans qualification non linéaire générale. La rotation teste la covariance d’orientation initiale, pas une grande rotation dynamique. Le travail complet aux quatre points, utilisant chaque saut interpolé, est analysé séparément et passe au seuil préexistant ; l’ancien diagnostic par saut moyen reste préservé et n’est pas supposé exact pour le trapèze. Les 624 erreurs volumiques observées en A65 sont résolues dans les deux CHECK, mais les contrôles restants ne sont pas admissibles. Les anciennes sorties sont vérifiées par métadonnées et les six anciens moteurs isolés par empreinte.

## 6. Contradictions et informations manquantes

Les avertissements de connexion possible ne prouvent pas encore une déconnexion géométrique : DIAG_M doit être suivi depuis sa construction et normalisation. L’erreur de chargement ne prouve pas que la vitesse initiale est absente ; LB/R2 nécessite un audit distinct. Les cinq contacts TYPE25 ignorés demeurent bloquants. A52 reste non intégrée. Dommage général, retour arrière d’état, rotation dynamique, inerties, domaines matériaux et bilans locaux entiers non qualifiés. X prescrit dans le témoin évolutif ne qualifie pas les compteurs globaux KE/P ; échecs A62/A63/A64 et tous les budgets antérieurs préservés. Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D incomplètes. Aucun temps de témoin crédité à l’objectif.

AIRCRAFT-A68 : audit borné en lecture seule des deux nouveaux CHECK A67 et des sources figées du même moteur. Tracer la création/normalisation de DIAG_M, la branche de chargement LB/R2 et le rôle des 75 nœuds de translation signalés ; examiner séparément les cinq contacts TYPE25 ignorés et leur équivalence mécanique éventuelle. Réutiliser les sorties A67, sans nouveau Starter/Engine ni modification/compilation. /IMPL/DYNA/2 est déjà présent dans les cartes. Ne pas ajouter de force fictive, masquer les messages, changer RREF ou les seuils sans preuve et protocole déclaré. A67 est compilée ; les huit Engine autorisés sont consommés. Six témoins locaux passent dans leur domaine déclaré, dont aire évolutive limitée à Y libre. Les deux CHECK entiers échouent chacun : une erreur de chargement implicite, 107391 avertissements de connexion possible et cinq TYPE25 ignorés ; les 624 STOP de volume sont résolus. A52 reste non intégrée, aucun impact entier prolongé. Toute nouvelle modification/compilation ou nouveau lot natif nécessite une proposition concrète et un accord distinct. Préserver budgets, sorties, échecs et bilans sans RKE compensateur. Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D restent incomplètes.
