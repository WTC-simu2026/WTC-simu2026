"""Immutable fresh-state LAW36 shell unit tests; no import or rewrite of past models."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / 'wtc1_simulation_v8/data/impact_i02i_material_predeclaration.json'
OUT = ROOT / 'wtc1_simulation_v8/output/impact_i02i_material'
RT = ROOT / 'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'

def dump(p, value):
    Path(p).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def ff(*values):
    return ''.join(f'{v:20.12g}' if isinstance(v, (int,float)) else f'{v:>20}' for v in values)

def ii(*values):
    return ''.join(f'{v:10d}' if isinstance(v, int) else f'{v:>10}' for v in values)

def curve(cfg, interpretation):
    m = cfg['material']; E = m['young_modulus_mpa']; points = []; ledger = []
    for e0, s0 in zip(m['source_total_strain'],m['source_stress_mpa']):
        e = math.log1p(e0) if interpretation == 'engineering' else e0
        s = s0*(1+e0) if interpretation == 'engineering' else s0
        p_raw = e - s/E
        points.append([max(0.,p_raw),s])
        ledger.append(dict(source_strain=e0,source_stress_MPa=s0,total_strain=e,stress_MPa=s,raw_plastic_strain=p_raw,plastic_strain=max(0.,p_raw),origin_clipped=p_raw<0))
    return points+[[1.,points[-1][1]]],ledger

def targets(cfg, case):
    m = cfg['material']; E=m['young_modulus_mpa']; kind=case['interpretation']
    if case['path']=='elastic': return [0.,0.002,0.]
    strains = m['source_total_strain']
    if kind=='true_total': strains = [math.expm1(v) for v in strains]
    values = [0.]+strains
    if case['path']=='cycle':
        final_s = m['source_stress_mpa'][-1]*(1+m['source_total_strain'][-1]) if kind=='engineering' else m['source_stress_mpa'][-1]
        final_e = math.log1p(values[-1])
        values += [math.expm1(final_e-(final_s-50.)/E),values[-1]]
    return values

def generate(cfg, case, folder):
    m=cfg['material']; g=cfg['geometry']; x=g['length_mm']; y=g['width_mm']; th=g['thickness_mm']
    prop=cfg['shell_variants'][case['shell']]; crv, ledger=curve(cfg,case['interpretation'])
    name='I02I_'+case['id']; factor=case.get('time_factor',1.)
    ts=targets(cfg,case); path=[(0.,0.)]; knot_times=[0.]
    t=0.; ex=cfg['execution']; n=ex['function_subdivisions_per_segment']
    for a,b in zip(ts[:-1],ts[1:]):
        for j in range(1,n+1):
            q=j/n; f=q*q*q*(10+q*(-15+6*q))
            path.append((t+factor*ex['segment_ms']*q,x*(a+(b-a)*f)))
        t+=factor*ex['segment_ms']; knot_times.append(t)
        t+=factor*ex['hold_ms']; path.append((t,x*b))
    nodes=[(0.,0.,0.),(x,0.,0.),(x,y,0.),(0.,y,0.)]
    lines=['#RADIOSS STARTER','# fresh generic homogeneous QEPH patch, no physical identification','/BEGIN',name,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',name,'/ANALY',ii(0,'',0,0),'/SPMD',ii(0,0)+ff(0,1),'/MAT/PLAS_TAB/1','FRESH_LAW36_'+case['interpretation'],ff(m['density_g_per_mm3'],0),ff(m['young_modulus_mpa'],m['poisson_ratio'],0,0,0),f'{1:10d}{0:10d}{0:20g}{0:20g}{0:20g}{"":10s}{0:10d}',f'{0:10d}{0:20g}{0:10d}{0:20g}{0:20g}',ii(200),ff(1),ff(0),'/FUNCT/200','FRESH_PLASTIC_HARDENING']
    lines += [ff(p,s) for p,s in crv]+['/NODE']+[ii(j)+ff(*v) for j,v in enumerate(nodes,1)]
    lines += ['/PART/1','HOMOGENEOUS_PATCH',ii(1,1,0),'/SHELL/1',ii(1,1,2,3,4),'/PROP/SHELL/1','QEPH_'+case['shell'],f'{24:10d}{prop["Ismstr"]:10d}{0:10d}{0:10d}{0:10d}{"":10s}{0:20g}',ff(0,0,0,prop['dm'],prop['dn']),ii(5,1)+ff(th,0)+ii('',prop['Ithick'],prop['Iplas'],0)]
    for group,title,ids in [(1,'ALL',[1,2,3,4]),(2,'LEFT',[1,4]),(3,'RIGHT',[2,3]),(4,'Y_ANCHOR',[1])]:
        lines += [f'/GRNOD/NODE/{group}',title,ii(*ids)]
    lines += ['/BCS/1','PLANE_ROTATIONS',f'{"001":>6}{"111":>4}'+ii(0,1),'/BCS/2','LEFT_X',f'{"100":>6}{"000":>4}'+ii(0,2),'/BCS/3','Y_TRANSLATION',f'{"010":>6}{"000":>4}'+ii(0,4),'/FUNCT/90','PRESCRIBED_RIGHT_X']
    lines += [ff(tt,uu) for tt,uu in path]
    lines += ['/IMPDISP/1','RIGHT_X',ii(90,'X',0,0,3,'',0),ff(1,1,0,1e30),'/TH/PART/1','PATCH',ii('IE','KE','MASS','HE'),ii(1),'/TH/SHEL/2','SHELL',ii('F1','F2','F12','EMAX','THIC','IEM','OFF','E1','E2'),ii(1,0),'/TH/NODE/3','NODES',ii('DX','DY','VX','VY','REACX','REACY')]
    lines += [ii(j,0) for j in range(1,5)]+['/UNIT/1','G_MM_MS',ff('g','mm','ms'),'/END']
    (folder/f'{name}_0000.rad').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
    eng=['/DT',ff(case.get('dt_scale',ex['dt_scale']),0),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',ff(t),'/TFILE/4',ff(ex['history_dt_ms']*factor),'/VERS/2026']
    (folder/f'{name}_0001.rad').write_text('\n'.join(eng)+'\n',encoding='utf-8',newline='\n')
    meta=dict(name=name,case=case,geometry=g,shell_requested=prop,curve=crv,conversion_ledger=ledger,path_time_ms_displacement_mm=path,knot_times_ms=knot_times,targets_engineering_strain=ts,end_ms=t,expected_mass_g=x*y*th*m['density_g_per_mm3'],config_sha256=sha(CFG),generator_sha256=sha(__file__))
    dump(folder/'generation.json',meta); return meta

def snapshot():
    OUT.mkdir(parents=True,exist_ok=False)
    old=ROOT/'wtc1_simulation_v8/output/impact_i02h_local_cohesive'
    entries={}
    for name in ['preservation_before_finalization.json','artifact_manifest.json']:
        for entry in json.loads((old/name).read_text(encoding='utf-8'))['files']:
            actual=sha(ROOT/entry['path'])
            if actual!=entry['sha256']: raise ValueError('Old provenance changed: '+entry['path'])
            entries[entry['path']]=entry
    for path in [old/'publication_verification.json',old/'artifact_manifest.json',old/'preservation_before_finalization.json',ROOT/'harness/handoffs/WTC1_V11G_HANDOFF.md']:
        entries[path.relative_to(ROOT).as_posix()]={'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}
    dump(OUT/'preservation_before.json',{'files':list(entries.values()),'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'All I02H manifest and prior preservation entries, including V11F/V11R; no archive enumeration.'})
    for name in ['state.json','experiments/registry.jsonl']:
        (OUT/('before_'+Path(name).name)).write_bytes((ROOT/'harness'/name).read_bytes())
    print(json.dumps({'snapshot_files':len(entries)}),flush=True)

def execute(cfg, case, directory):
    directory.mkdir(parents=True,exist_ok=False); meta=generate(cfg,case,directory)
    env=os.environ.copy(); env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m',PYTHONDONTWRITEBYTECODE='1')
    records=[]
    jobs=[('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]
    for exe,args,log in jobs:
        start=time.perf_counter()
        try:
            p=subprocess.run([str(RT/exe),*args],cwd=directory,env=env,capture_output=True,timeout=cfg['execution']['maximum_case_wall_seconds'])
        except subprocess.TimeoutExpired as exc:
            (directory/log).write_bytes((exc.stdout or b'')+(exc.stderr or b''))
            dump(directory/'timeout.json',{'job':exe,'limit_seconds':cfg['execution']['maximum_case_wall_seconds'],'status':'diagnostic_incomplete'})
            raise
        (directory/log).write_bytes(p.stdout+p.stderr)
        records.append(dict(command=[str(RT/exe),*args],returncode=p.returncode,seconds=time.perf_counter()-start,executable_sha256=sha(RT/exe)))
        dump(directory/'execution.json',records)
        if p.returncode: raise RuntimeError(log+' failed')
        if exe.startswith('starter'):
            text=(directory/(meta['name']+'_0000.out')).read_text(errors='replace')
            err=re.findall(r'(?:WARNING|ERROR) ID',text)
            if err or 'unsupported field' in text.lower(): raise RuntimeError('Preflight warnings/errors; engine not authorized by gate')
    print(json.dumps({'case':case['id'],'seconds':sum(v['seconds'] for v in records)}),flush=True)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--snapshot',action='store_true'); parser.add_argument('--case'); args=parser.parse_args()
    if args.snapshot: snapshot(); return
    cfg=json.loads(CFG.read_text(encoding='utf-8'))
    if not (OUT/'preservation_before.json').exists(): raise RuntimeError('Snapshot required')
    cases=[c for c in cfg['cases'] if c['id']==args.case] if args.case else cfg['cases']
    if not cases: raise ValueError('Unknown case')
    start=time.perf_counter()
    for case in cases:
        if time.perf_counter()-start>cfg['execution']['maximum_campaign_wall_seconds']: raise RuntimeError('Campaign cost gate reached')
        execute(cfg,case,OUT/case['id'])

if __name__=='__main__': main()
