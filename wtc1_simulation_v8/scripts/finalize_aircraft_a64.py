"""Seal the authorized refined/local and conditional whole checks, including failures."""
from run_aircraft_a64_step import ROOT, OUT, CFG, read, dump, sha, now, rel, harness
import json, re

REPORT = OUT / 'rapport_aircraft_a64.md'
HANDOFF = ROOT / 'harness/handoffs/WTC1_AIRCRAFT_A64_HANDOFF.md'

def route():
    return ('AIRCRAFT-A65 : préparer les sorties TH à chaque pas et sauvegarder la frontière1ms, '
            'sans changement moteur, mécanique ou de seuil. Nouveau lot à autoriser : deux témoins puis deux CHECK entiers seulement si les critères passent. '
            'A64 deux Engine exécutés ; ses deux CHECK conditionnels non utilisés car le composé initial échoue. '
            'Préserver les défauts au repos et sous mouvements imposés A62, le critère temporel échoué A63, '
            'les budgets, anciennes sorties et tous les critères entiers ouverts. '
            'Objectif dix secondes physiques puis vidéo3D incomplet ; meilleur impact entier0,0200001220703125s. '
            'Une nouvelle modification ou compilation moteur exige un accord distinct sur une proposition prête.')

def assess():
    assert not REPORT.exists()
    assert read(ROOT/'harness/state.json') == read(OUT/'before_state.json')
    assert sha(CFG) == read(OUT/'declaration_guard.json')['sha256']
    cfg = read(CFG); free = read(OUT/'free_cohesive_qualification_review.json')
    sampling=read(OUT/'sampling_and_actual_cycle_review.json')
    whole_path = OUT/'whole_CHECK_review.json'
    assert whole_path.exists() == bool(free['pass'])
    whole = read(whole_path) if whole_path.exists() else None
    launches = list(OUT.rglob('engine.execution.json'))
    assert len(launches) == (4 if whole else 2)
    assert all(read(p)['cap_s'] == 180 and read(p)['CPU_threads'] == 1 and not read(p)['GPU'] for p in launches)
    if whole:
        rows = []
        for case in whole['cases']:
            folder = OUT/case['case']; log = (folder/'engine.log').read_text(encoding='utf8', errors='replace')
            rows.append({'case':case['case'], 'engine_completion':case,
                         'zero_negative_volume_lines': [line.strip() for line in log.splitlines() if re.search('zero|negative',line,re.I) and re.search('volum',line,re.I)],
                         'stop_break_abort_lines': [line.strip() for line in log.splitlines() if re.search(r'USER\s*BREAK|STOP|MPI_ABORT|SIGSEGV',line,re.I)]})
        dump(OUT/'whole_CHECK_observed_messages.json', {'created_utc':now(), 'cases':rows, 'literal_messages_preserved':True})
    changed=[]
    for row in read(OUT/'preservation_before_metadata.json')['files']:
        stat=(ROOT/row['path']).stat()
        if stat.st_size != row['bytes'] or stat.st_mtime_ns != row['mtime_ns_before']: changed.append(row['path'])
    assert not changed
    assert sha(ROOT/'harness/experiments/registry.jsonl') == sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json', {'created_utc':now(), 'pass':True, 'changed_paths':changed,
        'old_files_metadata_checked':len(read(OUT/'preservation_before_metadata.json')['files']),
        'all_old_files_rehashed':False, 'old_diagnostics_replayed':False, 'archives_not_rescanned':True})
    temporal=all(row['pass'] for row in free['half_dt_energy_comparisons'])
    status='completed_refined_free_gate_pass__whole_CHECK_'+('pass_not_dynamic_qualification' if whole['all_clean'] else 'failed') if whole else 'completed_refined_free_gate_failed__conditional_whole_not_run'
    a={'created_utc':now(),'iteration':'AIRCRAFT-A64','status':status,'new_Engine_runs':len(launches),
       'new_Starter_runs':len(list(OUT.rglob('starter.execution.json'))),'authorized_A64_maximum_native':4,
       'separate_A64_authorization':rel(ROOT/'wtc1_simulation_v8/data/aircraft_a64_authorization.json'),
       'prior_A61_cap_consumed_preserved':12,'new_software_changes_or_compilation':False,
       'free_case_checks_pass':sum(row['pass'] for row in free['cases']),
       'free_boolean_checks_pass':sum(sum(row['checks'].values()) for row in free['cases']),
       'refined_free_composite_pass':free['pass'],'half_dt_temporal_pass':temporal,
       'sampling_diagnosis':rel(OUT/'sampling_and_actual_cycle_review.json'),
       'fine_TH_missing_intermediate_steps':sampling['cases'][1]['missing_steps_before_last_saved_cycle'],
       'native_counter_half_dt_pass_on_saved_times':all(row['pass'] for row in sampling['native_counter_comparisons']),
       'A64_raw_reader_inapplicable_to_sparse_second_case':True,
       'unused_conditional_whole_controls':2,
       'maximum_energy_difference_J':max(row['maximum_difference_J'] for row in free['half_dt_energy_comparisons']),
       'half_dt_energy_tolerance_J':free['half_dt_energy_comparisons'][0]['tolerance_J'],
       'new_whole_CHECK':whole is not None,'whole_CHECK_clean':bool(whole and whole['all_clean']),
       'A52_integrated':False,'whole_mass_material_budgets_changed':False,'RKE_added':False,
       'failed_coarse_A63_criteria_preserved':True,'A62_failures_preserved':True,
       'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,
       'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A65'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'free':free,'sampling':sampling,'whole_CHECK':whole,
         'budget_context':'A62+A63 consumed previous12; A64 separately authorized maximum4. Legacy reviewer field describes previous lot only.'})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    comparisons='; '.join(f"{row['channel']} : {row['maximum_difference_J']:.10g} J, seuil {row['tolerance_J']:.10g} J, PASS={row['pass']}" for row in free['half_dt_energy_comparisons'])
    whole_text='Deux CHECK entiers conditionnels exécutés sur les anciennes entrées exactes, empreintes vérifiées. '+json.dumps(whole['cases'],ensure_ascii=False) if whole else 'Les CHECK entiers conditionnels ne sont pas exécutés car le composé local échoue.'
    report=f'''# AIRCRAFT-A64 — raffinement libre et contrôles entiers conditionnels

Composé local PASS={free['pass']}. {comparisons}. CHECK entier propre={bool(whole and whole['all_clean'])}. Aucun crédit de temps physique pour l’impact entier.

## 1. Faits directement observés ou transcrits

{len(launches)} nouveaux Engine sur le moteur A62 inchangé, un CPU, plafond180s chacun, sansGPU, installation ou compilation. Accord distinct «continue» du14octobre2026 sur la proposition de quatre contrôles maximum ; les douze anciens restent consommés. Deux Starter locaux propres ; sorties et messages natifs conservés. Chaque cas libre garde les22contrôles A63 et les mêmes seuils. {comparisons}.

Le lecteur initial est inapplicable au second cas : TFILE0,0001ms dépasse le pas0,0000625ms, et6000pas intermédiaires manquent. Les calculs dérivés qui supposent une ligne par cycle restent sauvegardés comme échecs initiaux, sans les confondre avec une divergence physique. Une analyse séparée des cycles réellement enregistrés trouve déplacement analytique≤7,31e-10mm, compteurs KE/IE≤5,58e-10J d’écart à la solution exacte, conservation native≤6,01e-10J et impulsion/support≤2,21e-9Ns. Les différences des compteurs KE/IE entre pas, aux temps sauvegardés communs, passent le seuil inchangé. Cela ne répare pas l’absence du champ terminal complet à1ms et ne promeut pas la qualification globale.

{whole_text}

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Moteur OpenRadioss A62 figé SHA256 {cfg['binary_sha256']}, schéma Newmark gamma0,5/beta0,25 et reconstruction de vitesse sur degrés libres selon les sources déjà vérifiées. Aucun ancien diagnostic natif rejoué. Intégrité logicielle et publication ne prouvent pas la simulation physique entière.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo, photographie ou PDF consulté/modifié. Aucun dégât historique utilisé comme cible.

## 4. Hypothèses propres au modèle

Graine{cfg['seed']}, zéro tirage ; oscillateur surfacique élastique10×10mm, masse instrumentale8g, quatre nœuds mobiles, vitesse initialeY1mm/ms et travail extérieur nul. Matériau, géométrie et masse identiques à A63. Seul le pas devient0,000125/0,0000625ms selon la borne de dispersion analytique. Ni masse ni propriété ajustée ; les masses instrumentales ne fixent pas le pas du futur avion entier.

## 5. Résultats dérivés

Les analyses libres suivent les canaux natifs binaires et CSV, la réponse Newmark discrète exacte, l’énergie physique et l’impulsion des seuls supports. Les différences temporelles sont évaluées avec le seuil préexistant, sans assouplissement. Les CHECK entiers, lorsqu’exécutés, vérifient les mêmes scènes originales et appariées sur le nouveau moteur ; ils ne sont pas une extension dynamique. Scripts, paramètres, messages et sorties sauvegardés ; budgets et anciens échecs préservés.

## 6. Contradictions et informations manquantes

Composé local={free['pass']}, CHECK entier propre={bool(whole and whole['all_clean'])}. Les échecs au repos et sous mouvements prescrits A62, l’échec temporel aux anciens pas A63, les domaines matériaux, inerties, grandes rotations, retour arrière natif et bilans locaux entiers restent ouverts. A52 non intégré. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes. Aucune seconde manquante fabriquée, aucun RKE compensateur.

{route()}
'''
    REPORT.write_text(report,encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A64 → AIRCRAFT-A65\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a64*.py'))+[CFG,ROOT/'wtc1_simulation_v8/data/aircraft_a64_authorization.json',HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'owned_results_only':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps(a),flush=True)

def register():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json')
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl') and cycle['pending_iterations']==[]
    manifest=read(OUT/'artifact_manifest.json')
    for row in manifest['files']: assert sha(ROOT/row['path'])==row['sha256'],row['path']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A64','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as stream: stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A64',next_iteration='AIRCRAFT-A65',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a64_key_results']=row
    state['validated_artifacts'].update(aircraft_a64_report=rel(REPORT),aircraft_a64_results=rel(OUT/'composite_qualification_review.json'),aircraft_a64_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A64'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A64+AIRCRAFT-A65 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]: p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==183
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':len(manifest['files']),'harness':h,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A65'})
    print(json.dumps({'A64_registered':True,'registry_entries':183,'pending_publication_count':1}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
