"""One explicitly authorized Engine observation, no Starter or retry."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import json,shlex,shutil,subprocess,time,re

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a83'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a83_predeclaration.json'
AUTH=ROOT/'wtc1_simulation_v8/data/aircraft_a83_authorization.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a82_proposal.json'
PROOF=ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a80_a81/final_remote_verification.json'


def prerequisites():
    proof=read(PROOF);assert proof['pass'] and proof['cadence_pending_count']==0
    assert proof['scientific_ci']['conclusion']==proof['final_ci']['conclusion']=='success'
    s=read(ROOT/'harness/state.json');cycle=read(ROOT/'harness/publication_cycle.json')
    assert s['current_iteration']=='AIRCRAFT-A82' and s['next_iteration']=='AIRCRAFT-A83'
    assert cycle['pending_iterations']==['AIRCRAFT-A82'] and cycle['last_published_iteration']=='AIRCRAFT-A81'
    a=read(AUTH);p=read(PLAN)
    assert a['explicit_human_authorization'] and a['plan_sha256']==sha(PLAN)
    assert a['answer']=='Oui, exécuter l’observation détaillée A83'
    assert a['question_item']=='request_user_input_async/call_3e99b79a34d14243b0cdbbaca9e5799b/0'
    assert a['maximum_Engine']==1 and a['maximum_Starter']==0 and a['CPU_threads']==1 and a['cap_s']==180
    assert sha(ROOT/a['proposal'])==a['proposal_sha256']
    assert p['maximum_Engine']==1 and p['maximum_Starter']==0 and p['CPU_threads']==1 and p['cap_s']==180
    assert not any(p[k] for k in ['GPU','source_patch','compilation','installation','whole_dynamic_extension'])
    assert read(ROOT/p['scope_review'])['pass']
    for r in p['inputs']+p['unchanged_software']:assert sha(ROOT/r['path'])==r['sha256']
    assert sha(ROOT/p['source_Starter_gate'])==p['source_Starter_gate_sha256'] and read(ROOT/p['source_Starter_gate'])['pass']
    return p,a


def declare():
    assert not OUT.exists() and not CFG.exists()
    p,a=prerequisites();h=harness();assert h['RegistryEntries']==201
    OUT.mkdir();dump(OUT/'harness_before.json',h);dump(OUT/'authorization.json',a)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={**p,'iteration':'AIRCRAFT-A83','declared_utc':now(),'authorization':a,'plan_sha256':sha(PLAN),
        'authorization_sha256':sha(AUTH),'publication_proof_sha256':sha(PROOF),'driver_sha256':sha(Path(__file__)),
        'new_explicit_human_authorization_required':False,'native_consumed':0}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_native':True})
    pins={}
    for n in [81,82]:
        folder=ROOT/f'wtc1_simulation_v8/output/aircraft_a{n}'
        assert read(folder/'publication_verification.json')['pass']
        for r in read(folder/'artifact_manifest.json')['files']:
            pp=ROOT/r['path'];assert sha(pp)==r['sha256'];pins[r['path']]={**r,'mtime_ns_before':pp.stat().st_mtime_ns}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':list(pins.values()),'all_old_failed_gates_preserved':True})
    print(json.dumps({'A83_declared':True,'maximum_Engine':1,'Starter':0}),flush=True)


def guard():
    prerequisites();assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];c=read(CFG)
    assert sha(AUTH)==c['authorization_sha256'] and sha(PROOF)==c['publication_proof_sha256']
    assert sha(Path(__file__))==c['driver_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/n)==sha(OUT/('before_'+Path(n).name))
    return c


def run():
    c=guard();assert not list(OUT.rglob('Engine_launch_declaration.json'))
    d=OUT/c['case'];assert not d.exists();d.mkdir()
    for r in c['inputs']:
        p=ROOT/r['path'];shutil.copy2(p,d/p.name);assert sha(d/p.name)==r['sha256']
    assert not list(d.glob('*_0000.rad'))
    row=next(r for r in c['unchanged_software'] if 'engine_linux' in r['path']);binary=ROOT/row['path'];candidate=binary.parent.parent
    q=lambda p:shlex.quote(linux(p));script=d/'engine.launch.sh'
    script.write_text('set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 OMP_THREAD_LIMIT=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n'
        'export OPENRADIOSS_PATH='+q(candidate)+'\nexport RAD_CFG_PATH='+q(candidate/'hm_cfg_files')+'\nexec '+q(binary)+' -i '+shlex.quote(c['name']+'_0001.rad')+' > engine.log 2>&1\n',encoding='utf8',newline='\n')
    dump(d/'Engine_launch_declaration.json',{'created_utc':now(),'ordinal':1,'maximum':1,'Starter':0,
        'CPU_threads':1,'cap_s':180,'GPU':False,'counts_even_if_failed_or_expired':True,'config_sha256':sha(CFG)})
    argv=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',linux(script)]
    start=time.perf_counter();code=None;timed=False;out=b'';err=b''
    try:
        result=subprocess.run(argv,capture_output=True,timeout=195);code=result.returncode;out=result.stdout;err=result.stderr
    except subprocess.TimeoutExpired as e:timed=True;out=e.stdout or b'';err=e.stderr or b''
    (d/'engine.launcher.log').write_bytes(out+err)
    x={'created_utc':now(),'argv':argv,'parent_exit_code':code,'wall_s':time.perf_counter()-start,'timed_out':timed or code in [124,137],
        'CPU_threads':1,'cap_s':180,'GPU':False,'binary_sha256':sha(binary)}
    dump(d/'engine.execution.json',x)
    dump(OUT/'native_execution_review.json',{'created_utc':now(),'new_Engine':1,'new_Starter':0,'Engine_remaining':0,
        'execution':x,'software_patch_compilation_GPU_installation':False,'whole_dynamic_extension':False,
        'old_failed_gates_preserved':True,'observation_qualification_pending':True,'whole_credit_s':0})
    print(json.dumps({'A83_native_finished':True,'Engine':1,'Starter':0,'exit':code,'wall_s':x['wall_s']}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
