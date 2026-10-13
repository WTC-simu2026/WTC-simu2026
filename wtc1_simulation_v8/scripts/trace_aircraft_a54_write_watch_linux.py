"""Observe the corrected native watched row through graph-builder return, without writes."""
from trace_aircraft_a53_write_watch_linux import ptrace, registers, i32, u64, integers
from pathlib import Path
import hashlib
import json
import os
import signal
import time


def arg(pid,r,index):
    return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][index-1] if index<=6 else u64(pid,r.rsp+8*(index-6))


def main():
    import sys
    c=json.loads(Path(sys.argv[1]).read_text()); binary=Path(c['binary']); d=Path(c['directory'])
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d); out=d/'write_watch_result.json'; assert not out.exists()
    start=time.monotonic(); pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0); fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.dup2(fd,1); os.dup2(fd,2); os.close(fd)
            os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
        except BaseException:
            os._exit(77)
    _,status=os.waitpid(pid,0); assert os.WIFSTOPPED(status)
    maps=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(binary))]
    base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in maps)
    entry=base+c['IND_KINE_K_offset']; return_target=None
    ptrace(6,pid,848,entry); ptrace(6,pid,904,1)
    deliver=0; watch=None; records=[]; faults=[]; final=None
    try:
        while True:
            ptrace(7,pid,0,deliver); _,status=os.waitpid(pid,0)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
            sig=os.WSTOPSIG(status); deliver=sig
            if sig==signal.SIGTRAP:
                r=registers(pid); deliver=0; dr6=ptrace(3,pid,896)&((1<<64)-1); ptrace(6,pid,896,0)
                if r.rip==entry:
                    assert watch is None
                    p={k:arg(pid,r,n) for k,n in c['arguments'].items()}
                    dims={k:i32(pid,p[k]) for k in ['NNMAX','NKMAX','NKINE','INK']}
                    itab=integers(pid,p['ITAB'],c['maximum_nodes'])
                    index=itab.index(c['watched_original_node'])+1
                    row=i32(pid,p['INLOC']+4*(index-1)); assert dims['INK']<row<=dims['NKINE']
                    countaddr=p['NROWK']+4*(row-1); n=i32(pid,countaddr)
                    assert 0<=n<dims['NKMAX']<=4096
                    correct=p['ICOKM']+4*dims['NKMAX']*(row-dims['INK']-1)
                    wrong=p['ICOK']+4*dims['NNMAX']*(row-1); assert correct!=wrong
                    columns=integers(pid,correct,n)
                    watch={'dimensions':dims,'original_node':c['watched_original_node'],
                        'internal_node':index,'local_row':row,'initial_count':n,
                        'correct_initial_columns':columns,
                        'correct_initial_original_labels':[itab[v-1] for v in columns],
                        'expected_next_value_before':i32(pid,correct+4*n),
                        'wrong_next_value_before':i32(pid,wrong+4*n),
                        'countaddr':countaddr,'correct':correct,'wrong':wrong,'itab':itab}
                    return_target=u64(pid,r.rsp)
                    for slot,address in [(0,return_target),(1,countaddr),(2,wrong+4*n),(3,correct+4*n)]:
                        ptrace(6,pid,848+8*slot,address)
                    ptrace(6,pid,904,85+(13<<20)+(13<<24)+(13<<28))
                elif return_target and r.rip==return_target:
                    n=i32(pid,watch['countaddr']); assert 0<=n<=watch['dimensions']['NKMAX']
                    columns=integers(pid,watch['correct'],n)
                    final={'count':n,'correct_columns':columns,
                        'correct_original_labels':[watch['itab'][v-1] for v in columns],
                        'next_column':i32(pid,watch['correct']+4*n) if n<watch['dimensions']['NKMAX'] else None}
                    ptrace(6,pid,904,0)
                elif watch and dr6&14:
                    n=watch['initial_count']
                    records.append({'DR6_watch_bits':dr6&14,'instruction_after_write_offset':hex(r.rip-base),
                        'row_count_now':i32(pid,watch['countaddr']),
                        'wrong_stride_next_value_now':i32(pid,watch['wrong']+4*n),
                        'correct_stride_next_value_now':i32(pid,watch['correct']+4*n),
                        'watched_wrong_column_written':bool(dr6&4),
                        'watched_correct_column_written':bool(dr6&8),'watched_row_count_written':bool(dr6&2)})
                    if len(records)>=c['maximum_write_events']:
                        ptrace(6,pid,904,1)
            elif sig==signal.SIGSEGV:
                faults.append({'signal':sig,'instruction_offset':hex(registers(pid).rip-base)});ptrace(6,pid,904,0)
    except BaseException:
        os.kill(pid,signal.SIGKILL);os.waitpid(pid,0);raise
    public={k:v for k,v in (watch or {}).items() if k not in ['countaddr','correct','wrong','itab']}
    checks={'entry_and_return_captured':bool(watch and final),
        'expected_native_labels_initial':bool(watch) and set(public['correct_initial_original_labels'])==set(c['expected_neighbor_labels']),
        'expected_native_labels_final':bool(final) and set(final['correct_original_labels'])==set(c['expected_neighbor_labels']),
        'initial_count_expected':bool(watch) and public['initial_count']==len(c['expected_neighbor_labels']),
        'final_count_expected':bool(final) and final['count']==len(c['expected_neighbor_labels']),
        'no_wrong_next_column_write_observed':not any(e['watched_wrong_column_written'] for e in records),
        'no_duplicate_counter_inflation_observed':not any(e['row_count_now']>len(c['expected_neighbor_labels']) for e in records),
        'final_columns_unique':bool(final) and len(final['correct_columns'])==len(set(final['correct_columns']))}
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,
        'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
        'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
        'watch':public,'final_at_IND_KINE_K_return':final,'write_events':records,'faults':faults,
        'checks':checks,'watched_row_native_gate_pass':all(checks.values()),
        'scope':'Same predeclared original node48151; native row and stride recomputed. Hardware watches through native builder return, maximum64write events. Scientific arrays and code unchanged by observer.',
        'all_other_rows_or_physics_qualified':False}
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'watched_row_gate_pass':all(checks.values()),'write_events':len(records),
        'initial':public.get('initial_count'),'final':final['count'] if final else None,
        'Engine_exit':result['Engine_exit_code']}),flush=True)


if __name__=='__main__':main()
