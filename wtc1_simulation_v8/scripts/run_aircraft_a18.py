"""A18: fresh coupled impact with separable radome facets; no historical fitting."""
import argparse,copy,json,re,shutil,traceback,urllib.request,csv
from pathlib import Path
from collections import defaultdict
import numpy as np
from run_aircraft_a17 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,SOURCE
from run_aircraft_a04 import blocks
from run_aircraft_a13 import contact25
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a18'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a18_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a17'
CASE='FACET_COHESIVE_20'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def declare():
    assert not OUT.exists() and not CFG.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A17'
    OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for fn in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/fn)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c=copy.deepcopy(read(ROOT/'wtc1_simulation_v8/data/aircraft_a16_predeclaration.json'))
    c.update(iteration='AIRCRAFT-A18',declared_utc=now(),seed=1102043,random_draws=0,
      scope='Fresh exploratory whole aircraft/facade20ms with native cohesive radome facet separation. Not physical validation; no earlier Engine rerun.',
      parent=rel(SOURCE),
      topology={'split':'216 radome triangles, distinct midsurface nodes per facet except original root at x2000mm retained shared',
        'original_nodes':'first incident facet keeps original ID; unchanged non-radome and RBE3 cards',
        'connections':'two zero-height LAW117/TYPE43 strips per internal radome edge, one through each0.5mm skin at z_local +/-4..4.5mm',
        'area':'each strip area = initial edge length *0.5mm; skin/core shell volume and material mass unchanged',
        'RBE2':'each offset corner tied to its own facet midsurface corner; Iflag0, dependent translations111000 includes independent rotational offsets',
        'core_edge_traction':'none;8mm core remains inside facets but core-edge tearing/crushing not identified or modelled',
        'bulk_damage':'retain exact A16R20 ORTHSTRAIN skin history inside facets; added interface work is separately recorded; combined mechanisms not physically calibrated',
        'path_bias':'cracks restricted to declared initial triangle edges; not a spatial convergence claim',
        'geometry_repositioned':False},
      cohesive={**read(ROOT/'wtc1_simulation_v8/data/aircraft_a17_predeclaration.json')['cohesive'],
        'material_id':117,'part_id':117,'property_id':117,'nodal_instrument_mass_g':0,'Ismstr':4,
        'Ismstr_change':'full geometric nonlinearities for moving facet offsets; A17 uniform tests alone do not qualify this transfer',
        'mixed_mode_qualified':False,'rotation_qualified':False,'compression_after_fracture_qualified':False},
      self_contact={'keyword':'TYPE25','secondary_group':1004,'main_surface':1005,'gap_mm':9,'Inacti':1000,
        'initial_pairs':'coincident split corner/neighbor pairs initially ignored natively until separation then reentry; no geometric shift or invented initial force',
        'limitation':'initially overlapping neighbors can compress before leaving gap; LAW117 compression remains while intact, postfailure contact recovery requires exit; unqualified for long fragment motion',
        'all_aircraft_self_contact':False},
      execution={'cpu_threads':2,'GPU':False,'starter_timeout_s':120,'engine_timeout_s':2700,'converter_timeout_s':120,'estimated_minutes':[17,45],
        'cases':[{'id':CASE,'end_ms':20,'dt_scale':.5,'transition_fraction':.2}],
        'stop':'error, nonpositive time step,2700s cap; preserve incomplete native attempts and checkpoints; no mass scaling or prescribed aircraft trajectory'},
      output_contract={'history_interval_ms':.01,'animation_interval_ms':.2,'geometry_review_stride':5,'damage':'native skin DAMA retained','cohesive':'native BRICK stress, ELEM energy and erosion plus separate nine-channel part history','observer':'isolated restart first record; no observer impulses mixed with main'},
      insertion_acceptance={'initial_mass_relative':1e-6,'initial_CG_mm':.001,'initial_inertia_relative':1e-6,'offset_RBE2_distance_error_mm':.001,'cohesive_initial_IE_J':.001,'no_initial_contact_work_J':.001,'shell_connectivity_exact':True},
      video={'source':rel(OUT/'r0'/CASE),'views':['whole','nose_closeup'],'resolution_each':[1280,720],'fps':30,'frames_per_saved_state':9,'displacement_scale':1,'geometry_interpolation':'constant exact native states','objective1_complete':False},
      physical_impact_qualified=False,NIST_outcomes_used_as_target=False,old_solver_reruns=0,
      goal={'target_physical_s':10,'complete':False,'previous_coverage_s':.010000175476,'requested_new_coverage_s':.02},
      sources=['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type25_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law117_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type43_connect_starter_r.htm'])
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_any_A18_solver':True})
    sd=OUT/'sources';sd.mkdir();src=[]
    for i,url in enumerate(c['sources']):
        p=sd/f'primary_{i}.html';p.write_bytes(urllib.request.urlopen(url,timeout=60).read());src.append({'path':rel(p),'url':url,'sha256':streamsha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    for p in [SOURCE/'generation.json',SOURCE/'mesh.json',SOURCE/'A16_IMPACT_R20_10_0000.rad',PREV/'cohesive_review.json',PREV/'scientific_assessment.json']:
        src.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':src,'archive_rescanned':False,'no_new_historical_video_analysis':True})
    print({'declared':'AIRCRAFT-A18','old_files_pinned':len(pins)},flush=True)

def build():
    guard();cfg=read(CFG);d=OUT/'r0'/CASE;assert not d.exists();d.mkdir(parents=True);n='A18_'+CASE
    m=read(SOURCE/'mesh.json');g=read(SOURCE/'generation.json');B=blocks((SOURCE/(g['name']+'_0000.rad')).read_text().splitlines());orig={b[0]:b for b in B}
    xyz=np.array(m['nodes_mm']);newxyz=xyz.tolist();radset=set(m['radome_element_ids']);T=[(int(row[:10]),[int(row[j:j+10]) for j in [10,20,30]]) for row in orig['/SH3N/21'][1:]]
    assert len(T)==216 and {e for e,t in T}==radset
    seen={};newtri={};corner_map={};edges=defaultdict(list);normal={};centroid={}
    root={i for i in m['radome_node_ids'] if xyz[i-1,0]==2000}
    for eid,tr in T:
        X=xyz[np.array(tr)-1];normal[eid]=np.cross(X[1]-X[0],X[2]-X[0]);normal[eid]/=np.linalg.norm(normal[eid]);centroid[eid]=X.mean(axis=0);nn=[]
        for ni in tr:
            if ni in root or ni not in seen:ni_new=ni;seen[ni]=eid
            else:newxyz.append(xyz[ni-1].tolist());ni_new=len(newxyz)
            corner_map[(eid,ni)]=ni_new;nn.append(ni_new)
        newtri[eid]=nn
        for a,b in zip(tr,tr[1:]+tr[:1]):edges[tuple(sorted([a,b]))].append(eid)
    assert all(len(es) in [1,2] for es in edges.values());facet_extra=list(range(len(xyz)+1,len(newxyz)+1));rbe_deps=defaultdict(list);coh=[];seams=[];offsets=[]
    # IDs >=60001 avoid all inherited shell/beam IDs and groups >=2000 avoid inherited groups.
    for (a,b),es in sorted(edges.items()):
        if len(es)!=2 or (a in root and b in root):continue
        ea,eb=es;norm=normal[ea]+normal[eb];norm/=np.linalg.norm(norm);A=xyz[a-1];BB=xyz[b-1];edge=BB-A;L=float(np.linalg.norm(edge))
        for low,high in [(-4.5,-4),(4,4.5)]:
            host_order=[a,b,b,a];Z=[low,low,high,high];face=[A+norm*low,BB+norm*low,BB+norm*high,A+norm*high]
            if np.dot(np.cross(face[1]-face[0],face[3]-face[0]),centroid[eb]-centroid[ea])<0:
                face=face[::-1];host_order=host_order[::-1];Z=Z[::-1]
            ids=[]
            for ee in [ea,eb]:
                for old,q,zoff in zip(host_order,face,Z):
                    newxyz.append(q.tolist());ni=len(newxyz);host=corner_map[(ee,old)];ids.append(ni);rbe_deps[host].append(ni);offsets.append([host,ni,float(abs(zoff))])
            eid=60001+len(coh);coh.append([eid,*ids]);seams.append({'element_id':eid,'facet_ids':[ea,eb],'original_edge':[a,b],'area_mm2':L*.5,'skin_offset_bounds_mm':[low,high]})
    dummy=list(range(len(xyz)+len(facet_extra)+1,len(newxyz)+1));radnodes=sorted({n for t in newtri.values() for n in t});airids=sorted(set(m['aircraft_node_ids']+facet_extra+dummy))
    changes=[];out=[]
    for old in B:
        b=old.copy();key=b[0]
        if key in ['/BEGIN','/TITLE']:b[1]=n
        elif key=='/NODE':b=[key]+[ii(i+1)+ff(*q) for i,q in enumerate(newxyz)]
        elif key=='/SH3N/21':b=[key]+[ii(e,*newtri[e]) for e,tr in T]
        elif key.startswith('/GRNOD/NODE/') and int(key.rsplit('/',1)[1]) in [1,1004,1103]:
            gid=int(key.rsplit('/',1)[1]);ids=airids if gid==1 else radnodes if gid==1004 else sorted(set([int(x) for row in old[2:] for x in row.split()]+facet_extra))
            b=old[:2]+[ii(*ids[j:j+10]) for j in range(0,len(ids),10)]
        elif key=='/INTER/TYPE7/2':
            b=contact25(9);b[0]='/INTER/TYPE25/2';b[1]='SPLIT_RADOME_SELF_INITIAL_PAIRS_IGNORED';b[2]=ii(0,1005,4,0,5,3,0,1000,1000,0);b[3]=ii(1004,0)+b[3][20:]
        elif key=='/END':continue
        if b!=old:changes.append(key)
        out+=b
    c=cfg['cohesive'];out+=['/MAT/LAW117/117','TRIAL_RADOME_EDGE_COHESION_NOT_IDENTIFIED',ff(c['area_mass_density_g_mm2']),ff(c['EN_N_mm3'],c['ET_N_mm3'])+ii(c['Imass'],c['Idel'],c['Irupt']),ii(0,0)+ff(c['TN_MPa'],c['TT_MPa'],1),ff(c['GI_N_mm'],c['GII_N_mm'],2,2,1),'/PROP/TYPE43/117','FINITE_ROTATION_ZERO_HEIGHT_STRIPS',ii(4)+' '*70+ff(0),'/PART/117','RADOME_EDGE_COHESIVE',ii(117,117,0),'/BRICK/117']+[ii(*row) for row in coh]
    rbe_rows=[]
    for i,(host,deps) in enumerate(sorted(rbe_deps.items())):
        gid=2000+i;out += [f'/GRNOD/NODE/{gid}',f'OFFSET_CORNERS_OF_{host}']+[ii(*deps[j:j+10]) for j in range(0,len(deps),10)]+[f'/RBE2/{gid}',f'RADOME_OFFSET_FROM_{host}',ii(host)+'   111 000'+ii(0,gid,0)];rbe_rows.append({'id':gid,'host':host,'dependent_nodes':deps})
    out+=['/TH/PART/33','RADOME_EDGE_COHESIVE',orig['/TH/PART/32'][2],ii(117),'/END']
    newblocks={b[0]:b for b in blocks(out)}
    assert all(newblocks[k]==b for k,b in orig.items() if k.startswith(('/MAT/','/PROP/','/PART/','/ADMAS/','/RBE3/','/BCS/','/INIVEL/','/BEAM/','/SHELL/','/FAIL/')))
    # Whole element areas, nodal locations and continuum mass moments remain exactly mapped to parent.
    area_error=0.
    for eid,tr in T:
        assert np.array_equal(xyz[np.array(tr)-1],np.array(newxyz)[np.array(newtri[eid])-1])
        A=xyz[np.array(tr)-1];AA=np.array(newxyz)[np.array(newtri[eid])-1];area_error=max(area_error,abs(np.linalg.norm(np.cross(A[1]-A[0],A[2]-A[0]))-np.linalg.norm(np.cross(AA[1]-AA[0],AA[2]-AA[0])))*.5)
    (d/(n+'_0000.rad')).write_text('\n'.join(out)+'\n',encoding='utf-8')
    for job in [1,2]:
        E=blocks((SOURCE/(g['name']+f'_000{job}.rad')).read_text().replace(g['name'],n).splitlines());eo=[]
        for b in E:
            if b[0].startswith('/RUN/'):b[1]=ff(20+(1e-6 if job==2 else 0))
            elif b[0]=='/ANIM/DT':b[1]=ff(0,.2)
            eo+=b
        eo+=['/ANIM/BRICK/TENS/STRESS'];(d/(n+f'_000{job}.rad')).write_text('\n'.join(eo)+'\n',encoding='utf-8')
    oldtr=m['original_triangle_node_ids'];m['original_triangle_node_ids']=[newtri.get(e,t) for e,t in zip(m['aircraft_triangle_ids'],oldtr)]
    m.update(nodes_mm=newxyz,aircraft_node_ids=airids,aircraft_node_count=len(airids),radome_node_ids=radnodes,cohesive_connectivity=coh,cohesive_part_id=117,cohesive_offset_map=offsets,cohesive_seams=seams,original_parent_radome_nodes=read(SOURCE/'mesh.json')['radome_node_ids'])
    dump(d/'mesh.json',m);shutil.copy2(__file__,d/'generator_snapshot.py')
    dump(d/'generation.json',{**g,'name':n,'case':cfg['execution']['cases'][0],'created_utc':now(),'parent':rel(SOURCE),'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__)),'changed_cards':changes,'mechanical_scene_unchanged':False,'new_RBE2':rbe_rows,'new_cohesive_elements':len(coh),'facet_extra_nodes':len(facet_extra),'cohesive_dummy_nodes':len(dummy),'history_records_per_frame':15,'full_historical_impact':False})
    dump(d/'scene_audit.json',{'created_utc':now(),'geometry_before_solve_pass':True,'exact_parent_shell_locations':True,'maximum_radome_area_error_mm2':area_error,'all_original_mass_material_RBE3_BCS_cards_unchanged':True,'cohesive_total_area_mm2':sum(s['area_mm2'] for s in seams),'cohesive_added_mass_kg_upper_bound':sum(s['area_mm2'] for s in seams)*c['area_mass_density_g_mm2']*.001,'core_edge_cohesion_absent':True,'native_mass_and_rotation_verification_pending':True,'split_triangles':len(T),'cohesive_elements':len(coh),'new_midsurface_nodes':len(facet_extra),'dummy_nodes':len(dummy),'new_RBE2':len(rbe_rows),'nodes':len(newxyz),'aircraft_nodes':len(airids)})
    print({'built':CASE,'nodes':len(newxyz),'cohesive_elements':len(coh),'offset_RBE2':len(rbe_rows)},flush=True)

def starter():
    guard();d=OUT/'r0'/CASE;g=read(d/'generation.json');n=g['name'];assert not (d/'starter.log').exists()
    ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,env());s=(d/'starter.log').read_text(errors='replace')
    warnings=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);errors=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':warnings,'errors':errors,'pass':ok and not warnings and not errors});assert ok and not warnings and not errors,s[-4000:]
    print({'starter_pass':True},flush=True)

def recover(d,n):
    H=histories(d/(n+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(d/(n+'T01'));nr=14;header=len(rr)-len(v)*nr;assert header>0
    frames=[rr[header+i*nr:header+(i+1)*nr] for i in range(len(v))];sizes=[len(q) for q in frames[0]];assert sizes[:2]==[4,88] and all([len(q) for q in f]==sizes for f in frames)
    raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in f]) for f in frames]);assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
    ro=records(d/'observer'/(n+'T02'));assert len(ro)==header+nr and [len(q) for q in ro[header:]]==sizes;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[header:]]);assert end[0]>v[-1,0]
    with (d/'observer'/(n+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:w=csv.writer(f);w.writerow(list(H));w.writerow([format(q,'.9g') for q in end])
    dump(d/'history_recovery.json',{'pass':True,'rows':len(v),'records_per_frame':nr,'sizes':sizes,'all_channels_CSV_binary_verified':True,'actual_end_ms':float(end[0])})

def engine():
    guard();d=OUT/'r0'/CASE;g=read(d/'generation.json');n=g['name'];assert read(d/'starter_gate.json')['pass'] or read(d/'initial_overlap_diagnostic_gate.json')['exploratory_engine_allowed'];assert not (d/'engine.log').exists()
    try:
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',2700,env());s=(d/'engine.log').read_text(errors='replace');assert 'NORMAL TERMINATION' in s and 'TIME STEP LESS OR EQUAL ZERO' not in s
        pins={p.name:streamsha(p) for p in d.iterdir() if p.is_file()};o=d/'observer';o.mkdir();shutil.copy2(d/(n+'_0002.rad'),o/(n+'_0002.rad'))
        for p in d.glob(n+'_0001_*.rst'):shutil.copy2(p,o/p.name)
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0002.rad'],o,'observer.log',60,env());assert all(streamsha(d/p)==h for p,h in pins.items());dump(d/'observer_preservation.json',{'main_outputs_unchanged':True,'pass':True})
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,env());recover(d,n);print({'whole_finished':CASE},flush=True)
    except Exception:
        dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'traceback':traceback.format_exc(),'not_qualified':True});raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','starter','engine']);globals()[p.parse_args().action]()
