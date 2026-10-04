"""K separable free X/Y reference; not a physical mixed-fracture model."""
from __future__ import annotations
import json,math,time,platform
import numpy as np
import reference_impact_i02i_free_return as normal
h=normal.h;ROOT=h.ROOT
OUT=ROOT/'wtc1_simulation_v8/output/impact_i02i_free_mixed'
CFG=ROOT/'wtc1_simulation_v8/data/impact_i02i_k_predeclaration.json'
PLAN=ROOT/'wtc1_simulation_v8/data/impact_i02i_k_plan_from_j.json'

def parameters(vx,vy):
    py=normal.parameters(vy);m=py['moving_mass_g'];kt=21500.;wx=math.sqrt(kt/m)
    return {'normal':py,'moving_mass_g':m,'fixed_mass_g':m,'kt_N_per_mm':kt,'vx0_mm_per_ms':vx,
        'omega_x_rad_per_ms':wx,'period_x_ms':2*math.pi/wx,'amplitude_x_mm':vx/wx,
        'force_x_amplitude_N':kt*vx/wx,'initial_Px_N_ms':m*vx,'initial_Py_N_ms':m*vy,
        'initial_Ex_J':.5*m*vx*vx*.001,'initial_Ey_J':py['initial_energy_J'],
        'initial_energy_J':.5*m*vx*vx*.001+py['initial_energy_J']}

def state(t,p):
    t=np.asarray(t);y=normal.state(t,p['normal']);w=p['omega_x_rad_per_ms'];m=p['moving_mass_g']
    x=p['amplitude_x_mm']*np.sin(w*t);vx=p['vx0_mm_per_ms']*np.cos(w*t);fx=p['kt_N_per_mm']*x
    ux=.5*p['kt_N_per_mm']*x*x*.001;kx=.5*m*vx*vx*.001
    return {'x_mm':x,'y_mm':y['delta_mm'],'vx_mm_per_ms':vx,'vy_mm_per_ms':y['v_mm_per_ms'],
        'Fx_N':fx,'Fy_N':y['force_N'],'Ux_J':ux,'Uy_J':y['recoverable_J'],'Dy_J':y['retained_J'],
        'IE_J':ux+y['IE_J'],'KE_J':kx+y['KE_J'],'Px_N_ms':m*vx,'Py_N_ms':y['P_N_ms'],
        'Jx_N_ms':m*vx-p['initial_Px_N_ms'],'Jy_N_ms':y['J_support_N_ms']}

def independent_rk4(p,end,n):
    """One direct 4-state ODE with history, independent of branch times."""
    m=p['moving_mass_g'];kt=p['kt_N_per_mm'];py=p['normal'];kn=py['k_N_per_mm'];ks=py['softening_N_per_mm'];d0=py['delta0_mm'];df=py['deltaf_mm']
    def rates(z,history):
        x,y,vx,vy=z;maximum=max(history,y);fmax=kn*maximum if maximum<=d0 else ks*(df-maximum)
        fy=max(0.,fmax+kn*(y-maximum));return np.array([vx,vy,-kt*x/m,-fy/m])
    z=np.array([0.,0.,p['vx0_mm_per_ms'],py['v0_mm_per_ms']]);history=0.;dt=end/n;series=np.zeros((n+1,4));series[0]=z
    for k in range(n):
        r1=rates(z,history);r2=rates(z+.5*dt*r1,history);r3=rates(z+.5*dt*r2,history);r4=rates(z+dt*r3,history)
        z=z+dt/6*(r1+2*r2+2*r3+r4);history=max(history,z[1]);series[k+1]=z
    exact=state(np.linspace(0,end,n+1),p)
    scales=[p['amplitude_x_mm'],py['turning_gap_mm'],p['vx0_mm_per_ms'],py['v0_mm_per_ms']]
    metrics={name:float(np.max(abs(series[:,k]-exact[name]))/scales[k]) for k,name in enumerate(['x_mm','y_mm','vx_mm_per_ms','vy_mm_per_ms'])}
    return {'steps':n,'fractions':metrics}

def verify():
    dest=OUT/'reference_verification.json';assert not dest.exists(),'Keep references'
    tick=time.perf_counter();plan=json.loads(PLAN.read_text());parameters_by_family={};checks={};metrics={}
    for c in plan['cases_proposed']:
        name=c['family'];p=parameters(c['initial_vX_mm_per_ms'],c['initial_vY_mm_per_ms']);parameters_by_family[name]=p
        t=np.linspace(0,c['end_ms'],8193);s=state(t,p);e0=p['initial_energy_J']
        residual=float(np.max(abs(s['IE_J']+s['KE_J']-e0))/e0)
        rk=[independent_rk4(p,c['end_ms'],n) for n in [4096,8192]]
        fd=1e-9;mask=t>10*fd
        for ts in [p['normal']['peak_time_ms'],p['normal']['turn_time_ms'],p['normal']['zero_force_time_ms']]:
            if ts is not None:mask &= abs(t-ts)>10*fd
        plus=state(t[mask]+fd,p);minus=state(t[mask]-fd,p)
        ox=float(np.max(abs(m*(plus['vx_mm_per_ms']-minus['vx_mm_per_ms'])/(2*fd)+s['Fx_N'][mask]))/p['force_x_amplitude_N']) if (m:=p['moving_mass_g']) else math.inf
        oy=float(np.max(abs(m*(plus['vy_mm_per_ms']-minus['vy_mm_per_ms'])/(2*fd)+s['Fy_N'][mask]))/p['normal']['force_amplitude_N'])
        metrics[name]={'energy_identity_fraction':residual,'ODE_x_fraction':ox,'ODE_y_fraction':oy,'RK4':rk,
            'normal_positive_window_margin_ms':p['normal']['positive_domain_end_ms']-c['end_ms'],
            'minimum_y_after_initial_mm':float(s['y_mm'][1:].min()),'max_x_mm':float(abs(s['x_mm']).max()),
            'final_reference':{key:float(value[-1]) for key,value in s.items()}}
        local={'energy_identity':residual<1e-12,'independent_RK4':all(max(r['fractions'].values())<1e-5 for r in rk),
            'ODE_x':ox<1e-7,'ODE_y':oy<1e-7,'positive_normal_domain':c['end_ms']<p['normal']['positive_domain_end_ms'] and s['y_mm'][1:].min()>0,
            'no_failure':s['y_mm'].max()<p['normal']['deltaf_mm'],'initial_energy':abs(e0-c['initial_total_energy_J'])<1e-15,
            'energy_partition':np.max(abs(s['IE_J']-s['Ux_J']-s['Uy_J']-s['Dy_J']))<1e-14,
            'initial_momentum':s['Px_N_ms'][0]==p['initial_Px_N_ms'] and s['Py_N_ms'][0]==p['initial_Py_N_ms'],
            'support_impulses':np.max(abs(s['Jx_N_ms']+p['initial_Px_N_ms']-s['Px_N_ms']))<1e-14 and np.max(abs(s['Jy_N_ms']+p['initial_Py_N_ms']-s['Py_N_ms']))<1e-14}
        checks.update({name+'_'+k:bool(v) for k,v in local.items()})
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'checks':checks,'parameters':parameters_by_family,'metrics':metrics,
        'seconds':time.perf_counter()-tick,'software':{'python':platform.python_version(),'numpy':np.__version__},
        'script_sha256':h.sha(__file__),'inherited_reference_script_sha256':h.sha(normal.__file__),
        'saved_I_reference_sha256':h.sha(normal.OUT/'reference_verification.json'),
        'hypotheses':['Independent TYPE8 translational laws and shared point mass; zero rotation/contact, no material coupling',
            'Fresh maximum-gap normal history, no separation; X purely elastic and symmetric'],
        'formulas':'x=vx0/wx*sin(wx*t); vx=vx0*cos(wx*t); Fx=Kt*x. Y follows I H2. IE=Ux+Uy+Dy; KE=m*(vx²+vy²)/2; Jaxis=Paxis-P0axis; units g,mm,ms,N, J=0.001 N mm',
        'physical_calibration':False,'old_solver_run':False}
    h.dump(dest,result);assert result['pass'],result
    print(json.dumps({'reference_pass':True,'checks':len(checks),'seconds':result['seconds']}),flush=True)

if __name__=='__main__':verify()
