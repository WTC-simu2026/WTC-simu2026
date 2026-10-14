"""New cached-source CHECK semantics/role audit and exact bounded observer proposal; no Engine execution."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import json,re,collections,tarfile,hashlib,subprocess,shutil,ast

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a68'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a68_check_semantics_audit'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a69_preparation'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a68_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a69_proposal.json'
REPORT=OUT/'rapport_aircraft_a68.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A68_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A69_2026-10-14.md'

def route():
    return ('AIRCRAFT-A69 proposée : trois nouvelles observations natives bornées, non exécutées, moteur A67 inchangé. '
        'Mesurer directement R2/LB et les diagonales avant/après préconditionnement dans les deux CHECK entiers et un témoin libre CHECK. '
        'Observer par points d’arrêt matériels et lectures mémoire du seul enfant propre, sans gdb, installation, patch ni compilation. '
        'Un CPU, plafond 180 s chacun, maximum trois Engine, aucun Starter ni prolongement entier. '
        'Attendre un accord humain distinct sur ce lot, car les huit Engine A67 sont consommés. '
        'Ces mesures nouvelles ne répètent pas les anciens diagnostics de volume ou de graphe. '
        'Les cinq contacts TYPE25 restent ignorés et bloquants ; aucune substitution ou modification de seuils. '
        'Meilleur impact entier 0,0200001220703125 s ; dix secondes physiques et vidéo 3D incomplètes.')

def main():
    assert not any(p.exists() for p in [OUT,PRIVATE,PREP,CFG,PLAN]);h=harness()
    assert h['CurrentIteration']=='AIRCRAFT-A67' and read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-14_aircraft_a66_a67/final_remote_verification.json');assert proof['pass']
    OUT.mkdir();PRIVATE.mkdir();PREP.mkdir();dump(OUT/'harness_before.json',h)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    assert sha(archive)=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    names=['imp_solv.F','lin_solv.F','imp_fsa_inv.F','prec_solv.F','upd_glob_k.F','imp_dyna.F','imp_setb.F','produt_v.F'];sources=[];raw={}
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A68','seed':1102093,'random_draws':0,'purpose':'Read-only cached CHECK source semantics and printed-node role audit',
        'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','source_archive':rel(archive),'source_archive_sha256':sha(archive),
        'cached_results':'wtc1_simulation_v8/output/aircraft_a67','new_native':0,'source_modification_or_compilation':False})
    with tarfile.open(archive) as t:
        for name in names:
            m=next(m for m in t.getmembers() if m.name.endswith('/engine/source/implicit/'+name));b=t.extractfile(m).read();p=PRIVATE/name;p.write_bytes(b);raw[name]=b.decode('utf8')
            sources.append({'source_path':'engine/source/implicit/'+name,'private_copy':rel(p),'sha256':hashlib.sha256(b).hexdigest()})
    assert sha(PRIVATE/'imp_solv.F')==sha(ROOT/'wtc1_simulation_v8/openradioss_runtime/a66_current_area_proposal_r1/imp_solv.F')
    checks={'A67_checker_source_exact_pin':True,
        'checker_calls_connection_after_linear_solver':raw['imp_solv.F'].index('CALL IMP_CHECM0',raw['imp_solv.F'].index('SUBROUTINE IMP_CHKM'))>raw['imp_solv.F'].index('CALL LIN_SOLV',raw['imp_solv.F'].index('SUBROUTINE IMP_CHKM')),
        'K_checker_copies_base_and_interface_diagonal':all(s in raw['imp_solv.F'] for s in ['DIAG_M(I) = DIAG_K(I)','DIAG_M(J)=DIAG_M(J)+DIAG_I(I)']),
        'FSAI_uses_inverse_column':all(s in raw['imp_fsa_inv.F'] for s in ['MJ(NC)=ONE','CALL IMP_FSAI','DIAG_M(I)=MJ(NC)']),
        'FSAI_inv_solve_uses_MUMPS5_conditional':all(s in raw['imp_fsa_inv.F'] for s in ['#ifdef MUMPS5','CALL PREC0_SOLV']),
        'loading_condition_positive_bounded_norm':all(s in raw['imp_solv.F'] for s in ['CALL PRODUT_W(NDDL,LB,LB,W_DDL,R2)','R2>ZERO.AND.R2<EP30']),
        'single_process_norm_ignores_weight_array':bool(re.search(r'ELSE\s+DO I=1,NDDL\s+R = R \+ X\(I\)\*Y\(I\)',raw['produt_v.F'])),
        'dynamic_residual_uses_acceleration_not_velocity_directly':all(s in raw['imp_dyna.F'] for s in ['DY_AC(1,I)=-ABS(MS(I))*DY_A(1,I)','IF (IDY_DAMP>0)']),
        'R2_remains_unobserved_in_existing_whole_listings':True}
    assert all(checks.values())
    models=[ROOT/'wtc1_simulation_v8/output/aircraft_a49/WHOLE_EQUIVALENT_RIGID_CHAINS_CHECK/A49_EQUIVALENT_RIGID_CHAINS_0000.rad',
        ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1/A52_TYPE2_FACET_PAIRS_R1_0000.rad']
    listings=read(ROOT/'wtc1_simulation_v8/output/aircraft_a67/whole_CHECK_classification.json')['cases'];model_rows=[]
    for p,listing in zip(models,listings):
        d=sections(p);s=(ROOT/listing['listing']).read_text(encoding='utf8');assert sha(ROOT/listing['listing'])==listing['listing_sha256']
        assert 'FACTORED APPRO. INVERSES' in s
        flagged=[(int(n),kind,a,float(v)) for n,kind,a,v in re.findall(r'NODE NUM\.\s*=\s*(\d+)\s+(TRA|ROT)_DIR\s*=\s*([XYZ])\s+VAL\.\s*=\s*([\d.E+\-]+)',s)]
        tra=sorted({n for n,k,a,v in flagged if k=='TRA'});rot=sorted({n for n,k,a,v in flagged if k=='ROT'});assert len(tra)==75 and len(rot)==35722
        wanted=set(tra+rot);incidence=collections.defaultdict(list);groups=collections.defaultdict(list);elements=0
        for key,values in d.items():
            if key.startswith('/GRNOD/NODE/'):
                for line in values[1:]:
                    for node in map(int,line.split()):
                        if node in wanted:groups[node].append({'keyword':key,'title':values[0]})
            family=key.split('/')[1]
            if family not in {'SHELL','SH3N','BRICK','BEAM','TRUSS','SPRING'}:continue
            part=key.split('/')[-1];parttitle=d.get('/PART/'+part,[part])[0];width={'SHELL':4,'SH3N':3,'BRICK':8,'BEAM':2,'TRUSS':2,'SPRING':2}[family]
            for line in values:
                if not re.fullmatch(r'\s*\d+\s*',line[:10]):continue
                eid=int(line[:10]);nodes=[int(line[i:i+10]) for i in range(10,10*(width+1),10)];elements+=1
                for node in set(nodes)&wanted:incidence[node].append({'family':family,'part':part,'part_title':parttitle,'element':eid})
        rows=[{'node_id':node,'element_incidence':incidence[node],'node_groups':groups[node],
            'printed_directions':[a for n,k,a,v in flagged if n==node and k=='TRA']} for node in tra]
        titles=collections.Counter(title for node in tra for title in {e['part_title'] for e in incidence[node]})
        loads=[k for k in d if k.startswith(('/CLOAD','/GRAV','/PLOAD','/LOAD/','/IMPVEL','/IMPDISP','/IMPACC'))]
        contacts=[{'keyword':k,'cards':v,'silently_replaced':False,'whole_qualification_blocking':True} for k,v in d.items() if k.startswith('/INTER/TYPE25/')]
        assert len(contacts)==5
        model_rows.append({'path':rel(p),'sha256':sha(p),'listing':listing['listing'],'listing_sha256':listing['listing_sha256'],
            'node_count':len(d['/NODE']),'element_records_read':elements,'translational_warning_node_count':75,'rotational_warning_node_count':35722,
            'translational_nodes_with_element_incidence':sum(bool(incidence[n]) for n in tra),'translational_part_title_counts':dict(titles),
            'translational_node_roles':rows,'rotational_nodes_with_element_incidence':sum(bool(incidence[n]) for n in rot),
            'force_or_prescribed_motion_keywords':loads,'INIVEL_cards':{k:v for k,v in d.items() if k.startswith('/INIVEL')},
            'BCS_cards':{k:v for k,v in d.items() if k.startswith('/BCS/')},'TYPE25_contacts':contacts,
            'element_incidence_is_not_full_constraint_rank_proof':True})
    dump(OUT/'node_roles_and_cards_review.json',{'created_utc':now(),'models':model_rows,'source_inputs_read_only':True,'native_reexecution':False,'whole_pass':False})
    # A nonsingular connected matrix can trigger the same inverse-value condition: this is a semantic example, not whole data.
    scale=1e14;inverse_last=2/(3*scale)
    dump(OUT/'source_semantics_review.json',{'created_utc':now(),'pass':True,'checks':checks,'source_rows':sources,
        'connection_DIAG_M_is_preconditioning_workspace_not_mass':True,'reported_values_can_be_inverse_submatrix_coefficients':True,
        'connected_SPD_counterexample':{'K':[[2*scale,-scale],[-scale,2*scale]],'eigenvalues':[scale,3*scale],
            'inverse_last_diagonal':inverse_last,'native_small_inverse_condition_true':inverse_last<1e-12,'whole_native_diagonal_not_inferred':True},
        'loading_requires_0_R2_1e30':True,'single_process_R2_is_plain_LB_norm_squared':True,
        'initial_velocity_does_not_require_nonzero_initial_acceleration_or_residual':True,'actual_whole_R2_not_measured':True,
        'preconditioner_thresholds_unmodified':True,'TYPE25_five_per_scene_still_blocking':True,'no_physical_gate_lowered':True})
    b=ROOT/'wtc1_simulation_v8/openradioss_runtime/a67_current_area_iteration_candidate/isolated_exec/engine_linux64_gf_ompi';binaryhash=sha(b)
    assert binaryhash=='89a87631eb2e7f87db29e03247717556818567e41feb7fa2e768a10e03b642f8'
    linux='/mnt/'+b.drive[0].lower()+b.as_posix()[2:]
    r=subprocess.run(['wsl','-d','Ubuntu','--exec','nm','-S',linux],capture_output=True,text=True,timeout=25);assert r.returncode==0
    symbols={}
    for line in r.stdout.splitlines():
        m=re.match(r'([0-9a-f]+) ([0-9a-f]+) [Tt] (\w+)$',line)
        if m and m[3] in ['imp_check0_','imp_checm0_','imp_chkm_','lin_solv_','produt_w_']:symbols[m[3]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
    assert len(symbols)==5
    observer=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a69_check_linux.py';ast.parse(observer.read_text(encoding='utf8'))
    cases=[];controls=read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json')
    for c,model in zip(controls['whole_CHECK_cases'],model_rows):
        cases.append({'case':c['id'],'name':c['name'],'input_files':c['files'],'node_count':model['node_count'],
            'CHECK_cards_unchanged':True,'new_observation':'native_R2_LB_and_pre_post_precondition_diagonal','whole_duration_credit_s':0})
    local=ROOT/'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4';name=read(local/'generation.json')['name'];card=local/(name+'_0001.rad')
    text=card.read_text(encoding='utf8');assert text.count('/RUN/')==1 and '/IMPL/CHECK' not in text
    newcard=PREP/(name+'_0001.rad');newcard.write_text(text.replace('/RUN/','/IMPL/CHECK\n/RUN/',1),encoding='utf8',newline='\n')
    restart=local/(name+'_0000_0001.rst')
    cases.append({'case':'FREE_ZERO_RESIDUAL_CHECK','name':name,'node_count':8,
        'input_files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [restart,newcard]],
        'only_new_keyword':'/IMPL/CHECK','zero_force_initial_velocity_control':True,'whole_duration_credit_s':0})
    dump(PLAN,{'created_utc':now(),'iteration':'AIRCRAFT-A69_PROPOSAL','seed':1102094,'random_draws':0,'binary':rel(b),'binary_sha256':binaryhash,
        'observer':rel(observer),'observer_sha256':sha(observer),'helper':'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py',
        'helper_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py'),'symbols':symbols,'cases':cases,
        'maximum_Engine':3,'maximum_Starter':0,'CPU_threads':1,'each_cap_s':180,'GPU':False,'installation':False,'source_patch':False,'compilation':False,
        'whole_dynamic_extension':False,'instrumentation':'Owned-child TRACEME with hardware execution breakpoints, numeric memory reads only; no instruction or mechanical-state writes',
        'gdb_not_available_and_not_required':True,'prepared_not_executed':True,'requires_distinct_explicit_human_consent':True,
        'old_A67_budget_remaining':0,'stop_if_address_array_or_symbol_guard_fails_no_unbudgeted_retry':True,
        'deliverable':'R2 and plain norm of actual LB, combined assembled diagonal before LIN_SOLV, preconditioner coefficients at IMP_CHECM0, per-node direction map, complete native logs and observer scopes',
        'acceptance':'Observation completeness, exact binary/input hashes, bounded arrays and unchanged source/checker values; physics remains FAIL while TYPE25 ignored or whole gates unresolved',
        'all_five_TYPE25_preserved_blocking':True,'old_errors_not_suppressed':True,'best_whole_physical_s':.0200001220703125,'objective1_complete':False})
    proposal=PREP/'proposition_observation_R2_preconditionneur.md'
    proposal.write_text('''# AIRCRAFT-A69 — trois mesures natives nouvelles, moteur inchangé

Les CHECK A67 sont terminés et restent refusés ; aucun diagnostic de volume ou de graphe n’est à rejouer. L’audit A68 suit la transformation de DIAG_M : la valeur contrôlée après LIN_SOLV peut être un coefficient d’inverse approché, et non une masse ou une raideur physique brute. Une matrice connectée et positive peut donner une petite valeur signalée. Le contrôle de chargement exige un résidu LB non nul et fini ; une vitesse initiale avec accélération et force initiales nulles n’implique pas ce résidu. La valeur native R2 manque dans les sorties actuelles.

Proposition concrète : deux anciens CHECK entiers copiés exactement et un CHECK du témoin libre A67, avec le seul mot-clé /IMPL/CHECK ajouté. Le moteur, les données mécaniques et les seuils restent identiques. L’observateur propre préparé lit R2/LB et les diagonales avant/après préconditionnement par points d’arrêt matériels sur son enfant propre. Aucun gdb, logiciel à installer, instruction ou état mécanique modifié ; aucune compilation. Plan exact et empreintes : wtc1_simulation_v8/data/aircraft_a69_proposal.json.

Plafond : trois Engine, un CPU, 180 s chacun ; zéro Starter, sans GPU ni prolongement d’impact entier. Aucun retry hors budget. Échec si symbole, taille d’array, empreinte ou observation ne correspond pas au contrat ; le calcul conserve son résultat natif et ses signaux. Sorties attendues : valeurs natives, comparaison du résidu calculé, diagonales et directions, journaux complets, qualification de la mesure et limitations.

Les cinq TYPE25 sont conservés, ignorés et bloquants ; aucune substitution, fausse force, changement de RREF ou seuil assoupli. Le passage de ces mesures n’est pas un passage physique de la scène ni une autorisation de dix secondes. Un accord distinct est requis : le précédent lot A67 de huit Engine est entièrement consommé. Lot non exécuté.
''',encoding='utf8')
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'plan_sha256':sha(PLAN),'observer_syntax_valid':True,'native_symbols_present':True,
        'gdb_missing_no_installation':True,'cases':3,'proposal':rel(proposal),'new_native':0,'new_compilation':False,'source_modified':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    summary='\n'.join(f"- {Path(m['path']).name} : 75 nœuds de translation signalés ; {m['translational_nodes_with_element_incidence']} ont des incidences d’éléments ; rôles : {json.dumps(m['translational_part_title_counts'],ensure_ascii=False)}." for m in model_rows)
    REPORT.write_text('''# AIRCRAFT-A68 — audit du résidu et de la sémantique CHECK

L’audit en lecture seule précise les deux blocages numériques nouveaux, sans modifier leur statut échoué. Il prépare trois mesures natives directes, non exécutées, nécessaires pour attribuer précisément les valeurs manquantes.

## 1. Faits directement observés ou transcrits

Les deux nouvelles sorties A67 emploient le gradient conjugué et des inverses approchés factorisés. IMP_CHKM appelle IMP_CHECK0, puis le contrôle de norme de LB, LIN_SOLV et enfin IMP_CHECM0. IMP_CHECK0 copie DIAG_K et ajoute DIAG_I dans DIAG_M ; LIN_SOLV réutilise ce tableau comme espace de préconditionnement. FSA_SOLV y écrit la dernière composante obtenue en résolvant un sous-système avec second membre unité. IMP_CHECM0 teste ces valeurs avec les bornes fixes 1e-12 et 1e10. Les 107391 directions imprimées sont entièrement relues depuis les sorties A67 ; les 75 nœuds de translation sont reliés aux cartes d’entrée.

'''+summary+'''

Les cinq contacts TYPE25 gardent leurs cartes et noms exacts. Aucun chargement de force ou mouvement imposé détecté dans les familles de mots-clés examinées ; la carte INIVEL de translation est conservée. /IMPL/DYNA/2 était déjà présent. La valeur R2 effective n’est pas disponible dans ces listings. Le binaire A67 possède les cinq symboles nécessaires à l’observation. gdb est absent : aucune installation effectuée ; la méthode locale déjà disponible de points d’arrêt matériels est utilisée dans la proposition, sans rejouer ses anciens diagnostics.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel. Huit fichiers du même pin OpenRadioss sont lus depuis le cache logiciel vérifié, copies privées sous AGPL, hors publication MIT. La routine PRODUT_W calcule pour un seul processus la norme carrée ordinaire de LB ; W_DDL ne filtre que la branche multi-processus. La chaîne dynamique soustrait masse × accélération ; une vitesse initiale ne garantit pas une force résiduelle initiale non nulle. La branche d’amortissement est distincte.

## 3. Affirmations provenant des archives locales

Aucune archive historique consultée ou modifiée ; aucune nouvelle analyse vidéo. Aucun ajustement aux dégâts connus.

## 4. Hypothèses propres au modèle

Graine 1102093, zéro tirage. La cause exacte des valeurs natives reste inconnue : l’audit n’assimile pas un coefficient d’inverse à une raideur ou une masse brute. L’incidence d’un élément ne démontre pas le rang complet des contraintes. Un exemple algébrique connecté positif à échelle 1e14 illustre seulement la dépendance d’échelle du test d’inverse, sans attribuer cette matrice à la scène entière.

## 5. Résultats dérivés

Les faibles valeurs signalées ne suffisent pas à prouver des déconnexions. Le résidu initial nul d’un problème à vitesse initiale pourrait expliquer l’erreur de chargement, mais R2 doit être mesuré pour confirmer ou rejeter cette hypothèse. Trois mesures préparées lisent R2/LB et les diagonales avant/après transformation dans deux CHECK entiers et un témoin libre CHECK. Le moteur et les cartes entières restent exactement identiques. L’observation n’exige ni patch ni compilation ; les valeurs nouvelles recherchées n’existent pas dans les sorties vérifiées précédemment.

## 6. Contradictions et informations manquantes

Aucun nouvel Engine ni Starter exécuté ; les mesures proposées sont non qualifiées en exécution. Une erreur de chargement, 107391 directions signalées et cinq TYPE25 ignorés par scène restent des critères échoués, intégration entière refusée. Aucun changement de RREF, seuil, force, masse, matériau, inertie ou RKE. Préconditionnement et résidu demandent des valeurs natives avant tout correctif éventuel. Les cinq contacts exigent ensuite une variante mécanique déclarée, des contrôles distincts et une preuve d’équivalence, sans substitution silencieuse. Meilleur impact entier 0,0200001220703125 s ; objectif dix secondes puis vidéo 3D incomplet. A66+A67 publiées et vérifiées avant déclaration A68, intégrité distincte de validation physique.

'''+route()+'\n',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A68','status':'completed_read_only_CHECK_semantics_role_audit__new_observer_lot_prepared_not_run',
        'new_native_Engine_or_Starter':0,'new_source_patch_or_compilation':False,'audit_checks':len(checks),'audit_pass':True,
        'DIAG_M_after_solve_is_precondition_workspace':True,'whole_R2_unobserved':True,'translational_warning_nodes_per_scene':75,
        'node_roles_review':rel(OUT/'node_roles_and_cards_review.json'),'future_proposal':rel(proposal),'future_native_maximum':3,
        'future_lot_explicit_consent_received':False,'TYPE25_ignored_per_scene':5,'whole_CHECK_pass':False,'whole_budgets_or_failed_criteria_changed':False,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A69'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'source_semantics':'source_semantics_review.json','node_roles':'node_roles_and_cards_review.json','whole_physical_qualification':False})
    HANDOFF.write_text('# Reprise AIRCRAFT-A68 → AIRCRAFT-A69\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(proposal)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json et harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(proposal)+' et '+rel(HANDOFF)+'.\nL’état local actuel prime ; aucun calcul en cours.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    old=read(ROOT/'wtc1_simulation_v8/output/aircraft_a67/preservation_before_metadata.json')['files'];changed=[]
    for row in old:
        s=(ROOT/row['path']).stat()
        if s.st_size!=row['bytes'] or s.st_mtime_ns!=row['mtime_ns_before']:changed.append(row['path'])
    assert not changed
    for row in read(ROOT/'wtc1_simulation_v8/output/aircraft_a67/artifact_manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_metadata_files_checked':len(old),'A67_sealed_files_rehashed':True,
        'old_diagnostics_replayed':False,'new_native':0,'archive_not_rescanned':True,'source_binary_inputs_unchanged':True})
    dump(OUT/'harness_after_analysis.json',harness())
    files=[p for folder in [OUT,PREP] for p in folder.rglob('*') if p.is_file()]+[Path(__file__),observer,CFG,PLAN,HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_data_script_outputs_only_raw_AGPL_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    print(json.dumps({'A68_assessed':True,'audit_checks':len(checks),'roles':[{'nodes_with_elements':m['translational_nodes_with_element_incidence'],'parts':m['translational_part_title_counts']} for m in model_rows],'new_native':0}),flush=True)

if __name__=='__main__':main()
