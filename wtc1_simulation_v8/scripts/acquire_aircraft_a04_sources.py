"""Reacquire only missing declared primary copies; existing source bytes never overwritten."""
import hashlib,urllib.request
from run_aircraft_a04 import ROOT,OUT,read,sha
if __name__=='__main__':
    records=read(ROOT/'wtc1_simulation_v8/input/aircraft_a04_sources/acquisition.json')+[read(ROOT/'wtc1_simulation_v8/input/aircraft_a04_sources/acquisition_boeing.json')]
    for r in records:
        p=ROOT/r['path'];assert p.parent==ROOT/'wtc1_simulation_v8/input/aircraft_a04_sources'
        if p.exists():assert sha(p)==r['sha256'];continue
        request=urllib.request.Request(r['url'],headers={'User-Agent':'WTC-simu2026 reproducibility source fetch'})
        with urllib.request.urlopen(request,timeout=60) as f:data=f.read()
        assert hashlib.sha256(data).hexdigest()==r['sha256'], 'Source changed; preserve version evidence, do not replace recorded hash.'
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
        print({'acquired':r['path'],'redistribution':'external source excluded'})
