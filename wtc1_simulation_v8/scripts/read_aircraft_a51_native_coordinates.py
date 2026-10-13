"""Read only the cached v44 native coordinate block, preserving its float32 precision."""
from probe_aircraft_a51 import *
import struct,ast
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a51_native_coordinate_reader_predeclaration.json'

def raw_native_coordinates(p,Q):
 guard();c=read(DEC);assert streamsha(p)==c['native_animation_sha256'];b=p.read_bytes();magic,tt=struct.unpack_from('>if',b,0);assert magic==21548 and tt==0
 assert b[8:89].startswith(b'Time=') and b[89:170].startswith(b'ModAnim') and b[170:251].startswith(b'Radioss Run=')
 flags=struct.unpack_from('>10i',b,251);counts=struct.unpack_from('>8i',b,291);nn=counts[0];nskew=counts[7]
 assert nn==48171 and nn==len(Q['NODE_ID']) and flags[8]==0 and flags[9]==0
 assert nskew==4680,'Only the declared cached v44 file is supported'
 offset=323+nskew*6*2;end=offset+nn*3*4;assert end<=len(b)
 X=np.frombuffer(b,dtype='>f4',count=nn*3,offset=offset).astype(float).reshape(-1,3);assert np.isfinite(X).all()
 q=Q['points'].reshape(-1,3);difference=float(abs(X-q).max())
 dump(OUT/'native_coordinate_reader_review.json',{'created_utc':now(),'magic':magic,'version':44,'time_ms':tt,'flags':list(flags),'counts':list(counts),'coordinate_offset_bytes':offset,'coordinate_end_bytes':end,'native_array_type':'big-endian IEEEfloat32, three coordinates in increasing internal node order','ASCII_vs_native_coordinate_max_difference_mm':difference,'original_ASCII_coordinate_gate_failed_and_retained':True,'coordinate_tolerance_mm_unchanged':read(CFG)['acceptance']['coordinate_export_tolerance_mm'],'native_input_unchanged':True,'native_solver_replayed':False,'reader_scope':'This one pinned v44 mono-domain cached frame only; not a general animation reader.'})
 return X

def prepare():
 guard();assert not DEC.exists()
 dump(OUT/'retained_ASCII_coordinate_reader_failure.json',{'created_utc':now(),'original_script':rel(ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a51.py'),'original_script_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a51.py'),'failed_line':72,'maximum_ASCII_coordinate_error_mm':.049999999999272404,'declared_threshold_mm':.003,'pass':False,'original_script_and_failed_output_preserved':True,'new_native_Engine_executions':0,'external_converter_repository_GET_404_does_not_block_cached_writer_source':True})
 source=[]
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for p in ['engine/source/output/anim/generate/genani.F','engine/source/output/anim/generate/aniskew.F','common_source/tools/input_output/write_routines.c']:
   b=tar.extractfile(members[p]).read();t=b.decode();source.append({'path':p,'sha256':hashlib.sha256(b).hexdigest(),'raw_source_redistributed':False})
   if p.endswith('genani.F'):assert 'MAGIC = 21548' in t and 'CALL WRITE_I_C(NSKEWA,1)' in t
   elif p.endswith('aniskew.F'):assert 'CALL WRITE_S_C(ISK,6)' in t and 'CALL WRITE_S_C(WA,LEN)' in t
   else:assert 'for(i=2;i<4;i++) write_buffer' in t
 native=ROOT/read(CFG)['files']['native_animation']['path'];dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A51','seed':1102076,'random_draws':0,'native_animation':rel(native),'native_animation_sha256':streamsha(native),'format':'Pinned mono-domain animation44 only: magic/time8bytes,3titles81bytes,10flagints40bytes,8countints32bytes,skews6big-endianint16each,then3float32coordinates pernode.','source':source,'original_ASCII_failure_retained':True,'unchanged_acceptance_mm':.003,'native_node_labels':'Use intact integer NODE_ID array from cached converter; raw coordinate validation required for every label.','software_runtime_or_physics_changed':False})
 src=ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a51.py';dst=ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a51_native_precision.py';assert not dst.exists();s=src.read_text();s=s.replace('import numpy as np','import numpy as np\nfrom read_aircraft_a51_native_coordinates import raw_native_coordinates')
 old="coords=Q['points'].reshape(-1,3);a=c['acceptance']";assert s.count(old)==1;s=s.replace(old,"coords=raw_native_coordinates(ROOT/c['files']['native_animation']['path'],Q);a=c['acceptance']")
 s=s.replace("OUT/'source_order_and_graph_review.json'","OUT/'source_order_and_graph_review_native_precision.json'");ast.parse(s);dst.write_text(s,encoding='utf8')
 dump(OUT/'native_precision_reader_derivation.json',{'created_utc':now(),'original_script':rel(src),'original_sha256':streamsha(src),'derived_script':rel(dst),'derived_sha256':streamsha(dst),'changes':'Only own cached-coordinate reader precision and distinct source review filename. No acceptance threshold, node roles, scientific input, solver or runtime changed.','new_Engine_executions':0})
 print({'native_precision_reader_predeclared':True,'original_0p003mm_threshold_preserved':True},flush=True)

if __name__=='__main__':prepare()
