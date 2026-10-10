"""One full SHA-256 pass over protected predecessors; no archive rescan."""
import time
from run_aircraft_a17 import ROOT,OUT,read,dump,now,guard,streamsha
def main():
    guard();dst=OUT/'preservation_verification.json';assert not dst.exists();start=time.perf_counter();bad=[];rows=read(OUT/'preservation_before.json')['files']
    for i,r in enumerate(rows):
        p=ROOT/r['path']
        if not p.is_file() or p.stat().st_size!=r['bytes'] or streamsha(p)!=r['sha256']:bad.append(r['path'])
        if (i+1)%2000==0:print({'old_files_checked':i+1,'failures':len(bad)},flush=True)
    v={'created_utc':now(),'pass':not bad,'files':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows),'seconds':time.perf_counter()-start,'failures':bad,'old_solver_reruns':0,'archive_rescanned':False};dump(dst,v);assert v['pass'];print({k:v[k] for k in ['pass','files','bytes_hashed','seconds']},flush=True)
if __name__=='__main__':main()
