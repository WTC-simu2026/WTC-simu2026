"""Eight predeclared native controls of the authorized current-area Engine, never a whole dynamic extension."""
from build_aircraft_a67_current_area import ROOT,OUT,CFG,read,dump,sha,now,guard as build_guard
from prepare_aircraft_a66_current_area_r1 import current_areas
from material_aircraft_a60 import path_values
from pathlib import Path
import probe_aircraft_a54 as launcher
import numpy as np,ast,subprocess,shutil,json,re,time,argparse

CONTROL=ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json'
RUNTIME=launcher.RUNTIME

def declare():
    build_guard();assert not CONTROL.exists()
    prior=read(ROOT/'wtc1_simulation_v8/data/aircraft_a65_predeclaration.json');base_case=prior['cases'][0]
    square=np.array([[0,0,0],[10,0,0],[10,10,0],[0,10,0]]*2,float)
    axis=np.array([1,2,3])/np.sqrt(14);W=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    angle=1.1;R=np.eye(3)+np.sin(angle)*W+(1-np.cos(angle))*W@W
    cases=[]
    specs=[('FREE_Ismstr4',square,[0,1,0],.000125,'constant_uniform'),
           ('FREE_Ismstr4_HALF',square,[0,1,0],.0000625,'constant_uniform'),
           ('RIGID_ROTATED_FREE',square@R.T+[31,-7,15],R@np.array([0,1,0]),.000125,'constant_uniform'),
           ('AREA_x4_FREE',square*2,[0,1,0],.0000625,'constant_uniform'),
           ('NONUNIFORM_AREA_FREE',np.array([[0,0,0],[10,0,0],[8,10,0],[1,10,0]]*2,float),[0,.01,0],.000125,'small_amplitude_nonuniform'),
           ('AREA_EVOLUTION_FREE_Y',square,[0,1,0],.000125,'current_area_evolution_free_Y')]
    for key,x,v,dt,reference in specs:
        c={**base_case,'id':key,'nodes_mm':x.tolist(),'L_mm':20 if key=='AREA_x4_FREE' else 10,'dt_cap_ms':dt,
            'initial_free_velocity_mm_ms':list(map(float,v)),'reference':reference,'Ismstr':4,
            'field_output_dt_ms':dt/2,'RUN_stop_ms':1+dt/2,'initial_top_mass_g':4,'total_instrument_mass_g':8,
            'nodal_mass_g':[1]*8,'whole_budget_change':False,'initial_current_GP_area_mm2':current_areas(x).tolist(),
            'full_free_counter_qualification_required':reference!='current_area_evolution_free_Y',
            'linear_reference_small_amplitude_not_full_nonlinear_qualification':reference=='small_amplitude_nonuniform',
            'uniform_top_motion_required':reference!='small_amplitude_nonuniform'}
        if key=='AREA_EVOLUTION_FREE_Y':
            c.update(imposed_common_X_scale='1+0.1*sin(pi*t/1ms)^2',only_Y_counter_and_support_qualified_scope=True,
                full_prescribed_X_KE_P_observables_remain_unqualified=True,top_Y_Z_free=True,all_X_prescribed=True,
                reference_Newmark='Mass4g, K(t)=80000*(1+0.1*sin(pi*t)^2)N/mm, gamma.5 beta.25; no fitted coefficient.')
        cases.append(c)
    contract=read(CFG)['future_control_contract'];assert [c['id'] for c in cases]==contract['cases'][:6]
    whole=[]
    for c,key in zip(prior['whole_CHECK_cases'],contract['cases'][6:]):whole.append({**c,'id':key})
    data={'created_utc':now(),'iteration':'AIRCRAFT-A67','seed':1102092,'random_draws':0,'build_configuration_sha256':sha(CFG),
        'cohesive':prior['cohesive'],'acceptance':prior['acceptance'],'cases':cases,'whole_CHECK_cases':whole,
        'extra_analytical_displacement_tolerance_mm':prior['extra_analytical_displacement_tolerance_mm'],
        'extra_analytical_velocity_tolerance_mm_ms':prior['extra_analytical_velocity_tolerance_mm_ms'],
        'authorized_maximum_native':8,'each_cap_s':180,'CPU':1,'GPU':False,'software_changes_beyond_exact_A66':False,
        'whole_dynamic_extension':False,'minimum_case_error_not_used_to_refit':True,
        'source_interpretation':'Endpoint velocity from all-step secants only for actually free translations. Prescribed X counters not promoted in area-evolution case.',
        'units':{'length':'mm','time':'ms','mass':'g','energy_to_J':.001,'momentum_to_Ns':.001},
        'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0,'objective1_complete':False}
    dump(CONTROL,data);dump(OUT/'controls_guard.json',{'created_utc':now(),'sha256':sha(CONTROL),'before_any_native':True})
    print(json.dumps({'A67_controls_predeclared':8,'new_native_started':0,'no_whole_dynamic_extension':True}),flush=True)

def control_guard():
    build_guard();assert sha(CONTROL)==read(OUT/'controls_guard.json')['sha256'];return read(CONTROL)

def engine():
    control_guard();b=read(OUT/'build_finished.json');assert b['build_success'] and b['exact_A66_current_area_patch_applied']
    p=ROOT/b['candidate_directory'];binary=p/'isolated_exec/engine_linux64_gf_ompi';assert sha(binary)==b['binary_sha256'];return p,binary

source=(ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a62_surface.py').read_text(encoding='utf8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='generate');s=ast.get_source_segment(source,node)
s=s.replace("name='A62_'","name='A67_'")
s=s.replace('xyz=[[0,0,0],[L,0,0],[L,L,0],[0,L,0]]*2',"xyz=case['nodes_mm']")
assert s.count("i(1)+' '*70+f(0)")==1;s=s.replace("i(1)+' '*70+f(0)","i(4)+' '*70+f(0)")
assert s.count("'   111 111'+i(0,1)")==1;s=s.replace("'   111 111'+i(0,1)","('   011 111' if case['reference']=='current_area_evolution_free_Y' else '   111 111')+i(0,1)")
extra='''    if case['reference']=='current_area_evolution_free_Y':
        dt=case['dt_cap_ms'];end=1+dt
        rows +=['/GRNOD/NODE/4','ALL_LEFT_X',i(1,4,5,8),'/GRNOD/NODE/5','ALL_RIGHT_X',i(2,3,6,7)]
        rows +=['/FUNCT/401','LEFT_COMMON_X',f(0,0),f(end,0),'/IMPDISP/401','LEFT_COMMON_X',i(401)+f'{'X':>10}'+i(0,0,4)+' '*10+i(0),f(1,1,0,1e30)]
        rows +=['/FUNCT/402','RIGHT_COMMON_X']
        times=np.arange(int(round(end/(dt/2)))+1)*(dt/2)
        rows +=[f(t,L*.1*np.sin(np.pi*t)**2) for t in times]
        rows +=['/IMPDISP/402','RIGHT_COMMON_X',i(402)+f'{'X':>10}'+i(0,0,5)+' '*10+i(0),f(1,1,0,1e30)]
'''
marker="    rows+=['/END'];";assert s.count(marker)==1;s=s.replace(marker,extra+marker)
exec(compile(s,__file__,'exec'));generate_raw=generate

def generate(case):
    d,name=generate_raw(case)
    from prepare_aircraft_a65_sampling import updated_cards
    p=d/(name+'_0001.rad');old=p.read_text(encoding='utf8');(d/'original_Engine_card_before_output_schedule.rad').write_text(old,encoding='utf8',newline='\n')
    p.write_text(updated_cards(old,case['dt_cap_ms']),encoding='utf8',newline='\n')
    dump(d/'current_area_case_predeclaration.json',{'created_utc':now(),'Ismstr':4,'case':case,'SOURCE_binary_SHA256':sha(engine()[1]),
        'input_sha256':sha(d/(name+'_0000.rad')),'Engine_card_sha256':sha(p),'material_and_whole_budgets_unchanged':True})
    return d,name

def native(d,name):
    engine();ordinal=len(list(OUT.rglob('native_launch_declaration.json')))+1;assert ordinal<=8
    dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':ordinal,'maximum_native':8,'CPU':1,'GPU':False,'cap_s':180,
        'controls_sha256':sha(CONTROL),'binary_sha256':sha(engine()[1]),'whole_dynamic_extension':False})
    launcher.engine=engine;return launcher.run_native(d,name)

def local():
    results=[]
    for case in control_guard()['cases']:
        d,name=generate(case);r=native(d,name)
        if r['parent_exit_code']==0 and r['normal_termination']:
            start=time.perf_counter();conv=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60)
            (d/'converter.log').write_bytes(conv.stdout+conv.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':conv.returncode,'wall_s':time.perf_counter()-start,'cap_s':60})
        results.append({'case':case['id'],**r});print(json.dumps(results[-1]),flush=True)
    dump(OUT/'local_execution_review.json',{'created_utc':now(),'cases':results,'normal_cases':sum(r['parent_exit_code']==0 and r['normal_termination'] for r in results),
        'mechanical_qualification_not_inferred_from_completion':True})

def whole():
    results=[]
    for case in control_guard()['whole_CHECK_cases']:
        d=OUT/case['id'];assert not d.exists();d.mkdir()
        for p in case['files']:
            source=ROOT/p['path'];assert sha(source)==p['sha256'];shutil.copy2(source,d/source.name)
        dump(d/'generation.json',{'created_utc':now(),'case':case,'configuration_sha256':sha(CONTROL),'unchanged_whole_inputs_and_cards':True})
        result=native(d,case['name']);log=(d/'engine.log').read_text(encoding='utf8',errors='replace')
        errors=re.findall(r'^\s*(\d+)\s+ERRORS\s*$',log,re.M)
        warnings=re.findall(r'^\s*(\d+)\s+WARNINGS\s*$',log,re.M)
        result.update(printed_errors=int(errors[-1]) if errors else None,printed_warnings=int(warnings[-1]) if warnings else None,
            STOP_volume_messages=log.count('STOP: ZERO OR NEGATIVE VOLUME'),STOP_colon_messages=log.count('STOP:'),
            native_STOP66=bool(re.search(r'STOP\s+66|USER\s*BREAK',log,re.I)),
            clean_whole_qualification=False)
        results.append({'case':case['id'],**result});print(json.dumps(results[-1]),flush=True)
    dump(OUT/'whole_CHECK_review.json',{'created_utc':now(),'cases':results,'all_clean':all(r['parent_exit_code']==0 and r['CHECK_ended'] and r['printed_errors']==0 and r['TYPE25_ignored']==0 and r['STOP_colon_messages']==0 for r in results),
        'TYPE25_remains_blocking':True,'whole_credit_s':0,'no_whole_dynamic_extension':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','local','whole']);globals()[p.parse_args().action]()
