# AIRCRAFT-A10 — témoin isolé et inerties natives

A10 est terminée comme diagnostic numérique limité : 17 Engine neufs (13 contacts, un libre, trois rotations initiales), un Starter initial rejeté et conservé, zéro ancien Engine. Les critères ne sont pas tous satisfaits. Une réduction de pas suffit à fermer les bilans du témoin contraint pour Stfac1 aux facteurs0,05/0,025, mais les contacts plus souples gardent un déficit. Aucun réglage n’est transféré à l’avion. A09 et ses échecs restent inchangés.

## 1. Faits directement observés et transcriptions

Plaque carrée20×20×1mm, façade témoin fixe40×40×1mm, distance initiale1,01mm et gap1mm. Déplacement libre uniquement suivantX, rotations bloquées pour le contact, aucune RBE3/ADMAS/rupture/masse ajoutée. LAW1, rho0,00278g/mm³, E70000MPa, nu0,3 sont des valeurs synthétiques déclarées. Masse mobile1,112g, vitesse1mm/ms =1m/s, K0=0,000556J, P0=0,001112N·s ; rebond conservatif attendu |J|=0,002224N·s et vx=-1m/s. L’énergie de contact fait partie du bilan pendant l’engagement.

Configuration principale et deux extensions horodatées avant leurs nouveaux calculs ; graine1102035, aucun tirage. Les dossiersr0/r1/r2 et chaque générateur sauvegardé rendent les tentatives traçables. Le Starterr0 signale1084 (LAW1 N5 devientN0), puis s’arrête avant Engine ; une déclaration de correction distincte imposeN0 pourr1/r2. Les critères restent inchangés. Les libellés natifs PART sont les noms des pièces, et NODE/INTER utilisent des indicesvar : premières erreurs de lecture conservées et corrections uniquement dans des relectures séparées. Tous les canaux CSV sont comparés aux records binaires T01 float32 natifs, sans modifier le CSV.

Les docs [TH/PART](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_part_starter_r.htm) distinguentRKE etRKERB. Dans le code primaire [0168ab344bd743051e996d90c7c8d80728bb04a8](https://github.com/OpenCourant/OpenCourant/tree/0168ab344bd743051e996d90c7c8d80728bb04a8), hist2.F écrit PARTSAV(22) pourRKE. cinmas.F donne, pour QEPH sans offset, I_nodal=(m/4)(A/12+t²/12) ; c3inmas.F utilise I_element=m(A/(9/2)+t²/12), distribué par les angles/pi. Cette dernière expression diffère de2A/6 utilisée en A09. pmass.F emploie une inertie sphérique stabilisée, dépendant de la longueur et des inerties de section, et pas seulement une inertie géométrique. Les valeurs sont testées ci-dessous à t0 ; l’équivalence intégrale du commit source et du binaire installé n’est pas démontrée.

BCS1TH accumule FTHREAC += (-a)·m·DT12 : sansTH/TITLE, REACX brut représente une impulsion cumulée, pas une force instantanée. Le témoin non nul confirme son égalité avec la variation finale de quantité de mouvement globale, à l’arrondi sauvegardé. La documentation générale la désigne comme force, ce qui ne suffit pas à lire le T-file brut de ce build. Les intégrales de force erronées restent dans review.json ; authoritative_review.json utilise directement l’impulsion et conserve les écarts intermédiaires dus au décalage temporel. A09 n’est pas réécrit.

## 2. Résultats d’un modèle officiel

Aucun résultat WTC/NIST n’est une cible, un critère, ou une donnée ajustée dans ces témoins. Les seules sorties officielles utilisées ici sont celles du solveur natif. Elles constituent des tests numériques, pas des résultats du modèle historique officiel.

## 3. Affirmations des archives locales

Aucune nouvelle lecture d’archive, photographie ou vidéo. Le suivi local A09 et la preuve de publication A08+A09 sont réutilisés. 5505 fichiers antérieurs épinglés parSHA256 sont vérifiés inchangés, comprenant les chaînes de préservation héritées. V11F/V11R restent préservées ; V11S/I02I-M différées.

## 4. Hypothèses propres aux témoins

Ces plaques, les matériaux, la vitesse, l’absence de rupture et les appuis sont des choix de vérification. Un mouvement contraint1D ne reproduit ni un moteur, ni une aile, ni un avion traversant une tour. TYPE7 Istf4 etStfac1/0,01/0,001 sont des sensibilités ; aucune sélection en fonction de dégâts historiques. Le Starter confirme friction0, amortissement normal1e-20, friction visqueuse1 sans friction active, gap constant1 etN0 ; les champs natifs effectifs sont documentés, plutôt que supposés égaux à tous les noms de la déclaration initiale. La rotation initiale des témoins SPIN a les translations fixes et omegaZ=0,01rad/ms ; seuls l’état initial et les canaux d’inertie sont qualifiés, pas une rotation rigide physique.

Critères : résidu énergétique maximal≤1%K0, quantité de mouvement contact≤1%P0, appuis≤2%P0, vitesse finale±1%, variation d’impulsion demi-pas≤1%, variation de résidu demi-pas≤0,5%K0. Les fenêtres échantillonnées sont conservées ; l’intervalle demandé0,0001ms ne force pas une résolution plus fine que le pas réel.

## 5. Résultats dérivés

|Cas|Dernier échantillon ms|Max résidu %K0|vx final m/s|J brut N·s|Erreur contact %P0|Erreur appuis %P0|Critères échoués corrigés|
|---|---:|---:|---:|---:|---:|---:|---|
|FREE|0.399313|0.00000|1.0000000|0.000000000|0.00000|0.00000|aucun|
|K1_DT080|0.397705|18.23799|-0.9492912|0.002437563|79.89344|27.86920|energy_closure,momentum_contact,support_momentum,complete_rebound_speed|
|K1_DT040|0.398751|4.77969|-0.9768889|0.002364429|33.67702|9.37353|energy_closure,momentum_contact,support_momentum,complete_rebound_speed|
|K01_DT080|0.397828|1.48011|-0.9936026|0.002217373|9.29974|4.62303|energy_closure,momentum_contact,support_momentum|
|K01_DT040|0.399607|1.25912|-0.9938182|0.002217459|4.42141|2.19181|energy_closure,momentum_contact,support_momentum|
|K001_DT080|0.397896|3.81813|-0.9808012|0.002202671|3.12492|1.55980|energy_closure,momentum_contact,complete_rebound_speed|
|K001_DT040|0.399851|3.73261|-0.9811617|0.002203066|1.53671|0.76710|energy_closure,momentum_contact,complete_rebound_speed|
|K1_DT010|0.399791|0.46646|-0.9976662|0.002233566|2.48722|0.69590|momentum_contact|
|K1_DT0025|0.399904|0.14243|-0.9992877|0.002223723|0.13469|0.04412|aucun|
|K01_DT010|0.399756|1.19939|-0.9939870|0.002217396|0.81255|0.40127|energy_closure|
|K01_DT0025|0.399975|1.19451|-0.9940096|0.002217361|0.08447|0.04097|energy_closure|
|K001_DT010|0.399963|3.71581|-0.9812458|0.002203152|0.34689|0.17260|energy_closure,complete_rebound_speed|
|K001_DT0025|0.399981|3.71268|-0.9812611|0.002203168|0.05922|0.02903|energy_closure,complete_rebound_speed|
|K1_DT0050|0.399861|0.18075|-0.9990974|0.002224405|0.47911|0.17603|aucun|

Le libre garde exactement K0 etvx aux sorties sauvegardées. La reconstruction indépendante des KE par masses nodales et vitesses est conservée comme diagnostic : elle diffère duKE natif dans le transitoire, de0,176%K0 àdt0,05 et0,0441% àdt0,025 pourStfac1. L’alignement temporel n’est pas qualifié. Un seuil1e-9J introduit dans une première relecture après calcul n’était pas pré-déclaré : ce contrôle exploratoire échoué et sa première synthèse sont conservés, mais séparés des critères déclarés. Aucun critère pré-déclaré n’est retiré. Rotation, énergie interne, hourglass et amortissement de contact sont nuls dans les témoins de translation ; aucun déficit n’est comblé par une énergie hypothétique.

|Paire|Comparaison|ΔJ %|Δmax résidu %K0|Critères J/E|
|---|---|---:|---:|---|
|K1_DT080 / K1_DT040|original_half_dt|3.00029|13.45831|False/False|
|K01_DT080 / K01_DT040|original_half_dt|0.00388|0.22100|True/True|
|K001_DT080 / K001_DT040|original_half_dt|0.01793|0.08552|True/True|
|K1_DT0050 / K1_DT0025|fine_half_dt|0.03066|0.03832|True/True|
|K1_DT010 / K1_DT0025|fourfold_time_refinement|0.44069|0.32403|True/True|
|K01_DT010 / K01_DT0025|fourfold_time_refinement|0.00158|0.00488|True/True|
|K001_DT010 / K001_DT0025|fourfold_time_refinement|0.00073|0.00313|True/True|

|Rotation initiale|Somme inerties prévue g·mm²|RKE global J|RKE pièce J|Erreur global %|Critères échoués|
|---|---:|---:|---:|---:|---|
|QUAD|37.1593333|1.857967e-06|1.857967e-06|0.0000179|aucun|
|TRIA|49.5148889|2.475744e-06|9.313e-07|0.0000180|initial_part_RKE_matches_global|
|BEAM|6.41438667|3.207193e-07|0|0.0000104|initial_part_RKE_matches_global|

Les trois RKE globaux initiaux sont reproduits par les inerties natives déclarées. Le RKE par pièce est différent pourTRIA et nul pourBEAM alors que le global est positif. La signification globaleRKE est donc bornée par ces essais, mais le ledger localRKE reste non qualifié. NiRKE niRKERB ne doivent être ajoutés arbitrairement au bilan global. Les scripts, sorties complètes et unités sont sauvegardés ; temps cumulé des étapes natives et convertisseurs : 40.842s, CPU2threads, pasGPU.

## 6. Contradictions, données manquantes et suite

Les anciens échecs, le passage automatiqueN5→N0, l’ambiguïté force/impulsion brute et les désaccordsRKE par pièce sont conservés. Les contacts plus souples présentent des pertes finales et maximales qui persistent sous raffinement temporel ; leur cause algorithmique n’est pas identifiée. Le bon bilan àStfac1 ne qualifie qu’un témoin simple à translation contraint1D, sans convergence spatiale ni problème de fracture. Aucune explication exhaustive du déficit A09 n’est établie.

AIRCRAFT-A11 : conserver le témoin A10 et ses échecs. Avant tout transfert vers l’avion, vérifier le ledger local RKE des triangles/poutres et l’attribution native des inerties, puis ajouter au témoin un contrôle spatial et un contrôle contact/formulation à raideur déclarée. Stfac1 avec dt_scale0.05/0.025 satisfait seulement le témoin contraint 1D : ne pas le promouvoir comme contact avion qualifié. Les déficits Stfac0.01/0.001 persistent au pas réduit ; cause non identifiée. Les REACX bruts T-file de ce build sont des impulsions cumulées ; ne pas les réintégrer. Maintenir A09 immuable, V11F/V11R préservées et V11S/I02I-M différées. Publication A08+A09 déjà vérifiée ; prochaine paire A10+A11 après vérification, aucun X/Yoremi.

Impact et écrasement historiques non qualifiés ; localisation en flexion après fracture complète non validée ; température imposée distincte d’un incendie calculé ; tests numériques distincts d’une validation de l’effondrement réel ; Blender reste une visualisation. Aucun Blender, aucune publication et aucun envoi externe n’ont été réalisés dansA10.
