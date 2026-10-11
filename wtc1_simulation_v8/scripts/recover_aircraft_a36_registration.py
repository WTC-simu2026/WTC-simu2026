"""Repair a missing serialization import before registry mutation; retain evidence."""
from probe_aircraft_a36 import *
from finalize_aircraft_a22 import verify_files
import json

def main():
 guard();assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json');assert (ROOT/'harness/experiments/registry.jsonl').read_bytes()==(OUT/'before_registry.jsonl').read_bytes();assert read(ROOT/'harness/publication_cycle.json')==read(OUT/'before_publication_cycle.json')
 manifest=OUT/'artifact_manifest.json';data=read(manifest);verify_files(data['files']);dest=OUT/'sealing_recovery';assert not dest.exists();dest.mkdir();script=ROOT/'wtc1_simulation_v8/scripts/finalize_aircraft_a36.py';shutil.copy2(script,dest/'finalizer_before_import_repair.py');shutil.copy2(manifest,dest/'artifact_manifest_before_import_repair.json')
 s=script.read_text(encoding='utf8');needle='from finalize_aircraft_a22 import verify_files\n';assert s.count(needle)==1 and '\nimport json\n' not in s;s=s.replace(needle,needle+'import json\n');script.write_text(s,encoding='utf8',newline='\n')
 dump(dest/'repair.json',{'created_utc':now(),'failure':'NameError: json not defined during registry serialization','registry_and_state_changed_by_failed_call':False,'repair':'Add missing standard-library json import; no scientific computation or threshold changed','old_finalizer_and_manifest_preserved':True,'native_solver_reruns':0})
 for r in data['files']:
  if r['path']==rel(script):r.update(bytes=script.stat().st_size,sha256=streamsha(script))
 for p in [Path(__file__),*dest.iterdir()]:data['files'].append({'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)})
 data['registration_import_repair']=rel(dest/'repair.json');dump(manifest,data);verify_files(data['files']);print({'registration_import_repaired':True,'original_evidence_preserved':True},flush=True)

if __name__=='__main__':main()
