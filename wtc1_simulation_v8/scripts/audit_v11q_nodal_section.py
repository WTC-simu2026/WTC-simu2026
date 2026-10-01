"""Independent saved-data audit; no production section imports or conduction runs."""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def integrate(x,t,inv,q):
    """Two-point Gauss independently recovers stiffness, eigenloads, energy and stress."""
    h=inv['h']; Ac=inv['Ac']; Ec=inv['Ec']; ac=inv['alphac']; ys=np.array(inv['ys'])
    As=np.array(inv['As']); Es=np.array(inv['Es']); als=np.array(inv['alphas'])
    K=np.zeros((2,2)); f=np.zeros(2); S=U=sensible=0.; mom=np.zeros(3)
    for z in [-1/math.sqrt(3),1/math.sqrt(3)]:
        r=(z+1)/2; xx=(1-r)*x[:-1]+r*x[1:]; tt=(1-r)*t[:-1]+r*t[1:]; weights=np.diff(x)/(2*h)
        y=xx-h/2; B=np.column_stack((np.ones(len(y)),-y)); dA=Ac*weights
        K+=B.T@((Ec*dA)[:,None]*B); f+=B.T@(Ec*dA*ac*tt); S+=float(np.sum(Ec*dA*(ac*tt)**2))
        eps=B@q-ac*tt; U+=float(np.sum(.5*Ec*dA*eps**2)); sensible+=float(np.sum(dA*inv['rhoc']*inv['cpc']*tt))
        mom += [float(weights@tt),float(weights@(tt*y/h)),float(weights@(tt*tt))]
    Ts=np.interp(ys+h/2,x,t); Bs=np.column_stack((np.ones(len(ys)),-ys)); EA=Es*As
    K+=Bs.T@(EA[:,None]*Bs); f+=Bs.T@(EA*als*Ts); S+=float(np.sum(EA*(als*Ts)**2))
    epss=Bs@q-als*Ts; U+=float(np.sum(.5*EA*epss**2)); sensible+=float(np.sum(As*np.array(inv['rhos'])*np.array(inv['cps'])*Ts))
    stress=Ec*(q[0]-(x-h/2)*q[1]-ac*t); steels=Es*epss
    ratios=[max(0,float(stress.max()))/inv['ft'],max(0,float((-stress).max()))/inv['fc'],float(np.max(np.abs(steels),initial=0))/inv['fy']]
    return {'K':K,'f':f,'S':S,'U':U,'sensible':sensible,'mom':mom,'Ts':Ts,'stress':stress,'steels':steels,'ratios':ratios}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--read-only',action='store_true'); args=ap.parse_args()
    out=(ROOT/args.output).resolve(); manifest=read(out/'offline_manifest.json'); checks=[]
    def check(name,value,limit): checks.append({'name':name,'value':float(value),'limit':float(limit),'pass':bool(np.isfinite(value) and value<=limit)})
    for p,h in manifest['input_sha256'].items(): check('input:'+p,int(sha(ROOT/p)!=h),0)
    for p,h in manifest['output_sha256'].items(): check('output:'+p,int(sha(out/p)!=h),0)
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11q_nodal_section.json'); inv=read(out/'section_inventory.json'); paths=read(out/'section_paths.json'); result=read(out/'results_v11q.json')
    sources={n:read(ROOT/cfg['source_directory']/(n+'.json')) for n in cfg['source_jobs']}
    maxima={k:0. for k in ['stiffness_relative','force_relative','energy_relative','S_relative','sensible_relative','stress_pa','reaction_relative','guard_ratio','moment_k','square_k2','ledger_relative','heat_j_m2','strain','steel_temperature_k']}
    count=0
    for path in paths:
        source=sources[path['job']]; x=np.array(source['x_m']); Wth=Wext=0.; previous=None
        check(path['job']+path['mode']+':steps_consecutive',int([r['step'] for r in path['history']]!=list(range(len(path['history'])))),0)
        for row in path['history']+([path['rejected_trial']] if path['rejected_trial'] else []):
            count+=1; p=source['profiles'][row['step']]; h=source['history'][row['step']]; t=np.array(p['temperature_c'])-20; q=np.array(row['q']); calc=integrate(x,t,inv,q)
            K=calc['K']; f=calc['f']; R=K@q-f
            maxima['stiffness_relative']=max(maxima['stiffness_relative'],float(np.max(np.abs(K-inv['K'])))/np.max(np.abs(K)))
            maxima['force_relative']=max(maxima['force_relative'],float(np.max(np.abs(f-row['thermal_force_N_Nm'])))/max(1,np.max(np.abs(f))))
            maxima['energy_relative']=max(maxima['energy_relative'],abs(calc['U']-row['stored_J_per_m'])/max(1,abs(calc['U'])))
            maxima['S_relative']=max(maxima['S_relative'],abs(calc['S']-row['thermal_square_energy_S_J_per_m'])/max(1,abs(calc['S'])))
            maxima['sensible_relative']=max(maxima['sensible_relative'],abs(calc['sensible']-row['sensible_J_per_m'])/max(1,abs(calc['sensible'])))
            maxima['stress_pa']=max(maxima['stress_pa'],float(np.max(np.abs(calc['stress']-row['concrete_knot_stress_pa']))),float(np.max(np.abs(calc['steels']-row['steel_stress_pa']),initial=0)),float(np.max(np.abs(calc['stress'][[0,-1]]-row['face_stress_pa']))))
            maxima['guard_ratio']=max(maxima['guard_ratio'],float(np.max(np.abs(np.array(calc['ratios'])-row['cold_strength_ratios']))),abs(max(calc['ratios'])-row['maximum_cold_strength_ratio']))
            maxima['moment_k']=max(maxima['moment_k'],abs(calc['mom'][0]-row['mean_delta_k']),abs(calc['mom'][1]-row['first_moment_eta_k']))
            maxima['square_k2']=max(maxima['square_k2'],abs(calc['mom'][2]-row['mean_square_delta_k2']))
            maxima['steel_temperature_k']=max(maxima['steel_temperature_k'],float(np.max(np.abs(calc['Ts']-row['steel_delta_k']),initial=0)))
            maxima['strain']=max(maxima['strain'],float(np.max(np.abs(inv['alphac']*t-row['concrete_thermal_strain_at_knots']))),float(np.max(np.abs(np.array(inv['alphas'])*calc['Ts']-row['steel_thermal_strain']),initial=0)))
            reaction=-R if path['mode']=='FULLY_RESTRAINED' else np.zeros(2)
            equilibrium=R if path['mode']=='FREE' else q
            maxima['reaction_relative']=max(maxima['reaction_relative'],float(np.max(np.abs(reaction-row['support_reaction_N_Nm'])))/max(1,np.max(np.abs(f))),float(np.max(np.abs(R-row['resultant_N_Nm'])))/max(1,np.max(np.abs(f))),float(np.max(np.abs(equilibrium)))/max(1,np.max(np.abs(f))))
            gross=inv['width']*h['enthalpy_j_m2']; gap=calc['sensible']-gross
            maxima['heat_j_m2']=max(maxima['heat_j_m2'],abs(inv['h']*2160000*calc['mom'][0]-h['enthalpy_j_m2']))
            check(path['job']+path['mode']+':heat_gap_'+str(row['step']),abs(gap-row['composite_minus_gross_J_per_m']),1e-7)
            check(path['job']+path['mode']+':time_'+str(row['step']),abs(row['time_s']-p['time_s']),1e-12)
            if row['committed']:
                check('guard_committed',max(calc['ratios'])-cfg['cold_strength_guard'],1e-12)
                if previous is not None:
                    oq,of,oR,oS=previous; Wth+=float(-.5*(oq+q)@(f-of)+.5*(calc['S']-oS)); Wext+=float(.5*(oR+R)@(q-oq))
                scale=max(1,abs(Wth),abs(Wext),abs(calc['U']))
                maxima['ledger_relative']=max(maxima['ledger_relative'],abs(calc['U']-Wth-Wext)/scale,abs(Wth-row['thermal_work_J_per_m'])/scale,abs(Wext-row['external_work_J_per_m'])/scale)
                previous=q,f,R,calc['S']
            else: check('guard_rejected',int(max(calc['ratios'])<=cfg['cold_strength_guard']),0)
        rejected=path['rejected_trial']
        check('guard_stops_at_first_rejection',int(rejected is not None and rejected['step']!=len(path['history'])),0)
        check('path_terminal_summary',int(path['last_committed_time_s']!=path['history'][-1]['time_s']),0)
        check('path_completion',int(path['completed_to_source_end']!=(len(path['history'])==len(source['profiles']))),0)
    for key,value in maxima.items(): check('independent_max:'+key,value,1e-6 if key=='stress_pa' else 1e-4 if key=='heat_j_m2' else 1e-8 if key=='square_k2' else 1e-10)
    controls=read(out/'closed_form_controls.json'); cold=read(out/'cold_comparison.json'); comparisons=read(out/'comparisons.json')
    for c in controls:
        v=c['inventory']; a,b=c['bottom_delta_k'],c['top_delta_k']; mean=(a+b)/2; delta=b-a
        expected_q=v['alphac']*np.array([mean,-delta/v['h']]) if c['mode']=='FREE' else np.zeros(2)
        expected_U=0 if c['mode']=='FREE' else v['Ec']*v['Ac']*v['alphac']**2*(a*a+a*b+b*b)/6
        check(c['id']+c['mode']+':analytic_q',np.max(np.abs(expected_q-c['state']['q'])),1e-12)
        check(c['id']+c['mode']+':analytic_U',abs(expected_U-c['state']['stored_J_per_m']),1e-9)
    for c in comparisons:
        a,b=[next(r for r in next(p for p in paths if p['job']==job and p['mode']==c['mode'])['history'] if r['time_s']==c['time_s']) for job in [c['coarse'],c['fine']]]
        check('comparison_q',np.max(np.abs(np.array(b['q'])-a['q']-c['q_difference'])),1e-12)
        check('comparison_reaction',np.max(np.abs(np.array(b['support_reaction_N_Nm'])-a['support_reaction_N_Nm']-c['reaction_difference_N_Nm'])),1e-8)
        check('comparison_U',abs((b['stored_J_per_m']-a['stored_J_per_m'])/max(1e-30,abs(b['stored_J_per_m']))-c['stored_relative_difference']),1e-12)
    correction=inv['Ec']*inv['Ac']*inv['h']**2/(12*cold['midpoint_fibers']**2)
    check('cold_K_correction',abs((np.array(cold['continuous_K'])-cold['midpoint_K'])[1,1]-correction)/inv['K'][1][1],1e-10)
    payload={'paths':paths,'controls':controls,'cold':cold,'comparisons':comparisons,'inventory':inv}
    check('payload_digest',int(digest(payload)!=result['numerical_digest_sha256']),0)
    tests=read(out/'numerical_audit.json'); check('all_driver_tests',sum(not t['pass'] for t in tests),0)
    check('test_counts',int(len(tests)!=result['test_count'] or len(tests)!=result['tests_passed']),0)
    check('scope',int(any(result[k] for k in ['conduction_rerun','panel_history_solved','heated_fracture_solved','coupled_first_law_closed','fire_solved','blender_changed','temporal_interpolation_qualified'])),0)
    audit={'iteration':'V11Q','status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':len(checks),'passed':sum(c['pass'] for c in checks),'states_independently_integrated':count,'maxima':maxima,'failures':[c for c in checks if not c['pass']],'details':checks,'numerical_digest_sha256':result['numerical_digest_sha256']}
    if not args.read_only:
        p=out/'release_audit.json'
        if p.exists(): raise ValueError('Do not overwrite audit')
        p.write_text(json.dumps(audit,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='details'}))
    if audit['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
