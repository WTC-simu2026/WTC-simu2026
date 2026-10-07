"""A11 fresh whole-aircraft nose-first impact scene; no historical damage fitting."""
import argparse,copy,json,re,shutil,sys
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness
from run_aircraft_a04 import blocks
from run_aircraft_a07 import group
import run_aircraft_a08 as runner

CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a11_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a11'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a10'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a09/r0/BASE_FINE'
EXT=ROOT/'wtc1_simulation_v8/data/aircraft_a11_horizon_extension.json'

def cases():return read(CFG)['execution']['cases']+(read(EXT)['cases'] if EXT.exists() else [])
def guard():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    if EXT.exists():assert sha(EXT)==read(OUT/'extension_guard.json')['sha256']

def declare():
    assert not CFG.exists() and not OUT.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A10'
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a09_predeclaration.json')
    c.update(iteration='AIRCRAFT-A11',declared_utc=now(),seed=1102036,random_draws=0,
      scope='Fresh intact coupled aircraft, restored representative facade ahead of nose, exterior aircraft surface contact. Diagnostic first milliseconds only; fracture/erosion, core crushing/delamination and whole-aircraft self-contact not qualified.',
      user_steering='2026-10-07: advance Boeing construction and actual nose-first impact; parallel mechanical construction has separate directories and no shared-state writes.',
      scene_changes={'facade_translation_mm':[-15468.6,0,0],'basis':'exact inverse of prior A07 engine-front displacement, not a fit to observed damage','aircraft_geometry_mass_material_properties_RBE3':'unchanged A09 BASE_FINE','exterior_contact':'original external skins/caps and radome, plus inherited nacelle/fan/core domains; no duplicated nodes between interfaces','radome_self_contact':'unchanged','whole_aircraft_self_contact':False,'prescribed_motion':False,'damage_failure_erosion':False},
      output_contract={'history_interval_ms':.0005,'animation_interval_ms':.05,'nodal_mass':True,'part_channels':['IE','KE','HE','PW','RKE','XMOM','YMOM','ZMOM','MASS'],'all_aircraft_node_channels':['VX','VY','VZ','VRX','VRY','VRZ'],'support_REAC_units':'cumulative impulse, established by A10 native source and witness; no reintegration'},
      transfer_policy={'A10_contact_option_qualified_for_aircraft':False,'Stfac1':'inherited default and diagnostic candidate; no spatial/aircraft qualification inherited from 1D witness','native_RKE':'use global once only, part and independent reconstructions exploratory, never added to close budget'},
      stages={'initial':'FREE_04, NOSE_04_DT10, NOSE_04_DT05','fallback':'NOSE_04_DT025 allowed only if half-step or local numerical energy gate fails; retain failures','extension_1ms':'predeclare extension only after zero warnings/errors, mass/topology/finite/supports/no erosion, global and local energy/momentum gates pass and half-step impulse/generated-energy gates pass. Material diagnostic failure may allow one explicitly out-of-domain numerical continuation to 1ms, never physical qualification.','extension_2ms':'requires 1ms numerical gates AND radome/metal material-domain gates; otherwise stop and preserve blockers','seconds':'not pre-authorized as qualified; estimate and declare any hours-scale run first'},
      execution={'starter_timeout_s':120,'engine_timeout_s':1200,'converter_timeout_s':120,'cpu_threads':2,'GPU':False,'cases':[
        {'id':'FREE_04','contact':False,'composite':True,'self_contact':True,'domain':'whole_exterior','dt_scale':.1,'end_ms':.4},
        {'id':'NOSE_04_DT10','contact':True,'composite':True,'self_contact':True,'domain':'whole_exterior','dt_scale':.1,'end_ms':.4},
        {'id':'NOSE_04_DT05','contact':True,'composite':True,'self_contact':True,'domain':'whole_exterior','dt_scale':.05,'end_ms':.4},
        {'id':'NOSE_04_DT025','contact':True,'composite':True,'self_contact':True,'domain':'whole_exterior','dt_scale':.025,'end_ms':.4,'conditional':'fallback only if declared half-step/numerical gates fail'}]})
    # Keep the prior numerical/material thresholds exactly; don't hide small losses in the 2.44GJ initial KE.
    c['acceptance_extra']={'independent_nodal_translation_KE_fraction_of_initial':.005,'independent_nodal_momentum_absolute_Ns':10,'independent_nodal_momentum_relative':.02,'mesh_convergence_qualified':False,'part_RKE_ledger_qualified':False}
    dump(CFG,c);OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for k in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/k)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_new_solver':True})
    files=[PARENT/n for n in ['generation.json','mesh.json','A09_BASE_FINE_0000.rad','A09_BASE_FINE_0001.rad','A09_BASE_FINE_0002.rad']]+[PREV/'authoritative_review.json',PREV/'source_manifest.json',ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'primary_links':c['sources'],'inherited_source_manifests':[rel(PREV/'source_manifest.json'),'wtc1_simulation_v8/output/aircraft_a09/source_manifest.json'],'new_external_data':False,'NIST_dependency':'representative facade geometry/material inputs inherited; historical NIST damage outputs never a target','archive_rescanned':False})
    print({'declared':True,'old_files_pinned':len(pins),'cases':[q['id'] for q in c['execution']['cases']]},flush=True)

def build(caseid):
    guard();cfg=read(CFG);c=next(q for q in cases() if q['id']==caseid);d=OUT/'r0'/caseid;assert not d.exists();d.mkdir(parents=True);g=read(PARENT/'generation.json');mesh=read(PARENT/'mesh.json');name='A11_'+caseid
    bs=blocks((PARENT/(g['name']+'_0000.rad')).read_text().splitlines());orig={b[0]:b for b in bs};xyz=np.array(mesh['nodes_mm']);fa=sorted({n for q in mesh['facade_quads_node_ids'] for n in q});oldxyz=xyz.copy();xyz[np.array(fa)-1]+=cfg['scene_changes']['facade_translation_mm'];assert set(mesh['fixed_node_ids']).issubset(fa)
    original=read(ROOT/'wtc1_simulation_v8/output/aircraft_a01/verification_r2/airframe_mesh_SI.json');part={i+1:e['part'] for i,e in enumerate(original['triangular_shells'])};external={'fuselage_skin','fuselage_caps','wing_skin','horizontal_tail','horizontal_tail_caps','vertical_tail','vertical_tail_caps'}
    airskin=sorted({n for eid,p,tr in zip(mesh['aircraft_triangle_ids'],mesh['aircraft_triangle_part_ids'],mesh['original_triangle_node_ids']) if part.get(eid) in external or p==21 for n in tr});eng={label:sorted(ids) for label,ids in g['contact_segments'].items()};segments={'AIRFRAME':airskin,**eng};flat=sum(segments.values(),[]);assert len(flat)==len(set(flat));assert set(flat).issubset(mesh['aircraft_node_ids'])
    assert np.array_equal(xyz[np.array(mesh['aircraft_node_ids'])-1],oldxyz[np.array(mesh['aircraft_node_ids'])-1]);mesh.update(nodes_mm=xyz.tolist(),aircraft_contact_node_ids=flat)
    changed=[];out=[]
    for b0 in bs:
        b=b0.copy();key=b[0]
        if key in ['/BEGIN','/TITLE']:b[1]=name
        elif key=='/NODE':b=[key]+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
        elif key.startswith(('/INTER/TYPE7/','/TH/INTER/')) and int(key.split('/')[-1]) in [101,102,103] and not c['contact']:continue
        elif key=='/TH/NODE/52':continue
        elif key=='/END':continue
        if b!=b0:changed.append(key)
        out+=b
    if c['contact']:
        b=copy.deepcopy(orig['/INTER/TYPE7/101']);b[0]='/INTER/TYPE7/104';b[1]='A11_AIRFRAME_TO_FACADE';b[2]=ii(1103)+b[2][10:];out+=group(1103,'A11_AIRFRAME_CONTACT',airskin)+b+['/TH/INTER/104','CONTACT_RAW_HISTORY_AIRFRAME',orig['/TH/INTER/101'][2],ii(104)]
    diag=sorted(mesh['aircraft_node_ids']);out+=['/TH/NODE/53','AIRCRAFT_NATIVE_VELOCITY_ROTATION',''.join(f'{v:>10}' for v in ['VX','VY','VZ','VRX','VRY','VRZ'])]+[ii(n,0)+f'N{n}' for n in diag]+['/END']
    (d/(name+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    for suffix in ['_0001.rad','_0002.rad']:
        bb=blocks((PARENT/(g['name']+suffix)).read_text().replace(g['name'],name).splitlines())
        for b in bb:
            if b[0]=='/DT':b[1]=ff(c['dt_scale'],0)
            if b[0].startswith('/RUN/'):b[1]=ff(c['end_ms']+(1e-6 if suffix=='_0002.rad' else 0))
            if b[0].startswith('/TFILE') and suffix=='_0001.rad':b[1]=ff(cfg['output_contract']['history_interval_ms'])
            if b[0]=='/ANIM/DT':b[1]=ff(0,cfg['output_contract']['animation_interval_ms'])
        (d/(name+suffix)).write_text('\n'.join(q for b in bb for q in b)+'\n',encoding='utf-8')
    th=[b[0] for b in blocks(out) if b[0].startswith('/TH/')];nr=len(th)-sum(k.startswith('/TH/PART/') for k in th)+3
    dump(d/'mesh.json',mesh);dump(d/'generation.json',{**g,'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'parent_deck':rel(PARENT/(g['name']+'_0000.rad')),'parent_deck_sha256':sha(PARENT/(g['name']+'_0000.rad')),'changed_cards':changed,'facade_translated_node_ids':fa,'facade_translation_mm':cfg['scene_changes']['facade_translation_mm'],'contact_segments':segments,'aircraft_diag_node_ids':diag,'history_records_per_frame':nr,'material_and_properties_changed':False,'RBE3_changed':False,'failure_transfer_enabled':False,'local_contact_control_not_full_impact':False,'full_historical_impact':False})
    dump(d/'scene_audit.json',{'pass':True,'aircraft_nodes':len(mesh['aircraft_node_ids']),'facade_nodes':len(fa),'contact_nodes_by_segment':{k:len(v) for k,v in segments.items()},'contact_node_domains_disjoint':True,'aircraft_geometry_unchanged':True,'materials_and_masses_unchanged':True,'aircraft_bounds_mm':[xyz[np.array(mesh['aircraft_node_ids'])-1].min(0).tolist(),xyz[np.array(mesh['aircraft_node_ids'])-1].max(0).tolist()],'facade_bounds_mm':[xyz[np.array(fa)-1].min(0).tolist(),xyz[np.array(fa)-1].max(0).tolist()],'undeformed_nose_gap_contact_estimate_ms':(50-5)/200,'estimate_not_measured_onset':True,'units':{'length':'mm','time':'ms','velocity':'mm/ms = m/s','native_mass':'g','native_energy':'g mm2/ms2 = 0.001 J','native_impulse':'g mm/ms = 0.001 Ns'}})
    print({'built':caseid,'history_records':nr,'airframe_contact_nodes':len(airskin),'diag_nodes':len(diag)},flush=True)

def run(caseid):
    guard();runner.OUT=OUT;runner.CFG=CFG;runner.guard=guard;runner.run(caseid)

def extend():
    guard();assert not EXT.exists();s=read(OUT/'initial_stage_review.json');assert s['one_ms_extension_numerically_allowed'],s
    new=[{'id':'NOSE_1_DT05','contact':True,'composite':True,'self_contact':True,'domain':'whole_exterior','dt_scale':.05,'end_ms':1.0}]
    dump(EXT,{'declared_utc':now(),'iteration':'AIRCRAFT-A11','parent_configuration_sha256':sha(CFG),'decision_evidence':rel(OUT/'initial_stage_review.json'),'decision_evidence_sha256':sha(OUT/'initial_stage_review.json'),'one_ms_numerical_extension':True,'material_domain_qualified':s['initial_material_domain_pass'],'physical_impact_qualified':False,'cases':new,'all_initial_gates_unchanged':True})
    dump(OUT/'extension_guard.json',{'declared_utc':now(),'sha256':sha(EXT),'before_extension_solver':True});print({'extension_declared':[q['id'] for q in new]},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','run','extend']);p.add_argument('--case',default='FREE_04');a=p.parse_args();globals()[a.action](a.case) if a.action in ['build','run'] else globals()[a.action]()
