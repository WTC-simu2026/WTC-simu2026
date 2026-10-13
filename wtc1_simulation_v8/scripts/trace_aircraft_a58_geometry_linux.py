"""Bounded native dispatch and volumetric Jacobian observation in an owned child."""
from trace_aircraft_a48_linux import ptrace,registers,u64,i32
from pathlib import Path
import hashlib,json,os,signal,sys,time,struct

def main():
    c=json.loads(Path(sys.argv[1]).read_text());b=Path(c['binary']);d=Path(c['directory']);assert hashlib.sha256(b.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);out=d/'geometry_dispatch_result.json';assert not out.exists();start=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(b),[str(b),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
    maps=[v.split() for v in Path(f'/proc/{pid}/maps').read_text().splitlines() if v.endswith(str(b))];base=min(int(v[0].split('-')[0],16)-int(v[2],16) for v in maps)
    names=['s8zke3_','s8zderict3_','schkjab3_','suser43_'];sites=[base+c['symbols'][n] for n in names]
    for j,address in enumerate(sites):ptrace(6,pid,848+8*j,address)
    ptrace(6,pid,904,85);events=[];deliver=0
    while True:
        ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
        sig=os.WSTOPSIG(status);deliver=sig
        if sig==signal.SIGTRAP:
            deliver=0;r=registers(pid);ptrace(6,pid,896,0);j=sites.index(r.rip);record={'function':names[j],'entry_offset':hex(r.rip-base)}
            if j==0:
                pointers={key:([r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][i-1] if i<=6 else u64(pid,r.rsp+8*(i-6))) for i,key in enumerate(c['S8ZKE3_arguments'],1)}
                record['native_arguments']={key:i32(pid,pointers[key]) for key in ['NEL','MTN','ISMSTR','JHBE','JCVT','IGTYP','ISORTH','IREP']}
            elif j==2:
                nel=i32(pid,r.rcx);assert 0<nel<=128
                double=lambda a:struct.unpack('<d',u64(pid,a).to_bytes(8,'little'))[0]
                record.update(NEL=nel,DET=[double(r.rsi+8*i) for i in range(nel)],OFF=[double(r.rdi+8*i) for i in range(nel)],element_labels=[i32(pid,r.rdx+4*i) for i in range(nel)])
            events.append(record);ptrace(6,pid,848+8*j,0)
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'events':events,'scope':'First entry only for four native functions; typed scalar/determinant reads bounded to128 elements. No code or mechanical data writes. The absence of a later material call before the STOP is not an all-input support proof.'}
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'events':len(events),'Engine_exit':result['Engine_exit_code']}),flush=True)

if __name__=='__main__':main()
