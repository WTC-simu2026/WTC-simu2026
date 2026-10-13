# Instantané AIRCRAFT-A50+AIRCRAFT-A51 — 13 octobre 2026

Instantané du **13 octobre 2026** : **AIRCRAFT-A51 terminée**, prochaine étape **AIRCRAFT-A52**. Le registre compte **170 entrées**. Le démarrage natif de la copie à chaînes rigides composées est comparé à la référence, puis les messages de contraintes sont classés depuis les appels réels du moteur.

A50 exécute un nouvel Engine explicite de trois cycles, un threadCPU, en17,858s. Les cinqTYPE25sont conservés. Deux histoires0/10ns et trois animations0/10/20ns correspondent à la référence A45 à la précision enregistrée : masses, énergies, impulsionsXYZ, coordonnées, déplacements et vitesses. La comparaison brute de topologie reste échouée :384extrémités de traits rigides changent, exactement comme les144relations A49. Un audit distinct confirme chaque changement pré-déclaré et l’identité des éléments physiques et autres traits. Les sorties originales sont conservées, aucun ancien solveur relancé.

Le compteur natifADDED MASS=**0,0002019107g**est minuscule mais non nul, identique à A45. Il n’est pas confondu avec les ADMAS non structurelles prescrites. Cette fenêtre20ns sans charge significative ne qualifie pas l’inertie en rotation ou les travaux locaux. La source précise que **CHECKforceISOLV1/IPREC5/ILINE1 puisIKPAT1**, indépendamment du mot-clé de solveur demandé ; ce contrôle n’est pas une dynamique MUMPS qualifiée. Changer seulement le solveur dansCHECKserait neutralisé. Les blocs absents de PUT_KIJ ne sont pas ajoutés.

A51 réemploie l’état natif à temps zéro. L’export texte arrondi échoue à0,05mm ; le lecteur natif vérifie les **48171nœuds**, erreur maximale **0,00167415mm**, sous le seuil inchangé0,003mm. Les302correspondances capturées directement sont confirmées. Les réparations de lecteurs sont conservées dans des fichiers distincts, sans modifier moteur ou physique.

**Une interprétation initiale des messages est rejetée** : les appels TYPE2/RBE2 transmettent ITAB(N), donc les nombres imprimés sont déjà les labels d’entrée. La classification corrigée conserve l’ancienne tentative comme erreur explicite. Les15directions suspectes appartiennent aux racines99/103/107/109/111/119. Les49370messages forment20483paires ordonnées par famille : **37165TYPE2entre ensembles distincts**,11831avec une interface commune,374RBE2. Aucune double contrainte secondaire déclarée ;96interfaces ont des parents de surface potentiellement dépendants. Les groupes de surface ne sont pas assimilés aux facettes ou poids natifs réellement sélectionnés.

La sourceIND_KINE_K laisseNMC2à zéro et traite les couples secondaires à l’intérieur de chaque TYPE2avantRBE2. Une interaction de deuxTYPE2au travers du même noyau constitue une **hypothèse à tester**, aucune cause complète n’est déclarée prouvée. Le prochain reproducer copie une facette complète avec ses peaux, noyau3D, cellules cohésives et deuxTYPE2originaux. Tout regroupement doit conserver facettes, coefficients et déports natifs avant transfert entier.

Les [rapports A50](wtc1_simulation_v8/output/aircraft_a50/rapport_aircraft_a50.md) et [A51](wtc1_simulation_v8/output/aircraft_a51/rapport_aircraft_a51.md) séparent les six catégories de preuve. A51 n’exécute aucun nouveau solveur. Aucun patch logiciel, installation, compilation, masse compensatoire ou ajustement aux dégâts historiques. A49 garde15erreurs mécaniques et cinqTYPE25ignorés en implicite ; A40 chargé/croissance, A34 peaux et A36 raffinement restent échoués.

La vidéo3D des **dix premières secondes physiques** reste incomplète : meilleur impact entier A20 = **0,0200001220703125seconde**. Aucun temps de diagnostic ou de panneau n’est crédité à l’impact entier. L’intégrité de publication ne valide pas la physique ni l’événement historique.

Archives antérieures, tentatives rejetées et critères échoués conservés.


1 archives complémentaires ; 127 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
