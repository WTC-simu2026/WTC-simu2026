"""Reuse pinned saved-field audit without writing to any predecessor iteration."""
import argparse,re
import numpy as np
import audit_aircraft_a05 as inherited
from run_aircraft_a06 import ROOT,CFG,OUT,PREV,read,dump,sha,rel,now
def main(case,revision='r1'):
    merged=read(ROOT/read(CFG)['inherited_configuration']);merged['iteration']='AIRCRAFT-A06';merged['audit_reuse_only']=True
    p=OUT/'inherited_field_audit_configuration.json'
    if not p.exists():dump(p,merged)
    inherited.OUT=OUT;inherited.CFG=p;inherited.PREV=PREV
    r=inherited.audit(revision,case);d=OUT/revision/case;z=np.load(d/'balance_history_SI.npz');mask=z['generated_energy_J']>1000
    r['maximum_local_energy_residual_fraction_above_1kJ']=float(np.max(abs(z['energy_residual_J'][mask])/z['generated_energy_J'][mask],initial=0))
    r['maximum_face_reference_strength_ratio']=max(s.get('radome_face_strength_ratio',0) for s in r['states']);r['first_saved_face_reference_exceeded_ms']=next((s['time_ms'] for s in r['states'] if s.get('radome_face_strength_ratio',0)>1),None)
    n=read(d/'generation.json')['name'];text=(d/(n+'_0000.out')).read_text(encoding='utf-8',errors='replace')
    vals=re.findall(r'SHELL (?:MEMBRANE|NUMERICAL) DAMPING[^=]*=\s*([\d.E+\-]+)',text)
    assert vals and all(abs(float(s)-1e-20)<1e-30 for s in vals),vals
    r.update(authoritative_A06_audit=True,explicit_negligible_native_metal_damping=True,native_property_damping_values=[float(s) for s in vals],failure_transfer_enabled=False,first_audit_sha256=sha(d/'audit.json'),inherited_audit_code=rel(ROOT/'wtc1_simulation_v8/scripts/audit_aircraft_a05.py'),inherited_code_sha256=sha(ROOT/'wtc1_simulation_v8/scripts/audit_aircraft_a05.py'))
    dump(d/'review.json',r);print({'case':case,'Jx_Ns':r['final_contact_impulse_Ns'][0],'residual_J':r['final_energy_residual_J'],'generated_J':r['final_generated_energy_J'],'local_energy_pass':r['checks']['energy_local_within_declared_limit']},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('--revision',default='r1');a=p.parse_args();main(a.case,a.revision)
