"""Seal approved eighth build and six controls; zero-time policy FAILED, free regression and positive load PASS."""
from build_aircraft_a71_initial_zero import ROOT,OUT,CFG,read,dump,sha,now,guard
from build_aircraft_a54_graph import rel,harness
from pathlib import Path
import json

REPORT=OUT/'rapport_aircraft_a71.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A71_HANDOFF.md';PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A72_2026-10-14.md'

def route():
    return ('AIRCRAFT-A72 : audit/proposition en lecture seule de la sélection CHECK, à partir du nouvel échec A71. '
        'Le moteur avance TT avant IMP_CHKM ; la garde TT==0 ne correspond pas au contexte du premier contrôle. '
        'Préparer une sélection explicite par IMP_CHK>0, sans temps absolu supposé, et des observations des flags/horloges dans les futurs contrôles. '
        'A71 huitième moteur compilé exactement après accord ; six Engine et un Starter autorisés consommés, aucun replay ou crédit entier. '
        'Dynamique libre1ms et charge positive R2=4 passent ; zéro statique reste refusé comme prévu ; zéro dynamique et deuxCHECK entiers restent échoués avec R2=0. '
        'Conserver cette nouvelle garde ratée et toutes les anciennes sorties/critères/budgets. Les 107391 avertissements et cinq TYPE25 par scène sont bloquants. '
        'Toute nouvelle modification/compilation et lot natif exigent une proposition concrète et un accord distinct. '
        'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.')

def assess():
    config=guard();assert not REPORT.exists();built=read(OUT/'build_finished.json');policy=read(OUT/'CHECK_policy_control_review.json');free=read(OUT/'free_dynamic_regression_review.json')
    assert built['build_success'] and built['exact_A70_R4_CHECK_policy_applied'] and not policy['pass'] and free['pass']
    runs=list(OUT.rglob('engine.execution.json'));stars=list(OUT.rglob('starter.execution.json'));assert len(runs)==6 and len(stars)==1
    for p in runs:
        r=read(p);assert r['CPU_threads']==1 and r['cap_s']==180 and not r['GPU'] and r['binary_sha256']==built['binary_sha256']
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[];binaries=[]
    for r in old:
        p=ROOT/r['path'];s=p.stat()
        if s.st_size!=r['bytes'] or s.st_mtime_ns!=r['mtime_ns_before']:changed.append(r['path'])
        if '/isolated_exec/engine_' in r['path']:assert sha(p)==r['sha256'];binaries.append(r['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'old_Engines_rehashed':binaries,
        'changed_paths':changed,'all_old_files_rehashed':False,'old_native_diagnostics_replayed':False,'archive_not_rescanned':True,'old_failed_time_guards_preserved':True})
    controls=read(OUT/'native_execution_review.json')['cases']
    a={'created_utc':now(),'iteration':'AIRCRAFT-A71','status':'completed_eighth_isolated_Engine_and_six_controls__literal_TT_zero_policy_FAILED',
        'source_pin':config['source_pin'],'exact_A70_R4_patch_applied':True,'build_success':True,'binary_sha256':built['binary_sha256'],
        'build_wall_s':built['wall_s_from_original_start'],'build_CPU':6,'build_within_hour':True,'GPU':False,'installation':False,
        'new_Engine':6,'new_Starter':1,'controls_remaining':0,'Starter_remaining':0,'five_native_CHECK_observations_complete':True,
        'initial_zero_CHECK_policy_pass':False,'failed_expected_zero_cases':policy['failed_expected_initial_zero_cases'],
        'positive_static_load_R2':4.,'positive_static_CHECK_pass':True,'static_zero_rejected_as_expected':True,'free_dynamic_regression_pass':True,
        'free_dynamic_checks':len(free['case']['checks']),'free_actual_TH_last_ms':free['case']['last_TH_ms'],
        'native_original_and_paired_R2_measured_zero':True,'original_A69_missing_observation_not_relabelled':True,
        'TT_advance_before_CHECK_source_verified':True,'native_flags_and_TT_not_directly_observed':True,
        'whole_CHECK_pass':False,'whole_loading_errors_per_scene':1,'whole_warnings_per_scene':107396,'TYPE25_ignored_per_scene':5,
        'new_CHECK_admissibility_patch_ineffective_in_zero_controls':True,'whole_inputs_mass_material_inertia_budgets_changed':False,'RKE_added':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A72'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'policy':'CHECK_policy_control_review.json',
        'free':'free_dynamic_regression_review.json','source_chronology':'CHECK_call_order_review.json','whole_physical_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    table='\n'.join(f"| {r['case']} | {r.get('native_R2','dynamique')} | {r['loading_errors']} | {r['initial_zero_dynamic_INFO']} | {next(v['software_control_pass'] for v in policy['cases'] if v['case']==r['case'])} |" for r in controls)
    REPORT.write_text(f'''# AIRCRAFT-A71 — moteur compilé, garde TT initial échouée

Le huitième moteur applique exactement le correctif A70 R4 autorisé et compile. Les six contrôles sont terminés ; la garde de résidu initial échoue dans trois cas. La dynamique libre et le contrôle chargé positif passent. Aucun prolongement d’impact entier.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, appliquer et compiler le correctif A70 et exécuter le lot A71 » lié aux empreintes avant application. Premier build en {built['wall_s_from_original_start']:.3f}s, six CPU/plafond1h, sans GPU ni installation ; Starter non recompilé. Binaire SHA256 {built['binary_sha256']}. Toutes les corrections A67 conservées ; source appliquée égale exactement à la proposition R4, patch fuzz0, workspace distinct puis démonté. Six Engine CPU1/cap180s et un Starter CPU1/cap180s, propres, budgets entièrement consommés.

| Contrôle | R2 natif | Erreurs de chargement | Nouveau INFO | Critères attendus |
|---|---:|---:|---:|---|
{table}

Le Starter du témoin positif passe sans erreur ni avertissement. Sa charge déclarée1N sur chacun des quatre nœuds supérieurs donne R2=4, et aucune erreur CHECK. Le zéro statique reste refusé, comme demandé. Les cinq observations CHECK sont complètes, y compris l’original jusque-là manquant en A69 ; R2=0 dans original/appairé et témoin libre. Le premier échec A69 n’est pas réécrit. Aucune nouvelle INFO dans ces trois cas : l’exception proposée n’est pas atteinte. Chaque scène entière garde1ERROR/107396WARNINGS et cinq TYPE25 ignorés ; pas de STOPvolume.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La chronologie native du pin déclaré est lue après le nouvel échec : RESOL incrémente son horloge TT avant CALL IMP_CHKM, sous IF(IMP_CHK>0), puis fixe MSTOP2. Le contexte d’un CHECK initial ne correspond donc pas à TT exactement zéro. Cette relation est directement vérifiée dans la source, mais les flags et la valeur précise de TT à l’appel ne sont pas directement capturés ici. Aucune valeur scalaire native supposée à partir du seul affichage de départ.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée, aucune analyse vidéo ni ajustement aux dégâts connus. Source logicielle figée et entrées de modèle distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102096, zéro tirage. Unitésg/mm/ms, coupon instrumental8g conservé. L’idée de résidu nul admissible pour un problème dynamique reste appuyée par le témoin libre, mais le critère de sélection TT0 proposé est incorrect pour le contexte observé. Aucun remplacement silencieux de contact ni force ajoutée aux scènes entières. Matrice surfacique toujours d’itération, pas jacobien exact ; domaine libre élastique uniquement.

## 5. Résultats dérivés

La régression libre du nouveau binaire passe {len(free['case']['checks'])}critères, avec TH terminal {free['case']['last_TH_ms']}ms, résidu énergie {free['case']['maximum_scope_energy_residual_J']:.10g}J et résidu impulsion/support {free['case']['maximum_scope_momentum_residual_Ns']:.10g}Ns, aux seuils A67 inchangés. Charge positive et refus statique préviennent une acceptation universelle de zéro. Le critère neuf zéro dynamique reste échoué, ainsi que les deux CHECK entiers. Il faut préparer une sélection par le contexte CHECK explicite et mesurer les flags/horloges dans la prochaine variante, sans rejouer l’ancien lot ni réinitialiser son budget.

## 6. Contradictions et informations manquantes

Compilation/NORMAL ne sont pas réussite de la garde ou de l’impact. La proposition A70 TT0 reste conservée comme nouvelle tentative ratée ; source audit15contrôles et compilation ne l’avaient pas qualifiée nativement. Les107391 avertissements de coefficients transformés et cinq TYPE25 restent bloquants. Les flags IDYNA/IQSTAT/IMP_CHK/TT/NCYCLE à l’appel manquent encore ; pas de valeur inventée. A52nonintégrée, inerties, matériaux, contacts et bilans locaux entiers non qualifiés. A71 six Engine/un Starter entièrement consommés. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet, aucun temps de témoin crédité.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A71 → AIRCRAFT-A72\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+' et '+rel(HANDOFF)+'.\nL’état local prime. Aucun calcul en cours. Vérifier la publication A70+A71 avant nouvelle itération.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a71*.py'))+[CFG,ROOT/'wtc1_simulation_v8/data/aircraft_a71_authorization.json',
        ROOT/'wtc1_simulation_v8/data/aircraft_a71_controls.json',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_output_script_only_no_AGPL_raw_binary_or_source':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A71_assessed':True,'initial_zero_policy_PASS':False,'free_dynamic_PASS':True,'native_budget_consumed':6}),flush=True)

def register():
    guard();s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json');assert c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==['AIRCRAFT-A70']
    m=read(OUT/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now();row={'experiment_id':'WTC1-AIRCRAFT-A71','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A71',next_iteration='AIRCRAFT-A72',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a71_key_results']=row;s['validated_artifacts'].update(aircraft_a71_report=rel(REPORT),aircraft_a71_results=rel(OUT/'composite_qualification_review.json'),aircraft_a71_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A70','AIRCRAFT-A71'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A70+AIRCRAFT-A71 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==190
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),'harness':h,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A72'})
    print(json.dumps({'A71_registered':True,'registry':190,'pending_publication':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
