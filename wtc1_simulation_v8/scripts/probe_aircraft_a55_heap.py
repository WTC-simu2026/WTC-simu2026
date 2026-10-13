"""Predeclare the allocator-header measurement after the native SIGABRT stack."""
from probe_aircraft_a55 import ROOT,OUT,read,dump,sha,now,rel,engine
from build_aircraft_a54_graph import linux
from pathlib import Path
import shutil,json,subprocess
import probe_aircraft_a54 as launcher


def main():
    candidate,binary=engine();source=OUT/'active_dof_controls_r1/w0/NORMAL_L10';name=read(source/'generation.json')['name']
    symbols={line.split()[-1]:int(line.split()[0],16) for line in (ROOT/'wtc1_simulation_v8/output/aircraft_a54/engine_symbols.txt').read_text().splitlines() if len(line.split())>=3}
    d=OUT/'ACTIVE_COHESIVE_HEAP_WATCH';assert not d.exists();d.mkdir();files=[]
    for path in [source/(name+'_0000_0001.rst'),source/(name+'_0001.rad')]:
        files.append({'path':rel(path),'sha256':sha(path),'bytes':path.stat().st_size});shutil.copy2(path,d/path.name)
    observer=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a55_heap_linux.py'
    disassembly=subprocess.run(['wsl.exe','-d','Ubuntu','--','objdump','-d','--start-address=0xb20280','--stop-address=0xb202d0',linux(binary)],capture_output=True,check=True,timeout=30)
    (d/'NODREAC_free_call.disassembly.txt').write_bytes(disassembly.stdout)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A55','seed':1102080,'random_draws':0,
        'source_files':files,'binary':linux(binary),'binary_sha256':sha(binary),'directory':linux(d),'Engine_card':name+'_0001.rad',
        'NODREAC_symbol_offset':symbols['__threac_mod_MOD_nodreac'],'free_call_offset':int('b202a1',16),
        'maximum_events':64,'observer_sha256':sha(observer),'CPU_threads':1,'GPU':False,'cap_s':180,
        'purpose':'Observe descriptor allocation and size-header writes before the specific failing NODREAC free call. Do not assume the corrupting writer or cohesive mechanism.',
        'no_process_mechanical_or_instruction_patch':True,'native_signal_forwarded':True,'new_physical_duration_credit':0}
    dump(OUT/'heap_watch_predeclaration.json',config);instrument=d/'instrumentation_config.json';dump(instrument,config)
    launcher.engine=engine;print(json.dumps(launcher.run_native(d,name,observer,instrument)),flush=True)


if __name__=='__main__':main()
