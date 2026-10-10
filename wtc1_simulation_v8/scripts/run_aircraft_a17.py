"""A17: native separation-energy checks and a solver-driven 3D movie export."""
import argparse,json,re,shutil,subprocess,time,traceback,urllib.request
from pathlib import Path
import numpy as np
from run_aircraft_a16 import ROOT,RUNTIME,read,dump,rel,now,harness,execute as native_execute,env,streamsha,ff,ii

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a17'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a16'
SOURCE=PREV/'r0/IMPACT_R20_10'
BLENDER=Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')

def execute(exe,args,d,log,timeout,environ):
    if exe.is_relative_to(ROOT):return native_execute(exe,args,d,log,timeout,environ)
    assert not (d/log).exists();start=time.perf_counter();status=None;timed=False
    with (d/log).open('w',encoding='utf-8') as f:
        try:status=subprocess.run([str(exe),*args],cwd=d,env=environ,stdout=f,stderr=subprocess.STDOUT,timeout=timeout).returncode
        except subprocess.TimeoutExpired:timed=True
    dump(d/(log+'.execution.json'),{'exe':str(exe),'sha256':streamsha(exe),'args':args,'seconds':time.perf_counter()-start,'exit_code':status,'timeout_s':timeout,'timed_out':timed,'created_utc':now()});return status==0 and not timed

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
    assert not OUT.exists() and not CFG.exists();v=harness();assert v['CurrentIteration']=='AIRCRAFT-A16';OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archive_rescanned':False})
    seconds=[read(PREV/'r0'/c/'engine.log.execution.json')['seconds'] for c in ['IMPACT_R20_10','IMPACT_R02_10']];mean=sum(seconds)/len(seconds)
    c={'iteration':'AIRCRAFT-A17','declared_utc':now(),'seed':1102042,'random_draws':0,'user_objective':'Produce 3D visualization and video of first10 physical simulated seconds; slow replay of10ms is only an interim preview.','target_physical_duration_s':10,'current_whole_physical_duration_s':.0100001755,'scope':'LAW117 cohesive opening energy/history implementation check, not actual radome material identification. Export cached A16 whole scene through Blender, with no physics extrapolation.','cohesive':{'law':'LAW117','property':'TYPE43','EN_N_mm3':4400,'ET_N_mm3':800,'TN_MPa':450,'TT_MPa':100,'GI_N_mm':50,'GII_N_mm':50,'area_mass_density_g_mm2':1e-20,'nodal_instrument_mass_g':1,'Imass':1,'Idel':4,'Irupt':1,'Ismstr':1,'stiffness_derivation':'A07 analytical contract E22000MPa/5mm; ET4000/5. Numerical interface reference only.','G_physical_measured':False,'shear_strength_measured':False,'whole_aircraft_transfer_qualified':False,'true_glue_or_tearing_properties_identified':False},'witness':{'time_ms':[0,.25,.5,.75,1],'opening_path':'0 -> midpoint(initiation,complete) ->0 ->same midpoint ->1.1*complete; cubic smooth each leg','TH_interval_ms':.0001,'ANIM_interval_ms':.005,'cases':[{'id':'NORMAL_L10','mode':'Z','L_mm':10,'dt_cap_ms':.000025},{'id':'NORMAL_L10_HALF','mode':'Z','L_mm':10,'dt_cap_ms':.0000125},{'id':'NORMAL_L20','mode':'Z','L_mm':20,'dt_cap_ms':.000025},{'id':'SHEAR_L10','mode':'X','L_mm':10,'dt_cap_ms':.000025}]},'acceptance':{'work_energy_fraction':.01,'absolute_energy_J':.001,'work_per_area_G_fraction':.02,'equal_peak_energy_fraction':.005,'traction_maximum_relative':.02,'prescribed_motion_mm':.0001,'half_dt_work_fraction':.005,'area_normalized_work_fraction':.005,'stored_dissipated_reference_identity_relative':1e-8},'execution':{'CPU_threads':2,'GPU_physics':False,'starter_cap_s':120,'engine_cap_s':180,'converter_cap_s':120,'no_whole10s_job_launched_in_A17':True},'video':{'source':rel(SOURCE),'selection':'first declared A16R20, no selection by historical resemblance','renderer':'Blender5.2 Workbench, geometry only, no rigid-body physics','unique_saved_states':21,'views':['whole','nose_closeup'],'resolution_each':[1280,720],'movie_resolution':[2560,720],'fps':30,'frames_per_saved_state':9,'display_duration_s':6.3,'geometry_interpolation':'none, hold exact native states','displacement_scale':1,'output':'MP4 H264 yuv420p plus labelled GIF','renderer_cap_s':900,'physical_10s_goal_complete':False},'cost_estimate':{'observed_10ms_seconds':seconds,'mean_10ms_seconds':mean,'linear_10s_seconds':mean*1000,'linear_10s_days':mean*1000/86400,'CPU_threads':2,'not_a_reliable_ETA':'Fracture, contacts, deformation and changed output cadence can change cost. No GPU solve or mass scaling assumed.'},'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/brick_starter_r.htm'],'NIST_outcomes_used_as_target':False,'old_solver_reruns':0,'sources_read_only':True,'physical_impact_qualified':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_any_A17_solver_or_render':True})
    sd=OUT/'sources';sd.mkdir();src=[]
    for i,url in enumerate(c['sources']):
        p=sd/f'primary_{i}.html';p.write_bytes(urllib.request.urlopen(url,timeout=60).read());src.append({'path':rel(p),'url':url,'bytes':p.stat().st_size,'sha256':streamsha(p),'redistribution':'exclude_third_party'})
    for p in [SOURCE/'verified_states_SI.npz',SOURCE/'native_radome_damage.npz',SOURCE/'mesh.json',PREV/'campaign_review.json',ROOT/'wtc1_simulation_v8/output/aircraft_a07/future_fracture_energy_contract.json']:
        src.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':src,'archive_rescanned':False,'no_new_video_archive_analysis':True})
    dump(OUT/'objectif1_route.json',{'created_utc':now(),'objective':'10 simulated physical seconds, native physics visualization, export video','target_physical_seconds':10,'coverage_now_s':.0100001755,'complete':False,'steps':[{'horizon_s':.01,'status':'cached_A16_exploratory'},{'horizon_s':.02,'status':'after native separation/contact checks and fresh intact coupled setup'},{'horizon_s':.1,'status':'future contact, metal failure and geometry domain checks'},{'horizon_s':1,'status':'requires interior structure, gravity and free fragments'},{'horizon_s':10,'status':'requires bounded resumable campaign and final video audit'}],'no_kinematic_extrapolation':True,'no_slow_preview_substitution':True,'cost':c['cost_estimate']})
    print({'declared':'AIRCRAFT-A17','old_files_pinned':len(pins),'whole10s_estimate_days':c['cost_estimate']['linear_10s_days']},flush=True)

def opening(ts,mode):
    c=read(CFG)['cohesive'];K,T,G=(c['EN_N_mm3'],c['TN_MPa'],c['GI_N_mm']) if mode=='Z' else (c['ET_N_mm3'],c['TT_MPa'],c['GII_N_mm']);d0=T/K;df=2*G/T;assert d0<df
    peak=(d0+df)/2;values=[0,peak,0,peak,1.1*df];times=read(CFG)['witness']['time_ms'];out=np.zeros_like(ts)
    for ta,tb,qa,qb in zip(times[:-1],times[1:],values[:-1],values[1:]):
        ix=(ts>=ta)&(ts<=tb);u=(ts[ix]-ta)/(tb-ta);out[ix]=qa+(qb-qa)*(3*u*u-2*u*u*u)
    return out

def witness(case):
    guard();cfg=read(CFG);c=cfg['cohesive'];L=case['L_mm'];mode=case['mode'];d=OUT/'w0'/case['id'];assert not d.exists();d.mkdir(parents=True);n='A17_'+case['id'];xyz=[[0,0,0],[L,0,0],[L,L,0],[0,L,0]]*2
    lines=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    lines+=['/MAT/LAW117/1','COHESIVE_REFERENCE_NOT_MEASURED',ff(c['area_mass_density_g_mm2']),ff(c['EN_N_mm3'],c['ET_N_mm3'])+ii(1,4,1),ii(0,0)+ff(c['TN_MPa'],c['TT_MPa'],1),ff(c['GI_N_mm'],c['GII_N_mm'],2,2,1),'/PROP/TYPE43/1','ZERO_HEIGHT_COHESIVE',ii(1)+' '*70+ff(0),'/PART/1','COHESIVE_REFERENCE',ii(1,1,0),'/BRICK/1',ii(1,1,2,3,4,5,6,7,8),'/ADMAS/5/1','INSTRUMENT_NODAL_MASSES']+[ff(c['nodal_instrument_mass_g'])+ii(i) for i in range(1,9)]
    for gid,ids in [(1,list(range(1,5))),(2,list(range(5,9))),(3,list(range(1,9)))]:lines += [f'/GRNOD/NODE/{gid}',f'GROUP_{gid}',ii(*ids)]
    lines+=['/BCS/1','BOTTOM_FIXED','   111 111'+ii(0,1),'/BCS/2','TOP_TRANSVERSE_FIXED',('   110 111' if mode=='Z' else '   011 111')+ii(0,2)]
    ts=np.linspace(0,1,10001);q=opening(ts,mode)
    lines+=['/FUNCT/90','OPENING_SMOOTH']+[ff(t,x) for t,x in zip(ts,q)]+['/IMPDISP/90','TOP_OPENING',ii(90)+f'{mode:>10}'+ii(0,0,2)+' '*10+ii(0),ff(1,1,0,1e30),'/TH/PART/1','COHESIVE_PART',''.join(f'{s:>10}' for s in ['IE','KE','HE','PW']),ii(1),'/TH/NODE/2','REACTION_NODES',''.join(f'{s:>10}' for s in ['D'+mode,'V'+mode,'REAC'+mode])]+[ii(i,0) for i in range(1,9)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8');w=cfg['witness']
    engine=['/ANIM/DT',ff(0,w['ANIM_interval_ms']),'/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/BRICK/TENS/STRESS','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(case['dt_cap_ms'],case['dt_cap_ms']),'/MON/ON','/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(w['TH_interval_ms']),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':case,'area_mm2':L*L,'nodes_mm':xyz,'nodal_masses_g':[1]*8,'configuration_sha256':streamsha(CFG),'fresh_intact_start':True,'instrument_masses_are_not_aircraft_parameters':True})
    assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env())
    log=(d/'starter.log').read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',log)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',log)[-1])==0
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',180,env());assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace')
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());print({'witness_finished':case['id']},flush=True)

def witnesses():
    for c in read(CFG)['witness']['cases']:
        try:witness(c)
        except Exception:
            d=OUT/'w0'/c['id'];d.mkdir(parents=True,exist_ok=True);dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'case':c,'traceback':traceback.format_exc()});print(traceback.format_exc(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','witnesses']);a=p.parse_args();globals()[a.action]()
