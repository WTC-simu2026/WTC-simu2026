"""Read-only normalization audit and bounded unmodified-engine observer proposal."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import ast,json,re,tarfile,subprocess,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a84'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a84_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a84_normalization_audit'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a84_preparation.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a84_proposal.json'
REPORT=OUT/'rapport_aircraft_a84.md'
PROPOSAL=PREP/'proposition_mesure_references_brutes_A85.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A84_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A85_2026-10-15.md'
OBSERVER=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a85_normalization_linux.py'


def route():
    return ('AIRCRAFT-A85 proposée non exécutée : une mesure nouvelle des références Newton brutes, '
        'un seul Engine A73 inchangé sous observateur en lecture seule, CPU1/plafond180s ; '
        'restart initial propre A81 et carte exacte A83 réutilisés, zéro Starter/correctif/compilation/GPU/installation. '
        'Observer DE0,EIMP,R02,F libre et normes natives U2/DU2 aux premières itérations0à2, '
        'puis laisser le moteur terminer sans changer les données, critères ou bornes de pas. '
        'Quatre points matériels, aucune écriture de code ou données numériques. '
        'Accord distinct requis : le seul Engine A83 est consommé. Une observation manquée consomme sa place sans réessai. '
        'L’hypothèse de dénominateurs nuls n’est pas encore une mesure ; aucun correctif ne doit masquer les non-finis. '
        'Compression, rupture, refermeture et contacts restent non qualifiés. '
        'Anciennes sorties, budgets,107391avertissements et critères échoués conservés. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def stage():
    assert not any(p.exists() for p in [OUT,PREP,CFG,PLAN,PRIVATE])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A83' and h['RegistryEntries']==202
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a83_predeclaration.json')
    old=read(ROOT/'wtc1_simulation_v8/output/aircraft_a83/observation_review.json')
    assert old['partial_observation_useful'] and old['printed_iterations']==31
    OUT.mkdir();PREP.mkdir();PRIVATE.mkdir();dump(OUT/'harness_before_preparation.json',h)
    tar=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    digest=sha(tar);assert digest=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A84_PREPARATION','seed':1102107,'random_draws':0,
        'source_cache':rel(tar),'source_cache_sha256':digest,'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a',
        'new_Engine':0,'new_Starter':0,'source_patch_compilation_GPU_installation':False,
        'publication_A82_A83_may_still_be_pending_during_read_only_preparation':True})
    copied=[]
    with tarfile.open(tar,'r:gz') as archive:
        for basename in ['nl_solv.F','produt_v.F']:
            members=[m for m in archive.getmembers() if m.name.endswith('/engine/source/implicit/'+basename)]
            assert len(members)==1
            p=PRIVATE/basename;p.write_bytes(archive.extractfile(members[0]).read())
            copied.append({'member':members[0].name,'private_path':rel(p),'sha256':sha(p)})
    dump(PRIVATE/'source_selection.json',{'created_utc':now(),'pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a',
        'cache_sha256':digest,'copied_members_unmodified':copied,'no_source_modified':True})
    source=(PRIVATE/'nl_solv.F').read_text(encoding='utf8');product=(PRIVATE/'produt_v.F').read_text(encoding='utf8')
    signature=source[source.index('      SUBROUTINE NL_SOLV('):source.index('C-----------------------------------------------',source.index('      SUBROUTINE NL_SOLV('))]
    continuation=''.join(line[6:] for line in signature.splitlines())
    names=[s.strip() for s in continuation[continuation.index('(')+1:continuation.index(')')].split(',')]
    expected={0:'NDDL',1:'IDDL',2:'NDOF',4:'D',11:'F',22:'R02',23:'DD',26:'IT',28:'RU0',29:'ROLD',34:'E02',35:'DE0',36:'EIMP',38:'NDDL0',39:'LS',40:'U02'}
    checks={'all_ABI_argument_indices_match_pinned_source':all(names[k]==v for k,v in expected.items()),
        'energy_ratio_direct_division_present':'RE=DE0/EIMP' in source,
        'small_DE0_positive_floor_present':'IF (ABS(DE0)<EM20) DE0=EM20' in source,
        'displacement_ratio_direct_division_present':'RU=LS(3)*SQRT(DU2/U2)' in source,
        'initial_row_prints_absolute_quantities':'WRITE(IOUT,1003)IT,anew_stif,RU,R01,EIMP' in source,
        'later_row_prints_normalized_quantities':'WRITE(IOUT,1003)IT,anew_stif,RU,RR,RE' in source,
        'norm_uses_condensed_free_coordinates':'CALL CONDENS_B(NDDL0  ,IKC  ,TMP_W1)' in product,
        'norm_result_argument_eighth':'DD    ,DDR   ,NORM2 ,W_IMP' in product,
        'own_observer_ast_valid':True,'observer_no_native_invocation_during_preparation':True}
    tree=ast.parse(OBSERVER.read_text(encoding='utf8'));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    ptrace_calls=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='ptrace']
    requests=[n.args[0].value for n in ptrace_calls];assert set(requests)=={0,6,7}
    checks['only_TRACEME_USER_debug_register_and_CONT_requests']=set(requests)=={0,6,7}
    checks['memory_open_readonly']='os.O_RDONLY' in OBSERVER.read_text(encoding='utf8') and 'os.pwrite' not in OBSERVER.read_text(encoding='utf8')
    checks['bounded_breakpoint_events']='traps<=64' in OBSERVER.read_text(encoding='utf8')
    checks['all_breakpoints_disabled_after_iteration2']='sites=[0,0,0,0];enable()' in OBSERVER.read_text(encoding='utf8')
    binary=ROOT/next(r['path'] for r in c['unchanged_software'] if 'engine_linux' in r['path'])
    result=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-S',linux(binary)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0;symbols={}
    for line in result.stdout.splitlines():
        m=re.match(r'^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+[Tt]\s+(\S+)$',line)
        if m and m[3] in ['nl_solv_','crit_ite_','produt_uhp_']:symbols[m[3]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
    checks['three_native_symbols_present']=len(symbols)==3
    checks['all_software_binaries_unchanged']=all(sha(ROOT/r['path'])==r['sha256'] for r in c['unchanged_software'])
    assert all(checks.values()),checks
    dump(PREP/'source_and_observer_static_review.json',{'created_utc':now(),'pass':True,'checks':checks,
        'scope':'Static preparation only; actual runtime ABI capture unqualified until a newly authorized observation',
        'zero_denominators_are_a_hypothesis_not_native_values':True,'ABI_indices':expected,'native_symbols':symbols,
        'source_selection':rel(PRIVATE/'source_selection.json'),'source_selection_sha256':sha(PRIVATE/'source_selection.json')})
    p={'created_utc':now(),'iteration':'AIRCRAFT-A84_PROPOSAL','seed':1102107,'random_draws':0,
        'case':'RAW_NEWTON_REFERENCES','name':c['name'],'inputs':c['inputs'],'unchanged_software':c['unchanged_software'],
        'observer':rel(OBSERVER),'observer_sha256':sha(OBSERVER),
        'helper':'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py','helper_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py'),
        'symbols':symbols,'node_count':8,'maximum_Engine':1,'maximum_Starter':0,'CPU_threads':1,'cap_s':180,
        'GPU':False,'source_patch':False,'compilation':False,'installation':False,'whole_dynamic_extension':False,
        'new_explicit_human_authorization_required':True,'previous_A83_Engine_remaining':0,'expected_wall_s':[5,30],
        'source_Starter_gate':c['source_Starter_gate'],'source_Starter_gate_sha256':c['source_Starter_gate_sha256'],
        'source_static_review':rel(PREP/'source_and_observer_static_review.json'),
        'source_static_review_sha256':sha(PREP/'source_and_observer_static_review.json'),
        'measure':['Native DE0,EIMP,R02 and free F at NL_SOLV/CRIT_ITE entry','Native U2/DU2 from PRODUT_UHP returns',
            'Normalized UR/RR/ER entering convergence test at iterations1,2','Full D and DD arrays for8nodes',
            'Preserved terminal stop,warnings and actual saved states'],
        'no_newton_global_time_cycle_observation_promised':True,
        'fixed_dt_min_max_ms':[.000125,.000125],'three_tolerances':1e-11,
        'observation_acceptance':['All required entry and return samples captured and source-domain checked',
            'All nonfinite values classified in strict JSON','All hardware breakpoints disabled after criterion2',
            'No numerical data,instruction or general register writes','Engine reaches its own stop; failure is not a passed trajectory'],
        'physical_pass_not_assumed':True,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    for r in p['inputs']:assert sha(ROOT/r['path'])==r['sha256']
    dump(PLAN,p)
    PROPOSAL.write_text('''# Proposition A85 — mesurer les références brutes sans modifier le moteur

A83 a révélé énergieInfinity dès1 et déplacementNaN dès2, puis arrêt79/ISTOP−2. Le seul Engine autorisé est consommé. La source définit RE=DE0/EIMP et RU=LS(3)*sqrt(DU2/U2), avec un plancher positif de DE0. Des dénominateurs nuls constituent une hypothèse compatible ; leurs valeurs réelles ne sont pas encore mesurées. Changer les tolérances ou remplacer les non-finis par zéro n’est pas proposé.

Un seul Engine A73 inchangé est proposé sous un observateur qui lit les valeurs brutes aux premières itérations0à2. Même restart initial propre A81, même carte A83, chargement, trois tolérances, pas initial/minimum/maximum et horizon identiques. Zéro Starter, correctif, compilation, GPU, installation ou prolongement entier. UnCPU, plafond180s, estimation5–30s. Vérifier auparavant la publication A82+A83.

Quatre points d’exécution matériels au maximum, sur le processus enfant propre. Lecture seule des données numériques, sans remplacement d’instruction, modification de données ou registres numériques. Les seuls registres configurés sont les registres matériels de débogage ; les signaux sont transmis. Les points sont tous désactivés après l’entrée du critère à l’itération2 ; l’Engine poursuit jusqu’à son arrêt propre. Un plafond de64arrêts d’observation protège les captures ; tout échec consomme sa seule place, sans réessai automatique.

Mesures : DE0,EIMP,R02 et vecteurF libre, normes natives U2 et DU2 à leur retour, ratiosUR/RR/ER transmis au critère, D/DD des huit nœuds. Le résidu carré recalculé depuis F sur un seul domaine sera identifié comme dérivé, jamais confondu avec une variable native non lue. Les numéros d’itération sont observés ; aucune capture du temps/cycle global n’est promise. La correction d’interprétation de la ligne0 (grandeurs initiales absolues plutôt que ratios) est documentée dans A84.

La signature source épinglée, les indices d’arguments, trois symboles du binaire actuel, empreintes et bornes du lecteur sont vérifiés statiquement. Le déroulement effectif sous cet observateur demeure à qualifier. Une mesure de dénominateurs nuls n’autorisera pas un correctif automatique : il faudra définir et approuver séparément tout changement du moteur ou de la mécanique.

Nouvel accord explicite requis pour ce lot, distinct d’A83 consommé. Compression, rupture et refermeture restent non mesurées. Anciennes sorties, budgets, critères échoués et107391avertissements conservés ; aucun temps physique entier supplémentaire. Dix secondes et vidéo3D incomplètes.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A84',
        'status':'completed_read_only_normalization_audit__raw_reference_observer_prepared_unrun',
        'new_Engine':0,'new_Starter':0,'source_patch_compilation_GPU_installation':False,
        'energy_DE0_over_EIMP_source_confirmed':True,'displacement_DU2_over_U2_source_confirmed':True,
        'small_DE0_positive_floor_present':True,'norm_uses_condensed_free_coordinates':True,
        'initial_table_row_absolute_not_normalized_addendum':True,
        'zero_native_denominators_not_yet_observed':True,'static_review_pass':True,'static_checks':len(checks),
        'future_maximum_Engine':1,'future_maximum_Starter':0,'future_CPU':1,'future_cap_s':180,
        'new_explicit_consent_received':False,'source_binary_patch_or_build_proposed':False,
        'all_old_failed_gates_and_physical_budgets_preserved':True,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A85'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A84 — audit des normalisations et mesure brute préparée

Travail en lecture seule, zéro Engine/Starter ; aucun correctif du moteur. Les deux divisions non protégées sont localisées, mais leurs opérandes réels ne sont pas encore mesurés.

## 1. Faits directement observés ou transcrits

A83 imprimeInfinity sur le critère énergie dès1 etNaN sur le déplacement dès2 ; arrêt au maximum30 puis79/ISTOP−2. Une seule ligneTH réelle à0ms. Deux fichiers logiciels sont copiés sans modification depuis le cache épinglé3d75ff13d1946f6d28a43920eac4fa2aae41b27a. Le binaire actuel conserve les trois symboles nécessaires ; aucune exécution Engine pour les inspecter.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La source logicielle de NL_SOLV calcule RE=DE0/EIMP, puis à partir d’IT2, RU=LS(3)*sqrt(DU2/U2), sans garde locale de ces dénominateurs. Après une itération non négative, DE0 est ramené à une constante positive si sa valeur absolue est trop petite. PRODUT_UHP projette/condense les déplacements avant de former la norme sur les inconnues libres. NITOL123 combine les trois critères normalisés.

## 3. Affirmations provenant des archives locales

Aucune archive historique, photographie ou vidéo réanalysée ou modifiée. Les sources AGPL brutes demeurent dans le répertoire logiciel privé, exclues du manifeste propre public. Le précédent cache A34 a servi au repérage ; les conclusions sont liées aux copies exactes du cache épinglé vérifié.

## 4. Hypothèses propres au modèle

Graine1102107, zéro tirage, unitésg/mm/ms. Des mouvements libres nuls et une énergie cumulée nulle sont compatibles avec ce témoin dont les mouvements normaux sont imposés. Le plancher deDE0 pourrait alors produireInfinity, et une normeDU2/U2 nulle sur nulleNaN. Ce mécanisme reste une hypothèse à mesurer, pas un constat de valeurs internes natives. Un mouvement imposé non nul ne garantit pas une norme libre non nulle. Aucun remplacement arbitraire des non-finis ni changement de tolérances proposé.

## 5. Résultats dérivés

Addendum d’interprétation A83 : la ligne d’itération0 utilise le même en-tête visuel que les suivantes, mais la source imprime sqrt(U2),sqrt(R02),EIMP à0, puis RU,RR,RE pourIT>0. Les chaînes et nombres A83 restent exacts ; l’appellation générale de ratios dans son rapport est trop large pour0. Le rapport initial est conservé, cette correction est ajoutée explicitement ici. Les observationsInfinity/NaN aux itérations positives restent valides.

Une observation nouvelle du moteur inchangé est préparée. Les signatures et indices d’arguments sont comparés à la source épinglée, les trois symboles au binaire exact. Le lecteur utilise quatre points matériels maximum, lectures de données seules et désactivation à l’itération2, puis laisse le calcul terminer. Un seul EngineCPU1/plafond180s est proposé, zéro Starter/correctif/compilation/GPU/installation. Les données et le restart propre sont identiques à A83 ; aucun ancien diagnostic n’est rejoué pour sa question déjà résolue : les nouvelles valeurs demandées sont les références brutes absentes.

## 6. Contradictions et informations manquantes

Les valeurs exactes deDE0,EIMP,U2,DU2 et le vecteur libre restent inconnus. Le lecteur est vérifié statiquement, pas encore au fonctionnement natif ; une observation manquée ne sera pas remplacée automatiquement. Aucun temps/cycle global n’est promis par cette capture. Le seul EngineA83 est consommé ; nouvel accord requis pour A85. Toute proposition future de changement du moteur restera distincte. Compression, rupture, refermeture, contacts et dix secondes physiques non qualifiés ; meilleur impact entier0,0200001220703125s. Anciennes sorties, budgets, échecs et107391avertissements conservés.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A84 → AIRCRAFT-A85\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prime ; vérifierpublicationA82+A83. A84peutêtrepréparée maisnonenregistrée pendantconfirmation. Aucun calcul en cours.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_preparation.json',harness())
    dump(OUT/'preparation_verification.json',{'created_utc':now(),'pass':True,'prepared_not_registered':True,
        'plan_sha256':sha(PLAN),'report_sha256':sha(REPORT),'observer_sha256':sha(OBSERVER),'new_native_Engine_Starter':0})
    print(json.dumps({'A84_prepared':True,'static_checks':len(checks),'proposed_Engine':1,'new_native_Engine_Starter':0}),flush=True)


def register():
    assert not (OUT/'artifact_manifest.json').exists()
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a82_a83/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    h=harness();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert h['RegistryEntries']==202 and s['current_iteration']=='AIRCRAFT-A83' and cycle['pending_iterations']==[]
    pv=read(OUT/'preparation_verification.json');assert pv['pass'] and sha(PLAN)==pv['plan_sha256'] and sha(REPORT)==pv['report_sha256'] and sha(OBSERVER)==pv['observer_sha256']
    final=read(PREP/'final_launcher_review.json')
    assert final['pass'] and final['plan_sha256']==sha(PLAN)
    assert sha(ROOT/final['launcher'])==final['launcher_sha256'] and sha(ROOT/final['reviewer_script'])==final['reviewer_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_registration_'+Path(n).name))
    dump(OUT/'verified_prior_publication.json',proof)
    for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a83/artifact_manifest.json')['files']:assert sha(ROOT/r['path'])==r['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A83_sealed_files_rehashed':True,'old_native_replayed':False})
    files=[p for folder in [OUT,PREP] for p in folder.rglob('*') if p.is_file()]+[CFG,PLAN,OBSERVER,Path(__file__),HANDOFF,PROMPT,
        ROOT/final['launcher'],ROOT/final['reviewer_script']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_no_raw_AGPL':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A84','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    entry.update(final_launcher_review_pass=True,final_launcher_scope_checks=len(final['checks']))
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A84',next_iteration='AIRCRAFT-A85',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a84_key_results']=entry;s['validated_artifacts'].update(aircraft_a84_report=rel(REPORT),aircraft_a84_results=rel(OUT/'composite_qualification_review.json'),aircraft_a84_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A84'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A84+AIRCRAFT-A85 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==203
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,
        'new_Engine':0,'new_Starter':0,'future_native_authorized':False,'whole_qualified':False,'next_iteration':'AIRCRAFT-A85'})
    print(json.dumps({'A84_registered':True,'registry':203,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','register']);globals()[p.parse_args().action]()
