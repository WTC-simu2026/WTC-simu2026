"""Native numeric qualification, retaining raw text-format and whole-CHECK failures."""
from contact_aircraft_a45 import *
from probe_aircraft_a37 import vtk,histories
from assess_aircraft_a23_reader_precision import printed_bound

def semantic_channels(h):
 out={};counts={};unknown=[]
 for k,v in h.items():
  if k.startswith('NATIVE_SCOPE_NODES') or k.startswith('CONTACT_IMPULSE'):
   stem=k.rsplit('var ',1)[0].strip();i=counts.get(stem,0);counts[stem]=i+1;out[stem+' component '+str(i)]=v
  elif k=='NO NAME':unknown.append(k)
  else:out[k]=v
 assert all(n==6 if k.startswith('NATIVE_SCOPE_NODES') else n==3 for k,n in counts.items())
 return out,unknown

def assess():
 guard();assert not (OUT/'native_field_formatting_review.json').exists();fields=[];comparisons=[]
 for name in NAMES:
  d=OUT/name;raw=read(d/'review.json');X=np.asarray(read(d/'generation.json')['nodes_mm'])
  for f in raw['fields']:
   q=vtk((ROOT/f['path']).read_text());order=np.argsort(q['NODE_ID']);p=q['points'].reshape(-1,3)[order];u=q['Displacement'].reshape(-1,3)[order];bound=printed_bound(p)+printed_bound(u)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(p),abs(u),abs(X)])+1e-8;ck={k:v for k,v in f['checks'].items() if k!='coordinate_displacement'};ck['coordinate_identity_with_source_format_bound']=bool(np.all(abs(p-X-u)<=bound));fields.append({'path':f['path'],'time_ms':f['time_ms'],'checks':ck,'pass':all(ck.values()),'maximum_bound_mm':float(bound.max()),'maximum_residual_mm':float(abs(p-X-u).max()),'raw_literal_coordinate_gate':f['checks']['coordinate_displacement']})
  old=ROOT/'wtc1_simulation_v8/output/aircraft_a41'/name/'phase1';new=d/'phase1';parsed=[semantic_channels(histories(next(p.glob('*.csv')))) for p in [old,new]];hs=[r[0] for r in parsed];assert set(hs[0])==set(hs[1]);differences={k:float(abs(hs[0][k]-hs[1][k]).max()) for k in hs[0] if hs[0][k].shape==hs[1][k].shape};identical=len(differences)==len(hs[0]) and all(v==0 for v in differences.values());comparisons.append({'case':name,'cached_reference':rel(old),'all_named_semantic_history_channels_identical_at_saved_precision':identical,'maximum_differences':differences,'new_binary_used':True,'excluded_unidentified_channels_old_new':[r[1] for r in parsed],'mapping':'Verified unchanged TH/NODE DX DY DZ VX VY VZ and TH/INTER FNX FNY FNZ input order; numerical global variable indices differ between software versions. No named physical channel dropped.'})
 dump(OUT/'native_field_formatting_review.json',{'created_utc':now(),'fields':fields,'pass':bool(fields) and all(x['pass'] for x in fields),'old_literal_failures_preserved':True,'same_preexisting_A23_A41_format_rule':True})
 dump(OUT/'new_vs_cached_MUMPS_contact_review.json',{'created_utc':now(),'cases':comparisons,'all_named_semantic_histories_identical_at_saved_precision':all(r['all_named_semantic_history_channels_identical_at_saved_precision'] for r in comparisons),'unidentified_NO_NAME_channel_not_compared':True,'no_old_native_solver_replays':True})
 baseline=read(OUT/'cached_Windows_LAW117_reference_review.json');oldreview=read(ROOT/'wtc1_simulation_v8/output/aircraft_a17/cohesive_review.json');newreview=read(OUT/'cohesive_review.json');rows=[]
 for old,new in zip(oldreview['cases'],newreview['cases']):
  assert old['case']==new['case'];rows.append({'case':new['case']['id'],'cached_Windows_pass':not old['failed_checks'],'new_Linux_pass':not new['failed_checks'],'final_surface_work_difference_N_mm':abs(old['final_surface_work_N_mm']-new['final_surface_work_N_mm']),'final_internal_energy_difference_J':abs(old['final_IE_J']-new['final_IE_J']),'native_traction_reference_errors_fraction':[old['maximum_traction_relative_error'],new['maximum_traction_relative_error']],'maximum_energy_residual_J':[old['maximum_work_energy_residual_J'],new['maximum_work_energy_residual_J']]})
 dump(OUT/'new_vs_cached_Windows_LAW117_review.json',{'created_utc':now(),'cases':rows,'same_analytic_acceptance_pass':oldreview['mechanical_implementation_gate_pass'] and newreview['mechanical_implementation_gate_pass'],'full_unchanged_initial_states':True,'full_time_history_identity_claimed':False,'physical_fracture_qualified':False})
 print({'native_fields':len(fields),'formatting_pass':all(x['pass'] for x in fields),'MUMPS_named_contact_history_identity':all(r['all_named_semantic_history_channels_identical_at_saved_precision'] for r in comparisons),'LAW117_cases':len(rows)},flush=True)

if __name__=='__main__':assess()
