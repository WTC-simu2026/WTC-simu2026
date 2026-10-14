"""Seal two failed Starter preparations and the conditional omission of both CHECKs."""
from run_aircraft_a75_TYPE7_compatibility import ROOT,OUT,CFG,AUTH,read,dump,sha,now,rel,guard
from build_aircraft_a54_graph import harness
from pathlib import Path
import json,re,collections

REPORT=OUT/'rapport_aircraft_a75.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A75_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A76_2026-10-14.md'


def route():
    return ('AIRCRAFT-A76 : audit en lecture seule du nouvel échec d’initialisation TYPE7 A75 et proposition '
        'ciblée après publication A74+A75 vérifiée. Les deux Starter autorisés ont échoué avec916erreurs612 '
        'sur l’interface2 et11avertissements (10IBAG614 +1pénétrations343) ; aucun Engine exécuté. '
        'Les deux places CHECK restent conditionnellement inutilisées, non réaffectées et sans nouveau crédit Starter. '
        'Les cinq TYPE7/gaps0,5/5mm sont imprimés et masse/ADMAS conservés, mais aucun restart initial qualifié. '
        'La valeur Inacti1000 ne porte pas le même contrat entreTYPE25 etTYPE7 : ne pas désactiver globalement '
        'des contacts ni déplacer des nœuds pour forcer un passage. Inspecter le filtrage de voisinage/paires initiales '
        'et IBAG sans volume surveillé, préparer une différence exacte et un nouveau lot borné avec accord distinct. '
        'Moteur A73 conservé, zéro correctif/compilation/GPU/installation ; critères et anciens échecs inchangés. '
        'Les107391 avertissements et budgets physiques entiers restent bloquants. '
        'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.')


def assess():
    c=guard();assert not REPORT.exists()
    runs=read(OUT/'native_execution_review.json')
    assert runs['new_Starter']==2 and runs['new_Engine']==0 and runs['Engine_conditionally_unused']==2
    assert len(list(OUT.rglob('starter.execution.json')))==2 and not list(OUT.rglob('engine.execution.json'))
    message_rows=[]
    for case in c['cases']:
        d=OUT/case['case'];g=read(d/'Starter_gate_review.json');execution=read(d/'starter.execution.json')
        assert not g['pass'] and execution['exit_code']==2 and not execution['timed_out']
        assert execution['CPU_threads']==1 and execution['cap_s']==180 and not execution['GPU']
        assert g['mass_g']==191273837.9425 and g['prescribed_ADMAS_g']==100368522.1367
        listing=d/(case['name']+'_0000.out');text=listing.read_text(encoding='utf8')
        header=list(re.finditer(r'^(ERROR|WARNING) ID\s*:\s*(\d+)\s*$',text,re.M))
        events=[]
        for i,m in enumerate(header):
            block=text[m.end():header[i+1].start() if i+1<len(header) else len(text)]
            interface=re.search(r'-- INTERFACE ID:\s*(\d+)',block)
            event={'kind':m[1],'message_ID':int(m[2]),'interface_ID':int(interface[1]) if interface else None}
            if m[1]=='ERROR' and int(m[2])==612:
                a=re.search(r'SECONDARY NODE\s+(\d+)\s+IS ON THE MAIN SURFACE',block)
                b=re.search(r'IMPOSSIBLE TO CALCULATE NEW COORDINATES OF SECONDARY NODE\s+(\d+)',block)
                p=re.search(r'INITIAL PENETRATION\s*=\s*([\d.E+\-]+)',block)
                event.update(printed_secondary_number=int(a[1]) if a else None,
                    printed_failed_move_number=int(b[1]) if b else None,
                    printed_initial_penetration_mm=float(p[1]) if p else None,
                    native_message_INACTI_0='INACTI = 0' in block,
                    numeric_label_domains_not_assumed_equivalent=True)
            elif m[1]=='WARNING' and int(m[2])==343:
                n=re.search(r'THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS',block)
                node_count=re.search(r'CONCERNING\s+(\d+)\s+NODES',block)
                event.update(initial_penetrations=int(n[1]) if n else None,concerning_nodes=int(node_count[1]) if node_count else None)
            events.append(event)
        counts=collections.Counter((e['kind'],e['message_ID']) for e in events)
        assert counts=={('ERROR',612):916,('WARNING',614):10,('WARNING',343):1}
        assert {e['interface_ID'] for e in events if e['kind']=='ERROR'}=={2}
        failures=[e for e in events if e['kind']=='ERROR']
        assert all(e['native_message_INACTI_0'] for e in failures)
        warning=next(e for e in events if e['message_ID']==343)
        record={'created_utc':now(),'case':case['case'],'listing':rel(listing),'listing_sha256':sha(listing),
            'counts':[{'kind':k,'message_ID':v,'count':n} for (k,v),n in sorted(counts.items())],
            'failure_interface_IDs':[2],'initial_penetration_warning':warning,
            'all_612_messages_print_INACTI0':True,'input_and_parameter_summary_INACTI1000_preserved':True,
            'printed_node_domains_unqualified':True,'events':events,'new_native':0}
        dump(d/'initialization_message_audit.json',record)
        message_rows.append({k:v for k,v in record.items() if k!='events'})
    dump(OUT/'initialization_message_review.json',{'created_utc':now(),'cases':message_rows,
        'two_strict_Starter_failures_preserved':True,'new_native':0,'Engine_CHECK_omitted_as_authorized':True})
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[];binaries=[]
    for row in old:
        p=ROOT/row['path'];s=p.stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
        if '/isolated_exec/engine_' in row['path']:
            assert sha(p)==row['sha256'];binaries.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),
        'old_Engines_rehashed':binaries,'changed_paths':changed,'all_old_files_rehashed':False,
        'old_native_diagnostics_replayed':False,'archive_not_rescanned':True,'old_failed_gates_and_budgets_preserved':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A75','status':'completed_two_failed_TYPE7_Starter_controls__zero_conditional_CHECK',
        'explicit_authorization':c['authorization'],'new_Starter':2,'new_Engine':0,'Starter_remaining':0,
        'Engine_conditionally_unused':2,'unused_slots_not_reassigned':True,
        'Starter_errors_per_case':916,'Starter_warnings_per_case':11,
        'error612_count_per_case':916,'error612_interface_ID':2,'warning614_IBAG_per_case':10,
        'warning343_initial_penetration_per_case':1,'initial_penetration_counts':[r['initial_penetration_warning'] for r in message_rows],
        'five_TYPE7_parameter_summaries_read':True,'declared_gaps_mm':[.5,5.],
        'mass_g_each':191273837.9425,'prescribed_ADMAS_g_each':100368522.1367,
        'mass_and_ADMAS_totals_pass':True,'mass_redistributed_tensor_or_inertia_equivalence_not_assumed':True,
        'input_and_parameter_summary_INACTI1000_vs_error_message_INACTI0':True,
        'fresh_native_initial_restart_qualified':False,'Starter_strict_gate_pass':False,
        'TYPE25_TYPE7_dynamic_equivalence_qualified':False,'source_Engine_patch_compilation_GPU_installation':False,
        'binary_sha256_unchanged':c['binary_sha256'],'whole_CHECK_pass':False,'whole_dynamic_extension':False,
        'all_old_failed_gates_and_mass_material_inertia_budgets_preserved':True,'RKE_added':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A76'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,
        'initialization_messages':'initialization_message_review.json','whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    table='\n'.join(f"| {r['case']} | {read(OUT/r['case']/'starter.execution.json')['wall_s']:.3f} | 916 | 11 | omis |" for r in runs['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A75 — deux préparations TYPE7 échouées, CHECK omis

Les deux Starter autorisés sont terminés avec erreur. Aucun Engine lancé, conformément à la condition stricte de la proposition A74. Sources, erreurs, critères et budgets conservés ; aucun impact entier prolongé.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, exécuter les deux préparations et CHECK conditionnels A75 », lié aux empreintes avant lancement. Deux nouveaux Starter CPU1/plafond180s, sans délai dépassé, moteur A73 inchangé et aucun correctif/compilation/GPU/installation. Les entrées sont les copies A74 exactes, vérifiées avant lancement.

| Cas | Durée(s) | Erreurs | Avertissements | CHECK |
|---|---:|---:|---:|---|
{table}

Chaque cas imprime cinq TYPE7 et les paramètres déclarés, dont les gaps0,5mm/5mm. Masse191273837,9425g et ADMAS100368522,1367g égales aux totaux de référence, ainsi que les centres imprimés ; ce résultat ne qualifie pas le tenseur redistribué ni les inerties. Aucun restart initial propre produit.

Les916erreurs612 concernent uniquement l’interface2, auto-contact de la peau du radôme. Elles signalent des nœuds secondaires sur la surface principale et une impossibilité de calcul de nouvelles coordonnées, avec INACTI=0 dans le message. L’entrée et le résumé de paramètres impriment pourtant1000 : le résumé seul n’est donc pas le contrat effectif d’initialisation. Les deux nombres de nœuds imprimés dans chaque message sont conservés sans supposer leur domaine ou leur égalité.

Les11avertissements se décomposent en dix614 (IBAG activé sans volume surveillé puis remis à zéro, deux passages pour les cinq interfaces) et un343, qui compte4430pénétrations initiales sur1968nœuds de l’interface2. Le lecteur ne dispose pas d’un inventaire de paires initiales achevé dans ces sorties ; ce critère reste échoué.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les [définitions TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) et [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) montrent que Inacti1000 ne signifie pas le même traitement des pénétrations initiales entre les deux familles. A74 avait conservé la valeur sans présumer d’équivalence dynamique ; A75 établit nativement que cette variante d’initialisation échoue. Aucun résultat de documentation n’est substitué aux messages natifs.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée, aucune vidéo source réanalysée ni dégâts connus ciblés. Les copies de modèle et logiciels sont distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102100, zéro tirage ; unitésg/mm/ms et cartes mécaniques A74 conservées. La variante de contact est explicite et rejetée par ses critères. Les valeurs de gap imprimées ne suffisent pas à valider les paires, recherche, pénalité ou transfert d’efforts. Aucun nœud d’entrée déplacé, contact entier désactivé, matière/masse/inertie ou RKE ajouté pour forcer un passage. Les tentatives natives de coordonnées rapportées par le Starter ne sont pas un état initial validé.

## 5. Résultats dérivés

Les deux portes Starter sont échouées. Les deux CHECK autorisés seulement sous condition sont omis, leurs places ne sont ni consommées comme Engine ni réaffectées à de nouvelles préparations. Deux Starter consommés, zéro restant ; deux places CHECK conditionnellement inutilisées. La nouvelle cause concerne le filtrage initial de l’auto-contact2 et l’option IBAG sans volume surveillé. Il faut une proposition ciblée fondée sur ces données et le contrat de voisinage, sans nouvelle exécution dans le lotA75.

## 6. Contradictions et informations manquantes

Aucune compatibilité entière ou équivalence dynamique validée. Les paramètres natifs effectifs d’initialisation et le domaine des nombres de nœuds restent à tracer par source ; aucun domaine inventé. Les107391 avertissements de préconditionnement A73 restent bloquants, ainsi que inerties, matériaux, bilans et intégration A52. Les échecs TYPE25 antérieurs, gardeTT0 ratée A71 et variante A75 restent conservés. Nouveau lot Starter requiert un accord distinct ; les places CHECK inutilisées ne l’autorisent pas. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A75 → AIRCRAFT-A76\n\nRapport : '+rel(REPORT)+
        '\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+
        rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+' et '+rel(HANDOFF)+
        '.\nÉtat local prioritaire, aucun calcul en cours. Vérifier publication A74+A75 avant nouvelle itération.\n'+
        route()+'\nNouvelles courtes en français ; ne pas rejouer les diagnostics déjà vérifiés.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a75*.py'))
    files+=[CFG,AUTH,HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_output_script_only_no_AGPL_raw_source_binary':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A75_assessed':True,'Starter_pass':False,'new_Starter':2,'new_Engine':0,'two_CHECK_conditionally_omitted':True}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==['AIRCRAFT-A74']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A75','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A75',next_iteration='AIRCRAFT-A76',current_status=a['status'],
        next_objective=route(),updated_at=stamp);s['aircraft_a75_key_results']=row
    s['validated_artifacts'].update(aircraft_a75_report=rel(REPORT),aircraft_a75_results=rel(OUT/'composite_qualification_review.json'),aircraft_a75_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A74','AIRCRAFT-A75'],pending_count=2,updated_at=stamp,
        next_publication_after='AIRCRAFT-A74+AIRCRAFT-A75 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==194
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,
        'files_verified':len(m['files']),'harness':h,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A76'})
    print(json.dumps({'A75_registered':True,'registry':194,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['assess','register'])
    globals()[parser.parse_args().action]()
