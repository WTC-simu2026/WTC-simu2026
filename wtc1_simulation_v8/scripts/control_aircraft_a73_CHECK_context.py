"""Six approved A73 Engine controls; zero Starter, bounded read-only global observations."""
from build_aircraft_a73_CHECK_context import ROOT,OUT,CFG,read,dump,sha,now,guard as build_guard,CAND
from build_aircraft_a54_graph import rel,linux
from pathlib import Path
import json,re,subprocess,shutil,time,ast
import probe_aircraft_a54 as launcher

CONTROL=ROOT/'wtc1_simulation_v8/data/aircraft_a73_controls.json'
OBSERVER=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a73_context_linux.py'
RUNTIME=launcher.RUNTIME


def engine():
    build_guard(); b=read(OUT/'build_finished.json')
    assert b['build_success'] and b['exact_A72_CHECK_context_applied']
    candidate=ROOT/b['candidate_directory'];binary=candidate/'isolated_exec/engine_linux64_gf_ompi'
    assert sha(binary)==b['binary_sha256'];return candidate,binary


def declare():
    candidate,binary=engine();assert not CONTROL.exists()
    config=read(CFG);contract=config['control_contract'];obs_contract=config['observer_contract']
    assert rel(OBSERVER)==obs_contract['prepared_observer'] and sha(OBSERVER)==obs_contract['prepared_observer_sha256']
    ast.parse(OBSERVER.read_text(encoding='utf8'))
    r=subprocess.run(['wsl','-d','Ubuntu','--exec','nm','-S',linux(binary)],capture_output=True,text=True,timeout=25)
    assert r.returncode==0;symbols={};globals_={}
    functions=['imp_check0_','imp_checm0_','imp_chkm_','lin_solv_','produt_w_']
    global_names={d['symbol'] for d in contract['observe_native_globals'].values()}
    for line in r.stdout.splitlines():
        m=re.match(r'([0-9a-f]+) ([0-9a-f]+) ([A-Za-z]) (\w+)$',line)
        if not m:continue
        if m[4] in functions:
            assert m[3] in 'Tt';symbols[m[4]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
        if m[4] in global_names:
            assert m[3] in 'BbDd';globals_[m[4]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
    assert len(symbols)==5 and set(globals_)==global_names
    for label,d in contract['observe_native_globals'].items():
        width={'i32':4,'f64':8}[d['kind']]
        assert 0<=d['byte_offset'] and d['byte_offset']+width<=globals_[d['symbol']]['bytes']
        assert obs_contract['native_globals'][label]==d
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json')
    free={**old['cases'][0],'id':'FREE_DYNAMIC_REGRESSION'}
    for case in contract['cases']:
        assert not case['new_Starter']
        for row in case['inputs']:
            assert sha(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
    cfg={'created_utc':now(),'iteration':'AIRCRAFT-A73','seed':1102098,'random_draws':0,
        'cases':contract['cases'],'binary_sha256':sha(binary),'symbols':symbols,'global_symbols':globals_,
        'native_globals':contract['observe_native_globals'],'observer':rel(OBSERVER),'observer_sha256':sha(OBSERVER),
        'cohesive':old['cohesive'],'acceptance':old['acceptance'],'free_case':free,
        'extra_analytical_displacement_tolerance_mm':old['extra_analytical_displacement_tolerance_mm'],
        'extra_analytical_velocity_tolerance_mm_ms':old['extra_analytical_velocity_tolerance_mm_ms'],
        'maximum_Engine':6,'maximum_Starter':0,'CPU_threads':1,'each_cap_s':180,'GPU':False,
        'whole_dynamic_extension':False,'all_prior_budgets_not_reset':True,
        'global_symbol_sizes_and_pinned_typed_offsets_guarded':True,
        'additional_breakpoints_processes_or_native_data_writes':False}
    dump(CONTROL,cfg)
    dump(OUT/'controls_guard.json',{'created_utc':now(),'sha256':sha(CONTROL),'before_any_native':True})
    dump(OUT/'global_symbol_review.json',{'created_utc':now(),'pass':True,'binary_sha256':sha(binary),
        'global_symbols':globals_,'typed_fields':contract['observe_native_globals'],
        'symbols_from_new_A73_binary':True,'native_values_not_yet_observed':True})
    print(json.dumps({'A73_controls_declared':6,'maximum_Starter':0,'new_binary_global_ranges_guarded':True,'no_native_started':True}),flush=True)


def control_guard():
    engine();assert sha(CONTROL)==read(OUT/'controls_guard.json')['sha256'];c=read(CONTROL)
    assert sha(OBSERVER)==c['observer_sha256'];return c


def run():
    c=control_guard();assert not list(OUT.rglob('native_launch_declaration.json'));results=[]
    assert not list(OUT.rglob('starter.execution.json'))
    launcher.engine=engine
    for idx,case in enumerate(c['cases'],1):
        control_guard();assert idx<=6 and idx==len(list(OUT.rglob('native_launch_declaration.json')))+1
        assert not case['new_Starter']
        dynamic=case['case']=='FREE_DYNAMIC_REGRESSION'
        d=(OUT/'native'/case['case']) if dynamic else OUT/case['case']
        assert not d.exists();d.mkdir(parents=True)
        for row in case['inputs']:
            assert sha(ROOT/row['path'])==row['sha256']
            dest=d/Path(row['path']).name;shutil.copy2(ROOT/row['path'],dest)
            assert sha(dest)==row['sha256']
        name=case['name'];observer_cfg=None
        if not dynamic:
            node_count=48171 if case['case'].startswith('WHOLE_') else 8
            observer_cfg=d/'instrumentation_config.json'
            dump(observer_cfg,{'binary':linux(engine()[1]),'binary_sha256':c['binary_sha256'],
                'directory':linux(d),'Engine_card':name+'_0001.rad','symbols':c['symbols'],
                'global_symbols':c['global_symbols'],'native_globals':c['native_globals'],
                'node_count':node_count,'CPU_threads':1,'cap_s':180,'new_A73_explicit_human_consent':True})
        else:
            generation=read(ROOT/'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4/generation.json')
            dump(d/'generation.json',{**generation,'name':name,'case':c['free_case'],
                'current_iteration':'AIRCRAFT-A73','new_binary_sha256':c['binary_sha256'],'same_cached_physics_and_cards':True})
        dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':idx,'maximum':6,
            'CPU_threads':1,'GPU':False,'cap_s':180,'counts_even_if_failure':True,
            'control_sha256':sha(CONTROL),'binary_sha256':c['binary_sha256'],'whole_duration_credit_s':0})
        initial=launcher.run_native(d,name,None if dynamic else OBSERVER,observer_cfg)
        listing=d/(name+'_0001.out');s=listing.read_text(encoding='utf8',errors='replace') if listing.exists() else ''
        log=(d/'engine.log').read_text(encoding='utf8',errors='replace')
        errors=re.findall(r'\b(\d+)\s+ERRORS\b',log);warnings=re.findall(r'\b(\d+)\s+WARNINGS\b',log)
        row={'case':case['case'],**initial,'printed_errors':int(errors[-1]) if errors else None,
            'printed_warnings':int(warnings[-1]) if warnings else None,
            'loading_errors':s.count('** ERROR :IMPLICIT LOADING DATA **'),
            'initial_zero_dynamic_INFO':s.count('** INITIAL DYNAMIC RESIDUAL IS ZERO **'),
            'whole_qualified':False,'whole_credit_s':0}
        if not dynamic:
            obs=read(d/'check_observation.json') if (d/'check_observation.json').exists() else None
            row['observation_complete']=bool(obs and obs['observation_complete'])
            r2=[e['native_R2'] for e in obs['events'] if 'native_R2' in e] if obs else []
            contexts=[e['native_CHECK_context'] for e in obs['events'] if 'native_CHECK_context' in e] if obs else []
            row['native_R2']=r2[0] if len(r2)==1 else None
            row['native_CHECK_context']=contexts[0] if len(contexts)==1 else None
            row['context_observation_complete']=len(contexts)==1 and set(contexts[0])==set(c['native_globals'])
        if dynamic and initial['parent_exit_code']==0 and initial['normal_termination']:
            start=time.perf_counter()
            conv=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60)
            (d/'converter.log').write_bytes(conv.stdout+conv.stderr)
            dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':conv.returncode,'wall_s':time.perf_counter()-start,'cap_s':60})
            assert conv.returncode==0
        dump(d/'actual_message_review.json',row);results.append(row);print(json.dumps(row),flush=True)
        assert initial['parent_exit_code']==0 and initial['normal_termination'] and (dynamic or
            row['observation_complete'] and row['context_observation_complete']), 'Incomplete native control retained; stop, no unbudgeted retry'
    dump(OUT/'native_execution_review.json',{'created_utc':now(),'cases':results,'new_Engine':6,'new_Starter':0,
        'remaining_Engine':0,'remaining_Starter':0,'whole_dynamic_extension':False,'whole_credit_s':0})


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['declare','run'])
    globals()[parser.parse_args().action]()
