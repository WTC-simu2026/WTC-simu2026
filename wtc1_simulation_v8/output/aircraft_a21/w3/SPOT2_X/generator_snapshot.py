"""Replace only the isolated root RBE2 by a native finite-offset surface tie."""
from diagnose_aircraft_a21_root import *
TC=OUT/'root_type2_declaration.json'

def declare():
    wguard();assert not TC.exists();assert not read(OUT/'root_structural_review.json')['all_pass']
    c={'declared_utc':now(),'before_any_new_surface_tie_solver':True,'iteration':'AIRCRAFT-A21','revision':'w3','cases':['SPOT2_X','SPOT2_Y','SPOT2_Z','SPOT2_Y_HALF','SPOT5_X','SPOT5_Y','SPOT5_Z'],
       'purpose':'Matched known-mass backing witnesses after RBE2 rotational energy failures. Replace only root attachment, keep identical coordinates, material, known masses, imposed motion, energy thresholds and reference trajectories.',
       'reference_declaration_sha256':streamsha(WC),'root_config_sha256':streamsha(RC),
       'TYPE2':{'Ignore':1000,'Iproj':2,'dsearch_mm':5,'Idel2':1000,'secondary_nodes':[2,3,4,5,6,7],'main_part':1,'search_rationale':'Actual radial offsets4.25mm; small root corner extrapolations under1mm. All six points must follow native prescribed rigid reference; do not accept a silently unattached point.'},
       'acceptance':read(WC)['acceptance'],'execution':{'CPU_threads':1,'end_ms':1,'dt_cap_ms':.000025,'half_dt_cap_ms':.0000125,'solver_cap_s':90},
       'nested_TYPE2_hierarchy_not_yet_tested':True,'whole_attachment_not_yet_changed':True,'attachment_strength_or_failure_qualified':False,
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inter_type2_starter_r.htm']}
    dump(TC,c);dump(OUT/'root_type2_guard.json',{'created_utc':now(),'sha256':streamsha(TC)});print({'declared_root_surface_ties':len(c['cases'])},flush=True)

def tguard():wguard();assert streamsha(TC)==read(OUT/'root_type2_guard.json')['sha256']

def one(cid):
    tguard();tag,axis,*rest=cid.split('_');spot=int(tag[4:]);ax='XYZ'.index(axis);src=OUT/f'w2/RBE2_{axis}';pn='A21_ROOT_RBE2_'+axis;d=OUT/'w3'/cid;n='A21_ROOT_'+cid;assert not d.exists();d.mkdir(parents=True)
    L=[]
    for old in blocks((src/(pn+'_0000.rad')).read_text().splitlines()):
        b=old.copy()
        if b[0]=='/RBE2/1':
            b=['/SURF/PART/20','KNOWN_BACKING_MAIN',ii(1),'/INTER/TYPE2/20','FINITE_OFFSET_ROOT_SURFACE_TIE',ii(20,20,1000,spot,0,2,1000,0)+ff(5),ii(0)+ff(0)+' '*60+ii(2)]
        if b[0] in ['/BEGIN','/TITLE']:b[1]=n
        L+=b
    (d/(n+'_0000.rad')).write_text('\n'.join(L)+'\n',encoding='utf-8');E=[]
    for old in blocks((src/(pn+'_0001.rad')).read_text().splitlines()):
        b=old.copy()
        if b[0].startswith('/RUN/'):b[0]=f'/RUN/{n}/1'
        if b[0]=='/DTIX' and rest:b[1]=ff(.0000125,.0000125)
        E+=b
    (d/(n+'_0001.rad')).write_text('\n'.join(E)+'\n',encoding='utf-8');shutil.copy2(__file__,d/'generator_snapshot.py');dump(d/'generation.json',{'created_utc':now(),'name':n,'case':cid,'configuration_sha256':streamsha(TC),'source':rel(src),'only_attachment_replaced':True,'physical_source_masses_preserved':True})
    en=env();en['OMP_NUM_THREADS']='1';en['RAD_HMPP_DOMAINS']='1'
    try:
        ok=execute(RUNTIME/'starter_win64.exe',['-i',n+'_0000.rad','-np','1'],d,'starter.log',90,en);s=(d/'starter.log').read_text(errors='replace');nw=int(re.findall(r'(\d+) WARNING\(S\)',s)[-1]);ne=int(re.findall(r'(\d+) ERROR\(S\)',s)[-1]);dump(d/'starter_gate.json',{'exit_ok':ok,'warnings':nw,'errors':ne,'pass':bool(ok and nw==0 and ne==0)});assert ok and nw==0 and ne==0,s[-3000:]
        assert execute(RUNTIME/'engine_win64.exe',['-i',n+'_0001.rad'],d,'engine.log',90,en);assert 'NORMAL TERMINATION' in (d/'engine.log').read_text(errors='replace');assert execute(RUNTIME/'th_to_csv_win64.exe',[n+'T01'],d,'converter.log',90,en)
        H=histories(d/(n+'T01.csv'));T=H['time'];v=np.column_stack(list(H.values()))[:,23:83].reshape(len(T),10,6)
        A=histories(OUT/f'w2/REFERENCE_{axis}'/('A21_ROOT_REFERENCE_'+axis+'T01.csv'));av=np.column_stack(list(A.values()))[:,23:83].reshape(len(A['time']),10,6);va=np.column_stack([np.interp(T,A['time'],av.reshape(len(A['time']),-1)[:,j]) for j in range(60)]).reshape(len(T),10,6)
        total=sum(H[k] for k in ['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY'])*.001;EW=H['EXTERNAL WORK']*.001;R=total-total[0]-EW
        ref=np.load(OUT/f'w2/REFERENCE_{axis}/energy_history_SI.npz');refE=np.interp(T,ref['time_ms'],ref['native_total_J']);delta=total-refE;a=read(TC)['acceptance'];peak=float(refE.max());tol=a['matched_energy_relative']*peak+a['absolute_J']
        pos=float(abs(v[:,:,:3]-va[:,:,:3]).max());vel=float(abs(v[:,:,3:]-va[:,:,3:]).max());checks={'zero_errors_and_warnings':True,'all_secondary_points_follow_rigid_reference':pos<a['motion_mm'],'all_point_velocities_follow_reference':vel<a['velocity_m_s'],'matched_reference_energy':float(abs(delta).max())<tol,'native_energy_balance':float(abs(R).max())<a['native_energy_balance_relative']*max(float(abs(total).max()),float(abs(EW).max()))+a['absolute_J'],'physical_mass_preserved':bool(abs(H['MASS'][0]-A['MASS'][0])<1e-6*A['MASS'][0]),'no_scaled_mass':bool(np.all(H['ADDED MASS']==0))}
        r={'created_utc':now(),'case':cid,'spot':spot,'maximum_matched_displacement_error_mm':pos,'maximum_matched_velocity_error_m_s':vel,'maximum_native_energy_residual_J':float(abs(R).max()),'maximum_matched_energy_error_J':float(abs(delta).max()),'reference_peak_total_J':peak,'native_peak_total_J':float(total.max()),'matched_energy_tolerance_J':tol,'checks':{k:bool(x) for k,x in checks.items()},'pass':all(checks.values()),'nested_hierarchy_qualified':False,'strength_failure_qualified':False,'whole_cause_proven':False}
        np.savez_compressed(d/'energy_history_SI.npz',time_ms=T,native_total_J=total,reference_total_J=refE,energy_difference_J=delta,residual_J=R);dump(d/'review.json',r);print(r,flush=True)
    except Exception:
        dump(d/('retained_failure_'+now().replace(':','-')+'.json'),{'created_utc':now(),'traceback':traceback.format_exc()});raise

def run():
    tguard()
    for cid in read(TC)['cases']:one(cid)
    rows=[read(OUT/'w3'/cid/'review.json') for cid in read(TC)['cases']];dump(OUT/'root_type2_review.json',{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'Spot2_pass':all(r['pass'] for r in rows if r['spot']==2),'Spot5_pass':all(r['pass'] for r in rows if r['spot']==5),'whole_engine_allowed':False,'nested_hierarchy_qualified':False,'physical_root_strength_qualified':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
