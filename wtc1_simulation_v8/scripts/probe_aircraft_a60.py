"""Predeclare new mixed and nonproportional cohesive witnesses; no old native replay."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import numpy as np,json,shutil,subprocess,time,re,argparse,tarfile,hashlib
import probe_aircraft_a54 as launcher
from material_aircraft_a60 import D,thresholds,path_values

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a60'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a60_predeclaration.json'
RUNTIME=launcher.RUNTIME

def engine():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    c=read(CFG);p=ROOT/c['candidate_directory'];b=p/'isolated_exec/engine_linux64_gf_ompi';assert sha(b)==c['binary_sha256'];return p,b

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A59'
    inherited=read(ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json');p={**inherited['cohesive'],'power_exponent':2,'mode_coupling_gamma':1,'displacement_criterion':1,'linear_evolution':1,'symmetric_damage':False}
    cases=[]
    for identifier,beta,az,L,dt in [('MIX_B05_L10',.5,np.pi/4,10,2.5e-5),('MIX_B05_HALF',.5,np.pi/4,10,1.25e-5),('MIX_B05_L20',.5,np.pi/4,20,2.5e-5),('MIX_B20_L10',2,.31,10,2.5e-5)]:
        direction=np.array([beta*np.cos(az),beta*np.sin(az),1.]);direction/=np.linalg.norm(direction)
        d0,df,_=thresholds([D(a) for a in direction],p);peak=.5*(d0.v+df.v)
        cases.append({'id':identifier,'L_mm':L,'dt_cap_ms':dt,'proportional':True,'direction':direction.tolist(),'d0_mm':d0.v,'df_mm':df.v,'knot_times_ms':[0,.25,.5,.75,1],'knot_gaps_mm':[(direction*q).tolist() for q in [0,peak,0,peak,1.1*df.v]]})
    cases += [{'id':'NONPROPORTIONAL_L10','L_mm':10,'dt_cap_ms':2.5e-5,'proportional':False,'knot_times_ms':[0,.2,.4,.6,.8,1],'knot_gaps_mm':[[0,0,0],[0,0,.14],[.25,.12,.08],[0,0,0],[.25,.12,.08],[1.2,.6,.15]]},
       {'id':'COMPRESSION_AFTER_DAMAGE','L_mm':10,'dt_cap_ms':2.5e-5,'proportional':False,'knot_times_ms':[0,.25,.5,.75,1],'knot_gaps_mm':[[0,0,0],[0,0,.14],[0,0,-.05],[0,0,.14],[0,0,.25]]}]
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a59';built=read(ROOT/'wtc1_simulation_v8/output/aircraft_a57/build_finished.json');OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    config={'created_utc':now(),'iteration':'AIRCRAFT-A60','seed':1102085,'random_draws':0,'candidate_directory':built['candidate_directory'],'binary_sha256':built['binary_sha256'],'cohesive':p,'acceptance':inherited['acceptance'],'cases':cases,'purpose':'Mixed power-law/linear displacement branch, trial-state discipline and complete material Jacobian against NEW native explicit witnesses. Moving-frame geometry and Engine insertion remain separate gates.','expected_minutes':[1,5],'CPU_threads':1,'GPU':False,'Starter_cap_s':180,'Engine_cap_s':180,'maximum_native_Engines':6,'old_native_Engine_replays':0,'new_software_patch_or_compilation':False,'whole_physical_budgets_unchanged':True,'instrument_mass_g':8,'TH_interval_ms':.0001,'ANIM_interval_ms':.005,'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_whole_duration_credit_s':0,'objective1_complete':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_execution':True})
    pins={r['path']:r for r in read(prior/'preservation_before_metadata.json')['files']}
    for r in read(prior/'artifact_manifest.json')['files']:pins[r['path']]=r
    for q in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[rel(q)]={'path':rel(q),'bytes':q.stat().st_size,'sha256':sha(q)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})
    print(json.dumps({'A60_declared':True,'new_mixed_and_path_cases':6,'old_pure_native_replays':0}),flush=True)

def run():
    candidate,binary=engine();config=read(CFG);launcher.engine=engine
    from run_aircraft_a17 import env
    f=lambda *a:''.join(f'{x:20.12g}' for x in a);i=lambda *a:''.join(f'{x:10d}' for x in a)
    unit=lambda *a:''.join(f'{x:>20}' for x in a)
    c=config['cohesive'];rows=[]
    for case in config['cases']:
        d=OUT/'native'/case['id'];assert not d.exists();d.mkdir(parents=True);name='A60_'+case['id'];L=case['L_mm'];xyz=[[0,0,0],[L,0,0],[L,L,0],[0,L,0]]*2
        lines=['#RADIOSS STARTER','/BEGIN',name,i(2026,0),unit('g','mm','ms'),unit('g','mm','ms'),'/TITLE',name,'/ANALY',i(0)+f(0)+i(0),'/SPMD',i(0,0)+f(0,1),'/NODE']+[i(j+1)+f(*x) for j,x in enumerate(xyz)]
        lines+=['/MAT/LAW117/1','COHESIVE_REFERENCE_NOT_MEASURED',f(c['area_mass_density_g_mm2']),f(c['EN_N_mm3'],c['ET_N_mm3'])+i(1,4,1),i(0,0)+f(c['TN_MPa'],c['TT_MPa'],1),f(c['GI_N_mm'],c['GII_N_mm'],2,2,1),'/PROP/TYPE43/1','ZERO_HEIGHT_COHESIVE',i(1)+' '*70+f(0),'/PART/1','COHESIVE_REFERENCE',i(1,1,0),'/BRICK/1',i(1,1,2,3,4,5,6,7,8),'/ADMAS/5/1','INSTRUMENT_NODAL_MASSES']+[f(1)+i(j) for j in range(1,9)]
        for gid,ids in [(1,list(range(1,5))),(2,list(range(5,9))),(3,list(range(1,9)))]:lines += [f'/GRNOD/NODE/{gid}',f'GROUP_{gid}',i(*ids)]
        lines += ['/BCS/1','BOTTOM_FIXED','   111 111'+i(0,1),'/BCS/2','TOP_ROTATIONS_FIXED','   000 111'+i(0,2)]
        ts=np.linspace(0,1,10001);q=path_values(ts,case,c)
        for axis,label in enumerate('XYZ'):
            fid=90+axis;lines += [f'/FUNCT/{fid}',f'OPENING_{label}']+[f(t,x) for t,x in zip(ts,q[:,axis])]+[f'/IMPDISP/{fid}',f'TOP_OPENING_{label}',i(fid)+f'{label:>10}'+i(0,0,2)+' '*10+i(0),f(1,1,0,1e30)]
        lines += ['/TH/PART/1','COHESIVE_PART',''.join(f'{s:>10}' for s in ['IE','KE','HE','PW']),i(1)]
        for axis in 'XYZ':lines += [f'/TH/NODE/{2+"XYZ".index(axis)}','REACTION_'+axis,''.join(f'{s:>10}' for s in ['D'+axis,'V'+axis,'REAC'+axis])]+[i(j,0) for j in range(1,9)]
        lines += ['/END'];(d/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf8')
        cards=['/ANIM/DT',f(0,config['ANIM_interval_ms']),'/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/BRICK/TENS/STRESS','/ANIM/ELEM/ENER','/DT',f(.4,0),'/DTIX',f(case['dt_cap_ms'],case['dt_cap_ms']),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',f(1),'/TFILE/4',f(config['TH_interval_ms']),'/VERS/2026']
        (d/(name+'_0001.rad')).write_text('\n'.join(cards)+'\n',encoding='utf8');dump(d/'generation.json',{'created_utc':now(),'name':name,'case':case,'nodes_mm':xyz,'area_mm2':L*L,'nodal_mass_g':[1]*8,'configuration_sha256':sha(CFG),'only_witness_motion_and_output_changed':True,'no_whole_model_change':True})
        started=time.perf_counter();argv=[str(RUNTIME/'starter_win64.exe'),'-i',name+'_0000.rad','-np','1']
        with (d/'starter.log').open('xb') as stream:r=subprocess.run(argv,cwd=d,env=env()|{'OMP_NUM_THREADS':'1','RAD_HMPP_DOMAINS':'1'},stdout=stream,stderr=subprocess.STDOUT,timeout=180)
        log=(d/'starter.log').read_text(errors='replace');warnings=re.findall(r'(\d+) WARNING\(S\)',log);errors=re.findall(r'(\d+) ERROR\(S\)',log)
        parsed={'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-started,'CPU':1,'GPU':False,'cap_s':180,'warnings':int(warnings[-1]) if warnings else None,'errors':int(errors[-1]) if errors else None};dump(d/'starter.execution.json',parsed)
        ok=r.returncode==0 and parsed['errors']==0 and parsed['warnings']==0
        if ok:
            result=launcher.run_native(d,name);ok=result['parent_exit_code']==0 and result['normal_termination']
            if ok:
                started=time.perf_counter();r=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60);(d/'converter.log').write_bytes(r.stdout+r.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-started,'cap_s':60});ok=r.returncode==0
        rows.append({'case':case['id'],'prepared_and_executed':ok,'Starter':parsed});print(json.dumps(rows[-1]),flush=True)
    dump(OUT/'native_execution_review.json',{'created_utc':now(),'cases':rows,'all_complete':all(r['prepared_and_executed'] for r in rows)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
