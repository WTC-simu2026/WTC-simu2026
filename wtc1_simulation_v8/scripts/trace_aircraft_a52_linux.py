"""Capture TYPE2 binding inputs at two hardware breakpoints in our unmodified Engine child."""
from trace_aircraft_a48_linux import ptrace,registers,memory,u64,i32
import os,sys,json,signal,struct,time,hashlib,math
from pathlib import Path

def array(pid,addr,n,code):
 size=struct.calcsize('<'+code);data=b''.join(memory(pid,addr+i,min(8192,n*size-i)) for i in range(0,n*size,8192));return list(struct.unpack('<'+code*n,data))

def binding(pid,r,mode,nn):
 names=['NSN','NMN','IRECT','PARAM','MSR','NSV','IRTL','MS','X','WEIGHT','ITAB','NSC','ISI','NS','NODS','IKC','NDOF','NDDL','IDDL','IADK','JDIK','DIAG_K','LT_K','B']
 vals=[r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9]+[u64(pid,r.rsp+8*(i+1)) for i in range(len(names)-6)];p=dict(zip(names,vals));ns=i32(pid,p['NSN']);nm=i32(pid,p['NMN']);assert 0<ns<=64 and 0<nm<=64
 nodes=array(pid,p['NSV'],ns,'i');facets=array(pid,p['IRTL'],ns,'i');assert all(0<n<=nn for n in nodes) and all(0<f<=nm for f in facets)
 rect=array(pid,p['IRECT'],4*max(facets),'i');width=2 if mode==0 else 7;param=array(pid,p['PARAM'],width*ns,'d');out=[]
 for i,(n,f) in enumerate(zip(nodes,facets)):
  main=rect[4*(f-1):4*f];assert all(0<v<=nn for v in main);labels=[i32(pid,p['ITAB']+4*(v-1)) for v in main];coordinates=[array(pid,p['X']+24*(v-1),3,'d') for v in [n]+main];dof=[i32(pid,p['NDOF']+4*(v-1)) for v in [n]+main];coef=param[width*i:width*(i+1)];assert all(math.isfinite(v) for row in coordinates for v in row) and all(math.isfinite(v) for v in coef)
  out.append({'secondary_original_label':i32(pid,p['ITAB']+4*(n-1)),'secondary_internal_index':n,'selected_facet_internal_index':f,'main_original_labels_ordered':labels,'native_parameter_values':coef,'native_point_coordinates_mm':coordinates,'native_NDOF':dof,'mode':mode})
 return {'NSN':ns,'NMN':nm,'mode':mode,'bindings':out}

def main():
 c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256'];d=Path(c['directory']);os.chdir(d);targetfile=d/'type2_trace_result.json';assert not targetfile.exists();start=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
  except BaseException:os._exit(77)
 _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status);maps=Path(f'/proc/{pid}/maps').read_text();rows=[l.split() for l in maps.splitlines() if l.endswith(str(binary))];base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in rows);targets=[base+v for v in c['function_offsets']];ptrace(6,pid,848,targets[0]);ptrace(6,pid,856,targets[1]);ptrace(6,pid,904,5);calls=[];faults=[];deliver=0
 while True:
  ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
  if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
  sig=os.WSTOPSIG(status);deliver=sig
  if sig==signal.SIGTRAP:
   r=registers(pid);deliver=0
   if r.rip in targets:
    calls.append(binding(pid,r,targets.index(r.rip),c['maximum_nodes']));assert len(calls)<=512
  elif sig==signal.SIGSEGV:
   faults.append({'signal':sig,'instruction_offset':hex(registers(pid).rip-base)});ptrace(6,pid,904,0)
 result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'calls':calls,'faults':faults,'binary_sha256':c['binary_sha256'],'scope':'Our own TRACEME child; two hardware instruction breakpoints, bounded reads of TYPE2 scientific input arrays only. No data/instruction/binary/restart writes. Native signals forwarded.','software_installation_or_compilation':False,'whole_impact_qualified':False};targetfile.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'TYPE2_calls_captured':len(calls),'Engine_exit_code':result['Engine_exit_code'],'faults':len(faults)}),flush=True)

if __name__=='__main__':main()
