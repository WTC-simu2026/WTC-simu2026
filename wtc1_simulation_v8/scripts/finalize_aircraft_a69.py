"""Seal the three consumed observations, one observer failure and two complete zero-residual measurements."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,re,numpy as np

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a69';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a69_predeclaration.json'
REPORT=OUT/'rapport_aircraft_a69.md';HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A69_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A70_2026-10-14.md'

def route():
    return ('AIRCRAFT-A70 : préparer en lecture seule le correctif précis de classification du résidu initial dynamique nul dans IMP_CHKM, '
        'à partir de R2=0 directement mesuré dans le témoin libre et la scène appariée. '
        'Préserver les anciens CHECK refusés ; distinguer cette admissibilité numérique de la qualification physique entière. '
        'Conserver les 107391 avertissements de préconditionnement et les cinq TYPE25 bloquants, sans substitution silencieuse ni fausse force. '
        'A69 : trois Engine consommés, aucun Starter, moteur A67 inchangé ; première observation originale échouée sur le lecteur de tableau vide, '
        'deux restantes complètes après correction propre du lecteur, aucune répétition. Aucun crédit d’impact entier. '
        'Nouveau correctif/compilation et lot natif exigent une proposition concrète et un nouvel accord distinct. '
        'Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D incomplètes.')

def assess():
    assert not REPORT.exists() and read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];cfg=read(CFG)
    runs=list(OUT.rglob('engine.execution.json'));assert len(runs)==3 and len(list(OUT.rglob('native_launch_declaration.json')))==3
    for p in runs:
        r=read(p);assert r['CPU_threads']==1 and r['cap_s']==180 and not r['GPU'] and r['binary_sha256']==cfg['binary_sha256']
    assert not list(OUT.rglob('starter.execution.json')) and sha(ROOT/cfg['binary'])==cfg['binary_sha256']
    rows=[]
    for c in cfg['cases']:
        d=OUT/c['case'];obs=d/'check_observation.json';e=read(d/'engine.execution.json')
        if not obs.exists():
            assert c['case']=='WHOLE_ORIGINAL_CHECK' and e['parent_exit_code']==1
            rows.append({'case':c['case'],'observation_pass':False,'reason':'Own observer attempted an unused zero-length interface-array pointer; child stopped/killed, no R2 or diagonal attribution inferred.',
                'original_attempt_preserved':True,'rerun':False,'counts_in_budget':1,'whole_pass':False});continue
        r=read(obs);assert r['observation_complete'] and e['parent_exit_code']==0
        pre=np.fromfile(d/'pre_combined_diagonal.raw',dtype='<f8');post=np.fromfile(d/'post_precondition_diagonal.raw',dtype='<f8');lb=np.fromfile(d/'native_LB.raw',dtype='<f8')
        assert len(pre)==len(post)==len(lb)==r['pre']['NDDL']
        count=int(np.count_nonzero((post<1e-12)|(post>1e10)))
        events=[v for v in r['events'] if 'native_R2' in v];assert len(events)==1
        assert events[0]['native_R2']==float(np.dot(lb,lb))==r['LB_before_linear_solver']['norm_squared_single_process']==0
        assert np.isfinite(pre).all() and np.all(pre>0) and np.isfinite(post).all()
        listing=d/(c['name']+'_0001.out');s=listing.read_text(encoding='utf8');log=(d/'engine.log').read_text(encoding='utf8')
        reported=[int(v) for v in re.findall(r'ND\.\s*=\s*(\d+)\s+WITH POSSIBLE FREE CONNECTION CHECKED',s)];assert reported==[count]
        error=s.count('** ERROR :IMPLICIT LOADING DATA **');assert error==1
        directions=re.findall(r'NODE NUM\.\s*=\s*(\d+)\s+(TRA|ROT)_DIR\s*=\s*([XYZ])\s+VAL\.\s*=\s*([\d.E+\-]+)',s);assert len(directions)==count
        if count:
            values=np.array([float(v) for n,k,a,v in directions]);selected=post[(post<1e-12)|(post>1e10)]
            assert np.allclose(np.sort(values),np.sort(selected),rtol=6e-7,atol=1e-30)
        row={'case':c['case'],'observation_pass':True,'native_R2':0.,'native_LB_nonzero_entries':0,'NDDL':len(pre),'NDDLI':r['pre']['NDDLI'],
            'assembled_dynamic_and_constraint_diagonal_range':[float(pre.min()),float(pre.max())],
            'preconditioner_coefficient_range':[float(post.min()),float(post.max())],'printed_warning_coefficients_match_raw_distribution':True,
            'possible_connection_warning_DOF':count,'loading_error_count':error,'TYPE25_ignored':log.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),
            'native_code0_NORMAL':r['Engine_exit_code']==0 and 'NORMAL TERMINATION' in log,
            'full_pre_post_reduced_equation_node_map_not_reconstructed_without_IKC':True,
            'positive_dynamic_diagonal_is_not_static_constraint_rank_proof':True,'whole_pass':False,'whole_credit_s':0}
        rows.append(row)
    assert sum(r['observation_pass'] for r in rows)==2
    dump(OUT/'independent_observation_review.json',{'created_utc':now(),'cases':rows,'complete_cases':2,'original_observation_failed_preserved':True,
        'all_three_observations_pass':False,'native_measured_R2_plain_norm_agrees':True,'new_native':3,'controls_remaining':0,'whole_qualified':False})
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a68';m=read(prior/'artifact_manifest_r2.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A68_sealed_files_rehashed':len(m['files']),
        'A67_binary_rehashed_unchanged':True,'old_R0_observer_and_failure_preserved':True,'old_native_diagnostics_replayed':False,
        'old_sources_and_physical_inputs_budgets_unchanged':True,'archive_not_rescanned':True})
    a={'created_utc':now(),'iteration':'AIRCRAFT-A69','status':'completed_three_consumed_observations__R0_observer_failure_retained__paired_and_free_R2_zero_measured',
        'new_Engine':3,'new_Starter':0,'controls_remaining':0,'new_Engine_source_patch_or_compilation':False,
        'original_observation_pass':False,'paired_observation_pass':True,'free_CHECK_observation_pass':True,
        'zero_initial_dynamic_residual_directly_observed':True,'native_R2_zero_cases':2,'failed_first_counts_in_budget':True,
        'own_observer_zero_length_reader_repaired_in_separate_R1':True,'no_case_rerun':True,'whole_CHECK_pass':False,
        'TYPE25_ignored_whole':5,'possible_connection_warnings_whole':107391,'whole_R2_original_not_observed':True,
        'whole_budgets_or_physical_failed_criteria_changed':False,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A70'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'observations':'independent_observation_review.json','whole_physical_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A69 — résidu initial nul mesuré, observation originale échouée

Trois Engine autorisés sont consommés. Deux observations nouvelles sont complètes, une échoue dans le lecteur propre et reste conservée. R2=0 est directement mesuré dans la scène appariée et le témoin libre ; aucune modification du moteur ni dynamique entière.

## 1. Faits directement observés ou transcrits

Accord humain « Oui, exécuter les trois observations A69 » lié au plan et à la revue avant lancement. Trois Engine, un CPU/plafond 180 s, sans Starter, GPU, installation, correctif ou compilation du moteur A67. L’observateur R0 a refusé de lire l’adresse inutilisée d’un tableau d’interface de taille zéro. Son échec compte comme premier lancement ; son enfant propre est arrêté, trace incomplète, aucune valeur R2 attribuée à l’original. Une version R1 du seul lecteur retourne une liste vide sans lire de pointeur quand le compte est zéro ; toutes les gardes de compte positif, ABI, source et mécanique sont inchangées. Les deux cas restants sont exécutés, aucune répétition de l’original.

Scène appariée : NDDL227010/NDDLI0, LB entièrement nul et fini, norme carrée indépendante 0, R2 natif exactement 0. Diagonale assemblée dynamique/contraintes comprise entre 11372721,8312 et 1,14438279574e18 ; aucune valeur nulle/négative. Coefficients après préconditionnement compris entre 8,73833479254e-19 et 8,79297059769e-8 ; 107391 satisfont le test natif d’avertissement, en concordance avec toutes les valeurs imprimées à leur précision. Une erreur de chargement et cinq contacts TYPE25 ignorés persistent.

Témoin libre CHECK : NDDL12/NDDLI0, LB nul, R2=0, diagonale assemblée positive 8892,88838894–48892,8883889, coefficients de préconditionnement 2,04528722469e-5–1,99750422478e-4 ; zéro avertissement de connexion, une erreur de chargement. Son cas dynamique sans CHECK est conservé en A67, avec conservation libre élastique et réponse analytique qualifiées jusqu’à 1 ms.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Les fonctions natives observées sont IMP_CHECK0, PRODUT_W, LIN_SOLV et IMP_CHECM0 du même binaire A67 figé. Les registres et tableaux sont lus par points d’arrêt matériels dans l’enfant propre. Aucun code, instruction ou état mécanique modifié ; signaux natifs transmis. Le compteur de connexion porte ici sur le résultat de préconditionnement, pas directement sur une masse ou raideur brute.

## 3. Affirmations provenant des archives locales

Aucune archive historique consultée ou modifiée, aucun dégât connu ciblé ni nouvelle analyse vidéo.

## 4. Hypothèses propres au modèle

Graine1102094, zéro tirage ; unités native g/mm/ms, tableaux réels double précision. La validité d’un problème dynamique à vitesse initiale ne requiert pas que le résidu de force initial soit non nul. Cette observation ne suffit pas à valider les masses, inerties, contraintes ou contacts de la scène entière. La diagonale inclut des termes dynamiques et de contrainte : sa positivité ne prouve pas le rang des seules liaisons statiques.

## 5. Résultats dérivés

La condition native 0<R2<1e30 refuse également un témoin dont la dynamique libre est déjà qualifiée. Il faut préparer une admissibilité explicite et limitée du résidu initial nul pour CHECK dynamique, sans ajouter de force fictive ni relabelliser les anciens refus. L’attribution des 107391 avertissements aux coefficients transformés est directement vérifiée ; elle n’est pas une preuve de rupture physique. La distribution de leurs valeurs imprimées correspond aux coefficients binaires mesurés. Aucun contrôle de volume ou de graphe antérieur rejoué.

## 6. Contradictions et informations manquantes

L’observation originale reste échouée et R2 original non mesuré. Deux observations complètes ne constituent pas trois réussites. Les tableaux de nœuds sont sauvegardés, mais la correspondance complète entre diagonales avant/après et équations libres réduites n’est pas reconstruite sans IKC ; aucune correspondance précise inventée. Les cinq contacts TYPE25, la scène entière et les bilans/inerties/domaines matériaux restent bloquants. Budget trois entièrement consommé, ancien budget A67 non réinitialisé. Les deux CHECK complets restent refusés ; aucun changement de seuil physique, de RREF, de budgets ou RKE. Meilleur impact entier 0,0200001220703125 s ; dix secondes et vidéo 3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A69 → AIRCRAFT-A70\n\nRapport : '+rel(REPORT)+'\nRésultats : '+rel(OUT/'independent_observation_review.json')+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+' et '+rel(HANDOFF)+'.\nL’état local prime. Vérifier la publication A68+A69 avant nouvelle itération ; aucun calcul en cours.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a69*.py'))+[CFG,ROOT/'wtc1_simulation_v8/data/aircraft_a69_authorization.json',HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_script_and_output_only_no_AGPL_binary_or_raw_source':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A69_assessed':True,'observations_complete':2,'retained_observer_failure':1,'budget_consumed':3}),flush=True)

def register():
    s=read(ROOT/'harness/state.json');c=read(ROOT/'harness/publication_cycle.json')
    assert s==read(OUT/'before_state.json') and c==read(OUT/'before_publication_cycle.json') and c['pending_iterations']==['AIRCRAFT-A68']
    m=read(OUT/'artifact_manifest.json')
    for r in m['files']:assert sha(ROOT/r['path'])==r['sha256']
    assert sha(ROOT/'harness/experiments/registry.jsonl')==sha(OUT/'before_registry.jsonl')
    a=read(OUT/'scientific_assessment.json');stamp=now();row={'experiment_id':'WTC1-AIRCRAFT-A69','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A69',next_iteration='AIRCRAFT-A70',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a69_key_results']=row;s['validated_artifacts'].update(aircraft_a69_report=rel(REPORT),aircraft_a69_results=rel(OUT/'composite_qualification_review.json'),aircraft_a69_handoff=rel(HANDOFF))
    c.update(pending_iterations=['AIRCRAFT-A68','AIRCRAFT-A69'],pending_count=2,updated_at=stamp,next_publication_after='AIRCRAFT-A68+AIRCRAFT-A69 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',c)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==188
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'files_verified':len(m['files']),'harness':h,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A70'})
    print(json.dumps({'A69_registered':True,'registry':188,'pending':2}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assess','register']);globals()[p.parse_args().action]()
