"""Seal the bounded A79 observation separately from failed physical initialization."""
from run_aircraft_a79_pair_print import ROOT, OUT, CFG, AUTH, guard, read, dump, sha, now, rel
from build_aircraft_a54_graph import harness
import json

REPORT=OUT/'rapport_aircraft_a79.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A79_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A80_2026-10-15.md'


def route():
    return ('AIRCRAFT-A80 : après publication A78+A79 vérifiée, préparer en lecture seule une stratégie de contact '
        'pour les jointures cohésives initialement coïncidentes, à partir des paires réelles A79. '
        'Préserver les nœuds séparés voulus pour la rupture et les contacts après ouverture/refermeture ; '
        'ne pas fusionner les nœuds, réduire le gap, déplacer les coordonnées ou désactiver globalement le contact '
        'pour forcer une préparation propre. Écarter toute simple copie Inacti1000 entre TYPE25 et TYPE7. '
        'Définir des témoins distinctifs et vérifier les chemins sources avant de présenter un correctif concret. '
        'A79 consomme son unique Starter ; zéro Engine autorisé ou exécuté. Aucun autre lot natif/correctif logiciel '
        'ou compilation couvert par cet accord. Les916erreurs et deux avertissements A79 restent échoués, '
        'dont1164 supplémentaire dû à la sortie détaillée, sans modifier la prévision originale d’un avertissement. '
        'Conserver moteurs, sorties, budgets, critères échoués et107391avertissements A73. '
        'Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques puis vidéo3D incomplet.')


def assess():
    c=guard(); assert not REPORT.exists()
    r=read(OUT/'pair_listing_review.json'); x=read(OUT/'native_execution_review.json')
    g=read(OUT/c['case']/'Starter_gate_review.json')
    assert x['new_Starter']==1 and x['new_Engine']==0 and not x['execution']['timed_out']
    assert len(list(OUT.rglob('starter_launch_declaration.json')))==1
    assert not list(OUT.rglob('Engine_launch_declaration.json')) and not list(OUT.rglob('*_0001.rad'))
    assert not g['pass'] and g['errors']==916 and g['warnings']==2
    assert r['pass_observation'] is True, 'Do not seal a qualified observation when pair mapping has failed'
    assert r['same_error_node_sequence_as_A77'] is True
    assert g['mass_g']==191273837.9425 and g['prescribed_ADMAS_g']==100368522.1367
    changed=[]; pins=read(OUT/'preservation_before_metadata.json')['files']
    for row in pins:
        p=ROOT/row['path'];st=p.stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']: changed.append(row['path'])
    assert not changed and sha(ROOT/c['unchanged_A73_binary'])==c['unchanged_A73_sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(pins),
        'changed_paths':changed,'A73_binary_rehashed_unchanged':True,'old_native_replayed':False,
        'source_historical_archives_modified_or_rescanned':False})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A79',
        'status':'completed_detailed_native_pair_observation__physical_Starter_still_failed',
        'explicit_authorization':c['authorization'],'new_Starter':1,'new_Engine':0,'Starter_remaining':0,
        'wall_s':x['execution']['wall_s'],'CPU_threads':1,'cap_s':180,
        'native_pair_observation_pass':r['pass_observation'],'pair_listing_review':rel(OUT/'pair_listing_review.json'),
        'observed_error_pairs':r['error612_count'],'observed_additional_penetration_pairs':r['pair_count_1164'],
        'all_pair_tuples':r['total_initial_penetrations'],
        'all_error_pair_domains_verified':r['all_error612_pair_labels_and_native_geometry_verified'],
        'error_distinct_label_vertex_coincidences':r['error_secondary_coincident_with_distinct_main_vertex'],
        'zero_area_error_facets':r['zero_area_error_facets'],
        'eight_other_exact_coincidences_without_ERROR612_prevent_simple_causal_rule':True,
        'physical_Starter_pass':False,'errors':916,'warnings':2,'prior_predicted_warnings':1,
        'extra_warning1164_is_detailed_output_not_erased':True,
        'all_old_failed_gates_and_budgets_preserved':True,'mass_g':g['mass_g'],'ADMAS_g':g['prescribed_ADMAS_g'],
        'mass_center_mm':g['center_mm'],'redistributed_tensor_or_inertia_not_assumed_qualified':True,
        'software_patch_compilation_GPU_installation':False,'A73_binary_sha256_unchanged':c['unchanged_A73_sha256'],
        'whole_dynamic_extension':False,'whole_integration_ready':False,'RKE_added':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,
        'next_iteration':'AIRCRAFT-A80'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'pair_observation':r,
        'physical_initialization_qualified':False,'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text(f'''# AIRCRAFT-A79 — paires initiales mesurées, initialisation toujours échouée

L’unique observation autorisée est terminée en{x['execution']['wall_s']:.3f}s, sur unCPU, sous plafond180s. Les paires réellement imprimées et leur domaine géométrique sont contrôlés. Le Starter reste échoué avec916erreurs et2avertissements ; aucun Engine ou impact entier prolongé.

## 1. Faits directement observés ou transcrits

L’accord humain « bien, on reprends et on continue » répond à la proposition A79 et au rappel de sa portée. La déclaration conserve cette réponse et les empreintes exactes avant lancement. Une entrée A78 immuable est copiée ; ajout /IOFLAG Ipri5 et noms de cas constituent les seuls changements. Le binaire Starter Windows est inchangé et le moteur A73 n’est pas lancé. Code retour2, aucun dépassement du plafond. Les cinq paramètres TYPE7, gaps0,5/5mm et filtres sont toujours lus ; aucun restart initial propre.

Le détail d’observation est dans pair_listing_review.json et ses fichiers de paires référencés : coordonnées et connectivités natives imprimées, groupe secondaire et facettes déclarées sont comparés séparément. Premier exemple : secondaire50, segment37327/43926/43928/43925, puis pénétration0,5mm et ERROR612. La ligne de tuple précède la ligne de coordonnées impossibles puis l’erreur ; elle n’est pas associée au nœud suivant. Le numéro d’élément n’est pas confondu avec son indice interne.

Les4430tuples ont chacun un segment natif et une facette déclarée uniques, avec ordre exact des quatre sommets. Les48171coordonnées imprimées concordent avec l’entrée, écart absolu maximal0mm à cette précision. Les1296segments et3024nœuds secondaires sont contrôlés. Les916erreurs, portant676secondaires distincts, ont toutes une coïncidence exacte avec un sommet principal portant un autre numéro. Leurs916quads ne sont pas dégénérés ; aire triangulée de12686,35à36969,36mm², distance point–surface triangulée nulle. Les3514autres paires comportent aussi8coïncidences exactes sans ERROR612 : une règle causale fondée uniquement sur l’égalité des coordonnées serait excessive. Les432TYPE2 ont des groupes et surfaces imprimés, présence seulement.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat d’un modèle historique officiel. La documentation [IOFLAG](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/ioflag_starter_r.htm) définit l’impression détaillée ; la sortie réelle confirme IPRI5. Les sources logicielles figées éclairent l’ordre d’impression, sans revendication d’identité avec le binaire Windows. La documentation [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) et [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) n’attribue pas le même traitement initial à Inacti1000 : sa valeur numérique seule n’établit pas l’équivalence.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée et aucune vidéo source réanalysée. Aucun dégât connu utilisé comme cible. Les données propres, les sources logicielles et les observations natives restent distinctes de l’histoire réelle.

## 4. Hypothèses propres au modèle

Graine1102103, zéro tirage, unitésg/mm/ms. Les peaux des fragments du radôme ont été séparées pour autoriser la rupture via les joints existants ; une fusion de coordonnées identiques changerait ce mécanisme. Le graphe de surface n’est ni un rang de matrice ni une preuve de déconnexion mécanique. La présence de liaisons TYPE2 n’établit pas leur qualification dynamique. La norme de la direction de repositionnement dans la source liée ne constitue pas à elle seule une aire de facette.

## 5. Résultats dérivés

La réussite de l’observation est enregistrée séparément de l’échec de la préparation physique. Les données géométriques et tous les contrôles sont dans le JSON détaillé conservé, sans crédit de durée. Masse191273837,9425g, ADMAS100368522,1367g et centre identiques aux références ; cela ne valide pas le tenseur redistribué ou l’inertie native. Un Starter autorisé consommé, zéro restant ; aucun Engine autorisé, entrée Engine créée ou lancement.

## 6. Contradictions et informations manquantes

Le plan A78 prévoyait1avertissement. La sortie détaillée en émet2 : WARNING1164 liste3514pénétrations à direction calculable, en plus de WARNING343 qui compte4430pénétrations concernant1968nœuds. Avec916erreurs612,3514+916=4430. Le supplément diagnostique reste enregistré ; la prévision antérieure n’est pas réécrite. Les916erreurs, les2avertissements et la porte stricte restent échoués, même si les paires sont correctement observées. Les107391avertissements A73, contacts après séparation/refermeture, inerties, matériaux et bilans restent bloquants. Aucune nouvelle durée d’impact ; meilleur calcul entier0,0200001220703125s, dix secondes puis vidéo3D incomplètes.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A79 → AIRCRAFT-A80\n\nRapport : '+rel(REPORT)+'\nMesures : '+rel(OUT/'pair_listing_review.json')+'\nRésultats : '+rel(OUT/'scientific_assessment.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'pair_listing_review.json')+', '+rel(OUT/'scientific_assessment.json')+' et '+rel(HANDOFF)+'.\nÉtat local prioritaire, aucun calcul en cours. Vérifier publication A78+A79 avant nouvelle itération.\n'+route()+'\nNouvelles courtes en français ; aucun ancien diagnostic natif rejoué.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a79*.py'))
    files += [CFG,AUTH,HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_scripts_only_no_AGPL_raw':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A79_assessed':True,'observation_pass':True,'physical_Starter_pass':False}),flush=True)


def register():
    guard();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert cycle==read(OUT/'before_publication_cycle.json') and cycle['pending_iterations']==['AIRCRAFT-A78']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A79','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A79',next_iteration='AIRCRAFT-A80',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a79_key_results']=entry
    s['validated_artifacts'].update(aircraft_a79_report=rel(REPORT),aircraft_a79_results=rel(OUT/'composite_qualification_review.json'),aircraft_a79_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A78','AIRCRAFT-A79'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A78+AIRCRAFT-A79 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==198
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),
        'harness':h,'new_Starter':1,'new_Engine':0,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A80'})
    print(json.dumps({'A79_registered':True,'registry':198,'pending_publication':2}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register'])
    globals()[p.parse_args().action]()
