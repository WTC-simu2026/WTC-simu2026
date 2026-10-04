"""I: four fresh normal arrest/elastic return witnesses, immutable declarations."""
from __future__ import annotations
import argparse,copy,json,math
from pathlib import Path
import run_impact_i02i_free_fracture as h
import reference_impact_i02i_free_return as ref

ROOT,OUT,CFG=ref.ROOT,ref.OUT,ref.CFG
PLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_i_plan_from_h.json'

def initialize():
    assert not OUT.exists() and not CFG.exists(),'Never overwrite iteration'
    hv=h.harness();state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-H' and state['next_iteration']=='IMPACT-I02I-I'
    plan=json.loads(PLAN.read_text());assert h.sha(ROOT/plan['saved_H_summary'])==plan['saved_H_sha256']
    rows={}
    for p in [h.OUT/'preservation_before.json',h.OUT/'artifact_manifest.json']:
        for r in json.loads(p.read_text(encoding='utf-8'))['files']:
            assert h.sha(ROOT/r['path'])==r['sha256'],r['path'];rows[r['path']]=r
    for p in [h.OUT/'preservation_before.json',h.OUT/'artifact_manifest.json',h.OUT/'publication_verification.json',
        ROOT/'harness/handoffs/WTC1_IMPACT_I02I_H_HANDOFF.md']:
        rows[h.rel(p)]={'path':h.rel(p),'bytes':p.stat().st_size,'sha256':h.sha(p)}
    OUT.mkdir();h.dump(OUT/'harness_before.json',hv)
    h.dump(OUT/'preservation_before.json',{'created_utc':h.NOW(),'files':list(rows.values()),'scope':'Saved H and predecessor manifests only; no archive scan'})
    for n in h.g.f.ADMIN:(OUT/('before_'+Path(n).name)).write_bytes((ROOT/'harness'/n).read_bytes())
    print(json.dumps({'initialized':'IMPACT-I02I-I','old_files_pinned':len(rows)}),flush=True)

def declare():
    assert not CFG.exists(),'Preserve declaration'
    r=json.loads((OUT/'reference_verification.json').read_text());assert r['pass']
    cfg=copy.deepcopy(json.loads(h.FRACCFG.read_text(encoding='utf-8')))
    for k in ['reference','reference_verified_sha256','elastic_guard_sha256','free_reference','saved_F_baseline',
        'saved_G_baseline','comparison_common_post_failure_times_ms','comparison_pairs','audit_alignment_before_execution']:
        cfg.pop(k,None)
    cfg.update(id='IMPACT-I02I-I',seed=1102017,random_draws=0,declared_utc=h.NOW(),
        scope='Fresh normal positive-gap arrest/unload/return and elastic reversible controls; no separation or compression')
    cfg['references']=r['parameters'];cfg['reference_guard_sha256']=h.sha(OUT/'reference_verification.json')
    cfg['plan_sha256']=h.sha(PLAN);cfg['cases']=[]
    for family,v0,end,caps in [('NORMAL_ARREST_RETURN',20.,.012,[(.00005,'050NS'),(.000025,'025NS')]),
        ('NORMAL_SUBPEAK_RETURN',math.sqrt(20),.004,[(.000025,'025NS'),(.0000125,'012P5NS')])]:
        for cap,label in caps:
            cfg['cases'].append({'id':family+'_'+label,'family':family,'stage':'normal','maximum_dt_ms':cap,
                'dt_scale':.2,'fails':True,'expected_OFF':1,'end_ms':end,'initial_velocity_mm_per_ms':v0})
    cfg['gates']={'raw_amplitude_fraction':.01,'energy_fraction':.005,'work_fraction':.005,
        'mass_fraction':1e-5,'added_mass_g':1e-12,'no_external_work_J':1e-12,'fixed_gap_mm':1e-10,
        'other_axis_momentum_N_ms':1e-10,'force_zero_N':1e-5,'maximum_solver_dt_relative_tolerance':1e-5,
        'csv_time_difference_tolerance_ms':2e-8,'end_coverage_steps':2,'initial_fraction':1e-6,
        'turn_time_steps':2,'comparison_fraction':.005,'retained_negative_tolerance_J':1e-10}
    cfg['comparison_times_ms']={'NORMAL_ARREST_RETURN':[.006,.008,.01,.011],
        'NORMAL_SUBPEAK_RETURN':[.001,.002,.003,.0039]}
    cfg['predeclared_tolerance_rationale']={'raw':'Gap, velocity, force, P and initial-P impulse residual <=1% declared amplitude, no phase shift.',
        'energy':'IE+KE, history energy, force-work and analytic energy <=0.5% initial energy; U and unrecovered work explicitly separated.',
        'history':'delta_max retained through unloading and force-zero branch; positive gap only; OFF must remain 1.',
        'comparison':'Two caps per family at declared common covered times, <=0.5% respective amplitude; no extrapolation.'}
    cfg['qualification'].update(numerical_pure_normal_witness_only=True,numerical_unload_only=True,
        physical_fracture_calibrated=False,physical_propagation_qualified=False,mixed_mode_dissipation_calibrated=False)
    cfg['deferred']=['All prior E/F/G failed gates','Both NASA conventions','Gf15/60',
        'Mixed-mode free fracture','Plate/connection wavefield','Boeing/facade/fire/collapse','V11S thermal branch']
    cfg['sources'].append({'id':'I_OWN_REFERENCE','use':'Own positive-gap H2 history derivation, checked by RK4, quadrature, ODE and energy before engines'})
    h.dump(CFG,cfg);h.dump(OUT/'source_manifest.json',{'created_utc':h.NOW(),'sources':cfg['sources'],
        'cached_H_source_manifest':h.rel(h.OUT/'source_manifest.json'),'cached_H_sha256':h.sha(h.OUT/'source_manifest.json'),
        'no_new_physical_property':True,'copyright_documentation_not_redistributed':True})
    h.dump(OUT/'declaration_guard.json',{'pass':True,'created_utc':h.NOW(),'reference_sha256':cfg['reference_guard_sha256'],
        'config_sha256':h.sha(CFG),'no_engine_before_reference':not any((OUT/c['id']).exists() for c in cfg['cases'])})
    print(json.dumps({'declared':cfg['id'],'cases':4,'reference_verified_before_engine':True}),flush=True)

def generate(cfg,c,folder):
    previous=h.FRACCFG
    try:h.FRACCFG=CFG;meta=h.generate(cfg,c,folder)
    finally:h.FRACCFG=previous
    h.dump(folder/'generation_parent_H.json',meta);old=meta['name'];name='I02II_'+c['id']
    for suffix in ['_0000.rad','_0001.rad']:
        p=folder/(old+suffix);new=folder/(name+suffix);assert not new.exists()
        new.write_text(p.read_text(encoding='utf-8').replace(old,name),encoding='utf-8',newline='\n');p.unlink()
    meta.update(name=name,config_sha256=h.sha(CFG),generator_sha256=h.sha(__file__),expected_no_separation=True,
        failure_law_enabled=True,no_restart=True,history_properties_unchanged=True)
    h.dump(folder/'generation.json',meta);return meta

def run():
    cfg=json.loads(CFG.read_text());assert h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256']
    assert not (OUT/'execution_complete.json').exists(),'Reuse completed calculation'
    old=h.g.f.OUT,h.g.f.CFG,h.g.f.generate
    try:h.g.f.OUT,h.g.f.CFG,h.g.f.generate=OUT,CFG,generate;h.g.f.run()
    finally:h.g.f.OUT,h.g.f.CFG,h.g.f.generate=old

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['initialize','declare','run']);args=ap.parse_args();globals()[args.action]()
