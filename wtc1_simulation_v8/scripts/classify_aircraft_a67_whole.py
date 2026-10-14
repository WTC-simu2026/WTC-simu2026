"""Classify only the new A67 native listings and unchanged pinned checker source."""
from control_aircraft_a67_current_area import ROOT,OUT,CONTROL,read,dump,sha,now
from pathlib import Path
import re,collections,json

source=ROOT/'wtc1_simulation_v8/openradioss_runtime/a66_current_area_proposal_r1/imp_solv.F'
text=source.read_text(encoding='utf8');assert "CALL PRODUT_W(NDDL,LB,LB,W_DDL,R2)" in text and 'R2>ZERO.AND.R2<EP30' in text
rows=[]
for case in read(CONTROL)['whole_CHECK_cases']:
    d=OUT/case['id'];listing=d/(case['name']+'_0001.out');s=listing.read_text(encoding='utf8',errors='replace');log=(d/'engine.log').read_text(encoding='utf8')
    zero=[int(v) for v in re.findall(r'ND\.\s*=\s*(\d+)\s+WITH POSSIBLE FREE STIFFNESS CHECKED',s)]
    connection=[int(v) for v in re.findall(r'ND\.\s*=\s*(\d+)\s+WITH POSSIBLE FREE CONNECTION CHECKED',s)]
    node_rows=[{'node_id':int(n),'kind':k,'direction':a,'value':float(v.replace('D','E'))} for n,k,a,v in re.findall(r'NODE NUM\.\s*=\s*(\d+)\s+(TRA|ROT)_DIR\s*=\s*([XYZ])\s+VAL\.\s*=\s*([\d.E+\-]+)',s)]
    assert len(zero)==1 and len(connection)==1 and len(node_rows)==zero[0]+connection[0]
    counts=collections.Counter((v['kind'],v['direction']) for v in node_rows)
    row={'case':case['id'],'listing':str(listing.relative_to(ROOT)).replace('\\','/'),'listing_sha256':sha(listing),
        'zero_or_negative_volume_messages':s.count('STOP: ZERO OR NEGATIVE VOLUME'),'zero_stiffness_possible_DOF':zero[0],
        'possible_free_connection_reported_DOF':connection[0],'connection_direction_counts':{k[0]+'_'+k[1]:v for k,v in counts.items()},
        'minimum_printed_connection_value':min(v['value'] for v in node_rows),'maximum_printed_connection_value':max(v['value'] for v in node_rows),
        'first_printed_connection_examples':node_rows[:12],'implicit_loading_error_messages':s.count('** ERROR :IMPLICIT LOADING DATA **'),
        'TYPE25_ignored':log.count('INTERFACE TYPE 25 IS NOT AVAILABLE'),
        'generic_ISOLID0_advisory_preserved':('ELEMENT FORMULATION ISOLID=    0' in s),
        'matrix_dimensions':[{'label':a,'ND':int(n),'NZ':int(z),'NB_MAX':int(b)} for a,n,z,b in re.findall(r'(SYMBOLIC|FINAL)\s+DIM\s*:\s*ND\s*=\s*(\d+)\s+NZ\s*=\s*(\d+)\s+NB_MAX\s*=\s*(\d+)',s)],
        'possible_connection_not_assumed_proven_geometric_disconnection':True,'normal_exit_not_a_pass':True,
        'check_loading_R2_not_directly_observed':True,'native_initial_velocity_not_an_external_load_proof':True}
    rows.append(row);print(json.dumps({k:row[k] for k in ['case','zero_or_negative_volume_messages','zero_stiffness_possible_DOF','possible_free_connection_reported_DOF','connection_direction_counts','implicit_loading_error_messages']}),flush=True)
dump(OUT/'whole_CHECK_classification.json',{'created_utc':now(),'cases':rows,'pass':False,'blockers_preserved':True,'source_path':str(source.relative_to(ROOT)).replace('\\','/'),'source_sha256':sha(source),
    'source_loading_condition':'IMP_CHKM accepts0<R2=weighted norm squared(LB)<1e30; else warns in quasi-static mode or records an error. The listing alone does not print R2.',
    'connection_source_condition':'IMP_CHECM0 reports DIAG_M below1e-12 or above1e10; actual units/normalization and role classification require source-aware audit.',
    'no_new_native_or_threshold_change':True,'whole_impact_qualified':False,'whole_credit_s':0})
