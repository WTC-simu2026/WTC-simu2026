"""Same-state explicit/implicit loaded shell comparison; original whole properties retained."""
from probe_aircraft_a46 import ROOT,RUNTIME,CAND,BINARY,WHOLE,read,dump,rel,now,streamsha,harness,sections,ii,ff,group,env,win_execute
import probe_aircraft_a45 as launcher
import argparse,shutil,json,re,time,subprocess,numpy as np,tarfile,hashlib
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a47'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a47_predeclaration.json'
MODES=['MEMBRANE','BENDING']
DOCS={'node':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm','shell':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_shel_starter_r.htm'}

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256'];launcher.guard()

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A46';prior=ROOT/'wtc1_simulation_v8/output/aircraft_a46';assert read(prior/'publication_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
 patch=read(ROOT/'wtc1_simulation_v8/data/aircraft_a46_predeclaration.json')['patch'];X=np.asarray(patch['coordinates_mm']);center=X.mean(axis=0);Y=X-center;interior=np.flatnonzero((abs(Y[:,1])<1e-6)&(abs(Y[:,2])<1e-6));assert interior.tolist()==[4]
 t=np.r_[np.linspace(0,10,201),12.];z=np.minimum(t/10,1);s=10*z**3-15*z**4+6*z**5;E=200000;nu=.3;hmm=7.9375;area=patch['area_mm2'];epsilon=1e-5;kappa=1e-6
 c={'iteration':'AIRCRAFT-A47','declared_utc':now(),'seed':1102072,'random_draws':0,'purpose':'Compare source-identical steel facade shell under small prescribed boundary extension and anticlastic bending, with one free interior node; explicit/implicit direct from same native initial state.','units':['g','mm','ms'],'units_conversions':{'Nmm_to_J':.001,'g_to_kg':.001,'ms_to_s':.001},'patch':patch,'center_mm':center.tolist(),'interior_node_ids':[5],'boundary_node_ids':[i+1 for i in range(9) if i!=4],'material_property_whole_sections_unchanged':True,'load':{'ramp_ms':10,'end_ms':12,'times_ms':t.tolist(),'normalized_values':s.tolist(),'curve_interpolation':'Piecewise linear native FUNCT; reference uses identical interpolation, no output time shift.','membrane_strain':epsilon,'bending_curvature_per_mm':kappa,'bending_antiplane_curvature_per_mm':-nu*kappa,'initial_velocity':0},'reference':{'E_MPa':E,'nu':nu,'thickness_mm':hmm,'area_mm2':area,'membrane_energy_J':.5*E*epsilon**2*area*hmm*.001,'membrane_F1_MPa':E*epsilon,'membrane_F2_MPa':0,'bending_energy_J':E*hmm**3*kappa**2*area/24*.001,'bending_M1_MPa':E*hmm*kappa/12,'bending_M2_MPa':0,'scope':'Continuum plane stress affine membrane exact; homogeneous small-curvature Kirchhoff plate bending is an independent continuum reference, not a claim of exact coarse shell discretization.','source':'Linear isotropic plane stress Hooke law and through-thickness integral z²=h³/12; no historical damage data.'},'execution':{'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_total_s':300,'maximum_total_s':1080,'fresh_Starter_states':2,'Engine_cases':4,'no_software_installation_or_compilation':True,'dt_ms':.001,'history_dt_ms':.001,'animation_dt_ms':.5,'explicit_scale':.4,'implicit_Newmark':[.5,.25],'implicit_MUMPS':2,'nonlinear_tolerances':[1e-11]*3,'mass_scaling':False},'acceptance':{'Starter_warnings':0,'Starter_errors':0,'mass_relative':1e-6,'added_mass_relative':1e-9,'energy_fraction':.02,'absolute_energy_J':1e-7,'prescribed_displacement_mm':2e-5,'prescribed_rotation_rad':2e-6,'analytic_membrane_energy_fraction':.02,'analytic_bending_energy_fraction':.02,'analytic_resultant_fraction':.02,'explicit_implicit_energy_fraction':.02,'explicit_implicit_displacement_mm':2e-5,'force_or_moment_absolute_MPa':1e-5,'no_plastic_work_J':1e-7,'no_erosion':True},'sources':[{'path':rel(WHOLE),'sha256':streamsha(WHOLE)},{'path':rel(BINARY),'sha256':streamsha(BINARY)},{'path':rel(prior/'composite_qualification_review.json'),'sha256':streamsha(prior/'composite_qualification_review.json')}],'primary_documentation':DOCS,'whole_physics_changed':False,'new_whole_duration_credit_s':0,'objective1_complete':False,'conditional_refinement':'Do not rerun a failed native case. Further declared refinement/contract diagnosis only from retained evidence; never alter original criteria.'}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_native':True});pins={r['path']:r for f in ['preservation_before_metadata.json','artifact_manifest.json'] for r in read(prior/f)['files']}
 for f in ['artifact_manifest.json','publication_verification.json']:
  p=prior/f;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 rows=[]
 for r in pins.values():
  q=(ROOT/r['path']).stat();assert q.st_size==r['bytes'];rows.append({'path':r['path'],'bytes':r['bytes'],'sha256':r['sha256'],'mtime_ns_before':q.st_mtime_ns})
 dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'method':'Immutable prior SHA manifests retained, before/after metadata audit; not a fresh complete content rehash.','source_archives_not_rescanned':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':'A45 qualified six native controls and was publicly verified; A46 completed two fresh shell assemblies with actual mechanical warnings preserved, changing next action to loaded response.','same_external_blocker':False});print({'A47_declared':True,'fresh_Starter':2,'new_Engine':4,'expected_s':300},flush=True)

def amplitudes(mode,c):
 x=np.asarray(c['patch']['coordinates_mm'])-c['center_mm'];v=np.zeros((9,6));nu=c['reference']['nu']
 if mode=='MEMBRANE':v[:,1]=c['load']['membrane_strain']*x[:,1];v[:,2]=-nu*c['load']['membrane_strain']*x[:,2]
 else:
  k=c['load']['bending_curvature_per_mm'];v[:,0]=-.5*k*(x[:,1]**2-nu*x[:,2]**2);v[:,4]=nu*k*x[:,2];v[:,5]=k*x[:,1]
 return v

def prepare(mode):
 guard();c=read(CFG);d=OUT/mode/'preparation';assert not d.exists();d.mkdir(parents=True);n='A47_'+mode;sec=sections();patch=c['patch'];mapping={k:i+1 for i,k in enumerate(patch['original_node_ids'])};X=patch['coordinates_mm'];V=amplitudes(mode,c)
 L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*x) for i,x in enumerate(X)]
 for key in ['/MAT/LAW2/3','/PROP/TYPE1/31','/PART/31']:L+=[key]+sec[key]
 L+=['/SHELL/31']+[ii(i+1,*[mapping[n] for n in e[1:]]) for i,e in enumerate(patch['original_elements'])]+['/FUNCT/900','DECLARED_SMOOTH_LOAD']+[ff(t,s) for t,s in zip(c['load']['times_ms'],c['load']['normalized_values'])]
 for ni in c['boundary_node_ids']:
  L+=group(1000+ni,'DECLARED_BOUNDARY_NODE',[ni])
  for j,ax in enumerate(['X','Y','Z','XX','YY','ZZ']):
   if V[ni-1,j]==0:continue
   gid=2000+ni*10+j;L+=[f'/IMPDISP/{gid}','KNOWN_SMALL_ELASTIC_BOUNDARY',ii(900)+f'{ax:>10}'+ii(0,0,1000+ni)+' '*10+ii(0),ff(float(V[ni-1,j]),1,0,1e30)]
  # Fixed components and imposed components are mutually exclusive.
  trans=''.join('1' if V[ni-1,j]==0 else '0' for j in range(3));rot=''.join('1' if V[ni-1,j]==0 else '0' for j in range(3,6));L+=[f'/BCS/{1000+ni}','ONLY_ZERO_BOUNDARY_COMPONENTS',f'{trans:>6} {rot:>3}'+ii(0,1000+ni)]
 L+=['/TH/PART/31','PATCH_ENERGY',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(31)]
 for k,variables in [('MOTION',['DX','DY','DZ','DRX','DRY','DRZ','VX','VY','VZ','VRX','VRY','VRZ']),('REACTION',['REACX','REACY','REACZ','REACXX','REACYY','REACZZ'])]:
  L+=[f'/TH/NODE/{1 if k=="MOTION" else 2}','NATIVE_'+k]
  for i in range(0,len(variables),10):L+=[''.join(f'{v:>10}' for v in variables[i:i+10])]
  L+=[ii(i,0) for i in range(1,10)]
 L+=['/TH/SHEL/3','NATIVE_RESULTANTS',''.join(f'{v:>10}' for v in ['F1','F2','F12','M1','M2','M12','OFF','THIC'])]+[ii(i,0) for i in range(1,5)]+['/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf8');dump(d/'generation.json',{'created_utc':now(),'name':n,'mode':mode,'nodal_amplitudes':V.tolist(),'configuration_sha256':streamsha(CFG),'unmodified_physical_sections':['MAT/LAW2/3','PROP/TYPE1/31','PART/31'],'free_interior_node':5})
 ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,env());log=(d/'starter.log').read_text(errors='replace');w=int(re.findall(r'(\d+) WARNING\(S\)',log)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',log)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'warnings':w,'errors':e,'pass':ok and w==0 and e==0});return d,n,ok and w==0 and e==0

def run():
 guard();c=read(CFG);rows=[]
 for mode in MODES:
  src,n,strict=prepare(mode)
  if not strict:rows.append({'mode':mode,'Starter_pass':False,'Engine_not_run':True});continue
  for method in ['EXPLICIT','IMPLICIT']:
   d=OUT/mode/method;d.mkdir();rst=src/(n+'_0000_0001.rst');shutil.copy2(rst,d/rst.name);assert streamsha(rst)==streamsha(d/rst.name);shutil.copy2(src/'generation.json',d/'generation.json');dump(d/'state_transfer.json',{'created_utc':now(),'source':rel(rst),'target':rel(d/rst.name),'sha256':streamsha(rst),'full_unchanged_initial_state':True})
   dt=c['execution']['dt_ms'];end=c['load']['end_ms']
   if method=='EXPLICIT':E=['/DT',ff(.4,0),'/DTIX',ff(dt,dt)]
   else:E=['/IMPL/RREF/LIMIT',ff(1,1e30),'/IMPL/NONLIN/1','0 123 1e-11 1e-11 1e-11','/IMPL/SOLVER/2',ii(2,0,1)+ff(1e-8),'/IMPL/DTINI',ff(dt),'/IMPL/DYNA/2',ff(.5,.25),'/IMPL/DT/1',ii(2)+ff(1)+ii(30)+ff(.5),'/IMPL/DT/STOP',ff(1e-12,dt)]
   E+=['/ANIM/DT',ff(0,.5),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/PRINT/-100/100',f'/RUN/{n}/1',ff(end),'/TFILE/4',ff(dt),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf8');ok=launcher.execute(d,n);converted=False
   if ok:
    converted=win_execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env())
   rows.append({'mode':mode,'method':method,'Starter_pass':True,'native_completed':ok,'history_converted':converted});print(rows[-1],flush=True)
 dump(OUT/'native_execution_review.json',{'created_utc':now(),'cases':rows,'whole_duration_credit_s':0,'whole_impact_qualified':False})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
