"""Prepare, never apply, a correction-null predicate on the native condensed free vector."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from prepare_aircraft_a86_null_relative import eligible as old_policy
from pathlib import Path
import json,copy,math,difflib,shutil

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a90';PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a90_preparation'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a90_projected_null_proposal'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a90_preparation.json';PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a90_proposal.json'
REPORT=OUT/'rapport_aircraft_a90.md';PROPOSAL=PREP/'proposition_correction_libre_projetee_A91.md'
HANDOFF=ROOT/'harness/handoffs/WTC1_AIRCRAFT_A90_HANDOFF.md';PROMPT=ROOT/'harness/handoffs/PROMPT_REPRISE_A91_2026-10-15.md'

def route():
    return ('AIRCRAFT-A91 proposée non exécutée : appliquer le correctifA90 de correction exactement nulle '
        'après projection/condensation native, puis compiler un onzième moteur isolé, seulement après accord '
        'distinct. Plafond1h/6CPU, puis au maximum4EngineCPU1/180s, zéroStarter/GPU/installation : '
        'deux régressions, boucleA81 conditionnelle, CHECK entier conditionnel à toutes les qualifications '
        'locales. Aucun impact entier prolongé. Le vecteur libre exact doit être nul ; les non-zéros sous-normaux '
        'et les D/DD non finis restent exclus. Les mouvements imposés finis ne sont plus confondus avec une '
        'correction libre. Toutes les autres gardesA86, tolérances et budgets physiques conservés. '
        'Correctif préparé nonappliqué noncompilé ; A89consommé ne couvre aucune modification. '
        'Meilleur impact entier0,0200001220703125s ; dix secondes physiques puis vidéo3D incomplètes.')

def stage():
    assert not any(p.exists() for p in [OUT,PREP,PRIVATE,CFG,PLAN])
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A89' and h['RegistryEntries']==208
    OUT.mkdir();PREP.mkdir();PRIVATE.mkdir();dump(OUT/'harness_before_preparation.json',h)
    observed=read(ROOT/'wtc1_simulation_v8/output/aircraft_a89/observation_review.json');assert observed['pass_observation'] and observed['raw_ALL_DD_zero_is_false']
    previous=read(ROOT/'wtc1_simulation_v8/data/aircraft_a86_proposal.json');source=ROOT/previous['patch']['proposed_source']
    assert sha(source)==read(ROOT/'wtc1_simulation_v8/output/aircraft_a87/exact_null_relative_patch_application.json')['applied_source_sha256']
    old=source.read_text(encoding='utf8')
    oldblock='''         IF (ALL(F(1:NDDL)==ZERO).AND.
     .       ALL(DD(1:3,1:NUMNOD)==ZERO)) THEN
          CALL PRODUT_UHP(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                    D,DR,U2,W_DDL)
          CALL PRODUT_UHP(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                    DD,DDR,DU2,W_DDL)
          WTC_NULL_REL=(U2==ZERO.AND.DU2==ZERO)
         ENDIF
'''
    newblock='''         IF (ALL(F(1:NDDL)==ZERO).AND.
     .       ALL(ABS(D(1:3,1:NUMNOD))<=HUGE(ONE)).AND.
     .       ALL(ABS(DD(1:3,1:NUMNOD))<=HUGE(ONE))) THEN
          CALL WTC_DD_PROJECTED_ZERO(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                             DD,DDR,WTC_FREE_DD_NULL)
          IF (WTC_FREE_DD_NULL) THEN
           CALL PRODUT_UHP(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                     D,DR,U2,W_DDL)
           CALL PRODUT_UHP(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                     DD,DDR,DU2,W_DDL)
           WTC_NULL_REL=(U2==ZERO.AND.DU2==ZERO)
          ENDIF
         ENDIF
'''
    helper='''
C----Exact zero test in the same free coordinates as PRODUT_UHP.
      SUBROUTINE WTC_DD_PROJECTED_ZERO(NDDL0,NDDL,IDDL,NDOF,IKC,
     .                                 DD,DDR,ISZERO)
#include "implicit_f.inc"
      INTEGER NDDL0,NDDL,IDDL(*),NDOF(*),IKC(*)
      my_real DD(*),DDR(*),TMP_NULL(NDDL0)
      LOGICAL ISZERO
      ISZERO=.FALSE.
      IF (NDDL<=0.OR.NDDL0<NDDL) RETURN
      CALL IMP_SETB(DD,DDR,IDDL,NDOF,TMP_NULL)
      CALL CONDENS_B(NDDL0,IKC,TMP_NULL)
      ISZERO=ALL(TMP_NULL(1:NDDL)==ZERO)
      RETURN
      END
'''
    assert old.count(oldblock)==1 and old.count('      LOGICAL WTC_NULL_REL\n')==1
    assert all(len(l)<=72 for l in (newblock+helper).splitlines())
    new=old.replace('      LOGICAL WTC_NULL_REL\n','      LOGICAL WTC_NULL_REL,WTC_FREE_DD_NULL\n',1).replace(oldblock,newblock,1)+helper
    proposed=PRIVATE/'nl_solv.projected_null.proposed.F';proposed.write_text(new,encoding='utf8',newline='\n')
    patch=PRIVATE/'projected_free_correction.patch';patch.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='engine/source/implicit/nl_solv.F',tofile='engine/source/implicit/nl_solv.F')),encoding='utf8',newline='\n')
    dump(CFG,{'created_utc':now(),'iteration':'AIRCRAFT-A90_PREPARATION','seed':1102115,'random_draws':0,
        'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','base_A87_source':rel(source),'base_A87_source_sha256':sha(source),
        'new_Engine':0,'new_Starter':0,'patch_applied':False,'compiled':False})
    free=[12,13,15,16,18,19,21,22]
    base={'IDYNA':2,'IQSTAT':0,'INSOLV':1,'NITOL':123,'ISPRB':0,'IRIKS':0,'NFXVEL':4,'NINTER':0,'IRODDL':0,
        'NSPMD':1,'NTHREAD':1,'IT':2,'IMCONV':0,'NDDL':8,'ICONT':0,'EIMP':0.,'DE0':1e-20,'R2':0.,'R02':1.,
        'F':[0.]*8,'DD':[0.]*24,'D':[0.]*24,'U2':0.,'DU2':0.}
    for i in [14,17,20,23]:base['DD'][i]=-1.90288107842e-9;base['D'][i]=-1.328447181728e-8
    def model(s):
        if not all(math.isfinite(v) for v in s['DD']+s['D']):return False
        projected=[s['DD'][i] for i in free]
        other=copy.deepcopy(s);other['DD']=[0.]*24
        return old_policy(other) and all(v==0 for v in projected)
    cases=[('observed_second_trial_projected_null',copy.deepcopy(base),True)]
    for index in free:
        for value in [1e-300,-1e-300,1e-10,float('nan'),float('inf')]:
            s=copy.deepcopy(base);s['DD'][index]=value;cases.append((f'reject_free_component_{index}_{len(cases)}',s,False))
    for index in [0,2,11,14,17,20,23]:
        for key in ['D','DD']:
            for value in [float('nan'),float('inf'),-float('inf')]:
                s=copy.deepcopy(base);s[key][index]=value;cases.append((f'reject_nonfinite_{key}_{index}_{len(cases)}',s,False))
    for index in range(8):
        s=copy.deepcopy(base);s['F'][index]=1e-300;cases.append((f'reject_underflowing_F_{index}',s,False))
    for key,value in [('NINTER',1),('NTHREAD',2),('IT',1),('EIMP',1e-300),('DE0',0),('U2',1e-300),('DU2',1e-300),('NITOL',2),('IDYNA',0),('IQSTAT',1),('IRODDL',1),('NSPMD',2),('IMCONV',-1),('NFXVEL',0)]:
        s=copy.deepcopy(base);s[key]=value;cases.append((f'reject_scope_{key}',s,False))
    rows=[]
    for label,s,expected in cases:
        actual=model(s);assert actual==expected,label;rows.append({'case':label,'expected':expected,'actual':actual,'pass':True})
    restored=new[:-len(helper)].replace(newblock,oldblock,1).replace('      LOGICAL WTC_NULL_REL,WTC_FREE_DD_NULL\n','      LOGICAL WTC_NULL_REL\n',1)
    assert restored==old
    product=ROOT/'wtc1_simulation_v8/openradioss_runtime/a84_normalization_audit/produt_v.F'
    prodtext=product.read_text(encoding='utf8');assert 'CALL IMP_SETB(DD  ,DDR   ,IDDL   ,NDOF  ,TMP_W1)' in prodtext and 'CALL CONDENS_B(NDDL0  ,IKC  ,TMP_W1)' in prodtext
    checks={'exact_native_projection_then_condensation_order':True,'projected_vector_exact_zero_not_squared_norm_only':True,
        'all_original_modes_and_nonzero_path_restored_exact':restored==old,
        'full_D_DD_finite_guard_preserves_nonfinite_rejection':True,'underflowing_free_components_rejected':True,
        'all_new_fixed_format_lines_within72':True,'one_existing_file_only_new_helper_in_same_file':True,
        'no_movement_material_mass_dt_tolerance_changes':True,'prototype_pass':True,'patch_not_applied_or_compiled':True}
    dump(PREP/'projected_null_review.json',{'created_utc':now(),'pass':True,'checks':checks,'mathematical_cases':rows,'mathematical_cases_count':len(rows),
        'prototype_projection_scope':'This coupon: eight top XY free coordinates; source candidate uses actual native IMP_SETB and CONDENS_B for arbitrary eligible scene',
        'native_Fortran_behavior_not_yet_qualified':True,'projection_source':rel(product),'projection_source_sha256':sha(product),
        'current_source_sha256':sha(source),'proposed_source_sha256':sha(proposed),'patch_sha256':sha(patch)})
    baseline=ROOT/'wtc1_simulation_v8/data/aircraft_a87_predeclaration.json'
    p={'created_utc':now(),'iteration':'AIRCRAFT-A90_PROPOSAL','seed':1102115,'random_draws':0,
        'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a','patch':{'target':'engine/source/implicit/nl_solv.F','current_source':rel(source),'current_sha256':sha(source),
            'proposed_source':rel(proposed),'proposed_sha256':sha(proposed),'patch':rel(patch),'patch_sha256':sha(patch),'applied':False,'compiled':False},
        'prototype_review':rel(PREP/'projected_null_review.json'),'prototype_review_sha256':sha(PREP/'projected_null_review.json'),
        'baseline_recipe':rel(baseline),'baseline_recipe_sha256':sha(baseline),'baseline_builder':'wtc1_simulation_v8/scripts/build_aircraft_a87_null_relative.py',
        'baseline_builder_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a87_null_relative.py'),
        'future_candidate':'wtc1_simulation_v8/openradioss_runtime/a91_projected_null_candidate','future_Engine_number':11,
        'maximum_build_s':3600,'CPU_build':6,'maximum_Engine':4,'maximum_Starter':0,'CPU_native':1,'each_native_cap_s':180,
        'GPU':False,'installation':False,'whole_dynamic_extension':False,'new_explicit_human_authorization_required':True,
        'cases':previous['cases'],'reference_contract':previous['reference_contract'],'reference_contract_sha256':previous['reference_contract_sha256'],
        'all_prior_recipes_and_exact_A86_patch_carried':True,'nonzero_projected_correction_not_accepted':True,
        'all_physical_thresholds_and_old_failed_gates_preserved':True,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    for case in p['cases']:
        for row in case['inputs']:assert sha(ROOT/row['path'])==row['sha256']
    dump(PLAN,p)
    PROPOSAL.write_text('''# Proposition A91 — tester exactement la correction dans le sous-espace libre

A89 a mesuré au second essai toutes les conditions de portée admissibles, une force libre nulle et des normesU2/DU2 nulles, mais quatre correctionsZ imposées non nulles. La conditionA86 sur toutDD brut exclut ce cas. Le correctif proposé remplace uniquement ce test par un test exact du vecteur libre après les mêmes appels natifsIMP_SETB puisCONDENS_B quePRODUT_UHP. Il ne supprime pas la condition de correction nulle et ne se contente pas de son carré : une composante libre non nulle, même sous-normale, reste exclue.

Le candidat vérifie aussi que tousD etDD bruts restent finis. Une donnéeNaN/Infinity sur une coordonnée imposée ne peut donc pas disparaître du contrôle avec la projection. Toutes les autres gardesA86, le chemin non dégénéré, CRIT_ITE, tolérances, chargements, masse, matériaux et bornes de pas restent conservés. Les deux normes doivent toujours être nulles. L’ancienInfinity de l’itération1 reste visible. Un seul fichier moteur est concerné, avec un petit auxiliaire dans ce même fichier ; aucun nouveau module, fichier de construction ou dépendance.

Diff et source proposés préparés en privé sous licence source, non appliqués et non compilés. Après accord distinct : appliquer le diff exact en reprenant toute la recetteA87, y comprisA86 et les correctifs antérieurs, puis compiler un onzième moteur isoléA91. Plafond1h/sixCPU, sans GPU ni installation ; dix anciens moteurs conservés.

Puis au maximum quatreEngine sur unCPU,180s chacun, zéroStarter : deux régressionsFREE_Ismstr4 etAREA_EVOLUTION_FREE_Y contre les histoires sauvegardées et seuilsA67 inchangés ; boucleA81 compression–ouverture–refermeture originale uniquement si elles passent ; CHECK entier seulement si tous les critères locaux mécaniques, énergétiques et champs passent. Aucun prolongement dynamique entier. Entrées/restarts/horizon conservés. Toute place échouée/expirée est consommée, aucun réessai automatique ni réaffectation de CHECK conditionnel inutilisé.

La boucle doit réellement atteindre0,65ms et fournir ses champs, réactions, rupture/refermeture et contrôle énergétique indépendant. Le seuil0,02*K0+1e−7J reste1e−7J àK0=0 ; il n’est pas remplacé par une fraction du travail de fracture. Une convergence ou une compilation ne vaut pas qualification physique. Les cinqTYPE25 ignorés et107391avertissements restent bloquants.

Le prototype vérifie le casA89 et des cas adverses : chaque correction libre minuscule, chaque force libre minuscule, données non finies sur coordonnées imposées/fixes/libres et modes exclus. La projection Python est limitée au coupon et n’est pas une validation native du codeFortran. Accord explicite distinct requis pour application, compilation et lotA91 : A89 n’autorisait qu’une observation désormais consommée. Dix secondes et vidéo3D incomplètes.
''',encoding='utf8')
    a={'created_utc':now(),'iteration':'AIRCRAFT-A90','status':'completed_static_exact_projected_correction_proposal__unapplied_uncompiled',
        'new_Engine':0,'new_Starter':0,'patch_applied':False,'compiled':False,'mathematical_cases':len(rows),'scope_checks':len(checks),
        'exact_native_projection_reused':True,'full_D_DD_nonfinite_rejection_retained':True,'all_other_A86_guards_and_nonzero_criteria_retained':True,
        'future_Engine_number':11,'future_build_cap_s':3600,'future_CPU_build':6,'future_maximum_Engine':4,'future_maximum_Starter':0,
        'future_CPU_native':1,'future_each_cap_s':180,'GPU_installation_whole_dynamics':False,'new_explicit_consent_received':False,
        'native_patch_behavior_unqualified':True,'all_old_outputs_budgets_and_failed_gates_preserved':True,
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False,'next_iteration':'AIRCRAFT-A91'}
    dump(OUT/'scientific_assessment.json',a);dump(OUT/'composite_qualification_review.json',{'created_utc':now(),'assessment':a,'proposal':rel(PROPOSAL),'whole_qualification':False})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_physical_duration_credit_s':0,'complete':False,'next':route()})
    REPORT.write_text('''# AIRCRAFT-A90 — proposition de correction nulle après projection native

## 1. Faits directement observés ou transcrits

A89 observe les quatreDD imposés non nuls et les normes libres nulles au second essai, cycle2/temps0,00025ms. La première gardeA86 échoue surALLDD brut. Les sources proposées restent distinctes des sources opérationnelles ; zéro Engine/Starter et aucune compilation pendantA90.

## 2. Résultats d’un modèle officiel

Aucun nouveau résultat historique officiel. Le candidat reprend exactement l’ordreIMP_SETB puisCONDENS_B du calcul natif de norme librePRODUT_UHP, mais teste les composantes du vecteur libre plutôt que le seul carré. Le contrôle de sous-débordement est ainsi explicite.

## 3. Affirmations provenant des archives locales

Aucune archive historique ou vidéo source réanalysée/modifiée. Diff et copie logicielle proposés restent privés sous licence source, exclus du manifeste propre public. Les dix anciens moteurs restent conservés.

## 4. Hypothèses propres au modèle

Graine1102115, zéro tirage. Le choix deA86 pour les erreurs relatives dans le sous-espace nul reste conservé, avec toutes ses restrictions ; seul le test de correction nulle devient cohérent avec les coordonnées libres. LesD/DD non finis bruts sont explicitement rejetés même s’ils seraient retirés par la projection. Cela ne calcule pas l’énergie physique ni la rupture. L’ancienInfinity à1 reste conservé.

## 5. Résultats dérivés

Un seul fichier modifié dans la proposition, auxiliaire ajouté dans ce même fichier. Le reste de la sourceA87 est reconstruit exactement en retirant ces changements. Le prototype rejette les non-zéros libres sous-normaux et toutes les données non finies testées, mais accepte le casA89 où seules les commandes imposées corrigentDD. Il n’est pas une exécutionFortran. RecetteA87 et quatre contrôles conditionnels préparés : deux régressions, boucle originale, puisCHECK uniquement si toutes les portes locales passent ; mêmes entrées et mêmes seuils.

## 6. Contradictions et informations manquantes

Correctif non appliqué/non compilé, comportement natif encore inconnu. Une meilleure convergence ne qualifie pas l’énergie, les champs, rupture ou refermeture. Le seuil1e−7J de la boucle et tous échecs antérieurs restent conservés. Nouvel accord explicite requis pour un onzième moteur isolé et son lot ; le seul EngineA89 est consommé et le CHECK conditionnelA87 ne couvre pas cette proposition. Meilleur impact entier0,0200001220703125s ; dix secondes et vidéo3D incomplètes.

'''+route()+'\n',encoding='utf8')
    HANDOFF.write_text('# Reprise AIRCRAFT-A90 → AIRCRAFT-A91\n\nRapport : '+rel(REPORT)+'\nProposition : '+rel(PROPOSAL)+'\nPlan : '+rel(PLAN)+'\n\n'+route()+'\n',encoding='utf8')
    PROMPT.write_text('Reprends WTC1. Lis AGENTS.md, état/cadence puis intégralement '+rel(REPORT)+', '+rel(OUT/'scientific_assessment.json')+', '+rel(PROPOSAL)+', '+rel(PLAN)+' et '+rel(HANDOFF)+'.\nÉtat local prime ; vérifierpublicationA88+A89. Correctifpréparé nonappliqué noncompilé, aucun calcul en cours.\n'+route()+'\nNouvelles courtes en français.\n',encoding='utf8')
    dump(OUT/'harness_after_preparation.json',harness());dump(OUT/'preparation_verification.json',{'created_utc':now(),'pass':True,'prepared_not_registered':True,'plan_sha256':sha(PLAN),'report_sha256':sha(REPORT)})
    print(json.dumps({'A90_prepared':True,'mathematical_cases':len(rows),'patch_applied':False,'compiled':False}),flush=True)

def register():
    assert not (OUT/'artifact_manifest.json').exists();proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a88_a89/final_remote_verification.json')
    assert proof['pass'] and proof['cadence_pending_count']==0
    h=harness();s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert h['RegistryEntries']==208 and s['current_iteration']=='AIRCRAFT-A89' and cy['pending_iterations']==[]
    pv=read(OUT/'preparation_verification.json');assert sha(PLAN)==pv['plan_sha256'] and sha(REPORT)==pv['report_sha256']
    final=read(PREP/'final_scope_review.json');builder=read(PREP/'builder_preparation_review.json')
    assert final['pass'] and builder['pass'] and final['plan_sha256']==builder['plan_sha256']==sha(PLAN)
    assert sha(ROOT/final['reviewer_script'])==final['reviewer_sha256']
    assert sha(ROOT/builder['builder'])==builder['builder_sha256'] and sha(ROOT/builder['generator'])==builder['generator_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_registration_'+Path(n).name))
    dump(OUT/'verified_prior_publication.json',proof)
    for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a89/artifact_manifest.json')['files']:assert sha(ROOT/r['path'])==r['sha256']
    dump(OUT/'preservation_verification.json',{'created_utc':now(),'pass':True,'A89_sealed_files_rehashed':True,'new_native':0})
    files=[p for folder in [OUT,PREP] for p in folder.rglob('*') if p.is_file()]+[CFG,PLAN,Path(__file__),HANDOFF,PROMPT,
        ROOT/final['reviewer_script'],ROOT/builder['builder'],ROOT/builder['generator']]
    dump(OUT/'artifact_manifest.json',{'created_utc':now(),'raw_AGPL_patch_and_proposed_source_excluded':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(files))]})
    a=read(OUT/'scientific_assessment.json');stamp=now();entry={'experiment_id':'WTC1-AIRCRAFT-A90','registered_at':stamp,'configuration':rel(CFG),'report':rel(REPORT),
        'results':rel(OUT/'composite_qualification_review.json'),'handoff':rel(HANDOFF),'artifact_manifest':rel(OUT/'artifact_manifest.json'),'publication_verification':rel(OUT/'publication_verification.json'),**a}
    entry.update(final_scope_review_pass=True,final_scope_checks=len(final['checks']),
        prepared_builder=builder['builder'],builder_scope_checks=len(builder['checks']),own_builder_R0_path_guard_failure_preserved=True)
    with (ROOT/'harness/experiments/registry.jsonl').open('a',encoding='utf8',newline='\n') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    s.update(current_iteration='AIRCRAFT-A90',next_iteration='AIRCRAFT-A91',current_status=a['status'],next_objective=route(),updated_at=stamp);s['aircraft_a90_key_results']=entry
    s['validated_artifacts'].update(aircraft_a90_report=rel(REPORT),aircraft_a90_results=rel(OUT/'composite_qualification_review.json'),aircraft_a90_handoff=rel(HANDOFF))
    cy.update(pending_iterations=['AIRCRAFT-A90'],pending_count=1,updated_at=stamp,next_publication_after='AIRCRAFT-A90+AIRCRAFT-A91 verified')
    for p,v in [(ROOT/'harness/state.json',s),(ROOT/'harness/publication_cycle.json',cy)]:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    h=harness();assert h['RegistryEntries']==209
    dump(OUT/'publication_verification.json',{'created_utc':now(),'pass':True,'integrity_only':True,'harness':h,'patch_applied':False,'compiled':False,'new_native':0,'next_iteration':'AIRCRAFT-A91'})
    print(json.dumps({'A90_registered':True,'registry':209,'pending_publication':1}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','register']);globals()[p.parse_args().action]()
