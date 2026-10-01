"""Independent Gauss read-back of startup profiles, work and exact section energy."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def quadrature(x):
    mid=(x[:-1]+x[1:])/2; half=np.diff(x)/2
    return np.r_[mid-half/np.sqrt(3),mid+half/np.sqrt(3)],np.r_[half,half]


def audit(out):
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11o_startup_bridge.json'); result=read(out/'results_v11o.json')
    manifest=read(out/'offline_manifest.json'); paths=read(out/'startup_paths.json'); inv=read(out/'section_inventory.json')
    controls=read(out/'closed_form_controls.json'); stiffness=read(out/'stiffness_comparison.json')
    projections=read(out/'projection_square_diagnostics.json'); comparisons=read(out/'bridge_comparisons.json'); flux=read(out/'flux_mismatch_diagnostics.json')
    sources={j:read(ROOT/cfg['source_directory']/(j+'.json')) for j in cfg['source_jobs']}
    tests=[]
    def check(n,c,e): tests.append({'name':n,'pass':bool(c),'evidence':e})
    def near(n,v,l): check(n,v<=l,{'value':float(v),'limit':l})
    check('input_hashes',all(sha(ROOT/p)==h for p,h in manifest['input_sha256'].items()),len(manifest['input_sha256']))
    check('output_hashes',all(sha(out/p)==h for p,h in manifest['output_sha256'].items()),len(manifest['output_sha256']))
    numerical=read(out/'numerical_audit.json')
    check('numerical_checks',result['status']=='PASS' and len(numerical)==result['test_count']==result['tests_passed'] and all(t['pass'] for t in numerical),len(numerical))
    h=inv['h']; Ec=inv['Ec']; ac=inv['alphac']; Ac=inv['Ac']; wc=Ac/h
    ys,As,Es,alphas,rhos,cps=[np.array(inv[k]) for k in ('ys','As','Es','alphas','rhos','cps')]
    Bs=np.column_stack([np.ones(len(ys)),-ys]); K=np.array(inv['K'])
    gx,gw=quadrature(np.array([0.,h])); B=np.column_stack([np.ones(len(gx)),-(gx-h/2)])
    expectedK=B.T@((Ec*wc*gw)[:,None]*B)+Bs.T@((Es*As)[:,None]*Bs)
    near('exact_cold_stiffness',float(np.max(abs(K-expectedK)))/float(np.max(abs(K))),1e-12)
    near('modulus_units',abs(Ec-2500*4448.2216152605/.0254**2),1e-6)
    near('concrete_area',abs(Ac-2.032*.11049*.998),1e-12)
    mx={k:0. for k in ('mean_K','moment_K','square_K2','heat_J_m2','force_relative','stored_J_per_m',
                       'sensible_J_per_m','work_J_per_m','energy_relative','face_stress_Pa','weak_bound')}
    cache={}
    for path in paths:
        source=sources[path['job']]; previous=None; wth=wext=0.
        for row in path['history']:
            x=np.array(row['x_m']); t=np.array(row['bulk_delta_k']); q=np.array(row['q']); a=row['fraction']
            gx,w=quadrature(x); temp=np.interp(gx,x,t); y=gx-h/2
            B=np.column_stack([np.ones(len(gx)),-y]); ts=np.interp(ys+h/2,x,t)
            stress=Ec*(B@q-ac*temp); ss=Es*(Bs@q-alphas*ts)
            force=B.T@(wc*w*stress)+Bs.T@(As*ss)
            energy=float(.5*wc*np.sum(w*stress**2/Ec)+.5*np.sum(As*ss**2/Es))
            sensible=float(inv['rhoc']*inv['cpc']*wc*np.sum(w*temp)+sum(As*rhos*cps*ts))
            m0=float(w@temp/h); m1=float(w@((y/h)*temp)/h); m2=float(w@(temp**2)/h)
            mx['mean_K']=max(mx['mean_K'],abs(m0-row['mean_delta_k']),abs(m0-row['expected_mean_delta_k']))
            mx['moment_K']=max(mx['moment_K'],abs(m1-row['first_moment_eta_k']))
            mx['square_K2']=max(mx['square_K2'],abs(m2-row['mean_square_delta_k2']))
            expected_heat=a*source['history'][1]['cumulative_total_inward_heat_j_m2']
            mx['heat_J_m2']=max(mx['heat_J_m2'],abs(2160000*h*m0-expected_heat))
            mx['stored_J_per_m']=max(mx['stored_J_per_m'],abs(energy-row['stored_J_per_m']))
            mx['sensible_J_per_m']=max(mx['sensible_J_per_m'],abs(sensible-row['sensible_J_per_m']))
            mx['force_relative']=max(mx['force_relative'],float(max(abs(force-row['resultant_N_Nm'])))/max(1,float(max(np.abs(row['thermal_force_N_Nm'])))))
            face=np.array(row['face_delta_k']); face_stress=Ec*(q[0]-np.array([-h/2,h/2])*q[1]-ac*face)
            mx['face_stress_Pa']=max(mx['face_stress_Pa'],float(max(abs(face_stress-row['face_stress_pa']))))
            bound=max(float(max(t)),float(max(face)))*m0
            mx['weak_bound']=max(mx['weak_bound'],abs(m1)-m0/2,m2-bound,-energy,energy-row['thermal_square_energy_S_J_per_m']/2)
            if min(t)<0 or max(t)>230.00000001: raise ValueError('Temperature bounds')
            if previous is not None:
                ox,ot,oq,ots,os,of=previous
                union=np.unique(np.r_[x,ox]); uq,uw=quadrature(union)
                newT=np.interp(uq,x,t); oldT=np.interp(uq,ox,ot); uy=uq-h/2
                new_sig=Ec*(q[0]-uy*q[1]-ac*newT); old_sig=Ec*(oq[0]-uy*oq[1]-ac*oldT)
                wth-=float(wc*np.sum(uw*(new_sig+old_sig)/2*ac*(newT-oldT))+np.sum(As*(ss+os)/2*alphas*(ts-ots)))
                wext+=float((force+of)/2@(q-oq))
            mx['work_J_per_m']=max(mx['work_J_per_m'],abs(wth-row['thermal_work_J_per_m']),abs(wext-row['external_work_J_per_m']))
            mx['energy_relative']=max(mx['energy_relative'],abs(energy-wth-wext)/max(1,energy,abs(wth),abs(wext)))
            if path['restraint']=='FULLY_RESTRAINED': near('reaction_'+str(len(tests)),float(max(abs(np.array(row['support_reaction_N_Nm'])+force))),1e-7)
            if a==0:
                near('zero_bulk_'+str(len(tests)),energy+sensible+float(max(abs(q))),1e-12)
                if path['bridge']=='boundary_preserving_weak_limit':
                    check('zero_trace_retained_'+str(len(tests)),max(face)>0 and row['weak_zero_state'] and not row['resolved_new_thermal_time'],face.tolist())
            # Mean conservation applies cell by cell, not just globally.
            if row['phase']=='ASCENDING':
                sourceT=np.array(source['profiles'][1]['temperature_c'])-20; ncell=len(sourceT)
                for j,cell in enumerate(sourceT):
                    left,right=j*h/ncell,(j+1)*h/ncell
                    knots=np.r_[left,x[(x>left)&(x<right)],right]; cq,cw=quadrature(knots)
                    avg=float(cw@np.interp(cq,x,t)/(right-left))
                    mx['mean_K']=max(mx['mean_K'],abs(avg-a*cell))
                f0=np.array([source['history'][0][s+'_surface_temperature_c']-20 for s in ('bottom','top')])
                f1=np.array([source['history'][1][s+'_surface_temperature_c']-20 for s in ('bottom','top')])
                expected_face=f0+a*(f1-f0) if path['bridge']=='boundary_preserving_weak_limit' else a*f1
                near('face_convention_'+str(len(tests)),float(max(abs(expected_face-face))),1e-12)
                cache[(path['job'],path['bridge'],a)]=(x,t,m0,m1,m2)
            previous=x,t,q,ts,ss,force
    for d in projections:
        x,t,m0,m1,m2=cache[(d['job'],d['bridge'],d['fraction'])]; n=d['fibers']; eta=(np.arange(n)+.5)/n-.5
        raw=np.interp((eta+.5)*h,x,t); active=raw>0; target=12*m1*float(np.mean(eta**2))/m0
        if d['status']=='REJECTED':
            check('projection_rejection_'+str(len(tests)),target<min(eta[active]) or target>max(eta[active]),d['reason']); continue
        meta=d['projection']; logits=np.log(raw[active])+meta['beta']*(eta[active]-target)
        weights=np.exp(logits-max(logits)); weights/=sum(weights); value=np.zeros(n); value[active]=n*m0*weights
        if meta['beta']==0 and abs(float(np.mean(raw))-m0)<1e-13 and abs(float(np.mean(raw*eta))-12*m1*np.mean(eta**2))<1e-14: value=raw
        near('projection_square_'+str(len(tests)),abs(float(np.mean(value**2))-d['projected_mean_square_k2']),1e-10)
        near('exact_square_'+str(len(tests)),abs(m2-d['exact_mean_square_k2']),1e-10)
    for d in flux:
        x,t,_,_,_=cache[(d['job'],d['bridge'],d['fraction'])]
        actual=(t[-1]-t[-2])/(x[-1]-x[-2])
        near('flux_diagnostic_'+str(len(tests)),abs(actual-d['reconstructed_top_gradient_flux_w_m2'])/max(1,abs(actual)),1e-12)
        if d['is_heat_equation_solution']: raise ValueError('Unsupported heat-solution claim')
    for d in stiffness:
        deficit=Ec*Ac*h*h/(12*d['fibers']**2)
        near('midpoint_stiffness_closure_'+str(d['fibers']),abs(deficit-d['curvature_stiffness_deficit_Nm2'])/abs(K[1,1]),1e-10)
    for d in controls:
        near('closed_form_'+str(len(tests)),abs(d['state']['stored_J_per_m']-d['expected_stored_J_per_m']),1e-8)
    limits={'mean_K':1e-10,'moment_K':1e-10,'square_K2':1e-10,'heat_J_m2':1e-4,'force_relative':1e-10,
            'stored_J_per_m':1e-9,'sensible_J_per_m':1e-7,'work_J_per_m':1e-9,'energy_relative':1e-10,'face_stress_Pa':1e-6,'weak_bound':1e-10}
    for k,v in mx.items(): near(k,v,limits[k])
    payload={'paths':paths,'controls':controls,'stiffness':stiffness,'projections':projections,'comparisons':comparisons,'flux':flux}
    dig=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
    check('numerical_digest',dig==result['numerical_digest_sha256'],dig)
    check('coverage',len(paths)==12 and sum(len(p['history']) for p in paths)==result['state_count']==180,len(paths))
    check('scope',result['weak_mechanical_zero_limit_qualified'] and not result['heat_equation_bridge_validated'] and
          not result['continuous_initial_temperature_reconstruction_validated'] and not result['newly_resolved_thermal_time'] and
          not result['panel_history_solved'] and not result['heated_fracture_solved'] and not result['fire_solved'] and
          not result['coupled_first_law_closed'] and result['global_energy_credit_J']==0,True)
    return {'iteration':'V11O','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL','audit_count':len(tests),
            'audits_passed':sum(t['pass'] for t in tests),'checks':tests}


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--read-only',action='store_true'); args=ap.parse_args()
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11o_startup_bridge.json'); out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]): raise ValueError('Outside V11O roots')
    result=audit(out)
    if not args.read_only:
        target=out/'release_audit.json'
        if target.exists(): raise FileExistsError(target)
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':result['audit_count'],'failed':[t for t in result['checks'] if not t['pass']]}))
    if result['status']!='PASS': raise SystemExit(1)
