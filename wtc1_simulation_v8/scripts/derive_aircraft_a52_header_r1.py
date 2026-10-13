"""Restore only the mandatory Starter header in a separate candidate attempt."""
from probe_aircraft_a52 import *
import ast
scripts=ROOT/'wtc1_simulation_v8/scripts';src=scripts/'probe_aircraft_a52.py';dst=scripts/'probe_aircraft_a52_header_r1.py';assert not dst.exists();s=src.read_text()
s=s.replace("n='A52_TYPE2_FACET_PAIRS'","n='A52_TYPE2_FACET_PAIRS_R1'").replace("OUT/'WHOLE_PAIRED_TYPE2_BINDING_TRACE'","OUT/'WHOLE_PAIRED_TYPE2_BINDING_TRACE_R1'")
old=".write_text('\\n'.join(line for k,v in S.items() for line in [k]+v)+'\\n',encoding='utf8')";assert s.count(old)==1;s=s.replace(old,".write_text('#RADIOSS STARTER\\n'+'\\n'.join(line for k,v in S.items() for line in [k]+v)+'\\n',encoding='utf8')")
ast.parse(s);dst.write_text(s,encoding='utf8')
dump(OUT/'header_r1_derivation.json',{'created_utc':now(),'original_script':rel(src),'original_sha256':streamsha(src),'derived_script':rel(dst),'derived_sha256':streamsha(dst),'retained_failure':'First candidate omitted mandatory #RADIOSS STARTER. Starter exit2, errors100201/2000, no Engine executed; metadata parser then lacked warning count.','only_scientific_input_repair':'Restore original mandatory header; intended configuration unchanged. Separate root name and directory preserve the failed attempt.','original_failed_directory':rel(OUT/'WHOLE_PAIRED_TYPE2_BINDING_TRACE'),'no_physical_parameters_or_acceptance_criteria_changed':True,'before_new_Starter':True})
print('Header-only R1 prepared; original failed preparation retained.',flush=True)
