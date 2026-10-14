"""Independently remove the proposed additions and recover the exact A62 source."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import re,json,hashlib

plan=read(ROOT/'wtc1_simulation_v8/data/aircraft_a66_proposal.json');patch=plan['patch']
base=ROOT/patch['current_A62_source'];proposed=ROOT/patch['proposed_source'];a=base.read_text(encoding='utf8');b=proposed.read_text(encoding='utf8')
assert sha(base)==patch['current_A62_source_sha256'] and sha(proposed)==patch['proposed_sha256']
assert b.count('\nC     Current projected Gauss areas for TYPE43/LAW117/Ismstr4.')==1
prefix=b.split('\nC     Current projected Gauss areas for TYPE43/LAW117/Ismstr4.')[0]
prefix,n=re.subn(r'^        SUBROUTINE WTC_A66_S43_CURK.*?^        END SUBROUTINE WTC_A66_S43_CURK\n','',prefix,flags=re.M|re.S);assert n==1
prefix,n=re.subn(r'^      IF \(IGTYP==43.AND.MTN==117.AND.ISMSTR==4\) THEN\n.*?^      ENDIF\n','',prefix,flags=re.M|re.S);assert n==1
assert prefix==a
old_helper=re.search(r'^      SUBROUTINE WTC_A61_S43_K.*',a,re.M|re.S).group(0)
new_old_helper=re.search(r'^      SUBROUTINE WTC_A61_S43_K.*?(?=\nC     Current projected Gauss)',b,re.M|re.S).group(0)
assert new_old_helper==old_helper
assert base.read_bytes().count(b'\r\n')==0 and proposed.read_bytes().count(b'\r\n')==0
current=re.search(r'^      SUBROUTINE WTC_A66_S43_CURK.*',b,re.M|re.S).group(0)
assert '%VOL' not in current and 'AW=DOT_PRODUCT(N,CR)' in current and 'GPON(I,P)=GPON(I,P)*AW' in current
assert '.NOT.(AW>ZERO).OR.AW>HUGE(AW)' in current and 'STOP 66' in current
for term in ['CALL SIGEPS117','CALL SUSER43','CALL SRCOORK']:
    assert b.count(term)==a.count(term)
prep=ROOT/'wtc1_simulation_v8/output/aircraft_a66_preparation_r1'
dump(prep/'independent_patch_scope_review.json',{'created_utc':now(),'pass':True,'recover_A62_source_exactly_after_removing_only_additions':True,
    'old_Ismstr1_helper_byte_identical':True,'LF_line_endings_verified':True,'new_helper_does_not_read_reference_VOL':True,
    'current_area_positive_finite_guard_present':True,'material_force_history_calls_not_changed':True,
    'current_source_sha256':sha(base),'proposed_source_sha256':sha(proposed),'patch_sha256':sha(ROOT/patch['patch']),
    'source_applied':False,'compiled_or_native_qualified':False,'no_native_replay':True})
print(json.dumps({'source_scope_PASS':True,'old_helper_byte_identical':True,'source_not_applied':True}),flush=True)
