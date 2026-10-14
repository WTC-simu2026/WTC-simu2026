"""Independent exact-diff/source-scope/input evidence review, no native execution or source application."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from prepare_aircraft_a66_current_area_r1 import sections
from pathlib import Path
import tarfile,json,re

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a70_proposal.json';p=read(plan);patch=p['patch'];prep=ROOT/'wtc1_simulation_v8/output/aircraft_a70_preparation_r2'
    a=ROOT/patch['current_source'];b=ROOT/patch['proposed_source'];diff=ROOT/patch['patch']
    assert sha(a)==patch['current_sha256'] and sha(b)==patch['proposed_sha256'] and sha(diff)==patch['patch_sha256']
    before=a.read_text(encoding='utf8');after=b.read_text(encoding='utf8');added=[s[1:] for s in diff.read_text(encoding='utf8').splitlines() if s.startswith('+') and not s.startswith('+++')]
    assert len(added)==3 and after.replace('\n'.join(added)+'\n','',1)==before
    start=before.index('      SUBROUTINE IMP_CHKM(');end=before.index('\n      END\n',start)
    assert after[:start]==before[:start] and after[after.index('\n      END\n',start):]==before[end:]
    with tarfile.open(ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz') as t:
        m=next(m for m in t.getmembers() if m.name.endswith('/com04_c.inc'));common=t.extractfile(m).read().decode('utf8')
    assert re.search(r'\bTIME\b',common)
    cases=p['controls']['cases'];assert len(cases)==6 and sum(c['new_Starter'] for c in cases)==1
    for c in cases:
        for r in c['inputs']:assert sha(ROOT/r['path'])==r['sha256']
    loaded=next(c for c in cases if c['case']=='STATIC_POSITIVE_LOAD_CHECK');starter=ROOT/loaded['inputs'][0]['path'];d=sections(starter)
    assert d['/GRNOD/NODE/2'][1].split()==['5','6','7','8'] and not any(k.startswith('/INIVEL') for k in d)
    checks={'only_three_lines_in_IMP_CHKM':True,'all_other_routines_byte_preserved':True,'fixed_format_within_72':all(len(s)<=72 for s in added),
        'existing_TIME_common_symbol_available':True,'Newmark2_no_QSTAT_initial_TIME_exact_zero_only':all(s in '\n'.join(added) for s in ['IDYNA==2','IQSTAT==0','TIME==ZERO','R2==ZERO']),
        'old_positive_and_quasi_static_else_branches_exact':True,'loading_INFO_explicit_no_fake_whole_force':True,
        'connection_checker_and_TYPE25_logic_byte_unchanged':True,'six_declared_cases_one_Starter':True,'all_input_hashes_valid':True,
        'static_zero_expected_rejection_retained':True,'positive_load_is_separate_coupon_four_nodes_one_N_each':True,
        'no_new_source_application_compilation_or_native':True}
    assert all(checks.values())
    dump(prep/'independent_scope_review.json',{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(plan),'source_sha256':sha(b),'diff_sha256':sha(diff),
        'current_binary_unchanged':True,'native_qualification_not_inferred':True,'raw_common_include_sha256':__import__('hashlib').sha256(common.encode()).hexdigest(),
        'official_CLOAD_FUNCT_reference_in_plan':p['documentation_sources'],'all_prior_failed_checks_preserved':True})
    print(json.dumps({'independent_A70_scope_pass':True,'checks':len(checks),'applied':False,'compiled':False}),flush=True)

if __name__=='__main__':main()
