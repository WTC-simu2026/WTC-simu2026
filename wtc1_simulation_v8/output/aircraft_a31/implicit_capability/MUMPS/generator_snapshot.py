"""Bounded capability test of the existing binary; no installation or solver edits."""
from run_aircraft_a23 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,brick_grid,prop,histories
from linear_hexa_reference_aircraft_a23 import solve
import numpy as np
import argparse,re,traceback,urllib.request,shutil
from pathlib import Path

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a31/implicit_capability'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a31_implicit_capability.json'
URLS={
 'nonlin':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_nonlin_engine_r.htm',
 'solver':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_solver_engine_r.htm',
 'dtini':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dtini_engine_r.htm',
 'dyna':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dyna_2_engine_r.htm',
}

def declare():
    assert not OUT.exists() and not CFG.exists()
    h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A30'
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    c={'iteration':'AIRCRAFT-A31','subscope':'existing-binary implicit capability','declared_utc':now(),'seed':1102056,'random_draws':0,
       'purpose':'Probe a potentially efficient late-time physical dynamics route. This tiny fixture can establish binary capability only; it does not qualify nonlinear whole impact, restart, contact or regime transition.',
       'geometry_mm':{'lo':[-.5,-.5,-.5],'hi':[.5,.5,.5],'shape':[2,2,2]},
       'material':'unchanged source LAW2/1: rho.00278g/mm3 E73100MPa nu.33 yield324MPa, no added failure',
       'solid':'TYPE14 HA8 Isolid14 Ismstr4 Icpre2 Gauss222 Iframe2',
       'mass_g':.00278,'boundary':'Only x=-.5 and x=.5 faces fixed XYZ except right-face ramp ux; middle nodes free',
       'motion':{'duration_ms':.05,'displacement_mm':.001,'shape':'3u2-2u3','function_points':1001},
       'implicit':{'Newmark_gamma':.5,'Newmark_beta':.25,'initial_dt_ms':.001,'nonlin_N':1,'L_A':0,'Itol':123,'tolerances':[1e-6,1e-6,1e-6],
                   'cases':[{'name':'PCG','solver_N':1,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8},{'name':'MUMPS','solver_N':2,'Iprec':2,'It_max':0,'Itol':1,'Tol':1e-8}]},
       'execution':{'CPU_threads':1,'GPU':False,'per_process_cap_s':60,'estimated_seconds_max':240,'binary_changed':False,'installation':False,'mass_scaling':False},
       'acceptance':{'strict_zero_starter_warnings':True,'native_normal_termination':True,'mass_relative':1e-6,'ADMAS_relative':1e-9,'reference_IE_fraction':.02,'energy_fraction':.02,'energy_absolute_J':1e-7,'elastic_PW_J':1e-7},
       'independent_reference':'A23 conventional8node isotropic3D elastic stiffness,2x2x2Gauss; source tensor, saved before native outputs',
       'docs':URLS,'whole_inputs_changed':False,'whole_insertion_ready':False,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_reference_and_native':True})
    src=OUT/'sources';src.mkdir();sources=[]
    for key,url in URLS.items():
        p=src/(key+'.html');p.write_bytes(urllib.request.urlopen(url,timeout=45).read());sources.append({'url':url,'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p),'redistribution':'exclude_third_party'})
    for p in [RUNTIME/'engine_win64.exe',RUNTIME/'starter_win64.exe',ROOT/'wtc1_simulation_v8/scripts/linear_hexa_reference_aircraft_a23.py',ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad']:
        sources.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'source_archive_rescanned':False});print({'implicit_capability_declared':True,'existing_binary_only':True,'native_cap_s':60},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def run_one(case):
    guard();d=OUT/case['name'];assert not d.exists();d.mkdir();n='A31_IMPL_'+case['name'];X,B,m,left,right=brick_grid([2,2,2],[-.5,-.5,-.5],[.5,.5,.5]);c=read(CFG)
    ref=solve(X,B,left,right,.001);dump(d/'reference_before_native.json',{'created_utc':now(),'configuration_sha256':streamsha(CFG),**ref})
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(j+1)+ff(*x) for j,x in enumerate(X)]
    L+=parent()['/MAT/LAW2/1']+prop()+['/PART/1','UNCHANGED_PHYSICAL_METAL',ii(1,1,0),'/BRICK/1']+[ii(j+1,*b) for j,b in enumerate(B)]
    T=np.linspace(0,.05,1001);s=3*(T/.05)**2-2*(T/.05)**3
    L+=['/FUNCT/100','ZERO_DISPLACEMENT']+[ff(t,0) for t in T]+['/FUNCT/101','RIGHT_FACE_RAMP']+[ff(t,.001*u) for t,u in zip(T,s)]
    counter=1000
    for ni in left+right:
        L+=group(ni,'PHYSICAL_FACE_NODE',[ni])
        for ax in 'XYZ':
            counter+=1;fid=101 if ni in right and ax=='X' else 100
            L+=[f'/IMPDISP/{counter}',f'PHYSICAL_FACE_{ni}_{ax}',ii(fid)+f'{ax:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/PART/1','PHYSICAL_SCOPE',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(1),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(j,0) for j in range(1,len(X)+1)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/IMPL/NONLIN/1',ii(0,123)+ff(1e-6,1e-6,1e-6),f"/IMPL/SOLVER/{case['solver_N']}",ii(case['Iprec'],case['It_max'],case['Itol'])+ff(case['Tol']),'/IMPL/DTINI',ff(.001),'/IMPL/DYNA/2',ff(.5,.25),'/ANIM/DT',ff(0,.01),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/ANIM/BRICK/TENS/STRESS','/PRINT/-1/1',f'/RUN/{n}/1',ff(.05),'/TFILE/4',ff(.001),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'case':case,'name':n,'configuration_sha256':streamsha(CFG),'nodes_mm':X.tolist(),'bricks':B,'nodal_masses_g':m.tolist(),'boundary_nodes':left+right,'free_interior_nodes':[j for j in range(1,len(X)+1) if j not in left+right],'known_mass_g':float(m.sum())})
    en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');checks={};failed=None
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',60,en);txt=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1]);checks['strict_starter']=bool(ok and nw==0 and ne==0);dump(d/'starter_gate.json',{'warnings':nw,'errors':ne,'pass':checks['strict_starter']});assert checks['strict_starter']
        ok=execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',60,en);txt=(d/'engine.log').read_text(errors='replace');checks['native_completed']=bool(ok and 'NORMAL TERMINATION' in txt)
        if checks['native_completed']:
            assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',60,en);H=histories(d/(n+'T01.csv'));T=H['time'];u=np.clip(T/.05,0,1);s=3*u*u-2*u*u*u;IE=H['INTERNAL ENERGY']*.001;terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];total=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;R=total-total[0]-EW;PW=sum(H[k] for k in H if k.strip().endswith('PW'))*.001
            target=ref['energy_J']*s[-1]**2;checks.update(mass=bool(abs(H['MASS']-.00278).max()<1e-6*.00278),no_ADMAS=bool(abs(H['ADDED MASS']).max()<1e-9*.00278),independent_IE=bool(abs(IE[-1]-target)<.02*target+1e-7),native_full_balance=bool(abs(R).max()<.02*max(float(abs(total).max()),float(abs(EW).max()))+1e-7),elastic_PW=bool(abs(PW).max()<1e-7))
            dump(d/'native_diagnostics.json',{'last_ms':float(T[-1]),'IE_J':float(IE[-1]),'reference_J':target,'maximum_residual_J':float(abs(R).max()),'maximum_PW_J':float(abs(PW).max())})
    except Exception:failed=traceback.format_exc();dump(d/'retained_failure.json',{'created_utc':now(),'traceback':failed,'no_rerun':True})
    r={'created_utc':now(),'name':case['name'],'checks':checks,'all_declared_checks_pass':bool(checks.get('native_completed') and all(checks.values()) and not failed),'binary_implicit_completion':bool(checks.get('native_completed')),'failure_traceback':failed,'whole_impact_qualified':False};dump(d/'review.json',r);print({'implicit_case':case['name'],'completed':r['binary_implicit_completion'],'checks':checks},flush=True)

def run():
    guard()
    for case in read(CFG)['implicit']['cases']:run_one(case)
    rows=[read(OUT/x['name']/'review.json') for x in read(CFG)['implicit']['cases']];dump(OUT/'capability_review.json',{'created_utc':now(),'cases':rows,'existing_binary_support_demonstrated':any(x['binary_implicit_completion'] for x in rows),'whole_impact_qualified':False,'installation_or_binary_edits':False,'no_prior_native_solver_reruns':True});dump(OUT/'harness_after.json',harness())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
