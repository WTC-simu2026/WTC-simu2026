"""Predeclare a new read-only stack measurement of the failed active-DOF reproducer."""
from probe_aircraft_a55 import ROOT,OUT,read,dump,sha,now,rel,engine
from build_aircraft_a54_graph import linux
from pathlib import Path
import shutil,json
import probe_aircraft_a54 as launcher


def main():
    candidate,binary=engine();source=OUT/'active_dof_controls_r1/w0/NORMAL_L10';g=read(source/'generation.json');name=g['name']
    d=OUT/'ACTIVE_COHESIVE_ABORT_TRACE';assert not d.exists();d.mkdir()
    rows=[]
    for path in [source/(name+'_0000_0001.rst'),source/(name+'_0001.rad')]:
        rows.append({'path':rel(path),'sha256':sha(path),'bytes':path.stat().st_size});shutil.copy2(path,d/path.name)
    observer=ROOT/'wtc1_simulation_v8/scripts/trace_aircraft_a55_abort_linux.py'
    config={'created_utc':now(),'iteration':'AIRCRAFT-A55','seed':1102080,'random_draws':0,
        'source_files':rows,'binary':linux(binary),'binary_sha256':sha(binary),'directory':linux(d),'Engine_card':name+'_0001.rad',
        'observer_sha256':sha(observer),'maximum_stack_frames':24,'CPU_threads':1,'GPU':False,'cap_s':180,
        'purpose':'Read actual SIGABRT caller stack of the new active-DOF failed case, using existing readelf and ptrace; gdb is not installed and no software is installed.',
        'no_process_mechanical_or_instruction_patch':True,'native_signal_forwarded':True,'no_physical_duration_credit':True}
    dump(OUT/'abort_trace_predeclaration.json',config);instrument=d/'instrumentation_config.json';dump(instrument,config)
    launcher.engine=engine;print(json.dumps(launcher.run_native(d,name,observer,instrument)),flush=True)


if __name__=='__main__':main()
