"""Adapt sealed controls for the new Engine without rerunning old binaries."""
from build_aircraft_a54_graph import ROOT,dump,sha,now,rel
import ast,json

def main():
    folder=ROOT/'wtc1_simulation_v8/scripts';rows=[]
    pairs=[('probe_aircraft_a56.py','probe_aircraft_a57.py'),('regress_aircraft_a56.py','regress_aircraft_a57.py'),('probe_aircraft_a56_scratch_watch.py','probe_aircraft_a57_scratch_watch.py'),('probe_aircraft_a56_allocation_r1.py','probe_aircraft_a57_allocation.py')]
    for a,b in pairs:
        src=folder/a;dest=folder/b;assert not dest.exists();s=src.read_text(encoding='utf8')
        s=s.replace('import build_aircraft_a56_scratch as build','import build_aircraft_a57_original_scratch as build').replace('from build_aircraft_a56_scratch import OUT,CFG,guard','from build_aircraft_a57_original_scratch import OUT,CFG,guard').replace('from probe_aircraft_a56 import','from probe_aircraft_a57 import').replace('AIRCRAFT-A56','AIRCRAFT-A57').replace('1102081','1102082')
        if b=='probe_aircraft_a57_allocation.py':
            s=s.replace("'ACTIVE_COHESIVE_ALLOCATION_TRACE_R1'","'ACTIVE_COHESIVE_ALLOCATION_TRACE'").replace("'allocation_trace_r1_predeclaration.json'","'allocation_trace_predeclaration.json'")
            s=s.replace('Read actual SMSTR descriptor capacity, caller and pointer identity; reject temporary-buffer-only hypothesis if SAV matches original restart allocation.','Verify actual original SMSTR capacity >=21*NEL and exact SAV pointer identity on the approved A57 binary; keep loaded physical gates separate.')
        ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n');rows.append({'source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest)})
    dump(ROOT/'wtc1_simulation_v8/data/aircraft_a57_control_derivation.json',{'created_utc':now(),'controls':rows,'inputs_and_physical_acceptance_criteria_unchanged':True,'old_binaries_not_replayed':True,'native_cap_s':180,'CPU_threads':1,'GPU':False,'additional_Engine_only_if_new_unresolved_question_declared':True})
    print('A57 native controls ready.',flush=True)

if __name__=='__main__':main()
