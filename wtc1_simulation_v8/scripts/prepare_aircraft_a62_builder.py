"""Prepare the sixth Engine builder, guarded by the exact A61 human approval."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import ast,json

def main():
    proposal=read(ROOT/'wtc1_simulation_v8/output/aircraft_a61/surface_patch_proposal_review.json')
    auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a62_authorization.json')
    assert auth['explicit_human_authorization'] and auth['patch_sha256']==proposal['patch_sha256'] and auth['proposed_source_sha256']==proposal['proposed_sha256']
    assert sha(ROOT/auth['proposal'])==auth['proposal_sha256']
    src=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a57_original_scratch.py';dest=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a62_surface.py';assert not dest.exists()
    s=src.read_text(encoding='utf8').replace("output/aircraft_a57'","output/aircraft_a62'").replace("data/aircraft_a57_predeclaration.json'","data/aircraft_a62_predeclaration.json'").replace('a57_original_type43_scratch_candidate','a62_type43_surface_iteration_candidate')
    node=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='declare');old=ast.get_source_segment(s,node)
    declaration='''def declare():
    assert not OUT.exists() and not CFG.exists() and not CAND.exists()
    h=base.harness();assert h['CurrentIteration']=='AIRCRAFT-A61'
    assert read(ROOT/'harness/publication_cycle.json')['pending_iterations']==[]
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a61'
    surface=read(prior/'surface_patch_proposal_review.json')
    auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a62_authorization.json')
    assert auth['explicit_human_authorization'] and auth['patch_sha256']==surface['patch_sha256'] and auth['proposed_source_sha256']==surface['proposed_sha256']
    assert sha(ROOT/auth['proposal'])==auth['proposal_sha256']
    for path,key in [('patch_path','patch_sha256'),('proposed_source_path','proposed_sha256')]:assert sha(ROOT/surface[path])==surface[key]
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a57_predeclaration.json');OUT.mkdir()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    dump(OUT/'harness_before_build.json',h);dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A62','seed':1102087,'random_draws':0,'source_pin':base.PIN,'authorization':auth,'surface_patch':surface,'original_scratch_patch':old['original_scratch_patch'],'scratch_patch':old['scratch_patch'],'patch':old['patch'],'build':old['build'],'preservation':old['preservation'],'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'maximum_native_Engine_runs':12,'CPU_native':1,'GPU':False},'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'physical_inputs_and_criteria_unchanged':True,'surface_iteration_is_exact_Jacobian':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    pins={row['path']:row for row in read(prior/'preservation_before_metadata.json')['files']}
    for row in read(prior/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    for p in (ROOT/'wtc1_simulation_v8/openradioss_runtime').glob('*/isolated_exec/engine_linux64_gf_ompi'):
        pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_SHA256_manifests_retained':True})
    print(json.dumps({'A62_declared':True,'exact_surface_human_authorization':True,'maximum_build_s':3600,'CPU':6}),flush=True)
'''
    s=s.replace(old,declaration).replace("'iteration': 'AIRCRAFT-A57'","'iteration': 'AIRCRAFT-A62'").replace("'seed': 1102082","'seed': 1102087")
    s=s.replace('Explicit approval of exact A56 original scratch proposal, with A53 and A55 patches retained.','Explicit approval of exact A61 surface iteration proposal, retaining A53 graph and A55/A56 memory corrections.')
    insert='''        surface=config['surface_patch']
        target_surface=mount/'source'/surface['target']
        surface_file=ROOT/surface['patch_path']
        surface_proposed=ROOT/surface['proposed_source_path']
        assert sha(surface_file)==surface['patch_sha256'] and sha(surface_proposed)==surface['proposed_sha256']
        shutil.copy2(surface_file,CAND/'type43_surface_elastic_iteration.patch')
        shell('04d_exact_surface_patch',f'test "$(sha256sum {q(target_surface)} | cut -d " " -f 1)" = {surface["source_sha256"]}\\ncd {q(mount)}/source\\npatch --batch --fuzz=0 -p1 < {q(CAND/"type43_surface_elastic_iteration.patch")}\\ntest "$(sha256sum {q(target_surface)} | cut -d " " -f 1)" = {surface["proposed_sha256"]}\\ncmp {q(target_surface)} {q(surface_proposed)}')
        dump(OUT/'exact_surface_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,'only_new_changed_file':surface['target'],'patch_sha256':surface['patch_sha256'],'applied_source_sha256':surface['proposed_sha256'],'matches_approved_A61_source_exactly':True,'native_or_physical_qualified':False})
'''
    marker="        shell('05_dependencies'";assert s.count(marker)==1;s=s.replace(marker,insert+marker)
    s=s.replace("'exact_A56_original_scratch_patch_applied':True,'native_or_physical_qualification':False","'exact_A56_original_scratch_patch_applied':True,'exact_A61_surface_patch_applied':True,'native_or_physical_qualification':False")
    ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n')
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a62_builder_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest),'authorization':'Exact approved A61 surface proposal with prior three approved patches','new_source_difference':proposal['target'],'cap_s':3600,'CPU':6,'GPU':False,'installation':False,'old_sources_scripts_binaries_preserved':True})
    print('A62 exact approved builder ready.',flush=True)

if __name__=='__main__':main()
