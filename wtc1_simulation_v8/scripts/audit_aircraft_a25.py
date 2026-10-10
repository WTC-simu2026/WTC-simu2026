"""Same physical angular-momentum test as A24, with cached reference histories."""
from run_aircraft_a25 import *

def fields(d):
    g=read(d/'generation.json');h={k:v for k,v in np.load(d/'histories_SI.npz').items()};m=np.asarray(g['known_translational_node_masses_g']);X=h['positions_mm'];V=h['velocities_m_s'];W=h['angular_velocity_rad_ms'];L=np.sum(m[None,:,None]*np.cross(X,V),axis=1)
    for ids in [[0,1,2,3],[4,5,6,7],[16,17,18,19]]:
        n=np.cross(X[:,ids[1]]-X[:,ids[0]],X[:,ids[3]]-X[:,ids[0]]);n/=np.linalg.norm(n,axis=1)[:,None]
        for i in ids:L+=m[i]*.5**2/12*(W[:,i]-n*np.sum(W[:,i]*n,axis=1)[:,None])
    L*=1e-6;drift=float(np.linalg.norm(L-L[0],axis=1).max());tol=.002*np.linalg.norm(L[0])+1e-9
    return g,h,L,{'path':rel(d),'initial_L_kg_m2_s':L[0].tolist(),'maximum_drift_kg_m2_s':drift,'limit_kg_m2_s':float(tol),'pass':bool(drift<tol)}

def pair(motion):
    cfg=read(CFG);rd=ROOT/cfg['native_reference_paths'][motion];cd=OUT/'w0'/('CONNECTED_FREE_'+motion);rg,r,rl,rr=fields(rd);g,h,L,cr=fields(cd);T=h['time_ms'];mask=(T>=r['time_ms'][0])&(T<=r['time_ms'][-1]);T=T[mask];reference=np.column_stack([np.interp(T,r['time_ms'],rl[:,a]) for a in range(3)]);diff=L[mask]-reference
    ids=np.asarray(g['clip_node_ids'])-1;q=np.asarray(g['nodes_mm'])[ids];v=np.asarray(g['initial_velocity_m_s'])[ids];m=np.asarray(g['clip_known_nodal_masses_g']);known=np.sum(m[:,None]*np.cross(q,v),axis=0)*1e-6;err=float(np.linalg.norm(diff-known,axis=1).max());tol=.02*np.linalg.norm(known)+1e-9;expected=float(.5*np.sum(m[:,None]*v**2)*.001);ke=float(h['KE_J'][0]-r['KE_J'][0]);ktol=.002*expected+1e-7
    checks={'reference_L':rr['pass'],'connected_L':cr['pass'],'added_physical_L':err<tol,'added_initial_KE':abs(ke-expected)<ktol,'native_connected_gates':read(cd/'review.json')['pass'],'reference_native_gates':read(rd/'review.json')['pass'],'zero_initial_projection':g['initial_projection_distance_mm']<1e-8};checks={k:bool(v) for k,v in checks.items()}
    return {'motion':motion,'reference':rr,'connected':cr,'known_added_L_kg_m2_s':known.tolist(),'maximum_added_L_error_kg_m2_s':err,'added_L_limit_kg_m2_s':float(tol),'known_added_initial_KE_J':expected,'native_added_initial_KE_J':ke,'checks':checks,'pass':all(checks.values())}

def main():
    guard();dest=OUT/'coupling_review.json';assert not dest.exists();rows=[pair('ROTATION_'+a) for a in 'XYZ']+[pair('TRANSLATION')];half=pair('ROTATION_Y_HALF');g,h,L,r=fields(OUT/'w0/CONNECTED_FREE_ROTATION_Y');g2,h2,L2,r2=fields(OUT/'w0/CONNECTED_FREE_ROTATION_Y_HALF');mask=(h['time_ms']>=h2['time_ms'][0])&(h['time_ms']<=h2['time_ms'][-1]);T=h['time_ms'][mask];le=float(np.linalg.norm(L[mask]-np.column_stack([np.interp(T,h2['time_ms'],L2[:,a]) for a in range(3)]),axis=1).max());ee=float(abs(h['total_J'][mask]-np.interp(T,h2['time_ms'],h2['total_J'])).max());ratio=float(np.median(h2['time_step_ms'][1:])/np.median(h['time_step_ms'][1:]));refine={'actual_dt_ratio':ratio,'maximum_L_difference_kg_m2_s':le,'maximum_energy_difference_J':ee,'checks':{'actually_shorter':ratio<.6,'L_converges':bool(le<.002*np.linalg.norm(L[0])+1e-9),'energy_converges':bool(ee<.002*h['total_J'][0]+1e-7),'both_Y_pairs':rows[1]['pass'] and half['pass']}}
    ext=[read(OUT/'w0'/f'CONNECTED_EXTENSION_N{n}'/'review.json') for n in [4,8]];mesh=abs(ext[1]['last_clip_IE_J']-ext[0]['last_clip_IE_J'])/ext[1]['last_clip_IE_J'];checks={'primary_pairs':all(r['pass'] for r in rows),'time_refinement':all(refine['checks'].values()),'elastic_reference':all(r['pass'] for r in ext),'elastic_mesh':mesh<.05}
    dump(dest,{'created_utc':now(),'pairs':rows,'half_pair':half,'refinement':refine,'elastic':ext,'elastic_mesh_difference':mesh,'checks':checks,'flat_fixture_pass':all(checks.values()),'whole_insertion_ready':False,'actual_geometry_not_qualified':True,'physical_strength_and_fracture_qualified':False,'objective1_complete':False,'native_RKE_not_modified':True,'thresholds_same_as_A24':True});print({'A25_flat_controls':checks,'pass':all(checks.values())},flush=True)

if __name__=='__main__':main()
