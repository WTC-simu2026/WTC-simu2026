"""Read native SMSTR allocation descriptor and match it to SRCOORK's actual SAV."""
from trace_aircraft_a48_linux import ptrace,registers,u64,i32
from pathlib import Path
import hashlib,json,os,signal,sys,time

def signed(v):return v-(1<<64) if v&(1<<63) else v

def main():
    c=json.loads(Path(sys.argv[1]).read_text());b=Path(c['binary']);d=Path(c['directory']);assert hashlib.sha256(b.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);out=d/'allocation_trace_result.json';assert not out.exists();start=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(b),[str(b),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
    maps=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(b))];base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in maps)
    entries=[base+x for x in c['allocator_offsets']];source=base+c['SRCOORK_symbol_offset']
    ptrace(6,pid,848,entries[0]);ptrace(6,pid,856,entries[1]);ptrace(6,pid,872,source);control=69;ptrace(6,pid,904,control)
    calls=0;alloc=[];pending=None;return_site=None;context=None;deliver=0
    while True:
        ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
        sig=os.WSTOPSIG(status);deliver=sig
        if sig==signal.SIGTRAP:
            deliver=0;r=registers(pid);ptrace(6,pid,896,0)
            if r.rip in entries:
                calls+=1;length=r.r9
                label=''
                if r.rdx>4096 and 0<length<=128:
                    label=b''.join(u64(pid,r.rdx+i).to_bytes(8,'little') for i in range(0,length,8))[:length].decode('ascii',errors='replace')
                if 'SMSTR' in label:
                    pending={'label':label,'requested_values':i32(pid,r.rsi),'descriptor_address':hex(r.rdi),'caller_return_offset':hex(u64(pid,r.rsp)-base),'allocator_entry_offset':hex(r.rip-base)}
                    return_site=u64(pid,r.rsp);ptrace(6,pid,864,return_site);control|=16
                # Step once with execute breakpoints disabled, then restore them.
                ptrace(6,pid,904,0);ptrace(9,pid);_,step=os.waitpid(pid,0);assert os.WIFSTOPPED(step) and os.WSTOPSIG(step)==signal.SIGTRAP
                ptrace(6,pid,896,0);ptrace(6,pid,904,control if calls<c['maximum_allocator_calls'] else control&~5)
            elif return_site and r.rip==return_site:
                address=int(pending['descriptor_address'],16);words=[u64(pid,address+8*i) for i in range(8)]
                lower,upper=signed(words[6]),signed(words[7])
                pending.update(data_pointer=hex(words[0]),element_bytes=words[2],lower_bound=lower,upper_bound=upper,native_capacity=max(0,upper-lower+1),descriptor_raw_words=[hex(v) for v in words]);alloc.append(pending)
                pending=None;return_site=None;ptrace(6,pid,864,0);control&=~16;ptrace(6,pid,904,control)
            elif r.rip==source:
                p={key:([r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][j-1] if j<=6 else u64(pid,r.rsp+8*(j-6))) for j,key in enumerate(c['SRCOORK_arguments'],1)}
                context={'SAV_pointer':hex(p['SAV']),'NEL':i32(pid,p['NEL']),'IGTYP':i32(pid,p['IGTYP']),'matching_allocations':[v for v in alloc if int(v['data_pointer'],16)==p['SAV']]}
                ptrace(6,pid,904,0)
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'allocator_calls_observed':calls,'SMSTR_allocations':alloc,'SRCOORK_context':context,'scope':'Read caller label, requested n, and 64-byte descriptor at allocator return, then match native data pointer to SAV. Descriptor offset interpretation is verified from disassembly of this exact binary. Bounded owned child observation, no software/data patches.'}
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'SMSTR_allocations':len(alloc),'Engine_exit':result['Engine_exit_code']}),flush=True)

if __name__=='__main__':main()
