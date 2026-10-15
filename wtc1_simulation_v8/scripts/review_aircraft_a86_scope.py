"""Review the actual proposed source, builder and conditional budget without native work."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import ast,hashlib

def main():
    plan_path=ROOT/'wtc1_simulation_v8/data/aircraft_a86_proposal.json';p=read(plan_path);patch=p['patch']
    old=(ROOT/patch['current_source']).read_text(encoding='utf8');new=(ROOT/patch['proposed_source']).read_text(encoding='utf8')
    # Remove the complete added regions; require identity of every old byte.
    restored=new.replace('      LOGICAL WTC_NULL_REL\n','',1)
    begin=restored.index('C----Exact null free subspace: no tolerance or nonzero-path change.\n')
    end=restored.index('       RE=DE0/EIMP\n',begin)
    restored=restored[:begin]+restored[end:]
    restored=restored.replace('       ENDIF ! WTC_NULL_REL\n','',1)
    assert restored==old
    builder=ROOT/'wtc1_simulation_v8/scripts/build_aircraft_a87_null_relative.py'
    ast.parse(builder.read_text(encoding='utf8'))
    import build_aircraft_a87_null_relative as future
    assert not future.AUTH.exists() and not future.CAND.exists() and not future.OUT.exists()
    try:future.prerequisites()
    except AssertionError as exc:rejected='Fresh explicit consent' in str(exc)
    else:rejected=False
    assert rejected
    recipe=read(ROOT/p['baseline_recipe'])
    deps=[]
    for key in ['cached_source_archive','cached_dependency_archive']:
        r=recipe['build'][key];assert sha(ROOT/r['path'])==r['sha256'];deps.append({'path':r['path'],'sha256':r['sha256']})
    for case in p['cases']:
        for row in case['inputs']:assert sha(ROOT/row['path'])==row['sha256']
    old_binary=ROOT/'wtc1_simulation_v8/openradioss_runtime/a73_CHECK_context_candidate/isolated_exec/engine_linux64_gf_ompi'
    assert sha(old_binary)=='09a2f856d0eddb13ba56c80c578a12d058cb2cee1e403d46074b1b77b29aa158'
    diff=(ROOT/patch['patch']).read_text(encoding='utf8')
    checks={'old_full_source_restored_exact_after_removing_three_added_regions':True,
        'only_patch_target_nl_solv':diff.startswith('--- engine/source/implicit/nl_solv.F\n+++ engine/source/implicit/nl_solv.F\n') and diff.count('\n--- ')==0,
        'logical_declared_before_first_executable_statement':new.index('LOGICAL WTC_NULL_REL')<new.index('      FR = 0'),
        'NINTER0_excludes_whole_scene_interfaces':'NFXVEL>0.AND.NINTER==0.AND.IRODDL==0' in new,
        'build_body_has_exact_new_patch_hash_guard':"shell('04i_exact_A86_null_relative'" in future.body and 'matches_approved_A86_source_exactly' in future.body,
        'build_retains_all_A73_patch_recipe':all(k in future.body for k in ['current_area_patch','CHECK_context_patch','null_relative_patch','check_zero_residual_patch']),
        'old_false_criterion_change_annotation_corrected':"'physics_or_acceptance_criteria_changed': True" in future.body,
        'build_one_hour_six_CPU_unchanged':'deadline' in future.body and '--parallel 6' in future.body,
        'missing_new_human_approval_blocks_before_build':rejected,
        'four_ordered_controls_zero_Starter':len(p['cases'])==4 and p['maximum_Starter']==0 and [c['case'] for c in p['cases']]==['FREE_Ismstr4','AREA_EVOLUTION_FREE_Y','COMPRESSION_RUPTURE_RECLOSE','WHOLE_ORIGINAL_CHECK'],
        'loop_requires_two_regressions':p['cases'][2]['requires_prior_regressions_pass'],
        'whole_CHECK_requires_all_local_physical_gates':p['cases'][3]['requires_all_local_mechanical_and_energy_gates_pass'],
        'loop_literal_energy_1e7_J_preserved':p['cases'][2]['energy_absolute_J']==1e-7 and p['cases'][2]['initial_K_J']==0,
        'both_cached_dependencies_exact':True,'A73_binary_exactly_preserved':True,'no_candidate_or_native_A87_directory':True}
    assert all(checks.values()),checks
    folder=ROOT/'wtc1_simulation_v8/output/aircraft_a86_preparation'
    dump(folder/'final_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,
        'plan_sha256':sha(plan_path),'builder':rel(builder),'builder_sha256':sha(builder),
        'reviewer_script':rel(Path(__file__)),'reviewer_sha256':sha(Path(__file__)),
        'source_restoration_sha256':hashlib.sha256(restored.encode('utf8')).hexdigest(),
        'original_source_sha256':patch['current_sha256'],'dependencies':deps,
        'prepared_build_body_sha256':hashlib.sha256(future.body.encode('utf8')).hexdigest(),
        'source_patch_applied':False,'compiled':False,'new_Engine':0,'new_Starter':0,
        'native_Fortran_behavior_not_yet_qualified':True})
    dump(folder/'harness_after_final_scope_review.json',harness())
    print('A86 final scope review PASS:16 checks; no source application, build or native run.',flush=True)

if __name__=='__main__':main()
