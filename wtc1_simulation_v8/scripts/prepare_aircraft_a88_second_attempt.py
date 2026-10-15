"""Read cached A87 and prepare one unmodified-engine observation of the second trial."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import ast,json,re,shutil,tarfile,subprocess

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a88';PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a88_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a88_common_layout_audit'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a88_preparation.json';PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a88_proposal.json'
REPORT=OUT/'rapport_aircraft_a88.md';PROPOSAL=PREP/'proposition_observation_second_essai_A89.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A88_HANDOFF.md';PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A89_2026-10-15.md'
OBSERVER=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a89_second_attempt_linux.py'
DRIVER=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a89_second_attempt.py'

def route():
    return ('AIRCRAFT-A89 proposée non exécutée : un seul EngineA87 inchangé sous observateur en lecture seule, '
        'CPU1/plafond180s, restart initial propre A81 et carte exacte A83 réutilisés ; zéro Starter, correctif, '
        'compilation, GPU ou installation. Lire au second essai les coordonnéesD/DD, forces libres, références, '
        'normes natives et tous les paramètres accessibles de la garde, avec cycle/temps natifs. '
        'Quatre points matériels, désactivation après le critère2 du second essai, puis terminaison propre. '
        'Accord distinct requis : troisEngineA87 consommés ; son CHECK conditionnel inutilisé ne couvre pas '
        'cette nouvelle observation. Aucune nouvelle cause présumée ; ne pas élargir la garde sans preuve. '
        'Conserver seuils, sorties, budgets, critères échoués et contacts bloquants. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')

def common_names(text,name):
    lines=text.splitlines();start=next(i for i,l in enumerate(lines) if re.search(r'COMMON\s*/'+name+r'/',l))
    body=lines[start][6:].split('/'+name+'/')[1]
    for line in lines[start+1:]:
        if len(line)>5 and line[5] not in [' ','0']:body+=line[6:]
        else:break
    return [x.strip() for x in body.split(',') if x.strip()]

def stage():
    assert not any(p.exists() for p in [OUT,PREP,PRIVATE,CFG,PLAN,OBSERVER,DRIVER])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A87' and h['RegistryEntries']==206
    OUT.mkdir();PREP.mkdir();PRIVATE.mkdir();dump(OUT/'harness_before_preparation.json',h)
    assessment=read(ROOT/'wtc1_simulation_v8/output/aircraft_a87/scientific_assessment.json')
    assert assessment['first_two_regressions_pass'] and assessment['saved_coupon_nonzero_states']==1
    d=ROOT/'wtc1_simulation_v8/output/aircraft_a87/native/COMPRESSION_RUPTURE_RECLOSE'
    text=(d/'A81_COHESIVE_COMPRESSION_PARTIAL_OPEN_RECLOSE_0001.out').read_text(encoding='utf8')
    assert text.count('WTC1 EXACT NULL FREE RELATIVE CRITERIA')==1 and 'ISTOP=-2' in text
    cache=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
    assert sha(cache)=='d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8'
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A88_PREPARATION','seed':1102112,'random_draws':0,
        'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','new_Engine':0,'new_Starter':0,'source_patch_compilation_GPU_installation':False})
    copies=[]
    with tarfile.open(cache,'r:gz') as archive:
        members=archive.getmembers()
        for name in ['com01_c.inc','com04_c.inc','com08_c.inc','impl1_c.inc','task_c.inc']:
            mm=[m for m in members if m.name.endswith('/engine/share/includes/'+name)];assert len(mm)==1
            p=PRIVATE/name;p.write_bytes(archive.extractfile(mm[0]).read());copies.append({'member':mm[0].name,'path':rel(p),'sha256':sha(p)})
    dump(PRIVATE/'source_selection.json',{'created_utc':now(),'pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','unmodified_copies':copies})
    fields={}
    selected={'COM01':('com01_c.inc',['NCYCLE','IRODDL','NSPMD']),
        'COM04':('com04_c.inc',['NUMNOD','NFXVEL','NINTER']),
        'IMPL1':('impl1_c.inc',['IDYNA','IQSTAT','INSOLV','NITOL','ISPRB','IMCONV','IDTC','ILAST']),
        'TASK':('task_c.inc',['NTHREAD'])}
    for common,(filename,labels) in selected.items():
        names=common_names((PRIVATE/filename).read_text(encoding='utf8'),common)
        for label in labels:fields[label]={'symbol':common.lower()+'_','byte_offset':4*names.index(label),'kind':'i32','source_sha256':sha(PRIVATE/filename)}
    fields['TT']={'symbol':'com08_','byte_offset':0,'kind':'f64','source_sha256':sha(PRIVATE/'com08_c.inc')}
    assert fields['NCYCLE']['byte_offset']==16 and fields['IDYNA']['byte_offset']==84 and fields['IQSTAT']['byte_offset']==184
    binary=ROOT/'wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate/isolated_exec/engine_linux64_gf_ompi'
    assert sha(binary)==assessment['new_binary_sha256']
    r=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-S',linux(binary)],capture_output=True,text=True,timeout=30);assert r.returncode==0
    symbols={};globals_={};required={v['symbol'] for v in fields.values()}
    for line in r.stdout.splitlines():
        m=re.match(r'^([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([A-Za-z])\s+(\w+)$',line)
        if m and m[4] in ['nl_solv_','crit_ite_','produt_uhp_']:symbols[m[4]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
        if m and m[4] in required:globals_[m[4]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
    assert len(symbols)==3 and set(globals_)==required
    for field in fields.values():assert field['byte_offset']+({'i32':4,'f64':8}[field['kind']])<=globals_[field['symbol']]['bytes']
    source=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a85_normalization_linux.py'
    s=source.read_text(encoding='utf8').replace('new_A85_explicit_human_consent','new_A89_explicit_human_consent')
    s=s.replace("events=[];current=None;pending=None;deliver=0;traps=0","events=[];current=None;pending=None;deliver=0;traps=0;attempt=0")
    s=s.replace("def snapshot(a):\n",'''def native_globals():
            result={}
            for label,field in c['native_globals'].items():
                address=base+c['global_symbols'][field['symbol']]['offset']+field['byte_offset']
                result[label]=i32(pid,address) if field['kind']=='i32' else f(address)
            return result
        def snapshot(a):
''')
    s=s.replace("return {'NDDL':n,'NDDL0':i32(pid,a[38])","return {'native_globals':native_globals(),'ICONT':i32(pid,a[58]),'NDDL':n,'NDDL0':i32(pid,a[38])")
    s=s.replace('traps<=64','traps<=96').replace('a=args(r,41);it=i32(pid,a[26]);assert 0<=it<=2',
        'a=args(r,59);it=i32(pid,a[26]);assert 0<=it<=2\n                if it==0:attempt+=1\n                assert attempt<=2')
    s=s.replace("current={'iteration':it,'pointers':a}","current={'iteration':it,'pointers':a,'attempt':attempt}")
    s=s.replace("'event':'NL_SOLV_entry','iteration':it","'event':'NL_SOLV_entry','attempt':attempt,'iteration':it")
    s=s.replace("assert current is not None\n                a=args(r,6)","assert current is not None\n                if attempt!=2:continue\n                a=args(r,6)")
    s=s.replace("'event':'CRIT_ITE_entry','iteration':it","'event':'CRIT_ITE_entry','attempt':attempt,'iteration':it")
    s=s.replace('if current is not None and nl<=ret<nl_end:', 'if current is not None and attempt==2 and nl<=ret<nl_end:')
    s=s.replace('All breakpoints disabled at criterion iteration2.','All breakpoints disabled at criterion iteration2 of attempted step2.')
    ast.parse(s);OBSERVER.write_text(s,encoding='utf8',newline='\n')
    oldplan=read(ROOT/'wtc1_simulation_v8/data/aircraft_a84_proposal.json')
    p={**oldplan,'created_utc':now(),'iteration':'AIRCRAFT-A88_PROPOSAL','seed':1102112,'case':'SECOND_NEWTON_REFERENCES',
        'observer':rel(OBSERVER),'observer_sha256':sha(OBSERVER),'symbols':symbols,'native_globals':fields,'global_symbols':globals_,
        'unchanged_software':[oldplan['unchanged_software'][0],{'path':rel(binary),'sha256':sha(binary)}],
        'previous_A83_Engine_remaining':0,'A87_used_Engine':3,'A87_unused_CHECK_not_reassigned':True,
        'measure':['Raw DE0,EIMP,R02,F,D,DD and native U2/DU2 on second attempted step',
            'Current criterion ratios and guard mode parameters, ICONT, NCYCLE and TT'],
        'no_newton_global_time_cycle_observation_promised':False,
        'observation_acceptance':['Second attempted step actually reached, native cycle/time recorded',
            'Raw corrections and norms captured before criterion2 on that attempt',
            'All nonfinite values classified; source byte ranges and ABI checked','No numeric state/code modification; native terminal stop preserved'],
        'expected_wall_s':[5,30]}
    p.pop('source_static_review',None);p.pop('source_static_review_sha256',None)
    review_path=PREP/'source_and_observer_static_review.json'
    checks={'two_attempt_counter_bounded':"assert attempt<=2" in s,'criterion_capture_targets_attempt2':"if attempt!=2:continue" in s,
        'product_returns_targets_attempt2':'attempt==2 and nl<=ret<nl_end' in s,'native_cycle_time_typed':set(['NCYCLE','TT']).issubset(fields),
        'native_ICONT_from_verified_argument58':"i32(pid,a[58])" in s,'four_hardware_slots_only':"sites=[nl," in s,
        'trap_bound96':'traps<=96' in s,'same_readonly_memory_and_no_numeric_writes':'os.O_RDONLY' in s and 'os.pwrite' not in s,
        'same_exact_inputs':all(sha(ROOT/r['path'])==r['sha256'] for r in p['inputs']),
        'fresh_A87_symbols_not_A73_offsets':symbols!=oldplan['symbols'],'all_common_fields_in_symbol_bounds':True,
        'syntax_valid':True,'source_software_and_physics_unchanged':True}
    assert all(checks.values())
    dump(review_path,{'created_utc':now(),'pass':True,'checks':checks,'private_source_selection':rel(PRIVATE/'source_selection.json'),
        'source_selection_sha256':sha(PRIVATE/'source_selection.json'),'previous_observer':rel(source),'previous_observer_sha256':sha(source),
        'actual_runtime_observer_unqualified':True,'new_Engine_Starter':0})
    p['source_static_review']=rel(review_path);p['source_static_review_sha256']=sha(review_path);dump(PLAN,p)
    driver=(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a85_normalization.py').read_text(encoding='utf8')
    driver=driver.replace('aircraft_a85','aircraft_a89').replace('AIRCRAFT-A85','AIRCRAFT-A89').replace('new_A85','new_A89')
    driver=driver.replace('aircraft_a84','aircraft_a88').replace('AIRCRAFT-A84','AIRCRAFT-A88')
    driver=driver.replace('updates_2026-10-15_aircraft_a82_a83','updates_2026-10-15_aircraft_a86_a87').replace('AIRCRAFT-A83','AIRCRAFT-A87')
    driver=driver.replace("h['RegistryEntries']==203","h['RegistryEntries']==207").replace('for n in [83,84]:','for n in [87,88]:')
    driver=driver.replace("'node_count':8,","'node_count':8,'native_globals':c['native_globals'],'global_symbols':c['global_symbols'],")
    ast.parse(driver);DRIVER.write_text(driver,encoding='utf8',newline='\n')
    dump(PREP/'final_launcher_review.json',{'created_utc':now(),'pass':True,'checks':{'syntax_valid':True,'same_one_Engine_no_Starter_driver':True,
        'native_global_metadata_passed':"'native_globals':c['native_globals']" in driver,'fresh_A89_authorization_required':"aircraft_a89_authorization.json" in driver,
        'expected_registry207':"h['RegistryEntries']==207" in driver},'plan_sha256':sha(PLAN),'launcher':rel(DRIVER),'launcher_sha256':sha(DRIVER)})
    PROPOSAL.write_text('''# Proposition A89 — observer le second essai avec le moteur A87 inchangé

A87 compile, conserve les deux régressions exactement et accepte le premier pas du coupon. Il enregistre deux états, à0 et0,000125ms ; au second essai les ratios redeviennentInfinity/NaN, puis arrêt79. Une seule activation de la nouvelle garde est imprimée. La condition qui exclut le second cas n’a pas été mesurée et ne sera pas présumée à partir des seuls messages.

Un seul Engine A87 inchangé proposé, sous observateur en lecture seule, unCPU/plafond180s, estimation5–30s. Même carteA83 et même restart initial propreA81 ; chargement, tolérances, bornes de pas et horizon conservés. Zéro Starter, correctif, compilation, GPU, installation ou prolongement entier. Publication A86+A87 vérifiée avant lancement. L’ancienne place de CHECK conditionnelle non consommée ne couvre pas cette nouvelle observation ; nouvel accord distinct requis.

Le lecteur suit deux essais, lit les références et lesD/DD au second, capture les normes natives et critères1/2 de ce second essai, ainsi que les modes de la garde,ICONT, cycleNCYCLE et tempsTT natifs. Les positions typées des COMMON sont dérivées des déclarations source épinglées et bornées par les symboles du binaire A87 exact. Quatre points d’exécution matériels,96arrêts maximum, lecture seule des données ; désactivation après le critère2 du second essai, puis terminaison native. Aucune instruction, donnée numérique ou registre numérique remplacé. Les registres matériels de débogage sont les seuls configurés.

But : distinguer une correction sur coordonnées imposées d’une correction libre, ou une autre condition exclue, à partir des valeurs réellement lues. Aucune condition ne sera retirée et aucun critère abaissé dans ce lot. Une capture manquée consomme sa place sans réessai automatique. Une observation réussie ne donne aucun crédit mécanique entier. Rupture et refermeture restent non atteintes ; toutes les anciennes sorties, budgets et critères échoués conservés. Dix secondes et vidéo3D incomplètes.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A88','status':'completed_read_only_second_attempt_audit__unchanged_A87_observer_prepared_unrun',
        'new_Engine':0,'new_Starter':0,'source_patch_compilation_GPU_installation':False,'last_saved_coupon_time_ms':assessment['last_saved_coupon_time_ms'],
        'first_step_null_guard_native_marker':1,'second_step_guard_exclusion_not_yet_observed':True,
        'future_maximum_Engine':1,'future_maximum_Starter':0,'future_CPU':1,'future_cap_s':180,
        'source_static_checks':len(checks),'new_explicit_consent_received':False,'A87_unused_CHECK_not_reassigned':True,
        'all_old_failed_gates_outputs_and_budgets_preserved':True,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A89'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A88 — préciser le second essai avant toute nouvelle modification

## 1. Faits directement observés ou transcrits

A87 : compilation réussie, deux régressions identiques aux histoires sauvegardées et seuils mécaniques conservés. Une activation de garde au premier essai, deux états réels dont un positif à0,000125ms ; second essai bloqué parInfinity/NaN puis79/ISTOP−2. TroisEngine consommés, CHECK conditionnel non lancé. Lecture des sorties sauvegardées seulement, aucun nouveau moteur exécuté.

## 2. Résultats d’un modèle officiel

Aucun résultat historique officiel nouveau. Les déclarations de COMMON du solveur épinglé décrivent les modes et le cycle/temps ; leurs positions sont calculées avec types explicites et vérifiées sur la taille des symboles du binaire A87. Cette lecture de code ne donne pas leurs valeurs réellement actives au second essai.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée/modifiée. Cinq copies logicielles épinglées restent privées et exclues du manifeste propre. Anciennes sources, neuf moteurs précédents et moteurA87 conservés.

## 4. Hypothèses propres au modèle

Graine1102112, zéro tirage. Une correction non nulle sur coordonnées imposées pourrait exclure la garde exigeantDD entièrement nul, même avec un sous-espace libre nul ; une autre condition pourrait aussi l’exclure. Aucune de ces hypothèses n’est identifiée comme fait sans capture. Ne pas remplacer arbitrairement les non-finis ou élargir la garde.

## 5. Résultats dérivés

Préparation d’un lecteur ciblant le second essai : mêmes entrées initiales, moteurA87 exact, nouveaux symboles et positions typées bornées. CaptureD/DD, forces, références, normes, ratios et modes, avecNCYCLE/TT natifs. Quatre points matériels maximum,96arrêts bornés, aucune écriture numérique ; arrêt de l’observation au critère2 du second essai. Le lanceur garde unEngineCPU1/180s, zéroStarter et exige un nouvel accord. Aucun correctif moteur ou compilation proposé pour cette observation.

## 6. Contradictions et informations manquantes

Le second cas n’est pas encore observé en mémoire et le nouveau lecteur reste non qualifié nativement. Les champs A87 initiaux partiellement peuplés et le faible résidu énergétique sur deux états ne qualifient ni la trajectoire0,65ms ni sa rupture/refermeture. La place de CHECK conditionnelle inutilisée est réservée à ce CHECK et ne devient pas un autre essai. Anciennes sorties, critères échoués et budgets conservés ; meilleur impact entier0,0200001220703125s, dix secondes et vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A88 → AIRCRAFT-A89\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prime ; vérifierpublicationA86+A87. Aucun calcul en cours.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_preparation.json',harness());dump(OUT/'preparation_verification.json',{'created_utc':now(),'pass':True,'prepared_not_registered':True,'plan_sha256':sha(PLAN),'report_sha256':sha(REPORT)})
    print(json.dumps({'A88_prepared':True,'source_static_checks':len(checks),'proposed_Engine':1,'new_native':0}),flush=True)

def register():
    assert not (OUT/'artifact_manifest.json').exists();proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a86_a87/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    h=harness();s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert h['RegistryEntries']==206 and s['current_iteration']=='AIRCRAFT-A87' and cy['pending_iterations']==[]
    pv=read(OUT/'preparation_verification.json');assert sha(PLAN)==pv['plan_sha256'] and sha(REPORT)==pv['report_sha256']
    final=read(PREP/'final_observer_review.json')
    assert final['pass'] and final['plan_sha256']==sha(PLAN) and final['observer_sha256']==sha(OBSERVER) and final['launcher_sha256']==sha(DRIVER)
    assert sha(ROOT/final['reviewer_script'])==final['reviewer_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_registration_'+Path(n).name))
    dump(OUT/'verified_prior_publication.json',proof)
    for row in read(ROOT/'wtc1_simulation_v8/output/aircraft_a87/artifact_manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A87_sealed_files_rehashed':True,'new_native':0})
    files=[p for folder in [OUT,PREP] for p in folder.rglob('*') if p.is_file()]+[CFG,PLAN,OBSERVER,DRIVER,Path(__file__),HANDOFF,PROMPT,ROOT/final['reviewer_script']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_outputs_only_raw_AGPL_includes_excluded':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    a=read(OUT/'scientific_assessment.json');stamp=now();entry={'experiment_id':'WTC1-AIRCRAFT-A88','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    entry.update(final_observer_checks=len(final['checks']),final_observer_review_pass=True)
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A88',next_iteration='AIRCRAFT-A89',current_status=a['status'],next_objective=route(),updated_at=stamp);s['aircraft_a88_key_results']=entry
    s['validated_artifacts'].update(aircraft_a88_report=rel(REPORT),aircraft_a88_results=rel(OUT/'composite_qualification_review.json'),aircraft_a88_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A88'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A88+AIRCRAFT-A89 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cy)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==207
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,'new_native':0,'whole_qualified':False,'next_iteration':'AIRCRAFT-A89'})
    print(json.dumps({'A88_registered':True,'registry':207,'pending_publication':1}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','register']);globals()[p.parse_args().action]()
