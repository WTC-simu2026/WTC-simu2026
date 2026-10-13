"""Bounded native helper semantics and TYPE2 bindings in our corrected Engine child."""
from trace_aircraft_a48_linux import ptrace, registers, memory, u64, i32
from trace_aircraft_a52_linux import binding
from pathlib import Path
import hashlib
import json
import os
import signal
import struct
import sys
import time


def arg(pid, r, index):
    if index <= 6:
        return [r.rdi,r.rsi,r.rdx,r.rcx,r.r8,r.r9][index-1]
    return u64(pid, r.rsp+8*(index-6))


def ints(pid, pointer, count):
    if not count:
        return []
    data = b''.join(memory(pid,pointer+i,min(8192,count*4-i)) for i in range(0,count*4,8192))
    return list(struct.unpack('<'+'i'*count,data))


def main():
    c = json.loads(Path(sys.argv[1]).read_text())
    binary = Path(c['binary']); d = Path(c['directory'])
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == c['binary_sha256']
    os.chdir(d); output = d/'graph_binding_trace_result.json'; assert not output.exists()
    start = time.monotonic(); pid = os.fork()
    if pid == 0:
        try:
            ptrace(0,0)
            fd = os.open('engine.log', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
            os.dup2(fd,1); os.dup2(fd,2); os.close(fd)
            os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
        except BaseException:
            os._exit(77)
    _, status = os.waitpid(pid,0); assert os.WIFSTOPPED(status)
    maps = [line.split() for line in Path(f'/proc/{pid}/maps').read_text().splitlines() if line.endswith(str(binary))]
    base = min(int(row[0].split('-')[0],16)-int(row[2],16) for row in maps)
    add = base+c['symbols']['type2_kin_add_']
    ind = base+c['symbols']['ind_kine_k_']
    bind0 = base+c['symbols']['i2updk0_']; bind1 = base+c['symbols']['i2updk1_']
    slots = [add,0,ind,bind0]
    for index,address in enumerate(slots):
        ptrace(6,pid,848+8*index,address)
    def enable():
        ptrace(6,pid,904,sum(1<<(2*i) for i,value in enumerate(slots) if value))
    enable()
    deliver = 0; pending = None; graph = []; calls = []; faults = []
    phase_counts = {0:0,1:0}; contexts = 0; event_count = 0
    try:
        while True:
            ptrace(7,pid,0,deliver); _,status=os.waitpid(pid,0)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                break
            sig=os.WSTOPSIG(status); deliver=sig
            if sig==signal.SIGTRAP:
                deliver=0; r=registers(pid); ptrace(6,pid,896,0); event_count+=1
                assert event_count <= 4096
                if r.rip==ind:
                    contexts+=1
                    slots[0]=add; slots[2]=bind1
                    ptrace(6,pid,848,add); ptrace(6,pid,864,bind1); enable()
                elif r.rip==add:
                    assert pending is None
                    values=[arg(pid,r,i) for i in range(1,10)]
                    row,node,first,nnmax,nkmax,bound=[i32(pid,p) for p in values[:6]]
                    assert first in [0,1] and row>0 and 0<node<=c['maximum_nodes']
                    nrow,ordinary,main=values[6:]
                    main_region=(row<=bound) if first else (row>bound)
                    stride=nkmax if main_region else nnmax
                    column=row if first or not main_region else row-bound
                    table=main if main_region else ordinary
                    pointer=table+4*stride*(column-1)
                    count_pointer=nrow+4*(row-1); count=i32(pid,count_pointer)
                    assert 0<=count<=stride<=4096
                    columns=ints(pid,pointer,count)
                    pending={'phase_main_first':first,'row':row,'neighbor':node,
                        'NNMAX':nnmax,'NKMAX':nkmax,'boundary':bound,'main_region':main_region,
                        'expected_table':'ICOKM' if main_region else 'ICOK','expected_column':column,
                        'count_pointer':count_pointer,'buffer_pointer':pointer,'stride':stride,
                        'count_before':count,'columns_before':columns,'neighbor_already_present':node in columns}
                    slots[1]=u64(pid,r.rsp); ptrace(6,pid,856,slots[1]); enable()
                elif slots[1] and r.rip==slots[1]:
                    assert pending is not None
                    count=i32(pid,pending['count_pointer']); assert 0<=count<=pending['stride']
                    columns=ints(pid,pending['buffer_pointer'],count)
                    expected=set(pending['columns_before'])|{pending['neighbor']}
                    checks={'neighbor_set_matches_native_input_union':set(columns)==expected,
                        'counter_matches_unique_neighbor_count':count==len(expected),
                        'no_duplicate_columns':len(columns)==len(set(columns)),
                        'duplicate_does_not_inflate_count':not pending['neighbor_already_present'] or count==pending['count_before']}
                    graph.append({k:v for k,v in pending.items() if not k.endswith('_pointer')}|
                        {'count_after':count,'columns_after':columns,'checks':checks,'pass':all(checks.values())})
                    phase=pending['phase_main_first']; phase_counts[phase]+=1
                    pending=None; slots[1]=0; ptrace(6,pid,856,0)
                    if phase_counts[phase]>=c['helper_calls_per_phase']:
                        slots[0]=0; ptrace(6,pid,848,0)
                    enable()
                elif r.rip in [bind0,bind1]:
                    calls.append(binding(pid,r,0 if r.rip==bind0 else 1,c['maximum_nodes']))
                    assert len(calls)<=512
            elif sig==signal.SIGSEGV:
                faults.append({'signal':sig,'instruction_offset':hex(registers(pid).rip-base)})
                ptrace(6,pid,904,0)
    except BaseException:
        os.kill(pid,signal.SIGKILL)
        os.waitpid(pid,0)
        raise
    observed=bool(graph) and all(row['pass'] for row in graph)
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-start,
        'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
        'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
        'IND_KINE_K_contexts':contexts,'helper_calls_by_phase':phase_counts,
        'graph_helper_observations':graph,'graph_semantics_on_observed_calls_pass':observed,
        'helper_entry_inconclusive_if_zero_calls':not bool(graph),
        'TYPE2_calls':calls,'faults':faults,'binary_sha256':c['binary_sha256'],
        'scope':'Owned child, four hardware instruction breakpoints and bounded integer reads only. Native helper before/after neighbor-set oracle and existing TYPE2 binding reader. No instructions or mechanical process arrays altered.',
        'all_global_graph_writes_qualified':False,'whole_impact_qualified':False}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'helper_calls_by_phase':phase_counts,'observed_semantics_pass':observed,
        'TYPE2_calls':len(calls),'Engine_exit_code':result['Engine_exit_code'],'faults':len(faults)}),flush=True)


if __name__=='__main__':main()
