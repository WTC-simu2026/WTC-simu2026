# AIRCRAFT-A87 — dixième moteur isolé et contrôles bornés

Le correctif autorisé A86 est appliqué et compilé dans un nouveau moteur isolé. Les résultats locaux et critères encore échoués restent séparés de l’objectif des dix secondes d’impact entier.

## 1. Faits directement observés ou transcrits

Accord « Oui, appliquer le correctif A86, compiler et exécuter A87 », receipt request_user_input_async/call_a7e8e12bd9604e8ea2f8c1de6ddb4d3f/0. Publication A84+A85 vérifiée avant déclaration. Diff exact, un seul nouveau fichier moteurNL_SOLV ; toutes les corrections A73 précédentes conservées. Compilation309.388s, sixCPU, dans le plafond1h, sans GPU/installation/Starter compilé. BinaireSHA2569e72f04411158c9b48f67968eff3fe01f741aca5cb5bd3201985cdbaf75e27cd. Neuf anciens moteurs conservés.

- FREE_Ismstr4 : code0, 20.971s ; porte locale=True.
- AREA_EVOLUTION_FREE_Y : code0, 18.705s ; porte locale=True.
- COMPRESSION_RUPTURE_RECLOSE : code2, 0.602s ; porte locale=False.

3Engine utilisés sur4maximum, unCPU/plafond180s chacun, zéro Starter/convertisseur natif. Places conditionnelles inutilisées=1, non réaffectées. CHECK entier exécuté=False. Aucun prolongement dynamique entier.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Le solveur est une variante locale documentée, sous licence source. Ses régressions utilisent les cartes et résultats numériques A67 sauvegardés, pas des dégâts historiques comme cible. Une compilation ou une terminaison normale ne valide pas sa mécanique.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée/modifiée. Le cache logiciel est réutilisé à empreintes vérifiées ; aucun téléchargement ou changement de dépendance. Les sources et binaires tiers restent dans les répertoires privés, séparés des livrables propres. Aucun ancien calcul rejoué : les régressions évaluent le nouveau binaire face aux anciens résultats sauvegardés.

## 4. Hypothèses propres au modèle

Graine1102110, zéro tirage, unitésg/mm/ms conservées. La nouvelle garde définit les deux ratios relatifs à0 seulement dans le sous-espace libre exactement nul, sous les restrictions A86 ; elle change explicitement cette définition dégénérée, sans modifier les tolérances ou le chemin non nul. L’itération1 conserve sonInfinity possible. La garde ne calcule pas l’énergie totale physique ou le travail imposé. Masses, cartes matérielles et chargements sont ceux des cas référencés ; la masse8g du coupon est instrumentale.

## 5. Résultats dérivés

Les histoires nouvelles sont décodées en Python, sans convertisseur natif. Les deux régressions comparent chaque canal au binaire sauvegardé, puis reprennent l’analyse mécanique A67 et ses seuils d’origine sur les nouvelles sorties. La transcription CSV porte explicitement son originePython, avec labels liés au schéma natif exact.

La boucle enregistre2états TH, dernier temps0.000125000006ms, marqueurs de garde1. Force de plateau avant=NoneN, après refermeture=NoneN, par pente de l’impulsion de réaction des supports. Résidu énergétique maximal calculé=1.39044726e-12J pour le seuil inchangé1e−7J ; différence KE nodale reconstruite/native=1.824894e-12J. Les contrôles échoués sont : normal_Engine_and_positive_time_target, pre_rupture_compression_plateau_reference, post_reclosure_compression_plateau_reference, prescribed_top_Z_target_reclosed, native_USR_population_qualified, native_damage_and_rupture_semantics_certified, full_reaction_work_independent_closure_certified. Les plages natives de chaque champ sont conservées ; leur présence ou un changement ne certifie pas seul le dommage. Le travail indépendant des réactions et la sémantique des champs doivent être examinés sans crédit physique implicite.

Dernier temps local sauvegardé0.000125000006ms, 1états positifs. Cette durée locale n’ajoute aucun temps à l’impact entier et ne constitue pas un film de dix secondes.

## 6. Contradictions et informations manquantes

Qualification physique locale incomplète ; les échecs sont conservés. La fermeture énergétique indépendante, les champsUSR/dommage et la compression après rupture doivent être évalués selon les observations réellement disponibles. Aucun bilan ne sera fermé avec un termeRKE inventé, ni avec un seuil accru après coup. Le CHECK conditionnel ne peut pas être exécuté si les critères locaux restent échoués. Les cinqTYPE25 ignorés,107391avertissements et tous anciens budgets/échecs restent bloquants. Les places conditionnelles non utilisées ne deviennent pas des crédits pour un autre essai. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

AIRCRAFT-A88 : après publication A86+A87 vérifiée, analyser en lecture seule les nouveaux états A87 sauvegardés et leurs critères encore échoués. Distinguer la garde numérique des cas nuls, les régressions à seuils inchangés, le parcours commandé du coupon et ses qualifications physiques. Ne pas confondre durée locale en millisecondes et impact avion entier. Rechercher les valeurs de réaction, énergie et champs réellement disponibles avant une nouvelle proposition ; ne pas rejouer les diagnostics vérifiés. Aucun nouveau lancement automatique : les places utilisées A87 sont consommées et le CHECK conditionnel inutilisé ne devient pas un crédit générique. Toute autre modification du moteur ou exécution hors lot demande une proposition et un accord distinct. Conserver tolérances, budgets physiques, sources, sorties, critères échoués, cinqTYPE25 ignorés et107391avertissements. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
