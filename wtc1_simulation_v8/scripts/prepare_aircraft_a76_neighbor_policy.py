"""Read-only A76 proposal: no-airbag initialization and local self-neighbor filtering, unrun."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a66_current_area_r1 import sections
from run_aircraft_a04 import blocks
from run_aircraft_a02 import ii
from pathlib import Path
import json,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a76'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a76_initial_contact_source_audit'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a76_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a76_proposal.json'
REPORT=OUT/'rapport_aircraft_a76.md'
PROPOSAL=PREP/'proposition_filtrage_voisinage_local_TYPE7.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A76_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A77_2026-10-14.md'


def route():
    return ('AIRCRAFT-A77 proposée seulement : deux nouveaux Starter et deux CHECK Engine conditionnels '
        'sur variantes A76 exactes, unCPU/plafond180s chacun, moteur A73 inchangé. '
        'IBAG2→0 dans cinq cartes et Irem_gap1→2 seulement pour l’auto-contact2 ; '
        'tous les autres paramètres, groupes/surfaces, gaps0,5/5mm et cartes mécaniques conservés. '
        'Pas de désactivation globale de nœuds/contact ni Inacti1/2/3/5/6, coordonnées ou compensation RKE modifiées. '
        'Hypothèse de filtrage local de voisins, non qualifiée nativement et non équivalence dynamique TYPE25/TYPE7. '
        'Lecteur propre réparé pour tables d’impacts séparées et chronologie des messages, ancien lecteur/échecs A75 conservés. '
        'Deux Starter A75 épuisés ; deux CHECK inutilisés conditionnellement ne couvrent pas de nouveaux Starter. '
        'Accord distinct requis pour le nouveau lot ; aucun correctif moteur, compilation, GPU ou installation, '
        'aucun prolongement d’impact entier. Starter sans erreur/avertissement, masse/ADMAS/gaps/flags/contacts lus '
        'avant chaque CHECK ;107391 avertissements de préconditionnement toujours bloquants. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def declare():
    assert not any(p.exists() for p in [OUT,CFG,PLAN])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A75' and h['RegistryEntries']==194
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a74_a75/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    assert read(PREP/'cached_message_and_inventory_review.json')['pass']
    assert read(PREP/'own_Starter_reader_preparation_review.json')['pass']
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A76','seed':1102101,'random_draws':0,
        'purpose':'New A75 initialization-failure source audit and exact neighbor-policy proposal only',
        'source_references':['wtc1_simulation_v8/output/aircraft_a75/initialization_message_review.json',
            rel(PREP/'source_manifest.json'),rel(PREP/'source_manifest_supplement_r1.json'),
            rel(PREP/'cached_message_and_inventory_review.json')],
        'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a',
        'Windows_Starter_source_equivalence_not_assumed':True,'units':'g/mm/ms unchanged',
        'new_native':0,'source_Engine_patch_compilation_GPU_installation':False,
        'historical_archive_inspected':False,'full_dynamic_equivalence_qualified':False})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_variant_preparation':True})


def source_audit():
    names=['hm_read_inter_type07.F','definter.F','i7pwr3.F','get_list_remnode.F90']
    texts={n:(PRIVATE/n).read_text(encoding='utf8') for n in names}
    checks={'IBAG_without_volume_warns614_then_zero':all(s in texts[names[0]] for s in ['IF (IBAG/=0.AND.NVOLU==0','MSGID=614','IBAG=0']),
        'sentinel1000_normalizes_to_zero_in_operational_default_path':'IF(IVAL == 1000 .AND. IS_DEFAUT_1000 ) IVAL = 0' in texts['definter.F'],
        'parameter_print_path_separate':'FLAG == 1 .AND. IPRINT == 1' in texts['definter.F'],
        '612_uses_zero_direction_guard':all(s in texts['i7pwr3.F'] for s in ['IF(DN<=EM30)','IF (INACTI==0)','MSGID=612']),
        'move_line_precedes_612_message':texts['i7pwr3.F'].index('WRITE(IOUT,1100)')<texts['i7pwr3.F'].index('MSGID=612'),
        'pair_local_neighbor_list_by_main_segment':all(s in texts['get_list_remnode.F90'] for s in ['sqrt(two)','local_remnode','local_kremnode','dist1']),
        'source_binary_equivalence_not_assumed':True,'no_source_applied_or_compiled':True}
    assert all(checks.values())
    dump(PREP/'pinned_source_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,
        'sources':[{'private_copy':rel(PRIVATE/n),'sha256':sha(PRIVATE/n)} for n in names],
        'related_pinned_Starter_source_NOT_claimed_identical_to_Windows_binary':True,
        'actual_A75_native_messages_remain_authoritative':True})


def prepare():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'] and not REPORT.exists()
    source_audit();old_plan=read(ROOT/'wtc1_simulation_v8/data/aircraft_a74_proposal.json')
    variants=[];scope_rows=[]
    for index,case in enumerate(old_plan['cases']):
        source=ROOT/case['inputs'][0]['path'];original=sections(source)
        assert sha(source)==case['inputs'][0]['sha256']
        replacements={};changes=[]
        for key,values in original.items():
            if not key.startswith('/INTER/TYPE7/'):continue
            ID=int(key.split('/')[-1]);v=list(values)
            assert len(v[1])==100 and int(v[1][60:70])==2
            before=v[1];v[1]=v[1][:60]+ii(0)+v[1][70:]
            changes.append({'interface_ID':ID,'field':'IBAG','before':2,'after':0,'fixed_columns_1based':[61,70]})
            if ID==2:
                assert len(v[3])==100 and int(v[3][80:90])==1
                v[3]=v[3][:80]+ii(2)+v[3][90:]
                changes.append({'interface_ID':ID,'field':'Irem_gap','before':1,'after':2,'fixed_columns_1based':[81,90]})
            replacements[key]=v
        assert len(replacements)==5 and len(changes)==6
        key='WHOLE_ORIGINAL_NEIGHBOR_CHECK' if index==0 else 'WHOLE_PAIRED_NEIGHBOR_CHECK'
        name='A77_'+key;folder=PREP/key;assert not folder.exists();folder.mkdir()
        lines=[]
        for block in blocks(source.read_text(encoding='utf8').splitlines()):
            lines.extend([block[0]]+replacements[block[0]] if block[0] in replacements else block)
        text='\n'.join(lines)+'\n';old_name=original['/BEGIN'][0]
        assert text.count(old_name)==2;text=text.replace(old_name,name)
        new=folder/(name+'_0000.rad');new.write_text(text,encoding='utf8',newline='\n')
        old_engine=ROOT/case['inputs'][1]['path'];etext=old_engine.read_text(encoding='utf8')
        assert sha(old_engine)==case['inputs'][1]['sha256'] and etext.count(old_name)==1
        ec=folder/(name+'_0001.rad');ec.write_text(etext.replace(old_name,name),encoding='utf8',newline='\n')
        after=sections(new)
        assert set(after)==set(original)
        assert all(after[k]==v for k,v in original.items() if k not in replacements and k not in ['/BEGIN','/TITLE'])
        for k,v in replacements.items():assert after[k]==v
        checks={'six_field_changes_only_plus_BEGIN_TITLE_RUN_names':len(changes)==6,
            'all_other_mechanical_and_contact_cards_exact':True,'all_five_contacts_and_groups_surfaces_TH_retained':True,
            'no_global_node_or_interface_deactivation':True,'Inacti1000_and_gaps_unchanged':True,
            'only_self_interface_neighbor_policy_changed':True,'external_four_neighbor_flags_remain1':True,
            'mass_material_inertia_RKE_and_coords_unchanged':True,
            'Engine_CHECK_card_only_name_changed':ec.read_text(encoding='utf8').replace(name,old_name)==etext,
            'variant_and_dynamic_equivalence_unqualified':True,'old_A75_errors_NOT_relabelled':True}
        assert all(checks.values());scope_rows.append({'case':key,'checks':checks,'changes':changes})
        variants.append({'case':key,'name':name,'source_A74_variant':case['inputs'][0],
            'inputs':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [new,ec]],
            'contact_interface_IDs':[2,101,102,103,104],'expected_self_Irem_gap':2,
            'expected_other_Irem_gap':1,'new_Starter':True,'new_Engine_CHECK_only':True,
            'Starter_gate':case['Starter_gate'],'Engine_CHECK_gate':case['Engine_CHECK_gate'],
            'native_pair_local_exclusion_not_yet_measured':True,'dynamic_equivalence_qualified':False,'whole_credit_s':0})
    reader=read(PREP/'own_Starter_reader_preparation_review.json')
    p={'created_utc':now(),'iteration':'AIRCRAFT-A76_PROPOSAL','seed':1102101,'random_draws':0,
        'purpose':'New no-airbag and local self-neighbor filtering compatibility test, no dynamics',
        'cases':variants,'binary':old_plan['binary'],'binary_sha256':old_plan['binary_sha256'],
        'maximum_Starter':2,'maximum_Engine':2,'CPU_threads':1,'each_cap_s':180,'GPU':False,
        'compilation':False,'source_Engine_patch':False,'installation':False,'whole_dynamic_extension':False,
        'estimate_minutes':[1,5],'each_failed_launch_counts':True,'CHECK_only_if_own_Starter_gate_passes':True,
        'no_unbudgeted_retry_or_conditional_slot_reassignment':True,
        'prior_A75_Starter_remaining':0,'prior_A75_Engine_conditionally_unused':2,
        'new_explicit_human_authorization_required':True,'previous_UNUSED_CHECK_do_not_cover_new_Starter':True,
        'prepared_own_reader':reader['prepared_reader'],'prepared_own_reader_sha256':reader['prepared_reader_sha256'],
        'pair_labels_full_inventory_and_dynamic_equivalence_unqualified':True,
        'mechanical_gaps_forces_material_mass_inertia_and_RKE_not_fitted':True,
        'connection_warnings_remain_blocking':True,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,p)
    dump(PREP/'neighbor_policy_scope_review.json',{'created_utc':now(),'pass':True,'cases':scope_rows,
        'plan_sha256':sha(PLAN),'scope_checks':sum(len(r['checks']) for r in scope_rows),'new_native':0,
        'new_native_policy_not_qualified':True})
    PROPOSAL.write_text('''# AIRCRAFT-A76 — filtrage local de voisinage TYPE7, proposition seulement

A75 échoue dans les deux Starter :916erreurs612 sur l’auto-contact2,11avertissements dont dix614 liés à IBAG. Aucun Engine, restart initial qualifié ou temps entier crédité. Les deux Starter sont consommés ; les deux places CHECK conditionnellement inutilisées ne couvrent pas une nouvelle préparation.

La différence préparée change exactement six champs par modèle : IBAG2→0 pour les cinq TYPE7, et Irem_gap1→2 seulement pour l’auto-contact2. Toutes les autres cartes, coordonnées, masses/matériaux/inerties, groupes/surfaces, TH, gaps0,5/5mm, Istf4/Stfac1/friction0 et Inacti1000 restent identiques. BEGIN/TITLE/RUN sont renommés. Aucun contact ni nœud n’est désactivé globalement, aucune option Inacti1/2/3/5/6 n’est introduite.

Le filtrage proposé vise les voisins proches d’un segment de la surface d’auto-contact, au lieu d’une désactivation générale. Son effet réel sur les paires A75 reste inconnu, notamment avec les faces séparées et les liaisons TYPE2 ; aucune réussite ou équivalence dynamique n’est présumée. Les [définitions TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) décrivent ce filtre local. Les sources figées expliquent aussi la représentation1000 imprimée et sa normalisation0 opérationnelle ; leur identité avec le binaire Windows n’est pas revendiquée. Les messages natifs A75 restent prioritaires.

Le lecteur propre futur est préparé. Il lit séparément les paramètres et la table d’impacts : les sorties A75 impriment23520impacts possibles pour2 et0 pour101–104. Les916lignes de coordonnées impossibles précèdent leur message612 et portent le même numéro ; le décalage d’association du premier lecteur est conservé et corrigé en lecture seule. Les vrais916erreurs/11avertissements restent rejetés, sans nouveau calcul.

Lot A77 proposé : deux nouveaux Starter et au maximum deux Engine CHECK, seulement si chaque Starter passe. UnCPU/plafond180s chacun, moteur A73 inchangé, sans correctif moteur/compilation/GPU/installation. Estimation1–5minutes. Conserver strictement zéro erreur/avertissement Starter, masse/ADMAS, cinq contacts et paramètres lus, avant CHECK ; relever les inventaires imprimés. Les107391 avertissements de préconditionnement restent bloquants. Aucun impact entier prolongé, aucune suppression d’échec ou interpolation vers10s.

Accord distinct requis pour ce nouveau lot. Source/données préparées, aucune exécution A77. Compatibilité, paires effectivement exclues et dynamique des fragments restent à qualifier avant toute intégration. Plan : wtc1_simulation_v8/data/aircraft_a76_proposal.json. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A76','status':'completed_read_only_initial_contact_audit_and_neighbor_policy_proposal__unrun',
        'new_Engine':0,'new_Starter':0,'new_compilation':False,'third_party_source_modified':False,
        'pinned_source_scope_pass':True,'Windows_Starter_source_equivalence_not_assumed':True,
        'A75_failed_gates_and_old_reader_associations_preserved':True,
        'new_chronology_all916_preceding_node_numbers_match':True,
        'native_possible_impacts_per_case':{'2':23520,'101':0,'102':0,'103':0,'104':0},
        'own_reader_cached_validation_pass':True,'future_reader_native_policy_NOT_qualified':True,
        'proposed_changed_fields_each_model':6,'IBAG2_to0_each_five_interfaces':True,
        'only_self_Irem_gap1_to2':True,'all_other_cards_and_physical_budgets_preserved':True,
        'variant_scope_checks':sum(len(r['checks']) for r in scope_rows),'variant_scope_pass':True,
        'new_explicit_consent_received':False,'future_maximum_Starter':2,'future_maximum_Engine_CHECK':2,
        'future_CPU':1,'each_cap_s':180,'future_software_patch_compilation_GPU_installation':False,
        'future_whole_dynamic_extension':False,'native_pair_exclusion_and_dynamic_equivalence_unqualified':True,
        'R0_source_lookup_failure_and_partial_copies_preserved':True,'RKE_added':False,
        'whole_integration_ready':False,'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A77'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),
        'scope_review':rel(PREP/'neighbor_policy_scope_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A76 — audit de l’initialisation et filtrage local proposé

Audit en lecture seule de nouvelles sorties A75, proposition exacte non exécutée. Aucun nouveau Starter/Engine, moteur modifié/compilé ou temps entier simulé.

## 1. Faits directement observés ou transcrits

A75 échoue avec916erreurs/11avertissements dans chaque Starter ; ses deux CHECK conditionnels sont omis. Les deux préparations sont consommées. Le nouvel audit lit la table d’impacts séparée :23520possibles pour l’interface2 et0 pour101–104. Les lignes de coordonnées impossibles précèdent les messages612 : les916numéros concordent avec le message qui les suit. Le premier lecteur A75 avait associé la ligne suivante ; ses données et échecs restent intacts. La lecture réparée rejette toujours les vraies erreurs et avertissements.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Dix fichiers de sources Starter figées sont lus en copie privée AGPL ; aucune identité source/binaire Windows supposée. Le chemin opérationnel de valeurs par défaut normalise1000 en0, séparément du résumé imprimé. Le lecteur d’interface avertit614 puis remet IBAG à zéro sans volume surveillé. La routine de contrôle d’impacts émet612 quand la direction est nulle avec Inacti0 et écrit la ligne de coordonnées avant le message. Ces relations de source sont cohérentes avec A75 mais n’inventent pas un état natif non observé.

La [documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) décrit Irem_gap2 comme un filtrage local des voisins proches du segment, sans retirer le nœud du contact avec les autres segments. Cela justifie une nouvelle hypothèse à tester ; effet sur les faces distinctes reliées TYPE2 et dynamique après rupture restent inconnus.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée ni vidéo source réanalysée. Les lectures concernent seulement des sources logicielles en cache et les nouvelles sorties propres A75. A74+A75 publiées avec anciennes archives et deux CI vérifiées avant déclaration A76.

## 4. Hypothèses propres au modèle

Graine1102101, zéro tirage, unitésg/mm/ms inchangées. IBAG2→0 dans cinq cartes et Irem_gap1→2 uniquement pour l’auto-contact2 constituent la variante. Inacti1000, les autres contacts, paramètres/gaps, géométrie, groupes/surfaces, histoires, masses/matières/inerties restent identiques. Aucune désactivation globale, déplacement de coordonnées ou compensation RKE. Le filtre local est une hypothèse non qualifiée, sans ajustement aux dégâts connus ni preuve d’équivalence TYPE25/TYPE7.

## 5. Résultats dérivés

Les deux différences exactes, noms de cas et entrées futures sont préparés par empreintes. Vingt-deux critères de portée passent ; toutes les autres cartes mécaniques sont identiques. Le lecteur propre futur est vérifié sans écriture sur les deux sorties A75 en cache : il lit les flags et les tables séparées, tout en maintenant le refus916erreurs/11avertissements. Aucun ancien solveur rejoué.

Une préparation de supplément source R0 échoue sur un chemin de helper supposé ; ses trois copies correctes et script sont conservés. Une finition R1 réutilise ces copies, vérifie leurs empreintes et lit le vrai chemin du quatrième fichier. Aucun calcul ou code moteur affecté.

Lot A77 proposé : maximum deux Starter et deux EngineCHECK conditionnels, CPU1/plafond180s chacun, moteur A73 inchangé, sans correctif/compilation/GPU/installation et aucun impact entier prolongé. Avant chaqueCHECK : zéro erreur/avertissement Starter, masse/ADMAS, cinq contacts/gaps/flags et inventaires imprimés lus. Les107391 avertissements de préconditionnement restent bloquants.

## 6. Contradictions et informations manquantes

Aucune variante qualifiée nativement ; l’effet du filtre sur les paires de faces disjointes demeure inconnu. Les listes exactes de paires exclues et la dynamique après rupture ne sont pas établies par un simple compte de candidats. Les avertissements, inerties, matériaux, bilans et intégration entière restent non qualifiés. Nouveau lot soumis à accord distinct : deux Starter A75 épuisés et deux CHECK inutilisés ne peuvent devenir de nouvelles préparations. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A76 → AIRCRAFT-A77\n\nRapport : '+rel(REPORT)+
        '\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+
        rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+
        '.\nÉtat local prioritaire, aucun calcul en cours. A74+A75 publiées/vérifiées, A76 seule en attente de cadence.\n'+
        route()+'\nNouvelles courtes en français ; aucun ancien diagnostic natif rejoué.\n',encoding='utf8')
    previous=read(ROOT/'wtc1_simulation_v8/output/aircraft_a75/artifact_manifest.json')
    for row in previous['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/p['binary'])==p['binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A75_sealed_files_rehashed':len(previous['files']),
        'A73_binary_rehashed_unchanged':True,'A75_errors_unused_CHECK_slots_and_old_reader_preserved':True,
        'old_native_or_archives_replayed':False})
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[p for p in PREP.rglob('*') if p.is_file()]
    files+=list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a76*.py'))
    files+=[CFG,PLAN,ROOT/reader['prepared_reader'],HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_inputs_scripts_only_AGPL_raw_sources_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A76_prepared':True,'new_native':0,'scope_checks':a['variant_scope_checks'],'new_policy_unqualified':True}),flush=True)


def register():
    s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert s==read(OUT/'before_state.json') and c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==[]
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A76','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A76',next_iteration='AIRCRAFT-A77',current_status=a['status'],
        next_objective=route(),updated_at=stamp);s['aircraft_a76_key_results']=row
    s['validated_artifacts'].update(aircraft_a76_report=rel(REPORT),aircraft_a76_results=rel(OUT/'composite_qualification_review.json'),aircraft_a76_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A76'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A76+AIRCRAFT-A77 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==195
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,
        'files_verified':len(m['files']),'harness':h,'new_native':0,'whole_qualified':False,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A77'})
    print(json.dumps({'A76_registered':True,'registry':195,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['declare','prepare','register'])
    globals()[parser.parse_args().action]()
