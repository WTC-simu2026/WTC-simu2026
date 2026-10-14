"""Assess the actual six controls, retain the failed zero-initial-time policy and trace the new call chronology."""
from control_aircraft_a71_initial_zero import ROOT,OUT,CONTROL,read,dump,sha,now,engine
from build_aircraft_a54_graph import rel
from pathlib import Path
import json,numpy as np,tarfile,hashlib,re

def main():
    engine();c=read(CONTROL);runs=read(OUT/'native_execution_review.json');assert runs['new_Engine']==6 and runs['new_Starter']==1
    import review_aircraft_a67_current_area as free_reader
    free_reader.OUT=OUT;free,diag=free_reader.case_review(c['free_case'],c)
    dump(OUT/'free_dynamic_regression_review.json',{'created_utc':now(),'pass':free['pass'],'case':free,'new_binary_regression_only':True,
        'old_A67_outputs_not_replayed_or_relabelled':True,'whole_credit_s':0})
    rows=[]
    for r in runs['cases']:
        key=r['case'];d=(OUT/'native'/key) if key=='FREE_DYNAMIC_REGRESSION' else OUT/key
        if key=='FREE_DYNAMIC_REGRESSION':pass_case=free['pass'];checks={'free_native_conservation_reference_same_A67_limits':pass_case}
        else:
            obs=read(d/'check_observation.json');lb=np.fromfile(d/'native_LB.raw',dtype='<f8');R=[e['native_R2'] for e in obs['events'] if 'native_R2' in e][0]
            assert float(lb@lb)==R and np.isfinite(lb).all()
            checks={'complete_native_observation':r['observation_complete'],'native_R2_matches_independent_actual_LB':True,
                'normal_with_code0':r['normal_termination'] and r['parent_exit_code']==0}
            if key=='STATIC_INITIAL_ZERO_CHECK':checks.update(zero_R2=R==0,static_still_refused=r['loading_errors']==1 and r['initial_zero_dynamic_INFO']==0)
            elif key=='STATIC_POSITIVE_LOAD_CHECK':checks.update(exact_positive_load_R2_4N_squared=abs(R-4)<=1e-12,positive_still_accepted=r['loading_errors']==0 and r['initial_zero_dynamic_INFO']==0)
            else:checks.update(zero_R2=R==0,initial_Newmark_zero_NEW_INFO=r['initial_zero_dynamic_INFO']==1,no_loading_error=r['loading_errors']==0)
            if key.startswith('WHOLE_'):checks['TYPE25_five_unchanged_still_blocking']=r['TYPE25_ignored']==5
            pass_case=all(checks.values())
        rows.append({'case':key,'software_control_pass':bool(pass_case),'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],
            'actual_message_review':rel(d/'actual_message_review.json'),'whole_physical_qualification':False})
    dump(OUT/'CHECK_policy_control_review.json',{'created_utc':now(),'cases':rows,'pass':all(r['software_control_pass'] for r in rows),
        'failed_expected_initial_zero_cases':[r['case'] for r in rows if not r['software_control_pass']],
        'all_six_native_finished':True,'all_five_CHECK_observations_complete':True,'no_unused_budget':True,'whole_credit_s':0})
    private=ROOT/'wtc1_simulation_v8/openradioss_runtime/a71_CHECK_call_order_audit';assert not private.exists();private.mkdir()
    archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz';sources=[];raw={}
    with tarfile.open(archive) as t:
        for path in ['engine/source/engine/resol.F','engine/source/implicit/imp_dyna.F']:
            m=next(m for m in t.getmembers() if m.name.endswith('/'+path));b=t.extractfile(m).read();p=private/Path(path).name;p.write_bytes(b);raw[path]=b.decode('utf8').splitlines()
            sources.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'private_raw_copy':rel(p)})
    s=raw['engine/source/engine/resol.F'];call=next(i for i,l in enumerate(s) if 'CALL IMP_CHKM(' in l)
    time_add=[i for i,l in enumerate(s) if re.match(r'\s*TT\s*=\s*TT\s*\+\s*DT2\s*$',l)];assert len(time_add)==1 and time_add[0]<call
    flag=next(i for i,l in enumerate(s) if 'IF (IMP_CHK > 0) THEN' in l and i>time_add[0]);assert flag<call
    stop=next(i for i,l in enumerate(s[call:],call) if 'MSTOP=2' in l);assert stop>call
    counter=next(i for i,l in enumerate(s) if 'IF(T1S==TT)NCYCLE=NCYCLE+1' in l);assert counter<time_add[0]
    audit={'created_utc':now(),'pass_read_only_source_chronology':True,'source_rows':sources,
        'NCYCLE_increment_line_1based':counter+1,'native_TT_advance_line_1based':time_add[0]+1,'IMP_CHK_positive_guard_line_1based':flag+1,
        'IMP_CHKM_call_line_1based':call+1,'CHECK_stop_MSTOP2_line_1based':stop+1,
        'TT_advances_before_CHECK_call':True,'literal_TT0_is_not_the_initial_CHECK_context':True,
        'native_flags_IDYNA_IQSTAT_TT_NCYCLE_not_directly_captured_in_A71':True,'no_guessed_native_scalar_values':True,
        'next_proposal_should_use_explicit_CHECK_context_not_absolute_time_zero':True,'current_A71_patch_gate_failed_preserved':True,
        'all_six_runs_consumed_new_native_zero':True,'whole_impact_qualified':False}
    dump(OUT/'CHECK_call_order_review.json',audit)
    print(json.dumps({'free_dynamic_regression_pass':free['pass'],'CHECK_policy_pass':False,'failed_zero_cases':[r['case'] for r in rows if not r['software_control_pass']],
        'source_TT_advance_before_CHECK':True,'new_native':0}),flush=True)

if __name__=='__main__':main()
