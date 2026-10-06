"""Seal the bounded A08 results and append the verified local route, without publishing one iteration."""
import argparse,json
from pathlib import Path
import numpy as np
from run_aircraft_a08 import ROOT,OUT,PREV,CFG,read,dump,sha,rel,now,harness,preserved
REPORT=OUT/'rapport_aircraft_a08.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A08_HANDOFF.md'
NEXT=('AIRCRAFT-A09 : utiliser les nouveaux historiques natifs pour expliquer ou borner le déficit d’énergie du contact moteur. '
      'Comparer à paramètres matériels inchangés une formulation/gestion du contact explicitement documentée et contrôler les contraintes RBE3 et les énergies de rotation ; '
      'déclarer les essais avant exécution et préserver chaque échec. Ne prolonger au premier contact direct du fan-case que si le bilan et la sensibilité spatiale le permettent. '
      'La subdivision moteur A08 conserve la surface facettée et la masse mais change la répartition nodale et les points de contact ; deux maillages ne prouvent pas une convergence. '
      'Pales/disques, propriétés réelles, rupture/écrasement avec historique et dissipation, autocontact/fragments, planchers/noyau et identification des entrées AA11 restent à traiter. '
      'Aucun calage sur les dégâts NIST. V11F/V11R et anciennes sorties intacts ; V11S/I02I-M différées. Publication après la paire A08+A09 vérifiée.')
def figure():
    from PIL import Image,ImageDraw,ImageFont
    s=read(OUT/'authoritative_review.json');im=Image.new('RGB',(1600,1000),'#101a29');dr=ImageDraw.Draw(im);f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);sm=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);tf=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',32)
    dr.text((35,25),'A08 — contact moteur et sensibilité au maillage',font=tf,fill='white');dr.text((35,75),'Même surface facettée, mêmes matériaux, même masse — états natifs sauvegardés, déplacements ×1',font=sm,fill='#d0deee')
    inputs=[]
    for case,left in [('SPLIT',40),('FINE',820)]:
        d=OUT/'r0'/case;g=read(d/'generation.json');z=np.load(d/'verified_states_SI.npz');x=z['initial_positions_m']+z['displacement_m'][-1];dr.text((left,120),f'{case} : {len(g["added_engine_shells"])} triangles, fin {z["time_s"][-1]*1000:.6f} ms',font=f,fill='white');box=(left,165,left+735,500);dr.rectangle(box,outline='#71829a')
        def pt(q):return (left+(q[0]-15)*735/5,500-(q[2]+4.6)*335/3.5)
        for _,p,tr in g['added_engine_shells']:
            if p>=25:continue
            vv=[pt(x[n-1]) for n in tr];dr.line(vv+[vv[0]],fill={22:'#ffb454',23:'#64d4fa',24:'#bb93ef'}[p],width=1)
        inputs.append({'path':rel(d/'verified_states_SI.npz'),'sha256':sha(d/'verified_states_SI.npz')})
    dr.text((40,520),'Nacelle orange, enveloppe fan bleue, core violette. Pas de pales, disques, fracture ou fragments qualifiés.',font=sm,fill='#d0deee');dr.text((40,565),'Résultats du contrôle limité aux moteurs',font=tf,fill='white');y=620
    for r in s['cases']:
        dr.text((40,y),f'{r["case"]["id"]:<12} Jx {r["final_contact_impulse_Ns"][0]:9.1f} N·s  |  générée {r["final_generated_energy_J"]/1000:8.2f} kJ  |  résidu {r["final_energy_residual_J"]/1000:8.2f} kJ',font=f,fill='white');y+=44
    for i,c in enumerate(s['comparisons']):dr.text((40+510*i,866),f'{c["comparison"]} : ΔJ {100*c["impulse_difference_fraction"]:.3f}%, ΔE {100*c["generated_energy_difference_fraction"]:.3f}%',font=sm,fill='#77e5a3' if c['impulse_pass'] and c['generated_energy_pass'] else '#ffb454')
    dr.text((40,920),'Bilan local et critères échoués conservés. Cette figure ne valide pas l’impact historique.',font=f,fill='#ffb454');p=OUT/'summary_aircraft_a08.png';im.save(p);inputs.append({'path':rel(OUT/'authoritative_review.json'),'sha256':sha(OUT/'authoritative_review.json')});dump(OUT/'figure_provenance.json',{'created_utc':now(),'inputs':inputs,'output':rel(p),'sha256':sha(p),'displacement_scale':1,'native_mechanical_states':True,'Blender':False,'historical_mechanism_identified':False})
def prepare():
    assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass'];c=read(CFG);cached=read(OUT/'cached_A07_mass_output_review.json');n=preserved();assert n==4829;before=harness();assert before['Status']=='PASS';dump(OUT/'harness_after_calculations.json',before)
    table='\n'.join(f'|{r["case"]["id"]}|{r["actual_main_end_time_ms"]:.6f}|{r["engine_shell_count"]}|{r["final_contact_impulse_Ns"][0]:.3f}|{r["final_generated_energy_J"]/1000:.3f}|{r["final_energy_residual_J"]/1000:.3f}|{r["maximum_engine_shell_plastic_strain"]:.6f}|' for r in s['cases'])
    comparisons='\n'.join(f'|{q["comparison"]}|{" / ".join(q["cases"])}|{q["common_time_ms"]:.6f}|{100*q["impulse_difference_fraction"]:.5f}|{100*q["generated_energy_difference_fraction"]:.5f}|{q["impulse_pass"]}/{q["generated_energy_pass"]}|' for q in s['comparisons'])
    failed='\n'.join('- '+r['case']['id']+' : '+(', '.join(r['failed_checks']) or 'aucun critère échoué') for r in s['cases']);diagnoses='\n'.join(f'- {r["case"]["id"]} : plus forte baisse du résidu {r["largest_dense_saved_loss"]["residual_increment_J"]/1000:.4f}kJ entre {r["largest_dense_saved_loss"]["interval_ms"][0]:.6f} et {r["largest_dense_saved_loss"]["interval_ms"][1]:.6f}ms ; erreur maximale de ΔKtranslation reconstruite {r["native_nodal_translation_delta_KE_max_error_J"]:.3f}J.' for r in s['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A08 — mesures natives et comparaison du maillage des moteurs

Huitième itération de la branche avion entier : cinq nouveaux contrôles de0,8ms, géométrie couplée conservée. A08 résout l’écart de centre de masse A07 dans la vérification, ajoute les historiques qui manquaient pour les pièces moteur et leurs inerties, puis compare960 et3840triangles moteur à surface et masse identiques. La physique de l’impact complet reste non qualifiée. Aucun résultat de dégâts NIST n’a été une cible, aucun ancien solveur relancé.

## 1. Faits transcrits et sorties vérifiées

Le [manuel théorique Radioss2022]({c['nodal_mass_theory']['source']}), page imprimée154, équation574, répartit la masse et l’inertie d’un triangle au nœud i par αi/π, avec αi son angle intérieur. La page153duPDF a été rendue puis examinée : équation et figure51 confirmées. La vérification A07 utilisait des tiers égaux. Relecture de ses fichiers sauvegardés avec cette règle : son ancien écart0,0202956mm est expliqué ; erreur corrigée maximale {max(q['corrected_angle_weighted_error_mm'] for q in cached['cases']):.3g}mm, seuil original10⁻⁵mm respecté. Ancien échec et ancien rapport conservés, sans changer une masse, un matériau ou une force. Ce succès vérifie la distribution numérique, pas les inerties réelles de rotor.

La [syntaxe TH/PART](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_part_starter_r.htm) prévoit dix champs d’identifiants par ligne. La longue ligne A07 omettait les nouvelles pièces dans le CSV natif ; le lecteur A08 découpe ces identifiants en lignes de dix et vérifie neuf canaux par pièce moteur, avec titres distincts. Canaux IE,KE,HE,PW,RKE,XMOM,YMOM,ZMOM,MASS ;32historiques nodaux VX/VY/VZ pour les masses internes. Pas d’altération du résultat physique A07 : limitation d’observation documentée.

[ANIM/MASS](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_mass_engine_r.htm) active les masses nodales natives. Le convertisseur VTK installé les omet. Lecture indépendante du préfixe binaire FASTMAGI10, sans modifier le solveur : drapeau masse1, tableau de masses suivi des numéros de nœuds. Identifiants, coordonnées, vitesses et temps comparés à la sortie du convertisseur ; masses finies/non négatives, somme contrôlée contre le Starter et invariance entre états vérifiées. Source de format lue en copie, commit du convertisseur9f1d3e399a73b956c9b2b5066d98da44f7c36a97 ; commit exact du binaire installé inconnu. Une première vérification de coordonnées trop stricte a échoué : conversion à six chiffres significatifs, jusqu’à0,05mm d’arrondi. L’enveloppe de précision du format est traitée explicitement, sans changer les tolérances physiques. Tentative et diagnostic conservés.

Cinq Starter sans erreur/avertissement, cinq Engines terminés normalement, cinq observateurs isolés. Chaque T01 natif vérifié ligne par ligne contre le CSV ; seule la ligne initiale T02 utilisée pour la fin réelle, continuation exclue.9/10/12records par frame selon le domaine de contact. Topologie native, supports fixes, absence d’érosion, absence de travail extérieur et masse totale vérifiés. Harnais PASS avant/après calcul ;{n}anciens fichiers préservés, dont contrôles V11F/V11R. Temps/exécutables/hash/arguments conservés dans les journaux d’exécution.

## 2. Modèles officiels et dépendances

Dimensions globales et masse sèche CF6-80A/A2 EASA héritées : longueur4239,3mm, largeur2486,6mm, hauteur2415,5mm, masse3980,7kg. Elles n’identifient pas les contours, épaisseurs, attaches, disques ou alliages installés sur AA11. Boeing planning aéroportuaire pour implantation, façade représentative encore dépendante d’entrées NIST. Les propriétés géométriques initiales restent des entrées déclarées ; aucune sortie de dégâts, pénétration ou effondrement utilisée pour ajuster les paramètres. Documents tiers en copies locales sources immuables, exclus de la redistribution ; liens et hashes conservés.

## 3. Affirmations des archives locales

Aucune nouvelle vidéo, photographie ou affirmation d’archive examinée. Pas de scan d’archive, pas de comparaison visuelle pour choisir une résistance ou une loi de rupture. Archives et anciennes itérations intactes.

## 4. Hypothèses, propriétés, unités et protocole

Configuration aircraft_a08_predeclaration.json antérieure aux calculs, graine1102033, zéro tirage. Départs intacts, vitesse(−200,5,2)m/s, aucune trajectoire globale imposée. Avion entier couplé conservé, façade déplacée enXau front des moteurs ; seuls les nœuds moteur sont secondaires au contact. Le nez et les ailes ne touchent pas cette façade dans ces contrôles. Ce n’est pas une traversée historique complète. Façade59colonnes×3étages,944nœuds d’appui, sans planchers/noyau, gravité/précharge. Horizon0,8ms : nacelle touchée en premier, fan/core sans contact direct initial.

Propriétés A07 inchangées : nacelle2mm, aluminium génériqueρ2780kg/m³,E73,1GPa,ν0,33,seuil324MPa ; carters5mm, acier génériqueρ7860kg/m³,E200GPa,ν0,3,seuil427,656MPa. Profils propres au modèle,24positions angulaires.56poutres de liaison,A400mm²,Iyy=Izz80000mm⁴,J160000mm⁴ ; pylônes hérités. Pas de pales/disques/spin, rupture, autocontact moteur ou fragments. Loi plastique idéale avec diagnostic de déformation0,2 : dépassements conservés, pas assimilés à une loi d’écrasement validée.

Budget4500kg par ensemble : carters695,982173kg,nacelle165,694916kg,joints47,773689kg,inertie résiduelle3590,549222kg (16points224,409326kg par moteur). Masse avion121962,860670kg ; total avec façade191273,837943kg. Pas de masse ajoutée pour fermer un bilan. RBE3hôtes moteur, positions et poids inchangés dans la comparaison ; mêmes joints et ancrages. Le raffinement coupe chaque triangle en quatre triangles coplanaires avec milieux d’arête partagés :960→3840éléments et624→2208nœuds moteur. Surface conservée, erreur maximale{s['engine_surface_area_max_error_mm2']:.3g}mm². La répartition nodale selon les angles et les points échantillonnés par le contact changent avec le maillage ; changement du premier moment prédit et contrôlé, pas supposé nul. Deux maillages ne constituent pas une convergence asymptotique.

FREE supprime le contact extérieur. DENSE garde l’interface unique avec historiques toutes2µs au lieu20µs A07. SPLIT crée trois groupes de nœuds disjoints nacelle/fan/core et trois interfaces identiques sur la même façade, somme d’impulsions contrôlée : aucun nœud secondaire en double. FINE affine uniquement les coques moteur ; FINE_HALF réduit le facteur de pas0,8→0,4. Toutes les autres propriétés et viscosités sont conservées ; friction nulle,gap5mm. Animation0,1ms ; CPU2threads, limite300s/Engine, pas de GPU. Schéma du reader et canaux des poutres vérifiés par identifiants/titres, sans supposer leur ordre de déclaration.

## 5. Résultats dérivés et bilans

|Cas|Fin native ms|Triangles moteur|Jx N·s|Générée kJ|Résidu final kJ|Max plastique moteur|
|---|---:|---:|---:|---:|---:|---:|
{table}

|Comparaison|Cas|Temps commun ms|Écart impulsion %|Écart énergie générée %|Critères impulsion/énergie|
|---|---|---:|---:|---:|---|
{comparisons}

Seuils pré-déclarés : instrumentation1%/2%, spatial5%/10%, demi-pas5%/10%. Critère énergétique local inchangé5%générée+1000J après1kJ ; global0,5%Kinitial. Tous les échecs sont conservés :

{failed}

Unités natives g/mm/ms : contraintes MPa, force N, moment Nmm, énergie Nmm×0,001→J, impulsion Nms×0,001→Ns. Les vitesses mm/ms ont la même valeur numérique que m/s. E=Ktranslation+Krotation+IE+hourglass+spring+contact élastique+friction+amortissement ; résidu=ΔE−travail extérieur. PW est inclus dans IE et jamais ajouté deux fois ; générée=Krotation+IE+hourglass+spring+contact élastique. Ktranslation indépendant=Σ½miv² et P=Σmivi avec masses natives. Le contrôle FREE aIE/PW/rotation/contact nuls, translation uniforme et résidu−320J d’arrondi global. Les erreurs et critères du bilan indépendant sont explicités pour chaque cas dans review.json, sans remplacer le résidu natif par une somme choisie.

Deux définitions cinétiques sont explicitement conservées. Le premier ledger moteur ajoute une seule fois l’énergie des32points ADMAS aux KEdes pièces ; sa comparaison initiale aux coques avec masseα/π échoue, échec préservé. La relecture indépendante explique deux différences : les32points ont masse nodale native nulle après transfert vers leurs hôtes RBE3 (7181,098444kg redistribués au total, erreur de somme inférieure0,0001kg) ; et la KEdes parties de coque correspond à une répartition par tiers, à moins12,1J près dans ces états, alors que la masse nodale globale correspond àα/π. Ce sont des définitions différentes, non une énergie manquante que l’on peut ajouter arbitrairement. Le tableau redistribué et la différence d’énergie hôtes/points sont sauvegardés ; à la fin, cette différence vaut environ+32,16kJ sur le maillage courant et−5,29kJ sur le fin. Sa cause détaillée dans la contrainte reste non qualifiée : ne pas appliquer la formule de variance de poids égaux, les poids natifs ne sont pas supposés égaux.

Le canal RKEde la partie28(poutres de liaison) indique112,546GJ dès l’état initial, alors que la rotation globale initiale est nulle et Kglobal vaut2,441GJ. Ce canal est incompatible avec l’interprétation d’une énergie de rotation physique de cette partie ; valeur brute conservée, sémantique non qualifiée. Il n’est ajouté à aucun bilan global. La KEpoutre ne se réduit pas exactement à sa translation, rotation possible à contrôler séparément. Le bilan global reste fondé sur les termes globaux natifs et la translation nodale indépendante ; aucun remplacement par une somme des parties n’est effectué. Travail aux pylônes, rotation indépendante et réactions d’appui à distinguer force/impulsion restent ouverts.

Le premier résumé calculait par erreur deux fois les aires dans les seules métadonnées du maillage courant, parce que ses listes origine et comparaison étaient le même objet. Aucun deck ou calcul n’est affecté. Aires recalculées directement sur les éléments une seule fois, puis comparées : erreur maximale7,83×10⁻⁸mm². summary.json et premières vérifications conservés ; authoritative_review.json et additional_verification.json sont les résultats autoritatifs. Ne pas lire le premier échec de métadonnées comme un changement de géométrie.

Diagnostic des pertes à résolution2µs :

{diagnoses}

Incréments natifs K/rotation/IE/contact et contributions des masses/pièces moteur sauvegardés dans largest_dense_saved_loss et independent_translation_engine_ledger.npz ; le RKEbrut des poutres y est conservé comme canal non qualifié. Dans les quatre cas de contact, la plus forte baisse sur un intervalle2µs intervient à l’amorce du contact, avant tout travail plastique. Par exemple DENSE : ΔK−13kJ, gain contact+1,115kJ, gainIE+5,623J, déficit−11,880kJ, PWnul. Ce déficit dépasse l’allocation1kJ d’arrondi. Cela exclut pour cet intervalle une attribution à une fracture ou au travail plastique, sans identifier à lui seul l’algorithme de contact ou la contrainte responsable. Le déficit n’est pas corrigé par ajout de masse, amortissement, rupture artificielle ou ajustement au NIST. Figure summary_aircraft_a08.png issue des états natifs,×1, sans Blender ; lectures exactes et provenance conservées.

## 6. Contradictions, manques et travail restant sur l’impact

L’écart CGA07 et le manque d’observation énergétique des moteurs sont résolus pour ces vérifications. Le bilan local de contact demeure non qualifié ; résultats spatiaux et temporels ci-dessus sont des sensibilités de ce contrôle court, pas des probabilités historiques. Forme/matière interne réelle, rotors, écrasement et rupture d’assemblages non identifiés. Tout prolongement doit annoncer et traiter ces limites.

1. Expliquer ou borner le déficit numérique et vérifier le contact sur une plage spatiale/ temporelle suffisante.
2. Introduire rupture et écrasement avec historique, énergie dissipée et décharge/recharge contrôlés ; ne pas transférer ORTHENERG A06 refusé. Contrat analytique A07 seulement, sans propriétéGmesurée ni implémentation native qualifiée.
3. Compléter structure/inerties/liaisons des moteurs et de l’avion selon sources et sensibilités, puis autocontact/fragments.
4. Ajouter planchers et noyau, identifier les entrées plausibles AA11(vitesse, angle, masse, carburant) et explorer leurs plages sans objectif de dégâts imposé.
5. Produire des états de dommages et de transfert de masse/carburant avec bilans utilisables par les incendies puis la structure. Une température prescrite n’est pas un incendie calculé.

{NEXT}

Limites maintenues : flexion après fracture complète non validée ; tests numériques≠effondrement réel ; Blender visualisation. Un éventuel effondrement ou son arrêt doit résulter du calcul. A08 est conservée pour la prochaine paire GitHub A08+A09 ; rien envoyé surX.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation AIRCRAFT-A08 → A09

Lire AGENTS.md puis harness/state.json et cette passation. État local prioritaire. A08 huitième itération avion entier terminée comme contrôle limité, pas impact historique qualifié. Résultats : output/aircraft_a08/authoritative_review.json (summary.json initial conservé), additional_verification.json, cached_A07_mass_output_review.json, primary_source_reading_notes.json, converter_mass_reader_diagnosis.json, rapport_aircraft_a08.md, summary_aircraft_a08.png ; r0/FREE,DENSE,SPLIT,FINE,FINE_HALF.5Starter+5Engine+5observateurs, fins0,8ms observées ; aucun ancien Engine. {n}anciens fichiers préservés. V11F/V11R intacts ; V11S/I02I-M différées.

CG A07 corrigé dans le reviewer uniquement : triangles natifs masseα/π, pas m/3. Manuel2022page154eq574 vérifié visuellement. Écart corrigé maximal {max(q['corrected_angle_weighted_error_mm'] for q in cached['cases']):.3g}mm, seuil10⁻⁵mm inchangé ; ancien échec0,0202956mm conservé. A07 TH/PART omettait pièces moteur (ligne trop longue). A08 dix IDs/ligne, titres uniques, neuf canaux par pièce,32points ADMAS avecVX/VY/VZ. Intégrité et couverture vérifiées.

ANIM/MASS native présente mais VTK installé ne l’exporte pas. Reader propre FASTMAGI10 extrait masses et valide nœuds/coordonnées/vitesses/temps contre convertisseur. TableauMASS+vel reconstructK/P.32ADMAS dépendants masse native0,7181,098444kg retrouvés surhôtesRBE3, poids pas supposéségaux. KEdespartiescoques correspondm/3 etmasseglobaleα/π : comparaisondirecte initiale échouéeconservée, définitiondifférente vérifiéeà12,1Jprès. RKEpartie28indique112,546GJinitialcontre0rotationglobale : canalincompatible, brutpréservé NONajoutéauglobal. Ledgernefermepastravailpylônes/rotation. Sourceformatcopielectureseule/commit9f1d3e399a73b956c9b2b5066d98da44f7c36a97, commitbinaireinconnu. ArrondiscoordVTKjusqu’à0,05mm,sixchiffressignificatifs ; premierreaderéchouégardé,paschangementtolérancesphysiques. CSVinchangé ; adaptateursomme3interfacesdisjointes.

Contrôlefacade déplacéeX15468,6, moteursseulssecondaires ; avioncouplémaisnez/ailesexcluscontact, pastraverséehistorique. Façade59colonnes×3étages, pasplanchers/noyau/précharge. FINE subdivision4coplanaire960→3840tri,624→2208nœuds moteur ; surface/massetotaleégales, joints/RBE3hôtesinchangés. Distributionnodaleetpointscontactchangent, CGpréditvérifié. Courbes2µs,animation0,1ms,demipas0,4vs0,8. MêmeAL/acierplastiqueidéal,hypothèsesA07,aucunerupture. Fan/corepasencorecontactdirectà0,8ms ; pasesdisques/pales/spin/fragments/autocontactmoteur.

|Cas|Fin ms|Triangles|Jx Ns|Générée kJ|Résidu kJ|Plastique moteur|
|---|---:|---:|---:|---:|---:|---:|
{table}

|Comparaison|Cas|Temps ms|ΔJ %|ΔEgén %|Critères J/E|
|---|---|---:|---:|---:|---|
{comparisons}

Critèresphysiqueséchoués visibles ; bilanlocal5%gen+1000J nonqualifié. largest_dense_saved_loss : plusforteperteentre0,226et0,231ms avantPW danscascontact, causepasidentifiée. DENSEΔK−13kJ/gaincontact1,115kJ,IE5,623J,déficit11,880kJ. Necompenserparmasse/amortissement/Ggonflé. Premiergeneratordoublaitairecoarsedansmétadonnéesuniquement ; sortieinitialeconservée, recomputationindépendanteairesdonnediff7,83e−8mm², decksnonaffectés. authoritative_review.jsonsupersèdesummary.json. Deuxmaillages≠convergence, limitesplastiquesconservées. Tousnatifs/CSV/NPZ gardés ; T02initialeseule, readers9/10/12recordsvalidés.

Suite : {NEXT}

Publications autorisées toutes2itérations : A06+A07 publiée/vérifiéerelease snapshot-2026-10-06-aircraft-a06-a07 ; aprèsA08,pending1,seuleA09complètepair. Lirepublication_cyclepourétatactuel. AucunX/Yoremi. SourcesPDF/HTML/CPP/rendustiers excluspublication. Préférersortiescache,pasrelecturehistoriqueglobale ni scanarchive.
''',encoding='utf-8')
    own=list(OUT.rglob('*'))+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in ['run_aircraft_a08.py','review_aircraft_a08.py','finalize_aircraft_a08.py']]
    files=sorted(set(p for p in own if p.is_file() and p.name not in ['artifact_manifest.json','publication_verification.json']))
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'scope':'Own A08 configs, scripts, native results, failed gates and reports; integrity only','excluded':['third-party sources PDF HTML CPP render','mutable state registry cadence','self and publication verification']});print({'prepared':True,'files':len(files),'old_files_preserved':n},flush=True)
def register():
    assert not (OUT/'publication_verification.json').exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass']
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+Path(name).name))
    assert all(sha(ROOT/r['path'])==r['sha256'] for r in read(OUT/'artifact_manifest.json')['files']);v=harness();assert v['Status']=='PASS';t=now();state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A07' and cycle['pending_count']==0
    status='completed_engine_native_energy_and_mass_diagnostics_with_spatial_contact_controls_and_retained_failed_gates';record={'experiment_id':'WTC1-AIRCRAFT-A08','registered_at':t,'status':status,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'authoritative_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':s['all_declared_checks_pass'],'physical_impact_qualified':False,'engine_crushing_qualified':False,'failure_transfer_enabled':False,'local_energy_ledger_fully_qualified':s['local_energy_ledger_fully_qualified'],'spatial_convergence_qualified':False,'engine_spatial_sensitivity_tested':True,'energy_cause_identified':False,'whole_aircraft_iteration_count':8,'whole_aircraft_cases':5,'main_solver_jobs':5,'observation_jobs':5,'old_solver_reruns':0,'old_files_preserved':4829,'engine_coarse_shells':960,'engine_fine_shells':3840,'engine_joint_beams':56,'engine_assembly_budget_kg':9000,'A07_CG_review_corrected_without_model_change':True,'native_nodal_mass_reader_verified':True,'engine_geometry_and_materials_identified':False,'comparisons':s['comparisons'],'NIST_outcomes_used_as_target':False,'next_iteration':'AIRCRAFT-A09'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A08',next_iteration='AIRCRAFT-A09',current_status=status,next_objective=NEXT,updated_at=t);state['aircraft_a08_key_results']=record;state['user_steering_2026_10_05']['next']='AIRCRAFT-A09';state['validated_artifacts'].update(aircraft_a08_report=rel(REPORT),aircraft_a08_results=rel(OUT/'authoritative_review.json'),aircraft_a08_handoff=rel(HANDOFF),aircraft_a08_figure=rel(OUT/'summary_aircraft_a08.png'));cycle.update(pending_iterations=['AIRCRAFT-A08'],pending_count=1,next_publication_after='After verified A09, publish A08+A09 together',updated_at=t);dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(True)
def verify(write=False):
    n=preserved();state=read(ROOT/'harness/state.json');before=read(OUT/'before_state.json');protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();manifest=read(OUT/'artifact_manifest.json');cycle=read(ROOT/'harness/publication_cycle.json');sm=read(OUT/'source_manifest.json');sources=sm['local_inputs']+sm['new_primary_sources']
    checks={'new_artifact_hashes':all(sha(ROOT/r['path'])==r['sha256'] for r in manifest['files']),'old_files_preserved':n==4829,'predeclaration_unchanged':sha(CFG)==read(OUT/'declaration_guard.json')['sha256'],'source_inputs_unchanged':all(sha(ROOT/r['path'])==r['sha256'] for r in sources),'append_only_single_record':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A08','state_route':state['current_iteration']=='AIRCRAFT-A08' and state['next_iteration']=='AIRCRAFT-A09','protected_old_evidence':all(before[k]==state[k] for k in protected),'native_integrity_pass':read(OUT/'authoritative_review.json')['integrity_only_pass'],'A07_old_failed_CG_review_preserved_and_corrected':read(OUT/'cached_A07_mass_output_review.json')['all_corrected_CG_gates_pass'] and not read(PREV/'authoritative_review.json')['additional_CG_gate_pass'],'failed_physical_gates_visible':not read(OUT/'authoritative_review.json')['all_declared_checks_pass'],'reports_and_figure_exist':REPORT.exists() and HANDOFF.exists() and (OUT/'summary_aircraft_a08.png').exists(),'one_pending_at_authorized_cadence':cycle['pending_iterations']==['AIRCRAFT-A08'] and cycle['pending_count']==1 and cycle['last_published_iteration']=='AIRCRAFT-A07','harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'files_checked':len(manifest['files']),'old_files_checked':n,'harness':v,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'spatial_convergence_qualified':False,'next_iteration':'AIRCRAFT-A09'};assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['figure','prepare','register','verify']);globals()[p.parse_args().action]()
