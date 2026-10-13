"""Fresh physical/geometry controls on the approved scratch Engine, unchanged gates."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import build_aircraft_a57_original_scratch as build
import probe_aircraft_a54 as launcher
from probe_aircraft_a55 import cards
from pathlib import Path
import argparse,json,shutil,subprocess,time,traceback,re

OUT=build.OUT
CFG=build.CFG

def engine():
    build.guard();b=read(OUT/'build_finished.json');assert b['build_success']
    p=ROOT/b['candidate_directory'];binary=p/'isolated_exec/engine_linux64_gf_ompi';assert sha(binary)==b['binary_sha256'];return p,binary

def run(d,name):
    launcher.engine=engine;return launcher.run_native(d,name)

def checking():
    engine();inherited=read(ROOT/'wtc1_simulation_v8/data/aircraft_a55_predeclaration.json')
    zero=inherited['cohesive_cases'][0];solid=inherited['positive_volume_control']
    cases=[('CHECK_ZERO_HEIGHT_LAW117',zero['cached_generation']['name'],zero['initial_state']),
      ('CHECK_POSITIVE_VOLUME_SOLIDS',Path(solid['inputs'][1]['path']).name.removesuffix('_0000_0001.rst'),solid['inputs'][1])]
    dump(OUT/'geometry_controls_predeclaration.json',{'created_utc':now(),'iteration':'AIRCRAFT-A57','seed':1102082,'random_draws':0,'same_A55_initial_states':cases,'binary_sha256':sha(engine()[1]),'clean_CHECK_required_errors':0,'cap_s':180,'CPU':1,'GPU':False})
    for identifier,name,state in cases:
        d=OUT/identifier;assert not d.exists();d.mkdir();assert sha(ROOT/state['path'])==state['sha256']
        shutil.copy2(ROOT/state['path'],d/Path(state['path']).name)
        (d/(name+'_0001.rad')).write_text(cards(name,.000025,True),encoding='utf8')
        dump(d/'generation.json',{'created_utc':now(),'name':name,'same_initial_state':state,'CHECK_only':True,'configuration_sha256':sha(CFG)})
        print(json.dumps({'case':identifier,**run(d,name)}),flush=True)

def dynamics():
    engine();inherited=read(ROOT/'wtc1_simulation_v8/data/aircraft_a55_predeclaration.json')
    cfg=OUT/'implicit_cohesive_controls_predeclaration.json'
    dump(cfg,{**inherited,'created_utc':now(),'iteration':'AIRCRAFT-A57','seed':1102082,'binary_sha256':sha(engine()[1]),'same_A55_physical_initial_states':True,'new_software_source_patch':True,'loaded_physical_response_not_yet_qualified':True})
    target=OUT/'implicit_cohesive_controls';assert not target.exists();target.mkdir();results=[]
    for row in inherited['cohesive_cases']:
        case=row['case'];d=target/'w0'/case['id'];d.mkdir(parents=True);name=row['cached_generation']['name'];entry=row['initial_state']
        assert sha(ROOT/entry['path'])==entry['sha256'];shutil.copy2(ROOT/entry['path'],d/Path(entry['path']).name)
        (d/(name+'_0001.rad')).write_text(cards(name,case['dt_cap_ms']),encoding='utf8')
        dump(d/'generation.json',{**row['cached_generation'],'new_implicit_cards':True,'configuration_sha256':sha(CFG)})
        result=run(d,name)
        if result['parent_exit_code']==0 and result['normal_termination']:
            started=time.perf_counter();conversion=subprocess.run([str(launcher.RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60)
            (d/'converter.log').write_bytes(conversion.stdout+conversion.stderr)
            dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':conversion.returncode,'wall_s':time.perf_counter()-started,'cap_s':60})
        results.append({'case':case,'normal_termination':result['normal_termination'],'parent_exit_code':result['parent_exit_code']})
        print(json.dumps(results[-1]),flush=True)
    dump(target/'execution_review.json',{'created_utc':now(),'cases':results,'all_native_completed':all(row['normal_termination'] and row['parent_exit_code']==0 for row in results)})

def review():
    engine();target=OUT/'implicit_cohesive_controls'
    if not read(target/'execution_review.json')['all_native_completed']:
        print('Implicit loaded response incomplete; no physical pass inferred.',flush=True);return
    import review_aircraft_a17 as auditor
    auditor.OUT=target;auditor.CFG=OUT/'implicit_cohesive_controls_predeclaration.json';auditor.guard=engine
    try:auditor.main()
    except Exception as exc:dump(target/'retained_review_failure.json',{'created_utc':now(),'error':str(exc),'traceback':traceback.format_exc(),'native_outputs_preserved':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['checking','dynamics','review']);globals()[p.parse_args().action]()
