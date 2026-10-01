"""Analytical reference checks independent of saved solver histories."""
import json
import numpy as np
from audit_impact_i02i_material import reference, ROOT, CFG, dump

def main():
    E=1000.; checks={}
    s,p=reference([0.,.05,.1,.15,.2,.15,.2],[[0.,100.],[1.,100.]],E)
    checks['EPP_exact_stress_and_permanent_strain']=np.allclose(s,[0,50,100,100,100,50,100],rtol=0,atol=1e-10) and np.allclose(p,[0,0,0,.05,.1,.1,.1],rtol=0,atol=1e-10)
    s,p=reference([.22,.12,.22],[[0.,100.],[1.,1100.]],E)
    checks['linear_hardening_closed_solution']=np.allclose(s,[160,60,160],rtol=0,atol=1e-10) and np.allclose(p,[.06,.06,.06],rtol=0,atol=1e-10)
    cfg=json.loads(CFG.read_text()); cfgE=cfg['material']['young_modulus_mpa']
    for kind in ['engineering','true_total']:
        e=np.array(cfg['material']['source_total_strain'][1:]); s=np.array(cfg['material']['source_stress_mpa'][1:])
        if kind=='engineering': s=s*(1+e); e=np.log1p(e)
        pp=e-s/cfgE; curve=[[0.,346.66635 if kind=='engineering' else 345.]]+list(map(list,zip(pp,s)))+[[1.,s[-1]]]
        ss,ps=reference(e,curve,cfgE)
        checks[kind+'_source_knots_exact']=np.allclose(ss,s,rtol=0,atol=1e-9) and np.allclose(ps,pp,rtol=0,atol=1e-12)
    target=ROOT/'wtc1_simulation_v8/output/impact_i02i_material/reference_checks.json'
    if target.exists(): raise RuntimeError('Existing verification preserved')
    dump(target,{'checks':checks,'pass':all(checks.values()),'scope':'closed EPP/hardening cycles and source knots; not experimental agreement'})
    print(json.dumps(checks)); assert all(checks.values())

if __name__=='__main__': main()
