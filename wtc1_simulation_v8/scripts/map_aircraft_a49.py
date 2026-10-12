"""Validate actual user element IDs and coordinates, then link mixed DOF to source attachments."""
from probe_aircraft_a49 import *
import math

def map_source():
 guard();r=read(OUT/'WHOLE_NATIVE_ELEMENT_MAP/trace_result.json');f=r['fault'];b=f['native_shell_block'];assert b['same_NEL_as_assembly'];sec=sections();nodes={int(x[:10]):[float(v) for v in x[10:].split()] for x in sec['/NODE']};elements={}
 for key,rows in sec.items():
  if key.startswith(('/SHELL/','/SH3N/','/BRICK/')):
   for line in rows:
    v=list(map(int,line.split()));assert v[0] not in elements;elements[v[0]]={'keyword':key,'nodes':v[1:]}
 groups={int(k.split('/')[-1]):set(int(v) for line in rows[1:] for v in line.split()) for k,rows in sec.items() if k.startswith('/GRNOD/NODE/')};RBE=[]
 for key,rows in sec.items():
  if key.startswith('/RBE2/'):
   v=rows[1].split();RBE.append({'keyword':key,'title':rows[0],'reference_node':int(v[0]),'translation_mask':v[1],'rotation_mask':v[2],'group':int(v[4]),'formulation':int(v[5])})
 missing={x['element_in_block_1based']:x for x in f['sparse_rows'] if any(not z['column_present'] for z in x['sparse_search'])};rows=[];mapping={};maxerr=0
 for e in b['elements']:
  source=elements[e['user_element_id']];assert source['keyword'].startswith('/SHELL/') and len(source['nodes'])==4;corner=[]
  for internal,original in zip(e['native_node_indices'],source['nodes']):
   x=b['node_coordinates_mm'][str(internal)];error=max(abs(a-v) for a,v in zip(x,nodes[original]));maxerr=max(maxerr,error);assert error<=read(CFG)['source_coordinate_tolerance_mm'];assert internal not in mapping or mapping[internal]==original;mapping[internal]=original;links=[z for z in RBE if original in groups[z['group']]];corner.append({'internal_index':internal,'original_node_id':original,'native_coordinates_mm':x,'source_coordinates_mm':nodes[original],'coordinate_error_mm':error,'secondary_RBE2':links})
  part=source['keyword'].split('/')[-1];entry={'native_element':e,'source_keyword':source['keyword'],'source_part':sec['/PART/'+part],'source_nodes':source['nodes'],'corners':corner}
  if e['element_in_block_1based'] in missing:
   q=missing[e['element_in_block_1based']];entry['missing_sparse_pair']={'internal_nodes':q['internal_nodes'],'original_nodes':[mapping[n] for n in q['internal_nodes']],'NDOF':q['NDOF'],'IDDL':q['IDDL'],'missing_rows':sum(not z['column_present'] for z in q['sparse_search'])}
  rows.append(entry)
 result={'created_utc':now(),'pass':True,'trace_sha256':streamsha(OUT/'WHOLE_NATIVE_ELEMENT_MAP/trace_result.json'),'mapped_elements':len(rows),'mapped_internal_nodes':len(mapping),'maximum_coordinate_error_mm':maxerr,'native_scalars':b['scalars'],'source_property_keyword':'/PROP/TYPE51/122','source_property':sec['/PROP/TYPE51/122'],'source_ply_property':sec['/PROP/TYPE19/41'],'source_material':sec['/MAT/LAW25/4'],'missing_pairs_mapped':len(missing),'first_mapped_missing':next(x for x in rows if 'missing_sparse_pair' in x),'all_entries':rows,'original_node_labels_not_equal_to_runtime_indices':any(k!=v for k,v in mapping.items()),'upstream_layer_count_vs_integration_count_not_assumed_equivalent':True,'full_physical_qualification':False};dest=OUT/'native_to_source_mapping_review.json';assert not dest.exists();dump(dest,result);print({k:result[k] for k in ['mapped_elements','mapped_internal_nodes','maximum_coordinate_error_mm','missing_pairs_mapped','original_node_labels_not_equal_to_runtime_indices']},flush=True);print({'first_source_element':result['first_mapped_missing']['native_element']['user_element_id'],'source_keyword':result['first_mapped_missing']['source_keyword'],'source_nodes':result['first_mapped_missing']['source_nodes'],'pair':result['first_mapped_missing']['missing_sparse_pair']},flush=True)

if __name__=='__main__':map_source()
