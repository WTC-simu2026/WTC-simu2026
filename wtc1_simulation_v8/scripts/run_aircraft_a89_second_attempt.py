"""Prepared one-Engine launcher; a fresh explicit A85 receipt is mandatory."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux,harness
from pathlib import Path
import json,shutil,shlex,subprocess,time

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a89'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a89_predeclaration.json'
AUTH=ROOT/'wtc1_simulation_v8/data/aircraft_a89_authorization.json'
PLAN=ROOT/'wtc1_simulation_v8/data/aircraft_a88_proposal.json'
PROOF=ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a86_a87/final_remote_verification.json'
REVIEW=ROOT/'wtc1_simulation_v8/output/aircraft_a88_preparation/final_launcher_review.json'


def prerequisites():
    assert AUTH.exists(),'Fresh explicit A85 authorization missing; A83 Engine budget is consumed'
    proof=read(PROOF);assert proof['pass'] and proof['cadence_pending_count']==0
    assert proof['scientific_ci']['conclusion']==proof['final_ci']['conclusion']=='success'
    s=read(ROOT/'harness/state.json');cy=read(ROOT/'harness/publication_cycle.json')
    assert s['current_iteration']=='AIRCRAFT-A88' and s['next_iteration']=='AIRCRAFT-A89'
    assert cy['pending_iterations']==['AIRCRAFT-A88'] and cy['last_published_iteration']=='AIRCRAFT-A87'
    a=read(AUTH);p=read(PLAN);r=read(REVIEW)
    assert a['explicit_human_authorization'] and a['plan_sha256']==sha(PLAN)
    assert a['question_item'].startswith('request_user_input_async/')
    assert a['maximum_Engine']==p['maximum_Engine']==1 and a['maximum_Starter']==p['maximum_Starter']==0
    assert a['CPU_threads']==p['CPU_threads']==1 and a['cap_s']==p['cap_s']==180
    assert sha(ROOT/a['proposal'])==a['proposal_sha256']
    assert r['pass'] and r['plan_sha256']==sha(PLAN) and r['launcher_sha256']==sha(Path(__file__))
    assert sha(ROOT/p['observer'])==p['observer_sha256'] and sha(ROOT/p['helper'])==p['helper_sha256']
    assert sha(ROOT/p['source_static_review'])==p['source_static_review_sha256'] and read(ROOT/p['source_static_review'])['pass']
    assert not any(p[k] for k in ['GPU','source_patch','compilation','installation','whole_dynamic_extension'])
    for row in p['inputs']+p['unchanged_software']:assert sha(ROOT/row['path'])==row['sha256']
    assert sha(ROOT/p['source_Starter_gate'])==p['source_Starter_gate_sha256'] and read(ROOT/p['source_Starter_gate'])['pass']
    return p,a


def declare():
    assert not OUT.exists() and not CFG.exists()
    p,a=prerequisites();h=harness();assert h['RegistryEntries']==207
    OUT.mkdir();dump(OUT/'harness_before.json',h);dump(OUT/'authorization.json',a)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c={**p,'iteration':'AIRCRAFT-A89','declared_utc':now(),'authorization':a,'authorization_sha256':sha(AUTH),
        'plan_sha256':sha(PLAN),'driver_sha256':sha(Path(__file__)),'publication_proof_sha256':sha(PROOF),
        'new_explicit_human_authorization_required':False,'maximum_native_Engine':1,'consumed':0}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_native':True})
    pins={}
    for n in [87,88]:
        folder=ROOT/f'wtc1_simulation_v8/output/aircraft_a{n}';assert read(folder/'publication_verification.json')['pass']
        for row in read(folder/'artifact_manifest.json')['files']:
            path=ROOT/row['path'];assert sha(path)==row['sha256'];pins[row['path']]={**row,'mtime_ns_before':path.stat().st_mtime_ns}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':list(pins.values())})
    print(json.dumps({'A85_declared':True,'maximum_Engine':1,'Starter':0}),flush=True)


def guard():
    prerequisites();assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];c=read(CFG)
    assert sha(AUTH)==c['authorization_sha256'] and sha(PROOF)==c['publication_proof_sha256'] and sha(Path(__file__))==c['driver_sha256']
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:assert sha(ROOT/'harness'/n)==sha(OUT/('before_'+Path(n).name))
    return c


def run():
    c=guard();assert not list(OUT.rglob('Engine_launch_declaration.json'))
    d=OUT/c['case'];assert not d.exists();d.mkdir()
    for row in c['inputs']:
        p=ROOT/row['path'];shutil.copy2(p,d/p.name);assert sha(d/p.name)==row['sha256']
    assert not list(d.glob('*_0000.rad'))
    binary=ROOT/next(r['path'] for r in c['unchanged_software'] if 'engine_linux' in r['path']);candidate=binary.parent.parent
    observer=ROOT/c['observer'];icfg=d/'instrumentation_config.json'
    dump(icfg,{'binary':linux(binary),'binary_sha256':sha(binary),'directory':linux(d),
        'Engine_card':c['name']+'_0001.rad','symbols':c['symbols'],'node_count':8,'native_globals':c['native_globals'],'global_symbols':c['global_symbols'],
        'CPU_threads':1,'cap_s':180,'maximum_Engine':1,'maximum_Starter':0,'new_A89_explicit_human_consent':True})
    q=lambda p:shlex.quote(linux(p));script=d/'engine.launch.sh'
    script.write_text('set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 OMP_THREAD_LIMIT=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n'
        'export OPENRADIOSS_PATH='+q(candidate)+'\nexport RAD_CFG_PATH='+q(candidate/'hm_cfg_files')+'\nexec python3 '+q(observer)+' '+q(icfg)+'\n',encoding='utf8',newline='\n')
    dump(d/'Engine_launch_declaration.json',{'created_utc':now(),'ordinal':1,'maximum':1,'Starter':0,'CPU_threads':1,
        'cap_s':180,'counts_even_if_failed_or_expired':True,'config_sha256':sha(CFG)})
    argv=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',linux(script)]
    start=time.perf_counter();code=None;timed=False;out=b'';err=b''
    try:
        r=subprocess.run(argv,capture_output=True,timeout=195);code=r.returncode;out=r.stdout;err=r.stderr
    except subprocess.TimeoutExpired as e:timed=True;out=e.stdout or b'';err=e.stderr or b''
    (d/'engine.launcher.log').write_bytes(out+err)
    execution={'created_utc':now(),'argv':argv,'parent_exit_code':code,'wall_s':time.perf_counter()-start,
        'timed_out':timed or code in [124,137],'CPU_threads':1,'cap_s':180,'binary_sha256':sha(binary)}
    dump(d/'engine.execution.json',execution)
    observation=read(d/'normalization_observation.json') if (d/'normalization_observation.json').exists() else None
    dump(OUT/'native_execution_review.json',{'created_utc':now(),'new_Engine':1,'new_Starter':0,'Engine_remaining':0,
        'execution':execution,'observation_complete':bool(observation and observation['observation_complete']),
        'source_patch_compilation_GPU_installation':False,'no_automatic_retry':True,'whole_credit_s':0})
    print(json.dumps({'A85_native_finished':True,'Engine':1,'Starter':0,'observer_exit':code,
        'observation_complete':bool(observation and observation['observation_complete'])}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
