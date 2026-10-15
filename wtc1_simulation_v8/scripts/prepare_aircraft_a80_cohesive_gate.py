"""Preserve A80 read-only investigations and a concrete, unrun A81 witness."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,shutil

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a80_preparation'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a80'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a80_preparation.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a80_proposal.json'
CONTACT=ROOT/'tmp/aircraft_a80_contact_path'
TOPO=ROOT/'tmp/aircraft_a80_pair_eligibility'
REVIEW=ROOT/'tmp/aircraft_a80_witness_review'
REPORT=OUT/'rapport_aircraft_a80.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A80_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A81_2026-10-15.md'


def route():
    return ('AIRCRAFT-A81 proposée, non exécutée : un Starter puis un Engine conditionnel CPU1/plafond180s chacun, '
        'moteur A73 inchangé, zéro correctif, compilation, GPU, installation ou prolongement de l’impact entier. '
        'Témoin cohésif LAW117/TYPE43 exact,8nœuds/100mm²/8g instrumentaux, aucun contact général : '
        'compression−0,05mm, ouverture0,3mm puis refermeture−0,05mm, horizon0,65ms. '
        'Mesurer impulsions/réactions, contraintes, énergie, OFF et défaillance des quatre points ; '
        'USR absents ou nuls ne prouvent pas un dommage nul. Une rupture avant le gap nominal0,5mm rend '
        'insuffisante la simple attente jusqu’à sortie complète ; cette politique n’est pas retenue sans ce contrôle. '
        'Modes purs, aire constante et compressions avant/après à qualifier nativement. '
        'Accord distinct requis : unique Starter A79 consommé, aucun Engine prévu dans ce lot précédent. '
        'Conserver analyses R0/R1, anciennes sorties, budgets et critères échoués. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def stage():
    assert not any(p.exists() for p in [PREP,OUT,CFG,PLAN])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A79' and h['RegistryEntries']==198
    top=read(TOPO/'pair_cohesive_topology_review_r1.json');assert top['pass_topology_presence_only']
    independent=read(REVIEW/'independent_static_witness_review.json');assert independent['pass_static_preparation_review_only']
    w=CONTACT/'witness_preparation';final=read(w/'configuration_A81_final.json')
    assert read(w/'scope_review.json')['pass']
    assert final['Starter']==final['Engine_conditional']==1 and final['cpu']==1 and final['each_cap_s']==180
    assert read(CONTACT/'pair_lifecycle_specification_v3.json')['status']=='design_path_not_retained_pending_cohesive_gate'
    sources=[p for folder in [CONTACT,TOPO,REVIEW] for p in folder.iterdir() if p.is_file() and p.suffix in ['.json','.md','.py']]
    sources += [p for p in w.rglob('*') if p.is_file()]
    PREP.mkdir();OUT.mkdir();dump(OUT/'harness_before_preparation.json',h)
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A80_PREPARATION','seed':1102104,'random_draws':0,
        'purpose':'Reuse explicitly exploratory read-only investigations; synthesize contact-policy stop condition and prepare one new isolated cohesive loop',
        'units':'g/mm/ms unchanged; coupon8g distinct from whole budgets',
        'exploratory_analyses_predate_this_synthesis_declaration_and_are_not_native':True,
        'sources':[{'path':rel(p),'sha256':sha(p)} for p in sorted(sources)],
        'new_Starter':0,'new_Engine':0,'software_source_modified':False,'native_witness_authorized':False})
    for folder,label in [(CONTACT,'contact_design'),(TOPO,'cohesive_topology'),(REVIEW,'independent_review')]:
        d=PREP/label;d.mkdir()
        for p in folder.iterdir():
            if p.is_file() and p.suffix in ['.json','.md','.py']:shutil.copy2(p,d/p.name)
    target=PREP/'A81_COHESIVE_LOOP';shutil.copytree(w,target)
    for row in final['inputs']:
        assert sha(target/row['path'])==row['sha256']
    raw=read(w/'configuration_A81_proposed.json')
    assert raw['inputs']==final['inputs']
    proposal=PREP/'proposition_A81_compression_rupture_refermeture.md'
    shutil.copy2(w/'proposition_A81_compression_rupture_refermeture.md',proposal)
    with proposal.open('a',encoding='utf8',newline='\n') as f:
        f.write('\nComplément de portée avant résultats : la formule énergétique A67 est conservée séparément, tolérance0,02×K0+1e−7J. Ici K0=0 donc1e−7J ; ni1e−5J ni2%du travail de rupture ne la remplacent silencieusement. Son échec reste enregistré et distinct de la réussite de l’observation. Toute autre qualification du bilan au chargement imposé sera déclarée séparément avant ses résultats. Aucun nouveau calcul tant que publication A78+A79 et accord explicite A81 ne sont pas vérifiés.\n')
    plan={**final,'prepared_utc':now(),'iteration':'AIRCRAFT-A80_PROPOSAL',
        'new_explicit_human_authorization_required':True,'proposal':rel(proposal),'proposal_sha256':sha(proposal),
        'inputs':[{'path':rel(target/row['path']),'bytes':(target/row['path']).stat().st_size,'sha256':row['sha256']} for row in final['inputs']],
        'prepared_configuration':rel(target/'configuration_A81_final.json'),
        'prepared_configuration_sha256':sha(target/'configuration_A81_final.json'),
        'static_scope_review':rel(target/'scope_review.json'),
        'independent_review':rel(PREP/'independent_review/independent_static_witness_review.json'),
        'independent_final_addendum':rel(PREP/'independent_review/independent_final_addendum.json'),
        'retained_A67_energy_gate':{'formula_J':'0.02*K0_J+1e-7','K0_J':0,'tolerance_J':1e-7,
            'additional_driven_work_gate_not_substituted_after_results':True},
        'publication_A78_A79_must_be_verified_before_native_A81':True}
    dump(PLAN,plan)
    a={'created_utc':now(),'iteration':'AIRCRAFT-A80','status':'completed_read_only_cohesive_topology_and_sub_gap_rupture_gate__native_loop_unrun',
        'new_Starter':0,'new_Engine':0,'software_source_modified':False,'compilation':False,
        'all4430_initial_pairs_classified_topology_only':True,'direct_cohesive_edge_pairs':2910,
        'vertex_only_pairs':1520,'current_cohesive_elements_present':624,'root_host_rebindings_present':144,
        'R0_identity_failure_retained_R1_current_paths_presence_only':True,
        'topology_is_not_contact_exclusion_qualification':True,
        'initial_gap_exit_only_policy_not_retained':True,'source_feature_not_ready_to_compile':True,
        'conditional_pure_mode_I_initiation_mm':450/4400,'conditional_pure_mode_I_failure_mm':2*50/450,
        'nominal_gap_mm':.5,'future_Starter':1,'future_conditional_Engine':1,'future_each_cap_s':180,'future_CPU':1,
        'future_software_patch_compilation_GPU_installation_whole_extension':False,
        'future_witness_native_not_authorized':True,'independent_static_checks':len(independent['checks']),
        'independent_final_addendum_checks':6,'A67_literal_energy_tolerance_J_retained':1e-7,
        'all_old_failed_gates_and_physical_budgets_preserved':True,'best_whole_physical_s':.0200001220703125,
        'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A81'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'topology_review':rel(PREP/'cohesive_topology/pair_cohesive_topology_review_r1.json'),
        'prepared_plan':rel(PLAN),'physical_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A80 — vérifier la cohésion avant de changer le contact

Préparation en lecture seule, zéro calcul natif et aucun correctif appliqué. La politique d’attente jusqu’à sortie du gap n’est pas retenue : une rupture cohésive peut la précéder. Un témoin concret A81 est préparé, non exécuté, non autorisé. Les analyses exploratoires conservées précèdent la déclaration de cette synthèse ; elles ne sont pas présentées comme des exécutions natives préenregistrées.

## 1. Faits directement observés ou transcrits

Les4430paires A79 sont reliées aux assemblages du modèle courant :2910sur des facettes de même peau partageant une arête et un joint direct, dont les916erreurs ;1520partagent seulement un sommet d’origine. Pour ces dernières,1108chemins de longueur2 et412de longueur3 existent autour du sommet. Les624joints et chemins RBE2 vers leurs coins sont présents. Le contrôle R0 d’identité avec A20 échoue sur144hôtes réaffectés ; il reste conservé. R1 vérifie les raccords écrits actuellement vers les racines, sans conclure équivalence mécanique. Aucune exclusion de contact n’est ainsi qualifiée.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La documentation logicielle [TYPE7](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm) décrit une réduction de gap pour Inacti5/6 ; ces options ne satisfont pas ici la conservation du gap exigée. La sémantique [TYPE25](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm) d’ignorance initiale puis réentrée n’est pas transférée par la seule valeur1000. Des sources logicielles ciblées en cache expliquent stockage/tri/effort/matrice ; elles ne prouvent pas l’identité du Starter Windows avec ces sources.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source inspectée ou modifiée. Les seuls membres copiés proviennent du cache logiciel épinglé, avec empreintes conservées séparément ; leurs sources brutes ne sont pas incluses dans le manifeste public propre. Aucun dégât connu ciblé.

## 4. Hypothèses propres au modèle

Graine1102104 pour la synthèse, zéro tirage. Les nœuds distincts et les joints séparables restent conservés. Une table persistante par paire demanderait une nouvelle fonction transversale Starter/Engine, engagement au pas accepté, annulation des essais Newton et reprise/tri cohérents. Ce n’est pas un petit correctif prêt à compiler. Surtout, sous les hypothèses de modeI pur et d’évolution linéaire, les paramètres actuels EN4400,TN450,GI50 donnent450/4400=0,10227mm d’initiation et2×50/450=0,22222mm de rupture, avant le gap0,5mm. La rupture native et la compression résiduelle ne sont pas déduites de cette formule seule.

## 5. Résultats dérivés

Un témoin A81 conserve les cartes numériques LAW117/TYPE43 et la géométrie validée A67 : huit nœuds, carré100mm²,8g de masses instrumentales, sans contact général. Il impose en Z une compression−0,05mm, une ouverture0,3mm et une refermeture−0,05mm sur0,65ms. Les translationsXY restent libres comme la trame dynamique ; dériveXY, cisaillement, uniformité, aire et orientation doivent être contrôlés nativement avant d’invoquer le modeI. Les21contrôles indépendants de préparation et20contrôles du générateur passent, sans qualification native. Les10417échantillons de chargement sont vérifiés, erreur maximale5,01e−13mm. Un Starter puis un Engine uniquement si la préparation passe, unCPU/plafond180s chacun ; logiciels A73/Starter inchangés, zéro compilation/GPU/installation ou extension entière.

Les sorties demandent tous les pas acceptés, état final réel, OFF/contraintes/énergie et variables utilisateur. Leur peuplement natif n’est pas présumé. Les réactions de nœuds du précédent témoin sont des impulsions cumulées ; la pente de l’impulsion du support bas sur les plateaux de compression doit être comparée avant/après, référence conditionnelle22000N et tolérance2% héritée A67. Ne pas lire une impulsion comme une force. L’absence de contact dans le coupon sert uniquement à isoler la cohésion.

Six contrôles supplémentaires relient la configuration finale aux cartes inchangées. Le critère énergétique A67 conservé est0,02×K0+1e−7J ; ici K0=0, donc1e−7J. Il n’est remplacé ni par1e−5J ni par2%du travail de rupture après consultation des résultats. Une éventuelle qualification complémentaire du travail imposé devra être déclarée séparément avant ses résultats. Un échec de ce critère reste distinct du succès de la mesure.

## 6. Contradictions et informations manquantes

La compression après suppression éventuelle de l’élément n’est pas qualifiée ; une branche constitutive compressive ne garantit pas qu’un élément supprimé la transmette. Confirmer la rupture par statut natif/événements des quatre points, jamais par le déplacement0,3mm seul. USR absents ou nuls ne prouvent pas un dommage nul ; les champs manquants après suppression ne sont pas une guérison. Un essai complet peut réfuter la politique d’attente géométrique sans qualifier un futur contact. L’échec d’observation reste conservé sans réessai automatique. L’unique Starter A79 est consommé et n’autorise aucun nouveau Starter/Engine. Aucun nouveau correctif proposé à compiler. A75/A77/A79,107391avertissements A73, budgets et limites restent conservés. Meilleur impact entier0,0200001220703125s ; dix secondes physiques et vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A80 → AIRCRAFT-A81\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(proposal)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, harness/state.json, harness/publication_cycle.json puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(proposal)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prioritaire. Les fichiers A80 peuvent être préparés sans être encore enregistrés si publication A78+A79 attend sa connexion ; vérifier état réel et preuve finale avant tout calcul A81.\n'+route()+'\nNouvelles courtes en français, aucun diagnostic natif rejoué.\n',encoding='utf8')
    dump(OUT/'harness_after_preparation.json',harness())
    dump(OUT/'preparation_verification.json',{'created_utc':now(),'pass':True,'prepared_not_registered':True,
        'new_native':0,'all_inputs_hashed':True,'plan_sha256':sha(PLAN),'report_sha256':sha(REPORT),
        'prior_A79_scientific_manifest_unchanged':all(sha(ROOT/r['path'])==r['sha256'] for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a79/artifact_manifest.json')['files'])})
    print(json.dumps({'A80_prepared':True,'registered':False,'new_native':0,'A81_requires_authorization':True}),flush=True)


def register():
    assert not (OUT/'artifact_manifest.json').exists()
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a78_a79/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    h=harness();s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert h['RegistryEntries']==198 and s['current_iteration']=='AIRCRAFT-A79' and cycle['pending_iterations']==[]
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_registration_'+Path(name).name))
    pv=read(OUT/'preparation_verification.json');assert pv['pass']
    assert sha(PLAN)==pv['plan_sha256'] and sha(REPORT)==pv['report_sha256']
    for row in read(CFG)['sources']:assert sha(ROOT/row['path'])==row['sha256']
    dump(OUT/'verified_prior_publication.json',proof)
    a=read(OUT/'scientific_assessment.json');stamp=now();next_route=route()
    auth_path=ROOT/'wtc1_simulation_v8/data/aircraft_a81_authorization.json'
    if auth_path.exists():
        authorization=read(auth_path);assert authorization['explicit_human_authorization']
        assert sha(PLAN)==authorization['plan_sha256']
        dump(OUT/'subsequent_A81_authorization_received.json',{'created_utc':stamp,
            'authorization':rel(auth_path),'authorization_sha256':sha(auth_path),
            'receipt':authorization['question_item'],'Starter_consumed':0,'Engine_consumed':0,
            'later_than_initial_preparation':True,'publication_condition_satisfied':True})
        a.update(A81_subsequent_authorization_received=True,A81_authorization=rel(auth_path),
            A81_authorization_receipt=authorization['question_item'])
        next_route=next_route.replace('Accord distinct requis : unique Starter A79 consommé, aucun Engine prévu dans ce lot précédent.',
            'Accord A81 reçu et sauvegardé ; condition de publication A78+A79 satisfaite. Un Starter et un Engine conditionnel encore non consommés : ne pas redemander cet accord.')
    files=[p for folder in [PREP,OUT] for p in folder.rglob('*') if p.is_file()]
    files += [CFG,PLAN,Path(__file__),HANDOFF,PROMPT]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'own_files_only_no_AGPL_raw':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    entry={'experiment_id':'WTC1-AIRCRAFT-A80','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),
        'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A80',next_iteration='AIRCRAFT-A81',current_status=a['status'],next_objective=next_route,updated_at=stamp)
    s['aircraft_a80_key_results']=entry
    s['validated_artifacts'].update(aircraft_a80_report=rel(REPORT),aircraft_a80_results=rel(OUT/'composite_qualification_review.json'),aircraft_a80_handoff=rel(HANDOFF))
    cycle.update(pending_iterations=['AIRCRAFT-A80'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A80+AIRCRAFT-A81 verified')
    for path,value in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cycle)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==199
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,
        'harness':h,'new_native':0,'whole_qualified':False,'objective1_complete':False,'next_iteration':'AIRCRAFT-A81'})
    print(json.dumps({'A80_registered':True,'registry':199,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','register'])
    globals()[p.parse_args().action]()
