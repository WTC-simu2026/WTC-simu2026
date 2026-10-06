# Passation AIRCRAFT-A08 → A09

Lire AGENTS.md puis harness/state.json et cette passation. État local prioritaire. A08 huitième itération avion entier terminée comme contrôle limité, pas impact historique qualifié. Résultats : output/aircraft_a08/authoritative_review.json (summary.json initial conservé), additional_verification.json, cached_A07_mass_output_review.json, primary_source_reading_notes.json, converter_mass_reader_diagnosis.json, rapport_aircraft_a08.md, summary_aircraft_a08.png ; r0/FREE,DENSE,SPLIT,FINE,FINE_HALF.5Starter+5Engine+5observateurs, fins0,8ms observées ; aucun ancien Engine. 4829anciens fichiers préservés. V11F/V11R intacts ; V11S/I02I-M différées.

CG A07 corrigé dans le reviewer uniquement : triangles natifs masseα/π, pas m/3. Manuel2022page154eq574 vérifié visuellement. Écart corrigé maximal 3.17e-09mm, seuil10⁻⁵mm inchangé ; ancien échec0,0202956mm conservé. A07 TH/PART omettait pièces moteur (ligne trop longue). A08 dix IDs/ligne, titres uniques, neuf canaux par pièce,32points ADMAS avecVX/VY/VZ. Intégrité et couverture vérifiées.

ANIM/MASS native présente mais VTK installé ne l’exporte pas. Reader propre FASTMAGI10 extrait masses et valide nœuds/coordonnées/vitesses/temps contre convertisseur. TableauMASS+vel reconstructK/P.32ADMAS dépendants masse native0,7181,098444kg retrouvés surhôtesRBE3, poids pas supposéségaux. KEdespartiescoques correspondm/3 etmasseglobaleα/π : comparaisondirecte initiale échouéeconservée, définitiondifférente vérifiéeà12,1Jprès. RKEpartie28indique112,546GJinitialcontre0rotationglobale : canalincompatible, brutpréservé NONajoutéauglobal. Ledgernefermepastravailpylônes/rotation. Sourceformatcopielectureseule/commit9f1d3e399a73b956c9b2b5066d98da44f7c36a97, commitbinaireinconnu. ArrondiscoordVTKjusqu’à0,05mm,sixchiffressignificatifs ; premierreaderéchouégardé,paschangementtolérancesphysiques. CSVinchangé ; adaptateursomme3interfacesdisjointes.

Contrôlefacade déplacéeX15468,6, moteursseulssecondaires ; avioncouplémaisnez/ailesexcluscontact, pastraverséehistorique. Façade59colonnes×3étages, pasplanchers/noyau/précharge. FINE subdivision4coplanaire960→3840tri,624→2208nœuds moteur ; surface/massetotaleégales, joints/RBE3hôtesinchangés. Distributionnodaleetpointscontactchangent, CGpréditvérifié. Courbes2µs,animation0,1ms,demipas0,4vs0,8. MêmeAL/acierplastiqueidéal,hypothèsesA07,aucunerupture. Fan/corepasencorecontactdirectà0,8ms ; pasesdisques/pales/spin/fragments/autocontactmoteur.

|Cas|Fin ms|Triangles|Jx Ns|Générée kJ|Résidu kJ|Plastique moteur|
|---|---:|---:|---:|---:|---:|---:|
|FREE|0.800514|960|0.000|0.000|-0.320|0.000000|
|DENSE|0.800514|960|-6005.975|816.711|-121.559|0.435030|
|SPLIT|0.800514|960|-6005.975|816.711|-121.559|0.435030|
|FINE|0.800514|3840|-4510.912|592.114|-48.356|0.712613|
|FINE_HALF|0.800141|3840|-4506.984|592.955|-47.775|0.712311|

|Comparaison|Cas|Temps ms|ΔJ %|ΔEgén %|Critères J/E|
|---|---|---:|---:|---:|---|
|instrument|DENSE / SPLIT|0.800514|0.00000|0.00000|True/True|
|mesh|SPLIT / FINE|0.800514|24.89382|27.50018|False/False|
|half_dt|FINE / FINE_HALF|0.800141|0.08069|0.08049|True/True|

Critèresphysiqueséchoués visibles ; bilanlocal5%gen+1000J nonqualifié. largest_dense_saved_loss : plusforteperteentre0,226et0,231ms avantPW danscascontact, causepasidentifiée. DENSEΔK−13kJ/gaincontact1,115kJ,IE5,623J,déficit11,880kJ. Necompenserparmasse/amortissement/Ggonflé. Premiergeneratordoublaitairecoarsedansmétadonnéesuniquement ; sortieinitialeconservée, recomputationindépendanteairesdonnediff7,83e−8mm², decksnonaffectés. authoritative_review.jsonsupersèdesummary.json. Deuxmaillages≠convergence, limitesplastiquesconservées. Tousnatifs/CSV/NPZ gardés ; T02initialeseule, readers9/10/12recordsvalidés.

Suite : AIRCRAFT-A09 : utiliser les nouveaux historiques natifs pour expliquer ou borner le déficit d’énergie du contact moteur. Comparer à paramètres matériels inchangés une formulation/gestion du contact explicitement documentée et contrôler les contraintes RBE3 et les énergies de rotation ; déclarer les essais avant exécution et préserver chaque échec. Ne prolonger au premier contact direct du fan-case que si le bilan et la sensibilité spatiale le permettent. La subdivision moteur A08 conserve la surface facettée et la masse mais change la répartition nodale et les points de contact ; deux maillages ne prouvent pas une convergence. Pales/disques, propriétés réelles, rupture/écrasement avec historique et dissipation, autocontact/fragments, planchers/noyau et identification des entrées AA11 restent à traiter. Aucun calage sur les dégâts NIST. V11F/V11R et anciennes sorties intacts ; V11S/I02I-M différées. Publication après la paire A08+A09 vérifiée.

Publications autorisées toutes2itérations : A06+A07 publiée/vérifiéerelease snapshot-2026-10-06-aircraft-a06-a07 ; aprèsA08,pending1,seuleA09complètepair. Lirepublication_cyclepourétatactuel. AucunX/Yoremi. SourcesPDF/HTML/CPP/rendustiers excluspublication. Préférersortiescache,pasrelecturehistoriqueglobale ni scanarchive.
