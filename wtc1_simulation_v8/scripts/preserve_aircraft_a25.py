"""Verify prior pins while independent A25 controls run; no source archive rescan."""
from run_aircraft_a25 import *

def main():
    guard();p=OUT/'preservation_verification.json';assert not p.exists();rows=read(OUT/'preservation_before.json')['files'];t=time.perf_counter()
    for i,r in enumerate(rows):
        q=ROOT/r['path'];assert q.is_file() and q.stat().st_size==r['bytes'] and streamsha(q)==r['sha256'],r['path']
        if (i+1)%2000==0:print({'verified':i+1,'of':len(rows)},flush=True)
    dump(p,{'created_utc':now(),'pass':True,'files':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True});print({'preservation':True,'files':len(rows)},flush=True)

if __name__=='__main__':main()
