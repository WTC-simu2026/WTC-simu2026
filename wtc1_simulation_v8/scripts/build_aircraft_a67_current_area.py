"""Authorized seventh isolated Engine: retain A62 and apply exact A66 current-area proposal."""
import build_aircraft_a54_graph as base
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,time,ast

ROOT,read,dump,sha,now,linux=base.ROOT,base.read,base.dump,base.sha,base.now,base.linux
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a67'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a67_predeclaration.json'
CAND=ROOT/'wtc1_simulation_v8/openradioss_runtime/a67_current_area_iteration_candidate'
ATT=OUT/'build_attempt_0'

def declare():
    assert not OUT.exists() and not CFG.exists() and not CAND.exists()
    h=base.harness();assert h['CurrentIteration']=='AIRCRAFT-A66'
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==['AIRCRAFT-A66']
    plan=read(ROOT/'wtc1_simulation_v8/data/aircraft_a66_proposal.json');area=plan['patch']
    auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_authorization.json')
    assert auth['explicit_human_authorization'] and auth['plan_sha256']==sha(ROOT/auth['plan'])
    assert auth['patch_sha256']==area['patch_sha256'] and auth['proposed_source_sha256']==area['proposed_sha256']
    assert auth['maximum_native_runs']==8 and sha(ROOT/auth['proposal'])==auth['proposal_sha256']
    for path,key in [('current_A62_source','current_A62_source_sha256'),('proposed_source','proposed_sha256'),('patch','patch_sha256')]:assert sha(ROOT/area[path])==area[key]
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a62_predeclaration.json');prior=ROOT/'wtc1_simulation_v8/output/aircraft_a66'
    OUT.mkdir()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    dump(OUT/'harness_before_build.json',h);dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A67','seed':1102092,'random_draws':0,'source_pin':base.PIN,'authorization':auth,
        'current_area_patch':area,'future_control_contract':plan['future_A67'],
        **{key:old[key] for key in ['surface_patch','original_scratch_patch','scratch_patch','patch','build','preservation']},
        'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'maximum_native_Engine_runs':8,'CPU_native':1,'GPU':False},
        'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,
        'whole_physical_inputs_and_criteria_unchanged':True,'iteration_matrix_is_exact_Jacobian':False,'new_installation':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    pins={row['path']:row for row in read(prior/'preservation_before_metadata.json')['files']}
    for row in read(prior/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    for p in (ROOT/'wtc1_simulation_v8/openradioss_runtime').glob('*/isolated_exec/engine_linux64_gf_ompi'):
        pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    rows=[]
    for row in pins.values():
        stat=(ROOT/row['path']).stat();assert stat.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':stat.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_manifests_retained':True})
    dump(OUT/'builder_derivation.json',{'created_utc':now(),'source':'wtc1_simulation_v8/scripts/build_aircraft_a62_surface.py',
        'source_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a62_surface.py'),
        'changes':'Carry exact A62 R2 source after original A61 patch, then apply exact approved A66 diff; same initial1h/6CPU/cache build protocol.'})
    print(json.dumps({'A67_declared':True,'explicit_A66_authorization':True,'maximum_build_s':3600,'CPU':6}),flush=True)

def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    c=read(CFG);assert c['authorization']['explicit_human_authorization'];return c

source=(ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a62_surface.py').read_text(encoding='utf8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='run');body=ast.get_source_segment(source,node)
body=body.replace('AIRCRAFT-A62','AIRCRAFT-A67').replace('1102087','1102092')
marker="        shell('05_dependencies'"
assert body.count(marker)==1
insertion='''        area=config['current_area_patch']
        baseline_file=ROOT/area['current_A62_source']
        new_source=ROOT/area['proposed_source']
        new_patch=ROOT/area['patch']
        assert sha(baseline_file)==area['current_A62_source_sha256']
        assert sha(new_source)==area['proposed_sha256'] and sha(new_patch)==area['patch_sha256']
        shutil.copy2(new_patch,CAND/'type43_current_area_Ismstr4.patch')
        shell('04e_exact_A62_R2_baseline',f'test "$(sha256sum {q(target_surface)} | cut -d " " -f 1)" = {surface["proposed_sha256"]}\\ncp {q(baseline_file)} {q(target_surface)}\\ntest "$(sha256sum {q(target_surface)} | cut -d " " -f 1)" = {area["current_A62_source_sha256"]}\\ncmp {q(target_surface)} {q(baseline_file)}')
        shell('04f_exact_A66_current_area',f'cd {q(mount)}/source\\npatch --batch --fuzz=0 -p0 < {q(CAND/"type43_current_area_Ismstr4.patch")}\\ntest "$(sha256sum {q(target_surface)} | cut -d " " -f 1)" = {area["proposed_sha256"]}\\ncmp {q(target_surface)} {q(new_source)}')
        dump(OUT/'exact_current_area_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,
            'only_new_changed_source':area['target'],'baseline_A62_R2_sha256':area['current_A62_source_sha256'],
            'patch_sha256':area['patch_sha256'],'applied_source_sha256':area['proposed_sha256'],
            'matches_explicitly_approved_A66_source_exactly':True,'old_Ismstr1_helper_preserved':True,
            'old_workspaces_or_Engines_modified':False,'compiled_or_native_qualified':False})
'''
body=body.replace(marker,insertion+marker)
body=body.replace("'exact_A61_surface_patch_applied':True,","'exact_A61_surface_patch_applied':True,'exact_A62_R2_interface_carried':True,'exact_A66_current_area_patch_applied':True,")
body=body.replace('Explicit approval of exact A61 surface iteration proposal, retaining A53 graph and A55/A56 memory corrections.','Explicit approval of exact A66 Ismstr4 current-area proposal, retaining A62 R2 and all earlier approved corrections.')
exec(compile(body,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
