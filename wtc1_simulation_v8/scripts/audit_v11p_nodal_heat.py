"""Read-back audit. Independent balances/Gauss integration/modal BE; no model import."""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); ap.add_argument('--read-only',action='store_true'); args=ap.parse_args()
    out=(ROOT/args.output).resolve(); manifest=read(out/'offline_manifest.json'); checks=[]
    def check(name,value,limit=0): checks.append({'name':name,'value':float(value),'limit':float(limit),'pass':bool(np.isfinite(value) and value<=limit)})
    for p,h in manifest['input_sha256'].items(): check('input:'+p,int(sha(ROOT/p)!=h))
    for p,h in manifest['output_sha256'].items(): check('output:'+p,int(sha(out/p)!=h))
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11p_nodal_heat.json'); thermal=read(ROOT/cfg['thermal_configuration']); a=cfg['acceptance']
    props=thermal['constant_properties']; cpv=props['density_kg_m3']*props['specific_heat_j_kg_k']; k=props['conductivity_w_m_k']; L=thermal['geometry']['thickness_m']
    sigma=thermal['surface_exchange']['stefan_boltzmann_w_m2_k4']; offset=thermal['surface_exchange']['celsius_to_kelvin_offset']
    result=read(out/'results_v11p.json'); runs={}
    for name,summary in result['run_summaries'].items():
        run=read(out/(name+'.json')); runs[name]=run; T=np.array([p['temperature_c'] for p in run['profiles']]); x=np.array(run['x_m']); w=np.array(run['control_width_m']); history=run['history']; case=run['case']; dt=summary['dt_s']
        check(name+':shape',int(T.shape!=(summary['steps']+1,summary['nodes'])))
        check(name+':grid',np.max(np.abs(x-np.linspace(0,L,summary['nodes']))),1e-14)
        expected_w=np.full(summary['nodes'],L/summary['intervals']); expected_w[[0,-1]]/=2
        check(name+':control_widths',np.max(np.abs(w-expected_w)),1e-14)
        check(name+':total_width',abs(math.fsum(w)-L),a['total_width_absolute_m'])
        check(name+':mass',abs(summary['mass_kg_m2']-props['density_kg_m3']*L),1e-9)
        check(name+':capacity',abs(summary['heat_capacity_j_m2_k']-cpv*L),1e-7)
        components=[]
        for side,i in [('bottom',0),('top',-1)]:
            b=case[side+'_boundary']; ts=T[:,i]
            components += [b['h_w_m2_k']*(b['gas_temperature_c']-ts),b['emissivity']*sigma*((b['radiative_temperature_c']+offset)**4-(ts+offset)**4)]
        q=np.array(components).T; inside=k*np.diff(T,axis=1)/(L/summary['intervals'])
        net=np.column_stack((q[:,:2].sum(axis=1)+inside[:,0],np.diff(inside,axis=1),q[:,2:].sum(axis=1)-inside[:,-1]))
        storage=cpv*w*np.diff(T,axis=0)/dt
        local=float(np.max(np.abs(storage-net[1:])))
        H=cpv*((T-20)@w); cumulative=np.vstack((np.zeros(4),np.cumsum(q[1:]*dt,axis=0)))
        check(name+':all_nodal_balances',local,a['local_balance_absolute_w_m2'])
        check(name+':all_increment_heat',np.max(np.abs(np.diff(H)-dt*q[1:].sum(axis=1))),a['increment_heat_absolute_j_m2'])
        check(name+':all_cumulative_heat',np.max(np.abs(H-H[0]-cumulative.sum(axis=1))),a['total_heat_absolute_j_m2'])
        check(name+':saved_flux',np.max(np.abs(q-np.array([h['inward_components_w_m2'] for h in history]))),1e-8)
        check(name+':saved_enthalpy',np.max(np.abs(H-[h['enthalpy_j_m2'] for h in history])),1e-7)
        check(name+':saved_components',np.max(np.abs(cumulative-np.array([h['cumulative_components_j_m2'] for h in history]))),1e-6)
        storage_full=np.vstack((net[0],storage))
        for side,i in [('bottom',0),('top',-1)]:
            check(name+':'+side+'_storage',np.max(np.abs(storage_full[:,i]-[h[side+'_storage_w_m2'] for h in history])),1e-7)
            check(name+':'+side+'_rate',np.max(np.abs(storage_full[:,i]/(cpv*w[i])-[h[side+'_temperature_rate_k_s'] for h in history])),1e-9)
        check(name+':bottom_inside_flux',np.max(np.abs(-inside[:,0]-[h['bottom_inside_conduction_w_m2'] for h in history])),1e-8)
        check(name+':top_inside_flux',np.max(np.abs(inside[:,-1]-[h['top_inside_conduction_w_m2'] for h in history])),1e-8)
        # Two-point Gauss is exact for T, eta*T and T^2 on every linear segment.
        integrals=np.zeros((len(T),3)); eta=x/L-.5
        for z in [-1/math.sqrt(3),1/math.sqrt(3)]:
            f=(z+1)/2; tg=(1-f)*T[:,:-1]+f*T[:,1:]-20; eg=(1-f)*eta[:-1]+f*eta[1:]; weights=np.diff(x)/(2*L)
            integrals[:,0]+=tg@weights; integrals[:,1]+=(tg*eg)@weights; integrals[:,2]+=(tg*tg)@weights
        for i,key in enumerate(['mean_delta_k','first_moment_eta_k','mean_square_delta_k2']):
            check(name+':gauss_'+key,np.max(np.abs(integrals[:,i]-[h[key] for h in history])),a['square_moment_absolute_k2'] if i==2 else a['moment_absolute_k'])
        check(name+':heat_profile_integral',np.max(np.abs(H-cpv*L*integrals[:,0])),1e-7)
        check(name+':times',np.max(np.abs(np.arange(len(T))*dt-[h['time_s'] for h in history])),1e-12)
        if name.startswith('N'):
            check(name+':cold_initial',np.max(np.abs(T[0]-20)),a['initial_temperature_absolute_k'])
            check(name+':maximum_principle',max(20-T.min(),T.max()-250,0),a['maximum_principle_k'])
            check(name+':no_initial_jump',abs(H[0]),1e-12)
            check(name+':initial_storage_kind',int(history[0]['storage_rate_kind']!='INITIAL_SEMIDISCRETE_RHS'))
        else:
            check(name+':hot_initial_enthalpy_change',abs(history[0]['enthalpy_change_j_m2']),1e-12)
        if name in cfg['controls']:
            check(name+':stationary_profile',np.max(np.abs(T-T[0])),a['steady_temperature_absolute_k'])
            check(name+':stationary_flux',np.max(np.abs(net[0])),1e-7)
    convergence=read(out/'convergence.json')
    # Independent continuous eigenmode root and discrete operator/modal evolution.
    eigen=next(c for c in thermal['cases'] if c['id']=='CONVECTION_EIGENMODE_TRANSIENT'); h=eigen['top_boundary']['h_w_m2_k']; half=L/2
    low,high=0.,math.pi/2
    for _ in range(100):
        mid=(low+high)/2
        if mid*math.tan(mid)>h*half/k: high=mid
        else: low=mid
    zeta=(low+high)/2; ambient=eigen['initial']['ambient_temperature_c']; amplitude=eigen['initial']['amplitude_k']; duration=eigen['duration_s']
    for r in convergence['space']+[convergence['time_reference']]:
        n=r['intervals']; dx=L/n; x=np.linspace(0,L,n+1); widths=np.full(n+1,dx); widths[[0,-1]]/=2; C=cpv*widths
        B=np.zeros((n,n+1)); B[np.arange(n),np.arange(n)]=-1; B[np.arange(n),np.arange(1,n+1)]=1
        A=k/dx*B.T@B; A[0,0]+=h; A[-1,-1]+=h; root=np.sqrt(C)
        rates,V=np.linalg.eigh(A/root[:,None]/root[None,:]); initial=amplitude*np.cos(zeta*(x-half)/half)
        exact=ambient+(V@(np.exp(-rates*duration)*(V.T@(root*initial))))/root
        continuous=ambient+initial*np.exp(-k/cpv*(zeta/half)**2*duration)
        check('eigen_N'+str(n)+':exponential',np.max(np.abs(exact-r['semidiscrete_terminal_c'])),1e-8)
        check('eigen_N'+str(n)+':continuous',np.max(np.abs(continuous-r['continuous_terminal_c'])),1e-10)
        if n==cfg['time_reference_intervals']:
            for s in cfg['time_reference_steps']:
                be=ambient+(V@((1+rates*duration/s)**(-s)*(V.T@(root*initial))))/root
                check('BE_modal_S'+str(s),np.max(np.abs(be-runs['EIGEN_S'+str(s)]['profiles'][-1]['temperature_c'])),1e-7)
    for key,metric,limits in [('space','linf_spatial_error_k',a['space_order_range']),('time','linf_temporal_error_k',a['time_order_range'])]:
        rows=convergence[key]
        for previous,new in zip(rows,rows[1:]):
            order=math.log2(previous[metric]/new[metric]); check(key+':order',max(limits[0]-order,order-limits[1],0))
    comparisons=read(out/'cached_comparisons.json'); sensitivities=read(out/'sensitivities.json')
    for c in comparisons:
        n=c['intervals']; old=read(ROOT/cfg['cached_directory']/('C'+str(n)+'_S640.json')); new=runs['N'+str(n)+'_S640']
        i=round(c['time_s']/new['summary']['dt_s']); saved=old['history'][i]; nodal=new['history'][i]
        check('cached:N'+str(n)+':surface',abs(c['surface_difference_k']-(nodal['top_surface_temperature_c']-saved['top_surface_temperature_c'])),1e-12)
        check('cached:N'+str(n)+':heat',abs(c['enthalpy_difference_j_m2']-(nodal['enthalpy_j_m2']-saved['enthalpy_j_m2'])),1e-8)
    check('payload_digest',int(digest({'runs':runs,'convergence':convergence,'cached_comparisons':comparisons,'sensitivities':sensitivities})!=result['numerical_digest_sha256']))
    tests=read(out/'numerical_audit.json'); check('tests_all_pass',sum(not t['pass'] for t in tests))
    check('test_count',int(len(tests)!=result['test_count'] or len(tests)!=result['tests_passed']))
    check('scope_no_physical_claim',int(any(result[k] for k in ['panel_history_solved','coupled_first_law_closed','heated_fracture_solved','fire_solved','blender_changed','time_interpolation_qualified'])))
    audit={'iteration':'V11P','status':'PASS' if all(c['pass'] for c in checks) else 'FAIL','checks':len(checks),'passed':sum(c['pass'] for c in checks),'failures':[c for c in checks if not c['pass']],'details':checks,'numerical_digest_sha256':result['numerical_digest_sha256']}
    if not args.read_only:
        target=out/'release_audit.json'
        if target.exists(): raise ValueError('Do not overwrite an audit')
        target.write_text(json.dumps(audit,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k!='details'}))
    if audit['status']!='PASS': raise SystemExit(1)

if __name__=='__main__': main()
