# AIRCRAFT-A20 — cœur en3D, peaux distinctes et nouvel impact exploratoire

Un nouveau départ intact couvre **20.000122100ms physiques**, avec un MP4 et un GIF montrant les positions et suppressions natives des éléments. Le cœur du nez présente désormais un cisaillement et un écrasement finis vérifiés sur témoins. **L'objectif des10 secondes physiques reste incomplet.** Les réussites d'implémentation ne qualifient pas le choc historique ni les bilans entiers échoués.

## 1. Faits directement observés ou transcrits

Graine1102045, zéro tirage. Déclarations préalables du cœur, du sandwich et de l'intégration; revisions d'axes et de couplage conservées. Nouveau modèle:48171nœuds,648solides HA8 de cœur8mm,1296coques de peau0,5mm,432attaches TYPE2. Chaque ancien triangle est subdivisé en3quadrilatères puis extrudé; les deux peaux ont leurs plans moyens à±4,25mm, les faces du cœur à±4mm. Épaisseur matérielle totale9mm. Aire18,5468484323m²; masse41,0627224292kg, budget initial2,214kg/m² conservé. Aucun changement de densité, ADMAS, vitesse[-200;5;2]m/s, autres matériaux, poutres, RBE3, façade ou appuis.

Starter: zéro erreur et deux avertissements1166/343 concernant1803paires initiales de l'autocontact du nez. Le contrôle zéro avertissement reste échoué. Les4contacts extérieurs TYPE25 sont inchangés; l'autocontact des peaux réelles utilise un écart0,5mm, issu des demi-épaisseurs0,25mm de chacune. L'absence d'avertissement incompatible ne qualifie pas le contact des fragments sur plusieurs secondes.

Temps du nouvel impact sur2threads CPU:1191.420s. Fin native20.000122100ms, observateur terminal isolé et fichiers principaux conservés. Les histoires binaires sont confrontées auCSV; coordonnées et vitesses sont confrontées à un second lecteur. Géométrie examinée sur21états, énergie de peau lue dans tous les états conservés. Les états supprimés ne sont pas dessinés comme des solides intacts. Aucun ancien solveur relancé.

## 2. Résultats d'un modèle officiel

Aucun résultat de dommage officiel n'a servi de cible. La documentation primaire Altair précise les entrées du [cœur LAW28](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm), des [solides orthotropes TYPE6](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm) et des [attaches TYPE2](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm). Les axes locaux ont été contrôlés dans le binaire; SKEW/FIX attendY etZ, d'où la conservation des premiers essais mal orientés. La référence générale nominale de façade héritée n'est pas une identification indépendante de tous les détails historiques.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie ou vidéo historique analysée. La fiche Hexcel HRH10 p4 déjà acquise fournit pour le produit de référence3.2-48 des valeurs typiques à température ambiante:rho48kg/m³,E33=138MPa,G31=41/G23=24MPa,τ31=1,21/τ23=0,69MPa,compression nue2,07MPa. Les essais concernent12,7mm; le modèle8mm et le matériau AA11 ne sont pas identifiés par cette fiche. Sources en lecture seule, hashes enregistrés. Les12027anciens fichiers épinglés (49.573Go) sont conservés sans modification constatée.

## 4. Hypothèses propres au modèle

LAW28 à orthotropie découplée, plateaux constants sans densification ni dépendance au taux. E11/E22=1MPa,G12=0,5MPa et résistances dans le plan sont des substituts déclarés. Seuils de rupture normaux[0,2;0,2;0,05],cisaillement[0,1;0,06;0,06]hypothétiques, avec contrôles0,03/0,06/0,12. Le déclenchement natif est vérifié; l'interprétation exacte comme déformation plastique ou totale n'est pas prouvée. AucunG mesuré, ni transfert de ces valeurs vers une assertion historique.

Les peaux réutilisent LAW25 et leurs seuils déclarés. Attaches cœur-peau TYPE2 sans décollement,1320RBE2 dont24attaches idéales de racine. Les solides du cœur sont continus dans chaque facette, séparés entre facettes; les peaux et joints portent les efforts d'arête. La fracture cohésive624bandes conserve ses anciens paramètres hypothétiques. Pas de rupture du métal ou de la façade, de gravité, d'intérieur porteur ni de carburant résolu.

## 5. Résultats dérivés

Le cœur isolé reproduit les énergies élastiques et les plateaux de force attendus dans les directions testées. La rotation90° a une IE≈1,77×10⁻¹⁰J. Le demi-pas reproduit l'IE finale de cisaillement à≈10⁻⁶relatif. Le témoin haut0,12 ne se supprime pas sur le trajetγ0,15; cet échec d'attente reste enregistré. Un trajetγ0,35 pré-déclaré confirme la suppression au chargement supérieur. La réaction TH/NODE du binaire se comporte ici comme une impulsion: la comparaison à la quantité de mouvement et sa dérivée, après retrait de l'inertie imposée, étayent les plateaux; elle n'est pas lue directement comme une force.

Les premiers panneaux sont conservés:offset TYPE51 p1 échoue sur l'énergie de flexion; RBE2 p2 échoue sur le bilan de rotation. Le couplage TYPE2 p3 à offset physique0,25mm passe les quatre contrôles sans ajout de masse:

|Témoin p3|IE finale(J)|Résidu énergétique maximal(J)|Contrôle|
|---|---:|---:|---|
|ROTATION|1.886864e-10|1.20774e-08|réussi|
|MEMBRANE|0.002935094|9.647e-10|réussi|
|SHEAR|0.1025935|9.089e-06|réussi|
|BENDING|0.0002120601|1.063e-07|réussi|

La comparaison initiale brute àA19 échoue de0,00119582mm sur le CGx. La pièce A19 avait un centre natifx1053,83601mm, tandis que l'intégrale de l'aire triangulaire inchangée donne1048,265705615mm. Cœur et peaux A20 concordent avec cette intégrale. Le remplacement du seul moment du nez prédit le CG global avec une erreurx-7.31015461e-08mm, sous le même seuil0,001mm. L'ancien contrôle échoué n'est pas écrasé et la cause exacte de son moment natif n'est pas établie; aucune modification de masse ou de position ne cherche à le reproduire.

À la fin du nouvel impact:IE cœur18794.659497J,peaux200047.222095J,joints5445.038000J. Énergie générée totale22239891.964000J;résidu final-303238.036000J. Minimum par élément peau sauvegardé-3.937582J, cœur échantillonné0.000000J. Ruptures finales:1164/1296peaux,630/648cœurs,619/624joints.

|Contrôle entier|Résultat|
|---|---|
|native_binary_CSV|réussi|
|normal_termination|réussi|
|requested_horizon_reached|réussi|
|declared_connectivity|réussi|
|finite_states|réussi|
|supports_fixed|réussi|
|native_global_mass_expected|réussi|
|animation_mass_matches_native_global_mass|**échoué**|
|animation_nodal_mass_unchanged|réussi|
|no_added_or_scaled_mass|réussi|
|no_external_work|réussi|
|global_energy|réussi|
|local_energy|**échoué**|
|global_support_momentum|réussi|
|contact_facade_momentum|réussi|
|metal_material_domain|**échoué**|
|facade_material_domain|**échoué**|
|beam_material_domain|**échoué**|
|core_part_IE_nonnegative|réussi|
|all_core_facets_IE_nonnegative|réussi|
|skin_part_IE_nonnegative|réussi|
|all_skin_facets_IE_nonnegative|réussi|
|cohesive_part_IE_nonnegative|réussi|
|saved_skin_elements_IE_nonnegative|**échoué**|
|sampled_core_elements_IE_nonnegative|réussi|
|core_final_element_part_IE_agree|réussi|
|zero_initial_IE|réussi|
|no_generated_energy_before_contact|réussi|
|geometric_insertion_addendum_pass|réussi|
|initial_constraint_mass_duplicate_reconciled|réussi|
|original_parent_CG_gate|**échoué**|
|zero_warning_gate|**échoué**|
|independent_translation_delta_KE|réussi|
|independent_delta_momentum|réussi|

La masse physique native initiale vaut191273.837942500kg. La somme du champ nodal d'animation diffère de1.145638179kg après application des contraintes. Le détail Starter supplémentaire Ipri6 montre que la somme NODAL MASSES conserve les masses des secondaires de racine, déjà transportées vers les principaux RBE2. Après identification de ces 1144.154463516g, le résidu de masse imprimée vaut 0.000241697g. Le champ d'animation diffère encore de la somme imprimée de 1.483473718g, dans sa précision float32. Ce champ n'est donc pas un total de masse matérielle. Les masses nodales individuelles subissent ensuite le transfert TYPE2: soustraire les secondaires animés courants serait injustifié. L'ancien contrôle brut est conservé; aucune correction de KE/impulsion ni RKE n'est ajoutée pour fermer le bilan. Plasticité maximale métal2.16686,façade0.477177,poutres1.84703;seuil diagnostique0,1inchangé.

Le MP4/GIF ralentit0.020000122s physiques en6.3s de lecture. Deux vues, déplacement×1, couleur du cœur et peaux distinctes, suppressions natives et horloge explicite. Encodage/décodage et inspection des images première/milieu/dernière vérifiés. Blender n'effectue aucune dynamique ni extrapolation; la lectureGUI n'est pas certifiée. Les10secondes demandées ne sont pas couvertes.

## 6. Contradictions et informations manquantes

Les contrôles locaux réussis n'effacent pas les défauts du modèle entier. Il manque les courbes après pic, effets de taux, énergie de fracture, décollement cœur-peau, qualification du transfert d'inertie aux racines, rupture ductile du métal, intérieur et qualification des fragments. La duplication initiale du champ de masse est expliquée, sans reconstruire une KE matérielle ou valider les inerties sphériques RBE2 en rotation. Le bilan doit passer avant prolongation. Les premiers axes et couplages échoués, ainsi que la comparaison parent-CG échouée, sont explicitement conservés. L'intégrité des fichiers est distincte de la qualification physique.

AIRCRAFT-A21 : objectif vidéo3D10 secondes physiques incomplet. Réutiliser les contrôles LAW28 et sandwich TYPE2 p3 réussis A20, sans relancer A19 ni les anciens témoins. Lire le rapport A20, review.json, geometric_moment_addendum.json, constraint_mass_listing/constraint_mass_interpretation.json et video/video_audit.json. Le nez a maintenant648 solides de cœur8mm et1296 peaux0,5mm distinctes, avec432 attaches TYPE2 conservant l'offset0,25mm. Rupture du cœur et des peaux native, seuils hypothétiques; pas de décollement cœur-peau ni densification. La comparaison CG brute A19 a échoué de0,00119582mm; la nouvelle position correspond à l'intégrale géométrique, sans ajustement de densité/ADMAS, et le défaut de référence parent est conservé. Contrôles entiers encore échoués : animation_mass_matches_native_global_mass, local_energy, metal_material_domain, facade_material_domain, beam_material_domain, saved_skin_elements_IE_nonnegative, original_parent_CG_gate, zero_warning_gate. La somme du champ nodal Starter double-compte1144,1544635g sur les dépendants des24racines RBE2; le détail retrouve la masse matérielle à0,000242g près. La différence supplémentaire1,483474g de l'animation est sous la précisionfloat32. Ne pas additionner ce champ comme une masse physique ou soustraire les secondaires animés pour fermer KE/RKE. Ne pas prolonger vers100ms,1s ou10s ces états hors domaine. Vérifier le bilan local et les éléments à énergie négative; comparer le transfert d'inertie/impulsion des attaches RBE2 à une solution indépendante avant toute correction. Ajouter ensuite une rupture mécanique justifiée du métal et de la façade, à partir de sources et de plages pré-déclarées, sans sélectionner les dégâts connus ni inventer une RKE. Un changement mécanique exige un nouveau départ intact. Gravité, contact des fragments, intérieur porteur et coût de la progression en secondes restent à traiter. Conserver tous les essais w0/w1/w2/w3 et p0/p1/p2/p3. Les paramètres HRH10 typiques concernent12,7mm et ne prouvent pas le matériau historique8mm ni sa fracture dynamique. A12+A13 déjà publiés intacts; A14 àA20 restent locaux en attente d'autorisation externe explicite.
