"""Observe bounded adjacency-row destinations in the unmodified graph builder of our own child."""
from trace_aircraft_a48_linux import *

def arg(pid,r,n):return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][n-1] if n<=6 else u64(pid,r.rsp+8*(n-6))
def integers(pid,p,n):
 data=b''.join(memory(pid,p+i,min(8192,n*4-i)) for i in range(0,n*4,8192));return list(struct.unpack('<'+'i'*n,data))

def main():
 c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256'];d=Path(c['directory']);os.chdir(d);out=d/'routing_trace_result.json';assert not out.exists();start=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
  except BaseException:os._exit(77)
 _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status);rows=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(binary))];base=min(int(r[0].split('-')[0],16)-int(r[2],16) for r in rows);targets=[base+c['IND_KINE_K_offset'],base+c['REORDER_A_offset']];ptrace(6,pid,848,targets[0]);ptrace(6,pid,856,targets[1]);ptrace(6,pid,904,5);ctx=None;observations=[];context_count=0;calls=0;violations=0;deliver=0;faults=[]
 while True:
  ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
  if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
  sig=os.WSTOPSIG(status);deliver=sig
  if sig==signal.SIGTRAP:
   r=registers(pid);deliver=0
   if r.rip==targets[0]:
    context_count+=1;assert context_count<=4;p={k:arg(pid,r,n) for k,n in c['arguments'].items()};dims={k:i32(pid,p[k]) for k in ['NNMAX','NKMAX','NKINE','INK']};assert 0<dims['INK']<dims['NKINE']<=c['maximum_nodes'] and 0<dims['NNMAX']<=4096 and 0<dims['NKMAX']<=4096
    iloc=integers(pid,p['INLOC'],c['maximum_nodes']);itab=integers(pid,p['ITAB'],c['maximum_nodes']);inverse={v:itab[i] for i,v in enumerate(iloc) if 0<v<=dims['NKINE']};ctx={'pointers':p,'dimensions':dims,'inverse_local_to_original_label':inverse};calls=0;ptrace(6,pid,904,5)
   elif r.rip==targets[1] and ctx:
    calls+=1;p=ctx['pointers'];dims=ctx['dimensions'];count_address=r.rdi;actual_buffer=r.rsi;offset=count_address-p['NROWK'];row=offset//4+1
    if offset>=0 and offset%4==0 and 0<row<=dims['NKINE']:
     expected=p['ICOK']+4*dims['NNMAX']*(row-1) if row<=dims['INK'] else p['ICOKM']+4*dims['NKMAX']*(row-dims['INK']-1);wrong_stride=p['ICOK']+4*dims['NNMAX']*(row-1);bad=actual_buffer!=expected
     if bad or len(observations)<4:
      observations.append({'context':context_count,'local_row':row,'original_row_node':ctx['inverse_local_to_original_label'].get(row),'main_region':row>dims['INK'],'NNMAX':dims['NNMAX'],'NKMAX':dims['NKMAX'],'INK':dims['INK'],'actual_buffer_address':hex(actual_buffer),'expected_buffer_address':hex(expected),'ordinary_stride_address':hex(wrong_stride),'actual_uses_ordinary_stride':actual_buffer==wrong_stride,'destination_matches_expected_region':not bad,'caller_return_offset':hex(u64(pid,r.rsp)-base),'row_count_before':i32(pid,count_address),'neighbor_internal_node':i32(pid,r.rdx)})
     if bad:violations+=1
    if violations>=20 or calls>=512:ptrace(6,pid,904,1)
  elif sig==signal.SIGSEGV:
   faults.append({'signal':sig,'instruction_offset':hex(registers(pid).rip-base)});ptrace(6,pid,904,0)
 result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'IND_KINE_K_contexts':context_count,'observed_REORDER_calls_before_disarm':calls,'observed_wrong_destinations':violations,'observations':observations,'dimensions':ctx['dimensions'] if ctx else None,'faults':faults,'observation_bound':'Disarm REORDER after20wrong destinations or512calls; no assertion about total wrong calls.','instrumentation':'Owned child hardware breakpoints, scientific integer-array and register reads only. No graph, instruction, restart or binary patch; native signals forwarded.','new_installation_or_compilation':False};out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'routing_contexts':context_count,'wrong_destinations':violations,'Engine_exit':result['Engine_exit_code']}),flush=True)

if __name__=='__main__':main()
