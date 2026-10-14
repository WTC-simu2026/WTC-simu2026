"""Seal the exact not-applied CHECK classification proposal after verified A68+A69 publication."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a70';PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a70_preparation_r4'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal_r4.json';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a70_predeclaration.json'
REPORT=OUT/'rapport_aircraft_a70.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A70_HANDOFF.md';PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A71_2026-10-14.md'

def route():
    return ('AIRCRAFT-A71 proposée, non appliquée/non compilée : huitième moteur isolé avec le correctif exact A70 de CHECK initial à résidu nul. '
        'Nouvel accord humain distinct requis avant toute modification/compilation, conformément à AGENTS.md. '
        'Ajout limité à quatre lignes dans IMP_CHKM (déclaration COM08 et garde) : IDYNA2, IQSTAT0, TT0, R2 exactement0 ; diagnostic explicite, aucun chargement entier artificiel. '
        'Les anciennes erreurs restent conservées ; les 107391 avertissements et cinq TYPE25 restent présents et bloquants. '
        'Plafond compilation1h/CPU6 ; maximum six Engine et un Starter sur CPU1/cap180s chacun, sans GPU ni installation, aucune dynamique entière prolongée. '
        'Témoins zéro dynamique, zéro statique refusé, charge positive instrumentale, régression libre1ms puis deuxCHECK entiers. '
        'Budget A69 trois entièrement consommé (deux observations complètes, première originale échouée), jamais réinitialisé. '
        'Préserver budgets, sorties, critères échoués et RKE sans compensation. Meilleur impact entier0,0200001220703125s ; objectif dix secondes physiques et vidéo3D incomplet.')

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A69'
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a68_a69/final_remote_verification.json');assert proof['pass']
    review=read(PREP/'independent_scope_review.json');assert review['pass'] and review['plan_sha256']==sha(PLAN)
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(CFG,{**read(PLAN),'iteration':'AIRCRAFT-A70','created_utc':now(),'new_native':0,'new_software_not_applied':True,'new_compilation':False})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_sealing':True})

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];p=read(PLAN);review=read(PREP/'independent_scope_review.json')
    assert review['pass'] and sha(ROOT/p['patch']['proposed_source'])==p['patch']['proposed_sha256']
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a69';m=read(prior/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    assert sha(ROOT/'wtc1_simulation_v8/openradioss_runtime/a67_current_area_iteration_candidate/isolated_exec/engine_linux64_gf_ompi')=='89a87631eb2e7f87db29e03247717556818567e41feb7fa2e768a10e03b642f8'
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A69_sealed_files_rehashed':len(m['files']),'A67_binary_rehashed_unchanged':True,
        'R0_R1_R2_preparation_failures_preserved':True,'cached_correct_R2_inputs_and_source_reused_for_R3_finish':True,'old_native_diagnostics_replayed':False,
        'historical_source_archives_not_rescanned':True,'pinned_software_COM08_read_only':True,'undeclared_TIME_proposal_failed_review_preserved':True,'physical_budgets_and_failed_criteria_preserved':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A70','status':'completed_exact_CHECK_initial_Newmark_zero_residual_proposal__not_applied_or_compiled',
        'new_native_Engine_or_Starter':0,'source_patch_applied':False,'new_compilation':False,'independent_scope_checks':len(review['checks']),
        'independent_scope_pass':True,'exact_added_source_lines':4,'target_routine':'IMP_CHKM','patch':p['patch'],
        'admissibility_CHANGE_is_explicit_and_limited':True,'all_prior_failed_CHECK_results_preserved':True,
        'connection_warnings_and_TYPE25_ignored_unchanged':True,'future_Engine_number':8,'future_Engine_maximum':6,'future_Starter_maximum':1,
        'future_build_maximum_s':3600,'future_build_CPU':6,'future_native_CPU':1,'each_native_cap_s':180,'new_explicit_consent_received':False,
        'native_inputs_and_patch_prepared_but_not_native_qualified':True,'whole_mass_material_inertia_budgets_changed':False,'whole_force_added':False,'RKE_added':False,
        'whole_integration_ready':False,'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A71'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':read(PREP/'preparation_review.json')['proposal'],
        'independent_scope_review':rel(PREP/'independent_scope_review.json'),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A70 — correctif de classification CHECK initial, proposé seulement

Le correctif exact ajoute quatre lignes dans IMP_CHKM et préserve toutes les autres routines. Aucun code moteur appliqué ou compilé, aucun nouveau Starter/Engine. Son admissibilité numérique modifiée est annoncée explicitement ; elle ne valide pas les contacts ni la scène entière.

## 1. Faits directement observés ou transcrits

A69 mesure R2=0/LB nul dans deux cas, dont le témoin dont la dynamique libre A67 passe. L’observation originale A69 reste échouée et non répétée. Source proposée et différence exactes en copie privée AGPL. La revue indépendante passe 15 critères de portée, garde, entrées et conservation des autres routines. En retirant seulement les quatre lignes ajoutées, on retrouve exactement la source de base. TT est déclaré par COM08, ajoutée uniquement dans cette routine ; la proposition TIME antérieure, non déclarée, est refusée.

Les préparations R0 (espacement d’inclusion), R1 (ancien identifiant INIVEL supposé1 au lieu de500) et R2 (comparaison du TITLE volontairement renommé) échouent avant toute application. Toutes sont conservées. Les cartes R2 correctes sont réutilisées sans régénération. La proposition utilisant TIME est refusée par la revue indépendante avant application ; R4 utilise TT et la déclaration COM08 native. Tous les champs mécaniques sont identiques sauf la suppression déclarée de vitesse initiale dans le coupon statique chargé, et sa charge de contrôle explicite ; BEGIN/TITLE sont renommés. A68+A69 publiées, hashes et deux CI vérifiés avant déclaration A70.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Le pin OpenRadioss et la base IMP_CHKM sont identiques à A67/A68. La modification porte sur la classification du résidu, sans modifier force, matériau, histoire, raideur ou intégration. Le format de charge du coupon est vérifié dans la [documentation officielle CLOAD](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/cload_starter_r.htm), qui applique la force individuellement à chaque nœud du groupe, et dans [FUNCT](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/funct_starter_r.htm). Le Starter natif n’est pas encore exécuté.

## 3. Affirmations provenant des archives locales

Aucune archive historique inspectée ou modifiée ; aucun dégât connu ciblé. Les références logicielles de contrôle sont séparées des archives historiques.

## 4. Hypothèses propres au modèle

Graine1102095, zéro tirage. Une vitesse initiale peut donner un résidu initial nul ; les bilans, paramètres physiques et contacts doivent être vérifiés séparément. La proposition autorise seulement R2 exactement zéro pour IDYNA2, IQSTAT0, TT0, avec diagnostic explicite. Les autres méthodes, temps non nul, zéro statique, valeurs hors plage/non finies gardent leur ancienne branche. Cette règle est une nouvelle admissibilité de CHECK, pas une relaxation cachée d’un critère physique ni une réussite rétroactive.

## 5. Résultats dérivés

Huitième moteur isolé A71 proposé avec toutes les corrections A67 conservées, compilation plafond1h/CPU6, sans GPU ni installation. Maximum six Engine et un Starter CPU1/cap180s chacun : zéro dynamique accepté avec message ; zéro statique toujours refusé ; charge statique positive ; régression libre élastique1ms avec seuils A67 conservés ; deux CHECK entiers avec cartes/restarts inchangés. Le coupon positif applique1N à chacun des quatre nœuds libres, total4N ; aucune force ajoutée aux scènes entières. Sources, entrées, graines, empreintes et résultats attendus dans le plan ; aucun contrôle natif présumé passé.

## 6. Contradictions et informations manquantes

Patch non appliqué, moteur non compilé, cartes nouvelles non qualifiées par Starter. Accord A69 limité aux trois observations moteur inchangé et épuisé : nouveau consentement requis avant toute modification/compilation ou calcul proposé. Les 107391 avertissements et cinq contacts TYPE25 restent présents et bloquants. A52nonintégrée, inerties, domaines matériaux et bilans entiers non qualifiés. Tous les refus antérieurs restent inchangés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes, aucun temps manquant fabriqué.

'''+route()+'\n',encoding='utf8')
    proposal=read(PREP/'preparation_review.json')['proposal']
    HANDOFF.write_text('# Reprise AIRCRAFT-A70 → AIRCRAFT-A71\n\nRapport : '+rel(REPORT)+'\nProposition : '+proposal+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1 dans C:/Users/jeuxpc/Documents/Codex/2026-08-13/referenced-chatgpt-conversation-this-is-an.\nLis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+proposal+' et '+rel(HANDOFF)+'.\nL’état local prime, aucun calcul en cours.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a70*.py'))+[CFG,PLAN,HANDOFF,PROMPT]
    for n in ['aircraft_a70_preparation','aircraft_a70_preparation_r1','aircraft_a70_preparation_r2','aircraft_a70_preparation_r4']:
        files.extend(p for p in (ROOT/'wtc1_simulation_v8/output'/n).rglob('*') if p.is_file())
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_output_script_inputs_only_AGPL_raw_source_patch_excluded':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A70_assessed':True,'independent_checks':len(review['checks']),'applied':False,'compiled':False,'new_native':0}),flush=True)

def register():
    s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert s==read(OUT/'before_state.json') and c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==[]
    m=read(OUT/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now();row={'experiment_id':'WTC1-AIRCRAFT-A70','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A70',next_iteration='AIRCRAFT-A71',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a70_key_results']=row;s['validated_artifacts'].update(aircraft_a70_report=rel(REPORT),aircraft_a70_results=rel(OUT/'composite_qualification_review.json'),aircraft_a70_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A70'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A70+AIRCRAFT-A71 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==189
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),'harness':h,'new_native':0,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A71'})
    print(json.dumps({'A70_registered':True,'registry_entries':189,'pending_publication':1}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','assess','register']);globals()[p.parse_args().action]()
