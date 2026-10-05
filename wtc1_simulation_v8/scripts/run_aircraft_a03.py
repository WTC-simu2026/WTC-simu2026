"""New whole-aircraft/representative-band decks, bounded first contact, no fracture fit."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,time
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,group,harness,execute
from generate_v8v_deformable_projectile import ShellMesh,add_facade,type7_lines
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a03_predeclaration.json';OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a03';PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a02'
def preserved():
    pins=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in pins if sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(pins)
def initialize():
    assert not OUT.exists();v=harness();assert v['CurrentIteration']=='AIRCRAFT-A02';OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for n in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/n)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:
        pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())})
    cfg=read(CFG);paths=[ROOT/cfg['input_deck'],ROOT/cfg['input_mesh'],ROOT/'wtc1_simulation_v8/data/impact_i02a_structured_wing.json',ROOT/'wtc1_simulation_v8/data/v8v_openradioss_deformable_projectile.json',ROOT/'wtc1_simulation_v8/scripts/generate_v8v_deformable_projectile.py',ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a02.py']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p)} for p in paths],'sources':cfg['sources'],'NIST_dependency':'nominal representative facade inputs only; no observed/output damage used','archive_rescanned':False})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'path':rel(CFG),'sha256':sha(CFG),'declared_before_new_generation_and_solver':True,'outcome_fit_allowed':False})
    print(json.dumps({'initialized':True,'old_files_pinned':preserved(),'harness':v},indent=2))
def build(revision):
    cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];preserved();base=OUT/revision;assert not base.exists();base.mkdir();shutil.copy2(__file__,base/'generator_snapshot.py')
    aircraft=read(ROOT/cfg['input_mesh']);n=len(aircraft['nodes_m']);oldlines=(ROOT/cfg['input_deck']).read_text().splitlines();m=ShellMesh();f=cfg['facade'];m.shells={1:[],2:[]}
    geometry={'column_centers_x_mm':[(i-(f['column_count']-1)/2)*f['column_spacing_mm'] for i in range(f['column_count'])],'column_width_mm':f['column_width_mm'],'column_depth_mm':f['column_depth_mm'],'story_height_mm':f['story_height_mm'],'story_count':f['story_count'],'panel_width_mm':f['panel_width_mm'],'spandrel_height_mm':f['spandrel_height_mm'],'spandrel_center_y_mm':f['spandrel_center_vertical_mm']}
    fixed=add_facade(m,geometry,f['target_mesh_mm']);front=-cfg['aircraft']['initial_gap_to_facade_midsurface_mm'];xyz=np.array([[p[2]+front,p[0],p[1]] for p in m.nodes]);allxyz=np.vstack([np.array(aircraft['nodes_m'])*1000,xyz]);facadeids={1:31,2:32};shells=[];partids=[]
    for part in [1,2]:
        for q in m.shells[part]:shells.append([i+n for i in q]);partids.append(facadeids[part])
    external={'fuselage_skin','fuselage_caps','wing_skin','horizontal_tail','horizontal_tail_caps','vertical_tail','vertical_tail_caps'}
    original=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json');contactnodes=sorted({i+1 for s in original['triangular_shells'] if s['part'] in external for i in s['nodes']});fixedids=sorted(i+n for i in fixed)
    # The original graph is intact. Facade nodes may never be shared with aircraft nodes.
    assert min(fixedids)>n and max(contactnodes)<=2860
    mass={str(facadeids[p]):m.part_area(p)*f['material']['density_g_mm3']*f['column_shell_thickness_mm' if p==1 else 'spandrel_shell_thickness_mm']*.001 for p in [1,2]}
    expectedM=read(PREV/'r1/translation_dt080/audit.json')['native_mass_kg']+sum(mass.values())
    dump(base/'mesh.json',{'nodes_mm':allxyz.tolist(),'aircraft_node_count':n,'facade_quads_node_ids':shells,'facade_part_ids':partids,'fixed_node_ids':fixedids,'aircraft_contact_node_ids':contactnodes,'original_triangle_node_ids':aircraft['triangle_node_ids'],'original_beam_node_ids':aircraft['beam_node_ids'],
        'facade_mass_kg_by_part':mass,'expected_total_mass_kg':expectedM,'geometry':geometry,'facade_nodes':len(xyz),'facade_quads':len(shells),'frame_determinant':1,'joint_type':'shared facade nodes, no aircraft-facade node merge'})
    additions=['/MAT/LAW1/3','REPRESENTATIVE_STEEL_INTACT_NO_FAILURE',ff(f['material']['density_g_mm3']),ff(f['material']['E_MPa'],f['material']['nu'])]
    eid=20001
    for p,pid in facadeids.items():
        title='FACADE_COLUMNS' if p==1 else 'FACADE_SPANDRELS';t=f['column_shell_thickness_mm' if p==1 else 'spandrel_shell_thickness_mm']
        additions.extend([f'/PROP/TYPE1/{pid}',title,ii(24,4,2,2),ff(0,0,0,0,0),ii(0)+' '*10+ff(t,5/6),f'/PART/{pid}',title,ii(pid,3,0),f'/SHELL/{pid}'])
        for q in m.shells[p]:additions.append(ii(eid,*(i+n for i in q)));eid+=1
    group(additions,1001,'FIXED_BAND_ENDS',fixedids);additions.extend(['/BCS/1','FIXED_COLUMN_TOP_BOTTOM','   111 111'+ii(0,1001)])
    group(additions,1002,'AIRCRAFT_EXTERNAL_CONTACT',contactnodes);additions.extend(['/SURF/PART/1003','REPRESENTATIVE_FACADE_SURFACE',ii(31,32)])
    additions.extend(['/TH/PART/11','FACADE_STATE', ''.join(f'{s:>10}' for s in ['MASS','XMOM','YMOM','ZMOM','KE','IE','HE','ERODED']),ii(31,32)])
    # Each reaction component gets its own title to disambiguate converter columns.
    for axis,i in zip('XYZ',[21,22,23]):
        additions.extend([f'/TH/NODE/{i}','SUPPORT_IMPULSE_'+axis,f'{"REAC"+axis:>10}'])
        additions.extend(ii(node,0) for node in fixedids)
    dump(base/'generation_audit.json',{'created_utc':now(),'original_aircraft_nodes':n,'facade_nodes':len(xyz),'facade_quads':len(shells),'fixed_nodes':len(fixedids),'external_contact_nodes':len(contactnodes),'expected_facade_mass_kg':sum(mass.values()),'expected_total_mass_kg':expectedM,
        'original_deck_sha256':sha(ROOT/cfg['input_deck']),'original_aircraft_geometry_and_mass_cards_unchanged':True,'A02_CG_failure_retained':True,'contact_engines_not_implemented':True,'radome_not_reconstructed':True})
    for case in cfg['execution']['cases']:
        d=base/case['id'];d.mkdir();name='A03_'+case['id'];lines=oldlines.copy();lines[2]=f'{name:<80}';lines[lines.index('/TITLE')+1]=name
        ni=lines.index('/NODE')+1
        while not lines[ni].startswith('/'):ni+=1
        lines[ni:ni]=[ii(n+i+1)+ff(*p) for i,p in enumerate(xyz)];lines=lines[:-1]+additions.copy()
        if case['contact']:
            c=cfg['contact'];cs=type7_lines(1,'AIRFRAME_TO_REPRESENTATIVE_FACADE',1002,1003);cs[2]=ii(1002,1003,c['Istf'],0,c['Igap'])+' '*10+ii(0,2,0,0)
            cs[5]=ff(c['Stfac'],c['friction'],c['Gapmin_mm'],0,1e30)
            cs[6]='       000'+' '*20+ii(1000)+ff(c['VISs'],c['VISF'],.2)
            lines+=cs+['/TH/INTER/1','CONTACT_RAW_HISTORY',''.join(f'{s:>10}' for s in ['FNX','FNY','FNZ','CE_ELAST']),ii(1)]
        lines+=['/END'];(d/(name+'_0000.rad')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
        e=cfg['execution'];engine=['/ANIM/DT',ff(0,e['animation_dt_ms']),'/ANIM/ELEM/ENER','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/ANIM/SHELL/VONM','/DT',ff(case['dt_scale'],0),'/MON/ON','/PRINT/-100/100',f'/RUN/{name}/1',ff(e['end_ms']),'/TFILE/4',ff(e['history_dt_ms']),'/VERS/2026']
        (d/(name+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8');dump(d/'generation.json',{'name':name,'case':case,'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'geometry_file':rel(base/'mesh.json'),'no_prescribed_aircraft_trajectory':True,'no_fracture':True,'no_mass_scaling':True})
    dump(base/'harness_after_generation.json',harness());print(json.dumps(read(base/'generation_audit.json'),indent=2))
def run(revision,case_id):
    cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];e=cfg['execution'];d=OUT/revision/case_id;meta=read(d/'generation.json');n=meta['name'];assert not (d/'starter.log').exists()
    env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS=str(e['threads']),KMP_STACKSIZE='400m')
    for exe,args,log,timeout in [('starter_win64.exe',['-i',n+'_0000.rad','-np','1'],'starter.log',e['starter_timeout_s']),('engine_win64.exe',['-i',n+'_0001.rad'],'engine.log',e['engine_timeout_s']),('th_to_csv_win64.exe',[n+'T01'],'converter.log',e['converter_timeout_s'])]:
        if not execute(RUNTIME/exe,args,d,log,timeout,env):print(json.dumps({'failed':log,'case':case_id,'revision':revision}));return
    print(json.dumps({'completed':case_id,'revision':revision}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['initialize','build','run']);ap.add_argument('--revision',default='r0');ap.add_argument('--case',default='FREE_F200_DT080');a=ap.parse_args()
    if a.action=='initialize':initialize()
    elif a.action=='build':build(a.revision)
    else:run(a.revision,a.case)
