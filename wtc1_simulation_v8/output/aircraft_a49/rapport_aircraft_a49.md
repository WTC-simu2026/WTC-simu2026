# AIRCRAFT-A49 — correspondance native et composition exacte des chaînes rigides

Le bloc fautif est identifié dans les peaux inférieures du radôme. Une copie distincte compose144chaînes déjà entièrement rigides : l’assemblage entier atteint désormais la fin de CHECK sans SIGSEGV, avec les RBE3 conservés. Cette avancée logicielle ne qualifie pas le modèle :15directions suspectes et49370messages de connectivité restent présents. Aucun temps d’impact supplémentaire.

## 1. Faits directement observés ou transcrits

Sept préparations Starter et neuf Engine nouveaux, un thread CPU chacun, sans GPU, caps180s. Les lancements instrumentés observent uniquement notre processus fils ; le code de sortie du parent n’est pas assimilé à celui du moteur. Trois observations entières conservent SIGSEGV/code3 : mapping de la variante A48 sans RBE3, variante originale entière avec Idrill1, puis observation de cette option effective. Les petits reproducer et le dernier CHECK entier terminent normalement.

La capture CBAKE3/ASSEMC_KIJ conserve les identifiants originaux IXC(7,I), indices internes et coordonnées. Les128éléments et302nœuds internes correspondent exactement à l’entrée, erreur maximale0mm. Premier élément70513, /SHELL/12171, RADOME_LOWER_FACET_171, propriétéTYPE51/122 et matériauLAW25/4. La paire interne[41005,41002] correspond aux labels[46990,46993]. Le premier nœud est secondaire de la racineRBE2/6014 entièrement rigide et principal du déport cohésifRBE2/3126. Les26paires manquantes partagent ce double rôle. Les déports cohésifs sont non nuls ; ils ne sont pas supprimés.

Les cinq petits cas copient une coque hôte, la coque fautive, et selon le cas une brique cohésive avec deux nœuds déportés contraints. Chaque Starter est sans erreur/avertissement, masse878,5142410262g ; chaque CHECK termine et l’observateur ne trouve aucune colonne manquante. Ils ne reproduisent pas la panne entière. Les autres nœuds cohésifs libres excluent leur emploi comme dynamique de substitution.

La variante entière Idrill2→1 dans les propriétés122/123 conserve masse et centre, mais s’arrête encore au même offset+0x664. L’observation indépendante vérifie IPARG41=1 réellement reçu ; les26paires/156lignes manquantes persistent avec NDOF[6,6]. Le mélange6/3 seul ne suffit donc pas à expliquer la panne.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat d’un modèle historique officiel. La source figée du moteur et sa documentation servent uniquement à interpréter données et contraintes. IXC(7,I) est l’identifiant utilisateur, distinct des indices internes /NODE. Le premier champ de TYPE19 est mat_ID4 ; Npt_ply est3. Un addendum corrige toute confusion antérieure avec4points d’intégration, sans changer l’entrée ou effacer les déclarations. Le NPT natif CBAKE3 n’est pas assimilé à Npt_ply.

- [RBE2 : masques et déports](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm)
- [TYPE51 : empilement et champs des plis](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm)
- [Source figée CBACOORK](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/elements/shell/coqueba/cbacoork.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle photographie, vidéo, archive ou source historique inspectée. Aucun dégât observé ni résultat NIST utilisé comme cible. Les archives restent en lecture seule.

## 4. Hypothèses propres au modèle

Graine1102074. Les déclarations propres à chaque diagnostic sont enregistrées avant son lancement. Pour144liaisons internes uniquement, la référence est redirigée du nœud intermédiaire vers la racine qui impose déjà ses six mouvements. Les masques111/000 de la liaison interne,111/111 de la racine, Iflag0 et skew0 sont vérifiés. Les groupes secondaires, positions, matériaux, propriétés, masses, RBE3 et contacts restent identiques. Seuls144labels de référence et deux titres changent dans la copie entière originale. Aucune masse ou inertie compensatoire.

Équations composées : v_m=v_r+Ω_r×(X_m−X_r), Ω_m=Ω_r ; puis v_s=v_m+Ω_m×(X_s−X_m)=v_r+Ω_r×(X_s−X_r). La pose finie et les moments composent les mêmes bras de levier. Une simple suppression du déport ou une liaison translatoire sans rotation n’est pas cette transformation. Huit poses aléatoires par branche, angles±0,7rad, vitesses et efforts indépendants, servent de contrôles algébriques ; aucune sortie mécanique ne sert de cible.

## 5. Résultats dérivés

Les3072échantillons d’identité rigide passent les seuils pré-déclarés : erreur maximale de pose2,27e−13mm, de vitesse3,55e−15mm/ms, de moment3,64e−12Nmm. Cela vérifie les équations, pas leur élimination native ni la réponse chargée. La masse Starter reste191273837,9425g, centre[14245,90260656;−0,00031019191109262;−211,2460794408]mm et ADMAS prescrites100368522,1367g, exactement comme la référence enregistrée.

La copie entière termine BEGIN/END CHECK, code0/NORMAL en7,39s natives, sans l’arrêt ASSEMC_KIJ. Matrice symboliqueND257154/NZ6819585, finaleND227010/NZ5841201. Le compte rendu conserve15erreurs et5avertissements récapitulatifs. Le listing contient49370messages de connectivité :48996lors de la condensationTYPE2 et374lors deRBE2. Ces messages ne sont pas réduits aux seuls cinq avertissements du récapitulatif. Quinze directions de raideur suspectes sont listées aux nœuds119,111,109,107,103,99, avec valeurs négatives parfois extrêmes. Ils ne prouvent pas un mécanisme physique : l’assemblage condensé reste suspect.

Le Starter entier conserve les deux avertissements initiaux et0erreur. Les cinqTYPE25 sont ignorés en implicite. La conversion de l’histoire initiale CHECK échoue ; fichier natif et échec conservés. Aucune valeur d’inertie redistribuée ou de compteur EngineADDED MASS n’est inférée d’une histoire illisible.

## 6. Contradictions et informations manquantes

La composition des chaînes supprime cet arrêt d’assemblage dans la copie entière. La cause logicielle amont complète n’est pas prouvée, et les petits reproducer négatifs restent explicites. Aucune qualification de raideur, de masse/inertie redistribuée, de travail local ou d’impact chargé ne découle de la terminaison. Le test natif explicite suivant doit conserver les contacts originaux et examiner les bilans. Les TYPE2/RBE2 sans connectivité nécessitent une analyse du graphe ; aucune suppression de contraintes ou modification arbitraire des budgets n’est autorisée par ces diagnostics.

A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués ; structure intérieure, gravité, ruptures et bilan entier restent ouverts. Meilleur impact entierA20=0,0200001220703125s. Objectif : dix secondes physiques puis vidéo3DMP4/GIF, toujours incomplet. Aucun diagnostic ou petit panneau crédité à cet objectif.

Les anciennes empreintes sont conservées ; tailles/dates sont comparées sans nouvelle lecture de tous les contenus anciens. L’original entier et le moteur sont revérifiés par SHA256. Aucun patch logiciel, installation, compilation, écriture d’instructions ou de données mécaniques dans le processus. Rapport, sorties et validation du harnais précèdent l’ajout au registre.

AIRCRAFT-A50 : partir de la copie A49 à chaînes rigides composées, qui termine désormais CHECK sans SIGSEGV. Les144références internes sont redirigées vers leur racine entièrement rigide, sans perdre offsets, bras de levier, masses ou matériaux. Les cinq petits reproducer ne reproduisent pas la panne ; Idrill1 reçu par le moteur ne la corrige pas. La copie entière conserve RBE3 et TYPE25, mais CHECK reste échoué :15directions de raideur suspectes et49370messages de connectivité, dont48996TYPE2 et374RBE2. Vérifier dans un lancement explicite entier très court et borné les masses/inerties/énergies natives après redistribution, avec les TYPE25 conservés, par comparaison aux sorties A45 déjà en cache ; aucun ancien calcul réussi à relancer. Identifier ensuite les nœuds et contraintes des messages TYPE2/RBE2 et leur construction du graphe depuis la source figée. Ne pas lancer un impact implicite avec contacts ignorés, supprimer des contraintes, ajouter des masses, ajuster les matériaux ou contourner une panne logicielle. Les équations rigides composées sont vérifiées, leur implémentation native chargée reste à qualifier. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF actif et incomplet. Publier A48+A49 avec tous les échecs puis continuer A50.
