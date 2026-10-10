"""Analytical triangle checks for identical native sandwich materials, no impact reruns."""
import numpy as np
import csv
from run_aircraft_a19 import *
from run_aircraft_a18 import blocks
def histories(p):
    with p.open(encoding='utf-8-sig') as f:r=csv.reader(f);keys=next(r);rows=list(r)
    while not keys[-1].strip():keys.pop()
    rows=[row[:len(keys)] for row in rows];assert all(len(row)==len(keys) for row in rows)
    v=np.array([[float(x) for x in row] for row in rows]);return {k:v[:,i] for i,k in enumerate(keys)}

TCFG=ROOT/'wtc1_simulation_v8/data/aircraft_a19_triangle_declaration.json'
def declare():
    guard();assert not TCFG.exists();c={'iteration':'AIRCRAFT-A19','declared_utc':now(),'seed':1102044,'random_draws':0,
      'scope':'Two independent native triangle formulations, rigid90-degree rotation and small equibiaxial elastic strain. Not a core fracture calibration.',
      'source_materials':rel(SOURCE),'Ish3n':[2,31],'same_material_density_thickness':True,'core_failure_absent':True,
      'triangle_mm':[[0,0,0],[300,0,0],[0,300,0]],'duration_ms':1,'equibiaxial_strain':.001,'angle_rad':float(np.pi/2),
      'input_dt_ms':.0001,'dt_cap_ms':.000025,'history_dt_ms':.001,'animation_dt_ms':.25,'engine_cap_seconds':120,
      'acceptance':{'rigid_rotation_maximum_IE_J':.01,'analytic_elastic_final_IE_fraction':.01,'energy_balance_relative':.002,'absolute_energy_J':.01},
      'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impdisp_starter_r.htm'],
      'physical_whole_impact_qualified':False,'whole_experiment_requires_separate_declaration':True}
    dump(TCFG,c);dump(OUT/'triangle_declaration_guard.json',{'sha256':streamsha(TCFG),'declared_before_any_witness':True});print({'triangle_controls_declared':4},flush=True)

def witness(ish,mode):
    c=read(TCFG);assert streamsha(TCFG)==read(OUT/'triangle_declaration_guard.json')['sha256'];d=OUT/'w0'/f'{mode}_ISH{ish}';n=f'A19_{mode}_{ish}'
    if d.exists():
        assert not (d/'review.json').exists();assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');review(d,n,ish,mode,c);return
    d.mkdir(parents=True)
    xyz=np.array(c['triangle_mm']);pb={b[0]:b for b in blocks((SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.rad')).read_text().splitlines())}
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*x) for i,x in enumerate(xyz)]
    for key in ['/MAT/LAW25/4','/MAT/LAW25/5','/PROP/TYPE19/41','/PROP/TYPE19/42','/PROP/TYPE19/43','/PROP/TYPE51/21']:
        b=pb[key].copy()
        if key=='/PROP/TYPE51/21':b[2]=b[2][:20]+ii(ish)+b[2][30:]
        L+=b
    L+=['/PART/21','INDEPENDENT_REFERENCE_TRIANGLE',ii(21,4,0),'/SHELL/21',ii(1,1,2,3,3)]
    ts=np.linspace(0,1,10001);u=3*ts*ts-2*ts**3;angle=c['angle_rad']*u if mode=='ROTATION' else np.zeros_like(ts);eps=c['equibiaxial_strain']*u if mode=='STRAIN' else np.zeros_like(ts)
    moved=np.zeros((len(ts),3,3));moved[:,:,0]=(1+eps[:,None])*xyz[None,:,0]*np.cos(angle[:,None]);moved[:,:,1]=(1+eps[:,None])*xyz[None,:,1];moved[:,:,2]=-(1+eps[:,None])*xyz[None,:,0]*np.sin(angle[:,None]);disp=moved-xyz[None];fid=10
    for ni in range(1,4):
        L += [f'/GRNOD/NODE/{ni}',f'NODE_{ni}',ii(ni)]
        for direction,values in [('X',disp[:,ni-1,0]),('Y',disp[:,ni-1,1]),('Z',disp[:,ni-1,2]),('XX',np.zeros_like(ts)),('YY',angle),('ZZ',np.zeros_like(ts))]:
            fid+=1;L += [f'/FUNCT/{fid}',f'PRESCRIBED_{ni}_{direction}']+[ff(t,v) for t,v in zip(ts,values)]+[f'/IMPDISP/{fid}',f'MOTION_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/PART/21','REFERENCE_TRIANGLE',''.join(f'{s:>10}' for s in ['IE','KE','HE','PW']),ii(21),'/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,.25),'/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(c['dt_cap_ms'],c['dt_cap_ms']),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');dump(d/'generation.json',{'created_utc':now(),'name':n,'Ish3n':ish,'mode':mode,'configuration_sha256':streamsha(TCFG),'no_instrument_mass':True,'no_failure_or_contact':True})
    assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env());s=(d/'starter.log').read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',s)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',s)[-1])==0,s[-3000:]
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',c['engine_cap_seconds'],env());assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env())
    review(d,n,ish,mode,c)

def review(d,n,ish,mode,c):
    H=histories(d/(n+'T01.csv'));IE=H['INTERNAL ENERGY']*.001;T=H['time'];ec=c['equibiaxial_strain']*(3*T**2-2*T**3);reference=.5*300*300*(22000/(1-.25)*1+1/(1-.1)*8)*ec**2*.001
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'];total=sum(H[k] for k in terms)*.001;res=total-total[0]-H['EXTERNAL WORK']*.001;scale=max(float(np.max(abs(total))),float(np.max(abs(H['EXTERNAL WORK'])))*.001)
    checks={'normal_termination':True,'finite':bool(np.isfinite(IE).all()),'native_energy_balance':bool(np.max(abs(res))<=.002*scale+.01),'expected_material_response':bool(np.max(abs(IE))<.01) if mode=='ROTATION' else bool(abs(IE[-1]-reference[-1])<=.01*reference[-1]+.0001),'nonnegative_internal_energy':bool(IE.min()>-.001)}
    r={'created_utc':now(),'Ish3n':ish,'mode':mode,'last_history_ms':float(T[-1]),'maximum_IE_J':float(IE.max()),'minimum_IE_J':float(IE.min()),'last_IE_J':float(IE[-1]),'analytic_last_IE_J':0 if mode=='ROTATION' else float(reference[-1]),'maximum_energy_residual_J':float(np.max(abs(res))),'energy_scale_J':scale,'checks':checks,'pass':all(checks.values()),'physical_impact_qualified':False};dump(d/'review.json',r);print(r,flush=True)

def run():
    for ish in [2,31]:
        for mode in ['ROTATION','STRAIN']:witness(ish,mode)
    r=[read(OUT/'w0'/f'{mode}_ISH{ish}'/'review.json') for ish in [2,31] for mode in ['ROTATION','STRAIN']];dump(OUT/'triangle_review.json',{'created_utc':now(),'cases':r,'pass':all(q['pass'] for q in r),'does_not_qualify_high_strain_or_core_failure':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
