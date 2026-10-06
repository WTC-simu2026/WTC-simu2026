# AIRCRAFT-A09 — formulations de contact, contraintes et rotation

Neuvième itération de la branche avion entier. Neuf contrôles neufs de 0,4 ms ont été exécutés ; aucun ancien Engine relancé. Les formulations alternatives testées ne résolvent pas le déficit énergétique du premier contact. La réduction Stfac à 0,1 est inactive dans les historiques sauvegardés de ce contrôle ; des facteurs 0,01 et 0,001, déclarés séparément avant leur calcul, modifient effectivement la réponse mais conservent un déficit plus grand. Aucun de ces réglages n’est sélectionné comme matériau réel ou comme moyen de rejoindre les dégâts NIST.

## 1. Faits transcrits et sorties observées

La [documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) définit, pour les coques, Km = Stfac·Em·tm côté principal et Ks = Es·ts côté secondaire ; Istf=4 utilise min(Km,Ks), Istf=5 leur combinaison en série, puis bornes et division par deux. Stfac ne multiplie donc pas toute la raideur de contact. Le facteur 0,1 peut rester au-dessus de la branche limitante Ks. C’est cohérent avec l’identité constatée, sans prétendre identifier la valeur locale exacte de toutes les raideurs actives.

La [documentation RBE3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe3_starter_r.htm) distingue Iform=2 cinématique et Iform=3 pénalité. Le Starter des cas PENALTY affiche explicitement « 32 OF RBE3 HAVE BEEN SWITCHED TO PENALTY METHOD ». Ces 32 liaisons moteur ont donc été converties ; les 336 autres restent inchangées. L’identité des historiques au premier contact n’implique pas que l’option soit ignorée : les hôtes fan/core ne sont pas encore touchés directement dans ce contrôle court.

La [documentation TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) expose VX/VY/VZ, VRX/VRY/VRZ et REAC comme force. Les nouveaux bilans d’appui intègrent les forces en N dans le temps ; les anciennes interprétations restent sauvegardées. Les réactions sont nulles à cet horizon : les données seules ne distinguent donc pas les deux lectures anciennes. Les rotations nodales sont enregistrées en rad/ms et converties en rad/s ; la somme des carrés utilisée ici est indépendante d’une permutation des axes, sans prétendre avoir calibré séparément chacun des axes angulaires.

Neuf Starter sans erreur/avertissement, neuf Engines et neuf observateurs terminés normalement. Fin native observée par la première ligne T02 isolée, sans utiliser la continuation. CSV T01 comparé au binaire natif, topologie/masse/supports/absence d’érosion et de travail extérieur contrôlés. Le reader FASTMAGI10 des masses valide identifiants, temps, coordonnées et vitesses contre le convertisseur natif. Harnais PASS avant/après ; 5076 anciens fichiers sont préservés.

## 2. Modèles officiels et dépendances

Dimensions EASA CF6-80A/A2 héritées : longueur 4239,3 mm, largeur 2486,6 mm, hauteur 2415,5 mm, masse sèche 3980,7 kg. Ces données ne reconstruisent ni les rotors ni les alliages/attaches réellement installés sur AA11. Implantation globale héritée du document Boeing de planification aéroportuaire. Géométrie nominale de façade encore dépendante d’entrées NIST ; aucune sortie NIST de dommages, pénétration ou effondrement utilisée comme cible.

Le [manuel théorique Radioss 2022](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_TheoryManual.pdf), page imprimée 154, équations 571–574, donne I=m(2A/6+t²/12), Ixx=Iyy=Izz et une répartition nodale αi/π. Sa transcription A08 sert au calcul indépendant de rotation des seules coques moteur. Son identité avec les inerties réellement utilisées par les formulations/propriétés du présent deck n’est pas démontrée ; la comparaison échoue et reste visible. Les copies sources précédentes et nouvelles restent en lecture seule et sont exclues de la redistribution tierce.

## 3. Affirmations des archives locales

Aucune nouvelle archive, vidéo ou photographie examinée. Aucun scan d’archive, aucune ressemblance visuelle utilisée pour identifier un mécanisme. Les anciens calculs et contrôles V11F/V11R restent intacts.

## 4. Hypothèses propres au modèle, propriétés et unités

Configuration principale pré-déclarée aircraft_a09_predeclaration.json, extension aircraft_a09_effective_stiffness_extension.json antérieure aux trois essais supplémentaires ; graine 1102034, zéro tirage. Avion entier couplé, départ intact, vitesse (−200,5,2) m/s. Façade déplacée au front des moteurs ; seules les surfaces moteur participent au contact extérieur. Nez/ailes exclus de ce contact ; absence de planchers/noyau, gravité/précharge, pales/disques/spin, rupture, fragments et autocontact moteur. Ce contrôle de 0,4 ms ne représente pas la traversée complète historique.

Propriétés inchangées : nacelle 2 mm, aluminium générique ρ=2780 kg/m³, E=73,1 GPa, ν=0,33, seuil 324 MPa ; carters 5 mm, acier générique ρ=7860 kg/m³, E=200 GPa, ν=0,3, seuil 427,656 MPa. Loi plastique idéale, pas d’endommagement/rupture. Les 56 poutres moteur ont A=400 mm², Iyy=Izz=80000 mm⁴, J=160000 mm⁴. Budget hypothétique 4500 kg par ensemble moteur ; masse avion 121962,860670 kg, masse totale 191273,837943 kg. Aucun ajout de masse ou de dissipation pour fermer le bilan.

Mêmes surfaces facettées et épaisseurs : 960 triangles courant, 3840 fin par subdivision coplanaire en quatre avec milieux partagés. La répartition nodale et l’échantillonnage du contact changent avec le maillage ; le centre de masse Starter est comparé à celui du parent avec seuil 10⁻⁵ mm. Joints et hôtes RBE3 identiques. TYPE7 : gap constant 5 mm, friction nulle, viscosité normale héritée 10⁻²⁰. Istf=4/5 et Stfac=1/0,1/0,01/0,001 sont des paramètres numériques de sensibilité, pas des propriétés identifiées. Historiques 2 µs ; animations 0,1 ms ; deux threads CPU, aucun GPU, limite 300 s par Engine. IOFLAG et propriétés matérielles inchangés.

Unités natives g/mm/ms : MPa pour contraintes, N pour forces, N·mm×0,001→J, N·ms×0,001→N·s ; mm/ms et m/s même valeur numérique. Densités coques pour le kernel d’inertie : 2,78×10⁻³ g/mm³ et 7,86×10⁻³ g/mm³. I en g·mm², ω en rad/ms : Krot=Σ½Ii|ωi|²×0,001 J. La première vérification indépendante utilisait par erreur une densité kg/mm³ en l’étiquetant g/mm³ ; sorties et script de cette tentative sont préservés dans initial_review_unit_error. Correction du lecteur uniquement, sans nouveau calcul mécanique ni tolérance modifiée. Le premier arrêt sur un nom de champ CG inexistant est documenté séparément ; comparaison corrigée entre sorties Starter de même précision.

Les critères appliqués sont ceux du JSON, inchangés : énergie globale 0,5 % de Kinitial ; bilan local 5 % d’énergie générée + 1000 J après 1000 J générés ; déformation plastique diagnostique 0,1 ; quantité de mouvement 2 % d’impulsion + 10 N·s. Le seuil 0,2 mentionné dans le texte A08 était une erreur de description : ses calculs utilisaient déjà 0,1. Instrumentation 1 %/2 %, spatial 5 %/10 %. Rotation indépendante 5 % + 50 J. Les anciens rapports sont conservés.

## 5. Résultats dérivés et bilans

|Cas|Stfac|Istf|RBE3 Iform|Fin ms|Triangles|Jx N·s|Générée kJ|Résidu kJ|Max plastique moteur|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|BASE_FINE|1.0|4|2|0.400630|3840|-1892.751|276.456|-36.074|0.295476|
|SERIES_FINE|1.0|5|2|0.400630|3840|-1893.146|275.004|-37.266|0.295813|
|SOFT_FINE|0.1|4|2|0.400630|3840|-1892.751|276.456|-36.074|0.295476|
|SOFT_COARSE|0.1|4|2|0.400630|960|-3168.732|325.295|-110.185|0.133361|
|PENALTY_FINE|1.0|4|3|0.400630|3840|-1892.751|276.456|-36.074|0.295476|
|PENALTY_FREE|1.0|4|3|0.400630|3840|0.000|0.000|-0.320|0.000000|
|EFFECTIVE_FINE_01|0.01|4|2|0.400630|3840|-1905.279|237.667|-69.623|0.281062|
|EFFECTIVE_FINE_001|0.001|4|2|0.400148|3840|-2002.561|230.065|-65.165|0.487603|
|EFFECTIVE_COARSE_001|0.001|4|2|0.400623|960|-3072.447|237.431|-185.459|0.103993|

|Comparaison|Cas|Temps commun ms|Écart impulsion %|Écart générée %|Critères J/E|
|---|---|---:|---:|---:|---|
|instrument|A08/FINE / BASE_FINE|0.400630|0.00001|0.00002|True/True|
|SERIES_FINE|BASE_FINE / SERIES_FINE|0.400630|0.03034|0.52537|sensibilité, sans sélection|
|SOFT_FINE|BASE_FINE / SOFT_FINE|0.400630|0.00000|0.00000|sensibilité, sans sélection|
|PENALTY_FINE|BASE_FINE / PENALTY_FINE|0.400630|0.00000|0.00000|sensibilité, sans sélection|
|EFFECTIVE_FINE_01|BASE_FINE / EFFECTIVE_FINE_01|0.400630|1.32082|14.03091|sensibilité, sans sélection|
|EFFECTIVE_FINE_001|BASE_FINE / EFFECTIVE_FINE_001|0.400148|7.80563|16.60184|sensibilité, sans sélection|
|mesh|EFFECTIVE_COARSE_001 / EFFECTIVE_FINE_001|0.400148|34.87304|2.83260|False/True|

L’ajout d’instrumentation est comparé à A08/FINE au temps commun, avec sorties A08 mises en cache. BASE_FINE/SOFT_FINE ont des historiques natifs exactement identiques à la précision sauvegardée. Pour BASE_FINE/PENALTY_FINE, seules les impulsions de contact et les énergies globales sont identiques : des différences internes sont présentes, mesurées dans authoritative_review.json et listées dans raw_history_pair_difference_channels.json. Ne pas généraliser l’identité globale à chaque canal. Istf=5 modifie légèrement la réponse, sans résoudre le bilan. Les facteurs effectifs 0,01/0,001 conservent un déficit ; aucune baisse de résidu sélectionnée pour ajuster la simulation à l’événement. La comparaison spatiale utilise l’interpolation au temps commun, les fins natives différant d’une fraction de pas. Deux maillages ne prouvent pas une convergence asymptotique.

E=Ktranslation+Krotation+IE+hourglass+spring+contact élastique+friction+amortissement. Résidu=ΔE−Wextérieur. PW est inclus dans IE et jamais ajouté deux fois. Énergie générée=Krotation+IE+hourglass+spring+contact élastique, selon le contrat antérieur. Tous les termes natifs et résidus sont sauvegardés ; aucun canal suspect n’est utilisé comme compensation. La translation indépendante Σ½mi vi² et la quantité de mouvement Σmi vi utilisent les masses nodales natives, vérifiées constantes. Le sous-ensemble moteur utilise ces masses redistribuées, pas une duplication des ADMAS et de leurs hôtes. Il ne constitue pas un bilan fermé de travail aux pylônes.

À l’amorce BASE_FINE, plus forte baisse sauvegardée : -5.979 kJ entre 0.226054 et 0.228292 ms. Termes natifs et PW avant/après sont détaillés dans review.json. Cause non identifiée ; pas d’attribution arbitraire à une fracture, absente du deck.

|Cas|Rotation coques indépendante finale J|RKE coques native finale J|Rotation globale native finale J|Erreur maximale coques J|Critère indépendant|
|---|---:|---:|---:|---:|---|
|BASE_FINE|21112.967|4467.303|15622.230|24066.106|False|
|SERIES_FINE|20562.134|4353.048|15251.199|23933.924|False|
|SOFT_FINE|21112.967|4467.303|15622.230|24066.106|False|
|SOFT_COARSE|58426.779|13135.548|43183.832|47257.759|False|
|PENALTY_FINE|21112.967|4467.303|15622.230|24066.106|False|
|PENALTY_FREE|0.000|0.000|0.000|0.000|True|
|EFFECTIVE_FINE_01|15328.291|3323.623|11543.461|20011.216|False|
|EFFECTIVE_FINE_001|27705.602|6233.150|19830.538|24782.898|False|
|EFFECTIVE_COARSE_001|34455.715|7918.317|26241.240|26602.226|False|

La formule théorique indépendante ne reproduit pas les RKE de coque natives après contact, malgré la correction des unités. Cela impose d’identifier la convention d’inertie/formulation avant d’en tirer un bilan : l’écart n’est pas ajouté à l’énergie globale et n’explique pas à lui seul le déficit du contact. Le RKE brut de la partie poutres reste environ 112,546 GJ initial contre rotation globale initiale nulle ; canal conservé mais non qualifié. En libre PENALTY_FREE, résidu -320 J ; les termes générés atteignent seulement 9.0278e-30 J, conservés avec l’échec de l’égalité stricte à zéro. Les écarts d’arrondi ne sont pas confondus avec les dizaines de kJ perdues en contact.

La répartition native d’inertie distingue effectivement les formulations. Iform=2 : masse des 32 points dépendants nulle, environ 7181,0984 kg redistribués aux hôtes. Iform=3 : environ 7181,0985 kg conservés aux points dépendants, excès résiduel sur les hôtes proche de zéro à l’arrondi float32. La somme points+hôtes respecte le même seuil 0,0001 kg dans les neuf cas. Le premier contrôle imposait à tort la redistribution cinématique aux deux variantes : premières revues conservées dans before_constraint_mass_interpretation, correction et preuve dans constraint_mass_verification.json. Aucun changement de masse/deck/énergie ni relance Engine. Les différences internes pénalité/cinématique atteignent seulement 0,0001 m/s en translation moteur et 7,34×10⁻⁹ rad/ms en rotation à la précision du CSV ; les termes globaux restent identiques.

Échecs complets, sans suppression :

- BASE_FINE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native
- SERIES_FINE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native
- SOFT_FINE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native
- SOFT_COARSE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native
- PENALTY_FINE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native
- PENALTY_FREE : free_energies_zero
- EFFECTIVE_FINE_01 : energy_local_within_declared_limit, momentum_contact_facade_balance, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native, extra:support_force_integral_facade
- EFFECTIVE_FINE_001 : energy_local_within_declared_limit, momentum_contact_facade_balance, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native, extra:support_force_integral_facade
- EFFECTIVE_COARSE_001 : energy_local_within_declared_limit, momentum_contact_facade_balance, plastic_strain_below_diagnostic_limit, extra:independent_shell_rotation_matches_native, extra:support_force_integral_facade

## 6. Contradictions, informations manquantes et suite

Intégrité d’exécution et traçabilité vérifiées ; bilan local, sensibilité spatiale et convention de rotation non qualifiés. La variante RBE3 n’a pas encore été sollicitée au premier contact direct fan/core. Une absence d’effet dans 0,4 ms ne qualifie pas son comportement ultérieur. Les facteurs de contact effectivement différents aggravent ici le déficit ; les adopter pour « améliorer » une cible serait injustifié. Aucune loi d’écrasement réel n’est encore validée.

AIRCRAFT-A10 : isoler le premier contact dans un témoin élastique sans redistribution RBE3, avec un bilan analytique et les mêmes conventions de sortie. Identifier dans les propriétés/formulations natives la définition des inerties de coque et du canal RKE avant d’ajouter une énergie indépendante au bilan. Comparer contact et pas de temps sur ce témoin avant de retransférer une option qualifiée vers l’avion. Le contact moteur A09 reste énergétiquement et spatialement non qualifié ; ne pas choisir Stfac pour ajuster un résultat et ne pas prolonger la scène comme un écrasement validé. Ensuite seulement : écrasement/rupture avec historique et dissipation, autocontact/fragments, structure et rotors plus réalistes, planchers/noyau et plages d’entrée AA11. Aucun calage sur les dégâts NIST. Préserver V11F/V11R ; V11S/I02I-M différées. Publication A08+A09 due après vérification ; paire suivante A10+A11.

Il reste sur l’impact : conditions AA11 plausibles et leurs plages, géométrie/inerties/liaisons du Boeing et des moteurs plus réalistes, rupture/écrasement avec historique et dissipation, autocontact/fragments, traversée de façade puis planchers/noyau, enfin transferts cohérents de dommages/masse/carburant vers les incendies et la structure. Température prescrite ≠ incendie calculé ; localisation en flexion après fracture complète non validée ; tests numériques ≠ validation de l’effondrement réel ; Blender demeure une visualisation. A08+A09 forme la paire de publication autorisée, avec tous les échecs visibles ; aucun envoi sur X.
