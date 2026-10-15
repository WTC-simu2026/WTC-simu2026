"""Final source/recipe/budget review without compiling or applying the candidate."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path

def main():
    plan_path=ROOT/'wtc1_simulation_v8/data/aircraft_a90_proposal.json';p=read(plan_path);pp=p['patch']
    old=(ROOT/pp['current_source']).read_text(encoding='utf8');new=(ROOT/pp['proposed_source']).read_text(encoding='utf8')
    diff=(ROOT/pp['patch']).read_text(encoding='utf8');prototype=read(ROOT/p['prototype_review'])
    assert prototype['pass'] and prototype['mathematical_cases_count']==105
    assert sha(ROOT/p['prototype_review'])==p['prototype_review_sha256']
    oldtail=old[old.index('      SUBROUTINE CRIT_ITE('):]
    helper_start=new.index('C----Exact zero test in the same free coordinates as PRODUT_UHP.')
    assert new[new.index('      SUBROUTINE CRIT_ITE('):helper_start].rstrip()==oldtail.rstrip()
    helper=new[helper_start:]
    assert helper.index('CALL IMP_SETB(')<helper.index('CALL CONDENS_B(')<helper.index('ISZERO=ALL(TMP_NULL(1:NDDL)==ZERO)')
    baseline=ROOT/p['baseline_recipe'];recipe=read(baseline);assert sha(baseline)==p['baseline_recipe_sha256']
    for row in [recipe['build']['cached_source_archive'],recipe['build']['cached_dependency_archive']]:assert sha(ROOT/row['path'])==row['sha256']
    assert recipe['null_relative_patch']['proposed_sha256']==pp['current_sha256']
    assert not (ROOT/p['future_candidate']).exists()
    for case in p['cases']:
        for row in case['inputs']:assert sha(ROOT/row['path'])==row['sha256']
    oldbinary=ROOT/'wtc1_simulation_v8/openradioss_runtime/a87_null_relative_candidate/isolated_exec/engine_linux64_gf_ompi'
    assert sha(oldbinary)=='9e72f04411158c9b48f67968eff3fe01f741aca5cb5bd3201985cdbaf75e27cd'
    checks={'one_patch_header_target_only':diff.startswith('--- engine/source/implicit/nl_solv.F\n+++ engine/source/implicit/nl_solv.F\n') and diff.count('\n--- ')==0,
        'CRIT_ITE_and_all_following_original_routines_unchanged':True,'native_projection_order_exact':True,
        'no_threshold_norm_in_exact_projected_vector_test':'ISZERO=ALL(TMP_NULL(1:NDDL)==ZERO)' in helper,
        'full_D_DD_nonfinite_exclusion_before_projection':new.index('ALL(ABS(D(1:3,1:NUMNOD))<=HUGE(ONE))')<new.index('CALL WTC_DD_PROJECTED_ZERO('),
        'native_U2_DU2_still_must_equal_zero':'WTC_NULL_REL=(U2==ZERO.AND.DU2==ZERO)' in new,
        'all_other_null_mode_guards_retained':'NFXVEL>0.AND.NINTER==0.AND.IRODDL==0' in new and 'NSPMD==1.AND.NTHREAD==1.AND.IT>=2' in new,
        'baseline_recipe_carries_A86_source_exactly':True,'both_dependency_caches_exact':True,
        'four_ordered_Engine_zero_Starter':p['maximum_Engine']==4 and p['maximum_Starter']==0 and [c['case'] for c in p['cases']]==['FREE_Ismstr4','AREA_EVOLUTION_FREE_Y','COMPRESSION_RUPTURE_RECLOSE','WHOLE_ORIGINAL_CHECK'],
        'loop_and_whole_CHECK_remain_conditional':p['cases'][2]['requires_prior_regressions_pass'] and p['cases'][3]['requires_all_local_mechanical_and_energy_gates_pass'],
        'literal_loop_energy_1e7J':p['cases'][2]['energy_absolute_J']==1e-7,
        'no_candidate_no_A91_authorization_no_native':not (ROOT/p['future_candidate']).exists() and not (ROOT/'wtc1_simulation_v8/data/aircraft_a91_authorization.json').exists(),
        'current_A87_binary_unchanged':True}
    assert all(checks.values())
    folder=ROOT/'wtc1_simulation_v8/output/aircraft_a90_preparation'
    dump(folder/'final_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(plan_path),
        'proposed_source_sha256':sha(ROOT/pp['proposed_source']),'patch_sha256':sha(ROOT/pp['patch']),
        'reviewer_script':rel(Path(__file__)),'reviewer_sha256':sha(Path(__file__)),
        'patch_applied':False,'compiled':False,'new_Engine':0,'new_Starter':0,'native_Fortran_behavior_not_yet_qualified':True})
    dump(folder/'harness_after_final_scope_review.json',harness())
    print('A90 final scope review PASS:14 checks; no application/build/native process.',flush=True)

if __name__=='__main__':main()
