"""Preserve w1 Starter failure, fix reserved blanks in TYPE20 before new cases."""
from run_aircraft_a26 import *
import ast

def main():
    source=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a26_solidshell.py';target=ROOT/'wtc1_simulation_v8/scripts/test_aircraft_a26_solidshell_w2.py';cfg=ROOT/'wtc1_simulation_v8/data/aircraft_a26_solidshell_w2.json';assert not target.exists() and not cfg.exists();h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_solidshell_w2.json',h)
    failed=OUT/'w1/FREE_ROTATION_X_N12';assert read(failed/'starter_gate.json')['warnings']==1 and not (failed/'engine.log').exists();c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a26_solidshell.json');c.update(revision='w2',declared_utc=now(),previous_cfg_sha256=streamsha(ROOT/'wtc1_simulation_v8/data/aircraft_a26_solidshell.json'),format_correction='TYPE20 reserved columns3/4 and unused Iint for HA8 must be blank, not numeric zero. Preserve warning100214 w1; no w1 Engine ran. Geometry/material/solver thresholds unchanged.');dump(cfg,c);dump(OUT/'solidshell_w2_guard.json',{'created_utc':now(),'sha256':streamsha(cfg),'before_new_native_solvers':True})
    s=source.read_text(encoding='utf-8');audit=[]
    for old,new in [("aircraft_a26_solidshell.json","aircraft_a26_solidshell_w2.json"),("OUT/'solidshell_guard.json'","OUT/'solidshell_w2_guard.json'"),("OUT/'w1'","OUT/'w2'"),("OUT/'native_case_summary_w1.json'","OUT/'native_case_summary_w2.json'"),("OUT/'solidshell_review_derivation.json'","OUT/'solidshell_w2_review_derivation.json'"),("ii(14,4,0,0,10,222,0)+' '*10+ff(0)","ii(14,4)+' '*20+ii(10,222)+' '*20+ff(0)")]:
        count=s.count(old);assert count>0,old;s=s.replace(old,new);audit.append({'old':old,'new':new,'count':count})
    ast.parse(s);target.write_text(s,encoding='utf-8',newline='\n');dump(OUT/'solidshell_w2_derivation.json',{'created_utc':now(),'source':rel(source),'source_sha256':streamsha(source),'target':rel(target),'target_sha256':streamsha(target),'changes':audit,'w1_Starter_failure_preserved':True,'native_solver_reruns':0});print({'A26_w2_declared':True,'format_only':True},flush=True)

if __name__=='__main__':main()
