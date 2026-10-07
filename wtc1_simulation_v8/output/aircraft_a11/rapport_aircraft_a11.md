# AIRCRAFT-A11 — avion couplé, premier contact du nez

A11 est terminée comme diagnostic limité de la nouvelle scène : 4 calculs Engine neufs, sans ancien calcul relancé. La façade n’est plus devant les moteurs : sa translation A07 est inversée exactement et le contact des surfaces extérieures de l’avion est activé. Le nez rencontre la façade vers0,225ms. La fenêtre atteinte est0,4ms, soit0,0004s ; les premières secondes et la traversée historique ne sont pas calculées. Le déficit énergétique local reste un critère échoué et bloque le passage déclaré à1ms. Aucune rupture, érosion ou loi d’écrasement n’est qualifiée.

## 1. Faits directement observés ou transcrits

Starter sans erreur ni avertissement, terminaisons normales et extrémités temporelles récupérées par un observateur séparé qui ne modifie pas les sorties principales. Tous les canaux CSV sont vérifiés contre les records T01 binaires natifs ; les états d’animation et masses nodales sont lus indépendamment. Masse avion native après redistribution≈121962.861144kg, masse totale modèle≈191273.837943kg. L’écart des masses nodales float32 est contrôlé séparément.

Façade : domaine existant couvrant environ59,3m en largeur et10,97m en hauteur, trois étages représentatifs, face avant x=-50mm ; translation[-15468,6,0,0]mm. Nez initial x=0, vitesse hypothétique[-200,5,2]m/s, gap extérieur5mm : estimation de contact(50-5)/200=0,225ms, puis observation native concordante. AIRFRAME commence effectivement à0.2250046ms ; NACELLE/FAN/CORE restent sans contact dans la fenêtre. Les mêmes moteurs couplés, ailes et sous-structures sont conservés. Les groupes de contact ne partagent aucun nœud.

Le libre conserve le mouvement uniforme et ne développe aucune déformation plastique. Son résidu maximal320J est à distinguer de la précision float32 des sorties sur≈2,441GJ ; les mêmes seuils de comparaison sauvegardés sont appliqués. Il n’explique pas les≈6kJ manquants pendant le contact.

## 2. Résultats d’un modèle officiel

La façade représentative et ses propriétés héritent de sources NIST identifiées dans la chaîne de provenance ; cela limite l’indépendance des données d’entrée. Aucun résultat de dommages NIST, aucune pénétration observée ni résultat d’effondrement n’est une cible de réglage. Les sorties présentes sont celles du solveur OpenRadioss dans notre sous-modèle, pas la validation du modèle historique officiel.

## 3. Affirmations d’archives locales

Aucune nouvelle analyse vidéo ni scan d’archive. Sources et sorties sauvegardées A01/A09/A10 réutilisées. 6085 fichiers antérieurs épinglésSHA256 vérifiés inchangés. V11F/V11R préservées, V11S/I02I-M différées. Les premières erreurs de découverte des outils et refus d’aperçu sont sauvegardés dans tooling_discovery_errors.json ; aucun solveur ancien ou logiciel installé/modifié.

## 4. Hypothèses propres au modèle

Configuration aircraft_a11_predeclaration.json déclarée avant calcul, graine1102036, zéro tirage. Géométrie, masse, matériaux, propriétés, RBE3 et assemblages A09 BASE_FINE conservés. La nouvelle scène complète uniquement le domaine des contacts extérieurs et remet la façade devant le nez. Contact radôme lui-même hérité ; auto-contact de l’ensemble de l’avion absent. Radôme TYPE51/TYPE19 sandwich LAW25 de référence, sans reconstruction historique démontrée, écrasement de cœur ni délamination. Aucun transfert de rupture/érosion ; températures, incendie et intérieur complet de la tour absents.

Stfac1 est un candidat numérique hérité ; son bon bilan dans le témoin A10 contraint1D n’est pas une qualification pour l’avion. Les facteursdt_scale0,1/0,05/0,025 sont des multiplicateurs du pas stable natif, pas des pas en millisecondes. Les horizons identiques commencent tous de l’avion intact. Le dernier raffinement conditionnel est décidé sur l’échec sauvegardé du critère énergétique, sans modifier de seuil, de matériau ni de masse.

Seuils numériques hérités : masse1e-6 relative, masse ajoutée1e-9, énergie globale0,5%K0 ; énergie locale |résidu|≤5% énergie générée+1000J dès énergie générée>1000J ; impulsion/appuis10N·s+2%impulsion, demi-pas5%impulsion/10%énergie générée. Domaine matériau : déformation plastique métal≤0,1, diagnostic contrainte des faces radôme≤référence déclarée, zéro plasticité radôme. Les budgets globaux peuvent réussir alors que le budget local échoue : ils sont publiés séparément.

## 5. Résultats dérivés

|Cas|Fin native ms|Jx façade N·s|Énergie générée J|Résidu final J|Max résidu absolu J|Critères échoués|
|---|---:|---:|---:|---:|---:|---|
|FREE_04|0.400070|0.000000|0.000|-320.000|320.000|aucun|
|NOSE_04_DT025|0.400007|-93.888555|8011.863|-5938.137|6430.973|energy_local_within_declared_limit|
|NOSE_04_DT05|0.400037|-93.891031|8012.726|-5937.274|6429.824|energy_local_within_declared_limit|
|NOSE_04_DT10|0.400077|-93.908977|8011.606|-5938.394|6430.463|energy_local_within_declared_limit|

|Demi-pas|Δimpulsion %|Δénergie générée %|Critères impulsion/énergie|
|---|---:|---:|---|
|NOSE_04_DT10 / NOSE_04_DT05|0.015258|0.048614|True/True|
|NOSE_04_DT05 / NOSE_04_DT025|0.002951|0.015294|True/True|

Le dernier cas donne |résidu final|/énergie générée≈74.117%. La constance des impulsions sous raffinement ne suffit donc pas à qualifier le contact. Maximum d’erreur indépendante de variation duKE translationnel≈398.362J ; erreur indépendante de quantité de mouvement≈2.896651N·s. Les limites d’arrondi et de décalage temporel restent présentes ; aucun terme manquant n’est inventé pour fermer le bilan.

KE+RKE global+IE+hourglass+spring+énergies de contact sont additionnés une seule fois, puis travail externe déduit. Le travail plastique est déjà contenu dansIE et n’est pas rajouté. Le RKE par pièce et les inerties du sandwich restent non qualifiés pour un ledger local ; les diagnostics A10 sont préservés. REAC brut représente l’impulsion cumulée confirmée A10, sans réintégration comme force.

États natifs dansr0/*/verified_states_SI.npz ; bilans dansbalance_history_SI.npz ; reconstruction nodale dansindependent_native_mass_diagnostics_SI.npz ; preuves dansnative_mass_reader_proofs.json ethistory_recovery.json. Visualisation hors ligne visualisation/premier_contact.html : déplacements natifs×1, lecture artificiellement ralentie, temps physique affichéms. Figure vectorielle ReportLab visualisation/bilans_et_nez.svg. Données et syntaxe vérifiées ; aperçu GUI non vérifié, serveur local et protocolefile: refusés par les outils. Aucune animation n’est une validation physique.

Temps cumulé des étapes natives et convertisseurs : 633.617s, CPU2threads, pasGPU. Une simple extrapolation linéaire des durées Engine vers1s donne un ordre de grandeur de plusieurs dizaines à plus de cent heures selon le facteur de pas, sans prédire le coût après déformation. Aucun calcul de plusieurs heures n’a été lancé.

## 6. Contradictions, informations manquantes et suite

Le déficit persiste sous raffinement temporel et dépasse le seuil local déclaré. Sa cause n’est pas démontrée ; effets du contact composite, inerties/énergies LAW25/TYPE19, décalages des canaux et discrétisation doivent être discriminés. L’essai de convergence spatiale A10 reste manquant. La direction A11 initiale a été réorientée explicitement par la demande utilisateur vers la scène du Boeing et son premier contact ; ce changement ne transforme pas les contrôles manquants en résultats acquis.

AIRCRAFT-A12 : réutiliser la scène A11 et ses échecs. Isoler le premier contact du nez/radôme dans un témoin sans redistribution RBE3, avec inerties natives et énergie LAW25/TYPE19 vérifiables ; comparer à un témoin élastique simple et à une formulation de contact déclarée. Ajouter le contrôle spatial encore manquant. Ne pas prolonger comme impact qualifié avant fermeture du bilan local. Examiner ensuite le module Boeing parallèle s’il est livré, sans modifier implicitement matériaux/masses. Impact historique, rupture et écrasement restent non qualifiés.

Le deuxième agent dispose d’un prompt et de quatre dossiers propres aircraft_a11_boeing_parallel ; il n’a pas été lancé ni ses résultats supposés livrés par l’agent principal. État/registre restent gérés ici. Une intégration ultérieure devra conserver ses erreurs, contrôler mass/CG/inerties et faire l’objet d’une nouvelle déclaration.

Impact/écrasement historiques non qualifiés ; localisation en flexion après fracture complète non validée ; température imposée distincte d’un incendie calculé ; tests numériques distincts d’une validation de l’effondrement réel ; Blender reste une visualisation. Publication A08+A09 déjà vérifiée. A10+A11 constituent la prochaine paire de diagnostics vérifiables, avec tous les critères échoués ; aucunX/Yoremi.
