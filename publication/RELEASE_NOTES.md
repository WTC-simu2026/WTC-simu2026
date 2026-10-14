# Instantané AIRCRAFT-A72+AIRCRAFT-A73 — 14 octobre 2026

Instantané du **14 octobre 2026** : **AIRCRAFT-A73 terminée**, prochaine **AIRCRAFT-A74**, registre **192 entrées**. Objectif dix secondes physiques puis vidéo 3D incomplet.

**A72 : proposition concrète de contexte CHECK explicite.** La garde TT0 ratée A71 est conservée. La source avance TT avant CALL IMP_CHKM ; le correctif propose IMP_CHK>0, en conservant IDYNA2/IQSTAT0/R2exact0 et un diagnostic explicite, et retire l’inclusion COM08 devenue inutile. Quatorze critères de portée passent ; aucun moteur modifié en A72. Cinq lectures scalaires sont préparées, avec offsets typés figés et bornes à vérifier dans le futur binaire. La revue statique ne présume aucune valeur native ni qualification physique.

**A73 : neuvième moteur isolé, autorisé distinctement, appliqué exactement et compilé.** Build en 301.832s sur six CPU, plafond1h, sans GPU ni installation. Les sources/moteurs antérieurs sont conservés ; différence exacte appliquée fuzz0 dans un nouveau workspace puis démontée. Six Engine sur unCPU/plafond180s, zéro Starter, budget entièrement consommé. Le Starter positif propre A71 est réutilisé par empreintes, sans répétition.

**Le contrôle logiciel de la nouvelle garde passe.** Les cinq contextes et R2 sont mesurés directement dans l’enfant, en lecture seule, aux points d’arrêt matériels existants. Aucun scalaire inventé ou instruction/état mécanique modifié. La dynamique libre passe : True, 23 critères aux seuils A67 conservés, TH terminal1.0ms ; aucun crédit entier donné aux témoins. Les anciennes erreurs TT0 A71 et le premier échec d’observation A69 ne sont pas réécrits.

| Contrôle | IDYNA | IQSTAT | IMP_CHK | NCYCLE | TT natif(ms) | R2 |
|---|---:|---:|---:|---:|---:|---:|
| FREE_INITIAL_ZERO_CHECK | 2 | 0 | 1 | 1 | 1.0000625 | 0.0 |
| STATIC_INITIAL_ZERO_CHECK | 0 | 0 | 1 | 1 | 1.0000625 | 0.0 |
| STATIC_POSITIVE_LOAD_CHECK | 0 | 0 | 1 | 1 | 1.0000625 | 4.0 |
| WHOLE_ORIGINAL_CHECK | 2 | 0 | 1 | 1 | 0.001 | 0.0 |
| WHOLE_PAIRED_CHECK | 2 | 0 | 1 | 1 | 0.001 | 0.0 |

**Les scènes entières restent bloquées.** WHOLE_ORIGINAL_CHECK : 0 erreurs/107396 avertissements, 5 TYPE25 ignorés ; WHOLE_PAIRED_CHECK : 0 erreurs/107396 avertissements, 5 TYPE25 ignorés. Les avertissements de préconditionnement et cinq contacts ignorés restent des critères échoués, sans substitution silencieuse ni force ou RKE de compensation. A52nonintégrée, inerties/matériaux/contacts/bilans entiers non qualifiés, aucun prolongement dynamique entier. Toutes les sorties, tentatives ratées, versions, budgets et archives sont conservés. Le prochain audit en lecture seule doit utiliser les résultats A73 et les audits existants ; toute nouvelle modification/compilation ou lot natif nécessite une proposition concrète et un accord distinct.

Les [rapports A72](wtc1_simulation_v8/output/aircraft_a72/rapport_aircraft_a72.md) et [A73](wtc1_simulation_v8/output/aircraft_a73/rapport_aircraft_a73.md) séparent les six catégories de preuve. **Meilleur impact entier : 0,0200001220703125 s.** Dix secondes et vidéo 3D ne sont pas produites ; aucune extrapolation visuelle fabriquée ni ajustement à des dégâts connus. Publication et CI attestent l’intégrité, pas la physique de l’impact réel.


1 archives complémentaires ; 140 archives précédentes conservées. Sources externes exclues, scripts et résultats propres sous MIT. Vérification de publication sans relancer les solveurs.
