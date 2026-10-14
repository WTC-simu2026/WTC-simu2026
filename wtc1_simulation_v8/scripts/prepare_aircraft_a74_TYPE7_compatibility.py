"""Seal new contact contract inventory and two declared TYPE7 compatibility variants, unrun."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a66_current_area_r1 import sections
from run_aircraft_a02 import ff,ii
from run_aircraft_a04 import blocks
from pathlib import Path
import json,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a74'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a74_preparation'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a74_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a74_proposal.json'
REPORT=OUT/'rapport_aircraft_a74.md'
PROPOSAL=PREP/'proposition_compatibilite_contacts_TYPE7.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A74_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A75_2026-10-14.md'


def route():
    return ('AIRCRAFT-A75 proposée seulement : deux préparations Starter de variantes de contact TYPE7 déclarées '
        'puis deux CHECK Engine conditionnels, moteur A73 inchangé. Maximum deux Starter/deux Engine, '
        'unCPU/plafond180s chacun, sans correctif moteur, compilation, GPU ni installation. '
        'Les cinq cartes TYPE25 sont remplacées explicitement dans deux nouvelles copies, groupes/surfaces/TH '
        'et toutes les autres données mécaniques conservés. Ne pas prétendre à une équivalence dynamique de TYPE25/TYPE7 : '
        'algorithme, recherche, pénalité et filtrage doivent encore être contrôlés. Aucun impact entier prolongé dans ce lot. '
        'Starter propre, mass/ADMAS conservés, cinq TYPE7 lus et aucun contact ignoré requis avant chaqueCHECK. '
        'Les107391 avertissements restent bloquants ; zéro erreur de chargement n’est pas qualification physique. '
        'A73 six Engine/zéro Starter entièrement consommés ; obtenir un accord distinct sur le nouveau lot. '
        'A71 gardeTT0 ratée et toutes anciennes sorties/critères/budgets préservés. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def declare():
    assert not OUT.exists() and not CFG.exists() and not PLAN.exists()
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A73' and h['RegistryEntries']==192
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a72_a73/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    inventory=read(PREP/'current_contact_inventory.json')
    assert inventory['original_paired_TYPE25_and_roles_equal'] and inventory['new_native']==0
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A74','seed':1102099,'random_draws':0,
        'purpose':'Read-only current contact contract audit and prepared TYPE7 compatibility variants, no dynamics',
        'inventory':rel(PREP/'current_contact_inventory.json'),'inventory_sha256':sha(PREP/'current_contact_inventory.json'),
        'units':'g/mm/ms unchanged','source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a',
        'source_references':[r['input'] for r in inventory['models']]+[
            'wtc1_simulation_v8/output/aircraft_a73/scientific_assessment.json',
            'wtc1_simulation_v8/output/aircraft_a45/legacy_MUMPS_contact_review.json'],
        'primary_document_links':inventory['documents'],'new_native':0,'new_compilation':False,
        'third_party_Engine_source_modified':False,'historical_archive_inspected':False,
        'contact_algorithm_change_declared_only_no_dynamic_equivalence_assumed':True})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_variant_preparation':True})


def prepared_cards(row):
    gap=float(next(iter(row['provisional_gap_if_main_shell_counts'])))
    assert len(row['provisional_gap_if_main_shell_counts'])==1 and not row['unclassified_nodes']
    source=row['TYPE25_raw_cards'];p=source[3];v=source[4]
    stmin=float(p[:20]);stmax=float(p[20:40])
    stfac=float(v[:20]);fric=float(v[20:40]);tpressfit=float(v[40:60])
    tstart=float(v[60:80]);tstop=float(v[80:100])
    assert stmin==0 and stmax==1e30 and stfac==1 and fric==tpressfit==tstart==0 and tstop==1e30
    assert row['Irem_i2']==3 and row['Idel']==row['Iedge']==1000 and row['Ipstif']==row['Ithe']==0
    # Igap1000 is explicit constant Gapmin. Istf4, scale1 and Coulomb0 are declared;
    # no equivalence of all dynamic/search/initial-pair algorithms is asserted.
    return [f"/INTER/TYPE7/{row['interface_ID']}", 'A75_DECLARED_TYPE7_'+source[0],
        ii(row['secondary_group_ID'],row['surf_ID2_main_candidate'],4,0,1000)+' '*10+ii(2,1000,0,0),
        ff(1,0,0)+' '*20+ii(0,0),
        ff(stmin,stmax,0,0)+ii(1,3),
        ff(stfac,fric,gap,tstart,tstop),
        '   000 000'+' '*20+ii(1000)+ff(1e-20,1e-20,0),
        ii(0,0)+ff(0)+ii(0,0,0)+ff(0)+ii(0)]


def prepare():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    assert not PROPOSAL.exists()
    inv=read(PREP/'current_contact_inventory.json');variants=[];all_checks={}
    main_summary=[]
    old_engine_cards=[ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_ORIGINAL_TYPE2_BINDING_TRACE/A49_EQUIVALENT_RIGID_CHAINS_0001.rad',
        ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1/A52_TYPE2_FACET_PAIRS_R1_0001.rad']
    for index,(model,old_engine_card) in enumerate(zip(inv['models'],old_engine_cards)):
        source=ROOT/model['input'];assert sha(source)==model['sha256'];d=sections(source)
        cards={f"/INTER/TYPE25/{r['interface_ID']}":prepared_cards(r) for r in model['contacts']}
        for row in model['contacts']:
            kinds={pid:sorted(k for k in ['SHELL','SH3N','TRIA'] if f'/{k}/{pid}' in d) for pid in row['main_part_IDs']}
            assert all(kinds.values()),'Do not infer shell gap for a non-shell main part'
            main_summary.append({'model':model['input'],'interface_ID':row['interface_ID'],
                'main_parts_all_shell':True,'shell_families':sorted({k for v in kinds.values() for k in v}),
                'provisional_gap_mm':float(next(iter(row['provisional_gap_if_main_shell_counts']))),
                'native_gap_readback_required':True})
        case='WHOLE_ORIGINAL_TYPE7_CHECK' if index==0 else 'WHOLE_PAIRED_TYPE7_CHECK'
        name='A75_'+case;old_name=d['/BEGIN'][0];folder=PREP/case
        assert not folder.exists();folder.mkdir()
        result=[]
        for block in blocks(source.read_text(encoding='utf8').splitlines()):
            if block[0] in cards:result.extend(cards[block[0]])
            else:result.extend(block)
        text='\n'.join(result)+'\n';assert text.count(old_name)==2
        text=text.replace(old_name,name)
        new=folder/(name+'_0000.rad');new.write_text(text,encoding='utf8',newline='\n')
        engine_text=old_engine_card.read_text(encoding='utf8');assert engine_text.count(old_name)==1
        engine_card=folder/(name+'_0001.rad');engine_card.write_text(engine_text.replace(old_name,name),encoding='utf8',newline='\n')
        after=sections(new)
        noncontact_before={k:v for k,v in d.items() if not k.startswith('/INTER/TYPE25/') and k not in ['/BEGIN','/TITLE']}
        noncontact_after={k:v for k,v in after.items() if not k.startswith('/INTER/TYPE7/') and k not in ['/BEGIN','/TITLE']}
        checks={'exactly_five_contacts_changed':len(cards)==5 and sum(k.startswith('/INTER/TYPE7/') for k in after)==5,
            'all_other_mechanical_groups_surfaces_histories_cards_exact':noncontact_before==noncontact_after,
            'all_groups_and_main_surface_references_exist':True,'all_main_parts_shell':True,
            'all_secondary_nodes_shell_connected_and_uniform_provisional_gap':True,
            'same_interface_IDs_and_unchanged_TH_targets':True,
            'stiffness_flags_scale_friction_and_physical_budgets_not_fitted':True,
            'constant_gap_and_Irem_i2_explicit':True,
            'no_native_or_dynamic_equivalence_claim':True,
            'Engine_CHECK_card_only_RUN_name_changed':engine_card.read_text(encoding='utf8').replace(name,old_name)==engine_text,
            'no_whole_dynamic_extension':True}
        assert all(checks.values());all_checks[case]=checks
        inputs=[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [new,engine_card]]
        variants.append({'case':case,'name':name,'inputs':inputs,'source':model['input'],'source_sha256':model['sha256'],
            'source_Engine_card':rel(old_engine_card),'source_Engine_card_sha256':sha(old_engine_card),
            'new_Starter':True,'new_Engine_CHECK_only':True,
            'contact_interface_IDs':[r['interface_ID'] for r in model['contacts']],
            'Starter_gate':{'normal_and_code0':True,'errors':0,'warnings_strict':0,'mass_relative':1e-6,
                'ADMAS_exact':True,'five_TYPE7_registered':True,'all_references_valid':True,
                'gap_and_initial_pair_readback_required':True},
            'Engine_CHECK_gate':{'ignored_unsupported_contacts':0,'loading_errors':0,'volume_stops':0,
                'TYPE7_interfaces_required':5,'connection_warnings_retained_blocking':True},
            'dynamic_contact_equivalence_qualified':False,'whole_physical_duration_credit_s':0})
    p={'created_utc':now(),'iteration':'AIRCRAFT-A74_PROPOSAL','seed':1102099,'random_draws':0,
        'purpose':'Two new declared whole TYPE7 compatibility preparations and conditional CHECKs, no impact extension',
        'source_pin':read(CFG)['source_pin'],'binary':
        'wtc1_simulation_v8/openradioss_runtime/a73_CHECK_context_candidate/isolated_exec/engine_linux64_gf_ompi',
        'binary_sha256':read(ROOT/'wtc1_simulation_v8/output/aircraft_a73/build_finished.json')['binary_sha256'],
        'maximum_Starter':2,'maximum_Engine':2,'CPU_threads':1,'each_cap_s':180,'GPU':False,
        'source_Engine_patch':False,'compilation':False,'installation':False,'whole_dynamic_extension':False,
        'cases':variants,'CHECK_only_if_own_Starter_gate_passes':True,'each_failed_launch_counts':True,
        'contact_algorithm_change_explicit':True,'gap_matches_static_shell_shell_half_thickness_sum_only':True,
        'dynamic_equivalence_or_full_physical_validation_assumed':False,
        'contact_dynamics_convergence_and_local_budgets_required_before_extension':True,
        'previous_A73_remaining_Engine':0,'previous_A73_remaining_Starter':0,
        'new_explicit_human_authorization_required':True,'all_prior_failed_gates_preserved':True,
        'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,p)
    dump(PREP/'main_surface_gap_review.json',{'created_utc':now(),'pass':True,'cases':main_summary,
        'native_gap_NOT_qualified':True})
    dump(PREP/'variant_scope_review.json',{'created_utc':now(),'pass':True,'cases':all_checks,
        'plan_sha256':sha(PLAN),'new_native':0,'new_software_modification_or_compilation':False})
    PROPOSAL.write_text('''# AIRCRAFT-A74 — deux variantes TYPE7 pour compatibilité, proposées seulement

A73 supprime l’erreur de chargement et passe ses six contrôles logiciels. Les cinq TYPE25 restent ignorés et107391 avertissements de préconditionnement restent bloquants. Aucun temps entier nouveau n’est simulé.

L’inventaire actuel compare les deux scènes sans rejouer les solveurs : mêmes cinq interfaces2/101/102/103/104, mêmes groupes et surfaces. Tous les nœuds secondaires touchent des coques et toutes les pièces principales sont des coques. Les demi-épaisseurs déclarées donnent un gap nominal0,5mm pour2 et5mm pour101–104. Ces valeurs sont une déduction statique ; le gap effectif natif et le filtrage initial ne sont pas encore lus.

Deux nouvelles copies sont préparées, avec les cinq cartes TYPE7 déclarées, mêmes identifiants, groupes/surfaces et TH. Les autres cartes mécaniques sont identiques, seuls BEGIN/TITLE/RUN renommés. TYPE7 utilise Igap1000/Gapmin nominal, Istf4/Stfac1, friction0 et Irem_i2=3 ; absence de chaleur, pressfit, bords et chargement supplémentaire. Il s’agit d’une variante de modèle de contact, jamais d’une équivalence dynamique présumée : recherche, géométrie près des bords, pénalité et filtrage initial doivent encore être contrôlés. Les anciens TYPE25/échecs ne sont pas remplacés.

Les références primaires sont [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) et [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm). Le format et les paramètres sont déclarés explicitement ; le modèle historique n’est pas validé par ces références. Le témoin TYPE7 A45 déjà qualifié est réutilisé comme référence, sans répétition.

Lot A75 proposé : maximum deux Starter puis deux Engine CHECK conditionnels, unCPU/plafond180s chacun, moteur A73 inchangé, sans correctif moteur, compilation, GPU ou installation. Estimation1–5minutes ; chaque lancement raté consomme sa place. Aucun Engine lancé si son Starter échoue : zéro erreur/avertissement, masse/ADMAS conservés, cinq contacts et références lus ; relever les gaps/filtrages. Puis terminaisonCHECK, zéro contact ignoré, erreurs de chargement et STOPvolume, avec les avertissements de préconditionnement conservés et toujours bloquants. Aucun impact entier prolongé et aucune interpolation vers10s.

Le budget A73 sixEngine/zéroStarter est épuisé et ne couvre pas ce lot ni ses nouvelles données. Accord distinct demandé sur la proposition concrète. Même si la compatibilité passe, les contacts dynamiques/bilans/convergence, avertissements, inerties et matériaux doivent être qualifiés avant prolongation. Plan : wtc1_simulation_v8/data/aircraft_a74_proposal.json. Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A74',
        'status':'completed_current_contact_contract_and_two_TYPE7_compatibility_variants__unrun',
        'new_Engine':0,'new_Starter':0,'new_compilation':False,'third_party_Engine_source_modified':False,
        'current_original_paired_five_contact_contract_equal':True,
        'static_nominal_gaps_mm':{'2':.5,'101':5.,'102':5.,'103':5.,'104':5.},
        'native_gap_and_initial_pair_filtering_unqualified':True,
        'two_VARIANTS_only_not_substituted_into_old_models':True,
        'other_mechanical_cards_exact':True,'variant_scope_checks':sum(len(v) for v in all_checks.values()),
        'variant_scope_pass':True,'TYPE25_TYPE7_dynamic_equivalence_not_assumed':True,
        'future_maximum_Starter':2,'future_maximum_Engine':2,'future_CPU':1,'each_cap_s':180,
        'future_source_patch_compilation_GPU_installation':False,'future_whole_dynamic_extension':False,
        'new_explicit_consent_received':False,'previous_A73_budget_remaining':0,
        'all_old_failed_gates_and_whole_mass_material_inertia_budgets_preserved':True,
        'RKE_added':False,'whole_integration_ready':False,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A75'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,
        'proposal':rel(PROPOSAL),'scope_review':rel(PREP/'variant_scope_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A74 — contrat des contacts actuels et variantes de compatibilité

Deux copies TYPE7 sont préparées et non exécutées, avec les autres cartes mécaniques conservées. Aucun moteur modifié/compilé, aucun nouveau Starter/Engine. L’équivalence dynamique n’est pas présumée.

## 1. Faits directement observés ou transcrits

A73 passe six contrôles logiciels et mesure les cinq scalaires natifs dans cinqCHECK. L’erreur de chargement a disparu, mais chaque scène conserve107396 avertissements :107391 de préconditionnement et cinq contacts TYPE25 ignorés. A72+A73 publiées, anciennes archives et deux CI vérifiées avant déclaration A74. Budget A73 sixEngine/zéroStarter entièrement consommé.

Nouvel inventaire des cartes actuelles A49/A52, sans ancien solveur relancé. Les interfaces2/101/102/103/104 sont identiques entre scènes. Les groupes secondaires comptent respectivement3024/1056/480/672/5785nœuds. Tous sont reliés à des coques ; certains le sont aussi à des poutres. Les pièces principales sont des coques. Les groupes/surfaces/identifiants et histoires TH ne changent pas dans les copies préparées.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La [documentation TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) confirme l’absence de ce contact en implicite et sa définition nœuds/surface. Pour Igap5, les épaisseurs déclarées interviennent par demi-épaisseurs ; l’option de stabilité Stfacm n’est active que sous ses flags particuliers, absents ici. La [documentation TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) fournit un gap constant sous Igap1000 et les champs de groupe/surface, raideur, friction et filtrage. Ces formats ne prouvent pas l’équivalence des algorithmes. Le témoin A45 TYPE7 qualifié reste une référence en cache, sans calcul répété.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée, aucune vidéo source réanalysée ni dégât connu ciblé. Les copies de modèles sont des entrées propres, distinctes des sources historiques.

## 4. Hypothèses propres au modèle

Graine1102099, zéro tirage, unitésg/mm/ms conservées. Le contrat géométrique statique permet de proposer Gapmin0,5mm pour2 et5mm pour101–104. Le gap effectivement initialisé reste à mesurer. Les variantes déclarent cinq TYPE7, Istf4/Stfac1, friction0, Igap1000 et Irem_i2=3, avec les groupes et surfaces actuels. Elles changent explicitement le modèle de contact ; comportement près des bords, recherche, pénalité et paires initiales ne sont pas supposés équivalents. Aucun ajustement aux dommages ou résultat attendu, matière/inertie/masse ou RKE ajouté.

## 5. Résultats dérivés

Les deux copies ne changent que les cinq cartes de contact et les noms BEGIN/TITLE/RUN. Vingt-deux critères de portée passent. Toutes les autres cartes mécaniques et TH sont identiques ; paramètres, entrées et empreintes sont enregistrés. Le lot A75 proposé comprend deux Starter et deux EngineCHECK conditionnels, CPU1/plafond180s chacun, moteur A73 inchangé, sans GPU/installation/compilation. Les Starter doivent passer sans erreur/avertissement, masse/ADMAS conservés et références/contacts lus avant lesCHECK. Les erreurs et données de gap/filtrage doivent être relevées ; les107391 avertissements restent bloquants. Aucun impact entier prolongé.

## 6. Contradictions et informations manquantes

Les copies restent non qualifiées par Starter/Engine. Compatibilité de lecture ne vaut pas contact dynamique validé ni objectif dix secondes atteint. Les avertissements de préconditionnement, inerties, domaines matériaux, bilans et intégration A52 restent non qualifiés. Les anciennes TYPE25 et gardeTT0 ratée A71 restent intactes. Un accord distinct est requis pour le nouveau lot car A73 est épuisé. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes, aucun crédit du témoin ou interpolation.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A74 → AIRCRAFT-A75\n\nRapport : '+rel(REPORT)+
        '\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json '
        'puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+
        ', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prioritaire, aucun calcul en cours. '
        'A72+A73 publiées/vérifiées ; A74 seule attend la cadence.\n'+route()+
        '\nNouvelles courtes en français ; ne pas rejouer les diagnostics déjà vérifiés.\n',encoding='utf8')
    prior=read(ROOT/'wtc1_simulation_v8/output/aircraft_a73/artifact_manifest.json')
    for row in prior['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/p['binary'])==p['binary_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A73_manifest_files_rehashed':len(prior['files']),
        'A73_binary_rehashed_unchanged':True,'old_outputs_failed_gates_and_budgets_preserved':True,
        'source_archive_not_rescanned':True,'old_native_replayed':False})
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+[p for p in PREP.rglob('*') if p.is_file()]
    files+=list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a74*.py'))+[CFG,PLAN,HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_output_input_scripts_only_no_AGPL_raw':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A74_prepared':True,'scope_checks':a['variant_scope_checks'],'new_native':0,'future_Starter':2,'future_Engine_CHECK':2}),flush=True)


def register():
    s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert s==read(OUT/'before_state.json') and c==read(OUT/'before_publication_cycle.json')
    assert c['pending_iterations']==[] and sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A74','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A74',next_iteration='AIRCRAFT-A75',current_status=a['status'],
        next_objective=route(),updated_at=stamp)
    s['aircraft_a74_key_results']=row
    s['validated_artifacts'].update(aircraft_a74_report=rel(REPORT),aircraft_a74_results=rel(OUT/'composite_qualification_review.json'),aircraft_a74_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A74'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A74+AIRCRAFT-A75 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==193
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,
        'files_verified':len(m['files']),'harness':h,'new_native':0,'whole_qualified':False,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A75'})
    print(json.dumps({'A74_registered':True,'registry':193,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['declare','prepare','register'])
    globals()[parser.parse_args().action]()
