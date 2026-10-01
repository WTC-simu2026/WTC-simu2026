"""Independent saved-output audit. Does not import V11N reconstruction or mechanics."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def integrals(x,t):
    h=x[-1]-x[0]; m0=m1=0.
    for z in (-1/np.sqrt(3),1/np.sqrt(3)):
        gx=(x[:-1]+x[1:])/2+z*np.diff(x)/2
        gt=(t[:-1]+t[1:])/2+z*np.diff(t)/2
        m0+=float(np.sum(gt*np.diff(x)/(2*h)))
        m1+=float(np.sum((gx/h-.5)*gt*np.diff(x)/(2*h)))
    return m0,m1


def independent_profile(source,step,mode):
    """Algebraic reconstruction oracle; no calls to the tested implementation."""
    p=source['profiles'][step]; record=source['history'][step]
    centres=np.array(p['x_m']); c=np.array(p['temperature_c'])-20
    h=2*centres[0]*len(c)
    if mode=='legacy_mean_scaled':
        x=np.r_[0,centres,h]; t=np.r_[c[0]-(c[1]-c[0])/2,c,c[-1]+(c[-1]-c[-2])/2]
        mean,_=integrals(x,t)
        if abs(mean)>1e-14: t*=float(np.mean(c))/mean
        return x,t
    f=[record['bottom_surface_temperature_c']-20]
    for a,b in zip(c[:-1],c[1:]): f.append(min((a+b)/2,2*min(a,b)))
    f.append(record['top_surface_temperature_c']-20)
    x=[0.]; t=[f[0]]; dx=h/len(c)
    for i,avg in enumerate(c):
        a,b=f[i:i+2]
        if avg==0 and max(a,b)>0: return None
        if abs(avg-(a+b)/2)<=4*np.finfo(float).eps*max(avg,a,b,1e-300):
            x.append((i+1)*dx); t.append(b)
        else:
            fraction=min(.25,avg/(a+b)) if a+b>0 else .25
            value=(avg-fraction*(a+b)/2)/(1-fraction)
            x.extend([i*dx+fraction*dx,(i+1)*dx-fraction*dx,(i+1)*dx]); t.extend([value,value,b])
    return np.array(x),np.array(t)


def audit(out):
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11n_positive_transfer.json')
    manifest=read(out/'offline_manifest.json'); result=read(out/'results_v11n.json')
    sweep=read(out/'projection_sweep.json'); details=read(out/'selected_details.json')
    coupons=read(out/'section_coupons.json'); controls=read(out/'reference_controls.json')
    recon=read(out/'reconstruction_checks.json'); inventory=read(out/'section_inventory.json')
    sources={j:read(ROOT/cfg['source_directory']/(j+'.json')) for j in cfg['source_jobs']}
    tests=[]
    def check(n,c,e): tests.append({'name':n,'pass':bool(c),'evidence':e})
    def near(n,v,l): check(n,v<=l,{'value':float(v),'limit':l})
    check('input_hashes',all(sha(ROOT/p)==h for p,h in manifest['input_sha256'].items()),len(manifest['input_sha256']))
    check('output_hashes',all(sha(out/p)==h for p,h in manifest['output_sha256'].items()),len(manifest['output_sha256']))
    numerical=read(out/'numerical_audit.json')
    check('numerical_checks',result['status']=='PASS' and all(t['pass'] for t in numerical) and
          len(numerical)==result['test_count']==result['tests_passed'],len(numerical))
    near('affine_controls',max(float(np.max(abs(np.array(r['projected_k'])-r['expected_k']))) for r in controls),1e-10)
    # Direct quadrature checks on every fully saved selected profile and projection.
    mx={k:0. for k in ('mean','gradient','cell_mean','face','positive_tilt','heat','stress','section_energy',
                       'sensible','work','free_resultant','cycle_return','reconstruction_formula')}
    for d in details:
        x=np.array(d['x_m']); t=np.array(d['profile_delta_k']); temp=np.array(d['fiber_delta_k'])
        n=d['fibers']; h=x[-1]; eta=(np.arange(n)+.5)/n-.5; inertia=float(np.mean(eta**2))
        m0,m1=integrals(x,t)
        source=sources[d['job']]; profile=source['profiles'][d['step']]; history=source['history'][d['step']]
        values=np.array(profile['temperature_c'])-20; dx=h/len(values)
        mx['mean']=max(mx['mean'],abs(m0-float(np.mean(temp))),abs(m0-float(np.mean(values))))
        mx['gradient']=max(mx['gradient'],abs(float(np.mean(eta*temp))/inertia-12*m1))
        mx['heat']=max(mx['heat'],abs(2160000*h*m0-history['cumulative_total_inward_heat_j_m2']))
        if d['reconstruction']=='surface_cell_conservative':
            faces=np.array([history[f+'_surface_temperature_c']-20 for f in ('bottom','top')])
            mx['face']=max(mx['face'],float(np.max(abs(t[[0,-1]]-faces))))
            for i,c in enumerate(values):
                a,b=i*dx,(i+1)*dx; xx=np.r_[a,x[(x>a)&(x<b)],b]
                tt=np.interp(xx,x,t); avg,_=integrals(xx-a,tt)
                mx['cell_mean']=max(mx['cell_mean'],abs(avg-c))
        raw=np.interp((eta+.5)*h,x,t); active=raw>0
        if m0>0:
            logits=np.log(raw[active])+d['beta']*(eta[active]-d['target_centroid_eta'])
            weights=np.exp(logits-max(logits)); weights/=sum(weights)
            expected=np.zeros(n); expected[active]=n*m0*weights
            # Zero-beta affine branch intentionally retains exact raw samples.
            if d['beta']==0 and np.max(abs(raw-temp))<1e-10: expected=raw
            mx['positive_tilt']=max(mx['positive_tilt'],float(np.max(abs(expected-temp))))
        check('selected_positive_'+str(len(tests)),min(t)>=0 and min(temp)>=0 and max(temp)<=230.00000001,
              {'job':d['job'],'step':d['step'],'fibers':n})
    # Independently reconstruct EVERY saved knot and replay its stored exponential tilt.
    rindex={(r['job'],r['reconstruction'],r['step']):r for r in recon}
    oracle={}
    for rr in recon:
        key=(rr['job'],rr['reconstruction'],rr['step'])
        oracle[key]=independent_profile(sources[rr['job']],rr['step'],rr['reconstruction'])
        expected=oracle[key]
        if expected is None:
            if rr['status']!='REJECTED': raise ValueError('Unreported incompatible boundary')
            continue
        xx,tt=expected; m0,m1=integrals(xx,tt)
        mx['reconstruction_formula']=max(mx['reconstruction_formula'],abs(m0-rr['mean_k']),abs(m1-rr['first_moment_eta_k']))
        if min(tt)<0 or max(tt)>230.00000001: raise ValueError('Reconstruction bounds')
    for d in sweep:
        key=(d['job'],d['reconstruction'],d['step']); rr=rindex[key]
        if d['status']=='SUPPORTED':
            if d['minimum_k']<0 or d['maximum_k']>230.00000001: raise ValueError('Nonpositive or excessive stored projection')
            if d['mean_error_k']>1e-10 or d['gradient_error_k']>1e-10: raise ValueError('Moment mismatch')
            xx,tt=oracle[key]; m0,m1=integrals(xx,tt); n=d['fibers']; eta=(np.arange(n)+.5)/n-.5
            raw=np.interp((eta+.5)*xx[-1],xx,tt); active=raw>0; projected=np.zeros(n)
            if m0>0:
                target=12*m1*float(np.mean(eta**2))/m0
                logits=np.log(raw[active])+d['beta']*(eta[active]-target)
                weights=np.exp(logits-max(logits)); weights/=sum(weights); projected[active]=n*m0*weights
                if d['beta']==0 and abs(float(np.mean(raw))-m0)<1e-13 and abs(float(np.mean(raw*eta))-12*m1*np.mean(eta**2))<1e-14: projected=raw
            mx['mean']=max(mx['mean'],abs(float(np.mean(projected))-m0))
            mx['gradient']=max(mx['gradient'],abs(float(np.mean(eta*projected)/np.mean(eta**2))-12*m1))
            mx['positive_tilt']=max(mx['positive_tilt'],abs(float(min(projected))-d['minimum_k']),abs(float(max(projected))-d['maximum_k']))
        elif d['status']=='PROJECTION_REJECTED' and d['reason']=='target_outside_positive_fiber_support':
            target=d['target_centroid_eta']; lo,hi=d['support_eta']
            if lo<=target<=hi or d['committed']: raise ValueError('Invalid rejection certificate')
            xx,tt=oracle[key]; m0,m1=integrals(xx,tt); n=d['fibers']; eta=(np.arange(n)+.5)/n-.5
            expected_target=12*m1*float(np.mean(eta**2))/m0
            raw=np.interp((eta+.5)*xx[-1],xx,tt); support=eta[raw>0]
            if abs(target-expected_target)>1e-12 or abs(lo-min(support))>1e-12 or abs(hi-max(support))>1e-12:
                raise ValueError('Source does not support rejection certificate')
        elif d['status']=='RECONSTRUCTION_REJECTED':
            if rr['status']!='REJECTED' or d['committed']: raise ValueError('Reconstruction rejection mismatch')
        else: raise ValueError('Unreviewed status/reason')
    check('all_knots_independently_reconstructed',len(oracle)==3846,len(oracle))
    check('sweep_partition',len(sweep)==11538 and result['supported_count']==sum(r['status']=='SUPPORTED' for r in sweep)
          and result['rejected_count']==sum(r['status']!='SUPPORTED' for r in sweep),len(sweep))
    startup=[r for r in recon if r['reconstruction']=='surface_cell_conservative' and r['step']==0]
    check('startup_not_silently_repaired',len(startup)==3 and all(r['status']=='REJECTED' and r['reason']=='zero_cell_mean_positive_face' for r in startup),startup)
    for r in result['coverage']:
        rows=[d for d in sweep if all(d[k]==r[k] for k in ('job','reconstruction','fibers'))]
        if r['positive_time_rejections']!=sum(d['status']!='SUPPORTED' and d['time_s']>0 for d in rows): raise ValueError('Coverage mismatch')
    for c in coupons:
        sec={k:np.array(v) for k,v in inventory[str(c['fibers'])].items()}
        y,A,E,alpha,rho,cp=[sec[k] for k in ('y','area','E','alpha','density','cp')]
        B=np.column_stack([np.ones(len(y)),-y]); old=None; wt=we=0.
        for state in c['cycle']:
            q=np.array(state['q']); temp=np.array(state['delta_k']); em=B@q-alpha*temp; stress=E*em
            force=B.T@(A*stress); energy=float(.5*np.sum(A*stress*em)); sensible=float(np.sum(A*rho*cp*temp))
            mx['stress']=max(mx['stress'],float(np.max(abs(stress-state['stress_pa']))))
            mx['section_energy']=max(mx['section_energy'],abs(energy-state['stored_J_per_m']))
            mx['sensible']=max(mx['sensible'],abs(sensible-state['sensible_J_per_m']))
            if old is not None:
                oq,ot,os,of=old; wt-=float(np.sum(A*(stress+os)/2*alpha*(temp-ot))); we+=float((force+of)/2@(q-oq))
            mx['work']=max(mx['work'],abs(wt-state['thermal_work_J_per_m']),abs(we-state['external_work_J_per_m']),abs(energy-wt-we))
            if c['restraint']=='FREE':
                norm=np.array([max(1,float(sum(A*abs(stress)))),max(1,float(sum(A*abs(stress*y))))])
                mx['free_resultant']=max(mx['free_resultant'],float(max(abs(force)/norm)))
            else:
                near('reaction_'+str(len(tests)),float(np.max(abs(np.array(state['support_reaction_N_Nm'])+force))),1e-7)
            old=q,temp,stress,force
        mx['cycle_return']=max(mx['cycle_return'],abs(c['cycle'][-1]['stored_J_per_m']))
        near('composite_ledger_'+str(len(tests)),abs(c['composite_minus_gross_J_per_m']-(c['cycle'][4]['sensible_J_per_m']-c['gross_sensible_J_per_m'])),1e-8)
    limits={'mean':1e-10,'gradient':1e-10,'cell_mean':1e-10,'face':1e-12,'positive_tilt':1e-8,'heat':1e-4,
            'stress':1e-6,'section_energy':1e-7,'sensible':1e-7,'work':1e-7,'free_resultant':1e-10,'cycle_return':1e-8,'reconstruction_formula':1e-10}
    for k,v in mx.items(): near(k,v,limits[k])
    payload={'sweep':sweep,'details':details,'coupons':coupons,'controls':controls,'reconstruction':recon}
    dig=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
    check('numerical_digest',dig==result['numerical_digest_sha256'],dig)
    check('scope',not result['full_panel_history_solved'] and not result['startup_interface_validated'] and
          not result['thermal_solver_rerun'] and not result['fire_solved'] and not result['heated_fracture_solved'] and
          not result['coupled_first_law_closed'] and result['global_energy_credit_J']==0,True)
    return {'iteration':'V11N','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL',
            'audit_count':len(tests),'audits_passed':sum(t['pass'] for t in tests),'checks':tests}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--read-only',action='store_true'); args=p.parse_args()
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11n_positive_transfer.json'); out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]): raise ValueError('Outside V11N roots')
    result=audit(out)
    if not args.read_only:
        target=out/'release_audit.json'
        if target.exists(): raise FileExistsError(target)
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':result['audit_count'],'failed':[t for t in result['checks'] if not t['pass']]}))
    if result['status']!='PASS': raise SystemExit(1)
