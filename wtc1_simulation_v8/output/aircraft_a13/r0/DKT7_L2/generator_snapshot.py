"""A13 contact and shell witnesses: fresh starts, immutable declarations and native ledgers."""
import argparse, copy, csv, json, re, shutil, subprocess, sys, traceback
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT, RUNTIME, read, dump, sha, rel, now, ff, ii, harness, execute
from run_aircraft_a04 import blocks
from run_aircraft_a06 import env
from run_aircraft_a08 import triangle
from audit_aircraft_a05 import histories, vtk
from recover_aircraft_a05_history import records
from review_aircraft_a08 import binary_mass


CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a13_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a13'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a12'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a11/r0/NOSE_04_DT05'
CHANNELS=['IE','KE','HE','PW','RKE','XMOM','YMOM','ZMOM','MASS']
REV='r0'
def guard():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def allcases():return read(CFG)['execution']['cases']
def contact25(gap):
    # Fixed-width columns follow the 2026 TYPE25 primary documentation.
    # Node group 1 is secondary; surface 3 main, no secondary surface/edge contact.
    return ['/INTER/TYPE25/1','CONSTANT_STIFFNESS_CONTACT',
      ii(3,0,4,0,5,3,0,1000,1000,0),
      ii(1,0)+ff(1,0,1e30,1e30),
      ff(0,1e30)+ii(1000,2)+ff(135,.1),
      ff(1,0,0,0,1e30),
      '   000 000'+ii(0,0,1000)+ff(1e-20),
      ii(0,0)+ff(0)+ii(0,0)+ff(0)+ii(0,0),
      ff(gap,1,gap,1)]

def declare():
    assert not OUT.exists() and not CFG.exists()
    v=harness();assert v['CurrentIteration']=='AIRCRAFT-A12' and v['NextIteration']=='AIRCRAFT-A13'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for r in read(PREV/'preservation_before.json')['files']}
    for r in read(PREV/'preservation_baseline_correction.json')['corrections']:pins[r['path']]=r
    for r in read(PREV/'artifact_manifest.json')['files']:pins[r['path']]=r
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:
        pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'A12_canonical_baseline_corrections_applied':True,'archives_rescanned':False})
    a12=read(ROOT/'wtc1_simulation_v8/data/aircraft_a12_predeclaration.json')
    cases=[]
    for typ in [7,25]:
        for dt in [.05,.025]:cases.append({'id':f'W{typ}_DT{int(dt*1000):03d}','witness':True,'contact':True,'contact_type':typ,'dt_scale':dt,'end_ms':.02})
    cases.insert(0,{'id':'WFREE','witness':True,'contact':False,'contact_type':7,'dt_scale':.05,'end_ms':.02})
    for lev in [0,1,2,3]:cases.append({'id':f'T25_L{lev}','witness':False,'contact':True,'contact_type':25,'simple':False,'fine':lev>0,'refinement_levels':lev,'Istf':4,'Ish3n':2,'dt_scale':.05,'end_ms':.4})
    cases.append({'id':'T25_L2_HALF','witness':False,'contact':True,'contact_type':25,'simple':False,'fine':True,'refinement_levels':2,'Istf':4,'Ish3n':2,'dt_scale':.025,'end_ms':.4})
    for lev in [0,1,2]:cases.append({'id':f'DKT7_L{lev}','witness':False,'contact':True,'contact_type':7,'simple':False,'fine':lev>0,'refinement_levels':lev,'Istf':4,'Ish3n':30,'dt_scale':.05,'end_ms':.4})
    c={**a12,'iteration':'AIRCRAFT-A13','declared_utc':now(),'seed':1102038,'random_draws':0,
       'scope':'Separated high-speed quad witness, TYPE25 node-to-surface radome control and DKT18/TYPE7 shell control. Fresh isolated starts only; no old solver reruns.',
       'parent':rel(PREV),'execution':{**a12['execution'],'cases':cases,'estimated_minutes':[5,15]},
       'witness':{'velocity_m_s':[200,0,0],'mass_kg':.001112,'initial_KE_J':22.24,'initial_P_Ns':.2224,'rebound_J_Ns':.4448,'start_x_mm':-1.01,'gap_mm':1,'end_ms':.02,'source':'A10 saved LAW1 quad 20mm/wall40mm; moving X only, all rotations locked; no RBE3'},
       'witness_acceptance':{'energy_fraction_initial':.01,'momentum_fraction_initial':.01,'support_fraction_initial':.02,'rebound_velocity_fraction':.01,'half_dt_impulse_relative':.01,'half_dt_energy_relative_initial':.005,'free_velocity_m_s':.000001},
       'contact25':{'Istf':4,'Igap':5,'Thickness_s_and_m_mm':5,'Scale_s_and_m':1,'gap_total_mm':5,'Ishape':2,'Iedge':1000,'Igap0':1000,'Inacti':1000,'Stfac':1,'Stmin':0,'Stmax':1e30,'VIS_s':1e-20,'Ipstif':0,'friction':0,'no_fitted_target':True,'different_algorithm_not_same_stiffness_law':True},
       'DKT18_control':{'Ish3n':30,'other_material_geometry_and_contact_unchanged':True,'same_damping_input_1e_20':True,'different_formulation_and_numerical_inertia_allowed':True,'not_a_material_equivalence_claim':True},
       'timing_diagnostic':{'native_acceleration_channels':['AX','AY','AZ','ARX','ARY','ARZ'],'candidates':[0,-.5,.5],'formula':'v_candidate=v_native+candidate*TIME_STEP_native*a_native; same for rotation. Compare all candidates; no fitted shift and no acceptance credit, ledger never changed.','source_binary_equivalence_established':False},
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm'],
       'extension_policy':'No full-aircraft/seconds extension. TYPE25 and DKT are diagnostic controls, not calibrated physical choices.'}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_A13_solver':True})
    import urllib.request
    sd=OUT/'sources';sd.mkdir();sources=[]
    for i,url in enumerate(c['sources']):
        p=sd/f'primary_{i}.html';p.write_bytes(urllib.request.urlopen(url,timeout=60).read());sources.append({'path':rel(p),'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    for p in [PREV/'authoritative_review.json',PARENT/'A11_NOSE_04_DT05_0000.rad',ROOT/'wtc1_simulation_v8/output/aircraft_a10/r1/K1_DT040/A10_K1_DT040_0000.rad',ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a12.py',ROOT/'wtc1_simulation_v8/input/aircraft_a10_sources/c3inmas.F']:
        sources.append({'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'archives_rescanned':False,'NIST_input_dependency_only':True,'NIST_outcomes_target':False})
    print({'declared':len(cases),'preserved_files_pinned':len(pins)},flush=True)
def group(gid,title,ids):
    return [f'/GRNOD/NODE/{gid}',title]+[ii(*ids[k:k+10]) for k in range(0,len(ids),10)]

def build(caseid):
    guard();cfg=read(CFG);c=next(x for x in allcases() if x['id']==caseid)
    
    if c['witness']:return build_witness(c)
    d=OUT/REV/caseid;assert not d.exists();d.mkdir(parents=True);name='A13_'+caseid+'_R0'
    pg=read(PARENT/'generation.json');bs=blocks((PARENT/(pg['name']+'_0000.rad')).read_text().splitlines());orig={q[0]:q for q in bs}
    px=np.array(read(PARENT/'mesh.json')['nodes_mm']);rt=[[int(s[k:k+10]) for k in [0,10,20,30]] for s in orig['/SH3N/21'][1:]]
    wall={}
    for pid in [31,32]:
        q=[[int(s[k:k+10]) for k in [0,10,20,30,40]] for s in orig[f'/SHELL/{pid}'][1:]]
        wall[pid]=[r for r in q if np.max(abs(px[np.array(r[1:])-1,0]+50))<1e-5 and np.max(abs(px[np.array(r[1:])-1].mean(0)[1:]))<=3000]
    assert wall[31] and wall[32]
    ri=sorted({n for r in rt for n in r[1:]});wi=sorted({n for q in wall.values() for r in q for n in r[1:]});assert not set(ri)&set(wi)
    mapping={n:k+1 for k,n in enumerate(ri+wi)};x=px[np.array(ri+wi)-1].tolist();tr=[[mapping[n] for n in r[1:]] for r in rt];quads={p:[[mapping[n] for n in r[1:]] for r in q] for p,q in wall.items()}
    base=x.copy();base_tr=tr.copy();edges={}
    if c['fine']:
        def mid(a,b):
            key=tuple(sorted((a,b)))
            if key not in edges:x.append(((np.array(x[a-1])+x[b-1])/2).tolist());edges[key]=len(x)
            return edges[key]
        for level in range(c.get('refinement_levels',1)):
            fine=[]
            for a,b,z in tr:
                ab,bz,za=mid(a,b),mid(b,z),mid(z,a);fine.extend([[a,ab,za],[ab,b,bz],[za,bz,z],[ab,bz,za]])
            tr=fine
    rn=sorted({n for r in tr for n in r});wn=sorted({n for q in quads.values() for r in q for n in r});assert not set(rn)&set(wn) and len(rn)+len(wn)==len(x)
    area=sum(triangle(np.array(x)[np.array(t)-1])[0] for t in tr);a0=sum(triangle(np.array(base)[np.array(t)-1])[0] for t in base_tr);assert abs(area-a0)/a0<1e-12
    L=['#RADIOSS STARTER','/BEGIN',name,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',name,'/ANALY',ii(0,0,0,0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(k+1)+ff(*q) for k,q in enumerate(x)]
    for key in ['/MAT/LAW2/3','/PROP/TYPE1/31','/PROP/TYPE1/32','/PART/31','/PART/32']:L+=orig[key]
    for p,q in quads.items():L += [f'/SHELL/{p}']+[ii((100000 if p==31 else 200000)+j+1,*t) for j,t in enumerate(q)]
    if not c['simple']:
        for key in ['/MAT/LAW25/4','/MAT/LAW25/5','/PROP/TYPE19/41','/PROP/TYPE19/42','/PROP/TYPE19/43','/PROP/TYPE51/21','/PART/21']:L+=orig[key]
        pi=L.index('/PROP/TYPE51/21');L[pi+2]=L[pi+2][:20]+ii(c['Ish3n'])+L[pi+2][30:]
    else:
        sm=cfg['simple_elastic_control'];L+=['/MAT/LAW1/6','SIMPLE_ELASTIC_AREAL_MASS_CONTROL',ff(sm['rho_g_mm3']),ff(sm['E_MPa'],sm['nu']),'/PROP/TYPE1/21','SIMPLE_RADOME_CONTROL',ii(24,4,2,2),ff(*([1e-20]*5)),ii(5)+' '*10+ff(sm['thickness_mm'],5/6),'/PART/21','SIMPLE_RADOME',ii(21,6,0)]
    L+=['/SH3N/21']+[ii(j+1,*t) for j,t in enumerate(tr)];L+=group(1,'RADOME_ALL',rn)+group(2,'FACADE_FIXED',wn)
    L+=['/BCS/1','ALL_FACADE_NODES_FIXED','   111 111'+ii(0,2),'/INIVEL/TRA/1','RADOME_INITIAL_VELOCITY',ff(*cfg['velocity_m_s'])+ii(1,0),ff(0)+ii(0)]
    if c['contact']:
        contact=copy.deepcopy(orig['/INTER/TYPE7/104']);contact[0]='/INTER/TYPE7/1';contact[1]='RADOME_TO_FIXED_FRONT';contact[2]=ii(1,3,c['Istf'])+contact[2][30:]
        contact[7]=contact[7][:40]+ii(cfg['contact']['Iform'])+contact[7][50:]
        
        if c['contact_type']==25:contact=contact25(cfg['contact']['gap_mm'])
        L+=['/SURF/PART/3','CROPPED_INHERITED_FRONT',ii(31,32)]+contact+['/TH/INTER/1','CONTACT_RAW',''.join(f'{q:>10}' for q in ['FNX','FNY','FNZ','CE_ELAST']),ii(1)]
    L+=['/TH/PART/1','PART_STATE',''.join(f'{q:>10}' for q in CHANNELS),ii(21,31,32),'/TH/NODE/2','NATIVE_NODES',''.join(f'{q:>10}' for q in ['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ'])]
    L += [ii(k+1,0)+f'N{k+1}' for k in range(len(x))]
    L += ['/TH/NODE/3','SUPPORT_NATIVE',''.join(f'{q:>10}' for q in ['REACX','REACY','REACZ'])]+[ii(k,0)+f'S{k}' for k in wn]
    L+=['/TH/NODE/4','ACCEL_NATIVE',''.join(f'{q:>10}' for q in ['AX','AY','AZ','ARX','ARY','ARZ'])]+[ii(k+1,0)+f'A{k+1}' for k in range(len(x))]+['/END']
    assert not any(q.startswith(('/RBE3','/ADMAS','/BEAM','/FAIL','/IMPDISP')) for q in L)
    (d/(name+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,cfg['execution']['animation_interval_ms']),'/ANIM/ELEM/ENER','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/ANIM/SHELL/EPSP/ALL','/ANIM/MASS','/DT',ff(c['dt_scale'],0),'/MON/ON','/PRINT/10/100',f'/RUN/{name}/1',ff(cfg['end_ms']),'/TFILE/4',ff(cfg['execution']['history_interval_ms']),'/VERS/2026']
    (d/(name+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8')
    E2=['/ANIM/DT',ff(0,1),'/ANIM/MASS','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/DT',ff(c['dt_scale'],0),'/MON/ON',f'/RUN/{name}/2',ff(cfg['end_ms']+1e-6),'/TFILE/4',ff(1),'/VERS/2026']
    (d/(name+'_0002.rad')).write_text('\n'.join(E2)+'\n',encoding='utf-8')
    theoretical=np.zeros(len(x))
    for t in tr:
        ar,w=triangle(np.array(x)[np.array(t)-1]);theoretical[np.array(t)-1]+=ar*(.00183*1+.000048*8)*w*.001
    np.savez_compressed(d/'theoretical_radome_mass_SI.npz',nodal_mass_kg=theoretical)
    dump(d/'generation.json',{'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'nodes_mm':x,'radome_nodes':rn,'fixed_nodes':wn,'triangles':tr,'facade_quads':quads,'source_node_mapping':mapping,'history_records_per_frame':7 if c['contact'] else 6,'area_mm2':float(area),'radome_analytic_mass_kg':float(theoretical.sum()),'source_triangles':len(rt),'radome_triangles':len(tr),'no_RBE3':True,'no_ADMAS':True,'no_added_mass':True,'no_erosion':True,'whole_aircraft_impact':False})
    shutil.copy2(__file__,d/'generator_snapshot.py');print({'built':caseid,'nodes':len(x),'triangles':len(tr),'wall_quads':sum(map(len,quads.values()))},flush=True)


def build_witness(c):
    cfg=read(CFG);d=OUT/REV/c['id'];assert not d.exists();d.mkdir(parents=True);name='A13_'+c['id']+'_R0'
    source=ROOT/'wtc1_simulation_v8/output/aircraft_a10/r1/K1_DT040/A10_K1_DT040_0000.rad'
    bs=blocks(source.read_text().splitlines());L=[];x=[]
    for block in bs:
        k=block[0]
        if k.startswith(('/TH/','/INTER/','/SURF/')) or k=='/END':continue
        if k=='/BEGIN':block[1]=name
        if k=='/TITLE':block[1]=name
        if k=='/INIVEL/TRA/1':block[2]=ff(200,0,0)+ii(1,0)
        if k=='/NODE':x=[[float(s[j:j+20]) for j in [10,30,50]] for s in block[1:]]
        L+=block
    if c['contact']:
        ob={b[0]:b for b in bs};contact=ob['/INTER/TYPE7/1'] if c['contact_type']==7 else contact25(1)
        L+=['/SURF/PART/3','FIXED_MAIN',ii(2)]+contact+['/TH/INTER/1','CONTACT_RAW',''.join(f'{q:>10}' for q in ['FNX','FNY','FNZ','CE_ELAST']),ii(1)]
    L+=['/TH/PART/1','PART_STATE',''.join(f'{q:>10}' for q in CHANNELS),ii(1,2),'/TH/NODE/2','NATIVE_NODES',''.join(f'{q:>10}' for q in ['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ'])]+[ii(k,0)+f'N{k}' for k in range(1,9)]
    L+=['/TH/NODE/3','SUPPORT_NATIVE',''.join(f'{q:>10}' for q in ['REACX','REACY','REACZ'])]+[ii(k,0)+f'S{k}' for k in range(5,9)]
    L+=['/TH/NODE/4','ACCEL_NATIVE',''.join(f'{q:>10}' for q in ['AX','AY','AZ','ARX','ARY','ARZ'])]+[ii(k,0)+f'A{k}' for k in range(1,9)]+['/END']
    (d/(name+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    for job,end,interval in [(1,c['end_ms'],.000001),(2,c['end_ms']+1e-6,1)]:
        E=['/ANIM/DT',ff(0,.002),'/ANIM/MASS','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/DT',ff(c['dt_scale'],0),'/MON/ON','/PRINT/10/100',f'/RUN/{name}/{job}',ff(end),'/TFILE/4',ff(interval),'/VERS/2026']
        (d/(name+f'_000{job}.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8')
    dump(d/'generation.json',{'name':name,'case':c,'created_utc':now(),'nodes_mm':x,'radome_nodes':[1,2,3,4],'fixed_nodes':[5,6,7,8],'triangles':[],'radome_analytic_mass_kg':.001112,'history_records_per_frame':7 if c['contact'] else 6,'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__))})
    shutil.copy2(__file__,d/'generator_snapshot.py');print({'built':c['id']},flush=True)
def run(caseid):
    guard();d=OUT/REV/caseid;g=read(d/'generation.json');name=g['name'];e=read(CFG)['execution'];assert not (d/'starter.log').exists()
    for exe,args,log,limit in [('starter_win64.exe',['-i',name+'_0000.rad','-np','1'],'starter.log',e['starter_timeout_s']),('engine_win64.exe',['-i',name+'_0001.rad'],'engine.log',e['engine_timeout_s'])]:
        assert execute(RUNTIME/exe,args,d,log,limit,env()),log
        if log=='starter.log':
            txt=(d/log).read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1])==0,txt[-4000:]
    pins={p.name:sha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(name+'_0002.rad'),o/(name+'_0002.rad'))
    for p in d.glob(name+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',name+'_0002.rad'],o,'observer.log',60,env())
    assert all(sha(d/n)==s for n,s in pins.items());dump(d/'observer_preservation.json',{'pass':True,'main_outputs_unchanged':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[name+'T01'],d,'converter.log',60,env())
    recover(caseid)

def recover(caseid):
    guard();d=OUT/REV/caseid;g=read(d/'generation.json');name=g['name'];o=d/'observer';assert not (d/'history_recovery.json').exists()
    H=histories(d/(name+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(name+'T01'));nr=g['history_records_per_frame'];header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    nat=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert nat.shape==v.shape and np.allclose(nat,v,rtol=6e-7,atol=1e-12)
    ro=records(o/(name+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (o/(name+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:
        wr=csv.writer(f);wr.writerow(list(H));wr.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'records_per_frame':nr,'generator_record_count':g['history_records_per_frame'],'schema_metadata_corrected':nr!=g['history_records_per_frame'],'sizes_bytes':sizes,'native_rows_verified':len(v),'native_channels':v.shape[1],'actual_end_ms':float(end[0]),'recovery_used_saved_native_outputs_no_solver_rerun':True});print({'executed':caseid},flush=True)


def batch():
    guard()
    for c in allcases():
        d=OUT/REV/c['id']
        if (d/'history_recovery.json').exists() or list(d.glob('retained_failure_*.json')):continue
        try:
            assert not d.exists(),'Existing incomplete case requires explicit new revision; never overwrite.'
            build(c['id']);run(c['id'])
        except Exception:
            d.mkdir(parents=True,exist_ok=True)
            dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc(),'case':c,'no_retry_overwrite':True})
            print({'retained_case_failure':c['id'],'traceback':traceback.format_exc()},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','batch','build','run','recover']);p.add_argument('--case');a=p.parse_args()
    globals()[a.action](a.case) if a.case else globals()[a.action]()
