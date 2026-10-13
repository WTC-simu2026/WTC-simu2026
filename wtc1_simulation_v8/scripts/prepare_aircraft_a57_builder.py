"""Prepare the approved fifth Engine with exactly the original SMSTR allocation fix."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import ast,json

def main():
    src=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a56_scratch.py'
    dest=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a57_original_scratch.py'
    assert not dest.exists();s=src.read_text(encoding='utf8')
    s=s.replace("output/aircraft_a56'","output/aircraft_a57'").replace("data/aircraft_a56_predeclaration.json'","data/aircraft_a57_predeclaration.json'").replace('a56_type43_scratch_candidate','a57_original_type43_scratch_candidate')
    tree=ast.parse(s);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='declare');old=ast.get_source_segment(s,node)
    new='''def declare():
    assert not OUT.exists() and not CFG.exists() and not CAND.exists()
    h=base.harness();assert h['CurrentIteration']=='AIRCRAFT-A56'
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a56'
    original=read(prior/'original_scratch_patch_proposal_review.json')
    auth=read(ROOT/'wtc1_simulation_v8/data/aircraft_a57_authorization.json')
    assert auth['explicit_human_authorization'] and auth['patch_sha256']==original['patch_sha256']
    assert sha(ROOT/auth['proposal'])==auth['proposal_sha256']
    for key,expected in [('patch_path','patch_sha256'),('proposed_source_path','proposed_sha256')]:assert sha(ROOT/original[key])==original[expected]
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a56_predeclaration.json');OUT.mkdir()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    dump(OUT/'harness_before_build.json',h);dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A57','seed':1102082,'random_draws':0,'source_pin':base.PIN,'authorization':auth,'original_scratch_patch':original,'scratch_patch':old['scratch_patch'],'patch':old['patch'],'build':old['build'],'preservation':old['preservation'],'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'CPU_native':1,'GPU':False},'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False,'original_restart_widths_read_counts_offsets_unchanged':True,'physical_inputs_and_criteria_unchanged':True,'original_A55_authorization':read(prior/'software_authorization.json')}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    pins={row['path']:row for row in read(prior/'preservation_before_metadata.json')['files']}
    for row in read(prior/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [prior/'artifact_manifest.json',prior/'publication_verification.json',ROOT/'harness/handoffs/PROMPT_REPRISE_A57_2026-10-13.md']:pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_SHA256_manifests_retained':True})
    print(json.dumps({'A57_declared':True,'explicit_original_scratch_authorization':True}),flush=True)
'''
    s=s.replace(old,new).replace("'iteration': 'AIRCRAFT-A56'","'iteration': 'AIRCRAFT-A57'").replace("'seed': 1102081","'seed': 1102082")
    s=s.replace('Explicit approval of exact A55 scratch proposal plus retained A53 graph patch.','Explicit approval of exact A56 original scratch proposal, with A53 and A55 patches retained.')
    insert='''        original=config['original_scratch_patch']
        target_original=mount/'source'/original['target']
        original_file=ROOT/original['patch_path']
        original_proposed=ROOT/original['proposed_source_path']
        assert sha(original_file)==original['patch_sha256'] and sha(original_proposed)==original['proposed_sha256']
        shutil.copy2(original_file,CAND/'type43_original_smstr.patch')
        shell('04c_exact_original_scratch_patch',f'test "$(sha256sum {q(target_original)} | cut -d " " -f 1)" = {original["source_sha256"]}\\ncd {q(mount)}/source\\npatch --batch --fuzz=0 -p1 < {q(CAND/"type43_original_smstr.patch")}\\ntest "$(sha256sum {q(target_original)} | cut -d " " -f 1)" = {original["proposed_sha256"]}\\ncmp {q(target_original)} {q(original_proposed)}')
        dump(OUT/'exact_original_scratch_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,'only_new_changed_file':original['target'],'patch_sha256':original['patch_sha256'],'applied_source_sha256':original['proposed_sha256'],'restart_read_counts_offsets_and_widths_unchanged':True,'native_or_physical_qualified':False})
'''
    marker="        shell('05_dependencies'";assert s.count(marker)==1;s=s.replace(marker,insert+marker)
    s=s.replace("'exact_A55_scratch_patch_applied':True,'native_or_physical_qualification':False", "'exact_A55_scratch_patch_applied':True,'exact_A56_original_scratch_patch_applied':True,'native_or_physical_qualification':False")
    ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n')
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a57_builder_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest),'authorization':'Exact approved original allocation patch and retained prior approved patches','new_source_difference':'allocbuf_auto.F only','old_scripts_and_binaries_unchanged':True,'cap_s':3600,'CPU':6,'GPU':False,'installation':False})
    print('A57 builder prepared.',flush=True)

if __name__=='__main__':main()
