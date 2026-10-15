"""Seal the single second-trial observation and preserve the failed raw-DD gate."""
from run_aircraft_a89_second_attempt import ROOT,OUT,CFG,AUTH,PLAN,guard,read,dump,sha,now,rel,harness
from read_aircraft_a81_th_binary import decode
from pathlib import Path
import json

REPORT=OUT/'rapport_aircraft_a89.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A89_HANDOFF.md';PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A90_2026-10-15.md'

def route():
    return ('AIRCRAFT-A90 : après publication A88+A89 vérifiée, préparer en lecture seule une garde de correction '
        'nulle sur coordonnées libres projetées/condensées. A89 observeNCYCLE2/TT0,00025ms, tous modes admissibles, '
        'forces libres0,EIMP0,DE0=1e−20,U2=DU2=0 mais quatreDD Z imposés−1,90288107842e−9mm ; '
        'ALLDD brut exclut ce cas alors que la projection native est nulle. Ne pas supprimer la garde de correction : '
        'vérifier exactement son vecteur projeté pour rejeter un petit non-zéro dont le carré sous-déborde. '
        'Aucun nouveau correctif appliqué/compilé ; accord distinct requis. Un EngineA89consommé, aucun réessai, '
        'CHECK A87 inutilisé non réaffecté. Conserver toutes sorties, critères échoués, budgets et contacts bloquants. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')

def assess():
    c=guard();assert not REPORT.exists();d=OUT/c['case'];x=read(d/'normalization_observation.json');ex=read(d/'engine.execution.json')
    assert x['observation_complete'] and x['Engine_exit_code']==2 and ex['parent_exit_code']==0 and not ex['timed_out']
    cc=[e for e in x['events'] if e.get('event')=='CRIT_ITE_entry'];assert [(e['attempt'],e['iteration']) for e in cc]==[(2,1),(2,2)]
    norms=[e for e in x['events'] if e.get('event')=='PRODUT_UHP_return' and e['iteration']==2];assert len(norms)==2 and all(e['native_norm_squared']==0 for e in norms)
    expected_modes={'NCYCLE':2,'IRODDL':0,'NSPMD':1,'NUMNOD':8,'NFXVEL':4,'NINTER':0,'IDYNA':2,'IQSTAT':0,'INSOLV':1,'NITOL':123,'ISPRB':0,'IMCONV':0,'IDTC':1,'ILAST':0,'NTHREAD':1,'TT':.00025}
    for e in cc:
        v=e['values'];assert v['native_globals']==expected_modes and v['ICONT']==0 and v['NDDL']==8
        assert v['F_free']==[0.]*8 and v['DE0']==1e-20 and v['EIMP']==0 and v['R02']==1
        nz=[i for i,z in enumerate(v['DD_all24']) if z!=0];assert nz==[14,17,20,23]
        assert all(v['DD_all24'][i]==-1.90288107842e-9 for i in nz)
    assert cc[1]['UR']=='NaN' and all(e['ER']=='+Infinity' for e in cc)
    meta,a,flat=decode(d/(c['name']+'T01'));assert len(a['time'])==2
    checks={'second_attempt_and_cycle_time_native_confirmed':True,'all_guard_global_modes_observed':True,
        'ICONT_argument_native_read':True,'only_four_prescribed_Z_corrections_nonzero':True,
        'free_residual_exactly_zero':True,'native_projected_U2_DU2_zero':True,'energy_operands_confirmed':True,
        'same_nonfinite_criteria_and_native_stop':True,'bounded19_traps':x['trap_count']==19,
        'strictly_read_only_and_no_new_source_or_binary':True}
    assert all(checks.values())
    dump(OUT/'observation_review.json',{'created_utc':now(),'pass_observation':True,'physical_pass':False,'checks':checks,
        'native_modes':expected_modes,'native_ICONT':0,'native_DE0':1e-20,'native_EIMP':0,'native_U2_DU2':0,
        'nonzero_DD_zero_based_indices':[14,17,20,23],'nonzero_DD_mm':-1.90288107842e-9,
        'raw_ALL_DD_zero_is_false':True,'all_other_guard_conditions_from_native_or_explicit_source_reconstruction':True,
        'R2_zero_reconstructed_from_exactly_zero_F_not_directly_read':True,'IRIKS_zero_reconstructed_from_native_IDTC1_not_directly_read':True,
        'last_saved_coupon_time_ms':float(a['time'][-1,0]),'saved_nonzero_states':1,'global_second_attempt_time_ms':.00025,
        'second_attempt_is_not_accepted_saved_state':True,'stop_message':79,'ISTOP':-2,
        'observer_exit_code':0,'Engine_exit_code':2,'new_Engine':1,'new_Starter':0,'Engine_remaining':0,
        'console_A85_label_in_inherited_driver_is_cosmetic_actual_config_and_directory_A89':True})
    old=read(OUT/'preservation_before_metadata.json')['files']
    for r in old:
        st=(ROOT/r['path']).stat();assert st.st_size==r['bytes'] and st.st_mtime_ns==r['mtime_ns_before']
    for r in c['unchanged_software']:assert sha(ROOT/r['path'])==r['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'both_binaries_rehashed':True,'old_native_replayed':False})
    status='completed_authorized_second_trial_observation__raw_prescribed_DD_exclusion_identified__physical_stop_retained'
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A89','status':status,'explicit_authorization':c['authorization'],
        'new_Engine':1,'new_Starter':0,'Engine_remaining':0,'CPU_threads':1,'cap_s':180,'wall_s':ex['wall_s'],
        'observation_pass':True,'physical_pass':False,'native_NCYCLE':2,'native_TT_ms':.00025,
        'four_prescribed_Z_DD_nonzero_mm':-1.90288107842e-9,'raw_ALL_DD_zero_condition_false':True,
        'native_U2_and_DU2':0,'native_free_F_all_zero':True,'native_EIMP':0,'native_DE0':1e-20,
        'last_saved_coupon_time_ms':float(a['time'][-1,0]),'saved_nonzero_states':1,'stop_message':79,'ISTOP':-2,
        'source_patch_compilation_GPU_installation':False,'whole_dynamic_extension':False,
        'all_old_failed_gates_outputs_and_budgets_preserved':True,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A90'}
    dump(OUT/'scientific_assessment.json',assessment);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':assessment,'observation':rel(OUT/'observation_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text(f'''# AIRCRAFT-A89 — correction imposée non nulle, correction libre nulle

## 1. Faits directement observés ou transcrits

Accord « Oui, exécuter l’observation A89 », receipt request_user_input_async/call_983cb4f571c74eff9c7f88cff44ed49d/0 ; publication A86+A87 vérifiée. Un EngineA87 inchangé,CPU1/plafond180s, zéroStarter/correctif/compilation/GPU/installation. Durée{ex['wall_s']:.3f}s,19arrêts matériels. Lecteur code0, Engine code2 sans signal ; observation réussie et calcul physique échoué restent distincts.

Second essai réellement observé :NCYCLE2,TT0,00025ms. ModesIDYNA2,IQSTAT0,INSOLV1,NITOL123,ISPRB0,IDTC1,ILAST0,NFXVEL4,NINTER0,IRODDL0,NSPMD1,NTHREAD1,IMCONV0,ICONT0,NDDL8. F libre contient huit zéros exacts,DE0=1e−20,EIMP0,R02=1. NormesU2 etDU2 nativement0. D etDD ne sont non nuls que sur lesZ supérieurs imposés :DD=−1,90288107842e−9mm sur chacun, D=−1,328447181728e−8mm. Au critère2 :URNaN,RR0,ERInfinity ; arrêt79/ISTOP−2. Deux états réels restent sauvegardés, dernier0,000125ms ; le temps tenté0,00025ms n’est pas accepté.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La projection/condensation utilisée parPRODUT_UHP n’est pas une norme de toutes les coordonnées brutes. Les valeurs observées montrent ici un mouvement imposé avec norme libre nulle.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source inspectée/modifiée. Les sources logicielles privées restent épinglées et les deux binaires sont inchangés. Les libellés consoleA85 hérités du lanceur sont cosmétiques ; configuration, autorisation et répertoire réels sontA89, sans ambiguïté de budget.

## 4. Hypothèses propres au modèle

Graine1102112, zéro tirage, unitésg/mm/ms. R2=0 est reconstruit depuisF exactement nul avec la somme source sur un domaine ; la variable localeR2 n’a pas été directement lue. IRIKS=0 est reconstruit depuisIDTC1 selon la source, pas directement lu. Tous les autres paramètres de la garde sont mesurés. Aucun élargissement automatique de garde n’est autorisé.

## 5. Résultats dérivés

La conditionALL(DD brut==0) est fausse à cause des quatre corrections imposées ; les autres conditions sont admissibles et les normes libres restent nulles. Ce résultat explique l’exclusion par la garde actuelle, sans supposer un déséquilibre libre. Il faut tester exactement le vecteur de correction projeté/condensé plutôt que retirer tout contrôleDD : une petite composante libre non nulle peut avoir un carré sous-débordé et doit rester bloquante. Les dix contrôles de transcription/portée passent. Le nouvel observateur lit seulement les données et configure des registres matériels ; les points sont désactivés après le critère2 du second essai, puis le moteur termine selon son propre chemin.

## 6. Contradictions et informations manquantes

La boucle0,65ms, rupture et refermeture ne sont pas parcourues. Le seul EngineA89 est consommé, aucun réessai ; le CHECK conditionnelA87 inutilisé ne couvre aucun autre processus. Aucun nouveau correctif moteur n’est appliqué/compilé. Anciennes sorties, budgets, critères échoués, cinqTYPE25 ignorés et107391avertissements restent conservés. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A89 → AIRCRAFT-A90\n\nRapport : '+rel(REPORT)+'\nObservation : '+rel(OUT/'observation_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'observation_review.json')+' et '+rel(HANDOFF)+'.\nA89terminée,1Engineconsommé, aucun calcul en cours ; vérifierpublicationA88+A89.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[CFG,AUTH,Path(__file__),ROOT/'wtc1_simulation_v8/scripts/authorize_aircraft_a89.py',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_no_raw_AGPL':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A89_assessed':True,'observation_pass':True,'physical_pass':False,'NCYCLE':2,'TT_ms':.00025}),flush=True)

def register():
    guard();s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_iterations']==['AIRCRAFT-A88']
    m=read(OUT/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    a=read(OUT/'scientific_assessment.json');stamp=now();entry={'experiment_id':'WTC1-AIRCRAFT-A89','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A89',next_iteration='AIRCRAFT-A90',current_status=a['status'],next_objective=route(),updated_at=stamp);s['aircraft_a89_key_results']=entry
    s['validated_artifacts'].update(aircraft_a89_report=rel(REPORT),aircraft_a89_results=rel(OUT/'composite_qualification_review.json'),aircraft_a89_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A88','AIRCRAFT-A89'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A88+AIRCRAFT-A89 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cy)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==208
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,'native_observation_pass':True,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A90'})
    print(json.dumps({'A89_registered':True,'registry':208,'pending_publication':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
