"""Seal the approved seventh isolated Engine and all eight controls, retaining whole CHECK failure."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a67'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a67_predeclaration.json'
CONTROL=ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json'
REPORT=OUT/'rapport_aircraft_a67.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A67_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A68_2026-10-14.md'

def route():
    return ('AIRCRAFT-A68 : audit borné en lecture seule des deux nouveaux CHECK A67 et des sources figées du même moteur. '
        'Tracer la création/normalisation de DIAG_M, la branche de chargement LB/R2 et le rôle des 75 nœuds de translation signalés ; '
        'examiner séparément les cinq contacts TYPE25 ignorés et leur équivalence mécanique éventuelle. '
        'Réutiliser les sorties A67, sans nouveau Starter/Engine ni modification/compilation. /IMPL/DYNA/2 est déjà présent dans les cartes. '
        'Ne pas ajouter de force fictive, masquer les messages, changer RREF ou les seuils sans preuve et protocole déclaré. '
        'A67 est compilée ; les huit Engine autorisés sont consommés. Six témoins locaux passent dans leur domaine déclaré, '
        'dont aire évolutive limitée à Y libre. Les deux CHECK entiers échouent chacun : une erreur de chargement implicite, '
        '107391 avertissements de connexion possible et cinq TYPE25 ignorés ; les 624 STOP de volume sont résolus. '
        'A52 reste non intégrée, aucun impact entier prolongé. Toute nouvelle modification/compilation ou nouveau lot natif '
        'nécessite une proposition concrète et un accord distinct. Préserver budgets, sorties, échecs et bilans sans RKE compensateur. '
        'Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D restent incomplètes.')

def assess():
    assert not REPORT.exists()
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    assert sha(CONTROL)==read(OUT/'controls_guard.json')['sha256']
    cfg=read(CFG);ctrl=read(CONTROL);built=read(OUT/'build_finished.json')
    local=read(OUT/'current_area_mechanical_review.json');work=read(OUT/'quadrature_work_review.json');whole=read(OUT/'whole_CHECK_review.json');detail=read(OUT/'whole_CHECK_classification.json')
    assert built['build_success'] and built['within_original_hour'] and local['pass'] and work['pass']
    assert len(local['cases'])==6 and not whole['all_clean'] and not detail['pass']
    assert sha(ROOT/cfg['current_area_patch']['proposed_source'])==cfg['current_area_patch']['proposed_sha256']
    assert sha(ROOT/cfg['current_area_patch']['patch'])==cfg['current_area_patch']['patch_sha256']
    assert sha(ROOT/built['candidate_directory']/'isolated_exec/engine_linux64_gf_ompi')==built['binary_sha256']
    runs=list(OUT.rglob('engine.execution.json'));assert len(runs)==8 and len(list(OUT.rglob('starter.execution.json')))==6
    for p in runs:
        e=read(p);assert e['CPU_threads']==1 and e['cap_s']==180 and not e['GPU'] and e['binary_sha256']==built['binary_sha256']
    old=read(OUT/'preservation_before_metadata.json')['files'];changed=[];binary_checks=[]
    for r in old:
        p=ROOT/r['path'];s=p.stat()
        if s.st_size!=r['bytes'] or s.st_mtime_ns!=r['mtime_ns_before']:changed.append(r['path'])
        if '/isolated_exec/engine_' in r['path']:
            assert sha(p)==r['sha256'],r['path'];binary_checks.append(r['path'])
    assert not changed and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(old),'changed_paths':changed,
        'old_Engines_rehashed':binary_checks,'all_old_outputs_rehashed':False,'old_native_diagnostics_replayed':False,'archives_not_rescanned':True,
        'whole_input_hashes_verified_at_launch':True,'old_failures_and_physical_budgets_preserved':True})
    count=sum(len(r['checks']) for r in local['cases'])
    a={'created_utc':now(),'iteration':'AIRCRAFT-A67','status':'completed_seventh_current_area_Engine_local_scoped_PASS__whole_CHECK_failed',
        'source_pin':cfg['source_pin'],'exact_A66_patch_applied':True,'build_success':True,'build_wall_s':built['wall_s_from_original_start'],
        'build_CPU':6,'GPU':False,'new_installation':False,'Starter_rebuilt':False,'binary_sha256':built['binary_sha256'],
        'new_Engine_runs':8,'new_Starter_runs':6,'authorized_maximum_Engine_runs':8,'controls_remaining':0,'prior_budgets_not_reset':True,
        'local_case_checks_pass':count,'full_quadrature_work_pass':True,'five_free_cases_pass':True,'variable_area_Y_only_pass':True,
        'variable_area_global_prescribed_X_KE_P_qualified':False,'native_local_TH_terminal_ms':[r['last_TH_ms'] for r in local['cases']],
        'maximum_scope_energy_residual_J':max(r['maximum_scope_energy_residual_J'] for r in local['cases']),
        'maximum_scope_support_momentum_residual_Ns':max(r['maximum_scope_momentum_residual_Ns'] for r in local['cases']),
        'half_dt_energy_comparisons':local['half_dt_energy_comparisons'],
        'whole_CHECK_cases':detail['cases'],'whole_CHECK_pass':False,'whole_volume_STOPs_per_scene':0,
        'whole_loading_errors_per_scene':1,'possible_free_connection_DOF_per_scene':107391,'rotational_DOF_per_scene':107166,
        'translational_DOF_per_scene':225,'TYPE25_ignored_per_scene':5,'whole_total_warnings_per_scene':107396,
        'A52_integrated':False,'whole_mass_material_or_inertia_budgets_changed':False,'RKE_added':False,
        'all_prior_failed_criteria_preserved':True,'exact_Jacobian_damage_rollback_large_rotation_whole_not_qualified':True,
        'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A68'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'local':'current_area_mechanical_review.json',
        'full_quadrature_work':'quadrature_work_review.json','whole':'whole_CHECK_classification.json','whole_dynamic_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    table='\n'.join(f"| {r['case']} | {len(r['checks'])} | {r['last_TH_ms']} | {r['maximum_scope_energy_residual_J']:.8g} | {r['maximum_scope_momentum_residual_Ns']:.8g} |" for r in local['cases'])
    REPORT.write_text(f'''# AIRCRAFT-A67 — aire courante compilée, contrôle entier toujours refusé

Le septième moteur isolé applique exactement le correctif A66 autorisé. Six témoins locaux passent dans leur domaine déclaré ; les deux CHECK entiers ne signalent plus les 624 volumes nuls, mais restent échoués. Aucun prolongement d’impact entier.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, appliquer et compiler ce correctif A66 » et empreintes du plan, de la proposition, de la différence et de la source enregistrés avant exécution. Première compilation réussie en {built['wall_s_from_original_start']:.3f} s, plafond 3600 s, six CPU, sans GPU ni installation ; Starter non recompilé. Source pin {cfg['source_pin']}, binaire SHA256 {built['binary_sha256']}. Anciennes corrections autorisées conservées ; ancienne branche Ismstr1 byte à byte préservée. Huit Engine sur un CPU avec plafond 180 s chacun, six Starter propres : budget entièrement consommé, aucun replay.

| Témoin | Critères locaux | Dernier TH ms | Résidu énergie dans le domaine J | Résidu impulsion/support Ns |
|---|---:|---:|---:|---:|
{table}

Les {count} critères locaux passent, ainsi que les deux comparaisons demi-pas au seuil inchangé 1,01e-5 J : KE 5,47014241452e-6 J, IE 5,49140000000e-6 J. Chaque TH atteint réellement 1 ms. Les cinq cas à translations supérieures libres qualifient leurs bilans globaux ; le sixième prescrit X commun et qualifie seulement Y libre. Son aire évolue de 100 à 110 mm². Les anciens indicateurs génériques « all_top_translations_free » ne décrivent pas ce sixième cas ; les métadonnées initiales restent conservées et une clarification explicite accompagne les cartes réelles.

Dans chaque CHECK entier : code 0, NORMAL et fin du CHECK, mais une erreur « IMPLICIT LOADING DATA », 107391 avertissements de connexion possible et cinq TYPE25 ignorés, soit 107396 avertissements. Zéro avertissement de raideur nulle, zéro STOPvolume et aucun STOP66. Les 107391 directions sont 35722 de chaque rotation et 75 de chaque translation. La valeur native R2 du chargement n’est pas imprimée. Les cartes contiennent déjà /IMPL/DYNA/2. Les anciennes initialisations et cartes entières sont identiques, empreintes vérifiées. Le premier champ CHECK_errors=null est conservé ; les messages détaillés et décomptes affichés déterminent l’échec.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les routines natives du pin déclaré servent à distinguer construction de matrice, forces/histoires de matériau et règles CHECK. La matrice ajoutée utilise les quatre aires Gauss projetées de la face médiane courante pour TYPE43/LAW117/Ismstr4. Elle ne lit pas VOL de référence. Le message générique ISOLID0 reste présent ; sa présence n’annule pas la sélection particulière vérifiée. Ces résultats logiciels ne valident pas une reconstruction historique de l’impact.

## 3. Affirmations provenant des archives locales

Aucune archive historique, vidéo, photographie ou PDF consulté ou modifié. Aucun dommage connu n’est ciblé. Les surfaces et matériaux instrumentaux sont distincts de mesures réelles d’une jonction Boeing/façade.

## 4. Hypothèses propres au modèle

Graine {cfg['seed']}, zéro tirage. Unités g/mm/ms, force N, énergie native N·mm convertie en J. Masse instrumentale 8 g sans masse ajoutée. Les variantes testent demi-pas, orientation initiale rigide, aire multipliée par quatre, trapèze à petite amplitude et aire évolutive prescrite. La matrice reste symétrique EN/ET, sans dérivée d’aire, de repère ou de dommage : matrice d’itération, pas jacobien exact. Aucun seuil physique assoupli, volume fictif, force de chargement ajoutée ou terme RKE compensateur.

## 5. Résultats dérivés

Les sorties binaires/CSV et tous les pas sont vérifiés. Les vitesses physiques libres sont reconstruites par la relation Newmark, confrontées aux bilans natifs et à la référence indépendante. Le trapèze est comparé à la limite de petite amplitude, sans qualification non linéaire générale. La rotation teste la covariance d’orientation initiale, pas une grande rotation dynamique. Le travail complet aux quatre points, utilisant chaque saut interpolé, est analysé séparément et passe au seuil préexistant ; l’ancien diagnostic par saut moyen reste préservé et n’est pas supposé exact pour le trapèze. Les 624 erreurs volumiques observées en A65 sont résolues dans les deux CHECK, mais les contrôles restants ne sont pas admissibles. Les anciennes sorties sont vérifiées par métadonnées et les six anciens moteurs isolés par empreinte.

## 6. Contradictions et informations manquantes

Les avertissements de connexion possible ne prouvent pas encore une déconnexion géométrique : DIAG_M doit être suivi depuis sa construction et normalisation. L’erreur de chargement ne prouve pas que la vitesse initiale est absente ; LB/R2 nécessite un audit distinct. Les cinq contacts TYPE25 ignorés demeurent bloquants. A52 reste non intégrée. Dommage général, retour arrière d’état, rotation dynamique, inerties, domaines matériaux et bilans locaux entiers non qualifiés. X prescrit dans le témoin évolutif ne qualifie pas les compteurs globaux KE/P ; échecs A62/A63/A64 et tous les budgets antérieurs préservés. Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D incomplètes. Aucun temps de témoin crédité à l’objectif.

{route()}
''',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A67 → AIRCRAFT-A68\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'composite_qualification_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('''Reprends WTC1 dans C:/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an.
Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement :
- wtc1_simulation_v8/output/aircraft_a67/rapport_aircraft_a67.md
- wtc1_simulation_v8/output/aircraft_a67/scientific_assessment.json
- wtc1_simulation_v8/output/aircraft_a67/whole_CHECK_classification.json
- harness/handoffs/WTC1_AIRCRAFT_A67_HANDOFF.md
L’état local actuel prime. Ne rejoue ni compilation ni diagnostics natifs A67 : les huit Engine autorisés sont consommés ; aucun calcul en cours. Vérifie le statut de publication A66+A67 avant une nouvelle itération.
'''+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a67*.py'))
    files += [CFG,CONTROL,ROOT/'wtc1_simulation_v8/data/aircraft_a67_authorization.json',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'owned_output_and_scripts_only_AGPL_binary_raw_source_patch_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A67_assessed':True,'local_criteria':count,'whole_CHECK_pass':False,'native_remaining':0}),flush=True)

def register():
    state=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert state==read(OUT/'before_state.json') and cycle==read(OUT/'before_publication_cycle.json')
    assert cycle['pending_iterations']==['AIRCRAFT-A66'] and sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    m=read(OUT/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256'],r['path']
    a=read(OUT/'scientific_assessment.json');stamp=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A67','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    state.update(current_iteration='AIRCRAFT-A67',next_iteration='AIRCRAFT-A68',current_status=a['status'],next_objective=route(),updated_at=stamp)
    state['aircraft_a67_key_results']=row
    state['validated_artifacts'].update(aircraft_a67_report=rel(REPORT),aircraft_a67_results=rel(OUT/'composite_qualification_review.json'),aircraft_a67_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A66','AIRCRAFT-A67'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A66+AIRCRAFT-A67 verified')
    for p,v in [(ROOT/'harness/state.json',state),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==186
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':len(m['files']),
        'harness':h,'whole_impact_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A68'})
    print(json.dumps({'A67_registered':True,'registry_entries':186,'pending_publication_count':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
