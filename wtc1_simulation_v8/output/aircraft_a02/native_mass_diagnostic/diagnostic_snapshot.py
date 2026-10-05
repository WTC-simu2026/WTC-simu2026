"""Whole-aircraft Starter-only isolation of reported CG, never an accepted flight model."""
import os,re,shutil
import numpy as np
from run_aircraft_a02 import ROOT,OUT,RUNTIME,read,dump,sha,rel,now,execute
from audit_aircraft_a02 import numbers_after
def main():
    d=OUT/'native_mass_diagnostic';assert not d.exists();d.mkdir();shutil.copy2(__file__,d/'diagnostic_snapshot.py')
    source=OUT/'r1/translation_dt080/A02_translation_dt080_0000.rad';lines=source.read_text().splitlines();out=[];i=0;removed=0
    while i<len(lines):
        if lines[i].startswith('/RBE3/'):
            i+=4;removed+=1;continue
        out.append(lines[i]);i+=1
    assert removed==368
    (d/'CG_only_0000.rad').write_text('\n'.join(out)+'\n',encoding='utf-8')
    dump(d/'predeclaration.json',{'created_utc':now(),'purpose':'Isolate native element mass moments from RBE3 effects on Starter reported CG; no Engine, no impact and no accepted uncoupled extra masses.',
        'source':rel(source),'source_sha256':sha(source),'only_card_change':'Remove exactly 368 RBE3 blocks. Keep coordinates/materials/elements/additional masses unchanged.',
        'incomplete_physical_model':True,'starter_only':True,'engine_jobs':0,'timeout_s':120})
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='2',KMP_STACKSIZE='400m')
    ok=execute(RUNTIME/'starter_win64.exe',['-i','CG_only_0000.rad','-np','1'],d,'starter.log',120,env)
    result={'created_utc':now(),'completed':ok,'engine_jobs':0,'accepted_as_flight_model':False}
    if ok:
        s=(d/'CG_only_0000.out').read_text();v=numbers_after(s,'TOTAL MASS AND MASS CENTER',4);iv=numbers_after(s,'TOTAL INERTIA',6)
        reference=read(OUT/'r1/mapping_audit.json')['reference_A01'];coupled=read(OUT/'r1/translation_dt080/audit.json') if (OUT/'r1/translation_dt080/audit.json').exists() else None
        result.update(native_mass_kg=v[0]*.001,native_CG_m=(np.array(v[1:])*.001).tolist(),native_CG_error_m=float(np.linalg.norm(np.array(v[1:])*.001-reference['CG_m'])),native_inertia_six_kg_m2=(np.array(iv)*1e-9).tolist(),
            warnings=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]),errors=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]))
        if coupled: result['coupled_minus_uncoupled_CG_m']=(np.array(coupled['native_CG_m'])-result['native_CG_m']).tolist()
    dump(d/'result.json',result);print(result)
if __name__=='__main__':main()
