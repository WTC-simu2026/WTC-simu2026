# AIRCRAFT-A38 — diagnostic du premier pas, dynamique libre toujours échouée

Huit nouveaux témoins ont été déclarés puis exécutés avec le moteur Linux séparé A35 et des préparations Windows fraîches. Sept terminent normalement ; le huitième est arrêté après une perte énergétique native de75%, avant sa limite180s. Aucun ne respecte l’ensemble des critères du mouvement libre. Le compteur des vitesses initiales est conservé dans dix reprises inspectées. Un raccourci absolu de convergence est identifié au premier pas ; le contourner par tolérance plus stricte engage la résolution mais ne rétablit pas la dynamique. Aucun nouvel impact entier ni vidéo de dix secondes physiques.

## 1. Faits directement observés ou transcrits

Les trois premières variantes changent séparément AUTOSPC, le solveur linéaire MUMPS→PCG, puis Newmark→HHTα−0,05. Les préparations fraîches terminent sans avertissement ni erreur. Les trois dynamiques terminent et échouent aux historiques énergétiques et de quantité de mouvement ainsi qu’aux vitesses/déplacements exacts. Les options testées ne suffisent donc pas isolément à corriger le défaut.

Deux extensions acquièrent la trace non linéaire sur quatre pas et testent une voie linéaire. Deux autres testent le critère de déplacement seul et l’acquisition du premier pas avec une sortie native tous les0,001ms. Les quatre terminent et échouent également. Le mode LINEAR réalise un seul pas de0,1ms : il ne fournit pas cent pas. La première acquisition TRACE ne possède qu’une animation àt0 ; ses historiques atteignent0,004ms et montrent le défaut. Ce manque d’animation finale est conservé.

Les reprises sont lues sans aucune modification. Leur en-tête contient27nœuds et un compteur NINVEL27 dans les six fichiers frais des trois premières variantes et les quatre états A37 avant/après transfert explicite→implicite. La présence de ce compteur réfute sa seule disparition dans ces fichiers, sans démontrer la compatibilité complète des versions.

Le témoin TIGHT conserve la physique et resserre les trois tolérances non linéaires de10⁻⁶ à10⁻¹¹. MUMPS intervient au premier pas ; le moteur annonce ensuite une erreur énergétique globale de−75% et réduit son pas à environ4,8828×10⁻⁷ms. La branche est arrêtée par signal TERM après observation de cet échec : le moteur journalise un arrêt utilisateur puis MPI_ABORT3. Ce code n’est pas présenté comme un nouvel avortement indépendant de la demande d’arrêt. Temps de lancement76,02s, dernière ligne de progressiont≈0,011623ms, douze animations partielles conservées. Pas de terminaison normale ni d’état final à0,1ms crédité.

## 2. Résultats d’un modèle officiel

La documentation des cartes AUTOSPC, SOLVER, DYNA, NONLIN et LINEAR définit les options utilisées. Elle ne constitue pas une qualification de cette compilation OpenRadioss ni une observation de l’événement historique.

- [autospc](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_autospc_engine_r.htm)
- [solver](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_solver_engine_r.htm)
- [HHT](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_1_engine_r.htm)
- [nonlinear](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_nonlin_engine_r.htm)
- [linear](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_linear_engine_r.htm)
- [trace](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_print_nonlin_engine_r.htm)

L’inspection de la source figée bad6688602d770e019b75773d2d5a48b4f9bd918 montre dans NL_SOLV un retour àitération0 lorsque R01×NL_TOL≤10⁻¹² et NL_TOL>10⁻¹⁰, sous les conditions supplémentaires enregistrées dans source_startup_review.json. Ce retour précède CRIT_ITE : sélectionner le déplacement seul ne l’empêche pas. Dans cette branche particulière, R01 est la norme absolue du résidu, malgré l’intitulé relatif de la colonne imprimée. Le premier affichage0/Y/1/3,750×10⁻¹²/1/C concorde avec cette règle. Ce constat source est distinct de la cause complète de la vitesse fausse. Les empreintes et liens primaires des sept fichiers inspectés sont enregistrés ; aucune source tierce brute ni modification du code physique n’est incorporée à cette itération.

## 3. Affirmations provenant des archives locales

Aucune nouvelle lecture d’archive, photographie, vidéo historique ou PDF. Aucun nouveau fait sur AA11 transcrit. Les résultats de ces cubes numériques ne sont pas des probabilités de l’événement réel.

## 4. Hypothèses propres au modèle

Graine1102063, zéro tirage. Même cube libre1mm N2 :27nœuds,8HA8, masse0,00278g ; LAW2 avec densité0,00278g/mm³, E73100MPa,ν0,33 et yield324MPa ; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Vitesse initiale[-200,5,2]mm/ms, KE initiale0,05564031J. Sans charge ni contact, l’oracle est V=V0, U=tV0, P et KE constantes, énergie interne nulle.

Mêmes critères physiques déclarés : erreur énergétique<2%KE0+10⁻⁷J, vitesse<2×10⁻⁴mm/ms, déplacement<2×10⁻⁵mm, absence de masse ajoutée et vérification séparée des grandeurs nodales et globales. Aucun seuil physique élargi, ajout de masse, rescaling de vitesse, modification de matériau ou patch de reprise. Les cartes numériques et limites de temps sont pré-déclarées avant chaque supplément. Les sorties de chaque variante restent séparées. Aucun ancien calcul natif réussi n’est relancé.

## 5. Résultats dérivés

| Témoin | Terminaison normale | Critères complets |
|---|---|---|
| FREE_AUTOSPC_OFF_I | oui | échoués |
| FREE_PCG_I | oui | échoués |
| FREE_HHT_I | oui | échoués |
| FREE_TRACE_I | oui | échoués |
| FREE_LINEAR_I | oui | échoués |
| FREE_DISPLACEMENT_I | oui | échoués |
| FREE_TRACE_INITIAL_I | oui | échoués |
| FREE_TIGHT_I | non, arrêté sur échec énergétique | échoués |

7 historiques complets échouent au bilan énergétique ; 52 champs des sept calculs terminés passent les contrôles de lecture, identifiants, finitude et cohérence coordonnées/déplacement. Ces contrôles de champs ne valident pas le mouvement physique. Les masses et l’absence de masse ajoutée passent dans ces historiques. Les douze animations du calcul arrêté sont analysées séparément comme sorties partielles.

AUTOSPC/OFF, PCG et le critère de déplacement seul reproduisent la vitesse finale[600,−15,−6]mm/ms et KE0,5007628J, soit9KE0. HHT finit vers[525,622,−13,1405,−5,25622] et KE0,3843055J calculée depuis les masses physiques nodales. LINEAR immobilise pratiquement le corps et perd son énergie initiale. La comparaison indépendante aux champs confirme les défauts ; le seul décodeur d’historiques ne les explique pas.

La trace avec tolérance stricte montre que le raccourci peut être évité. Les douze animations partielles gardent V=[−200,5,2]mm/ms et KE nodale0,05564031J. Cela contredit l’erreur énergétique globale annoncée−75%, qui n’est donc pas assimilée à une perte physique nodale démontrée. Le déplacement garde néanmoins un décalage initial maximal d’environ0,000293mm, supérieur au seuil0,00002mm. Ce témoin ne qualifie pas le démarrage ni l’intervalle complet ; les comparaisons au demi-pas et en contact prévues conditionnellement ne sont donc pas exécutées. Tous les échecs initiaux, les acquisitions manquantes et l’arrêt explicite restent dans les sorties.

## 6. Contradictions et informations manquantes

Le défaut complet d’initialisation des prédicteurs, le traitement du premier incrément et la compatibilité entre préparateur Windows et moteur Linux restent à départager. La présence de NINVEL ne garantit pas l’identité de toutes les données de reprise. L’absence d’un appel DYNA_INIV dans l’arbre inspecté est une piste de source, pas une preuve de correction à appliquer. Une comparaison cohérente Windows avec le témoin PCG Linux conservé peut isoler une dépendance de plateforme/version avant toute nouvelle compilation.

Les échecs de qualification mécanique A34 et de raffinement A36 restent conservés. Le contrôle implicite entier A37 a avorté avant son compte rendu, avec cause non identifiée ; les limites documentées des TYPE25 sont distinctes. Aucun nouveau coût de calcul entier n’est projeté depuis ce témoin. Le meilleur impact entier reste20ms A20, et son aperçu ralenti ne représente pas dix secondes physiques.

AIRCRAFT-A39 : comparer le témoin libre PCG Linux échoué A38 à une préparation et un moteur Windows cohérents déjà présents, à mêmes masses, matériaux, vitesses et pas. Vérifier avant calcul que ce contrôle précis n’existe pas déjà; utiliser les résultats mis en cache s’ils existent. Ce changement de plateforme/version est un diagnostic de compatibilité, pas une preuve unique de la cause. Le compteur NINVEL27 est conservé dans les dix reprises inspectées; cela ne qualifie pas tout le pont binaire. Le raccourci de convergence absolue du premier pas est confirmé, mais le désactiver par tolérance plus stricte ne suffit pas : erreur énergétique globale annoncée -75%, décalage de déplacement environ0,000293mm; vitesses et KE nodales correctes aux douze animations partielles. Branche arrêtée, pas de terminaison normale. Ne pas rescaler la vitesse ni modifier la masse, les matériaux ou les reprises. Tout contrôle libre doit conserver les champs, KE/P et déplacement exact; un succès seul permet un nouveau témoin de transition/contact et demi-pas. Les états initiaux/predictors et le calcul global de KE restent à isoler sans nouvelle compilation automatique. La compilation A35 autorisée est terminée39,29min; aucune nouvelle installation ou compilation engagée. Compatibilité implicite entière, peaux A34 et raffinement A36 restent non qualifiés. Meilleur impact entier A20=20ms; objectif dix secondes physiques 3D puis MP4/GIF incomplet. A36+A37 publiées et vérifiées; A38 sera publiée avec A39 après intégrité des deux.
