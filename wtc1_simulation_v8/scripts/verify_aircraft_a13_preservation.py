"""Fresh streaming SHA-256 comparison of corrected immutable input baseline."""
import hashlib,time
from run_aircraft_a13 import ROOT,OUT,read,dump,now
start=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];bad=[];size=0
assert not (OUT/'preservation_verification.json').exists()
for r in rows:
    p=ROOT/r['path'];h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
    size+=p.stat().st_size
    if h.hexdigest()!=r['sha256'] or p.stat().st_size!=r['bytes']:bad.append(r['path'])
proof={'created_utc':now(),'pass':not bad,'files':len(rows),'bytes_hashed':size,'seconds':time.perf_counter()-start,'fresh_full_streaming_SHA256':True,'canonical_A12_baseline_applied':True,'failures':bad,'old_solver_reruns':0,'archives_rescanned':False}
dump(OUT/'preservation_verification.json',proof);print(proof,flush=True);assert not bad
