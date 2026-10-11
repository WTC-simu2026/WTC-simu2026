"""Preserve Starter1574; declare automatic native strain choice without an Engine rerun."""
from run_aircraft_a29 import *

def main():
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_auto_strain.json',h);old=OUT/'w0/PATCH_NORMAL_X_N12';assert read(old/'starter_gate.json')['warnings']==1 and not (old/'engine.log').exists()
    cfg=ROOT/'wtc1_simulation_v8/data/aircraft_a29_auto_strain.json';target=Path(__file__).with_name('test_aircraft_a29_auto_strain.py');assert not cfg.exists() and not target.exists();c=read(CFG);c.update(revision='w1',declared_utc=now(),parent_configuration_sha256=streamsha(CFG),strain_choice='Starter1574 recommends Ismstr0 for Isolid18, resolving to native Ismstr2. Remains full geometric nonlinearities because no /DT/BRICK/CST switch is specified. Material fields, volume, density, orientation, motion and thresholds unchanged. Failed Starter input kept; original Engine never ran.');c['branches']['w1']={'property':'TYPE6 Isolid18 Ismstr0 native-auto (recommended2), Icpre3 Iframe2; geometry and source material card unchanged.'};dump(cfg,c);dump(OUT/'auto_strain_guard.json',{'created_utc':now(),'sha256':streamsha(cfg),'before_new_native_solvers':True})
    source=Path(__file__).with_name('run_aircraft_a29.py');s=source.read_text(encoding='utf-8');audit=[]
    for old,new in [('aircraft_a29_predeclaration.json','aircraft_a29_auto_strain.json'),("OUT/'declaration_guard.json'","OUT/'auto_strain_guard.json'"),("OUT/'w0'","OUT/'w1'"),("OUT/'native_case_summary.json'","OUT/'native_case_summary_w1.json'"),("OUT/'runner_derivation.json'","OUT/'runner_w1_derivation.json'"),("OUT/'review_derivation.json'","OUT/'review_w1_derivation.json'"),('ii(18,4)','ii(18,0)'),("n='A29_3D_'+cid","n='A29_W1_3D_'+cid")]:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);target.write_text(s,encoding='utf-8',newline='\n');dump(OUT/'auto_strain_derivation.json',{'created_utc':now(),'source':rel(source),'source_sha256':streamsha(source),'target':rel(target),'target_sha256':streamsha(target),'changes':audit,'native_old_solver_reruns':0,'no_original_Engine_ran':True});print({'A29_w1_declared':True,'Starter1574_retained':True,'expected_native_Ismstr':2},flush=True)

if __name__=='__main__':main()
