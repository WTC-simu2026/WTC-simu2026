"""Finish only patch preparation, reusing successful R1 geometry/prototype evidence."""
from prepare_aircraft_a66_current_area_r1 import *
import textwrap

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
body=textwrap.dedent(code[a:b]);assert body.count("marker='      NF1 = NFT+1'")==1
body=body.replace("marker='      NF1 = NFT+1'","marker='      NLAY = ELBUF_STR%NLAY'")
dump(PREP/'patch_preparation_R1_failure.json',{'created_utc':now(),'failure':'Source insertion anchor NF1 used a different spacing in the pinned file; stopped before source proposal, plan or Engine execution.',
    'successful_geometry_and_52_prototype_checks_reused':len(checks),'no_replay_of_successful_analysis':True,
    'R2_anchor':'NLAY = ELBUF_STR%NLAY immediately after existing scoped surface dispatch',
    'source_script':rel(source),'source_script_sha256':sha(source),'R2_script':rel(Path(__file__))})
exec(compile(body,__file__,'exec'))
