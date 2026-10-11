"""Diagnose transverse assumed strain, then qualify a documented thick-shell alternative.

No material, density, geometry, mass, strength, or acceptance threshold is fitted.
"""
from run_aircraft_a27 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories
from run_aircraft_a23 import brick_grid
import run_aircraft_a26 as A26
import test_aircraft_a26_solidshell_w2 as metal
import argparse,inspect,ast,json,shutil,re,traceback,time,urllib.request
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a28'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a28_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a27'
REV='w0'

def constitutive():
    C=np.zeros((6,6));E=22000.;v=.25;C[:2,:2]=[[E/(1-v*v),v*E/(1-v*v)],[v*E/(1-v*v),E/(1-v*v)]];C[2,2]=10000.;C[3:,3:]=np.diag([4000.,4000.*5/6,4000.*5/6]);return C

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A27';OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a27_plane_w3.json');c.update(iteration='AIRCRAFT-A28',revision='w0',declared_utc=now(),seed=1102053,random_draws=0,
      parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a27_plane_w3.json'),
      purpose='Test analytical ASQBI transverse assumed-strain explanation of A27 bending; diagnostic global Icpre1, then documented HSEPH alternative. No selecting a quadrature to hit a target.',
      material_card_sha256=__import__('hashlib').sha256(('\n'.join(parent()['/MAT/LAW25/4'])+'\n').encode()).hexdigest(),
      branches={'w0':{'property':'TYPE22 HA8 Isolid14 Ismstr4 Icstr010 Inpts292; unchanged9 regular homogeneous layers and all material fields. /DEF_SOLID Icpre1 is a diagnostic only, not declared realistic for this compressible material.',
        'cases':['PATCH_NORMAL_X_N12','PATCH_NORMAL_Y_N12','PATCH_NORMAL_Z_N12','MEMBRANE_N6','MEMBRANE_N12','BENDING_N6','BENDING_N12']},
        'w1':{'property':'TYPE22 HSEPH Isolid15 Ismstr4 Icstr0 Inpts9 Iint0 dn1e-20; same9 homogeneous numerical subdivisions, source orientation90, shear factor5/6. No /DEF_SOLID override.',
        'cases':read(ROOT/'wtc1_simulation_v8/data/aircraft_a27_plane_w3.json')['cases']+['PATCH_NORMAL_X_N12','PATCH_NORMAL_Y_N12','PATCH_NORMAL_Z_N12','PATCH_SHEAR_XY_N12','PATCH_SHEAR_YZ_N12','PATCH_SHEAR_XZ_N12']}},
      constitutive_reference={'block_stiffness_global_MPa':constitutive().tolist(),'Voigt_order':['XX','YY','ZZ','gammaXY','gammaYZ','gammaXZ'],
        'status':'explicit thick-shell plane law plus independent transverse elasticity, tested by new affine controls, not a claim of general LAW25 3D coupled-law equivalence or historical layup',
        'material_orientation':'90deg source but E11=E22 and G13=G23; equal plane constants make this global block invariant under that rotation',
        'transverse_shear':'source Ashear5/6 explicitly included in expected thick-shell transverse shear response; no calibration'},
      elastic_reference_scope='w0 uses native IE; w1 uses native IE+HE because HSEPH physical stabilization is stored elastic energy. Each original energy channel remains separate in full balance; no reconstructed RKE, no subtraction, same2%+1e-7J tolerance.',
      native_old_reruns=0,whole_insertion_ready=False,objective1_complete=False)
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True});sd=OUT/'sources';sd.mkdir();sources=[]
    for name,u in [('assumed_strain','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_assumed_strain_rate.htm'),('def_solid','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/def_solid_starter_r.htm'),('solid_shell','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/theory_element_library_solid_shell_elements_r.htm')]:
        q=sd/(name+'.html');q.write_bytes(urllib.request.urlopen(u,timeout=45).read());sources.append({'url':u,'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'redistribution':'exclude_third_party'})
    for source in [PREV/'sources/type22.html',PREV/'sources/law25_theory.html',PREV/'sources/tsai_wu.html']:
        q=sd/source.name;assert not q.exists();shutil.copy2(source,q);sources.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'copied_from':rel(source),'redistribution':'exclude_third_party'})
    actual=ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad'
    for q in [actual,PREV/'constitutive_observation.json',PREV/'composite_qualification_review.json',PREV/'publication_verification.json',Path(metal.__file__),Path(A26.__file__)]:sources.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'source_archive_rescanned':False,'material_card':parent()['/MAT/LAW25/4'],'no_known_damage_target':True,'previous_goal_turn_classification':'progress: A26/A27 completed and registered, verified public release with successful CI. No live solver inherited.'});print({'declared':'AIRCRAFT-A28','native_cases':22,'CPU_minutes':[3,10]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def property_card():
    if REV=='w0':L=['/DEF_SOLID',ii(14,4,1,0,0,0,0,0,0),'/PROP/TYPE22/1','HA8_DIAGNOSTIC_CONSTANT_PRESSURE',ii(14,4)+' '*20+ii(10,292,0)+' '*10+ff(0)]
    else:L=['/PROP/TYPE22/1','HSEPH_HOMOGENEOUS_ORTHOTROPIC_SKIN',ii(15,4)+' '*20+ii(0,9,0)+' '*10+ff(1e-20)]
    return L+[ff(0,0),ff(1,0,0)+ii(0,0,0),ff(5/6)]+[ff(90,1/9,0)+ii(4) for _ in range(9)]+[ff(0,0,0,0,0),' '*20+ii(2)]

def imposed(L,X,cid):
    T=np.linspace(0,.1,1001);s=3*(T/.1)**2-2*(T/.1)**3;cache={};counter=10000
    for ni,q in enumerate(X,1):
        x,y,z=q;L+=group(ni,f'PRESCRIBED_NODE_{ni}',[ni]);D=np.zeros(3)
        if cid.startswith('PATCH_NORMAL_'):
            a='XYZ'.index(cid.split('_')[2]);D[a]=.001*q[a]
        elif cid.startswith('PATCH_SHEAR_'):
            a,b=['XYZ'.index(t) for t in cid.split('_')[2]];D[a]=.0005*q[b];D[b]=.0005*q[a]
        elif cid.startswith('MEMBRANE'):D=np.array([.001*x,-.00025*y,0])
        else:D=np.array([-.001*x*z-.001**2*x**3/6,0,.001*x*x/2])
        for a,direction in enumerate('XYZ'):
            val=D[a]*s;key=val.tobytes()
            if key not in cache:
                counter+=1;cache[key]=counter;L+=[f'/FUNCT/{counter}',f'KNOWN_DISPLACEMENT_{counter}']+[ff(t,v) for t,v in zip(T,val)]
            fid=cache[key];counter+=1;L+=[f'/IMPDISP/{counter}',f'PRESCRIBED_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def patch_strain(cid):
    e=np.zeros(6)
    if cid.startswith('PATCH_NORMAL_'):e['XYZ'.index(cid.split('_')[2])]=.001
    else:e[{'XY':3,'YZ':4,'XZ':5}[cid.split('_')[2]]=.001
    return e

def patch_energy(cid):
    e=patch_strain(cid);return float(.5*e@constitutive()@e*50*.001)

def review(d,n):
    s=inspect.getsource(A26.review)
    old="area=(10*(g['mesh_n']-2)/g['mesh_n'])**2;D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*area*.001;actual=float(next(v[-1]*.001 for k,v in H.items() if k.startswith('PLATE_INTERIOR') and k.strip().endswith('IE')))"
    assert s.count(old)==1;s=s.replace(old,"D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*100*.001;actual=float(IE[-1])").replace('73100','22000').replace('.139','.0915').replace('.33','.25')
    s=s.replace("if g['case'].startswith('MEMBRANE'):","if g['case'].startswith('PATCH_'):ref=patch_energy(g['case']);actual=float(IE[-1])\n        elif g['case'].startswith('MEMBRANE'):")
    s=s.replace('actual=float(IE[-1])',"actual=float(IE[-1]+(H['HOURGLASS ENERGY'][-1]*.001 if REV=='w1' else 0))")
    namespace=dict(globals());exec(compile(s,__file__+'::review','exec'),namespace);namespace['review'](d,n);p=d/'review.json';r=read(p);H=histories(d/(n+'T01.csv'));r.update(revision=REV,native_internal_final_J=float(H['INTERNAL ENERGY'][-1]*.001),native_hourglass_final_J=float(H['HOURGLASS ENERGY'][-1]*.001),maximum_hourglass_J=float(abs(H['HOURGLASS ENERGY']).max()*.001),elastic_scope='native IE+HE physical HSEPH stabilization' if REV=='w1' else 'native IE',original_energy_channels_unchanged=True);dump(p,r)
    q=OUT/f'review_{REV}_derivation.json'
    if not q.exists():dump(q,{'created_utc':now(),'source':rel(Path(A26.__file__)),'source_sha256':streamsha(Path(A26.__file__)),'derived_source':s,'acceptance_thresholds_unchanged':True,'scope_explicit_before_native_run':True})

def create_runner():
    s=inspect.getsource(metal.run_one);audit=[]
    prop="prop=['/PROP/TYPE20/1','HALF_MM_HA8_SOLID_SHELL_TRANSLATIONS',ii(14,4)+' '*20+ii(10,222)+' '*20+ff(0),ff(0,0,0),ff(0,0,0,0,0),' '*20+ii(2)]"
    for old,new in [("OUT/'w2'","OUT/REV"),("n='A26_HA8_'+cid","n='A28_'+REV.upper()+'_'+cid"),(";free=cid.startswith('FREE')",";m=m*(.00183/.00278);free=cid.startswith('FREE')"),(prop,'prop=property_card()'),("P['/MAT/LAW2/1']+prop","P['/MAT/LAW25/4']+prop"),("'METAL_FULL_VOLUME',ii(1,1,0)","'ORTHOTROPIC_SKIN_VOLUME',ii(1,4,0)"),("'TYPE20':True,'Icstr':10","'TYPE22':True,'Isolid':14 if REV=='w0' else 15,'Icstr':10 if REV=='w0' else 0,'native_revision':REV")]:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());q=OUT/f'runner_{REV}_derivation.json'
    if not q.exists():dump(q,{'created_utc':now(),'source':rel(Path(metal.__file__)),'source_sha256':streamsha(Path(metal.__file__)),'derived_source':s,'changes':audit})

def run():
    guard();create_runner()
    for cid in read(CFG)['branches'][REV]['cases']:
        d=OUT/REV/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
    dump(OUT/f'native_case_summary_{REV}.json',{'created_utc':now(),'cases':[read(OUT/REV/cid/'review.json') for cid in read(CFG)['branches'][REV]['cases']],'whole_insertion_ready':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);p.add_argument('--revision',choices=['w0','w1'],default='w0');a=p.parse_args();REV=a.revision;globals()[a.action]()
