"""I02I-F: fresh imposed-motion TYPE8 witnesses with a maximum time step.

No old solver rerun, added mass, restart, or damaged-state property change.
Sequential actions: declare, run; auditing and registration are separate.
"""
from __future__ import annotations
import argparse, copy, json, os, re, subprocess, time, urllib.request
from pathlib import Path
import run_impact_i02i_energy as inherited

ROOT, RUNTIME = inherited.ROOT, inherited.RUNTIME
NOW, sha, dump, rel, harness = inherited.NOW, inherited.sha, inherited.dump, inherited.rel, inherited.harness
E = ROOT/'wtc1_simulation_v8/output/impact_i02i_sensitivity'
D = inherited.OUT
OUT = ROOT/'wtc1_simulation_v8/output/impact_i02i_dtcap'
CFG = ROOT/'wtc1_simulation_v8/data/impact_i02i_dtcap_predeclaration.json'
ADMIN = ['state.json','experiments/registry.jsonl','publication_cycle.json']
SOURCE_URL = 'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/dtix_engine_r.htm'

def declare():
    assert not CFG.exists() and not OUT.exists(), 'Never overwrite an iteration'
    hv=harness();state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-E' and state['next_iteration']=='IMPACT-I02I-F'
    cfg=copy.deepcopy(json.loads(inherited.CFG.read_text(encoding='utf-8')))
    cfg.update(id='IMPACT-I02I-F',seed=1102014,random_draws=0,
        scope='Fresh imposed two-node controls: maximum time step through whole-element deactivation, no free aircraft impact')
    wanted=[('FIXED_CAP200NS','MIXED_FIXED_SHEAR_FAILURE',.0002),
        ('FIXED_CAP100NS','MIXED_FIXED_SHEAR_FAILURE',.0001),
        ('FIXED_CAP050NS','MIXED_FIXED_SHEAR_FAILURE',.00005),
        ('PROP_CAP100NS','MIXED_PROP_HALF_DT',.0001),
        ('PROP_CAP050NS','MIXED_PROP_HALF_DT',.00005),
        ('AFTER_CAP100NS','SHEAR_AFTER_FAILURE',.0001),
        ('AFTER_CAP050NS','SHEAR_AFTER_FAILURE',.00005),
        ('RETURN_CAP100NS','SHEAR_RETURN',.0001)]
    old={c['id']:c for c in cfg['cases']};cases=[]
    for name,base,cap in wanted:
        case=copy.deepcopy(old[base]);case.update(id=name,cached_D_case=base,dt_scale=.2,maximum_dt_ms=cap)
        cases.append(case)
    cfg['cases']=cases
    cfg['execution'].update(history_dt_ms=.000001,maximum_case_wall_seconds=90,
        maximum_campaign_wall_seconds=600,expected_wall_minutes=[1,5],
        maximum_time_step_keyword='/DTIX',initial_dt_equals_maximum=True)
    cfg['gates'].update(maximum_solver_dt_relative_tolerance=1e-5,
        csv_time_difference_tolerance_ms=.000002,end_coverage_steps=2,
        impulse_boundary_fraction=.01,nodal_momentum_fraction=.01,
        added_mass_g=1e-12,comparison_energy_fraction=.005,
        after_failure_impulse_comparison_fraction=.01)
    cfg['qualification'].update(post_deactivation_free_inertia_qualified=False,
        prescribed_motion_is_not_free_release=True,E_sensitivity_gates_closed=False)
    cfg['sources'].append({'id':'ALTAIR_DTIX_2026','url':SOURCE_URL,
        'use':'Initial and maximum step, without mass scaling; confirm actual TIME STEP through deletion'})
    cfg['comparison_common_post_failure_times_ms']=[1.1,1.25,1.5,1.75,1.9,2.]
    cfg['comparison_pairs']=[['FIXED_CAP200NS','FIXED_CAP100NS'],
        ['FIXED_CAP100NS','FIXED_CAP050NS'],['PROP_CAP100NS','PROP_CAP050NS'],
        ['AFTER_CAP100NS','AFTER_CAP050NS']]
    cfg['deferred']=['All E failed inertia/angle and missing-coverage gates remain open',
        'Gf15/60','Free-body release and free impact','Source nominal/true convention identification']
    cfg['precision_policy']={'raw_impulse_residual_retained':True,
        'net_momentum_residual_is_diagnostic':True,
        'reason':'Cancellation of two large float32 impulses limits small net momentum; no precision correction promotes a gate',
        'output':'TFILE/4 IEEE32; converter decimal precision and saved TIME STEP both audited'}
    # Read only the saved preservation inventories, never rescan the archive.
    rows={}
    for file in [E/'preservation_before.json',E/'artifact_manifest.json']:
        for r in json.loads(file.read_text(encoding='utf-8'))['files']:
            assert sha(ROOT/r['path'])==r['sha256'],r['path'];rows[r['path']]=r
    for p in [E/'preservation_before.json',E/'artifact_manifest.json',E/'publication_verification.json',
              ROOT/'harness/handoffs/WTC1_IMPACT_I02I_E_HANDOFF.md']:
        rows[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    OUT.mkdir();dump(CFG,cfg);dump(OUT/'harness_before.json',hv)
    dump(OUT/'preservation_before.json',{'created_utc':NOW(),'files':list(rows.values()),
        'scope':'Union of E manifest and saved predecessor pins; no archive scan'})
    for name in ADMIN:(OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    req=urllib.request.Request(SOURCE_URL,headers={'User-Agent':'WTC-simu2026-primary-source-audit'})
    with urllib.request.urlopen(req,timeout=40) as f:data=f.read()
    snapshot=OUT/'sources';snapshot.mkdir();p=snapshot/'altair_dtix_2026.html';p.write_bytes(data)
    assert b'/DTIX' in data and b'Maximum time step' in data
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':cfg['sources'],
        'new_primary_snapshot':{'url':SOURCE_URL,'path':rel(p),'sha256':sha(p),'bytes':len(data)},
        'cached_D_sources':rel(D/'source_manifest.json'),'cached_D_sha256':sha(D/'source_manifest.json'),
        'copyright_documentation_excluded_from_redistribution':True})
    print(json.dumps({'declared':cfg['id'],'cases':len(cases),'old_files_pinned':len(rows)}),flush=True)

def generate(cfg,case,folder):
    # Generate entirely fresh state with the immutable D function. Its temporary
    # name/config binding is confined to this process and this new directory.
    original_cfg=inherited.CFG
    try:
        inherited.CFG=CFG
        meta=inherited.generate(cfg,case,folder)
    finally:inherited.CFG=original_cfg
    dump(folder/'generation_inherited.json',meta)
    old=meta['name'];name='I02IF_'+case['id']
    for suffix in ['_0000.rad','_0001.rad']:
        p=folder/(old+suffix);text=p.read_text(encoding='utf-8').replace(old,name)
        if suffix=='_0001.rad':
            marker='/MON/ON';assert text.count(marker)==1
            text=text.replace(marker,'/DTIX\n'+inherited.deck.ff(case['maximum_dt_ms'],case['maximum_dt_ms'])+'\n'+marker)
        new=folder/(name+suffix);assert not new.exists();new.write_text(text,encoding='utf-8',newline='\n');p.unlink()
    meta.update(name=name,config_sha256=sha(CFG),generator_sha256=sha(__file__),
        inherited_generator_sha256=sha(inherited.__file__),maximum_dt_ms=case['maximum_dt_ms'],
        inherited_function_used_on_fresh_state=True,old_iterations_modified=False)
    dump(folder/'generation.json',meta);return meta

def run():
    cfg=json.loads(CFG.read_text(encoding='utf-8'));harness()
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',
        RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',
        OMP_NUM_THREADS='1',KMP_STACKSIZE='400m',PYTHONDONTWRITEBYTECODE='1')
    for case in cfg['cases']:
        folder=OUT/case['id']
        if folder.exists():
            records=json.loads((folder/'execution.json').read_text(encoding='utf-8'))
            assert len(records)==3 and all(r['returncode']==0 for r in records),'Preserve incomplete attempt'
            print(json.dumps({'cached_new_case':case['id'],'no_rerun':True}),flush=True);continue
        total=sum(r['seconds'] for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text()))
        assert total<cfg['execution']['maximum_campaign_wall_seconds'],'Campaign ceiling'
        folder.mkdir();meta=generate(cfg,case,folder);records=[];case_start=time.perf_counter()
        for exe,args,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),
                ('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),
                ('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
            available=min(cfg['execution']['maximum_case_wall_seconds']-(time.perf_counter()-case_start),
                cfg['execution']['maximum_campaign_wall_seconds']-total-sum(r['seconds'] for r in records))
            assert available>0,'Declared executable ceiling reached'
            tick=time.perf_counter()
            try:p=subprocess.run([str(RUNTIME/exe),*args],cwd=folder,env=env,capture_output=True,timeout=available)
            except subprocess.TimeoutExpired as exc:
                (folder/log).write_bytes((exc.stdout or b'')+(exc.stderr or b''))
                dump(folder/'timeout.json',{'executable':exe,'seconds_limit':available,'preserved':True});raise
            (folder/log).write_bytes(p.stdout+p.stderr)
            records.append({'command':[str(RUNTIME/exe),*args],'returncode':p.returncode,
                'seconds':time.perf_counter()-tick,'executable_sha256':sha(RUNTIME/exe)})
            dump(folder/'execution.json',records);assert p.returncode==0,log
            if exe.startswith('starter'):
                txt=(folder/(meta['name']+'_0000.out')).read_text(errors='replace')
                warnings=re.findall(r'^\s*WARNING ID\s*:\s*(\d+)',txt,re.M)
                ok=not warnings and not re.search('ERROR ID',txt) and 'unsupported field' not in txt.lower()
                dump(folder/'preflight.json',{'pass':bool(ok),'warning_ids':warnings,'all_warnings_block_engine':True});assert ok,'Preflight'
        print(json.dumps({'case':case['id'],'seconds':sum(r['seconds'] for r in records)}),flush=True)
    dump(OUT/'execution_complete.json',{'created_utc':NOW(),'completed_cases':len(cfg['cases']),
        'no_old_solver_rerun':True,'runtime_seconds':sum(r['seconds'] for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text()))})

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);a=p.parse_args();globals()[a.action]()
if __name__=='__main__':main()
