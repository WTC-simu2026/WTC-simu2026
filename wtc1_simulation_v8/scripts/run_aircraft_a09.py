"""Predeclared whole-aircraft onset controls: unchanged materials, contact and RBE3 formulations."""
import argparse,copy,re,shutil,urllib.request
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness
from run_aircraft_a04 import blocks
import run_aircraft_a08 as predecessor
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a09_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a09'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a08'
EXT=ROOT/'wtc1_simulation_v8/data/aircraft_a09_effective_stiffness_extension.json'
def cases():return read(CFG)['execution']['cases']+(read(EXT)['cases'] if EXT.exists() else [])
def extend():
    guard();assert not EXT.exists();cfg=read(CFG);new=[]
    for name,parent,factor in [('EFFECTIVE_FINE_01','FINE',.01),('EFFECTIVE_FINE_001','FINE',.001),('EFFECTIVE_COARSE_001','SPLIT',.001)]:
        new.append({**cfg['execution']['cases'][0],'id':name,'parent':parent,'fine':parent=='FINE','Stfac':factor})
    dump(EXT,{'iteration':'AIRCRAFT-A09','declared_utc':now(),'seed':1102034,'random_draws':0,'parent_configuration_sha256':sha(CFG),'reason':'Saved BASE/SOFT0.1 native histories identical. Official TYPE7 formula scales only main stiffness Km=Stfac*E*t; secondary Ks=E*t and Istf4 uses min. Thus0.1 need not change effective stiffness. Test0.01/0.001 separately without changing materials, gap or gate thresholds. No criterion or old result edited.','primary_source':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm','cases':new,'selection_by_NIST_outcome':False,'new_cases_before_execution':True})
    dump(OUT/'extension_guard.json',{'sha256':sha(EXT),'before_new_extended_solver':True});print({'extended_cases_declared':[c['id'] for c in new]},flush=True)
def declare():
    assert not CFG.exists() and not OUT.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A08'
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a08_predeclaration.json');c.update(iteration='AIRCRAFT-A09',seed=1102034,random_draws=0,
      scope='Fresh intact coupled aircraft. Diagnostic onset0.4ms, same displaced facade and engines-only exterior contact. Not complete historical flight through a tower.',
      sources=['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe3_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm'],
      declared_mechanism_controls={'TYPE7_Istf4':'minimum main/secondary stiffness, inherited','TYPE7_Istf5':'main/secondary stiffness in series, documented alternative','Stfac0.1':'numerical penalty sensitivity only, not material softness identification','RBE3_Iform2':'inherited engine32 constraints, kinematic only','RBE3_Iform3':'engine32 constraints penalty only, documented alternative; other336 unchanged','material_failure':'disabled; no material or thickness changes','stored_constraint_energy':'all native global spring/IE/damping/contact terms retained; missing attribution must not be assumed zero'},
      output_contract={'history_interval_ms':.002,'animation_interval_ms':.1,'engine_shell_and_hub_node_channels':['VX','VY','VZ','VRX','VRY','VRZ'],'original32_ADMAS_velocity_channels_retained':True,'nodal_mass':True,'IOFLAG_Idrot_unchanged':True},
      acceptance_extra={'instrument_J_fraction':.01,'instrument_generated_fraction':.02,'native_shell_rotation_relative_fraction':.05,'native_shell_rotation_absolute_allowance_J':50,'native_historical_CG_error_mm':1e-5},
      execution={'starter_timeout_s':90,'engine_timeout_s':300,'converter_timeout_s':60,'cpu_threads':2,'GPU':False,'cases':[
        {'id':'BASE_FINE','parent':'FINE','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':.8,'end_ms':.4,'fine':True,'Istf':4,'Stfac':1.,'engine_RBE3_Iform':2},
        {'id':'SERIES_FINE','parent':'FINE','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':.8,'end_ms':.4,'fine':True,'Istf':5,'Stfac':1.,'engine_RBE3_Iform':2},
        {'id':'SOFT_FINE','parent':'FINE','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':.8,'end_ms':.4,'fine':True,'Istf':4,'Stfac':.1,'engine_RBE3_Iform':2},
        {'id':'SOFT_COARSE','parent':'SPLIT','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':.8,'end_ms':.4,'fine':False,'Istf':4,'Stfac':.1,'engine_RBE3_Iform':2},
        {'id':'PENALTY_FINE','parent':'FINE','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':.8,'end_ms':.4,'fine':True,'Istf':4,'Stfac':1.,'engine_RBE3_Iform':3},
        {'id':'PENALTY_FREE','parent':'FINE','contact':False,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':.8,'end_ms':.4,'fine':True,'Istf':4,'Stfac':1.,'engine_RBE3_Iform':3}]})
    dump(CFG,c);OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for n in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/n)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    # Newly acquired A08 sources also preserved without rescanning archives.
    for r in read(PREV/'source_manifest.json')['new_primary_sources']:pins[r['path']]={'path':r['path'],'sha256':r['sha256'],'bytes':r['bytes']}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_new_solver':True})
    inputs=[PREV/'authoritative_review.json',PREV/'additional_verification.json',PREV/'source_manifest.json']
    for case in ['SPLIT','FINE']:
        inputs.extend(PREV/'r0'/case/n for n in ['generation.json','mesh.json','A08_'+case+'_0000.rad','A08_'+case+'_0001.rad','A08_'+case+'_0002.rad','balance_history_SI.npz'])
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs],'primary_links':c['sources'],'inherited_material_sources':rel(PREV/'source_manifest.json'),'archive_rescanned':False})
    p=ROOT/'wtc1_simulation_v8/input/aircraft_a09_sources';p.mkdir();rows=[]
    for i,url in enumerate(c['sources']):
        file=p/['TYPE7.html','RBE3.html','TH_NODE.html'][i];req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'});file.write_bytes(urllib.request.urlopen(req,timeout=60).read());rows.append({'path':rel(file),'url':url,'sha256':sha(file),'bytes':file.stat().st_size,'redistribution':'exclude_third_party'})
    dump(p/'acquisition.json',{'created_utc':now(),'sources':rows,'read_only_after_acquisition':True});s=read(OUT/'source_manifest.json');s['new_primary_sources']=rows;dump(OUT/'source_manifest.json',s);print({'declared':True,'old_files_pinned':len(pins),'cases':6},flush=True)
def guard():
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    if EXT.exists():assert sha(EXT)==read(OUT/'extension_guard.json')['sha256']
def preserved():
    rows=read(OUT/'preservation_before.json')['files'];assert all(sha(ROOT/r['path'])==r['sha256'] for r in rows);return len(rows)
def build(caseid):
    guard();c=next(q for q in cases() if q['id']==caseid);p=PREV/'r0'/c['parent'];g=read(p/'generation.json');d=OUT/'r0'/caseid;assert not d.exists();d.mkdir(parents=True);name='A09_'+caseid;bs=blocks((p/(g['name']+'_0000.rad')).read_text(encoding='utf-8').splitlines());out=[];modified=[]
    diag=sorted(set(g['added_engine_nodes']+[2859,2860]));form_changes=[]
    for b0 in bs:
        b=b0.copy();key=b[0]
        if key in ['/BEGIN','/TITLE']:b[1]=name
        elif key.startswith('/INTER/TYPE7/') and int(key.split('/')[-1]) in [101,102,103]:
            if not c['contact']:continue
            b[2]=b[2][:20]+ii(c['Istf'])+b[2][30:];b[5]=ff(c['Stfac'])+b[5][20:]
        elif key.startswith('/TH/INTER/') and int(key.split('/')[-1]) in [101,102,103] and not c['contact']:continue
        elif key.startswith('/RBE3/') and 1<=int(key.split('/')[-1])<=32:
            assert int(b[2][0:10]) in range(2861,2893) and int(b[2][40:50])==2
            if c['engine_RBE3_Iform']!=2:b[2]=b[2][:40]+ii(c['engine_RBE3_Iform'])+b[2][50:];form_changes.append(int(key.split('/')[-1]))
        elif key=='/END':continue
        if b!=b0:modified.append(key)
        out+=b
    out+=['/TH/NODE/52','ENGINE_NATIVE_VELOCITY_ROTATION',''.join(f'{v:>10}' for v in ['VX','VY','VZ','VRX','VRY','VRZ'])]+[ii(n,0)+f'N{n}' for n in diag]+['/END']
    (d/(name+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    for suffix in ['_0001.rad','_0002.rad']:
        bb=blocks((p/(g['name']+suffix)).read_text().replace(g['name'],name).splitlines())
        for b in bb:
            if b[0]=='/DT':b[1]=ff(c['dt_scale'],0)
            if b[0].startswith('/RUN/'):b[1]=ff(c['end_ms']+(1e-6 if suffix=='_0002.rad' else 0))
        (d/(name+suffix)).write_text('\n'.join(q for b in bb for q in b)+'\n',encoding='utf-8')
    th=[b[0] for b in blocks(out) if b[0].startswith('/TH/')];nr=len(th)-sum(k.startswith('/TH/PART/') for k in th)+1+2
    shutil.copy2(p/'mesh.json',d/'mesh.json');meta={**g,'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'extension_configuration_sha256':sha(EXT) if caseid.startswith('EFFECTIVE') else None,'generator_sha256':sha(Path(__file__)),'parent_deck':rel(p/(g['name']+'_0000.rad')),'parent_deck_sha256':sha(p/(g['name']+'_0000.rad')),'changed_cards':modified,'engine_RBE3_Iform_changed_IDs':form_changes,'history_records_per_frame':nr,'native_TH_PART_groups_aggregated_into_one_record':True,'dense_engine_diag_node_ids':diag,'material_and_properties_changed':False,'failure_transfer_enabled':False};dump(d/'generation.json',meta);print({'built':caseid,'native_diag_nodes':len(diag),'TH_records':meta['history_records_per_frame'],'RBE3_changed':len(form_changes)},flush=True)
def run(caseid):
    predecessor.OUT=OUT;predecessor.CFG=CFG;predecessor.run(caseid)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','extend','build','run']);p.add_argument('--case',default='BASE_FINE');a=p.parse_args();globals()[a.action](a.case) if a.action in ['build','run'] else globals()[a.action]()
