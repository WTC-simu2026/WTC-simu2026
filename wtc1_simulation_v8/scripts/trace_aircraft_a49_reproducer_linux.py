"""Observe shell connectivity/coordinates and sparse fault in the same unmodified Engine child."""
from trace_aircraft_a48_linux import *

def shell_arguments(pid,r):
 names=['JFT','JLT','NFT','NPT','MTN','ITHK','NCYCLE','ISTRAIN','IPLA','PM','GEO','IXC','ELBUF_STR','BUFMAT','OFFSET','INDXOF','ETAG','IDDL','NDOF','K_DIAG','K_LT','IADK','JDIK','IHBE','THKE','ISMSTR','X','IKGEO','IPM','IGEO','IEXPAN','IPARG','ISUBSTACK','STACK','DRAPE_SH4N','INDX_DRAPE','SEDRAPE','NUMEL_DRAPE'];values=[r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9]+[u64(pid,r.rsp+8*(i+1)) for i in range(len(names)-6)];p=dict(zip(names,values));return {'pointers':p,'scalars':{k:i32(pid,p[k]) for k in ['JFT','JLT','NFT','NPT','MTN','ITHK','NCYCLE','ISMSTR']},'caller_return_address':hex(u64(pid,r.rsp))}

def shell_block(pid,context,assembly,max_nodes):
 p=context['pointers'];a=context['scalars'];assert a['JFT']==1 and 0<a['JLT']<=128;nel=a['JLT'];raw=struct.unpack('<'+'i'*(7*nel),memory(pid,p['IXC'],4*7*nel));items=[];points={}
 for j in range(nel):
  row=list(raw[7*j:7*j+7]);nodes=row[1:5];assert all(0<n<=max_nodes for n in nodes)
  for n in nodes:
   if n not in points:points[n]=list(struct.unpack('<ddd',memory(pid,p['X']+24*(n-1),24)))
  items.append({'element_in_block_1based':j+1,'native_material_index':row[0],'native_node_indices':nodes,'native_property_index':row[5],'user_element_id':row[6],'IXC_raw':row})
 return {'scalars':a,'IXC_dimension':7,'elements':items,'node_coordinates_mm':{str(k):v for k,v in points.items()},'same_NEL_as_assembly':nel==assembly['NEL']}

def main():
 c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256'];d=Path(c['directory']);os.chdir(d);out=d/'trace_result.json';assert not out.exists();started=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
  except BaseException:os._exit(77)
 _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status);maps=Path(f'/proc/{pid}/maps').read_text();lines=[l.split() for l in maps.splitlines() if l.endswith(str(binary))];base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in lines);target=base+c['function_offset'];shelltarget=base+c['shell_function_offset'];ptrace(6,pid,848,target);ptrace(6,pid,856,shelltarget);ptrace(6,pid,904,5);count=0;shellcount=0;args=None;context=None;fault=None;events=0;deliver=0;missing_events=[]
 while True:
  ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
  if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
  sig=os.WSTOPSIG(status);deliver=sig;events+=1
  if sig==signal.SIGTRAP:
   r=registers(pid);deliver=0
   if r.rip==target:
    count+=1;args=capture_arguments(pid,r);pattern=i32(pid,base+c['pattern_symbol_offset']);sr=sparse_rows(pid,args,pattern,c['maximum_nodes']);bad=[x for x in sr if any(not y['column_present'] for y in x['sparse_search'])]
    if bad:missing_events.append({'call':count,'NEL':args['NEL'],'ND':args['ND'],'pattern':pattern,'missing_pairs':bad})
   elif r.rip==shelltarget:shellcount+=1;context=shell_arguments(pid,r)
   if count>10000 or shellcount>2000:os.kill(pid,signal.SIGKILL);raise RuntimeError('Trace call bound reached')
  elif sig==signal.SIGSEGV and fault is None:
   r=registers(pid);info=(ctypes.c_byte*128)();ptrace(0x4202,pid,0,ctypes.addressof(info));fault_address=struct.unpack('<Q',bytes(info)[16:24])[0];pattern=i32(pid,base+c['pattern_symbol_offset']);fault={'signal':sig,'signal_code':struct.unpack('<i',bytes(info)[8:12])[0],'function_relative_fault_hex':hex(r.rip-target),'fault_address':hex(fault_address),'registers':{n:hex(getattr(r,n)) for n in REGN},'native_IKPAT':pattern,'native_args':{**args,'pointers':{k:hex(v) for k,v in args['pointers'].items()}} if args else None}
   if args:
    fault['sparse_rows']=sparse_rows(pid,args,pattern,c['maximum_nodes']);fault['destination_KLT_index_from_RAX_1based']=(r.rax-args['pointers']['K_LT'])//8+1
   if context and args:
    try:fault['native_shell_block']=shell_block(pid,context,args,c['maximum_nodes'])
    except BaseException as exc:fault['shell_read_error']=str(exc)
   ptrace(6,pid,904,0)
 result={'created_epoch':time.time(),'wall_s':time.monotonic()-started,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'fault':fault,'assembly_call_count':count,'shell_call_count':shellcount,'trace_event_count':events,'entry_missing_events':missing_events,'binary_sha256':c['binary_sha256'],'instrumentation':'Owned child, two hardware instruction breakpoints; read registers and bounded native matrix/IXC/X arrays. No physical-data, instruction, binary or restart writes; signal forwarded unchanged.','new_installation_or_compilation':False,'whole_impact_qualified':False};out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'trace_complete':True,'fault_captured':fault is not None,'shell_block_captured':bool(fault and 'native_shell_block' in fault),'assembly_calls':count,'shell_calls':shellcount,'Engine_exit_code':result['Engine_exit_code']}),flush=True)

if __name__=='__main__':main()
