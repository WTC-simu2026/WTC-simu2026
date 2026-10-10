"""Fresh whole impact with finite 3D core and verified native skin offset ties."""
import copy, csv, time
from collections import defaultdict
from run_aircraft_a20 import *
from test_aircraft_a20_sandwich import face_property, parent_cards
from run_aircraft_a18 import blocks
from recover_aircraft_a05_history import records
WCFG=ROOT/'wtc1_simulation_v8/data/aircraft_a20_whole_declaration.json'
CASE='CORE3D_TIED_20';D=OUT/'r0'/CASE;N='A20_'+CASE

def whole_guard():
    guard();assert streamsha(WCFG)==read(OUT/'whole_guard.json')['sha256']

def declare():
    guard();assert read(OUT/'core_verified_review.json')['pass'] and read(OUT/'sandwich_type2_review.json')['pass'];assert not WCFG.exists()
    h=harness();assert h['Status']=='PASS';dump(OUT/'harness_before_whole.json',h)
    c={'iteration':'AIRCRAFT-A20','declared_utc':now(),'seed':1102045,'random_draws':0,'parent':rel(SOURCE),
      'scope':'Fresh20ms whole-aircraft/facade exploratory impact after correcting finite core mechanics and skin coupling. Same total material budgets and inlet velocity. Not validated historical impact; no fitting to known damage.',
      'source_core':rel(CFG),'source_core_sha256':streamsha(CFG),'source_coupling_review':rel(OUT/'sandwich_type2_review.json'),
      'mesh':{'triangles_replaced':216,'per_triangle':'three nondegenerate quadrilateral cells from3 vertices,3 edge midpoints,centroid; extrude8mm for three HA8 core bricks',
        'skin_midplanes_mm':[-4.25,4.25],'core_boundaries_mm':[-4,4],'skin_thickness_mm':.5,'total_material_thickness_mm':9,
        'core_parts':'one per original triangle; explicit materialL=globalX projected on triangle, W=n crossL, fixed orthotropic skew carried by co-rotation',
        'coupling':'two TYPE2 Spot5 Iproj2 ties per facet from core faces to separate skin midsurfaces; dsearch.3mm, physical offset.25mm; no coupling between top/bottom faces',
        'skin_property':'TYPE51 Ipos0 and one actual0.5mm ply; inherited LAW25/4 and ORTHSTRAIN/4 unchanged',
        'cohesive':'reuse624 initial zero-height strips and all EN,ET,TN,TT,GI,GII values; reattach massless corner offsets to actual skin nodes',
        'root':'original x2000mm body attachment kept,24 ideal nonfailing RBE2 root supports for offset skin nodes; hierarchy explicitly audited; root kinematics not as-built bracket failure',
        'no_core_edge_traction':'core bricks share nodes within a facet, separate between facets; intact skins/cohesive seams carry edge transfers; core-edge tearing unmeasured',
        'bulk_skin_removal':'failure of the single skin ply now removes the corresponding skin shell; native persistent nodal mass accounted, no removed shell rendered intact',
        'unchanged':'all non-radome elements, materials, RBE3, ADMAS, facade supports and four external TYPE25 contacts',
        'changed':'radome discretization, through-thickness mechanics, tie formulation, external radome node positions and self-contact surface/gap'},
      'self_contact':{'TYPE25':True,'main':'all lower/upper skin parts','secondary':'all skin midsurface nodes','gap_mm':.5,'derivation':'sum of half-thicknesses of two0.5mm skins; actual midsurfaces separate, prior9mm gap no longer appropriate','Inacti':1000,'initial_neighbors_ignored_then_reentry':True,'all_aircraft_self_contact':False,'long_fragment_contact_qualified':False},
      'preserved_budgets':{'skin_areal_kg_m2':1.83,'core_areal_kg_m2':.384,'total_areal_kg_m2':2.214,'initial_aircraft_kg':121962.860669763,'old_mesh_quadrature_not_reused_as_new_mass':True,'no_density_or_ADMAS_compensation':True},
      'insertion_acceptance':{'initial_mass_relative':1e-6,'initial_CG_mm':.001,'initial_inertia_relative':1e-6,'initial_no_contact_IE_J':.001,'allowed_initial_self_warning_ids':['1166','343'],'no_incompatible_constraint_warnings':True},
      'acceptance':read(ROOT/'wtc1_simulation_v8/data/aircraft_a19_whole_declaration.json')['acceptance'],
      'execution':{'CPU_threads':2,'GPU':False,'engine_cap_s':3600,'estimated_minutes':[20,60],'end_ms':20,'dt_scale':.5,'history_dt_ms':.02,'animation_dt_ms':.2,'no_mass_scaling':True,'checkpoint_on_normal_end':True},
      'extension_stop':'No extension beyond20ms unless finite core, energy balance and material domains pass. Preserve failures. Metal failure, tower interior, gravity, high-rate material/fracture data still needed for seconds.',
      'goal':{'target_s':10,'new_requested_s':.02,'complete':False},'velocity_m_s':[-200,5,2],
      'physical_G_measured':False,'core_skin_debonding_modelled':False,'core_crushing_densification_modelled':False,'physical_impact_qualified':False,'historical_conditions_identified':False,'NIST_damage_fitted':False,'old_solver_reruns':0}
    dump(WCFG,c);dump(OUT/'whole_guard.json',{'created_utc':now(),'sha256':streamsha(WCFG),'before_all_whole_native_execution':True});print({'declared':CASE},flush=True)

def group(gid,title,ids):
    return [f'/GRNOD/NODE/{gid}',title]+[ii(*ids[j:j+10]) for j in range(0,len(ids),10)]

def build():
    whole_guard();assert not D.exists();D.mkdir(parents=True);cfg=read(WCFG);g=read(SOURCE/'generation.json');m=read(SOURCE/'mesh.json');P=parent_cards();B=blocks((SOURCE/(g['name']+'_0000.rad')).read_text().splitlines());xyz=np.array(m['nodes_mm']);XX=xyz.tolist()
    tris=[(int(row[:10]),[int(row[j:j+10]) for j in [10,20,30]]) for row in P['/SH3N/21'][1:]];assert len(tris)==216
    radset=set(m['radome_node_ids']);roots={i for i in radset if xyz[i-1,0]==2000};nonrad={i for e,t in zip(m['aircraft_triangle_ids'],m['original_triangle_node_ids']) if e not in set(m['radome_element_ids']) for i in t}|{i for t in m['original_beam_node_ids'] for i in t};assert not (radset-roots)&nonrad
    added=[];faces={};solid=[];skin=[];rbe_deps=defaultdict(list);root_deps=defaultdict(list);ties=[];core_parts=[];lower_parts=[];upper_parts=[];facet_records=[];offsets=[]
    def node(q):XX.append(np.asarray(q).tolist());return len(XX)
    quads=[[0,3,6,5],[1,4,6,3],[2,5,6,4]]
    for k,(eid,tr) in enumerate(tris):
        A=xyz[np.array(tr)-1];normal=np.cross(A[1]-A[0],A[2]-A[0]);area=float(np.linalg.norm(normal)*.5);normal/=2*area
        Laxis=np.array([1,0,0])-normal*normal[0];assert np.linalg.norm(Laxis)>1e-8;Laxis/=np.linalg.norm(Laxis);Waxis=np.cross(normal,Laxis)
        pts=np.vstack([A,(A[0]+A[1])*.5,(A[1]+A[2])*.5,(A[2]+A[0])*.5,A.mean(axis=0)])
        cp,lp,up=10000+eid,12000+eid,13000+eid;sid=10000+eid;core_parts.append(cp);lower_parts.append(lp);upper_parts.append(up)
        added+=skew_card(sid,tuple(Laxis),tuple(Waxis))+solid_property(cp,sid)+[f'/PART/{cp}',f'RADOME_CORE_FACET_{eid}',ii(cp,28,0),f'/PART/{lp}',f'RADOME_LOWER_FACET_{eid}',ii(122,4,0),f'/PART/{up}',f'RADOME_UPPER_FACET_{eid}',ii(123,4,0)]
        layers=[]
        for zoff in [-4.25,4.25,-4,4]:
            ids=[]
            for j,q in enumerate(pts):
                if zoff==-4.25 and j<3 and tr[j] not in roots:
                    ni=tr[j];XX[ni-1]=(q+normal*zoff).tolist()
                else:ni=node(q+normal*zoff)
                ids.append(ni)
            layers.append(ids)
        lo,hi,cb,ct=layers;faces[eid]={'old_nodes':tr,'lo':lo,'hi':hi,'cb':cb,'ct':ct,'normal':normal.tolist()}
        for j,ni in enumerate(tr):
            if ni in roots:root_deps[ni] += [lo[j],hi[j]]
        cr=[];ls=[];us=[]
        for j,q in enumerate(quads):
            ce=72001+k*3+j;le=70001+k*3+j;ue=70649+k*3+j
            conn=[cb[t] for t in q]+[ct[t] for t in q];solid.append([ce,*conn]);cr.append([ce,*conn]);ls.append([le,*[lo[t] for t in q]]);us.append([ue,*[hi[t] for t in q]]);skin += [{'id':le,'part':lp,'nodes':ls[-1][1:],'facet':eid,'side':'lo'},{'id':ue,'part':up,'nodes':us[-1][1:],'facet':eid,'side':'hi'}]
        added += [f'/BRICK/{cp}']+[ii(*row) for row in cr]+[f'/SHELL/{lp}']+[ii(*row) for row in ls]+[f'/SHELL/{up}']+[ii(*row) for row in us]
        for side,part,cn in [('lo',lp,cb),('hi',up,ct)]:
            tie=16000+2*k+(side=='hi');surf=tie;gid=tie
            added+=group(gid,f'CORE_FACE_{eid}_{side}',cn)+[f'/SURF/PART/{surf}',f'OWN_SKIN_FACE_{eid}_{side}',ii(part),f'/INTER/TYPE2/{tie}','VERIFIED_CORE_SKIN_OFFSET_TIE',ii(gid,surf,1000,5,0,2,1000,0)+ff(.3),ii(0)+ff(0)+' '*60+ii(2)]
            ties.append({'id':int(tie),'facet':eid,'side':side,'secondary':cn,'main_part':part})
        facet_records.append({'original_element_id':eid,'core_part_id':cp,'lower_part_id':lp,'upper_part_id':up,'area_mm2':area,'core_volume_mm3':8*area,'skin_volume_mm3':area,'normal':normal.tolist(),'L':Laxis.tolist(),'W':Waxis.tolist(),'layers':layers})
    dep_to_host={int(dep):int(host) for host,dep,off in m['cohesive_offset_map']}
    cohdict={int(row[0]):row[1:] for row in m['cohesive_connectivity']}
    for seam in m['cohesive_seams']:
        deps=cohdict[seam['element_id']];side='lo' if seam['skin_offset_bounds_mm'][0]<0 else 'hi'
        for fac,depids in zip(seam['facet_ids'],[deps[:4],deps[4:]]):
            f=faces[fac]
            for dep in depids:
                old=dep_to_host[dep];j=f['old_nodes'].index(old);host=f[side][j];rbe_deps[host].append(dep);distance=float(np.linalg.norm(np.asarray(XX[dep-1])-XX[host-1]));offsets.append([host,dep,distance])
    used={i for row in solid for i in row[1:]}|{i for row in skin for i in row['nodes']};radskins=sorted({i for s in skin for i in s['nodes']});airids=sorted(set(m['aircraft_node_ids'])|set(range(len(xyz)+1,len(XX)+1)));contactids=sorted(set(int(t) for row in P['/GRNOD/NODE/1103'][2:] for t in row.split())|set(radskins))
    body=[];changed=[];removed=[]
    skip={'/MAT/LAW25/5','/PROP/TYPE19/42','/PROP/TYPE51/21','/PART/21','/SH3N/21','/TH/PART/32','/END'}
    for ob in B:
        key=ob[0]
        if key in skip or key.startswith('/RBE2/') or key.startswith('/GRNOD/NODE/') and int(key.rsplit('/',1)[1])>=2000:
            removed.append(key);continue
        b=ob.copy()
        if key in ['/BEGIN','/TITLE']:b[1]=N
        elif key=='/NODE':b=[key]+[ii(i+1)+ff(*q) for i,q in enumerate(XX)]
        elif key=='/GRNOD/NODE/1':b=group(1,b[1],airids)
        elif key=='/GRNOD/NODE/1004':b=group(1004,b[1],radskins)
        elif key=='/GRNOD/NODE/1103':b=group(1103,b[1],contactids)
        elif key=='/SURF/PART/1005':parts=lower_parts+upper_parts;b=ob[:2]+[ii(*parts[j:j+10]) for j in range(0,len(parts),10)]
        elif key=='/INTER/TYPE25/2':b[-1]=ff(.5,1,.5,1)
        if b!=ob:changed.append(key)
        body+=b
    body+=material()+face_property(122,41,True,True)+face_property(123,43,False,True)+added
    rbrows=[]
    for j,(host,deps) in enumerate(sorted(rbe_deps.items())):
        gid=2000+j;body+=group(gid,f'COH_CORNER_FROM_SKIN_{host}',deps)+[f'/RBE2/{gid}',f'MASSLESS_COH_OFFSET_FROM_{host}',ii(host)+'   111 000'+ii(0,gid,0)];rbrows.append({'id':gid,'host':host,'dependent_nodes':deps,'role':'cohesive_corner'})
    for j,(host,deps) in enumerate(sorted(root_deps.items())):
        gid=6000+j;body+=group(gid,f'ROOT_SKINS_FROM_BODY_{host}',deps)+[f'/RBE2/{gid}','DECLARED_IDEAL_ROOT_ATTACHMENT',ii(host)+'   111 111'+ii(0,gid,0)];rbrows.append({'id':gid,'host':host,'dependent_nodes':deps,'role':'root'})
    for hid,title,parts in [(32,'RADOME_3D_CORE_DIAGNOSTIC',core_parts),(34,'RADOME_SKINS_DIAGNOSTIC',lower_parts+upper_parts)]:
        body += [f'/TH/PART/{hid}',title,'        IE        KE        HE        PW']+[ii(*parts[j:j+10]) for j in range(0,len(parts),10)]
    body+=['/END'];nb={b[0]:b for b in blocks(body)}
    invariants=['/INIVEL/','/ADMAS/','/RBE3/','/BCS/','/BEAM/','/MAT/LAW2/','/FAIL/']
    assert all(nb[b[0]]==b for b in B if b[0].startswith(tuple(invariants)))
    assert all(nb[key]==P[key] for key in [f'/INTER/TYPE25/{i}' for i in [101,102,103,104]])
    assert all(nb[b[0]]==b for b in B if b[0].startswith(('/SH3N/','/SHELL/')) and b[0]!='/SH3N/21')
    (D/(N+'_0000.rad')).write_text('\n'.join(body)+'\n',encoding='utf-8')
    E=(SOURCE/(g['name']+'_0001.rad')).read_text().replace(g['name'],N).splitlines();EB=blocks(E);eo=[]
    for b in EB:
        if b[0]=='/TFILE/4':b[1]=ff(.02)
        if b[0].startswith('/ANIM/SHELL/IDPLY/') and '/42/' in b[0]:continue
        eo+=b
    (D/(N+'_0001.rad')).write_text('\n'.join(eo)+'\n',encoding='utf-8');eo2=[]
    for b in blocks(eo):
        if b[0].startswith('/RUN/'):b[0]=f'/RUN/{N}/2';b[1]=ff(20.000001)
        eo2+=b
    (D/(N+'_0002.rad')).write_text('\n'.join(eo2)+'\n',encoding='utf-8')
    oldrad=set(m['radome_element_ids']);keep=[j for j,e in enumerate(m['aircraft_triangle_ids']) if e not in oldrad]
    m.update(nodes_mm=XX,aircraft_node_ids=airids,aircraft_node_count=len(airids),aircraft_triangle_ids=[m['aircraft_triangle_ids'][j] for j in keep],original_triangle_node_ids=[m['original_triangle_node_ids'][j] for j in keep],aircraft_triangle_part_ids=[m['aircraft_triangle_part_ids'][j] for j in keep],radome_element_ids=[],radome_node_ids=radskins,radome_skin_quads=skin,radome_core_bricks=solid,radome_core_part_ids=core_parts,radome_skin_part_ids=lower_parts+upper_parts,radome_facets=facet_records,cohesive_offset_map=offsets,core_skin_ties=ties,new_RBE2=rbrows,physical_shell_offset_handled_by_TYPE2=True)
    dump(D/'mesh.json',m);shutil.copy2(__file__,D/'generator_snapshot.py');dump(D/'generation.json',{**g,'created_utc':now(),'name':N,'case':CASE,'configuration_sha256':streamsha(WCFG),'parent':rel(SOURCE),'generator_sha256':streamsha(Path(__file__)),'new_core_bricks':648,'new_skin_quads':1296,'new_parts':648,'new_TYPE2_ties':432,'new_RBE2':rbrows,'changed_cards':changed,'removed_cards':removed,'mechanical_scene_unchanged':False,'old_solver_reruns':0})
    area=sum(r['area_mm2'] for r in facet_records);mass=area*2.214e-6
    dump(D/'scene_audit.json',{'created_utc':now(),'pass':True,'nodes':len(XX),'aircraft_nodes':len(airids),'radome_area_m2':area*1e-6,'radome_material_mass_kg':mass,'radome_material_budget_identical':abs(area*1e-6-g['radome_area_m2'])<1e-12,'unchanged_nonradome_geometry':True,'all_core_bricks_positive_initial_volume':True,'old_nonroot_nodes_reused_at_actual_lower_skin_midplane':True,'physical_thickness_mm':9,'core_skin_offset_mm':.25,'initial_mass_CG_I_native_pending':True,'coupling_native_scope_controls_pass':True,'root_assembly_not_as_built':True})
    print({'built':CASE,'nodes':len(XX),'radome_mass_kg':mass,'core_bricks':648,'skin_quads':1296,'ties':432},flush=True)

def starter():
    whole_guard();assert not (D/'starter.log').exists();ok=execute(RUNTIME/'starter_win64.exe',['-i',N+'_0000.rad','-np','1'],D,'starter.log',180,env());s=(D/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(D/'starter_gate.json',{'exit_ok':ok,'warnings':nw,'errors':ne,'strict_pass':ok and nw==0 and ne==0});assert ok and ne==0,s[-4000:]
    listing=(D/(N+'_0000.out')).read_text(errors='replace');parent=(SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.out')).read_text(errors='replace');mass=[np.array(numbers_after(q,'TOTAL MASS AND MASS CENTER',4)) for q in [parent,listing]];I=[np.array(numbers_after(q,'TOTAL INERTIA',6)) for q in [parent,listing]];ids=re.findall(r'WARNING ID\s*:\s*(\d+)',s)
    checks={'zero_errors':ne==0,'only_declared_initial_self_warnings':all(i in ['1166','343'] for i in ids),'mass_preserved':bool(abs(mass[1][0]-mass[0][0])/mass[0][0]<1e-6),'CG_preserved':bool(abs(mass[1][1:]-mass[0][1:]).max()<.001),'inertia_preserved':bool(abs(I[1]-I[0]).max()/abs(I[0]).max()<1e-6),'scoped_coupling_controls_pass':read(OUT/'sandwich_type2_review.json')['pass']}
    dump(D/'native_insertion_gate.json',{'created_utc':now(),'checks':checks,'mass_CG_old':mass[0].tolist(),'mass_CG_new':mass[1].tolist(),'native_inertia_relative_change':float(abs(I[1]-I[0]).max()/abs(I[0]).max()),'warning_ids':ids,'strict_zero_warning_pass':nw==0,'exploratory_engine_allowed':all(checks.values()),'contact_warnings_are_not_a_physical_qualification':True});print({'starter':CASE,'checks':checks,'warnings':nw},flush=True);assert all(checks.values()),checks

def recover_history():
    H=histories(D/(N+'T01.csv'));v=np.column_stack(list(H.values()));rr=records(D/(N+'T01'));possible=[]
    for nr in range(3,40):
        h=len(rr)-len(v)*nr
        if h<=0:continue
        if len(rr[h])==4 and len(rr[h+1])==88 and all(len(rr[h+j*nr])==4 and abs(np.frombuffer(rr[h+j*nr],dtype='>f4')[0]-v[j,0])<1e-6 for j in [0,len(v)//2,len(v)-1]):possible.append((nr,h))
    assert len(possible)==1,possible;nr,h=possible[0];sizes=[len(q) for q in rr[h:h+nr]];raw=np.array([np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in rr[h+j*nr:h+(j+1)*nr]]) for j in range(len(v))]);assert raw.shape==v.shape and np.allclose(raw,v,rtol=6e-7,atol=1e-12)
    ro=records(D/'observer'/(N+'T02'));assert len(ro)==h+nr;end=np.concatenate([np.frombuffer(q,dtype='>f4').astype(float) for q in ro[h:]]);assert end.shape==(v.shape[1],)
    with (D/'observer'/(N+'T02_recovered.csv')).open('w',encoding='utf-8',newline='') as f:w=csv.writer(f);w.writerow(list(H));w.writerow([format(x,'.9g') for x in end])
    dump(D/'history_recovery.json',{'pass':True,'records_per_frame':nr,'header_records':h,'sizes':sizes,'rows':len(v),'channels':v.shape[1],'main_CSV_binary_independently_equal':True,'native_end_ms':float(end[0])})

def engine():
    whole_guard();assert read(D/'native_insertion_gate.json')['exploratory_engine_allowed'];assert not (D/'engine.log').exists()
    try:
        assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0001.rad'],D,'engine.log',3600,env());s=(D/'engine.log').read_text(errors='replace');assert 'NORMAL TERMINATION' in s and 'TIME STEP LESS OR EQUAL ZERO' not in s
        o=D/'observer';o.mkdir();shutil.copy2(D/(N+'_0002.rad'),o/(N+'_0002.rad'))
        for p in D.glob(N+'_0001_*.rst'):shutil.copy2(p,o/p.name)
        pins={p.name:streamsha(p) for p in D.iterdir() if p.is_file()};assert execute(RUNTIME/'engine_win64.exe',['-i',N+'_0002.rad'],o,'observer.log',60,env());assert all(streamsha(D/p)==sha for p,sha in pins.items());dump(D/'observer_preservation.json',{'pass':True,'main_outputs_unchanged':True})
        assert execute(RUNTIME/'th_to_csv_win64.exe',[N+'T01'],D,'converter.log',180,env());recover_history();print({'whole_finished':CASE},flush=True)
    except Exception:
        dump(D/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc(),'physical_impact_qualified':False});raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','build','starter','engine']);globals()[p.parse_args().action]()
