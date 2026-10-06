# Passation AIRCRAFT-A09 → A10

Lire AGENTS.md, harness/state.json puis cette passation. A09, neuvième itération avion entier, terminée comme diagnostic limité ; impact/écrasement réels non qualifiés. Résultats autoritatifs : wtc1_simulation_v8/output/aircraft_a09/authoritative_review.json, rapport_aircraft_a09.md, source_interpretation.json, summary_aircraft_a09.png. Neuf cas r0, config principale + extension Stfac déclarées avant calcul, graine 1102034. Neuf Starter/Engine/observateurs normaux, fins 0,4 ms vérifiées, zéro ancien Engine ; 5076 anciens fichiers préservés. V11F/V11R intacts, V11S/I02I-M différées.

Même avion couplé, façade déplacée au front moteur, moteurs seuls au contact extérieur, pas traversée historique. Matériaux A07/A08 inchangés, pas de rupture ni fragments ; fan/core sans contact direct initial. TYPE7 Km=Stfac*Em*tm, Ks=Es*ts, Istf4=min, Istf5=série puis bornes/2. Stfac0,1 ne change pas les historiques BASE_FINE ; extension effective0,01/0,001 change la réponse mais déficit plus grand. PENALTY Iform3 natif confirmé par message Starter32RBE3 ; impulsions/énergies globales identiques BASE_FINE à cet horizon, différences internes quantifiées ; ne pas conclure flag ignoré ou tous canaux identiques.

|Cas|Stfac|Istf|Iform|Fin ms|Triangles|Jx Ns|Générée kJ|Résidu kJ|Plastique|
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

Comparaisons au temps commun :

|Comparaison|Cas|Temps ms|ΔJ %|ΔG %|Critères|
|---|---|---:|---:|---:|---|
|instrument|A08/FINE / BASE_FINE|0.400630|0.00001|0.00002|True/True|
|SERIES_FINE|BASE_FINE / SERIES_FINE|0.400630|0.03034|0.52537|sensibilité, sans sélection|
|SOFT_FINE|BASE_FINE / SOFT_FINE|0.400630|0.00000|0.00000|sensibilité, sans sélection|
|PENALTY_FINE|BASE_FINE / PENALTY_FINE|0.400630|0.00000|0.00000|sensibilité, sans sélection|
|EFFECTIVE_FINE_01|BASE_FINE / EFFECTIVE_FINE_01|0.400630|1.32082|14.03091|sensibilité, sans sélection|
|EFFECTIVE_FINE_001|BASE_FINE / EFFECTIVE_FINE_001|0.400148|7.80563|16.60184|sensibilité, sans sélection|
|mesh|EFFECTIVE_COARSE_001 / EFFECTIVE_FINE_001|0.400148|34.87304|2.83260|False/True|

DenseTH52 :6 canaux ×626/2210 nœuds moteur/hub, plus32ADMAS×3vitesses conservées. Native MASS FASTMAGI10+IDs/vitesses validés ; ledger translation natif global et sous-ensemble moteur sans double ADMAS. REAC=force documentaire, nouveau bilan intègre N dt_ms*0,001 ; appuis nuls ici, pas distinction empirique ancienne ambiguïté. TH/PART tous groupes combinés en un record binaire :13 contact/10 libre, schéma pré-exécution corrigé et premières métadonnées conservées. Canonical9canaux poutres, ordre natif part/ID adapté uniquement dans reviewer.

Rotation indépendante coques : page154eq571–574 I=m_g*(2A/6+t²/12), α/π, omega rad/ms. Première tentative densité kg/mm³ traitée comme g/mm³, script/sorties conservés initial_review_unit_error, correction reader uniquement. Critères inchangés ; après correction comparaison RKE coque reste échouée. Ne pas ajouter cet écart au bilan global. RKE poutre brut initial112,546GJ toujours incompatible rotation globale0, non qualifié. Support/CG comparaison Starter de même précision ; premier arrêt sur nom de champ absent documenté. Critère plastique JSON0,1 déjà utilisé A08, son texte0,2 erroné conservé.

NativeMASS : cinématique Iform2 dépendants0/redis hôtes7181,0984kg ; pénalité Iform3 dépendants7181,0985kg/hôtes≈0. Somme deux domaines validée au même seuil1e−4kg ; ancien test host-only injustifié pour pénalité conservé before_constraint_mass_interpretation et corrigé dans constraint_mass_verification.json, sans relance. Ne pas doubler la masse des points et hôtes. VariantePENALTY :4886canaux internes diffèrent, maximumtranslation1e−4m/s/rotation7,34e−9rad/ms ; globalE/contact identiques, pas touscanaux. PENALTY_FREE énergie générée≈9e−30J, échecstrictzéro préservé.

Suite : AIRCRAFT-A10 : isoler le premier contact dans un témoin élastique sans redistribution RBE3, avec un bilan analytique et les mêmes conventions de sortie. Identifier dans les propriétés/formulations natives la définition des inerties de coque et du canal RKE avant d’ajouter une énergie indépendante au bilan. Comparer contact et pas de temps sur ce témoin avant de retransférer une option qualifiée vers l’avion. Le contact moteur A09 reste énergétiquement et spatialement non qualifié ; ne pas choisir Stfac pour ajuster un résultat et ne pas prolonger la scène comme un écrasement validé. Ensuite seulement : écrasement/rupture avec historique et dissipation, autocontact/fragments, structure et rotors plus réalistes, planchers/noyau et plages d’entrée AA11. Aucun calage sur les dégâts NIST. Préserver V11F/V11R ; V11S/I02I-M différées. Publication A08+A09 due après vérification ; paire suivante A10+A11.

Publications autorisées toutes2itérations : A08+A09 due, vérifier harness/publication_cycle.json et outputs/github_publication/updates_2026-10-06_aircraft_a08_a09/final_remote_verification.json pour état réellement envoyé. Compte/repo WTC-simu2026/WTC-simu2026 ; credentials anonymes GCM disponibles au contrôle actuel, ne jamais enregistrer/imprimer token. Pas X/Yoremi, pas scan archive, pas anciens calculs. Sources tierces exclues du dépôt/release ; rapports et liens conservés. Utiliser états/CSV/NPZ déjà sauvegardés.
