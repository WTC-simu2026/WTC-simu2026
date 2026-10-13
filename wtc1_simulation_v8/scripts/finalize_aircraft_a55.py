"""Seal new A55 native failures and precise scratch proposal without replay."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,re,hashlib

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a55'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a55_predeclaration.json'
REPORT=OUT/'rapport_aircraft_a55.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A55_HANDOFF.md'

def route():
    return ('AIRCRAFT-A56 : accord explicite reçu le13octobre pour le nouveau correctif A55 du tampon SMSTR temporaire TYPE43, '
      'patch a0d52993240ac373a726185b2a3400d447bd947a59aa483b7f60e45c2bdc8503, source alloc_elbuf_imp.F seulement ; '
      'préserver le correctif de graphe A53, source figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a. '
      'Compiler un quatrième moteur isolé a56_type43_scratch_candidate, une heure maximum/sixCPU/sansGPU ni installation, puis contrôles natifs capacité/mémoire et cohésion implicite chargée, '
      'graphe/CHECK et régressions explicites/TYPE7 avec critères inchangés et180s par processus. '
      'A55 :16Engine,10Starter dont4échecs de configuration conservés, aucun temps physique chargé ; corruption malloc directement écrite par SRCOORK surTYPE43, '
      'insuffisance de capacité inférée du contrat SAV(NEL,21) et allocation NEL*G_SMSTR ; capacité native G_SMSTR non lue. '
      'La suppression de la corruption ne qualifiera pas les lois, les15erreurs CHECK entières ni les5TYPE25 ignorés. '
      'Le contrôle solide ordinaire termine mais conserve1erreur de matrice définie positive. '
      'A52 non intégré, budgets et tous échecs conservés, aucune RKE compensatoire. Meilleur impact entier A20=0,0200001220703125s ; '
      'objectif1 dix secondes physiques puis vidéo3D toujours incomplet. Publication A54+A55 à vérifier avant remise à zéro de la cadence.')

def assess():
    config=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A54'
    engines=[]
    for p in sorted(OUT.rglob('engine.execution.json')):
        v=read(p);d=p.parent;log=(d/'engine.log').read_text(errors='replace')
        observer=next((d/name for name in ['heap_watch_result.json','abort_trace_result.json'] if (d/name).exists()),None)
        result=read(observer) if observer else {}
        engine_exit=result.get('Engine_exit_code',v['parent_exit_code'])
        engines.append({'path':rel(p),**v,'actual_Engine_exit_code':engine_exit,
          'observer_exit_is_not_engine_exit':bool(observer),'normal_termination':'NORMAL TERMINATION' in log,
          'abort_invalid_pointer':'free(): invalid pointer' in log,
          'last_physical_time_ms':float(re.findall(r'NC=\s*\d+ T=\s*([\d.E+-]+)',log)[-1]) if re.findall(r'NC=\s*\d+ T=\s*([\d.E+-]+)',log) else None,
          'CHECK_errors':int(re.findall(r'(\d+) ERRORS',log)[-1]) if re.findall(r'(\d+) ERRORS',log) else None,
          'zero_volume_messages':log.count('ZERO OR NEGATIVE VOLUME')})
    starters=[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('starter.execution.json'))]
    assert len(engines)==16 and len(starters)==10
    assert sum(row['actual_Engine_exit_code']==3 for row in engines)==15
    assert sum(row['exit_code']==2 for row in starters)==4 if all('exit_code' in row for row in starters) else sum(row.get('exit_code',row.get('parent_exit_code'))==2 for row in starters)==4
    assert all(row['CPU_threads']==1 and row['cap_s']==180 for row in engines)
    ordinary=next(row for row in engines if 'CHECK_POSITIVE_VOLUME_SOLIDS' in row['path'])
    assert ordinary['normal_termination'] and ordinary['CHECK_errors']==1 and ordinary['zero_volume_messages']==0
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'native_Engine_executions':16,'fresh_Starter_launches':10,'Starter_reader_configuration_failures':4,'parsed_Starter_cases':6,
       'engines':engines,'starters':starters,'old_native_solver_replays':0,'GPU':False,'new_build_or_installation':False})
    heap=read(OUT/'ACTIVE_COHESIVE_HEAP_WATCH_R2/heap_watch_result.json')
    events=heap['events'];ctx=heap['SRCOORK_contexts'];assert len(ctx)==1 and ctx[0]['NEL']==1
    write=next(v for v in events if v['bits']==2);assert write['watched_header_now']=='0x0'
    assert write['store_destination_from_R8_RAX']==hex(int(events[0]['pointer'],16)-8)
    assert events[0]['watched_header_now']=='0x31' and heap['Engine_exit_code']==3
    dump(OUT/'native_memory_corruption_review.json',{'created_utc':now(),'binary_sha256':config['binary_sha256'],
       'native_memory_writer_proven':True,'allocation_header_before':'0x31','header_after':'0x0',
       'instruction_after_store':'0x8decc8','store_instruction':'0x8decc1','function':'SRCOORK+0x4488','destination_matches_NODREAC_header':True,
       'actual_context':ctx,'abort_after_same_corrupted_pointer_free':True,'source_capacity_contract_inference':True,
       'native_G_SMSTR_descriptor_capacity_read':False,'all_other_failures_explained':False,'physical_law_qualified':False})
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    assert sha(ROOT/config['candidate_directory']/'isolated_exec/engine_linux64_gf_ompi')==config['binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),'changed_paths':changed,
      'old_content_rehashed':False,'prior_SHA256_manifests_preserved':True,'A54_binary_fresh_hash_pass':True,'archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A55','status':'completed_native_implicit_cohesive_abort_localization_and_new_scratch_proposal__physical_response_not_obtained',
       'native_Engine_executions':16,'Starter_launches':10,'Starter_config_failures_preserved':4,'parsed_Starter_cases':6,
       'implicit_cohesive_native_Engine_failures':15,'implicit_cohesive_loaded_mechanical_gate_pass':False,
       'ordinary_solid_CHECK_normal_termination':True,'ordinary_solid_CHECK_errors':1,'ordinary_solid_zero_volume_messages':0,
       'heap_header_corruption_native_writer_proven':True,'SRCOORK_TYPE43_context_observed':True,'scratch_capacity_defect_source_inference':True,
       'native_scratch_capacity_not_read':True,'new_patch_applied':False,'new_engine_compiled':False,
       'new_patch_preparatory_arithmetic_cases_passed':48,'explicit_new_patch_authorization_received':True,
       'same_A54_binary_preserved':True,'mass_or_material_budgets_changed':False,'RKE_compensation_added':False,
       'old_outputs_and_failed_gates_preserved':True,'whole_CHECK_mechanical_gate_pass':False,'implicit_TYPE25_qualified':False,
       'A52_integrated':False,'whole_insertion_ready':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,
       'objective1_complete':False,'next_iteration':'AIRCRAFT-A56'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'runtime':'runtime_manifest.json','corruption':'native_memory_corruption_review.json','proposal':'smstr_patch_proposal_review.json','physical_qualification':False,'failed_or_inconclusive_attempts_retained':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A55 — corruption mémoire localisée, cohésion implicite non qualifiée

Le moteur A54 inchangé s'arrête avant la charge dans les témoins cohésifs implicites. Une surveillance native établit l'écriture qui corrompt un en-tête mémoire, puis sa libération échoue. Un nouveau correctif limité au tampon temporaire est préparé ; l'accord explicite reçu couvre sa future application et compilation A56. Aucun temps physique entier supplémentaire n'est obtenu.

## 1. Faits directement observés ou transcrits

Seize nouveaux Engine, un CPU, plafond180s, aucun calcul GPU. Quinze s'arrêtent code3 à NC=0/T=0 avec free(): invalid pointer ; les lanceurs observateurs terminent0 mais le code Engine reste3. Le CHECK solide ordinaire termine normalement, sans volume nul, mais garde1erreur de matrice définie positive : ce n'est pas un CHECK propre. Aucun ancien Engine rejoué.

Quatre témoins implicites initialement prescrits échouent. Quatre variantes libérant des déplacements transversaux non chargés échouent aussi ; leurs quatre premières préparations avaient échoué à la lecture de configuration Starter, conservées dans leur dossier initial. R1 utilise l'environnement déjà établi et quatre Starter propres. Deux autres contrôles ne changent que les sorties nodales (sans réaction, puis sans bloc nodal) : deux Starter propres, deux arrêts identiques. Dix lancements Starter au total, quatre échecs de configuration et six préparations sans erreur ni avertissement. Les hypothèses simples de contrainte complète et de sortie nodale ne résolvent pas l'arrêt.

La capture SIGABRT déroule15trames CFI puis conserve honnêtement l'arrêt sur règle non prise en charge. RESOL libère NODREAC. La surveillance matérielle observe son allocation alignée, en-tête0x31, puis une écriture SRCOORK+0x4488 qui remplace cet en-tête par0 avant free/SIGABRT. R1 n'avait pas capturé le contexte SRCOORK car la sonde désactivait son propre point d'entrée ; cette observation incomplète reste conservée. R2 corrige uniquement l'observateur : un appel, NEL=1, IGTYP=43, ISMSTR=1, JHBE=0, JCVT=1, connectivité1..8. La destination calculée par les registres correspond exactement à l'en-tête surveillé. Aucune instruction mécanique ni tableau du moteur n'est modifié par la sonde.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel. Le binaire A54 SHA256 c4a18b981b9beb461fbb570a12d5ef04aa9a97293c61875c9d458ea99579d3b2 reste intact. Le logiciel figé déclare SAV(NEL,21) dans SRCOORK ; S8ZKE3 transmet GBUF%SMSTR et l'allocation temporaire implicite utilise NEL*G_SMSTR. Sources archivées en lecture seule ; aucune installation, application de patch ni compilation A55.

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive, photographie, vidéo ou PDF historique consulté. Les sources et les anciennes sorties sont préservées. Les dégâts connus ne constituent pas une cible.

## 4. Hypothèses propres au modèle

Graine1102080, aucun tirage ; unités g/mm/ms, conversion Nmm vers J=0,001. Les variantes de supports et de sorties sont déclarées séparément ; masses, matériaux et budgets ne changent pas. L'insuffisance de capacité du tampon est inférée du contrat source et de l'écriture observée ; la capacité native G_SMSTR n'a pas été lue. Cette inférence ne prouve pas la compatibilité physique implicite des TYPE43.

## 5. Résultats dérivés

La proposition réserve au moins21*NEL valeurs dans le SMSTR temporaire TYPE43 uniquement et initialise si l'allocation réussit. Source/restart et autres types restent inchangés.48cas arithmétiques/bornes et72colonnes passent ; aucun contrôle Fortran compilé n'est revendiqué. La première proposition utilisant ZERO absent de la portée est conservée ; R1 emploie0.0D0. Les sources dérivées et patch AGPL restent hors du manifeste public MIT ; proposition, empreintes et scripts propres sont publiables. Accord humain reçu distinctement pour ce correctif, quatrième moteur isolé, plafond1h/sixCPU, puis contrôles bornés180s.

Préservation vérifiée par métadonnées et manifestes antérieurs, hash neuf du binaire A54, harnais PASS. L'intégrité de cette itération ne constitue pas un passage des critères physiques.

## 6. Contradictions et informations manquantes

Aucune réponse cohésive implicite chargée, énergie, traction, rechargement ou demi-pas obtenue. Aucun résultat à convertir en vidéo3D nouvelle. Le CHECK entier A54 garde15erreurs,624messages de volume et5TYPE25 ignorés. Les critères échoués, y compris l'erreur du témoin solide, restent conservés. A52 non intégré ; contacts entiers, inerties/travaux et couverture énergétique manquent encore. La meilleure fenêtre entière reste0,0200001220703125s ; dix secondes physiques et leur vidéo restent incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A55 → AIRCRAFT-A56\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(OUT/'proposition_correctif_tampon_cohesif.md')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a55*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'source_and_patch_AGPL_outside_public_MIT_manifest':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A55_assessed':True,'Engine_executions':16,'objective1_complete':False}),flush=True)

def register():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json')
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A55','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A55',next_iteration='AIRCRAFT-A56',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a55_key_results']=row
    state['validated_artifacts'].update(aircraft_a55_report=rel(REPORT),aircraft_a55_results=rel(OUT/'composite_qualification_review.json'),aircraft_a55_handoff=rel(HANDOFF))
    assert cycle['pending_iterations']==['AIRCRAFT-A54']
    cycle.update(pending_iterations=['AIRCRAFT-A54','AIRCRAFT-A55'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A54+AIRCRAFT-A55 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==174
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':len(m['files']),'harness':h,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A56'})
    print(json.dumps({'A55_registered':True,'registry_entries':174,'pending_publication_count':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
