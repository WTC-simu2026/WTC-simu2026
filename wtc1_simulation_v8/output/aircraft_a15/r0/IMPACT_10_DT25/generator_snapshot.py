"""User-directed whole-aircraft/facade exploratory impact; preserved failed gates."""
import argparse,copy,csv,json,re,shutil,traceback
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
from run_aircraft_a04 import blocks
from run_aircraft_a06 import env
from run_aircraft_a13 import contact25
from run_aircraft_a14 import streamsha
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a15'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a15_predeclaration.json'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a11/r0/NOSE_04_DT05'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a14'

def guard():assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def cases():return read(CFG)['execution']['cases']

def declare():
    assert not OUT.exists() and not CFG.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A14'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    cfg=read(ROOT/'wtc1_simulation_v8/data/aircraft_a11_predeclaration.json')
    cfg.update(iteration='AIRCRAFT-A15',declared_utc=now(),seed=1102040,random_draws=0,
        scope='Whole inherited coupled aircraft versus inherited deformable three-storey facade. Fresh 10ms exploratory impacts, no historical damage fitting. Not physically qualified.',
        user_steering='2026-10-08 direct request: if aircraft ready launch it into facade; advance beyond local controls. This changes A15 work route to a bounded exploratory whole-scene experiment, without changing any A11-A14 failures or qualifying the aircraft.',
        parent=rel(PARENT),parent_status='Main A11 prototype executable; parallel joint adapter not dynamically ready and not integrated.',
        scene_changes={'aircraft_geometry_materials_mass_RBE3_facade_and_BCS':'exactly inherited A11 NOSE_04_DT05','contacts':'four exterior TYPE7 replaced by canonical TYPE25 nodes/surface, same nodal groups and fixed gap5mm','native_penalty':'Stfac1, Istf4; no area weighting introduced or qualified on aircraft','radome_self':'existing TYPE7 unchanged','rupture_erosion':'disabled as inherited','prescribed_motion':False,'facade':'31986 quadrilateral shells, only944 boundary nodes fixed; interior deformable, no fire/building interior'},
        output_contract={'history_interval_ms':.01,'animation_interval_ms':.1,'aircraft_TH_nodes':'96 declared probes from existing aircraft nodes; full nodal geometry/velocity/mass in native animations','support_REAC_units':'cumulative impulse; observer REAC excluded','part_ledger':'native global once; no reconstructed RKE added'},
        qualification_policy={'old_failed_gates_retained':True,'A14_qualified_transfer_allowed':False,'execution_is_exploratory_authorized_by_current_user':True,'scientific_qualification_requires_existing_numerical_and_material_gates':True,'historical_outcomes_used_as_targets':False,'parallel_module_integrated':False,'time_cap_not_a_scientific_pass':True},
        execution={'starter_timeout_s':120,'engine_timeout_s':600,'converter_timeout_s':120,'cpu_threads':2,'GPU':False,'requested_end_ms':10,'estimated_minutes':[5,20],'cases':[
            {'id':'IMPACT_10_DT50','contact':True,'composite':True,'self_contact':True,'dt_scale':.5,'end_ms':10},
            {'id':'IMPACT_10_DT25','contact':True,'composite':True,'self_contact':True,'dt_scale':.25,'end_ms':10}]},
        stages={'execution':'Both cases predeclared. Stop each on error, nonpositive step or600s cost cap; save incomplete attempts. No restarts beyond declared horizon. Numerical/material failures retained and reported, not an authorization barrier to this exploratory run.','seconds':'not requested as an hours-long job here; 10ms=0.01s, not first seconds'},
        physical_impact_qualified=False,NIST_outcomes_used_as_target=False)
    dump(CFG,cfg);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_A15_solver':True})
    inputs=[PARENT/'generation.json',PARENT/'mesh.json',PARENT/'A11_NOSE_04_DT05_0000.rad',PARENT/'A11_NOSE_04_DT05_0001.rad',PREV/'scientific_assessment.json',ROOT/'wtc1_simulation_v8/output/aircraft_a11_boeing_parallel/native_adapter_v2/integration_ready.json',PREV/'sources/TYPE25.html']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':[{'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)} for p in inputs],'inherited_sources':'A11 aircraft, reference material and facade provenance; A14 TYPE25 primary documentation','new_archive_inspection':False,'NIST_dependency':'representative facade inputs only; no outcomes fitted'})
    print({'declared':True,'preserved_files':len(pins),'scope':'two fresh10ms whole-scene impacts'},flush=True)

def build(caseid):
    guard();cfg=read(CFG);c=next(q for q in cases() if q['id']==caseid);d=OUT/'r0'/caseid;assert not d.exists();d.mkdir(parents=True)
    g=read(PARENT/'generation.json');m=read(PARENT/'mesh.json');name='A15_'+caseid;B=blocks((PARENT/(g['name']+'_0000.rad')).read_text().splitlines());out=[];changed=[]
    ids=g['aircraft_diag_node_ids'];probe=sorted(set(np.array(ids)[np.linspace(0,len(ids)-1,96,dtype=int)].tolist()));contact_modes={}
    for old in B:
        b=old.copy();key=b[0]
        if key in ['/BEGIN','/TITLE']:b[1]=name
        elif key.startswith('/INTER/TYPE7/') and int(key.rsplit('/',1)[1]) in [101,102,103,104]:
            cid=int(key.rsplit('/',1)[1]);gid=int(b[2][:10]);b=contact25(5);b[0]=f'/INTER/TYPE25/{cid}';b[1]=f'A15_CANONICAL_EXTERIOR_{cid}';b[2]=ii(0,1003,4,0,5,3,0,1000,1000,0);b[3]=ii(gid,0)+b[3][20:];contact_modes[cid]={'secondary_nodes_group':gid,'main_surface':1003,'Starter_mode_expected':3,'Stfac':1}
        elif key=='/TH/NODE/53':b=[key,'AIRCRAFT_NATIVE_VELOCITY_ROTATION',old[2]]+[ii(n,0)+f'N{n}' for n in probe]
        elif key=='/END':continue
        if b!=old:changed.append(key)
        out+=b
    out+=['/END'];assert len(contact_modes)==4
    # Mechanical scene is inherited byte-for-byte except explicit contact/outputs and titles.
    old_mech={b[0]:b for b in B if b[0].startswith(('/NODE','/MAT/','/PROP/','/SHELL/','/SH3N/','/BEAM/','/ADMAS/','/RBE3/','/BCS/','/INIVEL/'))}
    new_mech={b[0]:b for b in blocks(out) if b[0] in old_mech};assert old_mech==new_mech
    (d/(name+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    for job in [1,2]:
        E=blocks((PARENT/(g['name']+f'_000{job}.rad')).read_text().replace(g['name'],name).splitlines())
        for b in E:
            if b[0]=='/DT':b[1]=ff(c['dt_scale'],0)
            elif b[0].startswith('/RUN/'):b[1]=ff(c['end_ms']+(1e-6 if job==2 else 0))
            elif b[0].startswith('/TFILE'):b[1]=ff(.01 if job==1 else 1)
            elif b[0]=='/ANIM/DT':b[1]=ff(0,.1)
        (d/(name+f'_000{job}.rad')).write_text('\n'.join(q for b in E for q in b)+'\n',encoding='utf-8')
    shutil.copy2(PARENT/'mesh.json',d/'mesh.json');shutil.copy2(__file__,d/'generator_snapshot.py')
    dump(d/'generation.json',{**g,'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'aircraft_diag_node_ids':probe,'parent':rel(PARENT),'contact_modes':contact_modes,'changed_cards':changed,'mechanical_scene_unchanged':True,'full_historical_impact':False,'history_records_per_frame':14})
    dump(d/'scene_audit.json',{'pass':True,'aircraft_nodes':len(m['aircraft_node_ids']),'facade_nodes':len(g['facade_translated_node_ids']),'facade_shells':len(m['facade_quads_node_ids']),'facade_fixed_boundary_nodes':len(m['fixed_node_ids']),'deformable_facade':True,'mechanical_cards_unchanged':True,'motion_prescribed':False,'parallel_adapter_integrated':False,'new_mass_scaling':False})
    print({'built':caseid,'native_probes':len(probe)},flush=True)

def recover(d,n):
    H=histories(d/(n+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'));nr=14;header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[:2]==[4,88] and all([len(q) for q in f]==sizes for f in frames)
    raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
    o=d/'observer';ro=records(o/(n+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (o/(n+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:w=csv.writer(f);w.writerow(list(H));w.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'rows':len(v),'records_per_frame':nr,'sizes':sizes,'all_channels_CSV_binary_verified':True,'actual_end_ms':float(end[0])})

def run(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');n=g['name'];c=read(CFG)['execution'];assert not (d/'starter.log').exists()
    assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',c['starter_timeout_s'],env())
    txt=(d/'starter.log').read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1])==0,txt[-3000:]
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',c['engine_timeout_s'],env())
    log=(d/'engine.log').read_text(errors='replace');assert 'NORMAL TERMINATION' in log.upper() and 'TIME STEP LESS OR EQUAL ZERO' not in log.upper()
    pins={p.name:streamsha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
    for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env());assert all(streamsha(d/p)==h for p,h in pins.items());dump(d/'observer_preservation.json',{'main_outputs_unchanged':True,'pass':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());recover(d,n);print({'finished':caseid},flush=True)

def batch():
    for c in cases():
        d=OUT/'r0'/c['id']
        if (d/'history_recovery.json').exists() or list(d.glob('retained_failure_*.json')):continue
        try:build(c['id']);run(c['id'])
        except Exception:
            d.mkdir(parents=True,exist_ok=True);dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'case':c,'traceback':traceback.format_exc(),'partial_not_qualified':True});print(traceback.format_exc(),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','batch']);globals()[p.parse_args().action]()
