"""Prepared launcher: require a distinct human receipt; never reset A67 or permit more than three observations."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import shutil,subprocess,shlex,time,json

PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a69_proposal.json'
REVIEW=ROOT/'wtc1_simulation_v8/output/aircraft_a69_preparation/independent_preparation_review.json'
AUTH=ROOT/'wtc1_simulation_v8/data/aircraft_a69_authorization.json'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a69_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a69'

def guard():
    assert AUTH.exists(),'A69 requires a NEW explicit human authorization; A67 budget is consumed'
    a=read(AUTH);p=read(PLAN);r=read(REVIEW)
    assert a['explicit_human_authorization'] and a['plan_sha256']==sha(PLAN) and a['review_sha256']==sha(REVIEW)
    assert r['pass'] and r['plan_sha256']==sha(PLAN) and r['launcher_sha256']==sha(Path(__file__))
    assert sha(ROOT/p['binary'])==p['binary_sha256'] and sha(ROOT/p['observer'])==p['observer_sha256']
    assert sha(ROOT/p['helper'])==p['helper_sha256'] and p['maximum_Engine']==3 and not p['source_patch'] and not p['compilation']
    for c in p['cases']:
        for f in c['input_files']:assert sha(ROOT/f['path'])==f['sha256'],f['path']
    return p,a

def declare():
    p,a=guard();assert not OUT.exists() and not CFG.exists();h=harness()
    assert h['CurrentIteration']=='AIRCRAFT-A68' and h['NextIteration']=='AIRCRAFT-A69'
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    dump(CFG,{**p,'iteration':'AIRCRAFT-A69','created_utc':now(),'authorization':a})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_new_native':True})
    print(json.dumps({'A69_declared':True,'maximum_new_Engine':3}),flush=True)

def run():
    p,a=guard();assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    assert not list(OUT.rglob('native_launch_declaration.json')),'Do not automatically retry any launched observation'
    b=ROOT/p['binary'];candidate=b.parent.parent;observer=ROOT/p['observer'];q=lambda x:shlex.quote(linux(x));rows=[]
    for idx,c in enumerate(p['cases'],1):
        assert idx<=3;d=OUT/c['case'];assert not d.exists();d.mkdir()
        for f in c['input_files']:
            dest=d/Path(f['path']).name;shutil.copy2(ROOT/f['path'],dest);assert sha(dest)==f['sha256']
        cfg=d/'instrumentation_config.json';dump(cfg,{'binary':linux(b),'binary_sha256':p['binary_sha256'],'directory':linux(d),
            'Engine_card':c['name']+'_0001.rad','symbols':p['symbols'],'node_count':c['node_count'],
            'CPU_threads':1,'cap_s':180,'new_A69_explicit_human_consent':True})
        script=d/'engine.launch.sh';script.write_text('set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(candidate)+'\nexport RAD_CFG_PATH='+q(candidate/'hm_cfg_files')+'\nexec python3 '+q(observer)+' '+q(cfg)+'\n',encoding='utf8',newline='\n')
        dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':idx,'maximum':3,'counts_even_if_failure_or_timeout':True,'authorization_sha256':sha(AUTH)})
        argv=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',linux(script)]
        start=time.perf_counter()
        try:
            v=subprocess.run(argv,capture_output=True,timeout=195);code=v.returncode;log=v.stdout+v.stderr
        except subprocess.TimeoutExpired as e:
            code=124;log=(e.stdout or b'')+(e.stderr or b'')
        (d/'engine.launcher.log').write_bytes(log)
        dump(d/'engine.execution.json',{'created_utc':now(),'parent_exit_code':code,'wall_s':time.perf_counter()-start,'CPU_threads':1,'cap_s':180,'GPU':False,
            'binary_sha256':p['binary_sha256'],'observer':rel(observer),'new_source_or_compilation':False})
        result=read(d/'check_observation.json') if (d/'check_observation.json').exists() else None
        row={'case':c['case'],'exit_code':code,'observation_complete':bool(result and result['observation_complete']),
            'whole_physical_qualification':False,'whole_credit_s':0};rows.append(row)
        dump(OUT/f'observation_progress_{idx}.json',{'created_utc':now(),'cases':rows,'budget_consumed':idx,'maximum':3})
        print(json.dumps(row),flush=True)
        assert code==0 and row['observation_complete'],'Stop on incomplete observation; preserve failure, no unbudgeted retry'
    dump(OUT/'execution_review.json',{'created_utc':now(),'cases':rows,'new_Engine':len(rows),'controls_remaining':3-len(rows),'whole_credit_s':0})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
