"""Restrict surface membership parsing to actual shell/solid connectivity; retain the R2 attempt."""
from probe_aircraft_a51 import *
import ast
scripts=ROOT/'wtc1_simulation_v8/scripts';src=scripts/'probe_aircraft_a51_native_precision_r2.py';dst=scripts/'probe_aircraft_a51_native_precision_r3.py'
helper=scripts/'read_aircraft_a51_native_coordinates_r2.py';h3=scripts/'read_aircraft_a51_native_coordinates_r3.py';assert not dst.exists() and not h3.exists()
s=src.read_text();old="('/SHELL/','/SH3N/','/BRICK/','/BEAM/','/TRUSS/')";assert s.count(old)==1
s=s.replace(old,"('/SHELL/','/SH3N/','/BRICK/')")
s=s.replace('from read_aircraft_a51_native_coordinates_r2 import','from read_aircraft_a51_native_coordinates_r3 import').replace('source_order_and_graph_review_native_precision_r2.json','source_order_and_graph_review_native_precision_r3.json').replace('full_native_node_order_mapping.json','full_native_node_order_mapping_r3.json')
h=helper.read_text().replace('native_coordinate_reader_review_r2.json','native_coordinate_reader_review_r3.json');ast.parse(s);ast.parse(h);dst.write_text(s,encoding='utf8');h3.write_text(h,encoding='utf8')
dump(OUT/'native_precision_r3_derivation.json',{'created_utc':now(),'original':rel(src),'original_sha256':streamsha(src),'derived':rel(dst),'derived_sha256':streamsha(dst),'helper':rel(h3),'helper_sha256':streamsha(h3),'retained_failure':'R2 mapped all48171nodes and302direct captures, then tried to parse real-valued beam direction cosines as node IDs. Surface membership requires shell/solid connectivity only.','scope_correction':'Exclude beam/truss orientation records from surface-node membership; actual declared main surfaces contain shells/solids. No scientific input or criteria changed.','before_analysis':True,'new_native_solver_executions':0})
print('Separate surface-membership reader R3 prepared; R2 mapping and failure retained.',flush=True)
