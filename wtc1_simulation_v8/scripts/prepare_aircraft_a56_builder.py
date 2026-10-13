"""Reuse the verified bounded build procedure for the separately approved scratch fix."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import ast,json

def main():
    src=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a54_graph_r1.py'
    dest=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a56_scratch.py'
    assert not dest.exists();s=src.read_text();audit=[]
    def rep(a,b):
        nonlocal s
        n=s.count(a);assert n>0,a;s=s.replace(a,b);audit.append({'old':a,'new':b,'count':n})
    rep('ROOT, OUT, read, dump, sha, now, linux = base.ROOT, base.OUT, base.read, base.dump, base.sha, base.now, base.linux',
        "ROOT, read, dump, sha, now, linux = base.ROOT, base.read, base.dump, base.sha, base.now, base.linux\nOUT=ROOT/'wtc1_simulation_v8/output/aircraft_a56'\nCFG=ROOT/'wtc1_simulation_v8/data/aircraft_a56_predeclaration.json'")
    rep("a54_type2_graph_candidate_r1","a56_type43_scratch_candidate")
    rep("build_attempt_r1","build_attempt_0")
    rep('config = base.guard()','config = guard()')
    rep("    assert read(OUT/'build_failure.json')['error'] == '04_exact_patch'\n",'')
    rep("    deadline = read(OUT/'build_clock.json')['deadline_epoch']","    started=time.time();deadline=started+3600\n    dump(OUT/'build_clock.json',{'started_epoch':started,'deadline_epoch':deadline,'limit_s':3600})")
    rep("'iteration': 'AIRCRAFT-A54'","'iteration': 'AIRCRAFT-A56'")
    rep("'R1'","'R0'")
    rep("'seed': 1102079","'seed': 1102081")
    rep("'authorization': 'Same approved exact A53 file; no new code change.'","'authorization': 'Explicit approval of exact A55 scratch proposal plus retained A53 graph patch.'")
    rep("'previous_attempt_preserved': True, 'previous_failure': 'GNU patch strips CRLF; exact raw hash guard stopped before compilation.'","'previous_A54_attempts_preserved': True, 'graph_EOL_procedure_reused': True")
    marker="        shell('05_dependencies'"
    assert s.count(marker)==1
    insert='''        scratch=config['scratch_patch']
        target_scratch=mount/'source'/scratch['target']
        scratch_file=ROOT/scratch['patch_path']
        scratch_proposed=ROOT/scratch['proposed_source_path']
        assert sha(scratch_file)==scratch['patch_sha256']
        assert sha(scratch_proposed)==scratch['proposed_sha256']
        shutil.copy2(scratch_file,CAND/'type43_smstr_scratch.patch')
        shell('04b_exact_scratch_patch',f'test "$(sha256sum {q(target_scratch)} | cut -d " " -f 1)" = {scratch["source_sha256"]}\\ncd {q(mount)}/source\\npatch --batch --fuzz=0 -p1 < {q(CAND/"type43_smstr_scratch.patch")}\\ntest "$(sha256sum {q(target_scratch)} | cut -d " " -f 1)" = {scratch["proposed_sha256"]}\\ncmp {q(target_scratch)} {q(scratch_proposed)}')
        dump(OUT/'exact_scratch_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,'only_new_changed_file':scratch['target'],'patch_sha256':scratch['patch_sha256'],'applied_source_sha256':scratch['proposed_sha256'],'source_and_restart_widths_unchanged':True,'native_or_physical_qualified':False})
'''
    s=s.replace(marker,insert+marker)
    rep("'exact_A53_graph_patch_applied':True,'native_or_physical_qualification':False,","'exact_A53_graph_patch_applied':True,'exact_A55_scratch_patch_applied':True,'native_or_physical_qualification':False,")
    rep("'initial_EOL_guard_failure_preserved':True","'prior_A54_EOL_guard_failure_preserved':True")
    rep("if __name__=='__main__':run()", "if __name__=='__main__':\n    import argparse\n    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()")
    extra='''
def declare():
    assert not OUT.exists() and not CFG.exists() and not CAND.exists()
    h=base.harness();assert h['CurrentIteration']=='AIRCRAFT-A55'
    a55=ROOT/'wtc1_simulation_v8/output/aircraft_a55'
    auth=read(a55/'new_patch_authorization.json');scratch=read(a55/'smstr_patch_proposal_review.json')
    assert auth['explicit_human_authorization'] and auth['patch_sha256']==scratch['patch_sha256']
    assert sha(ROOT/auth['proposal'])==auth['proposal_sha256']
    for key,expected in [('patch_path','patch_sha256'),('proposed_source_path','proposed_sha256')]:assert sha(ROOT/scratch[key])==scratch[expected]
    old=read(base.CFG);OUT.mkdir()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    dump(OUT/'harness_before_build.json',h)
    dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A56','seed':1102081,'random_draws':0,'source_pin':base.PIN,'authorization':auth,'scratch_patch':scratch,'patch':old['patch'],'build':old['build'],'preservation':old['preservation'],'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'CPU_native':1,'GPU':False},'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    previous=read(a55/'preservation_before_metadata.json');pins={row['path']:row for row in previous['files']}
    for row in read(a55/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [a55/'artifact_manifest.json',a55/'publication_verification.json']:pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_SHA256_manifests_retained':True})
    print(json.dumps({'A56_declared':True,'explicit_scratch_authorization':True}),flush=True)

def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    config=read(CFG);assert config['authorization']['explicit_human_authorization']
    return config

'''
    s=s.replace('def run():',extra+'def run():')
    ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n')
    proof=ROOT/'wtc1_simulation_v8/data/aircraft_a56_builder_derivation.json'
    dump(proof,{'created_utc':now(),'source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest),'replacements':audit,'native_build_not_started':True,'exact_authorized_scratch_inserted':True})
    print('A56 builder ready.',flush=True)

if __name__=='__main__':main()
