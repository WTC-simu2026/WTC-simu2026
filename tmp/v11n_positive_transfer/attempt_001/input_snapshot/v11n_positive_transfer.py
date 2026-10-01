"""Proposed positive bounded remap. No panel evolution or material-history edits."""
import numpy as np


class Incompatible(ValueError):
    def __init__(self,reason,**evidence):
        super().__init__(reason)
        self.evidence={'reason':reason,**evidence,'committed':False}


def moments(x,t):
    h=x[-1]-x[0]; eta=(x-(x[0]+x[-1])/2)/h
    a,b=eta[:-1],eta[1:]; ta,tb=t[:-1],t[1:]
    return float(np.sum((b-a)*(ta+tb)/2)),float(np.sum((b-a)*((2*a+b)*ta+(a+2*b)*tb)/6))


def reconstruct(centres,values,faces,mode):
    centres,values,faces=map(lambda v:np.array(v,dtype=float),(centres,values,faces))
    if not all(np.isfinite(v).all() for v in (centres,values,faces)): raise ValueError('Nonfinite input')
    if min(values)<0 or min(faces)<0: raise Incompatible('negative_source_increment')
    n=len(values); h=2*centres[0]*n; dx=h/n
    if mode=='legacy_mean_scaled':
        x=np.r_[0.,centres,h]
        t=np.r_[1.5*values[0]-.5*values[1],values,1.5*values[-1]-.5*values[-2]]
        m0,_=moments(x,t)
        if abs(m0)>1e-14: t*=float(np.mean(values))/m0
        return x,t
    if mode!='surface_cell_conservative': raise ValueError(mode)
    inner=np.minimum((values[:-1]+values[1:])/2,2*np.minimum(values[:-1],values[1:]))
    boundary=np.r_[faces[0],inner,faces[1]]
    xx=[0.]; tt=[float(boundary[0])]
    for i,c in enumerate(values):
        a,b=boundary[i:i+2]; left,right=i*dx,(i+1)*dx
        if c==0 and max(a,b)>0:
            raise Incompatible('zero_cell_mean_positive_face',cell=i,mean_k=float(c),face_values_k=[float(a),float(b)])
        if abs(c-(a+b)/2)<=4*np.finfo(float).eps*max(c,a,b,1e-300):
            xx.append(right); tt.append(float(b)); continue
        r=min(.25,c/(a+b)) if a+b>0 else .25
        p=(c-r*(a+b)/2)/(1-r)
        if r<=0 or left+r*dx<=left or right-r*dx>=right:
            raise Incompatible('unresolved_shoulder_coordinate',cell=i,shoulder_fraction=float(r))
        xx.extend([left+r*dx,right-r*dx,right]); tt.extend([float(p),float(p),float(b)])
    x,t=np.array(xx),np.array(tt)
    if np.any(np.diff(x)<=0) or min(t)<0: raise ArithmeticError('Invalid positive reconstruction')
    return x,t


def project(x,t,n,tolerance=1e-14):
    h=x[-1]-x[0]; eta=(np.arange(n)+.5)/n-.5
    raw=np.interp((eta+.5)*h,x,t); m0,m1=moments(x,t); inertia=float(np.mean(eta**2))
    if min(raw)<0: raise Incompatible('negative_reconstructed_sample',minimum_k=float(min(raw)))
    if m0==0:
        return np.zeros(n),{'beta':0.,'target_centroid_eta':None,'support_eta':None,
                            'absolute_first_moment_discrepancy_k':0.,'maximum_change_k':0.}
    active=raw>0
    if not np.any(active): raise Incompatible('positive_heat_without_sampled_support',mean_k=m0)
    target=12*m1*inertia/m0
    support=[float(min(eta[active])),float(max(eta[active]))]
    if target<support[0] or target>support[1]:
        raise Incompatible('target_outside_positive_fiber_support',target_centroid_eta=target,support_eta=support)
    ea=eta[active]; logs=np.log(raw[active])
    def weights(beta):
        logits=logs+beta*(ea-target); weights=np.exp(logits-np.max(logits)); weights/=sum(weights)
        return weights
    if abs(float(np.mean(raw))-m0)<1e-13 and abs(float(np.mean(eta*raw))-12*m1*inertia)<1e-14:
        result=raw.copy(); beta=0.
    else:
        lo,hi=-1.,1.
        for _ in range(80):
            if float(weights(lo)@ea)<=target<=float(weights(hi)@ea): break
            lo*=2; hi*=2
        else: raise Incompatible('centroid_root_not_bracketed',target_centroid_eta=target,support_eta=support)
        for _ in range(100):
            beta=(lo+hi)/2; w=weights(beta); centroid=float(w@ea)
            if abs(centroid-target)<=tolerance: break
            if centroid<target: lo=beta
            else: hi=beta
        else: raise ArithmeticError('Projection centroid solve did not converge')
        result=np.zeros(n); result[active]=n*m0*w
    return result,{'beta':float(beta),'target_centroid_eta':float(target),'support_eta':support,
                   'absolute_first_moment_discrepancy_k':float(np.mean(eta*result)-m1),
                   'maximum_change_k':float(np.max(abs(result-raw)))}


def section_response(section,delta,mode):
    thermal=section.alpha*delta; force=section.B.T@(section.EA*thermal)
    q=np.linalg.solve(section.K,force) if mode=='FREE' else np.zeros(2)
    strain=section.B@q-thermal; stress=section.E*strain
    resultant=section.B.T@(section.area*stress)
    return {'q':q.tolist(),'delta_k':delta.tolist(),'stress_pa':stress.tolist(),
            'resultant_N_Nm':resultant.tolist(),'support_reaction_N_Nm':(-resultant if mode=='FULLY_RESTRAINED' else np.zeros(2)).tolist(),
            'stored_J_per_m':float(.5*np.sum(section.area*stress*strain)),
            'sensible_J_per_m':float(np.sum(section.area*section.density*section.cp*delta))}
