"""Independent small-strain3D static stiffness for the finite clip, using conventional2x2x2 integration."""
import numpy as np

def solve(xyz,bricks,left,right,displacement=.004,E=73100.,nu=.33):
    n=len(xyz);K=np.zeros((3*n,3*n));lam=E*nu/((1+nu)*(1-2*nu));mu=E/(2*(1+nu));C=np.zeros((6,6));C[:3,:3]=lam;C[np.diag_indices(3)]+=2*mu;C[3:,3:]=np.eye(3)*mu
    signs=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])
    for conn in bricks:
        ids=np.asarray(conn)-1;X=xyz[ids];ke=np.zeros((24,24));dofs=(3*ids[:,None]+np.arange(3)).ravel()
        for r in [-1/np.sqrt(3),1/np.sqrt(3)]:
            for s in [-1/np.sqrt(3),1/np.sqrt(3)]:
                for t in [-1/np.sqrt(3),1/np.sqrt(3)]:
                    p=np.array([r,s,t]);dN=np.column_stack([signs[:,a]*np.prod(1+signs[:,[q for q in range(3) if q!=a]]*p[[q for q in range(3) if q!=a]],axis=1)/8 for a in range(3)]);J=X.T@dN;det=np.linalg.det(J);assert det>0;grad=dN@np.linalg.inv(J);B=np.zeros((6,24))
                    for j,(x,y,z) in enumerate(grad):B[:,3*j:3*j+3]=[[x,0,0],[0,y,0],[0,0,z],[y,x,0],[0,z,y],[z,0,x]]
                    ke+=B.T@C@B*det
        K[np.ix_(dofs,dofs)]+=ke
    u=np.zeros(3*n);fixed=np.array([3*(i-1)+a for i in left+right for a in range(3)]);u[[3*(i-1) for i in right]]=displacement;free=np.setdiff1d(np.arange(3*n),fixed);u[free]=np.linalg.solve(K[np.ix_(free,free)],-K[np.ix_(free,fixed)]@u[fixed]);F=K@u
    return {'energy_J':float(.5*u@F*.001),'reaction_N':float(sum(F[3*(i-1)] for i in right)),'displacements_mm':u.reshape(n,3).tolist(),'free_equilibrium_N':float(abs(F[free]).max()),'fixed_node_ids_left':left,'fixed_node_ids_right':right,'method':'independent linear isotropic small-strain static3D stiffness,8-node interpolation,2x2x2Gauss; compare to dynamic corotational HA8 native solver, not a native result fit','E_MPa':E,'nu':nu}
