"""A07: new deformable engine envelopes in the coupled whole-aircraft model."""
import argparse,copy,json,csv,re,shutil,subprocess,os
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
from run_aircraft_a04 import blocks
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records
from run_aircraft_a06 import env
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a07_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a07'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a06'
PARENT=PREV/'r1/ZERO_DM'
def declare():
    assert not CFG.exists() and not OUT.exists();assert harness()['CurrentIteration']=='AIRCRAFT-A06'
    inherited=read(PREV/'inherited_field_audit_configuration.json')
    c={**inherited,'iteration':'AIRCRAFT-A07','seed':1102032,'random_draws':0,'NIST_outcomes_used_as_target':False,
       'parent_deck':rel(PARENT/'A06_ZERO_DM_0000.rad'),'fresh_intact_only':True,'failure_transfer_enabled':False,
       'sources':['https://www.easa.europa.eu/en/downloads/136365/en','https://www.geaerospace.com/commercial/aircraft-engines/cf6',
       'https://www.boeing.com/content/dam/boeing/boeingdotcom/commercial/airports/acaps/767.pdf'],
       'engine':{'reference_family':'CF6-80A/A2, not a historical aircraft engine identification',
       'dry_mass_kg':3980.7,'dry_mass_original_lb':8776,'mass_scope':'EASA p19 note1 includes basic accessories and listed optional equipment/sensors',
       'bare_length_mm':4239.3,'bare_length_original_in':166.9,'bare_width_mm':2486.6,'bare_height_mm':2415.5,
       'envelope_scope':'EASA p9 bare engine overall dimensions; they do not identify nacelle contours, structural radii or thicknesses',
       'assembly_budget_kg':4500,'assembly_budget_is_own_hypothesis':True,'additional_external_budget_kg':519.3,
       'front_x_mm':15468.6,'center_y_mm':[-7924.8,7924.8],'center_z_mm':-3000,
       'location_scope':'Boeing airport-planning geometry inherited; vertical offset own hypothesis',
       'theta_count':24,'nacelle_profile_mm':[[0,1200],[300,1300],[1200,1300],[2400,1120],[3400,900],[4239.3,700]],
       'fan_case_profile_mm':[[150,1100],[600,1100],[1200,1100]],
       'core_case_profile_mm':[[1200,550],[2000,550],[3000,550],[4239.3,550]],
       'all_profiles_are_own_hypotheses':True,'nacelle_thickness_mm':2,'case_thickness_mm':5,
       'nacelle_material':'inherited aluminum reference LAW2/1, not measured nacelle material',
       'case_and_mount_material':'inherited generic steel reference LAW2/3, not actual engine alloy identification',
       'mount_area_mm2':400,'mount_Iyy_Izz_mm4':80000,'mount_J_mm4':160000,
       'weak_hub_mount_area_factor':0.5,'weak_hub_mount_inertia_factor':0.25,
       'mass_partition':'dry shell mass subtracted from3980.7; nacelle+new joints subtracted from519.3; nonnegative residual distributed in32 existing engine ADMAS points; old pylon mass unchanged',
       'RBE3_scope':'engine inertia supported only by new engine shell nodes; no direct nearest-wing shortcut',
       'unmodeled':['blades/disks/rotor spin','actual nacelle layup','mount failure','engine crushing/fragmentation','engine self-contact']},
       'execution':{'starter_timeout_s':90,'engine_timeout_s':300,'converter_timeout_s':60,'cpu_threads':2,'GPU':False,
       'cases':[{'id':'FREE','contact':False,'composite':True,'self_contact':True,'domain':'none','dt_scale':0.8,'end_ms':0.6},
       {'id':'NOSE','contact':True,'composite':True,'self_contact':True,'domain':'all_external','dt_scale':0.8,'end_ms':0.6},
       {'id':'ENGINE_LOCAL','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.8,'end_ms':0.8},
       {'id':'ENGINE_HALF','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.4,'end_ms':0.8},
       {'id':'ENGINE_WEAK','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.8,'end_ms':0.8,'weak_hub_mounts':True}]},
       'local_control_scope':'Whole coupled airframe retained; facade translated by engine front x, only new engine shell secondary nodes contact it. Nose/wing contact intentionally excluded; this is not a full flight-through-facade simulation.',
       'comparison_limits':{'half_dt_impulse_fraction':0.05,'half_dt_generated_energy_fraction':0.10},
       'energy_contract_for_future_fracture':{'E_MPa':22000,'sigma_MPa':450,'G_N_mm':50,'G_is_unmeasured_trial':True,'candidate':'traction-opening law with maximum-opening history and explicit stored/dissipated energy; not transferred to Engine or whole airplane'}}
    dump(CFG,c);OUT.mkdir();dump(OUT/'harness_before.json',harness())
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for n in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/n)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_new_solver':True})
    src=list((ROOT/'wtc1_simulation_v8/input/aircraft_a07_sources').glob('*'))+[PARENT/'A06_ZERO_DM_0000.rad',PARENT/'mesh.json',ROOT/'wtc1_simulation_v8/output/aircraft_a02/r1/solver_mesh.json',ROOT/'wtc1_simulation_v8/input/impact_i02_geom/boeing/767_REV_K.pdf']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party' if p.suffix in ['.pdf','.png','.html'] else 'own_or_prior_input'} for p in src],'primary_links':c['sources'],'archive_rescanned':False})
    print({'declared':True,'old_files':len(pins)},flush=True)
def guard():assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def preserved():
    rows=read(OUT/'preservation_before.json')['files'];assert all(sha(ROOT/r['path'])==r['sha256'] for r in rows);return len(rows)
def group(gid,title,ids):return [f'/GRNOD/NODE/{gid}',title]+[ii(*ids[i:i+10]) for i in range(0,len(ids),10)]
def build(caseid,revision='r0'):
    guard();cfg=read(CFG);c=next(c for c in cfg['execution']['cases'] if c['id']==caseid);e=cfg['engine'];d=OUT/revision/caseid;assert not d.exists();d.mkdir(parents=True);name='A07_'+caseid
    bs=blocks((PARENT/'A06_ZERO_DM_0000.rad').read_text(encoding='utf-8').splitlines());orig={b[0]:b for b in bs};mesh=read(PARENT/'mesh.json');oldmeta=read(PARENT/'generation.json');xyz=np.array(mesh['nodes_mm']).tolist();newnodes=[];shells=[];beams=[];sections=[];ledger=[];hostchanges={};sid=100000;bid=110000
    def node(q):xyz.append(list(map(float,q)));newnodes.append(len(xyz));return len(xyz)
    def tube(profile,y,part):
        nonlocal sid
        rings=[];mass=0.;rho=2.78e-3 if part in [22,25] else 7.86e-3;t=e['nacelle_thickness_mm'] if part in [22,25] else e['case_thickness_mm']
        for x,r in profile:rings.append([node([e['front_x_mm']+x,y+r*np.cos(a),e['center_z_mm']+r*np.sin(a)]) for a in np.arange(e['theta_count'])*2*np.pi/e['theta_count']])
        for left,right in zip(rings[:-1],rings[1:]):
            for j in range(e['theta_count']):
                k=(j+1)%e['theta_count']
                for tr in [[left[j],right[j],right[k]],[left[j],right[k],left[k]]]:
                    sid+=1;v=np.array([xyz[n-1] for n in tr]);area=np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2;mass+=rho*t*area*.001;shells.append((sid,part,tr))
        return rings,mass
    def joint(a,b,weak=False):
        nonlocal bid
        bid+=1;prop=29 if weak else 28;L=np.linalg.norm(np.array(xyz[a-1])-xyz[b-1]);mass=L*e['mount_area_mm2']*(e['weak_hub_mount_area_factor'] if weak else 1)*7.86e-6;beams.append((bid,prop,a,b));return mass
    for k,y in enumerate(e['center_y_mm']):
        pn=22+3*k;nf,mn=tube(e['nacelle_profile_mm'],y,pn);ffan,mf=tube(e['fan_case_profile_mm'],y,pn+1);cc,mc=tube(e['core_case_profile_mm'],y,pn+2);mj=0
        for j in range(0,24,3):
            mj+=joint(nf[2][j],ffan[-1][j]);mj+=joint(nf[4][j],cc[-2][j]);mj+=joint(ffan[-1][j],cc[0][j])
        for ring,j in [(ffan[-1],0),(ffan[-1],12),(cc[-2],6),(cc[-2],18)]:mj+=joint(2859+k,ring[j],bool(c.get('weak_hub_mounts')))
        dryrem=e['dry_mass_kg']-mf-mc;externalrem=e['additional_external_budget_kg']-mn-mj;assert dryrem>0 and externalrem>0
        ids=[n for ring in ffan+cc for n in ring];pts=np.array([xyz[n-1] for n in ids]);admass=(dryrem+externalrem)/16
        for j in range(16):
            ni=2861+16*k+j;xoff=600 if j<8 else 3000;r=750 if j<8 else 350;theta=(j%8)*np.pi/4;xyz[ni-1]=[e['front_x_mm']+xoff,y+r*np.cos(theta),e['center_z_mm']+r*np.sin(theta)];near=np.argsort(np.sum((pts-np.array(xyz[ni-1]))**2,axis=1),kind='stable')[:8];hostchanges[100+16*k+j]=[ids[i] for i in near]
        ledger.append({'side':k,'dry_shell_mass_kg':mf+mc,'nacelle_shell_mass_kg':mn,'new_joint_mass_kg':mj,'dry_residual_kg':dryrem,'external_residual_kg':externalrem,'admas_each_kg':admass,'assembly_total_kg':mn+mf+mc+mj+16*admass,'pylon_mass_is_inherited_separately':True})
    airids=mesh['aircraft_node_ids']+newnodes;contact=newnodes if c['domain']=='engines_only' else mesh['aircraft_contact_node_ids']+newnodes
    if c['domain']=='engines_only':
        for ni in range(3228,35020):xyz[ni][0]+=e['front_x_mm']
    out=[];changes=[]
    for b0 in bs:
        b=b0.copy();key=b[0]
        if key=='/BEGIN':b[1]=name
        elif key=='/TITLE':b[1]=name
        elif key=='/NODE':b=['/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
        elif key=='/GRNOD/NODE/1':b=group(1,'ALL_AIRCRAFT_NODES',airids)
        elif key=='/GRNOD/NODE/1002':b=group(1002,'A07_DECLARED_CONTACT_DOMAIN',contact)
        elif key.startswith('/GRNOD/NODE/') and int(key.split('/')[-1]) in hostchanges:b=group(int(key.split('/')[-1]),'ENGINE_ONLY_INERTIAL_HOSTS',hostchanges[int(key.split('/')[-1])])
        elif key=='/ADMAS/5/1':
            b=[key,b[1]]+[ff(ledger[(int(q[20:30])-2861)//16]['admas_each_kg']*1000)+q[20:] if 2861<=int(q[20:30])<=2892 else q for q in b[2:] if q.strip() and not q.startswith('#')]
        elif key=='/TH/PART/31':b=b[:3]+[ii(*(list(range(1,19))+list(range(22,29 if not c.get('weak_hub_mounts') else 30))))]
        elif key=='/TH/BEAM/41':b=b[:3]+[ii(el)+' '*10+f'B{el:<70}' for el in oldmeta['beam_history_ids']+[q[0] for q in beams]+list(range(11135,11139))]
        elif not c['contact'] and key in ['/INTER/TYPE7/1','/TH/INTER/1']:continue
        if b!=b0:changes.append(key)
        if key=='/END':continue
        out+=b
    for p in range(22,28):
        pb=copy.deepcopy(orig['/PROP/TYPE1/1']);pb[0]=f'/PROP/TYPE1/{p}';pb[1]='A07_NACELLE' if p in [22,25] else 'A07_ENGINE_CASE';pb[4]=ii(5)+' '*10+ff(e['nacelle_thickness_mm'] if p in [22,25] else e['case_thickness_mm'],5/6);out+=pb+[f'/PART/{p}',pb[1],ii(p,1 if p in [22,25] else 3,0),f'/SH3N/{p}']+[ii(q[0],*q[2]) for q in shells if q[1]==p]
    for p,af,If in [(28,1,1),(29,e['weak_hub_mount_area_factor'],e['weak_hub_mount_inertia_factor'])]:
        if not any(q[1]==p for q in beams):continue
        pb=copy.deepcopy(orig['/PROP/TYPE3/12']);pb[0]=f'/PROP/TYPE3/{p}';pb[1]='A07_JOINT_REFERENCE';pb[4]=ff(e['mount_area_mm2']*af,e['mount_Iyy_Izz_mm4']*If,e['mount_Iyy_Izz_mm4']*If,e['mount_J_mm4']*If);out+=pb+[f'/PART/{p}','A07_JOINT_REFERENCE',ii(p,3,0),f'/BEAM/{p}']
        for el,pr,a,b in beams:
            if pr!=p:continue
            direction=np.array(xyz[b-1])-xyz[a-1];axis=np.eye(3)[int(np.argmin(abs(direction)))];axis-=direction*np.dot(axis,direction)/np.dot(direction,direction);axis/=np.linalg.norm(axis);out+=[ii(el,a,b,0)+ff(*axis)]
    out+=['/END'];(d/(name+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    for suffix in ['_0001.rad','_0002.rad']:
        bb=blocks((PARENT/('A06_ZERO_DM'+suffix)).read_text(encoding='utf-8').replace('A06_ZERO_DM',name).splitlines())
        for b in bb:
            if b[0]=='/DT':b[1]=ff(c['dt_scale'],0)
            if b[0].startswith('/RUN/'):b[1]=ff(c['end_ms']+(1e-6 if suffix=='_0002.rad' else 0))
            if b[0]=='/ANIM/DT' and suffix=='_0001.rad':b[1]=ff(0,.1)
        (d/(name+suffix)).write_text('\n'.join(x for b in bb for x in b)+'\n',encoding='utf-8')
    mesh.update(nodes_mm=xyz,aircraft_node_count=len(airids),aircraft_node_ids=airids,aircraft_contact_node_ids=contact)
    for el,p,tr in shells:mesh['original_triangle_node_ids'].append(tr);mesh['aircraft_triangle_ids'].append(el);mesh['aircraft_triangle_part_ids'].append(p)
    for el,p,a,b in beams:mesh['original_beam_node_ids'].append([a,b]);mesh['aircraft_beam_ids'].append(el)
    # CG prediction accounts for relocated old inertia and all new structural mass, with no correction force or mass top-up.
    oldx=np.array(read(PARENT/'mesh.json')['nodes_mm']);moment=np.array(mesh['expected_aircraft_CG_mm'])*mesh['expected_aircraft_mass_kg']
    for k,row in enumerate(ledger):
        for j in range(16):ni=2860+16*k+j;moment+=row['admas_each_kg']*np.array(xyz[ni])-281.25*oldx[ni]
    for el,p,tr in shells:
        v=np.array([xyz[n-1] for n in tr]);mass=np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2*(2.78e-3*2 if p in [22,25] else 7.86e-3*5)*.001;moment+=mass*v.mean(0)
    for el,p,a,b in beams:
        mass=np.linalg.norm(np.array(xyz[a-1])-xyz[b-1])*400*(.5 if p==29 else 1)*7.86e-6;moment+=mass*(np.array(xyz[a-1])+xyz[b-1])/2
    mesh['expected_aircraft_CG_mm']=(moment/mesh['expected_aircraft_mass_kg']).tolist();dump(d/'mesh.json',mesh)
    dump(d/'generation.json',{**oldmeta,'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'parent_deck':rel(PARENT/'A06_ZERO_DM_0000.rad'),'parent_deck_sha256':sha(PARENT/'A06_ZERO_DM_0000.rad'),'changed_old_cards':changes,'added_engine_nodes':newnodes,'added_engine_shells':shells,'added_joint_beams':beams,'engine_mass_ledger':ledger,'RBE3_engine_hosts':hostchanges,'beam_history_ids':oldmeta['beam_history_ids']+[q[0] for q in beams]+list(range(11135,11139)),'beam_history_scope':'Inherited504 forward beams plus56 engine joints plus4 inherited pylons; canonical native9 channels','failure_transfer_enabled':False,'engine_self_contact_enabled':False,'local_contact_control_not_full_impact':c['domain']=='engines_only','expected_aircraft_CG_mm':mesh['expected_aircraft_CG_mm']});print({'built':caseid,'engine_shells':len(shells),'joints':len(beams),'mass_ledger':ledger},flush=True)
def run(caseid,revision='r0'):
    guard();d=OUT/revision/caseid;n=read(d/'generation.json')['name'];c=read(CFG)['execution'];assert not (d/'starter.log').exists()
    assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',c['starter_timeout_s'],env())
    txt=(d/'starter.log').read_text(encoding='utf-8',errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1])==0,txt[-4000:]
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',c['engine_timeout_s'],env())
    pins={p.name:sha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
    for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env());assert all(sha(d/p)==h for p,h in pins.items());dump(d/'observer_preservation.json',{'main_outputs_unchanged':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',90,env())
    H=histories(d/(n+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'));nr=9 if read(d/'generation.json')['case']['contact'] else 8;header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    nat=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert nat.shape==v.shape and np.allclose(nat,v,rtol=6e-7,atol=1e-12)
    ro=records(o/(n+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (o/(n+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:wr=csv.writer(f);wr.writerow(list(H));wr.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'main_rows_matched':len(v),'records_per_frame':nr,'sizes':sizes,'all_native_channels_verified_against_CSV':True,'observer_initial_row_only':True,'end_ms':float(end[0])});print({'completed':caseid,'end_ms':float(end[0])},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','run']);p.add_argument('--case',default='FREE');p.add_argument('--revision',default='r0');a=p.parse_args()
    if a.action=='declare':declare()
    else:globals()[a.action](a.case,a.revision)
