"""Read-only watches on the NODREAC descriptor and its allocator header in our child."""
from trace_aircraft_a48_linux import ptrace,registers,u64
from pathlib import Path
import hashlib,json,os,signal,sys,time


def main():
    c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);d=Path(c['directory'])
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);output=d/'heap_watch_result.json';assert not output.exists();start=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
    maps=[row.split() for row in Path(f'/proc/{pid}/maps').read_text().splitlines() if row.endswith(str(binary))]
    base=min(int(row[0].split('-')[0],16)-int(row[2],16) for row in maps)
    pointer_address=base+c['NODREAC_symbol_offset'];free_site=base+c['free_call_offset']
    ptrace(6,pid,848,pointer_address);ptrace(6,pid,864,free_site);ptrace(6,pid,904,17+(9<<16))
    records=[];deliver=0;header=None;abort=None
    while True:
        ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
        sig=os.WSTOPSIG(status);deliver=sig
        if sig==signal.SIGTRAP:
            deliver=0;r=registers(pid);bits=ptrace(3,pid,896)&7;ptrace(6,pid,896,0)
            pointer=u64(pid,pointer_address)
            record={'bits':bits,'instruction_after_event_offset':hex(r.rip-base),
                'pointer':hex(pointer),'pointer_mod16':pointer%16,'at_known_free_call':r.rip==free_site}
            if pointer>4096:
                try:
                    record['malloc_size_word']=hex(u64(pid,pointer-8));record['preceding_word']=hex(u64(pid,pointer-16))
                    if bits&1 and pointer%8==0:
                        header=pointer-8;ptrace(6,pid,856,header);ptrace(6,pid,904,21+(9<<16)+(9<<20))
                except OSError as exc:record['header_read_error']=str(exc)
            if header:
                try:record['watched_header_now']=hex(u64(pid,header))
                except OSError as exc:record['watched_header_read_error']=str(exc)
            records.append(record)
            if len(records)>=c['maximum_events']:ptrace(6,pid,904,16)
        elif sig==signal.SIGABRT and abort is None:
            r=registers(pid);abort={'signal':sig,'PC':hex(r.rip),'NODREAC_pointer':hex(u64(pid,pointer_address))}
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,
        'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
        'events':records,'abort':abort,
        'scope':'Three hardware watches in an owned TRACEME child: descriptor pointer writes, allocated header writes and the native free call identified by CFI/disassembly. Bounded numeric reads, no code or mechanical process writes; native signals forwarded.'}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'events':len(records),'Engine_exit':result['Engine_exit_code']}),flush=True)


if __name__=='__main__':main()
