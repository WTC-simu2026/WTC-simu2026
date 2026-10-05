"""Fresh whole-aircraft metallic plasticity, fixed conditions, no restart property changes."""
import argparse,json,os,re,shutil
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a04_predeclaration.json';OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a04';PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a03'

def preserved():
    pins=read(OUT/'preservation_before.json')['files'];bad=[r['path'] for r in pins if sha(ROOT/r['path'])!=r['sha256']];assert not bad,bad;return len(pins)

def blocks(lines):
    result=[]
    for line in lines:
        if line.startswith('/') or not result:result.append([line])
        else:result[-1].append(line)
    return result

def initialize():
    assert not OUT.exists();v=harness();assert v['CurrentIteration']=='AIRCRAFT-A03';OUT.mkdir();dump(OUT/'harness_before.json',v)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+name.split('/')[-1]))
    pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/name)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'declared_before_generation_and_solver':True,'outcome_fit_allowed':False})
    cfg=read(CFG);files=[ROOT/cfg['input_deck'],ROOT/cfg['input_mesh'],ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json']+list((ROOT/'wtc1_simulation_v8/input/aircraft_a04_sources').glob('*'))
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'exclude_external_source' if p.suffix.lower()=='.pdf' else 'own_provenance'} for p in files],'primary_links':cfg['sources'],'NIST_dependency':'nominal representative facade inputs only; never damage-output target','archive_rescanned':False})
    dump(OUT/'source_transcription.json',{'2024_yield':{'original_ksi':47,'printed_MPa':324,'exact_ksi_conversion_MPa':47*cfg['units']['ksi_to_MPa'],'temper':'T4/T351','source_pdf':'kaiser_2024.pdf','page':1},'7075_yield':{'original_ksi':73,'printed_MPa':503,'exact_ksi_conversion_MPa':73*cfg['units']['ksi_to_MPa'],'temper':'T651','source_pdf':'kaiser_7075.pdf','page':1,'visual_table_inspection':True},'Boeing_radome':{'source_pdf':'boeing_arff767.pdf','page':6,'document_label':'767.0.6 April29 2022','observation':'RADOME in COMPOSITE MATERIALS LOCATIONS; no layup/thickness/strength supplied','not_historical_as_built_record':True}})
    print({'initialized':True,'old_files_pinned':preserved()})

def material(mid,m,case):
    if case['law']=='elastic':return [f'/MAT/LAW1/{mid}',m['name'],ff(m['rho_g_mm3']),ff(m['E_MPa'],m['nu'])]
    a=1e12 if case['law']=='high_yield' else m['yield_MPa']*case['yield_scale'];b=m['E_MPa']*case['H_to_E']
    return [f'/MAT/LAW2/{mid}',m['name'],ff(m['rho_g_mm3']),ff(m['E_MPa'],m['nu'])+ii(0,2)+ff(-1e30),ff(a,b,1,1e30,1e30),ff(0,.001)+ii(1,1)+ff(1e20,0),ff(1,1e30,0,293.15,1e30)]

def build(revision):
    cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];preserved();base=OUT/revision;assert not base.exists();base.mkdir();shutil.copy2(__file__,base/'generator_snapshot.py');shutil.copy2(ROOT/cfg['input_mesh'],base/'mesh.json')
    original=(ROOT/cfg['input_deck']).read_text().splitlines();mesh=read(base/'mesh.json');x=np.array(mesh['nodes_mm']);nb=len(mesh['original_triangle_node_ids']);beams=mesh['original_beam_node_ids'];selected=[nb+i+1 for i,e in enumerate(beams) if max(x[np.array(e)-1,0])<=cfg['beam']['history_preselected_max_endpoint_X_m']*1000]
    dump(base/'beam_selection.json',{'criterion_before_new_solver':'max endpoint X<=8m (nose and forward fuselage); not output-selected','element_ids':selected,'count':len(selected),'full_beam_count':len(beams),'not_global_maximum_beam_stress':True})
    for case in cfg['execution']['cases']:
        d=base/case['id'];d.mkdir();name='A04_'+case['id'];bs=blocks(original);result=[];counts={'materials':0,'shell_props':0,'beam_props':0}
        for card in bs:
            key=card[0]
            if key=='/END':continue
            if key.startswith('/MAT/LAW1/'):
                mid=int(key.split('/')[-1]);card=material(mid,cfg['materials'][str(mid)],case);counts['materials']+=1
            if key.startswith('/PROP/TYPE1/'):
                card=card.copy();card[4]=ii(case['shell_N'])+card[4][10:];counts['shell_props']+=1
            if key.startswith('/PROP/TYPE3/'):
                card=card.copy();card[3]=ff(cfg['beam']['dm'],cfg['beam']['df_nearly_zero']);counts['beam_props']+=1
            if key.startswith('/INTER/') and not case['contact']:continue
            if key.startswith('/TH/INTER/') and not case['contact']:continue
            if key.startswith('/TH/PART/'):
                card=card.copy();card[2]=card[2]+f'{"PW":>10}'
            if key=='/BEGIN':card=card.copy();card[1]=f'{name:<80}'
            if key=='/TITLE':card=[key,name]
            result.extend(card)
        result+=['/TH/PART/31','AIRCRAFT_PART_DIAGNOSTIC',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(*range(1,11)),ii(*range(11,19))]
        result+=['/TH/BEAM/41','FORWARD_BEAM_DIAGNOSTIC',''.join(f'{v:>10}' for v in ['F1','F2','F3','M1','M2','M3','SX','EPSP','IE'])]
        result.extend(ii(e)+' '*10+f'B{e:<79}' for e in selected);result+=['/END']
        assert counts['materials']==3 and counts['shell_props']==13 and counts['beam_props']==7,counts
        (d/(name+'_0000.rad')).write_text('\n'.join(result)+'\n',encoding='utf-8')
        e=cfg['execution'];engine=['/ANIM/DT',ff(0,e['animation_dt_ms']),'/ANIM/ELEM/ENER','/ANIM/VECT/VEL','/ANIM/VECT/DISP','/ANIM/SHELL/VONM']
        if case['shell_N']>0:engine+=['/ANIM/SHELL/EPSP/ALL','/ANIM/SHELL/TENS/STRESS/UPPER','/ANIM/SHELL/TENS/STRESS/LOWER']
        engine+=['/DT',ff(case['dt_scale'],0),'/MON/ON','/PRINT/1/100',f'/RUN/{name}/1',ff(case['end_ms']),'/TFILE/4',ff(e['history_dt_ms']),'/VERS/2026']
        (d/(name+'_0001.rad')).write_text('\n'.join(engine)+'\n',encoding='utf-8')
        observe=['/ANIM/DT',ff(0,1e30),'/PRINT/-1/100',f'/RUN/{name}/2',ff(case['end_ms']+e['additional_observation_time_ms']),'/TFILE/4',ff(1e30),'/VERS/2026']
        (d/(name+'_0002.rad')).write_text('\n'.join(observe)+'\n',encoding='utf-8')
        # Original topology/masses/velocity/contact remain byte-equivalent card by card.
        oldbs={c[0]:c for c in blocks(original) if c[0].startswith(('/NODE','/SH3N','/SHELL','/BEAM/','/ADMAS','/RBE3','/INIVEL','/BCS'))}
        newbs={c[0]:c for c in blocks(result) if c[0] in oldbs};same=all(newbs[k]==c for k,c in oldbs.items());assert same
        dump(d/'generation.json',{'name':name,'case':case,'configuration_sha256':sha(CFG),'generator_sha256':sha(__file__ and ROOT/rel(__import__('pathlib').Path(__file__))),'geometry_and_mass_cards_unchanged':same,'card_changes':counts,'fresh_intact_start':True,'no_fracture':True,'no_mass_scaling':True,'no_prescribed_trajectory':True,'beam_history_count':len(selected)})
    dump(base/'harness_after_generation.json',harness());print({'built':revision,'cases':len(cfg['execution']['cases']),'beam_history':len(selected),'original_graph_and_masses_preserved':True})

def run(revision,case_id):
    cfg=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];d=OUT/revision/case_id;meta=read(d/'generation.json');n=meta['name'];assert not (d/'starter.log').exists();e=cfg['execution'];env=os.environ.copy();env.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files',RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',OPENRADIOSS_PATH='C:/OpenRadioss',OMP_NUM_THREADS=str(e['threads']),KMP_STACKSIZE='400m')
    if not execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',e['starter_timeout_s'],env):print({'failed':'starter','case':case_id});return
    s=(d/'starter.log').read_text();warnings=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1])
    if warnings or errors:print({'failed':'starter_gate','case':case_id,'warnings':warnings,'errors':errors});return
    if not execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',e['engine_timeout_s'],env):print({'failed':'engine','case':case_id});return
    # Observe a newly-created restart with identical materials, never use A03 damaged history.
    pins={rel(p):sha(p) for p in d.glob('*') if p.is_file()}
    if not execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],d,'observer.log',60,env):print({'failed':'observer','case':case_id});return
    changed=[p for p,h in pins.items() if sha(ROOT/p)!=h];dump(d/'observer_preservation.json',{'main_outputs_unchanged':not changed,'changed':changed,'previous_files_checked':len(pins),'main_binary_animations':[p for p in pins if re.search(r'A\d{3}$',p)]})
    assert not changed,changed
    for stream in ['T01','T02']:
        if (d/(n+stream)).exists():
            if not execute(RUNTIME/'th_to_csv_win64.exe',[n+stream],d,'converter_'+stream+'.log',e['converter_timeout_s'],env):print({'failed':'converter','case':case_id});return
    print({'completed':case_id,'revision':revision},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['initialize','build','run']);p.add_argument('--revision',default='r0');p.add_argument('--case',default='ELASTIC_N0_DFMIN');a=p.parse_args()
    if a.action=='initialize':initialize()
    elif a.action=='build':build(a.revision)
    else:run(a.revision,a.case)
