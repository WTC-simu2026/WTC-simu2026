# AIRCRAFT-A41 — contact direct implicite qualifié dans le témoin ; impact entier à poursuivre

Cinq dynamiques nouvelles terminent et le contrôle CHECK simple termine avec son compte rendu. Quatre contacts directs passent les critères physiques après interprétation des vitesses publiée conforme à la source. Les deux pas les plus fins passent aussi le critère de convergence énergétique. La reprise déjà chargée A40 et sa croissance de pas restent échouées ; aucune insertion dans l’impact entier ni dix secondes physiques déduites de ce résultat.

## 1. Faits directement observés ou transcrits

Les cinq préparations Windows fraîches terminent sans erreur ni avertissement. Le moteur Linux MUMPS A35 inchangé calcule le contact directement depuis la géométrie initiale, sans reprise explicite chargée. Pas successifs0,00005,0,000025,0,0000125,0,00000625 et0,000003125ms ; terme demandé0,015ms. Le sixième raffinement prévu conditionnellement n’est pas exécuté après succès de la paire convergée. Chaque processus reste limité180s, un thread, sans GPU.

Les anciens contrôles comparant directement la vitesse publiée à une vitesse instantanée et les contrôles littéraux de coordonnées restent dans les revues brutes. Le huitième de pas avait été arrêté par un contrôle trop littéral des décimales de temps : ses données physiques passent après application de la borne de format déjà documentée et vérification indépendante du nombre de cycles et des pas réellement imprimés. Les premiers diagnostics sont conservés ; aucun temps enregistré n’est décalé ou resamplé.

Une préparation initiale A40 du témoin libre déjà vérifié est copiée intégralement pour /IMPL/CHECK, sans relancer son préparateur ou sa dynamique. Le moteur écrit BEGIN/END IMPLICIT MODEL CHECKING, puis NORMAL TERMINATION avec code0. Aucun temps de contrôle n’est crédité à l’impact. Le contrôle entier A37 avait avorté avant ce compte rendu ; sa cause reste inconnue.

## 2. Résultats d’un modèle officiel

La documentation décrit /IMPL/DYNA/2 comme méthode Newmark et /IMPL/CHECK comme contrôle de modèle. Elle ne constitue pas une validation du moteur compilé ni d’une chaîne historique.

- [Newmark /IMPL/DYNA/2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_2_engine_r.htm)
- [Contrôle /IMPL/CHECK](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_check_engine_r.htm)

Dans la source figée bad6688602d770e019b75773d2d5a48b4f9bd918, INTEGRATOR/INTEGRATOR_HP appellent INTE_DYNA puis remplacent V par le déplacement incrémental divisé par DT2 et NDT. THNOD publie ce tableau V. ECRIT calcule les vitesses cinétiques dynamiques depuis DY_V et DY_A. La vitesse publiée et la vitesse instantanée Newmark ne sont donc pas interchangeables pendant une accélération. Le sens d’un argument de temps dans ECRIT ne peut pas être déduit du seul scalaire DT1 trouvé dans une reprise : son contexte d’appel compte. Aucune correction empirique du compteur n’est utilisée.

## 3. Affirmations provenant des archives locales

Aucune nouvelle lecture d’archive, photographie, vidéo ou PDF. Aucun nouveau fait AA11 transcrit. La fraction de critères réussis dans ce témoin n’est pas une probabilité de l’événement réel et ne valide pas l’effondrement.

## 4. Hypothèses propres au modèle

Graine1102066, zéro tirage. Même collision fermée de deux cubes1mm N2 :54nœuds,16HA8, masse0,00556g ; V0=±5mm/ms, KE0=6,95×10⁻⁵J. Géométrie séparée et sans force/contact àt0, même TYPE7, mêmes surfaces physiques, gap0,01mm, friction0 et options d’amortissement déclarées. LAW2 densité0,00278g/mm³, E73100MPa,ν0,33,yield324MPa ; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Aucun changement de masse, matériau, inertie ou état physique.

MUMPS/Newmarkγ0,5/β0,25, tolérances non linéaires10⁻¹¹, plancher de référence1N et plafond10³⁰, pas constant sans croissance. NDT=NEXP et NEXP vaut1 dans cette entrée sans partition mixte. Chaque cycle physique est enregistré dans l’historique. Pour ces paramètres, la vitesse sécante est la moyenne des vitesses instantanées adjacentes : v[n]=2×v_sécante[n]−v[n−1], avec la vitesse initiale connue indépendamment. La reconstruction est une lecture dérivée, jamais injectée dans le solveur ou une reprise.

L’identité entre incréments de déplacement et vitesses sécantes, les temps nominaux, le nombre de cycles et les pas imprimés sont vérifiés avant acceptation. La méthode est rejetée pour un pas variable ou des cycles manquants. Les critères physiques restent ceux déclarés : bilan/KE2%KE0+10⁻⁷J, momentum2%+10⁻⁹Ns, masse et absence d’ADMAS, travail externe nul. Comparaison au demi-pas0,5%KE0+10⁻⁷J pour KE, énergie interne et contact élastique. Aucun nouveau terme RKE, facteur ajusté ou cible de dommage connue.

Les bornes six chiffres significatifs/float32 A23 sont appliquées séparément aux coordonnées et aux temps, avec conservation des critères littéraux initiaux. Pour les temps, une comparaison à la grille nominale et les cycles/pas natifs empêchent de confondre une vraie réduction de pas avec l’arrondi d’écriture.

## 5. Résultats dérivés

| Cas | Budget physique et lecture conforme à la source |
|---|---|
| CONTACT_RREF_DIRECT_BASE | échoués |
| CONTACT_RREF_DIRECT_HALF | réussis |
| CONTACT_RREF_DIRECT_QUARTER | réussis |
| CONTACT_RREF_DIRECT_EIGHTH | réussis |
| CONTACT_RREF_DIRECT_SIXTEENTH | réussis |

La relecture au pas initial0,00005ms reste échouée au bilan, environ3,499×10⁻⁶J contre1,49×10⁻⁶J. Les quatre pas suivants passent leurs budgets physiques. Les résidus reconstruits diminuent vers1,173×10⁻⁶,2,789×10⁻⁷,4,213×10⁻⁸ et1,044×10⁻⁸J à la précision publiée. La KE reconstruite coïncide avec la KE native à quelques10⁻¹⁰J, sans coefficient déterminé depuis le résultat. Momentum, masse, absence de masse ajoutée, travail externe nul et contact observable passent.

| Comparaison6,25ns →3,125ns | Écart maximal | Seuil |
|---|---|---|
| KINETIC ENERGY | 2.4267e-07J | 4.475e-07J |
| INTERNAL ENERGY | 2.1228e-07J | 4.475e-07J |
| ELASTIC CONTACT ENERGY | 2.6065e-07J | 4.475e-07J |

La paire converge dans ce domaine temporel déclaré. 1503 champs passent la vérification de format distincte. Les anciens contrôles de vitesse instantanée appliqués à la vitesse sécante restent présents, ainsi que les écarts littéraux de coordonnées et de temps. Cette qualification concerne le contact direct élastique TYPE7 de ce témoin, sans rupture ni représentation historique.

## 6. Contradictions et informations manquantes

La vitesse sécante explique une partie des anciens écarts entre KE nodale et globale, mais ne referme pas le bilan du contact chargé repris A40. Ce sous-domaine reste échoué, de même que la croissance de pas. Les conventions et l’initialisation des états lors d’un changement de régime doivent rester distinctes du contact direct maintenant qualifié.

La réussite CHECK simple n’établit pas la compatibilité entière. L’avortement A37, avant le compte rendu, doit être localisé dans les données/leur lecture/leur complexité. Les cinq contacts TYPE25 entiers ne figurent pas parmi les contacts implicites documentés ; ils ne sont ni validés ni remplacés par ce TYPE7 de témoin. Peaux A34 et raffinement A36 restent non qualifiés. Aucun coût10s extrapolé depuis le cube.

La compilation A35 reste terminée39,29min ; pas d’installation, compilation, patch ou remplacement de logiciel. Meilleur impact entier A20≈20ms ; visualisation3D des dix secondes physiques puis MP4/GIF encore incomplète. Les états et bilans échoués restent conservés.

AIRCRAFT-A42 : reprendre le contact direct implicite qualifié A41 à pas fixes6,25e-6/3,125e-6ms, sans recalculer ces témoins. La vitesse nodale publiée est une vitesse sécante; la reconstruction Newmark àγ.5/β.25 avec tous les cycles est vérifiée par déplacement, KE et momentum natifs. Les comparaisons de KE/IE/contact au demi-pas passent. Garder les diagnostics instantanés et les critères de format initiaux échoués. Le CHECK simple réussit avec compte rendu; l’avortement entier A37 est donc à diagnostiquer dans sa préparation/lecture/complexité, sans attribution automatique aux cinq TYPE25 non documentés pour l’implicite. Inspecter les fichiers et sources en cache pour localiser l’étape d’arrêt, puis déclarer une vérification bornée qui change une seule famille de données à la fois; conserver masse, matériaux, géométrie et anciens résultats. Toute variante de contact entière doit être déclarée, justifiée et comparée, jamais substituée silencieusement. Pas de pilotage/coût10s déduit du cube. La reprise chargée E→I et la croissance de pas A40 restent échouées; ne pas les utiliser. Peaux A34 et raffinement A36 restent non qualifiés. Compilation A35 terminée39,29min; aucune nouvelle compilation/installation ou modification de logiciel. Meilleur impact entier A20=20ms; dix secondes physiques3D puis vidéo/GIF incomplètes. Publier A40+A41 maintenant après intégrité des deux, selon autorisation/cadence.
