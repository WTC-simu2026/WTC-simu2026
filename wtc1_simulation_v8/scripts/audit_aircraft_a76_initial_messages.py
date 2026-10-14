"""New cached A75 message chronology and separately printed impact inventory; no native replay."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
from pathlib import Path
import re,json

PREP=ROOT/'wtc1_simulation_v8/output/aircraft_a76_preparation'


def main():
    rows=[];inventory=[]
    for case in read(ROOT/'wtc1_simulation_v8/data/aircraft_a75_predeclaration.json')['cases']:
        d=ROOT/'wtc1_simulation_v8/output/aircraft_a75'/case['case']
        listing=d/(case['name']+'_0000.out');text=listing.read_text(encoding='utf8')
        error_regex=r'\*\* INITIAL PENETRATION\s*=\s*([\d.E+\-]+) IMPOSSIBLE TO CALCULATE NEW COORDINATES OF SECONDARY NODE\s+(\d+)\s+ERROR ID\s*:\s*612\s+\*\* ERROR IN INITIAL PENETRATION IN INTERFACE\s+DESCRIPTION\s*:\s+-- INTERFACE ID:\s*(\d+)\s+-- INTERFACE TITLE:[^\n]*\s+INACTI\s*=\s*(\d+)\s+SECONDARY NODE\s+(\d+) IS ON THE MAIN SURFACE'
        events=[{'penetration_mm':float(m[1]),'preceding_move_print_number':int(m[2]),'interface_ID':int(m[3]),
            'message_INACTI':int(m[4]),'error_node_print_number':int(m[5])} for m in re.finditer(error_regex,text)]
        assert len(events)==916 and all(e['preceding_move_print_number']==e['error_node_print_number'] for e in events)
        assert {e['interface_ID'] for e in events}=={2}
        native=re.findall(r'INTERFACE NUMBER\.[^\n]*?(\d+)\s*\n\s*INTERFACE TYPE\.[^\n]*?(\d+)\s*\n\s*POSSIBLE IMPACT NUMBER:\s*(\d+)',text)
        impacts={int(ID):int(count) for ID,typ,count in native if int(typ)==7}
        assert set(impacts)=={2,101,102,103,104}
        row={'case':case['case'],'listing':rel(listing),'listing_sha256':sha(listing),'events':events,
            'all_916_preceding_move_numbers_equal_612_numbers':True,
            'A75_following_print_association_is_next_message_not_an_ID_domain_shift':True,
            'source_binary_numerical_label_mapping_NOT_claimed':True}
        dump(PREP/(case['case']+'_message_chronology.json'),row)
        inventory.append({'case':case['case'],'native_printed_possible_impact_counts':impacts,
            'old_A75_parameter_heading_reader_did_not_capture_separate_impact_table':True,
            'old_raw_failed_gate_unchanged':True,'full_filtered_pair_labels_NOT_available':True})
        rows.append({k:v for k,v in row.items() if k!='events'})
    dump(PREP/'cached_message_and_inventory_review.json',{'created_utc':now(),'pass':True,'cases':rows,
        'separate_impact_table':inventory,'new_native':0,'A75_916errors_and11warnings_still_fail':True,
        'own_reader_repair_only_no_software_source_change':True})
    print(json.dumps({'cached_chronology_pass':True,'possible_impact_counts':inventory,'new_native':0}),flush=True)


if __name__=='__main__':main()
