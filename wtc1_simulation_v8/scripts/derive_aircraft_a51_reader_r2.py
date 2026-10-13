"""Correct the metadata entry schema in a separate reader, preserving both earlier attempts."""
from probe_aircraft_a51 import *
import ast
scripts=ROOT/'wtc1_simulation_v8/scripts'
src=scripts/'probe_aircraft_a51_native_precision.py';dst=scripts/'probe_aircraft_a51_native_precision_r2.py'
helper=scripts/'read_aircraft_a51_native_coordinates.py';h2=scripts/'read_aircraft_a51_native_coordinates_r2.py'
assert not dst.exists() and not h2.exists()
s=src.read_text();assert s.count("entry['native']['native_node_indices']")==1 and s.count("entry['source']['nodes']")==1
s=s.replace("entry['native']['native_node_indices']","entry['native_element']['native_node_indices']").replace("entry['source']['nodes']","entry['source_nodes']")
s=s.replace('from read_aircraft_a51_native_coordinates import','from read_aircraft_a51_native_coordinates_r2 import')
s=s.replace('source_order_and_graph_review_native_precision.json','source_order_and_graph_review_native_precision_r2.json')
h=helper.read_text().replace('native_coordinate_reader_review.json','native_coordinate_reader_review_r2.json');ast.parse(s);ast.parse(h)
dst.write_text(s,encoding='utf8');h2.write_text(h,encoding='utf8')
dump(OUT/'native_precision_r2_derivation.json',{'created_utc':now(),'original':rel(src),'original_sha256':streamsha(src),'derived':rel(dst),'derived_sha256':streamsha(dst),'helper_derived':rel(h2),'helper_sha256':streamsha(h2),'retained_failure':'First native-precision attempt read the standard-trace schema instead of the source-mapping schema: native_element/source_nodes are the actual keys.','changes':'Two metadata keys and distinct own output names only. Criteria, native coordinates, source input and solve unchanged.','before_analysis':True,'new_native_solver_executions':0,'retained_pre_derivation_command_syntax_error':True})
print('Separate reader R2 prepared; original readers retained.',flush=True)
