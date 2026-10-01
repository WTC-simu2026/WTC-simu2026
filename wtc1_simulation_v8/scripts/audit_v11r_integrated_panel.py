"""Independent replay from saved coordinates/constitutive constants, no panel import."""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--read-only',action='store_true'); args=ap.parse_args(); out=(ROOT/args.output).resolve()
    checks=[]
    def check(name,v,tol): checks.append({'name':name,'value':float(v),'limit':float(tol),'pass':bool(np.isfinite(v) and v<=tol)})
    mf=read(out/'offline_manifest.json')
    for p,h in mf['input_sha256'].items(): check('input:'+p,int(sha(ROOT/p)!=h),0)
    for p,h in mf['output_sha256'].items(): check('output:'+p,int(sha(out/p)!=h),0)
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11r_integrated_panel.json'); results=read(out/'results_v11r.json'); runs={}; inventories={}; counted=0
    sources={c['source']:read(ROOT/cfg['thermal_directory']/(c['source']+'.json')) for c in cfg['cases']}
    maxima={k:0. for k in ['equilibrium','forces_relative','energy_relative','sensible_relative','thermal_work_relative','external_work_relative','slab_q_work_defect','reaction_relative','DCR_absolute','heat_J','term_gap','displacement_summary']}
    for spec in cfg['cases']:
        name=spec['id']; run=read(out/(name+'.json')); v=read(out/(name+'_inventory.json')); runs[name]=run; inventories[name]=v
        s=v['section']; B=np.array(v['B']); ends=np.array(v['Bends']); dofs=np.array(v['dofs']); weights=np.array(v['weights_m']); zone=np.array(v['zone']); ez=np.array(v['end_zone'])
        TB=np.array(v['term_B']); tk=np.array(v['term_k']); comp=np.array(v['compression_only']); tens=np.array(v['tension_only']); F1=np.array(v['force_unit']); source=sources[spec['source']]; x=np.array(source['x_m']); eta=x/s['h']-.5
        # Independent Gaussian integration of the P1 thermal field and exact section stiffness.
        fields={}; As=np.array(s['As']); Es=np.array(s['Es']); ys=np.array(s['ys']); als=np.array(s['alphas']); Bs=np.column_stack((np.ones(len(ys)),-ys))
        K=s['Ec']*s['Ac']*np.diag([1,s['h']**2/12])+Bs.T@((As*Es)[:,None]*Bs)
        check(name+':section_K',np.max(np.abs(K-s['K']))/np.max(np.abs(K)),1e-12)
        old=None; W=Wth=0.; heating_steps=[]
        for row in run['history']+([run['rejected_trial']] if run['rejected_trial'] else []):
            counted+=1; i=row['thermal_step']; temp=np.array(source['profiles'][i]['temperature_c'])-20
            if i not in fields:
                mom=np.zeros(3)
                for z in [-1/math.sqrt(3),1/math.sqrt(3)]:
                    r=(z+1)/2; t=(1-r)*temp[:-1]+r*temp[1:]; e=(1-r)*eta[:-1]+r*eta[1:]; w=np.diff(x)/(2*s['h']); mom += [w@t,w@(t*e),w@(t*t)]
                ts=np.interp(ys+s['h']/2,x,temp); f=s['Ec']*s['Ac']*s['alphac']*np.array([mom[0],-s['h']*mom[1]])+Bs.T@(As*Es*als*ts)
                S=s['Ec']*s['Ac']*s['alphac']**2*mom[2]+np.sum(As*Es*(als*ts)**2)
                sensible=s['Ac']*s['rhoc']*s['cpc']*mom[0]+np.sum(As*np.array(s['rhos'])*np.array(s['cps'])*ts)
                fields[i]=(f,S,sensible,ts)
            f,S,sensible,ts=fields[i]; fz=zone[:,None]*f; Sz=zone**2*S; u=np.array(row['u']); q=np.einsum('pai,pi->pa',B,u[dofs]); Q=q@K-fz
            gap=TB@u; elastic_gap=np.where(comp,np.minimum(gap,0),np.where(tens,np.maximum(gap,0),gap)); force=tk*elastic_gap
            internal=TB.T@force; local=np.einsum('pai,pa,p->pi',B,Q,weights); internal+=np.bincount(dofs.ravel(),weights=local.ravel(),minlength=v['size'])
            absolute=np.abs(TB).T@np.abs(force)+np.bincount(dofs.ravel(),weights=np.einsum('pai,pa,p->pi',np.abs(B),np.abs(Q),weights).ravel(),minlength=v['size'])
            F=row['gravity']*F1; eq=np.max(np.abs(internal-F)/np.maximum(1,np.maximum(np.abs(F),absolute)))
            maxima['equilibrium']=max(maxima['equilibrium'],eq)
            maxima['forces_relative']=max(maxima['forces_relative'],np.max(np.abs(force-row['term_force_N']))/max(1,np.max(np.abs(force))))
            maxima['term_gap']=max(maxima['term_gap'],np.max(np.abs(gap-row['term_gap'])))
            slabU=weights@(.5*np.einsum('pa,ab,pb->p',q,K,q)-np.sum(q*fz,axis=1)+.5*Sz); springU=.5*np.sum(tk*elastic_gap**2); U=slabU+springU
            maxima['energy_relative']=max(maxima['energy_relative'],abs(U-row['stored_J'])/max(1,abs(U)),abs(slabU-row['slab_stored_J'])/max(1,abs(slabU)),abs(springU-row['spring_stored_J'])/max(1,springU))
            sensible_total=(weights@zone)*sensible; gross=s['width']*(weights@zone)*source['history'][i]['enthalpy_j_m2']
            maxima['sensible_relative']=max(maxima['sensible_relative'],abs(sensible_total-row['sensible_enthalpy_J'])/max(1,abs(sensible_total)))
            maxima['heat_J']=max(maxima['heat_J'],abs(gross-row['gross_coupon_sensible_J']),abs(sensible_total-gross-row['composite_minus_gross_sensible_J']))
            qe=np.einsum('ejai,ei->eja',ends,u[dofs[::2]]).reshape(-1,2); qa=np.vstack((qe,q)); za=np.r_[ez,zone]
            stress=s['Ec']*(qa[:,0,None]-qa[:,1,None]*(x-s['h']/2)-s['alphac']*za[:,None]*temp)
            rebar=Es*(qa[:,0,None]-qa[:,1,None]*ys-als*za[:,None]*ts)
            ratios=[max(0,stress.max())/s['ft'],max(0,-stress.min())/s['fc'],np.max(np.abs(rebar),initial=0)/s['fy']]
            component=[]; vertical=horizontal=0.; uplift=unsupported=False
            for term,n in zip(v['terms'],force):
                kind=term['kind']; d=0.
                if kind=='horizontal_tie': d=abs(n)/term['cap_abs_N']
                elif kind=='vertical_tie': d=max(n,0)/term['cap_tension_N']
                elif kind=='seat_v':
                    d=max(-n,0)/term['cap_compression_N']; vertical-=n; uplift |= n>1e-5
                elif kind=='seat_h':
                    d=max(n*term['tension_sign'],0)/term['cap_signed_tension_N']; horizontal-=n; unsupported |= n*term['tension_sign'] < -1e-5
                elif kind in ['top_chord','bottom_chord','web']: d=abs(n)/(term['cap_compression_N'] if n<0 else term['cap_tension_N'])
                component.append(d)
            maxD=max(ratios+component); maxima['DCR_absolute']=max(maxima['DCR_absolute'],abs(maxD-row['max_DCR']),np.max(np.abs(np.array(component)-row['term_DCR'])))
            maxima['reaction_relative']=max(maxima['reaction_relative'],abs(vertical-row['seat_vertical_reaction_N'])/max(1,abs(vertical)),abs(horizontal-row['seat_horizontal_reaction_N'])/max(1,abs(vertical)))
            maxima['displacement_summary']=max(maxima['displacement_summary'],abs(max(-u[v['slab_w_dofs']])-row['max_slab_down_m']))
            check(name+':support_flags',int(bool(uplift)!=row['support_uplift_unchecked'] or bool(unsupported)!=row['support_horizontal_compression_unchecked']),0)
            if row['committed']:
                check(name+':guard',maxD-cfg['guard_DCR'],cfg['acceptance']['guard_absolute'])
                check(name+':support_domain',int(uplift or unsupported),0)
                if old is not None:
                    ou,oF,oq,ofz,oSz=old; W+=float(.5*(oF+F)@(u-ou)); Wth+=float(weights@(-.5*np.sum((oq+q)*(fz-ofz),axis=1)+.5*(Sz-oSz)))
                old=u,F,q,fz,Sz
                maxima['thermal_work_relative']=max(maxima['thermal_work_relative'],abs(Wth-row['thermal_work_J'])/max(1,abs(Wth)))
                maxima['external_work_relative']=max(maxima['external_work_relative'],abs(W-row['external_work_J'])/max(1,abs(W)))
                if row['phase']=='HEATING': heating_steps.append(i)
            else: check(name+':rejection_justified',int(maxD<=cfg['guard_DCR'] and not (uplift or unsupported)),0)
        check(name+':consecutive_saved_heat',int(heating_steps!=list(range(1,len(heating_steps)+1))),0)
        declared=run['summary']['energy_qualified']; computed=max(r['increment_energy_residual_relative'] for r in run['history'])<=cfg['acceptance']['increment_energy_relative'] and max(r['total_energy_residual_relative'] for r in run['history'])<=cfg['acceptance']['total_energy_relative']
        check(name+':energy_status_honest',int(declared!=computed),0)
    for k,v in maxima.items(): check('independent:'+k,v,1e-5 if k=='heat_J' else 1e-8)
    comparisons=read(out/'comparisons.json'); cold=read(out/'cold_comparison.json')
    check('digest',int(digest({'runs':runs,'inventories':inventories,'comparisons':comparisons,'cold':cold})!=results['numerical_digest_sha256']),0)
    check('state_count',int(sum(len(r['history']) for r in runs.values())!=results['accepted_states']),0)
    tests=read(out/'numerical_audit.json'); check('driver_tests',sum(not t['pass'] for t in tests),0)
    check('scope',int(any(results[k] for k in ['historical_event_validated','fire_solved','heated_fracture_solved','coupled_first_law_closed','old_drivers_rerun','blender_changed'])),0)
    audit={'iteration':'V11R','status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':len(checks),'passed':sum(c['pass'] for c in checks),'states_independently_reconstructed':counted,'maxima':maxima,'failures':[c for c in checks if not c['pass']],'details':checks,'numerical_digest_sha256':results['numerical_digest_sha256']}
    if not args.read_only:
        target=out/'release_audit.json'
        if target.exists(): raise ValueError('Audit exists')
        target.write_text(json.dumps(audit,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='details'}),flush=True)
    if audit['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
