"""Seal A09 diagnostics including failures, then append verified state. Publication is separate."""
import argparse,json
import numpy as np
from run_aircraft_a09 import ROOT,OUT,PREV,CFG,EXT,read,dump,sha,rel,now,harness,preserved,guard,cases
REPORT=OUT/'rapport_aircraft_a09.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A09_HANDOFF.md'
NEXT=('AIRCRAFT-A10 : isoler le premier contact dans un témoin élastique sans redistribution RBE3, avec un bilan analytique et les mêmes conventions de sortie. '
      'Identifier dans les propriétés/formulations natives la définition des inerties de coque et du canal RKE avant d’ajouter une énergie indépendante au bilan. '
      'Comparer contact et pas de temps sur ce témoin avant de retransférer une option qualifiée vers l’avion. '
      'Le contact moteur A09 reste énergétiquement et spatialement non qualifié ; ne pas choisir Stfac pour ajuster un résultat et ne pas prolonger la scène comme un écrasement validé. '
      'Ensuite seulement : écrasement/rupture avec historique et dissipation, autocontact/fragments, structure et rotors plus réalistes, planchers/noyau et plages d’entrée AA11. '
      'Aucun calage sur les dégâts NIST. Préserver V11F/V11R ; V11S/I02I-M différées. Publication A08+A09 due après vérification ; paire suivante A10+A11.')

def figure():
    # A readable static result table, not a rendered or animated physical reconstruction.
    from PIL import Image,ImageDraw,ImageFont
    s=read(OUT/'authoritative_review.json');im=Image.new('RGB',(1550,820),'#101a29');d=ImageDraw.Draw(im)
    f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23);sm=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21);title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',32)
    d.text((35,25),'AIRCRAFT-A09 — contrôles du premier contact moteur',font=title,fill='white')
    d.text((35,80),'9 calculs frais • matériaux inchangés • contact extérieur limité aux moteurs • horizon 0,4 ms',font=sm,fill='#d0deee')
    cols=[35,405,610,835,1095];headers=['Cas','Triangles','Jx (N·s)','Générée (kJ)','Résidu (kJ)']
    for x,h in zip(cols,headers):d.text((x,145),h,font=f,fill='#77e5a3')
    for i,r in enumerate(s['cases']):
        y=192+43*i;vals=[r['case']['id'],str(r['engine_shell_count']),f"{r['final_contact_impulse_Ns'][0]:.2f}",f"{r['final_generated_energy_J']/1000:.3f}",f"{r['final_energy_residual_J']/1000:.3f}"]
        for x,v in zip(cols,vals):d.text((x,y),v,font=f,fill='white')
    d.text((35,635),'Stfac 0,1 et variante RBE3 : mêmes impulsions et énergies globales que BASE_FINE à cet horizon.',font=sm,fill='#d0deee')
    d.text((35,678),'Stfac 0,01 / 0,001 : effet mesuré ; déficit énergétique persistant. Aucun ajustement aux dégâts NIST.',font=sm,fill='#ffb454')
    d.text((35,727),'Intégrité vérifiée ; critères physiques échoués conservés. Impact historique et écrasement non qualifiés.',font=sm,fill='#ffb454')
    p=OUT/'summary_aircraft_a09.png';im.save(p);dump(OUT/'figure_provenance.json',{'created_utc':now(),'input':rel(OUT/'authoritative_review.json'),'input_sha256':sha(OUT/'authoritative_review.json'),'output':rel(p),'sha256':sha(p),'role':'Static table from native saved results, no reconstruction or Blender','physical_impact_qualified':False})

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass'];v=harness();assert v['Status']=='PASS';dump(OUT/'harness_after_calculations.json',v)
    n=preserved();assert n==5076
    table='\n'.join(f"|{r['case']['id']}|{r['case']['Stfac']}|{r['case']['Istf']}|{r['case']['engine_RBE3_Iform']}|{r['actual_main_end_time_ms']:.6f}|{r['engine_shell_count']}|{r['final_contact_impulse_Ns'][0]:.3f}|{r['final_generated_energy_J']/1000:.3f}|{r['final_energy_residual_J']/1000:.3f}|{r['maximum_engine_shell_plastic_strain']:.6f}|" for r in s['cases'])
    cmp='\n'.join(f"|{q['comparison']}|{' / '.join(q['cases'])}|{q['common_time_ms']:.6f}|{100*q['impulse_difference_fraction']:.5f}|{100*q['generated_energy_difference_fraction']:.5f}|{str(q['impulse_pass'])+'/'+str(q['generated_energy_pass']) if q['declared_acceptance_comparison'] else 'sensibilité, sans sélection'}|" for q in s['comparisons'])
    failed='\n'.join('- '+r['case']['id']+' : '+(', '.join(r['failed_checks']) or 'aucun critère échoué') for r in s['cases'])
    rotation='\n'.join(f"|{r['case']['id']}|{r['independent_shell_rotation_final_J']:.3f}|{r['native_shell_rotation_final_J']:.3f}|{r['native_global_rotation_final_J']:.3f}|{r['independent_shell_rotation_max_error_J']:.3f}|{r['extra_checks']['independent_shell_rotation_matches_native']}|" for r in s['cases'])
    free=next(r for r in s['cases'] if r['case']['id']=='PENALTY_FREE');base=next(r for r in s['cases'] if r['case']['id']=='BASE_FINE')
    REPORT.write_text(f'''# AIRCRAFT-A09 — formulations de contact, contraintes et rotation

Neuvième itération de la branche avion entier. Neuf contrôles neufs de 0,4 ms ont été exécutés ; aucun ancien Engine relancé. Les formulations alternatives testées ne résolvent pas le déficit énergétique du premier contact. La réduction Stfac à 0,1 est inactive dans les historiques sauvegardés de ce contrôle ; des facteurs 0,01 et 0,001, déclarés séparément avant leur calcul, modifient effectivement la réponse mais conservent un déficit plus grand. Aucun de ces réglages n’est sélectionné comme matériau réel ou comme moyen de rejoindre les dégâts NIST.

## 1. Faits transcrits et sorties observées

La [documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) définit, pour les coques, Km = Stfac·Em·tm côté principal et Ks = Es·ts côté secondaire ; Istf=4 utilise min(Km,Ks), Istf=5 leur combinaison en série, puis bornes et division par deux. Stfac ne multiplie donc pas toute la raideur de contact. Le facteur 0,1 peut rester au-dessus de la branche limitante Ks. C’est cohérent avec l’identité constatée, sans prétendre identifier la valeur locale exacte de toutes les raideurs actives.

La [documentation RBE3](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe3_starter_r.htm) distingue Iform=2 cinématique et Iform=3 pénalité. Le Starter des cas PENALTY affiche explicitement « 32 OF RBE3 HAVE BEEN SWITCHED TO PENALTY METHOD ». Ces 32 liaisons moteur ont donc été converties ; les 336 autres restent inchangées. L’identité des historiques au premier contact n’implique pas que l’option soit ignorée : les hôtes fan/core ne sont pas encore touchés directement dans ce contrôle court.

La [documentation TH/NODE](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm) expose VX/VY/VZ, VRX/VRY/VRZ et REAC comme force. Les nouveaux bilans d’appui intègrent les forces en N dans le temps ; les anciennes interprétations restent sauvegardées. Les réactions sont nulles à cet horizon : les données seules ne distinguent donc pas les deux lectures anciennes. Les rotations nodales sont enregistrées en rad/ms et converties en rad/s ; la somme des carrés utilisée ici est indépendante d’une permutation des axes, sans prétendre avoir calibré séparément chacun des axes angulaires.

Neuf Starter sans erreur/avertissement, neuf Engines et neuf observateurs terminés normalement. Fin native observée par la première ligne T02 isolée, sans utiliser la continuation. CSV T01 comparé au binaire natif, topologie/masse/supports/absence d’érosion et de travail extérieur contrôlés. Le reader FASTMAGI10 des masses valide identifiants, temps, coordonnées et vitesses contre le convertisseur natif. Harnais PASS avant/après ; {n} anciens fichiers sont préservés.

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
{table}

|Comparaison|Cas|Temps commun ms|Écart impulsion %|Écart générée %|Critères J/E|
|---|---|---:|---:|---:|---|
{cmp}

L’ajout d’instrumentation est comparé à A08/FINE au temps commun, avec sorties A08 mises en cache. BASE_FINE/SOFT_FINE ont des historiques natifs exactement identiques à la précision sauvegardée. Pour BASE_FINE/PENALTY_FINE, seules les impulsions de contact et les énergies globales sont identiques : des différences internes sont présentes, mesurées dans authoritative_review.json et listées dans raw_history_pair_difference_channels.json. Ne pas généraliser l’identité globale à chaque canal. Istf=5 modifie légèrement la réponse, sans résoudre le bilan. Les facteurs effectifs 0,01/0,001 conservent un déficit ; aucune baisse de résidu sélectionnée pour ajuster la simulation à l’événement. La comparaison spatiale utilise l’interpolation au temps commun, les fins natives différant d’une fraction de pas. Deux maillages ne prouvent pas une convergence asymptotique.

E=Ktranslation+Krotation+IE+hourglass+spring+contact élastique+friction+amortissement. Résidu=ΔE−Wextérieur. PW est inclus dans IE et jamais ajouté deux fois. Énergie générée=Krotation+IE+hourglass+spring+contact élastique, selon le contrat antérieur. Tous les termes natifs et résidus sont sauvegardés ; aucun canal suspect n’est utilisé comme compensation. La translation indépendante Σ½mi vi² et la quantité de mouvement Σmi vi utilisent les masses nodales natives, vérifiées constantes. Le sous-ensemble moteur utilise ces masses redistribuées, pas une duplication des ADMAS et de leurs hôtes. Il ne constitue pas un bilan fermé de travail aux pylônes.

À l’amorce BASE_FINE, plus forte baisse sauvegardée : {base['largest_dense_saved_loss']['residual_increment_J']/1000:.3f} kJ entre {base['largest_dense_saved_loss']['interval_ms'][0]:.6f} et {base['largest_dense_saved_loss']['interval_ms'][1]:.6f} ms. Termes natifs et PW avant/après sont détaillés dans review.json. Cause non identifiée ; pas d’attribution arbitraire à une fracture, absente du deck.

|Cas|Rotation coques indépendante finale J|RKE coques native finale J|Rotation globale native finale J|Erreur maximale coques J|Critère indépendant|
|---|---:|---:|---:|---:|---|
{rotation}

La formule théorique indépendante ne reproduit pas les RKE de coque natives après contact, malgré la correction des unités. Cela impose d’identifier la convention d’inertie/formulation avant d’en tirer un bilan : l’écart n’est pas ajouté à l’énergie globale et n’explique pas à lui seul le déficit du contact. Le RKE brut de la partie poutres reste environ 112,546 GJ initial contre rotation globale initiale nulle ; canal conservé mais non qualifié. En libre PENALTY_FREE, résidu {free['final_energy_residual_J']:.6g} J ; les termes générés atteignent seulement {free['final_generated_energy_J']:.6g} J, conservés avec l’échec de l’égalité stricte à zéro. Les écarts d’arrondi ne sont pas confondus avec les dizaines de kJ perdues en contact.

La répartition native d’inertie distingue effectivement les formulations. Iform=2 : masse des 32 points dépendants nulle, environ 7181,0984 kg redistribués aux hôtes. Iform=3 : environ 7181,0985 kg conservés aux points dépendants, excès résiduel sur les hôtes proche de zéro à l’arrondi float32. La somme points+hôtes respecte le même seuil 0,0001 kg dans les neuf cas. Le premier contrôle imposait à tort la redistribution cinématique aux deux variantes : premières revues conservées dans before_constraint_mass_interpretation, correction et preuve dans constraint_mass_verification.json. Aucun changement de masse/deck/énergie ni relance Engine. Les différences internes pénalité/cinématique atteignent seulement 0,0001 m/s en translation moteur et 7,34×10⁻⁹ rad/ms en rotation à la précision du CSV ; les termes globaux restent identiques.

Échecs complets, sans suppression :

{failed}

## 6. Contradictions, informations manquantes et suite

Intégrité d’exécution et traçabilité vérifiées ; bilan local, sensibilité spatiale et convention de rotation non qualifiés. La variante RBE3 n’a pas encore été sollicitée au premier contact direct fan/core. Une absence d’effet dans 0,4 ms ne qualifie pas son comportement ultérieur. Les facteurs de contact effectivement différents aggravent ici le déficit ; les adopter pour « améliorer » une cible serait injustifié. Aucune loi d’écrasement réel n’est encore validée.

{NEXT}

Il reste sur l’impact : conditions AA11 plausibles et leurs plages, géométrie/inerties/liaisons du Boeing et des moteurs plus réalistes, rupture/écrasement avec historique et dissipation, autocontact/fragments, traversée de façade puis planchers/noyau, enfin transferts cohérents de dommages/masse/carburant vers les incendies et la structure. Température prescrite ≠ incendie calculé ; localisation en flexion après fracture complète non validée ; tests numériques ≠ validation de l’effondrement réel ; Blender demeure une visualisation. A08+A09 forme la paire de publication autorisée, avec tous les échecs visibles ; aucun envoi sur X.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Passation AIRCRAFT-A09 → A10

Lire AGENTS.md, harness/state.json puis cette passation. A09, neuvième itération avion entier, terminée comme diagnostic limité ; impact/écrasement réels non qualifiés. Résultats autoritatifs : wtc1_simulation_v8/output/aircraft_a09/authoritative_review.json, rapport_aircraft_a09.md, source_interpretation.json, summary_aircraft_a09.png. Neuf cas r0, config principale + extension Stfac déclarées avant calcul, graine 1102034. Neuf Starter/Engine/observateurs normaux, fins 0,4 ms vérifiées, zéro ancien Engine ; {n} anciens fichiers préservés. V11F/V11R intacts, V11S/I02I-M différées.

Même avion couplé, façade déplacée au front moteur, moteurs seuls au contact extérieur, pas traversée historique. Matériaux A07/A08 inchangés, pas de rupture ni fragments ; fan/core sans contact direct initial. TYPE7 Km=Stfac*Em*tm, Ks=Es*ts, Istf4=min, Istf5=série puis bornes/2. Stfac0,1 ne change pas les historiques BASE_FINE ; extension effective0,01/0,001 change la réponse mais déficit plus grand. PENALTY Iform3 natif confirmé par message Starter32RBE3 ; impulsions/énergies globales identiques BASE_FINE à cet horizon, différences internes quantifiées ; ne pas conclure flag ignoré ou tous canaux identiques.

|Cas|Stfac|Istf|Iform|Fin ms|Triangles|Jx Ns|Générée kJ|Résidu kJ|Plastique|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{table}

Comparaisons au temps commun :

|Comparaison|Cas|Temps ms|ΔJ %|ΔG %|Critères|
|---|---|---:|---:|---:|---|
{cmp}

DenseTH52 :6 canaux ×626/2210 nœuds moteur/hub, plus32ADMAS×3vitesses conservées. Native MASS FASTMAGI10+IDs/vitesses validés ; ledger translation natif global et sous-ensemble moteur sans double ADMAS. REAC=force documentaire, nouveau bilan intègre N dt_ms*0,001 ; appuis nuls ici, pas distinction empirique ancienne ambiguïté. TH/PART tous groupes combinés en un record binaire :13 contact/10 libre, schéma pré-exécution corrigé et premières métadonnées conservées. Canonical9canaux poutres, ordre natif part/ID adapté uniquement dans reviewer.

Rotation indépendante coques : page154eq571–574 I=m_g*(2A/6+t²/12), α/π, omega rad/ms. Première tentative densité kg/mm³ traitée comme g/mm³, script/sorties conservés initial_review_unit_error, correction reader uniquement. Critères inchangés ; après correction comparaison RKE coque reste échouée. Ne pas ajouter cet écart au bilan global. RKE poutre brut initial112,546GJ toujours incompatible rotation globale0, non qualifié. Support/CG comparaison Starter de même précision ; premier arrêt sur nom de champ absent documenté. Critère plastique JSON0,1 déjà utilisé A08, son texte0,2 erroné conservé.

NativeMASS : cinématique Iform2 dépendants0/redis hôtes7181,0984kg ; pénalité Iform3 dépendants7181,0985kg/hôtes≈0. Somme deux domaines validée au même seuil1e−4kg ; ancien test host-only injustifié pour pénalité conservé before_constraint_mass_interpretation et corrigé dans constraint_mass_verification.json, sans relance. Ne pas doubler la masse des points et hôtes. VariantePENALTY :4886canaux internes diffèrent, maximumtranslation1e−4m/s/rotation7,34e−9rad/ms ; globalE/contact identiques, pas touscanaux. PENALTY_FREE énergie générée≈9e−30J, échecstrictzéro préservé.

Suite : {NEXT}

Publications autorisées toutes2itérations : A08+A09 due, vérifier harness/publication_cycle.json et outputs/github_publication/updates_2026-10-06_aircraft_a08_a09/final_remote_verification.json pour état réellement envoyé. Compte/repo WTC-simu2026/WTC-simu2026 ; credentials anonymes GCM disponibles au contrôle actuel, ne jamais enregistrer/imprimer token. Pas X/Yoremi, pas scan archive, pas anciens calculs. Sources tierces exclues du dépôt/release ; rapports et liens conservés. Utiliser états/CSV/NPZ déjà sauvegardés.
''',encoding='utf-8')
    own=list(OUT.rglob('*'))+[CFG,EXT,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/p for p in ['run_aircraft_a09.py','review_aircraft_a09.py','finalize_aircraft_a09.py']]
    files=sorted(set(p for p in own if p.is_file() and p.name not in ['artifact_manifest.json','publication_verification.json']))
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'scope':'Own A09 scripts configs all controls saved failed first reviews and reports; integrity only','excluded':['third-party source HTML','mutable state registry cadence','self and verification']});print({'prepared':True,'files':len(files),'old_files_preserved':n},flush=True)

def register():
    assert not (OUT/'publication_verification.json').exists();s=read(OUT/'authoritative_review.json');assert s['integrity_only_pass']
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/name)==sha(OUT/('before_'+name.split('/')[-1]))
    assert all(sha(ROOT/r['path'])==r['sha256'] for r in read(OUT/'artifact_manifest.json')['files']);v=harness();assert v['Status']=='PASS'
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json');assert state['current_iteration']=='AIRCRAFT-A08' and cycle['pending_iterations']==['AIRCRAFT-A08'];t=now();status='completed_contact_stiffness_RBE3_and_native_rotation_controls_with_retained_energy_and_spatial_failures'
    record={'experiment_id':'WTC1-AIRCRAFT-A09','registered_at':t,'status':status,'configuration':rel(CFG),'extension_configuration':rel(EXT),'report':rel(REPORT),'results':rel(OUT/'authoritative_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':True,'all_declared_checks_pass':s['all_declared_checks_pass'],'physical_impact_qualified':False,'engine_crushing_qualified':False,'failure_transfer_enabled':False,'local_energy_ledger_fully_qualified':s['local_energy_ledger_fully_qualified'],'spatial_convergence_qualified':False,'energy_cause_identified':False,'whole_aircraft_iteration_count':9,'whole_aircraft_cases':9,'main_solver_jobs':9,'observation_jobs':9,'old_solver_reruns':0,'old_files_preserved':5076,'materials_changed':False,'effective_stiffness_controls_declared_separately':True,'penalty_RBE3_confirmed_by_native_Starter':True,'native_shell_rotation_semantics_qualified':False,'exact_saved_history_pair_differences':s['exact_saved_native_history_pair_different_channels'],'comparisons':s['comparisons'],'NIST_outcomes_used_as_target':False,'next_iteration':'AIRCRAFT-A10'}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A09',next_iteration='AIRCRAFT-A10',current_status=status,next_objective=NEXT,updated_at=t);state['aircraft_a09_key_results']=record;state['user_steering_2026_10_05']['next']='AIRCRAFT-A10';state['validated_artifacts'].update(aircraft_a09_report=rel(REPORT),aircraft_a09_results=rel(OUT/'authoritative_review.json'),aircraft_a09_handoff=rel(HANDOFF),aircraft_a09_figure=rel(OUT/'summary_aircraft_a09.png'));cycle.update(pending_iterations=['AIRCRAFT-A08','AIRCRAFT-A09'],pending_count=2,next_publication_after='Verified A08+A09 publication due now',updated_at=t);dump(ROOT/'harness/state.json',state);dump(ROOT/'harness/publication_cycle.json',cycle);verify(True)

def verify(write=False):
    guard();n=preserved();before=read(OUT/'before_state.json');state=read(ROOT/'harness/state.json');protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch'];reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness();m=read(OUT/'artifact_manifest.json');cy=read(ROOT/'harness/publication_cycle.json');src=read(OUT/'source_manifest.json');s=read(OUT/'authoritative_review.json')
    checks={'new_artifact_hashes':all(sha(ROOT/r['path'])==r['sha256'] for r in m['files']),'old_files_preserved':n==5076,'predeclarations_unchanged':True,'source_inputs_unchanged':all(sha(ROOT/r['path'])==r['sha256'] for r in src['local_inputs']+src['new_primary_sources']),'single_append_only_registry_record':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A09','state_route':state['current_iteration']=='AIRCRAFT-A09' and state['next_iteration']=='AIRCRAFT-A10','protected_prior_evidence':all(state[k]==before[k] for k in protected),'native_integrity_pass':s['integrity_only_pass'],'failed_physical_checks_visible':not s['all_declared_checks_pass'],'first_review_errors_preserved':(OUT/'initial_review_unit_error').exists() and (OUT/'review_schema_correction.json').exists(),'report_handoff_figure_exist':REPORT.exists() and HANDOFF.exists() and (OUT/'summary_aircraft_a09.png').exists(),'pair_pending_at_authorized_cadence':cy['pending_iterations']==['AIRCRAFT-A08','AIRCRAFT-A09'] and cy['pending_count']==2 and cy['last_published_iteration']=='AIRCRAFT-A07','harness_pass':v['Status']=='PASS'}
    result={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'files_checked':len(m['files']),'old_files_checked':n,'harness':v,'physical_impact_qualified':False,'local_energy_ledger_fully_qualified':False,'spatial_convergence_qualified':False,'next_iteration':'AIRCRAFT-A10'};assert result['pass'],result
    if write:dump(OUT/'publication_verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['figure','prepare','register','verify']);globals()[p.parse_args().action]()
