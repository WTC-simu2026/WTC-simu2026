# Reprise WTC 1 après V11D

Lire AGENTS.md et harness/state.json, puis lancer Test-WtcHarness.ps1 depuis le dossier actif. V11D est terminée, prochaine V11E. Ne pas reprendre de l'ancien V8H/V10J, ni rescanner les archives. Les prototypes exploratoires avec hypothèses visibles restent autorisés par Jeremy.

## Résultat sauvegardé

La dalle du panneau possède maintenant sa flexion et son mouvement vertical propres : contact comprimé, ouverture et attache tendue sont distincts. Le modèle est un prédicteur élastique NON FISSURÉ. Un premier seuil de traction du béton termine ce prédicteur ; ne jamais appeler ce seuil une rupture complète du plancher. Aucun calcul global d'effondrement n'est mis à jour.

Au maillage de référence : 33 nœuds de treillis, 63 barres d'acier ; 33 nœuds de dalle avec ux/w/theta, 32 éléments axiaux et de flexion ; 17 stations de contact/attache et 32 knuckles équivalents supposés ; 165 degrés de liberté ; 213 termes scalaires dont 64 quadratures de flexion. Les quadratures ne sont pas 64 poutres supplémentaires. Trois termes d'appui pour le rouleau, quatre si retenu horizontalement.

12 parcours et 278 états : huit parcours froids atteignent la borne1,25 de charge sans franchir les critères vérifiés ; les trois parcours thermiques atteignent une première fissuration ; l'abaissement local imposé de20mm atteint sa borne sans autre seuil. Aucun parcours de panneau n'atteint un seuil d'attache avant fissuration ; donc zéro diagnostic de retrait de panneau. Un contrôle d'attache isolée à20/450/600°C démontre séparément retrait et recontact, pas une fracture historique.

56/56 contrôles passent :22 essais génériques indépendants,18 contrôles de panneau indépendants,16 contrôles d'ensemble/répétition/raffinement. Le noyau et les équations ont été relus indépendamment ; aucune anomalie bloquante. Une valeur par défaut de facteur de résistance a été corrigée avant l'exécution finale (facteur déclaré1, valeurs actuelles inchangées).

Résidus max sur parcours : équilibre par équation4,789211946e-11 ; identité d'énergie discrète2,263534742e-11 ; identité corrigée2,263523998e-11. Les équations de force et moment sont normalisées séparément, sans addition de grandeurs de dimensions différentes. Diviser le pas de parcours par2 ne déplace aucun premier seuil au niveau de précision choisi. Raffiner seulement la dalle de2 à4 subdivisions donne0 de différence du paramètre terminal et1,185574394e-11 d'écart relatif maximal de flèche nodale.

Exécution CPU31,105s avec répétition et raffinements, Python3.14.3/NumPy2.4.6. Le dossier validé tmp/v11d_slab_contact/attempt01 a été conservé et publié à l'identique dans le dossier final, après contrôle des empreintes. Aucun GPU, logiciel installé, Blender ou nouvelle lecture d'archive/PDF/réseau.

## Sources et hypothèses importantes

Géométrie V11A/V11C : paire symétrique de treillis, 713in de portée, largeur80in, dalle rectangulaire équivalente4,35in, 16panneaux Warren supposés. Les stations réelles et l'armature ne sont pas inventoriées. La densité équivalente de32attaches reste fixe quand le maillage de DALLE change ; le treillis et ses17stations ne changent pas. Raffinement1/2/4 est un contrôle de discrétisation de cette bande, pas validation du vrai plancher.

La traction verticale active les capacités déjà vérifiées en V11C, NCSTAR1-6C tableau5-7 p67/PDF115 local :15/12/10/7kip PAR knuckle pour T moyenne du BÉTON20-300/450/600/750°C. Source officielle calculée/estimée, pas essai incendie des pièces réelles. Interpolation linéaire propre au modèle, sans indexation sur T acier. Anciennes tables de glissement/sièges préservées.

E,fc et réductions de béton hérités des hypothèses V11A. Nouvelle traction ft20=0,5/1/2MPa et réductions hypothétiques ; aucune formule réglementaire ni donnée mesurée WTC revendiquée. Pas de résistance postfissurée ou d'armature créditée. Le contact vertical ne devient pas automatiquement un contreventement latéral du cordon.

Raideur de contact1000MN/m par attache équivalente, traction10/100/1000MN/m hypothétiques. Le contact autorise une faible interpénétration numérique, explicitement mesurée. Excentricité0 ou t/2 : l'attache au-dessous d'une dalle rectangulaire équivalente est supposée, la géométrie exacte bac/cordon reste inconnue. La valeur t/2 vaut0,055245m.

## Mécanique

Dalle axiale bilatérale EA jusqu'au premier critère combiné, contrairement à V11C qui supprimait la traction axiale sans résoudre la flexion. Flexion Euler-Bernoulli, theta=dw/dx, déplacements positifs vers le haut. Glissement horizontal us+e theta−uacier ; le moment conjugué eN est assemblé. Un mouvement rigide avec rotation donne glissement et énergie nuls (test indépendant).

Jeu g=wdalle−wtreillis : contact Nc=kc min(g,0), attache Nt=kt max(g,0). Au zéro initial, seule la tangente de contact est active. Après retrait d'attache à une station, supprimer glissement et traction verticale ensemble, conserver le contact. Ne pas supprimer une barre au premier écran Euler/yield ; pas de postflambement ni de fracture dynamique. Un système sans rang est signalé non résolu, pas déclaré effondré.

Toute la référence80psf, poids propre compris, est appliquée UNE SEULE FOIS à la dalle : charges réparties cohérentes [qL/2,qL²/12,qL/2,−qL²/12] avec q négatif pour gravité. Le test d'abaissement du treillis impose un déplacement au milieu après une précharge0,25 ; inclure sa réaction et son travail. Ce n'est pas un dommage spontané ni une simulation d'impact.

Température moyenne des deux faces pour E/forces/capacités. Courbure libre kappa0=−alpha(Tsup−Tinf)/t, gradient prescrit et alpha constant supposé. Pas de section thermique multicouche, de feu, transfert thermique, fluage ou durée réelle.

Moment récupéré dans un élément : M=EI(Hxx u−kappa0)+q(L²−6Lx+6x²)/12. Le terme de charge vient de la bulle q x²(x−L)²/(24EI). Vérifier M aux bouts et à sa station intérieure éventuelle. Contraintes sup/inf=N/A ∓ Mt/(2I). Le premier max traction/ft ou compression/fc arrête le prédicteur ; cela ne dit pas la résistance d'une dalle armée fissurée. Les flèches exportées sont des maxima NODAUX, pas une recherche exacte dans chaque élément.

Énergie de la bulle q²L⁵/(1440EI), travail ajouté deux fois cette valeur ; identité d'état vérifiée séparément de l'énergie discrète. Les termes de Gauss ont raideurN·m³, courbure1/m et conjuguéN·m² : ils sont exclus du CSV d'efforts physiques enN. L'identité inclut déformations propres et travaux imposés mais n'est pas un bilan de chaleur ou de fracture dynamique.

## Exemples interprétés correctement

À80psf, modèle de référence froid : flèche de dalle43,218mm et treillis43,214mm ; 17contacts comprimés, aucune attache verticale tendue ; recouvrement maximal de contact0,00730mm ; charge paire140,959kN. À125% les cas e0/e=t/2 donnent58,519/54,023mm de flèche nodale sans atteindre les critères vérifiés. Ce ne sont pas des charges admissibles réelles.

Les trois chauffages s'arrêtent à fissuration : uniforme roulant282,396°C ; uniforme retenu82,396°C ; chauffage par dessous acier42,704°C, dalle20/30,960°C. Les faibles températures du dernier cas sont celles d'un prédicteur non fissuré soumis à un gradient, pas des températures de ruine. Deux attaches sont tendues dans les cas retenu et par-dessous, sans atteindre leur arrachement. La résistance après fissuration reste inconnue ici.

Ne pas comparer directement ces fins à V11C : nouvelle vérification traction+flexion, liaison verticale différente, excentricité et précharge0,25 au lieu de0,5. L'ancien cas V11C uniforme roulant allait à600°C sans son ancien seuil ; V11D ne déclare pas cet ancien résultat faux ou une chute à282°C.

L'abaissement central de20mm produit une réaction d'actionneur−39,965kN et une somme de sièges75,205kN, soit bien la charge35,240kN ; une attache verticale est tendue. Sans compter l'actionneur, on inventerait une charge supplémentaire. Les données de sortie conservent cette distinction.

## Livrables et prochaine V11E

Dossier wtc1_simulation_v8/output/v11d_slab_contact : rapport_v11d_dalle_contact.md, results_v11d.json, synthese_v11d_dalle_contact.png, panel_inventory.json, path_summaries.csv, path_history.csv, slab_fiber_stresses.csv, physical_component_forces.csv, slab_displacements.csv, release_diagnostics.json (liste vide justifiée), slab_mesh_comparison.csv, isolated_pullout_coupon.csv, numerical_audit.json, source_manifest.json, offline_manifest.json et release_audit.json.

Code : scripts/v11d_panel_model.py, run_v11d_slab_contact.py, test_v11d_independent.py, test_v11d_panel_review.py. Configuration : data/v11d_slab_contact_predeclaration.json. Le runner refuse d'écraser une sortie ; choisir un nouveau sous-dossier tmp/v11d_slab_contact pour toute répétition. Le runner réutilise les fonctions de fichiers V11C sans lancer son main ; dépendance ancienne hachée.

Empreinte numérique :93499651e33446ed49ac2f3b40ba5ec6987791b8f407d40c3645ae2c6ab7960e. Vérifications séparées :14sorties hors manifestes supplémentaires,13entrées/protégés,5fichiers code/configuration,11anciennes entrées V11C. Aucun ancien fichier de simulation ou master3D modifié.

V11E : construire et vérifier une réponse de section de dalle après fissuration avec hypothèses d'armatures explicites et cycles élémentaires, AVANT transfert au panneau. Ne pas ajouter une résistance fictive pour forcer un arrachement ou un effondrement. Puis géométrie non linéaire, postflambement, liaisons avec colonnes/allèges, impact calculé du767, incendies et couplage spatial. V11D n'est pas déjà ce calcul complet et ne donne aucun verdict historique.
