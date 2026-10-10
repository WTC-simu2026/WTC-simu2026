"""Fresh full SHA-256 audit of the immutable baseline saved before A14."""
import time
from run_aircraft_a14 import ROOT,OUT,read,dump,now,streamsha

assert not (OUT/'preservation_verification.json').exists()
start=time.perf_counter(); rows=read(OUT/'preservation_before.json')['files'];bad=[];size=0
for r in rows:
    p=ROOT/r['path'];size+=p.stat().st_size
    if p.stat().st_size!=r['bytes'] or streamsha(p)!=r['sha256']:bad.append(r['path'])
proof={'created_utc':now(),'pass':not bad,'files':len(rows),'bytes_hashed':size,'seconds':time.perf_counter()-start,'fresh_full_streaming_SHA256':True,'canonical_A12_baseline_inherited':True,'failures':bad,'old_solver_reruns':0,'archives_rescanned':False}
dump(OUT/'preservation_verification.json',proof);print(proof,flush=True);assert not bad
