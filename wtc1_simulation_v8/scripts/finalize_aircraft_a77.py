"""Seal successful IBAG correction, ineffective local-neighbor hypothesis and conditional skips."""
from run_aircraft_a77_neighbor_policy_r1 import ROOT,OUT,CFG,AUTH,read,dump,sha,now,rel,guard
from build_aircraft_a54_graph import harness
from pathlib import Path
import re,json,collections

REPORT=OUT/'rapport_aircraft_a77.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A77_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A78_2026-10-14.md'


def route():
    return ('AIRCRAFT-A78 : audit géométrique/topologique en lecture seule des contacts initiaux A77, '
        'après publication A76+A77 vérifiée. IBAG0 supprime les dix614, mais Irem_gap2 natif confirmé '
        'ne résout aucune des916erreurs612 de l’auto-contact2 ;23520candidats et4430pénétrations initiales '
        'restent. Deux Starter autorisés consommés, zéro Engine ; deux CHECK conditionnellement inutilisés '
        'non réaffectés. Cartographier les numéros effectivement imprimés vers les faces/connexions '
        'du modèle et préparer une mesure de paires initiales si elles manquent, sans rejouer les anciens diagnostics. '
        'Ne pas désactiver globalement le contact, réduire le gap ou déplacer les nœuds pour forcer un passage. '
        'Moteur A73 inchangé ; tout nouveau lot natif/correctif/compilation nécessite une proposition et accord distinct. '
        'Préserver A75, Irem_gap2 raté, anciennes sorties, budgets et critères échoués. '
        'Les107391 avertissements et budgets physiques entiers restent bloquants. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def assess():
    c=guard();assert not REPORT.exists();runs=read(OUT/'native_execution_review.json')
    assert runs['new_Starter']==2 and runs['new_Engine']==0 and runs['Engine_conditionally_unused']==2
    assert len(list(OUT.rglob('starter.execution.json')))==2 and not list(OUT.rglob('engine.execution.json'))
    rows=[]
    for index,case in enumerate(c['cases']):
        d=OUT/case['case'];g=read(d/'Starter_gate_review.json');x=read(d/'starter.execution.json')
        assert not g['pass'] and g['errors']==916 and g['warnings']==1 and x['exit_code']==2 and not x['timed_out']
        assert x['CPU_threads']==1 and x['cap_s']==180 and not x['GPU']
        assert g['native_contact_readback']['2']['Irem_gap']==2 and g['checks']['native_initial_contact_inventory_printed']
        assert g['mass_g']==191273837.9425 and g['prescribed_ADMAS_g']==100368522.1367
        listing=d/(case['name']+'_0000.out');text=listing.read_text(encoding='utf8')
        events=[]
        heads=list(re.finditer(r'^(ERROR|WARNING) ID\s*:\s*(\d+)\s*$',text,re.M))
        for i,m in enumerate(heads):
            block=text[m.end():heads[i+1].start() if i+1<len(heads) else len(text)]
            ID=re.search(r'-- INTERFACE ID:\s*(\d+)',block)
            node=re.search(r'SECONDARY NODE\s+(\d+)\s+IS ON THE MAIN SURFACE',block)
            events.append({'kind':m[1],'message_ID':int(m[2]),'interface_ID':int(ID[1]) if ID else None,
                'printed_node':int(node[1]) if node else None})
        counts=collections.Counter((e['kind'],e['message_ID']) for e in events)
        assert counts=={('ERROR',612):916,('WARNING',343):1}
        assert {e['interface_ID'] for e in events}=={2}
        previous_case=read(ROOT/'wtc1_simulation_v8/data/aircraft_a75_predeclaration.json')['cases'][index]['case']
        previous=read(ROOT/'wtc1_simulation_v8/output/aircraft_a75'/previous_case/'initialization_message_audit.json')
        new_nodes=[e['printed_node'] for e in events if e['kind']=='ERROR']
        old_nodes=[e['printed_secondary_number'] for e in previous['events'] if e['kind']=='ERROR']
        assert new_nodes==old_nodes
        impacts={int(ID):int(count) for ID,typ,count in re.findall(r'INTERFACE NUMBER\.[^\n]*?(\d+)\s*\n\s*INTERFACE TYPE\.[^\n]*?(\d+)\s*\n\s*POSSIBLE IMPACT NUMBER:\s*(\d+)',text) if int(typ)==7}
        assert impacts=={2:23520,101:0,102:0,103:0,104:0}
        warning=re.search(r'THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS\s+\( CONCERNING\s+(\d+)\s+NODES',text)
        assert warning and list(map(int,warning.groups()))==[4430,1968]
        row={'case':case['case'],'listing':rel(listing),'listing_sha256':sha(listing),
            '916_same_printed_node_sequence_as_A75':True,'error612_interface_ID':2,
            'native_self_Irem_gap_printed':2,'possible_impacts':impacts,'initial_penetrations':4430,
            'concerning_nodes':1968,'IBAG_614_count':0,'events':events}
        dump(d/'initialization_message_audit.json',{'created_utc':now(),**row,'new_native':0})
        rows.append({k:v for k,v in row.items() if k!='events'})
    dump(OUT/'initialization_message_review.json',{'created_utc':now(),'cases':rows,'new_native':0,
        'local_neighbor_hypothesis_ineffective':True,'IBAG_warning_correction_pass':True,'no_Check_executed':True})
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[];binaries=[]
    for row in old:
        p=ROOT/row['path'];s=p.stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
        if '/isolated_exec/engine_' in row['path']:
            assert sha(p)==row['sha256'];binaries.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),
        'old_Engines_rehashed':binaries,'changed_paths':changed,'all_old_files_rehashed':False,
        'old_native_diagnostics_replayed':False,'historical_archive_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A77','status':'completed_two_failed_neighbor_Starter_controls__IBAG_fixed__self_errors_unchanged',
        'explicit_authorization':c['authorization'],'new_Starter':2,'new_Engine':0,'Starter_remaining':0,
        'Engine_conditionally_unused':2,'unused_slots_not_reassigned':True,'Starter_strict_gate_pass':False,
        'errors_per_case':916,'warnings_per_case':1,'IBAG614_removed':True,'IBAG614_count_per_case':0,
        'local_Irem_gap2_confirmed_but_ineffective':True,'same_916_printed_error_node_sequence_as_A75':True,
        'self_possible_impacts_per_case':23520,'self_initial_penetrations_per_case':4430,
        'self_concerning_nodes_per_case':1968,'five_TYPE7_parameters_and_impact_counts_read':True,
        'mass_ADMAS_totals_pass':True,'mass_g_each':191273837.9425,'ADMAS_g_each':100368522.1367,
        'native_redistributed_tensor_or_inertia_equivalence_not_assumed':True,
        'fresh_restart_initial_state_qualified':False,'source_Engine_patch_compilation_GPU_installation':False,
        'binary_sha256_unchanged':c['binary_sha256'],'whole_CHECK_pass':False,'whole_dynamic_extension':False,
        'all_prior_failed_gates_and_physical_budgets_preserved':True,'RKE_added':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A78'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'message_review':'initialization_message_review.json','whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    table='\n'.join(f"| {r['case']} | {read(OUT/r['case']/'starter.execution.json')['wall_s']:.3f} | 916 | 1 | omis |" for r in runs['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A77 — IBAG corrigé, filtrage de voisins inefficace

Les deux préparations autorisées échouent. IBAG0 supprime les dix avertissements614, mais Irem_gap2 ne résout pas les916erreurs612 de l’auto-contact2. Aucun Engine lancé, aucun impact entier prolongé.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, exécuter les préparations et CHECK conditionnels A77 », reçu request_user_input_async/call_432df3436b51458fb51e0780402fed83/0, lié aux empreintes avant lancement. Les entrées sont les variantes A76 exactes. Deux Starter CPU1/plafond180s, sans dépassement ; moteur A73 inchangé, aucun correctif/compilation/GPU/installation. Le pilote R0 non exécuté reste conservé ; R1 corrige deux noms d’artefacts avant déclaration, sans changer entrées, budgets ou lecteur.

| Cas | Durée(s) | Erreurs | Avertissements | CHECK |
|---|---:|---:|---:|---|
{table}

Les cinq TYPE7, gaps0,5/5mm et Irem_gap2 pour2 sont effectivement imprimés. Les quatre autres filtres restent1. Les10messages614 ont disparu. Chaque cas garde916erreurs612 et1message343, tous sur2 : même séquence de numéros de nœuds queA75,23520impacts possibles et4430pénétrations initiales concernant1968nœuds. Aucun restart initial propre. Masse191273837,9425g et ADMAS100368522,1367g égales aux références ; cela ne qualifie pas le tenseur redistribué ou les inerties.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. La proposition A76 s’appuyait sur des sources et définitions de filtre local, sans présumer son efficacité sur les faces distinctes reliéesTYPE2. Le nouveau résultat natif rejette cette hypothèse dans ce modèle : le flag est lu mais les erreurs ne changent pas. Aucune modification des sources logicielles.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée/modifiée ou vidéo source réanalysée ; aucun dégât connu ciblé. Les variantes propres restent distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102102, zéro tirage ; unitésg/mm/ms et budgets mécaniques conservés. IBAG2→0 et filtre local1→2 constituent la variante explicitement autorisée. Aucun contact ou nœud désactivé globalement, gap réduit, nœud déplacé, force/matière/inertie/masse ou RKE ajouté. Le paramètre passé n’est pas une garantie du comportement initial ; les916erreurs restent un critère échoué.

## 5. Résultats dérivés

La correction IBAG est vérifiée séparément ; la règle de voisinage est inefficace dans les deux modèles. Le lecteur A76 lit la table d’impacts et les flags sans modifier les anciens refus A75. Les deux portes strictes Starter restent échouées ; les deux CHECK conditionnels sont omis, places inutilisées non réaffectées. Deux Starter consommés, zéro restant. La prochaine analyse doit cartographier la géométrie/topologie et les paires initiales avant toute nouvelle variante, en conservant cette nouvelle tentative ratée.

## 6. Contradictions et informations manquantes

Les listes exactes de paires fautives, leur relation aux faces séparées/liaisons et la qualification dynamique restent manquantes. Les107391 avertissements A73, inerties, matériaux, bilans et intégration entière demeurent bloquants. Les anciennes TYPE25 et gardeTT0 ratéeA71 sont conservées. Aucun nouveau lot couvert par les places CHECK inutilisées. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A77 → AIRCRAFT-A78\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+' et '+rel(HANDOFF)+'.\nÉtat local prioritaire, aucun calcul en cours. Vérifier publication A76+A77 avant nouvelle itération.\n'+route()+'\nNouvelles courtes en français ; aucun ancien diagnostic natif rejoué.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a77*.py'))
    files+=[CFG,AUTH,ROOT/'wtc1_simulation_v8/data/aircraft_a77_driver_derivation.json',ROOT/'wtc1_simulation_v8/data/aircraft_a77_driver_derivation_r1.json',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_scripts_only_no_AGPL_raw':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A77_assessed':True,'IBAG_warning_fixed':True,'neighbor_policy_failed':True,'new_Starter':2,'new_Engine':0}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==['AIRCRAFT-A76']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A77','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A77',next_iteration='AIRCRAFT-A78',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a77_key_results']=row;s['validated_artifacts'].update(aircraft_a77_report=rel(REPORT),aircraft_a77_results=rel(OUT/'composite_qualification_review.json'),aircraft_a77_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A76','AIRCRAFT-A77'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A76+AIRCRAFT-A77 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==196
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),
        'harness':h,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A78'})
    print(json.dumps({'A77_registered':True,'registry':196,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['assess','register'])
    globals()[parser.parse_args().action]()
