"""Verify adjacency routing at native call sites before proposing any software change."""
from probe_aircraft_a53 import *
DEC=ROOT/'wtc1_simulation_v8/data/aircraft_a53_routing_predeclaration.json'

def declare():
 guard();assert not DEC.exists();assert read(OUT/'actual_triangle_source_mapping_review.json')['pass_actual_block_mapping'];source='engine/source/implicit/ind_glob_k.F'
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  m=next(x for x in tar if x.name.endswith('/'+source));b=tar.extractfile(m).read();lines=b.decode().splitlines();i=next(i for i,s in enumerate(lines) if 'SUBROUTINE IND_KINE_K(' in s);parts=[lines[i].split('(',1)[1]];j=i+1
  while ')' not in parts[-1]:parts.append(lines[j][6:].strip());j+=1
  names=[v.strip() for v in ''.join(parts).split(')',1)[0].split(',')];indices={k:names.index(k)+1 for k in ['ITAB','NNMAX','NKMAX','NKINE','INK','NROWK','ICOK','ICOKM','INLOC']};assert indices=={'ITAB':3,'NNMAX':21,'NKMAX':24,'NKINE':22,'INK':30,'NROWK':25,'ICOK':26,'ICOKM':27,'INLOC':23}
 p=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-n',bridge.linux(BINARY)],capture_output=True,timeout=30);assert p.returncode==0;lines=p.stdout.decode().splitlines();offsets={s:int(next(l.split()[0] for l in lines if l.endswith(' '+s)),16) for s in ['ind_kine_k_','reorder_a_']}
 dump(DEC,{'created_utc':now(),'iteration':'AIRCRAFT-A53','seed':1102078,'random_draws':0,'source':{'path':source,'sha256':hashlib.sha256(b).hexdigest(),'raw_source_redistributed':False},'arguments':indices,'IND_KINE_K_offset':offsets['ind_kine_k_'],'REORDER_A_offset':offsets['reorder_a_'],'hypothesis':'TYPE2 writes appear to use ICOK(1,row) even when the row is in the main region that uses ICOKM(1,row-INK) with a different stride. Verify actual pointer destinations and dimensions; do not patch or infer all faults from text alone.','expected_source_layout':'IND_GLOB_K mono-domain branch uses ordinary rows<=INK with NNMAX, main rows>INK with NKMAX; RBE2/RBE3 code selects those buffers explicitly.','observation_bound':{'maximum_REORDER_calls':512,'maximum_wrong_destinations':20},'CPU_threads':1,'GPU':False,'per_process_cap_s':180,'expected_s':20,'software_or_mechanical_data_change':False,'new_physical_duration_credit_s':0});print('Native routing observation declared; no software patch.',flush=True)

def run():
 guard();c=read(CFG);extra=read(DEC);d=OUT/'WHOLE_GRAPH_ROW_ROUTING_TRACE';assert not d.exists();d.mkdir()
 for r in c['files'][:2]:p=ROOT/r['path'];assert streamsha(p)==r['sha256'];shutil.copy2(p,d/p.name)
 script=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a53_routing_linux.py';config=d/'instrumentation_config.json';dump(config,{'binary':bridge.linux(BINARY),'binary_sha256':streamsha(BINARY),'directory':bridge.linux(d),'Engine_card':c['name']+'_0001.rad','maximum_nodes':c['maximum_nodes'],**{k:extra[k] for k in ['arguments','IND_KINE_K_offset','REORDER_A_offset']}});q=lambda p:shlex.quote(bridge.linux(p));launch=d/'trace.launch.sh';launch.write_text('set -eu\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexec python3 '+q(script)+' '+q(config)+'\n',encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(launch)];start=time.perf_counter();p=subprocess.run(cmd,capture_output=True,timeout=195);(d/'trace.launcher.log').write_bytes(p.stdout+p.stderr);dump(d/'trace.launcher.execution.json',{'created_utc':now(),'argv':cmd,'parent_exit':p.returncode,'wall_s':time.perf_counter()-start,'CPU_threads':1,'GPU':False,'cap_s':180,'script_sha256':streamsha(script)});print({'routing_trace_saved':(d/'routing_trace_result.json').exists(),'parent_exit':p.returncode},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
