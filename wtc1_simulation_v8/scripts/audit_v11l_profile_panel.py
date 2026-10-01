"""Independent V11L read-back: does not import the mechanical adapter."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(directory):
    manifest=read(directory/'offline_manifest.json'); result=read(directory/'results_v11l.json')
    runs=read(directory/'panel_runs.json'); comp=read(directory/'comparisons.json')
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11l_profile_panel.json')
    tests=[]
    def check(name,condition,evidence): tests.append({'name':name,'pass':bool(condition),'evidence':evidence})
    bad=[p for p,h in manifest['input_sha256'].items() if sha(ROOT/p)!=h]
    badout=[p for p,h in manifest['output_sha256'].items() if sha(directory/p)!=h]
    check('input_hashes',not bad,bad); check('output_hashes',not badout,badout)
    numerical=read(directory/'numerical_audit.json')
    check('tests_PASS',result['status']=='PASS' and all(t['pass'] for t in numerical) and
          len(numerical)==result['tests_passed']==result['test_count'],len(numerical))
    source=next(c for c in read(ROOT/cfg['thermal_cases']) if c['summary']['id']==cfg['source_case'])
    times=np.array([r['time_s'] for r in source['profiles']])
    vals=np.array([r['temperature_c'] for r in source['profiles']])-20
    checks_max={'constitutive_stress_Pa':0.,'resultant_relative':0.,'stored_relative':0.,'thermal_work_J':0.,
                'external_work_J':0.,'sensible_relative':0.,'source_mean_K':0.,'vertical_relative':0.,
                'total_energy_relative':0.,'mapped_gradient_K':0.,'source_projection_K':0.}
    for run in runs+[r['run'] for r in comp]:
        sec={k:np.array(v) for k,v in run['section'].items()}
        y,A,E,alpha,rho,cp=[sec[k] for k in ('y','area','E','alpha','density','cp')]
        B=np.column_stack([np.ones(len(y)),-y]); weights=np.array(run['longitudinal_weights_m'])
        old=None; wth=wext=0.
        for row in run['history']:
            q=np.array(row['section_q']); dt=np.array(row['fiber_delta_temperature_k'])
            em=q@B.T-alpha*dt
            stress=E*em
            stored=float(weights@(.5*(stress*em)@A))+row['spring_stored_J']
            sensible=float(weights.sum()*np.sum(A*rho*cp*dt))
            checks_max['stored_relative']=max(checks_max['stored_relative'],abs(stored-row['stored_J'])/max(1,stored))
            checks_max['sensible_relative']=max(checks_max['sensible_relative'],abs(sensible-row['sensible_enthalpy_J'])/max(1,abs(sensible)))
            if old is not None:
                prev,prevstress,prevdt=old
                wth-=float(np.sum(weights[:,None]*A*(stress+prevstress)/2*alpha*(dt-prevdt)))
                wext+=(row['gravity']+prev['gravity'])/2*(row['unit_gravity_displacement_work_J']-prev['unit_gravity_displacement_work_J'])
            checks_max['thermal_work_J']=max(checks_max['thermal_work_J'],abs(wth-row['thermal_work_J']))
            checks_max['external_work_J']=max(checks_max['external_work_J'],abs(wext-row['external_work_J']))
            checks_max['total_energy_relative']=max(checks_max['total_energy_relative'],abs(stored-wth-wext)/max(1,stored,abs(wth),abs(wext)))
            checks_max['vertical_relative']=max(checks_max['vertical_relative'],abs(row['seat_vertical_reaction_N']-row['gravity_load_N'])/max(1,row['gravity_load_N']))
            if run['mode'] in ('profile','uniform'):
                t=row['profile_time_coordinate_s']; j=min(len(times)-2,max(0,np.searchsorted(times,t,side='right')-1))
                f=(t-times[j])/(times[j+1]-times[j]); mean=float(np.mean((1-f)*vals[j]+f*vals[j+1]))
                # Concrete fibers precede the two reinforcement layers.
                checks_max['source_mean_K']=max(checks_max['source_mean_K'],abs(mean-float(np.mean(dt[:-2]))))
                raw=(1-f)*vals[j]+f*vals[j+1]
                if run['mode']=='uniform': raw=np.full_like(raw,mean)
                centres=np.array(source['profiles'][0]['x_m']); length=2*centres[0]*len(centres)
                x=np.r_[0,centres,length]
                temperature=np.r_[1.5*raw[0]-.5*raw[1],raw,1.5*raw[-1]-.5*raw[-2]]
                integral=float(np.sum(np.diff(x)*(temperature[:-1]+temperature[1:])/2))/length
                if abs(integral)>1e-14: temperature*=mean/integral
                checks_max['source_projection_K']=max(checks_max['source_projection_K'],float(np.max(abs(temperature-np.array(row['mapping']['delta_k'])))))
                # Independent two-point Gauss integration of eta*T is exact on each segment.
                m1=0.
                for xa,xb,ta,tb in zip(x[:-1],x[1:],temperature[:-1],temperature[1:]):
                    for z in (-1/np.sqrt(3),1/np.sqrt(3)):
                        xx=(xa+xb)/2+z*(xb-xa)/2
                        tt=(ta+tb)/2+z*(tb-ta)/2
                        m1+=(xx/length-.5)*tt*(xb-xa)/(2*length)
                eta=y[:-2]/length
                mapped=float(np.mean(eta*dt[:-2])/np.mean(eta**2))
                checks_max['mapped_gradient_K']=max(checks_max['mapped_gradient_K'],abs(mapped-12*m1))
            old=(row,stress,dt)
        q=np.array(run['terminal_section_q']); dt=np.array(run['terminal_fiber_temperature_k'])
        stress=E*(q@B.T-alpha*dt)
        expected=np.array(run['terminal_fiber_stress_pa'])
        checks_max['constitutive_stress_Pa']=max(checks_max['constitutive_stress_Pa'],float(np.max(abs(stress-expected))))
        force=(stress*A)@B
        expected=np.array(run['terminal_section_resultants'])
        checks_max['resultant_relative']=max(checks_max['resultant_relative'],float(np.max(abs(force-expected)))/max(1,float(np.max(abs(force)))))
        bracket=run['guard_bracket']
        check('guard_'+run['mode']+'_'+str(len(tests)),bracket is None or
              bracket['accepted_DCR']<.9<=bracket['rejected_DCR'] and not bracket['rejected_committed'],bracket)
    limits={'constitutive_stress_Pa':1e-6,'resultant_relative':1e-10,'stored_relative':1e-10,'thermal_work_J':1e-6,
            'external_work_J':1e-6,'sensible_relative':1e-10,'source_mean_K':1e-10,
            'vertical_relative':1e-8,'total_energy_relative':2e-8,'mapped_gradient_K':1e-10,'source_projection_K':1e-10}
    for key,value in checks_max.items(): check(key,value<=limits[key],{'value':value,'limit':limits[key]})
    sections=read(directory/'section_controls.json')
    payload={'runs':runs,'comparisons':comp,'sections':sections}
    dig=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
    check('numerical_digest',dig==result['numerical_digest_sha256'],dig)
    check('scope',result['one_way_profile_transfer'] and not result['coupled_first_law_closed'] and
          not result['heated_fracture_solved'] and not result['fire_solved'] and result['global_energy_credit_J']==0,
          {'one_way':True,'thermodynamic_feedback':False})
    lowest=min(min(row['fiber_delta_temperature_k']) for run in runs for row in run['history'])
    check('no_undershoot',lowest>=-1e-10,lowest)
    return {'iteration':'V11L','status':'PASS' if all(t['pass'] for t in tests) else 'FAIL',
            'audit_count':len(tests),'audits_passed':sum(t['pass'] for t in tests),'checks':tests}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); p.add_argument('--read-only',action='store_true'); args=p.parse_args()
    directory=(ROOT/args.output).resolve()
    cfg=read(ROOT/'wtc1_simulation_v8/data/v11l_profile_panel.json')
    if not any(directory==r or r in directory.parents for r in [(ROOT/cfg[k]).resolve() for k in ('scratch_directory','output_directory')]):
        raise ValueError('Outside V11L roots')
    result=audit(directory)
    if not args.read_only:
        target=directory/'release_audit.json'
        if target.exists(): raise FileExistsError(target)
        target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'checks':result['audit_count'],'failed':[t for t in result['checks'] if not t['pass']]}))
    if result['status']!='PASS': raise SystemExit(1)
