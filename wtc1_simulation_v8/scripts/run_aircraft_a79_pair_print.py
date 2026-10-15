"""One authorized detailed Starter observation; never invokes an Engine."""
from build_aircraft_a54_graph import ROOT, read, dump, sha, now, rel, harness
from run_aircraft_a17 import env
from read_aircraft_a77_Starter import read_starter
from pathlib import Path
import json, shutil, subprocess, time

OUT = ROOT/'wtc1_simulation_v8/output/aircraft_a79'
CFG = ROOT/'wtc1_simulation_v8/data/aircraft_a79_predeclaration.json'
AUTH = ROOT/'wtc1_simulation_v8/data/aircraft_a79_authorization.json'
PLAN = ROOT/'wtc1_simulation_v8/data/aircraft_a78_proposal.json'


def declare():
    assert not any(p.exists() for p in [OUT, CFG, AUTH])
    h = harness()
    s = read(ROOT/'harness/state.json'); cycle = read(ROOT/'harness/publication_cycle.json')
    assert s['current_iteration']=='AIRCRAFT-A78' and s['next_iteration']=='AIRCRAFT-A79'
    assert h['RegistryEntries']==197 and cycle['pending_iterations']==['AIRCRAFT-A78']
    p = read(PLAN)
    assert p['maximum_Starter']==1 and p['maximum_Engine']==0 and p['CPU_threads']==1 and p['cap_s']==180
    scope = ROOT/'wtc1_simulation_v8/output/aircraft_a78_preparation/print_observation_scope_review.json'
    proposal = ROOT/'wtc1_simulation_v8/output/aircraft_a78_preparation/proposition_observation_paires_initiales_DETAIL.md'
    assert read(scope)['pass'] and read(scope)['plan_sha256']==sha(PLAN)
    previous = ROOT/'wtc1_simulation_v8/output/aircraft_a78'
    assert read(previous/'publication_verification.json')['pass']
    for row in read(previous/'artifact_manifest.json')['files']:
        assert sha(ROOT/row['path'])==row['sha256'], row['path']
    for row in p['inputs']:
        assert sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
    assert sha(ROOT/p['Starter_binary'])==p['Starter_sha256']
    assert sha(ROOT/p['mass_baseline']['path'])==p['mass_baseline']['sha256']
    engine = s['aircraft_a77_key_results']['binary_sha256_unchanged']
    engine_path = ROOT/'wtc1_simulation_v8/openradioss_runtime/a73_CHECK_context_candidate/isolated_exec/engine_linux64_gf_ompi'
    assert sha(engine_path)==engine
    auth = {'received_utc':now(), 'explicit_human_authorization':True,
        'answer':'bien, on reprends et on continue',
        'context':'Direct reply after A79 proposal, bounded observation explained and pending authorization stated; continue that concrete next action.',
        'proposal':rel(proposal), 'proposal_sha256':sha(proposal), 'plan_sha256':sha(PLAN),
        'scope_review_sha256':sha(scope), 'maximum_Starter':1, 'maximum_Engine':0,
        'CPU_threads':1, 'cap_s':180, 'GPU':False, 'software_patch':False,
        'compilation':False, 'installation':False, 'whole_dynamic_extension':False,
        'old_budgets_not_reset_or_reassigned':True}
    OUT.mkdir(); dump(AUTH,auth); dump(OUT/'authorization.json',auth); dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n, OUT/('before_'+Path(n).name))
    cfg = {**p, 'iteration':'AIRCRAFT-A79', 'declared_utc':now(), 'authorization':auth,
        'new_explicit_human_authorization_required':False,
        'unchanged_A73_binary':rel(engine_path), 'unchanged_A73_sha256':engine}
    dump(CFG,cfg); dump(OUT/'declaration_guard.json', {'created_utc':now(),'sha256':sha(CFG),'before_native':True})
    pins = {}
    for n in [77,78]:
        folder = ROOT/f'wtc1_simulation_v8/output/aircraft_a{n}'
        for row in read(folder/'artifact_manifest.json')['files']: pins[row['path']]=row
        for path in [folder/'artifact_manifest.json',folder/'publication_verification.json']:
            pins[rel(path)]={'path':rel(path),'bytes':path.stat().st_size,'sha256':sha(path)}
    dump(OUT/'preservation_before_metadata.json', {'created_utc':now(), 'files':[
        {**row,'mtime_ns_before':(ROOT/row['path']).stat().st_mtime_ns} for row in pins.values()],
        'old_failed_gates_and_budgets_preserved':True})
    print(json.dumps({'A79_declared':True,'Starter':1,'Engine':0}),flush=True)


def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    c=read(CFG)
    assert c['authorization']['explicit_human_authorization'] and sha(PLAN)==c['authorization']['plan_sha256']
    assert sha(ROOT/c['Starter_binary'])==c['Starter_sha256']
    assert sha(ROOT/c['unchanged_A73_binary'])==c['unchanged_A73_sha256']
    return c


def run():
    c=guard(); assert not list(OUT.rglob('starter_launch_declaration.json'))
    d=OUT/c['case']; assert not d.exists(); d.mkdir()
    for row in c['inputs']:
        assert sha(ROOT/row['path'])==row['sha256']
        target=d/Path(row['path']).name; shutil.copy2(ROOT/row['path'],target)
        assert sha(target)==row['sha256']
    assert len(list(d.glob('*.rad')))==1 and not list(d.glob('*_0001.rad'))
    dump(d/'starter_launch_declaration.json',{'created_utc':now(),'ordinal':1,'maximum':1,
        'counts_even_if_failure':True,'CPU_threads':1,'GPU':False,'cap_s':180,'config_sha256':sha(CFG)})
    en=env(); en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1',OPENBLAS_NUM_THREADS='1')
    argv=[str(ROOT/c['Starter_binary']),'-i',c['name']+'_0000.rad','-np','1']
    start=time.perf_counter(); code=None; timed=False
    with (d/'starter.log').open('x',encoding='utf8') as f:
        try: code=subprocess.run(argv,cwd=d,env=en,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
        except subprocess.TimeoutExpired: timed=True
    execution={'created_utc':now(),'argv':argv,'exit_code':code,'wall_s':time.perf_counter()-start,
        'timed_out':timed,'CPU_threads':1,'GPU':False,'cap_s':180,'binary_sha256':c['Starter_sha256']}
    dump(d/'starter.execution.json',execution)
    case={**c['source_original_A77_case'],'case':c['case'],'name':c['name']}
    gate=read_starter(d,case,execution,c['mass_baseline']['values'])
    dump(OUT/'native_execution_review.json', {'created_utc':now(),'new_Starter':1,'new_Engine':0,
        'Starter_remaining':0,'software_patch_compilation_GPU_installation':False,
        'whole_dynamic_extension':False,'whole_credit_s':0,'case':c['case'],
        'execution':execution,'physical_Starter_gate_pass':gate['pass'],
        'errors':gate['errors'],'warnings':gate['warnings'],
        'observation_qualification_pending':True,'no_Engine_input_or_launch':True})
    print(json.dumps({'A79_native_finished':True,'exit':code,'wall_s':execution['wall_s'],
        'errors':gate['errors'],'warnings':gate['warnings'],'physical_gate':gate['pass'],'new_Engine':0}),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run'])
    globals()[p.parse_args().action]()
