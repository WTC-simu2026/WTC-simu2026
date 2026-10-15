# AIRCRAFT-A86 — proposition bornée pour les critères relatifs dégénérés

Préparation statique uniquement : aucun correctif appliqué, aucune compilation, zéro Engine/Starter. Le changement de définition des deux ratios est explicite et limité au sous-espace exactement nul observé ; les tolérances restent conservées.

## 1. Faits directement observés ou transcrits

A85 mesure la force libre nulle, toutes les correctionsDD nulles,DE0=1e−20,EIMP=0,U2=DU2=0 et le déplacement normal imposé non nul. Les rapports et captures restent conservés. La source préparée provient du cache épinglé, sans modification d’un arbre opérationnel.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La recette logicielle A73 est reprise sans changement de dépendance. Les divisions d’origine restent exactes hors de la nouvelle garde ; CRIT_ITE est conservée intégralement.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée. Le diff et la copie logicielle proposés restent privés sous licence source, exclus du manifeste propre de publication. Neuf anciens moteurs, sources et résultats restent intacts.

## 4. Hypothèses propres au modèle

Graine1102109, zéro tirage. Choix numérique proposé : attribuer0 aux deux erreurs relatives indéfinies seulement lorsque les inconnues libres sont exactement en équilibre et sans correction. Ce choix est un changement algorithmique explicite, pas une propriété physique mesurée. Il ne calcule pas le travail imposé et ne démontre ni rupture ni conservation énergétique. Une garde très restrictive évite d’étendre le choix aux mouvements libres non nuls ou aux contacts. Le chemin de l’itération1 reste inchangé et sonInfinity possible reste visible.

## 5. Résultats dérivés

Un seul fichier moteur proposé, gardes exactes, pas de seuil heuristique supplémentaire. Le bloc original non dégénéré et la fonction de convergence sont textuellement conservés. Le prototype mathématique vérifie le cas observé et rejette les variantes hors portée, sous-normales/non finies et chacune des composantes de force/correction non nulles. Les lignes nouvelles respectent le format fixe. Ce contrôle Python statique n’est pas une exécution du codeFortran. Deux régressions A67 sauvegardées doivent être confrontées au nouveau binaire, puis la boucle A81 seulement si elles passent ; un CHECK entier reste conditionnel aux qualifications locales, jamais un prolongement d’impact.

## 6. Contradictions et informations manquantes

Le correctif n’est ni appliqué ni compilé et son comportement natif reste inconnu. La boucle A81 pourrait encore échouer après le premier pas, notamment sur une loi, l’historiqueUSR, le travail imposé ou les critères d’énergie. Le seuil indépendant1e−7J est maintenu ; aucun succès ne sera accordé au seul changement des ratios. Accord distinct requis pour un dixième moteur isolé et quatreEngine au plus ; A85consommé n’autorise aucune modification. Les cinq contactsTYPE25,107391avertissements, limites, budgets et échecs antérieurs restent bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

AIRCRAFT-A87 proposée non exécutée : nouveau traitement A86 des critères relatifs exactement nuls, moteur isolé numéro10, application/compilation seulement après accord explicite distinct. Plafond compilation1h/6CPU, puis au maximum4EngineCPU1/180s, zéro Starter/GPU/installation. Deux régressions libres anciennes avec le nouveau binaire, puis boucle A81 ; CHECK entier uniquement si toutes les qualifications locales passent. Aucun prolongement dynamique entier. Garde limitée Newmark non quasi-statique, Newton modifié, trois critères123, mouvement imposé, sans interface générale/rotation, un domaine/un thread, itération>=2, force libre et correction exactement nulles, référencesEIMP=0/DE0=1e−20 et normesU2=DU2=0. Les tolérances et le chemin non dégénéré restent inchangés ; l’itération1 conserve son ancien affichageInfinity. Le critère relatif reçoit0 dans ce seul sous-espace nul ; cela ne valide pas l’énergie physique indépendante. A85consommé, aucun nouveau correctif appliqué ou compilé ; budgets, échecs et sorties conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
