"""Separate cached printing audit and fresh one-cycle junction-state observer."""
from probe_aircraft_a37 import *
from assess_aircraft_a23_reader_precision import printed_bound

def declare():
 guard();p=OUT/'observation_predeclaration.json';assert not p.exists()
 dump(p,{'created_utc':now(),'seed':1102062,'random_draws':0,'parent_configuration_sha256':streamsha(CFG),'cases':['CONTACT_EE','CONTACT_EI','CONTACT_EI_HALF'],'purpose':'Phase1 saved animation did not include its exact end. Read freshly produced phase1 complete restart in a separate explicit one-cycle observer to obtain initial full native fields before advancing. Compare exact same timestamp to phase2 initial fields. No original dynamic run repeated.','native_process_cap_s':180,'state_tolerances':'Original A37 junction tolerances unchanged','reader_addendum':'Independent six-significant-digit plus float32 storage rounding bounds from A23, original literal gates preserved','before_new_observers':True})

def observe():
 guard();assert read(OUT/'observation_predeclaration.json')['before_new_observers']
 for cid in read(OUT/'observation_predeclaration.json')['cases']:
  d=OUT/'w2_front_facets'/cid;g=read(d/'generation.json');n=g['name'];f2=min(read(d/'review.json')['fields'],key=lambda q:abs(q['time_ms']-.00920457) if '/phase2/' in q['path'] else 1e30);t=f2['time_ms'];p=d/'junction_observer';assert not p.exists();p.mkdir();dump(p/'generation.json',g);rows=[]
  for src in (d/'phase1').glob(n+'_0001*.rst'):
   dst=p/src.name;shutil.copy2(src,dst);sh=streamsha(src);assert streamsha(dst)==sh;rows.append({'source':rel(src),'target':rel(dst),'sha256':sh,'bytes':src.stat().st_size})
  assert rows;dump(p/'restart_transfer.json',{'created_utc':now(),'files':rows,'complete_native_copy':True});s=engine_cards(n,2,'E',1e-5,t+1e-6,'CONTACT');(p/(n+'_0002.rad')).write_text(s,encoding='utf8');ok=native(p,n,2)
  if ok:convert(p,n)
  dump(p/'observer_scope.json',{'created_utc':now(),'initial_state_only':True,'not_credited_as_new_impact_coverage':True,'intended_start_ms':t,'end_requested_ms':t+1e-6,'pass':ok})
  print({'junction_observer':cid,'completed':ok},flush=True)

def assess():
 guard();rows=[]
 for c in CASES:
  d=OUT/c['name'] if c['scope']=='FREE' else OUT/'w2_front_facets'/c['name'];original=read(d/'review.json');fieldrows=[]
  for r in original['fields']:
   q=vtk((ROOT/r['path']).read_text());order=np.argsort(q['NODE_ID']);g=read(d/'generation.json');X=np.asarray(g['nodes_mm']);p=q['points'].reshape(-1,3)[order];u=q['Displacement'].reshape(-1,3)[order];bound=printed_bound(p)+printed_bound(u)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(p),abs(u),abs(X)])+1e-8;ck={k:v for k,v in r['checks'].items() if k!='coordinate_displacement'};ck['identity_with_printing_and_float32_bound']=bool(np.all(abs(p-X-u)<=bound));fieldrows.append({'path':r['path'],'time_ms':r['time_ms'],'checks':ck,'pass':all(ck.values()),'maximum_bound_mm':float(bound.max()),'maximum_residual_mm':float(abs(p-X-u).max()),'literal_gate_preserved':r['checks']['coordinate_displacement']})
  revised=original['checks'].copy();revised['native_fields']=all(r['pass'] for r in fieldrows);junction=original['junction']
  if c['scope']=='CONTACT' and c['mode']!='I':
   p=d/'junction_observer';ob=sorted(p.glob('*.vtk'));assert ob;v1=vtk(ob[0].read_text());f2=min((r for r in original['fields'] if '/phase2/' in r['path']),key=lambda r:r['time_ms']);v2=vtk((ROOT/f2['path']).read_text());a=read(CFG)['acceptance'];checks={};diffs={}
   for key in ['points','Displacement','Velocity','3DELEM_Stress','3DELEM_Specific_Energy','EROSION_STATUS']:
    err=float(abs(v1[key]-v2[key]).max());tol=a['junction_state_absolute']+a['junction_state_relative']*max(float(abs(v1[key]).max()),float(abs(v2[key]).max()));checks[key]=err<=tol;diffs[key]={'difference':err,'tolerance':tol}
   checks['same_time']=abs(v1['time']-v2['time'])<a['junction_time_ms'];checks['native_restart_copy']=all(streamsha(ROOT/r['source'])==r['sha256']==streamsha(ROOT/r['target']) for r in read(p/'restart_transfer.json')['files']);junction={'observer':rel(ob[0]),'phase2':f2['path'],'first_ms':v1['time'],'second_ms':v2['time'],'checks':checks,'differences':diffs,'pass':all(checks.values()),'original_unequal_time_review_preserved':True};revised['junction']=junction['pass'];revised['active_contact_at_join']=float(abs(v1['3DELEM_Stress']).max())>1 and float(abs(v1['3DELEM_Specific_Energy']).max())>1e-4
  row={'created_utc':now(),'case':c['name'],'original_review':rel(d/'review.json'),'checks':revised,'pass':all(revised.values()),'fields':fieldrows,'junction':junction,'original_numerical_energy_momentum_gates_not_changed':True};dump(d/'observation_addendum.json',row);rows.append(row)
 dump(OUT/'native_review.json',{'created_utc':now(),'cases':rows,'pass':all(r['pass'] for r in rows),'new_full_impact':False,'failed_original_checks_preserved':True});print({'native_completed':len(rows),'qualified_individual':sum(r['pass'] for r in rows),'free_transition_qualified':False},flush=True)
 # Common-time comparisons, using exactly the cached final phase histories.
 cp=[]
 for scope in ['FREE','CONTACT']:
  base=OUT if scope=='FREE' else OUT/'w2_front_facets'
  for ca,cb,frac in [(scope+'_EE',scope+'_EI',.02),(scope+'_EI',scope+'_EI_HALF',.005),(scope+'_EI',scope+'_I',.02)]:
   hs=[]
   for name in [ca,cb]:
    p=base/name/('phase1' if name.endswith('_I') else 'phase2');fs=list(p.glob('*.csv'));assert len(fs)==1;hs.append(histories(fs[0]))
   lo=max(h['time'][0] for h in hs);hi=min(h['time'][-1] for h in hs);T=hs[0]['time'][(hs[0]['time']>=lo)&(hs[0]['time']<=hi)];K0=read(base/ca/'generation.json')['kinetic_energy_J'];cks={};errors={}
   for key in ['KINETIC ENERGY','INTERNAL ENERGY','ELASTIC CONTACT ENERGY']:
    vals=[np.interp(T,h['time'],h[key])*.001 for h in hs];err=float(abs(vals[0]-vals[1]).max());tol=frac*K0+1e-7;cks[key]=err<tol;errors[key]={'maximum_difference_J':err,'tolerance_J':tol}
   cp.append({'cases':[ca,cb],'first_ms':float(T[0]),'last_ms':float(T[-1]),'samples':len(T),'checks':cks,'errors':errors,'pass':all(cks.values())})
 dump(OUT/'comparison_review.json',{'created_utc':now(),'rows':cp,'pass':all(r['pass'] for r in cp),'no_whole_performance_extrapolation':True})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','observe','assess']);globals()[p.parse_args().action]()
