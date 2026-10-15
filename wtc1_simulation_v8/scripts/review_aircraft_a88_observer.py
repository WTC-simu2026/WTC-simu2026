"""Verify the second-trial observer's ABI, mode fields and fresh-budget guard statically."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import ast

def main():
    folder=ROOT/'wtc1_simulation_v8/output/aircraft_a88_preparation';plan_path=ROOT/'wtc1_simulation_v8/data/aircraft_a88_proposal.json';p=read(plan_path)
    source=ROOT/'wtc1_simulation_v8/openradioss_runtime/a86_null_relative_proposal/nl_solv.proposed.F'
    text=source.read_text(encoding='utf8');start=text.index('      SUBROUTINE NL_SOLV(');end=text.index('C-----------------------------------------------',start)
    signature=''.join(line[6:] for line in text[start:end].splitlines());names=[x.strip() for x in signature[signature.index('(')+1:signature.index(')')].split(',')]
    assert names[58]=='ICONT' and names[26]=='IT' and names[35:37]==['DE0','EIMP']
    observer=ROOT/p['observer'];s=observer.read_text(encoding='utf8');tree=ast.parse(s)
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='ptrace']
    assert {n.args[0].value for n in calls}=={0,6,7}
    import run_aircraft_a89_second_attempt as future
    assert not future.AUTH.exists() and not future.OUT.exists()
    try:future.prerequisites()
    except AssertionError as exc:rejected='authorization missing' in str(exc)
    else:rejected=False
    assert rejected
    checks={'actual_59th_argument_is_ICONT':True,'IT_and_energy_ABI_indices_unchanged':True,
        'ptrace_requests_only_TRACEME_debug_register_CONT':True,'missing_new_authorization_rejected':rejected,
        'no_native_A89_output_directory':not future.OUT.exists(),
        'criterion2_disable_still_present':'sites=[0,0,0,0];enable()' in s,
        'completion_uses_second_criterion_samples_only':"if attempt!=2:continue" in s,
        'newbinary_hash_matches_sealed_A87':p['unchanged_software'][1]['sha256']==read(ROOT/'wtc1_simulation_v8/output/aircraft_a87/build_finished.json')['binary_sha256'],
        'all_typed_global_ranges_guarded':all(v['byte_offset']+({'i32':4,'f64':8}[v['kind']])<=p['global_symbols'][v['symbol']]['bytes'] for v in p['native_globals'].values()),
        'same_exact_initial_inputs':all(sha(ROOT/r['path'])==r['sha256'] for r in p['inputs'])}
    assert all(checks.values())
    dump(folder/'final_observer_review.json',{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(plan_path),
        'observer_sha256':sha(observer),'launcher_sha256':sha(Path(future.__file__)),
        'reviewer_script':rel(Path(__file__)),'reviewer_sha256':sha(Path(__file__)),
        'runtime_still_unqualified':True,'new_Engine_Starter':0})
    dump(folder/'harness_after_final_observer_review.json',harness())
    print('A89 final observer review PASS:10 checks, zero native process.',flush=True)

if __name__=='__main__':main()
