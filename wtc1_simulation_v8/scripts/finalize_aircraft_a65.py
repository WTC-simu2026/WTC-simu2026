"""Seal full-recording refined free passes and the observed whole-model CHECK failures."""
from run_aircraft_a65_sampling import ROOT,OUT,CFG,read,dump,sha,now,rel,harness
import json

REPORT=OUT/'rapport_aircraft_a65.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A65_HANDOFF.md'

def route():
    return ('AIRCRAFT-A66 : audit borné en lecture seule des nouveaux messages CHECK A65, '
      'des624éléments60001–60624 et des cinq contacts TYPE25, puis de leurs branches sources natives. '
      'Réutiliser les sorties A65 sans nouveau Starter/Engine, sans patch/compilation ni modification des budgets. '
      'Distinguer un contrôle volumique appliqué à une surface valide d’une géométrie réellement invalide ; '
      'ne pas supprimer les messages ou substituer silencieusement les contacts. Préparer ensuite la proposition concrète nécessaire. '
      'A65 quatre contrôles autorisés exécutés : local libre raffiné PASS, scènes entières quinze erreurs affichées/624STOPvolume/cinqTYPE25 ignorés chacune. '
      'Les échecs au repos/imposés A62, temporels grossiers A63 et lecteur incomplet A64 restent préservés. '
      'Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes. '
      'Toute nouvelle modification/compilation du moteur exige un accord explicite distinct.')

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    cfg=read(CFG);free=read(OUT/'free_cohesive_qualification_review.json');whole=read(OUT/'whole_CHECK_message_review.json')
    assert free['pass'] and not whole['pass']
    executions=list(OUT.rglob('engine.execution.json'));assert len(executions)==4
    assert len(list(OUT.rglob('starter.execution.json')))==2
    for path in executions:
        r=read(path);assert r['CPU_threads']==1 and r['cap_s']==180 and not r['GPU'] and r['binary_sha256']==cfg['binary_sha256']
    changed=[];old=read(OUT/'preservation_before_metadata.json')['files']
    for row in old:
        s=(ROOT/row['path']).stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'changed_paths':changed,
         'old_manifests_and_failures_preserved':True,'all_old_files_rehashed':False,'old_native_diagnostics_replayed':False,'archives_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A65','status':'completed_full_recording_refined_free_convergence_pass__whole_CHECK_failed',
       'new_Engine_runs':4,'new_Starter_runs':2,'authorized_A65_maximum_native':4,'A65_controls_remaining':0,
       'new_source_patch_software_changes_or_compilation':False,'prior_budgets_not_reset':True,
       'free_boolean_checks_pass':sum(len(r['checks']) for r in free['cases']),'refined_free_composite_pass':True,
       'maximum_energy_residual_J':max(r['maximum_energy_residual_J'] for r in free['cases']),
       'maximum_support_momentum_residual_Ns':max(r['maximum_support_momentum_residual_Ns'] for r in free['cases']),
       'maximum_half_dt_difference_J':max(r['maximum_difference_J'] for r in free['half_dt_energy_comparisons']),
       'unchanged_half_dt_tolerance_J':free['half_dt_energy_comparisons'][0]['tolerance_J'],
       'each_actual_terminal_field_ms':[r['actual_saved_terminal_ms'] for r in free['cases']],
       'whole_CHECK_cases':[{'case':r['case'],'printed_error_count':r['printed_error_count'],'printed_warning_count':r['printed_warning_count'],
            'STOP_volume_count':r['STOP_volume_message_count'],'TYPE25_ignored':r['TYPE25_ignored'],'pass':r['pass']} for r in whole['cases']],
       'whole_CHECK_pass':False,'A52_integrated':False,'whole_mass_material_budgets_changed':False,'RKE_added':False,
       'A62_A63_A64_failed_criteria_preserved':True,'physical_free_elastic_scope_only':True,
       'mixed_damage_large_rotations_native_state_rollback_and_whole_unqualified':True,
       'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A66'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'free':'free_cohesive_qualification_review.json',
       'whole_initial_parser':'whole_CHECK_review.json','whole_observed_messages':'whole_CHECK_message_review.json',
       'legacy_review_budget_field_describes_prior_A62_A63_lot':12,'current_A65_separately_authorized_maximum':4,'whole_dynamic_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    table='\n'.join(f"| {r['case']} | {r['native_rows']} | {r['actual_saved_terminal_ms']} | {r['maximum_energy_residual_J']:.10g} | {r['maximum_support_momentum_residual_Ns']:.10g} |" for r in free['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A65 — dynamique libre raffinée qualifiée, CHECK entier échoué

Les deux témoins passent22contrôles chacun et la comparaison demi-pas au seuil conservé. Les deux scènes entières terminent leur CHECK avec quinze erreurs affichées,624messages STOPvolume et cinq contactsTYPE25 ignorés chacune. Aucun crédit d’impact entier ni nouvelle compilation.

## 1. Faits directement observés ou transcrits

Accord humain explicite «Oui, exécuter ce lot A65» enregistré avec empreintes du plan/proposition/lanceur. Deux Starter propres et quatre Engine CPU1/cap180s, sansGPU/installation/compilation. Les sorties locales enregistrent8001 et16001lignes, chaque pas réellement calculé, et rejoignent1ms ; le second champ terminal provient des huit nœuds TH, car sa dernière animation reste0,995062ms. Aucune extrapolation.

| Cas libre | Lignes natives | Champ terminal ms | Résidu énergie J | Résidu impulsion/support Ns |
|---|---:|---:|---:|---:|
{table}

Les44contrôles locaux passent : formats binaires/CSV, cycles/horloges et pas, identité de déplacement/sécante, vitesse physique Newmark, KE/P natifs et bilans/supports, masse8g, masse ajoutée0, travail extérieur0, réponse discrète exacte, tractions, domaine élastique et supports. Comparaison KEmax={free['half_dt_energy_comparisons'][0]['maximum_difference_J']:.10g}J ; IEmax={free['half_dt_energy_comparisons'][1]['maximum_difference_J']:.10g}J ; seuil préexistant1,01e-5J.

Les deux CHECK utilisent exactement les anciennes initialisations/cartes originales et appariées, empreintes vérifiées. Les messagesSTOPvolume visent les624ID60001–60624 et concordent dans journal et listing. Chaque résumé affiche15ERRORS/5WARNINGS ; ce décompte n’est pas supposé égal aux624messages détaillés. TYPE25 ignoré cinq fois. Le code0/NORMAL n’est pas un passage. Le premier lecteur étroit cherchaitERROR(S) et STOPsans deux-points : ses champs null/false sont conservés, une nouvelle analyse reconnaît les messages réels.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Le moteurA62 inchangé est figé SHA256{cfg['binary_sha256']}. Le protocole Newmarkgamma0,5/beta0,25 et ses sources précédemment vérifiées servent au lecteur ; la référence analytique exacte n’est pas ajustée aux sorties. Un passage de ce domaine élastique libre ne valide pas toute la physique de l’impact.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF inspecté/modifié ; aucun dégât connu ciblé. Les sources logicielles et entrées propres au projet sont distinctes des archives historiques.

## 4. Hypothèses propres au modèle

Graine{cfg['seed']}, zéro tirage, unitésg/mm/ms. Les surfaces10×10mm, masse instrumentale8g, quatre nœuds supérieurs libres, vitesse initialeY1mm/ms, supports et propriétés A64 sont conservés. Pas0,000125/0,0000625ms, seuils inchangés. SeulsTFILEdt/2 et arrêt1+dt/2 changent pour enregistrer chaque cycle et sauvegarder la frontière cible, dans la borne d’un pas d’overshoot déjà déclarée. Les masses instrumentales ne fixent pas le futur pas d’avion ; propriétés de cohésion non identifiées comme mesures physiques réelles.

## 5. Résultats dérivés

Le défaut de sortieA64 est résolu dans ces nouveaux essais : les bilans physiques, la solution discrète exacte et la convergence temporelle au seuil déclaré passent simultanément. Le critère grossierA63 et l’analyse initialeA64 restent échoués/conservés. Les CHECK entiers montrent que le correctif d’assemblage surfacique ne suffit pas à rendre la scène entière admissible. Il faut localiser leurs contrôles géométriques et contacts incompatibles avant toute extension dynamique. Scripts, paramètres, horloges et messages sauvegardés ; anciens fichiers vérifiés par métadonnées, anciens étatsCHECK rehashés.

## 6. Contradictions et informations manquantes

Les erreursCHECK et contacts ignorés sont bloquants malgréNORMAL. A52nonintégré ; domaines matériaux, inerties, bilans locaux entiers, état/retour arrière, dommage général et grandes rotations restent non qualifiés. Échecs au repos et sous mouvements imposésA62 préservés. LotA65 de quatre Engine entièrement consommé ; aucun nouveau correctif moteur appliqué. Meilleur impact entier0,0200001220703125s, dix secondes physiques et vidéo3D incomplètes. Aucun RKE compensateur ni temps manquant fabriqué.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A65 → AIRCRAFT-A66\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    dump(OUT/'harness_after_calculation.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a65*.py'))+[CFG,ROOT/'wtc1_simulation_v8/data/aircraft_a65_authorization.json',HANDOFF]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'owned_outputs_only_no_AGPL_binary_or_raw_source':True,
       'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A65_assessed':True,'local_checks':44,'temporal_PASS':True,'whole_CHECK_PASS':False,'native_runs':4}),flush=True)

def register():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json')
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl') and cycle['pending_iterations']==['AIRCRAFT-A64']
    m=read(OUT/'artifact_manifest.json')
    for row in m['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A65','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
       'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
       'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as stream:stream.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A65',next_iteration='AIRCRAFT-A66',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a65_key_results']=row;state['validated_artifacts'].update(aircraft_a65_report=rel(REPORT),aircraft_a65_results=rel(OUT/'composite_qualification_review.json'),aircraft_a65_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A64','AIRCRAFT-A65'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A64+AIRCRAFT-A65 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==184
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':len(m['files']),
        'harness':h,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A66'})
    print(json.dumps({'A65_registered':True,'registry_entries':184,'pending_publication_count':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
