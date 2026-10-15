# AIRCRAFT-A90 — proposition de correction nulle après projection native

## 1. Faits directement observés ou transcrits

A89 observe les quatreDD imposés non nuls et les normes libres nulles au second essai, cycle2/temps0,00025ms. La première gardeA86 échoue surALLDD brut. Les sources proposées restent distinctes des sources opérationnelles ; zéro Engine/Starter et aucune compilation pendantA90.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Le candidat reprend exactement l’ordreIMP_SETB puisCONDENS_B du calcul natif de norme librePRODUT_UHP, mais teste les composantes du vecteur libre plutôt que le seul carré. Le contrôle de sous-débordement est ainsi explicite.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée/modifiée. Diff et copie logicielle proposés restent privés sous licence source, exclus du manifeste propre public. Les dix anciens moteurs restent conservés.

## 4. Hypothèses propres au modèle

Graine1102115, zéro tirage. Le choix deA86 pour les erreurs relatives dans le sous-espace nul reste conservé, avec toutes ses restrictions ; seul le test de correction nulle devient cohérent avec les coordonnées libres. LesD/DD non finis bruts sont explicitement rejetés même s’ils seraient retirés par la projection. Cela ne calcule pas l’énergie physique ni la rupture. L’ancienInfinity à1 reste conservé.

## 5. Résultats dérivés

Un seul fichier modifié dans la proposition, auxiliaire ajouté dans ce même fichier. Le reste de la sourceA87 est reconstruit exactement en retirant ces changements. Le prototype rejette les non-zéros libres sous-normaux et toutes les données non finies testées, mais accepte le casA89 où seules les commandes imposées corrigentDD. Il n’est pas une exécutionFortran. RecetteA87 et quatre contrôles conditionnels préparés : deux régressions, boucle originale, puisCHECK uniquement si toutes les portes locales passent ; mêmes entrées et mêmes seuils.

## 6. Contradictions et informations manquantes

Correctif non appliqué/non compilé, comportement natif encore inconnu. Une meilleure convergence ne qualifie pas l’énergie, les champs, rupture ou refermeture. Le seuil1e−7J de la boucle et tous échecs antérieurs restent conservés. Nouvel accord explicite requis pour un onzième moteur isolé et son lot ; le seul EngineA89 est consommé et le CHECK conditionnelA87 ne couvre pas cette proposition. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

AIRCRAFT-A91 proposée non exécutée : appliquer le correctifA90 de correction exactement nulle après projection/condensation native, puis compiler un onzième moteur isolé, seulement après accord distinct. Plafond1h/6CPU, puis au maximum4EngineCPU1/180s, zéroStarter/GPU/installation : deux régressions, boucleA81 conditionnelle, CHECK entier conditionnel à toutes les qualifications locales. Aucun impact entier prolongé. Le vecteur libre exact doit être nul ; les non-zéros sous-normaux et les D/DD non finis restent exclus. Les mouvements imposés finis ne sont plus confondus avec une correction libre. Toutes les autres gardesA86, tolérances et budgets physiques conservés. Correctif préparé nonappliqué noncompilé ; A89consommé ne couvre aucune modification. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
