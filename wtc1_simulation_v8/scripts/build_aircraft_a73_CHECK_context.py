"""Approved ninth isolated Engine: retain A71 recipe, then exact A72 CHECK-context diff."""
import build_aircraft_a54_graph as base
import build_aircraft_a71_initial_zero as previous
from pathlib import Path
import json, hashlib, shlex, shutil, subprocess, time, copy

ROOT,read,dump,sha,now,linux = base.ROOT,base.read,base.dump,base.sha,base.now,base.linux
OUT = ROOT/'wtc1_simulation_v8/output/aircraft_a73'
CFG = ROOT/'wtc1_simulation_v8/data/aircraft_a73_predeclaration.json'
CAND = ROOT/'wtc1_simulation_v8/openradioss_runtime/a73_CHECK_context_candidate'
ATT = OUT/'build_attempt_0'
PLAN = ROOT/'wtc1_simulation_v8/data/aircraft_a72_proposal.json'
OBS_PLAN = ROOT/'wtc1_simulation_v8/data/aircraft_a72_observer_plan.json'
AUTH = ROOT/'wtc1_simulation_v8/data/aircraft_a73_authorization.json'


def declare():
    assert not any(p.exists() for p in [OUT,CFG,CAND,AUTH])
    h = base.harness()
    assert h['CurrentIteration']=='AIRCRAFT-A72' and h['RegistryEntries']==191
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==['AIRCRAFT-A72']
    p=read(PLAN); op=read(OBS_PLAN); check=p['patch']
    review=ROOT/'wtc1_simulation_v8/output/aircraft_a72_preparation/independent_scope_review.json'
    observer_review=ROOT/'wtc1_simulation_v8/output/aircraft_a72_preparation/observer_preparation_review.json'
    proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a72_preparation/proposition_contexte_CHECK_explicite.md'
    assert read(review)['pass'] and read(review)['plan_sha256']==sha(PLAN)
    assert read(observer_review)['pass'] and op['main_plan_sha256']==sha(PLAN)
    assert sha(ROOT/op['prepared_observer'])==op['prepared_observer_sha256']
    for f,k in [('current_source','current_sha256'),('proposed_source','proposed_sha256'),('patch','patch_sha256')]:
        assert sha(ROOT/check[f])==check[k]
    auth={'created_utc':now(),'explicit_human_authorization':True,
        'answer':'Oui, appliquer le correctif A72, compiler et exécuter le lot A73',
        'question_item':'request_user_input_async/call_e3f6b6f4ebbd4da5bb9b7775f41c96e9/0',
        'plan':base.rel(PLAN),'plan_sha256':sha(PLAN),'observer_plan_sha256':sha(OBS_PLAN),
        'review_sha256':sha(review),'observer_review_sha256':sha(observer_review),'proposal_sha256':sha(proposal),
        'source_sha256':check['proposed_sha256'],'patch_sha256':check['patch_sha256'],
        'maximum_build_s':3600,'CPU_build':6,'maximum_Engine':6,'maximum_Starter':0,
        'CPU_native':1,'each_native_cap_s':180,'GPU':False,'installation':False,
        'whole_dynamic_extension':False,'prior_budgets_not_reset':True}
    dump(AUTH,auth)
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a71_predeclaration.json')
    assert old['check_zero_residual_patch']['proposed_sha256']==check['current_sha256']
    OUT.mkdir()
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(OUT/'harness_before_build.json',h);dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A73','seed':1102098,'random_draws':0,
        'source_pin':base.PIN,'authorization':auth,
        **{k:copy.deepcopy(old[k]) for k in ['surface_patch','original_scratch_patch','scratch_patch','patch','build','preservation','current_area_patch','check_zero_residual_patch']},
        'CHECK_context_patch':check,'control_contract':p['controls'],'observer_contract':op,
        'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'maximum_Engine':6,'maximum_Starter':0,'CPU_native':1,'GPU':False},
        'source_references':[base.rel(PLAN),base.rel(OBS_PLAN),'wtc1_simulation_v8/output/aircraft_a71/CHECK_call_order_review.json'],
        'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,
        'whole_physical_inputs_and_physical_gates_unchanged':True,
        'CHECK_zero_Newmark_explicit_context_admissibility_CHANGED':True,
        'whole_dynamic_extension':False,'new_installation':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    pins={r['path']:r for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a71/preservation_before_metadata.json')['files']}
    for n in [71,72]:
        d=ROOT/f'wtc1_simulation_v8/output/aircraft_a{n}'
        for row in read(d/'artifact_manifest.json')['files']:pins[row['path']]=row
        for f in [d/'artifact_manifest.json',d/'publication_verification.json']:
            pins[base.rel(f)]={'path':base.rel(f),'bytes':f.stat().st_size,'sha256':sha(f)}
    for f in (ROOT/'wtc1_simulation_v8/openradioss_runtime').glob('*/isolated_exec/engine_linux64_gf_ompi'):
        pins[base.rel(f)]={'path':base.rel(f),'bytes':f.stat().st_size,'sha256':sha(f)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes']
        rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_failed_TT0_policy_preserved':True})
    dump(OUT/'builder_derivation.json',{'created_utc':now(),'source':base.rel(Path(previous.__file__)),
        'source_sha256':sha(Path(previous.__file__)),'same_existing_initial_hour_6_CPU_cached_build':True,
        'changes':'Carry complete exact A71 recipe and its failed TT0 patch, then apply exact newly approved A72 diff before configure/compile.'})
    print(json.dumps({'A73_declared':True,'maximum_build_s':3600,'CPU':6,'new_A72_explicit_consent':True}),flush=True)


def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    c=read(CFG);assert c['authorization']['explicit_human_authorization']
    assert sha(PLAN)==c['authorization']['plan_sha256'] and sha(OBS_PLAN)==c['authorization']['observer_plan_sha256']
    return c


body=previous.body.replace('AIRCRAFT-A71','AIRCRAFT-A73').replace('1102096','1102098')
marker="        shell('05_dependencies'"
assert body.count(marker)==1
insert='''        context=config['CHECK_context_patch']
        context_source=ROOT/context['proposed_source']
        context_patch=ROOT/context['patch']
        assert sha(context_source)==context['proposed_sha256'] and sha(context_patch)==context['patch_sha256']
        shutil.copy2(context_patch,CAND/'explicit_CHECK_context.patch')
        target_context=mount/'source'/context['target']
        shell('04h_exact_A72_CHECK_context',f'test "$(sha256sum {q(target_context)} | cut -d " " -f 1)" = {context["current_sha256"]}\\ncd {q(mount)}/source\\npatch --batch --fuzz=0 -p0 < {q(CAND/"explicit_CHECK_context.patch")}\\ntest "$(sha256sum {q(target_context)} | cut -d " " -f 1)" = {context["proposed_sha256"]}\\ncmp {q(target_context)} {q(context_source)}')
        dump(OUT/'exact_CHECK_context_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,
            'only_new_changed_source':context['target'],'baseline_sha256':context['current_sha256'],
            'patch_sha256':context['patch_sha256'],'applied_source_sha256':context['proposed_sha256'],
            'matches_approved_A72_source_exactly':True,'old_Engines_sources_workspaces_modified':False,
            'native_or_physical_qualified':False})
'''
body=body.replace(marker,insert+marker)
body=body.replace("'exact_A70_R4_CHECK_policy_applied':True,", "'exact_A70_R4_CHECK_policy_applied':True,'exact_A72_CHECK_context_applied':True,")
body=body.replace('Explicit approval of exact A70 R4 initial-zero CHECK classification, retaining complete A67 source recipe.',
    'Explicit approval of exact A72 CHECK-context classification, retaining complete A71 recipe; A71 failed TT0 results remain unchanged.')
exec(compile(body,__file__,'exec'))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['declare','run'])
    globals()[parser.parse_args().action]()
