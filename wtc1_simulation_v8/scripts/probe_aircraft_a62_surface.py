"""Bounded loaded tests of the exact authorized sixth Engine, no old Engine replay."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from build_aircraft_a62_surface import OUT,CFG,guard
from material_aircraft_a60 import path_values,thresholds,D
from pathlib import Path
import probe_aircraft_a54 as launcher
import numpy as np,subprocess,json,time,re,shutil,argparse

RUNTIME=launcher.RUNTIME
CONTROL=OUT/'native_controls_predeclaration.json'

def engine():
    guard();b=read(OUT/'build_finished.json');assert b['build_success'];c=ROOT/b['candidate_directory'];p=c/'isolated_exec/engine_linux64_gf_ompi';assert sha(p)==b['binary_sha256'];return c,p

def declare():
    engine();assert not CONTROL.exists();p=read(ROOT/'wtc1_simulation_v8/data/aircraft_a60_predeclaration.json')['cohesive'];cases=[]
    for name,gap,axes,dt in [('ELASTIC_NORMAL',[0,0,.04],[2],.001),('ELASTIC_SHEAR',[.04,0,0],[0],.001),('ELASTIC_MIXED',[.02,0,.03],[0,2],.001),('ELASTIC_MIXED_HALF',[.02,0,.03],[0,2],.0005)]:
        cases.append({'id':name,'stage':'elastic','L_mm':10,'dt_cap_ms':dt,'imposed_axes':axes,'knot_times_ms':[0,.25,.5,.75,1],'knot_gaps_mm':[(np.array(gap)*s).tolist() for s in [0,1,0,1,0]],'end_ms':1})
    direction=np.array([.5,0,1.])/np.sqrt(1.25);d0,df,_=thresholds([D(x) for x in direction],p);peak=.5*(d0.v+df.v)
    for name,dt in [('DAMAGE_MIXED',.001),('DAMAGE_MIXED_HALF',.0005)]:
        cases.append({'id':name,'stage':'damage','L_mm':10,'dt_cap_ms':dt,'imposed_axes':[0,2],'knot_times_ms':[0,.25,.5,.75,1],'knot_gaps_mm':[(direction*s).tolist() for s in [0,peak,0,peak,1.1*df.v]],'end_ms':1,'proportional':True,'direction':direction.tolist(),'d0_mm':d0.v,'df_mm':df.v})
    cases.append({'id':'DAMAGE_NONPROPORTIONAL','stage':'damage','L_mm':10,'dt_cap_ms':.001,'imposed_axes':[0,2],'knot_times_ms':[0,.2,.4,.6,.8,1],'knot_gaps_mm':[[0,0,0],[0,0,.14],[.25,0,.08],[0,0,0],[.25,0,.08],[1.2,0,.15]],'end_ms':1})
    dump(CONTROL,{'created_utc':now(),'iteration':'AIRCRAFT-A62','seed':1102087,'random_draws':0,'binary_sha256':sha(engine()[1]),'cohesive':p,
      'cases':cases,'acceptance':read(ROOT/'wtc1_simulation_v8/data/aircraft_a60_predeclaration.json')['acceptance'],
      'elastic_first_new_question':'Does the new surface branch advance under load with at least one unconstrained translation? No claim from NORMAL/exit0 alone.',
      'unused_top_axes_free':True,'same_nodal_instrument_mass_g':8,'whole_budgets_unchanged':True,
      'implicit_numerics':{'solver':2,'Newmark_gamma_beta':[.5,.25],'nonlinear_tolerances':[1e-11]*3,'linear_tolerance':1e-8,'fixed_dt_ms':'each declared case','minimum_dt_ms':1e-12},
      'maximum_native_Engine_runs_all_stages':12,'each_cap_s':180,'CPU':1,'GPU':False,'new_software_changes_beyond_approved_patch':False,'old_Engine_replays':0,
      'regression_plan':['Two explicit mixed controls on the new binary from cached A60 initial states','TYPE7 implicit contact on the new binary from cached accepted input','Whole CHECK only after local implicit mechanical gate; at most one further native observer if needed'],
      'new_whole_duration_credit_s':0})
    print(json.dumps({'A62_controls_declared':True,'elastic':4,'damage':3,'maximum_all_native':12}),flush=True)

def run_native(d,name):
    completed=list(OUT.rglob('engine.execution.json'));assert len(completed)<12,'authorized native launch cap reached'
    dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':len(completed)+1,'maximum_all_runs':12,'cap_s':180,'CPU':1,'GPU':False,'binary_sha256':sha(engine()[1])})
    launcher.engine=engine;result=launcher.run_native(d,name);log=(d/'engine.log').read_text(encoding='utf8',errors='replace')
    result['no_USER_BREAK_or_STOP']=not bool(re.search(r'USER\s*BREAK|USERBREAK|STOP\s+(?:zero|61)|SIGSEGV|ABORT',log,re.I))
    return result

def generate(case):
    config=read(CONTROL);c=config['cohesive'];d=OUT/'native'/case['id'];assert not d.exists();d.mkdir(parents=True);name='A62_'+case['id'];L=case['L_mm']
    f=lambda *v:''.join(f'{x:20.12g}' for x in v);i=lambda *v:''.join(f'{x:10d}' for x in v);unit=lambda *v:''.join(f'{x:>20}' for x in v)
    xyz=[[0,0,0],[L,0,0],[L,L,0],[0,L,0]]*2
    rows=['#RADIOSS STARTER','/BEGIN',name,i(2026,0),unit('g','mm','ms'),unit('g','mm','ms'),'/TITLE',name,'/ANALY',i(0)+f(0)+i(0),'/SPMD',i(0,0)+f(0,1),'/NODE']+[i(j+1)+f(*q) for j,q in enumerate(xyz)]
    rows+=['/MAT/LAW117/1','UNCHANGED_NUMERICAL_COHESIVE_REFERENCE',f(c['area_mass_density_g_mm2']),f(c['EN_N_mm3'],c['ET_N_mm3'])+i(1,4,1),i(0,0)+f(c['TN_MPa'],c['TT_MPa'],1),f(c['GI_N_mm'],c['GII_N_mm'],2,2,1),'/PROP/TYPE43/1','ZERO_HEIGHT_COHESIVE',i(1)+' '*70+f(0),'/PART/1','COHESIVE_REFERENCE',i(1,1,0),'/BRICK/1',i(1,1,2,3,4,5,6,7,8),'/ADMAS/5/1','INSTRUMENT_NODAL_MASSES']+[f(1)+i(j) for j in range(1,9)]
    for gid,ids in [(1,list(range(1,5))),(2,list(range(5,9))),(3,list(range(1,9)))]:rows +=[f'/GRNOD/NODE/{gid}',f'GROUP_{gid}',i(*ids)]
    rows+=['/BCS/1','BOTTOM_FIXED','   111 111'+i(0,1),'/BCS/2','TOP_ROTATIONS_FIXED_UNUSED_TRANSLATIONS_FREE','   000 111'+i(0,2)]
    if 'initial_free_velocity_mm_ms' in case:
        rows+=['/INIVEL/TRA/500','DECLARED_INITIAL_FREE_AXIS_MOTION',f(*case['initial_free_velocity_mm_ms'])+i(2,0),f(0)+i(0)]
    times=np.linspace(0,1,10001);gaps=path_values(times,case,c)
    for axis in case['imposed_axes']:
        label='XYZ'[axis];fid=90+axis
        rows +=[f'/FUNCT/{fid}',f'OPENING_{label}']+[f(t,q) for t,q in zip(times,gaps[:,axis])]+[f'/IMPDISP/{fid}',f'TOP_OPENING_{label}',i(fid)+f'{label:>10}'+i(0,0,2)+' '*10+i(0),f(1,1,0,1e30)]
    rows+=['/TH/PART/1','COHESIVE_PART',''.join(f'{q:>10}' for q in ['IE','KE','HE','PW']),i(1)]
    for axis in 'XYZ':rows +=[f'/TH/NODE/{2+"XYZ".index(axis)}','REACTION_'+axis,''.join(f'{q:>10}' for q in ['D'+axis,'V'+axis,'REAC'+axis])]+[i(j,0) for j in range(1,9)]
    rows+=['/END'];(d/(name+'_0000.rad')).write_text('\n'.join(rows)+'\n',encoding='utf8')
    from probe_aircraft_a55 import cards
    (d/(name+'_0001.rad')).write_text(cards(name,case['dt_cap_ms']),encoding='utf8')
    dump(d/'generation.json',{'created_utc':now(),'name':name,'case':case,'nodes_mm':xyz,'area_mm2':L*L,'nodal_mass_g':[1]*8,'configuration_sha256':sha(CONTROL),'unused_top_axes_free':True,'physical_budget_change_to_whole':False})
    from run_aircraft_a17 import env
    start=time.perf_counter()
    with (d/'starter.log').open('xb') as stream:r=subprocess.run([str(RUNTIME/'starter_win64.exe'),'-i',name+'_0000.rad','-np','1'],cwd=d,env=env()|{'OMP_NUM_THREADS':'1','RAD_HMPP_DOMAINS':'1'},stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    log=(d/'starter.log').read_text(encoding='utf8',errors='replace');errors=re.findall(r'(\d+) ERROR\(S\)',log);warnings=re.findall(r'(\d+) WARNING\(S\)',log)
    result={'created_utc':now(),'exit_code':r.returncode,'errors':int(errors[-1]) if errors else None,'warnings':int(warnings[-1]) if warnings else None,'wall_s':time.perf_counter()-start,'cap_s':180,'CPU':1,'GPU':False};dump(d/'starter.execution.json',result)
    assert r.returncode==0 and result['errors']==0 and result['warnings']==0,result
    return d,name

def stage(label):
    engine();cases=[c for c in read(CONTROL)['cases'] if c['stage']==label];results=[]
    for case in cases:
        d,name=generate(case);result=run_native(d,name)
        if result['parent_exit_code']==0 and result['normal_termination'] and result['no_USER_BREAK_or_STOP']:
            start=time.perf_counter();r=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60);(d/'converter.log').write_bytes(r.stdout+r.stderr)
            dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':60});result['history_converter_exit_code']=r.returncode
        results.append({'case':case['id'],**result});print(json.dumps(results[-1]),flush=True)
        if result['parent_exit_code']!=0 or not result['normal_termination'] or not result['no_USER_BREAK_or_STOP']:break
    dump(OUT/(label+'_execution_review.json'),{'created_utc':now(),'cases':results,'all_requested_cases_completed':len(results)==len(cases) and all(r['parent_exit_code']==0 and r['normal_termination'] and r['no_USER_BREAK_or_STOP'] for r in results),'loaded_mechanical_gate_not_inferred_from_completion':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','elastic','damage']);a=p.parse_args().action
    if a=='declare':declare()
    else:stage(a)
