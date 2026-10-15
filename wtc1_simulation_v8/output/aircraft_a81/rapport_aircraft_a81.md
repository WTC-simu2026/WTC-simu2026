# AIRCRAFT-A81 — préparation propre, arrêt sur la limite de pas

Le lot autorisé est terminé : un Starter et un Engine consommés, aucun relancement. La préparation passe mais le calcul s’arrête avant le premier état sauvegardé à temps positif. Compression, rupture et refermeture restent non observées.

## 1. Faits directement observés ou transcrits

Accord « Oui, exécuter le témoin A81 après vérification de la publication », receipt request_user_input_async/call_a5c8cd61518347429f6bb01020760042/0. Publication A78+A79 vérifiée avant déclaration et exécution. Entrées A80 exactes, logiciels inchangés et empreintes contrôlées. UnCPU, plafond180s chacun, zéro GPU/installation/correctif/compilation/extension entière. Starter6.945s, code0, zéro erreur/zéro avertissement, restart initial valide. Matériau LAW117, critères1/1, ISYM0, EN4400, ET800, TN450, TT100, GI/GII50 et seuilmodeI0,2222222mm réellement imprimés. Masse8g et ADMAS8g instrumentaux.

Engine4.955s, code2, aucun dépassement. MESSAGE79 : arrêt implicite sur limite de pas, ISTOP−2. Les minima et maxima0,000125ms sont conservés. La matrice libre a huit inconnues ; factorisation MUMPS sans pivot négatif imprimé. Cela ne prouve pas la convergence non linéaire. Les avertissements PARITH/ON incompatible et formulationISOLID0 générique sont conservés séparément.

## 2. Résultats d’un modèle officiel

Aucun résultat historique officiel nouveau. Les définitions logicielles documentées et le modèle de sortie TH3040 servent à lire les observations, sans être assimilés à une validation mécanique. Les valeurs de la carte courte sont cette fois vérifiées dans la sortie native propre au témoin.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée ou modifiée. Les copies privées de sources logicielles sont distinctes, sans modification de binaire. Aucun dégât connu ajusté.

## 4. Hypothèses propres au modèle

Graine1102092, zéro tirage, unitésg/mm/ms. Coupon indépendant8nœuds/100mm², cartes cohésives actuelles exactes, aucune compensation de masse de l’avion. La trajectoire prévue−0,05/+0,3/−0,05mm et l’horizon0,65ms ne sont pas des résultats : ils n’ont pas été parcourus. La borne minimale égale au pas initial devait arrêter une réduction ; ce refus reste un résultat, sans abaissement après coup. La cause précise du premier refus non linéaire n’est pas déduite du seul message générique.

## 5. Résultats dérivés

Le fichier TH natif contient exactement un état, à0ms. Son schéma lie les groupes, nœuds, variables et élément présents ; le lecteur Python a été comparé au CSV natif A67 sauvegardé sur8001lignes/99colonnes, sans exécution native rejouée. Le CSV A81 est une transcription du binaire initial, pas un second convertisseur ni un historique reconstruit. Une seule animation initiale est présente. Aucun plateau, force après rupture, travail de fracture ou dommage n’est qualifié ; les zéros USR initiaux ne signifient pas que leur peuplement est validé.

Le premier contrôle du nouveau lecteur de préparation confondait les lignes de seuil et de fonction de seuil TN/TT : R0 est conservé, la sélection de préfixe a été corrigée et testée sur la sortie A67 sauvegardée avant tout lancement. Ce correctif de lecteur propre n’a changé aucune carte physique, binaire ou budget.

## 6. Contradictions et informations manquantes

L’objectif du coupon n’est pas atteint. Ni rupture ni compression après refermeture ne sont mesurées ; aucune conclusion sur la politique de contact n’est autorisée à partir de l’état initial. La tolérance énergétique A67 de1e−7J est conservée, sans faux succès d’un bilan portant seulement sur0ms. L’Engine ne disposait pas d’impression détaillée des critères Newton ; il faut les observer avant de modifier les pas ou les tolérances. Les deux places natives sont consommées ; aucun remplacement automatique. A75/A77/A79,107391avertissements A73, limites et budgets restent conservés. Meilleur impact entier0,0200001220703125s ; dix secondes puis vidéo3D incomplètes.

AIRCRAFT-A82 : après publication A80+A81 vérifiée, diagnostiquer en lecture seule l’arrêt au premier pas imposé A81, message79/ISTOP−2, sans rupture ni refermeture observées. Préparer une observation des critères de convergence au premier essai, avec impression nonlinéaire détaillée et restart initial A81 réutilisé, sans modifier le chargement, les tolérances, le minimum/maximum de pas, le moteur ou les paramètres physiques. Toute nouvelle exécution nécessite une proposition concrète et accord distinct : les1Starter+1Engine A81 sont consommés. Ne pas abaisser silencieusement le pas minimum ni compter l’état initial comme trajectoire. Les impulsions de plateau, USR, dégâts, compression après rupture et retour en contact restent non mesurés. Conserver erreurs, avertissements, refus R0, limites et budgets antérieurs. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
