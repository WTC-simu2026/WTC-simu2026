"""Isolated prescribed rigid motion of the actual root offset geometry and known point masses."""
from run_aircraft_a21 import *
import urllib.request
RC=ROOT/'wtc1_simulation_v8/data/aircraft_a21_root_declaration.json'

def rguard():guard();assert streamsha(RC)==read(OUT/'root_guard.json')['sha256']

def declare():
    guard();assert not RC.exists();m=read(SOURCE/'mesh.json');x=np.asarray(m['nodes_mm']);root=[r for r in m['new_RBE2'] if r['role']=='root'][0]
    xyz=np.vstack([np.zeros(3),x[np.asarray(root['dependent_nodes'])-1]-x[root['host']-1]])
    masses=np.r_[10.,np.ones(6)];I=sum((mass*(np.dot(q,q)*np.eye(3)-np.outer(q,q)) for q,mass in zip(xyz,masses)))
    c={'iteration':'AIRCRAFT-A21','declared_utc':now(),'seed':1102046,'random_draws':0,'cases':['TRANSLATION_X','ROTATION_X','ROTATION_Y','ROTATION_Z','ROTATION_Y_HALF'],
       'purpose':'Independent known point-mass witness of ideal full111111 RBE2, including its scalar rotational inertia; no structural or material response and no fitting of whole impact.',
       'source_root':root,'source_mesh':rel(SOURCE/'mesh.json'),'source_mesh_sha256':streamsha(SOURCE/'mesh.json'),'nodes_mm':xyz.tolist(),'point_masses_g':masses.tolist(),'physical_point_inertia_about_host_g_mm2':I.tolist(),
       'motion':{'duration_ms':1,'smooth_path':'s=3t^2-2t^3, 0<=t<=1ms','translation_mm':10,'rotation_rad':float(np.pi/2),'host_other_DOF':'zero imposed displacement','initial_velocity':'zero'},
       'RBE2':{'Trarot':'111111','Iflag':0,'no_mass_compensation':True},
       'execution':{'CPU_threads':1,'GPU':False,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'history_dt_ms':.001,'animation_dt_ms':.025,'solver_cap_s':90},
       'acceptance':{'mass_relative':1e-6,'energy_balance_fraction':.02,'physical_kinetic_energy_fraction':.02,'absolute_energy_J':.0001,'analytic_motion_mm':.002,'analytic_velocity_m_s':.005,'impulse_relative':.02,'impulse_absolute_Ns':.00001},
       'references':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/rbe2_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/admas_starter_r.htm'],
       'known_test_masses_are_not_whole_aircraft_mass_changes':True,'independent_of_historical_damage':True,'source_A20_not_modified':True,'root_attachment_strength_or_fracture_qualified':False,'whole_dynamic_qualification':False}
    dump(RC,c);dump(OUT/'root_guard.json',{'created_utc':now(),'sha256':streamsha(RC),'before_any_new_root_solver':True})
    d=OUT/'sources';d.mkdir(exist_ok=True);src=[]
    for i,u in enumerate(c['references']):
        p=d/f'root_primary_{i}.html';assert not p.exists();p.write_bytes(urllib.request.urlopen(u,timeout=40).read());src.append({'url':u,'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    dump(OUT/'root_source_manifest.json',{'created_utc':now(),'files':src});print({'root_witness_declared':len(c['cases']),'point_inertia_diagonal_g_mm2':np.diag(I).tolist()},flush=True)

def run_one(cid):
    rguard();c=read(RC);rev=read(OUT/'root_w1_declaration.json');assert streamsha(RC)==rev['configuration_sha256'];d=OUT/'w1'/cid;n='A21_ROOT_'+cid;assert not d.exists();d.mkdir(parents=True)
    xyz=np.asarray(c['nodes_mm']);mass=np.asarray(c['point_masses_g']);ts=np.linspace(0,1,10001);u=3*ts**2-2*ts**3;motion=np.zeros((len(ts),6))
    ax=0 if cid=='TRANSLATION_X' else 'XYZ'.index(cid.split('_')[1]);motion[:,ax if cid=='TRANSLATION_X' else ax+3]=u*(10 if cid=='TRANSLATION_X' else np.pi/2)
    L=['#RADIOSS STARTER','/BEGIN',n,ii(2026,0),ff('g','mm','ms'),ff('g','mm','ms'),'/TITLE',n,'/ANALY',ii(0)+ff(0)+ii(0),'/SPMD',ii(0,0)+ff(0,1),'/NODE']+[ii(i+1)+ff(*q) for i,q in enumerate(xyz)]
    L+=['/ADMAS/5/1','KNOWN_INDEPENDENT_POINT_MASSES']+[ff(v)+ii(i+1) for i,v in enumerate(mass)]
    L+=['/GRNOD/NODE/1','HOST',ii(1),'/GRNOD/NODE/2','DEPENDENTS',ii(2,3,4,5,6,7),'/RBE2/1','ACTUAL_ROOT_OFFSET_GEOMETRY_WITH_KNOWN_MASSES',ii(1)+'   111 111'+ii(0,2,0)]
    for j,direction in enumerate(['X','Y','Z','XX','YY','ZZ']):
        f=1001+j; L +=[f'/FUNCT/{f}',f'HOST_{direction}']+[ff(t,v) for t,v in zip(ts,motion[:,j])]+[f'/IMPDISP/{f}',f'HOST_{direction}',ii(f)+f'{direction:>10}'+ii(0,0,1)+' '*10+ii(0),ff(1,1,0,1e30)]
    L+=['/TH/NODE/1','POINT_DIAGNOSTIC',''.join(f'{k:>10}' for k in ['DX','DY','DZ','VX','VY','VZ','REACX','REACY','REACZ'])]+[ii(i,0) for i in range(1,8)]+['/IOFLAG',ii(6)+' '*20+ii(-1,0,0,0),'/END']
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8')
    dt=c['execution']['half_dt_cap_ms'] if cid.endswith('_HALF') else c['execution']['dt_cap_ms']
    E=['/ANIM/DT',ff(0,.025),'/ANIM/MASS','/ANIM/VECT/DISP','/ANIM/VECT/VEL','/DT',ff(.4,0),'/DTIX',ff(dt,dt),'/PRINT/-100/100',f'/RUN/{n}/1',ff(1),'/TFILE/4',ff(.001),'/VERS/2026']
    (d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'axis':ax,'config_sha256':streamsha(RC),'dt_cap_ms':dt})
    en=env();en['OMP_NUM_THREADS']='1';en['RAD_HMPP_DOMAINS']='1'
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',90,en)
        s=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);ids=re.findall(r'WARNING ID\s*:\s*(\d+)',s);allowed=bool(ok and ne==0 and nw==1 and ids==['1114']);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':nw,'errors':ne,'warning_ids':ids,'strict_zero_warning_pass':nw==0,'declared_point_mass_execution_allowed':allowed,'no_parts_expected_in_this_point_mass_witness':True}); assert allowed,s[-3000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',90,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace')
        assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',90,en);review(d,n,cid)
    except Exception:
        dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc(),'source_unchanged':True});raise

def review(d,n,cid):
    c=read(RC);a=c['acceptance'];H=histories(d/(n+'T01.csv'));T=H['time'];mass=np.asarray(c['point_masses_g']);xyz=np.asarray(c['nodes_mm']); ax=read(d/'generation.json')['axis']
    terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'];total=sum(H[k] for k in terms)*.001;EW=H['EXTERNAL WORK']*.001;R=total-total[0]-EW
    if cid=='TRANSLATION_X':expected=.5*mass.sum()*(10*(6*T-6*T**2))**2*.001
    else:expected=.5*np.asarray(c['physical_point_inertia_about_host_g_mm2'])[ax,ax]*(np.pi/2*(6*T-6*T**2))**2*.001
    peak=float(expected.max());checks={'physical_mass':bool(abs(H['MASS'][0]-mass.sum())<a['mass_relative']*mass.sum()),'no_scaled_mass':bool(np.all(H['ADDED MASS']==0)),'zero_internal_energy':bool(abs(H['INTERNAL ENERGY']).max()*.001<a['absolute_energy_J']),'native_energy_balance':bool(abs(R).max()<a['energy_balance_fraction']*max(float(abs(total).max()),float(abs(EW).max()))+a['absolute_energy_J']),'physical_point_kinetic_energy':bool(abs(total-expected).max()<a['physical_kinetic_energy_fraction']*peak+a['absolute_energy_J'])}
    r={'created_utc':now(),'case':cid,'rows':len(T),'last_history_ms':float(T[-1]),'expected_peak_physical_KE_J':peak,'native_peak_total_energy_J':float(total.max()),'maximum_native_energy_residual_J':float(abs(R).max()),'maximum_native_vs_point_KE_J':float(abs(total-expected).max()),'native_peak_KE_J':float((H['KINETIC ENERGY']*.001).max()),'native_peak_RKE_J':float((H['ROTATION ENERGY']*.001).max()),'checks':checks,'pass':all(checks.values()),'physical_energy_not_invented':True,'point_mass_witness_only':True,'whole_root_cause_proven':False,'root_strength_qualified':False}
    np.savez_compressed(d/'energy_history_SI.npz',time_ms=T,native_total_J=total,external_work_J=EW,residual_J=R,physical_point_KE_J=expected);dump(d/'review.json',r);print(r,flush=True)

def run():
    rguard()
    p=OUT/'root_w1_declaration.json';assert not p.exists()
    dump(p,{'declared_utc':now(),'configuration_sha256':streamsha(RC),'revision':'w1','before_all_w1_native_runs':True,'w0_zero_warning_failure_retained':True,'only_execution_interpretation_change':'Expected warning1114: there is no defined part. This is deliberately a seven-node point-mass-only kinematic witness with one RBE2 and six prescribed host DOFs; no continuum parts or constitutive response. Retain strict zero-warning failure. Require exactly this warning and zero errors before controlled execution. No mechanical or acceptance-energy changes.','expected_warning_ids':['1114'],'new_whole_impact_changes':False})
    for cid in read(RC)['cases']:run_one(cid)
    rows=[read(OUT/'w1'/cid/'review.json') for cid in read(RC)['cases']];dump(OUT/'root_witness_review.json',{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'strict_zero_warning_gate_pass':False,'point_mass_no_part_warning_explicit':True,'scalar_inertia_root_qualified':all(r['pass'] for r in rows),'whole_root_cause_proven':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
