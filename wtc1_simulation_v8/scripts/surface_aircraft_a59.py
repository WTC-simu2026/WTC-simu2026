"""Owned area-based prototype: planar interface, elastic and pure-mode bilinear response.

This is not a complete LAW117 implementation or an Engine integration. Mixed-mode
damage, rate dependence, moving frames and Newton state rollback are unqualified.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import numpy as np

def shapes():
    g=1/np.sqrt(3)
    return np.asarray([[(1-x)*(1-y),(1+x)*(1-y),(1+x)*(1+y),(1-x)*(1+y)] for x in [-g,g] for y in [-g,g]])/4

def point(q,previous_peak,K,T,G):
    d0=T/K;df=2*G/T;p=max(previous_peak,max(q,0))
    D=0 if p<=d0 else (1 if p>=df else df*(p-d0)/(p*(df-d0)))
    traction=(1-D)*K*q
    tangent=(1-D)*K
    if q>previous_peak and d0<q<df:tangent=-T/(df-d0)
    return traction,tangent,p,D

def kernel(displacement,L,mode,previous_peaks,parameters,rotation=None):
    R=np.eye(3) if rotation is None else np.asarray(rotation)
    assert displacement.shape==(8,3) and np.allclose(R.T@R,np.eye(3),atol=1e-12)
    local=displacement@R
    F=np.zeros((8,3));Knode=np.zeros((24,24));peaks=[];damage=[]
    stiffness=np.array([parameters['ET_N_mm3'],parameters['ET_N_mm3'],parameters['EN_N_mm3']])
    strength=parameters['TN_MPa'] if mode==2 else parameters['TT_MPa'];G=parameters['GI_N_mm'] if mode==2 else parameters['GII_N_mm']
    for j,N in enumerate(shapes()):
        q=N@(local[4:]-local[:4]);tr,tan,p,D=point(q[mode],previous_peaks[j],stiffness[mode],strength,G)
        t=(1-D)*stiffness*q;t[mode]=tr
        C=np.diag((1-D)*stiffness);C[mode,mode]=tan
        # Passive off-axis stiffness holds this pure-mode damage fixed. It does
        # not claim a mixed-mode damage derivative or complete coupled law.
        B=np.hstack([-n*np.eye(3) for n in N]+[n*np.eye(3) for n in N])
        w=L*L/4;F+=(B.T@t*w).reshape(8,3);Knode+=B.T@C@B*w;peaks.append(p);damage.append(D)
    F=F@R.T;Q=np.kron(np.eye(8),R);Knode=Q@Knode@Q.T
    return F,Knode,np.asarray(peaks),np.asarray(damage)

def validate(configuration,output):
    from pathlib import Path
    import json,hashlib,time
    start=time.perf_counter();cfg=json.loads(Path(configuration).read_text(encoding='utf8'));p=cfg['cohesive'];root=Path(cfg['workspace']);out=Path(output);checks=[]
    def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
    exact_mass=np.array([[4,2,1,2],[2,4,2,1],[1,2,4,2],[2,1,2,4]],float)/36
    sample=[]
    for L in [10.,20.]:
        for mode in [0,2]:
            for q,peak,label in [(0.01,0,'elastic'),(.15 if mode==2 else .4,.02,'softening'),(.05,.16 if mode==2 else .5,'unloading'),(.3 if mode==2 else 1.1,.28 if mode==2 else 1.05,'failed')]:
                u=np.zeros((8,3));u[4:,mode]=q;history=np.full(4,peak);F,K,_,D=kernel(u,L,mode,history,p)
                check(f'equilibrium_{L}_{mode}_{label}',np.linalg.norm(F.sum(axis=0))<1e-8)
                eps=1e-7;indices=np.arange(mode,24,3);fd=np.zeros((8,8))
                for j,index in enumerate(indices):
                    plus=u.copy().reshape(-1);minus=plus.copy();plus[index]+=eps;minus[index]-=eps
                    f1=kernel(plus.reshape(8,3),L,mode,history,p)[0];f2=kernel(minus.reshape(8,3),L,mode,history,p)[0];fd[:,j]=(f1[:,mode]-f2[:,mode])/(2*eps)
                relative=np.max(abs(fd-K[np.ix_(indices,indices)]))/max(1,np.max(abs(K)))
                check(f'active_pure_mode_tangent_FD_{L}_{mode}_{label}',relative<1e-7,float(relative))
                check(f'translation_null_{L}_{mode}_{label}',np.max(abs(K@np.tile([1.3,-.7,2.1],8)))<1e-7)
                if label=='elastic':
                    expected=np.zeros((24,24));diag=np.diag([p['ET_N_mm3'],p['ET_N_mm3'],p['EN_N_mm3']])
                    for a in range(8):
                        for b in range(8):expected[3*a:3*a+3,3*b:3*b+3]=(-1 if (a<4)!=(b<4) else 1)*L*L*exact_mass[a%4,b%4]*diag
                    check(f'closed_integral_mass_matrix_{L}_{mode}',np.max(abs(K-expected))<1e-8)
                    check(f'elastic_rank12_{L}_{mode}',np.linalg.matrix_rank(K,tol=1e-6)==12)
                    check(f'elastic_nonnegative_spectrum_{L}_{mode}',np.linalg.eigvalsh(K).min()>-1e-7)
                if label=='softening':check(f'negative_active_softening_tangent_{L}_{mode}',np.linalg.eigvalsh(K).min()<0)
                R=np.array([[0,-1,0],[1,0,0],[0,0,1]],float);FR,KR,_,_=kernel(u@R.T,L,mode,history,p,R);Q=np.kron(np.eye(8),R)
                check(f'rotation_covariance_{L}_{mode}_{label}',np.allclose(FR,F@R.T,rtol=1e-12,atol=1e-8) and np.allclose(KR,Q@K@Q.T,rtol=1e-12,atol=1e-8))
                sample.append({'L_mm':L,'mode_axis':mode,'state':label,'opening_mm':q,'damage':D.tolist(),'maximum_force_N':float(abs(F).max())})
    comparison=[]
    for row in cfg['cached_native_diagnostics']:
        path=root/row['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'];z=np.load(path)
        case=row['case'];mode=2 if case['mode']=='Z' else 0;L=case['L_mm'];K=p['EN_N_mm3'] if mode==2 else p['ET_N_mm3'];T=p['TN_MPa'] if mode==2 else p['TT_MPa'];G=p['GI_N_mm'] if mode==2 else p['GII_N_mm']
        q=z['opening_mm'];history=0;force=[];damage=[]
        for value in q:
            tr,_,history,D=point(float(value),history,K,T,G);force.append(tr*L*L);damage.append(D)
        force=np.asarray(force);damage=np.asarray(damage);native=z['native_reaction_force_N'];relative=float(abs(force-native).max()/(T*L*L))
        work=float(np.sum((force[1:]+force[:-1])*.5*np.diff(q))*.001);target=G*L*L*.001
        check('cached_native_traction_'+case['id'],relative<=cfg['acceptance']['traction_maximum_relative'],relative)
        check('full_separation_work_'+case['id'],abs(work-target)<=cfg['acceptance']['work_energy_fraction']*target+cfg['acceptance']['absolute_energy_J'],{'work_J':work,'target_J':target})
        check('irreversible_damage_'+case['id'],np.all(np.diff(damage)>=-1e-12))
        comparison.append({'case':case,'maximum_traction_relative_error':relative,'integrated_work_J':work,'target_work_J':target,'cached_native_no_rerun':True})
    result={'created_epoch':time.time(),'wall_s':time.perf_counter()-start,'checks':checks,'pass':all(c['pass'] for c in checks),'sample_states':sample,'cached_native_comparisons':comparison,'scope':'Planar reference-frame area kernel; pure normal/shear linear softening, elastic three-axis matrix. Active pure-mode tangent only.','mixed_mode_damage_qualified':False,'moving_frames_and_geometric_tangent_qualified':False,'Newton_state_commit_rollback_qualified':False,'compiled_Engine_integration_ready':False,'whole_impact_qualified':False,'new_whole_physical_duration_credit_s':0}
    assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8');print(json.dumps({'prototype_pass':result['pass'],'checks':len(checks),'failed':[r['name'] for r in checks if not r['pass']]}),flush=True)

if __name__=='__main__':
    import sys
    validate(sys.argv[1],sys.argv[2])
