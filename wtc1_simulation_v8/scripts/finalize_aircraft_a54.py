"""Assess and seal A54; keep failed/inconclusive controls and original physical limits."""
from build_aircraft_a54_graph import ROOT,OUT,CFG,read,dump,sha,now,rel,harness,guard
from pathlib import Path
import json,re,time,tarfile,hashlib
import numpy as np

REPORT=OUT/'rapport_aircraft_a54.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A54_HANDOFF.md'


def route():
    return ('AIRCRAFT-A55 : moteur A54 corrigé compilé et conservé, SHA256 c4a18b981b9beb461fbb570a12d5ef04aa9a97293c61875c9d458ea99579d3b2, dossier a54_type2_graph_candidate_r1. '
        '256 opérations natives passent les ensembles de voisins dans quatre régions ; référence et candidat A52 terminent CHECK, toutes3024attaches identiques, aucun message de connectivité manquante. '
        'CHECK entier reste échoué :15erreurs,624messages166 sur60001..60624 cohésifs LAW117/TYPE43 de hauteur nulle, cinqTYPE25 ignorés. '
        'Qualifier indépendamment le traitement géométrique des cohésifs et leur réponse chargée implicite avec des cas isolés et des critères inchangés ; confronter un CHECK cohésif à un solide ordinaire et vérifier les bilans avant toute décision. '
        'Préserver la sonde auxiliaire sans appel, le critère erroné de compteur final3 et l’analyse contact initiale sans métadonnée completion. Aucun nouveau correctif moteur n’est implicitement autorisé par l’accord A53 ; présenter toute nouvelle modification concrète avant application/compilation. '
        'L’accord humain A54 est enregistré ; les contrôles supplémentaires avec ce même binaire et les données de cas sont autorisés pour poursuivre objectif1. '
        'A52 reste non intégré : seule équivalence native des attaches passe, inerties/travaux et insertion non qualifiés. '
        'Meilleure durée entière A20=0,0200001220703125s, pas de nouveau crédit physique. Aucun impact de dix secondes lancé avec des contacts ignorés ; zéro RKE inventée, budgets et échecs conservés. Prochaine publication A54+A55 vérifiées.')


def assess():
    guard();assert not REPORT.exists() and not HANDOFF.exists()
    built=read(OUT/'build_finished.json');assert built['build_success']
    oracle=read(OUT/'WHOLE_OPTIMIZED_GRAPH_SET_TRACE/optimized_add_trace_result.json')
    assert oracle['native_observed_graph_set_gate_pass']
    cases=[]; traces=[]
    for name in ['WHOLE_ORIGINAL_CORRECTED_GRAPH','WHOLE_PAIRED_CORRECTED_GRAPH']:
        d=OUT/name;trace=read(d/'graph_binding_trace_result.json');traces.append(trace)
        text=(d/'engine.log').read_text();errors=re.findall(r'\b(\d+) ERRORS\b',text);warnings=re.findall(r'\b(\d+) WARNINGS\b',text)
        ids=[int(v) for v in re.findall(r'ZERO OR NEGATIVE VOLUME FOR 3D-ELEMENT ID=(\d+)',text)]
        cases.append({'case':name,'Engine_exit_code':trace['Engine_exit_code'],
            'normal_termination':'NORMAL TERMINATION' in text,'CHECK_errors':int(errors[-1]),'CHECK_warnings':int(warnings[-1]),
            'zero_volume_message_count':len(ids),'zero_volume_element_ids':sorted(set(ids)),
            'missing_connectivity_messages':text.count('CONNECTIVITY BETWEEN NODES'),
            'TYPE25_ignored':text.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),
            'TYPE2_binding_calls':len(trace['TYPE2_calls']),
            'helper_entry_calls':sum(trace['helper_calls_by_phase'].values()),
            'helper_entry_probe_inconclusive':trace['helper_entry_inconclusive_if_zero_calls'],
            'clean_mechanical_CHECK_pass':int(errors[-1])==0})
    cached=read(ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_ORIGINAL_TYPE2_BINDING_TRACE/type2_trace_result.json')
    bindings=lambda calls:{b['secondary_original_label']:b for call in calls for b in call['bindings']}
    original=bindings(cached['calls']); comparisons=[]
    for name,trace in zip(['corrected_original','corrected_paired'],traces):
        current=bindings(trace['TYPE2_calls']);assert set(current)==set(original)
        checks={key:all(original[node][key]==current[node][key] for node in original) for key in
            ['mode','main_original_labels_ordered','native_NDOF','native_parameter_values','native_point_coordinates_mm']}
        comparisons.append({'case':name,'bindings':len(current),'checks_exact_saved_values':checks,'pass':all(checks.values())})
    dump(OUT/'whole_graph_and_binding_review.json',{'created_utc':now(),'cases':cases,
        'binding_comparisons':comparisons,'both_binding_equivalence_pass':all(row['pass'] for row in comparisons),
        'cached_reference_missing_connectivity_messages':49370,'corrected_missing_connectivity_messages':[row['missing_connectivity_messages'] for row in cases],
        'clean_whole_mechanical_CHECK_pass':all(row['clean_mechanical_CHECK_pass'] for row in cases),
        'implicit_TYPE25_contacts_qualified':False,'whole_insertion_ready':False})
    source=read(ROOT/'wtc1_simulation_v8/data/aircraft_a52_predeclaration.json')['source_files']['input']
    assert sha(ROOT/source['path'])==source['sha256']
    sections={};key=None
    for line in (ROOT/source['path']).read_text().splitlines():
        if line.startswith('/'):key=line;sections[key]=[]
        elif key is not None:sections[key].append(line)
    coordinates={int(line[:10]):[float(line[j:j+20]) for j in [10,30,50]] for line in sections['/NODE'] if line.strip()}
    geometry=[]
    for key,lines in sections.items():
        if not key.startswith('/BRICK/'):continue
        part=int(key.split('/')[-1]);pfields=sections['/PART/'+str(part)][1].split();prop,material=map(int,pfields[:2])
        law=next(k for k in sections if k.startswith('/MAT/') and k.endswith('/'+str(material)))
        property_key=next(k for k in sections if k.startswith('/PROP/') and k.endswith('/'+str(prop)))
        for line in lines:
            fields=[int(v) for v in line.split()];eid=fields[0]
            if eid not in cases[0]['zero_volume_element_ids']:continue
            nodes=fields[1:];X=np.asarray([coordinates[node] for node in nodes]);assert X.shape==(8,3)
            area=.5*(np.linalg.norm(np.cross(X[1]-X[0],X[2]-X[0]))+np.linalg.norm(np.cross(X[2]-X[0],X[3]-X[0])))
            geometry.append({'element':eid,'part':part,'material':law,'property':property_key,
                'face_area_mm2':float(area),'maximum_corresponding_face_separation_mm':float(np.linalg.norm(X[:4]-X[4:],axis=1).max())})
    assert len(geometry)==624
    dump(OUT/'remaining_cohesive_geometry_review.json',{'created_utc':now(),'input':source,
        'elements':geometry,'all_reported_elements_LAW117_TYPE43':all('/LAW117/' in row['material'] and '/TYPE43/' in row['property'] for row in geometry),
        'all_face_areas_positive':all(row['face_area_mm2']>0 for row in geometry),
        'maximum_face_separation_mm':max(row['maximum_corresponding_face_separation_mm'] for row in geometry),
        'CHECK_errors_not_dismissed':True,'loaded_implicit_cohesive_or_whole_impact_qualified':False})
    contact=read(OUT/'contact_controls/contact_review.json');cohesive=read(OUT/'cohesive_controls/cohesive_review.json')
    from probe_aircraft_a37 import vtk
    from assess_aircraft_a23_reader_precision import printed_bound
    field_rows=[]
    for case in contact['cases']:
        d=OUT/'contact_controls'/case['case'];raw=read(d/'review_after_completion_metadata.json');X=np.asarray(read(d/'generation.json')['nodes_mm'])
        for row in raw['fields']:
            field=vtk((ROOT/row['path']).read_text());order=np.argsort(field['NODE_ID']);p=field['points'].reshape(-1,3)[order];u=field['Displacement'].reshape(-1,3)[order]
            bound=printed_bound(p)+printed_bound(u)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(p),abs(u),abs(X)])+1e-8
            checks={k:v for k,v in row['checks'].items() if k!='coordinate_displacement'}
            checks['coordinate_identity_with_preexisting_source_format_bound']=bool(np.all(abs(p-X-u)<=bound))
            field_rows.append({'path':row['path'],'raw_literal_gate':row['checks']['coordinate_displacement'],
                'checks':checks,'pass':all(checks.values()),'maximum_residual_mm':float(abs(p-X-u).max()),'maximum_format_bound_mm':float(bound.max())})
    dump(OUT/'contact_field_formatting_review.json',{'created_utc':now(),'fields':field_rows,
        'pass':bool(field_rows) and all(row['pass'] for row in field_rows),
        'literal_failed_gates_preserved':True,'same_A23_A41_A45_source_printing_rule':True,'physical_tolerances_changed':False})
    old=read(OUT/'preservation_before_metadata.json');changed=[]
    for row in old['files']:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    candidate=ROOT/built['candidate_directory'];assert sha(candidate/'isolated_exec/engine_linux64_gf_ompi')==built['binary_sha256']
    assert sha(ROOT/read(CFG)['preservation']['protected_A44_binary'])==read(CFG)['preservation']['protected_A44_binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old['files']),
        'changed_paths':changed,'immutable_old_SHA256_manifests_retained':True,'all_old_content_rehashed':False,
        'old_A44_binary_fresh_SHA256_pass':True,'original_whole_input_fresh_SHA256_pass':True,'archives_not_rescanned':True})
    h=harness();dump(OUT/'harness_after_calculation.json',h)
    executions=[{'path':rel(path),**read(path)} for path in OUT.rglob('engine.execution.json')]
    assert len(executions)==10 and all(row['CPU_threads']==1 and row['cap_s']==180 for row in executions)
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'native_executions':executions,'native_Engine_executions':10,
        'fresh_Starter_executions':0,'old_Engine_replays':0,'new_isolated_build':built,
        'source_and_patch_license':'AGPL-3.0-or-later','CPU_threads_native':1,'GPU':False,'per_process_cap_s':180})
    assessment={'created_utc':now(),'iteration':'AIRCRAFT-A54',
        'status':'completed_authorized_exact_graph_patch_build_and_native_graph_binding_qualification__whole_CHECK_and_TYPE25_still_failed',
        'new_Engine_executions':10,'fresh_Starter_executions':0,'new_installations':0,'new_isolated_Engine_builds':1,
        'exact_A53_patch_compiled':True,'binary_sha256':built['binary_sha256'],'candidate_directory':built['candidate_directory'],
        'compile_wall_s':read(OUT/'build_attempt_r1/build_logs/07_compile.execution.json')['wall_s'],
        'build_wall_s_from_initial_start':built['wall_s_from_original_start'],'build_within_original_hour':True,
        'initial_EOL_guard_failure_preserved':True,'generic_helper_entry_zero_calls_preserved':True,
        'incorrect_three_neighbor_final_count_hypothesis_failed_and_preserved':True,
        'native_graph_set_calls':256,'native_graph_duplicate_calls':oracle['duplicate_calls'],
        'native_graph_new_neighbor_calls':oracle['new_neighbor_calls'],'native_four_region_graph_oracle_pass':True,
        'corrected_original_and_paired_CHECK_normal_completions':2,
        'corrected_missing_connectivity_messages':0,'cached_reference_missing_connectivity_messages':49370,
        'original_TYPE2_calls':432,'paired_TYPE2_calls':216,'native_bindings_compared':3024,
        'reference_and_paired_native_bindings_exact':all(row['pass'] for row in comparisons),
        'whole_CHECK_errors':15,'whole_zero_volume_messages':624,'reported_cohesive_elements_geometry_mapped':624,
        'implicit_TYPE25_ignored':5,'clean_whole_mechanical_CHECK_pass':False,
        'native_cohesive_cases':4,'native_explicit_cohesive_implementation_gate_pass':cohesive['mechanical_implementation_gate_pass'],
        'native_MUMPS_TYPE7_contact_cases':2,'native_TYPE7_contact_physical_and_time_step_gate_pass':contact['pass'],
        'native_contact_field_format_gate_pass':all(row['pass'] for row in field_rows),'native_contact_field_samples':len(field_rows),
        'initial_contact_analysis_metadata_failure_preserved':True,
        'old_binaries_and_outputs_preserved':True,'physical_inputs_or_budgets_changed':False,'RKE_or_mass_compensation_added':False,
        'A52_integrated_or_whole_insertion_ready':False,'new_whole_impact_extension_executed':False,
        'new_whole_physical_duration_credit_s':0,'best_whole_physical_s':.0200001220703125,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A55'}
    dump(OUT/'scientific_assessment.json',assessment)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':assessment,
        'native_graph_oracle':'WHOLE_OPTIMIZED_GRAPH_SET_TRACE/optimized_add_trace_result.json',
        'whole_binding_and_CHECK':'whole_graph_and_binding_review.json','cohesive':'cohesive_controls/cohesive_review.json',
        'contact':'contact_controls/contact_review.json','field_precision':'contact_field_formatting_review.json',
        'all_failed_or_inconclusive_attempts_preserved':True,'whole_impact_qualified':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A54 — moteur corrigé compilé, graphe natif contrôlé, impact toujours limité

Le correctif A53 autorisé est appliqué à un troisième moteur isolé. Il supprime les messages de connectivité manquante et permet au candidat regroupé A52 de terminer son CHECK. Les 15 erreurs restantes et les cinq contacts TYPE25 ignorés empêchent encore une qualification de l’impact implicite. Aucun temps physique supplémentaire n’est crédité à l’objectif des dix secondes.

## 1. Faits directement observés ou transcrits

L’accord humain du 13 octobre est enregistré dans software_authorization.json. Le premier contrôle du fichier patché a arrêté la préparation avant compilation : GNU patch produit des fins de ligne LF, le fichier proposé A53 est CRLF. Cette tentative est conservée. R1 vérifie le contenu LF, puis copie le fichier proposé intact et exige son SHA256 exact. La compilation prend '''+f'{assessment["compile_wall_s"]:.3f}'+''' secondes ; 474,160 secondes depuis le lancement initial, dans le plafond original d’une heure, six CPU, sans GPU ni installation. Aucun ancien moteur n’est remplacé.

Dix nouveaux Engine, un CPU chacun, limite 180 secondes, aucun Starter. Les deux CHECK entiers terminent code0/NORMAL : référence 432 appels TYPE2 et candidat 216, chacun 3024 attaches. Tous les labels de voisins, paramètres natifs, coordonnées et degrés de liberté correspondent exactement à la référence A52 enregistrée. Les 49370 anciens messages de connectivité sont absents dans ces deux sorties corrigées. Chaque CHECK conserve 15 ERRORS, 5 WARNINGS et 624 messages166 sur les éléments60001..60624.

La sonde au symbole auxiliaire générique capture zéro appel, résultat inconclusif conservé. La surveillance matérielle de la ligne48151 observe une nouvelle colonne3011 dans le bon rangement, aucune écriture à la mauvaise colonne surveillée, puis 41 voisins uniques au retour. L’hypothèse de diagnostic « compteur final3 » était trop restrictive : elle ignorait les autres vrais voisins ajoutés ; son échec reste conservé. Une nouvelle déclaration indépendante vise les clones réellement utilisés, dont l’ABI est vérifiée dans le désassemblage du binaire précis. 128 ajouts de dimensionnement et128 de construction passent l’oracle avant/après d’ensembles :140 doublons conservent leur compteur,116 nouveaux voisins l’augmentent correctement. Les quatre régions sont observées :28 principales et100 ordinaires par phase. Cela qualifie les opérations observées, sans total global extrapolé.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel exécuté. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a ; seul ind_glob_k.F porte le correctif exact A53. Les13869 fichiers sources/dépendances sont vérifiés avant modification. L’écart de métadonnées de dépendance71→67 hérité d’A44 reste explicite. Les versions GNU13.3.0, CMake3.28.3 et OpenMPI4.1.6 et les bibliothèques liées sont journalisées. CHECK conserve PCG/IPREC5, ce contrôle ne constitue pas une dynamique MUMPS entière.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou source officielle inspectée. Les archives et work/official_sources restent en lecture seule. Aucun dégât connu ne sert de cible d’ajustement.

## 4. Hypothèses propres au modèle

Graine1102079, aucun tirage. Les états physiques et les cartes Engine des comparaisons sont copiés avec empreintes identiques. Aucune masse, inertie, loi, liaison compensatoire ou RKE n’est ajoutée. Les oracles natifs d’ensembles sont des contrôles logiciels, pas des probabilités historiques. Les propriétés cohésives restent des paramètres de référence, sans mesure nouvelle de fracture réelle.

## 5. Résultats dérivés

Le binaire corrigé SHA256 c4a18b981b9beb461fbb570a12d5ef04aa9a97293c61875c9d458ea99579d3b2 est conservé dans a54_type2_graph_candidate_r1. Les sources complètes, patch et journaux sont conservés séparément sous AGPL ; ils restent exclus du manifeste public MIT courant. Les contrôles de graphe natif et d’équivalence des attaches passent dans leur domaine déclaré ; A52 n’est pas intégré pour autant.

Les quatre témoins cohésifs explicites passent leurs critères de masse, traction, rechargement et travail/énergie, aire et demi-pas. Les deux témoins TYPE7/MUMPS passent les bilans physiques et la comparaison du demi-pas. Les600 champs passent la règle de précision ASCII/float32 déjà utilisée A23/A41/A45 ; leurs échecs littéraux sont conservés. Une première analyse de contact a sauté la conversion faute de completion.json attendu par l’ancien lecteur : le moteur avait terminé normalement. Une passerelle de métadonnées et une analyse distincte réutilisent cette sortie sans rejouer le moteur.

Les624 éléments signalés sont tous LAW117/TYPE43, avec faces d’aire positive et hauteur initiale nulle. Ce constat n’annule pas le CHECK échoué : son traitement géométrique et la réponse cohésive implicite chargée doivent être qualifiés indépendamment. Les anciens fichiers sont vérifiés par métadonnées et manifestes SHA256 conservés, les entrées utilisées et A44 par empreintes fraîches. Harnais PASS avant et après ; intégrité et physique restent distinctes.

## 6. Contradictions et informations manquantes

Le CHECK entier n’est pas propre. Les cinq TYPE25 sont ignorés en implicite ; les témoins TYPE7 ne qualifient pas leur remplacement dans l’impact. Inertie et travaux des attaches, croissance cohésive chargée, peaux, raffinement et bilans locaux restent échoués ou manquants. L’absence de messages de graphe ne valide ni l’impact entier ni la chaîne historique.

La meilleure fenêtre d’impact entier reste0,0200001220703125s. Aucun des diagnostics A54 ne complète les dix secondes, et aucune vidéo de dix secondes physiques n’est fabriquée par extrapolation ou ralenti. La suite A55 examine les cohésifs isolés et leur compatibilité implicite, puis les contacts et autres domaines nécessaires avant extension.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A54 → AIRCRAFT-A55\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    files=[path for path in OUT.rglob('*') if path.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a54*.py'))+[CFG,HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'source_and_binary_AGPL_outside_public_MIT_manifest':True,
        'local_engine_binary':rel(candidate/'isolated_exec/engine_linux64_gf_ompi'),'local_engine_binary_sha256':built['binary_sha256'],
        'files':[{'path':rel(path),'bytes':path.stat().st_size,'sha256':sha(path)} for path in sorted(set(files))]})
    print(json.dumps({'A54_assessed':True,'native_Engine_executions':10,'objective1_complete':False}),flush=True)


def register():
    guard();manifest=read(OUT/'artifact_manifest.json')
    for row in manifest['files']:assert (ROOT/row['path']).stat().st_size==row['bytes'] and sha(ROOT/row['path'])==row['sha256'],row['path']
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json')
    registry=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert registry.read_bytes()==prefix
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A54','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with registry.open('a',encoding='utf8',newline='\n') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A54',next_iteration='AIRCRAFT-A55',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a54_key_results']=row
    state['validated_artifacts'].update(aircraft_a54_report=rel(REPORT),aircraft_a54_results=rel(OUT/'composite_qualification_review.json'),aircraft_a54_handoff=rel(HANDOFF))
    assert cycle['pending_count']==0 and cycle['pending_iterations']==[]
    cycle.update(pending_iterations=['AIRCRAFT-A54'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A54+AIRCRAFT-A55 verified')
    for path,value in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==173
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,
        'new_files_verified':len(manifest['files']),'harness':h,'old_outputs_preserved':True,
        'objective1_complete':False,'whole_impact_qualified':False,'next_iteration':'AIRCRAFT-A55'})
    print(json.dumps({'A54_registered':True,'registry_entries':173,'next_iteration':'AIRCRAFT-A55'}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
