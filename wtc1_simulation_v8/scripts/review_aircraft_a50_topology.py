"""Preserve the original broad topology failure; identify only the predeclared rigid-link glyph changes."""
from probe_aircraft_a50 import *
from collections import Counter

def cells(q):
 v=q['cells'].astype(int);out=[];i=0
 while i<len(v):
  n=int(v[i]);out.append(v[i+1:i+1+n]);i+=n+1
 assert i==len(v) and len(out)==len(q['types']);return out

def main():
 guard();target=OUT/'declared_constraint_glyph_topology_addendum.json';assert not target.exists()
 c=read(CFG);links=read(ROOT/'wtc1_simulation_v8/data/aircraft_a49_flatten_predeclaration.json')['relations']
 allowed=Counter((x['intermediate'],x['direct_main'],n) for x in links for n in x['secondary_nodes']);assert sum(allowed.values())==384
 original=read(OUT/'explicit_startup_budget_review.json');assert not original['startup_budget_and_field_comparison_pass'];rows=[]
 for f in original['fields']:
  A=vtk((ROOT/f['cached']).read_text());B=vtk((ROOT/f['candidate']).read_text());CA,CB=cells(A),cells(B);idsA=A['NODE_ID'].astype(int);idsB=B['NODE_ID'].astype(int);seen=Counter();changes=[]
  assert np.array_equal(A['types'],B['types']) and np.array_equal(A['ELEMENT_ID'],B['ELEMENT_ID']) and np.array_equal(A['PART_ID'],B['PART_ID'])
  for i,(a,b) in enumerate(zip(CA,CB)):
   if np.array_equal(a,b):continue
   assert A['types'][i]==3 and len(a)==len(b)==2,'Undeclared physical or other glyph cell changed'
   aa=idsA[a];bb=idsB[b];positions=np.flatnonzero(aa!=bb);assert len(positions)==1
   j=int(positions[0]);other=1-j;assert aa[other]==bb[other]
   key=(int(aa[j]),int(bb[j]),int(aa[other]));assert key in allowed,key;seen[key]+=1
   changes.append({'cell_index':i,'element_id':int(A['ELEMENT_ID'][i]),'VTK_type':3,'old_nodes':aa.tolist(),'new_nodes':bb.tolist()})
  assert seen==allowed,'Missing or additional link glyph changes'
  independent={k:v for k,v in f['checks'].items() if k!='same_topology'};checks={**independent,'only_exact_384_declared_link_endpoints_changed':True,'physical_element_topology_identical':True,'element_and_part_ids_identical':True}
  rows.append({'time_ms':f['time_ms'],'checks':checks,'changed_glyphs':changes,'changed_glyph_count':len(changes),'pass':all(checks.values())})
 unaffected={k:v for k,v in original['checks'].items() if k!='saved_fields'}
 result={'created_utc':now(),'original_broad_topology_gate_pass':False,'original_campaign_report_preserved':rel(OUT/'explicit_startup_budget_review.json'),'reader_scope_correction':'The original full-array equality included rigid-link drawing edges whose reference IDs intentionally change. It remains failed. This separate audit verifies every changed endpoint against the144predeclared links and keeps every physical element, element/part ID and other edge exact.','predeclared_rigid_relations':144,'expected_changed_link_glyphs_per_frame':384,'frames':rows,'startup_budget_and_physical_field_supplemental_pass':all(unaffected.values()) and all(r['pass'] for r in rows),'acceptance_tolerances_or_physics_changed':False,'old_solver_replayed':False,'native_inertia_tensor_or_rotating_equivalence_qualified':False,'whole_impact_qualified':False,'new_whole_duration_credit_s':0}
 dump(target,result);print({k:result[k] for k in ['original_broad_topology_gate_pass','expected_changed_link_glyphs_per_frame','startup_budget_and_physical_field_supplemental_pass']},flush=True)

if __name__=='__main__':main()
