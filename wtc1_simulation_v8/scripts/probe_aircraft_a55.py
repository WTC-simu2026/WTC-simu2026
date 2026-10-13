"""Independent isolated LAW117 implicit/geometry qualification with the unchanged A54 Engine."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import argparse,json,shutil,subprocess,time,traceback
import probe_aircraft_a54 as launcher

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a55'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a55_predeclaration.json'
A54=ROOT/'wtc1_simulation_v8/output/aircraft_a54'


def engine():
    config=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A54'
    candidate=ROOT/config['candidate_directory'];binary=candidate/'isolated_exec/engine_linux64_gf_ompi'
    assert sha(binary)==config['binary_sha256']
    return candidate,binary


def declare():
    assert not OUT.exists() and not CFG.exists()
    h=harness();assert h['CurrentIteration']=='AIRCRAFT-A54' and h['NextIteration']=='AIRCRAFT-A55'
    assert read(A54/'publication_verification.json')['pass']
    baseline=read(ROOT/'wtc1_simulation_v8/output/aircraft_a44/cached_Windows_LAW117_reference_review.json')
    solid=read(ROOT/'wtc1_simulation_v8/data/aircraft_a45_contact_predeclaration.json')['cases'][0]
    for row in baseline['cached_cases']:
        for entry in [row['initial_state'],row['Engine_cards']]:assert sha(ROOT/entry['path'])==entry['sha256']
    for entry in solid['inputs']:assert sha(ROOT/entry['path'])==entry['sha256']
    built=read(A54/'build_finished.json'); inherited=read(ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json')
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    config={'created_utc':now(),'iteration':'AIRCRAFT-A55','seed':1102080,'random_draws':0,
        'purpose':'Separate generic solid-volume CHECK from zero-height cohesive surface behavior, and test actual loaded LAW117 implicit dynamics before any whole insertion.',
        'candidate_directory':built['candidate_directory'],'binary_sha256':built['binary_sha256'],
        'cohesive':inherited['cohesive'],'acceptance':inherited['acceptance'],'witness':inherited['witness'],
        'cohesive_cases':baseline['cached_cases'],'positive_volume_control':solid,
        'numerical_controls':{'solver':2,'Newmark_gamma_beta':[.5,.25],'nonlinear_tolerances':[1e-11]*3,
            'linear_tolerance':1e-8,'reference_force_min_N':1,'reference_force_max_N':1e30,
            'fixed_time_step_ms':'same as each explicit witness dt_cap_ms','minimum_dt_ms':1e-12,'no_adaptive_growth':True},
        'units':{'input':['g','mm','ms'],'Nmm_to_J':.001,'physical_witness_end_ms':1},
        'execution':{'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_minutes':[1,5],'maximum_native_processes':6},
        'CHECK_cases':['one zero-height LAW117 surface','two ordinary positive-volume LAW2 cubes with known TYPE7 contact'],
        'dynamic_cases':[row['case']['id'] for row in baseline['cached_cases']],
        'physical_input_state_motion_material_mass_geometry_unchanged':True,
        'mechanical_acceptance_thresholds_unchanged':True,'old_native_solver_replays':0,
        'new_installation_or_compilation':False,'new_software_source_patch':False,
        'new_whole_physical_duration_credit_s':0,'whole_TYPE25_qualified':False,
        'whole_insertion_ready':False,'objective1_complete':False,'target_physical_s':10,
        'best_whole_physical_s':.0200001220703125}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_native':True})
    previous=read(A54/'preservation_before_metadata.json');pins={row['path']:row for row in previous['files']}
    for row in read(A54/'artifact_manifest.json')['files']:pins[row['path']]=row
    for path in [A54/'artifact_manifest.json',A54/'publication_verification.json']:
        pins[rel(path)]={'path':rel(path),'bytes':path.stat().st_size,'sha256':sha(path)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_immutable_hashes_retained':True})
    print(json.dumps({'A55_declared':True,'new_native_checks':2,'new_loaded_implicit_cases':4,'cap_s_each':180}),flush=True)


def cards(name,dt,check=False):
    f=lambda *values:''.join(f'{value:20.12g}' for value in values)
    i=lambda *values:''.join(f'{value:10d}' for value in values)
    rows=['/IMPL/RREF/LIMIT',f(1,1e30),'/IMPL/NONLIN/1','0 123 1e-11 1e-11 1e-11',
        '/IMPL/SOLVER/2',i(2,0,1)+f(1e-8),'/IMPL/DTINI',f(dt),'/IMPL/DYNA/2',f(.5,.25),
        '/IMPL/DT/1',i(2)+f(1)+i(30)+f(.5),'/IMPL/DT/STOP',f(1e-12,dt)]
    if check:rows+=['/IMPL/CHECK']
    else:rows+=['/ANIM/DT',f(0,.005),'/ANIM/VECT/DISP','/ANIM/VECT/VEL',
        '/ANIM/BRICK/TENS/STRESS','/ANIM/ELEM/ENER','/MON/ON']
    rows+=['/PRINT/-100/100',f'/RUN/{name}/1',f(1),'/TFILE/4',f(.0001),'/VERS/2026']
    return '\n'.join(rows)+'\n'


def run_case(d,name):
    launcher.engine=engine
    return launcher.run_native(d,name)


def checking():
    engine();config=read(CFG)
    zero=config['cohesive_cases'][0];solid=config['positive_volume_control']
    cases=[('CHECK_ZERO_HEIGHT_LAW117',zero['cached_generation']['name'],zero['initial_state']),
        ('CHECK_POSITIVE_VOLUME_SOLIDS',Path(solid['inputs'][1]['path']).name.removesuffix('_0000_0001.rst'),solid['inputs'][1])]
    for identifier,name,state in cases:
        d=OUT/identifier;assert not d.exists();d.mkdir()
        assert sha(ROOT/state['path'])==state['sha256'];shutil.copy2(ROOT/state['path'],d/Path(state['path']).name)
        (d/(name+'_0001.rad')).write_text(cards(name,.000025,True),encoding='utf8')
        dump(d/'generation.json',{'created_utc':now(),'name':name,'same_initial_state':state,'CHECK_only':True,'configuration_sha256':sha(CFG)})
        print(json.dumps({'case':identifier,**run_case(d,name)}),flush=True)


def dynamics():
    engine();root=OUT/'implicit_cohesive_controls';assert not root.exists();root.mkdir()
    results=[]
    for row in read(CFG)['cohesive_cases']:
        case=row['case'];d=root/'w0'/case['id'];d.mkdir(parents=True);name=row['cached_generation']['name']
        entry=row['initial_state'];assert sha(ROOT/entry['path'])==entry['sha256'];shutil.copy2(ROOT/entry['path'],d/Path(entry['path']).name)
        (d/(name+'_0001.rad')).write_text(cards(name,case['dt_cap_ms']),encoding='utf8')
        dump(d/'generation.json',{**row['cached_generation'],'new_implicit_cards':True,'A55_configuration_sha256':sha(CFG)})
        try:
            result=run_case(d,name)
            if result['parent_exit_code']==0 and result['normal_termination']:
                runtime=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64/th_to_csv_win64.exe'
                start=time.perf_counter();converted=subprocess.run([str(runtime),name+'T01'],cwd=d,capture_output=True,timeout=60)
                (d/'converter.log').write_bytes(converted.stdout+converted.stderr)
                dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':converted.returncode,'wall_s':time.perf_counter()-start,'cap_s':60})
                assert converted.returncode==0 and (d/(name+'T01.csv')).exists()
            results.append({'case':case,'native_completed':result['normal_termination'],'parent_exit_code':result['parent_exit_code']})
        except Exception as exc:
            dump(d/'retained_pipeline_failure.json',{'created_utc':now(),'error':str(exc),'traceback':traceback.format_exc()})
            results.append({'case':case,'native_completed':False,'analysis_exception':str(exc)})
        print(json.dumps(results[-1]),flush=True)
    dump(root/'execution_review.json',{'created_utc':now(),'cases':results,'all_native_completed':all(row['native_completed'] for row in results)})


def review():
    engine();root=OUT/'implicit_cohesive_controls'
    if read(root/'execution_review.json')['all_native_completed']:
        import review_aircraft_a17 as auditor
        auditor.OUT=root;auditor.CFG=CFG;auditor.guard=lambda:engine()
        try:auditor.main()
        except Exception as exc:dump(root/'retained_review_failure.json',{'created_utc':now(),'error':str(exc),'traceback':traceback.format_exc(),'raw_outputs_preserved':True})
    else:print('Native implicit cohesive campaign incomplete; no mechanical pass inferred.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','checking','dynamics','review']);globals()[p.parse_args().action]()
