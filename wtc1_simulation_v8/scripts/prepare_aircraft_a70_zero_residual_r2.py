"""Prepare exact CHECK-only Newmark initial-zero-residual policy change; do not apply or compile."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import difflib,re,json,hashlib

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a70_preparation_r2'
PRIVATE=ROOT/'wtc1_simulation_v8/openradioss_runtime/a70_initial_zero_residual_proposal_r2'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal.json'

def main():
    assert not any(p.exists() for p in [PREP,PRIVATE,PLAN]);assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A69'
    evidence=read(ROOT/'wtc1_simulation_v8/output/aircraft_a69/independent_observation_review.json')
    assert evidence['complete_cases']==2 and all(r.get('native_R2')==0 for r in evidence['cases'] if r['observation_pass'])
    PREP.mkdir();PRIVATE.mkdir();base=ROOT/'wtc1_simulation_v8/openradioss_runtime/a68_check_semantics_audit/imp_solv.F';original=base.read_text(encoding='utf8')
    start=original.index('      SUBROUTINE IMP_CHKM(');end=original.index('\n      END\n',start)+len('\n      END\n');body=original[start:end]
    old='''        IF (R2>ZERO.AND.R2<EP30) THEN
        ELSEIF(IQSTAT>0) THEN'''
    new='''        IF (R2>ZERO.AND.R2<EP30) THEN
        ELSEIF(IDYNA==2.AND.IQSTAT==0.AND.TIME==ZERO.AND.
     .         R2==ZERO) THEN
          WRITE(IOUT,*)' ** INITIAL DYNAMIC RESIDUAL IS ZERO **'
        ELSEIF(IQSTAT>0) THEN'''
    assert body.count(old)==1 and '#include "com04_c.inc"' in body
    changed=body.replace(old,new);proposed=original[:start]+changed+original[end:]
    assert proposed.replace(new,old,1)==original
    dest=PRIVATE/'imp_solv.proposed.F';dest.write_text(proposed,encoding='utf8',newline='\n')
    diff=PRIVATE/'initial_Newmark_zero_residual.patch';diff.write_text(''.join(difflib.unified_diff(original.splitlines(True),proposed.splitlines(True),
        fromfile='engine/source/implicit/imp_solv.F',tofile='engine/source/implicit/imp_solv.F')),encoding='utf8',newline='\n')
    added=[s[1:] for s in diff.read_text(encoding='utf8').splitlines() if s.startswith('+') and not s.startswith('+++')]
    assert len(added)==3 and all(len(s)<=72 for s in added)
    local=ROOT/'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4';name=read(local/'generation.json')['name'];rst=local/(name+'_0000_0001.rst')
    card=local/(name+'_0001.rad');dynamic=card.read_text(encoding='utf8');check=dynamic.replace('/RUN/','/IMPL/CHECK\n/RUN/',1)
    static=re.sub(r'(?m)^/IMPL/DYNA/2\n[^\n]*\n','',check);assert '/IMPL/DYNA' not in static
    freecheck=PREP/'FREE_INITIAL_ZERO_CHECK';freecheck.mkdir();fc=freecheck/card.name;fc.write_text(check,encoding='utf8',newline='\n')
    staticcheck=PREP/'STATIC_INITIAL_ZERO_CHECK';staticcheck.mkdir();sc=staticcheck/card.name;sc.write_text(static,encoding='utf8',newline='\n')
    loaded=PREP/'STATIC_POSITIVE_LOAD_CHECK';loaded.mkdir();loadedname='A71_STATIC_POSITIVE_LOAD_CHECK';starter=local/(name+'_0000.rad')
    s=starter.read_text(encoding='utf8').replace(name,loadedname)
    s=re.sub(r'(?ms)^/INIVEL/TRA/500\n.*?(?=^/)', '',s)
    # Documented concentrated force on each of the four upper nodes, positive-control coupon only.
    line=f"{701:10d}{'Y':>10}{0:10d}{0:10d}{2:10d}{1:10d}{1:20.12g}{1:20.12g}"
    additions='/FUNCT/701\nCONSTANT_POSITIVE_CONTROL_ONE_NEWTON\n'+f'{0:20.12g}{1:20.12g}\n{1:20.12g}{1:20.12g}\n'+'/CLOAD/701\nONE_NEWTON_PER_FREE_TOP_NODE\n'+line+'\n'
    assert s.count('/END')==1;s=s.replace('/END',additions+'/END')
    loadedstarter=loaded/(loadedname+'_0000.rad');loadedstarter.write_text(s,encoding='utf8',newline='\n')
    loadedcard=loaded/(loadedname+'_0001.rad');loadedcard.write_text(static.replace(name,loadedname),encoding='utf8',newline='\n')
    parsed=sections(loadedstarter);assert len(parsed['/NODE'])==8 and parsed['/GRNOD/NODE/2'][1].split()==['5','6','7','8']
    assert not any(k.startswith('/INIVEL') for k in parsed) and int(parsed['/CLOAD/701'][1][40:50])==2
    assert all(parsed[k]==v for k,v in sections(starter).items() if k not in ['/BEGIN','/INIVEL/TRA/500','/END'])
    file=lambda p:{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    cases=[{'case':'FREE_INITIAL_ZERO_CHECK','name':name,'inputs':[file(rst),file(fc)],'new_Starter':False,'expected':'zero residual INFO, no loading error; observation R2=0'},
        {'case':'STATIC_INITIAL_ZERO_CHECK','name':name,'inputs':[file(rst),file(sc)],'new_Starter':False,'expected':'R2=0 still loading ERROR in static CHECK; intentional rejection preserved'},
        {'case':'STATIC_POSITIVE_LOAD_CHECK','name':loadedname,'inputs':[file(loadedstarter),file(loadedcard)],'new_Starter':True,
            'force_per_node_N':1,'loaded_nodes':[5,6,7,8],'total_control_force_N':4,'expected':'R2 positive finite; no loading error; no residual-zero INFO'},
        {'case':'FREE_DYNAMIC_REGRESSION','name':name,'inputs':[file(rst),file(card)],'new_Starter':False,
            'expected':'1 ms native all-step free conservation/reference with unchanged A67 tolerances; no CHECK, no whole duration credit'}]
    for c in read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json')['whole_CHECK_cases']:
        cases.append({'case':c['id'],'name':c['name'],'inputs':c['files'],'new_Starter':False,'whole_cards_and_initial_state_unchanged':True,
            'expected':'observe zero/positive R2 classification in new binary; keep all warnings and five TYPE25 blocking, whole qualification remains false'})
    plan={'created_utc':now(),'iteration':'AIRCRAFT-A70_PROPOSAL','seed':1102095,'random_draws':0,'source_pin':'3d75ff13d1946f6d28a43920eac4fa2aae41b27a',
        'source_archive_sha256':'d64b773e899c174f5d59aadc4d2b73a101a083581e611d67215aaa50037cf9f8',
        'patch':{'target':'engine/source/implicit/imp_solv.F','current_source':rel(base),'current_sha256':sha(base),'proposed_source':rel(dest),'proposed_sha256':sha(dest),
            'patch':rel(diff),'patch_sha256':sha(diff),'only_routine_changed':'IMP_CHKM','added_fixed_form_lines':3,
            'admissibility_change':'Exactly R2=0 at TIME=0 with IDYNA=2 and IQSTAT=0 gets explicit diagnostic and no loading-error increment; all other paths identical.',
            'old_loading_failed_criteria_preserved_in_prior_outputs':True,'dynamics_force_material_stiffness_mass_inertia_unchanged':True,
            'preconditioner_connection_warnings_and_TYPE25_checks_unchanged':True,'applied':False,'compiled':False},
        'build':{'future_iteration':'AIRCRAFT-A71','future_candidate':'wtc1_simulation_v8/openradioss_runtime/a71_initial_zero_residual_candidate','Engine_number':8,
            'retain_all_A67_authorized_patches':True,'maximum_s':3600,'CPU_threads':6,'GPU':False,'installation':False,
            'reuse_cached_source_dependencies_and_toolchain':True,'estimate_minutes':[5,15],'estimate_basis':'A67 first compilation 291.077 seconds; host load and preparation uncertain.'},
        'controls':{'maximum_Engine':6,'maximum_Starter':1,'CPU_threads':1,'each_cap_s':180,'GPU':False,'whole_dynamic_extension':False,'cases':cases,
            'acceptance':read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json')['acceptance'],
            'mechanical_qualification_not_inferred_from_CHECK_INFO_or_source_prototype':True,'five_TYPE25_preserved_blocking':True,
            'native_READ_observer':'wtc1_simulation_v8/scripts/observe_aircraft_a69_check_r1_linux.py','native_READ_observer_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a69_check_r1_linux.py'),
            'new_binary_symbols_must_be_resolved_and_ABI_guarded':True},
        'documentation_sources':[{'url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/cload_starter_r.htm','claim':'CLOAD force is applied individually to each node; Dir right-justified, group mandatory.'},
            {'url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/funct_starter_r.htm','claim':'Time function supplies the constant ordinate for the positive-load coupon.'}],
        'new_explicit_human_authorization_required':True,'old_A69_controls_remaining':0,'whole_force_mass_material_or_inertia_budgets_changed':False,
        'no_force_added_to_whole_models':True,'RKE_added':False,'whole_integration_ready':False,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(PLAN,plan)
    proposal=PREP/'proposition_controle_residu_initial_nul.md'
    proposal.write_text('''# AIRCRAFT-A70 — proposition exacte, non appliquée/non compilée

A69 mesure R2=0 et LB entièrement nul dans la scène appariée et dans un témoin libre dont la dynamique A67 est qualifiée. Le CHECK rejette le témoin à cause du résidu nul. Une dynamique à vitesse initiale et force/accélération initiales nulles est possible ; ajouter une force artificielle dans la scène entière serait incorrect.

Le correctif proposé ajoute trois lignes dans la seule routine IMP_CHKM. Uniquement pour /IMPL/DYNA/2, sans quasi-statique, au temps initial zéro et avec R2 exactement nul, le CHECK écrit « INITIAL DYNAMIC RESIDUAL IS ZERO » au lieu d’incrémenter l’erreur de chargement. Les refus pour R2 non fini/hors plage, zéro statique, autre méthode ou temps non nul restent identiques. Ce changement d’admissibilité numérique est explicite ; tous les anciens CHECK échoués sont conservés. Aucune force, matrice, histoire de matériau, masse, inertie ou RKE modifiée. Les 107391 avertissements et cinq TYPE25 restent présents et bloquants.

Source et différence exactes préparées en copie privée AGPL, hors publication MIT. Plan avec empreintes : wtc1_simulation_v8/data/aircraft_a70_proposal.json. Aucun patch appliqué, aucun binaire compilé. Nouveau huitième moteur isolé A71 proposé : conserver toutes les corrections A67, compilation plafond une heure/six CPU, sans GPU ni installation ; estimation 5–15 minutes d’après A67, avec incertitude de charge.

Puis maximum six Engine et un Starter, un CPU, 180 s chacun : CHECK dynamique libre à résidu nul ; CHECK statique à résidu nul qui doit rester refusé ; témoin statique chargé positif ; régression de dynamique libre jusqu’à 1 ms sur le nouveau binaire ; deux CHECK entiers sans cartes modifiées. Le témoin positif applique 1 N à chacun des quatre nœuds supérieurs, uniquement dans ce coupon de contrôle, aucun chargement dans la scène entière. Les sorties, bilans et seuils A67 sont conservés ; nouvelles observations R2 et diagnostics complets. Aucun impact entier prolongé.

Ce correctif ne valide pas les contacts ou l’impact entier. Les cinq contacts ignorés demandent encore une variante déclarée, une équivalence mécanique contrôlée et des bilans physiques. Objectif dix secondes puis vidéo 3D incomplet ; meilleur impact entier 0,0200001220703125 s. Un accord humain distinct est requis pour cette nouvelle modification et compilation, conformément à AGENTS.md ; l’accord A69 couvrait uniquement trois observations avec moteur inchangé.

Le format du témoin chargé est vérifié auprès de la [documentation officielle CLOAD](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/cload_starter_r.htm) et de [FUNCT](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/funct_starter_r.htm). Son parsing natif reste à contrôler dans le futur Starter borné ; aucune qualification native présumée.
''',encoding='utf8')
    dump(PREP/'exact_patch_scope_review.json',{'created_utc':now(),'pass':True,'original_sha256':sha(base),'proposed_sha256':sha(dest),'patch_sha256':sha(diff),
        'removing_only_three_added_lines_recovers_exact_original':True,'all_other_routines_and_existing_checks_byte_preserved':True,
        'added_lines_within_72_columns':True,'global_TIME_already_declared_by_existing_com04_include':True,'native_checks_not_executed':True,'new_software_not_applied_or_compiled':True})
    dump(PREP/'prepared_inputs_review.json',{'created_utc':now(),'pass':True,'positive_load_coupon_nodes':8,'unchanged_mechanical_cards_except_velocity_removed_in_static_coupon':True,
        'force_per_top_node_N':1,'total_N':4,'native_Starter_not_run':True,'whole_models_no_added_force':True,'all_native_cases':6,'maximum_Starter':1,'max_CPU_native':1,
        'no_new_whole_duration_credit':True,'native_R1_observer_source_unchanged':True})
    dump(PREP/'preparation_review.json',{'created_utc':now(),'pass':True,'proposal':rel(proposal),'plan_sha256':sha(PLAN),'new_native':0,'source_applied':False,'compiled':False})
    print(json.dumps({'A70_prepared':True,'added_source_lines':3,'maximum_future_Engine':6,'maximum_future_Starter':1,'applied':False,'compiled':False}),flush=True)

if __name__=='__main__':main()
