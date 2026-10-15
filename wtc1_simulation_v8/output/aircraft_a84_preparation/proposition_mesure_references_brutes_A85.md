# Proposition A85 — mesurer les références brutes sans modifier le moteur

A83 a révélé énergieInfinity dès1 et déplacementNaN dès2, puis arrêt79/ISTOP−2. Le seul Engine autorisé est consommé. La source définit RE=DE0/EIMP et RU=LS(3)*sqrt(DU2/U2), avec un plancher positif de DE0. Des dénominateurs nuls constituent une hypothèse compatible ; leurs valeurs réelles ne sont pas encore mesurées. Changer les tolérances ou remplacer les non-finis par zéro n’est pas proposé.

Un seul Engine A73 inchangé est proposé sous un observateur qui lit les valeurs brutes aux premières itérations0à2. Même restart initial propre A81, même carte A83, chargement, trois tolérances, pas initial/minimum/maximum et horizon identiques. Zéro Starter, correctif, compilation, GPU, installation ou prolongement entier. UnCPU, plafond180s, estimation5–30s. Vérifier auparavant la publication A82+A83.

Quatre points d’exécution matériels au maximum, sur le processus enfant propre. Lecture seule des données numériques, sans remplacement d’instruction, modification de données ou registres numériques. Les seuls registres configurés sont les registres matériels de débogage ; les signaux sont transmis. Les points sont tous désactivés après l’entrée du critère à l’itération2 ; l’Engine poursuit jusqu’à son arrêt propre. Un plafond de64arrêts d’observation protège les captures ; tout échec consomme sa seule place, sans réessai automatique.

Mesures : DE0,EIMP,R02 et vecteurF libre, normes natives U2 et DU2 à leur retour, ratiosUR/RR/ER transmis au critère, D/DD des huit nœuds. Le résidu carré recalculé depuis F sur un seul domaine sera identifié comme dérivé, jamais confondu avec une variable native non lue. Les numéros d’itération sont observés ; aucune capture du temps/cycle global n’est promise. La correction d’interprétation de la ligne0 (grandeurs initiales absolues plutôt que ratios) est documentée dans A84.

La signature source épinglée, les indices d’arguments, trois symboles du binaire actuel, empreintes et bornes du lecteur sont vérifiés statiquement. Le déroulement effectif sous cet observateur demeure à qualifier. Une mesure de dénominateurs nuls n’autorisera pas un correctif automatique : il faudra définir et approuver séparément tout changement du moteur ou de la mécanique.

Nouvel accord explicite requis pour ce lot, distinct d’A83 consommé. Compression, rupture et refermeture restent non mesurées. Anciennes sorties, budgets, critères échoués et107391avertissements conservés ; aucun temps physique entier supplémentaire. Dix secondes et vidéo3D incomplètes.
