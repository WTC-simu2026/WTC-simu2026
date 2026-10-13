"""New controlled initial-motion question, retaining all convergence criteria and failures."""
from probe_aircraft_a62_surface import ROOT,OUT,CONTROL,engine,read,dump,sha,now,rel,generate,run_native,RUNTIME
import copy,subprocess,time,json,argparse

SEEDED=OUT/'initial_free_motion_predeclaration.json'

def declare():
    engine();old=read(CONTROL);cases=[]
    for identifier in ['ELASTIC_NORMAL','DAMAGE_MIXED','DAMAGE_MIXED_HALF']:
        case=copy.deepcopy(next(c for c in old['cases'] if c['id']==identifier));case.update(id=identifier+'_INITIAL_FREE_MOTION',model_domain=case['stage'],stage='initial_free_motion',initial_free_velocity_mm_ms=[0,.01,0]);cases.append(case)
    dump(SEEDED,{**old,'created_utc':now(),'cases':cases,'comparison_cases':[cases[1]['id'],cases[2]['id']],
       'new_question':'At-rest free unknowns have zero normalized displacement/energy references: Newton diagnostics show NaN/Infinity while force residual is0. Does a declared nonzero initial free-axis velocity remove the singular normalization, with all three criteria123 and1e-11 tolerances unchanged?',
       'initial_free_velocity_mm_ms':[0,.01,0],'top_instrument_mass_g':4,'initial_instrument_KE_J':.5*4*.01**2*.001,
       'only_additional_mechanical_condition':'Initial0.01mm/ms Y velocity on the four top instrument nodes; no aircraft/facade mass, material or whole budget changed.',
       'all_original_criteria_and_at_rest_failed_gates_preserved':True,'force_only_criterion_not_used':True,'no_new_software_change':True,'same_A62_binary':True,'counts_towards_original_maximum12':True})
    print(json.dumps({'initial_motion_variant_declared':True,'criteria123_unchanged':True,'initial_KE_J':.5*4*.01**2*.001}),flush=True)

def run():
    engine();cfg=read(SEEDED);results=[]
    for case in cfg['cases']:
        d,name=generate(case);dump(d/'initial_motion_configuration.json',{'created_utc':now(),'configuration':rel(SEEDED),'sha256':sha(SEEDED),'original_material_configuration':rel(CONTROL),'mechanical_criteria_unchanged':True})
        result=run_native(d,name)
        if result['parent_exit_code']==0 and result['normal_termination'] and result['no_USER_BREAK_or_STOP']:
            start=time.perf_counter();r=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60);(d/'converter.log').write_bytes(r.stdout+r.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':60});result['history_converter_exit_code']=r.returncode
        results.append({'case':case['id'],**result});print(json.dumps(results[-1]),flush=True)
        if result['parent_exit_code']!=0 or not result['normal_termination'] or not result['no_USER_BREAK_or_STOP']:break
    dump(OUT/'initial_free_motion_execution_review.json',{'created_utc':now(),'cases':results,'all_requested_cases_completed':len(results)==len(cfg['cases']) and all(r['parent_exit_code']==0 and r['normal_termination'] and r['no_USER_BREAK_or_STOP'] for r in results),'no_mechanical_pass_inferred_from_completion':True})

def review():
    import review_aircraft_a62_surface as reviewer
    reviewer.CONTROL=SEEDED;reviewer.review('initial_free_motion')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','review']);globals()[p.parse_args().action]()
