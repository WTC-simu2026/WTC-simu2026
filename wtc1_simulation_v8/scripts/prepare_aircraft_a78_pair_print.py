"""Seal static A78 topology evidence and one new detailed Starter observation proposal."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a66_current_area_r1 import sections
from run_aircraft_a04 import blocks
from run_aircraft_a02 import ii
from pathlib import Path
import json,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a78';PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a78_preparation'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a78_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a78_proposal.json'
REPORT=OUT/'rapport_aircraft_a78.md'
PROPOSAL=PREP/'proposition_observation_paires_initiales_DETAIL.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A78_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A79_2026-10-14.md'


def route():
    return ('AIRCRAFT-A79 proposée : une seule nouvelle observation Starter détaillée, '
        'IPRI5 ajouté par /IOFLAG et nom de cas changé, toutes les cartes physiques A77 originales exactes. '
        'UnCPU/plafond180s, zéro Engine, correctif logiciel, compilation, GPU ou installation, aucun impact entier prolongé. '
        'Mesurer les tuples réels nœud secondaire/quatre nœuds de segment et les relier à la géométrie, '
        'avant une nouvelle politique de contact. Les916erreurs/1avertissement A77 sont attendus et restent échoués ; '
        'réussite d’observation ne vaut pas préparation propre. Hypothèse de fragments de surface coïncidents : '
        '432composantes par identités de nœuds,340groupes de coordonnées identiques entre composantes, '
        '676numéros fautifs tous sur ces coïncidences, sans preuve de déconnexion mécanique ni paire native encore identifiée. '
        'Les deux Starter A77 sont consommés, CHECK inutilisés non réaffectés : accord distinct requis pour cette observation. '
        'Conserver anciens moteurs/sorties, A75/A77 échoués, budgets et critères.107391avertissements physiques bloquants. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def declare():
    assert not any(p.exists() for p in [OUT,CFG,PLAN])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A77' and h['RegistryEntries']==196
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a76_a77/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    geometry=read(PREP/'surface_topology_review.json');assert geometry['pass_static_only'] and geometry['new_native']==0
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A78','seed':1102103,'random_draws':0,
        'purpose':'New static topology/coordinate audit and prepared detailed native pair observation only',
        'source_references':[rel(PREP/'surface_topology_review.json'),
            'wtc1_simulation_v8/output/aircraft_a77/initialization_message_review.json'],
        'primary_source':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm',
        'units':'g/mm/ms unchanged','new_native':0,'software_source_or_binary_modified':False,
        'source_binary_equivalence_not_assumed':True,'historical_archive_inspected':False})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_observation_card_preparation':True})


def prepare():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'] and not REPORT.exists()
    geometry=read(PREP/'surface_topology_review.json');row=geometry['models'][0]
    source=ROOT/row['source'];assert sha(source)==row['source_sha256']
    old=sections(source);assert '/IOFLAG' not in old
    name='A79_SELF_PAIR_PRINT';old_name=old['/BEGIN'][0];lines=[]
    for block in blocks(source.read_text(encoding='utf8').splitlines()):
        if block[0]=='/END':lines.extend(['/IOFLAG',ii(5)+' '*20+ii(0,0,0,0)])
        lines.extend(block)
    text='\n'.join(lines)+'\n';assert text.count(old_name)==2;text=text.replace(old_name,name)
    folder=PREP/'SELF_PAIR_PRINT';assert not folder.exists();folder.mkdir()
    new=folder/(name+'_0000.rad');new.write_text(text,encoding='utf8',newline='\n')
    after=sections(new);unchanged={k:v for k,v in after.items() if k!='/IOFLAG' and k not in ['/BEGIN','/TITLE']}
    baseline={k:v for k,v in old.items() if k not in ['/BEGIN','/TITLE']}
    assert unchanged==baseline and after['/IOFLAG']==[ii(5)+' '*20+ii(0,0,0,0)]
    private=ROOT/'wtc1_simulation_v8/openradioss_runtime/a78_contact_geometry_audit'
    io=(private/'hm_read_ioflag.F').read_text(encoding='utf8');config=(private/'ioflag.cfg').read_text(encoding='utf8')
    source_checks={'IPRI_default0_and_reader_explicit':"IPRI=0" in io and "HM_GET_INTV('IPRI',IPRI" in io,
        'IDROT_default0_and_future_card0':"IDROT = 0" in io and after['/IOFLAG'][0][60:70]==ii(0),
        'current_format_column_order_matches':'IPRI, IOUTP, IOUTYY, IROOTYY, Irot' in config,
        'Windows_binary_source_identity_NOT_assumed':True,'physical_fields_unchanged':unchanged==baseline,
        'one_output_keyword_only_and_root_name_change':set(after)==set(old)|{'/IOFLAG'},
        'all_five_contact_cards_exact':all(after[k]==v for k,v in old.items() if k.startswith('/INTER/')),
        'no_Engine_input_prepared_or_execution_proposed':True,'new_native0':True}
    assert all(source_checks.values())
    oldcfg=read(ROOT/'wtc1_simulation_v8/data/aircraft_a77_predeclaration.json')
    p={'created_utc':now(),'iteration':'AIRCRAFT-A78_PROPOSAL','seed':1102103,'random_draws':0,
        'purpose':'Observe actual initial node/main-segment labels through detailed Starter listing, not retry pass',
        'case':'SELF_PAIR_PRINT','name':name,'source_original_A77_case':oldcfg['cases'][0],
        'inputs':[{'path':rel(new),'bytes':new.stat().st_size,'sha256':sha(new)}],
        'output_option':{'keyword':'/IOFLAG','Ipri':5,'Ioutp':0,'OutyyFMT':0,'Irootyy':0,'Idrot':0},
        'source_physical_cards_unchanged':True,'Starter_binary':oldcfg['Starter_binary'],
        'Starter_sha256':oldcfg['Starter_sha256'],'mass_baseline':oldcfg['mass_baselines'][0],
        'maximum_Starter':1,'maximum_Engine':0,'CPU_threads':1,'cap_s':180,'GPU':False,
        'software_source_patch':False,'compilation':False,'installation':False,'whole_dynamic_extension':False,
        'expected_observation_wall_s':[20,90],'old_A77_Starter_remaining':0,
        'old_A77_Engine_conditionally_unused':2,'unused_CHECK_slots_do_not_cover_new_Starter':True,
        'new_explicit_human_authorization_required':True,
        'expected_physical_Starter_errors':916,'expected_physical_Starter_warnings':1,
        'observation_acceptance':{'native_print_option_confirmed':True,'actual_secondary_and_four_main_node_numbers_printed':True,
            'tuple_domains_verified_against_native_coordinate_or_connectivity_listing':True,
            'printed_pair_nodes_found_in_predeclared_groups_and_main_facets':True,'mass_and_ADMAS_unchanged':True,
            'physical_errors_and_warnings_preserved_not_relabelled':True},
        'full_dynamic_contact_or_initialization_qualification':False,
        'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,p)
    dump(PREP/'print_observation_scope_review.json',{'created_utc':now(),'pass':True,'checks':source_checks,
        'plan_sha256':sha(PLAN),'sources':geometry['print_option_sources'],'new_native':0,
        'native_printing_or_pair_domain_NOT_yet_qualified':True})
    PROPOSAL.write_text('''# AIRCRAFT-A78 — une observation des paires initiales, proposée seulement

La variante de voisinage A77 reste échouée :916erreurs612/1avertissement par Starter, aucun Engine ni restart initial propre. Les deux préparations sont consommées. Aucune modification de contact supplémentaire n’est proposée sans identifier les paires fautives.

Le nouvel audit statique de l’auto-contact relève432morceaux reliés par identités de nœuds dans1296facettes,3024nœuds et340groupes de coordonnées identiques entre morceaux. Les676numéros de nœuds distincts des916erreurs correspondent tous à ces coïncidences. Les liaisons mécaniques TYPE2 ne sont pas incluses dans ce graphe de surface : aucune déconnexion structurelle déduite. Les tuples de segments réellement sélectionnés n’ont pas encore été imprimés.

Une seule nouvelle entrée est préparée depuis la variante originale A77. Elle ajoute uniquement /IOFLAG Ipri5 et renomme BEGIN/TITLE ; tous les contacts, gaps, coordonnées, propriétés, liaisons, masse/matière/inertie et conditions physiques restent identiques. Les autres flags de sortie et Idrot restent à leur valeur0 par défaut. La [documentation officielle IOFLAG](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm) définit cette sortie détaillée, incluant coordonnées/connectivités/pénétrations initiales. Sources en cache vérifiées, identité avec le binaire Windows non supposée ; le rendu natif reste à contrôler.

Lot A79 : un seul Starter d’observation, unCPU/plafond180s, estimation20–90s, zéro Engine, correctif logiciel, compilation, GPU ou installation. Il doit produire les numéros de nœud secondaire et quatre nœuds de segment, pour les vérifier contre la géométrie/connectivité imprimées et le modèle déclaré. Totaux masse/ADMAS à comparer. Les erreurs physiques916/1 restent attendues et échouées : réussite d’une observation ne devient pas préparation propre ni temps d’impact simulé.

Un accord distinct est requis : les deux Starter A77 sont épuisés et les CHECK inutilisés ne sont pas réaffectés. Aucun impact entier prolongé ni nouvelle règle de contact appliquée. Plan : wtc1_simulation_v8/data/aircraft_a78_proposal.json. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A78','status':'completed_static_self_surface_coincidence_audit_and_one_detailed_Starter_observation_proposal',
        'new_Engine':0,'new_Starter':0,'new_compilation':False,'software_binary_or_source_changed':False,
        'main_surface_parts':432,'main_surface_facets':1296,'main_surface_nodes':3024,
        'surface_components_by_shared_ID':432,'same_written_coordinates_across_components_groups':340,
        'printed_error_nodes_unique':676,'all676_on_same_coordinate_cross_component_groups':True,
        'surface_graph_does_not_include_TYPE2_and_is_NOT_structural_rank':True,
        'actual_native_segment_pairs_and_coordinate_mapping_unqualified':True,
        'prepared_observation_scope_pass':True,'scope_checks':len(source_checks),
        'future_maximum_Starter':1,'future_maximum_Engine':0,'future_CPU':1,'future_cap_s':180,
        'new_explicit_consent_received':False,'output_only_change_IPRI5':True,
        'all_physical_cards_and_failed_gates_preserved':True,'RKE_added':False,
        'future_GPU_installation_compilation_patch_whole_extension':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A79'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),
        'geometry_review':rel(PREP/'surface_topology_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A78 — coïncidences de surface et paires initiales à observer

Nouvel audit statique depuis les sorties A77, sans solveur rejoué. Une observation Starter avec sortie détaillée est préparée, non exécutée. Aucun contact ou paramètre mécanique changé.

## 1. Faits directement observés ou transcrits

A77 conserve916erreurs612/1avertissement ; les deux Starter sont consommés et ses deuxCHECK omis. Les numéros des676nœuds distincts sont présents dans les groupes et surfaces d’entrée. L’auto-contact possède432pièces,1296facettes et3024nœuds. Le graphe des facettes par identités de nœuds contient432composantes ;340groupes de coordonnées écrites identiques traversent ces composantes. Tous les676numéros fautifs apparaissent dans ces groupes. Les deux variantes donnent les mêmes mesures statiques. Cela ne prouve pas le segment réellement choisi par le Starter.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La [documentation IOFLAG](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm) décrit la sortie Starter détaillée Ipri5 avec coordonnées, connectivités et pénétrations initiales. Les sources et configuration figées en cache confirment l’ordre des champs, Ipri0 et Idrot0 par défaut. Leur identité avec le binaire Windows n’est pas revendiquée ; l’observation native proposée devra vérifier le résultat.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée, aucune vidéo source réanalysée ni dégâts connus ciblés. Les sources logicielles et données propres restent distinctes de l’histoire de l’impact. A76+A77 publiées avec anciennes archives et deux CI vérifiées avant déclaration A78.

## 4. Hypothèses propres au modèle

Graine1102103, zéro tirage ; unitésg/mm/ms. Des morceaux de surface distincts partageant les mêmes positions sont compatibles avec les erreurs d’auto-contact et l’inefficacité du filtre par voisinage. Cette relation reste une hypothèse tant que les paires effectivement sélectionnées sont absentes. Les contraintes TYPE2 ne sont pas incluses dans le graphe de surface ; aucune déconnexion mécanique ou rang structurel inférés. Coordonnées identiques écrites ne sont pas une observation de coordonnées internes natives.

## 5. Résultats dérivés

Une seule copie originale A77 est préparée avec ajout /IOFLAG Ipri5 et noms BEGIN/TITLE changés. Toutes les cartes physiques et contacts restent exactement identiques ; aucun Engine préparé/exécuté. Neuf critères de portée passent. Lot A79 proposé : un Starter CPU1/plafond180s, sans correctif/compilation/GPU/installation ni impact entier prolongé, estimation20–90s. Objectif : tuples réels secondaire/quatre nœuds du segment, vérifiés contre coordonnées/connectivités natives imprimées et modèle déclaré. Les masses/ADMAS et erreurs sont enregistrées. Le succès d’observation ne valide pas l’initialisation.

## 6. Contradictions et informations manquantes

Les paires fautives réelles restent manquantes. Le nouveau changement porte sur la sortie, jamais sur un filtre destiné à forcer le passage ; les erreurs916/1 restent attendues et échouées. Les107391 avertissements, inerties, matériaux, contacts dynamiques, bilans et intégration entière restent bloquants. Les budgets A77 sont conservés et aucun nouveau Starter n’est couvert par ses CHECK inutilisés. Accord distinct requis pour l’observation proposée. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A78 → AIRCRAFT-A79\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prioritaire, aucun calcul en cours. A76+A77 publiées/vérifiées, A78 seule en attente de cadence.\n'+route()+'\nNouvelles courtes en français ; aucun ancien diagnostic natif rejoué.\n',encoding='utf8')
    previous=read(ROOT/'wtc1_simulation_v8/output/aircraft_a77/artifact_manifest.json')
    for entry in previous['files']:assert sha(ROOT/entry['path'])==entry['sha256']
    assert sha(ROOT/oldcfg['binary'])==oldcfg['binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A77_sealed_files_rehashed':len(previous['files']),
        'A73_binary_rehashed_unchanged':True,'A77_failed_gates_and_conditional_unused_budget_retained':True,
        'new_native':0,'historical_archive_not_rescanned':True})
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[p for p in PREP.rglob('*') if p.is_file()]
    files+=list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a78*.py'))+[CFG,PLAN,HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_inputs_scripts_only_AGPL_raw_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A78_prepared':True,'new_native':0,'future_Starter':1,'future_Engine':0}),flush=True)


def register():
    s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert s==read(OUT/'before_state.json') and c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==[]
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    m=read(OUT/'artifact_manifest.json')
    for entry in m['files']:assert sha(ROOT/entry['path'])==entry['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A78','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A78',next_iteration='AIRCRAFT-A79',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a78_key_results']=entry;s['validated_artifacts'].update(aircraft_a78_report=rel(REPORT),aircraft_a78_results=rel(OUT/'composite_qualification_review.json'),aircraft_a78_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A78'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A78+AIRCRAFT-A79 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==197
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),
        'harness':h,'new_native':0,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A79'})
    print(json.dumps({'A78_registered':True,'registry':197,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['declare','prepare','register'])
    globals()[parser.parse_args().action]()
