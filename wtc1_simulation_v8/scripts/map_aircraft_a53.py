"""Verify the actual current triangle block against source element IDs, node labels and coordinates."""
from probe_aircraft_a53 import *
from collections import Counter,defaultdict

def main():
 guard();target=OUT/'actual_triangle_source_mapping_review.json';assert not target.exists();c=read(CFG);source=ROOT/c['files'][2]['path'];assert streamsha(source)==c['files'][2]['sha256'];S=parse(source);X={int(r[:10]):[float(v) for v in r[10:].split()] for r in S['/NODE']};elements={}
 for key,rows in S.items():
  if key.startswith(('/SHELL/','/SH3N/')):
   for row in rows:
    if row.strip():v=[int(x) for x in row.split()];assert v[0] not in elements;elements[v[0]]={'keyword':key,'nodes':v[1:]}
 j=read(OUT/'WHOLE_CURRENT_TRIANGLE_BLOCK_TRACE/trace_result.json');f=j['fault'];b=f['actual_assembly_block'];assert j['Engine_exit_code']==3 and b['element_kind']=='SH3N' and b['NEL']==128 and b['all_assembly_pairs_belong_to_current_element'];nodes={int(k):v for k,v in b['nodes'].items()};maxerror=0.;mapped=[];group_counts=Counter()
 groups={int(k.split('/')[-1]):[int(v) for row in rows[1:] for v in row.split()] for k,rows in S.items() if k.startswith('/GRNOD/NODE/')};roles=defaultdict(list)
 for key,rows in S.items():
  if key.startswith('/RBE2/'):
   v=rows[1].split();mainnode=int(v[0]);roles[mainnode].append({'constraint':key,'role':'main','title':rows[0],'mask':v[1:3]})
   for n in groups[int(v[4])]:roles[n].append({'constraint':key,'role':'secondary','main':mainnode,'mask':v[1:3]})
 for e in b['elements']:
  original=elements[e['original_element_id']];assert original['keyword'].startswith('/SH3N/') and original['nodes']==e['original_nodes'];part=int(original['keyword'].split('/')[-1]);partdef=S['/PART/'+str(part)];prop,mat,_=[int(v) for v in partdef[1].split()];group_counts[(original['keyword'],prop,mat)]+=1
  for n in e['internal_nodes']:
   label=nodes[n]['original_label'];assert label in X;error=max(abs(a-v) for a,v in zip(nodes[n]['coordinates_mm'],X[label]));maxerror=max(maxerror,error)
  mapped.append({'native_slot':e['slot_1based'],'original_element':e['original_element_id'],'source':original,'part_title':partdef[0],'property_ID':prop,'material_ID':mat})
 assert maxerror<=c['acceptance']['maximum_coordinate_error_mm']
 missing=[]
 for row in f['sparse_rows']:
  if not any(not q['column_present'] for q in row['sparse_search']):continue
  labels=[nodes[n]['original_label'] for n in row['internal_nodes']];missing.append({'native_slot':row['element_in_block_1based'],'original_element':b['elements'][row['element_in_block_1based']-1]['original_element_id'],'internal_nodes':row['internal_nodes'],'original_nodes':labels,'NDOF':row['NDOF'],'missing_rows':sum(not q['column_present'] for q in row['sparse_search']),'roles':[roles[n] for n in labels]})
 assert len(missing)==24 and sum(r['missing_rows'] for r in missing)==144
 result={'created_utc':now(),'pass_actual_block_mapping':True,'trace_sha256':streamsha(OUT/'WHOLE_CURRENT_TRIANGLE_BLOCK_TRACE/trace_result.json'),'actual_block_kind':'SH3N','actual_elements':128,'actual_nodes':len(nodes),'maximum_coordinate_error_mm':maxerror,'current_NI_NJ_cross_verified':True,'parts':[{'keyword':k,'property_ID':p,'material_ID':m,'elements':v} for (k,p,m),v in group_counts.items()],'mapped_elements':mapped,'missing_pairs':missing,'fault_source_labels_are_checked_not_assumed':True,'stale_quadrilateral_context_not_used':True,'grouped_candidate_still_rejected':True,'whole_impact_qualified':False,'new_whole_duration_credit_s':0}
 dump(target,result);print({'actual_block_mapping_pass':True,'kind':'SH3N','elements':128,'nodes':len(nodes),'max_error_mm':maxerror,'parts':result['parts'],'first_missing_pairs':missing[:2]},flush=True)

if __name__=='__main__':main()
