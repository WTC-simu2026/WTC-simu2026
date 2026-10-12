"""Resume cached, verified native explicit states with the qualified fixed-step MUMPS options."""
import probe_aircraft_a40 as experiment
from probe_aircraft_a40 import *
from probe_aircraft_a37 import vtk
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a37'
CASES=[{'name':scope+'_RREF_RESTART_'+suffix,'scope':scope,'mode':'I','dt_ms':dt,'platform':'Linux'} for scope,ds in [('FREE',[.001,.0005]),('CONTACT',[.00005,.000025])] for suffix,dt in zip(['BASE','HALF'],ds)]

def donor(scope):return SOURCE/'FREE_EE' if scope=='FREE' else SOURCE/'w2_front_facets/CONTACT_EE'

def declare():
 guard();p=OUT/'transition_predeclaration.json';assert not p.exists();fixed=read(OUT/'fixed_step_review.json');assert len(fixed['cases'])==2 and all(x['pass'] for x in fixed['cases']);rows=[];sealed={r['path']:r['sha256'] for r in read(SOURCE/'artifact_manifest.json')['files']}
 for scope in ['FREE','CONTACT']:
  d=donor(scope);g=read(d/'generation.json');n=g['name'];files=list((d/'phase1').glob(n+'_0001_*.rst'));qualified=next(x for x in read(SOURCE/'native_review.json')['cases'] if x['case']==scope+'_EE');assert files and qualified['pass'] and read(d/'phase1/starter_gate.json')['pass'];f=sorted((d/'phase2').glob('*.vtk'))[0]
  states=[]
  for q in files:assert streamsha(q)==sealed[rel(q)];states.append({'path':rel(q),'bytes':q.stat().st_size,'sha256':streamsha(q)})
  rows.append({'scope':scope,'donor':rel(d),'generation_sha256':streamsha(d/'generation.json'),'native_states':states,'cached_junction_field':rel(f),'cached_junction_field_sha256':streamsha(f),'native_join_ms':vtk(f.read_text())['time'],'qualified_source_review':rel(SOURCE/'native_review.json'),'qualified_source_review_sha256':streamsha(SOURCE/'native_review.json'),'original_raw_review_pass':read(d/'review.json')['pass'],'original_donor_field_acquisition_diagnostics_preserved':True,'fresh_Starter_or_explicit_replay':False})
 dump(p,{'created_utc':now(),'seed':1102065,'random_draws':0,'before_new_native':True,'parent_configuration_sha256':streamsha(CFG),'cases':CASES,'donors':rows,'numeric_options':{'MUMPS':True,'nonlinear_tolerances':[1e-11]*3,'force_reference_min_N':1.,'force_reference_max':1e30,'fixed_time_step':True,'minimum_dt_ms':1e-12,'Newmark_gamma_beta':[.5,.25]},'physical_fixture_unchanged':True,'full_native_state_copy_only':True,'no_field_injection_or_rescaling':True,'original_physical_gates_retained':True,'branch_rule':'Free restart base then half; if either fails, stop before contact. Contact base and half assess closed balance and numerical refinement; stop whole extension unless all original gates pass.','CPU_threads':1,'GPU':False,'per_process_cap_s':180,'estimated_seconds_max':720,'whole_duration_credit_s':0})
 print({'transitions_declared':True,'cached_explicit_states':True},flush=True)

def cards(n,index,mode,dt,end,scope,check=False):
 s=PARENT_CARDS(n,index,mode,dt,end,scope,check)
 if mode=='I':
  s=s.replace('0 123 1e-6 1e-6 1e-6','0 123 1e-11 1e-11 1e-11').replace('/IMPL/DT/STOP\n'+ff(1e-8,dt),'/IMPL/DT/STOP\n'+ff(1e-12,dt));s='/IMPL/RREF/LIMIT\n'+ff(1.,1e30)+'\n/IMPL/PRINT/NONLIN/1\n'+s
 return s

def one(c):
 d=OUT/c['name'];assert not d.exists();d.mkdir();p=d/'phase2';p.mkdir();source=donor(c['scope']);g=read(source/'generation.json');n=g['name'];g.update(case=c,name=n,configuration_sha256=streamsha(CFG),source_generation=rel(source/'generation.json'),source_generation_sha256=streamsha(source/'generation.json'),cached_native_initial_state=True);dump(d/'generation.json',g);dump(p/'generation.json',g);phase1=d/'phase1';phase1.mkdir();shutil.copy2(source/'phase1/starter_gate.json',phase1/'starter_gate.json');dump(phase1/'cached_source_notice.json',{'created_utc':now(),'source':rel(source/'phase1'),'no_fresh_Starter_or_solver':True});states=[]
 for f in (source/'phase1').glob(n+'_0001_*.rst'):
  q=p/f.name;shutil.copy2(f,q);h=streamsha(f);assert streamsha(q)==h;states.append({'source':rel(f),'target':rel(q),'sha256':h,'bytes':q.stat().st_size})
 dump(d/'restart_transfer.json',{'created_utc':now(),'files':states,'complete_native_copy':True,'physical_fields_not_injected':True});end=read(CFG)[c['scope'].lower()]['end_ms'];(p/(n+'_0002.rad')).write_text(cards(n,2,'I',c['dt_ms'],end,c['scope']),encoding='utf8');shutil.copy2(__file__,d/'generator_snapshot.py')
 ok=native37.native(p,n,2)
 if ok:dump(d/'run_completed.json',{'created_utc':now(),'pass':True,'only_new_phase2_solver':True})
 else:dump(d/'retained_failure.json',{'created_utc':now(),'phase2_native_completed':False})
 native37.audit_case(c);r=read(d/'review.json');sfield=sorted((source/'phase2').glob('*.vtk'))[0];source_sha=streamsha(sfield);decl=next(x for x in read(OUT/'transition_predeclaration.json')['donors'] if x['scope']==c['scope']);assert source_sha==decl['cached_junction_field_sha256'];junction={'pass':False,'reason':'new native phase did not complete'}
 if ok:
  f=sorted(p.glob('*.vtk'))[0];a=vtk(sfield.read_text());b=vtk(f.read_text());acc=read(CFG)['acceptance'];checks={};differences={}
  for key in ['points','Displacement','Velocity','3DELEM_Stress','3DELEM_Specific_Energy','EROSION_STATUS']:
   assert a[key].shape==b[key].shape;err=float(abs(a[key]-b[key]).max());tol=acc['junction_state_absolute']+acc['junction_state_relative']*max(float(abs(a[key]).max()),float(abs(b[key]).max()));checks[key]=err<=tol;differences[key]={'maximum_difference':err,'tolerance':tol}
  checks['same_time']=abs(a['time']-b['time'])<acc['junction_time_ms'];checks['native_state_copy']=all(streamsha(ROOT/q['source'])==q['sha256']==streamsha(ROOT/q['target']) for q in states)
  if c['scope']=='CONTACT':checks['active_contact_at_join']=float(abs(a['3DELEM_Stress']).max())>1 and float(abs(a['3DELEM_Specific_Energy']).max())>1e-4
  junction={'source_field':rel(sfield),'new_initial_field':rel(f),'source_time_ms':a['time'],'new_time_ms':b['time'],'checks':checks,'differences':differences,'pass':all(checks.values())}
 r['junction']=junction;r['checks']['cached_full_state_junction']=junction['pass'];r['pass']=all(r['checks'].values());r['source_Starter_reused_not_rerun']=True;dump(d/'transition_review.json',r);print({'transition':c['name'],'checks':r['checks'],'pass':r['pass']},flush=True);return r

def run():
 guard();assert read(OUT/'transition_predeclaration.json')['before_new_native'];native37.OUT=OUT;native37.CFG=CFG;rows=[]
 for c in CASES:
  r=one(c);rows.append(r)
  if c['scope']=='FREE' and not r['pass']:break
 dump(OUT/'transition_review.json',{'created_utc':now(),'cases':rows,'cached_donor_states_unchanged':True,'whole_impact_qualified':False});print({'transition_cases':len(rows),'passes':sum(r['pass'] for r in rows)},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
