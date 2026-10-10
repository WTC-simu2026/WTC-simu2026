"""Independent physical angular momentum: actual nodal mass plus actual shell rotation, never RKE repair."""
from run_aircraft_a24 import *

def fields(cid):
    d=OUT/'w3'/cid;g=read(d/'generation.json');h={k:v for k,v in np.load(d/'histories_SI.npz').items()}
    m=np.asarray(g['known_translational_node_masses_g']);X=h['positions_mm'];V=h['velocities_m_s'];W=h['angular_velocity_rad_ms']
    Ltrans=np.sum(m[None,:,None]*np.cross(X,V),axis=1);Lrot=np.zeros_like(Ltrans)
    for ids in [[0,1,2,3],[4,5,6,7],[16,17,18,19]]:
        normal=np.cross(X[:,ids[1]]-X[:,ids[0]],X[:,ids[3]]-X[:,ids[0]]);normal/=np.linalg.norm(normal,axis=1)[:,None]
        for i in ids:
            # Intrinsic physical inertia through thickness, transverse to shell normal; normal-axis inertia already represented by in-plane lumped masses.
            Lrot+=m[i]*.5**2/12*(W[:,i]-normal*np.sum(W[:,i]*normal,axis=1)[:,None])
    L=(Ltrans+Lrot)*1e-6
    drift=float(np.linalg.norm(L-L[0],axis=1).max());tol=.002*float(np.linalg.norm(L[0]))+1e-9
    return g,h,L,{'case':cid,'initial_L_kg_m2_s':L[0].tolist(),'maximum_L_drift_kg_m2_s':drift,'tolerance_kg_m2_s':tol,'physical_L_conserved':drift<tol,'shell_intrinsic_not_native_scalar_RKE':True,'model_control_only':True}

def pair(motion,suffix=''):
    rg,r,rl,rr=fields('REFERENCE_FREE_'+motion+suffix);g,h,cl,cr=fields('CONNECTED_FREE_'+motion+suffix)
    T=h['time_ms'];mask=(T>=r['time_ms'][0])&(T<=r['time_ms'][-1]);T=T[mask]
    reference=np.column_stack([np.interp(T,r['time_ms'],rl[:,a]) for a in range(3)]);difference=cl[mask]-reference
    ids=np.asarray(g['clip_node_ids'])-1;q=np.asarray(g['nodes_mm'])[ids];v=np.asarray(g['initial_velocity_m_s'])[ids];m=np.asarray(g['clip_known_nodal_masses_g']);expected=np.sum(m[:,None]*np.cross(q,v),axis=0)*1e-6
    drift=float(np.linalg.norm(difference-expected,axis=1).max());tol=.02*float(np.linalg.norm(expected))+1e-9
    expected_KE=float(.5*np.sum(m[:,None]*v**2)*.001);actual_KE=float(h['KE_J'][0]-r['KE_J'][0]);ktol=.002*expected_KE+1e-7
    checks={'reference_physical_L_conserved':rr['physical_L_conserved'],'connected_physical_L_conserved':cr['physical_L_conserved'],
       'added_physical_L_conserved':drift<tol,'added_initial_KE':abs(actual_KE-expected_KE)<ktol,
       'reference_native_gates':read(OUT/'w3'/('REFERENCE_FREE_'+motion+suffix)/'review.json')['pass'],
       'connected_native_gates':read(OUT/'w3'/('CONNECTED_FREE_'+motion+suffix)/'review.json')['pass']}
    return {'motion':motion,'suffix':suffix,'reference':rr,'connected':cr,'known_added_L_kg_m2_s':expected.tolist(),'maximum_added_L_error_kg_m2_s':drift,'added_L_tolerance_kg_m2_s':tol,'known_added_initial_KE_J':expected_KE,'native_added_initial_KE_J':actual_KE,'KE_tolerance_J':ktol,'checks':checks,'pass':all(checks.values())}

def main():
    cfg=ROOT/'wtc1_simulation_v8/data/aircraft_a24_angular.json';assert streamsha(cfg)==read(OUT/'angular_guard.json')['sha256']
    rows=[pair(f'ROTATION_S100_{a}') for a in 'XYZ']+[pair('TRANSLATION_S100')];half=pair('ROTATION_S100_Y','_HALF')
    g,h,L,r=fields('CONNECTED_FREE_ROTATION_S100_Y');g2,h2,L2,r2=fields('CONNECTED_FREE_ROTATION_S100_Y_HALF');dt_ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));T=h['time_ms'];mask=(T>=h2['time_ms'][0])&(T<=h2['time_ms'][-1]);T=T[mask]
    le=float(np.linalg.norm(L[mask]-np.column_stack([np.interp(T,h2['time_ms'],L2[:,a]) for a in range(3)]),axis=1).max());et=float(abs(h['total_J'][mask]-np.interp(T,h2['time_ms'],h2['total_J'])).max())
    refine={'actual_dt_ratio':dt_ratio,'L_difference_kg_m2_s':le,'energy_difference_J':et,'checks':{'dt_really_shorter':dt_ratio<.6,'physical_L_converges':le<.002*np.linalg.norm(L[0])+1e-9,'total_energy_converges':et<.002*h['total_J'][0]+1e-7,'both_Y_pairs':rows[1]['pass'] and half['pass']}}
    refine['checks']={k:bool(v) for k,v in refine['checks'].items()}
    checks={'all_primary_pairs':all(r['pass'] for r in rows),'shorter_step':all(refine['checks'].values())}
    dump(OUT/'physical_angular_momentum_review.json',{'created_utc':now(),'pairs':rows,'half_dt_pair':half,'refinement':refine,'checks':checks,'pass':all(checks.values()),'unit':'kg m2/s','no_native_RKE_added_reconstructed_or_subtracted':True,'hypothesis':'lumped translational masses plus physical shell thickness inertia; accuracy checked on source-backed model parameters, not historical impact identification','actual_curved_root_geometry_not_qualified':True,'whole_insertion_ready':False,'objective1_complete':False})
    print({'physical_angular_controls':checks,'pair_pass':[r['pass'] for r in rows]},flush=True)

if __name__=='__main__':main()
