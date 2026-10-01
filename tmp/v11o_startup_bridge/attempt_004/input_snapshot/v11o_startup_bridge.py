"""Exact section-integral startup experiment; not a modified V11F panel."""
import numpy as np
import math
import v11n_positive_transfer as inherited


def moments3(x,t):
    m0,m1=inherited.moments(x,t)
    m2=float(np.sum(np.diff(x)*(t[:-1]**2+t[:-1]*t[1:]+t[1:]**2)/3)/(x[-1]-x[0]))
    return m0,m1,m2


class ContinuousSection:
    def __init__(self,fiber_section):
        s=fiber_section; self.h=s.h; self.width=s.width
        c=s.kind=='concrete'; steel=~c
        self.Ac=math.fsum(s.area[c]); self.Ec=float(s.E[c][0]); self.alphac=float(s.alpha[c][0])
        self.rhoc=float(s.density[c][0]); self.cpc=float(s.cp[c][0])
        self.ys=s.y[steel].copy(); self.As=s.area[steel].copy(); self.Es=s.E[steel].copy()
        self.alphas=s.alpha[steel].copy(); self.rhos=s.density[steel].copy(); self.cps=s.cp[steel].copy()
        self.Bs=np.column_stack([np.ones(len(self.ys)),-self.ys])
        # Assemble symmetric coefficients directly, with compensated scalar sums.
        # The same K is then the Hessian of stored energy and the force tangent.
        EA=self.Es*self.As; coupling=-math.fsum(EA*self.ys)
        self.K=np.array([[self.Ec*self.Ac+math.fsum(EA),coupling],
                         [coupling,self.Ec*self.Ac*self.h**2/12+math.fsum(EA*self.ys**2)]])
        self.ft=s.ft; self.fc=s.fc; self.fy=s.fy

    def inventory(self):
        return {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in vars(self).items()}

    def solve(self,x,t,face_delta,mode):
        m0,m1,m2=moments3(x,t); ts=np.interp(self.ys+self.h/2,x,t)
        f=self.Ec*self.Ac*self.alphac*np.array([m0,-self.h*m1])+self.Bs.T@(self.Es*self.As*self.alphas*ts)
        S=self.Ec*self.Ac*self.alphac**2*m2+float(np.sum(self.Es*self.As*(self.alphas*ts)**2))
        q=np.linalg.solve(self.K,f) if mode=='FREE' else np.zeros(2)
        resultant=self.K@q-f
        stored=float(.5*q@self.K@q-q@f+.5*S)
        yc=x-self.h/2; stress=self.Ec*(q[0]-yc*q[1]-self.alphac*t)
        stress_face=self.Ec*(q[0]-np.array([-self.h/2,self.h/2])*q[1]-self.alphac*face_delta)
        stress_s=self.Es*(self.Bs@q-self.alphas*ts)
        ratios=[max(0,float(max(np.r_[stress,stress_face])))/self.ft,
                max(0,float(max(-np.r_[stress,stress_face])))/self.fc,float(np.max(abs(stress_s),initial=0.))/self.fy]
        sensible=self.Ac*self.rhoc*self.cpc*m0+float(np.sum(self.As*self.rhos*self.cps*ts))
        return {'q':q.tolist(),'thermal_force_N_Nm':f.tolist(),'thermal_square_energy_S_J_per_m':S,
                'resultant_N_Nm':resultant.tolist(),'support_reaction_N_Nm':(-resultant if mode=='FULLY_RESTRAINED' else np.zeros(2)).tolist(),
                'stored_J_per_m':stored,'sensible_J_per_m':sensible,
                'composite_minus_gross_J_per_m':sensible-self.width*self.h*2160000*m0,
                'mean_delta_k':m0,'first_moment_eta_k':m1,'mean_square_delta_k2':m2,
                'steel_delta_k':ts.tolist(),'concrete_knot_stress_pa':stress.tolist(),
                'face_stress_pa':stress_face.tolist(),'steel_stress_pa':stress_s.tolist(),
                'cold_strength_ratios':ratios,'maximum_cold_strength_ratio':max(ratios)}


def bridge(saved,fraction,kind):
    p0,p1=saved['profiles'][:2]; h0,h1=saved['history'][:2]
    centres=np.array(p0['x_m']); h=2*centres[0]*len(centres)
    v1=np.array(p1['temperature_c'])-20
    f0=np.array([h0[side+'_surface_temperature_c']-20 for side in ('bottom','top')])
    f1=np.array([h1[side+'_surface_temperature_c']-20 for side in ('bottom','top')])
    if kind=='boundary_preserving_weak_limit':
        face=f0+fraction*(f1-f0)
        if fraction==0: x,t=np.array([0.,h]),np.zeros(2)
        else: x,t=inherited.reconstruct(centres,fraction*v1,face,'surface_cell_conservative')
    elif kind=='scaled_first_profile_control':
        x,t=inherited.reconstruct(centres,v1,f1,'surface_cell_conservative'); t=t*fraction; face=fraction*f1
    else: raise ValueError(kind)
    return x,t,face,{'fraction':float(fraction),'interpolated_coordinate_s':float(fraction*p1['time_s']),
        'resolved_new_thermal_time':False,'weak_zero_state':bool(fraction==0 and kind=='boundary_preserving_weak_limit'),
        'reference_algebraic_face_delta_k':(f0+fraction*(f1-f0)).tolist(),
        'face_departure_from_reference_k':(face-f0-fraction*(f1-f0)).tolist(),
        'expected_mean_delta_k':float(fraction*np.mean(v1)),
        'expected_inward_heat_j_m2':float(fraction*h1['cumulative_total_inward_heat_j_m2'])}
