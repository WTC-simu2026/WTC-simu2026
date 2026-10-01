"""Independent read-back, no conduction, panel or transfer implementation imported."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def audit(out):
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11m_early_thermal.json')
    kc=read(ROOT/cfg['thermal_configuration']); case=read(out/'source_manifest.json')['case']
    result=read(out/'results_v11m.json'); manifest=read(out/'offline_manifest.json')
    tests=[]
    def check(n,c,e): tests.append({'name':n,'pass':bool(c),'evidence':e})
    def near(n,v,limit): check(n,v<=limit,{'value':float(v),'limit':limit})
    check('input_hashes',all(sha(ROOT/p)==h for p,h in manifest['input_sha256'].items()),len(manifest['input_sha256']))
    check('output_hashes',all(sha(out/p)==h for p,h in manifest['output_sha256'].items()),len(manifest['output_sha256']))
    numerical=read(out/'numerical_audit.json')
    check('numerical_checks',result['status']=='PASS' and all(t['pass'] for t in numerical)
          and len(numerical)==result['tests_passed']==result['test_count'],len(numerical))
    thermal={}; rho_cp=kc['constant_properties']['volumetric_heat_capacity_j_m3_k']
    conductivity=kc['constant_properties']['conductivity_w_m_k']; length=kc['geometry']['thickness_m']
    thermal_max={k:0. for k in ('surface_flux','surface_balance','local_cell_balance','increment_heat','total_heat','enthalpy','component_ledger')}
    for job in cfg['thermal_jobs']:
        saved=read(out/(job['id']+'.json')); thermal[job['id']]=saved
        history=saved['history']; profiles=saved['profiles']; dt=cfg['duration_s']/job['steps']; dx=length/job['cells']
        check(job['id']+'_grid',len(history)==len(profiles)==job['steps']+1 and
              all(abs(row['time_s']-i*dt)<1e-10 and row['step']==i for i,row in enumerate(history)),len(history))
        cumulative=np.zeros(4); oldT=None; oldH=0.
        for row,profile in zip(history,profiles):
            temp=np.array(profile['temperature_c']); enthalpy=float(rho_cp*dx*np.sum(temp-20))
            thermal_max['enthalpy']=max(thermal_max['enthalpy'],abs(enthalpy-row['enthalpy_j_m2']))
            fluxes=[]
            for face,index in [('bottom',0),('top',-1)]:
                b=case[face+'_boundary']; ts=row[face+'_surface_temperature_c']
                conv=b['h_w_m2_k']*(b['gas_temperature_c']-ts)
                rad=b['emissivity']*5.670374419e-8*((b['radiative_temperature_c']+273.15)**4-(ts+273.15)**4)
                fluxes.extend([conv,rad])
                thermal_max['surface_flux']=max(thermal_max['surface_flux'],
                    abs(conv-row[face+'_convective_inward_flux_w_m2']),abs(rad-row[face+'_radiative_inward_flux_w_m2']))
                thermal_max['surface_balance']=max(thermal_max['surface_balance'],abs(conv+rad-2*conductivity*(ts-temp[index])/dx))
            fluxes=np.array(fluxes)
            if oldT is not None:
                cumulative+=dt*fluxes
                flux=conductivity*np.diff(temp)/dx
                net=np.r_[flux[0]+sum(fluxes[:2]),np.diff(flux),sum(fluxes[2:])-flux[-1]]
                residual=rho_cp*dx*(temp-oldT)/dt-net
                thermal_max['local_cell_balance']=max(thermal_max['local_cell_balance'],float(np.max(abs(residual))))
                thermal_max['increment_heat']=max(thermal_max['increment_heat'],abs(enthalpy-oldH-dt*sum(fluxes)))
            stored=np.array([row['cumulative_'+face+'_'+kind+'_j_m2'] for face in ('bottom','top') for kind in ('convective','radiative')])
            thermal_max['component_ledger']=max(thermal_max['component_ledger'],float(np.max(abs(cumulative-stored))))
            thermal_max['total_heat']=max(thermal_max['total_heat'],abs(enthalpy-sum(cumulative)))
            if np.min(temp)<20-1e-8 or np.max(temp)>250+1e-8: raise ValueError('Thermal maximum principle')
            oldT,oldH=temp,enthalpy
        near(job['id']+'_terminal_summary',abs(oldH-saved['summary']['enthalpy_change_j_m2']),1e-7)
    for key,v in thermal_max.items(): near('thermal_'+key,v,1e-6 if key in ('surface_flux','surface_balance','local_cell_balance') else 1e-4)
    runs=read(out/'panel_runs.json'); comparisons=read(out/'comparisons.json')
    mx={k:0. for k in ('stored_relative','sensible_relative','thermal_work_J','external_work_J',
                       'total_energy_relative','vertical_relative','source_mean_K','projection_K',
                       'equivalent_gradient_K','constitutive_stress_Pa','resultant_relative','screen_DCR')}
    for run in runs:
        sec={k:np.array(v) for k,v in run['section'].items()}
        y,A,E,alpha,rho,cp=[sec[k] for k in ('y','area','E','alpha','density','cp')]
        weights=np.array(run['longitudinal_weights_m']); B=np.column_stack([np.ones(len(y)),-y])
        source=thermal[run['thermal_job']]; alltimes=np.array([p['time_s'] for p in source['profiles']])
        stride=round(run['snapshot_interval_s']/(alltimes[1]-alltimes[0])); selected=np.arange(0,len(alltimes),stride)
        times=alltimes[selected]; values=np.array([source['profiles'][i]['temperature_c'] for i in selected])-20
        centres=np.array(source['profiles'][0]['x_m']); x=np.r_[0,centres,length]
        previous=None; wth=wext=0.
        for row in run['history']:
            q=np.array(row['section_q']); delta=np.array(row['fiber_delta_temperature_k'])
            em=q@B.T-alpha*delta; stress=E*em
            stored=float(weights@(.5*(stress*em)@A))+row['spring_stored_J']
            sensible=float(weights.sum()*np.sum(A*rho*cp*delta))
            mx['stored_relative']=max(mx['stored_relative'],abs(stored-row['stored_J'])/max(1,stored))
            mx['sensible_relative']=max(mx['sensible_relative'],abs(sensible-row['sensible_enthalpy_J'])/max(1,abs(sensible)))
            if previous is not None:
                old,oldstress,olddelta=previous
                wth-=float(np.sum(weights[:,None]*A*(stress+oldstress)/2*alpha*(delta-olddelta)))
                wext+=(row['gravity']+old['gravity'])/2*(row['unit_gravity_displacement_work_J']-old['unit_gravity_displacement_work_J'])
            mx['thermal_work_J']=max(mx['thermal_work_J'],abs(wth-row['thermal_work_J']))
            mx['external_work_J']=max(mx['external_work_J'],abs(wext-row['external_work_J']))
            mx['total_energy_relative']=max(mx['total_energy_relative'],abs(stored-wth-wext)/max(1,stored,abs(wth),abs(wext)))
            mx['vertical_relative']=max(mx['vertical_relative'],abs(row['seat_vertical_reaction_N']-row['gravity_load_N'])/max(1,row['gravity_load_N']))
            t=row['profile_time_coordinate_s']; j=min(len(times)-2,max(0,np.searchsorted(times,t,side='right')-1))
            fraction=(t-times[j])/(times[j+1]-times[j])
            raw=(1-fraction)*values[j]+fraction*values[j+1]
            if run['mode']=='cold': raw=np.zeros_like(raw)
            temp=np.r_[1.5*raw[0]-.5*raw[1],raw,1.5*raw[-1]-.5*raw[-2]]
            mean=float(np.mean(raw)); integral=float(np.sum(np.diff(x)*(temp[:-1]+temp[1:])/2)/length)
            if abs(integral)>1e-14: temp*=mean/integral
            mx['projection_K']=max(mx['projection_K'],float(np.max(abs(temp-np.array(row['mapping']['delta_k'])))))
            mx['source_mean_K']=max(mx['source_mean_K'],abs(float(np.mean(delta[:-2]))-mean))
            m1=0.
            for z in (-1/np.sqrt(3),1/np.sqrt(3)):
                gx=(x[:-1]+x[1:])/2+z*np.diff(x)/2
                gt=(temp[:-1]+temp[1:])/2+z*np.diff(temp)/2
                m1+=float(np.sum((gx/length-.5)*gt*np.diff(x)/(2*length)))
            eta=y[:-2]/length
            mx['equivalent_gradient_K']=max(mx['equivalent_gradient_K'],abs(float(np.mean(eta*delta[:-2])/np.mean(eta**2))-12*m1))
            if min(delta)<-1e-10: raise ValueError('Cold undershoot in transfer')
            previous=row,stress,delta
        q=np.array(run['terminal_section_q']); delta=np.array(run['terminal_fiber_temperature_k'])
        stress=E*(q@B.T-alpha*delta)
        mx['constitutive_stress_Pa']=max(mx['constitutive_stress_Pa'],float(np.max(abs(stress-np.array(run['terminal_fiber_stress_pa'])))))
        force=(stress*A)@B
        mx['resultant_relative']=max(mx['resultant_relative'],float(np.max(abs(force-np.array(run['terminal_section_resultants']))))/max(1,float(np.max(abs(force)))))
        probes=run['terminal_probes']; pq=np.array(probes['q']); py=np.array(probes['concrete_y_m']); pt=np.array(probes['concrete_delta_k'])
        cs=E[0]*(pq[:,0,None]-pq[:,1,None]*py-alpha[0]*pt)
        ss=E[-2:]*(pq[:,0,None]-pq[:,1,None]*y[-2:]-alpha[-2:]*delta[-2:])
        dcr=[max(0,float(np.max(cs)))/probes['ft_pa'],max(0,float(-np.min(cs)))/probes['fc_pa'],float(np.max(abs(ss)))/probes['fy_pa']]
        mx['screen_DCR']=max(mx['screen_DCR'],max(abs(v-r['DCR']) for v,r in zip(dcr,probes['screens'])))
        bracket=run['guard_bracket']
        check(run['id']+'_guard', (run['mode']=='cold' and bracket is None) or (bracket is not None and
              bracket['accepted_DCR']<.9<=bracket['rejected_DCR'] and not bracket['rejected_committed'] and
              bracket['rejected_time_s']-bracket['accepted_time_s']<=1e-6),bracket)
        near(run['id']+'_cold_initial',float(np.max(abs(run['history'][0]['fiber_delta_temperature_k']))),1e-12)
    limits={'stored_relative':1e-10,'sensible_relative':1e-10,'thermal_work_J':1e-6,'external_work_J':1e-6,
            'total_energy_relative':2e-8,'vertical_relative':1e-8,'source_mean_K':1e-10,'projection_K':1e-10,
            'equivalent_gradient_K':1e-10,'constitutive_stress_Pa':1e-6,'resultant_relative':1e-10,'screen_DCR':1e-10}
    for key,v in mx.items(): near(key,v,limits[key])
    by={r['id']:r for r in runs}
    for c in comparisons:
        ta=by[c['coarse_or_baseline']]['terminal']['profile_time_coordinate_s']
        tb=by[c['fine_or_alternative']]['terminal']['profile_time_coordinate_s']
        near('comparison_'+str(len(tests)),abs(c['relative_guard_change']-abs(ta-tb)/tb),1e-14)
    payload={'runs':runs,'comparisons':comparisons,'thermal_summaries':{k:v['summary'] for k,v in thermal.items()}}
    dig=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
    check('numerical_digest',dig==result['numerical_digest_sha256'],dig)
    check('scope',result['one_way_profile_transfer'] and not result['coupled_first_law_closed'] and
          not result['surface_remap_validated'] and not result['fire_solved'] and not result['heated_fracture_solved'] and
          result['global_energy_credit_J']==0 and not result['blender_changed'],True)
    return {'iteration':'V11M','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL',
            'audit_count':len(tests),'audits_passed':sum(t['pass'] for t in tests),'checks':tests}


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--read-only',action='store_true'); args=p.parse_args()
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11m_early_thermal.json'); out=(ROOT/args.output).resolve()
    if not any(out==r or r in out.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]):
        raise ValueError('Outside V11M roots')
    result=audit(out)
    if not args.read_only:
        target=out/'release_audit.json'
        if target.exists(): raise FileExistsError(target)
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':result['audit_count'],'failed':[t for t in result['checks'] if not t['pass']]}))
    if result['status']!='PASS': raise SystemExit(1)
