"""Prepared observer only. A separate launcher must require fresh A85 consent.

Four hardware execution breakpoints; numeric data/code are never written.
Read the first NL_SOLV iterations and their native norm results, then disable
all breakpoints and let the unchanged Engine reach its own termination.
"""
from trace_aircraft_a48_linux import ptrace,registers,u64,i32
from pathlib import Path
import os,sys,json,hashlib,signal,time,struct,math


def main():
    c=json.loads(Path(sys.argv[1]).read_text());b=Path(c['binary']);d=Path(c['directory'])
    assert c['new_A85_explicit_human_consent'] and c['CPU_threads']==1 and c['cap_s']==180
    assert c['maximum_Engine']==1 and c['maximum_Starter']==0 and c['node_count']==8
    assert hashlib.sha256(b.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);output=d/'normalization_observation.json';assert not output.exists()
    start=time.monotonic();pid=os.fork();mem=None;completed=False
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
            os.execv(str(b),[str(b),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    try:
        _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
        maps=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(b))]
        base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in maps)
        sy=c['symbols'];nl=base+sy['nl_solv_']['offset'];nl_end=nl+sy['nl_solv_']['bytes']
        sites=[nl,base+sy['crit_ite_']['offset'],base+sy['produt_uhp_']['offset'],0]
        mem=os.open(f'/proc/{pid}/mem',os.O_RDONLY);events=[];current=None;pending=None;deliver=0;traps=0
        def read_values(address,count,kind):
            assert 0<count<=128 and address>4096
            width={'d':8,'i':4}[kind];payload=os.pread(mem,count*width,address)
            assert len(payload)==count*width
            return list(struct.unpack('<'+str(count)+kind,payload))
        def safe(x):
            if isinstance(x,list):return [safe(v) for v in x]
            if isinstance(x,float) and not math.isfinite(x):return 'NaN' if math.isnan(x) else '+Infinity' if x>0 else '-Infinity'
            return x
        def f(address):return safe(read_values(address,1,'d')[0])
        def args(r,n):return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][:n]+[u64(pid,r.rsp+8*(j-5)) for j in range(6,n)]
        def enable():
            for j,a in enumerate(sites):ptrace(6,pid,848+8*j,a)
            ptrace(6,pid,904,sum(1<<(2*j) for j,a in enumerate(sites) if a))
        def snapshot(a):
            n=i32(pid,a[0]);assert n==8
            return {'NDDL':n,'NDDL0':i32(pid,a[38]),'R02':f(a[22]),'RU0':f(a[28]),'ROLD':f(a[29]),
                'E02':f(a[34]),'DE0':f(a[35]),'EIMP':f(a[36]),'U02':f(a[40]),
                'LS':safe(read_values(a[39],3,'d')),'F_free':safe(read_values(a[11],n,'d')),
                'D_all24':safe(read_values(a[4],24,'d')),'DD_all24':safe(read_values(a[23],24,'d')),
                'IDDL8':read_values(a[1],8,'i'),'NDOF8':read_values(a[2],8,'i')}
        enable()
        while True:
            ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):completed=True;break
            sig=os.WSTOPSIG(status);deliver=sig
            if sig!=signal.SIGTRAP:events.append({'forwarded_signal':sig});continue
            deliver=0;r=registers(pid);ptrace(6,pid,896,0);traps+=1;assert traps<=64
            if sites[0] and r.rip==sites[0]:
                a=args(r,41);it=i32(pid,a[26]);assert 0<=it<=2
                current={'iteration':it,'pointers':a};events.append({'event':'NL_SOLV_entry','iteration':it,'values':snapshot(a)})
            elif sites[1] and r.rip==sites[1]:
                assert current is not None
                a=args(r,6);it=i32(pid,a[0]);assert it==current['iteration'] and it in [1,2]
                events.append({'event':'CRIT_ITE_entry','iteration':it,'UR':f(a[1]),'RR':f(a[2]),'ER':f(a[3]),
                    'TOL':f(a[5]),'values':snapshot(current['pointers'])})
                if it==2:
                    assert pending is None;sites=[0,0,0,0];enable()
            elif sites[2] and r.rip==sites[2]:
                ret=u64(pid,r.rsp)
                if current is not None and nl<=ret<nl_end:
                    assert pending is None
                    a=args(r,9);assert i32(pid,a[1])==8
                    p=current['pointers'];role='D' if a[5]==p[4] else 'DD' if a[5]==p[23] else 'unclassified'
                    assert role!='unclassified'
                    pending={'result_pointer':a[7],'role':role,'iteration':current['iteration'],'return_offset':ret-base}
                    sites[3]=ret;enable()
            elif pending is not None and sites[3] and r.rip==sites[3]:
                events.append({'event':'PRODUT_UHP_return','iteration':pending['iteration'],'role':pending['role'],
                    'native_norm_squared':f(pending['result_pointer']),'caller_return_offset':pending['return_offset']})
                pending=None;sites[3]=0;enable()
            else:raise RuntimeError('Unexpected observer trap; no numeric state patched')
        iterations=[e['iteration'] for e in events if e.get('event')=='CRIT_ITE_entry']
        complete=iterations==[1,2] and all(any(e.get('event')=='PRODUT_UHP_return' and e['iteration']==2 and e['role']==role for e in events) for role in ['D','DD'])
        result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
            'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'observation_complete':complete,
            'events':events,'trap_count':traps,'binary_sha256':c['binary_sha256'],
            'method':'Owned TRACEME child, four hardware execution breakpoints, O_RDONLY numeric memory reads; no instruction/data/register-numeric/source/binary patch. Signals forwarded. All breakpoints disabled at criterion iteration2.',
            'new_compilation_or_installation':False,'no_physical_qualification':True,'whole_credit_s':0}
        output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'observer_complete':complete,'Engine_exit':result['Engine_exit_code']}),flush=True)
    finally:
        if mem is not None:os.close(mem)
        if not completed:
            try:os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)
            except ProcessLookupError:pass

if __name__=='__main__':main()
