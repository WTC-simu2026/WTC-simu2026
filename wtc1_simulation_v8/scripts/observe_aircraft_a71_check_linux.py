"""Prepared read-only observer; the separate Windows launcher must enforce NEW human consent and budget."""
from trace_aircraft_a48_linux import ptrace,registers,u64,i32
from pathlib import Path
import os,sys,json,hashlib,signal,time,array,math

def main():
    c=json.loads(Path(sys.argv[1]).read_text());b=Path(c['binary']);d=Path(c['directory'])
    assert c['new_A71_explicit_human_consent'] and c['CPU_threads']==1 and c['cap_s']==180
    assert hashlib.sha256(b.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);output=d/'check_observation.json';assert not output.exists();start=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
            os.execv(str(b),[str(b),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    mem=None;completed=False
    try:
        _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
        maps=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(b))]
        base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in maps);symbols=c['symbols'];produt_site=base+symbols['produt_w_']['offset'];sites=[base+symbols[n]['offset'] for n in ['imp_check0_','lin_solv_']]+[0,0]
        mem=os.open(f'/proc/{pid}/mem',os.O_RDONLY);events=[];pre=None;lb=None;pending=None;post=None;deliver=0;trap_count=0
        def bulk(address,count,kind):
            width={'d':8,'i':4}[kind];assert 0<=count<=300000
            if count==0:return array.array(kind)
            assert address>4096
            buf=os.pread(mem,count*width,address);assert len(buf)==count*width
            a=array.array(kind);a.frombytes(buf);return a
        def args(r,n):return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][:n]+[u64(pid,r.rsp+8*(j-5)) for j in range(6,n)]
        def enable():
            for j,a in enumerate(sites):ptrace(6,pid,848+8*j,a)
            ptrace(6,pid,904,sum(1<<(2*j) for j,a in enumerate(sites) if a))
        enable()
        while True:
            ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):completed=True;break
            sig=os.WSTOPSIG(status);deliver=sig
            if sig!=signal.SIGTRAP:
                events.append({'signal_forwarded_unchanged':sig});continue
            deliver=0;r=registers(pid);ptrace(6,pid,896,0);trap_count+=1;assert trap_count<=24
            if r.rip==sites[0] and pre is None:
                a=args(r,15);n=i32(pid,a[1]);assert 0<n<=300000
                diagonal=bulk(a[3],n,'d');ni=i32(pid,a[10]);assert 0<=ni<=300000
                for idx,value in zip(bulk(a[11],ni,'i'),bulk(a[12],ni,'d')):
                    assert 1<=idx<=n;diagonal[idx-1]+=value
                Path('pre_combined_diagonal.raw').write_bytes(diagonal.tobytes())
                pre={'NDDL':n,'NDDLI':ni,'minimum':min(diagonal),'maximum':max(diagonal),'all_finite':all(math.isfinite(x) for x in diagonal),
                    'native_zero_stiffness_report_threshold_count':sum(x<1e-10 for x in diagonal)}
                sites[0]=base+symbols['imp_checm0_']['offset'];sites[2]=produt_site;enable()
            elif r.rip==sites[1]:
                a=args(r,25);n=i32(pid,a[0]);rhs=bulk(a[22],n,'d')
                lb={'NDDL':n,'all_finite':all(math.isfinite(x) for x in rhs),'norm_squared_single_process':sum(x*x for x in rhs),
                    'nonzero_entries':sum(x!=0 for x in rhs),'maximum_absolute_entry':max(abs(x) for x in rhs)}
                Path('native_LB.raw').write_bytes(rhs.tobytes());sites[1]=0;enable()
            elif r.rip==sites[2]:
                ret=u64(pid,r.rsp)-base;lo=symbols['imp_chkm_']['offset'];hi=lo+symbols['imp_chkm_']['bytes']
                if lo<=ret<hi and r.rsi==r.rdx:
                    pending={'result_pointer':r.r8,'caller_return_offset':ret};sites[2]=0;sites[3]=ret+base;enable()
            elif pending and r.rip==sites[3]:
                value=bulk(pending['result_pointer'],1,'d')[0]
                events.append({'native_R2':value if math.isfinite(value) else repr(value),'loading_positive_only_gate':math.isfinite(value) and 0<value<1e30,
                    'caller_return_offset':pending['caller_return_offset']});pending=None;sites[3]=0;enable()
            elif pre is not None and r.rip==sites[0]:
                a=args(r,10);n=i32(pid,a[1]);assert n==pre['NDDL'];diagonal=bulk(a[3],n,'d')
                Path('post_precondition_diagonal.raw').write_bytes(diagonal.tobytes())
                post={'NDDL':n,'minimum':min(diagonal),'maximum':max(diagonal),'all_finite':all(math.isfinite(x) for x in diagonal),
                    'native_connection_warning_condition_count':sum(x<1e-12 or x>1e10 for x in diagonal)}
                count=c['node_count'];assert 0<count<=100000
                for label,address in [('ITAB',a[0]),('IDDL',a[2]),('NDOF',a[4]),('INLOC',a[6])]:
                    Path('native_'+label+'.raw').write_bytes(bulk(address,count,'i').tobytes())
                sites[0]=0;enable()
            else:raise RuntimeError('Unclassified observer breakpoint; no numerical state changed')
        result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
            'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,'pre':pre,'LB_before_linear_solver':lb,'post':post,'events':events,
            'observation_complete':pre is not None and lb is not None and post is not None and any('native_R2' in e for e in events),
            'method':'Owned TRACEME child, four hardware execution breakpoints, numeric memory/ABI reads only. Signals forwarded. No instruction, source, binary, mechanical data or restart patch.',
            'whole_impact_qualified':False,'whole_credit_s':0,'no_installation_or_compilation':True}
        output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'observer_complete':result['observation_complete'],'Engine_exit':result['Engine_exit_code']}),flush=True)
    finally:
        if mem is not None:os.close(mem)
        if not completed:
            try:os.kill(pid,signal.SIGKILL);os.waitpid(pid,0)
            except ProcessLookupError:pass

if __name__=='__main__':main()
