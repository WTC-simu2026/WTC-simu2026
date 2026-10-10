"""Real shell/core/root hierarchy witness; undeforming body/skin/core under matched rigid motion."""
from run_aircraft_a21 import *
from run_aircraft_a18 import blocks
NC=OUT/'nested_root_declaration.json'
PANEL=PREV/'p3/ROTATION/A20_PANEL_ROTATION_0000.rad'

def declare():
    guard();assert not NC.exists();c={'declared_utc':now(),'iteration':'AIRCRAFT-A21','revision':'w6','before_any_w6_solver':True,
        'cases':['REFERENCE_X','REFERENCE_Y','REFERENCE_Z','RBE2_Y','TYPE2_X','TYPE2_Y','TYPE2_Z','TYPE2_Y_HALF'],
        'purpose':'Actual rotational DOFs on two0.5mm skins and finite8mm core, inherited A20 p3 constitutive cards. Avoid conclusions from point-mass-only TYPE2. One10x10x2.54mm fuselage backing extendsx=-10..0; skin/core panelx=0..10. Root corner midsurfaces atx=0 andz+/-4.25 project exactly to backing edge. This is a local implementation witness, not changed whole geometry.',
        'source_panel_sha256':streamsha(PANEL),'whole_material_sha256':streamsha(SOURCE/'A20_CORE3D_TIED_20_0000.rad'),
        'TYPE2_hierarchy':{'core_to_skins':'Spot2 Level0 Iproj2 dsearch0.3mm offset0.25mm','skin_roots_to_body':'Spot2 Level1 Iproj2 dsearch5mm offset4.25mm; all four roots must tie','core_ties':2,'root_ties':1},
        'reference':'Identical body/skins/core and masses; all skin nodes independently follow same rigid rotation; core attached identically viaTYPE2 Spot2 Level0.',
        'RBE2_control':'Two body root nodes, each paired with lower/upper skin corner. Original ideal111111 Iflag0. No mass compensation.',
        'mass_g':.2214+100*2.54*.00278,'execution':{'end_ms':1,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'history_ms':.001,'animation_ms':.025,'CPU_threads':1,'engine_cap_s':120},
        'acceptance':{'zero_errors_warnings':True,'mass_relative':1e-6,'added_mass_fraction':1e-9,'rigid_IE_J':.0001,'energy_balance_fraction':.02,'matched_energy_fraction':.02,'absolute_J':.0001,'motion_mm':.002,'velocity_m_s':.005},
        'source_reference':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm','old_control_failures_retained':True,'whole_geometry_changed':False,'root_strength_or_failure_qualified':False,'whole_cause_proven':False}
    dump(NC,c);dump(OUT/'nested_root_guard.json',{'sha256':streamsha(NC)});print({'declared':'w6 physical sandwich/body hierarchy','cases':len(c['cases'])},flush=True)

def nguard():guard();assert streamsha(NC)==read(OUT/'nested_root_guard.json')['sha256'];assert streamsha(PANEL)==read(NC)['source_panel_sha256']

def one(cid,revision='w6'):
    nguard();kind,axis,*rest=cid.split('_');ax='XYZ'.index(axis);d=OUT/revision/cid;n='A21_NESTED_'+cid;assert not d.exists();d.mkdir(parents=True)
    xyz=np.array([[0,0,-4.25],[10,0,-4.25],[10,10,-4.25],[0,10,-4.25],[0,0,4.25],[10,0,4.25],[10,10,4.25],[0,10,4.25],[0,0,-4],[10,0,-4],[10,10,-4],[0,10,-4],[0,0,4],[10,0,4],[10,10,4],[0,10,4],[-10,0,0],[0,0,0],[0,10,0],[-10,10,0]],float)
    L=[]
    for old in blocks(PANEL.read_text().splitlines()):
        if old[0]=='/END' or old[0].startswith(('/IMPDISP/','/TH/')):continue
        if old[0].startswith('/FUNCT/') and (revision=='w6' or int(old[0].rsplit('/',1)[1])>=1000):continue
        if old[0].startswith('/GRNOD/NODE/') and int(old[0].rsplit('/',1)[1])<200:continue
        b=old.copy()
        if b[0] in ['/BEGIN','/TITLE']:b[1]=n
        elif b[0]=='/NODE':b=[b[0]]+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
        elif b[0].startswith('/INTER/TYPE2/'):
            # Keep the original0.25mm core/skin geometry, use hierarchy-compatible formulation.
            row=b[2];b[2]=row[:30]+ii(2,0)+row[50:]
        L+=b
    whole={b[0]:b for b in blocks((SOURCE/'A20_CORE3D_TIED_20_0000.rad').read_text().splitlines())};L+=whole['/MAT/LAW2/1']+whole['/PROP/TYPE1/1']+['/PART/1','KNOWN_BODY_BACKING',ii(1,1,0),'/SHELL/1',ii(4,17,18,19,20)]
    roots=[1,4,5,8]
    if kind=='TYPE2':
        L+=['/GRNOD/NODE/301','SKIN_ROOT_SECONDARIES',ii(*roots),'/SURF/PART/301','BODY_BACKING_MAIN',ii(1),'/INTER/TYPE2/301','NESTED_SKIN_ROOT_TO_BODY',ii(301,301,1000,2,1,2,1000,0)+ff(5),ii(0)+ff(0)+' '*60+ii(2)]
    elif kind=='RBE2':
        for host,deps,gid in [(18,[1,5],301),(19,[4,8],302)]:L+=[f'/GRNOD/NODE/{gid}','SKIN_ROOTS_FROM_BODY',ii(*deps),f'/RBE2/{gid}','IDEAL_ROOT_WITH_ACTUAL_SKIN_INERTIA',ii(host)+'   111 111'+ii(0,gid,0)]
    forced=list(range(1,9)) if kind=='REFERENCE' else [i for i in range(1,9) if i not in roots];forced+=list(range(17,21));T=np.linspace(0,1,10001);theta=np.pi/2*(3*T*T-2*T**3);axisv=np.eye(3)[ax];rot=xyz[None,:,:]*np.cos(theta)[:,None,None]+np.cross(axisv,xyz)[None,:,:]*np.sin(theta)[:,None,None]+axisv[None,None,:]*np.dot(xyz,axisv)[None,:,None]*(1-np.cos(theta)[:,None,None]);U=rot-xyz;fid=1000
    for ni in forced:
        L+=[f'/GRNOD/NODE/{ni}',f'NODE_{ni}',ii(ni)]
        for j,direction in enumerate(['X','Y','Z','XX','YY','ZZ']):
            fid+=1;vals=U[:,ni-1,j] if j<3 else theta if j-3==ax else np.zeros(len(T));L+=[f'/FUNCT/{fid}',f'RIGID_{ni}_{direction}']+[ff(t,v) for t,v in zip(T,vals)]+[f'/IMPDISP/{fid}',f'RIGID_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/NODE/1','NATIVE_ALL_NODES',''.join(f'{q:>10}' for q in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(i,0) for i in range(1,21)]+['/TH/PART/1','NATIVE_ALL_PARTS','        IE        KE        HE        PW',ii(1,28,122,123),'/END'];(d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    dt=.0000125 if rest else .000025;E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/ANIM/ELEM/ENER','/DT',ff(.4,0),'/DTIX',ff(dt,dt),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'config_sha256':streamsha(NC),'nodes_mm':xyz.tolist(),'dt_cap_ms':dt})
    en=env();en['OMP_NUM_THREADS']='1';en['RAD_HMPP_DOMAINS']='1'
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',120,en);s=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,s[-3000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',120,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',120,en);review(d,n,cid,revision)
    except Exception:
        dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc()});raise

def review(d,n,cid,revision='w6'):
    c=read(NC);a=c['acceptance'];H=histories(d/(n+'T01.csv'));T=H['time'];V=np.column_stack(list(H.values()))[:,23:143].reshape(len(T),20,6);kind,axis,*rest=cid.split('_');ax='XYZ'.index(axis);q=np.asarray(read(d/'generation.json')['nodes_mm']);theta=np.pi/2*(3*T*T-2*T**3);av=np.eye(3)[ax];X=q[None,:,:]*np.cos(theta)[:,None,None]+np.cross(av,q)[None,:,:]*np.sin(theta)[:,None,None]+av[None,None,:]*np.dot(q,av)[None,:,None]*(1-np.cos(theta)[:,None,None]);velocity=np.cross(av,X)*(np.pi/2*(6*T-6*T*T))[:,None,None];pos=float(abs(q+V[:,:,:3]-X).max());vel=float(abs(V[:,:,3:]-velocity).max());tot=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;EW=H['EXTERNAL WORK']*.001;R=tot-tot[0]-EW;scale=max(float(abs(tot).max()),float(abs(EW).max()))
    checks={'zero_errors_warnings':True,'known_physical_mass':bool(abs(H['MASS'][0]-c['mass_g'])<a['mass_relative']*c['mass_g']),'no_scaled_or_added_mass':bool(abs(H['ADDED MASS']).max()/c['mass_g']<a['added_mass_fraction']),'rigid_IE':bool(abs(H['INTERNAL ENERGY']).max()*.001<a['rigid_IE_J']),'native_energy_balance':bool(abs(R).max()<a['energy_balance_fraction']*scale+a['absolute_J']),'all_node_positions':pos<a['motion_mm'],'all_node_velocities':vel<a['velocity_m_s']};err=None
    if kind!='REFERENCE':
        ref=np.load(OUT/f'{revision}/REFERENCE_{axis}/energy_history_SI.npz');e=np.interp(T,ref['time_ms'],ref['native_total_J']);err=float(abs(tot-e).max());checks['matched_reference_energy']=err<a['matched_energy_fraction']*float(e.max())+a['absolute_J']
    r={'created_utc':now(),'case':cid,'peak_total_energy_J':float(tot.max()),'maximum_native_residual_J':float(abs(R).max()),'maximum_matched_energy_error_J':err,'maximum_position_error_mm':pos,'maximum_velocity_error_m_s':vel,'maximum_IE_J':float(abs(H['INTERNAL ENERGY']).max()*.001),'maximum_added_mass_g':float(abs(H['ADDED MASS']).max()),'checks':{k:bool(v) for k,v in checks.items()},'pass':all(checks.values()),'whole_cause_proven':False,'root_strength_qualified':False};np.savez_compressed(d/'energy_history_SI.npz',time_ms=T,native_total_J=tot,residual_J=R,external_work_J=EW);dump(d/'review.json',r);print(r,flush=True)

def run():
    nguard()
    for cid in read(NC)['cases']:one(cid)
    rows=[read(OUT/'w6'/cid/'review.json') for cid in read(NC)['cases']];dump(OUT/'nested_root_review.json',{'created_utc':now(),'cases':rows,'references_pass':all(r['pass'] for r in rows if r['case'].startswith('REFERENCE')),'RBE2_pass':all(r['pass'] for r in rows if r['case'].startswith('RBE2')),'TYPE2_pass':all(r['pass'] for r in rows if r['case'].startswith('TYPE2')),'all_pass':all(r['pass'] for r in rows),'whole_Engine_allowed':False,'whole_edge_projections_not_yet_qualified':True,'root_strength_qualified':False})

def w7():
    nguard();p=OUT/'nested_root_w7_declaration.json';assert not p.exists();dump(p,{'declared_utc':now(),'before_any_w7_native_solver':True,'source_declaration_sha256':streamsha(NC),'w6_input_failure_preserved':True,'correction':'The prescribed-motion removal also removed the6LAW28yield functions280..285. Keep all inherited material functions; replace only motion functions>=1000. Mechanical witness declaration and unchanged thresholds retained; no Engine was run on w6.','revision':'w7','source_expected_yield_functions':[280,281,282,283,284,285]})
    for cid in read(NC)['cases']:one(cid,'w7')
    rows=[read(OUT/'w7'/cid/'review.json') for cid in read(NC)['cases']];dump(OUT/'nested_root_w7_review.json',{'created_utc':now(),'cases':rows,'references_pass':all(r['pass'] for r in rows if r['case'].startswith('REFERENCE')),'RBE2_pass':all(r['pass'] for r in rows if r['case'].startswith('RBE2')),'TYPE2_pass':all(r['pass'] for r in rows if r['case'].startswith('TYPE2')),'all_pass':all(r['pass'] for r in rows),'whole_Engine_allowed':False,'whole_edge_projections_not_yet_qualified':True,'root_strength_qualified':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run','w7']);globals()[p.parse_args().action]()
