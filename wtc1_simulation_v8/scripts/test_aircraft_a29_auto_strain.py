"""Explicit full-volume orthotropic branch, preserving physical material input fields.

The 3D constitutive assumption is independently declared; TYPE22 equivalence is
not presumed. Affine modes gate the subsequent free/plate controls.
"""
from run_aircraft_a28 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories
from run_aircraft_a23 import brick_grid
import run_aircraft_a26 as A26
import test_aircraft_a26_solidshell_w2 as metal
import argparse,inspect,ast,json,shutil,re,traceback,time,urllib.request
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a29'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a29_auto_strain.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a28'

def constitutive():
    E=22000.;Ez=10000.;nu=.25;S=np.array([[1/E,-nu/E,-nu/Ez],[-nu/E,1/E,-nu/E],[-nu/Ez,-nu/E,1/Ez]]);C=np.zeros((6,6));order=[1,0,2];normal=np.linalg.inv(S);C[:3,:3]=normal[np.ix_(order,order)];C[3:,3:]=np.eye(3)*4000;return C

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A28';OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a28_predeclaration.json');patch=['PATCH_NORMAL_X_N12','PATCH_NORMAL_Y_N12','PATCH_NORMAL_Z_N12','PATCH_SHEAR_XY_N12','PATCH_SHEAR_YZ_N12','PATCH_SHEAR_XZ_N12'];other=[x for x in c['branches']['w1']['cases'] if not x.startswith('PATCH_')]
    c.update(iteration='AIRCRAFT-A29',revision='w0',declared_utc=now(),seed=1102054,random_draws=0,parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a28_predeclaration.json'),
      purpose='Full3D LAW25 source card with TYPE6 Isolid18, four geometric thickness elements, explicit source-theory 3D constitutive tensor. Stop after first failed affine gate, retain failure; no post-hoc material fit.',
      cases=patch+other,branches={'w0':{'property':'TYPE6 SOL_ORTH Isolid18 Ismstr4 Icpre3 Iframe2. Fixed material skew: axis1=globalY, axis2=-globalX, axis3=globalZ. No composite layer card or Ashear correction. Same LAW25/4 input card and physical volume/density.'}},
      constitutive_reference={'Voigt_order':['XX','YY','ZZ','gammaXY','gammaYZ','gammaXZ'],'global_stiffness_MPa':constitutive().tolist(),'engineering_shear_G_MPa':[4000,4000,4000],
        'source':'LAW25 official Elastic Phase compliance equation, normal symmetric matrix S12=-nu/E11, S13=-nu/E33, S23=-nu/E22; invert positive definite S then rotate90deg. Engineering shear gamma=2epsilon, so stiffness is G, not2G.',
        'status':'new declared full3D interpretation of unchanged scalar material inputs. Not automatically equivalent to observed TYPE22 plane block, no historical fracture/material validation.'},
      mesh={'XY':[6,12],'Z':4,'bounds_mm':[[-5,-5,-.25],[5,5,.25]],'volume_mm3':50,'physical_mass_g':.0915,'known_mass':'integrate source density over each physical hexa, equal-volume lump at8corners; no inertia adjustment','initial_continuum_inertia_gate_fraction':.02},
      loading={'membrane':'uniaxial stress ideal: ux=.001x, uy=-.00025y, uz=-.00025z for material-axis2/globalX. This transverse contraction follows full3D source compliance.',
        'bending':'epsilon_x=-kz, epsilon_y=0, sigma_z=0 to first order: uz=k*x²/2+(Czx/Czz)*k*z²/2; ux=-k*x*z-k²*x³/6;uy=0;k=.001/mm. Transverse quadratic field represented by4geometric elements, not a fitted modulus.'},
      elastic_reference_scope='native IE, plus untouched separate HE in full balance; classical plane bending condenses source3D tensor at sigma_z=0, D=(Cxx-Cxz²/Czz)t³/12. Independent affine energy0.5epsilon*C*epsilon*volume.',
      execution={'CPU_threads':1,'GPU':False,'mass_scaling':False,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'per_process_cap_s':1200,'estimated_minutes':[4,20]},
      whole_insertion_ready=False,objective1_complete=False,native_old_reruns=0)
    dump(CFG,c);dump(OUT/'auto_strain_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True});sd=OUT/'sources';sd.mkdir();sources=[]
    u='https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type6_sol_orth_starter_r.htm';q=sd/'type6.html';q.write_bytes(urllib.request.urlopen(u,timeout=45).read());sources.append({'url':u,'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'redistribution':'exclude_third_party'})
    for p in [PREV/'sources/law25_theory.html',PREV/'sources/tsai_wu.html']:
        q=sd/p.name;shutil.copy2(p,q);sources.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'copied_from':rel(p),'redistribution':'exclude_third_party'})
    for p in [PREV/'assumed_strain_diagnostic.json',PREV/'shear_balance_diagnostic.json',PREV/'publication_verification.json',Path(metal.__file__),Path(A26.__file__),ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad']:sources.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'material_card':parent()['/MAT/LAW25/4'],'source_archive_rescanned':False,'no_known_damage_target':True});print({'declared':'AIRCRAFT-A29','native_cases':15,'CPU_minutes':[4,20]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'auto_strain_guard.json')['sha256']

def property_card():
    return ['/SKEW/FIX/1','SOURCE_MATERIAL_AXES_90DEG',ff(0,0,0),ff(0,1,0),ff(-1,0,0),'/PROP/TYPE6/1','FULL_VOLUME_ORTHOTROPIC_FOUR_THICKNESS_ELEMENTS',ii(18,0)+' '*10+ii(3,0,0,0,2)+ff(0),ff(0,0,0),ff(0,0,0)+ii(1,0,0),ff(0,0,0,0),ff(0,0,0,0,0),ii(0,0,2)]

def patch_strain(cid):
    e=np.zeros(6)
    if cid.startswith('PATCH_NORMAL_'):e['XYZ'.index(cid.split('_')[2])]=.001
    else:e[{'XY':3,'YZ':4,'XZ':5}[cid.split('_')[2]]]=.001
    return e

def patch_energy(cid):
    e=patch_strain(cid);return float(.5*e@constitutive()@e*50*.001)

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;cache={};counter=10000;C=constitutive();alpha=C[2,0]/C[2,2]
    for ni,q in enumerate(X,1):
        x,y,z=q;L+=group(ni,f'PRESCRIBED_NODE_{ni}',[ni]);D=np.zeros(3)
        if cid.startswith('PATCH_NORMAL_'):
            a='XYZ'.index(cid.split('_')[2]);D[a]=.001*q[a]
        elif cid.startswith('PATCH_SHEAR_'):
            a,b=['XYZ'.index(t) for t in cid.split('_')[2]];D[a]=.0005*q[b];D[b]=.0005*q[a]
        elif cid.startswith('MEMBRANE'):D=np.array([.001*x,-.00025*y,-.00025*z])
        else:D=np.array([-.001*x*z-.001**2*x**3/6,0,.001*x*x/2+alpha*.001*z*z/2])
        for a,direction in enumerate('XYZ'):
            val=D[a]*s;key=val.tobytes()
            if key not in cache:
                counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}',f'KNOWN_DISPLACEMENT_{counter}']+[ff(t,v) for t,v in zip(T,val)]
            fid=cache[key];counter+=1;L+=[f'/IMPDISP/{counter}',f'PRESCRIBED_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def review(d,n):
    s=inspect.getsource(A26.review);old="area=(10*(g['mesh_n']-2)/g['mesh_n'])**2;D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*area*.001;actual=float(next(v[-1]*.001 for k,v in H.items() if k.startswith('PLATE_INTERIOR') and k.strip().endswith('IE')))";assert s.count(old)==1;s=s.replace(old,"C=constitutive();D=(C[0,0]-C[0,2]**2/C[2,2])*.5**3/12;ref=.5*D*.001**2*100*.001;actual=float(IE[-1])").replace('73100','22000').replace('.139','.0915').replace('.33','.25');s=s.replace("if g['case'].startswith('MEMBRANE'):","if g['case'].startswith('PATCH_'):ref=patch_energy(g['case']);actual=float(IE[-1])\n        elif g['case'].startswith('MEMBRANE'):");ns=dict(globals());exec(compile(s,__file__+'::review','exec'),ns);ns['review'](d,n);p=OUT/'review_w1_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(A26.__file__)),'source_sha256':streamsha(Path(A26.__file__)),'derived_source':s,'acceptance_thresholds_unchanged':True,'references_from_source_tensor_not_native_response':True})

def create_runner():
    s=inspect.getsource(metal.run_one);audit=[];prop="prop=['/PROP/TYPE20/1','HALF_MM_HA8_SOLID_SHELL_TRANSLATIONS',ii(14,4)+' '*20+ii(10,222)+' '*20+ff(0),ff(0,0,0),ff(0,0,0,0,0),' '*20+ii(2)]"
    for old,new in [("OUT/'w2'","OUT/'w1'"),("n='A26_HA8_'+cid","n='A29_W1_3D_'+cid"),('brick_grid([ncell,ncell,1]','brick_grid([ncell,ncell,4]'),(";free=cid.startswith('FREE')",";m=m*(.00183/.00278);free=cid.startswith('FREE')"),(prop,'prop=property_card()'),("P['/MAT/LAW2/1']+prop","P['/MAT/LAW25/4']+prop"),("'METAL_FULL_VOLUME',ii(1,1,0)","'FULL_3D_ORTHOTROPIC_SKIN',ii(1,4,0)"),("'TYPE20':True,'Icstr':10","'TYPE6':True,'Isolid':18,'geometric_thickness_elements':4,'material_axes':[[0,1,0],[-1,0,0],[0,0,1]]"),('600,en','1200,en')]:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());p=OUT/'runner_w1_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(metal.__file__)),'source_sha256':streamsha(Path(metal.__file__)),'derived_source':s,'changes':audit})

def run():
    guard();create_runner()
    for cid in read(CFG)['cases']:
        d=OUT/'w1'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
        if cid.startswith('PATCH_'):assert read(d/'review.json')['pass'],'Affine independent 3D gate failed: stop before subsequent controls, keep all outputs'
    dump(OUT/'native_case_summary_w1.json',{'created_utc':now(),'cases':[read(OUT/'w1'/cid/'review.json') for cid in read(CFG)['cases']],'whole_insertion_ready':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
