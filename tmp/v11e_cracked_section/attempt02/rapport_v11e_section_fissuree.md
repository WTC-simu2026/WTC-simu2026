# V11E — section de dalle après fissuration

## Résultat et périmètre

La section peut maintenant franchir une première fissure, reprendre des efforts dans les armatures et suivre des chargements alternés. 14 parcours, 6768 états et 86/86 contrôles passent. Il s'agit d'une vérification numérique de lois hypothétiques, pas d'une validation expérimentale ou d'un verdict sur l'effondrement du WTC1.

V11D, le panneau, le calcul réduit V11B et Blender restent inchangés. V11E fournit une bibliothèque de section avec essais/validation avant couplage. Aucun déplacement de plancher, impact d'avion, incendie ou capacité globale nouvelle n'est déduit de ces courbes.

## 1. Faits transcrits ou directement constatés

Les entrées locales V11A/V11D contiennent une bande équivalente de 80 in (2,032 m) de largeur et 4,35 in (0,11049 m) d'épaisseur. Ce sont les dimensions du modèle d'exemple déjà transcrit, pas une section réelle de dalle-bac-armature reconstruite. La présente itération ne relit aucune archive ni aucun PDF source et n'ajoute aucun ferraillage documenté. Les fichiers protégés sont contrôlés par empreinte avant/après.

## 2. Résultats de modèles officiels et références de méthode

Aucun résultat NIST d'effondrement ou de feu n'entre dans la loi de section. Les capacités de knuckles de V11D ne sont pas activées ici. La géométrie équivalente reste héritée de l'exemple NIST local, donc n'est pas une identification géométrique indépendante.

La documentation primaire [DIANA — traction](https://manuals.dianafea.com/d108/en/1219784-1221375-total-strain-crack-models.html) décrit une famille de lois adoucissantes associées à une énergie de fissuration et une largeur de bande. Elle distingue aussi ouverture, déchargement sécant et fermeture en compression : [DIANA — états de fissure](https://manuals.dianafea.com/d102/Theory/Theorych74.html). Ces idées guident une simplification unidimensionnelle explicitement écrite ci-dessous, sans exécuter ni reproduire tout DIANA. La documentation [OpenSees — ElasticPP](https://opensees.berkeley.edu/OpenSees/manuals/usermanual/171.htm) définit la famille élastique-parfaitement plastique retenue pour l'acier ; OpenSees n'est pas exécuté. Aucun de ces documents ne donne les paramètres réels du ferraillage WTC1. Sources consultées le 6 septembre 2026.


## 3. Affirmations d'archives locales

Aucune nouvelle affirmation d'archive, analyse vidéo, identification de dommage ou hypothèse de mécanisme supplémentaire n'est introduite.

## 4. Hypothèses du modèle

Tout est isotherme à 20 °C. Béton : E = 2 500 ksi, fc = 3 ksi, ft = 1 MPa, déjà hypothétiques en V11A/V11D. Compression linéaire jusqu'au seul écran fc ; au-delà, arrêt, sans loi d'écrasement. Traction adoucissante avec Gf = 50/100/150 J/m² et longueur de bande Lch = 0,05/0,10/0,20 m selon les variantes. Ces nombres ne sont ni mesurés sur le WTC ni ajustés pour imposer un résultat.

Armatures : E = 200 GPa, fy = 400 MPa, aire totale 0/0,1/0,2/0,4 % de la section brute. Positions possibles : une nappe supérieure, une inférieure, ou deux nappes symétriques partageant l'aire totale. Les centres sont à 25 mm des faces. Grade, aires et positions sont supposés ; aucune correspondance à un plan de construction n'est revendiquée. Adhérence parfaite, pas de glissement acier-béton, bac acier, effort tranchant, membrane transverse, fatigue, rupture ou flambement des armatures. Le seuil de déformation acier de 1 % limite le domaine choisi, ce n'est pas une déformation de rupture mesurée.

Le béton est intégré en 160 bandes au milieu de chacune, avec raffinements 80 et 320. Son aire totale est uniformément réduite de l'aire d'acier : Ac + As = A brute. Ce remplacement diffus évite un ajout d'aire, mais ne reproduit pas les trous des barres. La longueur Lch est LONGITUDINALE, indépendante du nombre de fibres dans l'épaisseur ; elle n'est ni l'épaisseur de dalle ni la hauteur d'une fibre.

### Lois, signes et énergie

Déformation plane : eps(y) = eps0 − y kappa, y vers le haut ; traction positive. N = somme(A sigma), M = −somme(A y sigma). La matrice tangente est la somme des A Et [1,−y]ᵀ[1,−y]. N est en N, M en N·m, kappa en m⁻¹. Le travail de section N d(eps0) + M d(kappa) est en J/m de longueur, pas en J d'un étage.

Béton : e0 = ft/E ; ef = 2 Gf/(ft Lch) > e0. Enveloppe sigma = E eps jusqu'à e0, puis ft (ef−eps)/(ef−e0), puis zéro. r est le maximum historique de traction ; déchargement/rechargement par la sécante E(1−d) = sigma_enveloppe(r)/r. Compression sigma = E eps après fermeture à eps = 0, sans effacer r. Il n'y a pas de restauration de résistance en traction ni de plancher artificiel de contrainte. Cette fermeture réversible ne modélise ni frottement des lèvres ni déformation permanente du béton en compression.

Énergie stockée béton psi = sigma eps/2 ; dissipation D(r) = ft ef/(2(ef−e0)) × bornage(r−e0, 0, ef−e0). À ouverture complète, D = Gf/Lch, pré-pic compris. Le travail est calculé séparément par intégration exacte des segments de contrainte, pas défini par psi + D. La plasticité parfaite d'acier conserve eps_p ; retour de sigma à ±fy, D incrémentale = fy |delta eps_p|, psi = sigma²/(2E). Les cycles vérifient l'irréversibilité et W = psi + D.

La courbure est imposée et l'effort axial est nul, sauf un cas avec précompression de 5 % fc Ac. Les changements de pente de l'équation axiale sont énumérés pour trouver toutes les racines à tangente axiale positive : une seule est requise. Une racine multiple ou absente arrête le parcours comme non résolu ; aucune stabilisation n'est ajoutée. Les intervalles neutres sans raideur sont comptés à part. Cette règle de suivi quasistatique n'est pas une preuve de stabilité dynamique, notamment sur une branche où le moment diminue.

Les essais de recherche d'équilibre ne modifient jamais l'état engagé. La compression maximale est récupérée aux FACES extérieures exactes de la bande, pas au milieu de la première fibre intérieure. Les seuils fc/1 % sont localisés par subdivision du dernier incrément ; fissuration et plastification sont enregistrées mais n'arrêtent pas la section. Leurs premières courbures publiées sont les premiers échantillons détectés, pas des seuils continus de même précision que la limite de domaine.

## 5. Résultats dérivés

### Parcours de section

| Cas | Fin | Courbure finale (m⁻¹) | Moment final (kN·m) | Maximum absolu échantillonné (kN·m) |
|---|---|---:|---:|---:|
| MONO_PLAIN | Borne du parcours | 0.080000 | 0.290 | 8.054 |
| MONO_RHO01 | Borne du parcours | 0.080000 | 4.731 | 8.593 |
| MONO_REFERENCE | Borne du parcours | 0.080000 | 8.835 | 9.706 |
| MONO_RHO04 | Borne du parcours | 0.080000 | 16.528 | 16.568 |
| MONO_TOP_ONLY | Borne du parcours | 0.080000 | 2.754 | 8.009 |
| MONO_TOP_REVERSED | Borne du parcours | -0.080000 | -15.052 | 16.428 |
| MONO_BOTTOM_ONLY | Borne du parcours | 0.080000 | 15.052 | 16.428 |
| MONO_GF50 | Borne du parcours | 0.080000 | 8.625 | 8.625 |
| MONO_GF150 | Borne du parcours | 0.080000 | 9.158 | 11.854 |
| MONO_LCH005 | Borne du parcours | 0.080000 | 9.594 | 13.323 |
| MONO_LCH020 | Borne du parcours | 0.080000 | 8.625 | 8.625 |
| MONO_AXIAL_COMPRESSION | Limite compression | 0.067401 | 19.648 | 20.001 |
| CYCLE_REFERENCE | Borne du parcours | 0.000000 | 0.266 | 9.476 |
| CYCLE_TOP_ONLY | Borne du parcours | 0.000000 | 0.000 | 15.131 |

À la même courbure imposée 0,08 m⁻¹, le moment final vaut 0.290 kN·m sans armature, 4.731 à 0,1 %, 8.835 à 0,2 % et 16.528 à 0,4 %. Ce sont des réponses d'une section isolée au chargement imposé, pas des charges admissibles de plancher. L'effet de position est marqué : une nappe supérieure donne une autre réponse qu'une nappe inférieure sous le même signe de flexion ; inverser simultanément nappe et courbure reproduit le cas miroir.

Le parcours cyclique de référence termine à courbure nulle avec un moment de 266.091 N·m encore fourni par le dispositif qui impose la courbure. Ce n'est PAS un état libre de tout moment, ni la flèche résiduelle d'un plancher déchargé. Les dissipations finales sont 224.067 J/m pour le béton et 321.243 J/m pour l'acier ; elles ne sont transférées à aucun calcul de propagation.

Les variantes Gf=50 avec Lch=0,10 et Gf=100 avec Lch=0,20 ont exactement le même rapport Gf/Lch et la même courbe de section. Ce test rend visible une non-identifiabilité : une courbe contrainte-déformation seule ne détermine pas séparément ces deux paramètres. Le contrôle de travail Gf est effectué séparément sur une bande de longueur déclarée.

### Vérifications et reproduction

86/86 contrôles réussis, dont 62 contrôles analytiques et d'intégration séparée : enveloppes, fermeture/recharge, énergie de fissuration, plasticité alternée, section élastique, section pré-fissurée armée avec axe neutre analytique, tangente par différences finies, travail des efforts généralisés, racines comparées à une bissection indépendante et arrêts aux limites. Il n'y a pas de relecture par un agent indépendant ni de confrontation à un autre solveur dans cette itération.

Résidus relatifs maximaux : équilibre axial 4.132e-11, identité énergétique exacte des matériaux 7.444e-16. Le travail extérieur calculé séparément par trapèzes présente une erreur maximale de 0.2259 %, contrôlée par un calcul à demi-pas. Cette petite erreur d'intégration n'est pas une précision physique sur le WTC.

Raffinement 160→320 : écart maximal des moments 0.02131 % du pic de référence, et écart de courbure terminale 0.00000 %. Demi-pas : écarts correspondants 0.00000 % et 0.00000 %. Comparaison par segment cyclique et domaine de courbure commun, sans comparer des branches de cycles différentes ni extrapoler après une limite.

Exécution CPU : 54.850 s, Python 3.14.3, NumPy 2.4.6. Empreinte de reproduction numérique : dcbc9838edf537a696431d5b6a7c61f216f164435901b3e3145bc798763d5dfa. Configuration et scripts hachés dans le manifeste ; résultats antérieurs conservés. Aucun GPU, logiciel installé ni Blender lancé.

## 6. Limites, contradictions et suite

La résistance réelle après fissuration reste indéterminée sans ferraillage, adhérence, courbes béton/acier et géométrie de bac mieux documentés. Les vérifications passent pour les lois déclarées ; elles ne certifient pas leur représentativité historique. Une borne de parcours atteinte sans écran franchi ne prouve pas la survie du plancher, et le franchissement de fc ne prouve pas son effondrement. Pas de chauffage/cycles thermiques, fluage, écrasement, fracture d'armature, durée, vitesse, cisaillement, interaction 3D ou localisation longitudinale résolue.

Prochaine V11F : intégrer cette section trial/commit dans le panneau V11D avec le contact et les attaches ; récupérer d'abord le cas élastique, puis vérifier l'équilibre et le travail du panneau postfissuré. Choisir et justifier la longueur de fissuration longitudinale lors du maillage ; ne pas utiliser les 160 fibres comme 160 fissures. Traiter les branches adoucissantes, retours d'état et convergence avant d'en tirer une redistribution ou une rupture d'attache. Puis géométrie non linéaire, postflambement, liaisons colonnes/allèges, impact calculé et incendies, sans issue prédéfinie.

## Fichiers

results_v11e.json ; section_inventory.json ; section_summaries.csv ; section_history.csv ; section_fibers.csv ; cycle_vertices.csv ; material_coupons.csv ; convergence_comparison.csv ; numerical_audit.json ; source_manifest.json ; offline_manifest.json ; synthese_v11e_section_fissuree.png. Code : v11e_section_model.py, test_v11e_section.py et run_v11e_cracked_section.py. Toute répétition utilise un nouveau dossier, jamais une sortie existante.
