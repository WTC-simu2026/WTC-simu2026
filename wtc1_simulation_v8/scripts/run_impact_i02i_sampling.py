"""I02I-C: fresh TYPE8 controls and dense-history replicas; never rerun B."""
from __future__ import annotations
import argparse, copy, csv, hashlib, json, os, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import run_impact_i02i_fixed_penalty as predecessor
import run_impact_i02g as deck

ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_sampling_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_sampling'
B=ROOT/'wtc1_simulation_v8/output/impact_i02i_fixed_penalty'
RUNTIME=predecessor.RUNTIME
NOW=lambda:datetime.now(timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''): h.update(block)
    return h.hexdigest()
def dump(p,v): Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def rel(p): return Path(p).relative_to(ROOT).as_posix()
def harness():
    p=subprocess.run(['pwsh.exe','-NoProfile','-Command',"& './harness/tools/Test-WtcHarness.ps1' | ConvertTo-Json -Depth 8"],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert p.returncode==0,p.stderr
    v=json.loads(p.stdout); assert v['Status']=='PASS',v
    return v

def declare():
    assert not CFG.exists() and not OUT.exists(),'Never overwrite an iteration'
    state=json.loads((ROOT/'harness/state.json').read_text()); assert state['next_iteration']=='IMPACT-I02I-C'
    cfg=json.loads(predecessor.CFG.read_text())
    cfg.update(id='IMPACT-I02I-C',seed=1102011,scope='Bounded output sampling and TYPE8 work diagnostics; unresolved physical propagation. All solver states fresh.')
    cfg['execution'].update(history_dt_ms=.00005,expected_wall_minutes=[10,20],absolute_cost_ceiling_minutes=30,maximum_campaign_wall_seconds=1800,maximum_case_wall_seconds=900)
    cfg['diagnostics']={'control_area_mm2':1.,'control_mass_g':.2,'control_rotational_inertia_g_mm2':.001,'control_segment_ms':1.,'control_dt_scale':.2,'half_control_dt_scale':.1,'control_history_dt_ms':.00005,'control_shear_mm':.02,'normal_force_tolerance_fraction':.005,'work_tolerance_fraction':.005,'dense_work_tolerance_fraction':.005,'output_downsample_dt_ms':[.004,.002,.001,.0005], 'downsample_rule':'first, nearest-at-or-after uniform time-grid targets, last; no inserted fracture events; work trapezoid using recorded forces and elongations','dense_comparison_force_tolerance_fraction':.005,'dense_comparison_work_tolerance_fraction':.005,'trajectory_invariance':'Only TFILE frequency differs from B. Verify common displacement forces/work and actual solver timestep; any difference retained.','deferred':['Gf15/60','penalty or domain change','loading speed qualification','thermal branch'],'hypotheses':'Gf30 and fixed Kn/Kt remain numerical assumptions. No damaged material replacement.'}
    cfg['comparison']['common_displacements_mm']=[.2,.5,.8,1.,1.005,1.01,1.015,1.02,1.025,1.03,1.035,1.04,1.045,1.05,1.1,1.2]
    cfg['controls']=[{'id':k,'kind':kind,'dt_scale':dt} for k,kind,dt in [('NORMAL','normal',.2),('NORMAL_HALF_DT','normal',.1),('CYCLE','cycle',.2),('CYCLE_HALF_DT','cycle',.1),('SHEAR','shear',.2),('MIXED','mixed',.2)]]
    cfg['cases']=[]
    for original,new in [('ENG_L127_R3','ENG_DENSE_R1'),('TRUE_L127_R3','TRUE_DENSE_R1')]:
        case=copy.deepcopy(next(c for c in json.loads(predecessor.CFG.read_text())['cases'] if c['id']==original)); case.update(id=new,cached_B_case=original); cfg['cases'].append(case)
    cfg['sources'].append({'id':'ALTAIR_HARDENING','url':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/stiffness_formulation_spring_hardening_r.htm','use':'H2 uncoupled loading/unloading, linear unloading Ku and zero force plateau'})
    cfg['publication']['this_iteration_count_since_baseline']=2
    dump(CFG,cfg); OUT.mkdir()
    entries={}
    for name in ['preservation_before.json','artifact_manifest.json']:
        for row in json.loads((B/name).read_text())['files']:
            assert sha(ROOT/row['path'])==row['sha256'],row['path']; entries[row['path']]=row
    for p in [B/'preservation_before.json',B/'artifact_manifest.json',B/'publication_verification.json',ROOT/'harness/handoffs/WTC1_IMPACT_I02I_B_HANDOFF.md']:
        entries[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':NOW(),'scope':'Pinned previous manifests only; no archive scan or old solver run','files':list(entries.values())})
    for name in ['state.json','experiments/registry.jsonl','publication_cycle.json']:
        (OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    dump(OUT/'harness_before.json',harness())
    dump(OUT/'source_manifest.json',{'created_utc':NOW(),'sources':cfg['sources'],'predecessor_source_manifest':rel(B/'source_manifest.json'),'predecessor_source_manifest_sha256':sha(B/'source_manifest.json'),'reuse':'Bounded existing NASA pages and saved references; no historical source rescan.'})
    print(json.dumps({'declared':cfg['id'],'protected_files':len(entries),'fresh_controls':6,'fresh_coupons':2}),flush=True)

def smooth_path(targets):
    result=[]
    for segment,(a,b) in enumerate(zip(targets[:-1],targets[1:])):
        for j in range(801):
            if segment and j==0: continue
            s=j/800; q=s*s*s*(10+s*(-15+6*s)); result.append((segment+s,a+(b-a)*q))
    return result

def control_generate(cfg,case,folder):
    d=cfg['diagnostics']; kn=cfg['seam']['normal_penalty_N_per_mm3']; kt=cfg['seam']['tangent_penalty_N_per_mm3']; peak=cfg['seam']['peak_normal_traction_mpa']; gf=30.; df=2*gf/peak; d0=peak/kn
    name='I02IC_'+case['id']; kind=case['kind']
    yn=[0,0] if kind=='shear' else [0,.6*df,.2*df,.6*df,1.05*df] if kind=='cycle' else [0,1.05*df]
    xn=[0,d['control_shear_mm']] if kind in ['shear','mixed'] else [0]*len(yn)
    xp=smooth_path(xn); yp=smooth_path(yn); end=len(yn)-1
    lines=['#RADIOSS STARTER','/BEGIN',name,deck.ii(2026,0),deck.ff('g','mm','ms'),deck.ff('g','mm','ms'),'/TITLE',name,'/ANALY',deck.ii(0)+deck.ff(0)+deck.ii(0),'/SPMD',deck.ii(0,0)+deck.ff(0,1),'/SKEW/FIX/1','GLOBAL_XY',deck.ff(0,0,0),deck.ff(0,1,0),deck.ff(0,0,1),'/NODE',deck.ii(1)+deck.ff(0,0,0),deck.ii(2)+deck.ff(0,0,0)]
    start=len(lines); deck.add_spring_property(lines,1,10,11,kt,kn,peak,d0,df,False)
    lines[start+2]=deck.ff(d['control_mass_g'],d['control_rotational_inertia_g_mm2'])+deck.ii(1,0,0,0,0,1)
    lines += ['/PART/1','ONE_FRESH_TYPE8',deck.ii(1,0,0),'/SPRING/1',deck.ii(1,1,2,0,0,0,0,'','',1),'/GRNOD/NODE/1','FIXED_NODE',deck.ii(1),'/GRNOD/NODE/2','DRIVEN_NODE',deck.ii(2),'/BCS/1','FIX_NODE_1',f"{'111':>6}{'111':>4}"+deck.ii(0,1),'/BCS/2','BLOCK_Z_AND_ROTATIONS',f"{'001':>6}{'111':>4}"+deck.ii(0,2)]
    for fid,axis,path in [(90,'X',xp),(91,'Y',yp)]:
        lines += [f'/FUNCT/{fid}','PRESCRIBED_'+axis]+[deck.ff(t,u) for t,u in path]
        lines += [f'/IMPDISP/{fid}','DRIVE_'+axis,deck.ii(fid,axis,0,0,2,'',0),deck.ff(1,1,0,1e30)]
    lines += ['/TH/SPRING/2','SEAM_HISTORY',deck.ii('OFF','FX','FY','LX','LY','IE'),deck.ii(1,'')+'ONE_SPRING','/TH/NODE/3','NODES',deck.ii('DX','DY','VX','VY','REACX','REACY'),deck.ii(1,0),deck.ii(2,0),'/UNIT/1','I02IC_G_MM_MS',deck.ff('g','mm','ms'),'/END']
    (folder/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    engine=['/DT',deck.ff(case['dt_scale'],0),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',deck.ff(end+.002),'/TFILE/4',deck.ff(d['control_history_dt_ms']),'/VERS/2026']
    (folder/(name+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8',newline='\n')
    meta={'name':name,'case':case,'area_mm2':1.,'expected_mass_g':d['control_mass_g'],'kn_N_per_mm':kn,'kt_N_per_mm':kt,'peak_N':peak,'Gf_N_per_mm':gf,'delta0_mm':d0,'deltaf_mm':df,'x_path':xp,'y_path':yp,'end_ms':end+.002,'config_sha256':sha(CFG),'generator_sha256':sha(__file__),'dependency_sha256':{Path(deck.__file__).name:sha(deck.__file__)},'history':'fresh 0 state; H2; no mass scaling or material state substitution'}
    dump(folder/'generation.json',meta); return meta

def execute_case(cfg,case,control=False):
    folder=OUT/case['id']; folder.mkdir(exist_ok=False)
    if control: meta=control_generate(cfg,case,folder)
    else:
        meta=predecessor.generate(cfg,case,folder)
        meta['predecessor_metadata_hashes']={'generator':meta['generator_sha256'],'config':meta['config_sha256']}
        meta.update(generator_sha256=sha(__file__),config_sha256=sha(CFG),parent_generator_sha256=sha(predecessor.__file__),purpose='Fresh replica; only history output frequency changed against cached B; no restart import')
        dump(folder/'generation.json',meta)
    env=os.environ.copy(); env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m',PYTHONDONTWRITEBYTECODE='1')
    jobs=[('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]; records=[]
    for exe,args,log in jobs:
        tick=time.perf_counter()
        try: p=subprocess.run([str(RUNTIME/exe),*args],cwd=folder,env=env,capture_output=True,timeout=cfg['execution']['maximum_case_wall_seconds'])
        except subprocess.TimeoutExpired as exc:
            (folder/log).write_bytes((exc.stdout or b'')+(exc.stderr or b'')); dump(folder/'timeout.json',{'job':exe,'limit_seconds':cfg['execution']['maximum_case_wall_seconds']}); raise
        (folder/log).write_bytes(p.stdout+p.stderr)
        records.append({'command':[str(RUNTIME/exe),*args],'returncode':p.returncode,'seconds':time.perf_counter()-tick,'executable_sha256':sha(RUNTIME/exe)}); dump(folder/'execution.json',records)
        assert p.returncode==0,log
        if exe.startswith('starter'):
            txt=(folder/(meta['name']+'_0000.out')).read_text(errors='replace'); warnings=re.findall(r'^\s*WARNING ID\s*:\s*(\d+)',txt,re.M)
            known=(not control) and len(warnings)==len(meta['seam_pairs']) and set(warnings)=={'445'} and txt.count('NULL INERTIA')==len(meta['seam_pairs'])
            ok=not re.search('ERROR ID',txt) and 'unsupported field' not in txt.lower() and (not warnings or known)
            dump(folder/'preflight.json',{'pass':bool(ok),'warning_ids':warnings,'reviewed_445_blocked_rotations':bool(known),'no_unreviewed_warning':not warnings or bool(known)})
            assert ok,'Preflight failed; no engine launch'
    print(json.dumps({'case':case['id'],'seconds':sum(r['seconds'] for r in records)}),flush=True)

def read_history(folder):
    p=next(folder.glob('*.csv'))
    with p.open(encoding='utf-8',newline='') as f: headers=next(csv.reader(f))
    data=np.loadtxt(p,delimiter=',',skiprows=1,dtype=float)
    assert np.all(np.isfinite(data)) and np.all(np.diff(data[:,0])>0)
    return headers,data

def main():
    p=argparse.ArgumentParser(); p.add_argument('--declare',action='store_true');p.add_argument('--case'); p.add_argument('--campaign',action='store_true');a=p.parse_args()
    if a.declare: declare(); return
    cfg=json.loads(CFG.read_text()); assert (OUT/'preservation_before.json').exists()
    for case in cfg['controls']+cfg['cases']:
        if not a.campaign and case['id']!=a.case: continue
        folder=OUT/case['id']
        if folder.exists():
            records=json.loads((folder/'execution.json').read_text()); assert len(records)==3 and all(r['returncode']==0 for r in records)
            print(json.dumps({'cached':case['id'],'no_rerun':True}),flush=True);continue
        seconds=sum(r['seconds'] for f in OUT.glob('*/execution.json') for r in json.loads(f.read_text())); assert seconds<cfg['execution']['maximum_campaign_wall_seconds']
        execute_case(cfg,case,'kind' in case)

if __name__=='__main__': main()
