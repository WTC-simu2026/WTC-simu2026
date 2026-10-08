"""A12 isolated nose witness: fresh starts, immutable declarations and native ledgers."""
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

CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a12_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a12'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a11'
PARENT=PREV/'r0/NOSE_04_DT05'
CHANNELS=['IE','KE','HE','PW','RKE','XMOM','YMOM','ZMOM','MASS']

def guard():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def group(gid,title,ids):
    return [f'/GRNOD/NODE/{gid}',title]+[ii(*ids[k:k+10]) for k in range(0,len(ids),10)]

def declare():
    assert not OUT.exists() and not CFG.exists()
    v=harness();assert v['CurrentIteration']=='AIRCRAFT-A11' and v['NextIteration']=='AIRCRAFT-A12'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    state=read(ROOT/'harness/state.json')
    def walk(x):
        if isinstance(x,dict):return sum(walk(y) for y in x.values())
        if isinstance(x,list):return sum(walk(y) for y in x)
        return 1
    dump(OUT/'full_state_read_coverage.json',{'sha256':sha(ROOT/'harness/state.json'),'fields':{k:walk(x) for k,x in state.items()},'current':state['current_iteration'],'next':state['next_iteration']})
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:
        pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    parallel=ROOT/'wtc1_simulation_v8/output/aircraft_a11_boeing_parallel'
    for folder in [parallel,parallel/'native_adapter_v2']:
        for fn in ['artifact_manifest.json','delivery_verification.json','integration_ready.json']:
            p=folder/fn
            pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
        for r in read(folder/'artifact_manifest.json')['files']:pins[r['path']]=r
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archive_rescanned':False})
    cases=[{'id':'FREE','contact':False,'simple':False,'fine':False,'Istf':4,'dt_scale':.1},
           {'id':'SAND','contact':True,'simple':False,'fine':False,'Istf':4,'dt_scale':.1},
           {'id':'SAND_HALF','contact':True,'simple':False,'fine':False,'Istf':4,'dt_scale':.05},
           {'id':'SAND_FINE','contact':True,'simple':False,'fine':True,'Istf':4,'dt_scale':.05},
           {'id':'SAND_SERIES','contact':True,'simple':False,'fine':False,'Istf':5,'dt_scale':.05},
           {'id':'SIMPLE','contact':True,'simple':True,'fine':False,'Istf':4,'dt_scale':.05},
           {'id':'SIMPLE_FINE','contact':True,'simple':True,'fine':True,'Istf':4,'dt_scale':.05}]
    c={'iteration':'AIRCRAFT-A12','declared_utc':now(),'seed':1102037,'random_draws':0,
       'scope':'Isolated inherited 216-triangle radome, root free, no airframe/RBE3/ADMAS/beams. Cropped inherited front facade shell segments, ALL facade nodes fixed. Numerical witness only, no equivalence with coupled aircraft.',
       'parent':rel(PARENT),'velocity_m_s':[-200,5,2],'end_ms':.4,
       'units':{'native':'g mm ms MPa N','g_to_kg':.001,'mm_to_m':.001,'ms_to_s':.001,'native_energy_to_J':.001,'native_impulse_to_Ns':.001,'native_rotation_to_rad_s':1000},
       'geometry':{'facade_front_x_mm':-50,'facade_crop_centroid_abs_y_z_mm':3000,'only_front_quads':True,'all_facade_nodes_fixed':True,'radome_root':'free, deliberately removes airframe constraint','mesh_refinement':'all three edges bisected, 4 coplanar children, shared midpoints, no smoothing'},
       'material':'LAW25/TYPE51/TYPE19 unchanged in sandwich witnesses; failure, core crushing and delamination disabled.',
       'simple_elastic_control':{'law':'LAW1','E_MPa':22000,'nu':.25,'thickness_mm':9,'rho_g_mm3':(.00183*1+.000048*8)/9,'same_areal_mass':True,'membrane_bending_shear_not_equivalent':True,'not_transferred_to_aircraft':True},
       'contact':{'type':7,'Stfac':1,'gap_mm':5,'friction':0,'VIS_s':1e-20,'VIS_F':1,'Inacti':1000,'Iform':2,'Istf_cases':[4,5],'no_adjustment':True,'self_contact':False,'not_a_physical_contact_selection':True},
       'energy_contract':{'native_global_rotation_counted_once':True,'native_part_RKE_not_added':True,'plastic_work_already_in_IE':True,'spring_channel_zero_expected':True,'ledger':['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '],'native_inertia_dynamic_reconstruction':'exploratory only; never used to fix residual'},
       'acceptance':{'starter_errors':0,'starter_warnings':0,'mass_relative':1e-6,'added_mass_fraction':1e-9,'energy_global_fraction_initial':.005,'energy_local_fraction_generated':.05,'energy_precision_J':1,'local_generated_min_J':100,'momentum_absolute_Ns':.01,'momentum_relative':.02,'free_velocity_error_m_s':.001,'free_displacement_error_mm':.02,'half_dt_impulse_relative':.05,'half_dt_generated_relative':.10,'mesh_impulse_relative':.10,'mesh_generated_relative':.10,'native_csv_relative':6e-7,'native_csv_absolute':1e-12,'independent_KE_change_absolute_J':1,'independent_KE_change_fraction_generated':.005,'independent_mass_relative':1e-6,'native_part_vs_global_IE_relative':1e-5},
       'inherited_A11_gates_unchanged':read(ROOT/'wtc1_simulation_v8/data/aircraft_a11_predeclaration.json')['acceptance'],
       'execution':{'cases':cases,'starter_timeout_s':120,'engine_timeout_s':180,'converter_timeout_s':60,'CPU_threads':2,'GPU':False,'history_interval_ms':.0005,'animation_interval_ms':.025,'estimated_minutes':[3,10]},
       'extension_policy':'No coupled 1ms or seconds extension in A12. New declared parent required after diagnosing witness and completing spatial gates.',
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type1_shell_starter_r.htm'],
       'NIST_facade_input_dependency':True,'NIST_outcomes_used_as_target':False,'physical_impact_qualified':False,'seconds_impact_calculated':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'sha256':sha(CFG),'before_new_solver':True,'created_utc':now()})
    paths=[PARENT/n for n in ['generation.json','mesh.json','A11_NOSE_04_DT05_0000.rad']]+[PREV/'authoritative_review.json',ROOT/'wtc1_simulation_v8/input/aircraft_a10_sources/c3inmas.F']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths],'primary_links':c['sources'],'inherited_material_sources':'A11 -> A05, no Boeing material identification','source_binary_equivalence_established':False,'archive_rescanned':False})
    print({'declared':'A12','old_files_pinned':len(pins),'cases':[q['id'] for q in cases]},flush=True)

def build(caseid):
    guard();cfg=read(CFG);c=next(x for x in cfg['execution']['cases'] if x['id']==caseid)
    d=OUT/'r0'/caseid;assert not d.exists();d.mkdir(parents=True);name='A12_'+caseid
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
    else:
        sm=cfg['simple_elastic_control'];L+=['/MAT/LAW1/6','SIMPLE_ELASTIC_AREAL_MASS_CONTROL',ff(sm['rho_g_mm3']),ff(sm['E_MPa'],sm['nu']),'/PROP/TYPE1/21','SIMPLE_RADOME_CONTROL',ii(24,4,2,2),ff(*([1e-20]*5)),ii(5)+' '*10+ff(sm['thickness_mm'],5/6),'/PART/21','SIMPLE_RADOME',ii(21,6,0)]
    L+=['/SH3N/21']+[ii(j+1,*t) for j,t in enumerate(tr)];L+=group(1,'RADOME_ALL',rn)+group(2,'FACADE_FIXED',wn)
    L+=['/BCS/1','ALL_FACADE_NODES_FIXED','   111 111'+ii(0,2),'/INIVEL/TRA/1','RADOME_INITIAL_VELOCITY',ff(*cfg['velocity_m_s'])+ii(1,0),ff(0)+ii(0)]
    if c['contact']:
        contact=copy.deepcopy(orig['/INTER/TYPE7/104']);contact[0]='/INTER/TYPE7/1';contact[1]='RADOME_TO_FIXED_FRONT';contact[2]=ii(1,3,c['Istf'])+contact[2][30:]
        contact[7]=contact[7][:40]+ii(cfg['contact']['Iform'])+contact[7][50:]
        L+=['/SURF/PART/3','CROPPED_INHERITED_FRONT',ii(31,32)]+contact+['/TH/INTER/1','CONTACT_RAW',''.join(f'{q:>10}' for q in ['FNX','FNY','FNZ','CE_ELAST']),ii(1)]
    L+=['/TH/PART/1','PART_STATE',''.join(f'{q:>10}' for q in CHANNELS),ii(21,31,32),'/TH/NODE/2','NATIVE_NODES',''.join(f'{q:>10}' for q in ['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ','REACX','REACY','REACZ'])]
    L += [ii(k+1,0)+f'N{k+1}' for k in range(len(x))]+['/END']
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
    dump(d/'generation.json',{'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'nodes_mm':x,'radome_nodes':rn,'fixed_nodes':wn,'triangles':tr,'facade_quads':quads,'source_node_mapping':mapping,'history_records_per_frame':6 if c['contact'] else 5,'area_mm2':float(area),'radome_analytic_mass_kg':float(theoretical.sum()),'source_triangles':len(rt),'radome_triangles':len(tr),'no_RBE3':True,'no_ADMAS':True,'no_added_mass':True,'no_erosion':True,'whole_aircraft_impact':False})
    shutil.copy2(__file__,d/'generator_snapshot.py');print({'built':caseid,'nodes':len(x),'triangles':len(tr),'wall_quads':sum(map(len,quads.values()))},flush=True)

def run(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');name=g['name'];e=read(CFG)['execution'];assert not (d/'starter.log').exists()
    for exe,args,log,limit in [('starter_win64.exe',['-i',name+'_0000.rad','-np','1'],'starter.log',e['starter_timeout_s']),('engine_win64.exe',['-i',name+'_0001.rad'],'engine.log',e['engine_timeout_s'])]:
        assert execute(RUNTIME/exe,args,d,log,limit,env()),log
        if log=='starter.log':
            txt=(d/log).read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1])==0,txt[-4000:]
    pins={p.name:sha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(name+'_0002.rad'),o/(name+'_0002.rad'))
    for p in d.glob(name+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',name+'_0002.rad'],o,'observer.log',60,env())
    assert all(sha(d/n)==s for n,s in pins.items());dump(d/'observer_preservation.json',{'pass':True,'main_outputs_unchanged':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[name+'T01'],d,'converter.log',60,env())
    H=histories(d/(name+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(name+'T01'));nr=g['history_records_per_frame'];header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    nat=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert nat.shape==v.shape and np.allclose(nat,v,rtol=6e-7,atol=1e-12)
    ro=records(o/(name+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (o/(name+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:
        wr=csv.writer(f);wr.writerow(list(H));wr.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'records_per_frame':nr,'sizes_bytes':sizes,'native_rows_verified':len(v),'native_channels':v.shape[1],'actual_end_ms':float(end[0])});print({'executed':caseid},flush=True)

def audit(caseid):
    guard();cfg=read(CFG);a=cfg['acceptance'];d=OUT/'r0'/caseid;g=read(d/'generation.json');name=g['name'];assert not (d/'review.json').exists()
    H=histories(d/(name+'T01.csv'));Ho=histories(d/'observer'/(name+'T02_recovered.csv'));assert list(H)==list(Ho);H={k:np.r_[v,Ho[k][0]] for k,v in H.items()};T=H['time'];nn=len(g['nodes_mm'])
    nk=[k for k in H if k.startswith('NATIVE_NODES')];ids=[int(re.search(r'NATIVE_NODES\s+(\d+)\s+N',k).group(1)) for k in nk[::12]];assert len(nk)==nn*12 and set(ids)==set(range(1,nn+1))
    for j,n in enumerate(ids):assert all(re.search(r'\s'+str(n)+r'\s+N'+str(n)+r'\s',k) for k in nk[j*12:j*12+12])
    nodes=np.column_stack([H[k] for k in nk]).reshape(len(T),nn,12);order=np.argsort(ids);nodes=nodes[:,order,:]
    rn=np.array(g['radome_nodes'])-1;wn=np.array(g['fixed_nodes'])-1
    pkeys=[k for k in H if k.startswith(('REFERENCE_RADOME','SIMPLE_RADOME'))];assert len(pkeys)==9
    # CSV native title for RKE/XMOM/... may be var 5 etc. Save actual order; use global ledger only.
    P=np.column_stack([H[q+'-MOMENTUM'] for q in 'XYZ'])*.001
    J=np.column_stack([H[k] for k in H if k.startswith('CONTACT_RAW')][:3])*.001 if g['case']['contact'] else np.zeros((len(T),3));J-=J[0]
    Js=nodes[:,wn,9:12].sum(1)*.001;Js-=Js[0]
    terms={k:H[k]*.001 for k in cfg['energy_contract']['ledger']};E=sum(terms.values());res=E-E[0]-H['EXTERNAL WORK']*.001;generated=sum(v for k,v in terms.items() if k!='KINETIC ENERGY')
    local=generated>a['local_generated_min_J'];tol=a['energy_local_fraction_generated']*abs(generated)+a['energy_precision_J']
    animations=[p for p in d.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name)]+[p for p in (d/'observer').glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',p.name)]
    times=[];D=[];V=[];mass=None;proofs=[];top=None;eps=[]
    for p in animations:
        q=vtk(subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',check=True,timeout=60).stdout)
        if (times and abs(q['time']-times[-1])<1e-6) or q['time']>T[-1]+1e-5:continue
        ix=np.argsort(q['NODE_ID']);assert np.array_equal(q['NODE_ID'][ix],np.arange(1,nn+1));nm,pr=binary_mass(p,q)
        if mass is None:mass=nm
        else:assert np.array_equal(mass,nm)
        snap={k:q[k] for k in ['ELEMENT_ID','PART_ID','cells','types']}
        if top is None:top=snap
        else:assert all(np.array_equal(top[k],snap[k]) for k in top)
        times.append(q['time']);D.append(q['Displacement'].reshape(-1,3)[ix]*.001);V.append(q['Velocity'].reshape(-1,3)[ix]);proofs.append({'path':rel(p),**pr})
        ek=next((k for k in q if 'plastic' in k.lower()),None);eps.append(float(np.max(abs(q[ek]))) if ek else None)
    times=np.array(times);D=np.array(D);V=np.array(V);K=.5*np.sum(mass[None,:,None]*V*V,axis=(1,2));Km=np.interp(times,T,terms['KINETIC ENERGY']);keerr=(K-K[0])-(Km-Km[0]);pn=np.sum(mass[None,:,None]*V,axis=1);pm=np.column_stack([np.interp(times,T,P[:,i]) for i in range(3)]);perr=(pn-pn[0])-(pm-pm[0])
    mx=float(np.max(np.linalg.norm(J,axis=1)));ptol=a['momentum_absolute_Ns']+a['momentum_relative']*mx
    masserr=abs(float(mass[rn].sum())-g['radome_analytic_mass_kg'])/g['radome_analytic_mass_kg'];theory=np.load(d/'theoretical_radome_mass_SI.npz')['nodal_mass_kg'];nodalerr=float(np.max(abs(mass[rn]-theory[rn])))/max(float(np.max(theory)),1e-30)
    partIE=sum(H[k] for k in H if k.strip().endswith(' IE'))*.001
    freeV=float(np.max(abs(nodes[:,rn,3:6]-cfg['velocity_m_s'])));freeD=float(np.max(abs(nodes[:,rn,:3]-T[:,None,None]*np.array(cfg['velocity_m_s']))))
    checks={'native_CSV_all_channels_verified':read(d/'history_recovery.json')['pass'],'starter_zero_errors_warnings':True,'normal_engine_termination':'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace').upper(),'observer_outputs_preserved':read(d/'observer_preservation.json')['pass'],'finite_monotone_history':bool(np.all(np.isfinite(np.column_stack(list(H.values())))) and np.all(np.diff(T)>0)),'native_mass_preserved':True,'analytic_radome_mass':masserr<=a['mass_relative'],'native_nodal_mass_lumping':nodalerr<=a['independent_mass_relative'],'zero_added_mass':float(np.max(abs(H['DM/M'])))<=a['added_mass_fraction'],'connectivity_preserved':True,'supports_fixed':float(np.max(abs(nodes[:,wn,:9])))<=1e-10,'no_external_work':float(np.max(abs(H['EXTERNAL WORK'])))<=1e-8,'no_plastic_work':float(np.max(abs(H['PLASTIC WORK'])))<=1e-8,'zero_spring_channel':float(np.max(abs(terms['SPRING ENERGY'])))<=1e-8,'energy_global':float(np.max(abs(res)))<=a['energy_global_fraction_initial']*E[0],'energy_local':bool(np.all(abs(res[local])<=tol[local])),'momentum_support':float(np.max(np.linalg.norm(P-P[0]-Js,axis=1)))<=ptol,'momentum_contact_support':float(np.max(np.linalg.norm(J+Js,axis=1)))<=ptol,'independent_translation_KE_change':float(np.max(abs(keerr)))<=a['independent_KE_change_absolute_J']+a['independent_KE_change_fraction_generated']*float(np.max(abs(generated))),'independent_momentum_change':float(np.max(np.linalg.norm(perr,axis=1)))<=ptol,'part_IE_matches_global_IE':float(np.max(abs(partIE-terms['INTERNAL ENERGY'])))<=a['native_part_vs_global_IE_relative']*max(float(np.max(abs(terms['INTERNAL ENERGY']))),1)+1e-6}
    if not g['case']['contact']:checks.update(free_velocity=freeV<=a['free_velocity_error_m_s'],free_displacement=freeD<=a['free_displacement_error_mm'])
    onset=np.flatnonzero(np.linalg.norm(J,axis=1)>0)
    r={'case':g['case'],'created_utc':now(),'checks':{k:bool(v) for k,v in checks.items()},'all_checks_pass':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'actual_end_ms':float(T[-1]),'onset_ms':float(T[onset[0]]) if len(onset) else None,'radome_mass_kg':float(mass[rn].sum()),'analytic_mass_relative_error':masserr,'nodal_mass_relative_error':nodalerr,'initial_KE_J':float(terms['KINETIC ENERGY'][0]),'final_impulse_Ns':J[-1].tolist(),'final_generated_J':float(generated[-1]),'max_energy_residual_J':float(np.max(abs(res))),'final_energy_residual_J':float(res[-1]),'max_local_residual_fraction':float(np.max(abs(res[local])/generated[local])) if np.any(local) else None,'max_independent_KE_change_error_J':float(np.max(abs(keerr))),'max_independent_momentum_error_Ns':float(np.max(np.linalg.norm(perr,axis=1))),'native_global_rotation_J':float(terms['ROTATION ENERGY'][-1]),'native_part_channels':pkeys,'native_part_RKE_qualified':False,'native_inertia_reconstructed':False,'physical_impact_qualified':False,'full_aircraft_extension_allowed':False,'seconds_impact_calculated':False,'native_animation_states':len(times),'plastic_strain_samples':eps}
    np.savez_compressed(d/'balance_history_SI.npz',time_ms=T,residual_J=res,generated_J=generated,impulse_Ns=J,support_Ns=Js,momentum_Ns=P,native_rotation_J=terms['ROTATION ENERGY'],native_kinetic_J=terms['KINETIC ENERGY'],native_internal_J=terms['INTERNAL ENERGY'],native_contact_J=terms['ELASTIC CONTACT ENERGY'],native_nodal_velocity_m_s=nodes[:,:,3:6],native_nodal_rotation_rad_s=nodes[:,:,6:9]*1000)
    np.savez_compressed(d/'verified_states_SI.npz',time_ms=times,displacement_m=D,velocity_m_s=V,nodal_mass_kg=mass,initial_position_m=np.array(g['nodes_mm'])*.001,radome_triangles=np.array(g['triangles'])-1,radome_nodes=rn,fixed_nodes=wn,independent_KE_J=K,independent_momentum_Ns=pn)
    dump(d/'native_mass_reader_proofs.json',{'proofs':proofs});dump(d/'review.json',r)
    print({k:r[k] for k in ['case','failed_checks','actual_end_ms','final_impulse_Ns','final_generated_J','final_energy_residual_J','max_local_residual_fraction']},flush=True)

def batch():
    guard()
    for c in read(CFG)['execution']['cases']:
        caseid=c['id'];print({'starting':caseid},flush=True)
        try:
            build(caseid);run(caseid);audit(caseid)
        except Exception:
            d=OUT/'r0'/caseid;dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'case':caseid,'no_retry_overwrite':True});print(traceback.format_exc(),flush=True);raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','run','audit','batch']);p.add_argument('--case',default='FREE');a=p.parse_args();globals()[a.action](a.case) if a.action in ['build','run','audit'] else globals()[a.action]()
