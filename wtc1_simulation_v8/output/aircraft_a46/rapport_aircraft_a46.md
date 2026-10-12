# AIRCRAFT-A46 — assemblage du panneau isolé exécuté ; avertissements mécaniques conservés

Deux panneaux de quatre coques atteignent le compte rendu CHECK, avec mêmes matériaux, propriétés et coordonnées que leur extrait A20. Ils ne reproduisent pas l’avortement entier A45. Les contrôles signalent toutefois une erreur de chargement et27/21 directions de rotation presque sans raideur. Ils ne sont pas déclarés mécaniquement validés. Aucune extension temporelle de l’impact.

## 1. Faits directement observés ou transcrits

Deux préparations Windows nouvelles passent sans erreur ni avertissement. Deux Engine Linux nouveaux terminent normalement avec code0 et BEGIN/END IMPLICIT MODEL CHECKING. Le compte rendu natif indique1erreur et27avertissements pour le panneau libre,1erreur et21avertissements avec un bord bloqué. La revue initiale de complétion, qui teste seulement sortie0 et présence du compte rendu, reste conservée ; la revue mécanique supplémentaire porte explicitement clean_mechanical_CHECK_passfalse.

Le premier panneau contient les quatre éléments20001à20004 de la façade A20 et neuf nœuds. Les identifiants sont renumérotés localement ; coordonnées, connexions, MAT/LAW2/3, PROP/TYPE1/31 et PART/31 sont copiés inchangés. Le second ajoute seulement un appui déclaré sur les deux nœuds du premier bord. Aucun contact, RBE ou liaison au reste de la tour dans ces témoins. Aucun solveur ancien relancé, installation ou compilation.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat officiel historique. La source figée du moteur montre CBAKE3→ASSEM_C4→ASSEMC_KIJ pour les blocs de raideur de coques. ASSEM_C4 appelle des blocs nominaux à six composantes et NDOF détermine les composantes actives. ASSEMC_KIJ recherche un bloc JDIK puis utilise JDL sans branche explicite de bloc absent. Cette lecture est une observation de code ; elle ne démontre pas qu’un bloc manque dans le modèle entier ni que cette branche explique l’avortement.

- [Assemblage des coques figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/assem_c4.F)
- [Assemblage global figé](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/imp_glob_k.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo, photographie ou PDF inspecté. Les sources restent en lecture seule. Aucun dégât connu n’est une cible de réglage.

## 4. Hypothèses propres au modèle

Graine1102071, zéro tirage. Panneau diagnostique extrait, vitesse initiale nulle, quatre coques Ishell24/Ismstr4/Ish3n2/Idrill2, cinq points d’intégration, épaisseur7,9375mm. Acier de référence du modèle : densité0,00786g/mm³, E200000MPa, ν0,3, limite427,656MPa. Ces valeurs ne sont pas une mesure de ce panneau historique. Le bord fixé est une variante numérique déclarée, jamais transférée à l’impact entier. Les témoins ne reprennent ni la masse entière ni son chargement.

Chaque processus est borné180s, un thread CPU, sans GPU. CHECK utilise le même moteur A44 déjà qualifié dans les témoins A45. Le contrôle CHECK peut imposer ses propres options linéaires ; aucune nouvelle factorisation dynamique MUMPS ou collision n’est revendiquée ici.

## 5. Résultats dérivés

Les matrices atteignent leur compte rendu :54degrés pour le panneau libre,42après appuis, et0degré explicitement signalé dans la rubrique ZERO STIFFNESS. La rubrique POSITIVE DEFINITE MATRIX rapporte27/21directions ROT_DIR X/Y/Z, avec coefficients≈4,004e-14à1,602e-13. Leur signification physique et leur rôle dans la flexion restent à contrôler sous chargement. L’erreur IMPLICIT LOADING DATA est présente dans les deux témoins sans charge appliquée. NORMAL/0 atteste ici de la complétion du diagnostic, pas d’un modèle propre.

Masse géométrique attendue8640.489177995105g ; masses préparées8640.489177994999 et8640.489177994999g ; aucune masse ajoutée. Matériau/propriété et géométrie entiers restent inchangés. L’audit des anciennes sorties compare taille et date de modification avant/après et réutilise les preuves SHA256 précédentes ; ce n’est pas une nouvelle relecture intégrale de tous leurs contenus. Les entrées entières et le binaire sont revérifiés par SHA256.

## 6. Contradictions et informations manquantes

Le panneau isolé ne reproduit pas l’arrêt du modèle entier ; ni Ishell24 seul ni cet appui seul ne suffisent à expliquer l’avortement. Les couplages shell/solide, RBE, ties, graphes actifs et la topologie globale restent distincts. Les cinq TYPE25 ignorés A45 restent une incompatibilité indépendante, sans remplacement silencieux.

La réponse sous charge, rigidité de flexion, moments, flèche, forces et travail doivent être comparés entre explicite et implicite avant un transfert entier. Aucun changement de formulation, matériau, inertie ou appuis pour forcer le passage n’a lieu. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. Le meilleur impact entier demeure0,0200001220703125s. Structure intérieure, gravité et dix secondes physiques3D puisMP4/GIF restent à terminer. A44+A45 sont publiées et vérifiées ; A46 sera conservée dans la prochaine paire.

AIRCRAFT-A47 : utiliser les deux contrôles de panneau A46 en cache ; ne pas les refaire. Les quatre coques de façade Ishell24, géométrie/propriété/matériau A20 inchangés, atteignent BEGIN/END CHECK en libre et bord fixé ; la panne ASSEMC_KIJ entière A45 n’est pas reproduite. Chaque CHECK signale1erreur de chargement, plus27/21 directions ROT_DIR de raideur≈4e-14 à1,6e-13 ; NORMAL/0 n’est pas une qualification mécanique. Inspecter la formation des blocs membrane/flexion et la lecture de la propriété depuis les sources en cache, puis pré-déclarer un témoin élastique chargé permettant une comparaison explicite/implicite de force, flèche, moment et travail à données identiques. Ne pas changer discrètement la formulation, l’inertie, les coefficients ou les appuis pour faire disparaître les avertissements. La recherche du contrat de graphe entier/RBE/ties reste distincte des cinq TYPE25 ignorés. Moteur A44 déjà compilé, LAW117/contact direct A45 qualifiés dans leurs témoins ; aucune nouvelle compilation nécessaire. A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués. A20 demeure le meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques3D puisMP4/GIF actif et incomplet. A44+A45 sont publiées/vérifiées, A46 attend la prochaine paireA46+A47.
