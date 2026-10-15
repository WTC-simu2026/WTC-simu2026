"""Derive the eleventh builder without applying source, compiling or running native code."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import ast,importlib.util,hashlib

def main():
    folder=ROOT/'wtc1_simulation_v8/output/aircraft_a90_preparation';plan_path=ROOT/'wtc1_simulation_v8/data/aircraft_a90_proposal.json'
    source=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a87_null_relative.py';destination=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a91_projected_null_r1.py'
    assert not destination.exists();p=read(plan_path);assert sha(source)==p['baseline_builder_sha256']
    prefix=source.read_text(encoding='utf8').split('body=previous.body')[0]
    prefix=prefix.replace('aircraft_a87','aircraft_a91').replace('AIRCRAFT-A87','AIRCRAFT-A91')
    prefix=prefix.replace('aircraft_a86','aircraft_a90').replace('AIRCRAFT-A86','AIRCRAFT-A90')
    prefix=prefix.replace('a87_null_relative_candidate','a91_projected_null_candidate')
    prefix=prefix.replace('build_aircraft_a73_CHECK_context as previous','build_aircraft_a87_null_relative as previous')
    prefix=prefix.replace('tenth isolated','eleventh isolated').replace('for n in [85,86]:','for n in [89,90]:')
    prefix=prefix.replace("h['RegistryEntries']==205","h['RegistryEntries']==209").replace("'seed':1102110","'seed':1102116")
    prefix=prefix.replace("'CHECK_context_patch']","'CHECK_context_patch','null_relative_patch']")
    prefix=prefix.replace("'null_relative_patch':p['patch']","'projected_null_patch':p['patch']")
    prefix=prefix.replace("/final_scope_review.json'","/builder_preparation_review.json'")
    prefix=prefix.replace('updates_2026-10-15_aircraft_a84_a85','updates_2026-10-15_aircraft_a88_a89')
    body_code=r'''
body=previous.body.replace('AIRCRAFT-A87','AIRCRAFT-A91').replace('1102110','1102116')
marker="        shell('05_dependencies'"
assert body.count(marker)==1
insert='''+"'''"+r'''
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
'''+"'''"+r'''
body=body.replace(marker,insert+marker)
body=body.replace("'exact_A86_null_relative_applied':True,","'exact_A86_null_relative_applied':True,'exact_A90_projected_null_applied':True,")
body=body.replace('Explicit approval of exact A86 null-relative criterion definition, retaining complete A73 recipe and all prior failed results.',
    'Explicit approval of exact A90 projected-null correction, retaining complete A87 recipe and all prior failed results.')
exec(compile(body,__file__,'exec'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
'''
    # The raw composition above builds ordinary quoted Python, not shell text.
    content=prefix+body_code;ast.parse(content)
    destination.write_text(content,encoding='utf8',newline='\n')
    spec=importlib.util.spec_from_file_location('future_a91',destination);future=importlib.util.module_from_spec(spec);spec.loader.exec_module(future)
    assert not future.AUTH.exists() and not future.OUT.exists() and not future.CAND.exists()
    try:future.prerequisites()
    except AssertionError as exc:rejected='Fresh explicit consent' in str(exc)
    else:rejected=False
    assert rejected
    checks={'syntax_and_derived_body_valid':True,'missing_new_consent_rejected_before_build':rejected,
        'exact_A90_application_stage_before_configuration':future.body.index("shell('04j_exact_A90_projected_null'")<future.body.index("shell('06_configure'"),
        'A86_patch_still_applied_first':future.body.index("shell('04i_exact_A86_null_relative'")<future.body.index("shell('04j_exact_A90_projected_null'"),
        'current_recipe_retains_null_relative_patch':"'CHECK_context_patch','null_relative_patch']" in prefix,
        'new_source_hash_checked':'matches_approved_A90_source_exactly' in future.body,
        'one_hour_six_CPU_build_retained':'--parallel 6' in future.body and 'deadline=started+3600' in future.body,
        'expected_current_state_A90_and_registry209':"'AIRCRAFT-A90'" in prefix and "h['RegistryEntries']==209" in prefix}
    assert all(checks.values())
    dump(folder/'builder_preparation_review.json',{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(plan_path),
        'builder':rel(destination),'builder_sha256':sha(destination),'source_builder':rel(source),'source_builder_sha256':sha(source),
        'generator':rel(Path(__file__)),'generator_sha256':sha(Path(__file__)),
        'prepared_body_sha256':hashlib.sha256(future.body.encode('utf8')).hexdigest(),
        'patch_applied':False,'compiled':False,'new_native':0})
    dump(folder/'harness_after_builder_preparation.json',harness())
    print('A91 builder prepared with eight scope checks; no source applied or compilation run.',flush=True)

if __name__=='__main__':main()
