"""I02I-H staged fresh free controls. Declare/audit elastic before fracture.

The fracture declaration is immutable and conditional on a saved strict
elastic audit and independently checked analytic reference. No old solve.
"""
from __future__ import annotations
import argparse,copy,json
from pathlib import Path
import run_impact_i02i_table_free as g

ROOT,RUNTIME,NOW,sha,dump,rel,harness=g.ROOT,g.RUNTIME,g.NOW,g.sha,g.dump,g.rel,g.harness
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_free_fracture'
ELCFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_h_elastic_predeclaration.json'
FRACCFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_h_fracture_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_h_plan_from_g.json'

def declare_elastic():
    assert not OUT.exists() and not ELCFG.exists(),'Never overwrite iterations'
    hv=harness();state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-G' and state['next_iteration']=='IMPACT-I02I-H'
    cfg=copy.deepcopy(json.loads(g.CFG.read_text(encoding='utf-8')))
    cfg.update(id='IMPACT-I02I-H-ELASTIC',declared_utc=NOW(),seed=1102016,random_draws=0,
        scope='Two fresh free elastic X controls with all raw channels <=1%; fracture conditional and undeclared')
    old=next(c for c in cfg['cases'] if c['id']=='FREE_ELASTIC_050NS');cases=[]
    for cap,label in [(.000025,'025NS'),(.0000125,'012P5NS')]:
        c=copy.deepcopy(old);c.update(id='ELASTIC_'+label,stage='elastic',maximum_dt_ms=cap);cases.append(c)
    cfg['cases']=cases
    for k in ['free_displacement_fraction','free_nodal_velocity_fraction','free_force_fraction','free_global_momentum_fraction','free_impulse_fraction','free_nodal_global_momentum_fraction']:
        cfg['gates'][k]=.01
    cfg['gates']['elastic_step_scaling_relative_tolerance']=.10
    cfg['predeclared_tolerance_rationale']={'raw_fields':'All raw elastic amplitudes and initial-P impulse residuals <=1%; no output time shift. Energy/period <=0.5%.',
        'scaling':'Compared to cached G 50 ns, displacement/global P/energy errors expected to scale h^2; velocity/impulse h, within 10% relative. Keep failures.'}
    cfg['saved_G_baseline']={'path':rel(g.OUT/'verification_r1/summary.json'),'sha256':sha(g.OUT/'verification_r1/summary.json'),'case':'FREE_ELASTIC_050NS'}
    cfg['qualification'].update(free_elastic_control_only=True,free_fracture_qualified=False)
    cfg['sources']=cfg['sources']+[{'id':'H_ANALYTIC_REFERENCE','use':'Own exact derivation and independent quadrature, to be checked before any free fracture declaration'}]
    rows={}
    for p in [g.OUT/'preservation_before.json',g.OUT/'artifact_manifest.json']:
        for r in json.loads(p.read_text(encoding='utf-8'))['files']:
            assert sha(ROOT/r['path'])==r['sha256'],r['path'];rows[r['path']]=r
    for p in [g.OUT/'preservation_before.json',g.OUT/'artifact_manifest.json',g.OUT/'publication_verification.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_G_HANDOFF.md']:
        rows[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    OUT.mkdir();dump(ELCFG,cfg);dump(OUT/'harness_before.json',hv)
    dump(OUT/'preservation_before.json',{'created_utc':NOW(),'files':list(rows.values()),'scope':'Saved G/predecessor inventories; no archive scan'})
    for n in g.f.ADMIN:(OUT/('before_'+Path(n).name)).write_bytes((ROOT/'harness'/n).read_bytes())
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':cfg['sources'],
        'cached_G_sources':rel(g.OUT/'source_manifest.json'),'cached_G_sha256':sha(g.OUT/'source_manifest.json'),
        'no_new_physical_property':True,'REACX_documentation_runtime_discrepancy_retained':True,
        'copyright_documentation_not_redistributed':True})
    print(json.dumps({'declared':cfg['id'],'fresh_elastic_cases':2,'old_files_pinned':len(rows)}),flush=True)

def declare_fracture():
    assert not FRACCFG.exists(),'Preserve declaration'
    s=json.loads((OUT/'elastic_verification_r1/summary.json').read_text())
    reference=json.loads((OUT/'reference_verification.json').read_text())
    assert s['all_checks_pass'] and reference['pass'],'Strict elastic and analytic guards must both pass'
    cfg=copy.deepcopy(json.loads(ELCFG.read_text(encoding='utf-8')))
    cfg.update(id='IMPACT-I02I-H-FRACTURE',declared_utc=NOW(),scope='Two fresh free Y normal separation witnesses, no mixed shear or aircraft transfer')
    cfg['cases']=[{'id':name,'stage':'normal','maximum_dt_ms':cap,'dt_scale':.2,'fails':True,'end_ms':.012,'initial_velocity_mm_per_ms':30.}
        for name,cap in [('NORMAL_050NS',.00005),('NORMAL_025NS',.000025)]]
    cfg['reference']=reference['parameters'];cfg['reference_verified_sha256']=sha(OUT/'reference_verification.json')
    cfg['elastic_guard_sha256']=sha(OUT/'elastic_verification_r1/summary.json')
    cfg['gates'].update(normal_displacement_fraction=.01,normal_velocity_fraction=.01,normal_force_fraction=.01,
        normal_momentum_fraction=.01,normal_impulse_fraction=.01,normal_energy_fraction=.005,
        normal_work_fraction=.005,normal_post_failure_velocity_fraction=.01,normal_final_IE_fraction=.005,
        normal_off_time_steps=2,normal_final_comparison_fraction=.005,normal_y_path_monotone_tolerance_mm=1e-10,
        no_external_work_J=1e-12,other_axis_momentum_N_ms=1e-10)
    cfg['gates']['csv_time_difference_tolerance_ms']=2e-8
    cfg['qualification'].update(free_elastic_control_only=False,free_fracture_qualified=False,
        numerical_pure_normal_witness_only=True,mixed_mode_dissipation_calibrated=False,physical_propagation_qualified=False)
    cfg['predeclared_tolerance_rationale']={'reference':'Analytic monotone elastic/softening path with ideal retained work; E0=.045 J > normal work .03 J, v never zero.',
        'raw_fields':'1% of declared amplitude; no phase fitting. Energy and normal work 0.5%. OFF time within two coarse steps; no end extrapolation.',
        'interpretation':'Numerical pure-normal constitutive/inertia witness only; IE retained is not measured physical fracture energy.'}
    dump(FRACCFG,cfg);dump(OUT/'fracture_declaration_guard.json',{'created_utc':NOW(),'pass':True,
        'elastic_summary_sha256':cfg['elastic_guard_sha256'],'reference_sha256':cfg['reference_verified_sha256'],
        'no_fracture_engine_before_guard':not any((OUT/c['id']).exists() for c in cfg['cases'])})
    print(json.dumps({'declared':cfg['id'],'analytic_failure_time_ms':cfg['reference']['failure_time_ms'],'fresh_fracture_cases':2}),flush=True)

def generate(cfg,c,folder):
    d=g.f.inherited;deck=d.deck;config=ELCFG if c['stage']=='elastic' else FRACCFG
    if c['stage']=='elastic':
        prev=g.CFG
        try:g.CFG=config;temp=copy.deepcopy(c);temp['stage']='free';meta=g.generate(cfg,temp,folder)
        finally:g.CFG=prev
    else:
        prev=d.CFG;temp=copy.deepcopy(c);temp.update(x_mm=[0,0],y_deltaf=[0,0],expected_final='normal_only')
        try:d.CFG=config;meta=d.generate(cfg,temp,folder)
        finally:d.CFG=prev
    dump(folder/'generation_parent.json',meta);old=meta['name'];name='I02IH_'+c['id']
    for suffix in ['_0000.rad','_0001.rad']:
        p=folder/(old+suffix);lines=p.read_text(encoding='utf-8').replace(old,name).splitlines()
        if c['stage']=='normal':
            if suffix=='_0000.rad':
                j=lines.index('/BCS/2');lines[j+1]='FREE_Y_BLOCK_XZ_ROT';lines[j+2]=f"{'101':>6}{'111':>4}"+deck.ii(0,2)
                j=lines.index('/FUNCT/90');k=lines.index('/TH/SPRING/2');del lines[j:k]
                j=lines.index('/TH/SPRING/2');lines[j:j]=['/INIVEL/TRA/90/1','INITIAL_FREE_Y',deck.ff(0,c['initial_velocity_mm_per_ms'],0)+deck.ii(2,0),deck.ff(0)+deck.ii(0)]
                assert not any('/IMPDISP' in line for line in lines)
            else:
                j=lines.index('/MON/ON');lines[j:j]=['/DTIX',deck.ff(c['maximum_dt_ms'],c['maximum_dt_ms'])]
                lines[lines.index('/RUN/'+name+'/1')+1]=deck.ff(c['end_ms'])
        new=folder/(name+suffix);assert not new.exists();new.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n');p.unlink()
    meta.update(name=name,case=c,config_sha256=sha(config),generator_sha256=sha(__file__),end_ms=c['end_ms'],x_path=[],y_path=[],fresh_state=True,
        no_imposed_moving_X=True,no_imposed_moving_Y=True,fracture_disabled=c['stage']=='elastic',
        maximum_dt_ms=c['maximum_dt_ms'],stage=c['stage'],inherited_generator_sha256=sha(g.__file__ if c['stage']=='elastic' else d.__file__))
    dump(folder/'generation.json',meta);return meta

def run_stage(stage):
    config=ELCFG if stage=='elastic' else FRACCFG;endfile=OUT/('execution_'+stage+'_complete.json')
    assert not endfile.exists(),'Use saved stage; never repeat completed solves'
    cfg=json.loads(config.read_text(encoding='utf-8'))
    if stage=='normal':
        assert sha(OUT/'elastic_verification_r1/summary.json')==cfg['elastic_guard_sha256']
        assert sha(OUT/'reference_verification.json')==cfg['reference_verified_sha256']
    prev=g.f.OUT,g.f.CFG,g.f.generate
    try:g.f.OUT,g.f.CFG,g.f.generate=OUT,config,generate;g.f.run()
    finally:g.f.OUT,g.f.CFG,g.f.generate=prev
    (OUT/'execution_complete.json').rename(endfile)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare_elastic','run_elastic','declare_fracture','run_fracture']);a=p.parse_args()
    if a.action=='run_elastic':run_stage('elastic')
    elif a.action=='run_fracture':run_stage('normal')
    else:globals()[a.action]()
