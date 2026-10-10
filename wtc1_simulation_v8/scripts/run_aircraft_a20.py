"""Declared finite 3D honeycomb mechanics; preserve all older evidence."""
import argparse, json, re, shutil, subprocess, traceback, urllib.request
from pathlib import Path
import numpy as np
from run_aircraft_a19 import ROOT, RUNTIME, read, dump, rel, now, harness, execute, env, streamsha, ff, ii
from test_aircraft_a19_triangles import histories
from audit_aircraft_a05 import vtk
from audit_aircraft_a02 import numbers_after
from diagnose_aircraft_a19_cached import fast
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a20'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a20_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a19'
SOURCE=PREV/'r0/DKT_S3_20'

def guard(): assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
    assert not OUT.exists() and not CFG.exists()
    v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A19'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:
        pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    p=ROOT/'wtc1_simulation_v8/input/aircraft_a05_sources/hrh10_eu.pdf'
    c={'iteration':'AIRCRAFT-A20','declared_utc':now(),'seed':1102045,'random_draws':0,
       'goal':{'physical_duration_s':10,'complete':False,'last_whole_horizon_s':.0200002174},
       'scope':'Replace the radome unfailed shell core by a finite-thickness, finite-yield 3D honeycomb. Native implementation controls before fresh whole integration. No historical damage fitting.',
       'reference':{'path':rel(p),'sha256':streamsha(p),'page':4,'grade':'HRH10-3.2-48','rho_kg_m3':48,'E33_MPa':138,'G31_MPa':41,'G23_MPa':24,'tau31_MPa':1.21,'tau23_MPa':.69,'bare_compression33_MPa':2.07,'test_thickness_mm':12.7,'typical_room_temperature':True,'AA11_material_identified':False},
       'core':{'law':'LAW28','property':'TYPE6','Isolid':14,'Ismstr':4,'Icpre':3,'Gauss':222,'Iorth':0,
         'rho_g_mm3':4.8e-5,'E_MPa':[1,1,138],'G_MPa':[.5,24,41],
         'yield_MPa':[.1,.1,2.07,.05,.69,1.21],
         'failure_normal':[.2,.2,.05],'failure_shear':[.1,.06,.06],
         'failure_strain_interpretation':'Test actual native deletion; documentation labels plastic/total inconsistently. Do not assume measured elongation.',
         'yield_curve':'constant positive plateau over signed strain -2..2; no measured postpeak or densification curve',
         'unmeasured':['E11','E22','G12','yield11','yield22','yield12','all failure strains','postpeak','fracture energy','strain-rate dependence'],
         'failure_sensitivity_shear':[.03,.06,.12],'whole_baseline_shear_failure':.06,
         'thickness_mm':8,'E11_E22_G12_inherited_placeholders':True,'uncoupled_orthotropy_model_change':True,
         'bulk_viscosity':[1.1,.05],'no_added_or_scaled_mass':True,'physical_G_measured':False},
       'witness':{'length_xy_mm':10,'thickness_mm':8,'time_ms':[0,.25,.5,.75,1],
         'paths':{'L':[0,.015,0,.15,.15],'W':[0,.015,0,.15,.15],'C':[0,.005,0,.2,.2]},
         'cases':['SHEAR_L','SHEAR_W','CRUSH','ROTATION','SHEAR_L_HALF','SHEAR_L_LOW','SHEAR_L_HIGH'],
         'duration_ms':1,'dt_cap_ms':.000025,'history_dt_ms':.001,'anim_dt_ms':.025,
         'input_curve_dt_ms':.0001,'CPU_threads':2,'engine_cap_s':120,
         'acceptance':{'elastic_energy_fraction':.02,'yield_fraction':.03,'energy_balance_fraction':.02,'absolute_energy_J':.0001,'mass_relative':1e-6,'rotation_IE_J':.0001,'half_dt_energy_fraction':.01}},
       'integration':'Separate declaration after passing native core controls. Full skin/core coupling, external/contact meshes and mass moments audited before any whole Engine.',
       'old_solver_reruns':0,'sources_read_only':True,'NIST_outcomes_used_as_target':False,'physical_impact_qualified':False,
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law28_honeycomb_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm']}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'sha256':streamsha(CFG),'created_utc':now(),'before_any_A20_native_execution':True})
    sd=OUT/'sources';sd.mkdir();src=[]
    for i,url in enumerate(c['sources']):
        q=sd/f'primary_{i}.html';q.write_bytes(urllib.request.urlopen(url,timeout=45).read());src.append({'path':rel(q),'url':url,'sha256':streamsha(q),'bytes':q.stat().st_size,'redistribution':'exclude_third_party'})
    for q in [p,PREV/'whole_fragment_diagnostic.json',PREV/'core_shear_review.json',PREV/'source_inspection.json',SOURCE/'mesh.json',SOURCE/'generation.json']:
        src.append({'path':rel(q),'sha256':streamsha(q),'bytes':q.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':src,'archive_rescanned':False,'no_new_historical_video_analysis':True})
    print({'declared':'AIRCRAFT-A20','old_files_pinned':len(pins)},flush=True)

def material(mid=28,curve_base=280,fail_shear=None):
    c=read(CFG)['core'];fails=list(c['failure_shear'])
    if fail_shear is not None: fails[1:]=[fail_shear,fail_shear]
    L=[f'/MAT/LAW28/{mid}','REFERENCE_HONEYCOMB_FINITE_YIELD_UNMEASURED_FAILURE',ff(c['rho_g_mm3']),ff(*c['E_MPa']),ff(*c['G_MPa']),
       ii(curve_base,curve_base+1,curve_base+2,1)+ff(1,1,1),ff(*c['failure_normal']),
       ii(curve_base+3,curve_base+4,curve_base+5,1)+ff(1,1,1),ff(*fails)]
    for j,y in enumerate(c['yield_MPa']):
        L += [f'/FUNCT/{curve_base+j}',f'CONSTANT_YIELD_{j}']+[ff(x,y) for x in [-2,0,2]]
    return L

def solid_property(pid=28,skew=28,vec=(1,0,0),ip=0):
    c=read(CFG)['core']
    return [f'/PROP/TYPE6/{pid}','FINITE_3D_CORE_FULL_INTEGRATION',ii(c['Isolid'],c['Ismstr'])+' '*10+ii(c['Icpre'],0,c['Gauss'],0,2)+ff(0),
        ff(*c['bulk_viscosity'],.1),ff(*vec)+ii(skew,ip,0),ff(0,0,0,0),ff(0,0,0,0,0),ii(0,0,2)]

def skew_card(sid,x=(1,0,0),y=(0,1,0)):
    # Radioss takes Y and Z, not X and Y. x/y arguments define the intended material L/W axes.
    z=np.cross(x,y)
    return [f'/SKEW/FIX/{sid}','CORE_L_W_NORMAL_ORIENTATION',ff(0,0,0),ff(*y),ff(*z.tolist())]

def smooth_path(ts,values):
    c=read(CFG)['witness'];out=np.zeros_like(ts)
    for ta,tb,a,b in zip(c['time_ms'][:-1],c['time_ms'][1:],values[:-1],values[1:]):
        mask=(ts>=ta)&(ts<=tb);u=(ts[mask]-ta)/(tb-ta);out[mask]=a+(b-a)*(3*u*u-2*u*u*u)
    return out

def witness(cid,revision='w2',load_values=None):
    guard();c=read(CFG);w=c['witness'];d=OUT/revision/cid;n='A20_'+cid;assert not d.exists();d.mkdir(parents=True)
    xyz=np.array([[0,0,0],[10,0,0],[10,10,0],[0,10,0],[0,0,8],[10,0,8],[10,10,8],[0,10,8]],float)
    mode='R' if cid=='ROTATION' else 'C' if cid=='CRUSH' else 'W' if cid=='SHEAR_W' else 'L'
    fs=.03 if cid=='SHEAR_L_LOW' else .12 if cid.startswith('SHEAR_L_HIGH') else .06
    ts=np.linspace(0,1,10001);disp=np.zeros((len(ts),8,3))
    if mode=='R':
        a=np.pi/2*(3*ts*ts-2*ts**3);disp[:,:,0]=xyz[None,:,0]*np.cos(a[:,None])+xyz[None,:,2]*np.sin(a[:,None])-xyz[None,:,0]
        disp[:,:,2]=-xyz[None,:,0]*np.sin(a[:,None])+xyz[None,:,2]*np.cos(a[:,None])-xyz[None,:,2]
    else:
        strain=smooth_path(ts,w['paths'][mode] if load_values is None else load_values);ax={'L':0,'W':1,'C':2}[mode];disp[:,:,ax]=strain[:,None]*xyz[None,:,2]*(-1 if mode=='C' else 1)
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*x) for i,x in enumerate(xyz)]
    L+=material(fail_shear=fs)+skew_card(28)+solid_property()+['/PART/28','FINITE_3D_HONEYCOMB',ii(28,28,0),'/BRICK/28',ii(1,1,2,3,4,5,6,7,8)]
    fid=1000
    for ni in range(1,9):
        L += [f'/GRNOD/NODE/{ni}',f'NODE_{ni}',ii(ni)]
        for ax,direction in enumerate('XYZ'):
            fid+=1;L += [f'/FUNCT/{fid}',f'AFFINE_{ni}_{direction}']+[ff(t,v) for t,v in zip(ts,disp[:,ni-1,ax])]+[f'/IMPDISP/{fid}',f'AFFINE_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L += ['/TH/PART/28','CORE_PART',''.join(f'{q:>10}' for q in ['IE','KE','HE','PW']),ii(28),'/TH/NODE/28','CORE_NODES',''.join(f'{q:>10}' for q in ['DX','DY','DZ','REACX','REACY','REACZ'])]+[ii(i,0) for i in range(1,9)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    dt=w['dt_cap_ms']*(.5 if cid=='SHEAR_L_HALF' else 1)
    E=['/ANIM/DT',ff(0,w['anim_dt_ms']),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/BRICK/TENS/STRESS','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(dt,dt),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(w['history_dt_ms']),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py')
    dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'mode':mode,'failure_shear':fs,'load_values':load_values,'expected_volume_mm3':800,'expected_mass_g':.0384,'nodes_mm':xyz.tolist(),'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__)),'instrument_masses':False})
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env());s=(d/'starter.log').read_text(errors='replace')
        warnings=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':warnings,'errors':errors,'pass':ok and warnings==0 and errors==0});assert ok and warnings==0 and errors==0,s[-4000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',120,env());assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace')
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());review_witness(d,n)
    except Exception:
        dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'physical_impact_qualified':False});raise

def review_witness(d,n):
    g=read(d/'generation.json');c=read(CFG);w=c['witness'];H=histories(d/(n+'T01.csv'));IE=H['INTERNAL ENERGY']*.001;total=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;ew=H['EXTERNAL WORK']*.001;res=total-total[0]-ew;scale=max(float(abs(total).max()),float(abs(ew).max()))
    mass=H['MASS']*.001;frames=sorted(p for p in d.glob(n+'A*') if re.fullmatch(re.escape(n)+r'A\d{3}',p.name));states=[]
    for p in frames:
        pp=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,text=True,encoding='utf-8',timeout=120,check=True);q=vtk(pp.stdout)
        # Keep tiny independent native-converter evidence rather than assuming a shell-prefix layout for bricks.
        if p==frames[0] or p==frames[-1]:(d/(p.name+'.vtk')).write_text(pp.stdout,encoding='utf-8')
        stress=next((q[k].reshape(-1,3,3)[0] for k in q if k.startswith('3DELEM_Stress')),np.zeros((3,3)))
        # Converter omits nodal mass; binary prefix retains all8 nodal masses even with zero shells.
        b=fast(p);assert np.array_equal(np.sort(b['nid']),np.arange(1,9));nm=b['node_mass_g'][np.argsort(b['nid'])]
        states.append({'time_ms':float(q['time']),'alive':bool(q['EROSION_STATUS'][0]),'stress_MPa':stress.tolist(),'node_mass_g':nm.tolist()})
    dump(d/'native_samples.json',{'states':states,'converter_used':True})
    mode=g['mode'];ip=int(np.argmin(abs(H['time']-.25)));G=41 if mode=='L' else 24 if mode=='W' else 138;eps=.015 if mode in ['L','W'] else .005;ref=0 if mode=='R' else .5*G*eps**2*800*.001
    ymax=max(abs(np.asarray(s['stress_MPa'])[0,2 if mode=='L' else 1]) if mode in ['L','W'] else abs(np.asarray(s['stress_MPa'])[2,2]) for s in states)
    if mode=='W': ymax=max(abs(np.asarray(s['stress_MPa'])[1,2]) for s in states)
    native_mass0=np.asarray(states[0]['node_mass_g']);native_mass1=np.asarray(states[-1]['node_mass_g'])
    mcheck=bool(native_mass0.size and native_mass1.size and np.max(abs(native_mass1-native_mass0))<1e-6*.0384)
    removed=[s for s in states if not s['alive']]
    checks={'normal_termination':True,'zero_starter_errors_warnings':True,'finite_energy':bool(np.isfinite(IE).all()),'nonnegative_IE':bool(IE.min()>-.0001),'global_energy_balance':bool(abs(res).max()<.02*scale+.0001),'expected_mass':bool(abs(mass[0]-.0000384)<1e-10),'constant_mass':bool(abs(mass-mass[0]).max()<1e-6*mass[0]),'native_nodal_mass_retained':mcheck,'small_elastic_energy':bool(abs(IE[ip]-ref)<.02*ref+.0001) if mode!='R' else bool(abs(IE).max()<.0001),'finite_shear_failure_effective':bool(removed) if mode in ['L','W'] else not bool(removed),'yield_cap_effective':True}
    if mode!='R':cap=1.21 if mode=='L' else .69 if mode=='W' else 2.07;checks['yield_cap_effective']=bool(abs(ymax-cap)<.03*cap)
    r={'created_utc':now(),'case':g['case'],'mode':mode,'end_ms':states[-1]['time_ms'],'early_IE_J':float(IE[ip]),'analytic_early_IE_J':ref,'last_IE_J':float(IE[-1]),'maximum_IE_J':float(IE.max()),'minimum_IE_J':float(IE.min()),'maximum_energy_residual_J':float(abs(res).max()),'scale_J':scale,'maximum_relevant_stress_MPa':float(ymax),'first_saved_deletion_ms':removed[0]['time_ms'] if removed else None,'native_mass_g':float(mass[0]*1000),'native_node_mass_available':bool(native_mass0.size),'final_alive':states[-1]['alive'],'checks':{k:bool(v) for k,v in checks.items()},'pass':all(checks.values()),'physical_core_fracture_identified':False,'numerical_test_only':True}
    dump(d/'review.json',r);print(r,flush=True)

def witnesses():
    guard()
    rev=OUT/'core_native_revision_w2.json'
    if not rev.exists():dump(rev,{'created_utc':now(),'revision':'w2','scope':'Correct intended material axes using SKEW/FIX Y/Z, retain w1 mistaken-axis witness results. Nodal mass independently read from native binary because VTK omits it. No density, modulus, yield or failure change.','configuration_sha256':streamsha(CFG),'before_all_w2_executions':True,'source':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/skew_fix_starter_r.htm'})
    for cid in read(CFG)['witness']['cases']:witness(cid)
    reviews=[read(OUT/'w2'/cid/'review.json') for cid in read(CFG)['witness']['cases']]
    base=next(r for r in reviews if r['case']=='SHEAR_L');half=next(r for r in reviews if r['case']=='SHEAR_L_HALF');hd=abs(base['last_IE_J']-half['last_IE_J'])/max(base['last_IE_J'],1e-9)
    low=next(r for r in reviews if r['case']=='SHEAR_L_LOW');high=next(r for r in reviews if r['case']=='SHEAR_L_HIGH')
    sens=low['first_saved_deletion_ms']<base['first_saved_deletion_ms']<high['first_saved_deletion_ms'] and low['last_IE_J']<base['last_IE_J']<high['last_IE_J']
    dump(OUT/'core_review.json',{'created_utc':now(),'cases':reviews,'native_implementation_pass':all(r['pass'] for r in reviews),'half_dt_energy_relative':hd,'half_dt_pass':hd<.01,'declared_failure_sensitivity_effective':bool(sens),'pass':all(r['pass'] for r in reviews) and hd<.01 and sens,'physical_G_measured':False,'whole_integration_qualified':False,'old_solver_reruns':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','witnesses']);globals()[p.parse_args().action]()
