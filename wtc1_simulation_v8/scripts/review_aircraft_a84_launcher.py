"""Check observer call sites and fresh-consent guard without executing an Engine."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import ast,subprocess,re

def main():
    folder=ROOT/'wtc1_simulation_v8/output/aircraft_a84_preparation'
    p=ROOT/'wtc1_simulation_v8/data/aircraft_a84_proposal.json';plan=read(p)
    driver=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a85_normalization.py'
    observer=ROOT/plan['observer'];ast.parse(driver.read_text(encoding='utf8'));ast.parse(observer.read_text(encoding='utf8'))
    binary=ROOT/next(r['path'] for r in plan['unchanged_software'] if 'engine_linux' in r['path'])
    r=subprocess.run(['wsl.exe','-d','Ubuntu','--','objdump','-d','--disassemble=nl_solv_',linux(binary)],capture_output=True,text=True,timeout=30)
    assert r.returncode==0
    calls=[l.strip() for l in r.stdout.splitlines() if re.search(r'call\s+\S+ <(?:crit_ite_|produt_uhp_)>',l)]
    assert any('<crit_ite_>' in l for l in calls) and any('<produt_uhp_>' in l for l in calls)
    from run_aircraft_a85_normalization import prerequisites,AUTH
    assert not AUTH.exists()
    try:prerequisites()
    except AssertionError as exc:rejected='Fresh explicit A85 authorization missing' in str(exc)
    else:rejected=False
    assert rejected
    text=driver.read_text(encoding='utf8')
    checks={'syntax_valid_for_observer_and_launcher':True,'actual_binary_calls_not_inlined_away':True,
        'missing_new_authorization_rejected_before_any_process':rejected,
        'single_Engine_declaration_before_launch':text.index("dump(d/'Engine_launch_declaration.json'")<text.index('r=subprocess.run(argv'),
        'timeout_180_and_parent_195_present':"'--kill-after=5','180'" in text and 'timeout=195' in text,
        'no_Starter_card_copied':"assert not list(d.glob('*_0000.rad'))" in text,
        'no_existing_launch_can_retry':"assert not list(OUT.rglob('Engine_launch_declaration.json'))" in text,
        'observer_and_helper_pinned':sha(observer)==plan['observer_sha256'] and sha(ROOT/plan['helper'])==plan['helper_sha256']}
    assert all(checks.values())
    dump(folder/'native_call_site_metadata.json',{'created_utc':now(),'pass':True,'binary_sha256':sha(binary),
        'own_numeric_metadata_only_no_raw_source':True,'call_sites':calls,'native_Engine_Starter_executed':0})
    dump(folder/'final_launcher_review.json',{'created_utc':now(),'pass':True,'checks':checks,
        'plan_sha256':sha(p),'launcher':rel(driver),'launcher_sha256':sha(driver),
        'reviewer_script':rel(Path(__file__)),'reviewer_sha256':sha(Path(__file__)),
        'runtime_observer_behavior_not_yet_qualified':True,'new_Engine':0,'new_Starter':0})
    dump(folder/'harness_after_final_review.json',harness())
    print('A85 launcher prepared: eight scope checks pass; fresh consent still missing.',flush=True)

if __name__=='__main__':main()
