"""Own exact monotone one-mass reference, checked by independent quadrature.

Units g/mm/ms/N. W below is N mm, never J inside v^2=v0^2-2W/m.
This reference defines a hypothetical numerical law, not physical fracture.
"""
from __future__ import annotations
import json,math,sys,time
import numpy as np
import run_impact_i02i_free_fracture as h

def parameters(connector,v0=30.):
    m=connector['mass_g']/2;k=connector['kn_N_per_mm'];peak=connector['peak_normal_force_N']
    area=connector['initial_area_mm2'];G=connector['hypothetical_Gf_N_per_mm'];d0=peak/k;df=2*G*area/peak
    soft=peak/(df-d0);w=math.sqrt(k/m);lam=math.sqrt(soft/m)
    E0=.5*m*v0*v0;vpeak=math.sqrt(v0*v0-k*d0*d0/m)
    tpeak=math.asin(w*d0/v0)/w;x0=df-d0
    tf=tpeak+math.atanh(lam*x0/vpeak)/lam;vf=math.sqrt(v0*v0-2*G*area/m)
    assert df>d0>0 and E0>G*area and 0<lam*x0/vpeak<1
    return {'moving_mass_g':m,'fixed_mass_g':m,'k_N_per_mm':k,'peak_N':peak,'reference_area_mm2':area,
        'hypothetical_Gf_N_per_mm':G,'delta0_mm':d0,'deltaf_mm':df,'softening_N_per_mm':soft,
        'v0_mm_per_ms':v0,'initial_energy_N_mm':E0,'initial_energy_J':E0*.001,'initial_momentum_N_ms':m*v0,
        'normal_total_work_N_mm':G*area,'normal_total_work_J':G*area*.001,'omega_rad_per_ms':w,'lambda_rad_per_ms':lam,
        'peak_time_ms':tpeak,'failure_time_ms':tf,'peak_velocity_mm_per_ms':vpeak,'post_failure_velocity_mm_per_ms':vf,
        'formulas':{'elastic':'delta=v0/w*sin(w*t); v=v0*cos(w*t)',
            'softening':'x=df-delta=x0*cosh(lambda*tau)-vpeak/lambda*sinh(lambda*tau); v=vpeak*cosh(lambda*tau)-lambda*x0*sinh(lambda*tau)',
            'after':'delta=df+vf*(t-tf); v=vf; F=0; W=G*area',
            'force_work':'F=k*delta to d0, then soft*(df-delta) to df, then 0; W=integral F d(delta)',
            'units':'W in N mm, J=0.001*N mm; v(delta)=sqrt(v0^2-2W_N_mm/m_g)',
            'impulse':'J_support=m*v-m*v0; moving support reaction=0','energy':'E0_J=0.001*(m*v^2/2+W_N_mm)'},
        'domain':'Fresh monotone positive opening with E0>G*area, no shear reservoir or unloading'}

def work(delta,p):
    d=np.maximum(np.asarray(delta,dtype=float),0);d0,df=p['delta0_mm'],p['deltaf_mm']
    elastic=.5*p['k_N_per_mm']*np.minimum(d,d0)**2
    z=np.clip(d-d0,0,df-d0)
    return elastic+p['peak_N']*z-.5*p['softening_N_per_mm']*z*z

def force(delta,p):
    d=np.maximum(np.asarray(delta,dtype=float),0)
    return np.where(d<=p['delta0_mm'],p['k_N_per_mm']*d,np.maximum(0,p['softening_N_per_mm']*(p['deltaf_mm']-d)))

def state(t,p):
    t=np.asarray(t,dtype=float);d=np.empty_like(t);v=np.empty_like(t)
    a=t<=p['peak_time_ms'];b=(t>p['peak_time_ms'])&(t<p['failure_time_ms']);c=t>=p['failure_time_ms']
    w,lam=p['omega_rad_per_ms'],p['lambda_rad_per_ms'];v0=p['v0_mm_per_ms'];x0=p['deltaf_mm']-p['delta0_mm']
    d[a]=v0/w*np.sin(w*t[a]);v[a]=v0*np.cos(w*t[a])
    tau=t[b]-p['peak_time_ms'];vp=p['peak_velocity_mm_per_ms']
    d[b]=p['deltaf_mm']-x0*np.cosh(lam*tau)+vp/lam*np.sinh(lam*tau)
    v[b]=vp*np.cosh(lam*tau)-lam*x0*np.sinh(lam*tau)
    d[c]=p['deltaf_mm']+p['post_failure_velocity_mm_per_ms']*(t[c]-p['failure_time_ms']);v[c]=p['post_failure_velocity_mm_per_ms']
    W=work(d,p);F=force(d,p);P=p['moving_mass_g']*v
    return {'delta_mm':d,'v_mm_per_ms':v,'force_N':F,'work_J':W*.001,'KE_J':.5*p['moving_mass_g']*v*v*.001,
        'P_N_ms':P,'support_J_N_ms':P-p['initial_momentum_N_ms']}

def simpson_time(a,b,n,p):
    d=np.linspace(a,b,n+1);v=np.sqrt(p['v0_mm_per_ms']**2-2*work(d,p)/p['moving_mass_g']);f=1/v
    return float((b-a)/(3*n)*(f[0]+f[-1]+4*f[1:-1:2].sum()+2*f[2:-1:2].sum()))

def verify():
    file=h.OUT/'reference_verification.json';assert not file.exists(),'Preserve reference audit'
    start=time.perf_counter();cfg=json.loads(h.ELCFG.read_text(encoding='utf-8'));p=parameters(cfg['connector'])
    t=np.linspace(0,.012,10001);a=state(t,p)
    energy_error=float(np.max(np.abs(a['work_J']+a['KE_J']-p['initial_energy_J'])))
    q=[]
    for n in [512,1024,2048,4096]:
        tp=simpson_time(0,p['delta0_mm'],n,p);tf=tp+simpson_time(p['delta0_mm'],p['deltaf_mm'],n,p)
        q.append({'subdivisions_each_branch':n,'peak_time_ms':tp,'failure_time_ms':tf,'exact_failure_time_difference_ms':tf-p['failure_time_ms']})
    spots=[.3*p['delta0_mm'],p['delta0_mm']+.4*(p['deltaf_mm']-p['delta0_mm']),1.1*p['deltaf_mm']]
    eps=1e-7*p['deltaf_mm'];derivative=[]
    for d in spots:
        derivative.append(float(abs((work(d+eps,p)-work(d-eps,p))/(2*eps)-force(d,p))/p['peak_N']))
    ode=[];step=1e-7
    for t0 in [p['peak_time_ms']/2,(p['failure_time_ms']+p['peak_time_ms'])/2,p['failure_time_ms']+.001]:
        da=state(np.array([t0-step,t0,t0+step]),p);acc=(da['delta_mm'][2]-2*da['delta_mm'][1]+da['delta_mm'][0])/step**2
        ode.append(float(abs(p['moving_mass_g']*acc+da['force_N'][1])/p['peak_N']))
    boundaries=[]
    for t0 in [p['peak_time_ms'],p['failure_time_ms']]:
        b=state(np.array([t0-1e-12,t0,t0+1e-12]),p)
        boundaries.append({'time_ms':t0,'gap_range_mm':float(np.ptp(b['delta_mm'])),'velocity_range_mm_ms':float(np.ptp(b['v_mm_per_ms']))})
    checks={'initial_state':float(a['delta_mm'][0])==0 and float(a['v_mm_per_ms'][0])==30,
        'monotone_positive_path':bool(np.all(np.diff(a['delta_mm'])>0) and np.all(a['v_mm_per_ms']>0)),
        'energy_identity':energy_error<=1e-12,'quadrature_exact_time':abs(q[-1]['exact_failure_time_difference_ms'])<=1e-10,
        'quadrature_converged':abs(q[-1]['failure_time_ms']-q[-2]['failure_time_ms'])<=1e-10,
        'force_is_work_derivative':max(derivative)<=1e-6,'equation_of_motion':max(ode)<=1e-5,
        'continuity_at_peak_and_failure':all(b['gap_range_mm']<1e-8 and b['velocity_range_mm_ms']<1e-6 for b in boundaries),
        'final_work_and_speed':abs(float(a['work_J'][-1])-.03)<1e-12 and abs(float(a['v_mm_per_ms'][-1])-math.sqrt(300))<1e-12}
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'checks':checks,'parameters':p,'quadrature':q,
        'maximum_energy_identity_error_J':energy_error,'force_work_derivative_errors_over_peak':derivative,
        'motion_equation_residuals_over_peak':ode,'continuity':boundaries,'elapsed_seconds':time.perf_counter()-start,
        'script_sha256':h.sha(__file__),'elastic_config_sha256':h.sha(h.ELCFG),'python':sys.version,'numpy':np.__version__,
        'source':'Own piecewise analytic solution; independent Simpson quadrature and differential/energy checks; no source-derived physical property',
        'physical_fracture_energy_calibrated':False}
    h.dump(file,result);assert result['pass'],result
    print(json.dumps({'reference_pass':True,'tf_ms':p['failure_time_ms'],'vf_mm_ms':p['post_failure_velocity_mm_per_ms'],'energy_identity_J':energy_error}),flush=True)

if __name__=='__main__':verify()
