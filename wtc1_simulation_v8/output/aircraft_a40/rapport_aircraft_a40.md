# AIRCRAFT-A40 — mouvement libre et reprise à pas constant qualifiés ; contact échoué

La voie implicite MUMPS à pas constant conserve enfin le mouvement libre exact dans les témoins déclarés, avec un plancher explicite de normalisation de force. Les deux pas directs et les deux reprises complètes depuis l’explicite passent leurs critères et comparaisons. Les essais adaptatifs et les deux contacts repris échouent séparément. Aucun nouvel impact entier ni dix secondes physiques produits ; aucun changement de masse, de matériau ou de logiciel.

## 1. Faits directement observés ou transcrits

Neuf nouveaux calculs moteur sont exécutés : huit terminent normalement, le premier s’arrête àt0 sur limite de pas. Cinq préparations Windows fraîches passent sans avertissement ni erreur. Quatre phases implicites réutilisent intégralement des états explicites Linux A37 vérifiés, au lieu de relancer ces calculs réussis. Les empreintes de chaque copie native sont identiques avant/après exécution. Les quatre jonctions conservent coordonnées, déplacement, vitesse, contraintes, énergie spécifique et érosion au même instant, y compris pendant un contact actif.

Le premier pas très fin avec tolérances10⁻¹¹, sans plancher de référence, ne converge pas : résidu relatif extrêmement grand et Infinity dans la trace, réductions du pas jusqu’à environ1,22×10⁻¹²ms, puis ERROR TERMINATION. Aucune avance physique créditée. La branche au demi-pas prévue conditionnellement n’est pas lancée après cet échec.

Avec /IMPL/RREF/LIMIT, les deux essais adaptatifs terminent mais leur mouvement reste faux. Pendant une croissance de pas1,5, la vitesse nodale enregistrée devient approximativement la vitesse initiale divisée par1,5 ; elle redevient la vitesse initiale au pas maximal fixe. Le décalage de déplacement persiste vers0,2mm. La KE globale annoncée ne suffit pas à détecter ce défaut de trajectoire.

Les deux départs implicites à pas constant et leurs deux reprises libres depuis l’explicite terminent et respectent les vitesses, déplacements et budgets. Le contact repris aux deux pas termine avec contact observable et jonction correcte, mais dépasse le budget énergétique et ne passe pas le raffinement.

## 2. Résultats d’un modèle officiel

La documentation /IMPL/RREF/LIMIT prévoit des bornes sur la force de référence utilisée par les critères non linéaires. Le plancher facilite la convergence lorsque cette référence est proche de zéro ; il n’applique pas de charge physique. La documentation /IMPL/DT/1 décrit la croissance du pas selon le nombre d’itérations.

- [Référence de force /IMPL/RREF/LIMIT](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_rref_limit_engine_r.htm)
- [Pas initial /IMPL/DTINI](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dtini_engine_r.htm)
- [Croissance /IMPL/DT/1](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_1_engine_r.htm)

Dans la source figée bad6688602d770e019b75773d2d5a48b4f9bd918, DYNA_INA construit les prédicteurs avec DT2 ; son appel dans IMP_SOLV est limité au premier cycle, et INTE_DYNA prépare le prédicteur suivant avec le pas courant. Une dépendance au pas précédent est une hypothèse de source cohérente avec la trajectoire observée en croissance. Aucun patch natif ni preuve unique de cause interne n’est revendiqué. Le garde-fou d’initialisation des forces TT==DT2 ou IMPL_S0==0 doit aussi être distingué du comportement observé après une reprise àtemps non nul.

Les cartes documentées et le code OpenRadioss ne constituent pas un résultat d’un modèle officiel historique. Aucun résultat NIST utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle consultation d’archive, photographie, vidéo ou PDF. Aucun nouveau fait historique transcrit. Une réussite de ces cubes ne valide pas une chaîne d’impact ou d’effondrement réelle.

## 4. Hypothèses propres au modèle

Graine1102065, zéro tirage. Même cube libre1mm N2,27nœuds,8HA8, masse0,00278g et V0=[−200,5,2]mm/ms, KE0=0,05564031J. Collision fermée de deux cubes identiques, masse0,00556g,54nœuds,16HA8, vitesses initiales±5mm/ms, KE0=6,95×10⁻⁵J. LAW2 inchangée : densité0,00278g/mm³, E73100MPa,ν0,33,yield324MPa ; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. TYPE7 du témoin inchangé : mêmes facettes, gap0,01mm, sans frottement, amortissement déclaré quasi nul. Il ne remplace pas les TYPE25 du modèle entier.

La référence minimale1g·mm/ms² équivaut à1N ; maximum10³⁰. Les témoins qualifiés utilisent les trois tolérances non linéaires10⁻¹¹, MUMPS, Newmarkγ0,5/β0,25 et un pas constant. Le plancher est une normalisation numérique, sans changement de charge, masse, densité ou résistance. Un essai adaptatif séparé conserve la tolérance originelle10⁻⁶ ; il échoue également. Aucun critère physique élargi ni correction artificielle de temps, position, vitesse ou énergie.

Départs libres à0,001/0,0005ms, terme0,1ms. Reprises libres à0,04ms, mêmes pas et terme. Reprises de contact àtemps natif0,00920457ms, pas0,00005/0,000025ms, terme0,015ms. Énergie2%KE0+10⁻⁷J ; momentum2% de la somme des normes initiales+10⁻⁹Ns ; vitesse libre2×10⁻⁴mm/ms ; déplacement libre2×10⁻⁵mm ; comparaison énergétique au demi-pas0,5%KE0+10⁻⁷J. Tous les paramètres et suppléments sont déclarés avant leurs exécutions.

Les états donneurs A37 restent inchangés. Leur revue finale qualifiée et leurs empreintes sont utilisées ; les diagnostics initiaux d’acquisition et de coordonnées, conservés dans les revues brutes A37, ne sont pas effacés. Les nouveaux champs sont aussi examinés séparément avec la borne de six chiffres significatifs et de stockage float32 déjà définie en A23/A37. Les critères littéraux de coordonnées échoués restent présents ; cette vérification de format ne change aucun budget physique.

## 5. Résultats dérivés

| Cas | Critères complets dans le domaine déclaré |
|---|---|
| FREE_ADAPT_I | échoués |
| FREE_RREF_ADAPT_I | échoués |
| FREE_RREF_STANDARD_ADAPT_I | échoués |
| FREE_RREF_FIXED_I | réussis |
| FREE_RREF_FIXED_HALF_I | réussis |
| FREE_RREF_RESTART_BASE | réussis |
| FREE_RREF_RESTART_HALF | réussis |
| CONTACT_RREF_RESTART_BASE | échoués |
| CONTACT_RREF_RESTART_HALF | échoués |

4/9 ensembles passent ; 6/8 historiques passent le budget global. 581 champs passent la vérification de format distincte. Les masses et l’absence d’ADMAS passent dans tous les historiques complets ; quatre jonctions passent.

Les quatre voies libres à pas constant conservent V0, U=tV0, P0 et KE0 dans la précision et la durée déclarées. Le résidu énergétique maximal est environ6,94×10⁻¹⁸J à la précision des données publiées, sans revendiquer cette précision pour le calcul interne. Le demi-pas direct et celui de reprise passent ; aucune continuité de fichier seule n’est utilisée comme qualification. Ce succès est limité au mouvement libre élastique déclaré.

Pendant le contact repris, les résidus sont1,0987056×10⁻⁵J et5,00131×10⁻⁶J contre1,49×10⁻⁶J admis. La réduction du pas améliore l’écart sans satisfaire les critères. Les KE nodales calculées depuis les vitesses publiées ne coïncident pas avec les KE globales ; momentum total et absence de travail extérieur passent. Les comparaisons des composantes énergétiques au demi-pas échouent. Aucun terme RKE ou facteur empirique ne referme ces budgets.

## 6. Contradictions et informations manquantes

Une normalisation correcte de la référence rend le mouvement libre exploitable à pas constant, mais ne qualifie pas la croissance de pas ni le contact chargé repris. Il faut inspecter le sens temporel des vitesses/déplacements/KE publiés et tester un contact démarré directement en implicite, pour distinguer défaut de reprise et défaut du contact/dynamique. L’initialisation d’accélération après changement de régime reste une hypothèse, pas une cause confirmée.

Les propriétés et raffinements A34/A36 restent non qualifiés séparément. L’avortement /IMPL/CHECK entier A37 n’a pas de cause identifiée ; les TYPE25 ne figurent pas parmi les contacts implicites documentés. Aucun coût entier n’est extrapolé depuis ce cube. La compilation A35 reste terminée en39,29min ; aucune nouvelle compilation, installation ou modification de logiciel. Le meilleur impact entier reste A20≈20ms ; la vidéo3D de dix secondes physiques n’est pas achevée.

AIRCRAFT-A41 : utiliser la voie fixe MUMPS/Newmark avec /IMPL/RREF/LIMIT1,1e30 et tolérances1e-11, qui passe le mouvement libre exact et sa reprise native complète au demi-pas A40. Ne pas utiliser la croissance adaptative : vitesse observéeV0/1,5 pendant croissance1,5 puis décalage de déplacement environ0,2mm. Aucun code ou binaire modifié. Les quatre jonctions natives passent, mais le contact repris échoue encore à l’énergie et au demi-pas : résidus1,0987e-5/5,0013e-6J contre1,49e-6J. Inspecter le sens et le temps des vitesses nodales, déplacements et KE dans INTEGRATOR/TH et Newmark, puis déclarer un contact démarré directement en implicite depuis la géométrie initiale, mêmes TYPE7, masses/matériaux/vitesses et pas, afin de séparer contact implicite et initialisation E→I déjà chargé. Réutiliser les résultats explicites A37 vérifiés; ne pas recalculer les témoins réussis, injecter des champs ou inventer un terme RKE. Vérifier séparément le modèle de contrôle /IMPL/CHECK et son rapport avant toute hypothèse sur l’avortement entier A37. Les cinq TYPE25 entiers ne sont pas documentés parmi les contacts implicites; aucune substitution silencieuse. Peaux A34 et raffinement A36 restent échoués. Compilation A35 terminée39,29min; aucune nouvelle compilation/installation ou patch physique automatique. Meilleur impact entier A20=20ms; dix secondes physiques 3D puis vidéo/GIF restent incomplètes. A38+A39 publiées et vérifiées; A40 à publier avec A41 après intégrité des deux.
