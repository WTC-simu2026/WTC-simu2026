"""Predeclare a bounded observation of the newly allocated native scratch buffer."""
from probe_aircraft_a56 import ROOT,OUT,read,dump,sha,now,rel,engine
from build_aircraft_a54_graph import linux
from pathlib import Path
import probe_aircraft_a54 as launcher
import shutil,json

def main():
    candidate,binary=engine();source=ROOT/'wtc1_simulation_v8/output/aircraft_a55/ACTIVE_COHESIVE_HEAP_WATCH_R2'
    name=read(source/'instrumentation_config.json')['Engine_card'].removesuffix('_0001.rad')
    d=OUT/'ACTIVE_COHESIVE_SCRATCH_WATCH';assert not d.exists();d.mkdir();files=[]
    for p in [source/(name+'_0000_0001.rst'),source/(name+'_0001.rad')]:
        files.append({'path':rel(p),'sha256':sha(p)});shutil.copy2(p,d/p.name)
    symbols={line.split()[-1]:int(line.split()[0],16) for line in (OUT/'engine_symbols.txt').read_text().splitlines() if len(line.split())>=3}
    observer=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a56_scratch_linux.py'
    config={'created_utc':now(),'iteration':'AIRCRAFT-A56','seed':1102081,'random_draws':0,'source_files':files,'binary':linux(binary),'binary_sha256':sha(binary),'directory':linux(d),'Engine_card':name+'_0001.rad','NODREAC_symbol_offset':symbols['__threac_mod_MOD_nodreac'],'SRCOORK_symbol_offset':symbols['srcoork_'],'SRCOORK_arguments':read(source/'instrumentation_config.json')['SRCOORK_arguments'],'maximum_events':64,'observer_sha256':sha(observer),'CPU':1,'GPU':False,'cap_s':180,'purpose':'Observe TYPE43/NEL1 scratch function return and raw header stability with the exact authorized new binary. No physical gate weakened; raw allocation size is not a descriptor capacity proof.'}
    dump(OUT/'scratch_watch_predeclaration.json',config);instrument=d/'instrumentation_config.json';dump(instrument,config)
    launcher.engine=engine;print(json.dumps(launcher.run_native(d,name,observer,instrument)),flush=True)

if __name__=='__main__':main()
