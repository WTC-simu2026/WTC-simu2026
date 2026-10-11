# AIRCRAFT-A35 — moteur MUMPS disponible, qualification mécanique incomplète

Cinq calculs Linux terminés, dont PCG/MUMPS et deux raffinements temporels. Les cinq bilans et quinze échantillons de champs passent; les cinq références énergétiques et de déplacements échouent. Le moteur fonctionne réellement en implicite, mais le préparateur Linux n’a pas pu être lié. Les fichiers frais ont été créés par le préparateur Windows conservé; aucun ancien état calculé réutilisé.

## 1. Faits directement observés ou transcrits

Accord explicite de Jeremy : « Oui, installer et compiler le solveur séparé ». Installation minimale Ubuntu24.04.4WSL et dépendances, sans commande de mise à niveau générale. Moteur et lecteur compilés; préparateur Linux échoué sur cinq interfaces absentes. Aucun stub de mécanique/parser inventé. Bibliothèques MUMPS/MPI présentes au chargement. Les journaux natifs indiquent IMPLICIT OPTION USED, DMUMPS5.6.2 et 51cycles pour MUMPS nominal; ce n’est pas une déduction depuis les seules cartes. Les quinze champs ont des identifiants/finitude/coordonnées/déplacements cohérents et aucune suppression. Conservation de 24527 fichiers antérieurs vérifiée.

## 2. Résultats d’un modèle officiel

Source OpenRadioss préservée : commit bad6688602d770e019b75773d2d5a48b4f9bd918, 10546 fichiers vérifiés. Métadonnées de dépendances changées explicitement, code physique suivi inchangé. Révision82 indisponible; révision59 conservée mais incompatible H3D, puis révision67 vérifiée. Interface Python par défaut activée après une erreur de la branche désactivée, sans carte Python utilisée. Un en-tête local déclare trois fonctions de lecture de checksum H3D déjà définies dans le chargeur C source; aucune implémentation/stub ajouté, H3D non qualifié. GNU Fortran13.3, OpenMPI4.1.6, MUMPS5.6.2, double précision. Licence AGPL3 et licences annexes conservées localement; binaires/sources tierces exclus de publication. Aucun résultat NIST utilisé comme cible.

## 3. Affirmations provenant des archives locales

Aucune nouvelle inspection d’archive, photographie ou vidéo. Aucun de ces témoins n’identifie un comportement historique d’AA11. Les anciens budgets/prises/échecs A34 sont inchangés.

## 4. Hypothèses propres au modèle

Graine1102060, aucun tirage. Cube1mm, huit hexaèdres et27nœuds; masse0,00278g, LAW2source : densité0,00278g/mm³, E73100MPa, ν0,33, seuil324MPa, sans nouvelle rupture. TYPE14/HA8, Isolid14/Ismstr4/Icpre2/Gauss222/Iframe2. Deux faces X fixées sauf ux droit0,001mm en0,05ms; intérieur libre. Newmarkγ0,5/β0,25; pas implicite0,001/0,0005ms, explicite0,00001/0,000005ms. Référence indépendante conventionnelle8nœuds/2³Gauss enregistrée avant calcul. Comparaisons à temps commun natif0,049ms; dernier champ à0,05ms, dernier historique0,049–0,049005ms. Ce témoin dure50µs, pas dix secondes d’impact entier. Seuils originels conservés : énergie2%+10⁻⁷J, déplacement2×10⁻⁵mm, momentum2%+10⁻⁹Ns, travail2%+10⁻⁷J, raffinement temporel0,2%+10⁻⁷J. La compatibilité préparateur Windows/moteur Linux est testée dans ce seul périmètre, sans équivalence générale revendiquée.

## 5. Résultats dérivés

| Contrôle | IE(J) | Référence(J) | Résidu maximal(J) | Résultat original |
|---|---:|---:|---:|---|
| EXPLICIT | 4.140536e-05 | 4.27679785e-05 | 1.541394e-11 | énergie et déplacement échoués |
| EXPLICIT_HALF | 4.140633e-05 | 4.27689831e-05 | 1.020837e-11 | énergie et déplacement échoués |
| PCG | 4.140377e-05 | 4.27679785e-05 | 1.06681694e-09 | énergie et déplacement échoués |
| MUMPS | 4.140377e-05 | 4.27679785e-05 | 1.06681694e-09 | énergie et déplacement échoués |
| MUMPS_HALF | 4.140458e-05 | 4.27679785e-05 | 5.3698794e-10 | énergie et déplacement échoués |

À temps commun, MUMPS diffère de l’explicite d’environ0,00384% en énergie; PCG/MUMPS coïncident à la précision publiée. Rapports de pas demi/initial0,5, pas implicite/explicite100. Ce rapport de pas ne prédit pas l’accélération d’un avion entier. Masse, absence d’ADMAS, bilans et travail plastique nul passent. L’écart à la référence reste environ3,19% en énergie et2,49×10⁻⁵mm en déplacement, hors des seuils.

Les cinq premières tentatives ont échoué au lancement avant exécution du moteur Linux; elles restent distinctes des cinq nouveaux calculs. Un défaut de lecteur associait les réactions à l’ordre des faces dans l’entrée au lieu des identifiants triés dans les sorties. Correction sur les résultats en cache, sans solveur relancé ni seuil changé : momentum/travail explicites passent. Les interprétations impulsion brute ou intégrale de force échouent encore pour les trois implicites; aucun facteur ajouté pour refermer ces écarts. Les anciens fichiers de revue sont conservés à côté de la revue corrigée.

## 6. Contradictions et informations manquantes

Le bilan natif et l’accord explicite/implicite ne qualifient pas la référence mécanique ni le transfert d’efforts. Causes de l’écart référence/opérateur et réactions implicites non identifiées; il faut des contrôles distincts et une lecture des sources. Le préparateur Linux reste incomplet : cpp_create_rbodies_from_rigid_parts_, cpp_evaluate_rbodies_number_from_rigid_parts_, cpp_is_part_with_elements_, cpp_sale_mesh_create_, cpp_get_include_file_by_index. Aucun succès de compilation complète revendiqué. Interface H3D, redémarrage général/cross-version, transition de régime, contact/plasticité/rupture et avion entier restent à qualifier. La réussite du cube ne valide aucune chaîne historique d’effondrement.

Tentative logicielle terminée en 39.29 minutes, sous l’heure autorisée. Rapport/manifestes précédant inscription A35. Publication suivante A34+A35 avec les échecs.

AIRCRAFT-A36 : qualifier le moteur implicite effectivement disponible avant extension entière. Contrôler les mêmes données physiques avec un nouveau témoin du moteur Windows et une référence conventionnelle raffinée pour distinguer écart de formulation/référence et compatibilité du nouveau moteur. Lire dans les sources épinglées le stockage des réactions implicites et le relier à momentum/travail par un témoin distinct; ne pas appliquer un facteur ajusté aux résultats. Vérifier ensuite une transition explicite→implicite avec états fraîchement calculés et mêmes bilans avant un impact entier borné. Le préparateur Windows est inchangé; le préparateur Linux a échoué à cinq interfaces et reste incomplet. La compilation autorisée A35 est terminée en moins d’une heure, sans prolongation de ce budget. Conserver A34, les échecs A35, masse/densité/inertie, sources et seuils. La comparaison mécanique Isolid18/24 préparée reste différée. Objectif : dix secondes physiques 3D puis vidéo/GIF; meilleur entier A20=20ms, objectif incomplet, aucun dommage connu comme cible. Publication A34+A35 après vérification d’intégrité, sans redistribution des binaires ni sources tierces.
