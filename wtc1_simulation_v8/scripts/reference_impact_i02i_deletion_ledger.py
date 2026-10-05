"""L conditional deletion bookkeeping, not a calibrated mixed fracture law."""
from __future__ import annotations
import math,json,time
import numpy as np
import run_impact_i02i_deletion_ledger as run
import reference_impact_i02i_free_fracture as normal
h=run.h;OUT,CFG=run.OUT,run.CFG

def parameters(vx0,cfg):
    pn=run.read(h.ROOT/cfg['cached_references']['saved_H_reference']['path'])['parameters']
    m=pn['moving_mass_g'];kt=cfg['connector']['kt_N_per_mm'];w=math.sqrt(kt/m);tf=pn['failure_time_ms']
    xf=vx0/w*math.sin(w*tf);vf=vx0*math.cos(w*tf);u=.5*kt*xf*xf*.001
    return {'normal':pn,'m_g':m,'kt_N_mm':kt,'vx0_mm_ms':vx0,'omega_x_rad_ms':w,'tf_ms':tf,'x_at_deletion_mm':xf,
        'vx_at_deletion_mm_ms':vf,'Ux_at_deletion_J':u,'Ex0_J':.5*m*vx0*vx0*.001,
        'E0_J':pn['initial_energy_J']+.5*m*vx0*vx0*.001,'retained_IE_after_J':pn['normal_total_work_J']+u,
        'free_KE_after_J':.5*m*(vf*vf+pn['post_failure_velocity_mm_per_ms']**2)*.001,
        'release_policy_missing_energy_if_velocities_continuous_J':u,'calibrated':False}

def state(t,p):
    t=np.asarray(t);n=normal.state(t,p['normal']);w=p['omega_x_rad_ms'];m=p['m_g'];kt=p['kt_N_mm'];tf=p['tf_ms'];active=t<tf
    x=np.where(active,p['vx0_mm_ms']/w*np.sin(w*t),p['x_at_deletion_mm']+p['vx_at_deletion_mm_ms']*(t-tf))
    vx=np.where(active,p['vx0_mm_ms']*np.cos(w*t),p['vx_at_deletion_mm_ms']);fx=np.where(active,kt*x,0.)
    ux=np.where(active,.5*kt*x*x*.001,0.);uy=n['force_N']**2/(2*p['normal']['k_N_per_mm'])*.001
    ie=n['work_J']+np.where(active,ux,p['Ux_at_deletion_J']);ke=.5*m*(vx*vx+n['v_mm_per_ms']**2)*.001
    return {'x_mm':x,'y_mm':n['delta_mm'],'vx_mm_ms':vx,'vy_mm_ms':n['v_mm_per_ms'],'Fx_N':fx,'Fy_N':n['force_N'],
        'Ux_J':ux,'Uy_J':uy,'IE_J':ie,'KE_J':ke,'D_J':ie-ux-uy,'Px_Nms':m*vx,'Py_Nms':n['P_N_ms'],
        'Jx_Nms':m*(vx-p['vx0_mm_ms']),'Jy_Nms':n['support_J_N_ms']}

def simpson(values,dt):return dt/3*(values[0]+values[-1]+4*values[1:-1:2].sum()+2*values[2:-1:2].sum())

def independent_RK4_before(p,steps):
    """Direct monotone two-axis ODE up to the declared event, no analytic phases."""
    dt=p['tf_ms']/steps;z=np.array([0.,0.,p['vx0_mm_ms'],p['normal']['v0_mm_per_ms']]);m=p['m_g']
    def rates(z):return np.array([z[2],z[3],-p['kt_N_mm']*z[0]/m,-float(normal.force(z[1],p['normal']))/m])
    for j in range(steps):
        a=rates(z);b=rates(z+dt*a/2);c=rates(z+dt*b/2);d=rates(z+dt*c);z=z+dt*(a+2*b+2*c+d)/6
    expected=[p['x_at_deletion_mm'],p['normal']['deltaf_mm'],p['vx_at_deletion_mm_ms'],p['normal']['post_failure_velocity_mm_per_ms']]
    scales=[p['vx0_mm_ms']/p['omega_x_rad_ms'],p['normal']['deltaf_mm'],p['vx0_mm_ms'],p['normal']['v0_mm_per_ms']]
    return {'steps':steps,'fractions':[float(abs(z[j]-expected[j]))/scales[j] for j in range(4)]}

def verify():
    dest=OUT/'reference_verification.json';assert not dest.exists();cfg=run.read(CFG);tick=time.perf_counter();checks={};cases={}
    for vx0 in cfg['reference']['future_fresh_velocity_X_mm_ms']:
        p=parameters(vx0,cfg);t=np.unique(np.r_[np.linspace(0,cfg['reference']['future_end_ms'],12001),p['tf_ms']]);s=state(t,p)
        tf=p['tf_ms'];w=p['omega_x_rad_ms'];qt=np.linspace(0,tf,8193);fx=p['kt_N_mm']*vx0/w*np.sin(w*qt);vx=vx0*np.cos(w*qt)
        xwork=float(simpson(fx*vx,tf/8192))*.001;jx=float(simpson(-fx,tf/8192));rk=[independent_RK4_before(p,n) for n in [4096,8192]]
        boundary=state(np.array([tf-1e-12,tf,tf+1e-12]),p);post=t>=tf;eps=1e-9;times=np.array([tf/2,tf+.001])
        acc=(state(times+eps,p)['vx_mm_ms']-state(times-eps,p)['vx_mm_ms'])/(2*eps);force=state(times,p)['Fx_N']
        local={'total_energy':float(np.max(abs(s['IE_J']+s['KE_J']-p['E0_J'])))<1e-12,
            'independent_X_work':abs(xwork-p['Ux_at_deletion_J'])<1e-12,'independent_X_impulse':abs(jx-p['m_g']*(p['vx_at_deletion_mm_ms']-vx0))<1e-12,
            'independent_ODE':max(max(r['fractions']) for r in rk)<1e-5,
            'X_equation_before_after':float(np.max(abs(p['m_g']*acc+force)))<1e-6,
            'position_velocity_continuous':all(float(np.ptp(boundary[k]))<1e-7 for k in ['x_mm','y_mm','vx_mm_ms','vy_mm_ms']),
            'IE_continuous':float(np.ptp(boundary['IE_J']))<1e-10,
            'D_jump_equals_deleted_reserve':abs(float(boundary['D_J'][1]-boundary['D_J'][0])-p['Ux_at_deletion_J'])<1e-10,
            'ballistic_after':np.all(s['Fx_N'][post]==0) and np.all(s['Fy_N'][post]==0) and float(np.ptp(s['vx_mm_ms'][post]))==0 and float(np.ptp(s['vy_mm_ms'][post]))==0,
            'release_counterfactual_needs_explicit_channel':abs(p['E0_J']-p['normal']['normal_total_work_J']-p['free_KE_after_J']-p['Ux_at_deletion_J'])<1e-12 and p['Ux_at_deletion_J']>0}
        checks.update({f'vx{vx0:g}_{k}':bool(v) for k,v in local.items()});cases[f'vx{vx0:g}']={'parameters':p,'RK4':rk,'X_work_quadrature_J':xwork,'X_impulse_quadrature_Nms':jx}
    result={'created_utc':h.NOW(),'pass':all(checks.values()),'checks':checks,'cases':cases,'seconds':time.perf_counter()-tick,
        'script_sha256':h.sha(__file__),'inherited_H_reference_script_sha256':h.sha(normal.__file__),
        'policy':'Numerical retention: deleted recoverable X energy becomes part of the unrecovered IE ledger; no claim of heat or physical fracture',
        'release_policy_complete':False,'release_missing_information':'Transfer recipient, impulses, finite release mechanism and physical material calibration',
        'solver_run':False,'physical_propagation_qualified':False}
    h.dump(dest,result);assert result['pass'],result
    print(json.dumps({'conditional_reference_pass':True,'checks':len(checks),'seconds':result['seconds'],
        'Ux_at_deletion_J':{n:c['parameters']['Ux_at_deletion_J'] for n,c in cases.items()}}),flush=True)

if __name__=='__main__':verify()
