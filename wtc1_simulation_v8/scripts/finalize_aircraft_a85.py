"""Seal raw native normalization observations; no retry or source correction."""
from run_aircraft_a85_normalization import ROOT,OUT,CFG,AUTH,PLAN,guard,read,dump,sha,now,rel,harness
from read_aircraft_a81_th_binary import decode
from pathlib import Path
import json,re,csv

REPORT=OUT/'rapport_aircraft_a85.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A85_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A86_2026-10-15.md'


def route():
    return ('AIRCRAFT-A86 : après publication A84+A85 vérifiée, préparer une réponse précise aux critères '
        'relatifs dégénérés observés, en lecture seule. A85 mesureDE0=1e−20,EIMP=0,RE=Infinity ; '
        'U2=DU2=0,LS3=1,RU=NaN à2 ; les huit composantesF libres sont exactement0. '
        'Le mouvement normal imposé existe dansD mais ne contribue pas à la norme des inconnues libres. '
        'Proposer un traitement borné des cas exactement nuls, sans neutraliser les critères non nuls ni masquer '
        'un déséquilibre ; définir témoins adverses et vérifications énergétiques avant accord distinct. '
        'Aucun correctif moteur appliqué ou compilé. Le seul EngineA85 est consommé, zéro Starter, aucun réessai. '
        'Les captures natives s’arrêtent à2 ; la suite est seulement imprimée. Compression, rupture et refermeture '
        'restent non mesurées ; tous échecs, anciennes sorties et budgets conservés. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def assess():
    c=guard();assert not REPORT.exists();d=OUT/c['case'];x=read(d/'engine.execution.json')
    native=read(d/'normalization_observation.json');assert native['observation_complete'] and native['Engine_exit_code']==2 and x['parent_exit_code']==0 and not x['timed_out']
    entries=[e for e in native['events'] if e.get('event')=='NL_SOLV_entry']
    criteria=[e for e in native['events'] if e.get('event')=='CRIT_ITE_entry']
    norms=[e for e in native['events'] if e.get('event')=='PRODUT_UHP_return']
    assert [e['iteration'] for e in entries]==[0,1,2] and [e['iteration'] for e in criteria]==[1,2]
    assert [(e['iteration'],e['role']) for e in norms]==[(0,'D'),(2,'D'),(2,'DD')]
    checks={'all_raw_entries_and_criteria_present':True,'native_norm_return_domains_present':True,
        'free_residual_components_exactly_zero':all(e['values']['F_free']==[0.0]*8 for e in entries+criteria),
        'reference_force_squared_exactly1':all(e['values']['R02']==1 for e in entries+criteria),
        'cumulative_energy_exactly_zero':all(e['values']['EIMP']==0 for e in entries+criteria),
        'previous_energy_increment_floor_exactly1e20':all(e['values']['DE0']==1e-20 for e in criteria),
        'energy_ratio_infinite_at_criteria1and2':all(e['ER']=='+Infinity' for e in criteria),
        'native_U2_DU2_exactly_zero':all(e['native_norm_squared']==0 for e in norms),
        'line_search_factor1_at_iteration2':criteria[1]['values']['LS'][2]==1,
        'displacement_ratio_NaN_at2':criteria[1]['UR']=='NaN',
        'all_increment_components_zero':all(e['values']['DD_all24']==[0.0]*24 for e in entries+criteria),
        'normal_prescribed_movement_present':all(e['values']['D_all24'][3*n+2]==-1.90288107842e-9 for e in entries+criteria for n in range(4,8)),
        'eleven_bounded_traps_then_native_error_stop':native['trap_count']==11 and native['Engine_terminal_signal'] is None}
    listing=d/(c['name']+'_0001.out');text=listing.read_text(encoding='utf8',errors='replace')
    checks['same_native_timestep_limit_and_max_iterations']='ISTOP=-2' in text and 'MAX_ITER REACHED' in text
    checks['all_tolerances_and_step_bounds_unchanged']=c['fixed_dt_min_max_ms']==[.000125,.000125] and c['three_tolerances']==1e-11
    meta,arrays,flat=decode(d/(c['name']+'T01'));assert len(arrays['time'])==1 and arrays['time'][0,0]==0
    checks['actual_saved_state_only_time_zero']=True
    assert all(checks.values())
    rows=[]
    for e in criteria:
        v=e['values'];rows.append({'iteration':e['iteration'],'DE0_native':v['DE0'],'EIMP_native':v['EIMP'],'R02_native':v['R02'],
            'F_squared_recomputed_from_read_vector':sum(f*f for f in v['F_free']),'UR_native':e['UR'],'RR_native':e['RR'],'ER_native':e['ER']})
    with (OUT/'normalization_summary.csv').open('x',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    dump(OUT/'observation_review.json',{'created_utc':now(),'pass_observation':True,'physical_pass':False,'checks':checks,
        'criteria':rows,'native_norm_squared_samples':norms,'force_squared_recomputed_is_derived_not_read_local_R2':True,
        'DE0_raw_before_floor_not_captured':True,'native_internal_energy_EIMP_is_not_total_physical_energy':True,
        'source_equations_confirmed_by_operands_and_outputs':True,'strict_zero_case_observed_only_first_trial':True,
        'global_cycle_time_not_observed_or_promised':True,'read_only_breakpoints_disabled_after_criterion2':True,
        'last_saved_coupon_time_ms':0,'saved_nonzero_states':0,'TH_schema':meta,
        'Engine_exit_code':2,'observer_exit_code':0,'Engine_remaining':0,'new_Engine':1,'new_Starter':0,
        'preserved_warnings':['PARITH/ON incompatible with implicit','ISOLID0 generic stiffness'],
        'stop_message':79,'ISTOP':-2,'no_new_native_or_converter_for_analysis':True})
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[]
    for row in old:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed
    for row in c['unchanged_software']:assert sha(ROOT/row['path'])==row['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),
        'changed_paths':changed,'both_binaries_rehashed':True,'old_native_replayed':False})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A85',
        'status':'completed_authorized_raw_normalization_observation__zero_denominators_native_confirmed__physical_stop_retained',
        'explicit_authorization':c['authorization'],'new_Engine':1,'new_Starter':0,'Engine_remaining':0,
        'CPU_threads':1,'cap_s':180,'wall_s_including_launcher':x['wall_s'],'observer_native_wall_s':native['wall_s'],
        'observer_exit_code':0,'Engine_exit_code':2,'observation_pass':True,'physical_pass':False,
        'native_DE0_iterations1and2':1e-20,'native_EIMP':0,'native_R02':1,'free_F_eight_entries_exactly_zero':True,
        'native_U2_and_DU2_iteration2':0,'native_LS3_iteration2':1,'native_ER':'+Infinity','native_UR_iteration2':'NaN',
        'all24_correction_DD_components_zero':True,'imposed_top_Z_increment_present_mm':-1.90288107842e-9,
        'raw_pre_floor_DE_not_captured':True,'trap_count':11,'no_numeric_code_or_general_register_patch':True,
        'saved_nonzero_time_states':0,'last_saved_coupon_time_ms':0,'stop_message':79,'ISTOP':-2,
        'compression_rupture_reclosure_remain_unmeasured':True,'source_patch_compilation_GPU_installation':False,
        'whole_dynamic_extension':False,'all_prior_failed_gates_outputs_and_budgets_preserved':True,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A86'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'observation':rel(OUT/'observation_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text(f'''# AIRCRAFT-A85 — dénominateurs nuls directement mesurés

L’observation autorisée réussit. Les opérandes internes confirment les deux divisions dégénérées ; le calcul physique reste arrêté au premier essai et aucune trajectoire de compression/rupture/refermeture n’est qualifiée.

## 1. Faits directement observés ou transcrits

Accord « Oui, exécuter l’observation A85 », receipt request_user_input_async/call_61565801d9904c9cb78dcc622dc9c5d6/0. Publication A82+A83 vérifiée avant déclaration. Un EngineCPU1/plafond180s, zéro Starter, correctif, compilation, GPU, installation ou extension entière. Durée totale avec lancement{x['wall_s']:.3f}s ; observation/processus natif{native['wall_s']:.3f}s. Le lecteur retourne0, mais l’Engine retourne2 sans signal terminal : ces statuts sont distincts. Onze arrêts matériels bornés ; captures aux entréesNL_SOLV0,1,2, critères1,2 et retours des normesD0,D2,DD2. Les points sont désactivés après le critère2 ; le moteur poursuit vers son propre arrêt.

Aux critères1et2 : DE0=1e−20, EIMP=0, R02=1, les huit composantesF libres exactement0 et ER=+Infinity. À2 : U2=0 et DU2=0 au retour natif dePRODUT_UHP, LS3=1, UR=NaN. Toutes les24composantesDD sont nulles ; D contient cependant−1,90288107842e−9mm sur les quatreZ supérieurs imposés. L’Engine imprime à nouveau maximum30, MESSAGE79/ISTOP−2, ainsi que les avertissementsPARITH/ON etISOLID0.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La source logicielle épinglée définitRE=DE0/EIMP etRU=LS3*sqrt(DU2/U2), et remonte les très petitsDE0 à1e−20. Ces équations et les opérandes réellement lus expliquent les valeurs non finies du cas observé. La norme porte sur des coordonnées libres condensées ; elle peut être nulle alors que des coordonnées imposées bougent.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo ou photographie réanalysée ou modifiée. Aucun ancien solveur rejoué. Les sources logicielles privées restent distinctes et aucun binaire n’est modifié.

## 4. Hypothèses propres au modèle

Graine1102107, zéro tirage, unitésg/mm/ms et toutes cartes/tolérances/bornes de pas conservées. La capture valide ce cas de normalisation au premier essai seulement. Le temps/cycle global n’a pas été observé ni promis. LeDE antérieur brut avant plancher n’est pas capturé ;DE0=1e−20 est la valeur effectivement consommée par le critère. EIMP est une variable d’algorithme, pas l’énergie physique totale du coupon ou le travail de la commande imposée.

## 5. Résultats dérivés

Les divisions1e−20/0 et0/0 sont maintenant établies pour les critères correspondants, au lieu d’une hypothèse tirée du seul affichageInfinity/NaN. Le carré deF recalculé depuis ses huit composantes lues vaut0 ; il est explicitement étiqueté dérivé et n’est pas présenté comme la variable localeR2 directement lue. Les16contrôles de transcription/portée passent. La lecture TH sauvegardée donne un unique état réel à0ms, sans nouveau convertisseur. L’addendumA84 sur la ligne0 absolue reste applicable : seules les lignes positives impriment les ratios normalisés.

## 6. Contradictions et informations manquantes

La réussite de l’observation ne vaut pas convergence ni validation physique. Le seul EngineA85 est consommé, aucun remplacement ni réessai. Compression, rupture, refermeture, impulsions de plateau, travail de fracture et peuplementUSR restent non mesurés. Avant tout traitement des cas nuls, il faut définir les gardes, empêcher un faux succès sur valeurs non nulles/non finies et contrôler l’énergie indépendante. Aucun correctif moteur n’est encore appliqué ou compilé. Toutes anciennes sorties, budgets, échecs et107391avertissements A73 conservés. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A85 → AIRCRAFT-A86\n\nRapport : '+rel(REPORT)+'\nObservation : '+rel(OUT/'observation_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(OUT/'observation_review.json')+' et '+rel(HANDOFF)+'.\nA85terminée,1Engineconsommé, zéroStarter, aucun calcul en cours. Vérifier publication A84+A85.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,AUTH,Path(__file__),ROOT/'wtc1_simulation_v8/scripts/authorize_aircraft_a85.py',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_no_raw_AGPL':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A85_assessed':True,'observation_pass':True,'physical_pass':False,'saved_time_ms':0,'checks':len(checks)}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert cycle['pending_iterations']==['AIRCRAFT-A84']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A85','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A85',next_iteration='AIRCRAFT-A86',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a85_key_results']=entry;s['validated_artifacts'].update(aircraft_a85_report=rel(REPORT),aircraft_a85_results=rel(OUT/'composite_qualification_review.json'),aircraft_a85_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A84','AIRCRAFT-A85'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A84+AIRCRAFT-A85 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==204
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,
        'files_verified':len(m['files']),'native_observation_pass':True,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A86'})
    print(json.dumps({'A85_registered':True,'registry':204,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
