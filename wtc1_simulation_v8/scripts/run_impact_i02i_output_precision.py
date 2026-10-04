"""J: predeclared saved T01/CSV observability diagnosis, no executables run."""
from __future__ import annotations
import argparse,json,time,urllib.request
from pathlib import Path
import run_impact_i02i_free_return as i
h=i.h;ROOT=i.ROOT;OLD=i.OUT
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_output_precision'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_j_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_j_plan_from_i.json'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def initialize():
    assert not OUT.exists() and not CFG.exists(),'Preserve iterations'
    hv=h.harness();state=read(ROOT/'harness/state.json');plan=read(PLAN)
    assert state['current_iteration']=='IMPACT-I02I-I' and state['next_iteration']=='IMPACT-I02I-J'
    assert h.sha(ROOT/plan['saved_I_summary'])==plan['saved_I_sha256']
    rows={}
    for p in [OLD/'preservation_before.json',OLD/'artifact_manifest.json']:
        for r in read(p)['files']:
            assert h.sha(ROOT/r['path'])==r['sha256'],r['path'];rows[r['path']]=r
    for p in [OLD/'preservation_before.json',OLD/'artifact_manifest.json',OLD/'publication_verification.json',
        ROOT/'harness/handoffs/WTC1_IMPACT_I02I_I_HANDOFF.md']:
        rows[h.rel(p)]={'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)}
    OUT.mkdir();h.dump(OUT/'harness_before.json',hv)
    h.dump(OUT/'preservation_before.json',{'created_utc':h.NOW(),'files':list(rows.values()),'scope':'Saved I and predecessor inventories; no archive scan'})
    for n in h.g.f.ADMIN:(OUT/('before_'+Path(n).name)).write_bytes((ROOT/'harness'/n).read_bytes())
    print(json.dumps({'initialized':'IMPACT-I02I-J','old_files_pinned':len(rows),'no_engine':True}),flush=True)

def declare():
    assert not CFG.exists(),'Never rewrite gates'
    snapshots=OUT/'source_snapshots';assert not snapshots.exists();snapshots.mkdir()
    url='https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tfile_engine_r.htm'
    tick=time.perf_counter()
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WTC-simu2026-primary-source-audit'}),timeout=30) as f:data=f.read()
    page=snapshots/'altair_tfile_2026.html';page.write_bytes(data)
    assert b'IEEE 32-bit' in data and b'/TFILE' in data
    failures=[{'url':u,'status':404,'checked_utc':h.NOW(),'method':'unauthenticated urllib read, before declaration'} for u in [
        'https://api.github.com/repos/OpenRadioss/Tools/contents/output_converters/th_to_csv',
        'https://api.github.com/repos/OpenRadioss/OpenRadioss/contents/tools/th_to_csv',
        'https://api.github.com/repos/OpenRadioss/Tools/commits/main',
        'https://raw.githubusercontent.com/OpenRadioss/OpenRadioss/main/tools/th_to_csv/th_to_csv.c',
        'https://raw.githubusercontent.com/OpenRadioss/Tools/main/output_converters/th_to_csv/th_to_csv.c',
        'https://raw.githubusercontent.com/OpenRadioss/Tools/main/output_converters/th_to_csv/src/th_to_csv.c']]
    h.dump(OUT/'source_access_attempts.json',{'attempts':failures,'no_code_read':True,
        'search_cache_not_treated_as_live_code':True,'official_binary_schema_verified':False})
    observed={'origin':'Own byte inspection of I NORMAL_SUBPEAK_RETURN_025NS header before assessment; derived bounded schema, not official schema',
        'endian':'>','record_markers':'4-byte big-endian signed length repeated after payload, exact EOF consumption',
        'version':3040,'header_payload_bytes':[84,80,24,88,60,44,44,60,4,60,44,24,60,44,44,24],
        'counts_signature':[1,1,1,1,2,22],'global_codes':list(range(1,23)),
        'spring_group_signature':[2,6,0,1,6],'spring_codes':[1,2,3,8,9,14],
        'node_group_signature':[3,0,0,2,6],'node_codes':[1,2,4,5,620,621],
        'node_ids':[1,2],'row_payload_bytes':[4,88,24,48],'header_end_byte':916,
        'global_order_from_existing_converter_and_model_card':['INTERNAL ENERGY','KINETIC ENERGY','X-MOMENTUM','Y-MOMENTUM','Z-MOMENTUM','MASS','TIME STEP',
            'ROTATION ENERGY','EXTERNAL WORK','SPRING ENERGY','CONTACT ENERGY','HOURGLASS ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY',
            'DAMPING CONTACT ENERGY','PLASTIC WORK','ADDED MASS','PERCENTAGE ADDED MASS','INLET MASS','OUTLET MASS','INLET ENERGY','OUTLET ENERGY'],
        'spring_order_from_saved_card':['OFF','FX','FY','LX','LY','IE'],'node_order_from_saved_card':['DX','DY','VX','VY','REACX','REACY']}
    h.dump(OUT/'header_discovery.json',observed)
    cfg={'id':'IMPACT-I02I-J','seed':1102018,'random_draws':0,'declared_utc':h.NOW(),
        'scope':'Four saved I T01 files, bounded version3040 decoder and separate finite-representation diagnostic; no material or solver change',
        'cases':[],'schema':observed,'units':read(i.CFG)['units'],'k_N_per_mm':56000.,'hypothetical_Gf_N_per_mm':30.,
        'gates':{'exact_record_markers_and_EOF':True,'exact_header_signature_and_card_mapping':True,
            'all_binary_values_reproduce_CSV_6e':True,'exact_global_spring_and_element_IE_bits':True,
            'finite_and_strict_time':True,'binary_negative_elastic_rows_allow_zero_in_rounding_interval':True,
            'CSV_negative_rows_allow_zero_after_decimal_and_binary_rounding':True,
            'rounding_interval_arithmetic':'Exact rational dyadic midpoints for stored float32; exact decimal 0.001 and Kn; rational squared force extrema',
            'no_observation_assumed_for_generic_files':True,'old_I_gates_unchanged':True,'end_coverage_steps':2,
            'energy_balance_fraction':.005,'maximum_diagnostic_seconds':120},
        'diagnostics_only':['Sign of binary IE-U at old I threshold 1e-10 J is reported, never promoted to old I gate',
            'CSV-to-binary difference is measured directly, not a physical energy correction',
            'Quantization intervals assume nearest rounding; this does not establish internal mechanical dissipation',
            'Record labels/codes constrain mapping; global variable semantics also rely on original converter and cached output requests'],
        'source_manifest':h.rel(OUT/'source_manifest.json'),'preservation_manifest':h.rel(OUT/'preservation_before.json'),
        'saved_I_summary_sha256':h.sha(OLD/'verification_r1/summary.json'),'saved_I_config_sha256':h.sha(i.CFG),
        'no_solver_run':True,'no_converter_run':True,'no_property_change':True,'physical_qualification':False,
        'execution_budget':{'maximum_wall_seconds':120,'expected_seconds':[1,10]},
        'qualification':{'bounded_binary_layout_only':True,'official_decoder_source_read':False,
            'all_I_criteria_qualified':False,'mixed_mode_qualified':False,'physical_propagation_qualified':False,
            'aircraft_impact_qualified':False,'source_convention_verified':False}}
    oldcfg=read(i.CFG)
    for c in oldcfg['cases']:
        folder=OLD/c['id'];name=read(folder/'generation.json')['name'];paths={key:folder/(name+suffix) for key,suffix in
            [('T01','T01'),('csv','T01.csv'),('starter','_0000.rad'),('engine','_0001.rad')]}
        cfg['cases'].append({'id':c['id'],'family':c['family'],'saved_case':c,'title':name,
            'references':oldcfg['references'][c['family']],
            'inputs':{key:{'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)} for key,p in paths.items()}})
    h.dump(OUT/'source_manifest.json',{'created_utc':h.NOW(),'sources':[
        {'id':'ALTAIR_TFILE_2026','url':url,'path':h.rel(page),'bytes':len(data),'sha256':h.sha(page),'use':'TFILE/4 IEEE32, not exact binary schema'},
        {'id':'SAVED_I_DECKS_AND_RAW_BINARY','use':'Own directly observed primary numerical outputs, byte structure and requested fields'},
        {'id':'ALTAIR_SPRING','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm','use':'IE, FY, OFF definitions; cached H sources'},
        {'id':'ALTAIR_NODE','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm','use':'Requested fields, labeling discrepancy retained; cached H sources'}],
        'cached_I_source_manifest_sha256':h.sha(OLD/'source_manifest.json'),
        'source_acquisition_seconds':time.perf_counter()-tick,'upstream_converter_code_unavailable':True,
        'no_new_physical_property':True,'copyright_snapshots_not_redistributed':True})
    h.dump(CFG,cfg)
    h.dump(OUT/'declaration_guard.json',{'created_utc':h.NOW(),'config_sha256':h.sha(CFG),
        'no_assessment_before_declaration':not (OUT/'verification_r1').exists(),'no_engine':True,
        'old_I_failure_threshold_J':read(i.CFG)['gates']['retained_negative_tolerance_J']})
    print(json.dumps({'declared':'IMPACT-I02I-J','saved_files':4,'no_solver_or_converter_run':True}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['initialize','declare']);a=p.parse_args();globals()[a.action]()
