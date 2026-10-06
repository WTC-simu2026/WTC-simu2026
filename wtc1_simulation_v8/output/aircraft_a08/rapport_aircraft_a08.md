# AIRCRAFT-A08 — mesures natives et comparaison du maillage des moteurs

Huitième itération de la branche avion entier : cinq nouveaux contrôles de0,8ms, géométrie couplée conservée. A08 résout l’écart de centre de masse A07 dans la vérification, ajoute les historiques qui manquaient pour les pièces moteur et leurs inerties, puis compare960 et3840triangles moteur à surface et masse identiques. La physique de l’impact complet reste non qualifiée. Aucun résultat de dégâts NIST n’a été une cible, aucun ancien solveur relancé.

## 1. Faits transcrits et sorties vérifiées

Le [manuel théorique Radioss2022](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_TheoryManual.pdf), page imprimée154, équation574, répartit la masse et l’inertie d’un triangle au nœud i par αi/π, avec αi son angle intérieur. La page153duPDF a été rendue puis examinée : équation et figure51 confirmées. La vérification A07 utilisait des tiers égaux. Relecture de ses fichiers sauvegardés avec cette règle : son ancien écart0,0202956mm est expliqué ; erreur corrigée maximale 3.17e-09mm, seuil original10⁻⁵mm respecté. Ancien échec et ancien rapport conservés, sans changer une masse, un matériau ou une force. Ce succès vérifie la distribution numérique, pas les inerties réelles de rotor.

La [syntaxe TH/PART](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_part_starter_r.htm) prévoit dix champs d’identifiants par ligne. La longue ligne A07 omettait les nouvelles pièces dans le CSV natif ; le lecteur A08 découpe ces identifiants en lignes de dix et vérifie neuf canaux par pièce moteur, avec titres distincts. Canaux IE,KE,HE,PW,RKE,XMOM,YMOM,ZMOM,MASS ;32historiques nodaux VX/VY/VZ pour les masses internes. Pas d’altération du résultat physique A07 : limitation d’observation documentée.

[ANIM/MASS](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_mass_engine_r.htm) active les masses nodales natives. Le convertisseur VTK installé les omet. Lecture indépendante du préfixe binaire FASTMAGI10, sans modifier le solveur : drapeau masse1, tableau de masses suivi des numéros de nœuds. Identifiants, coordonnées, vitesses et temps comparés à la sortie du convertisseur ; masses finies/non négatives, somme contrôlée contre le Starter et invariance entre états vérifiées. Source de format lue en copie, commit du convertisseur9f1d3e399a73b956c9b2b5066d98da44f7c36a97 ; commit exact du binaire installé inconnu. Une première vérification de coordonnées trop stricte a échoué : conversion à six chiffres significatifs, jusqu’à0,05mm d’arrondi. L’enveloppe de précision du format est traitée explicitement, sans changer les tolérances physiques. Tentative et diagnostic conservés.

Cinq Starter sans erreur/avertissement, cinq Engines terminés normalement, cinq observateurs isolés. Chaque T01 natif vérifié ligne par ligne contre le CSV ; seule la ligne initiale T02 utilisée pour la fin réelle, continuation exclue.9/10/12records par frame selon le domaine de contact. Topologie native, supports fixes, absence d’érosion, absence de travail extérieur et masse totale vérifiés. Harnais PASS avant/après calcul ;4829anciens fichiers préservés, dont contrôles V11F/V11R. Temps/exécutables/hash/arguments conservés dans les journaux d’exécution.

## 2. Modèles officiels et dépendances

Dimensions globales et masse sèche CF6-80A/A2 EASA héritées : longueur4239,3mm, largeur2486,6mm, hauteur2415,5mm, masse3980,7kg. Elles n’identifient pas les contours, épaisseurs, attaches, disques ou alliages installés sur AA11. Boeing planning aéroportuaire pour implantation, façade représentative encore dépendante d’entrées NIST. Les propriétés géométriques initiales restent des entrées déclarées ; aucune sortie de dégâts, pénétration ou effondrement utilisée pour ajuster les paramètres. Documents tiers en copies locales sources immuables, exclus de la redistribution ; liens et hashes conservés.

## 3. Affirmations des archives locales

Aucune nouvelle vidéo, photographie ou affirmation d’archive examinée. Pas de scan d’archive, pas de comparaison visuelle pour choisir une résistance ou une loi de rupture. Archives et anciennes itérations intactes.

## 4. Hypothèses, propriétés, unités et protocole

Configuration aircraft_a08_predeclaration.json antérieure aux calculs, graine1102033, zéro tirage. Départs intacts, vitesse(−200,5,2)m/s, aucune trajectoire globale imposée. Avion entier couplé conservé, façade déplacée enXau front des moteurs ; seuls les nœuds moteur sont secondaires au contact. Le nez et les ailes ne touchent pas cette façade dans ces contrôles. Ce n’est pas une traversée historique complète. Façade59colonnes×3étages,944nœuds d’appui, sans planchers/noyau, gravité/précharge. Horizon0,8ms : nacelle touchée en premier, fan/core sans contact direct initial.

Propriétés A07 inchangées : nacelle2mm, aluminium génériqueρ2780kg/m³,E73,1GPa,ν0,33,seuil324MPa ; carters5mm, acier génériqueρ7860kg/m³,E200GPa,ν0,3,seuil427,656MPa. Profils propres au modèle,24positions angulaires.56poutres de liaison,A400mm²,Iyy=Izz80000mm⁴,J160000mm⁴ ; pylônes hérités. Pas de pales/disques/spin, rupture, autocontact moteur ou fragments. Loi plastique idéale avec diagnostic de déformation0,2 : dépassements conservés, pas assimilés à une loi d’écrasement validée.

Budget4500kg par ensemble : carters695,982173kg,nacelle165,694916kg,joints47,773689kg,inertie résiduelle3590,549222kg (16points224,409326kg par moteur). Masse avion121962,860670kg ; total avec façade191273,837943kg. Pas de masse ajoutée pour fermer un bilan. RBE3hôtes moteur, positions et poids inchangés dans la comparaison ; mêmes joints et ancrages. Le raffinement coupe chaque triangle en quatre triangles coplanaires avec milieux d’arête partagés :960→3840éléments et624→2208nœuds moteur. Surface conservée, erreur maximale7.82e-08mm². La répartition nodale selon les angles et les points échantillonnés par le contact changent avec le maillage ; changement du premier moment prédit et contrôlé, pas supposé nul. Deux maillages ne constituent pas une convergence asymptotique.

FREE supprime le contact extérieur. DENSE garde l’interface unique avec historiques toutes2µs au lieu20µs A07. SPLIT crée trois groupes de nœuds disjoints nacelle/fan/core et trois interfaces identiques sur la même façade, somme d’impulsions contrôlée : aucun nœud secondaire en double. FINE affine uniquement les coques moteur ; FINE_HALF réduit le facteur de pas0,8→0,4. Toutes les autres propriétés et viscosités sont conservées ; friction nulle,gap5mm. Animation0,1ms ; CPU2threads, limite300s/Engine, pas de GPU. Schéma du reader et canaux des poutres vérifiés par identifiants/titres, sans supposer leur ordre de déclaration.

## 5. Résultats dérivés et bilans

|Cas|Fin native ms|Triangles moteur|Jx N·s|Générée kJ|Résidu final kJ|Max plastique moteur|
|---|---:|---:|---:|---:|---:|---:|
|FREE|0.800514|960|0.000|0.000|-0.320|0.000000|
|DENSE|0.800514|960|-6005.975|816.711|-121.559|0.435030|
|SPLIT|0.800514|960|-6005.975|816.711|-121.559|0.435030|
|FINE|0.800514|3840|-4510.912|592.114|-48.356|0.712613|
|FINE_HALF|0.800141|3840|-4506.984|592.955|-47.775|0.712311|

|Comparaison|Cas|Temps commun ms|Écart impulsion %|Écart énergie générée %|Critères impulsion/énergie|
|---|---|---:|---:|---:|---|
|instrument|DENSE / SPLIT|0.800514|0.00000|0.00000|True/True|
|mesh|SPLIT / FINE|0.800514|24.89382|27.50018|False/False|
|half_dt|FINE / FINE_HALF|0.800141|0.08069|0.08049|True/True|

Seuils pré-déclarés : instrumentation1%/2%, spatial5%/10%, demi-pas5%/10%. Critère énergétique local inchangé5%générée+1000J après1kJ ; global0,5%Kinitial. Tous les échecs sont conservés :

- FREE : aucun critère échoué
- DENSE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:engine_element_plus_ADMAS_translation_matches_native_parts_1kJ
- SPLIT : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:engine_element_plus_ADMAS_translation_matches_native_parts_1kJ
- FINE : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:engine_element_plus_ADMAS_translation_matches_native_parts_1kJ
- FINE_HALF : energy_local_within_declared_limit, plastic_strain_below_diagnostic_limit, extra:engine_element_plus_ADMAS_translation_matches_native_parts_1kJ

Unités natives g/mm/ms : contraintes MPa, force N, moment Nmm, énergie Nmm×0,001→J, impulsion Nms×0,001→Ns. Les vitesses mm/ms ont la même valeur numérique que m/s. E=Ktranslation+Krotation+IE+hourglass+spring+contact élastique+friction+amortissement ; résidu=ΔE−travail extérieur. PW est inclus dans IE et jamais ajouté deux fois ; générée=Krotation+IE+hourglass+spring+contact élastique. Ktranslation indépendant=Σ½miv² et P=Σmivi avec masses natives. Le contrôle FREE aIE/PW/rotation/contact nuls, translation uniforme et résidu−320J d’arrondi global. Les erreurs et critères du bilan indépendant sont explicités pour chaque cas dans review.json, sans remplacer le résidu natif par une somme choisie.

Deux définitions cinétiques sont explicitement conservées. Le premier ledger moteur ajoute une seule fois l’énergie des32points ADMAS aux KEdes pièces ; sa comparaison initiale aux coques avec masseα/π échoue, échec préservé. La relecture indépendante explique deux différences : les32points ont masse nodale native nulle après transfert vers leurs hôtes RBE3 (7181,098444kg redistribués au total, erreur de somme inférieure0,0001kg) ; et la KEdes parties de coque correspond à une répartition par tiers, à moins12,1J près dans ces états, alors que la masse nodale globale correspond àα/π. Ce sont des définitions différentes, non une énergie manquante que l’on peut ajouter arbitrairement. Le tableau redistribué et la différence d’énergie hôtes/points sont sauvegardés ; à la fin, cette différence vaut environ+32,16kJ sur le maillage courant et−5,29kJ sur le fin. Sa cause détaillée dans la contrainte reste non qualifiée : ne pas appliquer la formule de variance de poids égaux, les poids natifs ne sont pas supposés égaux.

Le canal RKEde la partie28(poutres de liaison) indique112,546GJ dès l’état initial, alors que la rotation globale initiale est nulle et Kglobal vaut2,441GJ. Ce canal est incompatible avec l’interprétation d’une énergie de rotation physique de cette partie ; valeur brute conservée, sémantique non qualifiée. Il n’est ajouté à aucun bilan global. La KEpoutre ne se réduit pas exactement à sa translation, rotation possible à contrôler séparément. Le bilan global reste fondé sur les termes globaux natifs et la translation nodale indépendante ; aucun remplacement par une somme des parties n’est effectué. Travail aux pylônes, rotation indépendante et réactions d’appui à distinguer force/impulsion restent ouverts.

Le premier résumé calculait par erreur deux fois les aires dans les seules métadonnées du maillage courant, parce que ses listes origine et comparaison étaient le même objet. Aucun deck ou calcul n’est affecté. Aires recalculées directement sur les éléments une seule fois, puis comparées : erreur maximale7,83×10⁻⁸mm². summary.json et premières vérifications conservés ; authoritative_review.json et additional_verification.json sont les résultats autoritatifs. Ne pas lire le premier échec de métadonnées comme un changement de géométrie.

Diagnostic des pertes à résolution2µs :

- FREE : plus forte baisse du résidu -0.3200kJ entre 0.798276 et 0.800514ms ; erreur maximale de ΔKtranslation reconstruite 320.000J.
- DENSE : plus forte baisse du résidu -11.8797kJ entre 0.228292 et 0.230530ms ; erreur maximale de ΔKtranslation reconstruite 1859.213J.
- SPLIT : plus forte baisse du résidu -11.8797kJ entre 0.228292 et 0.230530ms ; erreur maximale de ΔKtranslation reconstruite 1859.213J.
- FINE : plus forte baisse du résidu -5.9786kJ entre 0.226054 et 0.228292ms ; erreur maximale de ΔKtranslation reconstruite 1209.257J.
- FINE_HALF : plus forte baisse du résidu -5.2590kJ entre 0.228292 et 0.230157ms ; erreur maximale de ΔKtranslation reconstruite 752.701J.

Incréments natifs K/rotation/IE/contact et contributions des masses/pièces moteur sauvegardés dans largest_dense_saved_loss et independent_translation_engine_ledger.npz ; le RKEbrut des poutres y est conservé comme canal non qualifié. Dans les quatre cas de contact, la plus forte baisse sur un intervalle2µs intervient à l’amorce du contact, avant tout travail plastique. Par exemple DENSE : ΔK−13kJ, gain contact+1,115kJ, gainIE+5,623J, déficit−11,880kJ, PWnul. Ce déficit dépasse l’allocation1kJ d’arrondi. Cela exclut pour cet intervalle une attribution à une fracture ou au travail plastique, sans identifier à lui seul l’algorithme de contact ou la contrainte responsable. Le déficit n’est pas corrigé par ajout de masse, amortissement, rupture artificielle ou ajustement au NIST. Figure summary_aircraft_a08.png issue des états natifs,×1, sans Blender ; lectures exactes et provenance conservées.

## 6. Contradictions, manques et travail restant sur l’impact

L’écart CGA07 et le manque d’observation énergétique des moteurs sont résolus pour ces vérifications. Le bilan local de contact demeure non qualifié ; résultats spatiaux et temporels ci-dessus sont des sensibilités de ce contrôle court, pas des probabilités historiques. Forme/matière interne réelle, rotors, écrasement et rupture d’assemblages non identifiés. Tout prolongement doit annoncer et traiter ces limites.

1. Expliquer ou borner le déficit numérique et vérifier le contact sur une plage spatiale/ temporelle suffisante.
2. Introduire rupture et écrasement avec historique, énergie dissipée et décharge/recharge contrôlés ; ne pas transférer ORTHENERG A06 refusé. Contrat analytique A07 seulement, sans propriétéGmesurée ni implémentation native qualifiée.
3. Compléter structure/inerties/liaisons des moteurs et de l’avion selon sources et sensibilités, puis autocontact/fragments.
4. Ajouter planchers et noyau, identifier les entrées plausibles AA11(vitesse, angle, masse, carburant) et explorer leurs plages sans objectif de dégâts imposé.
5. Produire des états de dommages et de transfert de masse/carburant avec bilans utilisables par les incendies puis la structure. Une température prescrite n’est pas un incendie calculé.

AIRCRAFT-A09 : utiliser les nouveaux historiques natifs pour expliquer ou borner le déficit d’énergie du contact moteur. Comparer à paramètres matériels inchangés une formulation/gestion du contact explicitement documentée et contrôler les contraintes RBE3 et les énergies de rotation ; déclarer les essais avant exécution et préserver chaque échec. Ne prolonger au premier contact direct du fan-case que si le bilan et la sensibilité spatiale le permettent. La subdivision moteur A08 conserve la surface facettée et la masse mais change la répartition nodale et les points de contact ; deux maillages ne prouvent pas une convergence. Pales/disques, propriétés réelles, rupture/écrasement avec historique et dissipation, autocontact/fragments, planchers/noyau et identification des entrées AA11 restent à traiter. Aucun calage sur les dégâts NIST. V11F/V11R et anciennes sorties intacts ; V11S/I02I-M différées. Publication après la paire A08+A09 vérifiée.

Limites maintenues : flexion après fracture complète non validée ; tests numériques≠effondrement réel ; Blender visualisation. Un éventuel effondrement ou son arrêt doit résulter du calcul. A08 est conservée pour la prochaine paire GitHub A08+A09 ; rien envoyé surX.
