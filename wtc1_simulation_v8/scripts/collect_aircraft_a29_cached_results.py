"""Collect completed native w4 results after a summary-path error; no solver rerun."""
from run_aircraft_a29 import *

def main():
    dest=OUT/'native_case_summary_w4.json';assert not dest.exists();cfg=CFG.with_name('aircraft_a29_law12.json');assert streamsha(cfg)==read(OUT/'law12_guard.json')['sha256'];cases=[];pins=[]
    for cid in read(cfg)['cases']:
        d=OUT/'w4'/cid;q=d/'review.json';r=read(q);assert r['checks']['normal_termination'] and read(d/'native_frame_gate.json')['pass'];cases.append(r);pins.append({'path':rel(q),'sha256':streamsha(q)})
    assert len(cases)==15;dump(dest,{'created_utc':now(),'cases':cases,'whole_insertion_ready':False,'summary_repair_only':True,'native_reruns':0});dump(OUT/'summary_path_correction.json',{'created_utc':now(),'original_generator':rel(Path(__file__).with_name('test_aircraft_a29_law12.py')),'original_generator_sha256':streamsha(Path(__file__).with_name('test_aircraft_a29_law12.py')),'error':'All15native cases completed and reviewed; final summary attempted to read w2 instead of w4. New collector reads only cached w4 reviews; old generator and outputs preserved.','native_result_pins':pins,'native_reruns':0});print({'cached_w4_results_collected':15,'native_reruns':0},flush=True)

if __name__=='__main__':main()
