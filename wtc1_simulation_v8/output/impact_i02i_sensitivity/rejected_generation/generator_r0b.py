"""I02I-E: fresh bounded speed, fixed-area penalty and refined-domain cases.

The declared plan from D is immutable. This wrapper records effective case
configurations and replaces only the new decks' title and history interval.
No old solver case or damaged state is imported or overwritten.
"""
from __future__ import annotations
import argparse, copy, json, os, re, subprocess, time
from pathlib import Path
import run_impact_i02i_sampling as common
import run_impact_i02i_fixed_penalty as generator

ROOT, RUNTIME = common.ROOT, common.RUNTIME
NOW, sha, dump, rel, harness = common.NOW, common.sha, common.dump, common.rel, common.harness
PLAN = ROOT/'wtc1_simulation_v8/data/impact_i02i_sensitivity_plan.json'
CFG = ROOT/'wtc1_simulation_v8/data/impact_i02i_sensitivity_predeclaration.json'
OUT = ROOT/'wtc1_simulation_v8/output/impact_i02i_sensitivity'
D = ROOT/'wtc1_simulation_v8/output/impact_i02i_energy'
C = common.OUT

def declare():
    assert not CFG.exists() and not OUT.exists(), 'Never overwrite an iteration'
    hv=harness();state=json.loads((ROOT/'harness/state.json').read_text(encoding='utf-8'))
    assert state['current_iteration']=='IMPACT-I02I-D' and state['next_iteration']=='IMPACT-I02I-E'
    plan=json.loads(PLAN.read_text(encoding='utf-8'));assert sha(ROOT/plan['baseline']['configuration'])==plan['baseline']['sha256']
    cfg=json.loads(common.CFG.read_text(encoding='utf-8'))
    cfg.update(id='IMPACT-I02I-E',seed=plan['seed'],random_draws=0,scope=plan['scope'],plan_path=rel(PLAN),plan_sha256=sha(PLAN))
    cfg['controls']=[];cfg['cases']=[]
    cfg['execution'].update(history_dt_ms=.00001,maximum_case_wall_seconds=plan['cost']['maximum_case_wall_seconds'],maximum_campaign_wall_seconds=60*plan['cost']['maximum_campaign_wall_minutes'],expected_wall_minutes=plan['cost']['expected_wall_minutes'],absolute_cost_ceiling_minutes=plan['cost']['maximum_campaign_wall_minutes'])
    cfg['comparison']['common_displacements_mm']=plan['numerical_comparisons']['common_displacements_mm']
    cfg['comparison']['common_nodal_advances_mm']=plan['numerical_comparisons']['common_nodal_advances_mm']
    cfg['gates'].update(maximum_mesh_force_difference_fraction=.05,maximum_time_force_difference_fraction=.05,maximum_mesh_work_difference_fraction=.05,maximum_mesh_ctoa_difference_fraction=.1,maximum_time_ctoa_difference_fraction=.1)
    cfg['gates']['maximum_spring_work_quadrature_fraction']=.005
    cfg['history_rule']='Fixed requested TFILE interval 0.00001 ms, independent of loading duration; verify interval <= minimum solved dt and rows = engine cycles, retain failures'
    cfg['publication'].update(baseline_iteration='IMPACT-I02I-C',this_iteration_count_since_baseline=2)
    cfg['invariants']=plan['invariants'];cfg['diagnostics']['deferred']=['Gf15/60','post-deactivation free-body inertia qualification','thermal branch']
    for factor in plan['factors_one_at_a_time']:
        for interpretation in factor['interpretations']:
            prefix='ENG' if interpretation=='engineering' else 'TRUE'
            case=copy.deepcopy(next(c for c in json.loads(common.CFG.read_text(encoding='utf-8'))['cases'] if c['interpretation']==interpretation))
            case.update(id=prefix+'_'+factor['name'].upper()+'_R1',factor=factor['name'],cached_C_case=prefix+'_DENSE_R1',factor_specification=factor)
            if factor['name']=='speed':case['loading_end_ms']=factor['loading_ms']
            cfg['cases'].append(case)
    cfg['qualification'].update(physical_material_calibrated=False,fracture_propagation_qualified=False,aircraft_facade_qualified=False,mixed_mode_dissipation_calibrated=False,post_deactivation_inertia_qualified=False)
    entries={}
    for name in ['preservation_before.json','artifact_manifest.json']:
        for row in json.loads((D/name).read_text(encoding='utf-8'))['files']:
            assert sha(ROOT/row['path'])==row['sha256'],row['path'];entries[row['path']]=row
    for p in [D/'preservation_before.json',D/'artifact_manifest.json',D/'publication_verification.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_D_HANDOFF.md']:
        entries[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    OUT.mkdir();dump(CFG,cfg);dump(OUT/'harness_before.json',hv)
    dump(OUT/'preservation_before.json',{'created_utc':NOW(),'scope':'Pinned D and predecessor manifests only, no source archive scan or old solver rerun','files':list(entries.values())})
    for name in ['state.json','experiments/registry.jsonl','publication_cycle.json']:(OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':cfg['sources'],'reused_C_source_manifest':rel(C/'source_manifest.json'),'reused_C_source_manifest_sha256':sha(C/'source_manifest.json'),'D_energy_diagnostic':rel(D/'verification_r1/summary.json'),'D_energy_diagnostic_sha256':sha(D/'verification_r1/summary.json'),'no_new_measurement_or_constitutive_identification':True})
    print(json.dumps({'declared':cfg['id'],'new_cases':len(cfg['cases']),'preserved_files':len(entries),'cost_ceiling_seconds':cfg['execution']['maximum_campaign_wall_seconds']}),flush=True)

def effective_configuration(cfg,case):
    effective=copy.deepcopy(cfg);spec=case['factor_specification']
    if case['factor'] in ['penalty_half','penalty_double']:
        effective['seam']['normal_penalty_N_per_mm3']=spec['Kn_N_per_mm3']
        effective['seam']['tangent_penalty_N_per_mm3']=spec['Kt_N_per_mm3']
    elif case['factor']=='domain':
        effective['mesh']['outer_x_break_mm']=spec['outer_x_break_mm']
        effective['mesh']['near_seam_half_height_mm']=spec['near_seam_half_height_mm']
        effective['comparison']['refined_domain_maximum_area_advance_mm']=spec['refined_domain_maximum_area_advance_mm']
    effective['cases']=[case]
    return effective

def generate(cfg,case,folder):
    effective=effective_configuration(cfg,case);epath=folder/'effective_configuration.json';dump(epath,effective)
    meta=generator.generate(effective,case,folder);oldname=meta['name'];newname='I02IE_'+case['id']
    for suffix in ['_0000.rad','_0001.rad']:
        oldpath=folder/(oldname+suffix);text=oldpath.read_text(encoding='utf-8').replace(oldname,newname)
        if suffix=='_0001.rad':
            lines=text.splitlines();j=lines.index('/TFILE/4');lines[j+1]=generator.i02g.ff(cfg['execution']['history_dt_ms']);text='\n'.join(lines)+'\n'
        # Only this newly generated deck is renamed; no prior artifact touched.
        newpath=folder/(newname+suffix);newpath.write_text(text,encoding='utf-8',newline='\n');oldpath.unlink()
    base=json.loads((C/case['cached_C_case']/'generation.json').read_text(encoding='utf-8'))
    # JSON readback turns generator tuples into lists. Compare serialized
    # coordinates/topology so the gate measures geometry rather than containers.
    same_mesh=json.dumps(meta['nodes_mm'])==json.dumps(base['nodes_mm']) and meta['shells']==base['shells']
    checks={'initial_geometry_mass_unchanged':meta['expected_mass_g']==base['expected_mass_g'],'material_and_measure_convention_unchanged':meta['material_applied']==base['material_applied'] and meta['conversion_ledger']==base['conversion_ledger'],'shell_options_unchanged':meta['shell_options']==base['shell_options'],'Gf_deltaf_unchanged':case['Gf_N_per_mm']==30. and meta['deltaf_mm']==base['deltaf_mm'],'positive_shell_areas':meta['mesh']['minimum_signed_area_mm2']>0,'mesh_unchanged_or_declared_domain':same_mesh or case['factor']=='domain','fixed_reference_ligament_area':abs(sum(p['area_mm2'] for p in meta['seam_pairs'])-2.3*(76.2-25.4))<1e-9,'penalties_match_effective_config':all(abs(p['normal_stiffness_N_per_mm']/p['area_mm2']-effective['seam']['normal_penalty_N_per_mm3'])<1e-8 and abs(p['tangent_stiffness_N_per_mm']/p['area_mm2']-effective['seam']['tangent_penalty_N_per_mm3'])<1e-8 for p in meta['seam_pairs']),'guards_at_declared_refinement_boundary':all(abs(abs(g['x_mm'])-effective['mesh']['outer_x_break_mm'])<1e-9 for g in meta['guards'])}
    dump(folder/'generation_checks.json',checks)
    assert all(checks.values()),checks
    meta['predecessor_provenance']={'generator_sha256':meta['generator_sha256'],'configuration_sha256':meta['config_sha256']}
    meta.update(name=newname,config_sha256=sha(CFG),effective_configuration_path=rel(epath),effective_configuration_sha256=sha(epath),generator_sha256=sha(__file__),parent_generator_sha256=sha(generator.__file__),history_interval_ms=cfg['execution']['history_dt_ms'],generation_checks=checks,initial_state='fresh zero state; no restart or damaged-property change')
    dump(folder/'generation.json',meta)
    return meta

def campaign(case_id=None):
    cfg=json.loads(CFG.read_text(encoding='utf-8'));harness()
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m',PYTHONDONTWRITEBYTECODE='1')
    for case in cfg['cases']:
        if case_id and case['id']!=case_id:continue
        folder=OUT/case['id']
        if folder.exists():
            assert (folder/'execution.json').exists() and not (folder/'timeout.json').exists(),'Incomplete fresh attempt preserved; never silently rerun'
            records=json.loads((folder/'execution.json').read_text(encoding='utf-8'));assert len(records)==3 and all(r['returncode']==0 for r in records)
            print(json.dumps({'cached_new_case':case['id'],'no_rerun':True}),flush=True);continue
        prior=sum(r['seconds'] for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text(encoding='utf-8')))
        # Cost limit is the total executable wall time; timeout uses remaining
        # case and campaign allowances, not a new allowance for each executable.
        remaining=cfg['execution']['maximum_campaign_wall_seconds']-prior
        if remaining<=0:
            dump(OUT/'campaign_cost_stop.json',{'created_utc':NOW(),'completed_execution_seconds':prior,'next_unstarted_case':case['id'],'scope':'remaining cases deferred; no new case launched'});return
        folder.mkdir();meta=generate(cfg,case,folder);records=[];case_tick=time.perf_counter()
        print(json.dumps({'starting':case['id'],'nodes':len(meta['nodes_mm']),'shells':len(meta['shells']),'springs':len(meta['seam_pairs']),'loading_end_ms':meta['loading_end_ms'],'Kn_N_per_mm3':effective_configuration(cfg,case)['seam']['normal_penalty_N_per_mm3']}),flush=True)
        for exe,args,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
            tick=time.perf_counter();timeout=min(cfg['execution']['maximum_case_wall_seconds']-(tick-case_tick),remaining-(tick-case_tick))
            assert timeout>0,'Cost exhausted before executable launch'
            try:p=subprocess.run([str(RUNTIME/exe),*args],cwd=folder,env=env,capture_output=True,timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                (folder/log).write_bytes((exc.stdout or b'')+(exc.stderr or b''));dump(folder/'timeout.json',{'created_utc':NOW(),'executable':exe,'remaining_timeout_seconds':timeout,'partial_solver_artifacts_retained':True});raise
            (folder/log).write_bytes(p.stdout+p.stderr);records.append({'command':[str(RUNTIME/exe),*args],'returncode':p.returncode,'seconds':time.perf_counter()-tick,'executable_sha256':sha(RUNTIME/exe)});dump(folder/'execution.json',records)
            assert p.returncode==0,log
            if exe.startswith('starter'):
                txt=(folder/(meta['name']+'_0000.out')).read_text(errors='replace');warnings=re.findall(r'^\s*WARNING ID\s*:\s*(\d+)',txt,re.M)
                reviewed=len(warnings)==len(meta['seam_pairs']) and set(warnings)=={'445'} and txt.count('NULL INERTIA')==len(meta['seam_pairs'])
                ok=not re.search('ERROR ID',txt) and 'unsupported field' not in txt.lower() and (not warnings or reviewed)
                dump(folder/'preflight.json',{'pass':bool(ok),'warning_ids':warnings,'reviewed_445_only_massless_springs_all_rotations_blocked':bool(reviewed),'generation_checks':meta['generation_checks']});assert ok,'Preflight blocks engine'
        print(json.dumps({'completed':case['id'],'seconds':sum(r['seconds'] for r in records)}),flush=True)
    dump(OUT/'execution_complete.json',{'created_utc':NOW(),'expected_cases':len(cfg['cases']),'all_expected_completed':all((OUT/c['id']/'converter.log').exists() for c in cfg['cases']),'execution_seconds':sum(r['seconds'] for p in OUT.glob('*/execution.json') for r in json.loads(p.read_text(encoding='utf-8'))),'no_old_case_rerun':True})

def main():
    p=argparse.ArgumentParser();p.add_argument('--declare',action='store_true');p.add_argument('--campaign',action='store_true');p.add_argument('--case');a=p.parse_args()
    if a.declare:declare()
    elif a.campaign or a.case:campaign(a.case)
    else:p.error('Choose --declare, --campaign or --case')

if __name__=='__main__':main()
