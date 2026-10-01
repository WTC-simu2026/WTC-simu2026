"""Nodal finite-volume heat equation with boundary half-volume storage."""
import numpy as np
import v11k_surface_exchange_model as reference


def grid(config,intervals):
    length=config['geometry']['thickness_m']; x=np.linspace(0.,length,intervals+1)
    widths=np.full(intervals+1,length/intervals); widths[[0,-1]]*=.5
    return x,widths


def profile_moments(x,temperature,reference_temperature=20.):
    t=temperature-reference_temperature; eta=x/x[-1]-.5; d=np.diff(eta)
    mean=float(np.sum(d*(t[:-1]+t[1:])/2))
    first=float(np.sum(d*((2*eta[:-1]+eta[1:])*t[:-1]+(eta[:-1]+2*eta[1:])*t[1:])/6))
    square=float(np.sum(d*(t[:-1]**2+t[:-1]*t[1:]+t[1:]**2)/3))
    return mean,first,square


def fluxes(temp,config,case,dx):
    k=config['constant_properties']['conductivity_w_m_k']
    faces=[reference.environment_flux_w_m2(float(temp[i]),case[side+'_boundary'],config['surface_exchange'])
           for i,side in [(0,'bottom'),(-1,'top')]]
    inside=k*np.diff(temp)/dx  # Positive from upper to lower x.
    net=np.r_[faces[0][2]+inside[0],np.diff(inside),faces[1][2]-inside[-1]]
    return faces,inside,net


def step(old,dt,config,case,widths):
    cpv=config['constant_properties']['volumetric_heat_capacity_j_m3_k']; dx=2*widths[0]
    g=config['constant_properties']['conductivity_w_m_k']/dx
    diagonal=cpv*widths/dt+2*g; diagonal[[0,-1]]-=g
    off=np.full(len(old)-1,-g); temp=old.copy()
    for iteration in range(1,13):
        faces,inside,net=fluxes(temp,config,case,dx)
        residual=cpv*widths*(temp-old)/dt-net
        error=float(np.max(abs(residual)))
        if error<=1e-7: return temp,{'iterations':iteration,'residual_w_m2':error}
        jac=diagonal.copy(); jac[0]+=faces[0][3]; jac[-1]+=faces[1][3]
        increment=reference.solve_tridiagonal(off,jac,off,-residual)
        temp+=increment
        if not np.isfinite(temp).all() or min(temp)<=-273.15: raise ArithmeticError('Nonphysical Newton trial')
    raise ArithmeticError('Nodal Newton did not converge: '+str(error))


def run(config,case,intervals,steps):
    x,widths=grid(config,intervals); dx=x[1]-x[0]; dt=case['duration_s']/steps
    properties=config['constant_properties']; cpv=properties['volumetric_heat_capacity_j_m3_k']
    temp=reference.initial_temperature(config,case,x)
    initial=temp.copy(); H0=float(cpv*widths@(temp-20)); cumulative=np.zeros(4)
    profiles=[]; history=[]; max_local=max_increment=max_total=0.; max_newton=0
    def record(index,old=None):
        nonlocal max_local,max_increment,max_total
        faces,inside,net=fluxes(temp,config,case,dx)
        components=np.array([faces[0][0],faces[0][1],faces[1][0],faces[1][1]])
        H=float(cpv*widths@(temp-20))
        storage=net if old is None else cpv*widths*(temp-old)/dt
        local=float(np.max(abs(storage-net)))
        if old is not None:
            previous_H=float(cpv*widths@(old-20)); max_increment=max(max_increment,abs(H-previous_H-dt*sum(components)))
            max_local=max(max_local,local)
        max_total=max(max_total,abs(H-H0-sum(cumulative)))
        mean,first,square=profile_moments(x,temp)
        history.append({'step':index,'time_s':index*dt,'enthalpy_j_m2':H,'enthalpy_change_j_m2':H-H0,
                        'cumulative_components_j_m2':cumulative.tolist(),'cumulative_inward_heat_j_m2':float(sum(cumulative)),
                        'bottom_surface_temperature_c':float(temp[0]),'top_surface_temperature_c':float(temp[-1]),
                        'inward_components_w_m2':components.tolist(),
                        'bottom_inside_conduction_w_m2':float(-inside[0]),'top_inside_conduction_w_m2':float(inside[-1]),
                        'bottom_storage_w_m2':float(storage[0]),'top_storage_w_m2':float(storage[-1]),
                        'storage_rate_kind':'INITIAL_SEMIDISCRETE_RHS' if old is None else 'BACKWARD_EULER_INCREMENT',
                        'bottom_temperature_rate_k_s':float(storage[0]/(cpv*widths[0])),
                        'top_temperature_rate_k_s':float(storage[-1]/(cpv*widths[-1])),
                        'local_balance_max_w_m2':local,'mean_delta_k':mean,'first_moment_eta_k':first,
                        'mean_square_delta_k2':square,'minimum_temperature_c':float(min(temp)),'maximum_temperature_c':float(max(temp))})
        profiles.append({'step':index,'time_s':index*dt,'temperature_c':temp.tolist()})
    record(0)
    for i in range(1,steps+1):
        previous=temp; temp,diagnostic=step(previous,dt,config,case,widths)
        max_newton=max(max_newton,diagnostic['iterations'])
        faces,_,_=fluxes(temp,config,case,dx)
        cumulative+=dt*np.array([faces[0][0],faces[0][1],faces[1][0],faces[1][1]])
        record(i,previous)
    return {'summary':{'case':case['id'],'intervals':intervals,'nodes':intervals+1,'steps':steps,'dt_s':dt,
                      'duration_s':case['duration_s'],'total_width_m':float(sum(widths)),
                      'mass_kg_m2':float(properties['density_kg_m3']*sum(widths)),
                      'heat_capacity_j_m2_k':float(cpv*sum(widths)),
                      'maximum_local_balance_w_m2':max_local,'maximum_increment_heat_error_j_m2':max_increment,
                      'maximum_total_heat_error_j_m2':max_total,'maximum_newton_iterations':max_newton,
                      'initial':history[0],'final':history[-1]},
            'case':case,'x_m':x.tolist(),'control_width_m':widths.tolist(),'profiles':profiles,'history':history}


def exact_linear_semidiscrete(config,case,intervals):
    """Convection-only nodal operator, symmetric capacity-weighted exponential."""
    x,widths=grid(config,intervals); dx=x[1]-x[0]
    cpv=config['constant_properties']['volumetric_heat_capacity_j_m3_k']; C=cpv*widths
    g=config['constant_properties']['conductivity_w_m_k']/dx
    diagonal=np.full(intervals+1,2*g); diagonal[[0,-1]]-=g
    for i,side in [(0,'bottom'),(-1,'top')]:
        b=case[side+'_boundary']
        if b['emissivity']!=0: raise ValueError('Linear reference requires zero radiation')
        diagonal[i]+=b['h_w_m2_k']
    A=np.diag(diagonal)+np.diag(np.full(intervals,-g),1)+np.diag(np.full(intervals,-g),-1)
    sqrtC=np.sqrt(C); operator=A/sqrtC[:,None]/sqrtC[None,:]
    rates,vectors=np.linalg.eigh(operator)
    ambient=case['initial']['ambient_temperature_c']; initial=reference.initial_temperature(config,case,x)
    final=ambient+(vectors@(np.exp(-rates*case['duration_s'])*(vectors.T@(sqrtC*(initial-ambient)))))/sqrtC
    exact=reference.analytical_temperature_c(config,case,x,case['duration_s'])
    return {'intervals':intervals,'x_m':x.tolist(),'initial_temperature_c':initial.tolist(),
            'semidiscrete_terminal_c':final.tolist(),'continuous_terminal_c':exact.tolist(),
            'linf_spatial_error_k':float(np.max(abs(final-exact))),
            'lowest_decay_rate_per_s':float(min(rates))}
