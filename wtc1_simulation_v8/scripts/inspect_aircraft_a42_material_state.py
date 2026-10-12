"""Read-only native MATPARAM header audit and paired Windows startup diagnostic."""
from normalize_aircraft_a42 import *
import struct, subprocess, time

def inspect():
 guard();p=OUT/'material_restart_layout_review.json';assert not p.exists();deck=SOURCE_DECK.read_text();expected=sorted((int(m[1]),int(m[0])) for m in re.findall(r'^/MAT/LAW(\d+)/(\d+)',deck,re.M));expected.append((0,0));rows=[]
 for f in [SOURCE/'A37_WHOLE_CHECK_0000_0001.rst',OUT/'WHOLE_CONST_TABLES_W1'/f'{NAME}_0000_0001.rst']:
  b=f.read_bytes();pattern=struct.pack('>ii',117,117);hits=[];pos=0
  while (pos:=b.find(pattern,pos))>=0:
   start=pos-100*(len(expected)-2)
   if start>=0:
    headers=[list(struct.unpack_from('>25i',b,start+100*i)) for i in range(len(expected))]
    if [(h[1],h[0]) for h in headers]==expected:hits.append({'offset':start,'headers':headers})
   pos+=1
  assert len(hits)==1,'MATPARAM record must be uniquely validated by all six material IDs/laws and synthetic default record'
  hit=hits[0];h=next(x for x in hit['headers'] if x[:2]==[117,117]);assert h[2:6]==[0,0,0,0]
  rows.append({'path':rel(f),'sha256':streamsha(f),'MATPARAM_header_block_offset':hit['offset'],'record_stride_bytes':100,'all_material_ids_and_laws_verified':True,'all_headers_25_BE_i32':hit['headers'],'LAW117':{'NUPARAM':h[2],'NIPARAM':h[3],'NFUNC':h[4],'NTABLE':h[5]}})
 sources=['engine/source/output/restart/read_matparam.F','starter/source/materials/mat/write_matparam.F','starter/source/materials/mat/mat117/hm_read_mat117.F90','engine/source/materials/mat/mat117/sigeps117.F90'];dump(p,{'created_utc':now(),'pass':True,'inspection_read_only':True,'source_commit':build.PIN,'records':rows,'source_files':[{'path':rel(build.CAND/'source'/x),'sha256':streamsha(build.CAND/'source'/x)} for x in sources],'pinned_new_Starter_LAW117_expected':{'NUPARAM':14,'NIPARAM':6,'NTABLE':2},'pinned_Engine_behavior':'READ_MATPARAM allocates table only if NTABLE>0; SIGEPS117 unconditionally accesses table(1), table(2) and fourteen user parameters.','conclusion':'Windows prepared LAW117 uses legacy parameter representation; it supplies no tables/user parameters expected by this pinned Linux Engine. Constant function cards did not change this representation. Initial-state interoperability fails for LAW117.','limits':['This is a validated material header parse, not a complete restart parser.','Zero counts plus source and abort stack localize a version/representation incompatibility; other whole-model compatibility deficits remain.','No checkpoint editing, source patch, binary replacement or physical parameter change.'],'whole_impact_qualified':False})
 print({'LAW117_serialized_counts':[r['LAW117'] for r in rows],'new_Engine_expected':[14,6,2]},flush=True)

def declare_windows():
 guard();p=OUT/'paired_windows_predeclaration.json';assert not p.exists();src=OUT/'WHOLE_CONST_TABLES_W1';dump(p,{'created_utc':now(),'before_native':True,'seed':1102067,'random_draws':0,'purpose':'Paired explicit startup from identical freshly prepared constant-table whole initial state with the already installed Windows Engine. Separates cross-version interoperability failure from invalid input. No whole physical extension/qualification.','source_initial_state':rel(src/f'{NAME}_0000_0001.rst'),'source_initial_sha256':streamsha(src/f'{NAME}_0000_0001.rst'),'source_engine_card_sha256':streamsha(src/f'{NAME}_0001.rad'),'binary_sha256':streamsha(RUNTIME/'engine_win64.exe'),'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'requested_end_ms':1e-5,'old_successful_solver_replay':False,'software_install_or_build':False})

def windows():
 guard();dec=read(OUT/'paired_windows_predeclaration.json');assert dec['before_native'];src=OUT/'WHOLE_CONST_TABLES_W1';d=OUT/'WHOLE_CONST_TABLES_WINDOWS';assert not d.exists();d.mkdir()
 for name in [f'{NAME}_0000_0001.rst',f'{NAME}_0001.rad','generation.json']:shutil.copy2(src/name,d/name)
 assert streamsha(d/f'{NAME}_0000_0001.rst')==dec['source_initial_sha256'];en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1');ok=native37.win_execute(RUNTIME/'engine_win64.exe',['-i',f'{NAME}_0001.rad','-nt','1'],d,'engine.log',180,en);log=(d/'engine.log').read_text(errors='replace');complete=ok and 'NORMAL TERMINATION' in log;dump(d/'review.json',{'created_utc':now(),'native_completed':complete,'same_initial_state_hash':streamsha(d/f'{NAME}_0000_0001.rst')==dec['source_initial_sha256'],'same_engine_card_hash':streamsha(d/f'{NAME}_0001.rad')==dec['source_engine_card_sha256'],'whole_impact_qualified':False,'objective1_duration_credit_s':0});print({'paired_Windows_explicit_completed':complete},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','declare_windows','windows']);globals()[p.parse_args().action]()
