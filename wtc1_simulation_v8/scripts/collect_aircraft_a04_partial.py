"""Convert saved histories from a time-boxed run. No restart or claimed endpoint."""
import argparse,os
from run_aircraft_a04 import OUT,RUNTIME,CFG,read,execute,dump,sha,rel,now

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();d=OUT/'r1'/a.case;n=read(d/'generation.json')['name']
    assert read(d/'engine.log.execution.json')['exit_code']=='TIMEOUT'
    assert 'NORMAL TERMINATION' not in (d/'engine.log').read_text()
    assert not (d/'converter_T01.log').exists()
    pins={rel(q):sha(q) for q in d.iterdir() if q.is_file()}
    ok=execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',read(CFG)['execution']['converter_timeout_s'],os.environ.copy())
    dump(d/'partial_collection.json',{'created_utc':now(),'converter_success':ok,'termination':'TIMEOUT','verified_endpoint':False,'saved_window_only':True,'preconversion_files':pins,'restart_attempted':False})
    assert ok
    print({'partial_history_collected':a.case})
