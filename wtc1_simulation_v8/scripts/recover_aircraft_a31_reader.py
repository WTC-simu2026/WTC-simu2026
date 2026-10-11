"""Read cached native completion after a part-label mismatch; no native rerun."""
from run_aircraft_a31 import *

def main():
    d=OUT/'w0/SHEAR_XZ_N6';n='A31_SHEAR_XZ_N6';assert not (d/'review.json').exists() and 'NORMAL TERMINATION' in (d/'engine.log').read_text();old=OUT/'reader_before_part_label_fix.py';new=Path(__file__).with_name('run_aircraft_a31.py');a="k.startswith('SANDWICH_PARTS') and k.strip().endswith('PW')";b="k.startswith(('LOWER_VOLUME_SKIN','UPPER_VOLUME_SKIN','UNCHANGED_SOURCE_CORE')) and k.strip().endswith('PW')";assert old.read_text(encoding='utf-8').count(a)==1 and old.read_text(encoding='utf-8').replace(a,b)==new.read_text(encoding='utf-8');dump(OUT/'part_label_reader_recovery.json',{'created_utc':now(),'original_reader':rel(old),'original_reader_sha256':streamsha(old),'fixed_reader':rel(new),'fixed_reader_sha256':streamsha(new),'only_change':{'old':a,'new':b},'reason':'TH/PART CSV names use actual part titles, not TH group name. All3PWchannels explicitly selected; no data, thresholds or reference changed.','native_reruns':0,'original_retained_failure':read(d/'retained_failure.json')});review(d,n);run()

if __name__=='__main__':main()
