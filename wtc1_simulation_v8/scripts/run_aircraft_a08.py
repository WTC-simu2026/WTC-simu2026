"""A08: bounded engine mesh/contact controls, richer native output, immutable A07."""
import argparse,copy,csv,re,shutil
from pathlib import Path
import numpy as np
from run_aircraft_a02 import ROOT,RUNTIME,read,dump,sha,rel,now,ff,ii,harness,execute
from run_aircraft_a04 import blocks
from run_aircraft_a06 import env
from run_aircraft_a07 import group
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a08_predeclaration.json'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a08'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a07'
PARENT=PREV/'r0/ENGINE_LOCAL'
def declare():
    assert not CFG.exists() and not OUT.exists();before=harness();assert before['Status']=='PASS' and before['CurrentIteration']=='AIRCRAFT-A07'
    c=read(ROOT/'wtc1_simulation_v8/data/aircraft_a07_predeclaration.json')
    c.update(iteration='AIRCRAFT-A08',seed=1102033,random_draws=0,parent_deck=rel(PARENT/'A07_ENGINE_LOCAL_0000.rad'),
        scope='Same coupled whole aircraft, facade at engine front; diagnostic contact controls, NOT historical whole flight through facade',
        mesh_refinement='Each engine triangle split into four coplanar triangles using shared edge midpoints. Original joint anchors and RBE3 hosts unchanged. No smoothing, no material/thickness/force adjustment.',
        output_contract={'history_interval_ms':0.002,'animation_interval_ms':0.1,'nodal_mass':True,'engine_ADMAS_node_velocities':32,'part_channels':['IE','KE','HE','PW','RKE','XMOM','YMOM','ZMOM','MASS'],'part_object_ids_per_line':10,'old_A07_engine_part_history_missing':True},
        nodal_mass_theory={'triangle_weights':'interior angle / pi','old_equal_thirds_CG_review_superseded_only_in_A08':True,'source':'https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_TheoryManual.pdf','printed_page':154,'equation':574},
        sources=c['sources']+['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/anim_mass_engine_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_part_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type7_starter_r.htm'],
        comparison_limits={'instrument_impulse_fraction':0.01,'instrument_generated_energy_fraction':0.02,'mesh_impulse_fraction':0.05,'mesh_generated_energy_fraction':0.10,'half_dt_impulse_fraction':0.05,'half_dt_generated_energy_fraction':0.10},
        execution={'starter_timeout_s':90,'engine_timeout_s':300,'converter_timeout_s':60,'cpu_threads':2,'GPU':False,'cases':[
            {'id':'FREE','contact':False,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.8,'end_ms':0.8,'split_contact':False,'fine':False},
            {'id':'DENSE','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.8,'end_ms':0.8,'split_contact':False,'fine':False},
            {'id':'SPLIT','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.8,'end_ms':0.8,'split_contact':True,'fine':False},
            {'id':'FINE','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.8,'end_ms':0.8,'split_contact':True,'fine':True},
            {'id':'FINE_HALF','contact':True,'composite':True,'self_contact':True,'domain':'engines_only','dt_scale':0.4,'end_ms':0.8,'split_contact':True,'fine':True}]})
    dump(CFG,c);OUT.mkdir();dump(OUT/'harness_before.json',before)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for n in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/n)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values())});dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_any_new_solver':True})
    src=[PARENT/n for n in ['A07_ENGINE_LOCAL_0000.rad','A07_ENGINE_LOCAL_0001.rad','A07_ENGINE_LOCAL_0002.rad','mesh.json','generation.json']]+[PREV/'source_manifest.json']
    dump(OUT/'source_manifest.json',{'created_utc':now(),'local_inputs':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size,'redistribution':'own_or_prior_input'} for p in src],'primary_links':c['sources'],'inherited_sources_manifest':rel(PREV/'source_manifest.json'),'archive_rescanned':False})
    print({'declared':True,'pinned_old_files':len(pins)},flush=True)
def guard():assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def preserved():
    rows=read(OUT/'preservation_before.json')['files'];assert all(sha(ROOT/r['path'])==r['sha256'] for r in rows);return len(rows)
def triangle(v):
    mass=np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))/2
    angles=[]
    for i in range(3):
        a=v[(i+1)%3]-v[i];b=v[(i+2)%3]-v[i];angles.append(np.arccos(np.clip(np.dot(a,b)/np.linalg.norm(a)/np.linalg.norm(b),-1,1)))
    assert abs(sum(angles)-np.pi)<1e-10
    return mass,np.array(angles)/np.pi
def cached():
    guard();s=read(PREV/'additional_verification.json');rows=[]
    for rr in s['cases']:
        d=PREV/'r0'/rr['case'];g=read(d/'generation.json');x=np.array(read(d/'mesh.json')['nodes_mm']);cor=np.zeros(3);parts={}
        for _,p,tr in g['added_engine_shells']:
            v=x[np.array(tr)-1];area,w=triangle(v);mass=area*(2*2.78e-6 if p in [22,25] else 5*7.86e-6);cor+=mass*(w@v-v.mean(0))
            if p not in parts:parts[p]=[0.,np.zeros(3)]
            parts[p][0]+=mass;parts[p][1]+=mass*(w@v)
        M=read(d/'audit.json')['native_total_mass_kg'];pred=np.array(rr['predicted_native_total_CG_mm'])+cor/M;err=float(np.max(abs(pred-np.array(rr['native_total_CG_mm']))))
        rows.append({'case':rr['case'],'previous_equal_thirds_error_mm':rr['CG_error_mm'],'corrected_angle_weighted_error_mm':err,'pass_unchanged_1e_5_mm_gate':err<1e-5,'corrected_predicted_total_CG_mm':pred.tolist(),'native_total_CG_mm':rr['native_total_CG_mm'],'new_shell_part_CG_mm':{str(p):(q[1]/q[0]).tolist() for p,q in parts.items()}})
    H=histories(PARENT/'A07_ENGINE_LOCALT01.csv');engine_part_present=any('A07_NACELLE' in k or 'A07_ENGINE_CASE' in k for k in H)
    dump(OUT/'cached_A07_mass_output_review.json',{'created_utc':now(),'old_solver_reruns':0,'cases':rows,'all_corrected_CG_gates_pass':all(q['pass_unchanged_1e_5_mm_gate'] for q in rows),'mass_or_force_changed':False,'old_failed_gate_and_interpretation_preserved':True,'A07_engine_part_energy_channels_present':engine_part_present,'finding':'The original equal-third triangle review was inconsistent with native angle-weighted lumping. A08 corrects the reviewer, not the model. Native A07 CSV lacks added engine part energy channels; A08 wraps object IDs into ten-column rows and verifies exact native channel coverage.'})
    print({'cached_CG_errors_mm':[q['corrected_angle_weighted_error_mm'] for q in rows],'A07_engine_part_channels_present':engine_part_present},flush=True)
def build(caseid):
    guard();cfg=read(CFG);c=next(q for q in cfg['execution']['cases'] if q['id']==caseid);d=OUT/'r0'/caseid;assert not d.exists();d.mkdir(parents=True);name='A08_'+caseid
    bs=blocks((PARENT/'A07_ENGINE_LOCAL_0000.rad').read_text(encoding='utf-8').splitlines());orig={b[0]:b for b in bs};mesh=read(PARENT/'mesh.json');g=read(PARENT/'generation.json');xyz=np.array(mesh['nodes_mm']).tolist();oldtri=copy.deepcopy(g['added_engine_shells']);shells=oldtri;newids=[];edge={}
    if c['fine']:
        def mid(a,b):
            k=tuple(sorted((a,b)))
            if k not in edge:xyz.append(((np.array(xyz[a-1])+xyz[b-1])/2).tolist());edge[k]=len(xyz);newids.append(len(xyz))
            return edge[k]
        shells=[];eid=200000
        for _,p,(a,b,z) in oldtri:
            ab,bz,za=mid(a,b),mid(b,z),mid(z,a)
            for tr in [[a,ab,za],[ab,b,bz],[za,bz,z],[ab,bz,za]]:eid+=1;shells.append([eid,p,tr])
        nold=len(oldtri);mesh['original_triangle_node_ids']=mesh['original_triangle_node_ids'][:-nold]+[q[2] for q in shells];mesh['aircraft_triangle_ids']=mesh['aircraft_triangle_ids'][:-nold]+[q[0] for q in shells];mesh['aircraft_triangle_part_ids']=mesh['aircraft_triangle_part_ids'][:-nold]+[q[1] for q in shells]
    ids=g['added_engine_nodes']+newids;mesh.update(nodes_mm=xyz,aircraft_node_ids=mesh['aircraft_node_ids']+newids,aircraft_node_count=mesh['aircraft_node_count']+len(newids),aircraft_contact_node_ids=ids)
    segments={'NACELLE':sorted({n for _,p,tr in shells if p in [22,25] for n in tr}),'FAN':sorted({n for _,p,tr in shells if p in [23,26] for n in tr}),'CORE':sorted({n for _,p,tr in shells if p in [24,27] for n in tr})}
    assert set(sum(segments.values(),[]))==set(ids) and len(sum(segments.values(),[]))==len(ids)
    titles={22:'A08_NAC_L',23:'A08_FAN_L',24:'A08_CORE_L',25:'A08_NAC_R',26:'A08_FAN_R',27:'A08_CORE_R',28:'A08_JOINTS'};out=[]
    for b0 in bs:
        b=b0.copy();key=b[0]
        if key in ['/BEGIN','/TITLE']:b[1]=name
        elif key=='/NODE':b=[key]+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
        elif key=='/GRNOD/NODE/1':b=group(1,'ALL_AIRCRAFT_NODES',mesh['aircraft_node_ids'])
        elif key=='/GRNOD/NODE/1002':b=group(1002,'A08_ENGINE_CONTACT_DOMAIN',ids)
        elif key.startswith('/SH3N/') and int(key.split('/')[-1]) in range(22,28):b=[key]+[ii(e,*tr) for e,p,tr in shells if p==int(key.split('/')[-1])]
        elif key.startswith('/PART/') and int(key.split('/')[-1]) in titles:b[1]=titles[int(key.split('/')[-1])]
        elif key=='/TH/PART/31':
            pids=list(range(1,19))+list(range(22,29));b=[key,b[1],''.join(f'{v:>10}' for v in cfg['output_contract']['part_channels'])]+[ii(*pids[i:i+10]) for i in range(0,len(pids),10)]
        elif key in ['/INTER/TYPE7/1','/TH/INTER/1'] and (not c['contact'] or c['split_contact']):continue
        elif key=='/END':continue
        out+=b
    if c['contact'] and c['split_contact']:
        for k,(label,nodes) in enumerate(segments.items()):
            gid=1100+k;cid=101+k;b=copy.deepcopy(orig['/INTER/TYPE7/1']);b[0]=f'/INTER/TYPE7/{cid}';b[1]='A08_'+label+'_TO_FACADE';b[2]=ii(gid)+b[2][10:];out+=group(gid,'A08_'+label,nodes)+b+[f'/TH/INTER/{101+k}','CONTACT_RAW_HISTORY_'+label,orig['/TH/INTER/1'][2],ii(cid)]
    out+=['/TH/NODE/51','ENGINE_ADMAS_VELOCITY',''.join(f'{v:>10}' for v in ['VX','VY','VZ'])]+[ii(n,0)+f'M{n}' for n in range(2861,2893)]+['/END']
    (d/(name+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    for suff in ['_0001.rad','_0002.rad']:
        bb=blocks((PARENT/('A07_ENGINE_LOCAL'+suff)).read_text().replace('A07_ENGINE_LOCAL',name).splitlines())
        for b in bb:
            if b[0]=='/DT':b[1]=ff(c['dt_scale'],0)
            if b[0].startswith('/RUN/'):b[1]=ff(c['end_ms']+(1e-6 if suff=='_0002.rad' else 0))
            if b[0].startswith('/TFILE') and suff=='_0001.rad':b[1]=ff(.002)
        bb.append(['/ANIM/MASS']);(d/(name+suff)).write_text('\n'.join(x for b in bb for x in b)+'\n',encoding='utf-8')
    areas={};moment=np.zeros(3);oldmoment=np.zeros(3)
    for qlist,mom in [(shells,moment),(oldtri,oldmoment)]:
        for _,p,tr in qlist:
            v=np.array(xyz)[np.array(tr)-1];area,w=triangle(v);mom+=area*(2*2.78e-6 if p in [22,25] else 5*7.86e-6)*(w@v)
            if qlist is shells:areas[p]=areas.get(p,0.)+area
    dump(d/'mesh.json',mesh);dump(d/'generation.json',{**g,'name':name,'case':c,'created_utc':now(),'configuration_sha256':sha(CFG),'generator_sha256':sha(Path(__file__)),'parent_deck':rel(PARENT/'A07_ENGINE_LOCAL_0000.rad'),'parent_deck_sha256':sha(PARENT/'A07_ENGINE_LOCAL_0000.rad'),'added_engine_nodes':ids,'added_engine_shells':shells,'contact_segments':segments,'refinement_new_nodes':newids,'piecewise_surface_area_mm2_by_part':areas,'native_nodal_CG_moment_shift_kg_mm':(moment-oldmoment).tolist(),'history_records_per_frame':10+(2 if c['split_contact'] else 0)-(0 if c['contact'] else 1),'part_titles':titles,'failure_transfer_enabled':False})
    print({'built':caseid,'engine_nodes':len(ids),'engine_triangles':len(shells),'TH_records':read(d/'generation.json')['history_records_per_frame']},flush=True)
def run(caseid):
    guard();d=OUT/'r0'/caseid;g=read(d/'generation.json');n=g['name'];c=read(CFG)['execution'];assert not (d/'starter.log').exists()
    assert execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',c['starter_timeout_s'],env())
    txt=(d/'starter.log').read_text(errors='replace');assert int(re.findall(r'(\d+) WARNING\(S\)',txt)[-1])==0 and int(re.findall(r'(\d+) ERROR\(S\)',txt)[-1])==0,txt[-4000:]
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',c['engine_timeout_s'],env())
    pins={p.name:sha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
    for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
    assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env());assert all(sha(d/p)==h for p,h in pins.items());dump(d/'observer_preservation.json',{'main_outputs_unchanged':True})
    assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter_T01.log',90,env())
    H=histories(d/(n+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'));nr=g['history_records_per_frame'];header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[0]==4 and sizes[1]==88 and all([len(q) for q in f]==sizes for f in frames)
    nat=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert nat.shape==v.shape and np.allclose(nat,v,rtol=6e-7,atol=1e-12)
    ro=records(o/(n+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (o/(n+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:wr=csv.writer(f);wr.writerow(list(H));wr.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'main_rows_matched':len(v),'records_per_frame':nr,'sizes':sizes,'all_native_channels_verified_against_CSV':True,'observer_initial_row_only':True,'end_ms':float(end[0])});print({'completed':caseid,'end_ms':float(end[0])},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','cached','build','run']);p.add_argument('--case',default='FREE');a=p.parse_args();globals()[a.action](a.case) if a.action in ['build','run'] else globals()[a.action]()
