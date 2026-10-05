"""New complete-aircraft transfer and short unforced controls; preserve all revisions."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, csv, hashlib, json, os, re, shutil, subprocess, time
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT/'wtc1_simulation_v8/data/aircraft_a02_predeclaration.json'
OUT = ROOT/'wtc1_simulation_v8/output/aircraft_a02'
PREV = ROOT/'wtc1_simulation_v8/output/aircraft_a01'
RUNTIME = ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v): p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def ff(*v): return ''.join(f'{x:20.12g}' if isinstance(x,(int,float)) else f'{x:>20}' for x in v)
def ii(*v): return ''.join(f'{x:10d}' for x in v)
def group(lines,gid,title,ids):
    lines.extend([f'/GRNOD/NODE/{gid}',title])
    for k in range(0,len(ids),10): lines.append(ii(*ids[k:k+10]))
def harness():
    r=subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe','-NoProfile','-Command','& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=60)
    assert r.returncode==0,r.stdout+r.stderr
    v=json.loads(r.stdout);assert v['Status']=='PASS';return v
def preserved():
    pins=read(OUT/'preservation_before.json')['files']
    bad=[r['path'] for r in pins if sha(ROOT/r['path'])!=r['sha256']]
    assert not bad,bad
    return len(pins)
def initialize():
    assert not OUT.exists();v=harness();assert v['CurrentIteration']=='AIRCRAFT-A01'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']: shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for n in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/n)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:
        pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())})
    cfg=read(CFG);inp=ROOT/cfg['input_root']
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'configuration':rel(CFG),'sha256':sha(CFG),'criteria_before_generation':True,'outcome_fit_allowed':False})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'input_files':[{'path':rel(inp/n),'sha256':sha(inp/n)} for n in ['airframe_mesh_SI.json','mass_quadrature_SI.csv','summary.json']],
        'inherited_manifest':{'path':rel(PREV/'source_manifest.json'),'sha256':sha(PREV/'source_manifest.json')},'documentation_urls':cfg['sources'][1:],
        'source_use':'Official keyword syntax only; no official event outcome used. No archive rescan or new video analysis.'})
    print(json.dumps({'initialized':True,'old_files_pinned':preserved(),'harness':v},indent=2))
def moments(m,x):
    M=float(m.sum());cg=np.einsum('i,ij->j',m,x)/M;d=x-cg
    S=np.einsum('i,ij,ik->jk',m,d,d);I=np.eye(3)*np.trace(S)-S
    return {'mass_kg':M,'CG_m':cg.tolist(),'inertia_CG_kg_m2':I.tolist()}
def build(revision):
    cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];preserved()
    base=OUT/revision;assert not base.exists();base.mkdir()
    shutil.copy2(Path(__file__),base/'generator_snapshot.py')
    inp=ROOT/cfg['input_root'];mesh=read(inp/'airframe_mesh_SI.json');x=np.asarray(mesh['nodes_m']);ns=len(x)
    shells=mesh['triangular_shells'];beams=mesh['equivalent_elastic_beams'];nm=np.zeros(ns)
    for s in shells: nm[s['nodes']]+=s['mass_kg']/3
    for b in beams: nm[b['nodes']]+=b['mass_kg']/2
    rows=list(csv.DictReader((inp/'mass_quadrature_SI.csv').open(encoding='utf-8')))
    extra=[r for r in rows if r['component'] in cfg['mapping']['additional_components']]
    em=np.array([float(r['mass_kg']) for r in extra]);ex=np.array([[float(r[k]) for k in ['x_m','y_m','z_m']] for r in extra]);allx=np.vstack([x,ex])
    hosts=[];cond=[]
    for p in ex:
        ids=np.argsort(np.sum((x-p)**2,axis=1),kind='stable')[:cfg['mapping']['nearest_independent_nodes']]
        r=x[ids]-x[ids].mean(axis=0);G=np.zeros((len(ids)*3,6))
        for i,d in enumerate(r):
            G[3*i:3*i+3,:3]=np.eye(3)
            G[3*i:3*i+3,3:]=np.array([[0,d[2],-d[1]],[-d[2],0,d[0]],[d[1],-d[0],0]])
        sv=np.linalg.svd(G,compute_uv=False);cond.append(float(sv[0]/sv[-1]));hosts.append((ids+1).tolist())
    a=moments(np.r_[nm,em],allx);reference=read(inp/'summary.json')['nominal'];Iref=np.array(reference['inertia_CG_kg_m2'])
    err=float(np.linalg.norm(np.array(a['inertia_CG_kg_m2'])-Iref)/np.linalg.norm(Iref))
    checks={'mass':abs(a['mass_kg']-reference['total_kg'])/reference['total_kg']<cfg['acceptance']['mass_relative_error'],
        'CG':float(np.linalg.norm(np.array(a['CG_m'])-reference['CG_m']))<cfg['acceptance']['CG_error_m'],
        'input_lumped_inertia':err<cfg['acceptance']['input_lumped_inertia_relative_norm_error'],
        'local_hosts_noncollinear':max(cond)<cfg['acceptance']['independent_host_rigid_fit_condition_number'],
        'positive_additional_mass':bool(np.all(em>0)),'all_structure_has_native_mass':bool(np.all(nm>0)),
        'no_duplicated_structural_quadrature_mass':len(extra)==368}
    audit={'created_utc':now(),'checks':checks,'pass':all(checks.values()),'original_nodes':ns,'additional_nodes':len(extra),'triangles':len(shells),'beams':len(beams),
        'reference_A01':reference,'input_lumped_prediction':a,'inertia_relative_norm_error':err,'maximum_host_condition_number':max(cond),
        'native_structure_mass_kg':float(nm.sum()),'additional_mass_kg':float(em.sum()),'scope':'Input spatial moments; not assumed to be solver effective inertia after RBE3. Native rotational inertia excluded here.'}
    dump(base/'mapping_audit.json',audit)
    dump(base/'solver_mesh.json',{'nodes_m':allx.tolist(),'native_nodal_mass_prediction_kg':nm.tolist(),'additional_mass_kg':em.tolist(),
        'additional_components':[r['component'] for r in extra],'RBE3_host_node_ids':hosts,'triangle_node_ids':[(np.array(s['nodes'])+1).tolist() for s in shells],
        'beam_node_ids':[(np.array(b['nodes'])+1).tolist() for b in beams]})
    assert audit['pass'],audit['checks']
    matids={k:i+1 for i,k in enumerate(mesh['materials'])}
    shellkeys=list(dict.fromkeys((s['part'],s['material'],s['thickness_m']) for s in shells))
    beamkeys=list(dict.fromkeys((b['part'],b['material'],b['area_m2'],b['Iyy_m4'],b['Izz_m4'],b['J_m4']) for b in beams))
    skeys={k:i+1 for i,k in enumerate(shellkeys)};bkeys={k:len(shellkeys)+i+1 for i,k in enumerate(beamkeys)}
    orientation=[]
    for b in beams:
        axis=x[b['nodes'][1]]-x[b['nodes'][0]];axis/=np.linalg.norm(axis);v=np.eye(3)[int(np.argmin(np.abs(axis)))];v=v-axis*float(v@axis);v/=np.linalg.norm(v);orientation.append(v)
    dump(base/'beam_frames.json',{'orientation_reference_vectors':np.asarray(orientation).tolist(),'minimum_cross_product':min(float(np.linalg.norm(np.cross((x[b['nodes'][1]]-x[b['nodes'][0]])/b['length_m'],v))) for b,v in zip(beams,orientation))})
    for case in cfg['execution']['cases']:
        directory=base/case['id'];directory.mkdir();name='A02_'+case['id']
        lines=['#RADIOSS STARTER','/BEGIN',f'{name:<80}',ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',name,'/ANALY',f'{0:10d}{"":10s}{0:10d}{0:10d}','/SPMD',f'{0:10d}{0:10d}{0:20d}{1:20d}','/NODE']
        lines.extend(ii(i+1)+ff(*(p*1000)) for i,p in enumerate(allx))
        for k,m in mesh['materials'].items(): lines.extend([f'/MAT/LAW1/{matids[k]}',k,ff(m['rho_kg_m3']*1e-6),ff(m['E_Pa']*1e-6,m['nu'])])
        for key,pid in skeys.items():
            title,mat,t=key;lines.extend([f'/PROP/TYPE1/{pid}',title,ii(24,4,2,2),ff(0,0,0,0,0),ii(0)+' '*10+ff(t*1000,5/6),f'/PART/{pid}',title,ii(pid,matids[mat],0),f'/SH3N/{pid}'])
            for eid,s in enumerate(shells,1):
                if (s['part'],s['material'],s['thickness_m'])==key: lines.append(ii(eid,*(np.array(s['nodes'])+1)))
        for key,pid in bkeys.items():
            title,mat,A,Iy,Iz,J=key;lines.extend([f'/PROP/TYPE3/{pid}',title,f'{4:20d}',ff(0,0),ff(A*1e6,Iy*1e12,Iz*1e12,J*1e12),'   000 000'+ii(0),f'/PART/{pid}',title,ii(pid,matids[mat],0),f'/BEAM/{pid}'])
            for j,(b,v) in enumerate(zip(beams,orientation)):
                if (b['part'],b['material'],b['area_m2'],b['Iyy_m4'],b['Izz_m4'],b['J_m4'])==key: lines.append(ii(len(shells)+j+1,*(np.array(b['nodes'])+1),0)+ff(*v))
        lines.extend(['/ADMAS/5/1','A01_INERTIAL_RESERVE_ENGINE_FUEL_PAYLOAD'])
        lines.extend(ff(m*1000)+ii(ns+i+1) for i,m in enumerate(em))
        for i,ids in enumerate(hosts):
            gid=100+i;group(lines,gid,'LOCAL_STRUCTURAL_HOSTS',ids)
            # DOF field is 3 blank chars, TX TY TZ, blank, RX RY RZ.
            lines.extend([f'/RBE3/{i+1}','LOCAL_INERTIAL_INTERPOLATION',ii(ns+i+1)+'   111 000'+ii(1,2,2),ff(1)+'   111 000'+ii(0,gid)])
        group(lines,1,'ALL_AIRCRAFT_NODES',list(range(1,len(allx)+1)))
        lines.extend(['/INIVEL/TRA/1','UNFORCED_INITIAL_TRANSLATION',ff(*case['velocity_m_s'])+ii(1,0),ff(0)+ii(0),'/END'])
        (directory/f'{name}_0000.rad').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        e=cfg['execution'];engine=['/ANIM/DT',ff(0,e['animation_dt_ms']),'/ANIM/ELEM/ENER','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/DT',ff(case['dt_scale'],0),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',ff(e['end_ms']),'/TFILE/4',ff(e['history_dt_ms']),'/VERS/2026']
        (directory/f'{name}_0001.rad').write_text('\n'.join(engine)+'\n',encoding='utf-8')
        dump(directory/'generation.json',{'created_utc':now(),'name':name,'case':case,'mapping_audit':rel(base/'mapping_audit.json'),'generator_sha256':sha(Path(__file__)),'configuration_sha256':sha(CFG),
            'no_BCS':True,'no_RBODY':True,'no_contact':True,'no_gravity':True,'no_mass_scaling':True})
    dump(base/'harness_after_generation.json',harness());print(json.dumps({k:audit[k] for k in ['pass','original_nodes','additional_nodes','triangles','beams','inertia_relative_norm_error','maximum_host_condition_number']},indent=2))
def execute(exe,args,directory,log,timeout,env):
    begin=time.perf_counter();status=None
    with (directory/log).open('w',encoding='utf-8') as f:
        try: r=subprocess.run([str(exe),*args],cwd=directory,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout);status=r.returncode
        except subprocess.TimeoutExpired: status='TIMEOUT'
    result={'exe':rel(exe),'sha256':sha(exe),'args':args,'seconds':time.perf_counter()-begin,'exit_code':status,'timeout_s':timeout,'created_utc':now()}
    dump(directory/(log+'.execution.json'),result);return status==0
def run(revision,case_id):
    cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];preserved();e=cfg['execution'];d=OUT/revision/case_id
    meta=read(d/'generation.json');n=meta['name'];assert not (d/'starter.log').exists(),'never overwrite a solver attempt'
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS=str(e['threads']),KMP_STACKSIZE='400m')
    for exe,args,log,limit in [('starter_win64.exe',['-i',n+'_0000.rad','-np','1'],'starter.log',e['starter_timeout_s']),('engine_win64.exe',['-i',n+'_0001.rad'],'engine.log',e['engine_timeout_s']),('th_to_csv_win64.exe',[n+'T01'],'converter.log',e['converter_timeout_s'])]:
        if not execute(RUNTIME/exe,args,d,log,limit,env): print(json.dumps({'failed':log,'case':case_id,'revision':revision}));return
    print(json.dumps({'completed':case_id,'revision':revision}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['initialize','build','run']);ap.add_argument('--revision',default='r0');ap.add_argument('--case',default='translation_dt080');a=ap.parse_args()
    if a.action=='initialize': initialize()
    elif a.action=='build': build(a.revision)
    else: run(a.revision,a.case)
