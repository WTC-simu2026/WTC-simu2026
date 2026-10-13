"""Bounded native SRCOORK/header observation in an owned child, no data edits."""
from trace_aircraft_a48_linux import ptrace,registers,u64,i32
from pathlib import Path
import hashlib,json,os,signal,sys,time,struct

def main():
    c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);d=Path(c['directory'])
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);output=d/'scratch_watch_result.json';assert not output.exists();start=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
    maps=[row.split() for row in Path(f'/proc/{pid}/maps').read_text().splitlines() if row.endswith(str(binary))]
    base=min(int(row[0].split('-')[0],16)-int(row[2],16) for row in maps)
    pointer_address=base+c['NODREAC_symbol_offset'];entry=base+c['SRCOORK_symbol_offset']
    ptrace(6,pid,848,pointer_address);ptrace(6,pid,864,entry)
    control=17+(9<<16);ptrace(6,pid,904,control)
    records=[];contexts=[];deliver=0;header=None;return_site=None;sav=None;nel=None;abort=None
    while True:
        ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
        sig=os.WSTOPSIG(status);deliver=sig
        if sig==signal.SIGTRAP:
            deliver=0;r=registers(pid);bits=ptrace(3,pid,896)&15;ptrace(6,pid,896,0)
            if r.rip==entry and not contexts:
                p={key:([r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][index-1] if index<=6 else u64(pid,r.rsp+8*(index-6))) for index,key in enumerate(c['SRCOORK_arguments'],1)}
                nel=i32(pid,p['NEL']);assert 0<nel<=128;sav=p['SAV'];return_site=u64(pid,r.rsp)
                contexts.append({'NEL':nel,'scalar_arguments':{key:i32(pid,p[key]) for key in ['ISMSTR','JHBE','JCVT','IREP','IGTYP','ISORTH']},'SAV_pointer':hex(sav),'SAV_preceding_size_word':hex(u64(pid,sav-8)),'NODREAC_pointer':hex(u64(pid,pointer_address)),'NODREAC_header':hex(u64(pid,header)) if header else None,'return_site_offset':hex(return_site-base)})
                ptrace(6,pid,864,0);ptrace(6,pid,872,return_site);control=(control&~16)|64;ptrace(6,pid,904,control)
            elif return_site and r.rip==return_site:
                values=[struct.unpack('<d',u64(pid,sav+8*i).to_bytes(8,'little'))[0] for i in range(21*nel)]
                contexts[-1].update(return_observed=True,SAV_21_columns_after_return=values,NODREAC_header_at_return=hex(u64(pid,header)) if header else None)
                ptrace(6,pid,872,0);control&=~64;ptrace(6,pid,904,control)
            else:
                pointer=u64(pid,pointer_address)
                record={'bits':bits,'instruction_after_event_offset':hex(r.rip-base),'NODREAC_pointer':hex(pointer)}
                if bits&1 and pointer>4096 and pointer%8==0:
                    header=pointer-8;ptrace(6,pid,856,header);control|=4+(9<<20);ptrace(6,pid,904,control)
                    record['allocation_size_word']=hex(u64(pid,header))
                if header:record['watched_header_now']=hex(u64(pid,header))
                records.append(record)
            if len(records)>=c['maximum_events']:ptrace(6,pid,904,0)
        elif sig in [signal.SIGABRT,signal.SIGSEGV] and abort is None:
            r=registers(pid);abort={'signal':sig,'PC_offset':hex(r.rip-base)}
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'events':records,'SRCOORK_contexts':contexts,'abort':abort,'scope':'Native source function entry/return and NODREAC pointer/header hardware watches. Heap size words are raw observations, not a read of the Fortran allocation descriptor. No mechanical data or instruction modifications; signals forwarded.'}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'Engine_exit':result['Engine_exit_code'],'contexts':len(contexts)}),flush=True)

if __name__=='__main__':main()
