"""Seal the exact approved original-buffer fix, keeping the geometry stop failed."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,re,ast
import numpy as np

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a57'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a57_predeclaration.json'
REPORT=OUT/'rapport_aircraft_a57.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A57_HANDOFF.md'

def route():
    return ('AIRCRAFT-A58 : moteur A57 compilé et contrôlé, SHA25634eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528, '
      'a57_original_type43_scratch_candidate ; accords A53 graphe/A55 temporaire/A56 original tous distincts enregistrés. '
      'Capacité native originale21 pourNEL1, pointeur identique àSAV, en-tête NODREAC0x31 intact au retour ; corruption observée levée dans ce témoin. '
      'Dix-sept nouveaux Engine code0/NORMAL, aucun Starter ; cela ne qualifie pas la réponse chargée : quatre témoins implicites restentT=0, STOP volume nul puisUSER BREAK, CSV vides, échec de lecteur conservé. '
      'CHECK cohésif isolé5erreurs/unvolume, solide ordinaire1erreur de matrice ; entier15erreurs/624volumes/cinqTYPE25 ignorés. '
      'Graphe256opérations,3024attaches exactes, quatre témoins explicites et deuxTYPE7/bilans etdemi-pas passent,600champs sous règle de précision préexistante. '
      'Prochaine étape : examiner et vérifier la chaîne géométrie/tangente implicite du TYPE43/LAW117 et les contacts entiers avant de proposer un traitement de surface. '
      'Les sources déjà ciblées S8ZKE3→S8ZDERICT3→SCHKJAB3 montrent un jacobien volumique ; MMATS/MMSTIFS nécessitent audit de compatibilité. '
      'Ne pas supprimer le STOP, inventer une épaisseur pour le contourner ou déclarer NORMAL comme réponse physique. '
      'Inspections et nouveaux contrôles de cas bornés avec le même binaire sont autorisés ; toute nouvelle modification du logiciel exige une proposition concrète et un accord distinct. '
      'A52 reste non intégré ; budgets, anciennes sorties et échecs conservés, zéroRKE compensatoire. Meilleur impact entierA20=0,0200001220703125s, objectif1 dix secondes physiques puis vidéo3D incomplet. '
      'Cadence A56+A57 à publier/vérifier ; ne pas rejouer les anciens Engine.')

def assess():
    assert not REPORT.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A56'
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    built=read(OUT/'build_finished.json');assert built['build_success'] and built['exact_A56_original_scratch_patch_applied']
    runs=[]
    for p in sorted(OUT.rglob('engine.execution.json')):
        v=read(p);log=(p.parent/'engine.log').read_text(encoding='utf8',errors='replace')
        observed=next((p.parent/n for n in ['scratch_watch_result.json','allocation_trace_result.json','graph_binding_trace_result.json','optimized_add_trace_result.json'] if (p.parent/n).exists()),None)
        actual=read(observed) if observed else {};times=re.findall(r'NC=\s*\d+ T=\s*([\d.E+-]+)',log);cycles=re.findall(r'TOTAL NUMBER OF CYCLES\s*:\s*(\d+)',log)
        runs.append({'path':rel(p),**v,'actual_Engine_exit_code':actual.get('Engine_exit_code',v['parent_exit_code']),'normal_termination':'NORMAL TERMINATION' in log,'last_time_ms':float(times[-1]) if times else None,'cycles':int(cycles[-1]) if cycles else None,'USER_BREAK':'USER BREAK' in log,'zero_volume_STOP':'STOP: ZERO OR NEGATIVE VOLUME' in log,'CHECK_errors':int(re.findall(r'(\d+) ERRORS',log)[-1]) if re.findall(r'(\d+) ERRORS',log) else None})
    assert len(runs)==17 and all(v['cap_s']==180 and v['CPU_threads']==1 and v['actual_Engine_exit_code']==0 and v['normal_termination'] for v in runs)
    assert not list(OUT.rglob('starter.execution.json'))
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'native_Engine_executions':17,'Starter_launches':0,'executions':runs,'new_build':built,'old_native_Engine_replays':0,'GPU':False,'normal_code_zero_is_not_physical_pass':True})
    alloc=read(OUT/'ACTIVE_COHESIVE_ALLOCATION_TRACE/allocation_trace_result.json');c=alloc['SRCOORK_context'];matched=c['matching_allocations'];assert len(matched)==1
    m=matched[0];assert m['label']=='ELBUF_STR%GBUF%SMSTR' and m['requested_values']==21*c['NEL'] and m['native_capacity']>=21*c['NEL'] and m['element_bytes']==8
    scratch=read(OUT/'ACTIVE_COHESIVE_SCRATCH_WATCH/scratch_watch_result.json');s=scratch['SRCOORK_contexts'][0]
    assert s['return_observed'] and s['NODREAC_header']==s['NODREAC_header_at_return']=='0x31' and scratch['Engine_exit_code']==0
    dump(OUT/'native_allocation_memory_review.json',{'created_utc':now(),'capacity_pointer_identity_gate_pass':True,'original_allocation':m,'SAV_pointer':c['SAV_pointer'],'NEL':c['NEL'],'IGTYP':c['IGTYP'],'NODREAC_header_entry_and_return':'0x31','observed_corruption_regression_gate_pass':True,'source_contract_and_native_descriptor_agree':True,'scope':'Observed TYPE43/NEL1 case only; no all-program memory-safety claim','implicit_loaded_mechanical_gate_pass':False})
    implicit=[]
    for p in sorted((OUT/'implicit_cohesive_controls').rglob('engine.execution.json')):
        r=next(v for v in runs if v['path']==rel(p));csvs=list(p.parent.glob('*T01.csv'));histories=[{'path':rel(q),'bytes':q.stat().st_size,'sha256':sha(q)} for q in p.parent.glob('*T01')]
        assert r['last_time_ms']==0 and r['USER_BREAK'] and r['zero_volume_STOP'] and len(csvs)==1 and csvs[0].stat().st_size==0
        implicit.append({'case':p.parent.name,'run':r,'CSV_bytes':0,'native_histories':histories,'loaded_response_obtained':False,'physical_gate_pass':False})
    assert len(implicit)==4
    dump(OUT/'implicit_loaded_response_review.json',{'created_utc':now(),'cases':implicit,'memory_abort_removed':True,'physical_completion_pass':False,'work_energy_and_traction_pass':False,'empty_history_reader_StopIteration_retained':True,'no_native_solver_rerun_for_analysis':True})
    oracle=read(OUT/'WHOLE_OPTIMIZED_GRAPH_SET_TRACE/optimized_add_trace_result.json');assert oracle['native_observed_graph_set_gate_pass']
    prior=read(ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_ORIGINAL_TYPE2_BINDING_TRACE/type2_trace_result.json');flatten=lambda calls:{b['secondary_original_label']:b for call in calls for b in call['bindings']};baseline=flatten(prior['calls']);rows=[]
    for name in ['WHOLE_ORIGINAL_CORRECTED_GRAPH','WHOLE_PAIRED_CORRECTED_GRAPH']:
        d=OUT/name;v=read(d/'graph_binding_trace_result.json');bindings=flatten(v['TYPE2_calls']);assert len(bindings)==3024
        checks={k:all(baseline[n][k]==bindings[n][k] for n in baseline) for k in ['mode','main_original_labels_ordered','native_NDOF','native_parameter_values','native_point_coordinates_mm']}
        log=(d/'engine.log').read_text(encoding='utf8');rows.append({'case':name,'binding_checks':checks,'binding_pass':all(checks.values()),'CHECK_errors':int(re.findall(r'(\d+) ERRORS',log)[-1]),'zero_volume_messages':log.count('ZERO OR NEGATIVE VOLUME'),'TYPE25_ignored':log.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),'missing_connectivity_messages':log.count('CONNECTIVITY BETWEEN NODES')})
    assert all(v['binding_pass'] and v['CHECK_errors']==15 and v['TYPE25_ignored']==5 and v['missing_connectivity_messages']==0 for v in rows)
    dump(OUT/'whole_graph_binding_review.json',{'created_utc':now(),'cases':rows,'graph_oracle_pass':True,'all_bindings_exact':True,'whole_mechanical_CHECK_pass':False,'A52_integrated':False})
    cohesive=read(OUT/'cohesive_controls/cohesive_review.json');contact=read(OUT/'contact_controls/contact_review.json');assert cohesive['mechanical_implementation_gate_pass'] and contact['pass']
    from probe_aircraft_a37 import vtk
    from assess_aircraft_a23_reader_precision import printed_bound
    fields=[]
    for case in contact['cases']:
        d=OUT/'contact_controls'/case['case'];raw=read(d/'review.json');X=np.asarray(read(d/'generation.json')['nodes_mm'])
        for row in raw['fields']:
            f=vtk((ROOT/row['path']).read_text());order=np.argsort(f['NODE_ID']);p=f['points'].reshape(-1,3)[order];u=f['Displacement'].reshape(-1,3)[order]
            bound=printed_bound(p)+printed_bound(u)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(p),abs(u),abs(X)])+1e-8
            checks={k:v for k,v in row['checks'].items() if k!='coordinate_displacement'};checks['coordinate_identity_source_print_bound']=bool(np.all(abs(p-X-u)<=bound));fields.append({'path':row['path'],'raw_literal_gate':row['checks']['coordinate_displacement'],'checks':checks,'pass':all(checks.values())})
    assert len(fields)==600 and all(v['pass'] for v in fields)
    dump(OUT/'contact_field_format_review.json',{'created_utc':now(),'fields':fields,'pass':True,'same_preexisting_A23_precision_rule':True,'raw_literal_failures_preserved':True,'physical_tolerances_changed':False})
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    assert sha(ROOT/built['candidate_directory']/'isolated_exec/engine_linux64_gf_ompi')==built['binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),'changed_paths':changed,'old_hash_manifests_preserved':True,'all_old_files_rehashed':False,'new_binary_fresh_hash_pass':True,'archives_not_rescanned':True})
    summary='Capacité native originale21/NEL1 et pointeur SAV exact, en-tête mémoire intact ; les quatre témoins implicites restent àT=0 avecSTOP volume nul etUSER BREAK. Graphe/attaches, quatre témoins explicites et deuxTYPE7 passent dans leur domaine, physique entière toujours non qualifiée.'
    a={'created_utc':now(),'iteration':'AIRCRAFT-A57','status':'completed_authorized_original_scratch_build_and_native_memory_regression__zero_height_implicit_geometry_STOP_remains',
       'new_engine_binary_sha256':built['binary_sha256'],'build_success':True,'original_scratch_patch_applied':True,'native_Engine_executions':17,'Starter_launches':0,
       'native_original_SMSTR_capacity':21,'native_original_SMSTR_requested_values':21,'native_original_SMSTR_element_bytes':8,'native_original_pointer_matches_SAV':True,'observed_native_memory_corruption_removed':True,
       'normal_exit_zero_Engine_count':17,'implicit_loaded_cases_stopped_at_zero':4,'implicit_loaded_mechanical_gate_pass':False,'isolated_cohesive_CHECK_errors':5,'isolated_cohesive_zero_volume_messages':1,'ordinary_solid_CHECK_errors':1,
       'graph_operations_pass':256,'native_bindings_exact':3024,'whole_CHECK_errors':15,'whole_zero_volume_messages':624,'TYPE25_ignored':5,'native_explicit_cohesive_cases_pass':4,'TYPE7_contact_cases_pass':2,'contact_fields_source_precision_pass':600,
       'old_outputs_and_failed_gates_preserved':True,'budgets_changed':False,'RKE_added':False,'new_unapproved_software_correction_applied':False,'A52_integrated':False,'whole_insertion_ready':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A58','qualification_summary_fr':summary}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'memory':'native_allocation_memory_review.json','implicit':'implicit_loaded_response_review.json','graph':'whole_graph_binding_review.json','cohesive':'cohesive_controls/cohesive_review.json','contact':'contact_controls/contact_review.json','physical_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A57 — allocation d'origine corrigée, arrêt géométrique implicite conservé

Le cinquième moteur isolé applique le correctif d'origine explicitement autorisé. La capacité native du tampon réellement transmis est21 pourNEL1, l'en-tête mémoire reste intact et l'ancien abort disparaît dans le témoin observé. Les cohésifs implicites s'arrêtent toutefois à zéro seconde sur le volume nul. Aucun temps physique d'impact entier supplémentaire.

## 1. Faits directement observés ou transcrits

Accord humain distinct enregistré : « Oui, appliquer et compiler ce correctif d'origine ». Les trois corrections exactes autorisées sont appliquées à une nouvelle copie : grapheA53, tampon temporaireA55, tampon original proposéA56. Sources/dépendances cachées vérifiées avant correction, compilation/export en environ285s, plafond1h/sixCPU, sans GPU ni installation. Anciens moteurs conservés, espace ext4 démonté. Binaire34eb01b358869b4acd34a6204ec29083b95530d62ff6d7f2c9e43d20a90ef528.

Dix-sept nouveaux Engine, aucun Starter, unCPU/cap180s. Tous retournent0/NORMAL ; cette observation n'est pas une qualification physique. Les quatre témoins cohésifs implicites signalentSTOP volume nul, restentNC=0/T=0 et terminentUSER BREAK après un cycle. CSV vides, aucun bilan de charge disponible. La première analyse héritée lèveStopIteration sur la sortie vide : échec conservé, pas de nouvelle exécution pour le contourner. CHECK cohésif isolé5erreurs et1volume, solide ordinaire1erreur de matrice ; CHECK entier15erreurs,624volumes et5TYPE25 ignorés.

La sonde d'allocateur capture la demande21, double8octets, bornes1..21, capacité21 et identité exacte du pointeur avecSAV reçu parSRCOORK, TYPE43/NEL1. Une autre sonde observeNODREAC0x31 avant et aprèsSRCOORK et jusqu'à sa libération ; les modifications ultérieures du bloc libéré restent décrites comme telles. Aucun abort mémoire dans ces processus, mais aucun passage mécanique de la cohésion implicite.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a ; seuls les trois fichiers approuvés portent leurs différences exactes. Mêmes outils/dépendancesA54, écart de métadonnées71→67 explicitement conservé. Le chargeur original est partagé explicite/implicite ; la nouvelle correction est une allocation mémoire, les largeurs sérialisées et offsets de lecture restent identiques. Les sondes ne modifient aucune instruction ou donnée mécanique.

## 3. Affirmations provenant des archives locales

Aucune archive historique, image, vidéo ou PDF inspecté ou modifié. Aucune cible de dégâtsNIST.

## 4. Hypothèses propres au modèle

Graine1102082, aucun tirage. Entrées et seuils physiques des témoins inchangés, aucune compensation de masse, inertie ouRKE. L'oracle de capacité21 suit le contratSAV(NEL,21), confirmé dans le cas natif observé ; cela n'implique pas une sûreté mémoire de tout le logiciel. La loi cohésive et son énergie restent des paramètres de témoin sans nouvelle mesure historique.

## 5. Résultats dérivés

La corruption observée est levée dans le témoin et son arrêt suivant est géométrique.256opérations de graphe passent l'oracle,3024attaches natives exactes dans référence et candidatA52, aucun message de connectivité manquante. Quatre témoins cohésifs explicites passent traction, travail/énergie, rechargement, aire et demi-pas ; deuxTYPE7/MUMPS passent bilans et demi-pas.600champs passent la règle de précision ASCII/float32 préexistante, critères littéraux échoués conservés. Métadonnée de fin fournie avant analyse de contact pour ne pas rejouer le défaut déjà connu.

Le document de propositionA56 avait un défaut d'affichage UTF8/cp1252 issu d'une lecture antérieure sans encodage explicite. Une copie lisible distincte est conservée dansA57 avec inversion vérifiée, l'original scellé, les patchs et l'autorisation restent inchangés. Sources/patch/binaireAGPL restent hors manifeste publicMIT. Préservation par métadonnées et manifestes SHA256 antérieurs, hash neuf du binaire, harnaisPASS.

## 6. Contradictions et informations manquantes

Code0/NORMAL n'autorise pas à déclarer la cohésion chargée validée : temps nul,STOP etUSER BREAK sont bloquants. Les routines ciblées S8ZKE3 etS8ZDERICT3 montrent une construction volumique et un contrôleSCHKJAB3 ; le traitement de surface et la tangente LAW117 nécessitent un audit distinct. Ne pas supprimer le contrôle de volume ou inventer une épaisseur pour le contourner. Les cinqTYPE25 ignorés restent incompatibles avec le crédit d'un impact entier implicite ; TYPE7 ne les qualifie pas. A52 non intégré, travaux/inerties et énergie locale entière manquants. Meilleure fenêtre entière0,0200001220703125s ; vidéo3D des dix secondes physiques toujours incomplète.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A57 → AIRCRAFT-A58\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a57*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a57*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'source_patch_and_binary_AGPL_outside_public_MIT_manifest':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A57_assessed':True,'memory_case_regression_pass':True,'implicit_loaded_mechanical_gate_pass':False,'Engine_executions':17}),flush=True)

source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a55.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='register');s=ast.get_source_segment(source,node)
s=s.replace('AIRCRAFT-A56','AIRCRAFT-A58').replace('AIRCRAFT-A55','AIRCRAFT-A57').replace('aircraft_a55','aircraft_a57').replace('A55_registered','A57_registered').replace('174','176')
s=s.replace("assert cycle['pending_iterations']==['AIRCRAFT-A54']","assert cycle['pending_iterations']==['AIRCRAFT-A56']").replace("pending_iterations=['AIRCRAFT-A54','AIRCRAFT-A57']","pending_iterations=['AIRCRAFT-A56','AIRCRAFT-A57']").replace('AIRCRAFT-A54+AIRCRAFT-A57 verified','AIRCRAFT-A56+AIRCRAFT-A57 verified')
exec(compile(s,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
