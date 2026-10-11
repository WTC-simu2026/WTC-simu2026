"""Independent conventional 3D elasticity with heterogeneous orthotropic tensors.

No native solver stiffness or measured response enters this calculation.
Matrix-free preconditioned CG avoids modifying the installed software.
"""
import numpy as np
import time
SIGNS=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]])

def assemble(xyz,bricks,parts,Cskin,Ccore):
    ids=np.asarray(bricks,dtype=int)-1;X=np.asarray(xyz)[ids];dofs=(3*ids[:,:,None]+np.arange(3)).reshape(-1,24);K=np.zeros((len(ids),24,24));C=np.where((np.asarray(parts)==28)[:,None,None],Ccore,Cskin);detmin=1e100
    for r in [-1/np.sqrt(3),1/np.sqrt(3)]:
        for s in [-1/np.sqrt(3),1/np.sqrt(3)]:
            for t in [-1/np.sqrt(3),1/np.sqrt(3)]:
                p=np.array([r,s,t]);dN=np.column_stack([SIGNS[:,a]*np.prod(1+SIGNS[:,[q for q in range(3) if q!=a]]*p[[q for q in range(3) if q!=a]],axis=1)/8 for a in range(3)]);J=np.einsum('eji,jk->eik',X,dN);det=np.linalg.det(J);assert np.all(det>0);detmin=min(detmin,float(det.min()));grad=np.einsum('ij,ejk->eik',dN,np.linalg.inv(J));B=np.zeros((len(ids),6,24))
                for j in range(8):
                    x,y,z=grad[:,j,:].T;B[:,0,3*j]=x;B[:,1,3*j+1]=y;B[:,2,3*j+2]=z;B[:,3,3*j]=y;B[:,3,3*j+1]=x;B[:,4,3*j+1]=z;B[:,4,3*j+2]=y;B[:,5,3*j]=z;B[:,5,3*j+2]=x
                K+=np.einsum('eji,ejk,ekl,e->eil',B,C,B,det,optimize=True)
    diag=np.bincount(dofs.ravel(),weights=np.diagonal(K,axis1=1,axis2=2).ravel(),minlength=3*len(xyz));assert np.all(diag>0)
    return K,dofs,diag,{'minimum_positive_Jacobian_mm3':detmin,'maximum_element_asymmetry':float(abs(K-K.transpose(0,2,1)).max())}

def solve(xyz,bricks,parts,Cskin,Ccore,bottom,top,axis,displacement,cached=None):
    start=time.perf_counter();K,dofs,diag,assembly=cached if cached is not None else assemble(xyz,bricks,parts,Cskin,Ccore);nd=3*len(xyz);fixed=(3*(np.asarray(bottom+top)-1)[:,None]+np.arange(3)).ravel();free=np.setdiff1d(np.arange(nd),fixed);u=np.zeros(nd);u[3*(np.asarray(top)-1)+axis]=displacement
    def mul(v):return np.bincount(dofs.ravel(),weights=np.einsum('eij,ej->ei',K,v[dofs],optimize=False).ravel(),minlength=nd)
    b=-mul(u)[free];scale=float(np.linalg.norm(b));x=np.zeros(len(free));r=b.copy();z=r/diag[free];p=z.copy();rz=float(r@z);iterations=0
    for iterations in range(1,12001):
        full=np.zeros(nd);full[free]=p;Ap=mul(full)[free];den=float(p@Ap);assert den>0,'Non-positive independent stiffness';alpha=rz/den;x+=alpha*p;r-=alpha*Ap
        if np.linalg.norm(r)<1e-10*scale+1e-11:break
        z=r/diag[free];new=float(r@z);p=z+(new/rz)*p;rz=new
    else:raise AssertionError('Independent CG did not converge; no native reference accepted')
    u[free]=x;F=mul(u);norm=float(np.linalg.norm(F[free]));reaction=float(F[3*(np.asarray(top)-1)+axis].sum());energy=float(.5*u@F*.001);part_energy={int(pid):float(.5*np.einsum('ei,eij,ej->',u[dofs[np.asarray(parts)==pid]],K[np.asarray(parts)==pid],u[dofs[np.asarray(parts)==pid]],optimize=False)*.001) for pid in np.unique(parts)}
    checks={'equilibrium':norm<1e-8*scale+1e-8,'virtual_work':abs(energy-.5*displacement*reaction*.001)<1e-9*abs(energy)+1e-12,'positive_energy':energy>0,'element_symmetry':assembly['maximum_element_asymmetry']<1e-8,'part_energy_sum':abs(sum(part_energy.values())-energy)<1e-9*energy+1e-12};assert all(checks.values()),checks
    return {'energy_J':energy,'top_reaction_N':reaction,'part_energy_J':part_energy,'displacements_mm':u.reshape(-1,3).tolist(),'top_node_forces_N':F.reshape(-1,3)[np.asarray(top)-1].tolist(),'bottom_node_forces_N':F.reshape(-1,3)[np.asarray(bottom)-1].tolist(),'free_equilibrium_norm_N':norm,'CG_iterations':iterations,'seconds':time.perf_counter()-start,'assembly':assembly,'checks':checks,'pass':True,'method':'Independent small-strain heterogeneous 8-node elasticity,2x2x2Gauss; matrix-free Jacobi-preconditioned CG. Native HA8/Isolid18 may have a different discrete operator; compare with refinement, not fit.'}
