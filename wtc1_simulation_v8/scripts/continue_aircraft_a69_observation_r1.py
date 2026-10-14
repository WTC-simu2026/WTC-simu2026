"""Fix only own zero-length observer read and execute the two remaining planned cases; no replay/reset."""
from run_aircraft_a69_observation import ROOT,OUT,CFG,AUTH,guard
from build_aircraft_a54_graph import read,dump,sha,now,rel,linux
from pathlib import Path
import ast,shutil,subprocess,shlex,time,json

def main():
    p,a=guard();assert len(list(OUT.rglob('native_launch_declaration.json')))==1
    first=read(OUT/'WHOLE_ORIGINAL_CHECK/engine.execution.json');assert first['parent_exit_code']==1
    log=(OUT/'WHOLE_ORIGINAL_CHECK/engine.launcher.log').read_text(encoding='utf8');assert "bulk(a[11],ni,'i')" in log and 'AssertionError' in log
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    original=ROOT/p['observer'];observer=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a69_check_r1_linux.py';assert not observer.exists()
    before=original.read_text(encoding='utf8');old="width={'d':8,'i':4}[kind];assert address>4096 and 0<=count<=300000"
    new="width={'d':8,'i':4}[kind];assert 0<=count<=300000\n            if count==0:return array.array(kind)\n            assert address>4096"
    assert before.count(old)==1;after=before.replace(old,new);ast.parse(after);observer.write_text(after,encoding='utf8',newline='\n')
    dump(OUT/'observer_revision_r1.json',{'created_utc':now(),'original_observer':rel(original),'original_sha256':sha(original),'revised_observer':rel(observer),'revised_sha256':sha(observer),
        'scope':'Own observer only: zero-count array returns empty without dereferencing unused pointer; all positive-count address/length guards and ABI unchanged.',
        'source_Engine_binary_or_physics_modified':False,'first_failed_native_counts':1,'remaining_new_native':2,'retry_original_case':False,
        'same_three_case_authorization_no_budget_reset':True,'original_source_inputs_failures_and_output_preserved':True})
    b=ROOT/p['binary'];candidate=b.parent.parent;q=lambda x:shlex.quote(linux(x));rows=[]
    for idx,c in enumerate(p['cases'][1:],2):
        assert idx==len(list(OUT.rglob('native_launch_declaration.json')))+1 and idx<=3
        d=OUT/c['case'];assert not d.exists();d.mkdir()
        for f in c['input_files']:
            assert sha(ROOT/f['path'])==f['sha256'];dest=d/Path(f['path']).name;shutil.copy2(ROOT/f['path'],dest);assert sha(dest)==f['sha256']
        cfg=d/'instrumentation_config.json';dump(cfg,{'binary':linux(b),'binary_sha256':p['binary_sha256'],'directory':linux(d),'Engine_card':c['name']+'_0001.rad',
            'symbols':p['symbols'],'node_count':c['node_count'],'CPU_threads':1,'cap_s':180,'new_A69_explicit_human_consent':True})
        script=d/'engine.launch.sh';script.write_text('set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(candidate)+'\nexport RAD_CFG_PATH='+q(candidate/'hm_cfg_files')+'\nexec python3 '+q(observer)+' '+q(cfg)+'\n',encoding='utf8',newline='\n')
        dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':idx,'maximum':3,'counts_even_if_failure_or_timeout':True,'authorization_sha256':sha(AUTH),'observer_revision_sha256':sha(observer)})
        argv=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',linux(script)];start=time.perf_counter()
        v=subprocess.run(argv,capture_output=True,timeout=195);(d/'engine.launcher.log').write_bytes(v.stdout+v.stderr)
        dump(d/'engine.execution.json',{'created_utc':now(),'parent_exit_code':v.returncode,'wall_s':time.perf_counter()-start,'CPU_threads':1,'cap_s':180,'GPU':False,
            'binary_sha256':p['binary_sha256'],'observer':rel(observer),'new_source_or_compilation':False})
        r=read(d/'check_observation.json') if (d/'check_observation.json').exists() else None
        row={'case':c['case'],'exit_code':v.returncode,'observation_complete':bool(r and r['observation_complete']),'whole_physical_qualification':False,'whole_credit_s':0};rows.append(row)
        dump(OUT/f'observation_progress_r1_{idx}.json',{'created_utc':now(),'cases':rows,'budget_consumed':idx,'maximum':3,'original_attempt_preserved_failed':True})
        print(json.dumps(row),flush=True)
        assert v.returncode==0 and row['observation_complete'],'Stop and preserve failure; never exceed three Engine launches'
    dump(OUT/'execution_review_r1.json',{'created_utc':now(),'remaining_cases':rows,'new_Engine_total':3,'controls_remaining':0,'original_observation_failed_and_not_replayed':True,'whole_credit_s':0})

if __name__=='__main__':main()
