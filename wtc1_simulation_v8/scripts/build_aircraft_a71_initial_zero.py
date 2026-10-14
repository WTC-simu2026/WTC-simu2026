"""Authorized eighth isolated Engine: exact A70 R4 CHECK policy, retain the complete A67 source recipe."""
import build_aircraft_a54_graph as base
import build_aircraft_a67_current_area as previous
from pathlib import Path
import json,hashlib,shlex,shutil,subprocess,time,copy

ROOT,read,dump,sha,now,linux=base.ROOT,base.read,base.dump,base.sha,base.now,base.linux
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a71';CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a71_predeclaration.json'
CAND=ROOT/'wtc1_simulation_v8/openradioss_runtime/a71_initial_zero_residual_candidate';ATT=OUT/'build_attempt_0'

def declare():
    assert not any(p.exists() for p in [OUT,CFG,CAND]);h=base.harness();assert h['CurrentIteration']=='AIRCRAFT-A70'
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==['AIRCRAFT-A70']
    planfile=ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal_r4.json';p=read(planfile);auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a71_authorization.json');check=p['patch']
    assert auth['explicit_human_authorization'] and auth['plan_sha256']==sha(planfile) and auth['maximum_Engine']==6 and auth['maximum_Starter']==1
    assert auth['source_sha256']==check['proposed_sha256'] and auth['patch_sha256']==check['patch_sha256']
    review=ROOT/'wtc1_simulation_v8/output/aircraft_a70_preparation_r4/independent_scope_review.json';assert read(review)['pass'] and auth['review_sha256']==sha(review)
    for f,k in [('current_source','current_sha256'),('proposed_source','proposed_sha256'),('patch','patch_sha256')]:assert sha(ROOT/check[f])==check[k]
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_predeclaration.json');OUT.mkdir()
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(OUT/'harness_before_build.json',h);dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A71','seed':1102096,'random_draws':0,'source_pin':base.PIN,'authorization':auth,
        **{k:copy.deepcopy(old[k]) for k in ['surface_patch','original_scratch_patch','scratch_patch','patch','build','preservation','current_area_patch']},
        'check_zero_residual_patch':check,'control_contract':p['controls'],
        'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'maximum_Engine':6,'maximum_Starter':1,'CPU_native':1,'GPU':False},
        'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,
        'whole_physical_inputs_and_physical_gates_unchanged':True,'CHECK_zero_initial_Newmark_admissibility_explicitly_CHANGED':True,
        'whole_dynamic_extension':False,'new_installation':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    pins={r['path']:r for r in read(ROOT/'wtc1_simulation_v8/output/aircraft_a67/preservation_before_metadata.json')['files']}
    for k,manifest in [(67,'artifact_manifest.json'),(68,'artifact_manifest_r2.json'),(69,'artifact_manifest.json'),(70,'artifact_manifest.json')]:
        d=ROOT/f'wtc1_simulation_v8/output/aircraft_a{k}'
        for row in read(d/manifest)['files']:pins[row['path']]=row
        for f in [d/manifest,d/'publication_verification.json']:pins[base.rel(f)]={'path':base.rel(f),'bytes':f.stat().st_size,'sha256':sha(f)}
    for f in (ROOT/'wtc1_simulation_v8/openradioss_runtime').glob('*/isolated_exec/engine_linux64_gf_ompi'):
        pins[base.rel(f)]={'path':base.rel(f),'bytes':f.stat().st_size,'sha256':sha(f)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_manifests_and_failed_attempts_preserved':True})
    dump(OUT/'builder_derivation.json',{'created_utc':now(),'source':base.rel(Path(previous.__file__)),'source_sha256':sha(Path(previous.__file__)),
        'same_existing_initial_hour_6_CPU_cached_build':True,'changes':'Add exact approved A70 R4 imp_solv patch after all A67 exact source checks, before configure/compile.'})
    print(json.dumps({'A71_declared':True,'maximum_build_s':3600,'CPU':6,'new_A70_explicit_consent':True}),flush=True)

def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json') and sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    c=read(CFG);assert c['authorization']['explicit_human_authorization'];return c

body=previous.body.replace('AIRCRAFT-A67','AIRCRAFT-A71').replace('1102092','1102096')
marker="        shell('05_dependencies'";assert body.count(marker)==1
insert='''        check=config['check_zero_residual_patch']
        check_source=ROOT/check['proposed_source']
        check_patch=ROOT/check['patch']
        assert sha(check_source)==check['proposed_sha256'] and sha(check_patch)==check['patch_sha256']
        shutil.copy2(check_patch,CAND/'initial_Newmark_zero_residual.patch')
        target_check=mount/'source'/check['target']
        shell('04g_exact_A70_R4_CHECK_policy',f'test "$(sha256sum {q(target_check)} | cut -d " " -f 1)" = {check["current_sha256"]}\\ncd {q(mount)}/source\\npatch --batch --fuzz=0 -p0 < {q(CAND/"initial_Newmark_zero_residual.patch")}\\ntest "$(sha256sum {q(target_check)} | cut -d " " -f 1)" = {check["proposed_sha256"]}\\ncmp {q(target_check)} {q(check_source)}')
        dump(OUT/'exact_CHECK_policy_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,
            'only_new_changed_source':check['target'],'baseline_sha256':check['current_sha256'],'patch_sha256':check['patch_sha256'],
            'applied_source_sha256':check['proposed_sha256'],'matches_approved_A70_R4_source_exactly':True,
            'old_Engines_sources_workspaces_modified':False,'native_or_physical_qualified':False})
'''
body=body.replace(marker,insert+marker)
body=body.replace("'physics_or_acceptance_criteria_changed':False", "'physical_inputs_unchanged':True,'CHECK_initial_zero_Newmark_admissibility_explicitly_CHANGED':True")
body=body.replace("'exact_A66_current_area_patch_applied':True,","'exact_A66_current_area_patch_applied':True,'exact_A70_R4_CHECK_policy_applied':True,")
body=body.replace('Explicit approval of exact A66 Ismstr4 current-area proposal, retaining A62 R2 and all earlier approved corrections.','Explicit approval of exact A70 R4 initial-zero CHECK classification, retaining complete A67 source recipe.')
exec(compile(body,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
