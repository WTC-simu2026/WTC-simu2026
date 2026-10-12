"""Read-only runtime register/array observation of our own unmodified native Engine child."""
import ctypes,os,sys,json,signal,struct,time,hashlib
from pathlib import Path
from collections import deque
LIB=ctypes.CDLL(None,use_errno=True);LIB.ptrace.restype=ctypes.c_long
REGN=['r15','r14','r13','r12','rbp','rbx','r11','r10','r9','r8','rax','rcx','rdx','rsi','rdi','orig_rax','rip','cs','eflags','rsp','ss','fs_base','gs_base','ds','es','fs','gs']
class Regs(ctypes.Structure):_fields_=[(n,ctypes.c_ulonglong) for n in REGN]
class FP(ctypes.Structure):_fields_=[(n,ctypes.c_ushort) for n in ['cwd','swd','ftw','fop']]+[(n,ctypes.c_ulonglong) for n in ['rip','rdp']]+[(n,ctypes.c_uint) for n in ['mxcsr','mxcr_mask']]+[('st_space',ctypes.c_uint*32),('xmm_space',ctypes.c_uint*64),('padding',ctypes.c_uint*24)]
class User(ctypes.Structure):_fields_=[('regs',Regs),('u_fpvalid',ctypes.c_int),('i387',FP)]+[(n,ctypes.c_ulonglong) for n in ['u_tsize','u_dsize','u_ssize','start_code','start_stack']]+[('signal',ctypes.c_long),('reserved',ctypes.c_int),('u_ar0',ctypes.c_void_p),('u_fpstate',ctypes.c_void_p),('magic',ctypes.c_ulonglong),('u_comm',ctypes.c_char*32),('u_debugreg',ctypes.c_ulonglong*8)]
assert ctypes.sizeof(Regs)==216 and ctypes.sizeof(FP)==512 and User.u_debugreg.offset==848

def ptrace(req,pid,address=0,data=0):
 ctypes.set_errno(0);r=LIB.ptrace(ctypes.c_uint(req),ctypes.c_int(pid),ctypes.c_void_p(address),ctypes.c_void_p(data));err=ctypes.get_errno()
 if r==-1 and err:raise OSError(err,os.strerror(err))
 return r

def registers(pid):
 r=Regs();ptrace(12,pid,0,ctypes.addressof(r));return r

def memory(pid,address,n):
 assert 0<n<=8192 and address>4096
 return b''.join(struct.pack('<Q',ptrace(2,pid,address+i)&((1<<64)-1)) for i in range(0,n,8))[:n]

def u64(pid,address):return struct.unpack('<Q',memory(pid,address,8))[0]
def i32(pid,address):return struct.unpack('<i',memory(pid,address,4))[0]
def f64(pid,address):return struct.unpack('<d',memory(pid,address,8))[0]

def capture_arguments(pid,r):
 names=['NI','NJ','NEL','IDDL','IADK','JDIK','K_DIAG','K_LT','KIJ','ND','OFF','NDOF'];values=[r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9]+[u64(pid,r.rsp+8*(i+1)) for i in range(6)];p=dict(zip(names,values));return {'pointers':p,'NEL':i32(pid,p['NEL']),'ND':i32(pid,p['ND']),'caller_return_address':hex(u64(pid,r.rsp))}

def sparse_rows(pid,args,pattern,max_nodes):
 p=args['pointers'];nel=args['NEL'];assert 0<nel<=128 and 0<args['ND']<=6;ni=struct.unpack('<'+'i'*nel,memory(pid,p['NI'],4*nel));nj=struct.unpack('<'+'i'*nel,memory(pid,p['NJ'],4*nel));rows=[]
 for ep,(a,b) in enumerate(zip(ni,nj)):
  if not (0<a<=max_nodes and 0<b<=max_nodes) or a==b:continue
  ia=i32(pid,p['IDDL']+4*(a-1));ib=i32(pid,p['IDDL']+4*(b-1));na=i32(pid,p['NDOF']+4*(a-1));nb=i32(pid,p['NDOF']+4*(b-1));off=f64(pid,p['OFF']+8*ep);lower=min(ia,ib) if pattern==0 else max(ia,ib);wanted=(max(ia,ib) if pattern==0 else min(ia,ib))+1;nd=na if ia==lower else nb;search=[]
  if 0<=lower<=6*max_nodes and 0<=nd<=6 and off>0:
   for k in range(1,nd+1):
    first=i32(pid,p['IADK']+4*(lower+k-1));last=i32(pid,p['IADK']+4*(lower+k));cols=[]
    if 0<first<=last and last-first<=1024:cols=list(struct.unpack('<'+'i'*(last-first),memory(pid,p['JDIK']+4*(first-1),4*(last-first)))) if last>first else []
    search.append({'equation_row':lower+k,'first':first,'end_exclusive':last,'wanted_column':wanted,'column_present':wanted in cols,'column_count':last-first,'observed_columns':cols})
  rows.append({'element_in_block_1based':ep+1,'internal_nodes':[a,b],'IDDL':[ia,ib],'NDOF':[na,nb],'OFF':off,'sparse_search':search})
 return rows

def main():
 c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256'];d=Path(c['directory']);os.chdir(d);out=d/'trace_result.json';assert not out.exists();started=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
  except BaseException:os._exit(77)
 _,status=os.waitpid(pid,0)
 if not os.WIFSTOPPED(status):raise RuntimeError('Owned-child tracing did not reach exec stop')
 maps=Path(f'/proc/{pid}/maps').read_text();lines=[l.split() for l in maps.splitlines() if l.endswith(str(binary))];base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in lines);target=base+c['function_offset'];ptrace(6,pid,848,target);ptrace(6,pid,904,1);count=0;args=None;fault=None;events=[];signal_to_deliver=0
 while True:
  ptrace(7,pid,0,signal_to_deliver);_,status=os.waitpid(pid,0)
  if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
  sig=os.WSTOPSIG(status);signal_to_deliver=sig
  if sig==signal.SIGTRAP:
   r=registers(pid);signal_to_deliver=0
   if r.rip==target:
    count+=1;args=capture_arguments(pid,r)
    if count>10000:os.kill(pid,signal.SIGKILL);raise RuntimeError('Trace call bound reached')
  elif sig==signal.SIGSEGV and fault is None:
   r=registers(pid);info=(ctypes.c_byte*128)();ptrace(0x4202,pid,0,ctypes.addressof(info));fault_address=struct.unpack('<Q',bytes(info)[16:24])[0];pattern=i32(pid,base+c['pattern_symbol_offset']);fault={'signal':sig,'instruction_offset_hex':hex(r.rip-base),'function_relative_fault_hex':hex(r.rip-target),'fault_address':hex(fault_address),'registers':{n:hex(getattr(r,n)) for n in REGN},'assembly_calls_before_fault':count,'native_args':{**args,'pointers':{k:hex(v) for k,v in args['pointers'].items()}} if args else None,'native_IKPAT':pattern}
   if args:
    try:fault['sparse_rows']=sparse_rows(pid,args,pattern,c['maximum_nodes'])
    except BaseException as exc:fault['sparse_read_error']=str(exc)
    fault['destination_KLT_index_from_RAX_1based']=(r.rax-args['pointers']['K_LT'])//8+1
   # Forward the original signal so the unchanged Engine keeps its own handler/termination.
   ptrace(6,pid,904,0)
  events.append({'signal':sig,'entry_calls':count})
 result={'created_epoch':time.time(),'wall_s':time.monotonic()-started,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'fault':fault,'assembly_call_count':count,'trace_event_count':len(events),'instrumentation':'Owned child PTRACE_TRACEME, hardware execution breakpoint, register and bounded numeric-array reads only; no instruction/data/binary/physical-state patch. Native signal forwarded unchanged.','binary_sha256':c['binary_sha256'],'new_software_installation_or_compilation':False,'whole_impact_qualified':False};out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'trace_completed':True,'fault_captured':fault is not None,'calls':count,'Engine_exit_code':result['Engine_exit_code']}),flush=True)

if __name__=='__main__':main()
