"""Specific compiled-clone ABI observer; before/after set oracle, no native data writes."""
from trace_aircraft_a48_linux import ptrace,registers,memory,u64,i32
from trace_aircraft_a54_graph_linux import ints
from pathlib import Path
import hashlib,json,os,signal,sys,time


def main():
    c=json.loads(Path(sys.argv[1]).read_text());binary=Path(c['binary']);d=Path(c['directory'])
    assert hashlib.sha256(binary.read_bytes()).hexdigest()==c['binary_sha256']
    os.chdir(d);output=d/'optimized_add_trace_result.json';assert not output.exists()
    started=time.monotonic();pid=os.fork()
    if pid==0:
        try:
            ptrace(0,0);fd=os.open('engine.log',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.dup2(fd,1);os.dup2(fd,2);os.close(fd)
            os.execv(str(binary),[str(binary),'-i',c['Engine_card']])
        except BaseException:os._exit(77)
    _,status=os.waitpid(pid,0);assert os.WIFSTOPPED(status)
    maps=[l.split() for l in Path(f'/proc/{pid}/maps').read_text().splitlines() if l.endswith(str(binary))]
    base=min(int(l[0].split('-')[0],16)-int(l[2],16) for l in maps)
    targets=[base+c['sizing_clone_offset'],base+c['building_clone_offset']]
    slots=[targets[0],targets[1],0]
    for index,address in enumerate(slots):ptrace(6,pid,848+8*index,address)
    def enable():ptrace(6,pid,904,sum(1<<(2*i) for i,value in enumerate(slots) if value))
    enable();deliver=0;pending=None;records=[];counts=[0,0];faults=[]
    try:
        while True:
            ptrace(7,pid,0,deliver);_,status=os.waitpid(pid,0)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):break
            sig=os.WSTOPSIG(status);deliver=sig
            if sig==signal.SIGTRAP:
                deliver=0;r=registers(pid);ptrace(6,pid,896,0)
                if r.rip in targets:
                    assert pending is None
                    phase=targets.index(r.rip);first=1 if phase==0 else 0
                    # Verified for this exact optimized binary: five INTEGER values
                    # in edi/esi/edx/ecx/r8d, then NROW pointer r9 and two stack pointers.
                    row,node,nnmax,nkmax,bound=[value&0xffffffff for value in [r.rdi,r.rsi,r.rdx,r.rcx,r.r8]]
                    nrow=r.r9;ordinary=u64(pid,r.rsp+8);main=u64(pid,r.rsp+16)
                    assert 0<row<=c['maximum_nodes'] and 0<node<=c['maximum_nodes']
                    main_region=(row<=bound) if first else (row>bound)
                    stride=nkmax if main_region else nnmax
                    column=row if first or not main_region else row-bound
                    pointer=(main if main_region else ordinary)+4*stride*(column-1)
                    count_pointer=nrow+4*(row-1);n=i32(pid,count_pointer)
                    assert 0<=n<=stride<=4096
                    columns=ints(pid,pointer,n)
                    pending={'phase':phase,'sizing_main_first':bool(first),'row':row,'neighbor':node,
                        'boundary':bound,'NNMAX':nnmax,'NKMAX':nkmax,'main_region':main_region,
                        'table':'ICOKM' if main_region else 'ICOK','column':column,
                        'count_before':n,'columns_before':columns,'duplicate':node in columns,
                        'count_pointer':count_pointer,'buffer_pointer':pointer,'stride':stride}
                    slots[2]=u64(pid,r.rsp);ptrace(6,pid,864,slots[2]);enable()
                elif slots[2] and r.rip==slots[2]:
                    assert pending is not None
                    n=i32(pid,pending['count_pointer']);assert 0<=n<=pending['stride']
                    columns=ints(pid,pending['buffer_pointer'],n)
                    expected=set(pending['columns_before'])|{pending['neighbor']}
                    checks={'after_set_equals_before_union_input':set(columns)==expected,
                        'count_equals_unique_neighbors':n==len(expected),
                        'columns_unique':len(columns)==len(set(columns)),
                        'duplicate_keeps_count':not pending['duplicate'] or n==pending['count_before']}
                    records.append({k:v for k,v in pending.items() if not k.endswith('_pointer')}|
                        {'count_after':n,'columns_after':columns,'checks':checks,'pass':all(checks.values())})
                    phase=pending['phase'];counts[phase]+=1;pending=None
                    slots[2]=0;ptrace(6,pid,864,0)
                    if counts[phase]>=c['calls_per_phase']:
                        slots[phase]=0;ptrace(6,pid,848+8*phase,0)
                    enable()
            elif sig==signal.SIGSEGV:
                faults.append({'signal':sig,'instruction_offset':hex(registers(pid).rip-base)});ptrace(6,pid,904,0)
    except BaseException:
        os.kill(pid,signal.SIGKILL);os.waitpid(pid,0);raise
    regions={}
    for record in records:
        key=('sizing' if record['phase']==0 else 'building')+('_main' if record['main_region'] else '_ordinary')
        regions[key]=regions.get(key,0)+1
    checks={'both_phases_observed':all(count>0 for count in counts),
        'all_native_set_operations_pass':bool(records) and all(record['pass'] for record in records),
        'duplicates_observed':any(record['duplicate'] for record in records),
        'new_neighbors_observed':any(not record['duplicate'] for record in records),
        'four_storage_regions_observed':len(regions)==4}
    result={'created_epoch':time.time(),'wall_s':time.monotonic()-started,
        'Engine_exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,
        'Engine_terminal_signal':os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
        'calls_by_phase_sizing_building':counts,'region_counts':regions,
        'duplicate_calls':sum(record['duplicate'] for record in records),
        'new_neighbor_calls':sum(not record['duplicate'] for record in records),
        'observations':records,'checks':checks,'native_observed_graph_set_gate_pass':all(checks.values()),
        'faults':faults,'scope':'Compiled constprop/isra clones for this exact binary, ABI read from preserved disassembly. Before/after neighbor-set oracle uses the actual native input neighbor. Three hardware breakpoints only; no process array or instruction writes.',
        'whole_global_graph_or_physics_qualified':False}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ['calls_by_phase_sizing_building','region_counts','duplicate_calls','new_neighbor_calls','native_observed_graph_set_gate_pass','Engine_exit_code']}),flush=True)


if __name__=='__main__':main()
