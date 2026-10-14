"""Independent static ABI/inputs/authorization review; this does NOT execute the prepared observer."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import re,ast,json

def signature(text,name):
    lines=text.splitlines();i=next(i for i,s in enumerate(lines) if 'SUBROUTINE '+name+'(' in s)
    parts=[]
    for s in lines[i:]:
        parts.append(s[6:])
        if ')' in s:break
    return ''.join(parts).split('(',1)[1].split(')',1)[0].replace(' ','').split(',')

def main():
    plan=ROOT/'wtc1_simulation_v8/data/aircraft_a69_proposal.json';p=read(plan);out=ROOT/'wtc1_simulation_v8/output/aircraft_a69_preparation'
    private=ROOT/'wtc1_simulation_v8/openradioss_runtime/a68_check_semantics_audit'
    observer=ROOT/p['observer'];launcher=ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a69_observation.py';s=observer.read_text(encoding='utf8');l=launcher.read_text(encoding='utf8')
    ast.parse(s);ast.parse(l)
    lin=signature((private/'lin_solv.F').read_text(encoding='utf8'),'LIN_SOLV')
    pre=signature((private/'imp_solv.F').read_text(encoding='utf8'),'IMP_CHECK0')
    post=signature((private/'imp_solv.F').read_text(encoding='utf8'),'IMP_CHECM0')
    norm=signature((private/'produt_v.F').read_text(encoding='utf8'),'PRODUT_W')
    checks={'source_rhs_is_argument_23':lin[22]=='F' and "rhs=bulk(a[22],n,'d')" in s,
        'pre_DIAG_K_arg4_and_interface_args11_12_13':pre[3]=='DIAG_K' and pre[10:13]==['NDDLI','ITOK','DIAG_I'],
        'post_DIAG_M_arg4_and_INLOC_arg7':post[3]=='DIAG_M' and post[6]=='INLOC',
        'norm_result_arg5_from_r8':norm==['NDDL','X','Y','W','R'] and "'result_pointer':r.r8" in s,
        'SysV_first_stack_argument_at_rsp_plus_8':'r.rsp+8*(j-5)' in s,
        'result_return_breakpoint_is_dynamic_not_guessed_instruction_offset':"sites[3]=ret+base" in s,
        'memory_file_read_only':"os.O_RDONLY" in s and 'os.pread' in s and 'os.pwrite' not in s,
        'no_ptrace_text_or_data_patch':not re.search(r'ptrace\([45],',s),
        'trace_failure_kills_only_own_child':'os.kill(pid,signal.SIGKILL)' in s,
        'NEW_receipt_required_before_launch':"A69 requires a NEW explicit human authorization" in l and "a['review_sha256']==sha(REVIEW)" in l,
        'budget_counts_before_launch':'counts_even_if_failure_or_timeout' in l and 'assert idx<=3' in l,
        'CPU_one_cap180_no_software_change':p['CPU_threads']==1 and p['each_cap_s']==180 and not any(p[k] for k in ['GPU','installation','source_patch','compilation','whole_dynamic_extension'])}
    for c in p['cases']:
        for f in c['input_files']:assert sha(ROOT/f['path'])==f['sha256']
    assert sha(observer)==p['observer_sha256'] and all(checks.values())
    review=out/'independent_preparation_review.json'
    dump(review,{'created_utc':now(),'pass':True,'checks':checks,'plan_sha256':sha(plan),'observer_sha256':sha(observer),'launcher_sha256':sha(launcher),
        'native_observer_not_run_or_runtime_qualified':True,'A69_explicit_authorization_not_received':True,'new_native':0,'inputs_hash_verified':True})
    a68=ROOT/'wtc1_simulation_v8/output/aircraft_a68';original=read(a68/'artifact_manifest.json');paths={ROOT/r['path'] for r in original['files']}
    paths.update([launcher,Path(__file__),review])
    dump(a68/'artifact_manifest_r1.json',{'created_utc':now(),'original_manifest_preserved':rel(a68/'artifact_manifest.json'),'original_sha256':sha(a68/'artifact_manifest.json'),
        'own_outputs_scripts_only_AGPL_excluded':True,'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(paths)]})
    print(json.dumps({'preparation_review_pass':True,'static_checks':len(checks),'new_native':0}),flush=True)

if __name__=='__main__':main()
