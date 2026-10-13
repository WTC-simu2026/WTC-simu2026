"""Read-only SIGABRT stack using installed readelf CFI in our own Engine child."""
from trace_aircraft_a48_linux import ptrace,registers,u64
from pathlib import Path
import hashlib,json,os,re,signal,subprocess,sys,time,bisect


def cfi_table(path):
    p=subprocess.run(['readelf','--debug-dump=frames-interp','--wide',str(path)],capture_output=True,check=True,timeout=25)
    lines=p.stdout.decode(errors='replace').splitlines();tables=[];index=0
    while index<len(lines):
        match=re.search(r'FDE .*pc=([0-9a-f]+)\.\.([0-9a-f]+)',lines[index])
        if not match:index+=1;continue
        first,last=map(lambda x:int(x,16),match.groups());index+=1;headers=None;rows=[]
        while index<len(lines) and lines[index].strip():
            parts=lines[index].split()
            if parts and parts[0]=='LOC':headers=parts
            elif headers and parts and re.fullmatch('[0-9a-f]+',parts[0]) and len(parts)==len(headers):
                rows.append((int(parts[0],16),dict(zip(headers[1:],parts[1:]))))
            index+=1
        if rows:tables.append((first,last,rows))
    return tables


def unwind(pid,r):
    maps=[line.split() for line in Path(f'/proc/{pid}/maps').read_text().splitlines()]
    regions=[];bases={}
    for row in maps:
        if len(row)<6 or not row[-1].startswith('/'):continue
        lo,hi=[int(value,16) for value in row[0].split('-')];path=row[-1]
        bases[path]=min(bases.get(path,lo-int(row[2],16)),lo-int(row[2],16))
        if 'x' in row[1]:regions.append((lo,hi,path))
    values={name:getattr(r,name) for name in ['rip','rsp','rbp','rbx','r12','r13','r14','r15']}
    cache={};frames=[];reason=None
    for depth in range(24):
        pc=values['rip'];region=next((entry for entry in regions if entry[0]<=pc<entry[1]),None)
        if region is None:reason='PC outside mapped executable regions';break
        path=region[2];base=bases[path];offset=pc-base
        frames.append({'depth':depth,'module':path,'module_offset':hex(offset),'PC':hex(pc),'SP':hex(values['rsp'])})
        if path not in cache:cache[path]=cfi_table(path)
        search=offset if depth==0 else offset-1
        table=next((entry for entry in cache[path] if entry[0]<=search<entry[1]),None)
        if table is None:reason='No matching installed ELF CFI';break
        row=next((entry[1] for entry in reversed(table[2]) if entry[0]<=search),None)
        if row is None:reason='No applicable CFI row';break
        cfa_rule=row.get('CFA','');match=re.fullmatch(r'(rsp|rbp|rbx|r12|r13|r14|r15)([+-]\d+)',cfa_rule)
        if not match:reason='Unsupported CFI CFA expression: '+cfa_rule;break
        cfa=values[match[1]]+int(match[2]);ra=row.get('ra')
        if ra is None or not re.fullmatch(r'c[+-]\d+',ra):reason='Unsupported CFI return-address rule: '+str(ra);break
        next_values=dict(values)
        for name,rule in row.items():
            if name in values and re.fullmatch(r'c[+-]\d+',rule):next_values[name]=u64(pid,cfa+int(rule[1:]))
        next_values['rip']=u64(pid,cfa+int(ra[1:]));next_values['rsp']=cfa
        frames[-1].update(CFI_CFA=cfa_rule,CFI_return_address_rule=ra)
        if not next_values['rip']:reason='Null return address';break
        if next_values['rsp']<=values['rsp']:reason='Non-increasing stack pointer';break
        values=next_values
    return {'frames':frames,'stop_reason':reason,'method':'Native registers, mapped executable modules and installed readelf interpreted ELF CFI; simple CFA and saved-register rules only. Unsupported expressions stop the walk rather than guessing.'}


def main():
    c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);d=Path(c['directory'])
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);output=d/'abort_trace_result.json';assert not output.exists()
    start=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.dup2(fd,1);os.dup2(fd,2);os.close(fd);os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status);deliver=0;abort=None
    while True:
        ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
        sig=os.WSTOPSIG(status);deliver=sig
        if sig==signal.SIGTRAP:deliver=0
        elif sig==signal.SIGABRT and abort is None:
            r=registers(pid)
            try:abort=unwind(pid,r)
            except Exception as exc:abort={'unwind_read_error':str(exc),'no_guessed_frames':True}
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,
        'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
        'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
        'native_SIGABRT_capture':abort,'scope':'Owned TRACEME child; native signal forwarded, register/stack reads only. No instruction, process mechanical data, restart or source/binary modification.'}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'abort_captured':abort is not None,'Engine_exit':result['Engine_exit_code']}),flush=True)


if __name__=='__main__':main()
