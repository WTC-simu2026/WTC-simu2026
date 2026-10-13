"""New symmetric elastic iteration, full mixed residual, frozen committed state.

The iteration matrix is deliberately not called an exact material/geometric
Jacobian. Native integration and history staging remain acceptance gates.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
from prepare_aircraft_a61_surface_iteration import ROOT,OUT,CFG,guard,read,dump,sha,now
from material_aircraft_a60 import trial,State
import numpy as np,json

def shape():
    g=1/np.sqrt(3);a=(1+g)**2/4;b=(1-g*g)/4;c=(1-g)**2/4
    return np.array([[a,b,c,b],[b,a,b,c],[c,b,a,b],[b,c,b,a]])

def normal(nodes):
    P=.5*(nodes[:4]+nodes[4:]);r=P[1]+P[2]-P[0]-P[3];s=P[2]+P[3]-P[0]-P[1]
    n=np.cross(r,s);length=np.linalg.norm(n)
    if length==0:raise ValueError('degenerate surface')
    return n/length

def iteration_matrix(nodes,areas,p,active=None):
    H=shape();n=normal(nodes);areas=np.asarray(areas,float)
    if np.any(areas<=0):raise ValueError('nonpositive reference area')
    if active is None:active=np.ones(4)
    D=p['ET_N_mm3']*np.eye(3)+(p['EN_N_mm3']-p['ET_N_mm3'])*np.outer(n,n)
    b=np.concatenate([-H,H],axis=1);M=b.T@np.diag(areas*np.asarray(active))@b
    return np.kron(M,D)

def approximate_newton(target,start,base,p,limits):
    elastic=np.diag([p['ET_N_mm3'],p['ET_N_mm3'],p['EN_N_mm3']]);structural=4*elastic
    force=trial(target,base,p)[0]+structural@target;x=np.asarray(start,float).copy();trace=[]
    for i in range(limits['maximum_iterations']):
        traction,_,prospective,_=trial(x,base,p);residual=traction+structural@x-force
        trace.append({'iteration':i,'gap_mm':x.tolist(),'force_residual_N':float(np.linalg.norm(residual)),'committed_state':base.__dict__,'trial_state':prospective.__dict__})
        if np.linalg.norm(residual)<=limits['force_residual_absolute_N']:return x,prospective,trace,True
        x-=np.linalg.solve(elastic+structural,residual)
    return x,prospective,trace,False

def main():
    c=guard();p=c['cohesive'];lim=c['prototype'];checks=[];matrices=[];traces=[]
    for source in c['cached_sources']:assert sha(ROOT/source['path'])==source['sha256']
    def check(name,value,detail=None):checks.append({'name':name,'pass':bool(value),'detail':detail})
    base_nodes=np.array([[0,0,0],[10,0,0],[10,10,0],[0,10,0]]*2,float)
    angle=.73;axis=np.array([1,2,3])/np.sqrt(14);W=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
    R=np.eye(3)+np.sin(angle)*W+(1-np.cos(angle))*W@W;Q=np.kron(np.eye(8),R)
    for label,areas in [('uniform',[25]*4),('nonuniform',[10,12,15,18])]:
        K=iteration_matrix(base_nodes,areas,p);Kr=iteration_matrix(base_nodes@R.T+np.array([30,-12,41]),areas,p)
        check(label+'_symmetric',np.max(abs(K-K.T))<lim['matrix_relative_tolerance']*np.max(abs(K)))
        check(label+'_positive_semidefinite',np.linalg.eigvalsh(K).min()>-1e-10*np.max(abs(K)))
        check(label+'_rank12',np.linalg.matrix_rank(K,tol=1e-8)==12)
        for j in range(3):
            translation=np.tile(np.eye(3)[j],8);check(label+'_translation_null_'+str(j),np.linalg.norm(K@translation)<1e-8)
        check(label+'_current_frame_rotation_covariance',np.max(abs(Kr-Q@K@Q.T))<1e-10*np.max(abs(K)))
        target=np.tile([.02,-.03,.04],4);u=np.r_[np.zeros(12),target];reaction=(K@u).reshape(8,3).sum(axis=0)
        check(label+'_nodal_balance',np.linalg.norm(reaction)<1e-8)
        force=(K@u).reshape(8,3)[4:].sum(axis=0);exact=sum(areas)*np.array([p['ET_N_mm3']*.02,p['ET_N_mm3']*-.03,p['EN_N_mm3']*.04])
        check(label+'_uniform_gap_integrated_force',np.max(abs(force-exact))<1e-8)
        active=iteration_matrix(base_nodes,areas,p,[0,0,0,0]);check(label+'_all_deleted_GP_zero',np.all(active==0))
        # The blocks which ASSEM_KII/KIJ receive reconstruct the same full matrix.
        reconstructed=np.zeros_like(K)
        for a in range(8):
            for b in range(a,8):
                block=K[3*a:3*a+3,3*b:3*b+3];reconstructed[3*a:3*a+3,3*b:3*b+3]=block;reconstructed[3*b:3*b+3,3*a:3*a+3]=block.T
        check(label+'_triangular_block_reconstruction',np.max(abs(reconstructed-K))<=lim['matrix_relative_tolerance']*np.max(abs(K)))
        matrices.append({'label':label,'areas_mm2':areas,'rank':int(np.linalg.matrix_rank(K,tol=1e-8)),'minimum_eigenvalue':float(np.linalg.eigvalsh(K).min()),'blocks_N_mm':K.tolist()})
    H=shape();M=H.T@np.diag([25]*4)@H;closed=100/36*np.array([[4,2,1,2],[2,4,2,1],[1,2,4,2],[2,1,2,4]])
    check('native_shape_order_closed_integral',np.max(abs(M-closed))<1e-12)
    for label,nodes,areas in [('degenerate',np.zeros((8,3)),[25]*4),('negative_area',base_nodes,[-1,25,25,25])]:
        caught=False
        try:iteration_matrix(nodes,areas,p)
        except ValueError:caught=True
        check('invalid_geometry_rejected_'+label,caught)
    targets=[(np.array([.11,.08,.13]),State(),'mixed_loading'),(np.array([.04,.025,-.03]),State(.18,.6),'compression_after_damage'),(np.array([.1,.06,.07]),State(.22,.7),'unloading')]
    for target,base,label in targets:
        for start in [[0,0,0],[.4,.3,.45],[-.03,.02,.07]]:
            x,state,trace,ok=approximate_newton(target,start,base,p,lim);key=label+'_'+str(start)
            check('symmetric_iteration_same_full_residual_root_'+key,ok and np.linalg.norm(x-target)<lim['root_tolerance_mm'],{'iterations':len(trace),'root_error_mm':float(np.linalg.norm(x-target))})
            check('no_trial_state_commit_'+key,all(t['committed_state']==base.__dict__ for t in trace))
            traces.append({'case':key,'converged':ok,'trace':trace})
    # Demonstrate that this matrix is not mislabelled as an exact softening derivative.
    _,exact,_,_=trial([.11,.08,.13],State(),p);elastic=np.diag([p['ET_N_mm3'],p['ET_N_mm3'],p['EN_N_mm3']])
    check('approximate_matrix_distinct_from_exact_mixed_derivative',np.max(abs(exact-elastic))>1)
    result={'created_utc':now(),'checks':checks,'pass':all(r['pass'] for r in checks),'surface_matrices':matrices,'approximate_Newton_traces':traces,
      'full_residual_unchanged':True,'iteration_matrix_is_exact_Jacobian':False,'native_Engine_integration_qualified':False,'native_state_rollback_qualified':False,'new_Engine_or_Starter':0,'new_whole_duration_credit_s':0}
    dump(OUT/'symmetric_surface_iteration_review_R1.json',result)
    print(json.dumps({'checks':len(checks),'pass':result['pass'],'failed':[r['name'] for r in checks if not r['pass']]}),flush=True)
    assert result['pass']

if __name__=='__main__':main()
