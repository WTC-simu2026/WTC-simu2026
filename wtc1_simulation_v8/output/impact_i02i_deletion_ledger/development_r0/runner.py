"""L declarations for a saved-output energy ledger; zero solver jobs."""
from __future__ import annotations
import argparse,json,copy,urllib.request
from pathlib import Path
import run_impact_i02i_free_mixed as k
import run_impact_i02i_dtcap as f
h=k.h;ROOT=k.ROOT
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_deletion_ledger'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_l_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_l_plan_from_k.json'
read=k.read
URLS={'ALTAIR_TYPE8':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type8_spr_gene_starter_r.htm',
      'ALTAIR_TH_SPRING':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_spring_starter_r.htm'}

def initialize():
    assert not OUT.exists() and not CFG.exists(),'Keep iterations'
    hv=h.harness();state=read(ROOT/'harness/state.json');assert state['current_iteration']=='IMPACT-I02I-K' and state['next_iteration']=='IMPACT-I02I-L'
    assert read(k.OUT/'publication_verification.json')['pass'];pins={}
    for path in [k.OUT/'preservation_before.json',k.OUT/'artifact_manifest.json']:
        for r in read(path)['files']:
            assert h.sha(ROOT/r['path'])==r['sha256'],r['path'];pins[r['path']]=r
    for path in [k.OUT/'preservation_before.json',k.OUT/'artifact_manifest.json',k.OUT/'publication_verification.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_K_HANDOFF.md']:
        pins[h.rel(path)]={'path':h.rel(path),'bytes':path.stat().st_size,'sha256':h.sha(path)}
    for v in read(PLAN)['inputs'].values():assert h.sha(ROOT/v['path'])==v['sha256']
    OUT.mkdir();h.dump(OUT/'harness_before.json',hv);h.dump(OUT/'preservation_before.json',{'created_utc':h.NOW(),'files':list(pins.values()),'scope':'Saved K and predecessor inventories, no archive rescan'})
    for name in h.g.f.ADMIN:(OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    print(json.dumps({'initialized':'IMPACT-I02I-L','old_files_pinned':len(pins)}),flush=True)

def declare():
    assert not CFG.exists();old=read(f.CFG);plan=read(PLAN);saved=read(f.OUT/'verification_r1/summary.json')
    cfg={'id':'IMPACT-I02I-L','seed':1102020,'random_draws':0,'declared_utc':h.NOW(),'scope':plan['scope'],
        'plan_sha256':h.sha(PLAN),'cached_references':plan['inputs'],'connector':copy.deepcopy(old['connector']),
        'binary_schema':read(k.CFG)['binary_schema'],'reader_sha256':h.sha(ROOT/'wtc1_simulation_v8/scripts/decode_impact_i02i_t01.py'),
        'cases':[],'event_selection':{'OFF':'First consecutive 1 to 0 transition; require no reactivation',
            'pre':'OFF row minus1','settled':'OFF row plus2, fixed before analysis, never chosen to optimize a residual',
            'inspect_rows':'OFF minus2 through OFF plus3, original times/values; no partition asserted on OFF row',
            'force_zero':'First row on/after OFF with both forces below fixed tolerance, diagnostic only'},
        'units':{'mass':'g','length':'mm','time':'ms','force':'N','raw_energy':'N mm','energy_conversion_J_per_N_mm':0.001,'impulse':'N ms'},
        'precision':{'policy':'Conditional nearest rounding IEEE32; exact Fraction cells only at selected rows, no empirical sign margin',
            'Ux':'Fx^2/(2Kt)','Uy':'Fy^2/(2Kn)','D':'IE-Ux-Uy',
            'delta':'Intervals of post minus pre, exact independent bounds; do not assume correlation or internal channels',
            'all_binary_values_reproduce_saved_CSV_6e':True,'official_schema_verified':False},
        'gates':{'energy_fraction':.005,'reservoir_fraction':.005,'force_zero_N':1e-5,'no_added_mass_g':1e-12,
            'mass_fraction':1e-5,'known_reference_error_J':1e-12,'maximum_diagnostic_seconds':120,
            'raw_same_OFF_FX_gate':'Old F values preserved; reported separately, never promoted',
            'near_event_quantization':'Report exact cells and zero inclusion; not a proof of the true rounding algorithm'},
        'reference':{'normal_work_J':.03,'linear_x_at_0p02_mm_J':.0043,
            'future_fresh_velocity_X_mm_ms':[5.,10.],'future_fresh_velocity_Y_mm_ms':30.,'future_end_ms':.012,
            'numerical_retention':'Continuous x,y,vx,vy at normal deletion; force X=Y=0 after; IE retains G+Ux_at_deletion',
            'release_counterfactual':'IE drops by Ux, so energy closure requires gain in KE, work/channel flux or another explicit reservoir; direction/impulse not specified',
            'calibration':False},'solver_jobs':0,'old_solver_rerun':False,'sources':old['sources']}
    for c in old['cases']:
        folder=f.OUT/c['id'];gen=read(folder/'generation.json');name=gen['name'];inputs={}
        for key,path in {'generation':folder/'generation.json','starter':folder/(name+'_0000.rad'),'engine':folder/(name+'_0001.rad'),
                'T01':folder/(name+'T01'),'csv':folder/(name+'T01.csv'),'execution':folder/'execution.json'}.items():
            inputs[key]={'path':h.rel(path),'bytes':path.stat().st_size,'sha256':h.sha(path)}
        assert inputs['csv']['sha256']==saved['cases'][c['id']]['raw_history_sha256']
        cfg['cases'].append({'id':c['id'],'title':name,'saved_case':c,'inputs':inputs,
            'expected_event_count':0 if c['id'].startswith('RETURN') else1,
            'normal_work_J':0. if c['id'].startswith('RETURN') else .03,
            'energy_scale_J':.0043 if c['id'].startswith('RETURN') else .0343 if c['id'].startswith('FIXED') else .03})
    h.dump(CFG,cfg);h.dump(OUT/'declaration_guard.json',{'created_utc':h.NOW(),'pass':True,'config_sha256':h.sha(CFG),'before_diagnostic':not (OUT/'verification_r1').exists()})
    print(json.dumps({'declared':'IMPACT-I02I-L','saved_cases':len(cfg['cases']),'solver_jobs':0,'diagnostic_budget_s':120}),flush=True)

def sources():
    dest=OUT/'source_snapshots';assert not dest.exists();dest.mkdir();entries=[]
    for name,url in URLS.items():
        req=urllib.request.Request(url,headers={'User-Agent':'WTC-simu2026-research'})
        with urllib.request.urlopen(req,timeout=25) as response:content=response.read()
        path=dest/(name+'.html');path.write_bytes(content)
        entries.append({'id':name,'url':url,'access_utc':h.NOW(),'snapshot':h.rel(path),'sha256':h.sha(path),
            'copyright':'Altair, all rights reserved; evidence snapshot excluded from redistribution',
            'use':'Independent modes and output definitions, not proof of deletion-energy routing'})
    h.dump(OUT/'source_manifest.json',{'created_utc':h.NOW(),'sources':entries,'inherited_sources':read(CFG)['sources'],
        'new_physical_data':False,'internal_code_energy_partition_verified':False,'exact_converter_source_obtained':False})
    print(json.dumps({'primary_sources_saved':len(entries),'internal_partition_claimed':False}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['initialize','declare','sources']);a=p.parse_args();globals()[a.action]()
