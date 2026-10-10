"""Finite, explicitly massive root connector controls; no old solver rerun or damage target."""
from run_aircraft_a20 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii
from test_aircraft_a19_triangles import histories
from run_aircraft_a18 import blocks
import argparse,json,shutil,re,traceback,urllib.request,time
from pathlib import Path
import numpy as np

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a22'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a22_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a21'
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20'

def geometry(nseg,straight=False):
    offsets=np.array(read(ROOT/'wtc1_simulation_v8/data/aircraft_a21_root_declaration.json')['nodes_mm'][1:])
    if straight:offsets=np.array([[20.,0,0]])
    xyz=[np.zeros(3)];beams=[]
    for v in offsets:
        last=1
        for j in range(1,nseg+1):
            xyz.append(v*j/nseg);nid=len(xyz);beams.append((last,nid));last=nid
    return np.asarray(xyz),np.asarray(beams),offsets

def mass_inertia(xyz,beams,diam,rho):
    area=np.pi*diam**2/4;I=np.pi*diam**4/64
    mass=np.zeros(len(xyz));tensor=np.zeros((3,3));continuous=np.zeros((3,3))
    for i,j in beams-1:
        q,p=xyz[i],xyz[j];v=p-q;L=np.linalg.norm(v);unit=v/L;m=rho*area*L
        mass[[i,j]]+=m/2
        section=rho*L*I*(np.eye(3)+np.outer(unit,unit))
        tensor+=section
        # Exact straight-cylinder integral, independent of nodal lumping.
        mid=(q+p)/2;continuous+=m*(np.dot(mid,mid)*np.eye(3)-np.outer(mid,mid)+L**2/12*(np.eye(3)-np.outer(unit,unit)))+section
    nodal=sum(m*(np.dot(q,q)*np.eye(3)-np.outer(q,q)) for m,q in zip(mass,xyz))
    return mass,nodal,tensor,continuous

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A21'
    cycle=read(ROOT/'harness/publication_cycle.json');assert cycle['last_published_iteration']=='AIRCRAFT-A21' and cycle['pending_count']==0
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    xyz,b,off=geometry(8);m,nodal,cross,cont=mass_inertia(xyz,b,.5,.00278)
    c={'iteration':'AIRCRAFT-A22','declared_utc':now(),'seed':1102047,'random_draws':0,
       'purpose':'Independent finite root beam connector, actual six offsets, no ideal constraint or nested TYPE2 in this isolated witness. Native ledger, known mass/inertia and free dynamics before any whole integration.',
       'geometry':{'root_offsets_mm':off.tolist(),'circular_diameter_mm':.5,'segments_per_spoke':[4,8],'all_spokes_share_host_node':True,'no_RBE2_RBE3_TYPE2_or_ADMAS':True,'shared_ends_are_point_connections_not_a_resolved_fastener_bearing_surface':True},
       'material':{'inherited':'LAW2/1 fuselage hypothesis A20','rho_g_mm3':.00278,'E_MPa':73100,'nu':.33,'yield_MPa':324,'hardening_MPa':0,'fracture':'absent; numerical elastic controls only','material_identified_as_AA11':False},
       'capacity':{'section_area_mm2':float(np.pi*.5**2/4),'second_moment_mm4':float(np.pi*.5**4/64),'elastic_axial_yield_N_per_spoke':float(324*np.pi*.5**2/4),'physical_fastener_strength_or_rupture_qualified':False},
       'mass_budget':{'one_root_g':float(m.sum()),'24_roots_added_g_if_integrated':float(m.sum()*24),'no_compensation':True,'whole_aircraft_unchanged_in_controls':True,'must_be_explicitly_added_if_later_integrated':True},
       'independent_inertia_g_mm2':{'lumped_centerline':nodal.tolist(),'physical_cross_section':cross.tolist(),'continuous_cylinders':cont.tolist(),'not_a_native_RKE_correction':True},
       'cases':['TRANSLATION_X','ROTATION_X','ROTATION_Y','ROTATION_Z','FREE_TRANSLATION','FREE_ROTATION_X','FREE_ROTATION_Y','FREE_ROTATION_Z','AXIAL'],
       'motion':{'duration_ms':1,'prescribed_path':'3*t^2-2*t^3 for t in [0,1]ms','translation_mm':10,'rotation_rad':float(np.pi/2),'free_translation_m_s':[10,5,2],'free_angular_rad_ms':.1,'axial_straight_length_mm':20,'axial_strain':.001},
       'execution':{'CPU_threads':1,'GPU':False,'dt_cap_ms':.000025,'history_dt_ms':.001,'animation_dt_ms':.1,'per_process_cap_s':120,'no_mass_scaling':True},
       'acceptance':{'mass_relative':1e-6,'mass_scaling_relative':1e-9,'energy_balance_fraction':.02,'absolute_energy_J':1e-7,'rigid_IE_J':1e-7,'physical_KE_fraction':.02,'analytic_axial_IE_fraction':.02,'motion_mm':.002,'velocity_m_s':.005,'free_momentum_fraction':.002,'free_energy_fraction':.002},
       'references':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type3_beam_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/beam_elements_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/beam_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inivel_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/th_node_starter_r.htm'],
       'no_historical_or_NIST_damage_target':True,'reuse_A20_passed_core_and_Spot5':True,'old_solver_reruns':0,'whole_impact_qualified':False,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'declared_before_new_solver':True})
    s=OUT/'sources';s.mkdir();sources=[]
    for j,u in enumerate(c['references']):
        p=s/f'beam_primary_{j}.html';p.write_bytes(urllib.request.urlopen(u,timeout=40).read());sources.append({'url':u,'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p),'redistribution':'exclude_third_party'})
    for p in [CFG,PREV/'scientific_assessment.json',PREV/'material_reference_assessment.json',SOURCE/'mesh.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/core_verified_review.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/sandwich_type2_review.json']:
        sources.append({'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'archive_rescanned':False})
    print({'declared':'AIRCRAFT-A22','controls':18,'one_root_mass_g':float(m.sum()),'24_root_added_mass_g_if_integrated':float(m.sum()*24)},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def prescribed(xyz,cid,T,c):
    s=3*T*T-2*T**3;sd=6*T-6*T*T
    X=np.broadcast_to(xyz,(len(T),*xyz.shape)).copy();V=np.zeros_like(X);angles=np.zeros_like(X);omega=np.zeros_like(X)
    if cid=='TRANSLATION_X':X[:,:,0]+=10*s[:,None];V[:,:,0]=10*sd[:,None]
    elif cid.startswith('ROTATION_'):
        ax='XYZ'.index(cid[-1]);u=np.eye(3)[ax];theta=np.pi/2*s
        X=xyz[None,:,:]*np.cos(theta)[:,None,None]+np.cross(u,xyz)[None,:,:]*np.sin(theta)[:,None,None]+u[None,None,:]*np.dot(xyz,u)[None,:,None]*(1-np.cos(theta)[:,None,None])
        V=np.cross(u,X)*(np.pi/2*sd)[:,None,None];angles[:,:,ax]=theta[:,None];omega[:,:,ax]=(np.pi/2*sd)[:,None]
    elif cid=='AXIAL':X[:,:,0]+=c['motion']['axial_strain']*s[:,None]*xyz[None,:,0];V[:,:,0]=c['motion']['axial_strain']*sd[:,None]*xyz[None,:,0]
    return X,V,angles,omega

def run_one(nseg,cid):
    guard();c=read(CFG);d=OUT/'w0'/f'{cid}_N{nseg}';n=f'A22_{cid}_N{nseg}';assert not d.exists();d.mkdir(parents=True)
    xyz,beam,_=geometry(nseg if cid!='AXIAL' else nseg*2,straight=cid=='AXIAL');mass,Ip,Ic,Icont=mass_inertia(xyz,beam,.5,.00278)
    parent={b[0]:b for b in blocks((SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.rad')).read_text().splitlines())}
    area=np.pi*.5**2/4;I=np.pi*.5**4/64
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    L+=parent['/MAT/LAW2/1']+['/PROP/TYPE3/1','FINITE_CIRCULAR_HALF_MM_CONNECTOR',ff(4),ff(0,1e-20),ff(area,I,I,2*I),'   000 000'+ii(0),'/PART/1','FINITE_ROOT_CONNECTOR',ii(1,1,0),'/BEAM/1']
    for eid,(i,j) in enumerate(beam,1):
        u=xyz[j-1]-xyz[i-1];vec=np.eye(3)[np.argmin(abs(u/np.linalg.norm(u)))];L.append(ii(eid,int(i),int(j),0)+ff(*vec))
    for ni in range(1,len(xyz)+1):L+=[f'/GRNOD/NODE/{ni}',f'NODE_{ni}',ii(ni)]
    L+=['/GRNOD/NODE/1000','ALL_FINITE_CONNECTOR_NODES']+[ii(*range(j,min(j+10,len(xyz)+1))) for j in range(1,len(xyz)+1,10)]
    if cid.startswith('FREE_'):
        omega=np.eye(3)['XYZ'.index(cid[-1])]*.1 if cid.startswith('FREE_ROTATION_') else np.zeros(3)
        V=np.cross(omega,xyz) if cid.startswith('FREE_ROTATION_') else np.broadcast_to([10.,5,2],xyz.shape)
        for ni,v in enumerate(V,1):L+=[f'/INIVEL/TRA/{ni}',f'INDEPENDENT_KNOWN_NODE_VELOCITY_{ni}',ff(*v)+ii(ni,0)]
        L+=['/INIVEL/ROT/1000','FINITE_BEAM_KNOWN_ANGULAR_VELOCITY',ff(*omega)+ii(1000,0)]
    else:
        ts=np.linspace(0,1,10001);X,V,A,W=prescribed(xyz,cid,ts,c);disp=X-xyz;fid=10000
        for ni in range(1,len(xyz)+1):
            for ax,direction in enumerate(['X','Y','Z','XX','YY','ZZ']):
                fid+=1;values=disp[:,ni-1,ax] if ax<3 else A[:,ni-1,ax-3]
                L+=[f'/FUNCT/{fid}',f'KNOWN_MOTION_{ni}_{direction}']+[ff(t,v) for t,v in zip(ts,values)]+[f'/IMPDISP/{fid}',f'KNOWN_MOTION_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/PART/1','FINITE_PART', ''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(1),'/TH/NODE/1','NATIVE_CONNECTOR_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ','VRX','VRY','VRZ'])]+[ii(i,0) for i in range(1,len(xyz)+1)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    E=['/ANIM/DT',ff(0,.1),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/DT',ff(.4,0),'/DTIX',ff(.000025,.000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py')
    dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'nseg':nseg,'nodes_mm':xyz.tolist(),'beams':beam.tolist(),'physical_lumped_mass_g':mass.tolist(),'physical_nodal_centerline_inertia_g_mm2':Ip.tolist(),'physical_cross_section_inertia_g_mm2':Ic.tolist(),'continuous_cylinder_inertia_g_mm2':Icont.tolist(),'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__)),'beam_length_exceeds_sqrt_area':bool(all(np.linalg.norm(xyz[j-1]-xyz[i-1])>np.sqrt(area) for i,j in beam))})
    en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,en);s=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'exit_ok':ok,'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,s[-3000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',120,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace')
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,en);review(d,n)
    except Exception:
        dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'whole_impact_qualified':False});raise

def review(d,n):
    guard();c=read(CFG);a=c['acceptance'];g=read(d/'generation.json');cid=g['case'];H=histories(d/(n+'T01.csv'));T=H['time'];keys=[k for k in H if k.startswith('NATIVE_CONNECTOR_NODES')];xyz=np.asarray(g['nodes_mm']);mass=np.asarray(g['physical_lumped_mass_g']);assert len(keys)==9*len(xyz)
    node=np.column_stack([H[k] for k in keys]).reshape(len(T),len(xyz),9);actualX=xyz+node[:,:,:3];actualV=node[:,:,3:6];actualW=node[:,:,6:9]
    total=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;EW=H['EXTERNAL WORK']*.001;R=total-total[0]-EW;IE=H['INTERNAL ENERGY']*.001;scale=max(float(abs(total).max()),float(abs(EW).max()));Ic=np.asarray(g['physical_cross_section_inertia_g_mm2'])
    checks={'normal_termination':True,'strict_zero_warnings_errors':read(d/'starter_gate.json')['pass'],'physical_mass':bool(abs(H['MASS'][0]-mass.sum())<a['mass_relative']*mass.sum()),'constant_mass':bool(np.max(abs(H['MASS']-mass.sum()))<a['mass_relative']*mass.sum()),'no_added_or_scaled_mass':bool(abs(H['ADDED MASS']).max()<a['mass_scaling_relative']*mass.sum()),'nonnegative_IE':bool(IE.min()>-a['absolute_energy_J']),'native_energy_balance':bool(abs(R).max()<a['energy_balance_fraction']*scale+a['absolute_energy_J']),'beam_mesh_recommendation':g['beam_length_exceeds_sqrt_area']}
    expected=None;motion_error=None;velocity_error=None;physical_initial_KE=None;axial_ref=None
    if not cid.startswith('FREE_'):
        X,V,A,W=prescribed(xyz,cid,T,c);expected=.5*np.sum(mass[None,:,None]*V**2,axis=(1,2))*.001
        if cid.startswith('ROTATION_'):
            ax='XYZ'.index(cid[-1]);expected+=.5*Ic[ax,ax]*(np.pi/2*(6*T-6*T*T))**2*.001
        motion_error=float(abs(actualX-X).max());velocity_error=float(abs(actualV-V).max());checks['prescribed_positions']=motion_error<a['motion_mm'];checks['prescribed_velocity']=velocity_error<a['velocity_m_s'];checks['prescribed_angular_velocity']=bool(abs(actualW-W).max()<.005)
        if cid=='AXIAL':
            axial_ref=.5*73100*(np.pi*.5**2/4)*20*.001**2*.001;checks['analytic_axial_IE']=bool(abs(IE[-1]-axial_ref)<a['analytic_axial_IE_fraction']*axial_ref+a['absolute_energy_J'])
        else:
            checks['rigid_motion_IE']=bool(abs(IE).max()<a['rigid_IE_J']);kinetic=(H['KINETIC ENERGY']+H['ROTATION ENERGY'])*.001;checks['independent_physical_KE']=bool(abs(kinetic-expected).max()<a['physical_KE_fraction']*float(expected.max())+a['absolute_energy_J'])
    else:
        omega=np.eye(3)['XYZ'.index(cid[-1])]*.1 if cid.startswith('FREE_ROTATION_') else np.zeros(3)
        V=np.cross(omega,xyz) if cid.startswith('FREE_ROTATION_') else np.broadcast_to([10.,5,2],xyz.shape)
        physical_initial_KE=float((.5*np.sum(mass[:,None]*V**2)+.5*omega@Ic@omega)*.001)
        checks['independent_initial_KE']=bool(abs(total[0]-physical_initial_KE)<a['physical_KE_fraction']*physical_initial_KE+a['absolute_energy_J']);checks['free_no_external_work']=bool(abs(EW).max()<a['absolute_energy_J']);checks['free_energy_conserved']=bool(abs(total-total[0]).max()<a['free_energy_fraction']*max(physical_initial_KE,float(total[0]))+a['absolute_energy_J'])
        P=np.sum(mass[None,:,None]*actualV,axis=1)*.001;P0=np.sum(mass[:,None]*V,axis=0)*.001;checks['free_linear_momentum']=bool(np.max(np.linalg.norm(P-P0,axis=1))<a['free_momentum_fraction']*max(float(np.linalg.norm(P0)),mass.sum()*.1*.001)+1e-9)
        if cid=='FREE_TRANSLATION':checks['free_rigid_translation']=bool(abs(actualX-(xyz+T[:,None,None]*V)).max()<a['motion_mm']);checks['free_zero_IE']=bool(abs(IE).max()<a['rigid_IE_J'])
    r={'created_utc':now(),'case':cid,'nseg':g['nseg'],'history_rows':len(T),'last_ms':float(T[-1]),'expected_mass_g':float(mass.sum()),'native_mass_g':float(H['MASS'][0]),'maximum_residual_J':float(abs(R).max()),'peak_native_KE_J':float(((H['KINETIC ENERGY']+H['ROTATION ENERGY'])*.001).max()),'peak_expected_prescribed_KE_J':float(expected.max()) if expected is not None else None,'physical_initial_KE_J':physical_initial_KE,'native_initial_total_J':float(total[0]),'last_IE_J':float(IE[-1]),'maximum_abs_IE_J':float(abs(IE).max()),'analytic_axial_IE_J':axial_ref,'maximum_motion_error_mm':motion_error,'maximum_velocity_error_m_s':velocity_error,'native_node_channels_selected_by_group_title':True,'checks':{k:bool(v) for k,v in checks.items()},'pass':bool(all(checks.values())),'whole_root_cause_proven':False,'physical_fastener_qualified':False,'whole_impact_qualified':False}
    np.savez_compressed(d/'review_histories_SI.npz',time_ms=T,total_J=total,EW_J=EW,IE_J=IE,residual_J=R,positions_mm=actualX,velocities_m_s=actualV,angular_velocity_rad_ms=actualW);dump(d/'review.json',r);print({'case':cid,'nseg':g['nseg'],'pass':r['pass'],'failed':[k for k,v in checks.items() if not v],'max_residual_J':r['maximum_residual_J']},flush=True)

def run():
    guard();rows=[]
    for nseg in [4,8]:
        for cid in read(CFG)['cases']:
            d=OUT/'w0'/f'{cid}_N{nseg}'
            if not d.exists():run_one(nseg,cid)
            else:assert (d/'review.json').exists(),'Preserve incomplete case; diagnose instead of rerunning'
            rows.append(read(d/'review.json'))
    dump(OUT/'connector_review.json',{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'finite_connector_qualified_for_whole':all(r['pass'] for r in rows),'strength_or_fracture_qualified':False,'whole_impact_qualified':False,'objective1_complete':False,'old_solver_reruns':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
