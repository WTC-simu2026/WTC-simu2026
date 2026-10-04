"""K four fresh free XY witnesses, declarations precede all executables."""
from __future__ import annotations
import argparse,copy,json
from pathlib import Path
import run_impact_i02i_output_precision as j
import reference_impact_i02i_free_mixed as ref
h=j.h;ROOT,OUT,CFG,PLAN=ref.ROOT,ref.OUT,ref.CFG,ref.PLAN

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def initialize():
    assert not OUT.exists() and not CFG.exists(),'Keep iterations'
    hv=h.harness();state=read(ROOT/'harness/state.json');plan=read(PLAN)
    assert state['current_iteration']=='IMPACT-I02I-J' and state['next_iteration']=='IMPACT-I02I-K'
    assert h.sha(ROOT/plan['saved_J_summary'])==plan['saved_J_sha256']
    rows={}
    for p in [j.OUT/'preservation_before.json',j.OUT/'artifact_manifest.json']:
        for r in read(p)['files']:
            assert h.sha(ROOT/r['path'])==r['sha256'],r['path'];rows[r['path']]=r
    for p in [j.OUT/'preservation_before.json',j.OUT/'artifact_manifest.json',j.OUT/'publication_verification.json',
        ROOT/'harness/handoffs/WTC1_IMPACT_I02I_J_HANDOFF.md']:
        rows[h.rel(p)]={'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)}
    OUT.mkdir();h.dump(OUT/'harness_before.json',hv)
    h.dump(OUT/'preservation_before.json',{'created_utc':h.NOW(),'files':list(rows.values()),'scope':'Saved J and predecessor inventories only, no archive scan'})
    for name in h.g.f.ADMIN:(OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    print(json.dumps({'initialized':'IMPACT-I02I-K','old_files_pinned':len(rows)}),flush=True)

def declare():
    assert not CFG.exists();r=read(OUT/'reference_verification.json');assert r['pass']
    cfg=copy.deepcopy(read(j.i.CFG));cfg.update(id='IMPACT-I02I-K',seed=1102019,random_draws=0,declared_utc=h.NOW(),
        scope='Two free translational modes X/Y simultaneously, no separation or compression; fresh states only')
    cfg['references']=r['parameters'];cfg['reference_guard_sha256']=h.sha(OUT/'reference_verification.json');cfg['plan_sha256']=h.sha(PLAN)
    cfg['cases']=[]
    for family in read(PLAN)['cases_proposed']:
        for cap,label in [(0.000025,'025NS'),(.0000125,'012P5NS')]:
            cfg['cases'].append({'id':family['family']+'_'+label,'family':family['family'],'stage':'normal','maximum_dt_ms':cap,
                'dt_scale':.2,'fails':True,'expected_OFF':1,'end_ms':family['end_ms'],
                'initial_velocity_mm_per_ms':family['initial_vY_mm_per_ms'],'initial_vX_mm_per_ms':family['initial_vX_mm_per_ms']})
    cfg['gates']={'raw_amplitude_fraction':.01,'energy_fraction':.005,'work_fraction':.005,'comparison_fraction':.005,
        'mass_fraction':1e-5,'added_mass_g':1e-12,'no_external_work_J':1e-12,'fixed_gap_mm':1e-10,'force_zero_N':1e-5,
        'free_axis_reaction_N_ms':1e-10,'other_axis_momentum_N_ms':1e-10,'initial_fraction':1e-6,
        'maximum_solver_dt_relative_tolerance':1e-5,'csv_time_difference_tolerance_ms':2e-8,'end_coverage_steps':2,
        'turn_time_steps':2,'signed_D_tolerance':None,'quantized_D_rule':'Exact nearest IEEE32 cell: D_upper >=0 on every row; in historically elastic phase D_lower<=0<=D_upper',
        'time_end_rule':'Exact nearest IEEE32 time cell intersects [requested_end-2*maximum_dt,requested_end]',
        'raw_signed_D_J_reported_without_override':1e-10}
    cfg['comparison_times_ms']={'FREE_MIXED_ARREST':[.006,.008,.01,.011],'FREE_MIXED_ELASTIC_RETURN':[.001,.002,.003,.0039]}
    cfg['binary_schema']=read(j.CFG)['schema'];cfg['binary_reader_sha256']=h.sha(ROOT/'wtc1_simulation_v8/scripts/decode_impact_i02i_t01.py')
    cfg['precision_policy']={'nearest_rounding_assumed':True,'interval_arithmetic':'Exact rational dyadic cells, squared Fx/Kt and Fy/Kn; J conversion rational 1/1000',
        'raw_signs_retained':True,'old_I_J_gates_not_reassessed':True,'no_phase_shift':True,'no_clipping':True,
        'all_values_must_reproduce_original_6e_CSV':True,'official_schema_verified':False}
    cfg['qualification'].update(mixed_mode_dissipation_calibrated=False,physical_fracture_calibrated=False,
        physical_propagation_qualified=False,numerical_pure_normal_witness_only=False,numerical_two_independent_modes_only=True)
    cfg['sources'].append({'id':'K_OWN_REFERENCE','use':'Separable X/Y exact reference, RK4 and energy/impulse independently checked before engines'})
    h.dump(CFG,cfg);h.dump(OUT/'declaration_guard.json',{'created_utc':h.NOW(),'pass':True,'config_sha256':h.sha(CFG),
        'reference_sha256':cfg['reference_guard_sha256'],'no_engine_before_reference':not any((OUT/c['id']).exists() for c in cfg['cases'])})
    h.dump(OUT/'source_manifest.json',{'created_utc':h.NOW(),'sources':cfg['sources'],
        'cached_I_source_manifest_sha256':h.sha(j.i.OUT/'source_manifest.json'),'cached_J_source_manifest_sha256':h.sha(j.OUT/'source_manifest.json'),
        'no_new_physical_property':True,'no_new_primary_source_required':True,'copyright_documentation_not_redistributed':True,
        'upstream_converter_code_unavailable_limitation_retained':True})
    print(json.dumps({'declared':'IMPACT-I02I-K','fresh_cases':4,'no_damaged_state_modified':True}),flush=True)

def generate(cfg,c,folder):
    previous=h.FRACCFG
    try:h.FRACCFG=CFG;meta=h.generate(cfg,c,folder)
    finally:h.FRACCFG=previous
    h.dump(folder/'generation_parent_H.json',meta);old=meta['name'];name='I02IK_'+c['id'];deck=h.g.f.inherited.deck
    for suffix in ['_0000.rad','_0001.rad']:
        p=folder/(old+suffix);new=folder/(name+suffix);assert not new.exists()
        lines=p.read_text(encoding='utf-8').replace(old,name).splitlines()
        if suffix=='_0000.rad':
            k=lines.index('/BCS/2');lines[k+1]='FREE_XY_BLOCK_Z_ROT';lines[k+2]=f"{'001':>6}{'111':>4}"+deck.ii(0,2)
            k=lines.index('/INIVEL/TRA/90/1');lines[k+2]=deck.ff(c['initial_vX_mm_per_ms'],c['initial_velocity_mm_per_ms'],0)+deck.ii(2,0)
            assert not any('/IMPDISP' in line for line in lines)
        new.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n');p.unlink()
    meta.update(name=name,config_sha256=h.sha(CFG),generator_sha256=h.sha(__file__),no_restart=True,
        history_properties_unchanged=True,expected_no_separation=True,two_free_axes=True,no_imposed_moving_X=True,no_imposed_moving_Y=True,
        initial_vX_mm_per_ms=c['initial_vX_mm_per_ms'],initial_vY_mm_per_ms=c['initial_velocity_mm_per_ms'])
    h.dump(folder/'generation.json',meta);return meta

def run():
    cfg=read(CFG);assert h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256']
    assert not (OUT/'execution_complete.json').exists(),'Reuse completed solves'
    old=h.g.f.OUT,h.g.f.CFG,h.g.f.generate
    try:h.g.f.OUT,h.g.f.CFG,h.g.f.generate=OUT,CFG,generate;h.g.f.run()
    finally:h.g.f.OUT,h.g.f.CFG,h.g.f.generate=old

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['initialize','declare','run']);args=p.parse_args();globals()[args.action]()
