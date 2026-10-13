"""Predeclare native allocator/descriptor identity after the scratch hypothesis failed."""
from probe_aircraft_a57 import ROOT,OUT,read,dump,sha,now,rel,engine
from build_aircraft_a54_graph import linux
from pathlib import Path
import probe_aircraft_a54 as launcher
import shutil,json,subprocess

def main():
    candidate,binary=engine();source=OUT/'ACTIVE_COHESIVE_SCRATCH_WATCH';old=read(source/'instrumentation_config.json')
    d=OUT/'ACTIVE_COHESIVE_ALLOCATION_TRACE';assert not d.exists();d.mkdir();name=old['Engine_card'].removesuffix('_0001.rad')
    for p in [source/(name+'_0000_0001.rst'),source/(name+'_0001.rad')]:shutil.copy2(p,d/p.name)
    symbols={l.split()[-1]:int(l.split()[0],16) for l in (OUT/'engine_symbols.txt').read_text().splitlines() if len(l.split())>=3}
    names=['__my_alloc_impl_idx4_mod_MOD_my_alloc_double_1d','__my_alloc_impl_idx4_mod_MOD_my_alloc_pdouble_1d'];evidence=[]
    for j,symbol in enumerate(names):
        result=subprocess.run(['wsl.exe','-d','Ubuntu','--','objdump','-d','--disassemble='+symbol,linux(binary)],capture_output=True,check=True,timeout=30)
        p=d/f'allocator_{j}.disassembly.txt';p.write_bytes(result.stdout);evidence.append({'path':rel(p),'sha256':sha(p),'symbol':symbol})
        text=result.stdout.decode();assert any(all(f'{off}(%{reg})' in text for off in ['0x30','0x38','0x10']) for reg in ['rbp','rbx'])
    observer=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a56_allocation_linux.py'
    c={**old,'created_utc':now(),'directory':linux(d),'allocator_offsets':[symbols[n] for n in names],'maximum_allocator_calls':8192,'ABI_evidence':evidence,'observer_sha256':sha(observer),'purpose':'Verify actual original SMSTR capacity >=21*NEL and exact SAV pointer identity on the approved A57 binary; keep loaded physical gates separate.'}
    dump(OUT/'allocation_trace_predeclaration.json',c);instrument=d/'instrumentation_config.json';dump(instrument,c)
    launcher.engine=engine;print(json.dumps(launcher.run_native(d,name,observer,instrument)),flush=True)

if __name__=='__main__':main()
