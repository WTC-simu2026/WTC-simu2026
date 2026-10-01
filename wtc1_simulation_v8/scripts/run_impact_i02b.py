"""Generate and run isolated, history-instrumented uniaxial joint coupons."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / 'wtc1_simulation_v8/data/impact_i02b_joint_coupon.json'
RUNTIME = ROOT / 'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def f20(*values):
    return ''.join(f'{v:20.12g}' if isinstance(v, (float, int)) else f'{v:>20}' for v in values)


def i10(*values):
    return ''.join(f'{v:10d}' if isinstance(v, int) else f'{v:>10}' for v in values)


def parameters(cfg, case):
    src, law = cfg['source_envelope'], cfg['connector']
    scale = (src['target_diameter_in'] / src['rivet_diameter_in']) ** src['capacity_scale_exponent']
    peak = src[case['mode'] + '_capacity_kN_approx'][1] * 1000 * scale * case['weight']
    d0, df = law['peak_displacement_mm'], law['final_displacement_mm'][case['energy']]
    return {'peak_N': peak, 'd0_mm': d0, 'df_mm': df, 'K_N_mm': peak/d0,
            'energy_J': 0.5*peak*df*0.001, 'count':case['count'], 'weight':case['weight']}


def loading_path(case, p):
    df=p['df_mm']
    if case['loading']=='cycle':
        # Partial postpeak excursion, unload to zero, reload through the same
        # history, complete separation, close and reopen to test no healing.
        return [(0,0), (1,0.4*df), (2,0), (3,0.4*df), (4,1.1*df),
                (4.2,1.1*df), (5.2,0), (6.2,0.5*df), (6.4,0.5*df)]
    return [(0,0), (1,1.1*df), (1.1,1.1*df)]


def generate(cfg, case, directory):
    p=parameters(cfg,case)
    count=case['count']
    name='I02B_'+case['id']
    fixed=[2*n+1 for n in range(count)]
    moving=[n+1 for n in fixed]
    mass=cfg['connector']['moving_mass_g']*case['weight']
    length=cfg['connector']['initial_length_mm']
    lines=['#RADIOSS STARTER','/BEGIN',f'{name:<80}',i10(2026,0),f20('g','mm','ms'),f20('g','mm','ms'),
           '/TITLE',name,'/ANALY',i10(0,'',0,0),'/SPMD',f'{0:10d}{0:10d}{0:20d}{1:20d}',
           '/NODE']
    for index,(n1,n2) in enumerate(zip(fixed,moving)):
        lines += [i10(n1)+f20(0,index*25.4,0),i10(n2)+f20(length,index*25.4,0)]
    lines += ['/PART/1','PROXY_RIVET_ROW',i10(1,0,0),'/PROP/SPRING/1','TRIANGULAR_H2_SOFTENING',
              f20(2*mass)+' '*30+i10(0,0,0),
              f20(p['K_N_mm'],0,1,0,1),
              i10(11,case['hardening'],0,0,0,'')+f20(-1e30,p['df_mm']),
              f20(1,0,1,0),'/FUNCT/11','LOAD_FORCE_VS_RELATIVE_DISPLACEMENT']
    for x,y in [(-10,0),(0,0),(p['d0_mm'],p['peak_N']),(p['df_mm'],0),(10,0)]:
        lines.append(f20(x,y))
    lines += ['/SPRING/1']
    for index,(n1,n2) in enumerate(zip(fixed,moving),1):
        lines.append(i10(index,n1,n2,0,0,0,0,'','',0))
    for group,title,nodes in [(1,'FIXED',fixed),(2,'MOVING',moving)]:
        lines += [f'/GRNOD/NODE/{group}',title]
        for start in range(0,len(nodes),10): lines.append(i10(*nodes[start:start+10]))
    lines += ['/BCS/1','FIXED_END',f"{'111':>6}{'111':>4}{0:10d}{1:10d}",
              '/BCS/2','MOVING_ONLY_X',f"{'011':>6}{'111':>4}{0:10d}{2:10d}"]
    if case['loading']=='dynamic':
        lines += ['/INIVEL/TRA/1','CONTROLLED_INITIAL_KINETIC_ENERGY',
                  f20(case['velocity_m_s'],0,0)+i10(2,0),f20(0)+i10(0)]
        end=case['end_ms']
        path=[]
    else:
        path=loading_path(case,p); end=path[-1][0]
        if case.get('smooth_segments',False):
            coarse=path; path=[]
            for (ta,da),(tb,db) in zip(coarse[:-1],coarse[1:]):
                for u in np.linspace(0,1,cfg['accepted_revision_R2']['samples_per_segment'],endpoint=False):
                    path.append((float(ta+(tb-ta)*u),float(da+(db-da)*(3*u*u-2*u*u*u))))
            path.append(coarse[-1])
        lines += ['/FUNCT/12','IMPOSED_DISPLACEMENT_VS_TIME']+[f20(t,d) for t,d in path]
        lines += ['/IMPDISP/1','TENSILE_COUPON',i10(12,'X',0,0,2,'',0),f20(1,1,0,1e30)]
    lines += ['/TH/SPRING/1','CONNECTOR_HISTORY',i10('OFF','FX','LX','IE','LENGTH')]
    for index in range(1,count+1): lines.append(i10(index,'')+f'LINK_{index}')
    lines += ['/TH/NODE/2','BOUNDARY_HISTORY',i10('DX','VX','REACX')]
    for index in fixed+moving: lines.append(i10(index,0))
    lines += ['/TH/PART/3','MASS_ENERGY',i10('IE','KE','MASS','XMOM'),i10(1),'/END']
    (directory/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    engine=['/DT',f20(case['dt_scale'],0),'/DTIX',f20(case['maximum_dt_ms'],case['maximum_dt_ms']),
            '/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',f20(end),
            '/TFILE/4',f20(cfg['execution']['history_dt_ms']),'/VERS/2026']
    (directory/(name+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8')
    meta={'name':name,'case':case,'parameters':p,'moving_mass_g':mass*count,'fixed_nodes':fixed,
          'moving_nodes':moving,'end_ms':end,'loading_path_ms_mm':path,
          'assumptions':cfg['connector']['assumptions']}
    write_json(directory/'generation.json',meta)
    return meta


def run_case(cfg,case):
    directory=ROOT/cfg['output_root']/case['id']
    if directory.exists(): raise RuntimeError('Existing case preserved: '+str(directory))
    directory.mkdir(parents=True)
    meta=generate(cfg,case,directory)
    env=os.environ.copy()
    env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',
               OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS='1',KMP_STACKSIZE='400m')
    records=[]
    for executable,args,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),
                                ('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),
                                ('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
        command=[str(RUNTIME/executable),*args]; start=time.perf_counter()
        proc=subprocess.run(command,cwd=directory,env=env,capture_output=True,timeout=cfg['execution']['maximum_case_wall_seconds'])
        (directory/log).write_bytes(proc.stdout+proc.stderr)
        records.append({'command':command,'returncode':proc.returncode,'seconds':time.perf_counter()-start,
                        'executable_sha256':sha(RUNTIME/executable)})
        write_json(directory/'execution.json',records)
        if proc.returncode: raise RuntimeError(f'{executable} failed: {directory/log}')
    print(json.dumps({'case':case['id'],'seconds':sum(r['seconds'] for r in records),'directory':str(directory)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--case',required=True); parser.add_argument('--revision',choices=['R1','R2'],required=True); args=parser.parse_args()
    cfg=json.loads(CFG.read_text())
    case=next(case for case in cfg['cases'] if case['id']==args.case).copy()
    case['id']=case['id'].replace('_R0','_'+args.revision)
    revision=cfg['accepted_revision_R1']
    case['maximum_dt_ms']=revision['half_dt_maximum_ms'] if 'HALFDT' in case['id'] else revision['maximum_dt_ms']
    case['smooth_segments']=args.revision=='R2'
    if case['id'].startswith('DYNAMIC_LOW_ENERGY'): case['end_ms']=revision['dynamic_low_energy_end_ms']
    run_case(cfg,case)
