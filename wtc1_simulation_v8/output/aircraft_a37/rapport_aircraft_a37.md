# AIRCRAFT-A37 — états natifs transférés, dynamique implicite échouée

Huit nouveaux témoins natifs sont terminés. Les copies complètes des fichiers de reprise conservent les champs à la jonction, y compris pendant un contact actif. Les deux contrôles explicites respectent leurs budgets. Les six voies implicites échouent : le mouvement libre acquiert une vitesse finale de signe opposé et de norme triple, et une énergie cinétique neuf fois initiale. Le contact implicite échoue également au bilan énergétique. Un départ implicite direct reproduit le défaut libre; aucune prolongation de l’impact entier n’est autorisée par ces résultats. La compilation autorisée A35 reste terminée à39,29min.

## 1. Faits directement observés ou transcrits

Quatre témoins libres et quatre témoins de collision fermée utilisent le même moteur Linux MUMPS A35 et des préparations Windows fraîches. Sept phases libres, sept phases de contact et trois observateurs d’un seul cycle sont terminés. Huit préparations de contact initiales échouent avant le moteur et restent conservées : identifiant d’historique partagé puis extraction automatique de surface solide. Une représentation explicite des quatre facettes avant physiques et un identifiant d’historique distinct corrigent ces entrées. Aucun état natif ancien réussi n’est recalculé.

Le contrôle du modèle avion–façade entier utilise les mêmes cartes physiques A20, seules deux lignes de nom changent. Le préparateur termine avec les deux avertissements conservés. Le moteur lit le mode CHECK puis avorte avec code3 avant le compte rendu de contrôle. Son échec ne constitue pas une mesure du coût de la dynamique entière ni un diagnostic natif spécifique du TYPE25.

## 2. Résultats d’un modèle officiel

La documentation Altair décrit l’activation implicite par fichier Engine et la vérification seule par /IMPL/CHECK. Elle liste les contacts implicites TYPE5/7/10/11 : les cinq contacts TYPE25 du modèle entier ne figurent pas dans cette liste. Les432 liaisons TYPE2/Spot5 sont cinématiques; elles ne sont pas assimilées aux liaisons par pénalité. Cette documentation doit être distinguée du comportement du moteur OpenRadioss figé au commit bad6688602d770e019b75773d2d5a48b4f9bd918, dont les empreintes sont déclarées.

Sources primaires :

- [compatibility](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/implicit_features_compatibility_intro_c.htm)
- [activation](https://help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/implicit_analysis_activation_r.htm)
- [check](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_check_engine_r.htm)
- [contact7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm)
- [time_control](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_1_engine_r.htm)
- [time_stop](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_stop_engine_r.htm)

Les sources FREIMPL/imp_solv/imp_dyna enregistrent l’activation, la dynamique Newmark et l’initialisation. Leur inspection ne prouve pas à elle seule la cause de la vitesse erronée. Aucun code physique du solveur n’est modifié; aucun résultat NIST n’est utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle consultation d’archive, photographie ou vidéo historique. Aucun nouveau fait AA11 transcrit. Aucune ressemblance visuelle n’est utilisée pour qualifier le moteur ou la chaîne causale.

## 4. Hypothèses propres au modèle

Graine1102062, zéro tirage. Cube libre1mm N2,27nœuds/8HA8, masse0,00278g. Collision de deux cubes identiques, masse totale0,00556g,54nœuds/16HA8. LAW2 source inchangée : E73100MPa,ν0,33,densité0,00278g/mm³,yield324MPa; TYPE14 Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Aucun ajout de masse, changement de densité, mécanisme de rupture ou inertie artificielle.

Mouvement libre initial[-200,5,2]mm/ms, reprise0,04ms et fin0,1ms, KE initiale0,05564031J. Collision symétrique à±5mm/ms, intervalle initial0,1mm, gap de contact0,01mm; reprise demandée0,0092ms, reprise native réelle0,00920457ms, fin0,015ms. KE initiale6,95×10⁻⁵J. Le TYPE7 sans frottement de ce témoin n’est pas une substitution silencieuse aux TYPE25 de l’avion. Le témoin vise la compatibilité numérique élastique, sans résistance historique qualifiée.

Pas explicite maximal10⁻⁵ms. Newmarkγ0,5/β0,25, MUMPS, pas libres0,001/0,0005ms, pas contacts0,00005/0,000025ms, contrôle de pas déclaré avec bornes. Seuil énergie2% de KE initiale+10⁻⁷J; momentum2% de la somme des normes initiales+10⁻⁹Ns. Demi-pas énergétique0,5%+10⁻⁷J. Les seuils ne sont pas ajustés aux sorties.

Chaque reprise copie intégralement les fichiers natifs fraîchement produits, avec empreintes identiques, sans injection de champs CSV. Les sorties des phases résident dans des dossiers distincts. L’animation de phase1 n’avait pas enregistré exactement la fin de contact : les différences entre temps distincts restent dans les diagnostics initiaux. Trois observateurs explicites d’un cycle lisent les reprises et fournissent les champs à l’instant initial exact, avant leur propre avance. Leur cycle n’est pas crédité à l’impact entier. L’identité coordonnées/déplacement est également examinée séparément avec la borne documentée d’impression à six chiffres et de stockage float32; les critères littéraux initiaux sont conservés.

## 5. Résultats dérivés

| Cas | Jonction | Budgets et champs de la voie |
|---|---|---|
| FREE_EE | réussie | réussis |
| FREE_EI | réussie | échoués |
| FREE_EI_HALF | réussie | échoués |
| FREE_I | sans changement | échoués |
| CONTACT_EE | réussie | réussis |
| CONTACT_EI | réussie | échoués |
| CONTACT_EI_HALF | réussie | échoués |
| CONTACT_I | sans changement | échoués |

2/8 ensembles complets passent; 8/14 jeux d’historiques énergétiques passent; 347 champs et six jonctions passent. Masses et absence de masse ajoutée passent dans tous les historiques. Le contact est actif aux trois jonctions : stress et énergie interne sont observables.

La vitesse libre native passe de[-200,5,2] à[600,-15,-6]mm/ms et KE atteint0,5007628J. Les historiques et animations indépendamment lus confirment le défaut; il ne s’agit pas du seul ordre des colonnes. Les reprises au demi-pas et le départ implicite direct échouent aussi. Pendant la collision, les résidus énergétiques maximaux après reprise sont environ1,0987×10⁻⁵J et5,0013×10⁻⁶J, contre un seuil1,49×10⁻⁶J. Les comparaisons explicite–implicite, demi-pas et départ direct échouent. Un fichier de reprise identique et une jonction correcte ne suffisent donc pas à qualifier la dynamique ultérieure.

## 6. Contradictions et informations manquantes

La cause exacte du défaut libre reste à isoler : initialisation Newmark, interactions avec les options de contraintes automatiques et état de démarrage du moteur. Le paramètre AUTOSPC par défaut n’est pas une cause confirmée. Le contrôle entier avorte avant son rapport; compatibilité générale du pont Windows–Linux et des lois/interfaces complexes non établie. La documentation TYPE25 fournit une limite distincte, pas une explication confirmée de l’avortement.

Les échecs des peaux A34, de référence et raffinement A36 restent conservés. Aucune insertion mécanique entière ni nouvelle simulation de10s. Le meilleur impact entier reste A20=20ms. Aucun ralentissement vidéo, extrapolation balistique ou succès de compilation ne remplace dix secondes de dynamique physique.

AIRCRAFT-A38 : reprendre les états et diagnostics A37, sans répéter les campagnes. La copie complète des reprises natives et les champs à la jonction passent dans les témoins libres et en contact; les deux contrôles explicites passent. Les six voies implicites échouent aux budgets : vitesse libre finale -3 fois la vitesse initiale et KE9 fois initiale, contact actif hors énergie et demi-pas. Départ implicite direct échoue aussi; ne pas attribuer ces effets au seul fichier de reprise. Tester une cause d’initialisation à la fois, dont AUTOSPC par défaut et l’initialisation Newmark, avec le même moteur figé, mêmes masses/matériaux/velocités et référence libre exacte. Arrêter une branche si les budgets échouent. Le contrôle entier /IMPL/CHECK a avorté avant son compte rendu; cause non identifiée. Les cinq contacts TYPE25 ne figurent pas parmi les contacts implicites documentés; ne pas les remplacer silencieusement. Aucun coût entier ni dix secondes ne doit être projeté depuis ces cubes. A34 mécanique des peaux et raffinement A36 restent échoués séparément. Compilation A35 terminée; aucune nouvelle installation/compilation engagée. Préserver tous les échecs. Meilleur impact entier A20=20ms; objectif dix secondes physiques 3D puis vidéo/GIF toujours incomplet. A36+A37 prêtes pour publication autorisée après leur intégrité.
