"""Reproduce cached error locations; no new native run or qualification gate."""
from run_aircraft_a33 import *

def main():
    guard();rows=[]
    for cid in ['FACE_BENDING_N12_Z2','FACE_BENDING_N24_Z2','FACE_BENDING_N24_Z4']:
        d=OUT/'w1'/cid;g=read(d/'generation.json');X=np.asarray(g['nodes_mm']);H=np.load(d/'histories_SI.npz');t=H['time_ms'][-1]/.1;s=3*t*t-2*t*t*t;U=H['positions_mm'][-1]-X;R=reference_nodes(X)*s;free=np.flatnonzero(abs(X[:,2])<.25);err=abs(U[free]-R[free]);node,axis=np.unravel_index(np.argmax(err),err.shape);ni=int(free[node]);rows.append({'case':cid,'worst_node_id':ni+1,'coordinate_mm':X[ni].tolist(),'axis':'XYZ'[axis],'native_displacement_mm':float(U[ni,axis]),'reference_displacement_mm':float(R[ni,axis]),'error_mm':float(err[node,axis]),'diagnostic_only':True})
    p=OUT/'interior_error_location_diagnostic.json'
    if p.exists():assert read(p)['cases']==rows
    else:dump(p,{'created_utc':now(),'cases':rows,'acceptance_unchanged':True,'native_fields_not_refitted':True})
    dump(OUT/'interior_location_reproducibility.json',{'created_utc':now(),'script':rel(Path(__file__)),'script_sha256':streamsha(Path(__file__)),'cache_reanalysis_only':True,'original_diagnostic_reproduced':True,'original_file_unchanged':True})

if __name__=='__main__':main()
