# Instantané AIRCRAFT-A32+AIRCRAFT-A33 — 11 octobre 2026

Instantané du **11 octobre 2026** : **AIRCRAFT-A33 terminée**, prochaine étape **AIRCRAFT-A34**. Le registre compte **152 entrées**. A32+A33 ajoutent **38 calculs natifs complets** : **29 ensembles individuels passent, neuf échouent et les 38 bilans énergétiques passent**. Tous les résultats, configurations, scripts et critères échoués sont conservés.

A32 compare deux formulations volumiques efficaces à une cellule géométrique dans l’épaisseur, avec même carte LAW12 explicite et masse physique 0,0915 g. Mouvements libres, champs affines et membrane passent. Quatre flexions échouent à leur référence Cxx initiale. Une référence indépendante séparée à faces chargées et intérieur libre révèle une relaxation transverse admissible et une sensibilité du maillage conventionnel; ses raffinements jusqu’à 192×192×16 atteignent 0,65% dans le plan et 0,34% dans l’épaisseur. L’écart natif subsiste; aucun ancien critère remplacé et aucune qualification de flexion accordée.

A33 donne aux peaux des nœuds intérieurs physiquement libres avec deux ou quatre cellules dans l’épaisseur. Huit calculs et 24 échantillons de champs natifs : trois ensembles réussis, cinq échoués, dont le témoin négatif à une cellule. Les bilans, impulsions, travaux aux faces et raffinements passent. Quatre cellules ramènent l’erreur énergétique sous 1%, mais le champ intérieur aux bords reste hors du seuil déclaré. L’accord énergétique seul ne qualifie pas la mécanique ou l’insertion dans l’avion.

Les [rapports A32](wtc1_simulation_v8/output/aircraft_a32/rapport_aircraft_a32.md) et [A33](wtc1_simulation_v8/output/aircraft_a33/rapport_aircraft_a33.md) séparent faits, références, archives, hypothèses, résultats dérivés et lacunes. Au total, 114 échantillons de champs natifs contrôlés, aucun ancien solveur relancé et aucune compensation de masse/inertie, densité modifiée ou RKE inventé. Les coefficients transverses et seuils élastiques LAW12 restent des hypothèses, sans résistance ou rupture historique identifiée. Les prises courbes, collage, décollement et contacts restent à qualifier.

Une proposition en lecture seule décrit une version séparée du solveur avec MUMPS, car le binaire installé refuse les sondes implicites A31. Outils manquants et source candidate figée sont inventoriés. Aucune installation, compilation ou modification logicielle effectuée; ces actions supplémentaires demandent un accord explicite et leur réussite ne garantit pas dix secondes d’impact. Les sources tierces et leurs licences restent exclues de la redistribution; références et empreintes conservées.

La vidéo 3D des **dix premières secondes physiques** reste incomplète : meilleur entier A20 = **20 millisecondes physiques**. Les aperçus ralentis ne remplissent pas cet objectif. Aucun nouvel impact entier ou prolongement balistique inventé. Aucun dommage connu comme cible. La publication vérifie l’intégrité des fichiers, sans validation historique de l’impact ou de l’effondrement.

Les anciennes archives et critères échoués restent conservés.


1 archives complémentaires ; 115 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
