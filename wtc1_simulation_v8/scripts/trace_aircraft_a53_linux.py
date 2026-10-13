"""Read the actual ASSEM_C4 block and CHECK globals in our unmodified native Engine child."""
from trace_aircraft_a48_linux import *

def arg(pid,r,index):
 return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][index-1] if index<=6 else u64(pid,r.rsp+8*(index-6))

def assembly_context(pid,r):
 p=arg(pid,r,1);n=i32(pid,arg(pid,r,2));assert 0<n<=128
 raw=struct.unpack('<'+'i'*(7*n),memory(pid,p,7*n*4))
 return {'NEL':n,'elements':[{'slot_1based':i+1,'raw_IXC':list(raw[7*i:7*i+7]),'material_index':raw[7*i],'internal_nodes':list(raw[7*i+1:7*i+5]),'property_index':raw[7*i+5],'original_element_id':raw[7*i+6]} for i in range(n)]}

def fault_block(pid,context,args,globals_,nn):
 assert context and globals_ and context['NEL']==args['NEL'];p=globals_;elements=[];nodes={}
 for e in context['elements']:
  labels=[]
  for n in e['internal_nodes']:
   assert 0<n<=nn
   if n not in nodes:nodes[n]={'original_label':i32(pid,p['ITAB']+4*(n-1)),'coordinates_mm':list(struct.unpack('<ddd',memory(pid,p['X']+24*(n-1),24)))}
   labels.append(nodes[n]['original_label'])
  elements.append({**e,'original_nodes':labels})
 # Every current NI/NJ pair must come from the corresponding current IXC row.
 ni=struct.unpack('<'+'i'*args['NEL'],memory(pid,args['pointers']['NI'],4*args['NEL']));nj=struct.unpack('<'+'i'*args['NEL'],memory(pid,args['pointers']['NJ'],4*args['NEL']))
 checks=[a in e['internal_nodes'] and b in e['internal_nodes'] for a,b,e in zip(ni,nj,elements)]
 assert all(checks),'Last ASSEM_C4 block does not match the faulting NI/NJ arrays'
 return {'NEL':context['NEL'],'elements':elements,'nodes':{str(k):v for k,v in nodes.items()},'all_assembly_pairs_belong_to_current_element':True,'labels_from_CHECK_ITAB':True}

def main():
 c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256'];d=Path(c['directory']);os.chdir(d);output=d/'trace_result.json';assert not output.exists();start=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
  except BaseException:os._exit(77)
 _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status);maps=Path(f'/proc/{pid}/maps').read_text();lines=[l.split() for l in maps.splitlines() if l.endswith(str(binary))];base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in lines)
 targets=[base+c[k] for k in ['function_offset','ASSEM_C4_offset','IMP_CHKM_offset']]
 for i,t in enumerate(targets):ptrace(6,pid,848+8*i,t)
 ptrace(6,pid,904,21);count=0;blockcount=0;globalcount=0;context=None;globals_=None;args=None;fault=None;deliver=0
 while True:
  ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
  if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
  sig=os.WSTOPSIG(status);deliver=sig
  if sig==signal.SIGTRAP:
   r=registers(pid);deliver=0
   if r.rip==targets[0]:count+=1;args=capture_arguments(pid,r)
   elif r.rip==targets[1]:blockcount+=1;context=assembly_context(pid,r)
   elif r.rip==targets[2]:globalcount+=1;globals_={'ITAB':arg(pid,r,c['ITAB_argument_1based']),'X':arg(pid,r,c['X_argument_1based'])}
   if count>10000 or blockcount>2000 or globalcount>4:os.kill(pid,signal.SIGKILL);raise RuntimeError('Native observation count bound exceeded')
  elif sig==signal.SIGSEGV and fault is None:
   r=registers(pid);info=(ctypes.c_byte*128)();ptrace(0x4202,pid,0,ctypes.addressof(info));pattern=i32(pid,base+c['pattern_symbol_offset']);fault={'signal':sig,'signal_code':struct.unpack('<i',bytes(info)[8:12])[0],'fault_address':hex(struct.unpack('<Q',bytes(info)[16:24])[0]),'function_relative_fault_hex':hex(r.rip-targets[0]),'native_IKPAT':pattern,'native_args':{k:v for k,v in (args or {}).items() if k!='pointers'}}
   if args:
    fault['sparse_rows']=sparse_rows(pid,args,pattern,c['maximum_nodes']);fault['invalid_KLT_index_1based']=(r.rax-args['pointers']['K_LT'])//8+1
    try:fault['actual_assembly_block']=fault_block(pid,context,args,globals_,c['maximum_nodes'])
    except BaseException as exc:fault['actual_block_read_error']=str(exc)
   ptrace(6,pid,904,0)
 result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'assembly_calls':count,'ASSEM_C4_calls':blockcount,'IMP_CHKM_calls':globalcount,'fault':fault,'binary_sha256':c['binary_sha256'],'instrumentation':'Own TRACEME child, three hardware breakpoints and bounded scientific-array reads. Current ASSEM_C4 IXC, passed CHECK ITAB/X and actual NI/NJ cross-verified. No binary/instruction/mechanical-data writes; signals forwarded.','new_installation_or_compilation':False,'whole_impact_qualified':False};output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'trace_saved':True,'actual_block_captured':bool(fault and 'actual_assembly_block' in fault),'Engine_exit':result['Engine_exit_code'],'ASSEM_C4_calls':blockcount,'IMP_CHKM_calls':globalcount}),flush=True)

if __name__=='__main__':main()
