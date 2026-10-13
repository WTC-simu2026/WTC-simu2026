"""Fresh bounded qualification of the exact new A54 Engine; cached old outputs stay immutable."""
from build_aircraft_a54_graph import ROOT,OUT,CFG,read,dump,sha,now,rel,linux,guard
from pathlib import Path
import argparse
import json
import re
import shlex
import shutil
import subprocess
import time

RUNTIME=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'


def engine():
    config=guard(); built=read(OUT/'build_finished.json'); assert built['build_success']
    candidate=ROOT/built['candidate_directory']; binary=candidate/'isolated_exec/engine_linux64_gf_ompi'
    assert sha(binary)==built['binary_sha256']
    return candidate,binary


def run_native(d,name,observer=None,observer_config=None):
    candidate,binary=engine(); q=lambda p:shlex.quote(linux(p))
    script=d/'engine.launch.sh'; assert not script.exists()
    body='set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(candidate)+'\nexport RAD_CFG_PATH='+q(candidate/'hm_cfg_files')+'\n'
    if observer:
        body+='exec python3 '+q(observer)+' '+q(observer_config)+'\n'
    else:
        body+='exec '+q(binary)+' -i '+shlex.quote(name+'_0001.rad')+' > engine.log 2>&1\n'
    script.write_text(body,encoding='utf8',newline='\n')
    argv=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',linux(script)]
    start=time.perf_counter(); result=subprocess.run(argv,capture_output=True,timeout=195)
    (d/'engine.launcher.log').write_bytes(result.stdout+result.stderr)
    dump(d/'engine.execution.json',{'created_utc':now(),'argv':argv,'parent_exit_code':result.returncode,
        'wall_s':time.perf_counter()-start,'CPU_threads':1,'GPU':False,'cap_s':180,
        'binary_sha256':sha(binary),'observer':rel(observer) if observer else None})
    text=(d/'engine.log').read_text(errors='replace') if (d/'engine.log').exists() else ''
    errors=re.findall(r'(\d+) ERROR\(S\)',text)
    summary={'created_utc':now(),'parent_exit_code':result.returncode,
        'normal_termination':'NORMAL TERMINATION' in text,'CHECK_started':'BEGIN IMPLICIT MODEL CHECKING' in text,
        'CHECK_ended':'END IMPLICIT MODEL CHECKING' in text,
        'CHECK_errors':int(errors[-1]) if errors else None,
        'TYPE25_ignored':text.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),
        'TYPE2_connectivity_messages':len(re.findall(r'CONNECTIVITY BETWEEN NODES.*INTERFACE TYPE 2',text)),
        'kill_or_abort':bool(re.search(r'USERBREAK|SIGSEGV|ABORT',text,re.I))}
    dump(d/'completion_review.json',summary)
    return summary


def whole():
    engine(); target=OUT/'whole_controls_predeclaration.json'; assert not target.exists()
    symbols={line.split()[-1]:int(line.split()[0],16) for line in (OUT/'engine_symbols.txt').read_text().splitlines() if len(line.split())>=3}
    needed=['type2_kin_add_','ind_kine_k_','i2updk0_','i2updk1_']
    assert all(name in symbols for name in needed)
    original=read(ROOT/'wtc1_simulation_v8/data/aircraft_a53_write_watch_predeclaration.json')
    paired=read(ROOT/'wtc1_simulation_v8/data/aircraft_a53_predeclaration.json')
    cases=[{'id':'WHOLE_ORIGINAL_CORRECTED_GRAPH','name':original['name'],'files':original['source_files']},
           {'id':'WHOLE_PAIRED_CORRECTED_GRAPH','name':paired['name'],'files':paired['files'][:2]}]
    for case in cases:
        for row in case['files']: assert sha(ROOT/row['path'])==row['sha256']
    declaration={'created_utc':now(),'iteration':'AIRCRAFT-A54','seed':1102079,'random_draws':0,
        'cases':cases,'binary_sha256':sha(engine()[1]),'symbols':{name:symbols[name] for name in needed},
        'helper_calls_per_phase':64,'maximum_nodes':48171,'CPU_threads':1,'GPU':False,'per_process_cap_s':180,
        'old_solver_replays':0,'same_physical_states_and_Engine_cards':True,
        'graph_acceptance':'Observed helper after-state equals before-neighbor-set union input neighbor; duplicate insertion preserves count, all observed native counts equal unique neighbor cardinality.',
        'binding_acceptance':read(ROOT/'wtc1_simulation_v8/data/aircraft_a52_predeclaration.json')['acceptance'],
        'original_CHECK_errors_required':0,'TYPE25_ignored_remains_blocking':True,
        'new_whole_physical_duration_credit_s':0,'whole_insertion_ready':False}
    dump(target,declaration)
    for case in cases:
        d=OUT/case['id']; assert not d.exists(); d.mkdir()
        for row in case['files']:
            shutil.copy2(ROOT/row['path'],d/Path(row['path']).name)
            assert sha(d/Path(row['path']).name)==row['sha256']
        config=d/'instrumentation_config.json'
        dump(config,{'binary':linux(engine()[1]),'binary_sha256':sha(engine()[1]),
            'directory':linux(d),'Engine_card':case['name']+'_0001.rad',
            'symbols':declaration['symbols'],'maximum_nodes':48171,'helper_calls_per_phase':64})
        summary=run_native(d,case['name'],ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a54_graph_linux.py',config)
        print(json.dumps({'case':case['id'],**summary}),flush=True)


def coupons():
    engine(); target=OUT/'cohesive_controls_predeclaration.json'; assert not target.exists()
    baseline=read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/cached_Windows_LAW117_reference_review.json')
    inherited=read(ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json')
    cases=baseline['cached_cases']
    for row in cases:
        for entry in [row['initial_state'],row['Engine_cards']]: assert sha(ROOT/entry['path'])==entry['sha256']
    dump(target,{'created_utc':now(),'iteration':'AIRCRAFT-A54','seed':1102079,'random_draws':0,
        'cached_cases':cases,'acceptance':inherited['acceptance'],'cohesive':inherited['cohesive'],
        'binary_sha256':sha(engine()[1]),'same_inputs_and_unchanged_thresholds':True,
        'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'old_solver_replays':0,
        'physical_G_measured':False,'whole_insertion_ready':False})
    root=OUT/'cohesive_controls'; root.mkdir()
    for row in cases:
        case=row['case']; d=root/'w0'/case['id']; d.mkdir(parents=True)
        for entry in [row['initial_state'],row['Engine_cards']]: shutil.copy2(ROOT/entry['path'],d/Path(entry['path']).name)
        dump(d/'generation.json',row['cached_generation'])
        name=row['cached_generation']['name']; result=run_native(d,name)
        if result['parent_exit_code']==0 and result['normal_termination']:
            argv=[str(RUNTIME/'th_to_csv_win64.exe'),name+'T01']
            start=time.perf_counter(); converted=subprocess.run(argv,cwd=d,capture_output=True,timeout=60)
            (d/'converter.log').write_bytes(converted.stdout+converted.stderr)
            dump(d/'converter.execution.json',{'created_utc':now(),'argv':argv,'exit_code':converted.returncode,
                'wall_s':time.perf_counter()-start,'cap_s':60})
            assert converted.returncode==0 and (d/(name+'T01.csv')).exists()
        print(json.dumps({'cohesive_case':case['id'],'native_completed':result['normal_termination']}),flush=True)
    import review_aircraft_a17 as auditor
    auditor.OUT=root; auditor.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json'
    auditor.guard=lambda: engine()
    auditor.main()


def watch():
    engine(); declaration=OUT/'write_watch_predeclaration.json'; assert not declaration.exists()
    previous=read(ROOT/'wtc1_simulation_v8/data/aircraft_a53_write_watch_predeclaration.json')
    d=OUT/'WHOLE_CORRECTED_GRAPH_WRITE_WATCH'; assert not d.exists()
    symbols=read(OUT/'whole_controls_predeclaration.json')['symbols']
    config={'created_utc':now(),'iteration':'AIRCRAFT-A54','seed':1102079,'random_draws':0,
        'binary':linux(engine()[1]),'binary_sha256':sha(engine()[1]),'directory':linux(d),
        'Engine_card':previous['name']+'_0001.rad','source_files':previous['source_files'],
        'arguments':previous['arguments'],'IND_KINE_K_offset':symbols['ind_kine_k_'],
        'maximum_nodes':48171,'watched_original_node':48151,'maximum_write_events':64,
        'expected_neighbor_labels':[48154,48155,48156],
        'reason':'New helper-entry observer returned zero calls; retain that inconclusive attempt and measure the actual watched row through native return.',
        'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'old_solver_replays':0,
        'expected_semantics':'Preserve the independently observed three neighbors when TYPE2 adds only duplicates; no counter inflation or incorrect column write.',
        'observer_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a54_write_watch_linux.py')}
    # Labels are transcribed from the immutable A52 native binding capture, not internal indices.
    captured=read(ROOT/'wtc1_simulation_v8/output/aircraft_a52/WHOLE_ORIGINAL_TYPE2_BINDING_TRACE/type2_trace_result.json')
    binding=next(b for call in captured['calls'] for b in call['bindings'] if b['main_original_labels_ordered'][0]==48151)
    config['expected_neighbor_labels']=binding['main_original_labels_ordered'][1:]
    assert len(config['expected_neighbor_labels'])==3
    dump(declaration,config);d.mkdir()
    for row in previous['source_files']:
        assert sha(ROOT/row['path'])==row['sha256'];shutil.copy2(ROOT/row['path'],d/Path(row['path']).name)
    instrument=d/'instrumentation_config.json';dump(instrument,config)
    summary=run_native(d,previous['name'],ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a54_write_watch_linux.py',instrument)
    print(json.dumps(summary),flush=True)


def optimized():
    candidate,binary=engine();declaration=OUT/'optimized_add_predeclaration.json';assert not declaration.exists()
    previous=read(ROOT/'wtc1_simulation_v8/data/aircraft_a53_write_watch_predeclaration.json')
    symbols={line.split()[-1]:int(line.split()[0],16) for line in (OUT/'engine_symbols.txt').read_text().splitlines() if len(line.split())>=3}
    names=['type2_kin_add_.constprop.0.isra.0','type2_kin_add_.constprop.1.isra.0']
    disassembly=[]
    for index,name in enumerate(names):
        assert name in symbols
        result=subprocess.run(['wsl.exe','-d','Ubuntu','--','objdump','-d','--disassemble='+name,linux(binary)],capture_output=True,check=True,timeout=30)
        path=OUT/('optimized_add_clone_'+str(index)+'.disassembly.txt');path.write_bytes(result.stdout)
        disassembly.append({'path':rel(path),'sha256':sha(path),'symbol':name,'offset':symbols[name]})
    d=OUT/'WHOLE_OPTIMIZED_GRAPH_SET_TRACE';assert not d.exists()
    config={'created_utc':now(),'iteration':'AIRCRAFT-A54','seed':1102079,'random_draws':0,
        'binary':linux(binary),'binary_sha256':sha(binary),'directory':linux(d),
        'Engine_card':previous['name']+'_0001.rad','source_files':previous['source_files'],
        'sizing_clone_offset':symbols[names[0]],'building_clone_offset':symbols[names[1]],
        'compiled_ABI':'row,node,NNMAX,NKMAX,bound by value in edi,esi,edx,ecx,r8d; NROW pointer r9; ICOK and ICOKM pointers at rsp+8,+16.',
        'ABI_evidence':disassembly,'calls_per_phase':128,'maximum_nodes':48171,
        'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'old_solver_replays':0,
        'criterion':'Actual after-set equals before-set union actual input neighbor, no duplicates, count equals set cardinality, duplicate leaves count unchanged.',
        'scope':'New per-operation independent oracle. Previous unjustified full-row three-neighbor expectation and failed gate remain preserved; this test permits other actual native input neighbors without assuming their total.'}
    dump(declaration,config);d.mkdir()
    for row in previous['source_files']:
        assert sha(ROOT/row['path'])==row['sha256'];shutil.copy2(ROOT/row['path'],d/Path(row['path']).name)
    instrument=d/'instrumentation_config.json';dump(instrument,config)
    print(json.dumps(run_native(d,previous['name'],ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a54_optimized_add_linux.py',instrument)),flush=True)


def contact():
    engine();declaration=OUT/'contact_controls_predeclaration.json';assert not declaration.exists()
    inherited=read(ROOT/'wtc1_simulation_v8/data/aircraft_a45_contact_predeclaration.json')
    for row in inherited['cases']:
        for entry in row['inputs']:assert sha(ROOT/entry['path'])==entry['sha256']
    dump(declaration,{'created_utc':now(),'iteration':'AIRCRAFT-A54','seed':1102079,'random_draws':0,
        'cases':inherited['cases'],'acceptance':inherited['acceptance'],
        'binary_sha256':sha(engine()[1]),'same_inputs_and_unchanged_thresholds':True,
        'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'old_solver_replays':0,
        'scope':'Independent inherited TYPE7/MUMPS witness only; whole TYPE25 is unchanged and still unsupported.'})
    root=OUT/'contact_controls';root.mkdir()
    import probe_aircraft_a37 as auditor
    import read_aircraft_a41_newmark as reader
    auditor.OUT=root;auditor.CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a41_predeclaration.json';auditor.guard=lambda:engine()
    reader.OUT=root
    rows=[]
    for row in inherited['cases']:
        case=row['case'];d=root/case['name'];p=d/'phase1';p.mkdir(parents=True)
        for entry in row['inputs']:
            source=ROOT/entry['path'];target=d/'generation.json' if source.name=='generation.json' else p/source.name
            shutil.copy2(source,target);assert sha(target)==entry['sha256']
        generation=read(d/'generation.json');completed=run_native(p,generation['name'])
        if completed['parent_exit_code']==0 and completed['normal_termination']:
            dump(d/'run_completed.json',{'created_utc':now(),'pass':True,'new_binary_sha256':sha(engine()[1])})
            auditor.audit_case(case);rows.append(reader.review(case,True))
        else:rows.append({'case':case['name'],'pass':False,'reason':'Native Engine incomplete'})
        print(json.dumps({'contact_case':case['name'],'pass':rows[-1]['pass']}),flush=True)
    import numpy as np
    comparison=[]
    if all(row['pass'] for row in rows):
        histories=[auditor.histories(next((root/row['case']['name']/'phase1').glob('*.csv'))) for row in inherited['cases']]
        tt=histories[0]['time'];tt=tt[tt<=min(h['time'][-1] for h in histories)]
        K0=read(root/inherited['cases'][0]['case']['name']/'generation.json')['kinetic_energy_J']
        tolerance=inherited['acceptance']['half_dt_energy_relative']*K0+inherited['acceptance']['comparison_energy_absolute_J']
        for key in ['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']:
            values=[np.interp(tt,h['time'],h[key])*.001 for h in histories]
            error=float(abs(values[0]-values[1]).max())
            comparison.append({'channel':key,'maximum_difference_J':error,'tolerance_J':tolerance,'pass':error<tolerance})
    dump(root/'contact_review.json',{'created_utc':now(),'cases':rows,'time_step_comparison':comparison,
        'pass':len(rows)==2 and all(row['pass'] for row in rows) and bool(comparison) and all(row['pass'] for row in comparison),
        'whole_TYPE25_qualified':False,'whole_impact_qualified':False,'new_whole_physical_duration_credit_s':0})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['whole','coupons','watch','optimized','contact'])
    globals()[p.parse_args().action]()
