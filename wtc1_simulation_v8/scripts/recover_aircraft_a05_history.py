"""Read the saved one-row observer when the native converter crashes.

No synthetic step and no Engine rerun. Match every main binary frame with
the working native T01 CSV before using the same record schema on T02.
"""
import argparse,csv,struct,os
import numpy as np
from run_aircraft_a05 import OUT,ROOT,RUNTIME,read,dump,sha,rel,now,execute
from audit_aircraft_a04 import histories

def records(path):
    b=path.read_bytes();pos=0;r=[]
    while pos<len(b):
        n=struct.unpack('>i',b[pos:pos+4])[0]
        assert 0<=n<100000000 and pos+n+8<=len(b)
        assert struct.unpack('>i',b[pos+n+4:pos+n+8])[0]==n
        r.append(b[pos+4:pos+4+n]);pos+=n+8
    return r

def recover(case,revision='r3'):
    d=OUT/revision/case;n=read(d/'generation.json')['name'];o=d/'observer'
    csvpath=d/(n+'T01.csv')
    if not csvpath.exists():
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',90,os.environ.copy())
    H=histories(csvpath);keys=list(H);v=np.column_stack(list(H.values()));r=records(d/(n+'T01'))
    # One global record followed by one record per TH group and a time record.
    ngroups=7;nr=ngroups+2;header=len(r)-len(v)*nr;assert header>0
    frames=[r[header+i*nr:header+(i+1)*nr] for i in range(len(v))]
    sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88
    assert all([len(q) for q in f]==sizes for f in frames)
    native=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames])
    assert native.shape==v.shape and np.allclose(native,v,rtol=6e-7,atol=1e-12)
    ro=records(o/(n+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes
    end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]])
    assert end[0]>v[-1,0] and np.all(np.isfinite(end))
    dst=o/(n+'T02_recovered.csv');assert not dst.exists()
    with dst.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(keys);w.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'created_utc':now(),'pass':True,'native_converter_failed':True,'binary_fortran_records_big_endian_float32':True,'all_main_frames_matched_working_native_csv':len(v),'CSV_rounding_relative_allowance':6e-7,'records_per_frame':nr,'payload_sizes_bytes':sizes,'one_observer_row_only':True,'end_time_ms':float(end[0]),'synthetic_step_added':False,'solver_rerun':False,'native_inputs':[{'path':rel(p),'sha256':sha(p)} for p in [d/(n+'T01'),o/(n+'T02'),csvpath]],'recovered_csv_sha256':sha(dst)})
    dump(d/'execution_summary.json',{'main_normal_termination':True,'verified_end_possible':True,'partial_data_only':False,'native_T02_converter_crash_preserved':True,'T02_binary_first_row_recovered':True})
    print({'recovered':case,'end_ms':float(end[0]),'main_frames_checked':len(v)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('--revision',default='r3');a=p.parse_args();recover(a.case,a.revision)
