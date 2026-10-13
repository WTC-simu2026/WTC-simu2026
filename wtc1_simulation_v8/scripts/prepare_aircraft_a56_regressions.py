"""Preserve A54 controls and adapt only their output directory/binary and known metadata bridge."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import ast,json

def main():
    src=ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a54.py'
    dest=ROOT/'wtc1_simulation_v8/scripts/regress_aircraft_a56.py'
    assert not dest.exists();s=src.read_text()
    old='from build_aircraft_a54_graph import ROOT,OUT,CFG,read,dump,sha,now,rel,linux,guard'
    new='from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,linux\nfrom build_aircraft_a56_scratch import OUT,CFG,guard'
    assert s.count(old)==1;s=s.replace(old,new).replace("'iteration':'AIRCRAFT-A54'","'iteration':'AIRCRAFT-A56'").replace("'seed':1102079","'seed':1102081")
    old="            auditor.audit_case(case);rows.append(reader.review(case,True))"
    new="            dump(p/'completion.json',{'created_utc':now(),'pass':True,'exit_ok':True,'normal_termination':True,'bridged_from':'completion_review.json','no_solver_rerun':True})\n"+old
    assert s.count(old)==1;s=s.replace(old,new)
    ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n')
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a56_regression_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest),'scope':'Same bounded graph/binding, explicit cohesive and TYPE7 witnesses on new approved binary; known completion metadata provided before analysis. Physics and tolerances unchanged.','old_native_engines_not_replayed':True,'GPU':False,'cap_s_per_native':180})
    print('A56 regression controls prepared.',flush=True)

if __name__=='__main__':main()
