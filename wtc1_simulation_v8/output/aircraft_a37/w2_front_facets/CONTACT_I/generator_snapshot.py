"""Fresh native restart transitions and unchanged whole-model implicit check."""
from run_aircraft_a23 import ROOT,RUNTIME,read,dump,rel,now,harness,execute as win_execute,env,streamsha,ff,ii,parent,group,brick_grid,prop,histories
import probe_aircraft_a36 as prior
import build_aircraft_a35_mumps as build
from audit_aircraft_a05 import vtk
from pathlib import Path
import numpy as np
import argparse,re,json,shutil,time,traceback

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a37'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a37_predeclaration.json'
WHOLE=ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20/A20_CORE3D_TIED_20_0000.rad'
CASES=[{'name':s+'_'+v,'scope':s,'mode':v,'dt_ms':dt} for s,ds in [('FREE',[.001,.0005]),('CONTACT',[.00005,.000025])] for v,dt in [('EE',.00001),('EI',ds[0]),('EI_HALF',ds[1]),('I',ds[0])]]
DOCS={
 'compatibility':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/implicit_features_compatibility_intro_c.htm',
 'activation':'https://help.altair.com/2024/hwsolvers/rad/topics/solvers/rad/implicit_analysis_activation_r.htm',
 'check':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_check_engine_r.htm',
 'contact7':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm',
 'time_control':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_1_engine_r.htm',
 'time_stop':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/impl_dt_stop_engine_r.htm'}

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists()
 h=harness();assert h['CurrentIteration']=='AIRCRAFT-A36'
 cy=read(ROOT/'harness/publication_cycle.json');assert cy['pending_iterations']==['AIRCRAFT-A36']
 OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 sources=[WHOLE,RUNTIME/'starter_win64.exe',build.CAND/'isolated_exec/engine_linux64_gf_ompi',build.CAND/'isolated_exec/libopen_reader_linux64.so',build.CAND/'source/engine/source/input/freimpl.F',build.CAND/'source/engine/source/implicit/imp_solv.F']
 c={'iteration':'AIRCRAFT-A37','declared_utc':now(),'seed':1102062,'random_draws':0,'cases':CASES,'purpose':'Native full restart explicit-to-implicit with free motion and active bounded contact, then unchanged whole model compatibility. No 10s physical credit from checker.',
 'units':{'input':['g','mm','ms'],'energy_Nmm_to_J':.001,'momentum_g_mm_ms_to_Ns':.001,'velocity_mm_ms_to_m_s':1},
 'geometry':{'free':'One 1mm cube N2, 27nodes 8HA8 bricks','contact':'Two separate 1mm cubes N2, 54nodes 16HA8 bricks, left x[-1.05,-.05], right [.05,1.05], y/z[-.5,.5]'},
 'material':'Unchanged LAW2/1 source rho .00278g/mm3 E73100MPa nu.33 yield324MPa, no added failure','property':'TYPE14 HA8 Isolid14 Ismstr4 Icpre2 Gauss222 Iframe2',
 'free':{'velocity_mm_ms':[-200,5,2],'mass_g':.00278,'join_ms':.04,'end_ms':.1,'history_dt_ms':.001,'animation_dt_ms':.01},
 'contact':{'velocity_left_mm_ms':[5,0,0],'velocity_right_mm_ms':[-5,0,0],'mass_g':.00556,'join_ms':.0092,'end_ms':.015,'history_dt_ms':.00005,'animation_dt_ms':.0002,'type':7,'stiffness_flag':4,'scale':1,'gap_mm':.01,'friction':0,'viscous_stiffness_coefficient':1e-20,'no_boundary_constraints':True,'scope':'Closed elastic collision witness, not AA11 material qualification; no silent replacement of whole TYPE25'},
 'implicit':{'solver':2,'Newmark_gamma':.5,'Newmark_beta':.25,'nonlinear_tolerances':[1e-6]*3,'time_control':'It_w2 scale_i1 maximumIterations30 scale_d.5; dtmin1e-8ms dtmax=declared initial step'},
 'execution':{'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'estimated_seconds_max':2700,'expected_seconds':300,'mass_scaling':False,'new_installation_or_compilation':False,'old_native_solver_reruns':0},
 'acceptance':{'mass_relative':1e-6,'added_mass_relative':1e-9,'energy_relative':.02,'energy_absolute_J':1e-7,'momentum_relative':.02,'momentum_absolute_Ns':1e-9,'free_displacement_mm':2e-5,'free_velocity_mm_ms':2e-4,'junction_state_relative':1e-5,'junction_state_absolute':1e-6,'junction_time_ms':2e-5,'contact_impulse_observable_Ns':1e-6,'contact_IE_observable_J':1e-7,'comparison_energy_relative':.02,'comparison_energy_absolute_J':1e-7,'half_dt_energy_relative':.005},
 'restart':'Fresh Windows Starter writes initial native state; Linux compiled engine runs all dynamics. Phase2 receives complete freshly produced phase1 restart files, byte/hash identity, no CSV injection. Fresh directories prevent output overwrite.',
 'whole_check':{'input_unchanged_physics':True,'mode':'/IMPL/CHECK','conditional':'Checking permitted independent of transition result; actual whole dynamics only after transition/contact compatibility gates','no_simulated_time_credit':True},
 'sources':[{'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size} for p in sources],'primary_documentation':DOCS,'source_commit':build.PIN,'whole_insertion_ready':False,'objective1_complete':False}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_native':True})
 pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(prior.OUT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=prior.OUT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archive_rescanned':False})
 print({'A37_declared':True,'fresh_cases':len(CASES),'cap_seconds_per_process':180},flush=True)

def fixture(scope):
 if scope=='FREE':
  X,B,m,l,r=brick_grid([2]*3,[-.5]*3,[.5]*3);V=np.tile([-200.,5,2],(len(X),1));parts=[1];M=parent()['/MAT/LAW2/1']+prop()+['/PART/1','PHYSICAL_CUBE',ii(1,1,0),'/BRICK/1']+[ii(i+1,*b) for i,b in enumerate(B)];return X,B,m,V,parts,M
 X1,B1,m1,l1,r1=brick_grid([2]*3,[-1.05,-.5,-.5],[-.05,.5,.5]);X2,B2,m2,l2,r2=brick_grid([2]*3,[.05,-.5,-.5],[1.05,.5,.5],first=28)
 X=np.vstack([X1,X2]);m=np.r_[m1,m2];V=np.vstack([np.tile([5.,0,0],(27,1)),np.tile([-5.,0,0],(27,1))]);M=parent()['/MAT/LAW2/1']+prop()
 for pid,B in [(1,B1),(2,B2)]:M+=[f'/PART/{pid}','CLOSED_ELASTIC_BODY_'+str(pid),ii(1,1,0),f'/BRICK/{pid}']+[ii((pid-1)*8+i+1,*b) for i,b in enumerate(B)]
 M+=['/SURF/PART/101','LEFT_BODY_MAIN',ii(1)]+group(102,'RIGHT_FRONT_SECONDARY',l2)+['/INTER/TYPE7/1','ELASTIC_CONTACT_WITNESS',ii(102,101,4,0,1000)+' '*10+ii(0,1000,0,0),ff(1,0,0)+' '*20+ii(0,0),ff(0,1e30,0,0)+ii(1,3),ff(1,0,.01,0,1e30),'       000'+' '*20+ii(1000)+ff(1e-20,1,.2),ii(0,0)+ff(0)+ii(0,0,0)+ff(0)+ii(0),'/TH/INTER/1','CONTACT_IMPULSE',''.join(f'{v:>10}' for v in ['FNX','FNY','FNZ']),ii(1)]
 # TH contact groups share the Starter namespace with part histories.
 M[M.index('/TH/INTER/1')]='/TH/INTER/11'
 # Enumerate the actual four front facets of the unchanged left solid.
 # /SURF/PART automatic extraction failed in the retained Starter attempts.
 si=M.index('/SURF/PART/101')
 front=[b for b in B1 if all(abs(X1[j-1,0]+.05)<1e-12 for j in [b[1],b[2],b[6],b[5]])]
 assert len(front)==4
 M[si:si+3]=['/SURF/SEG/101','LEFT_FRONT_PHYSICAL_FACETS']+[ii(k+1,b[1],b[2],b[6],b[5]) for k,b in enumerate(front)]
 return X,B1+B2,m,V,[1,2],M

def engine_cards(n,index,mode,dt,end,scope,check=False):
 q=read(CFG)[scope.lower()] if scope!='WHOLE' else {'animation_dt_ms':1,'history_dt_ms':1}
 E=[]
 if mode=='I':E=['/IMPL/NONLIN/1','0 123 1e-6 1e-6 1e-6','/IMPL/SOLVER/2',ii(2,0,1)+ff(1e-8),'/IMPL/DTINI',ff(dt),'/IMPL/DYNA/2',ff(.5,.25),'/IMPL/DT/1',ii(2)+ff(1)+ii(30)+ff(.5),'/IMPL/DT/STOP',ff(1e-8,dt)]
 else:E=['/DT',ff(.4,0),'/DTIX',ff(dt,dt)]
 if check:E+=['/IMPL/CHECK']
 else:E+=['/ANIM/DT',ff(0,q['animation_dt_ms']),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/ANIM/BRICK/TENS/STRESS']
 E+=['/PRINT/-100/100',f'/RUN/{n}/{index}',ff(end),'/TFILE/4',ff(q['history_dt_ms']),'/VERS/2026']
 return '\n'.join(E)+'\n'

def native(d,n,index):
 ok=prior.execute(RUNTIME/'engine_win64.exe',['-i',f'{n}_{index:04}.rad'],d,'engine.log',180,env());s=(d/'engine.log').read_text(errors='replace') if (d/'engine.log').exists() else ''
 dump(d/'completion.json',{'created_utc':now(),'exit_ok':ok,'normal_termination':'NORMAL TERMINATION' in s,'pass':ok and 'NORMAL TERMINATION' in s});return ok and 'NORMAL TERMINATION' in s

def prepare_case(case):
 guard();d=OUT/case['name'];assert not d.exists();d.mkdir();p=d/'phase1';p.mkdir();scope=case['scope'];n='A37_'+case['name'];X,B,m,V,parts,M=fixture(scope);q=read(CFG)[scope.lower()]
 L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*x) for i,x in enumerate(X)]+M
 for ni,v in enumerate(V,1):L+=group(ni,'PHYSICAL_INITIAL_NODE',[ni])+[f'/INIVEL/TRA/{ni}','INITIAL_TRANSLATION',ff(*v)+ii(ni,0),ff(0)+ii(0)]
 L+=['/TH/PART/1','PHYSICAL_BODIES',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(*parts),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(j,0) for j in range(1,len(X)+1)]+['/END']
 (p/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf8');mode='I' if case['mode']=='I' else 'E';end=q['end_ms'] if mode=='I' else q['join_ms'];dt=case['dt_ms'] if mode=='I' else 1e-5
 (p/(n+'_0001.rad')).write_text(engine_cards(n,1,mode,dt,end,scope),encoding='utf8')
 meta={'created_utc':now(),'case':{**case,'platform':'Linux'},'name':n,'nodes_mm':X.tolist(),'bricks':B,'nodal_masses_g':m.tolist(),'initial_velocity_mm_ms':V.tolist(),'expected_mass_g':float(m.sum()),'configuration_sha256':streamsha(CFG),'kinetic_energy_J':float(.5*np.sum(m[:,None]*V**2)*.001),'momentum_Ns':(np.sum(m[:,None]*V,axis=0)*.001).tolist()};dump(d/'generation.json',meta);dump(p/'generation.json',meta);shutil.copy2(__file__,d/'generator_snapshot.py')
 return d,p,n

def start_case(case):
 d,p,n=prepare_case(case)
 try:
  en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],p,'starter.log',180,en);s=(p/'starter.log').read_text(errors='replace');w=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);e=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(p/'starter_gate.json',{'warnings':w,'errors':e,'pass':ok and w==0 and e==0});assert ok and w==0 and e==0
  assert native(p,n,1),'phase1 did not complete'
  if case['mode']!='I':
   p2=d/'phase2';p2.mkdir();dump(p2/'generation.json',read(d/'generation.json'));rows=[]
   files=list(p.glob(n+'_0001*.rst'));assert files,'complete phase1 native restart absent'
   for f in files:
    target=p2/f.name;shutil.copy2(f,target);sh=streamsha(f);assert streamsha(target)==sh;rows.append({'source':rel(f),'target':rel(target),'bytes':f.stat().st_size,'sha256':sh})
   dump(d/'restart_transfer.json',{'created_utc':now(),'files':rows,'complete_native_copy':True,'physical_fields_not_injected':True})
   mode='E' if case['mode']=='EE' else 'I';q=read(CFG)[case['scope'].lower()];(p2/(n+'_0002.rad')).write_text(engine_cards(n,2,mode,case['dt_ms'],q['end_ms'],case['scope']),encoding='utf8');assert native(p2,n,2),'phase2 did not complete'
  dump(d/'run_completed.json',{'created_utc':now(),'pass':True})
 except Exception:dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'no_successful_solver_rerun':True})
 print({'case':case['name'],'completed':(d/'run_completed.json').exists()},flush=True)

def run(scope):
 guard()
 for c in CASES:
  if c['scope']==scope:start_case(c)

def whole_check():
 guard();d=OUT/'whole_compatibility';assert not d.exists();d.mkdir();n='A37_WHOLE_CHECK';s=WHOLE.read_text(encoding='utf8');l=s.splitlines();original=l.copy()
 for k in ['/BEGIN','/TITLE']:i=l.index(k);l[i+1]=n
 changes=[i+1 for i,(a,b) in enumerate(zip(original,l)) if a!=b];assert len(changes)==2
 (d/(n+'_0000.rad')).write_text('\n'.join(l)+'\n',encoding='utf8');(d/(n+'_0001.rad')).write_text(engine_cards(n,1,'I',.001,.001,'WHOLE',True),encoding='utf8');dump(d/'generation.json',{'case':{'platform':'Linux'},'name':n,'source_path':rel(WHOLE),'source_sha256':streamsha(WHOLE),'only_changed_name_lines':changes,'input_physics_unchanged':True,'simulated_seconds_credit':0})
 counts={}
 for row in l:
  if row.startswith('/'):k='/'.join(row.split('/')[:3]);counts[k]=counts.get(k,0)+1
 dump(d/'features.json',{'created_utc':now(),'counts':counts,'type25_contacts':counts.get('/INTER/TYPE25',0),'kinematic_spot5_ties':counts.get('/INTER/TYPE2',0),'documentation':DOCS['compatibility'],'documented_contact_support':[5,7,10,11],'whole_dynamics_not_executed':True})
 try:
  en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=win_execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,en);assert ok;native(d,n,1)
 except Exception:dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc()})
 print({'whole_compatibility_checked':True,'physical_seconds_added':0},flush=True)

def convert(d,n):
 guard();en=env();en.update(OMP_NUM_THREADS='1')
 for p in sorted(d.glob(n+'T[0-9][0-9]')):
  if not p.with_suffix('.csv').exists():assert win_execute(RUNTIME/'th_to_csv_win64.exe',[p.name],d,p.name+'.converter.log',60,en)
 for p in sorted(d.glob(n+'A[0-9][0-9][0-9]')):
  target=p.with_suffix('.vtk')
  if not target.exists():
   import subprocess
   r=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(p)],capture_output=True,timeout=60,env=en);assert r.returncode==0;target.write_bytes(r.stdout)

def audit_case(case):
 guard();d=OUT/case['name'];g=read(d/'generation.json');n=g['name'];m=np.asarray(g['nodal_masses_g']);X=np.asarray(g['nodes_mm']);V0=np.asarray(g['initial_velocity_mm_ms']);a=read(CFG)['acceptance'];K0=g['kinetic_energy_J'];P0=np.asarray(g['momentum_Ns']);ph=[];fields=[];checks={'native_completed':(d/'run_completed.json').exists(),'strict_starter':read(d/'phase1/starter_gate.json')['pass']};HT=[]
 for p in [d/'phase1',d/'phase2']:
  if not p.exists() or not (p/'completion.json').exists() or not read(p/'completion.json')['pass']:continue
  convert(p,n)
  for f in sorted(p.glob(n+'T[0-9][0-9].csv')):
   H=histories(f);T=H['time'];ks=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];ids=[int(re.match(r'NATIVE_SCOPE_NODES\s+(\d+)\s',k).group(1)) for k in ks][::6];assert set(ids)==set(range(1,len(m)+1));F=np.column_stack([H[k] for k in ks]).reshape(len(T),len(m),6);order=np.argsort(ids);U=F[:,order,:3];V=F[:,order,3:];P=np.sum(m[None,:,None]*V,axis=1)*.001;KN=.5*np.sum(m[None,:,None]*V**2,axis=(1,2))*.001
   terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY '];E=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;R=E-K0-EW;pt=.02*float(np.sum(m[:,None]*abs(V0)))*.001+1e-9;et=.02*K0+1e-7
   ck={'finite':all(np.isfinite(v).all() for v in H.values()),'mass':float(abs(H['MASS']-m.sum()).max())<1e-6*m.sum(),'no_added_mass':float(abs(H['ADDED MASS']).max())<1e-9*m.sum(),'full_native_energy_balance':float(abs(R).max())<et,'physical_nodal_KE_matches_global':float(abs(KN-H['KINETIC ENERGY']*.001).max())<et,'physical_nodal_P_matches_global':float(abs(P-np.column_stack([H[k+'-MOMENTUM'] for k in 'XYZ'])*.001).max())<pt,'closed_momentum':float(np.linalg.norm(P-P0,axis=1).max())<pt,'zero_external_work':float(abs(EW).max())<1e-7,'elastic_no_PW':float(abs(H['PLASTIC WORK']*.001).max())<1e-7}
   if case['scope']=='FREE':ck.update(free_displacement=float(abs(U-T[:,None,None]*V0).max())<a['free_displacement_mm'],free_velocity=float(abs(V-V0).max())<a['free_velocity_mm_ms'],free_internal_energy=float(abs(H['INTERNAL ENERGY']*.001).max())<1e-7)
   q={'history':rel(f),'checks':{k:bool(v) for k,v in ck.items()},'first_ms':float(T[0]),'last_ms':float(T[-1]),'energy_residual_J':float(abs(R).max()),'energy_tolerance_J':et,'maximum_IE_J':float(abs(H['INTERNAL ENERGY']*.001).max()),'maximum_KE_J':float(abs(H['KINETIC ENERGY']*.001).max()),'momentum_error_Ns':float(np.linalg.norm(P-P0,axis=1).max()),'pass':all(ck.values())};ph.append(q);HT.append((p,H))
  for f in sorted(p.glob(n+'A[0-9][0-9][0-9].vtk')):
   q=vtk(f.read_text());ids=q['NODE_ID'].astype(int);order=np.argsort(ids);pt=q['points'].reshape(-1,3)[order];U=q['Displacement'].reshape(-1,3)[order];V=q['Velocity'].reshape(-1,3)[order];ce=float(abs(pt-X-U).max());tol=4e-6*max(1,float(abs(pt).max()));ck={'all_node_ids':set(ids)==set(range(1,len(m)+1)),'finite':all(np.isfinite(v).all() for v in q.values()),'coordinate_displacement':ce<tol,'no_erosion':bool(np.all(q['EROSION_STATUS']>0))};fields.append({'path':rel(f),'time_ms':q['time'],'checks':ck,'pass':all(ck.values()),'coordinate_residual_mm':ce,'tolerance_mm':tol})
 checks.update(histories=bool(ph) and all(q['pass'] for q in ph),native_fields=bool(fields) and all(q['pass'] for q in fields))
 junction=None
 if case['mode']!='I' and (d/'phase2/completion.json').exists() and read(d/'phase2/completion.json')['pass']:
  f1=max([f for f in fields if '/phase1/' in f['path']],key=lambda r:r['time_ms']);f2=min([f for f in fields if '/phase2/' in f['path']],key=lambda r:r['time_ms']);v1=vtk((ROOT/f1['path']).read_text());v2=vtk((ROOT/f2['path']).read_text());diffs={};jc={}
  for key in ['points','Displacement','Velocity','3DELEM_Stress','3DELEM_Specific_Energy','EROSION_STATUS']:
   assert v1[key].shape==v2[key].shape;err=float(abs(v1[key]-v2[key]).max());tol=a['junction_state_absolute']+a['junction_state_relative']*max(float(abs(v1[key]).max()),float(abs(v2[key]).max()));diffs[key]={'maximum_difference':err,'tolerance':tol};jc[key]=err<=tol
  jc['same_time']=abs(f1['time_ms']-f2['time_ms'])<a['junction_time_ms'];jc['native_restart_hash_copy']=all(streamsha(ROOT/r['source'])==r['sha256']==streamsha(ROOT/r['target']) for r in read(d/'restart_transfer.json')['files']);junction={'phase1_time_ms':f1['time_ms'],'phase2_time_ms':f2['time_ms'],'checks':jc,'differences':diffs,'pass':all(jc.values())};checks['junction']=junction['pass']
  if case['scope']=='CONTACT':
   checks['active_contact_at_join']=float(abs(v1['3DELEM_Stress']).max())>1 and float(abs(v1['3DELEM_Specific_Energy']).max())>1e-4
 if case['scope']=='CONTACT' and HT:
  H=HT[-1][1];ks=[k for k in H if k.startswith('CONTACT_IMPULSE')];J=np.column_stack([H[k] for k in ks])* .001 if len(ks)==3 else np.zeros((len(H['time']),3));checks['observable_contact']=bool(float(abs(J).max())>a['contact_impulse_observable_Ns'] and max(q['maximum_IE_J'] for q in ph)>a['contact_IE_observable_J'])
 dump(d/'review.json',{'created_utc':now(),'case':case,'checks':checks,'pass':all(checks.values()),'histories':ph,'fields':fields,'junction':junction,'whole_scope_qualified':False});print({'review':case['name'],'checks':checks},flush=True)

def audit():
 guard()
 for c in CASES:
  if (OUT/c['name']).exists():audit_case(c)
 rows=[]
 for scope in ['FREE','CONTACT']:
  for ca,cb,frac in [(scope+'_EE',scope+'_EI',.02),(scope+'_EI',scope+'_EI_HALF',.005),(scope+'_EI',scope+'_I',.02)]:
   ds=[OUT/ca,OUT/cb]
   if not all((d/'run_completed.json').exists() for d in ds):rows.append({'cases':[ca,cb],'pass':False,'reason':'Native completion missing'});continue
   hs=[]
   for d in ds:
    fs=list((d/('phase1' if d.name.endswith('_I') else 'phase2')).glob('*.csv'));assert len(fs)==1;hs.append(histories(fs[0]))
   lo=max(h['time'][0] for h in hs);hi=min(h['time'][-1] for h in hs);tt=hs[0]['time'][(hs[0]['time']>=lo)&(hs[0]['time']<=hi)];errs={};cks={};K0=read(ds[0]/'generation.json')['kinetic_energy_J']
   for key in ['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']:
    ee=[np.interp(tt,h['time'],h[key])*.001 for h in hs];df=float(abs(ee[0]-ee[1]).max());tol=frac*K0+1e-7;errs[key]={'maximum_difference_J':df,'tolerance_J':tol};cks[key]=df<tol
   rows.append({'cases':[ca,cb],'first_ms':float(tt[0]),'last_ms':float(tt[-1]),'samples':len(tt),'checks':cks,'errors':errs,'pass':all(cks.values())})
 dump(OUT/'comparison_review.json',{'created_utc':now(),'rows':rows,'pass':all(r['pass'] for r in rows),'no_whole_performance_extrapolation':True})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','free','contact','whole','audit']);act=p.parse_args().action
 if act in ['free','contact']:run(act.upper())
 else:globals()[{'whole':'whole_check'}.get(act,act)]()
