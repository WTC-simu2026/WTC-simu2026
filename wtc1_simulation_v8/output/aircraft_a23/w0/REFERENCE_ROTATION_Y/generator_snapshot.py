"""Translational solid connector, independent mass tensor and paired skin coupling controls."""
from run_aircraft_a20 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,material,solid_property,skew_card
from test_aircraft_a20_sandwich import face_property
from test_aircraft_a19_triangles import histories
from run_aircraft_a18 import blocks
from audit_aircraft_a05 import vtk
import argparse,json,shutil,re,traceback,urllib.request,time
from pathlib import Path
import numpy as np

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a23'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a23_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a22'
SOURCE=ROOT/'wtc1_simulation_v8/output/aircraft_a20/r0/CORE3D_TIED_20'

def parent():
    return {b[0]:b for b in blocks((SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.rad')).read_text().splitlines())}

def brick_grid(shape,lo,hi,first=1):
    nx,ny,nz=shape;axes=[np.linspace(a,b,n+1) for a,b,n in zip(lo,hi,shape)];xyz=[];ids={}
    for k,z in enumerate(axes[2]):
        for j,y in enumerate(axes[1]):
            for i,x in enumerate(axes[0]):ids[i,j,k]=first+len(xyz);xyz.append([x,y,z])
    bricks=[];mass=np.zeros(len(xyz));volume=float(np.prod(np.asarray(hi)-lo));ev=volume/(nx*ny*nz)
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                nodes=[ids[i,j,k],ids[i+1,j,k],ids[i+1,j+1,k],ids[i,j+1,k],ids[i,j,k+1],ids[i+1,j,k+1],ids[i+1,j+1,k+1],ids[i,j+1,k+1]];bricks.append(nodes);mass[np.asarray(nodes)-first]+=.00278*ev/8
    left=[v for (i,j,k),v in ids.items() if i==0];right=[v for (i,j,k),v in ids.items() if i==nx]
    return np.asarray(xyz),bricks,mass,left,right

def inertia(xyz,mass):return sum(m*(np.dot(x,x)*np.eye(3)-np.outer(x,x)) for x,m in zip(xyz,mass))

def prop(pid=1):
    # Current TYPE14 format: Isolid,Ismstr,Iale,Icpre,Itetra10,Inpts,Itetra4,Iframe,dn.
    return [f'/PROP/TYPE14/{pid}','FINITE_FULL_INTEGRATION_METAL_WITHOUT_ROTATIONAL_DOF',ii(14,4,0,2,0,222,0,2)+ff(0),ff(0,0,0,0,0),ff(0,0,0,0,0),ii(0,0,0)]

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['Status']=='PASS' and h['CurrentIteration']=='AIRCRAFT-A22';OUT.mkdir();dump(OUT/'harness_before.json',h)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c={'iteration':'AIRCRAFT-A23','declared_utc':now(),'seed':1102048,'random_draws':0,
       'purpose':'Finite3D connector with translational mass/inertia, independent continuum and lumped tensor; paired reference/connector motion on real shell+Spot5 sandwich before whole insertion. No scalar beam inertia or ideal root constraint.',
       'solid':{'dimensions_mm':[4,1,.5],'material':'inherited LAW2/1: rho.00278g/mm3 E73100MPa nu.33 yield324MPa hardening0 fracture absent','property':'TYPE14 HA8 Isolid14 Ismstr4 Icpre2 Gauss222 Iframe2','rigid_control_shape':[4,2,2],'elastic_shapes':[[4,2,2],[8,4,4]],'free_tensor_shape':[12,12,12],'mass_g':.00556,'axial_yield_N':162,'as_built_identified':False},
       'fixture':{'body_plate_mm':[[-10,0,-4.25],[0,0,-4.25],[0,10,-4.25],[-10,10,-4.25]],'body_skin_thickness_mm':.5,'body_skin_material':'inherited LAW2/1','sandwich':'reuse A20p3 actual skins at z+-4.25, core+-4, skin.5mm and Spot5 Iproj2','clip_bounds_mm':[[-2,4.5,-5],[2,5.5,-4.5]],'clip_surface':'touches outer lower skin at z-4.5, no overlap with sandwich core','end_ties':'only new solid end nodes secondary; body/lower_skin shells main, Spot5 Iproj2 dsearch.8mm. Opposite end node sets disjoint. Existing core nodes never used as root main.','unknown_capacity_and_geometry':True},
       'mass_budget':{'one_clip_g':.00556,'whole_added_mass_not_assumed_until_actual_mapping_exists':True,'no_ADMAS_density_or_inertia_compensation':True,'whole_aircraft_unchanged_by_controls':True},
       'cases':{'primitive':['ROTATION_X','ROTATION_Y','ROTATION_Z','AXIAL_N4','AXIAL_N8','FREE_ROTATION_X','FREE_ROTATION_Y','FREE_ROTATION_Z'],'paired':['REFERENCE_ROTATION_X','CONNECTED_ROTATION_X','REFERENCE_ROTATION_Y','CONNECTED_ROTATION_Y','REFERENCE_ROTATION_Z','CONNECTED_ROTATION_Z','REFERENCE_EXTENSION','CONNECTED_EXTENSION_N4','CONNECTED_EXTENSION_N8']},
       'motion':{'prescribed_duration_ms':1,'s':'3*t^2-2*t^3','angle_rad':float(np.pi/2),'affine_axial_strain':.001,'free_duration_ms':.05,'free_omega_rad_ms':10,'connected_extension_mm':.004},
       'execution':{'CPU_threads':1,'GPU':False,'dt_cap_ms':.000025,'history_dt_ms':.001,'animation_dt_ms':.025,'per_process_cap_s':180,'estimated_minutes':[5,15],'no_mass_scaling':True},
       'acceptance':{'mass_relative':1e-6,'added_mass_relative':1e-9,'energy_fraction':.02,'absolute_energy_J':1e-7,'rigid_IE_J':1e-7,'known_lumped_KE_fraction':.002,'free_continuum_KE_fraction':.02,'physical_tensor_fraction':.02,'position_mm':.002,'velocity_m_s':.005,'elastic_IE_fraction':.02,'paired_added_KE_fraction':.02,'free_energy_fraction':.002,'elastic_mesh_fraction':.05},
       'references':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type14_solid_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/mat_law2_plas_johns_starter_r.htm'],
       'reuse_existing_A20_passed_core_and_Spot5':True,'no_old_solver_reruns':True,'no_historical_damage_target':True,'whole_insertion_requires_all_scope_controls':True,'whole_impact_qualified':False,'physical_connector_strength_or_fracture_qualified':False,'objective1_complete':False}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_new_native_solver':True});s=OUT/'sources';s.mkdir();sources=[]
    for j,u in enumerate(c['references']):
        p=s/f'primary_{j}.html';p.write_bytes(urllib.request.urlopen(u,timeout=40).read());sources.append({'url':u,'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    for p in [CFG,PREV/'native_inertia_audit.json',PREV/'material_preparation.json',SOURCE/'mesh.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/core_verified_review.json',ROOT/'wtc1_simulation_v8/output/aircraft_a20/sandwich_type2_review.json']:sources.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':sources,'archive_rescanned':False});print({'declared':'AIRCRAFT-A23','native_cases':17,'clip_mass_g':.00556},flush=True)

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def group(gid,title,ids):return [f'/GRNOD/NODE/{gid}',title]+[ii(*ids[j:j+10]) for j in range(0,len(ids),10)]

def rotation(xyz,T,axis):
    u=np.eye(3)['XYZ'.index(axis)];angle=np.pi/2*(3*T*T-2*T**3);w=np.pi/2*(6*T-6*T*T)
    X=xyz[None,:,:]*np.cos(angle)[:,None,None]+np.cross(u,xyz)[None,:,:]*np.sin(angle)[:,None,None]+u[None,None,:]*np.dot(xyz,u)[None,:,None]*(1-np.cos(angle)[:,None,None]);V=np.cross(u,X)*w[:,None,None]
    return X,V,angle,w

def imposed(L,xyz,node_ids,cid,start=10000,rotational_DOF=True):
    T=np.linspace(0,1,10001);D=np.zeros((len(T),len(xyz),3));A=np.zeros_like(D);s=3*T*T-2*T**3
    if 'ROTATION_' in cid:
        X,V,a,w=rotation(xyz,T,cid[-1]);D=X-xyz;A[:,:,'XYZ'.index(cid[-1])]=a[:,None]
    elif cid.startswith('AXIAL'):
        D[:,:,0]=.001*s[:,None]*xyz[None,:,0];D[:,:,1:]=-.33*.001*s[:,None,None]*xyz[None,:,1:]
    elif 'EXTENSION' in cid:
        D[:,:,0]=.004*s[:,None]*(xyz[None,:,0]>=0)
    for j,ni in enumerate(node_ids):
        L+=group(ni,f'KNOWN_NODE_{ni}',[int(ni)])
        for ax,direction in enumerate(['X','Y','Z','XX','YY','ZZ'] if rotational_DOF else ['X','Y','Z']):
            start+=1;val=D[:,j,ax] if ax<3 else A[:,j,ax-3]
            L+=[f'/FUNCT/{start}',f'KNOWN_{ni}_{direction}']+[ff(t,v) for t,v in zip(T,val)]+[f'/IMPDISP/{start}',f'KNOWN_{ni}_{direction}',ii(start)+f'{direction:>10}'+ii(0,0,int(ni))+' '*10+ii(0),ff(1,1,0,1e30)]
    return L

def run_one(cid):
    guard();c=read(CFG);primitive=cid in c['cases']['primitive'];free=cid.startswith('FREE_');connected=cid.startswith('CONNECTED_');d=OUT/'w0'/cid;n='A23_'+cid;assert not d.exists();d.mkdir(parents=True);P=parent();duration=.05 if free else 1
    if primitive:
        shape=[12,12,12] if free else [8,4,4] if cid=='AXIAL_N8' else [4,2,2]
        xyz,brick,mass,left,right=brick_grid(shape,[-2,-.5,-.25],[2,.5,.25]);clip_ids=np.arange(1,len(xyz)+1);main_ids=clip_ids.tolist();main_xyz=xyz;materials=P['/MAT/LAW2/1']+prop()+['/PART/1','FINITE_TRANSLATIONAL_METAL',ii(1,1,0),'/BRICK/1']+[ii(j+1,*conn) for j,conn in enumerate(brick)];known_mass=mass.copy()
    else:
        skin=np.array([[0,0,-4.25],[10,0,-4.25],[10,10,-4.25],[0,10,-4.25],[0,0,4.25],[10,0,4.25],[10,10,4.25],[0,10,4.25]],float);core=skin.copy();core[:4,2]=-4;core[4:,2]=4;body=np.array(c['fixture']['body_plate_mm']);xyz=np.vstack([skin,core,body]);main_ids=list(range(1,9))+list(range(17,21));main_xyz=xyz[np.asarray(main_ids)-1];clip_ids=np.array([],int);mass=np.zeros(0);brick=[];shape=[8,4,4] if cid.endswith('_N8') else [4,2,2]
        bp=P['/PROP/TYPE1/1'].copy();bp[1]='DECLARED_HALF_MM_METAL_BACKING';bp[4]=ii(5)+' '*10+ff(.5,.833333333333)
        materials=material()+skew_card(28)+solid_property()
        for key in ['/MAT/LAW2/1','/MAT/LAW25/4','/PROP/TYPE19/41','/PROP/TYPE19/43','/FAIL/ORTHSTRAIN/4']:materials+=P[key]
        materials+=bp+face_property(122,41,True,True)+face_property(123,43,False,True)+['/PART/28','VERIFIED_CORE',ii(28,28,0),'/BRICK/28',ii(1,9,10,11,12,13,14,15,16),'/PART/122','LOWER_SKIN',ii(122,4,0),'/SHELL/122',ii(2,1,2,3,4),'/PART/123','UPPER_SKIN',ii(123,4,0),'/SHELL/123',ii(3,5,6,7,8),'/PART/1','HALF_MM_BACKING',ii(1,1,0),'/SHELL/1',ii(4,17,18,19,20)]
        for sid,part,ids in [(201,122,[9,10,11,12]),(202,123,[13,14,15,16])]:
            materials+=group(sid,'CORE_FACE_SECONDARY',ids)+[f'/SURF/PART/{sid}','SKIN_MIDPLANE_MAIN',ii(part),f'/INTER/TYPE2/{sid}','UNCHANGED_SPOT5_CORE_SKIN',ii(sid,sid,1000,5,0,2,1000,0)+ff(.3),ii(0)+ff(0)+' '*60+ii(2)]
        if connected:
            clip,brick,mass,left,right=brick_grid(shape,*c['fixture']['clip_bounds_mm'],first=21);clip_ids=np.arange(21,21+len(clip));xyz=np.vstack([xyz,clip]);materials+=prop(501)+['/PART/501','FINITE_METAL_CLIP',ii(501,1,0),'/BRICK/501']+[ii(501+j,*conn) for j,conn in enumerate(brick)]
            for sid,part,ids in [(301,1,left),(302,122,right)]:
                materials+=group(sid,'ONLY_NEW_SOLID_END_NODES',ids)+[f'/SURF/PART/{sid}','BODY_OR_SKIN_MAIN',ii(part),f'/INTER/TYPE2/{sid}','FINITE_CLIP_END_SPOT5',ii(sid,sid,1000,5,0,2,1000,0)+ff(.8),ii(0)+ff(0)+' '*60+ii(2)]
        known_mass=np.array([])
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]+materials
    if free:
        omega=np.eye(3)['XYZ'.index(cid[-1])]*10;V=np.cross(omega,xyz)
        for ni,v in enumerate(V,1):L+=group(ni,f'INITIAL_NODE_{ni}',[ni])+[f'/INIVEL/TRA/{ni}',f'INITIAL_PHYSICAL_ROTATION_{ni}',ff(*v)+ii(ni,0),ff(0)+ii(0)]
    else:L=imposed(L,main_xyz,main_ids,cid,rotational_DOF=not primitive)
    parts=[1] if primitive else [1,28,122,123]+([501] if connected else [])
    L+=['/TH/PART/1','SCOPE_PARTS',''.join(f'{v:>10}' for v in ['IE','KE','HE','PW']),ii(*parts),'/TH/NODE/1','NATIVE_SCOPE_NODES',''.join(f'{v:>10}' for v in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(i,0) for i in range(1,len(xyz)+1)]+['/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8');E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/BRICK/TENS/STRESS','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(.000025,.000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(duration),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py')
    box=xyz if primitive else xyz[clip_ids-1];center=np.array([0,0,0]) if primitive else np.array([0,5,-4.75]);dm=np.array([4.,1,.5]);M=.00556;Icont=np.diag(M*(sum(dm**2)-dm**2)/12)+M*(center@center*np.eye(3)-np.outer(center,center))
    generation={'created_utc':now(),'case':cid,'name':n,'primitive':primitive,'connected':connected,'free':free,'duration_ms':duration,'shape':shape,'nodes_mm':xyz.tolist(),'main_node_ids':main_ids,'clip_node_ids':clip_ids.tolist(),'clip_known_nodal_masses_g':mass.tolist(),'clip_lumped_inertia_g_mm2':inertia(box,mass).tolist() if len(mass) else None,'clip_continuum_inertia_g_mm2':Icont.tolist(),'bricks':brick,'configuration_sha256':streamsha(CFG),'generator_sha256':streamsha(Path(__file__)),'expected_mass_g':.00556 if primitive else .3604+(.00556 if connected else 0),'clip_only_3_translational_DOF':True}
    # Fixture reference mass: sandwich.2214g + body10*10*.5*.00278=.139g.
    dump(d/'generation.json',generation);en=env();en.update(OMP_NUM_THREADS='1',RAD_HMPP_DOMAINS='1')
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',180,en);s=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'created_utc':now(),'exit_ok':ok,'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,s[-4000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',180,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace')
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',180,en);review(d,n)
    except Exception:
        dump(d/'retained_failure.json',{'created_utc':now(),'traceback':traceback.format_exc(),'whole_impact_qualified':False});raise

def review(d,n):
    guard();g=read(d/'generation.json');c=read(CFG);a=c['acceptance'];cid=g['case'];H=histories(d/(n+'T01.csv'));T=H['time'];xyz=np.asarray(g['nodes_mm']);keys=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];assert len(keys)==6*len(xyz);node=np.column_stack([H[k] for k in keys]).reshape(len(T),len(xyz),6);X=xyz+node[:,:,:3];V=node[:,:,3:]
    total=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;IE=H['INTERNAL ENERGY']*.001;EW=H['EXTERNAL WORK']*.001;R=total-total[0]-EW;scale=max(float(abs(total).max()),float(abs(EW).max()));mass=np.asarray(g['clip_known_nodal_masses_g'])
    checks={'normal_termination':True,'strict_zero_warnings_errors':read(d/'starter_gate.json')['pass'],'physical_mass':bool(abs(H['MASS'][0]-g['expected_mass_g'])<a['mass_relative']*g['expected_mass_g']),'constant_mass':bool(abs(H['MASS']-H['MASS'][0]).max()<a['mass_relative']*g['expected_mass_g']),'no_added_or_scaled_mass':bool(abs(H['ADDED MASS']).max()<a['added_mass_relative']*g['expected_mass_g']),'nonnegative_IE':bool(IE.min()>-a['absolute_energy_J']),'native_energy_balance':bool(abs(R).max()<a['energy_fraction']*scale+a['absolute_energy_J'])};expected=None;analytic=None;continuum_err=None;position_err=None;velocity_err=None
    if g['primitive']:
        if g['free']:
            axis='XYZ'.index(cid[-1]);w=np.eye(3)[axis]*10;v0=np.cross(w,xyz);expected=float(.5*np.sum(mass[:,None]*v0**2)*.001);physical=float(.5*np.asarray(g['clip_continuum_inertia_g_mm2'])[axis,axis]*100*.001);continuum_err=abs(expected-physical)/physical
            checks['known_lumped_initial_KE']=bool(abs(total[0]-expected)<a['known_lumped_KE_fraction']*expected+a['absolute_energy_J']);checks['physical_continuum_initial_KE']=bool(abs(total[0]-physical)<a['free_continuum_KE_fraction']*physical+a['absolute_energy_J']);checks['mesh_physical_tensor']=bool(continuum_err<a['physical_tensor_fraction']);checks['no_native_RKE']=bool(abs(H['ROTATION ENERGY']).max()*.001<a['absolute_energy_J']);checks['free_no_external_work']=bool(abs(EW).max()<a['absolute_energy_J']);checks['free_energy_conserved']=bool(abs(total-total[0]).max()<a['free_energy_fraction']*total[0]+a['absolute_energy_J'])
            P=np.sum(mass[None,:,None]*V,axis=1)*.001;L=np.sum(mass[None,:,None]*np.cross(X,V),axis=1)*.001;L0=np.sum(mass[:,None]*np.cross(xyz,v0),axis=0)*.001;checks['free_linear_momentum']=bool(abs(P).max()<1e-9);checks['free_angular_momentum']=bool(np.linalg.norm(L-L0,axis=1).max()<.002*np.linalg.norm(L0)+1e-9)
        elif cid.startswith('ROTATION_'):
            ex,ev,ang,w=rotation(xyz,T,cid[-1]);expected=.5*np.sum(mass[None,:,None]*ev**2,axis=(1,2))*.001;position_err=float(abs(X-ex).max());velocity_err=float(abs(V-ev).max());checks['known_discrete_KE']=bool(abs((H['KINETIC ENERGY']+H['ROTATION ENERGY'])*.001-expected).max()<a['known_lumped_KE_fraction']*float(expected.max())+a['absolute_energy_J']);checks['positions']=position_err<a['position_mm'];checks['velocity']=velocity_err<a['velocity_m_s'];checks['rigid_IE']=bool(abs(IE).max()<a['rigid_IE_J']);checks['no_native_RKE']=bool(abs(H['ROTATION ENERGY']).max()*.001<a['absolute_energy_J'])
        else:
            analytic=.5*73100*.001**2*2*.001;checks['analytic_uniaxial_IE']=bool(abs(IE[-1]-analytic)<a['elastic_IE_fraction']*analytic+a['absolute_energy_J'])
    else:
        if 'ROTATION_' in cid:
            ex,ev,ang,w=rotation(xyz,T,cid[-1]);position_err=float(abs(X-ex).max());velocity_err=float(abs(V-ev).max());checks['all_node_positions']=position_err<a['position_mm'];checks['all_node_velocity']=velocity_err<a['velocity_m_s'];checks['rigid_IE']=bool(abs(IE).max()<a['rigid_IE_J'])
        if g['connected'] and 'EXTENSION' in cid:
            from linear_hexa_reference_aircraft_a23 import solve
            q=xyz[np.asarray(g['clip_node_ids'])-1];b=[[v-20 for v in row] for row in g['bricks']];left=[i+1 for i,x in enumerate(q) if abs(x[0]+2)<1e-12];right=[i+1 for i,x in enumerate(q) if abs(x[0]-2)<1e-12];ref=solve(q,b,left,right);dump(d/'independent_elastic_reference.json',ref);analytic=ref['energy_J'];checks['independent_static_IE']=bool(abs(IE[-1]-analytic)<a['elastic_IE_fraction']*analytic+a['absolute_energy_J'])
    np.savez_compressed(d/'histories_SI.npz',time_ms=T,total_J=total,IE_J=IE,EW_J=EW,residual_J=R,KE_J=(H['KINETIC ENERGY']+H['ROTATION ENERGY'])*.001,positions_mm=X,velocities_m_s=V)
    review={'created_utc':now(),'case':cid,'rows':len(T),'last_ms':float(T[-1]),'native_mass_g':float(H['MASS'][0]),'expected_mass_g':g['expected_mass_g'],'maximum_residual_J':float(abs(R).max()),'maximum_IE_J':float(IE.max()),'last_IE_J':float(IE[-1]),'native_initial_total_J':float(total[0]),'analytic_IE_J':analytic,'continuum_mass_tensor_relative_error':continuum_err,'maximum_position_error_mm':position_err,'maximum_velocity_error_m_s':velocity_err,'checks':{k:bool(v) for k,v in checks.items()},'pass':bool(all(checks.values())),'physical_strength_or_fracture_qualified':False,'whole_impact_qualified':False};dump(d/'review.json',review);print({'case':cid,'pass':review['pass'],'failed':[k for k,v in checks.items() if not v],'max_residual_J':review['maximum_residual_J']},flush=True)

def pair_review():
    guard();rows=[];a=read(CFG)['acceptance']
    for axis in 'XYZ':
        rd=OUT/'w0'/f'REFERENCE_ROTATION_{axis}';cd=OUT/'w0'/f'CONNECTED_ROTATION_{axis}';ref=np.load(rd/'histories_SI.npz');con=np.load(cd/'histories_SI.npz');g=read(cd/'generation.json');q=np.asarray(g['nodes_mm'])[np.asarray(g['clip_node_ids'])-1];m=np.asarray(g['clip_known_nodal_masses_g']);T=con['time_ms'];assert np.allclose(T,ref['time_ms'],atol=1e-9,rtol=0);X,V,angle,w=rotation(q,T,axis);expected=.5*np.sum(m[None,:,None]*V**2,axis=(1,2))*.001;actual=con['KE_J']-ref['KE_J'];difference=float(abs(actual-expected).max());tol=a['paired_added_KE_fraction']*float(expected.max())+a['absolute_energy_J'];checks={'reference_energy_balance':read(rd/'review.json')['checks']['native_energy_balance'],'connected_energy_balance':read(cd/'review.json')['checks']['native_energy_balance'],'independent_added_clip_KE':difference<tol,'expected_added_mass':abs(read(cd/'review.json')['native_mass_g']-read(rd/'review.json')['native_mass_g']-.00556)<1e-6*.00556}
        row={'axis':axis,'maximum_added_KE_error_J':difference,'expected_peak_clip_KE_J':float(expected.max()),'tolerance_J':tol,'checks':checks,'pass':all(checks.values())};rows.append(row)
    e4=read(OUT/'w0/CONNECTED_EXTENSION_N4/review.json')['last_IE_J'];e8=read(OUT/'w0/CONNECTED_EXTENSION_N8/review.json')['last_IE_J'];mesh=abs(e8-e4)/max(abs(e8),1e-20);checks={'paired_all_axes':all(r['pass'] for r in rows),'elastic_mesh_change':mesh<a['elastic_mesh_fraction']};dump(OUT/'paired_coupling_review.json',{'created_utc':now(),'pairs':rows,'elastic_mesh_relative_difference':mesh,'checks':checks,'pass':all(checks.values()),'no_native_field_or_RKE_correction':True,'strength_or_fracture_qualified':False});print({'paired_coupling':checks},flush=True)

def run():
    guard();c=read(CFG);cases=c['cases']['primitive']+c['cases']['paired'];rows=[]
    for cid in cases:
        d=OUT/'w0'/cid
        if d.exists():assert (d/'review.json').exists(),'Preserve incomplete case and diagnose; no implicit rerun'
        else:run_one(cid)
        rows.append(read(d/'review.json'))
    pair_review();dump(OUT/'campaign_review.json',{'created_utc':now(),'cases':rows,'native_cases':len(rows),'all_case_pass':all(r['pass'] for r in rows),'paired_coupling_pass':read(OUT/'paired_coupling_review.json')['pass'],'implementation_ready_for_whole':all(r['pass'] for r in rows) and read(OUT/'paired_coupling_review.json')['pass'],'whole_impact_qualified':False,'objective1_complete':False,'old_solver_reruns':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
