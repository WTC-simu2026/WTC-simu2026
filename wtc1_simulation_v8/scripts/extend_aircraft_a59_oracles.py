"""Resolve arbitrary 3D frame and reload-work concerns without replaying a solver."""
from prepare_aircraft_a59_surface import ROOT,OUT,CFG,read,dump,now
from surface_aircraft_a59 import kernel,point
import numpy as np,json

def main():
    c=read(CFG);p=c['cohesive'];assert read(OUT/'surface_prototype_review.json')['pass']
    a=np.array([1.,2.,-3.]);a/=np.linalg.norm(a);theta=.63;cross=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    R=np.eye(3)*np.cos(theta)+(1-np.cos(theta))*np.outer(a,a)+np.sin(theta)*cross;Q=np.kron(np.eye(8),R);checks=[]
    for L in [10.,20.]:
        for mode in [0,2]:
            for q,peak,name in [(.01,0,'elastic'),(.15 if mode==2 else .4,.02,'softening'),(.05,.16 if mode==2 else .5,'unloading')]:
                u=np.zeros((8,3));u[4:,mode]=q;history=np.full(4,peak);F,K,_,_=kernel(u,L,mode,history,p);FR,KR,_,_=kernel(u@R.T,L,mode,history,p,R)
                checks.append({'name':f'arbitrary_3D_frame_{L}_{mode}_{name}','pass':bool(np.allclose(FR,F@R.T,rtol=1e-12,atol=1e-8) and np.allclose(KR,Q@K@Q.T,rtol=1e-12,atol=1e-8))})
    for row in c['cached_native_diagnostics']:
        z=np.load(ROOT/row['path']);case=row['case'];normal=case['mode']=='Z';K=p['EN_N_mm3'] if normal else p['ET_N_mm3'];T=p['TN_MPa'] if normal else p['TT_MPa'];G=p['GI_N_mm'] if normal else p['GII_N_mm'];A=case['L_mm']**2
        q=z['opening_mm'];peak=0;forces=[]
        for value in q:
            traction,_,peak,_=point(float(value),peak,K,T,G);forces.append(traction*A)
        f=np.asarray(forces);work=np.r_[0,np.cumsum((f[1:]+f[:-1])*.5*np.diff(q))]*.001;target=G*A*.001
        reload=float(abs(np.interp(.00075,z['time_s'],work)-np.interp(.00025,z['time_s'],work))/target)
        error=float(abs(work-z['native_internal_J']).max())
        checks.append({'name':'same_peak_reload_work_'+case['id'],'pass':reload<=c['acceptance']['equal_peak_energy_fraction'],'difference_fraction':reload})
        checks.append({'name':'complete_cached_native_internal_work_curve_'+case['id'],'pass':error<=c['acceptance']['work_energy_fraction']*target+c['acceptance']['absolute_energy_J'],'maximum_error_J':error})
    assert len(checks)==20
    result={'created_utc':now(),'checks':checks,'pass':all(v['pass'] for v in checks),'additional_question':'Arbitrary 3D reference-frame covariance and full reload work, beyond the initial single-axis rotation and final-work check.','native_solver_replays':0,'physical_tolerances_changed':False,'whole_transfer_or_mixed_mode_qualified':False}
    dump(OUT/'additional_oracle_review.json',result);print(json.dumps({'additional_checks':20,'pass':result['pass'],'failed':[v['name'] for v in checks if not v['pass']]}),flush=True)

if __name__=='__main__':main()
