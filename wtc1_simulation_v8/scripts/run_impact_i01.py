"""Bounded fresh 3D shell contact pilot. Old models are imports/read-only sources.
No rupture, no whole Boeing, no inferred physical penetration. Units g/mm/ms.
"""
import argparse, csv, hashlib, json, os, re, subprocess, time
from pathlib import Path
from generate_v8v_deformable_projectile import ShellMesh, add_facade, add_closed_box, chunks, fixed_fields as ff, material_lines, shell_property_lines, type7_lines
ROOT=Path(__file__).resolve().parents[2]
CFG=ROOT/'wtc1_simulation_v8/data/impact_i01_first_contact.json'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def generate(cfg,case,d):
    old=json.loads((ROOT/cfg['inherited_config']).read_text(encoding='utf-8'))
    mesh=ShellMesh(); geom=cfg['facade']; fixed=add_facade(mesh,geom,case['mesh_mm'])
    n_facade=len(mesh.nodes); box=cfg['box']; size=case['mesh_mm']
    add_closed_box(mesh,box['width_span_mm'],box['height_mm'],box['front_z_mm'],box['front_z_mm']+box['length_chord_mm'],3,size)
    for i in range(n_facade,len(mesh.nodes)):
        x,y,z=mesh.nodes[i]; mesh.nodes[i]=(x,y+box['center_y_mm'],z)
    name='I01_'+case['id']
    lines=['#RADIOSS STARTER','# Numerical component pilot; NO rupture or real Boeing claim','/BEGIN',f'{name:<80}',f'{2026:10d}{0:10d}',ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',name,'/ANALY',f'{0:10d}{"":10s}{0:10d}{0:10d}','/DEF_SHELL',f'{0:10d}{0:10d}{0:10d}{0:10d}{0:10d}{"":20s}{0:10d}{0:10d}','/SPMD',f'{0:10d}{0:10d}{0:20d}{1:20d}']
    lines+=material_lines(1,'Representative steel from V8V, no failure',old['facade_material'],1e30)
    lines+=material_lines(2,'Generic aluminum hypothesis, no failure',cfg['aluminum'],1e30)
    lines+=['/NODE']
    for i,(x,y,z) in enumerate(mesh.nodes,1): lines.append(f'{i:10d}{x:20.9g}{y:20.9g}{z:20.9g}')
    lines+=['/BCS/1','FIXED_COLUMN_ENDS',f'{"111":>6}{"111":>4}{0:10d}{10:10d}','/GRNOD/NODE/10','FIXED_COLUMN_ENDS']
    for group in chunks(sorted(fixed)): lines.append(''.join(f'{v:10d}' for v in group))
    eid=1; ranges={}; cells=[]; parts=[]
    for part,title,mat in [(1,'COLUMNS',1),(2,'SPANDREL',1),(3,'WING_BOX_SURROGATE',2)]:
        lines += [f'/PART/{part}',title,f'{part:10d}{mat:10d}{0:10d}',f'/SHELL/{part}']
        start=eid
        for shell in mesh.shells[part]:
            lines.append(f'{eid:10d}'+''.join(f'{n:10d}' for n in shell)); eid+=1
            cells.append([n-1 for n in shell]); parts.append(part)
        ranges[str(part)]=[start,eid-1]
    for part,title,thick in [(1,'COLUMN_SKIN',geom['column_shell_thickness_mm']),(2,'SPANDREL_SKIN',geom['spandrel_shell_thickness_mm']),(3,'BOX_SKIN',case['skin_mm'])]: lines+=shell_property_lines(part,title,thick)
    lines+=['/GRNOD/PART/20','BOX_NODES',f'{3:10d}','/SURF/PART/30','FACADE_SURFACE',f'{1:10d}{2:10d}','/INIVEL/TRA/1','BOX_INITIAL_SPEED',f'{0:20g}{0:20g}{-cfg["speed"]["m_per_s"]:20g}{20:10d}{0:10d}',f'{0:20g}{0:10d}']
    if case['contact']:
        lines+=type7_lines(1,'BOX_TO_FACADE',20,30)
        lines+=['/TH/INTER/1','CONTACT_IMPULSE',f'{"FNZ":>10}',f'{1:10d}']
    lines+=['/TH/PART/2','PART_STATES',''.join(f'{v:>10}' for v in ('IE','KE','ZMOM','MASS','HE','ERODED','VZ')),f'{1:10d}{2:10d}{3:10d}','/END']
    (d/f'{name}_0000.rad').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    ex=cfg['execution']
    engine=['/ANIM/DT',ff(0,ex['animation_dt_ms']),'/ANIM/SHELL/EPSP/ALL','/ANIM/ELEM/ENER','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/DT',ff(case['dt_scale'],0),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',ff(ex['end_ms']),'/TFILE/4',ff(ex['history_dt_ms']),'/VERS/2026']
    (d/f'{name}_0001.rad').write_text('\n'.join(engine)+'\n',encoding='utf-8')
    mass=mesh.part_area(3)*case['skin_mm']*cfg['aluminum']['density_g_per_mm3']
    meta={'name':name,'case':case,'nodes':len(mesh.nodes),'shells':len(cells),'fixed_nodes':len(fixed),'box_mass_g':mass,'box_initial_KE_J':0.5*mass*cfg['speed']['m_per_s']**2*0.001,'ranges':ranges,'initial_gap_surface_mm':box['front_z_mm']-(geom['column_shell_thickness_mm']+case['skin_mm'])/2,'source_sha256':{cfg['inherited_config']:sha(ROOT/cfg['inherited_config']),cfg['inherited_generator']:sha(ROOT/cfg['inherited_generator'])}}
    write_json(d/'mesh.json',{'nodes_mm':mesh.nodes,'quads':cells,'parts':parts,'fixed_nodes_zero_based':[n-1 for n in sorted(fixed)]})
    write_json(d/'generation.json',meta); return meta
def execute(exe,args,d,env,log,timeout):
    start=time.perf_counter()
    with (d/log).open('w',encoding='utf-8') as f:
        try: r=subprocess.run([str(exe),*args],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        except subprocess.TimeoutExpired: raise RuntimeError('Case exceeded declared wall limit; incomplete')
    if r.returncode: raise RuntimeError(f'{log} failed, exit {r.returncode}')
    return {'exit_code':r.returncode,'seconds':time.perf_counter()-start,'exe':str(exe),'sha256':sha(exe),'args':args}
def parse(cfg,case,d,meta):
    name=meta['name']
    with (d/f'{name}T01.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    headers=list(rows[0]); write_json(d/'history_headers.json',headers)
    def col(title,var):
        hits=[s for s in headers if title in s and s.endswith(' '+var)]
        if len(hits)!=1: hits=[s for s in headers if title in s and re.search(r'\b'+re.escape(var)+r'\b',s)]
        if len(hits)!=1: raise RuntimeError(f'Ambiguous column {title}/{var}: {hits}')
        return hits[0]
    var={k:col('WING_BOX_SURROGATE',k) for k in ['MASS','ZMOM','KE','IE','ERODED']}
    contact=next((h for h in headers if 'CONTACT_IMPULSE' in h),None)
    first=rows[0]; initKE=float(first['KINETIC ENERGY'])+float(first['ROTATION ENERGY']); initE=initKE+float(first['INTERNAL ENERGY']); p0=float(first[var['ZMOM']]); m0=float(first[var['MASS']])
    history=[]
    for r in rows:
        E=sum(float(r[x]) for x in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY']); W=float(r['EXTERNAL WORK'])
        # Explicitly include contact elastic storage in additional diagnostic, not in the conventional balance twice.
        impulse=(float(r[contact])-float(first[contact])) if contact else 0
        dp=float(r[var['ZMOM']])-p0
        history.append({'t_ms':float(r['time']),'KE_J':float(r['KINETIC ENERGY'])*0.001,'IE_J':float(r['INTERNAL ENERGY'])*0.001,'rotation_J':float(r['ROTATION ENERGY'])*0.001,'external_work_J':W*0.001,'elastic_contact_J':float(r['ELASTIC CONTACT ENERGY'])*0.001,'energy_error_fraction':(E-initE-W)/max(initE,1e-30),'box_pz_Ns':float(r[var['ZMOM']])*0.001,'contact_impulse_abs_Ns':abs(impulse)*0.001,'box_delta_pz_Ns':dp*0.001,'box_mass_kg':float(r[var['MASS']])*0.001,'box_eroded':float(r[var['ERODED']])})
    write_json(d/'history_si.json',history)
    starttext=(d/'starter.log').read_text(encoding='utf-8',errors='replace'); engtext=(d/'engine.log').read_text(encoding='utf-8',errors='replace')
    last=history[-1]; J=last['contact_impulse_abs_Ns']; dp=abs(last['box_delta_pz_Ns'])
    result={'case':case['id'],'normal_termination':'NORMAL TERMINATION' in engtext.upper(),'history_rows':len(rows),'end_ms':last['t_ms'],'initial_KE_J':initKE*0.001,'box_mass_kg':m0*0.001,'mass_error_fraction':abs(m0-meta['box_mass_g'])/meta['box_mass_g'],'max_energy_error_fraction':max(abs(h['energy_error_fraction']) for h in history),'final_impulse_Ns':J,'final_box_momentum_change_abs_Ns':dp,'momentum_balance_error_fraction':abs(J-dp)/max(J,dp,1),'max_box_mass_change_fraction':max(abs(h['box_mass_kg']-m0*.001)/(m0*.001) for h in history),'max_box_eroded':max(h['box_eroded'] for h in history),'initial_penetration_counts':[int(n) for n in re.findall(r'THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS',starttext)],'all_eroded_events':len(re.findall(r'SHELL.*RUPTURE',engtext)),'final':last,'scope':'Numerical non-eroding generic box contact, not physical wing or tower validation'}
    write_json(d/'results.json',result); return result
def main():
    p=argparse.ArgumentParser(); p.add_argument('--case',required=True); p.add_argument('--parse-only',action='store_true'); args=p.parse_args()
    cfg=json.loads(CFG.read_text(encoding='utf-8')); case=next(c for c in cfg['cases'] if c['id']==args.case); d=ROOT/cfg['output_root']/case['id']
    runtime=ROOT/'wtc1_simulation_v8/openradioss_runtime/v20260728-win64'
    env=os.environ.copy(); env.update({'RAD_CFG_PATH':'C:/OpenRadioss/hm_cfg_files','RAD_H3D_PATH':'C:/OpenRadioss/extlib/h3d/lib/win64','OPENRADIOSS_PATH':'C:/OpenRadioss','OMP_NUM_THREADS':'1','KMP_STACKSIZE':'400m'})
    if args.parse_only: meta=json.loads((d/'generation.json').read_text())
    else:
        if d.exists(): raise RuntimeError('Refuse to overwrite an existing case')
        d.mkdir(parents=True); meta=generate(cfg,case,d); runs=[]
        for exe,a,log in [('starter_win64.exe',['-i',meta['name']+'_0000.rad','-np','1'],'starter.log'),('engine_win64.exe',['-i',meta['name']+'_0001.rad'],'engine.log'),('th_to_csv_win64.exe',[meta['name']+'T01'],'converter.log')]:
            runs.append(execute(runtime/exe,a,d,env,log,cfg['execution']['maximum_case_wall_seconds']))
        write_json(d/'execution.json',runs)
    print(json.dumps(parse(cfg,case,d,meta),ensure_ascii=False))
if __name__=='__main__': main()
