"""Prepare an output-only first-Newton observation; never run any native tool."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import json,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a82'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a82_preparation'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a82_preparation.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a82_proposal.json'
REPORT=OUT/'rapport_aircraft_a82.md'
PROPOSAL=PREP/'proposition_observation_premier_Newton_A83.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A82_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A83_2026-10-15.md'
NAME='A81_COHESIVE_COMPRESSION_PARTIAL_OPEN_RECLOSE'


def route():
    return ('AIRCRAFT-A83 proposée non exécutée : une nouvelle observation Engine seulement, CPU1/plafond180s, '
        'restart initial propre A81 réutilisé, zéro Starter, correctif, compilation, GPU ou installation. '
        'Ajouter uniquement /IMPL/PRINT/NONLIN/-1 à la carte Engine A81 ; noms conservés dans un nouveau dossier isolé. '
        'Mesurer les critères du premier refus Newton et ses valeurs de référence avant tout changement de tolérance, '
        'pas, chargement ou physique. Le message79/ISTOP−2 peut rester attendu ; une observation ne devient pas '
        'trajectoire réussie. Un nouvel accord explicite est requis :1Starter+1Engine A81consommés. '
        'Ne pas redémarrer depuis une fin non convergée, ne pas abaisser silencieusement le minimum de pas. '
        'Anciennes sorties, critères échoués, budgets et107391avertissements conservés. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def stage():
    assert not any(p.exists() for p in [OUT,CFG,PLAN,PROPOSAL])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A81' and h['RegistryEntries']==200
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a81_predeclaration.json')
    d=ROOT/'wtc1_simulation_v8/output/aircraft_a81/A81_COHESIVE_LOOP'
    assert read(d/'starter_gate_review.json')['pass'] and read(OUT.parent/'aircraft_a81/publication_verification.json')['pass']
    assert read(OUT.parent/'aircraft_a81/observation_review.json')['native_last_time_ms']==0
    source=d/(NAME+'_0001.rad');initial=d/(NAME+'_0000_0001.rst')
    assert initial.stat().st_size>0
    OUT.mkdir();PREP.mkdir(exist_ok=True);dump(OUT/'harness_before_preparation.json',h)
    private=ROOT/'wtc1_simulation_v8/openradioss_runtime/a82_dt_limit_audit'
    sm=read(private/'source_selection.json')
    for row in sm['copied_members_unmodified']:assert sha(ROOT/row['private_path'])==row['sha256']
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A82_PREPARATION','seed':1102105,'random_draws':0,
        'purpose':'New source audit and output-only first-Newton observation prepared, no native rerun',
        'sources':[{'path':rel(source),'sha256':sha(source)},{'path':rel(initial),'sha256':sha(initial)}],
        'private_pinned_source_manifest':rel(private/'source_selection.json'),'private_source_manifest_sha256':sha(private/'source_selection.json'),
        'primary_output_reference':'https://www.2023.help.altair.com/2023/hwsolvers/rad/topics/solvers/rad/output_messages_implicit_fea_r.htm',
        'primary_example':'https://2022.help.altair.com/2022.3/hwsolvers/rad/topics/solvers/rad/fan_blade_rotation_initialization_example_r.htm',
        'new_Engine':0,'new_Starter':0,'source_patch_compilation_GPU_installation':False,
        'exploratory_source_copies_predate_synthesis_declaration':True})
    target=PREP/'FIRST_NEWTON_DETAIL';assert not target.exists();target.mkdir()
    new=target/source.name;text=source.read_text(encoding='utf8');assert '/IMPL/PRINT/' not in text
    new.write_text('/IMPL/PRINT/NONLIN/-1\n'+text,encoding='utf8',newline='\n')
    shutil.copy2(initial,target/initial.name)
    old=sections(source);after=sections(new)
    checks={'exactly_one_output_keyword_added':set(after)==set(old)|{'/IMPL/PRINT/NONLIN/-1'},
        'new_keyword_has_no_numeric_card':after['/IMPL/PRINT/NONLIN/-1']==[],
        'all_existing_Engine_keywords_and_values_exact':{k:v for k,v in after.items() if k!='/IMPL/PRINT/NONLIN/-1'}==old,
        'restart_is_exact_initial_Starter_snapshot':sha(initial)==sha(target/initial.name),
        'all_software_binaries_unchanged':all(sha(ROOT/r['path'])==r['sha256'] for r in c['unchanged_software']),
        'current_Starter_gate_pass':True,'fixed_dt_both_bounds_preserved':after['/IMPL/DT/STOP']==old['/IMPL/DT/STOP'],
        'all_three_nonlinear_tolerances_preserved':after['/IMPL/NONLIN/1']==old['/IMPL/NONLIN/1'],
        'RUN_and_target_unchanged':after['/RUN/'+NAME+'/1']==old['/RUN/'+NAME+'/1'],
        'no_new_native_or_source_change':True}
    assert all(checks.values())
    rows=[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [new,target/initial.name]]
    p={'created_utc':now(),'iteration':'AIRCRAFT-A82_PROPOSAL','seed':1102105,'random_draws':0,
        'name':NAME,'case':'FIRST_NEWTON_DETAIL','inputs':rows,'maximum_Engine':1,'maximum_Starter':0,
        'CPU_threads':1,'cap_s':180,'GPU':False,'source_patch':False,'compilation':False,'installation':False,
        'whole_dynamic_extension':False,'new_explicit_human_authorization_required':True,
        'unchanged_software':c['unchanged_software'],'source_Starter_gate':rel(d/'starter_gate_review.json'),
        'source_Starter_gate_sha256':sha(d/'starter_gate_review.json'),'restart_origin':'fresh successful Starter A81, no dynamic step accepted',
        'native_output_option':'/IMPL/PRINT/NONLIN/-1','expected_wall_s':[5,30],
        'unchanged_min_max_dt_ms':[.000125,.000125],'expected_physical_stop_may_remain':'MESSAGE79/ISTOP-2',
        'purpose':'Observe first Newton convergence criteria/references and sequence; no attempt to claim a passed trajectory',
        'observation_acceptance':['native NPRINT=-1 actually printed','first attempted cycle/time and nonlinear iteration observed',
            'convergence criteria and their available reference or normalized residuals printed and finite status classified',
            'stop, warnings, actual saved states and elapsed time preserved','no physical criterion reset or timestep reduction'],
        'scope_review':rel(PREP/'output_only_scope_review.json'),'old_A81_Starter_remaining':0,'old_A81_Engine_remaining':0,
        'physical_witness_or_contact_qualification':False,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,p);dump(PREP/'output_only_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,
        'plan_sha256':sha(PLAN),'new_native':0,'native_print_readback_not_yet_qualified':True})
    dump(PREP/'pinned_source_scope_review.json',{'created_utc':now(),'source_manifest':sm,
        'facts':{'freimpl.F:251-255':'PRINT/NONL prefix reads KEY4 into NPRINT; default0 at96',
            'imp_solv.F:1833-1849':'Rejected step rolls back time/cycle, adjusts DT, calls IMP_STOP if at minimum',
            'imp_dt.F:106-116':'Negative IMCONV reduces or clamps DT to declared minimum',
            'imp_solv.F:2022-2040':'ISTOP-2 maps to time-step-limit message79 and termination2'},
        'precise_initial_failure_cause_not_observed_in_A81':True,'raw_AGPL_sources_not_in_own_public_manifest':True})
    PROPOSAL.write_text('''# Proposition A83 — une observation détaillée du premier essai Newton

A81 a produit un Starter propre, puis un arrêt Engine79/ISTOP−2 avant tout état sauvegardé à temps positif. Les deux processus autorisés sont consommés. Le minimum de pas fixé au pas initial reste conservé, comme tous les critères échoués.

Une seule carte Engine est préparée dans un nouveau dossier. Elle ajoute uniquement /IMPL/PRINT/NONLIN/-1 ; la carte /IMPL/NONLIN/1, son premier paramètre et ses trois tolérances restent exactement identiques, ainsi que chargement, pas initial, minimum/maximum, sorties de champs, conditions physiques, solveur et horizon. Les noms restent A81 pour réutiliser exactement le restart initial, avec un dossier A83 distinct. Le restart vient du Starter réussi, jamais d’une fin dynamique rejetée. Aucun nouveau Starter.

Le lot proposé comporte un seul Engine A73 inchangé, unCPU/plafond180s, estimation5–30s, sans correctif, compilation, GPU, installation ou prolongement d’impact entier. Il doit imprimer les critères et valeurs normalisées/références disponibles du premier refus, le cycle/temps tenté et les messages. Une valeur non finie ou absente est signalée, jamais transformée en convergence. Le même arrêt peut rester attendu ; succès d’observation et réussite de trajectoire sont séparés. Un lancement échoué/expiré consomme sa seule place, sans réessai automatique.

L’analyse source explique le chemin compatible avec le message générique (rollback d’un pas rejeté puis minimum atteint), sans fournir les ratios réellement calculés dans A81. Il faut les mesurer avant de changer les bornes ou les tolérances. Documentation logicielle : [exemple officiel d’impression nonlinéaire](https://2022.help.altair.com/2022.3/hwsolvers/rad/topics/solvers/rad/fan_blade_rotation_initialization_example_r.htm). Le rendu réel de l’option reste à vérifier nativement.

Accord distinct requis pour ce nouveau lot : A81consommé n’autorise aucune autre exécution. Les échecs, avertissements et budgets anciens restent conservés. Aucun contact ou dommage n’est qualifié par cette observation. Dix secondes physiques et vidéo3D incomplètes ; meilleur impact entier0,0200001220703125s.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A82','status':'completed_read_only_first_step_stop_audit__output_only_Engine_observation_prepared_unrun',
        'new_Engine':0,'new_Starter':0,'source_patch':False,'compilation':False,'initial_R2_or_newton_ratios_not_observed':True,
        'native_A81_message':79,'native_A81_ISTOP':-2,'rejected_step_rollback_and_minimum_stop_source_path_identified':True,
        'prepared_output_only_scope_pass':True,'scope_checks':len(checks),'future_maximum_Engine':1,'future_maximum_Starter':0,
        'future_CPU':1,'future_cap_s':180,'new_explicit_consent_received':False,'cached_clean_Starter_restart_reused':True,
        'all_loads_nonlinear_tolerances_dt_bounds_and_binaries_preserved':True,'all_old_failed_gates_preserved':True,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A83'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A82 — rendre visible le premier refus de convergence

Préparation en lecture seule d’une observation nouvelle ; zéro exécution native, aucun correctif logiciel. Le prochain lot ne modifie que l’impression, pas les critères physiques ou numériques.

## 1. Faits directement observés ou transcrits

A81 : Starter propre, zéro erreur/zéro avertissement, Engine arrêté avec MESSAGE79/ISTOP−2. Un unique état natif sauvegardé à0ms, pas de compression ou rupture mesurée. La sortie confirme les deux bornes0,000125ms et une fréquence d’impression nonlinéaire0. Les valeurs ayant provoqué le premier refus ne figurent pas dans ce fichier.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Un [exemple logiciel officiel](https://2022.help.altair.com/2022.3/hwsolvers/rad/topics/solvers/rad/fan_blade_rotation_initialization_example_r.htm) documente l’impression des itérations nonlinéaires par /IMPL/PRINT/NONL/-1. Le parseur source épinglé accepte le préfixe NONL, lit la dernière composante dans NPRINT et le défaut vaut0. L’option NONLIN complète est préparée ; son rendu réel reste à vérifier.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source inspectée/modifiée. Trois fichiers logiciels sont copiés en privé depuis le cache épinglé, avec empreintes. La copie brute .F exploratoire dans la préparation est exclue explicitement du manifeste propre, avec les autres sources AGPL brutes.

## 4. Hypothèses propres au modèle

Graine1102105, zéro tirage ; unités g/mm/ms conservées. Le chemin source compatible rejette un pas, restaure temps/cycle, ajuste DT puis s’arrête lorsque DT égale le minimum. Cette lecture ne fournit pas la cause initiale du refus et ne permet pas d’accuser un résidu nul, un pivot ou la loi cohésive. Les sources éclairent une hypothèse de chemin ; seuls les critères nativement imprimés doivent la préciser.

## 5. Résultats dérivés

Une carte ajoute exactement /IMPL/PRINT/NONLIN/-1. Tous les blocs préexistants restent identiques, notamment /IMPL/NONLIN/1 (son premier champ n’est pas une fréquence d’impression), tolérances, /IMPL/DT/STOP, pas initial, chargement et horizon. Le restart initial du Starter A81 est copié à l’identique, sans Starter supplémentaire. Dix contrôles statiques de portée passent. Un EngineCPU1/plafond180s seulement est proposé, logiciel A73 inchangé, sans compilation/GPU/installation ou extension entière. La question porte sur les premières valeurs de convergence manquantes, pas sur un ancien diagnostic déjà vérifié.

## 6. Contradictions et informations manquantes

Aucun nouveau résultat natif. La trajectoire0,65ms du coupon, ses sortiesUSR peuplées, dommage, compression après rupture et retour de contact restent inconnus. L’arrêt79 peut être reproduit tout en réussissant une observation, mais ne sera jamais rebaptisé convergence. Une seule place nouvelle nécessite un accord explicite ; A81estconsommé. Toutes les anciennes sorties, bornes et tolérances restent conservées. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A82 → AIRCRAFT-A83\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prime ; A82peutêtrepréparée mais nonenregistrée pendantconfirmationpublicationA80+A81. Vérifierpreuvefinaleréelle.\n'+route()+'\nNouvellescourtesenfrançais.\n',encoding='utf8')
    dump(OUT/'harness_after_preparation.json',harness())
    dump(OUT/'preparation_verification.json',{'created_utc':now(),'pass':True,'prepared_not_registered':True,
        'plan_sha256':sha(PLAN),'report_sha256':sha(REPORT),'new_native':0})
    print(json.dumps({'A82_prepared':True,'registered':False,'new_native':0,'proposed_Engine':1}),flush=True)


def register():
    assert not (OUT/'artifact_manifest.json').exists()
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a80_a81/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    h=harness();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert h['RegistryEntries']==200 and s['current_iteration']=='AIRCRAFT-A81' and cycle['pending_iterations']==[]
    pv=read(OUT/'preparation_verification.json');assert pv['pass'] and sha(PLAN)==pv['plan_sha256'] and sha(REPORT)==pv['report_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_registration_'+Path(n).name))
    dump(OUT/'verified_prior_publication.json',proof)
    for e in read(ROOT/'wtc1_simulation_v8/output/aircraft_a81/artifact_manifest.json')['files']:assert sha(ROOT/e['path'])==e['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A81_sealed_files_rehashed':True,'no_old_native_replayed':True})
    auth_path=ROOT/'wtc1_simulation_v8/data/aircraft_a83_authorization.json'
    auth=read(auth_path)
    assert auth['explicit_human_authorization'] and auth['plan_sha256']==sha(PLAN)
    assert auth['proposal_sha256']==sha(PROPOSAL)
    assert auth['answer']=='Oui, exécuter l’observation détaillée A83'
    dump(OUT/'subsequent_A83_authorization.json',{'created_utc':now(),'authorization':rel(auth_path),
        'authorization_sha256':sha(auth_path),'receipt':auth['question_item'],
        'historical_preparation_preceded_approval':True,'A80_A81_publication_condition_now_verified':True})
    files=[p for folder in [OUT,PREP] for p in folder.rglob('*') if p.is_file() and p.suffix.lower()!='.f']+[CFG,PLAN,Path(__file__),HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'raw_AGPL_source_F_explicitly_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A82','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    entry.update(A83_subsequent_authorization_received=True,A83_authorization=rel(auth_path),
        A83_authorization_receipt=auth['question_item'])
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    authorized_route=route().replace('proposée non exécutée','autorisée non exécutée').replace(
        'Un nouvel accord explicite est requis :1Starter+1Engine A81consommés.',
        'Accord explicite A83 reçu ; publication A80+A81 vérifiée. Un seul Engine A83 autorisé ;1Starter+1Engine A81consommés.')
    s.update(current_iteration='AIRCRAFT-A82',next_iteration='AIRCRAFT-A83',current_status=a['status'],next_objective=authorized_route,updated_at=stamp)
    s['aircraft_a82_key_results']=entry;s['validated_artifacts'].update(aircraft_a82_report=rel(REPORT),aircraft_a82_results=rel(OUT/'composite_qualification_review.json'),aircraft_a82_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A82'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A82+AIRCRAFT-A83 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==201
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,'new_native':0,
        'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A83'})
    print(json.dumps({'A82_registered':True,'registry':201,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','register']);globals()[p.parse_args().action]()
