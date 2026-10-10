"""Seal the executed impact and the incomplete fine attempt, then register once."""
import argparse,json,re,subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from run_aircraft_a15 import ROOT,OUT,CFG,read,dump,rel,now,guard,harness,streamsha

REPORT=OUT/'rapport_aircraft_a15.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A15_HANDOFF.md'
NEXT="AIRCRAFT-A16 : partir de l'impact couplé A15 et de ses sorties enregistrées. Priorité à une loi mécanique de dommage/rupture du radôme, puis de l'avant métallique et de la façade, avec propriétés et plages indépendantes des dommages historiques. Le premier état échantillonné du radôme hors résistance de référence est vers1ms ; allonger seulement le modèle sans rupture produit des formes hors domaine. Déclarer les paramètres et dissipation, signaler les données manquantes plutôt que les inventer, vérifier une seule famille de contrôles mécaniques nécessaires puis revenir au contact avion/façade avec une durée et un coût réalistes. Réutiliser les sorties A15 ; ne pas relancer les anciens solveurs. Le demi-pas n'est comparé que jusqu'à6,240026ms, pas jusqu'à10ms ; prévoir un plafond de coût cohérent si sa fin est nécessaire. Convergence spatiale, géométrie/masse/conditions historiques, auto-contact global, carburant et assemblages restent à qualifier. Garder les échecs A11-A14 et les limites A15 ; aucun réglage pour retrouver NIST, une perforation ou une trajectoire connue. Le module parallèle n'est pas intégré. Premières secondes et chaîne d'effondrement non calculées. Publication A14+A15 due selon la cadence enregistrée, à préparer et vérifier séparément."

def checkrows(rows):
    for r in rows:
        p=ROOT/r['path'];assert p.stat().st_size==r['bytes'] and streamsha(p)==r['sha256'],r['path']
    return len(rows)

def prepare():
    guard();assert not REPORT.exists() and not HANDOFF.exists() and not (OUT/'artifact_manifest.json').exists()
    s=read(OUT/'campaign_review.json');assert s['available_output_integrity_pass'] and len(s['cases'])==1 and len(s['partial_cases'])==1
    r=s['cases'][0];partial=s['partial_cases'][0];cmp=s['comparison'];p=read(OUT/'preservation_verification.json');assert p['pass'] and p['files']==8795
    v=harness();assert v['Status']=='PASS';dump(OUT/'harness_after_calculations.json',v)
    ET.parse(OUT/'visualisation/bilans_impact.svg');vis=read(OUT/'visualisation/provenance.json');assert vis['data_schema_pass'] and vis['native_displacement_scale']==1 and vis['gzip_roundtrip_exact']
    node=Path('C:/Users/jeuxpc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    js=subprocess.run([str(node),'--check',str(OUT/'visualisation/viewer_script_for_validation.js')],capture_output=True,text=True);assert js.returncode==0
    dump(OUT/'visualisation/syntax_verification.json',{'created_utc':now(),'pass':True,'static_PNGs_visually_inspected':['bilans_impact.png','impact_natif_10ms.png'],'interactive_GUI_render_verified':False})
    jobs=[]
    for c in read(CFG)['execution']['cases']:
        d=OUT/'r0'/c['id'];log=(d/'starter.log').read_text(errors='replace')
        assert int(re.findall(r'(\d+) WARNING\(S\)',log)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',log)[-1])==0
        for logfile in ['starter.log','engine.log','observer/observer.log','converter.log','partial_converter.log']:
            fn=d/(logfile+'.execution.json')
            if fn.exists():jobs.append({'case':c['id'],'job':logfile,**read(fn)})
    assert len([j for j in jobs if j['job']=='engine.log'])==2
    assert sum(j['exit_code']=='TIMEOUT' for j in jobs)==1
    assert all(j['exit_code']==0 or (j['case']=='IMPACT_10_DT25' and j['job']=='engine.log' and j['exit_code']=='TIMEOUT') for j in jobs)
    execution={'created_utc':now(),'main_engine_jobs':2,'completed_main_engine_jobs':1,'capped_main_engine_jobs':1,'observer_jobs':1,'starter_jobs':2,'converter_jobs':2,'old_solver_reruns':0,'total_process_seconds':sum(j['seconds'] for j in jobs),'GPU':False,'CPU_threads':2,'runtime':'v20260728-win64','jobs':jobs}
    dump(OUT/'execution_summary.json',execution)
    first=next(z for z in r['state_diagnostics'] if z['radome_face_reference_strength_ratio']>1)
    a={'created_utc':now(),'whole_aircraft_exploratory_impact_executed':True,'completed_whole_scene_end_ms':r['end_ms'],'fine_case_incomplete_cost_cap':True,'fine_available_history_end_ms':partial['last_available_main_history_ms'],'half_dt_comparison_only_partial_window':True,'half_dt_impulse_difference_fraction':cmp['impulse_difference_fraction'],'half_dt_generated_energy_difference_fraction':cmp['generated_energy_difference_fraction'],'half_dt_comparison_pass_common_window':cmp['impulse_pass'] and cmp['generated_energy_pass'],'global_energy_pass_completed_case':r['checks']['global_energy'],'local_energy_pass_completed_case':r['checks']['local_energy'],'support_contact_momentum_pass_completed_case':r['checks']['global_support_momentum'] and r['checks']['contact_facade_momentum'],'material_domain_pass':False,'first_sampled_radome_reference_exceedance_ms':first['time_ms'],'maximum_facade_displacement_mm':r['maximum_facade_displacement_mm'],'last_main_contact_impulse_Ns':r['last_main_contact_impulse_Ns'],'spatial_convergence_qualified':False,'fracture_crushing_delamination_modelled':False,'physical_impact_qualified':False,'historical_impact_qualified':False,'seconds_impact_calculated':False,'parallel_module_integrated':False,'old_failed_A11_A14_gates_retained':True,'NIST_outcomes_used_as_target':False,'no_stiffness_material_or_damage_fitted_to_result':True,'user_directed_change_of_work_route':True}
    dump(OUT/'scientific_assessment.json',a)
    table=f"| IMPACT_10_DT50 | {r['end_ms']:.9f}, fin observée | {r['last_main_contact_impulse_Ns'][0]:.3f} | {r['final_generated_energy_J']/1e6:.6f} | {r['final_energy_residual_J']/1000:.6f} | {'; '.join(r['failed_checks'])} |\n| IMPACT_10_DT25 | {partial['last_available_main_history_ms']:.6f}, dernier historique seulement | {partial['last_main_contact_impulse_Ns'][0]:.3f} | {partial['last_generated_energy_J']/1e6:.6f} | {partial['last_energy_residual_J']/1000:.6f} | plafond600s ; fin10ms non atteinte |"
    REPORT.write_text(f'''# AIRCRAFT-A15 — lancement de l'avion complet contre la façade

**Le prototype complet a réellement été lancé dans OpenRadioss contre une façade déformable, sans trajectoire imposée.** Un essai atteint **{r['end_ms']:.9f} ms ≈0,01s**, contre0,4ms dans A11. L'essai au demi-pas est arrêté au plafond de coût déclaré600s ; ses données disponibles vont jusqu'à **{partial['last_available_main_history_ms']:.6f} ms**. Cet essai incomplet reste incomplet. Aucun ancien solveur relancé, aucune cible de dommages NIST utilisée.

Le déplacement maximal de façade dans les états échantillonnés atteint **{r['maximum_facade_displacement_mm']:.3f} mm**. L'impulsion X principale vaut **{r['last_main_contact_impulse_Ns'][0]/1000:.6f} kN·s** au dernier historique9,990103ms. Le nez transmet l'effort ; nacelles, fan et core n'ont pas encore de contact. Les bilans déclarés du cas achevé passent, mais **les limites matérielles échouent**. Cette avance est une expérience exploratoire, pas une reconstruction qualifiée de l'impact historique.

## 1. Faits directement observés ou transcrits

Deux Starter sans erreur ni avertissement. IMPACT_10_DT50 termine normalement ; l'observateur lit son état final sans modifier les sorties principales. IMPACT_10_DT25 porte explicitement TIMEOUT dans le journal et un fichier retained_failure conservé ; pas d'observateur, pas de fin réelle certifiée. Sa dernière image stockée est à{partial['last_available_animation_ms']:.9f}ms ; son dernier historique n'est pas un timestamp de fin.

Les1000 lignes principales du cas achevé et les625 lignes disponibles du cas incomplet sont vérifiées, tous canaux, contre les records binaires natifs. Le premier record de l'observateur confirme la fin et les énergies. Contact FNX/FNY/FNZ et REAC des appuis sont des **impulsions cumulatives**, converties N·ms→0,001N·s, sans réintégration. Les REAC et contacts de l'observateur sont exclus de tous les bilans de transfert car leurs cumuls repartent à zéro.

Lecture des temps corrigée et tracée : le convertisseur VTK affiche six chiffres significatifs ;10,000361ms est affiché10,0004ms. Le premier audit rejetait cette image avec une tolérance absolue trop fine. Le script antérieur et son journal d'échec sont conservés. Le lecteur utilise maintenant le temps float32 du fichier natif FASTMAGI10, vérifie l'accord avec la précision affichée du convertisseur, puis les coordonnées, IDs et vitesses. Aucun solveur ni seuil physique relancé ou modifié pour cette correction.

Ce sont des observations sur des fichiers numériques, aucune nouvelle observation historique.

## 2. Résultats d'un modèle officiel

Aucun résultat officiel de dommages, de pénétration, de trajectoire ou d'effondrement n'est utilisé comme cible. Les sorties nouvelles sont celles d'OpenRadioss v20260728-win64, empreintes et arguments enregistrés dans execution_summary.json. La façade représentative hérite d'entrées nominales NIST des branches précédentes ; sa géométrie et ses sections ne constituent donc pas un modèle historique entièrement indépendant. Cette dépendance d'entrée est distincte d'un ajustement aux résultats NIST.

La documentation primaire TYPE25 déjà copiée et épinglée dans A14 décrit le contact nœuds/surface. Les références Boeing/CF6 et sandwich sont celles du manifeste A11, avec leurs réserves d'attribution et leurs conversions originales. Aucune propriété nouvelle n'est attribuée à l'avion réel dans A15.

## 3. Affirmations provenant des archives locales

Aucune vidéo, photographie ou PDF source nouvellement inspecté ou modifié. **{p['files']} fichiers antérieurs**, **{p['bytes_hashed']/1e9:.3f} Go**, recontrôlés intégralement par SHA-256 sans différence. Les archives et work/official_sources restent en lecture seule. V11F/V11R, les rapports A11-A14 et leurs critères échoués restent intacts.

Le module Boeing parallèle v2 n'est pas intégré : ses défauts d'inertie/dynamique libre restent ouverts. Le prototype principal déjà exécutable est celui utilisé ici. La dernière publication distante vérifiée reste A12+A13 ; A14+A15 devient la paire locale à publier selon la cadence, aucune publication externe réalisée par ce script.

## 4. Hypothèses propres au modèle

Configuration aircraft_a15_predeclaration.json épinglée avant calcul, graine1102040, zéro tirage. Deux départs neufs de l'avion intact ; aucun dommage réinjecté ni continuation cachée. La demande directe de Jeremy de lancer l'avion change le programme A15 auparavant limité à des témoins locaux : l'exécution exploratoire est autorisée, **la qualification A14 et ses échecs ne sont pas réécrits**.

Géométrie, matériaux, masse, RBE3, assemblages, conditions aux limites et vitesse hérités exactement de A11/NOSE_04_DT05 ; cartes NODE/MAT/PROP/SHELL/SH3N/BEAM/ADMAS/RBE3/BCS/INIVEL comparées à l'identique.37228 nœuds, dont5436 d'avion et31792 de façade ;10378 triangles d'avion,4464 poutres,31986 quadrilatères de façade. Façade de trois étages représentatifs, environ59,3m×10,97m, **944 nœuds de bord fixes et intérieur déformable**. Masse native avion **{r['native_aircraft_mass_kg']:.6f} kg**, ensemble **{r['total_mass_kg']:.6f} kg**. Il s'agit de la masse du prototype ; les conditions historiques AA11 ne sont pas établies.

Vitesse initiale[-200,5,2]m/s, façade initiale X=−50mm, nez X=0, gap5mm. Quatre contacts extérieurs passent de TYPE7 à TYPE25 canonique : surfaces[0,1003], groupes secondaires1100/1101/1102/1103 conservés, mode3, Stfac1 et Istf4, pas de pondération par aire. L'auto-contact TYPE7 du radôme est conservé ; auto-contact global de l'avion absent. La pénalité est une option numérique non qualifiée spatialement, pas une raideur physique identifiée.

Radôme sandwich0,5/8/0,5mm, LAW25+TYPE51/TYPE19 élastique avec plafonds de rupture numériques très élevés : ni rupture, ni écrasement d'âme, ni délamination. Matériaux métalliques plastiques hérités, sans rupture ni érosion ; assemblages idéaux et paramètres approximatifs. Le carburant n'est pas résolu ; pas de feu ni d'intérieur de tour. Aucune masse ajoutée ou nouvelle mise à l'échelle de masse, aucun pilotage de pénétration.

Deux facteurs de pas stable0,5/0,25, durée demandée10ms chacun, deux threads CPU, zéro GPU, plafond600s par principal. Le premier prend{next(j['seconds'] for j in jobs if j['case']=='IMPACT_10_DT50' and j['job']=='engine.log'):.2f}s ; le demi-pas dépasse ce plafond. Ce plafond est un choix de coût, pas une instabilité ni une réussite scientifique. TH tous0,01ms ; animations natives tous0,1ms ;96 sondes nodales déclarées, toutes les masses/vitesses/positions conservées dans les animations. Vérification détaillée du cas achevé sur **{r['native_animation_states']} états régulièrement échantillonnés tous≈0,5ms**, premier et dernier inclus ; toutes les images brutes restent conservées. Les maxima matériels et de déplacements rapportés sont des maxima **échantillonnés**, pas une certification de chaque image.

Unités d'origine g/mm/ms/MPa/N/N·mm ; g→0,001kg, mm→0,001m, ms→0,001s, N·mm→0,001J et N·ms→0,001N·s. mm/ms=m/s. Ledger : KE+rotation globale+IE+hourglass+spring+contact élastique/frottement/amortissement−travail externe, chaque terme une fois. Travail plastique inclus dans IE ; aucun RKE reconstruit ou par pièce ajouté.

Seuils A11 conservés : masse relative10⁻⁶ ; résidu global≤0,5% KE initiale ; local≤5% énergie hors translation+1000J au-dessus1000J ; quantité de mouvement≤10N·s+2% max impulsion ; comparaison demi-pas≤5% d'impulsion et10% d'énergie hors translation ; déformation plastique de diagnostic≤0,1 ; ratio de résistance des peaux du radôme≤1. Ces résistances sont des références sandwich, pas des résistances AA11 identifiées. L'avion entier n'est pas qualifié par les témoins plans A14.

## 5. Résultats dérivés

| Cas | Temps ms / rôle | Impulsion X N·s | Énergie hors translation MJ | Résidu kJ | Échecs conservés |
|---|---|---:|---:|---:|---|
{table}

Le cas complet démarre le contact AIRFRAME vers **{r['contact_onsets_ms']['AIRFRAME']:.7f} ms**, résolution de l'historique0,01ms. Les trois autres impulsions sont nulles. KE initiale **{r['initial_KE_J']/1e9:.6f} GJ** ; travail plastique final **{r['final_plastic_work_J']/1e6:.6f} MJ**. Résidu énergétique maximal **{r['maximum_energy_residual_J']/1000:.6f} kJ**, soit **{100*r['maximum_energy_residual_J']/r['initial_KE_J']:.6f}%** de KE initiale. Écarts maximaux de quantité de mouvement globale/appuis **{r['momentum_global_support_error_Ns']:.6f} N·s**, façade/contact **{r['momentum_facade_contact_error_Ns']:.6f} N·s**, sous les seuils déclarés. Masses nodales décodées indépendamment, constantes dans les états contrôlés ; appuis fixes, masse ajoutée nulle, érosion absente et travail externe nul.

Le maximum de ratio local résidu/énergie est61,398453% au tout début : à0,3002859ms, G=1239,169J et R=−760,831J. Le critère déclaré autorise1061,958J à cet instant avec sa marge1000J. Le contrôle local passe **avec cette marge** ; cela ne signifie pas une erreur relative inférieure à5% à chaque instant. Le budget natif n'est pas corrigé a posteriori.

À **{cmp['common_time_ms']:.6f} ms**, la comparaison donne Δimpulsion **{100*cmp['impulse_difference_fraction']:.7f}%**, Δénergie hors translation **{100*cmp['generated_energy_difference_fraction']:.7f}%**. Les deux critères passent sur cette **fenêtre commune seulement**. Aucune convergence temporelle jusqu'à10ms n'est revendiquée ; aucune convergence spatiale nouvelle calculée.

Déplacement de façade complet échantillonné **{r['maximum_facade_displacement_mm']:.3f}mm** ; dernier état du cas incomplet **{partial['last_sample_facade_displacement_mm']:.3f}mm à{partial['last_available_animation_ms']:.6f}ms**. Déformations plastiques maximales des coques **{r['maximum_shell_plastic_strain']:.6f}**, des poutres sondées **{r['maximum_beam_plastic_strain']:.6f}**, au-delà du seuil0,1. Le premier état échantillonné dépassant la résistance de référence du radôme est à **{first['time_ms']:.6f}ms**, ratio **{first['radome_face_reference_strength_ratio']:.6f}** ; le précédent, vers0,500321ms, est sous le seuil. Ratio maximal **{r['maximum_radome_face_strength_ratio']:.6f}**. Ce diagnostic ne constitue ni une mesure du matériau réel, ni un instant de rupture ; la loi du modèle maintient ces peaux intactes.

Visualisation HTML : **21 états natifs ×1**, aucune interpolation géométrique ni trajectoire Blender, lecture artificiellement ralentie. Données comprimées avec retour exact, syntaxe JavaScript vérifiée. PNG des bilans et de la géométrie inspectés visuellement ; rendu interactif non certifié. Vue10ms hors domaine matériel destinée au diagnostic. Précision des coordonnées imprimées : écart maximal{r['native_geometry_rounding_error_mm']:.6f}mm, consigné plutôt que corrigé.

## 6. Contradictions et informations manquantes

L'avion complet a bien évolué sous contact avec la façade, mais à10ms seuls le nez et l'avant interagissent ; ce n'est ni une traversée complète, ni les premières secondes. Des bilans numériques et une comparaison temporelle courte réussis coexistent avec des matériaux hors domaine et une absence de rupture. Une ressemblance visuelle ne prouve aucun mécanisme historique.

Les résistances/énergies de rupture du sandwich réel, écrasement de l'âme, séparation des assemblages, fragmentation, auto-contact global, carburant, géométrie/sections de façade et conditions réelles d'impact restent à documenter et qualifier. Le demi-pas demandé10ms demeure incomplet, même si ses données disponibles sont cohérentes. Les anciennes qualifications A11-A14 restent échouées et distinctes de ces nouveaux résultats. Aucune cause unique de tout déficit énergétique ancien n'est prouvée par A15.

{NEXT}

Livrables : rapport, configuration épinglée, scripts/générateurs, campaign_review.json, scientific_assessment.json, execution_summary.json, historiques et états SI, journaux d'échecs, manifeste, preuve de préservation et handoff. Le contrôle d'intégrité des **sorties disponibles** passe ; l'ensemble des objectifs de deux calculs achevés et la qualification scientifique globale restent échoués.
''',encoding='utf-8')
    HANDOFF.write_text(f'''# Reprise WTC1 — AIRCRAFT-A15 → AIRCRAFT-A16

Demande utilisateur appliquée : lancement couplé du prototype avion complet contre façade déformable, programme A15 changé, qualification et échecs anciens inchangés.

Rapport : {rel(REPORT)} ; configuration : {rel(CFG)} ; résultats : {rel(OUT/'campaign_review.json')} ; assessment : {rel(OUT/'scientific_assessment.json')}. Premier principal terminé normalement à{r['end_ms']:.9f}ms ; demi-pas TIMEOUT600s, dernier TH{partial['last_available_main_history_ms']:.6f}ms, aucune fin certifiée. Deux principaux, un observateur, zéro ancien solveur relancé. Données disponibles binaires/CSV vérifiées,8795 fichiers39,5196Go préservés.

Déplacement façade échantillonné{r['maximum_facade_displacement_mm']:.3f}mm ; impulsion X{r['last_main_contact_impulse_Ns'][0]/1000:.6f}kN·s au dernier TH9,990103ms. Contact du nez seul ; moteurs encore sans contact. Bilans énergie et quantité de mouvement du principal passent leurs limites déclarées, avec marge locale1000J ; matériaux échoués, radôme ratiomax{r['maximum_radome_face_strength_ratio']:.6f}, premier état hors référence≈1ms. Demi-pas sur fenêtre commune6,240026ms : ΔJ{100*cmp['impulse_difference_fraction']:.7f}%, ΔG{100*cmp['generated_energy_difference_fraction']:.7f}%. Pas de convergence jusqu'à10ms ni spatiale.

Scène mécanique A11 identique, quatre contacts TYPE25 canoniques nœuds/surface, Stfac1 non pondéré ; auto-contact radôme TYPE7.944 bords fixes,31792 nœuds de façade déformable. Sans rupture, écrasement, délamination ou carburant résolu ; module parallèle non intégré. Temps exact des animations lu dans FASTMAGI10, échec du lecteur initial conservé, aucun crédit rétroactif.

Visualisation : {rel(OUT/'visualisation/impact_avion_facade.html')},21 états natifs×1, bilan comparatif SVG/PNG et géométrie PNG inspectés. État10ms hors domaine matériel ; GUI interactive non certifiée.

{NEXT}
''',encoding='utf-8')
    scriptnames=['run_aircraft_a15.py','review_aircraft_a15.py','recover_aircraft_a15_partial.py','visualize_aircraft_a15.py','verify_aircraft_a15_preservation.py','finalize_aircraft_a15.py']
    files=[q for q in OUT.rglob('*') if q.is_file()]+[CFG,HANDOFF]+[ROOT/'wtc1_simulation_v8/scripts'/n for n in scriptnames]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size} for q in sorted(set(files))]})
    print({'prepared':True,'new_files':len(set(files)),'completed_cases':1,'incomplete_cases':1,'available_output_integrity_pass':True,'scientific_pass':False},flush=True)

def register():
    guard();count=checkrows(read(OUT/'artifact_manifest.json')['files']);assert REPORT.exists() and HANDOFF.exists()
    s=read(OUT/'campaign_review.json');a=read(OUT/'scientific_assessment.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert st['current_iteration']=='AIRCRAFT-A14' and st['next_iteration']=='AIRCRAFT-A15' and cy['pending_iterations']==['AIRCRAFT-A14'] and harness()['Status']=='PASS'
    reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix;t=now()
    rec={'experiment_id':'WTC1-AIRCRAFT-A15','registered_at':t,'status':'completed_exploratory_whole_aircraft_facade_10ms_with_retained_incomplete_half_dt_and_material_failures','configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'campaign_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),'integrity_only_pass':s['integrity_only_pass'],'available_output_integrity_pass':s['available_output_integrity_pass'],'all_declared_checks_pass':False,'main_engine_jobs':2,'completed_main_engine_jobs':1,'capped_main_engine_jobs':1,'observer_jobs':1,'old_solver_reruns':0,'old_files_preserved':8795,'branch_iteration_count':15,'whole_aircraft_iteration_count':11,**a,'next_iteration':'AIRCRAFT-A16'}
    with reg.open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    st.update(current_iteration='AIRCRAFT-A15',next_iteration='AIRCRAFT-A16',current_status=rec['status'],next_objective=NEXT,updated_at=t)
    st['aircraft_a15_key_results']=rec;st['validated_artifacts'].update(aircraft_a15_report=rel(REPORT),aircraft_a15_results=rel(OUT/'campaign_review.json'),aircraft_a15_handoff=rel(HANDOFF))
    st['user_steering_2026_10_08_launch_whole_aircraft']={'request':'si avion prêt lance le sur façade ; avancer au-delà des contrôles locaux','implemented':'main executable inherited aircraft launched against deformable facade; fresh10ms completed, half-step retained incomplete600s; material limits preserved','known_damage_target':False,'old_failed_gates_retained':True,'next':'AIRCRAFT-A16'}
    cy.update(pending_iterations=['AIRCRAFT-A14','AIRCRAFT-A15'],pending_count=2,next_publication_after='A14+A15 pair due; prepare immutable scientific archives including material failures and incomplete fine attempt, then verify public release independently',updated_at=t)
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy);verify(count)

def verify(count=None):
    guard();count=count or checkrows(read(OUT/'artifact_manifest.json')['files']);before=read(OUT/'before_state.json');st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    reg=(ROOT/'harness/experiments/registry.jsonl').read_bytes();prefix=(OUT/'before_registry.jsonl').read_bytes();tail=reg[len(prefix):].decode('utf-8').splitlines();v=harness()
    protected=[k for k in before if k.endswith('_key_results')]+['source_archive','evidence_policy','open_limitations','deferred_thermal_branch']
    checks={'new_artifact_hashes_verified':True,'old_files_preserved':read(OUT/'preservation_verification.json')['pass'],'historical_results_and_policies_unchanged':all(st[k]==before[k] for k in protected),'registry_single_append':reg.startswith(prefix) and len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A15','state_route':st['current_iteration']=='AIRCRAFT-A15' and st['next_iteration']=='AIRCRAFT-A16','publication_pending_pair':cy['pending_iterations']==['AIRCRAFT-A14','AIRCRAFT-A15'] and cy['pending_count']==2,'publication_baseline_unchanged':all(cy[k]==read(OUT/'before_publication_cycle.json')[k] for k in ['last_published_commit','last_published_release','last_published_iteration']),'scientific_failures_and_incomplete_run_retained':not read(OUT/'campaign_review.json')['all_declared_checks_pass'] and read(OUT/'scientific_assessment.json')['fine_case_incomplete_cost_cap'],'required_artifacts_exist':REPORT.exists() and HANDOFF.exists(),'harness_pass':v['Status']=='PASS'}
    proof={'created_utc':now(),'pass':all(checks.values()),'integrity_only':True,'checks':checks,'new_files_verified':count,'old_files_verified':8795,'harness':v,'physical_impact_qualified':False,'seconds_impact_calculated':False,'next_iteration':'AIRCRAFT-A16','external_publication_performed':False}
    assert proof['pass'],proof;dump(OUT/'publication_verification.json',proof);print(proof,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register','verify']);globals()[p.parse_args().action]()
