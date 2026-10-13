"""Seal A56's failed software hypothesis and native original-buffer capacity evidence."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,re,ast
import numpy as np

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a56'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a56_predeclaration.json'
REPORT=OUT/'rapport_aircraft_a56.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A56_HANDOFF.md'

def route():
    auth=(OUT/'original_patch_authorization.json').exists()
    return ('AIRCRAFT-A57 : '+('accord explicite reçu pour' if auth else 'attendre accord explicite sur')+' le nouveau correctif de l’allocation d’origine TYPE43 dans allocbuf_auto.F ; '
      'patch ef56cf633e4d43b2dd4298f1c5995da1cae7f4a22130aea35e9702dc57c0427e, proposé et non appliqué. '
      'La mesure native A56 confirme demande0/capacité0/bornes1..0/double8octets, pointeur original ELBUF_STR%GBUF%SMSTR identique à SAV reçu par SRCOORK. '
      'Le correctif A55 appliqué au tampon temporaire dans A56 ne suffit pas ; cet échec reste conservé. '
      'Moteur A56 SHA256 ff062b207c262381e6886f0da3e3a568724d48651a21913b2a1f5596222b53f1, compilation301s plafonnée1h,17Engine, aucun Starter. '
      'Graphe256opérations et3024attaches exactes passent ; quatre témoins explicites et deuxTYPE7 passent ; sept arrêts cohésifs avantT=0 restent. '
      'Cinquième moteur séparé prévu, correctifs A53 graphe et A55 temporaire conservés, nouvelle seule différence allocbuf_auto.F,1h/sixCPU/sansGPU ni installation, '
      'capacité/pointeur/mémoire puis cohésion chargée et régressions avec critères inchangés,180s chacun. '
      'Largeurs de redémarrage, offsets, compteurs de lecture et budgets inchangés ; source fixée3d75ff13d1946f6d28a43920eac4fa2aae41b27a. '
      'CHECK entier15erreurs/624volumes/cinqTYPE25 ignorés, témoin ordinaire1erreur de matrice, A52 non intégré, couverture mécanique/énergétique entière manquante. '
      'Meilleur impact entier A20=0,0200001220703125s ; objectif1 dix secondes physiques puis vidéo3D incomplet, aucun temps des diagnostics crédité. '
      'A54+A55 publiées/vérifiées f44bcdfbe820eb624346ee51ce547c9bd0c5d215 ; prochaine cadence A56+A57 vérifiées.')

def assess():
    assert not REPORT.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A55'
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    built=read(OUT/'build_finished.json');assert built['build_success'] and built['exact_A55_scratch_patch_applied']
    executions=[]
    for p in sorted(OUT.rglob('engine.execution.json')):
        v=read(p);log=(p.parent/'engine.log').read_text(errors='replace')
        observed=next((p.parent/n for n in ['scratch_watch_result.json','allocation_trace_result.json','graph_binding_trace_result.json','optimized_add_trace_result.json'] if (p.parent/n).exists()),None)
        result=read(observed) if observed else {}
        executions.append({'path':rel(p),**v,'actual_Engine_exit_code':result.get('Engine_exit_code',v['parent_exit_code']),'normal_termination':'NORMAL TERMINATION' in log,'last_time_ms':float(re.findall(r'NC=\s*\d+ T=\s*([\d.E+-]+)',log)[-1]) if re.findall(r'NC=\s*\d+ T=\s*([\d.E+-]+)',log) else None,'CHECK_errors':int(re.findall(r'(\d+) ERRORS',log)[-1]) if re.findall(r'(\d+) ERRORS',log) else None})
    assert len(executions)==17 and all(v['cap_s']==180 and v['CPU_threads']==1 for v in executions)
    assert sum(v['actual_Engine_exit_code']==3 for v in executions)==7
    assert not list(OUT.rglob('starter.execution.json'))
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'native_Engine_executions':17,'Starter_launches':0,'executions':executions,'new_build':built,'old_native_Engine_replays':0,'GPU':False,'per_process_cap_s':180})
    alloc=read(OUT/'ACTIVE_COHESIVE_ALLOCATION_TRACE_R1/allocation_trace_result.json')
    matched=alloc['SRCOORK_context']['matching_allocations'];assert len(matched)==1 and matched[0]['native_capacity']==0
    scratch=read(OUT/'ACTIVE_COHESIVE_SCRATCH_WATCH/scratch_watch_result.json');context=scratch['SRCOORK_contexts'][0]
    assert context['return_observed'] and context['NODREAC_header']=='0x31' and context['NODREAC_header_at_return']=='0x0'
    dump(OUT/'native_allocation_identity_review.json',{'created_utc':now(),'pass_observation_integrity':True,'temporary_buffer_only_fix_resolves_corruption':False,'native_original_capacity_zero_proven':True,'matching_allocation':matched[0],'allocator_calls':alloc['allocator_calls_observed'],'SAV_pointer_identity_exact':True,'native_header_corruption_persists':True,'original_buffer_fix_applied':False,'loaded_implicit_cohesion_qualified':False})
    oracle=read(OUT/'WHOLE_OPTIMIZED_GRAPH_SET_TRACE/optimized_add_trace_result.json');assert oracle['native_observed_graph_set_gate_pass']
    prior=read(ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_ORIGINAL_TYPE2_BINDING_TRACE/type2_trace_result.json')
    flatten=lambda calls:{b['secondary_original_label']:b for call in calls for b in call['bindings']}
    baseline=flatten(prior['calls']);rows=[]
    for name in ['WHOLE_ORIGINAL_CORRECTED_GRAPH','WHOLE_PAIRED_CORRECTED_GRAPH']:
        d=OUT/name;v=read(d/'graph_binding_trace_result.json');bindings=flatten(v['TYPE2_calls']);assert len(bindings)==3024
        checks={k:all(baseline[n][k]==bindings[n][k] for n in baseline) for k in ['mode','main_original_labels_ordered','native_NDOF','native_parameter_values','native_point_coordinates_mm']}
        log=(d/'engine.log').read_text();rows.append({'case':name,'binding_checks':checks,'binding_pass':all(checks.values()),'CHECK_errors':int(re.findall(r'(\d+) ERRORS',log)[-1]),'zero_volume_messages':log.count('ZERO OR NEGATIVE VOLUME'),'TYPE25_ignored':log.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),'missing_connectivity_messages':log.count('CONNECTIVITY BETWEEN NODES')})
    assert all(v['binding_pass'] and v['CHECK_errors']==15 and v['TYPE25_ignored']==5 for v in rows)
    dump(OUT/'whole_graph_binding_review.json',{'created_utc':now(),'cases':rows,'graph_oracle_pass':True,'all_bindings_exact':True,'whole_mechanical_CHECK_pass':False,'A52_integrated':False})
    cohesive=read(OUT/'cohesive_controls/cohesive_review.json');contact=read(OUT/'contact_controls/contact_review.json')
    assert cohesive['mechanical_implementation_gate_pass'] and contact['pass']
    from probe_aircraft_a37 import vtk
    from assess_aircraft_a23_reader_precision import printed_bound
    fields=[]
    for case in contact['cases']:
        d=OUT/'contact_controls'/case['case'];raw=read(d/'review.json');X=np.asarray(read(d/'generation.json')['nodes_mm'])
        for row in raw['fields']:
            f=vtk((ROOT/row['path']).read_text());order=np.argsort(f['NODE_ID']);p=f['points'].reshape(-1,3)[order];u=f['Displacement'].reshape(-1,3)[order]
            bound=printed_bound(p)+printed_bound(u)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(p),abs(u),abs(X)])+1e-8
            checks={k:v for k,v in row['checks'].items() if k!='coordinate_displacement'};checks['coordinate_identity_source_print_bound']=bool(np.all(abs(p-X-u)<=bound))
            fields.append({'path':row['path'],'raw_literal_gate':row['checks']['coordinate_displacement'],'checks':checks,'pass':all(checks.values())})
    assert len(fields)==600 and all(v['pass'] for v in fields)
    dump(OUT/'contact_field_format_review.json',{'created_utc':now(),'fields':fields,'pass':True,'same_preexisting_A23_precision_rule':True,'raw_literal_failures_preserved':True,'physical_tolerances_changed':False})
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    assert sha(ROOT/built['candidate_directory']/'isolated_exec/engine_linux64_gf_ompi')==built['binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),'changed_paths':changed,'old_hash_manifests_preserved':True,'all_old_files_rehashed':False,'new_binary_fresh_hash_pass':True,'archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A56','status':'completed_authorized_temporary_scratch_build__native_original_zero_capacity_identified__implicit_failure_retained',
      'new_engine_binary_sha256':built['binary_sha256'],'build_success':True,'temporary_scratch_patch_applied':True,'temporary_only_hypothesis_pass':False,
      'native_Engine_executions':17,'Starter_launches':0,'implicit_cohesive_aborts':7,'implicit_loaded_cohesive_gate_pass':False,
      'native_original_SMSTR_requested_values':0,'native_original_SMSTR_capacity':0,'native_original_SMSTR_element_bytes':8,'native_original_pointer_matches_SAV':True,'native_allocator_calls_observed':740,
      'graph_operations_pass':256,'native_bindings_exact':3024,'whole_CHECK_errors':15,'whole_zero_volume_messages':624,'TYPE25_ignored':5,
      'native_explicit_cohesive_cases_pass':4,'TYPE7_contact_cases_pass':2,'contact_fields_source_precision_pass':600,
      'new_original_scratch_patch_prepared_not_applied':True,'new_original_scratch_patch_arithmetic_pass':48,
      'old_outputs_and_failed_gates_preserved':True,'budgets_changed':False,'RKE_added':False,'A52_integrated':False,'whole_insertion_ready':False,'new_whole_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A57'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'native_identity':'native_allocation_identity_review.json','graph':'whole_graph_binding_review.json','cohesive':'cohesive_controls/cohesive_review.json','contact':'contact_controls/contact_review.json','physical_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A56 — correctif temporaire insuffisant, capacité nulle du tampon d'origine mesurée

Le quatrième moteur isolé applique le correctif A55 explicitement autorisé. Il compile et conserve les contrôles de graphe et témoins explicites/TYPE7, mais les cohésifs implicites s'arrêtent encore avant le premier pas. Une mesure native établit que SAV est le tampon d'origine de capacité zéro, pas la copie temporaire visée. Cette hypothèse échouée reste conservée. Aucun temps physique entier supplémentaire.

## 1. Faits directement observés ou transcrits

Accord humain distinct A55 enregistré. Source et dépendances cachées vérifiées, correctifs exacts A53 graphe et A55 tampon temporaire appliqués ; compilation/export en environ301s, plafond1h/sixCPU, sans GPU ni installation. Binaire ff062b207c262381e6886f0da3e3a568724d48651a21913b2a1f5596222b53f1 séparé, anciens moteurs intacts, espace ext4 démonté.

Dix-sept Engine nouveaux, zéro Starter, un CPU/cap180s chacun. Sept arrêts cohésifs implicites code3 àNC=0/T=0 : CHECK isolé, quatre témoins chargés et deux observations. Les lanceurs observateurs code0 ne sont pas des passages Engine. Le CHECK solide ordinaire termine mais garde1erreur de matrice définie positive. Les deux CHECK entiers et l'oracle de graphe terminent normalement tout en conservant15erreurs,624messages de volume et5TYPE25 ignorés.

La surveillance observe le retour de SRCOORK avec21colonnes lues et NODREAC0x31→0 ; elle ne prétend pas lire un descripteur à partir d'un en-tête malloc. Une seconde sonde capture740appels d'allocateur et leurs labels. Pour ELBUF_STR%GBUF%SMSTR : demande0, élémentdouble8octets, bornes natives1..0, capacité0. Le pointeur alloué est exactement SAV transmis à SRCOORK, TYPE43/NEL1. Le retour appelant0x468d01 est dans ALLOCBUF_AUTO. Une première garde statique d'ABI supposait le même registre dans deux auxiliaires simple précision ; échec avant lancement Engine, conservé. R1 utilise les deux auxiliaires double précision et vérifie les vrais offsets du descripteur par le désassemblage du binaire.

## 2. Résultats d'un modèle officiel

Aucun nouveau modèle historique officiel. Source moteur fixée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, mêmes dépendances et outils hérités d'A54 ; écart de version71→67 conservé. La routine SRCOORK attend SAV(NEL,21), et ALLOCBUF_AUTO charge/alloue l'original selon la largeur du redémarrage. Les sondes ne changent aucune instruction ou donnée mécanique du processus.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF inspecté ou modifié. Aucune cible de dégâtsNIST.

## 4. Hypothèses propres au modèle

Graine1102081, aucun tirage. Entrées physiques et critères des témoins restent identiques ; aucune masse, inertie ou RKE compensatoire. L'hypothèse A55 « le tampon temporaire seul est insuffisant » ne résout pas la corruption. La capacité nulle du tampon réellement passé est maintenant une mesure native directe ; cela ne valide pas sa future correction ni la physique implicite.

## 5. Résultats dérivés

256opérations de graphe passent l'oracle d'ensembles ; les3024attaches du modèle original et du candidat A52 correspondent exactement à la référence enregistrée. Aucun message de connectivité manquante. Quatre témoins cohésifs explicites passent travail/énergie, traction, rechargement, aire et demi-pas ; deuxTYPE7/MUMPS passent bilans et demi-pas.600champs passent la règle de précision ASCII/float32 déjà établie ; échecs littéraux conservés. La passerelle de métadonnées completion est fournie avant analyse afin de ne pas rejouer le défaut de lecture connu.

Proposition distincte allocbuf_auto.F : réserver au moins21*NEL dans l'original TYPE43, initialiser le stockage, conserver largeur sérialisée, offsets, SDP_RBUF et valeurs restaurées.48cas arithmétiques/restauration passent, aucune compilation de cette proposition. Sources/patch/binaire AGPL hors manifeste MIT, empreintes et scripts propres conservés. Préservation des anciens fichiers par métadonnées et manifestes SHA256, hash neuf du moteur, harnais PASS.

## 6. Contradictions et informations manquantes

Le correctif temporaire a compilé mais échoue à son objectif mémoire. Aucun bilan cohésif implicite chargé n'est obtenu. Le CHECK entier et TYPE25 restent bloquants ; A52 non intégré, inerties/travaux et énergie locale entière manquent encore. La meilleure fenêtre entière demeure0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes. Aucun nouveau calcul entier ou rendu GPU lancé.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A56 → AIRCRAFT-A57\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(OUT/'proposition_correctif_tampon_origine.md')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a56*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a56*.json'))+[HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'source_patch_and_binary_AGPL_outside_public_MIT_manifest':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A56_assessed':True,'Engine_executions':17,'temporary_fix_gate_pass':False,'native_original_capacity_zero':True}),flush=True)

# Reuse the sealed predecessor's registration procedure with explicit pair/cadence changes.
source=(ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a55.py').read_text()
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='register')
register_source=ast.get_source_segment(source,node)
register_source=register_source.replace('AIRCRAFT-A56','AIRCRAFT-A57').replace('AIRCRAFT-A55','AIRCRAFT-A56').replace('aircraft_a55','aircraft_a56').replace('A55_registered','A56_registered')
register_source=register_source.replace("assert cycle['pending_iterations']==['AIRCRAFT-A54']","assert cycle['pending_iterations']==[]")
register_source=register_source.replace("pending_iterations=['AIRCRAFT-A54','AIRCRAFT-A56'],pending_count=2","pending_iterations=['AIRCRAFT-A56'],pending_count=1")
register_source=register_source.replace('AIRCRAFT-A54+AIRCRAFT-A56 verified','AIRCRAFT-A56+AIRCRAFT-A57 verified').replace('174','175').replace("'pending_publication_count':2","'pending_publication_count':1")
exec(compile(register_source,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
