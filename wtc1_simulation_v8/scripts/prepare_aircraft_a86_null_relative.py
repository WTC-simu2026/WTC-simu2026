"""Prepare an unapplied exact-zero relative-criterion patch and bounded controls."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import json,copy,math,difflib,shutil,tarfile

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a86'
PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a86_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a86_null_relative_proposal'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a86_preparation.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a86_proposal.json'
REPORT=OUT/'rapport_aircraft_a86.md'
PROPOSAL=PREP/'proposition_criteres_relatifs_exactement_nuls_A87.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A86_HANDOFF.md'
PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A87_2026-10-15.md'


def route():
    return ('AIRCRAFT-A87 proposée non exécutée : nouveau traitement A86 des critères relatifs exactement nuls, '
        'moteur isolé numéro10, application/compilation seulement après accord explicite distinct. '
        'Plafond compilation1h/6CPU, puis au maximum4EngineCPU1/180s, zéro Starter/GPU/installation. '
        'Deux régressions libres anciennes avec le nouveau binaire, puis boucle A81 ; CHECK entier uniquement '
        'si toutes les qualifications locales passent. Aucun prolongement dynamique entier. '
        'Garde limitée Newmark non quasi-statique, Newton modifié, trois critères123, mouvement imposé, '
        'sans interface générale/rotation, un domaine/un thread, itération>=2, force libre et correction '
        'exactement nulles, référencesEIMP=0/DE0=1e−20 et normesU2=DU2=0. '
        'Les tolérances et le chemin non dégénéré restent inchangés ; l’itération1 conserve son ancien affichageInfinity. '
        'Le critère relatif reçoit0 dans ce seul sous-espace nul ; cela ne valide pas l’énergie physique indépendante. '
        'A85consommé, aucun nouveau correctif appliqué ou compilé ; budgets, échecs et sorties conservés. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')


def eligible(s):
    """Independent mathematical predicate model; not execution of the Fortran patch."""
    mode=(s['IDYNA']==2 and s['IQSTAT']==0 and s['INSOLV']==1 and s['NITOL']==123 and s['ISPRB']==0
        and s['IRIKS']==0 and s['NFXVEL']>0 and s['NINTER']==0 and s['IRODDL']==0 and s['NSPMD']==1
        and s['NTHREAD']==1 and s['IT']>=2 and s['IMCONV']>=0 and s['NDDL']>0 and s['ICONT']==0)
    exact=(s['EIMP']==0 and s['DE0']==1e-20 and s['R2']==0 and 0<s['R02']<1e30
        and all(v==0 for v in s['F']) and all(v==0 for v in s['DD']) and s['U2']==0 and s['DU2']==0)
    return mode and exact


def stage():
    assert not any(p.exists() for p in [OUT,PREP,PRIVATE,CFG,PLAN])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A85' and h['RegistryEntries']==204
    OUT.mkdir();PREP.mkdir();PRIVATE.mkdir();dump(OUT/'harness_before_preparation.json',h)
    source=ROOT/'wtc1_simulation_v8/openradioss_runtime/a84_normalization_audit/nl_solv.F'
    selection=read(source.parent/'source_selection.json')
    assert sha(source)==next(r['sha256'] for r in selection['copied_members_unmodified'] if r['private_path']==rel(source))
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A86_PREPARATION','seed':1102109,'random_draws':0,
        'source_pin':selection['pin'],'base_source':rel(source),'base_source_sha256':sha(source),
        'observed_basis':'wtc1_simulation_v8/output/aircraft_a85/observation_review.json',
        'new_Engine':0,'new_Starter':0,'new_build':False,'patch_applied':False})
    old=source.read_text(encoding='utf8');anchor='       RE=DE0/EIMP\n';tail='       CALL CRIT_ITE(IT,RU,RR1,RE,NDIV,NL_TOL)'
    assert old.count(anchor)==old.count(tail)==1
    declaration='      LOGICAL WTC_NULL_REL\n'
    guard='''C----Exact null free subspace: no tolerance or nonzero-path change.
       WTC_NULL_REL=.FALSE.
       IF (IDYNA==2.AND.IQSTAT==0.AND.INSOLV==1.AND.
     .     NITOL==123.AND.ISPRB==0.AND.IRIKS==0.AND.
     .     NFXVEL>0.AND.NINTER==0.AND.IRODDL==0.AND.
     .     NSPMD==1.AND.NTHREAD==1.AND.IT>=2.AND.
     .     IMCONV>=0.AND.NDDL>0.AND.ICONT==0) THEN
        IF (EIMP==ZERO.AND.DE0==EM20.AND.R2==ZERO.AND.
     .      R02>ZERO.AND.R02<EP30) THEN
         IF (ALL(F(1:NDDL)==ZERO).AND.
     .       ALL(DD(1:3,1:NUMNOD)==ZERO)) THEN
          CALL PRODUT_UHP(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                    D,DR,U2,W_DDL)
          CALL PRODUT_UHP(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                    DD,DDR,DU2,W_DDL)
          WTC_NULL_REL=(U2==ZERO.AND.DU2==ZERO)
         ENDIF
        ENDIF
       ENDIF
       IF (WTC_NULL_REL) THEN
        RE=ZERO
        RU=ZERO
        IF (INPRINT/=0) WRITE(IOUT,*)
     .   'WTC1 EXACT NULL FREE RELATIVE CRITERIA, ITER=',IT
       ELSE
'''
    assert all(len(line)<=72 for line in (declaration+guard+'       ENDIF\n').splitlines())
    new=old.replace('      FR = 0 ! was not always initialized before use',declaration+'      FR = 0 ! was not always initialized before use',1)
    new=new.replace(anchor,guard+anchor,1).replace(tail,'       ENDIF ! WTC_NULL_REL\n'+tail,1)
    # This is a private proposed file, never an operational source tree.
    proposed=PRIVATE/'nl_solv.proposed.F';proposed.write_text(new,encoding='utf8',newline='\n')
    patch=PRIVATE/'null_free_relative_criteria.patch'
    patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile='engine/source/implicit/nl_solv.F',tofile='engine/source/implicit/nl_solv.F')),encoding='utf8',newline='\n')
    base={'IDYNA':2,'IQSTAT':0,'INSOLV':1,'NITOL':123,'ISPRB':0,'IRIKS':0,'NFXVEL':4,'NINTER':0,'IRODDL':0,
        'NSPMD':1,'NTHREAD':1,'IT':2,'IMCONV':0,'NDDL':8,'ICONT':0,'EIMP':0.,'DE0':1e-20,'R2':0.,'R02':1.,
        'F':[0.]*8,'DD':[0.]*24,'U2':0.,'DU2':0.}
    cases=[('exact_observed_null_case',copy.deepcopy(base),True)]
    negatives={'IDYNA':[0,1],'IQSTAT':[1],'INSOLV':[2,4,5],'NITOL':[1,2,3,12,13,23],
        'ISPRB':[1],'IRIKS':[1],'NFXVEL':[0],'NINTER':[1,5],'IRODDL':[1],
        'NSPMD':[2],'NTHREAD':[2,6],'IT':[0,1],'IMCONV':[-1,-2],'NDDL':[0],'ICONT':[1],
        'EIMP':[1e-300,-1e-300,float('nan'),float('inf')],
        'DE0':[0,math.nextafter(1e-20,0),math.nextafter(1e-20,1),float('nan'),float('inf')],
        'R2':[1e-300,-1,float('nan'),float('inf')],'R02':[0,-1,1e30,float('nan'),float('inf')],
        'U2':[1e-300,-1,float('nan'),float('inf')],'DU2':[1e-300,-1,float('nan'),float('inf')]}
    for key,values in negatives.items():
        for j,value in enumerate(values):
            s=copy.deepcopy(base);s[key]=value;cases.append((f'reject_{key}_{j}',s,False))
    for key,count in [('F',8),('DD',24)]:
        for index in range(count):
            s=copy.deepcopy(base);s[key][index]=1e-300
            cases.append((f'reject_underflowing_nonzero_{key}_{index}',s,False))
    rows=[]
    for label,s,expected in cases:
        got=eligible(s);assert got==expected,label;rows.append({'case':label,'expected_guard':expected,'actual_guard':got,'pass':True})
    core=old[old.index(anchor):old.index(tail)]
    checks={'old_nonnull_ratio_block_exactly_preserved':core in new,
        'convergence_function_CRIT_ITE_exactly_preserved':old[old.index('      SUBROUTINE CRIT_ITE('):]==new[new.index('      SUBROUTINE CRIT_ITE('):],
        'one_new_logical_declaration':new.count('      LOGICAL WTC_NULL_REL')==1,
        'first_iteration_original_path_preserved':eligible({**base,'IT':1}) is False,
        'all_new_fixed_format_lines_within72':True,'one_changed_engine_file':True,
        'no_tolerance_or_material_load_dt_changes':True,'no_patch_applied_or_compiled':True,
        'all_adversarial_predicate_cases_pass':True,'nonzero_underflowing_F_rejected':not eligible({**base,'F':[1e-300]+[0.]*7})}
    assert all(checks.values())
    dump(PREP/'prototype_review.json',{'created_utc':now(),'pass':True,'checks':checks,'mathematical_cases':rows,
        'mathematical_cases_count':len(rows),'python_predicate_is_not_native_Fortran_validation':True,
        'new_Engine_Starter_compilation':0,'current_source_sha256':sha(source),'proposed_source_sha256':sha(proposed),'patch_sha256':sha(patch)})
    previous=ROOT/'wtc1_simulation_v8/data/aircraft_a73_predeclaration.json';recipe=read(previous)
    for field in ['patch','scratch_patch','original_scratch_patch','surface_patch','current_area_patch','check_zero_residual_patch','CHECK_context_patch','build','preservation']:assert field in recipe
    inputs=[]
    for case in ['FREE_Ismstr4','AREA_EVOLUTION_FREE_Y']:
        folder=ROOT/f'wtc1_simulation_v8/output/aircraft_a67/native/{case}';name='A67_'+case
        assert read(folder/'mechanical_review.json')['pass']
        pp=[folder/(name+'_0001.rad'),folder/(name+'_0000_0001.rst')]
        inputs.append({'case':case,'name':name,'kind':'new_binary_regression_against_saved_A67',
            'inputs':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in pp],
            'saved_reference_review':rel(folder/'mechanical_review.json'),'target_ms':1,
            'existing_thresholds_preserved':True,'normal_termination_and_existing_mechanical_gates_required':True})
    a85=read(ROOT/'wtc1_simulation_v8/data/aircraft_a85_predeclaration.json')
    inputs.append({'case':'COMPRESSION_RUPTURE_RECLOSE','name':a85['name'],'kind':'original_A81_witness_first_new_candidate_trajectory',
        'inputs':a85['inputs'],'target_ms':.65,'requires_prior_regressions_pass':True,
        'energy_absolute_J':1e-7,'energy_relative_to_initial_K':.02,'initial_K_J':0,
        'complete_native_TH_fields_reactions_damage_and_independent_energy_required':True,
        'zero_USR_fields_do_not_certify_population':True})
    whole=ROOT/'wtc1_simulation_v8/output/aircraft_a67/WHOLE_ORIGINAL_CHECK';name='A49_EQUIVALENT_RIGID_CHAINS'
    inputs.append({'case':'WHOLE_ORIGINAL_CHECK','name':name,'kind':'bounded_CHECK_only_no_whole_dynamics',
        'inputs':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [whole/(name+'_0001.rad'),whole/(name+'_0000_0001.rst')]],
        'requires_all_local_mechanical_and_energy_gates_pass':True,
        'TYPE25_ignored5_and_107391_warnings_remain_blocking':True,'general_interface_guard_must_stay_off':True})
    p={'created_utc':now(),'iteration':'AIRCRAFT-A86_PROPOSAL','seed':1102109,'random_draws':0,
        'source_pin':selection['pin'],'patch':{'target':'engine/source/implicit/nl_solv.F','current_source':rel(source),'current_sha256':sha(source),
            'proposed_source':rel(proposed),'proposed_sha256':sha(proposed),'patch':rel(patch),'patch_sha256':sha(patch),'applied':False,'compiled':False},
        'prototype_review':rel(PREP/'prototype_review.json'),'prototype_review_sha256':sha(PREP/'prototype_review.json'),
        'baseline_recipe':rel(previous),'baseline_recipe_sha256':sha(previous),'baseline_builder':'wtc1_simulation_v8/scripts/build_aircraft_a73_CHECK_context.py',
        'baseline_builder_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a73_CHECK_context.py'),
        'future_candidate':'wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate','future_Engine_number':10,
        'maximum_build_s':3600,'CPU_build':6,'maximum_Engine':4,'maximum_Starter':0,'CPU_native':1,'each_native_cap_s':180,
        'GPU':False,'installation':False,'whole_dynamic_extension':False,'new_explicit_human_authorization_required':True,
        'cases':inputs,'no_automatic_retry_or_reassignment_of_conditional_slots':True,
        'reference_contract':'wtc1_simulation_v8/data/aircraft_a67_controls.json',
        'reference_contract_sha256':sha(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json'),
        'new_null_definition_changed_only_for_exact_degenerate_case':True,
        'old_first_iteration_Infinity_not_hidden':True,'independent_physical_energy_not_replaced_by_algorithm_EIMP':True,
        'old_Engines_sources_results_failed_gates_budgets_preserved':True,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,p)
    PROPOSAL.write_text('''# Proposition A87 — critères relatifs dans un sous-espace libre exactement nul

A85 a mesuréDE0=1e−20,EIMP=0,U2=DU2=0, force libre exactement nulle et correctionDD entièrement nulle ; les coordonnées imposées bougent. Le calcul des ratios produitInfinity puisNaN. Le correctif préparé définit les deux critères relatifs à0 pour ce seul cas dégénéré d’équilibre libre exact. Leur définition change dans ce cas ; les tolérances ne changent pas. L’énergie physique et le travail imposé restent soumis à des contrôles indépendants, jamais remplacés parEIMP.

La garde exige Newmark dynamique non quasi-statique, Newton modifié, critères123, déplacement imposé, aucun contact/interface générale, aucune rotation, un domaine et un thread, itération au moins2, état de convergence non négatif. Elle exige aussiEIMP exactement0,DE0 exactement1e−20,R2 exactement0, référenceR02 positive et bornée, toutes les composantesF libres etDD exactement0, puis normes nativesU2 etDU2 exactement0. Des valeurs non nulles même sous-normales,NaN ouInfinity ne satisfont pas cette garde. Les cas non dégénérés et CRIT_ITE restent textuellement inchangés. L’itération1 conserve son ancien chemin et peut encore imprimerInfinity ; ce fait ne sera pas masqué. Un marqueur est imprimé quand la garde intervient avec impression nonlinéaire active.

Une seule source est concernée :engine/source/implicit/nl_solv.F. Diff et fichier proposé sont préparés en privé, sous leur licence source ; aucun arbre opérationnel ni binaire n’est modifié, aucune compilation effectuée. La recette A73 complète est conservée, avec tous ses correctifs et sa dépendance déjà en cache. Proposition : appliquer ce diff exact puis compiler un dixième moteur isoléA87, plafond1h, sixCPU, sans GPU ni installation. Les neuf moteurs précédents restent conservés. Une compilation ne donne aucun crédit physique.

Après construction réussie, au maximum quatreEngine sur unCPU,180s chacun, zéro Starter : d’abord les deux régressionsFREE_Ismstr4 etAREA_EVOLUTION_FREE_Y à1ms, mêmes cartes/restarts et seuils A67, comparaison aux sorties sauvegardées ; ensuite seulement si elles passent la boucleA81 originale compression−0,05/ouverture0,3/refermeture−0,05mm jusqu’à0,65ms, sans changement de chargement, bornes, tolérances, masse, matériau ou sorties. Enfin un CHECK entier uniquement si tous les critères mécaniques/énergétiques locaux passent. Les cinqTYPE25 ignorés et107391avertissements restent bloquants ; aucun impact entier dynamique prolongé.

Le témoin de boucle doit réellement atteindre son horizon, fournir tous les états, réactions et champs nécessaires, qualifier leur peuplement, le mouvement libre, l’aire, la rupture et la refermeture. Tolérance énergétique initiale conservée :0,02*K0+1e−7J, iciK0=0, donc1e−7J. Aucun remplacement par une fraction du travail de fracture. Une trajectoire aboutie ne suffit pas si ces critères échouent. Une place échouée/expirée est consommée ; aucun réessai automatique ni réaffectation d’un CHECK conditionnel inutilisé.

Le prototype mathématique vérifie le cas observé et des cas adverses, dont forces non nulles dont le carré sous-déborde, correction non nulle sur chacun des24axes, références non finies et modes exclus. Ces contrôles statiques ne sont pas une validation Fortran native. Les sources opérationnelles et binaires restent inchangés. Accord distinct requis avant application, compilation et lotA87 ; l’accordA85 couvrait seulement une observation désormais consommée. Dix secondes physiques et vidéo3D incomplètes.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A86','status':'completed_static_exact_null_relative_criteria_proposal__unapplied_uncompiled',
        'new_Engine':0,'new_Starter':0,'new_build':False,'patch_applied':False,'compiled':False,
        'new_null_criterion_definition_not_a_tolerance_change':True,'one_proposed_engine_source_file':True,
        'source_and_mathematical_review_pass':True,'adversarial_mathematical_cases':len(rows),'static_scope_checks':len(checks),
        'future_Engine_number':10,'future_build_cap_s':3600,'future_CPU_build':6,'future_maximum_Engine':4,
        'future_maximum_Starter':0,'future_CPU_native':1,'future_each_cap_s':180,'GPU_installation_whole_dynamics':False,
        'new_explicit_consent_received':False,'all_old_failed_gates_outputs_and_budgets_preserved':True,
        'independent_loop_energy_tolerance_J':1e-7,'first_iteration_Infinity_path_preserved':True,
        'native_patch_behavior_unqualified':True,'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,
        'objective1_complete':False,'next_iteration':'AIRCRAFT-A87'}
    dump(OUT/'scientific_assessment.json',a)
    dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,
        'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A86 — proposition bornée pour les critères relatifs dégénérés

Préparation statique uniquement : aucun correctif appliqué, aucune compilation, zéro Engine/Starter. Le changement de définition des deux ratios est explicite et limité au sous-espace exactement nul observé ; les tolérances restent conservées.

## 1. Faits directement observés ou transcrits

A85 mesure la force libre nulle, toutes les correctionsDD nulles,DE0=1e−20,EIMP=0,U2=DU2=0 et le déplacement normal imposé non nul. Les rapports et captures restent conservés. La source préparée provient du cache épinglé, sans modification d’un arbre opérationnel.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. La recette logicielle A73 est reprise sans changement de dépendance. Les divisions d’origine restent exactes hors de la nouvelle garde ; CRIT_ITE est conservée intégralement.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée. Le diff et la copie logicielle proposés restent privés sous licence source, exclus du manifeste propre de publication. Neuf anciens moteurs, sources et résultats restent intacts.

## 4. Hypothèses propres au modèle

Graine1102109, zéro tirage. Choix numérique proposé : attribuer0 aux deux erreurs relatives indéfinies seulement lorsque les inconnues libres sont exactement en équilibre et sans correction. Ce choix est un changement algorithmique explicite, pas une propriété physique mesurée. Il ne calcule pas le travail imposé et ne démontre ni rupture ni conservation énergétique. Une garde très restrictive évite d’étendre le choix aux mouvements libres non nuls ou aux contacts. Le chemin de l’itération1 reste inchangé et sonInfinity possible reste visible.

## 5. Résultats dérivés

Un seul fichier moteur proposé, gardes exactes, pas de seuil heuristique supplémentaire. Le bloc original non dégénéré et la fonction de convergence sont textuellement conservés. Le prototype mathématique vérifie le cas observé et rejette les variantes hors portée, sous-normales/non finies et chacune des composantes de force/correction non nulles. Les lignes nouvelles respectent le format fixe. Ce contrôle Python statique n’est pas une exécution du codeFortran. Deux régressions A67 sauvegardées doivent être confrontées au nouveau binaire, puis la boucle A81 seulement si elles passent ; un CHECK entier reste conditionnel aux qualifications locales, jamais un prolongement d’impact.

## 6. Contradictions et informations manquantes

Le correctif n’est ni appliqué ni compilé et son comportement natif reste inconnu. La boucle A81 pourrait encore échouer après le premier pas, notamment sur une loi, l’historiqueUSR, le travail imposé ou les critères d’énergie. Le seuil indépendant1e−7J est maintenu ; aucun succès ne sera accordé au seul changement des ratios. Accord distinct requis pour un dixième moteur isolé et quatreEngine au plus ; A85consommé n’autorise aucune modification. Les cinq contactsTYPE25,107391avertissements, limites, budgets et échecs antérieurs restent bloquants. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A86 → AIRCRAFT-A87\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prime ; vérifierpublicationA84+A85. Aucun calcul en cours ; correctif préparé nonappliqué noncompilé.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_preparation.json',harness())
    dump(OUT/'preparation_verification.json',{'created_utc':now(),'pass':True,'prepared_not_registered':True,
        'plan_sha256':sha(PLAN),'report_sha256':sha(REPORT),'patch_applied':False,'compiled':False})
    print(json.dumps({'A86_prepared':True,'mathematical_cases':len(rows),'patch_applied':False,'compiled':False}),flush=True)


def register():
    assert not (OUT/'artifact_manifest.json').exists()
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a84_a85/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    h=harness();s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert h['RegistryEntries']==204 and s['current_iteration']=='AIRCRAFT-A85' and cy['pending_iterations']==[]
    pv=read(OUT/'preparation_verification.json');assert pv['pass'] and sha(PLAN)==pv['plan_sha256'] and sha(REPORT)==pv['report_sha256']
    final=read(PREP/'final_scope_review.json')
    assert final['pass'] and final['plan_sha256']==sha(PLAN)
    assert sha(ROOT/final['builder'])==final['builder_sha256'] and sha(ROOT/final['reviewer_script'])==final['reviewer_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_registration_'+Path(n).name))
    dump(OUT/'verified_prior_publication.json',proof)
    for row in read(ROOT/'wtc1_simulation_v8/output/aircraft_a85/artifact_manifest.json')['files']:assert sha(ROOT/row['path'])==row['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A85_sealed_files_rehashed':True,'old_native_replayed':False})
    files=[p for folder in [OUT,PREP] for p in folder.rglob('*') if p.is_file()]+[CFG,PLAN,Path(__file__),HANDOFF,PROMPT,
        ROOT/final['builder'],ROOT/final['reviewer_script']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'raw_AGPL_patch_and_proposed_source_excluded':True,
        'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    a=read(OUT/'scientific_assessment.json');stamp=now()
    entry={'experiment_id':'WTC1-AIRCRAFT-A86','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),
        'publication_verification':rel(OUT/'publication_verification.json'),**a}
    entry.update(final_scope_review_pass=True,final_scope_checks=len(final['checks']))
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A86',next_iteration='AIRCRAFT-A87',current_status=a['status'],next_objective=route(),updated_at=stamp)
    s['aircraft_a86_key_results']=entry;s['validated_artifacts'].update(aircraft_a86_report=rel(REPORT),aircraft_a86_results=rel(OUT/'composite_qualification_review.json'),aircraft_a86_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A86'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A86+AIRCRAFT-A87 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cy)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==205
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,
        'patch_applied':False,'compiled':False,'new_native':0,'physical_impact_qualified':False,'next_iteration':'AIRCRAFT-A87'})
    print(json.dumps({'A86_registered':True,'registry':205,'pending_publication':1}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','register']);globals()[p.parse_args().action]()
