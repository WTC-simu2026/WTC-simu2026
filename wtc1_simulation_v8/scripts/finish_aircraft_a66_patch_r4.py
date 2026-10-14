"""Finish source proposal only; verbatim function indentation preserves multiline source strings."""
from prepare_aircraft_a66_current_area_r1 import *

assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A65'
assert not PLAN.exists() and not (PREP/'preparation_review.json').exists()
domain=read(PREP/'whole_domain_and_geometry_review.json');prototype=read(PREP/'current_area_iteration_prototype_review.json')
assert domain['pass'] and prototype['pass']
base=ROOT/'wtc1_simulation_v8/openradioss_runtime/a62_type43_surface_iteration_candidate/s8zke3_R2_interface.proposed.F'
original=base.read_text(encoding='utf8');archive=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz'
files=[ROOT/m['path'] for m in domain['models']]
for model in domain['models']:assert sha(ROOT/model['path'])==model['sha256']
checks=prototype['checks'];source_rows=domain['source_rows'];start=time.perf_counter()
source=ROOT/'wtc1_simulation_v8/scripts/prepare_aircraft_a66_current_area_r1.py';code=source.read_text(encoding='utf8')
a=code.index('    # Prepare an exact AGPL diff');b=code.index("\nif __name__=='__main__'")
body=code[a:b];assert body.count("marker='      NF1 = NFT+1'")==1
body=body.replace("marker='      NF1 = NFT+1'","marker='      NLAY = ELBUF_STR%NLAY'")
body=body.replace('    assert proposed[proposed.index(original[helper_start:helper_start+60]):][:len(helper)]==helper',"    preserved_start=re.search(r'^      SUBROUTINE WTC_A61_S43_K',proposed,re.M).start();assert proposed[preserved_start:preserved_start+len(helper)]==helper")
function_code='def _finish_stage():\n'+body+'\n_finish_stage()\n'
compile(function_code,__file__,'exec')
dump(PREP/'patch_preparation_R3_failure.json',{'created_utc':now(),'failure':'Preservation checker matched an indented interface signature before the standalone helper; use anchored six-space declaration. Actual old helper unchanged.',
    'successful_geometry_and_prototype_evidence_reused':True,'successful_diagnostics_replayed':False,
    'R2_script':'wtc1_simulation_v8/scripts/finish_aircraft_a66_patch_r2.py','R3_script':rel(Path(__file__)),
    'source_application_compilation_or_native_runs':0})
exec(compile(function_code,__file__,'exec'))
