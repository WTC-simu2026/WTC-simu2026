"""Cached node-ID association repair; no native rerun or changed threshold."""
from probe_aircraft_a35_mumps import *
OUT=build.OUT/'implicit_capability/w1_launcher'
def main():
 dest=OUT/'fresh_capability_review_after_node_id_recovery.json';assert not dest.exists();old=read(OUT/'fresh_capability_review.json');rows=[]
 for c in CASES:
  d=OUT/c['name'];H=histories(d/(read(d/'generation.json')['name']+'T01.csv'));g=read(d/'generation.json');T=H['time'];m=np.asarray(g['nodal_masses_g']);nk=[k for k in H if k.startswith('NATIVE_SCOPE_NODES')];fk=[k for k in H if k.startswith('PHYSICAL_FACE_REACTIONS')]
  nid=[int(re.match(r'NATIVE_SCOPE_NODES\s+(\d+)\s',k).group(1)) for k in nk];fid=[int(re.match(r'PHYSICAL_FACE_REACTIONS\s+(\d+)\s',k).group(1)) for k in fk]
  assert len(nid)==6*len(m) and len(fid)==3*len(g['boundary_nodes']);assert all(len(set(nid[i:i+6]))==1 for i in range(0,len(nid),6));assert all(len(set(fid[i:i+3]))==1 for i in range(0,len(fid),3));norder=nid[::6];forder=fid[::3];assert set(norder)==set(range(1,len(m)+1)) and set(forder)==set(g['boundary_nodes']);idx={ni:i for i,ni in enumerate(norder)}
  N=np.column_stack([H[k] for k in nk]).reshape(len(T),len(m),6);V=N[:,:,3:];P=np.sum(m[np.asarray(norder)-1][None,:,None]*V,axis=1)*.001;VF=V[:,[idx[i] for i in forder],:];Q=np.column_stack([H[k] for k in fk]).reshape(len(T),len(forder),3)
  def trap(y):return np.concatenate([np.zeros_like(y[:1]),np.cumsum((y[1:]+y[:-1])*.5*np.diff(T).reshape((-1,)+(1,)*(y.ndim-1)),axis=0)],axis=0)
  dp=P-P[0];ie=float(np.linalg.norm((Q.sum(axis=1)-Q[0].sum(axis=0))*.001-dp,axis=1).max());fe=float(np.linalg.norm(trap(Q.sum(axis=1))*.001-dp,axis=1).max());pt=.02*float(np.linalg.norm(dp,axis=1).max())+1e-9;imp=ie<pt;force=fe<pt;unique=imp!=force;W=None;we=None;EW=H['EXTERNAL WORK']*.001;wt=.02*max(float(abs(EW).max()),read(d/'reference_before_native.json')['energy_J'])+1e-7
  if unique:F=np.gradient(Q,T,axis=0,edge_order=2) if imp else Q;W=trap(np.sum(F*VF,axis=(1,2)))*.001;we=float(abs(W-EW).max())
  ck={'unique_reaction_interpretation':unique,'native_reaction_work':bool(unique and we<wt),'global_history_momentum_matches_nodes':bool(abs(P-np.column_stack([H[a+'-MOMENTUM'] for a in 'XYZ'])*.001).max()<pt)}
  r={'created_utc':now(),'case':c['name'],'parent':rel(d/'transfer_review.json'),'input_face_node_order':g['boundary_nodes'],'actual_native_face_node_order':forder,'actual_native_node_order':norder,'checks':ck,'pass':all(ck.values()),'raw_impulse_error_Ns':ie,'force_integral_error_Ns':fe,'tolerance_Ns':pt,'interpretation':'impulse' if imp and not force else 'force' if force and not imp else 'undetermined','boundary_work_error_J':we,'work_tolerance_J':wt,'undetermined_units_never_used_to_compute_work':not unique,'native_solver_reruns':0,'thresholds_unchanged':True};dump(d/'transfer_review_after_node_id_recovery.json',r);rows.append(r)
 old.update(created_utc=now(),parent=rel(OUT/'fresh_capability_review.json'),transfer=rows,native_scope_pass=all(r['native_scope_pass'] for r in old['cases']) and all(r['pass'] for r in rows) and all(r['pass'] for r in old['comparisons']),reader_recovery_only=True,old_results_preserved=True,native_solver_reruns=0);dump(dest,old);print({'cached_reaction_recovery':[(r['case'],r['checks']) for r in rows]},flush=True)
if __name__=='__main__':main()
