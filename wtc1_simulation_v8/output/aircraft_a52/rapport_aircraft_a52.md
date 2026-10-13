# AIRCRAFT-A52 — regroupement TYPE2 entier rejeté, nouveau bloc fautif à identifier

La comparaison native est préparée sur le modèle entier. Le regroupement par facette prépare ses données mais s’arrête avant le contrôle des attaches : il reste rejeté. Une nouvelle mesure capture24paires/144lignes absentes dans un autre bloc d’assemblage. Le dernier bloc de peaux observé ne correspond pas à ce bloc ; aucune attribution de pièce n’est inférée de ce contexte périmé.

## 1. Faits directement observés ou transcrits

Deux Starter et trois Engine nouveaux, un threadCPU, caps180s, sans GPU. Une nouvelle observation du modèle A49non regroupé capture432appels I2UPDK0et3024attaches uniques : labels secondaires et principaux, paramètres CRST, positions natives et DOF. Le moteur termine CHECK avec les erreurs déjà connues, sans nouvelle qualification.

La première préparation de la copie omet l’en-tête obligatoireRADIOSS ; Starter sort2avec erreurs100201/2000. Échec conservé, aucun Engine pour cette tentative. Une versionR1distincte rétablit seulement l’en-tête d’origine et un nouveau nom/dossier, sans modifier paramètres ou critères. StarterR1 :2avertissements de pénétration initiaux,0erreur. Le moteurR1s’arrête avecSIGSEGV/code3avant tout appel d’assemblageTYPE2observé. Il ne produit donc aucune des attaches nécessaires à la comparaison d’équivalence.

Un troisième Engine, nouvelle observation de cette copie rejetée, capture le graphe au signal :1579appels ASSEMC,12CBAKE3observés, faute àASSEMC_KIJ+0x664. NEL128,ND6,IKPAT1,24paires NDOF[6,6] et144lignes sans colonne attendue. Indice d’accèsK_LT1072066364. La panne ne se réduit donc pas à un mélange6/3.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a et symboles du binaireA44inchangé. Les observations TYPE2lisent les arguments deI2UPDK0/I2UPDK1dans notre propre processus fils. Aucune instruction, donnée physique ou binaire modifié ; les signaux sont transmis au moteur.

ASSEM_C4reçoit directementIXC(NIXC,NEL),NIXC7dans la source, puis forme les tableaux de nœuds transmis àASSEMC_KIJ. Cela permet une observation plus directe du vrai bloc que le seul dernierCBAKE3. IMP_CHKMreçoitITABetXglobaux, à observer après vérification de leurs positions dans la signature.

- [Arguments TYPE2 et calcul des coefficients](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/interfaces/interf/i2_imp1.F)
- [Connectivité du bloc réellement assemblé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/assem_c4.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie, vidéo ou source historique inspectée. Archives en lecture seule ; aucun dégât connu ou résultat NIST utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine1102077, zéro tirage. Les37165messages TYPE2entre interfaces distinctes concernent tous les deux côtés d’une même facette, aucune autre facette. Cette précision nouvellement vérifiée motive un test entier direct de216paires, plutôt qu’un nouveau petit reproducer incomplet.

Chaque TYPE2pair reçoit les14secondaires disjoints et les deux parts principales de ses faces inférieure/supérieure. La définition TYPE2impaire est retirée ; ses groupes et surfaces inutilisés restent présents. Tous les autres éléments, coordonnées, matériaux, propriétés, masses, RBE2/RBE3,TYPE25, conditions initiales et appuis sont conservés exactement par sections, sans clé dupliquée. Le regroupement est un candidat diagnostique, pas une équivalence supposée. Les facettes principales ordonnées, paramètres natifs, déports/coordonnées et DOF doivent passer les tolérances déclarées avant intégration.

## 5. Résultats dérivés

Masse Starter191273837,9425g, centre[14245,90260656;−0,00031019191109262;−211,2460794408]mm et ADMAS prescrites100368522,1367g restent exactement ceux d’A49. Ces totaux ne prouvent pas l’inertie redistribuée ni l’équivalence des attaches. La comparaison native est indisponible : zéro appel TYPE2de la copie regroupée avant son arrêt. Son critère d’équivalence est échoué et la copie rejetée.

Le dernierCBAKE3observé porte8éléments, tandis que l’assemblage arrêté en porte128. Ses huit labels de peaux et ses coordonnées ne sont donc pas attribués au vrai bloc. Aucun nœud des24paires manquantes ne dispose de coordonnées dans cette captureCBAKE3périmée. Les indices internes fautifs restent à relier à l’entrée. Le signal au même offset queA48/A49ne prouve pas qu’il concerne les mêmes pièces.

## 6. Contradictions et informations manquantes

La piste des interactions entre TYPE2reste une hypothèse. Le regroupement nominal ne répare pas le graphe et son équivalence physique n’est pas vérifiée. La source prouve déjà que les blocs absents sont ignorés parPUT_KIJ ; ils ne deviennent pas une raideur physique nulle. Les contactsTYPE25ignorés en implicite, les deux avertissements Starter et les autres critères échoués restent explicites. Aucun impact implicite exécuté avec contacts ignorés.

Suite : observerASSEM_C4pour le vraiIXCet récupérerITAB/Xau début deCHECK, puis valider labels/connectivité/coordonnées avant reproducer ou correction. Aucune compensation de masse/inertie, modification arbitraire de matériau ou patch de moteur. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF inchangé et incomplet. Aucun temps de diagnostic crédité.

Anciennes sorties et scripts préservés : tailles/dates comparées avec manifestes existants, sans nouvelle relecture totale ; entrées utilisées et original entier recontrôlés par SHA256. Rapport et harnaisPASSprécèdent l’ajout au registre. A50+A51 sont publiées et leurs deuxCI vérifiées,127anciennes archives conservées ; cela ne valide pas la physique.

AIRCRAFT-A53 : capturer le bloc réellement passé à ASSEM_C4, pas le dernier CBAKE3 observé. A52 classe les37165messages croisés entre les deux faces de chaque même facette, puis teste un regroupement432→216TYPE2sur une copie entière conservant éléments, matériaux, masses, RBE2/RBE3,TYPE25et conditions initiales. Référence :432appels I2UPDK0/3024attaches natives capturées. La copie groupée s’arrête avant tout appel TYPE2, donc son équivalence d’attaches est inconnue et échouée. Regroupement rejeté, aucune intégration d’impact. Deux Starter dont une tentative avec en-tête manquant conservée, trois Engine nouveaux. CopieR1 : Starter2avertissements/0erreur, masse/centre/ADMAS identiques. Nouvelle capture ASSEMC+0x664 après1579appels :NEL128,ND6,IKPAT1,24paires6/6 et144lignes manquantes, indiceKLT1072066364. Dernier CBAKE3 :NEL8, donc contexte périmé et aucun label de ses huit peaux attribué au vrai bloc fautif. La fonctionASSEM_C4reçoit directementIXC(7,NEL), dont labels d’éléments et nœuds. Pré-déclarer trois observations matérielles ASSEM_C4/ASSEMC_KIJ/IMP_CHKM ; au début de CHECK récupérer ITAB etXglobaux par arguments vérifiés dans la source, puis comparer les128éléments et coordonnées au vrai bloc. Aucun patch source/binaire/données mécaniques, compensation ou critères relâchés. Le regroupement nominal ne résout pas encore le graphe. CHECKforcéPCG/IPREC5,TYPE25ignorés et autres critères échoués restent explicites. Meilleur impact entierA20=0,0200001220703125s ; dix secondes physiques3D puisMP4/GIF restent actives et incomplètes. A50+A51 publiées/vérifiées ; A52en attente deA52+A53.
