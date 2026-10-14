"""Seal the exact approved ninth build and six controls, with whole physical gates retained."""
from build_aircraft_a73_CHECK_context import ROOT,OUT,CFG,read,dump,sha,now,guard,AUTH
from control_aircraft_a73_CHECK_context import CONTROL
from build_aircraft_a54_graph import rel,harness
from pathlib import Path
import json

REPORT=OUT/'rapport_aircraft_a73.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A73_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A74_2026-10-14.md'


def route():
    return ('AIRCRAFT-A74 : préparer en lecture seule la prochaine étape à partir des résultats natifs A73, '
        'après publication A72+A73 vérifiée. Utiliser les cinq paramètres natifs, R2 et les avertissements effectivement mesurés ; '
        'conserver A71 gardeTT0 échouée, anciennes sorties, contacts/budgets et tous les critères physiques échoués. '
        'Si la garde CHECK passe, traiter le contrat des cinq TYPE25 ignorés et des avertissements de préconditionnement '
        'avant toute intégration/prolongation entière ; réutiliser les audits existants, aucune substitution silencieuse. '
        'A73 neuf moteurs isolés au total, six Engine/zéro Starter autorisés entièrement consommés. '
        'Toute nouvelle modification de logiciel/compilation ou lot natif requiert une proposition concrète et un accord distinct. '
        'Pas de GPU, installation, RKE de compensation, calibrage aux dégâts connus ni crédit de témoins. '
        'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.')


def assess():
    config=guard();assert not REPORT.exists()
    built=read(OUT/'build_finished.json');policy=read(OUT/'CHECK_policy_control_review.json')
    free=read(OUT/'free_dynamic_regression_review.json');contexts=read(OUT/'native_CHECK_context_review.json')
    assert built['build_success'] and built['exact_A72_CHECK_context_applied']
    assert built['within_original_hour'] and built['CPU_threads']==6 and built['no_installation']
    runs=list(OUT.rglob('engine.execution.json'));assert len(runs)==6 and not list(OUT.rglob('starter.execution.json'))
    for p in runs:
        r=read(p);assert r['CPU_threads']==1 and r['cap_s']==180 and not r['GPU']
        assert r['binary_sha256']==built['binary_sha256'] and r['wall_s']<195
    controls=read(OUT/'native_execution_review.json')
    assert controls['new_Engine']==6 and controls['new_Starter']==controls['remaining_Engine']==0
    assert policy['all_five_CHECK_observations_complete'] and policy['all_five_context_observations_complete']
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[];binaries=[]
    for row in old:
        p=ROOT/row['path'];s=p.stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
        if '/isolated_exec/engine_' in row['path']:
            assert sha(p)==row['sha256'];binaries.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,
        'old_files_metadata_checked':len(old),'old_Engines_rehashed':binaries,'changed_paths':changed,
        'all_old_files_rehashed':False,'old_native_diagnostics_replayed':False,
        'archive_not_rescanned':True,'A71_failed_time_guard_and_budget_preserved':True})
    whole=[r for r in controls['cases'] if r['case'].startswith('WHOLE_')]
    assert len(whole)==2
    a={'created_utc':now(),'iteration':'AIRCRAFT-A73',
        'status':'completed_ninth_isolated_Engine_and_six_controls__CHECK_context_policy_'+('PASS' if policy['pass'] else 'FAILED'),
        'source_pin':config['source_pin'],'exact_A72_patch_applied':True,'build_success':True,
        'binary_sha256':built['binary_sha256'],'build_wall_s':built['wall_s_from_original_start'],
        'build_CPU':6,'build_within_hour':True,'GPU':False,'installation':False,
        'new_Engine':6,'new_Starter':0,'controls_remaining':0,'Starter_remaining':0,
        'five_native_CHECK_observations_complete':True,'five_native_context_observations_complete':True,
        'CHECK_context_policy_pass':policy['pass'],'failed_expected_cases':policy['failed_expected_cases'],
        'positive_static_control':next(r for r in controls['cases'] if r['case']=='STATIC_POSITIVE_LOAD_CHECK'),
        'static_zero_case_pass':next(r['software_control_pass'] for r in policy['cases'] if r['case']=='STATIC_INITIAL_ZERO_CHECK'),
        'free_dynamic_regression_pass':free['pass'],'free_dynamic_checks':len(free['case']['checks']),
        'free_actual_TH_last_ms':free['case']['last_TH_ms'],'native_contexts':contexts['cases'],
        'old_A71_TT0_failed_policy_not_relabelled':True,'whole_CHECK_pass':False,
        'whole_actual_messages':whole,'five_TYPE25_and_warning_gates_preserved':True,
        'whole_inputs_mass_material_inertia_budgets_changed':False,'RKE_added':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A74'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,
        'policy':'CHECK_policy_control_review.json','free':'free_dynamic_regression_review.json',
        'native_context':'native_CHECK_context_review.json','whole_physical_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,
        'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    table='\n'.join(f"| {r['case']} | {r.get('native_R2','dynamique')} | {r['loading_errors']} | {r['initial_zero_dynamic_INFO']} | {next(v['software_control_pass'] for v in policy['cases'] if v['case']==r['case'])} |" for r in controls['cases'])
    context_table='\n'.join(f"| {r['case']} | {r['native_context']['IDYNA']} | {r['native_context']['IQSTAT']} | {r['native_context']['IMP_CHK']} | {r['native_context']['NCYCLE']} | {r['native_context']['TT']:.15g} |" for r in contexts['cases'])
    whole_text=' ; '.join(f"{r['case']} : {r['printed_errors']} erreurs/{r['printed_warnings']} avertissements, {r['TYPE25_ignored']} TYPE25 ignorés" for r in whole)
    REPORT.write_text(f'''# AIRCRAFT-A73 — moteur isolé et contrôle de contexte CHECK

Le neuvième moteur applique exactement le correctif A72 autorisé et compile. Les six contrôles sont terminés, cinq contextes CHECK sont directement mesurés. Le contrôle de la nouvelle politique est {policy['pass']}. La qualification physique des scènes entières reste échouée et aucun impact entier n’est prolongé.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, appliquer le correctif A72, compiler et exécuter le lot A73 », reçu request_user_input_async/call_e3f6b6f4ebbd4da5bb9b7775f41c96e9/0, lié aux empreintes avant application. Premier build en {built['wall_s_from_original_start']:.3f}s, six CPU/plafond1h, sans GPU ni installation ; Starter non recompilé. Binaire SHA256 {built['binary_sha256']}. Toutes les corrections A71 sont portées dans le nouveau workspace, puis la différence A72 est appliquée fuzz0 et comparée exactement à la source approuvée. Les anciens moteurs ne sont pas modifiés ; workspace démonté. Six Engine CPU1/plafond180s, zéro Starter, budget entièrement consommé.

| Contrôle | R2 natif | Erreurs de chargement | Diagnostic zéro | Critères logiciels |
|---|---:|---:|---:|---|
{table}

Lectures directes des cinq scalaires au premier point IMP_CHECK0 existant, par mémoire de l’enfant en lecture seule. Offsets typés déclarés en A72, symboles/taille vérifiés dans le nouveau binaire. Aucun scalaire déduit du seul affichage de départ, instruction ou état mécanique modifié. Les valeurs TT sont celles de la variable native, en unités ms des entrées.

| Contrôle | IDYNA | IQSTAT | IMP_CHK | NCYCLE | TT natif (ms) |
|---|---:|---:|---:|---:|---:|
{context_table}

{whole_text}. Ces messages et les critères physiques restent bloquants. Les fichiers détaillés, résidus LB/R2 et diagonales avant/après préconditionnement sont conservés.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Même pin OpenRadioss déclaré que les versions précédentes. La chronologie de source A71 place l’avance TT avant CHECK ; la présente itération apporte les lectures natives qui manquaient, sans rejouer l’ancien lot. Ces observations logicielles ne sont pas des observations historiques de l’impact.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée, aucune analyse vidéo ni ajustement aux dégâts connus. Les sources logicielles privées AGPL, entrées de modèle et scripts propres du harnais restent séparés des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102098, zéro tirage, unitésg/mm/ms et coupon instrumental8g conservés. La nouvelle admissibilité est explicite : R2 exactement zéro en CHECK IDYNA2/IQSTAT0/IMP_CHK>0 reçoit un diagnostic et n’incrémente pas l’erreur de chargement. Les autres branches sont conservées. Cette politique ne supprime ni les contacts ignorés ni les avertissements et ne valide pas les budgets physiques. Aucun chargement entier, RKE, masse, matière, inertie ou dynamique n’est changé.

## 5. Résultats dérivés

La nouvelle politique CHECK passe : {policy['pass']}. Cas logiciels échoués : {policy['failed_expected_cases']}. La régression libre passe : {free['pass']}, avec {len(free['case']['checks'])} critères et TH terminal {free['case']['last_TH_ms']}ms aux seuils A67 inchangés. Résidu énergie {free['case']['maximum_scope_energy_residual_J']:.10g}J, résidu impulsion/support {free['case']['maximum_scope_momentum_residual_Ns']:.10g}Ns. Le témoin positif réutilise son Starter A71 propre et son état initial par empreintes ; aucune répétition du Starter. Les contrôles sont ceux du nouveau binaire, aucun crédit physique entier donné aux témoins.

## 6. Contradictions et informations manquantes

Compilation, terminaison normale et contrôles logiciels sont distincts de la qualification physique. La garde TT0 ratée A71 et tous ses échecs/budgets restent inchangés. Les cinq TYPE25 ignorés et avertissements de préconditionnement demeurent bloquants. Les inerties, domaines matériaux, contacts, bilans et intégration A52 entiers restent non qualifiés. A73 six Engine/zéro Starter entièrement consommés ; aucun calcul supplémentaire inclus dans cet accord. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D toujours incomplètes, aucun temps manquant extrapolé.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A73 → AIRCRAFT-A74\n\nRapport : '+rel(REPORT)+
        '\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json '
        'puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+' et '+rel(HANDOFF)+
        '.\nL’état local prime. Aucun calcul en cours. Vérifier la publication A72+A73 avant nouvelle itération.\n'+
        route()+'\nNouvelles courtes en français ; aucun replay des diagnostics déjà vérifiés.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a73*.py'))
    files += [CFG,AUTH,CONTROL,HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_output_script_only_no_AGPL_raw_binary_or_source':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A73_assessed':True,'CHECK_policy_PASS':policy['pass'],'free_dynamic_PASS':free['pass'],
        'native_budget_consumed':6,'whole_qualified':False}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==['AIRCRAFT-A72']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A73','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A73',next_iteration='AIRCRAFT-A74',current_status=a['status'],
        next_objective=route(),updated_at=stamp)
    s['aircraft_a73_key_results']=row
    s['validated_artifacts'].update(aircraft_a73_report=rel(REPORT),aircraft_a73_results=rel(OUT/'composite_qualification_review.json'),aircraft_a73_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A72','AIRCRAFT-A73'],pending_count=2,updated_at=stamp,
        next_publication_after='AIRCRAFT-A72+AIRCRAFT-A73 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==192
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,
        'files_verified':len(m['files']),'harness':h,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A74'})
    print(json.dumps({'A73_registered':True,'registry':192,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['assess','register'])
    globals()[parser.parse_args().action]()
