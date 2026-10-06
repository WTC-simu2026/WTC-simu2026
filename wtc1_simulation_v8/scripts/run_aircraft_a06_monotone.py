"""A06 smooth monotone discriminator, fresh native state and unchanged material."""
import json
from pathlib import Path
import numpy as np
import run_aircraft_a06 as r
from run_aircraft_a04 import blocks
from run_aircraft_a02 import ROOT,read,dump,sha,rel,now,ff,execute,RUNTIME,harness
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a06_monotone_predeclaration.json'
def main():
    out=r.OUT/'m1';assert not out.exists();out.mkdir();c=read(CFG)
    dump(out/'declaration_guard.json',{'sha256':sha(CFG),'created_utc':now(),'before_any_new_solver':True,'cyclic_review_sha256':sha(r.OUT/'witness_review.json')})
    for case in c['cases']:
        d,n=r.generate_witness('m1',case)
        b=blocks((d/(n+'_0000.rad')).read_text(encoding='utf-8').splitlines());ts=np.linspace(0,1,10001);ep=.12*(3*ts**2-2*ts**3);lines=[]
        for q in b:
            if q[0] in ['/FUNCT/90','/FUNCT/91']:
                val=case['L_mm']*np.expm1(ep if q[0].endswith('90') else -.25*ep);q=q[:2]+[ff(t,v) for t,v in zip(ts,val)]+[ff(1.01,val[-1])]
            lines+=q
        (d/(n+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
        p=d/(n+'_0001.rad');text=p.read_text(encoding='utf-8');text=text.replace('/TFILE/4\n'+ff(.001),'/TFILE/4\n'+ff(c['history_dt_ms']));p.write_text(text,encoding='utf-8')
        g=read(d/'generation.json');g.update(supplementary_configuration=rel(CFG),supplementary_configuration_sha256=sha(CFG),generator_sha256=sha(Path(__file__)),path='smooth monotone log strain .12*(3u^2-2u^3)');dump(d/'generation.json',g)
        if r.start_engine(d,n):assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',90,r.env())
    dump(out/'harness_after.json',harness())
if __name__=='__main__':main()
