"""Hash every preserved pre-A15 output without source archive scanning."""
import time
from run_aircraft_a15 import ROOT,OUT,read,dump,now,streamsha
assert not (OUT/'preservation_verification.json').exists()
t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];bad=[];size=0
for r in rows:
    p=ROOT/r['path'];size+=p.stat().st_size
    if p.stat().st_size!=r['bytes'] or streamsha(p)!=r['sha256']:bad.append(r['path'])
p={'created_utc':now(),'pass':not bad,'files':len(rows),'bytes_hashed':size,'seconds':time.perf_counter()-t,'fresh_full_SHA256':True,'failures':bad,'archives_rescanned':False,'old_solver_reruns':0};dump(OUT/'preservation_verification.json',p);print(p,flush=True);assert not bad
