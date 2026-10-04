"""I: exact positive-gap H2 unloading reference, independent RK4 and quadrature.

Own numerical model, not a physical calibration. Mass in g, mm, ms, N;
N mm=mJ. History delta_max never reset or changed during unloading.
"""
from __future__ import annotations
import json,math,time,platform
import numpy as np
import run_impact_i02i_free_fracture as h

ROOT=h.ROOT
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_free_return'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_i_predeclaration.json'

def parameters(v0):
    old=json.loads((h.OUT/'reference_verification.json').read_text())['parameters']
    m,k,fp,df=old['moving_mass_g'],old['k_N_per_mm'],old['peak_N'],old['deltaf_mm']
    d0=fp/k;ks=fp/(df-d0);w=math.sqrt(k/m);lam=math.sqrt(ks/m);e0=.5*m*v0*v0
    p={'moving_mass_g':m,'fixed_mass_g':m,'k_N_per_mm':k,'peak_N':fp,'delta0_mm':d0,
       'deltaf_mm':df,'softening_N_per_mm':ks,'omega_rad_per_ms':w,'lambda_rad_per_ms':lam,
       'v0_mm_per_ms':v0,'initial_energy_J':e0*.001,'initial_momentum_N_ms':m*v0,
       'hypothetical_Gf_N_per_mm':30.,'area_mm2':1.,'domain':'fresh positive-gap trajectory; no compression or separation'}
    if e0<.5*k*d0*d0:
        p.update(family='NORMAL_SUBPEAK_RETURN',turning_gap_mm=v0/w,force_amplitude_N=k*v0/w,
            turn_time_ms=math.pi/(2*w),positive_domain_end_ms=math.pi/w,retained_work_J=0.,
            peak_time_ms=None,zero_force_time_ms=math.pi/w,release_velocity_mm_per_ms=-v0)
    else:
        assert e0<30.,'This reference only arrests before fracture'
        tp=math.asin(w*d0/v0)/w;vp=math.sqrt(v0*v0-k*d0*d0/m);x0=df-d0
        xt=math.sqrt(2*(30.-e0)/ks);dt=df-xt;ft=ks*xt;tt=tp+math.atanh(vp/(lam*x0))/lam
        dr=dt-ft/k;ur=.5*ft*ft/k;vr=-ft*w/k;tz=tt+math.pi/(2*w)
        p.update(family='NORMAL_ARREST_RETURN',turning_gap_mm=dt,force_amplitude_N=fp,
            force_at_turn_N=ft,residual_gap_mm=dr,recoverable_at_turn_J=ur*.001,
            retained_work_J=(e0-ur)*.001,peak_time_ms=tp,peak_velocity_mm_per_ms=vp,
            turn_time_ms=tt,zero_force_time_ms=tz,release_velocity_mm_per_ms=vr,
            positive_domain_end_ms=tz-dr/vr)
    return p

def envelope(d,p):
    return np.where(d<=p['delta0_mm'],p['k_N_per_mm']*d,
        p['softening_N_per_mm']*(p['deltaf_mm']-d))

def loading_work(d,p):
    d=np.asarray(d);z=np.maximum(d-p['delta0_mm'],0.)
    return .5*p['k_N_per_mm']*np.minimum(d,p['delta0_mm'])**2+p['peak_N']*z-.5*p['softening_N_per_mm']*z*z

def history_state(d,dm,p):
    """Energy stored plus unrecovered work, based on maximum historical gap."""
    f=np.maximum(0.,envelope(dm,p)+p['k_N_per_mm']*(d-dm))
    u=.5*f*f/p['k_N_per_mm']*.001
    retained=(loading_work(dm,p)-.5*envelope(dm,p)**2/p['k_N_per_mm'])*.001
    return {'force_N':f,'recoverable_J':u,'retained_J':retained,'IE_J':retained+u}

def state(t,p):
    t=np.asarray(t);m=p['moving_mass_g'];k=p['k_N_per_mm'];w=p['omega_rad_per_ms'];v0=p['v0_mm_per_ms'];tt=p['turn_time_ms']
    d=v0/w*np.sin(w*t);v=v0*np.cos(w*t)
    if p['family']=='NORMAL_SUBPEAK_RETURN':
        dm=np.where(t<=tt,d,p['turning_gap_mm'])
    else:
        tp=p['peak_time_ms'];lam=p['lambda_rad_per_ms'];tau=np.maximum(t-tp,0.);x0=p['deltaf_mm']-p['delta0_mm'];vp=p['peak_velocity_mm_per_ms']
        ds=p['deltaf_mm']-x0*np.cosh(lam*tau)+vp/lam*np.sinh(lam*tau)
        vs=vp*np.cosh(lam*tau)-lam*x0*np.sinh(lam*tau)
        d=np.where(t>tp,ds,d);v=np.where(t>tp,vs,v)
        z=np.maximum(t-tt,0.);amp=p['force_at_turn_N']/k
        d=np.where(t>tt,p['residual_gap_mm']+amp*np.cos(w*z),d)
        v=np.where(t>tt,-amp*w*np.sin(w*z),v)
        tz=p['zero_force_time_ms'];vr=p['release_velocity_mm_per_ms']
        d=np.where(t>tz,p['residual_gap_mm']+vr*(t-tz),d);v=np.where(t>tz,vr,v)
        dm=np.where(t<=tt,d,p['turning_gap_mm'])
    hs=history_state(d,dm,p);hs.update(delta_mm=d,delta_max_mm=dm,v_mm_per_ms=v,
        KE_J=.5*m*v*v*.001,P_N_ms=m*v,J_support_N_ms=m*(v-v0))
    return hs

def simpson(fun,a,b,n):
    x=np.linspace(a,b,n+1);y=fun(x)
    return float((b-a)/(3*n)*(y[0]+y[-1]+4*y[1:-1:2].sum()+2*y[2:-1:2].sum()))

def independent_rk4(p,end,n):
    """Direct ODE m*a=-F with maximum-gap history, no analytic branch times."""
    m=p['moving_mass_g'];k=p['k_N_per_mm'];fp=p['peak_N'];ks=p['softening_N_per_mm'];df=p['deltaf_mm'];d0=p['delta0_mm']
    def acceleration(d,history):
        history=max(history,d);fmax=k*history if history<=d0 else ks*(df-history)
        return -max(0.,fmax+k*(d-history))/m
    dt=end/n;d=0.;v=p['v0_mm_per_ms'];history=0.;a=np.zeros((n+1,3));a[0]=d,v,history
    for j in range(n):
        a1=acceleration(d,history);d2=d+.5*dt*v;v2=v+.5*dt*a1
        a2=acceleration(d2,history);d3=d+.5*dt*v2;v3=v+.5*dt*a2
        a3=acceleration(d3,history);d4=d+dt*v3;v4=v+dt*a3;a4=acceleration(d4,history)
        d+=dt/6*(v+2*v2+2*v3+v4);v+=dt/6*(a1+2*a2+2*a3+a4);history=max(history,d)
        a[j+1]=d,v,history
    exact=state(np.linspace(0,end,n+1),p)
    return {'steps':n,'gap_fraction':float(np.max(np.abs(a[:,0]-exact['delta_mm']))/p['turning_gap_mm']),
        'velocity_fraction':float(np.max(np.abs(a[:,1]-exact['v_mm_per_ms']))/p['v0_mm_per_ms']),
        'max_history_fraction':float(np.max(np.abs(a[:,2]-exact['delta_max_mm']))/p['turning_gap_mm'])}

def verify():
    assert not (OUT/'reference_verification.json').exists(),'Preserve reference audit'
    tick=time.perf_counter();cases=[];checks={};params={}
    for v0,end in [(20.,.012),(math.sqrt(20),.004)]:
        p=parameters(v0);name=p['family'];params[name]=p;t=np.linspace(0,end,8193);s=state(t,p);e0=p['initial_energy_J']
        energetic=float(np.max(np.abs(s['IE_J']+s['KE_J']-e0))/e0)
        rk=[independent_rk4(p,end,n) for n in [4096,8192]]
        continuity=[]
        for ts in [p['peak_time_ms'],p['turn_time_ms'],p['zero_force_time_ms']]:
            if ts is None or ts>=end:continue
            left=state([ts-1e-12],p);right=state([ts+1e-12],p)
            continuity.append(max(float(abs(left[key][0]-right[key][0]))/scale for key,scale in
                [('delta_mm',p['turning_gap_mm']),('v_mm_per_ms',v0),('force_N',p['force_amplitude_N']),('IE_J',e0)]))
        fd=1e-9;valid=np.ones(len(t),dtype=bool)
        for ts in [0.,p['peak_time_ms'],p['turn_time_ms'],p['zero_force_time_ms']]:
            if ts is not None:valid &= abs(t-ts)>10*fd
        a_fd=(state(t[valid]+fd,p)['v_mm_per_ms']-state(t[valid]-fd,p)['v_mm_per_ms'])/(2*fd)
        ode=float(np.max(abs(p['moving_mass_g']*a_fd+s['force_N'][valid]))/p['force_amplitude_N'])
        quadrature=[]
        if name=='NORMAL_ARREST_RETURN':
            for n in [512,1024,2048,4096]:
                elastic=simpson(lambda d:1/np.sqrt(v0*v0-2*loading_work(d,p)/p['moving_mass_g']),0,p['delta0_mm'],n)
                xt=p['deltaf_mm']-p['turning_gap_mm'];ymax=math.sqrt(p['turning_gap_mm']-p['delta0_mm'])
                soft=simpson(lambda y:2/(p['lambda_rad_per_ms']*np.sqrt(2*xt+y*y)),0,ymax,n)
                quadrature.append({'subintervals':n,'turn_time_ms':elastic+soft,'error_ms':abs(elastic+soft-p['turn_time_ms'])})
        metrics={'energy_identity_fraction':energetic,'ODE_fraction':ode,'continuity_fraction':max(continuity),
            'positive_gap_end_margin_ms':p['positive_domain_end_ms']-end,'minimum_gap_after_initial_mm':float(s['delta_mm'][1:].min()),
            'retained_work_monotonic_min_J':float(np.diff(s['retained_J']).min()),'RK4':rk,'quadrature':quadrature}
        gates={'energy_identity':energetic<1e-12,'ODE':ode<1e-7,'continuity':max(continuity)<1e-7,
            'positive_window':end<p['positive_domain_end_ms'] and s['delta_mm'][1:].min()>0,
            'before_separation':s['delta_mm'].max()<p['deltaf_mm'],
            'retained_nonnegative':s['retained_J'].min()>-1e-14 and np.diff(s['retained_J']).min()>-1e-14,
            'independent_RK4':all(max(r['gap_fraction'],r['velocity_fraction'],r['max_history_fraction'])<1e-5 for r in rk),
            'turn_quadrature':not quadrature or max(q['error_ms'] for q in quadrature)<1e-10}
        gates={key:bool(value) for key,value in gates.items()}
        checks.update({name+'_'+k:v for k,v in gates.items()});cases.append({'family':name,'parameters':p,'metrics':metrics,'checks':gates})
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'checks':checks,'families':cases,'parameters':params,
        'software':{'python':platform.python_version(),'numpy':np.__version__},'script_sha256':h.sha(__file__),
        'seconds':time.perf_counter()-tick,'saved_H_reference_sha256':h.sha(h.OUT/'reference_verification.json'),
        'no_solver_run':True,'no_physical_calibration':True,
        'formulas':{'history':'delta_max=max positive historical gap; F=max(0,F_envelope(delta_max)+Kn*(delta-delta_max))',
            'energy':'U=F^2/(2Kn); D=W_loading(delta_max)-F_envelope(delta_max)^2/(2Kn); IE=D+U; E0=IE+KE',
            'units':'mass g, displacement mm, time ms, force N, energy J=0.001 N mm',
            'impulse':'J_support=P-P0; P=m_g*v; P0=m_g*v0; no external work at stationary support',
            'arrest':'xturn=sqrt(2(G*A-E0_N_mm)/ks); delta_turn=df-xturn; unload omega=sqrt(Kn/m_g)',
            'energy_interpretation':'D denotes unrecovered numerical work; neither temperature nor measured physical dissipation'}}
    h.dump(OUT/'reference_verification.json',result)
    assert result['pass'],result
    print(json.dumps({'reference_pass':True,'checks':len(checks),'seconds':result['seconds'],
        'positive_window_end_ms':{k:p['positive_domain_end_ms'] for k,p in params.items()}}),flush=True)

if __name__=='__main__':verify()
