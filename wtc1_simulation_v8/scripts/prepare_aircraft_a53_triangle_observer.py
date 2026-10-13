"""Add ASSEM_C3 observation in separate files after the direct-C4 context proved stale."""
from probe_aircraft_a53 import *
import ast

def prepare():
 guard();dec=ROOT/'wtc1_simulation_v8/data/aircraft_a53_triangle_predeclaration.json';assert not dec.exists();old=read(OUT/'WHOLE_ACTUAL_ASSEMBLY_BLOCK_TRACE/trace_result.json');assert old['Engine_exit_code']==3 and old['ASSEM_C4_calls']==263 and old['assembly_calls']==1579 and 'actual_assembly_block' not in old['fault']
 paths=['engine/source/implicit/assem_c3.F','common_source/modules/elements/element_mod.F90'];sources=[]
 with tarfile.open(CAND/'source.tar.gz','r:gz') as tar:
  members={m.name.split('/',1)[1]:m for m in tar if '/' in m.name}
  for path in paths:
   b=tar.extractfile(members[path]).read();sources.append({'path':path,'sha256':hashlib.sha256(b).hexdigest(),'raw_source_redistributed':False})
   if path.endswith('assem_c3.F'):assert 'IXTG(NIXTG,*)' in b.decode() and 'CALL ASSEMC_KIJ' in b.decode()
   else:assert 'nixtg = 6' in b.decode().lower()
 p=subprocess.run(['wsl.exe','-d','Ubuntu','--','nm','-n',bridge.linux(BINARY)],capture_output=True,timeout=30);assert p.returncode==0;offset=int(next(l.split()[0] for l in p.stdout.decode().splitlines() if l.endswith(' assem_c3_')),16)
 src=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a53_linux.py';dst=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a53_triangle_linux.py';assert not dst.exists();s=src.read_text()
 oldfunc="""def assembly_context(pid,r):
 p=arg(pid,r,1);n=i32(pid,arg(pid,r,2));assert 0<n<=128
 raw=struct.unpack('<'+'i'*(7*n),memory(pid,p,7*n*4))
 return {'NEL':n,'elements':[{'slot_1based':i+1,'raw_IXC':list(raw[7*i:7*i+7]),'material_index':raw[7*i],'internal_nodes':list(raw[7*i+1:7*i+5]),'property_index':raw[7*i+5],'original_element_id':raw[7*i+6]} for i in range(n)]}
"""
 newfunc="""def assembly_context(pid,r,triangle=False):
 p=arg(pid,r,1);n=i32(pid,arg(pid,r,2));assert 0<n<=128;w=6 if triangle else 7
 raw=struct.unpack('<'+'i'*(w*n),memory(pid,p,w*n*4))
 return {'NEL':n,'element_kind':'SH3N' if triangle else 'SHELL','connectivity_width':w,'elements':[{'slot_1based':i+1,'raw_connectivity':list(raw[w*i:w*i+w]),'material_index':raw[w*i],'internal_nodes':list(raw[w*i+1:w*i+w-2]),'property_index':raw[w*i+w-2],'original_element_id':raw[w*i+w-1]} for i in range(n)]}
"""
 assert s.count(oldfunc)==1;s=s.replace(oldfunc,newfunc).replace("'IMP_CHKM_offset']]","'IMP_CHKM_offset','ASSEM_C3_offset']]")
 s=s.replace('ptrace(6,pid,904,21);count=0;blockcount=0;globalcount=0;','ptrace(6,pid,904,85);count=0;blockcount=0;trianglecount=0;globalcount=0;')
 marker="   elif r.rip==targets[2]:globalcount+=1;globals_={'ITAB':arg(pid,r,c['ITAB_argument_1based']),'X':arg(pid,r,c['X_argument_1based'])}"
 assert s.count(marker)==1;s=s.replace(marker,marker+"\n   elif r.rip==targets[3]:trianglecount+=1;context=assembly_context(pid,r,True)")
 s=s.replace("'ASSEM_C4_calls':blockcount,'IMP_CHKM_calls'","'ASSEM_C4_calls':blockcount,'ASSEM_C3_calls':trianglecount,'IMP_CHKM_calls'")
 s=s.replace("return {'NEL':context['NEL'],'elements'","return {'NEL':context['NEL'],'element_kind':context['element_kind'],'connectivity_width':context['connectivity_width'],'elements'")
 s=s.replace("fault['actual_block_read_error']=str(exc)","fault['actual_block_read_error']=type(exc).__name__+': '+str(exc)").replace('three hardware breakpoints','four hardware breakpoints')
 ast.parse(s);dst.write_text(s,encoding='utf8')
 dump(dec,{'created_utc':now(),'iteration':'AIRCRAFT-A53','seed':1102078,'random_draws':0,'reason':'C4last context differs from NEL128 and its263calls end after1578off-diagonal calls; next assembly may be C3. Observe that real caller, not infer its physical part.','source':sources,'ASSEM_C3_offset':offset,'IXTG_width':6,'IXTG_nodes_rows':[2,3,4],'IXTG_user_element_ID_row':6,'original_observer':rel(src),'original_sha256':streamsha(src),'derived_observer':rel(dst),'derived_sha256':streamsha(dst),'original_stale_context_attempt_retained':True,'acceptance_criteria_unchanged':True,'per_process_cap_s':180,'expected_s':20,'software_or_physical_data_patched':False,'new_physical_duration_credit_s':0})
 print({'triangle_observation_predeclared':True,'ASSEMC3_offset':offset,'four_hardware_slots':True},flush=True)

def run():
 guard();c=read(CFG);extra=read(ROOT/'wtc1_simulation_v8/data/aircraft_a53_triangle_predeclaration.json');script=ROOT/extra['derived_observer'];assert streamsha(script)==extra['derived_sha256'];d=OUT/'WHOLE_CURRENT_TRIANGLE_BLOCK_TRACE';assert not d.exists();d.mkdir()
 for r in c['files'][:2]:p=ROOT/r['path'];assert streamsha(p)==r['sha256'];shutil.copy2(p,d/p.name)
 config=d/'instrumentation_config.json';dump(config,{'binary':bridge.linux(BINARY),'binary_sha256':streamsha(BINARY),'directory':bridge.linux(d),'Engine_card':c['name']+'_0001.rad',**{k:c[k] for k in ['function_offset','ASSEM_C4_offset','IMP_CHKM_offset','ITAB_argument_1based','X_argument_1based','pattern_symbol_offset','maximum_nodes']},'ASSEM_C3_offset':extra['ASSEM_C3_offset']});q=lambda p:shlex.quote(bridge.linux(p));launch=d/'trace.launch.sh';launch.write_text('set -eu\nexport OMP_NUM_THREADS=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1\nexport OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexec python3 '+q(script)+' '+q(config)+'\n',encoding='utf8',newline='\n');cmd=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',bridge.linux(launch)];t=time.perf_counter();p=subprocess.run(cmd,capture_output=True,timeout=195);(d/'trace.launcher.log').write_bytes(p.stdout+p.stderr);dump(d/'trace.launcher.execution.json',{'created_utc':now(),'argv':cmd,'parent_exit':p.returncode,'wall_s':time.perf_counter()-t,'CPU_threads':1,'GPU':False,'cap_s':180,'script_sha256':streamsha(script),'immutable_helper_sha256':streamsha(ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a48_linux.py')});print({'triangle_trace_saved':(d/'trace_result.json').exists(),'parent_exit':p.returncode},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);globals()[p.parse_args().action]()
