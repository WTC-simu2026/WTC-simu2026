"""Composite solid-shell using unchanged elastic LAW25 witness; declare before testing."""
from run_aircraft_a26 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,parent,group,histories
from run_aircraft_a23 import brick_grid
import run_aircraft_a26 as A26
import test_aircraft_a26_solidshell_w2 as metal
import argparse,inspect,ast,json,shutil,re,traceback,time,urllib.request
from pathlib import Path
import numpy as np
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a27'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a27_plane_w3.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a26'

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A26';OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a26_solidshell_w2.json');c.update(iteration='AIRCRAFT-A27',revision='w0',declared_utc=now(),seed=1102052,random_draws=0,parent_configuration_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a26_solidshell_w2.json'),purpose='Same planar composite witness LAW25/4 as A23-A25, now TYPE22 HA8 with translations and explicit through-thickness Gauss quadrature. Isolated elastic/inertial qualification before conformal core and real root.',
      changes={'material':'unchanged LAW25/4 elastic-reference card, rho.00183g/mm3 E11=E22=22000MPa nu12=.25 G12/G23/G31=4000MPa; other source fields retained, no historical strength/fracture qualification','geometry':'same10x10x.5mm plate, physical mass.0915g from declared density; this is a different material from the.139g metal witness, not a mass compensation','property':'TYPE22 Isolid14 Ismstr4 Icstr010 Inpts232, Ipos1; 3 Gauss layer points same homogeneous material and90degree orientation. Thickness weights5/18,4/9,5/18 and z=+-sqrt(3/5)/2,0. Not a newly asserted physical layup. Ashear5/6 inherited from skin control.','reference':'free mass/tensor/energy/momenta with same thresholds as A26; uniaxial plane referenceE11, bending D11=E11*t³/[12(1-nu12*nu21)], no assumption that shear is isotropic. The prescribed 3D transverse strain is a control hypothesis, to be checked against actual native stresses; failures retained.'},
      whole_insertion_ready=False,objective1_complete=False,composite_strength_or_fracture_qualified=False,old_A20_A26_native_solver_reruns=0)
    c['plate'].update(rho_g_mm3=.00183,mass_g=.0915,E_MPa=22000,nu=.25,material='LAW25/4 inherited elastic-reference orthotropic witness',historical_attachment_unknown=True)
    c['motion'].update(membrane_transverse_strain=-.00025)
    dump(CFG,c);dump(OUT/'plane_w3_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solvers':True});sd=OUT/'sources';sd.mkdir();q=sd/'type22.html';u='https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type22_tsh_comp_starter_r.htm';q.write_bytes(urllib.request.urlopen(u,timeout=45).read());sources=[{'url':u,'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q),'redistribution':'exclude_third_party'}]
    for q in [Path(metal.__file__),Path(A26.__file__),PREV/'material_source_addendum.json',PREV/'metal_qualification_review.json',PREV/'publication_verification.json']:sources.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'source_archive_rescanned':False,'no_known_damage_target':True});print({'declared':'AIRCRAFT-A27','native_controls':9,'CPU_minutes':[3,8]},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'plane_w3_guard.json')['sha256']

def composite_property():
    L=['/PROP/TYPE22/1','COMPOSITE_HA8_TRANSLATIONS_EXPLICIT_GAUSS',ii(14,4)+' '*20+ii(10,292,0)+' '*10+ff(0),ff(0,0),ff(1,0,0)+ii(0,0,0),ff(.833333333333)]
    for w,z in [(1/9,0)]*9:L+=[ff(90,w,z)+ii(4)]
    return L+[ff(0,0,0,0,0),' '*20+ii(2)]

def imposed(L,X,cid):
    # Explicit plane displacement control; no alteration of constitutive fields.
    s=inspect.getsource(metal.imposed).replace('-.00033*y','-.00025*y').replace('-.00033*z','0*z').replace('.33/(1-.33)*.001*z*z/2','0*z')
    namespace=dict(globals());exec(compile(s,__file__+'::imposed','exec'),namespace);return namespace['imposed'](L,X,cid)

def review(d,n):
    s=inspect.getsource(A26.review);old="area=(10*(g['mesh_n']-2)/g['mesh_n'])**2;D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*area*.001;actual=float(next(v[-1]*.001 for k,v in H.items() if k.startswith('PLATE_INTERIOR') and k.strip().endswith('IE')))";assert s.count(old)==1;s=s.replace(old,"D=73100*.5**3/(12*(1-.33**2));ref=.5*D*.001**2*100*.001;actual=float(IE[-1])").replace('73100','22000').replace('.139','.0915').replace('.33','.25');namespace=dict(globals());exec(compile(s,__file__+'::review','exec'),namespace);namespace['review'](d,n)
    p=OUT/'review_w3_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(A26.__file__)),'sha256':streamsha(Path(A26.__file__)),'derived_source':s,'acceptance_thresholds_unchanged':True,'references_recomputed_from_declared_orthotropic_plane_parameters':True})

def create_runner():
    s=inspect.getsource(metal.run_one);audit=[]
    oldprop="prop=['/PROP/TYPE20/1','HALF_MM_HA8_SOLID_SHELL_TRANSLATIONS',ii(14,4)+' '*20+ii(10,222)+' '*20+ff(0),ff(0,0,0),ff(0,0,0,0,0),' '*20+ii(2)]"
    for old,new in [("OUT/'w2'","OUT/'w3'"),("n='A26_HA8_'+cid","n='A27_COMP_'+cid"),(";free=cid.startswith('FREE')",";m=m*(.00183/.00278);free=cid.startswith('FREE')"),(oldprop,"prop=composite_property()"),("P['/MAT/LAW2/1']+prop","P['/MAT/LAW25/4']+prop"),("'METAL_FULL_VOLUME',ii(1,1,0)","'ORTHOTROPIC_SKIN_VOLUME',ii(1,4,0)"),("'TYPE20':True,'Icstr':10","'TYPE22':True,'Icstr':10")]:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);exec(compile(s,__file__+'::run_one','exec'),globals());p=OUT/'runner_w3_derivation.json'
    if not p.exists():dump(p,{'created_utc':now(),'source':rel(Path(metal.__file__)),'source_sha256':streamsha(Path(metal.__file__)),'changes':audit,'derived_function_source':s,'old_generator_unchanged':True})

def run():
    guard();create_runner()
    for cid in read(CFG)['cases']:
        d=OUT/'w3'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case, no implicit rerun'
        else:run_one(cid)
    dump(OUT/'native_case_summary_w3.json',{'created_utc':now(),'cases':[read(OUT/'w3'/cid/'review.json') for cid in read(CFG)['cases']],'whole_insertion_ready':False,'core_coupling_and_curved_root_not_qualified':True})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
