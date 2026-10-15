"""Prepared eleventh isolated Engine builder; fresh A86/A87 source/build consent required."""
import build_aircraft_a54_graph as base
import build_aircraft_a87_null_relative as previous
from pathlib import Path
import json,hashlib,shlex,shutil,subprocess,time,copy

ROOT,read,dump,sha,now,linux=base.ROOT,base.read,base.dump,base.sha,base.now,base.linux
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a91'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a91_predeclaration.json'
CAND=ROOT/'wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate'
ATT=OUT/'build_attempt_0'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a90_proposal.json'
AUTH=ROOT/'wtc1_simulation_v8/data/aircraft_a91_authorization.json'
REVIEW=ROOT/'wtc1_simulation_v8/output/aircraft_a90_preparation/builder_preparation_review.json'


def prerequisites():
    assert AUTH.exists(),'Fresh explicit consent for A86 source patch/A87 build and controls is missing'
    p=read(PLAN);a=read(AUTH);r=read(REVIEW)
    assert a['explicit_human_authorization'] and a['plan_sha256']==sha(PLAN)
    assert a['patch_sha256']==p['patch']['patch_sha256'] and a['proposed_source_sha256']==p['patch']['proposed_sha256']
    assert a['maximum_build_s']==p['maximum_build_s']==3600 and a['CPU_build']==p['CPU_build']==6
    assert a['maximum_Engine']==p['maximum_Engine']==4 and a['maximum_Starter']==p['maximum_Starter']==0
    assert a['CPU_native']==p['CPU_native']==1 and a['each_native_cap_s']==p['each_native_cap_s']==180
    assert r['pass'] and r['plan_sha256']==sha(PLAN) and r['builder_sha256']==sha(Path(__file__))
    assert sha(ROOT/a['proposal'])==a['proposal_sha256']
    assert not any(p[k] for k in ['GPU','installation','whole_dynamic_extension'])
    for key,digest in [('current_source','current_sha256'),('proposed_source','proposed_sha256'),('patch','patch_sha256')]:assert sha(ROOT/p['patch'][key])==p['patch'][digest]
    assert read(ROOT/p['prototype_review'])['pass'] and sha(ROOT/p['prototype_review'])==p['prototype_review_sha256']
    assert sha(ROOT/p['baseline_recipe'])==p['baseline_recipe_sha256'] and sha(ROOT/p['baseline_builder'])==p['baseline_builder_sha256']
    proof=read(ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a88_a89/final_remote_verification.json')
    assert proof['pass'] and proof['scientific_ci']['conclusion']==proof['final_ci']['conclusion']=='success'
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A90'
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==['AIRCRAFT-A90']
    for case in p['cases']:
        for row in case['inputs']:assert sha(ROOT/row['path'])==row['sha256']
    return p,a


def declare():
    assert not any(p.exists() for p in [OUT,CFG,CAND])
    p,a=prerequisites();h=base.harness();assert h['RegistryEntries']==209
    old=read(ROOT/p['baseline_recipe']);OUT.mkdir()
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    dump(OUT/'harness_before_build.json',h);dump(OUT/'software_authorization.json',a)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A91','seed':1102116,'random_draws':0,'source_pin':base.PIN,'authorization':a,
        **{k:copy.deepcopy(old[k]) for k in ['surface_patch','original_scratch_patch','scratch_patch','patch','build','preservation','current_area_patch','check_zero_residual_patch','CHECK_context_patch','null_relative_patch']},
        'projected_null_patch':p['patch'],'control_contract':p['cases'],
        'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'maximum_Engine':4,'maximum_Starter':0,'CPU_native':1,'GPU':False},
        'relative_null_criterion_definition_changed':True,'nondegenerate_criteria_and_all_tolerances_preserved':True,
        'source_references':[base.rel(PLAN),'wtc1_simulation_v8/output/aircraft_a85/observation_review.json'],
        'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,
        'whole_dynamic_extension':False,'new_installation':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    pins={}
    for n in [89,90]:
        folder=ROOT/f'wtc1_simulation_v8/output/aircraft_a{n}'
        for row in read(folder/'artifact_manifest.json')['files']:pins[row['path']]=row
    for b in (ROOT/'wtc1_simulation_v8/openradioss_runtime').glob('*/isolated_exec/engine_linux64_gf_ompi'):
        pins[base.rel(b)]={'path':base.rel(b),'bytes':b.stat().st_size,'sha256':sha(b)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'all_prior_Engines_preserved':True})
    dump(OUT/'builder_derivation.json',{'created_utc':now(),'source':base.rel(Path(previous.__file__)),'source_sha256':sha(Path(previous.__file__)),
        'complete_prior_A73_recipe_carried':True,'new_source_only':'engine/source/implicit/nl_solv.F'})
    print(json.dumps({'A87_declared':True,'maximum_build_s':3600,'CPU_build':6,'maximum_Engine':4,'Starter':0}),flush=True)


def guard():
    prerequisites();assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/n)==sha(OUT/('before_'+Path(n).name))
    return read(CFG)



body=previous.body.replace('AIRCRAFT-A87','AIRCRAFT-A91').replace('1102110','1102116')
marker="        shell('05_dependencies'"
assert body.count(marker)==1
insert='''
        projected=config['projected_null_patch']
        projection_source=ROOT/projected['proposed_source']
        projection_patch=ROOT/projected['patch']
        assert sha(projection_source)==projected['proposed_sha256'] and sha(projection_patch)==projected['patch_sha256']
        shutil.copy2(projection_patch,CAND/'exact_projected_null.patch')
        target_projection=mount/'source'/projected['target']
        shell('04j_exact_A90_projected_null',f'test "$(sha256sum {q(target_projection)} | cut -d " " -f 1)" = {projected["current_sha256"]}\\ncd {q(mount)}/source\\npatch --batch --fuzz=0 -p0 < {q(CAND/"exact_projected_null.patch")}\\ntest "$(sha256sum {q(target_projection)} | cut -d " " -f 1)" = {projected["proposed_sha256"]}\\ncmp {q(target_projection)} {q(projection_source)}')
        dump(OUT/'exact_projected_null_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,
            'only_new_changed_source':projected['target'],'baseline_A87_sha256':projected['current_sha256'],
            'patch_sha256':projected['patch_sha256'],'applied_source_sha256':projected['proposed_sha256'],
            'matches_approved_A90_source_exactly':True,'old_Engines_or_sources_modified':False,
            'native_or_physical_qualified':False})
'''
body=body.replace(marker,insert+marker)
body=body.replace("'exact_A86_null_relative_applied':True,","'exact_A86_null_relative_applied':True,'exact_A90_projected_null_applied':True,")
body=body.replace('Explicit approval of exact A86 null-relative criterion definition, retaining complete A73 recipe and all prior failed results.',
    'Explicit approval of exact A90 projected-null correction, retaining complete A87 recipe and all prior failed results.')
exec(compile(body,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
