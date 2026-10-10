"""Independent paired added inertia, free initial energy and time step refinement."""
from run_aircraft_a24 import *
CONNECTED_REVISION='w0'

def load(cid):
    d=OUT/(CONNECTED_REVISION if cid.startswith('CONNECTED_') else 'w0')/cid;g=read(d/'generation.json');h={k:v for k,v in np.load(d/'histories_SI.npz').items()};r=read(d/'review.json');return g,h,r

def prescribed_pair(ax,suffix=''):
    rg,r,rr=load('REFERENCE_ROTATION_'+ax+suffix);g,h,cr=load('CONNECTED_ROTATION_'+ax+suffix)
    T=h['time_ms'];mask=(T>=r['time_ms'][0])&(T<=r['time_ms'][-1]);T=T[mask]
    ids=np.array(g['clip_node_ids'])-1;m=np.array(g['clip_known_nodal_masses_g']);q=np.array(g['nodes_mm'])[ids]
    X,V,a,w=rotation(q,T,ax,g['duration_ms']);expected=.5*np.sum(m[None,:,None]*V**2,axis=(1,2))*.001
    known_native_motion=.5*np.sum(m[None,:,None]*h['velocities_m_s'][mask][:,ids]**2,axis=(1,2))*.001
    actual=h['KE_J'][mask]-np.interp(T,r['time_ms'],r['KE_J']);diff=float(abs(actual-expected).max());tol=.02*float(expected.max())+1e-7
    shift=float(abs(h['time_ms']-r['time_ms']).max());slope=float(abs(np.diff(r['KE_J'])/np.diff(r['time_ms'])).max())
    checks={'both_balances':rr['checks']['native_full_energy_balance'] and cr['checks']['native_full_energy_balance'],'independent_added_rigid_KE':diff<tol,
       'added_KE_for_actual_native_velocities':bool(abs(actual-known_native_motion).max()<tol),
       'mass_addition':abs(cr['native_mass_g']-rr['native_mass_g']-.00556)<1e-6*.00556,
       'temporal_alignment_bound':slope*shift<tol/10,'no_extrapolation':len(T)>990,
       'connected_all_velocity_gate':cr['checks']['all_nodes_velocity']}
    observable=w>w.max()*.2;inf=2*actual[observable]/w[observable]**2/.001
    return {'axis':ax,'suffix':suffix,'maximum_added_KE_error_J':diff,'tolerance_J':tol,'peak_known_added_KE_J':float(expected.max()),
       'native_added_I_median_g_mm2':float(np.median(inf)),'known_I_g_mm2':float(inertia(q,m)['XYZ'.index(ax),'XYZ'.index(ax)]),
       'maximum_timestamp_shift_ms':shift,'temporal_alignment_bound_J':shift*slope,'checks':checks,'pass':all(checks.values())}

def main():
    guard();rows=[prescribed_pair(a) for a in 'XYZ'];half=prescribed_pair('Z','_HALF');free=[]
    for cid in ['TRANSLATION','ROTATION_X','ROTATION_Y','ROTATION_Z']:
        rg,r,rr=load('REFERENCE_FREE_'+cid);g,h,cr=load('CONNECTED_FREE_'+cid);ids=np.array(g['clip_node_ids'])-1;m=np.array(g['clip_known_nodal_masses_g']);v=np.array(g['initial_velocity_m_s'])[ids]
        expected=float(.5*np.sum(m[:,None]*v*v)*.001);actual=float(h['KE_J'][0]-r['KE_J'][0]);tol=.002*expected+1e-7
        checks={'both_native_free_balances':rr['checks']['native_full_energy_balance'] and cr['checks']['native_full_energy_balance'],
          'both_free_energy_checks':rr['checks']['free_energy'] and cr['checks']['free_energy'],
          'independent_added_initial_KE':abs(actual-expected)<tol,'no_contact_damping':cr['checks']['no_undeclared_contact_damping']}
        free.append({'motion':cid,'known_added_initial_KE_J':expected,'native_added_initial_KE_J':actual,'absolute_error_J':abs(actual-expected),'tolerance_J':tol,'checks':checks,'pass':all(checks.values())})
    rg,r,rr=load('REFERENCE_ROTATION_Z');g,h,cr=load('CONNECTED_ROTATION_Z');rg2,r2,rr2=load('REFERENCE_ROTATION_Z_HALF');g2,h2,cr2=load('CONNECTED_ROTATION_Z_HALF')
    common=min(h['time_ms'][-1],h2['time_ms'][-1]);mask=(h['time_ms']>=max(r['time_ms'][0],r2['time_ms'][0],h2['time_ms'][0]))&(h['time_ms']<=common);T=h['time_ms'][mask]
    e=h['KE_J'][mask]-np.interp(T,r['time_ms'],r['KE_J']);e2=np.interp(T,h2['time_ms'],h2['KE_J'])-np.interp(T,r2['time_ms'],r2['KE_J']);mesh_error=float(abs(e2-e).max());peak=max(float(abs(e).max()),float(abs(e2).max()));dt_ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));dtchecks={'actual_time_step_halved':dt_ratio<.6,'added_KE_converges':mesh_error<.01*peak+1e-7,'both_Z_pairs':rows[2]['pass'] and half['pass']}
    e4=load('CONNECTED_EXTENSION_N4')[2]['last_clip_IE_J'];e8=load('CONNECTED_EXTENSION_N8')[2]['last_clip_IE_J'];mesh=abs(e8-e4)/e8
    if CONNECTED_REVISION=='w0':case_pass=read(OUT/'native_case_summary.json')['all_pass']
    else:
        config=ROOT/'wtc1_simulation_v8/data/aircraft_a24_lowdamping.json';assert streamsha(config)==read(OUT/'lowdamping_guard.json')['sha256']
        case_pass=read(OUT/'native_case_summary_w1.json')['all_pass'] and all(r['pass'] for r in read(OUT/'native_case_summary.json')['cases'] if r['case'].startswith('REFERENCE_'))
    checks={'all_native_case_gates':case_pass,'all_paired_inertias':all(x['pass'] for x in rows),'all_free_initial_inertias':all(x['pass'] for x in free),'time_refinement':all(dtchecks.values()),'elastic_mesh':mesh<.05}
    dest=OUT/('paired_coupling_review.json' if CONNECTED_REVISION=='w0' else 'paired_coupling_w1_review.json');assert not dest.exists();dump(dest,{'created_utc':now(),'connected_revision':CONNECTED_REVISION,'reference_revision':'w0','pairs':rows,'free_pairs':free,'half_dt_pair':half,'time_refinement':{'checks':dtchecks,'median_dt_ratio':dt_ratio,'added_KE_difference_J':mesh_error,'limit_J':.01*peak+1e-7},'elastic_mesh_relative_difference':mesh,'checks':checks,'pass':all(checks.values()),'native_energy_not_reconstructed':True,'mass_not_compensated':True,'whole_insertion_ready':False,'actual_curved_geometry_controls_required':True,'physical_strength_or_fracture_qualified':False,'objective1_complete':False})
    print({'A24_paired_controls':checks},flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--connected-revision',choices=['w0','w1'],default='w0');CONNECTED_REVISION=p.parse_args().connected_revision;main()
