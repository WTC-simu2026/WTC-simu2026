"""A14: declared spatial contact controls, no fitted event outcome or old rerun."""
import argparse,copy,csv,json,re,shutil,sys,traceback,urllib.request,hashlib,time
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
from run_aircraft_a06 import env
from run_aircraft_a13 import contact25,group
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a14'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a14_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a13'
REV='r0'
def guard():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    if (OUT/'radome_extension.json').exists():assert sha(OUT/'radome_extension.json')==read(OUT/'radome_extension_guard.json')['sha256']
def allcases():return read(CFG)['execution']['cases']
def streamsha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()

def declare():
    assert not OUT.exists() and not CFG.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A13' and v['NextIteration']=='AIRCRAFT-A14'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json',ROOT/'outputs/github_publication/updates_2026-10-08_aircraft_a12_a13/final_remote_verification.json']:
        pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    cases=[{'id':'FREE_N8','n':8,'main_n':1,'contact':False,'weighting':'none','dt_scale':.05,'factor':1}]
    for w,label in [('native','RAW'),('area','AREA')]:
        for n in [1,2,4,8]:cases.append({'id':f'{label}_N{n}','n':n,'main_n':1,'contact':True,'weighting':w,'dt_scale':.05,'factor':1})
    cases+=[{'id':'AREA_N8_HALF','n':8,'main_n':1,'contact':True,'weighting':'area','dt_scale':.025,'factor':1},
            {'id':'AREA_N4_MAIN3','n':4,'main_n':3,'contact':True,'weighting':'area','dt_scale':.05,'factor':1},
            {'id':'AREA_N4_MAIN4','n':4,'main_n':4,'contact':True,'weighting':'area','dt_scale':.05,'factor':1}]
    for fac,label in [(.25,'SOFT'),(4,'STIFF')]:
        for n in [4,8]:cases.append({'id':f'AREA_{label}_N{n}','n':n,'main_n':1,'contact':True,'weighting':'area','dt_scale':.05,'factor':fac})
    cases.append({'id':'LEGACY_N1','n':1,'main_n':1,'contact':True,'weighting':'native','dt_scale':.025,'factor':1,'legacy_surface_mode':True,'start_x_mm':-1.01})
    c={'iteration':'AIRCRAFT-A14','declared_utc':now(),'seed':1102039,'random_draws':0,'scope':'Numerical spatial objectivity of a fixed area/mass plate impacting a plane at 200m/s. No Boeing qualification, no target damage, no historical fit.',
       'units':{'native':'g mm ms MPa N','g_to_kg':.001,'mm_to_m':.001,'ms_to_s':.001,'energy_to_J':.001,'impulse_to_Ns':.001},
       'geometry':{'moving_side_mm':20,'wall_side_mm':40,'thickness_mm':1,'start_x_mm':-5,'wall_x_mm':0,'moving_BCS':'X free; Y,Z and all rotations locked','wall_BCS':'all fixed'},
       'material_hypothesis':{'law':'LAW1','rho_g_mm3':.00278,'E_MPa':70000,'nu':.3,'source':'Synthetic verification values inherited A10, not aircraft material'},
       'velocity_m_s':[200,0,0],'end_ms':.04,
       'contact':{'type':25,'Istf':4,'canonical_surface_ids':[0,3],'secondary_group':1,'gap_card_mm':1,'contact_thickness_s_and_m_mm':1,'Ishape':2,'Inacti':1000,'Iedge':1000,'Ipstif':0,'VIS_s':1e-20,'friction':0,'all_secondary_nodes_in_one_disjoint_group_only':True},
       'area_weighting':{'law':'Stfac_i=factor*A_i/A_reference','A_reference_mm2':100,'A_i':'Initial quad area/4 summed over incident quads; total area fixed 400mm2','K_native_node_N_mm':35000,'kappa_nominal_N_mm3':350,'K_total_nominal_N_mm':140000,'reference_selection':'E*t/(2*A_reference); A_reference is A13 coarse witness per-node area, no fit to outputs or historical damage','sensitivity_factors':[.25,1,4],'numerical_penalty_not_physical_contact_identification':True},
       'analytical_reference':{'mass_kg':.001112,'initial_KE_J':22.24,'initial_P_Ns':.2224,'complete_rebound_impulse_Ns':.4448,'contact_duration_ms':'pi*sqrt(M_g/K_total_N_mm) for uniform motion of area weighted nodes','peak_penetration_mm':'v0*sqrt(M_g/K_total_N_mm)','native_unweighted_aggregate_stiffness_changes_with_nodal_count':True,'contact_onset_not_fitted':'Report native onset and static effective-plane diagnostic separately; no fitted gap to force onset.'},
       'energy_contract':{'ledger':read(ROOT/'wtc1_simulation_v8/data/aircraft_a13_predeclaration.json')['energy_contract']['ledger'],'no_reconstructed_RKE_added':True,'support_main_only':True,'contact_impulses_cumulative':True},
       'acceptance':{'mass_relative':1e-6,'added_mass_fraction':1e-9,'energy_fraction_initial':.01,'momentum_fraction_initial':.01,'support_fraction_initial':.02,'rebound_velocity_fraction':.01,'contact_duration_fraction':.02,'peak_penetration_fraction':.02,'contact_energy_law_fraction_initial':.01,'area_weighted_velocity_uniformity_fraction':.001,'mesh_impulse_fraction':.01,'mesh_duration_fraction':.02,'mesh_contact_energy_curve_fraction_initial':.02,'half_dt_impulse_fraction':.01,'native_csv_relative':6e-7,'native_csv_absolute':1e-12,'free_velocity_m_s':1e-6,'phase_centered_momentum_fraction_initial':.001,'phase_centered_KE_fraction_initial':.001},
       'timing_contract':{'raw_velocities_retained':True,'diagnostic_only':['v','v-dt*a/2','v+dt*a/2'],'source_binary_equivalence_established':False,'no_ledger_shift':True,'no_retroactive_A13_credit':True},
       'execution':{'cases':cases,'history_interval_ms':.000001,'animation_interval_ms':.002,'CPU_threads':2,'GPU':False,'starter_timeout_s':120,'engine_timeout_s':180,'converter_timeout_s':60,'estimated_minutes':[5,15]},
       'legacy_A13_card_audit':{'Starter_contact_type':1,'documented_expected_node_to_surface_type':3,'surface_ids_actual':[3,0],'supplementary_secondary_group':1,'preserve_A13':True,'no_old_results_relabelled_as_failed_or_passed':True},
       'conditional_radome_extension':'Only if area-weighted plate energy/momentum/rebound and secondary/main mesh checks pass; declare radome-only area scheme before fresh starts, no whole-aircraft extension.',
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm'],'NIST_input_dependency':False,'NIST_outcomes_target':False,'physical_impact_qualified':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_A14_solver':True})
    src=OUT/'sources';src.mkdir();p=src/'TYPE25.html';p.write_bytes(urllib.request.urlopen(c['sources'][0],timeout=60).read())
    rows=[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size,'url':c['sources'][0],'redistribution':'exclude_third_party'}]
    for p in [PREV/'campaign_review.json',PREV/'r0/W25_DT025/A13_W25_DT025_R0_0000.out',PREV/'r0/W25_DT025/A13_W25_DT025_R0_0000.rad',ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a13.py']:
        rows.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':rows,'archives_rescanned':False})
    print({'declared':len(cases),'old_files_pinned':len(pins)},flush=True)

def grid(x,side,n,base):
    nodes=[[x,-side/2+side*j/n,-side/2+side*k/n] for k in range(n+1) for j in range(n+1)];quads=[]
    for k in range(n):
        for j in range(n):
            a=base+k*(n+1)+j;quads.append([a,a+1,a+n+2,a+n+1])
    return nodes,quads

def contacts(gap,weights,mode='canonical'):
    L=[];ids=[];rows=[]
    for ix,(factor,nodeset) in enumerate(weights,1):
        gid=100+ix;L+=group(gid,f'CONTACT_NODES_{ix}',nodeset);q=contact25(gap);q[0]=f'/INTER/TYPE25/{ix}';q[1]=f'CONTACT_RAW_{ix}';q[2]=ii(3,0,4,0,5,3,0,1000,1000,0) if mode=='legacy' else ii(0,3,4,0,5,3,0,1000,1000,0);q[3]=ii(gid,0)+q[3][20:];q[5]=ff(factor,0,0,0,1e30);L+=q;ids.append(ix);rows.append({'interface':ix,'group':gid,'Stfac':factor,'nodes':nodeset})
    L+=['/TH/INTER/1','CONTACT_RAW',''.join(f'{s:>10}' for s in ['FNX','FNY','FNZ','CE_ELAST'])]+[ii(*ids[k:k+10]) for k in range(0,len(ids),10)]
    return L,rows

def build(caseid):
    guard();cfg=read(CFG);c=next(x for x in allcases() if x['id']==caseid);d=OUT/REV/caseid;assert not d.exists();d.mkdir(parents=True);name='A14_'+caseid+'_R0';geom=cfg['geometry'];mat=cfg['material_hypothesis'];x0=c.get('start_x_mm',geom['start_x_mm'])
    mx,mq=grid(x0,20,c['n'],1);wx,wq=grid(0,40,c['main_n'],len(mx)+1);x=mx+wx;rn=list(range(1,len(mx)+1));wn=list(range(len(mx)+1,len(x)+1))
    areas=np.zeros(len(x));area_element=400/c['n']**2
    for q in mq:areas[np.array(q)-1]+=area_element/4
    assert abs(areas.sum()-400)<1e-12
    L=['#RADIOSS STARTER','/BEGIN',name,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',name,'/ANALY',ii(0,0,0,0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(k+1)+ff(*v) for k,v in enumerate(x)]
    L+=['/MAT/LAW1/1','SYNTHETIC_ELASTIC',ff(mat['rho_g_mm3']),ff(mat['E_MPa'],mat['nu'])]
    for pid,title,qs in [(1,'MOVING_PLATE',mq),(2,'FIXED_PLANE',wq)]:
        L+=[f'/PROP/TYPE1/{pid}',title,ii(24,4,2,2),ff(*([1e-20]*5)),ii(0)+' '*10+ff(1,5/6),f'/PART/{pid}',title,ii(pid,1,0),f'/SHELL/{pid}']+[ii((1000 if pid==1 else 2000)+j,*q) for j,q in enumerate(qs)]
    L+=group(1,'MOVING_ALL',rn)+group(2,'FIXED_ALL',wn)+['/BCS/1','X_ONLY','   011 111'+ii(0,1),'/BCS/2','FIXED','   111 111'+ii(0,2),'/INIVEL/TRA/1','INITIAL_VELOCITY',ff(200,0,0)+ii(1,0),ff(0)+ii(0)]
    cr=[]
    if c['contact']:
        fac=areas/100*c['factor'] if c['weighting']=='area' else np.array([c['factor']]*len(x));weights=[]
        for v in sorted(set(float(fac[k-1]) for k in rn)):weights.append((v,[k for k in rn if fac[k-1]==v]))
        L+=['/SURF/PART/3','FIXED_MAIN',ii(2)];card,cr=contacts(1,weights,'legacy' if c.get('legacy_surface_mode') else 'canonical');L+=card
    L+=['/TH/PART/1','PARTS',''.join(f'{s:>10}' for s in ['IE','KE','HE','PW','RKE','XMOM','YMOM','ZMOM','MASS']),ii(1,2)]
    for gid,title,channels,nodeset,prefix in [(2,'NATIVE_NODES',['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ'],range(1,len(x)+1),'N'),(3,'SUPPORT_NATIVE',['REACX','REACY','REACZ'],wn,'S'),(4,'ACCEL_NATIVE',['AX','AY','AZ','ARX','ARY','ARZ'],range(1,len(x)+1),'A')]:
        L+=[f'/TH/NODE/{gid}',title,''.join(f'{s:>10}' for s in channels)]+[ii(k,0)+f'{prefix}{k}' for k in nodeset]
    L+=['/END'];assert not any(s.startswith(('/RBE3','/ADMAS','/FAIL','/IMPDISP')) for s in L)
    (d/(name+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    for job,end,interval in [(1,cfg['end_ms'],cfg['execution']['history_interval_ms']),(2,cfg['end_ms']+1e-6,1)]:
        E=['/ANIM/DT',ff(0,.002),'/ANIM/MASS','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/DT',ff(c['dt_scale'],0),'/MON/ON','/PRINT/10/100',f'/RUN/{name}/{job}',ff(end),'/TFILE/4',ff(interval),'/VERS/2026']
        (d/(name+f'_000{job}.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8')
    dump(d/'generation.json',{'created_utc':now(),'name':name,'case':c,'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'nodes_mm':x,'moving_nodes':rn,'fixed_nodes':wn,'moving_quads':mq,'wall_quads':wq,'nodal_tributary_area_mm2':areas.tolist(),'contact_groups':cr,'history_records_per_frame':7 if c['contact'] else 6,'analytic_moving_mass_kg':.001112,'K_total_expected_N_mm':float(sum(35000*r['Stfac']*len(r['nodes']) for r in cr)),'contact_surface_flag_expected':1 if c.get('legacy_surface_mode') else 3})
    shutil.copy2(__file__,d/'generator_snapshot.py');print({'built':caseid,'nodes':len(x),'contact_groups':len(cr)},flush=True)

def run(caseid):
    guard();d=OUT/REV/caseid;g=read(d/'generation.json');name=g['name'];e=read(CFG)['execution'];assert not (d/'starter.log').exists()
    for exe,args,log,limit in [('starter_win64.exe',['-i',name+'_0000.rad','-np','1'],'starter.log',e['starter_timeout_s']),('engine_win64.exe',['-i',name+'_0001.rad'],'engine.log',e['engine_timeout_s'])]:
        assert execute(RUNTIME/exe,args,d,log,limit,env()),log
        if log=='starter.log':
            text=(d/log).read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',text)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',text)[-1])==0
    pins={p.name:streamsha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(name+'_0002.rad'),o/(name+'_0002.rad'))
    for p in d.glob(name+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',name+'_0002.rad'],o,'observer.log',60,env());assert all(streamsha(d/n)==v for n,v in pins.items());dump(d/'observer_preservation.json',{'pass':True,'main_outputs_unchanged':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[name+'T01'],d,'converter.log',60,env());recover(caseid)

def recover(caseid):
    guard();d=OUT/REV/caseid;g=read(d/'generation.json');name=g['name'];H=histories(d/(name+'T01.csv'));v=np.column_stack(list(H.values()));r=records(d/(name+'T01'));nr=g['history_records_per_frame'];head=len(r)-len(v)*nr;assert head>0
    frames=[r[head+j*nr:head+(j+1)*nr] for j in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[:2]==[4,88] and all([len(q) for q in f]==sizes for f in frames)
    raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
    rr=records(d/'observer'/(name+'T02'));assert len(rr)==head+nr and [len(q) for q in rr[head:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in rr[head:]]);assert end[0]>v[-1,0]
    with (d/'observer'/(name+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(list(H));w.writerow([format(z,'.9g') for z in end])
    dump(d/'history_recovery.json',{'pass':True,'records_per_frame':nr,'sizes_bytes':sizes,'native_rows_verified':len(v),'native_channels':v.shape[1],'actual_end_ms':float(end[0])});print({'executed':caseid},flush=True)

def batch():
    guard()
    for c in allcases():
        d=OUT/REV/c['id']
        if (d/'history_recovery.json').exists() or list(d.glob('retained_failure_*.json')):continue
        try:build(c['id']);run(c['id'])
        except Exception:
            d.mkdir(parents=True,exist_ok=True);dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'case':c,'traceback':traceback.format_exc(),'no_retry_overwrite':True});print(traceback.format_exc(),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','run','recover','batch']);p.add_argument('--case');a=p.parse_args();globals()[a.action](a.case) if a.case else globals()[a.action]()
