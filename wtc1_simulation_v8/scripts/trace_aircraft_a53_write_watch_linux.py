"""Watch a known native TYPE2 main row in the unchanged reference, without patching code or data."""
from trace_aircraft_a48_linux import *

def arg(pid,r,n):return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][n-1] if n<=6 else u64(pid,r.rsp+8*(n-6))
def integers(pid,p,n):
 data=b''.join(memory(pid,p+i,min(8192,n*4-i)) for i in range(0,n*4,8192));return list(struct.unpack('<'+'i'*n,data))

def main():
 c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256'];d=Path(c['directory']);os.chdir(d);out=d/'write_watch_result.json';assert not out.exists();start=time.monotonic();pid=os.fork()
 if pid==0:
  try:
   ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
  except BaseException:os._exit(77)
 _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status);rows=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(binary))];base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in rows);target=base+c['IND_KINE_K_offset'];ptrace(6,pid,848,target);ptrace(6,pid,904,1);deliver=0;contexts=0;watch=None;records=[];faults=[];writes=0
 while True:
  ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
  if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
  sig=os.WSTOPSIG(status);deliver=sig
  if sig==signal.SIGTRAP:
   r=registers(pid);deliver=0;dr6=ptrace(3,pid,896)&((1<<64)-1);ptrace(6,pid,896,0)
   if r.rip==target:
    contexts+=1;assert contexts<=4;p={k:arg(pid,r,n) for k,n in c['arguments'].items()};dims={k:i32(pid,p[k]) for k in ['NNMAX','NKMAX','NKINE','INK']};assert 0<dims['INK']<dims['NKINE']<=c['maximum_nodes'];itab=integers(pid,p['ITAB'],c['maximum_nodes']);index=itab.index(c['watched_original_node'])+1;row=i32(pid,p['INLOC']+4*(index-1));assert dims['INK']<row<=dims['NKINE'];countaddr=p['NROWK']+4*(row-1);n=i32(pid,countaddr);assert 0<=n<dims['NKMAX'];correct=p['ICOKM']+4*dims['NKMAX']*(row-dims['INK']-1);wrong=p['ICOK']+4*dims['NNMAX']*(row-1);assert correct!=wrong
    watch={'pointers':p,'dimensions':dims,'original_node':c['watched_original_node'],'internal_node':index,'local_row':row,'row_count_address':countaddr,'initial_count':n,'correct_buffer':correct,'ordinary_stride_buffer':wrong,'correct_initial_columns':integers(pid,correct,n) if n else [],'expected_next_value_before':i32(pid,correct+4*n),'wrong_next_value_before':i32(pid,wrong+4*n)}
    for slot,address in [(1,countaddr),(2,wrong+4*n),(3,correct+4*n)]:ptrace(6,pid,848+8*slot,address)
    control=85+(13<<20)+(13<<24)+(13<<28);ptrace(6,pid,904,control)
   elif watch and dr6&14:
    n=watch['initial_count'];correct=watch['correct_buffer'];wrong=watch['ordinary_stride_buffer'];row_count=i32(pid,watch['row_count_address']);wrongval=i32(pid,wrong+4*n);rightval=i32(pid,correct+4*n);record={'DR6_watch_bits':dr6&14,'instruction_after_write_offset':hex(r.rip-base),'row_count_now':row_count,'wrong_stride_next_value_now':wrongval,'correct_stride_next_value_now':rightval,'watched_wrong_column_written':bool(dr6&4),'watched_correct_column_written':bool(dr6&8),'watched_row_count_written':bool(dr6&2)}
    if 0<wrongval<=c['maximum_nodes']:record['wrong_column_original_label']=i32(pid,watch['pointers']['ITAB']+4*(wrongval-1))
    records.append(record)
    if dr6&12:writes+=1
    if writes>=2 or len(records)>=12:ptrace(6,pid,904,1)
  elif sig==signal.SIGSEGV:
   faults.append({'signal':sig,'instruction_offset':hex(registers(pid).rip-base)});ptrace(6,pid,904,0)
 context={k:v for k,v in (watch or {}).items() if k not in ['pointers','row_count_address','correct_buffer','ordinary_stride_buffer']}
 if watch:context.update(correct_buffer_address=hex(watch['correct_buffer']),ordinary_stride_buffer_address=hex(watch['ordinary_stride_buffer']))
 result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'contexts':contexts,'watch':context,'write_events':records,'faults':faults,'scope':'Original ungrouped reference; watch a predeclared TYPE2main/RBE2main row. Four hardware registers only: entry plus count, wrong-stride next column and correct-stride next column writes. No mechanical array/instruction/binary/restart patch.','new_installation_or_compilation':False};out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'watch_records':len(records),'wrong_column_writes':sum(e['watched_wrong_column_written'] for e in records),'correct_column_writes':sum(e['watched_correct_column_written'] for e in records),'Engine_exit':result['Engine_exit_code']}),flush=True)

if __name__=='__main__':main()
