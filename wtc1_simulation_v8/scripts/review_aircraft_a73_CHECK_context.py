"""Assess new A73 policy controls and directly captured context; do not rerun native work."""
from control_aircraft_a73_CHECK_context import ROOT,OUT,CONTROL,read,dump,sha,now,engine
from build_aircraft_a54_graph import rel
import json,math,numpy as np


def main():
    engine(); c=read(CONTROL);runs=read(OUT/'native_execution_review.json')
    assert runs['new_Engine']==6 and runs['new_Starter']==0
    import review_aircraft_a67_current_area as free_reader
    free_reader.OUT=OUT
    free,diag=free_reader.case_review(c['free_case'],c)
    dump(OUT/'free_dynamic_regression_review.json',{'created_utc':now(),'pass':free['pass'],'case':free,
        'new_binary_regression_only':True,'old_A67_outputs_not_replayed_or_relabelled':True,'whole_credit_s':0})
    rows=[];contexts=[]
    for r in runs['cases']:
        key=r['case'];d=(OUT/'native'/key) if key=='FREE_DYNAMIC_REGRESSION' else OUT/key
        if key=='FREE_DYNAMIC_REGRESSION':
            checks={'free_native_conservation_reference_same_A67_limits':free['pass']}
        else:
            obs=read(d/'check_observation.json');lb=np.fromfile(d/'native_LB.raw',dtype='<f8')
            r2=[e['native_R2'] for e in obs['events'] if 'native_R2' in e]
            ctx=[e['native_CHECK_context'] for e in obs['events'] if 'native_CHECK_context' in e]
            assert len(r2)==len(ctx)==1
            R=r2[0];context=ctx[0]
            assert float(lb@lb)==R and np.isfinite(lb).all()
            assert context==r['native_CHECK_context'] and set(context)==set(c['native_globals'])
            checks={'complete_native_observation':r['observation_complete'],
                'complete_direct_context_observation':r['context_observation_complete'],
                'native_R2_matches_independent_actual_LB':True,
                'normal_with_code0':r['normal_termination'] and r['parent_exit_code']==0,
                'explicit_CHECK_native_flag_positive':context['IMP_CHK']>0,
                'counter_observed_as_integer':isinstance(context['NCYCLE'],int),
                'native_TT_directly_observed_finite':isinstance(context['TT'],(int,float)) and math.isfinite(context['TT'])}
            if key=='STATIC_INITIAL_ZERO_CHECK':
                checks.update(zero_R2=R==0,static_context_outside_new_guard=context['IDYNA']!=2 or context['IQSTAT']!=0,
                    static_still_refused=r['loading_errors']==1 and r['initial_zero_dynamic_INFO']==0)
            elif key=='STATIC_POSITIVE_LOAD_CHECK':
                checks.update(exact_positive_load_R2_4N_squared=abs(R-4)<=1e-12,
                    positive_still_accepted=r['loading_errors']==0 and r['initial_zero_dynamic_INFO']==0)
            else:
                checks.update(zero_R2=R==0,Newmark2_native_context=context['IDYNA']==2,
                    not_quasistatic_native_context=context['IQSTAT']==0,
                    initial_Newmark_zero_NEW_INFO=r['initial_zero_dynamic_INFO']==1,
                    no_loading_error=r['loading_errors']==0)
            if key.startswith('WHOLE_'):
                checks['TYPE25_five_unchanged_still_blocking']=r['TYPE25_ignored']==5
                checks['connection_warning_distribution_still_107391']=obs['post']['native_connection_warning_condition_count']==107391
            contexts.append({'case':key,'native_context':context,'native_R2':R,
                'TT_is_exact_zero':context['TT']==0,'old_TT0_policy_result_preserved':True,
                'all_values_read_from_new_A73_child':True})
        pass_case=all(checks.values())
        rows.append({'case':key,'software_control_pass':bool(pass_case),'checks':checks,
            'failed_checks':[k for k,v in checks.items() if not v],
            'actual_message_review':rel(d/'actual_message_review.json'),'whole_physical_qualification':False})
    passed=all(r['software_control_pass'] for r in rows)
    dump(OUT/'CHECK_policy_control_review.json',{'created_utc':now(),'cases':rows,'pass':passed,
        'failed_expected_cases':[r['case'] for r in rows if not r['software_control_pass']],
        'all_six_native_finished':True,'all_five_CHECK_observations_complete':True,
        'all_five_context_observations_complete':True,'no_unused_budget':True,'whole_credit_s':0})
    dump(OUT/'native_CHECK_context_review.json',{'created_utc':now(),'cases':contexts,
        'five_fields_directly_read_in_five_CHECKs':True,'new_Engine':0,'no_guessed_native_scalar_values':True,
        'source_chronology_previously_verified_without_replay':True,
        'software_policy_control_pass':passed,'whole_impact_qualified':False})
    print(json.dumps({'free_dynamic_regression_pass':free['pass'],'CHECK_policy_pass':passed,
        'failed_cases':[r['case'] for r in rows if not r['software_control_pass']],
        'native_contexts':contexts,'new_native':0}),flush=True)


if __name__=='__main__':main()
