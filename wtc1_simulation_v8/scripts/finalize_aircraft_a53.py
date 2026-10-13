"""Seal the measured graph defect and unapplied proposal, then hand off for human review."""
from probe_aircraft_a53 import *
from finalize_aircraft_a22 import verify_files
import difflib

REPORT = OUT/'rapport_aircraft_a53.md'
HANDOFF = ROOT/'harness/handoffs/WTC1_AIRCRAFT_A53_HANDOFF.md'


def route():
    return ('AIRCRAFT-A54 : demander l’accord explicite de Jeremy pour la proposition '
            'wtc1_simulation_v8/output/aircraft_a53/proposition_correctif_graphe_moteur.md '
            'avant toute application ou compilation. A53 identifie le vrai bloc fautif : '
            '128 triangles SH3N du fuselage, éléments193..320,89nœuds, coordonnées exactes ; '
            '24paires6/6 et144lignes manquantes. Une observation séparée du modèle entier '
            'A49 non regroupé montre une écriture TYPE2 dans ICOK au mauvais pas24 pour '
            'une ligne principale exigeant ICOKM au pas119, puis inflation du compteur '
            'de3à4 alors que le voisin existe déjà ; colonne correcte toujours0. '
            'Correctif d’un fichier préparé mais non appliqué et non compilé, huit '
            'contrôles Python de graphes réussis sans qualification native du correctif. '
            'Après autorisation seulement : troisième moteur isolé depuis la source '
            '3d75ff13d1946f6d28a43920eac4fa2aae41b27a, patch exact conservé, dépendances '
            'existantes, aucune installation/GPU, compilation≤1h et sixCPUmaximum ; '
            'contrôles natifs≤180s, destination des écritures puis CHECK original/candidat '
            'et lois/contacts/bilans. Ne pas déplacer les entrées physiques ni traiter '
            'les TYPE25 ignorés comme des contacts qualifiés. En dimensionnement, '
            'conserver le padding et les indices globaux ordinaires ; en construction, '
            'principales row-INK. A52 groupée reste rejetée, anciennes erreurs conservées. '
            'Meilleur impact entierA20=0,0200001220703125s ; objectif dix secondes physiques '
            '3D puisMP4/GIF incomplet. Jeremy demande de terminer A53 et sa publication '
            'puis de reprendre dans une nouvelle session ; ne pas commencer A54 ici.')


def proposal_static_review():
    meta = read(OUT/'engine_patch_proposal_review.json')
    for key, hkey in [('proposed_source_path','proposed_sha256'),('patch_path','patch_sha256')]:
        assert streamsha(ROOT/meta[key]) == meta[hkey]
    with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
        m = next(m for m in tar if m.name.endswith('/'+meta['source_path']))
        original = tar.extractfile(m).read()
    assert hashlib.sha256(original).hexdigest() == meta['original_sha256']
    before = original.decode().splitlines(keepends=True)
    after = (ROOT/meta['proposed_source_path']).read_text(encoding='utf8').splitlines(keepends=True)
    changed = []
    for tag, a, b, c, d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag != 'equal':
            assert (2320 <= a+1 <= 2570) or (2780 <= a+1 <= 2930) or a == len(before), (tag,a,b)
            changed.append({'kind':tag,'original_start_1based':a+1,'original_end_exclusive_1based':b+1,'proposed_start_1based':c+1,'proposed_end_exclusive_1based':d+1})
    patch = (ROOT/meta['patch_path']).read_text(encoding='utf8').splitlines()
    bad = [s for s in patch if s.startswith('+') and not s.startswith('+++') and s[1:2].lower() != 'c' and len(s)-1 > 72]
    assert not bad
    assert not meta['patch_applied'] and not meta['compiled_or_native_qualified']
    return {'created_utc':now(),'pass':True,'changed_ranges':changed,'added_fixed_form_code_lines_over72':bad,
            'scope':'Static diff scope and line length only; no Fortran compilation, installed-source patch or native qualification.',
            'original_source_sha256':meta['original_sha256'],'proposed_source_sha256':meta['proposed_sha256'],
            'raw_third_party_proposed_source_excluded_from_public_manifest':True}


def prepare():
    guard()
    assert not REPORT.exists() and not HANDOFF.exists()
    assert read(ROOT/'harness/state.json') == read(OUT/'before_state.json')
    assert read(ROOT/'harness/publication_cycle.json') == read(OUT/'before_publication_cycle.json')
    m = read(OUT/'actual_triangle_source_mapping_review.json')
    t = read(OUT/'WHOLE_CURRENT_TRIANGLE_BLOCK_TRACE/trace_result.json')
    w = read(OUT/'WHOLE_REFERENCE_GRAPH_WRITE_WATCH/write_watch_result.json')
    o = read(OUT/'graph_storage_oracle_review.json')
    assert m['pass_actual_block_mapping'] and m['actual_elements']==128 and m['actual_nodes']==89
    assert m['maximum_coordinate_error_mm']==0 and len(m['missing_pairs'])==24
    assert sum(p['missing_rows'] for p in m['missing_pairs'])==144
    assert t['ASSEM_C3_calls']==1 and t['assembly_calls']==1579 and t['Engine_exit_code']==3
    assert w['Engine_exit_code']==0 and len(w['write_events'])==12
    assert sum(e['watched_wrong_column_written'] for e in w['write_events'])==1
    assert not any(e['watched_correct_column_written'] for e in w['write_events'])
    assert w['watch']['local_row'] > w['watch']['dimensions']['INK']
    assert o['all_oracle_cases_pass'] and len(o['cases'])==8
    changed=[]
    oldrows=read(OUT/'preservation_before_metadata.json')['files']
    for row in oldrows:
        st=(ROOT/row['path']).stat()
        if st.st_size!=row['bytes'] or st.st_mtime_ns!=row['mtime_ns_before']:
            changed.append(row['path'])
    assert not changed,changed
    for cfg in (ROOT/'wtc1_simulation_v8/data').glob('aircraft_a53*.json'):
        c=read(cfg)
        for row in c.get('files',[]):
            assert streamsha(ROOT/row['path'])==row['sha256']
    assert streamsha(WHOLE)==read(ROOT/'wtc1_simulation_v8/data/aircraft_a49_predeclaration.json')['whole_input_sha256']
    assert streamsha(CAND/'source.tar.gz')==read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/source_archive.json')['sha256']
    dump(OUT/'proposal_static_scope_review.json',proposal_static_review())
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'old_files_metadata_checked':len(oldrows),
         'changed_paths':changed,'immutable_SHA256_manifests_retained':True,'fresh_all_old_content_rehash':False,
         'whole_original_fresh_SHA256':streamsha(WHOLE),'Engine_fresh_SHA256':streamsha(BINARY),'source_archives_not_rescanned':True})
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_after_calculation.json',h)
    a={'created_utc':now(),'iteration':'AIRCRAFT-A53','status':'completed_actual_triangle_block_mapped_native_wrong_graph_write_proved__unapplied_patch_awaits_explicit_software_authorization',
       'new_Starter_executions':0,'new_Engine_executions':4,'actual_fault_block_kind':'SH3N','actual_fault_elements':128,
       'actual_fault_original_element_ID_range':[193,320],'actual_fault_nodes':89,'coordinate_error_mm':0,
       'native_fault_offset':'ASSEMC_KIJ+0x664','assembly_calls_before_fault':1579,'missing_sparse_pairs':24,
       'missing_sparse_rows':144,'missing_pair_NDOF':[6,6],'native_IKPAT':1,'fault_input_mapping_gate_pass':True,
       'stale_C4_context_rejected':True,'REORDER_entry_probe_calls':0,'function_entry_probe_inconclusive':True,
       'native_original_reference_wrong_column_write_observed':True,'observed_graph_row':9891,'INK':9888,'NNMAX':24,'NKMAX':119,
       'native_observed_original_node':48151,'already_present_original_neighbor_written_to_wrong_table':48154,
       'correct_initial_row_count':3,'observed_count_after_duplicate_wrong_write':4,'bounded_last_observed_count':14,
       'correct_next_column_remained_zero_in12events':True,'observed_wrong_column_writes':1,'observed_correct_column_writes':0,
       'all_errors_causal_explanation_proved':False,'independent_Python_graph_oracle_cases_pass':8,
       'proposal_static_scope_pass':True,'patch_applied':False,'patch_compiled_or_native_qualified':False,
       'requires_explicit_user_software_authorization':True,'source_license':'AGPL-3.0-or-later',
       'new_installation_or_compilation':False,'source_binary_or_process_mechanics_patched':False,
       'mass_or_inertia_compensation':False,'original_whole_input_modified':False,'paired_A52_candidate_remains_rejected':True,
       'whole_insertion_ready':False,'new_whole_extension_executed':False,'new_whole_duration_credit_s':0,
       'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'next_iteration':'AIRCRAFT-A54',
       'user_requested_session_handoff':True}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,
         'actual_triangle_mapping':m,'native_wrong_graph_write':w,'graph_oracle':o,
         'unapplied_proposal':read(OUT/'engine_patch_proposal_review.json'),'whole_impact_qualified':False})
    executions=[{'path':rel(p),**read(p)} for p in sorted(OUT.rglob('*.execution.json'))]
    assert len(executions)==4 and all(e['CPU_threads']==1 and e['cap_s']==180 and not e['GPU'] for e in executions)
    dump(OUT/'runtime_manifest.json',{'created_utc':now(),'executions':executions,'new_Starter_executions':0,
         'new_Engine_executions':4,'old_successful_solver_replays':0,'new_instrumented_measurements_of_existing_cases':True,
         'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'software_installation_or_compilation':False,
         'source_binary_or_process_mechanical_data_patched':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':a['best_whole_physical_s'],
         'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A53 — vrai bloc fautif identifié et écriture de graphe incorrecte observée

Le bloc arrêté appartient à la peau triangulaire du fuselage. Une mesure séparée du moteur inchangé montre une écriture dans le mauvais tableau de connexions, suivie d’une augmentation du compteur de la ligne correcte. Un correctif limité est préparé ; il n’est ni appliqué ni compilé. A53 termine le diagnostic et prépare la décision suivante, sans prolonger l’impact.

## 1. Faits directement observés ou transcrits

Quatre Engine nouveaux, aucun Starter, un CPU chacun, limite180s, aucun GPU. Les durées internes des observations sont respectivement8,500s,8,134s,7,154s et7,786s ; les journaux conservent séparément les durées des lanceurs. Les trois premières exécutions terminent code3 au signal natif ; le lanceur d’observation peut terminer0 sans que le moteur réussisse. La référence non regroupée termine code0/NORMAL mais conserve ses erreurs mécaniques connues.

La première capture observe263ASSEM_C4 et1579ASSEMC. Son dernier bloc de quadrangles ne correspond toujours pas au bloc fautif ; tentative conservée et contexte rejeté. La capture suivante ajouteASSEM_C3 : un appel, bloc courantNEL128, connectivitéIXTG de largeur6. Chaque couple NI/NJ correspond à son élément courant. Les128éléments193..320 correspondent exactement à SH3N/1,fuselage_skin, propriété1, matériau1/LAW2 ; leurs89nœuds ont un écart de coordonnées nul. Premier élément193 :[97,121,122]. La faute ASSEMC_KIJ+0x664 concerne24pairesNDOF[6,6] et144lignes absentes, IKPAT1. Premier couple interne[42833,42834] : labels[97,121]. Le nœud97 est principal de septRBE2 ;121n’a aucun rôleRBE2 déclaré. La vérification ne dépend plus des huit peaux du contexte périmé A52.

Un contrôle d’entréeREORDER_A capture zéro appel, résultat inconclusif conservé : une optimisation/inlining peut expliquer l’absence, mais elle n’est pas prouvée uniquement par cette capture. Le défaut est ensuite observé par surveillance matérielle de trois adresses de données dans notre propre processus fils, sur l’entrée originale A49 non regroupée.

Au début IND_KINE_K :NNMAX24,NKMAX119,NKINE11064,INK9888. Le nœud d’entrée48151 correspond à l’indice42826, ligne9891>INK, compteur3 ; colonnes correctes[42827,42828,42829]. L’adresse correcte est0x616470c6d7c0 ; le calcul avec le pas ordinaire24 donne0x616470c6d4c8. Une écriture à l’adresse incorrecte ajoute42827(label48154), déjà présent dans la ligne correcte. L’instruction suivante est à l’offset0xbfe7be. Puis le compteur de la ligne correcte augmente3→4 à0xbfe7c2, alors que sa quatrième colonne reste0. Les douze événements bornés montrent le compteur monter jusqu’à14, une écriture dans la colonne incorrecte et aucune dans la colonne correcte observée. Aucun total global de mauvaises écritures n’est inféré de ces douze événements.

## 2. Résultats d’un modèle officiel

Aucun nouveau modèle historique officiel exécuté. Source moteur figée3d75ff13d1946f6d28a43920eac4fa2aae41b27a, binaireA44 intact. Les symboles et signatures sont vérifiés dans cette source et les adresses lues dans le processus exécuté. Les observateurs changent les registres matériels de débogage, aucune instruction, tableau mécanique, donnée de reprise ou binaire.

La source distingue deux rangements. Dans IND_KINE_K, les lignes ordinaires utilisent ICOK avec le pasNNMAX ; les principales utilisent ICOKM avec le pasNKMAX et l’indice row-INK. Dans DIM_KINE_T, les principales précèdent les ordinaires. Le tableau ordinaire de dimensionnement garde les indices globaux avec padding, selon l’allocation existante ; il ne faut pas y appliquer row-INK. Les branchesRBE2/RBE3 choisissent déjà ces tableaux, alors que les branchesTYPE2 emploient directement ICOK. Les écritures mesurées confirment un cas concret de mauvais rangement.

- [Assemblage triangulaire](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/assem_c3.F)
- [Dimensionnement et construction du graphe](https://github.com/gabrielrussell/OpenRadioss/blob/3d75ff13d1946f6d28a43920eac4fa2aae41b27a/engine/source/implicit/ind_glob_k.F)

## 3. Affirmations provenant des archives locales

Aucune nouvelle archive historique, vidéo, photographie ou source officielle inspectée. Les archives restent en lecture seule. Les dégâts historiques et les résultatsNIST ne servent pas de cible d’ajustement.

## 4. Hypothèses propres au modèle

Graine1102078 et configurations JSON fixées avant leurs mesures natives, aucun tirage dans ces quatre mesures. Les huit contrôles indépendants Python de rangement utilisent séparément cette graine pour des graphes synthétiques : ils vérifient des ensembles de voisins, aucune probabilité de l’événement réel. Les hypothèses physiques héritées restent celles des entrées ; aucune masse, inertie, loi de matériau, charge ou liaison mécanique compensatoire n’est ajoutée.

Le correctif proposé touche un fichier ind_glob_k.F : cinq ajouts, une lecture et un test d’appartenance dans chacun des deux blocs TYPE2, avec trois fonctions auxiliaires de sélection du rangement. Le dimensionnement garde son padding ; la construction utilise row-INK pour les principales. Les anciennes routines hors de ces deux blocs et déclarations restent identiques. Le contrôle statique vérifie la portée de la différence et la limite72colonnes des nouvelles lignes ; il ne compile pas le Fortran.

## 5. Résultats dérivés

L’attribution aux128triangles/89nœuds passe la connectivité et les coordonnées natives exactes. La surveillance prouve une écriture de colonne dans le mauvais tableau et une inflation du compteur correct pour un voisin déjà présent. C’est un défaut de stockage observé, sans preuve que sa correction résoudra toutes les15erreurs et49370messages de la référence ni l’ensemble des arrêts de variantes.

Les huit contrôles dictionnaire/ensembles passent, y compris les domaines sans principales ou sans ordinaires. Le cas natif observé montre compteur attendu3 contre4 après l’ajout erroné. Les sources complètes proposées et le patch AGPL restent dans tmp/aircraft_a53_graph_patch_proposal/, exclus du manifeste public ; leurs empreintes et la proposition sont conservées. Aucun moteur installé modifié, aucun nouveau binaire produit, aucun effet natif du correctif qualifié.

Les sorties anciennes sont conservées : métadonnées comparées avec manifestes SHA256 existants, sans nouvelle relecture intégrale. Entrées effectivement utilisées, source moteur figée, binaire et original entier sont recontrôlés. Les harnais PASS et empreintes vérifient la traçabilité ; ils ne valident pas la physique.

## 6. Contradictions et informations manquantes

Le regroupement A52 reste rejeté : équivalence des attaches native indisponible. Les erreurs initiales, la captureC4périmée et le contrôleREORDERsans appel restent archivés. La compilation et les essais du correctif ne sont pas autorisés par l’ancien accord A43 portant sur la source non modifiée. AGENTS.md exige une demande explicite pour les modifications de logiciels ; la proposition séparée prépare un troisième moteur isolé, compilation≤1h/sixCPU, dépendances existantes, sans nouvelle installation ni GPU, puis contrôles natifs≤180s.

CHECK force la voiePCG/IPREC5 et n’est pas une dynamiqueMUMPS qualifiée. Les cinqTYPE25 ignorés en implicite restent bloquants pour un impact avec ces contacts. Les lois cohésives chargées/croissanceA40, peauxA34, raffinementA36, travaux locaux/énergie et autres critères restent échoués ou manquants. Les essais sans charge et le défaut de logiciel ne qualifient pas l’initiation ou l’effondrement historique.

Meilleur impact entier A20 :0,0200001220703125seconde. Aucun temps des diagnostics A53 n’est crédité. L’objectif dix secondes physiques simulées, visualisation3D puisMP4/GIF, reste incomplet. Jeremy demande de finir cette sous-tâche et de préparer une nouvelle session : A54 ne commence pas ici. Publication A52+A53 selon l’autorisation existante, puis prompt de reprise daté avec preuve distante finale.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A53 → AIRCRAFT-A54\n\nRapport : '+rel(REPORT)+
         '\nRésultats : '+rel(OUT/'composite_qualification_review.json')+
         '\nProposition : '+rel(OUT/'proposition_correctif_graphe_moteur.md')+'\n\n'+route()+'\n',encoding='utf8')
    files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'wtc1_simulation_v8/scripts').glob('*aircraft_a53*.py'))+list((ROOT/'wtc1_simulation_v8/data').glob('aircraft_a53*.json'))+[HANDOFF]
    assert not any(rel(p).startswith('tmp/') for p in files)
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in sorted(set(files))]})
    print({'A53_prepared':True,'native_defect_observed':True,'patch_unapplied':True},flush=True)


def register():
    guard();n=verify_files(read(OUT/'artifact_manifest.json')['files'])
    st=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert st==read(OUT/'before_state.json') and cy==read(OUT/'before_publication_cycle.json')
    reg=ROOT/'harness/experiments/registry.jsonl';prefix=(OUT/'before_registry.jsonl').read_bytes();assert reg.read_bytes()==prefix
    a=read(OUT/'scientific_assessment.json');t=now()
    row={'experiment_id':'WTC1-AIRCRAFT-A53','registered_at':t,'configuration':rel(CFG),'report':rel(REPORT),
         'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
         'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with reg.open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    old=read(OUT/'before_state.json')
    st.update(current_iteration='AIRCRAFT-A53',next_iteration='AIRCRAFT-A54',current_status=a['status'],next_objective=route(),updated_at=t)
    st['aircraft_a53_key_results']=row
    st['validated_artifacts'].update(aircraft_a53_report=rel(REPORT),aircraft_a53_results=rel(OUT/'composite_qualification_review.json'),aircraft_a53_handoff=rel(HANDOFF))
    cy['pending_iterations'].append('AIRCRAFT-A53');cy.update(pending_count=2,updated_at=t,next_publication_after='AIRCRAFT-A52+AIRCRAFT-A53 verified')
    dump(ROOT/'harness/state.json',st);dump(ROOT/'harness/publication_cycle.json',cy)
    h=harness();tail=reg.read_bytes()[len(prefix):].decode('utf8').splitlines()
    checks={'hashes':True,'harness':h['Status']=='PASS','registry_single_append':len(tail)==1 and json.loads(tail[0])['experiment_id']=='WTC1-AIRCRAFT-A53',
            'prior_results':all(st[k]==old[k] for k in old if k.endswith('_key_results')),
            'objective_preserved':st['objective1_video_10s']==old['objective1_video_10s'],
            'old_outputs_preserved':read(OUT/'preservation_verification.json')['pass'],'route':st['next_iteration']=='AIRCRAFT-A54',
            'pending':cy['pending_iterations']==['AIRCRAFT-A52','AIRCRAFT-A53'],'no_patch_applied':not a['patch_applied']}
    assert all(checks.values()),checks
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'new_files_verified':n,
         'checks':checks,'harness':h,'whole_impact_qualified':False,'objective1_complete':False})
    print({'A53_registered':True,'new_files':n,'next':'AIRCRAFT-A54','registry_entries':len(reg.read_text(encoding='utf8').splitlines())},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','register']);globals()[p.parse_args().action]()
