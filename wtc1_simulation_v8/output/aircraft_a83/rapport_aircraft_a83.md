# AIRCRAFT-A83 — valeurs non finies dans les critères Newton

L’unique Engine autorisé est terminé. L’impression détaillée fournit les premières valeurs manquantes, mais aucune trajectoire à temps positif. Le succès complet de l’observation reste refusé : les références brutes et le temps/cycle tenté ne sont pas imprimés.

## 1. Faits directement observés ou transcrits

Accord A83 reçu, receipt request_user_input_async/call_3e99b79a34d14243b0cdbbaca9e5799b/0 ; publication A80+A81 vérifiée avant déclaration. Un EngineCPU1/plafond180s, zéro Starter/correctif/compilation/GPU/installation. Durée4.774s, code2, aucun dépassement. Restart initial exact du Starter A81 et carte Engine identique sauf /IMPL/PRINT/NONLIN/-1. La sortie confirme NPRINT−1, les trois tolérances1e−11 et les deux bornes de pas0,000125ms.

La table donne31lignes, itérations0à30. À0 : déplacement0, force1, énergie0. À1 : déplacement1, force0, énergieInfinity. De2à30 : déplacementNaN, force0, énergieInfinity. Ce sont des ratios nativement imprimés à leur précision, pas des valeurs de forces ou déplacements bruts. Les reformations de matrice sont marquées0,1,7,13,19,25. Le message « MAX_ITER REACHED » précède « RESET ITERATION WITH NEW TIMESTEP », puis MESSAGE79/ISTOP−2. Les avertissements PARITH/ON et ISOLID0 restent conservés.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La fonction d’impression logicielle révèle des valeurs de convergence du modèle numérique courant ; elle ne qualifie aucun mécanisme physique réel. Aucune correspondance avec des dégâts connus recherchée.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée ou modifiée. Aucun ancien diagnostic natif rejoué. Les sources logicielles privées épinglées restent distinctes des sources historiques.

## 4. Hypothèses propres au modèle

Graine1102105, zéro tirage, unitésg/mm/ms et hypothèses A81 conservées. Le premier temps tenté0,000125ms est une inférence du pas initial et du restart à0, pas une ligne temps/cycle imprimée ou un état accepté. Un ratio de force affiché0 ne prouve pas un résidu brut exactement nul. Infinity et NaN ne permettent pas d’attribuer seuls une division par zéro ou sa cause à un champ précis.

## 5. Résultats dérivés

Les31lignes sont transcrites avec numéros de ligne, chaînes d’origine et classes finite/NaN/positive_infinity, dans JSON strict et CSV. Le fichier TH contient un unique état réel à0ms ; une animation initiale seulement existe. L’impression a donc fourni une observation partielle utile : la normalisation énergie devient non finie dès1, puis déplacement dès2, avant le refus à30. Les numérateurs et références bruts n’étant pas imprimés, le critère complet d’observation reste échoué. Le prochain travail doit examiner leur définition et les conditions au premier pas, sans modifier les tolérances ou masquer les non-finis.

## 6. Contradictions et informations manquantes

Aucun état à temps positif accepté et sauvegardé ; compression, rupture, refermeture, impulsions de plateau, travail de fracture et peuplementUSR restent non mesurés. La cause unique n’est pas établie. Le seul Engine A83 est consommé, sans remplacement ni relance ; A81 et anciens budgets restent consommés. Aucun correctif du moteur n’est autorisé par ce lot. Échecs antérieurs,107391avertissements A73, budgets et sorties conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

AIRCRAFT-A84 : après publication A82+A83 vérifiée, examiner en lecture seule les normalisations des critères Newton de déplacement et énergie et les références au premier pas imposé. A83 imprime31lignes, itérations0à30 : force normalisée0 dès1, énergie Infinity de1à30, déplacement NaN de2à30, puis maximum d’itérations et limite de pas79/ISTOP−2. Numérateurs/dénominateurs bruts et temps/cycle tenté ne sont pas imprimés ; aucune cause unique encore prouvée. Préparer une proposition concrète avant toute nouvelle exécution ou modification du moteur. Le seul Engine A83 est consommé, zéro Starter ; aucun réessai. Ne pas neutraliser les critères, abaisser silencieusement le minimum ou attribuer une trajectoire à l’état initial. Compression, rupture et refermeture restent non mesurées. Conserver anciennes sorties, budgets, 107391avertissements et critères échoués. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
