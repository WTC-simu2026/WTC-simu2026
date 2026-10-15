"""Read-only recovery of the completed A91 coupon analysis; no native process."""
from pathlib import Path
import json, shutil
import numpy as np
import control_aircraft_a91_projected_null as original
from build_aircraft_a54_graph import rel, sha, now

OUT=original.OUT

def plain(v):
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {k:plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [plain(x) for x in v]
    return v

def dump(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:
        json.dump(plain(v),f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write('\n')

def main():
    cfg=original.read(original.CONTROL)
    assert sha(Path(original.__file__))==cfg['driver_sha256']
    before=original.read(OUT/'controls_execution_review.json')
    assert before['new_Engine']==3 and before['new_Starter']==0 and not before['whole_CHECK_executed']
    d=OUT/'native/COMPRESSION_RUPTURE_RECLOSE'
    assert original.read(d/'completion_review.json')['normal_termination']
    backup=OUT/'own_analysis_development_R0';backup.mkdir()
    failed=d/'loop_review.json'
    if failed.exists():shutil.copy2(failed,backup/'loop_review.partial.json');failed.unlink()
    shutil.copy2(d/'analysis_incomplete.json',backup/'analysis_incomplete.json')
    original.dump=dump
    case=next(c for c in cfg['cases'] if c['case']=='COMPRESSION_RUPTURE_RECLOSE')
    result=original.loop_review(case,d)
    review=original.read(d/'loop_review.json')
    dump(OUT/'controls_analysis_supplement_r1.json',{
        'created_utc':now(),'new_native_processes':0,'new_Starter':0,'new_Engine':0,
        'original_control_review_preserved':True,'original_analysis_exception_preserved':True,
        'repair':'Serialize numpy scalar booleans as Python booleans; all formulas and thresholds unchanged',
        'source_driver_sha256':sha(Path(original.__file__)),'reader':rel(Path(__file__)),
        'reader_sha256':sha(Path(__file__)),'result':result,
        'qualification':review['pass'],'whole_CHECK_condition_met':False})
    print(json.dumps(plain({'analysis_recovered':True,**result,
        'pre_force_N':review['pre_compression_force_N'],'post_force_N':review['post_reclosure_force_N'],
        'energy_residual_J':review['global_energy_residual_J_max']})),flush=True)

if __name__=='__main__':main()
