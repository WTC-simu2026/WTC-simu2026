"""Read all cached point histories, then compare structurally attached and independent point motion."""
from test_aircraft_a21_root import *
from run_aircraft_a18 import blocks
WC=OUT/'root_w2_declaration.json'

def kinematics(cid):
    c=read(RC);d=OUT/'w1'/cid;n='A21_ROOT_'+cid;H=histories(d/(n+'T01.csv'));T=H['time'];v=np.column_stack(list(H.values()))[:,23:].reshape(len(T),7,9)
    q=np.asarray(c['nodes_mm']);mass=np.asarray(c['point_masses_g']);ax=read(d/'generation.json')['axis'];u=3*T*T-2*T**3;ud=6*T-6*T*T
    if cid=='TRANSLATION_X':
        expected=np.broadcast_to(q,(len(T),7,3)).copy(); expected[:,:,0]+=10*u[:,None];V=np.zeros_like(expected);V[:,:,0]=10*ud[:,None]
    else:
        a=np.pi/2*u;om=np.pi/2*ud;axis=np.eye(3)[ax];cos=np.cos(a)[:,None,None];sin=np.sin(a)[:,None,None]
        expected=q[None,:,:]*cos+np.cross(axis,q)[None,:,:]*sin+axis[None,None,:]*np.dot(q,axis)[None,:,None]*(1-cos)
        V=np.cross(axis,expected)*om[:,None,None]
    X=q+v[:,:,:3];e=float(abs(X-expected).max());ve=float(abs(v[:,:,3:6]-V).max());actualKE=.5*np.sum(mass[None,:,None]*v[:,:,3:6]**2,axis=(1,2))*.001
    a=c['acceptance'];r={'case':cid,'native_TH_order':'the nine fields DX,DY,DZ,VX,VY,VZ,REACX,REACY,REACZ for each listed node, independently from the deck','maximum_position_error_mm':e,'maximum_velocity_error_m_s':ve,'native_point_kinetic_energy_peak_J':float(actualKE.max()),'checks':{'analytic_motion':e<a['analytic_motion_mm'],'analytic_velocity':ve<a['analytic_velocity_m_s']},'reaction_interpretation':'REAC is recorded unchanged; a global translation impulse cross-check is applied below.'}
    if cid=='TRANSLATION_X':
        globalP=np.column_stack([H[z+'-MOMENTUM'] for z in 'XYZ'])*.001;actualP=np.sum(mass[None,:,None]*v[:,:,3:6],axis=1)*.001;reaction=v[:,0,6:9]*.001
        pe=float(np.linalg.norm(actualP-globalP,axis=1).max());re=float(np.linalg.norm(globalP-globalP[0]-reaction+reaction[0],axis=1).max());tol=a['impulse_absolute_Ns']+a['impulse_relative']*float(np.linalg.norm(globalP-globalP[0],axis=1).max())
        r.update(independent_point_momentum_error_Ns=pe,host_cumulative_reaction_vs_global_impulse_error_Ns=re,impulse_tolerance_Ns=tol);r['checks'].update(independent_point_momentum=pe<tol,cumulative_reaction_impulse=re<tol)
    r['checks']={k:bool(x) for k,x in r['checks'].items()};r['pass']=all(r['checks'].values());return r

def cached():
    rguard();p=OUT/'root_cached_kinematics.json';assert not p.exists();rows=[kinematics(cid) for cid in read(RC)['cases']];dump(p,{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'point_motion_does_not_qualify_global_rotation_ledger':True,'no_extra_energy_added_to_whole':True});print(rows,flush=True)

def declare():
    rguard();assert not WC.exists();dump(WC,{'declared_utc':now(),'revision':'w2','before_all_native_w2_execution':True,'root_config_sha256':streamsha(RC),'cases':[kind+'_'+axis for axis in 'XYZ' for kind in ['REFERENCE','RBE2']],
        'purpose':'Distinguish missing rotational global accounting in a no-part point witness from the actual root whose main node has shell rotations. Add one fully prescribed undeforming10x10mm fuselage shell using inherited LAW2/1 and TYPE1/1 thickness2.54mm. Every RBE2 case has a matched independently prescribed reference with the identical continuum and point masses, coordinates and rigid motion.',
        'geometry':'Host at origin, backing corners[10,0,0],[10,0,10],[0,0,10]; six actual root offsets unchanged; no massless artificial material.',
        'inherited_sources':{'source':rel(SOURCE),'deck_sha256':streamsha(SOURCE/'A20_CORE3D_TIED_20_0000.rad')},
        'point_masses':read(RC)['point_masses_g'],'analytical_backing_mass_g':100*2.54*.00278,
        'acceptance':{'matched_energy_relative':.02,'absolute_J':.0001,'native_energy_balance_relative':.02,'motion_mm':.002,'velocity_m_s':.005,'zero_errors_and_warnings':True},
        'execution':{'duration_ms':1,'dt_cap_ms':.000025,'CPU_threads':1,'solver_cap_s':90},'whole_mechanics_changed':False,'whole_root_cause_proven':False,'strength_or_fracture_qualified':False})
    dump(OUT/'root_w2_guard.json',{'sha256':streamsha(WC)});print({'declared':'w2 structural root witnesses','cases':6},flush=True)

def wguard():rguard();assert streamsha(WC)==read(OUT/'root_w2_guard.json')['sha256']

def one(cid):
    wguard();c=read(RC);kind,axis=cid.split('_');ax='XYZ'.index(axis);d=OUT/'w2'/cid;n='A21_ROOT_'+cid;assert not d.exists();d.mkdir(parents=True)
    xyz=np.vstack([c['nodes_mm'],[10,0,0],[10,0,10],[0,0,10]]);T=np.linspace(0,1,10001);theta=np.pi/2*(3*T*T-2*T**3);a=np.eye(3)[ax]
    rotated=xyz[None,:,:]*np.cos(theta)[:,None,None]+np.cross(a,xyz)[None,:,:]*np.sin(theta)[:,None,None]+a[None,None,:]*np.dot(xyz,a)[None,:,None]*(1-np.cos(theta)[:,None,None]);disp=rotated-xyz
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    src={b[0]:b for b in blocks((SOURCE/'A20_CORE3D_TIED_20_0000.rad').read_text().splitlines())}
    L+=src['/MAT/LAW2/1']+src['/PROP/TYPE1/1']+['/PART/1','UNDEFORMED_KNOWN_FUSELAGE_BACKING',ii(1,1,0),'/SHELL/1',ii(1,1,8,9,10),'/ADMAS/5/1','KNOWN_POINT_MASSES']+[ff(v)+ii(i+1) for i,v in enumerate(c['point_masses_g'])]
    if kind=='RBE2':L+=['/GRNOD/NODE/20','DEPENDENTS',ii(2,3,4,5,6,7),'/RBE2/1','SHELL_ATTACHED_ROOT_OFFSET',ii(1)+'   111 111'+ii(0,20,0)]
    forced=[1,8,9,10]+(list(range(2,8)) if kind=='REFERENCE' else []); fid=1000
    for ni in forced:
        L+=[f'/GRNOD/NODE/{ni}',f'NODE_{ni}',ii(ni)]
        dirs=['X','Y','Z']+(['XX','YY','ZZ'] if ni in [1,8,9,10] else [])
        for j,direction in enumerate(dirs):
            fid+=1;vals=disp[:,ni-1,j] if j<3 else theta if j-3==ax else np.zeros(len(T))
            L +=[f'/FUNCT/{fid}',f'RIGID_{ni}_{direction}']+[ff(t,v) for t,v in zip(T,vals)]+[f'/IMPDISP/{fid}',f'RIGID_{ni}_{direction}',ii(fid)+f'{direction:>10}'+ii(0,0,ni)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/NODE/1','POINT_DIAGNOSTIC',''.join(f'{k:>10}' for k in ['DX','DY','DZ','VX','VY','VZ'])]+[ii(i,0) for i in range(1,11)]+['/TH/PART/1','BACKING_ENERGY','        IE        KE        HE        PW',ii(1),'/IOFLAG',ii(6)+' '*20+ii(-1,0,0,0),'/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8');E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/DT',ff(.4,0),'/DTIX',ff(.000025,.000025),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026'];(d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'config_sha256':streamsha(WC),'nodes_mm':xyz.tolist()})
    en=env();en['OMP_NUM_THREADS']='1';en['RAD_HMPP_DOMAINS']='1'
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',90,en);s=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,s[-3000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',90,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',90,en)
        H=histories(d/(n+'T01.csv'));tot=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;R=tot-tot[0]-H['EXTERNAL WORK']*.001
        r={'created_utc':now(),'case':cid,'peak_total_energy_J':float(tot.max()),'peak_KE_J':float(H['KINETIC ENERGY'].max()*.001),'peak_RKE_J':float(H['ROTATION ENERGY'].max()*.001),'maximum_energy_residual_J':float(abs(R).max()),'minimum_IE_J':float(H['INTERNAL ENERGY'].min()*.001),'maximum_IE_J':float(H['INTERNAL ENERGY'].max()*.001),'native_energy_balance_pass':bool(abs(R).max()<.02*max(float(abs(tot).max()),float(abs(H['EXTERNAL WORK']*.001).max()))+.0001),'same_masses_and_geometry_as_matched_case':True,'physical_strength_qualified':False};dump(d/'review.json',r);np.savez_compressed(d/'energy_history_SI.npz',time_ms=H['time'],native_total_J=tot,external_work_J=H['EXTERNAL WORK']*.001,residual_J=R);print(r,flush=True)
    except Exception:
        dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc()});raise

def run():
    wguard()
    for cid in read(WC)['cases']:one(cid)
    pairs=[]
    for ax in 'XYZ':
        A=np.load(OUT/f'w2/REFERENCE_{ax}/energy_history_SI.npz');B=np.load(OUT/f'w2/RBE2_{ax}/energy_history_SI.npz');delta=B['native_total_J']-np.interp(B['time_ms'],A['time_ms'],A['native_total_J']);peak=float(A['native_total_J'].max());tol=.02*peak+.0001
        pairs.append({'axis':ax,'reference_peak_total_J':peak,'RBE2_peak_total_J':float(B['native_total_J'].max()),'maximum_energy_difference_J':float(abs(delta).max()),'tolerance_J':tol,'matched_energy_pass':bool(abs(delta).max()<tol),'reference_energy_balance_pass':read(OUT/f'w2/REFERENCE_{ax}/review.json')['native_energy_balance_pass'],'RBE2_energy_balance_pass':read(OUT/f'w2/RBE2_{ax}/review.json')['native_energy_balance_pass']})
    dump(OUT/'root_structural_review.json',{'created_utc':now(),'pairs':pairs,'all_pass':all(all(r[k] for k in ['matched_energy_pass','reference_energy_balance_pass','RBE2_energy_balance_pass']) for r in pairs),'source_not_modified':True,'whole_cause_proven':False});print(pairs,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['cached','declare','run']);globals()[p.parse_args().action]()
