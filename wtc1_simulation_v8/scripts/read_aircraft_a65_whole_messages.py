"""Read new native CHECK logs/listings, retaining the initial narrow parser."""
from run_aircraft_a65_sampling import ROOT,OUT,read,dump,sha,now,rel
import re,json

rows=[]
for case in read(OUT/'whole_CHECK_review.json')['cases']:
    d=OUT/case['case'];log=(d/'engine.log').read_text(encoding='utf8',errors='replace')
    ids=[int(x) for x in re.findall(r'STOP:\s*ZERO OR NEGATIVE VOLUME FOR 3D-ELEMENT ID=\s*(\d+)',log)]
    error=re.findall(r'^\s*(\d+)\s+ERRORS\s*$',log,re.M);warning=re.findall(r'^\s*(\d+)\s+WARNINGS\s*$',log,re.M)
    assert len(error)==1 and len(warning)==1
    name=read(d/'generation.json')['case']['name'];listing=d/(name+'_0001.out');text=listing.read_text(encoding='utf8',errors='replace')
    listing_ids=[int(x) for x in re.findall(r'STOP:\s*ZERO OR NEGATIVE VOLUME FOR 3D-ELEMENT ID=\s*(\d+)',text)]
    assert listing_ids==ids
    row={'case':case['case'],'native_exit_code':case['parent_exit_code'],'NORMAL_TERMINATION':case['normal_termination'],
         'CHECK_ended':case['CHECK_ended'],'printed_error_count':int(error[0]),'printed_warning_count':int(warning[0]),
         'TYPE25_ignored':case['TYPE25_ignored'],'STOP_volume_message_count':len(ids),'STOP_volume_element_ids':ids,
         'STOP_colon_messages_present':bool(re.search(r'\bSTOP\s*:',log)),
         'log_listing_volume_messages_match':True,'native_log':rel(d/'engine.log'),'native_log_sha256':sha(d/'engine.log'),
         'native_listing':rel(listing),'native_listing_sha256':sha(listing),
         'pass':bool(case['parent_exit_code']==0 and case['CHECK_ended'] and int(error[0])==0 and case['TYPE25_ignored']==0 and len(ids)==0),
         'initial_parser_null_error_and_false_STOP_flag_preserved':True}
    rows.append(row);print(json.dumps({k:row[k] for k in ['case','printed_error_count','printed_warning_count','STOP_volume_message_count','TYPE25_ignored','pass']}),flush=True)
dump(OUT/'whole_CHECK_message_review.json',{'created_utc':now(),'cases':rows,'pass':all(r['pass'] for r in rows),
    'initial_completion_parser_preserved':'whole_CHECK_review.json','no_native_reexecution':True,
    'summary_error_count_not_assumed_equal_to_individual_message_count':True,
    'NORMAL_and_exit0_are_not_pass':True,'whole_credit_s':0,'whole_dynamic_qualification':False})
