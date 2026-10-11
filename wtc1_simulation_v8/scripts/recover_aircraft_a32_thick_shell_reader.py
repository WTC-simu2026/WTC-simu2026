"""Resume the unchanged Starter-only branch; never rerun completed HEPH controls."""
from run_aircraft_a32 import *

def main():
    guard();dest=OUT/'native_case_summary_after_reader_recovery.json';assert not dest.exists();original=OUT/'runner_before_thick_shell_reader_fix.py';assert original.exists();d=OUT/'w0'/PATCH[0];g=read(d/'generation.json');n=g['name'];assert read(d/'starter_gate.json')['pass'] and not (d/'engine.log').exists();pin={p.name:streamsha(p) for p in [d/(n+'_0000.rad'),d/(n+'_0001.rad'),d/(n+'_0000_0001.rst')]};en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    dump(OUT/'thick_shell_reader_recovery.json',{'created_utc':now(),'original_source':rel(original),'original_sha256':streamsha(original),'fixed_source_sha256':streamsha(Path(__import__('run_aircraft_a32').__file__)),'old_failure':read(OUT/'w0_case_summary.json')['stopped'],'change':'Read TYPE21five-column Isolid/Ismstr/Icpre/NPT/ICONTROL table, rather than nonexistent TYPE6nine-column table. Values/gates on actual thick-shell flags preserved, native inputs unchanged. Co-rotation follows documented HSEPH formulation; unavailable Iframe numeric field not invented.','untouched_deck_and_restart_sha256':pin,'previous_native_solver_reruns':0})
    native_frame(d,n,'w0');assert all(streamsha(d/k)==v for k,v in pin.items());assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',600,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',600,en);review(d,n);rows=[];stopped=None
    for cid in read(CFG)['branches']['w0']['cases']:
        q=OUT/'w0'/cid
        if q.exists():assert (q/'review.json').exists(),'No rerun of incomplete branch'
        else:run_one('w0',cid)
        r=read(q/'review.json');rows.append(r)
        if cid.startswith('PATCH') and not r['pass']:stopped={'case':cid,'reason':'original affine/full-balance gate failed'};break
    r={'created_utc':now(),'branch':'w0','cases':rows,'stopped':stopped,'declared_controls':15,'completed_controls':len(rows),'old_Starter_only_failure_retained':True,'whole_insertion_ready':False};dump(OUT/'w0_case_summary_after_reader_recovery.json',r);dump(dest,{'created_utc':now(),'branches':[r,read(OUT/'w1_case_summary.json')],'old_campaign_summary_retained':True,'whole_insertion_ready':False,'old_native_solver_reruns':0,'objective1_complete':False});print({'recovered_w0_completed':len(rows),'stopped':stopped},flush=True)

if __name__=='__main__':main()
