# Instantané AIRCRAFT-A34+AIRCRAFT-A35 — 11 octobre 2026

Instantané du **11 octobre 2026** : **AIRCRAFT-A35 terminée**, prochaine étape **AIRCRAFT-A36**. Le registre compte **154 entrées**. A34+A35 ajoutent **neuf calculs natifs terminés** : **un ensemble individuel passe, huit échouent et les neuf bilans énergétiques passent**. Les configurations, scripts, tentatives échouées et limites sont conservés.

A34 affine les peaux LAW12 avec 48 cellules dans le plan et quatre ou huit dans l’épaisseur, à masse physique inchangée de 0,0915 g. Le mouvement libre passe. L’énergie et les raffinements temporels/spatiaux passent, mais les trois champs intérieurs en flexion restent hors du seuil indépendant. Un accord énergétique ne suffit pas pour insérer cette mécanique dans l’avion.

A35 réalise la compilation séparée avec MUMPS explicitement autorisée, en **39,29 minutes**, sous l’heure prévue. Les dépendances minimales ont été installées dans Ubuntu WSL. Le moteur et le lecteur sont compilés; le préparateur Linux échoue à la liaison sur cinq fonctions manquantes. Le solveur Windows est conservé. La source OpenRadioss est figée au commit bad6688602d770e019b75773d2d5a48b4f9bd918, sans modification du code physique suivi; les métadonnées de dépendances et l’interface H3D locale sont documentées. La compilation complète et H3D restent non qualifiés. Les binaires, bibliothèques, archives de compilation et sources tierces ne sont pas redistribués.

Cinq nouveaux calculs du moteur Linux ont été préparés par le préparateur Windows : explicite, demi-pas explicite, PCG, MUMPS et demi-pas MUMPS. Les journaux confirment l’exécution implicite et MUMPS 5.6.2. Cette compatibilité est mesurée seulement sur un cube élastique de 1 mm durant 50 microsecondes. Les cinq bilans, masses et quinze champs passent. L’énergie implicite et explicite diffère d’environ 0,00384 % à temps commun, avec un pas implicite 100 fois plus grand. Ce rapport ne prédit pas le coût de l’impact entier. Les cinq références indépendantes échouent encore : environ 3,19 % d’écart énergétique et 2,49×10⁻⁵ mm de déplacement, au-delà des seuils conservés.

Un lecteur associait les réactions au mauvais ordre de nœuds. La correction par identifiants est vérifiée sur les sorties en cache, sans relancer les solveurs ni changer les critères : impulsions et travaux explicites passent. Les trois transferts implicites échouent encore. Aucun facteur empirique n’est ajouté pour fermer ces écarts. Cinq premières tentatives de lancement, échouées avant le moteur Linux, restent conservées séparément.

Les [rapports A34](wtc1_simulation_v8/output/aircraft_a34/rapport_aircraft_a34.md) et [A35](wtc1_simulation_v8/output/aircraft_a35/rapport_aircraft_a35.md) séparent faits, références, archives, hypothèses, résultats dérivés et lacunes. **27 échantillons de champs natifs** sont contrôlés. Aucun changement des budgets de masse/inertie, aucune densité compensatrice, aucun RKE inventé et aucun dommage connu comme cible. La résistance, la rupture, les prises courbes, les contacts et la transition explicite–implicite restent à qualifier.

La vidéo 3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **20 millisecondes physiques**. Aucun nouvel impact entier ni prolongement balistique inventé. La publication vérifie l’intégrité des fichiers, sans validation historique de l’impact ou de l’effondrement.

Les anciennes archives et critères échoués sont conservés.


2 archives complémentaires ; 116 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
