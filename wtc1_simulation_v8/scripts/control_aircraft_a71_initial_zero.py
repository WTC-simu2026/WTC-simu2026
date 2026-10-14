"""Six authorized new-binary controls and exactly one Starter, no whole dynamic extension."""
from build_aircraft_a71_initial_zero import ROOT,OUT,CFG,read,dump,sha,now,guard as build_guard,CAND
from build_aircraft_a54_graph import rel,linux
from pathlib import Path
import json,re,subprocess,shutil,time,ast
import probe_aircraft_a54 as launcher

CONTROL=ROOT/'wtc1_simulation_v8/data/aircraft_a71_controls.json'
OBSERVER=ROOT/'wtc1_simulation_v8/scripts/observe_aircraft_a71_check_linux.py'
RUNTIME=launcher.RUNTIME

def engine():
    build_guard();b=read(OUT/'build_finished.json');assert b['build_success'] and b['exact_A70_R4_CHECK_policy_applied']
    candidate=ROOT/b['candidate_directory'];binary=candidate/'isolated_exec/engine_linux64_gf_ompi';assert sha(binary)==b['binary_sha256'];return candidate,binary

def declare():
    candidate,binary=engine();assert not CONTROL.exists() and not OBSERVER.exists();contract=read(CFG)['control_contract']
    inherited=ROOT/contract['native_READ_observer'];assert sha(inherited)==contract['native_READ_observer_sha256']
    code=inherited.read_text(encoding='utf8').replace("new_A69_explicit_human_consent","new_A71_explicit_human_consent").replace("'loading_source_accepts'","'loading_positive_only_gate'")
    ast.parse(code);OBSERVER.write_text(code,encoding='utf8',newline='\n')
    r=subprocess.run(['wsl','-d','Ubuntu','--exec','nm','-S',linux(binary)],capture_output=True,text=True,timeout=25);assert r.returncode==0;symbols={}
    for l in r.stdout.splitlines():
        m=re.match(r'([0-9a-f]+) ([0-9a-f]+) [Tt] (\w+)$',l)
        if m and m[3] in ['imp_check0_','imp_checm0_','imp_chkm_','lin_solv_','produt_w_']:symbols[m[3]]={'offset':int(m[1],16),'bytes':int(m[2],16)}
    assert len(symbols)==5
    old=read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json');free={**old['cases'][0],'id':'FREE_DYNAMIC_REGRESSION'}
    cfg={'created_utc':now(),'iteration':'AIRCRAFT-A71','seed':1102096,'random_draws':0,'cases':contract['cases'],'binary_sha256':sha(binary),
        'symbols':symbols,'observer':rel(OBSERVER),'observer_sha256':sha(OBSERVER),'cohesive':old['cohesive'],'acceptance':old['acceptance'],
        'free_case':free,'extra_analytical_displacement_tolerance_mm':old['extra_analytical_displacement_tolerance_mm'],
        'extra_analytical_velocity_tolerance_mm_ms':old['extra_analytical_velocity_tolerance_mm_ms'],
        'maximum_Engine':6,'maximum_Starter':1,'CPU_threads':1,'each_cap_s':180,'GPU':False,'whole_dynamic_extension':False,
        'positive_only_source_field_in_old_observer_renamed_for_new_policy_clarity':True,'all_prior_budgets_not_reset':True}
    dump(CONTROL,cfg);dump(OUT/'controls_guard.json',{'created_utc':now(),'sha256':sha(CONTROL),'before_any_native':True})
    dump(OUT/'observer_derivation.json',{'created_utc':now(),'inherited':rel(inherited),'inherited_sha256':sha(inherited),'derived':rel(OBSERVER),
        'derived_sha256':sha(OBSERVER),'changes':'Own observer labels only: bind A71 consent flag and rename positive-only mathematical test; hardware ABI/memory/control logic unchanged.',
        'third_party_Engine_changes_beyond_approved_four_lines':False})
    print(json.dumps({'A71_controls_declared':6,'maximum_Starter':1,'no_native_started':True}),flush=True)

def control_guard():
    engine();assert sha(CONTROL)==read(OUT/'controls_guard.json')['sha256'];c=read(CONTROL)
    assert sha(OBSERVER)==c['observer_sha256'];return c

def start_loaded(d,name):
    assert len(list(OUT.rglob('starter_launch_declaration.json')))==0
    dump(d/'starter_launch_declaration.json',{'created_utc':now(),'ordinal':1,'maximum':1,'cap_s':180,'CPU_threads':1})
    from run_aircraft_a17 import env
    exe=RUNTIME/'starter_win64.exe';args=[str(exe),'-i',name+'_0000.rad','-np','1'];start=time.perf_counter()
    with (d/'starter.log').open('x',encoding='utf8') as f:v=subprocess.run(args,cwd=d,env=env(),stdout=f,stderr=subprocess.STDOUT,timeout=180)
    dump(d/'starter.execution.json',{'created_utc':now(),'exit_code':v.returncode,'wall_s':time.perf_counter()-start,'cap_s':180,'CPU_threads':1,'GPU':False,'binary_sha256':sha(exe)})
    log=(d/'starter.log').read_text(encoding='utf8',errors='replace');errors=re.findall(r'(\d+) ERROR\(S\)',log);warnings=re.findall(r'(\d+) WARNING\(S\)',log)
    assert v.returncode==0 and errors and warnings and int(errors[-1])==int(warnings[-1])==0
    assert (d/(name+'_0000_0001.rst')).exists()

def run():
    c=control_guard();assert not list(OUT.rglob('native_launch_declaration.json'));results=[]
    launcher.engine=engine
    for idx,case in enumerate(c['cases'],1):
        control_guard();assert idx<=6 and idx==len(list(OUT.rglob('native_launch_declaration.json')))+1
        dynamic=case['case']=='FREE_DYNAMIC_REGRESSION';d=(OUT/'native'/case['case']) if dynamic else OUT/case['case'];assert not d.exists();d.mkdir(parents=True)
        for row in case['inputs']:
            assert sha(ROOT/row['path'])==row['sha256'];dest=d/Path(row['path']).name;shutil.copy2(ROOT/row['path'],dest);assert sha(dest)==row['sha256']
        name=case['name']
        if case['new_Starter']:start_loaded(d,name)
        observer_cfg=None
        if not dynamic:
            if case['case'].startswith('WHOLE_'):node_count=48171
            else:node_count=8
            observer_cfg=d/'instrumentation_config.json';dump(observer_cfg,{'binary':linux(engine()[1]),'binary_sha256':c['binary_sha256'],'directory':linux(d),
                'Engine_card':name+'_0001.rad','symbols':c['symbols'],'node_count':node_count,'CPU_threads':1,'cap_s':180,'new_A71_explicit_human_consent':True})
        else:
            generation=read(ROOT/'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4/generation.json')
            dump(d/'generation.json',{**generation,'name':name,'case':c['free_case'],'current_iteration':'AIRCRAFT-A71','new_binary_sha256':c['binary_sha256'],'same_cached_physics_and_cards':True})
        dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':idx,'maximum':6,'CPU_threads':1,'GPU':False,'cap_s':180,
            'counts_even_if_failure':True,'control_sha256':sha(CONTROL),'binary_sha256':c['binary_sha256'],'whole_duration_credit_s':0})
        initial=launcher.run_native(d,name,None if dynamic else OBSERVER,observer_cfg)
        listing=d/(name+'_0001.out');s=listing.read_text(encoding='utf8',errors='replace') if listing.exists() else ''
        log=(d/'engine.log').read_text(encoding='utf8',errors='replace');errors=re.findall(r'\b(\d+)\s+ERRORS\b',log);warnings=re.findall(r'\b(\d+)\s+WARNINGS\b',log)
        row={'case':case['case'],**initial,'printed_errors':int(errors[-1]) if errors else None,'printed_warnings':int(warnings[-1]) if warnings else None,
            'loading_errors':s.count('** ERROR :IMPLICIT LOADING DATA **'),'initial_zero_dynamic_INFO':s.count('** INITIAL DYNAMIC RESIDUAL IS ZERO **'),
            'whole_qualified':False,'whole_credit_s':0}
        if not dynamic:
            obs=read(d/'check_observation.json') if (d/'check_observation.json').exists() else None
            row['observation_complete']=bool(obs and obs['observation_complete']);row['native_R2']=[e['native_R2'] for e in obs['events'] if 'native_R2' in e][0] if obs and obs['observation_complete'] else None
        if dynamic and initial['parent_exit_code']==0 and initial['normal_termination']:
            start=time.perf_counter();conv=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60)
            (d/'converter.log').write_bytes(conv.stdout+conv.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':conv.returncode,'wall_s':time.perf_counter()-start,'cap_s':60});assert conv.returncode==0
        dump(d/'actual_message_review.json',row);results.append(row);print(json.dumps(row),flush=True)
        assert initial['parent_exit_code']==0 and initial['normal_termination'] and (dynamic or row['observation_complete']),'Stop on incomplete execution/observation; preserve failed control, no unbudgeted retry'
    dump(OUT/'native_execution_review.json',{'created_utc':now(),'cases':results,'new_Engine':6,'new_Starter':1,'remaining_Engine':0,'remaining_Starter':0,
        'whole_dynamic_extension':False,'whole_credit_s':0})

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
