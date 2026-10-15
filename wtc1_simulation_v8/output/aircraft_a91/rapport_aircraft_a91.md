# AIRCRAFT-A91 — onzième moteur isolé et contrôles bornés

Le correctif autorisé A90 est appliqué et compilé dans un nouveau moteur isolé. Les résultats locaux et critères encore échoués restent séparés de l’objectif des dix secondes d’impact entier.

## 1. Faits directement observés ou transcrits

Accord « Oui, appliquer le correctif A90, compiler et exécuter A91 », receipt request_user_input_async/call_eb3cec6ec1704469a8b062d90392f066/0. Publication A88+A89 vérifiée avant déclaration. Diff exact A90, un seul fichier moteur NL_SOLV modifié ; toutes les corrections A73 et A86 précédentes conservées. Compilation320.630s, sixCPU, dans le plafond1h, sans GPU/installation/Starter compilé. BinaireSHA25604e260a0f090153f899bf6300dbaff82c51aa0d3eb95ca8c0aa54d7c5d359e6c. Dix anciens moteurs conservés.

- FREE_Ismstr4 : code0, 21.076s ; porte locale=True.
- AREA_EVOLUTION_FREE_Y : code0, 18.832s ; porte locale=True.
- COMPRESSION_RUPTURE_RECLOSE : code0, 25.072s ; porte locale=False.

3Engine utilisés sur4maximum, unCPU/plafond180s chacun, zéro Starter/convertisseur natif. Places conditionnelles inutilisées=1, non réaffectées. CHECK entier exécuté=False. Aucun prolongement dynamique entier.

Le calcul local termine normalement. Son premier export d’analyse a échoué sur la sérialisation JSON d’un booléen NumPy. Le fichier partiel et l’exception sont conservés ; une lecture séparée des mêmes sorties corrige uniquement cet export, sans changement des formules/seuils et sans nouveau lancement natif. Les contrôles initiaux restent archivés avec leur échec d’analyse ; le supplément R1 contient la récupération.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Le solveur est une variante locale documentée, sous licence source. Ses régressions utilisent les cartes et résultats numériques A67 sauvegardés, pas des dégâts historiques comme cible. Une compilation ou une terminaison normale ne valide pas sa mécanique.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée/modifiée. Le cache logiciel est réutilisé à empreintes vérifiées ; aucun téléchargement ou changement de dépendance. Les sources et binaires tiers restent dans les répertoires privés, séparés des livrables propres. Aucun ancien calcul rejoué : les régressions évaluent le nouveau binaire face aux anciens résultats sauvegardés.

## 4. Hypothèses propres au modèle

Graine1102116, zéro tirage, unitésg/mm/ms conservées. La nouvelle garde définit les deux ratios relatifs à0 seulement dans le sous-espace libre exactement nul, sous les restrictions A86 conservées, après projection de la correction par IMP_SETB puis CONDENS_B et rejet des valeurs D/DD non finies ; elle change explicitement cette définition dégénérée, sans modifier les tolérances ou le chemin non nul. L’itération1 conserve sonInfinity possible. La garde ne calcule pas l’énergie totale physique ou le travail imposé. Masses, cartes matérielles et chargements sont ceux des cas référencés ; la masse8g du coupon est instrumentale.

## 5. Résultats dérivés

Les histoires nouvelles sont décodées en Python, sans convertisseur natif. Les deux régressions comparent chaque canal au binaire sauvegardé, puis reprennent l’analyse mécanique A67 et ses seuils d’origine sur les nouvelles sorties. La transcription CSV porte explicitement son originePython, avec labels liés au schéma natif exact.

La boucle enregistre5201états TH, dernier temps0.649999976ms, marqueurs de garde5200. Force de plateau avant=-22000.006638469316N, après refermeture=-0.0N, par pente de l’impulsion de réaction des supports. Résidu énergétique maximal calculé=6.15396457e-05J pour le seuil inchangé1e−7J ; différence KE nodale reconstruite/native=3.86075989e-05J. Les contrôles échoués sont : literal_independent_energy_threshold, physical_reconstructed_KE_vs_native, post_reclosure_compression_plateau_reference, native_USR_population_qualified, native_damage_and_rupture_semantics_certified, full_reaction_work_independent_closure_certified. Les plages natives de chaque champ sont conservées ; leur présence ou un changement ne certifie pas seul le dommage. Le plateau initial vaut environ22000N en valeur absolue ; après refermeture il vaut0N, donc la transmission en compression après rupture échoue réellement sur ce témoin. Le résidu issu de la reconstruction des vitesses dépasse aussi le seuil ; les sorties simple précision et la reconstruction doivent être examinées avant d’attribuer cet écart à la mécanique. Le travail indépendant des réactions et la sémantique des champs doivent être examinés sans crédit physique implicite.

Dernier temps local sauvegardé0.649999976ms, 5200états positifs. Cette durée locale n’ajoute aucun temps à l’impact entier et ne constitue pas un film de dix secondes.

## 6. Contradictions et informations manquantes

Qualification physique locale incomplète ; les échecs sont conservés. La fermeture énergétique indépendante, les champsUSR/dommage et la compression après rupture doivent être évalués selon les observations réellement disponibles. Aucun bilan ne sera fermé avec un termeRKE inventé, ni avec un seuil accru après coup. Le CHECK conditionnel ne peut pas être exécuté si les critères locaux restent échoués. Les cinqTYPE25 ignorés,107391avertissements et tous anciens budgets/échecs restent bloquants. Les places conditionnelles non utilisées ne deviennent pas des crédits pour un autre essai. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

AIRCRAFT-A92 : après publication A90+A91 vérifiée, analyser en lecture seule les nouveaux états A91 sauvegardés et leurs critères encore échoués. Distinguer la garde numérique des cas nuls, les régressions à seuils inchangés, le parcours commandé du coupon et ses qualifications physiques. Ne pas confondre durée locale en millisecondes et impact avion entier. Le coupon atteint0,65ms mais ne transmet plus de compression après refermeture ; tracer les états de suppression et les champs TH dans les sources exactes, puis examiner le bilan indépendant des réactions et sa précision. Ne pas rejouer les diagnostics vérifiés. Aucun nouveau lancement automatique : les places utilisées A91 sont consommées et le CHECK conditionnel inutilisé ne devient pas un crédit générique. Toute autre modification du moteur ou exécution hors lot demande une proposition et un accord distinct. Conserver tolérances, budgets physiques, sources, sorties, critères échoués, cinqTYPE25 ignorés et107391avertissements. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
