"""Evaluate actual loaded fields, impulses and work; no pass from exit0 alone."""
from probe_aircraft_a62_surface import ROOT,OUT,CONTROL,RUNTIME,engine,read,dump,sha,now,rel
from material_aircraft_a60 import run_path,path_values
from audit_aircraft_a05 import histories
from recover_aircraft_a05_history import records
from probe_aircraft_a37 import vtk
import tarfile,hashlib,numpy as np,json,re,subprocess,time,argparse

def declare_review():
    engine();assert not (OUT/'loaded_review_predeclaration.json').exists()
    rows=[]
    with tarfile.open(ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate/source.tar.gz') as t:
        for suffix in ['engine/source/output/th/bcs1th_imp.F','engine/source/output/th/thnod.F']:
            n=next(n for n in t.getnames() if n.endswith('/'+suffix));raw=t.extractfile(n).read();lines=raw.decode('utf8').splitlines()
            rows.append({'path':suffix,'sha256':hashlib.sha256(raw).hexdigest(),'anchors':[{'line':i+1,'keyword':'FTHREAC'} for i,l in enumerate(lines) if 'FTHREAC' in l and ('DT3' in l or 'WA(IJK)' in l)]})
    dump(OUT/'loaded_review_predeclaration.json',{'created_utc':now(),'source_units':rows,'reaction_contract':'BCS1TH_IMP accumulates force times DT3/2, including previous force; THNOD writes FTHREAC. Thus recorded REAC is integrated impulse, not direct force.','acceptance':read(CONTROL)['acceptance'],'terminal_clock_interval':'[requested_end-1e-6ms,requested_end+declared_maximum_dt+1e-6ms], actual clock unchanged','end_motion_reference':'curve at requested_end, constant beyond end','elastic_energy_scale':'maximum analytical stored elastic energy along declared imposed path','damage_energy_scale':'mixed power-law G when proportional, otherwise max(GI,GII)*area','no_native_runs_for_analysis':True,'whole_credit_s':0})

def review(stage):
    engine();cfg=read(CONTROL);p=cfg['cohesive'];lim=cfg['acceptance'];execution=read(OUT/(stage+'_execution_review.json'));rows=[]
    available={r['case']:r for r in execution['cases']}
    for case in [c for c in cfg['cases'] if c['stage']==stage]:
        if case['id'] not in available:
            rows.append({'case':case['id'],'pass':False,'not_executed_after_prior_stop':True});continue
        d=OUT/'native'/case['id'];name=read(d/'generation.json')['name'];e=available[case['id']];csv=d/(name+'T01.csv')
        if e['parent_exit_code']!=0 or not e['normal_termination'] or not e['no_USER_BREAK_or_STOP'] or not csv.exists():
            rows.append({'case':case['id'],'pass':False,'completion':e,'loaded_response_not_obtained':True});continue
        H=histories(csv);T=H['time'];V=np.column_stack(list(H.values()));rr=records(d/(name+'T01'))
        assert len(T)>3 and np.all(np.diff(T)>0)
        nr=next(n for n in range(3,10) if sum(map(len,rr[-n:]))==V.shape[1]*4 and len(rr[-n])==4);header=len(rr)-len(T)*nr
        frames=[rr[header+k*nr:header+(k+1)*nr] for k in range(len(T))]
        binary=np.asarray([np.concatenate([np.frombuffer(v,dtype='>f4').astype(float) for v in f]) for f in frames]);binary_ok=binary.shape==V.shape and np.allclose(binary,V,rtol=6e-7,atol=1e-12)
        N=np.stack([np.column_stack([v for k,v in H.items() if k.startswith('REACTION_'+axis)]).reshape(len(T),8,3) for axis in 'XYZ'],axis=-1)
        q=N[:,4:,0,:].mean(axis=1);uniform=float(abs(N[:,4:,0,:]-q[:,None,:]).max());impulse=N[:,:4,2,:].sum(axis=1);forces=-np.gradient(impulse,T,axis=0)
        area=case['L_mm']**2;traction,state,limits=run_path(q,p);reference=area*traction;strengths=area*np.array([p['TT_MPa'],p['TT_MPa'],p['TN_MPa']]);force_error=float((abs(forces-reference)/strengths).max())
        expected=path_values(np.minimum(T,case['end_ms']),case,p);motion=float(abs(q-expected).max())
        EW=H['EXTERNAL WORK']*.001;IE=H['INTERNAL ENERGY']*.001;KE=H['KINETIC ENERGY']*.001;residual=IE+KE+H['ROTATION ENERGY']*.001+H['HOURGLASS ENERGY']*.001-EW;residual-=residual[0]
        work=float(np.sum((N[1:,:,1,:]+N[:-1,:,1,:])*.5*np.diff(N[:,:,2,:],axis=0))*.001)
        model_work=np.r_[0,np.cumsum(np.sum((reference[1:]+reference[:-1])*.5*np.diff(q,axis=0),axis=1)*.001)]
        expected_G=None
        domain=case.get('model_domain',stage)
        if domain=='elastic':
            commanded=np.asarray(case['knot_gaps_mm']);target=float(.5*area*np.max(np.sum(commanded**2*np.array([p['ET_N_mm3'],p['ET_N_mm3'],p['EN_N_mm3']]),axis=1))*.001)
        elif case.get('proportional'):
            direction=np.asarray(case['direction']);kn=p['EN_N_mm3']*direction[2]**2;ks=p['ET_N_mm3']*np.sum(direction[:2]**2);wn=kn/(kn+ks);ws=1-wn;g=p['power_exponent'];expected_G=((wn/p['GI_N_mm'])**g+(ws/p['GII_N_mm'])**g)**(-1/g);target=expected_G*area*.001
        else:target=max(p['GI_N_mm'],p['GII_N_mm'])*area*.001
        last=sorted(q for q in d.glob(name+'A*') if re.fullmatch(re.escape(name)+r'A\d{3}',q.name))[-1]
        start=time.perf_counter();converted=subprocess.run([str(RUNTIME/'anim_to_vtk_win64.exe'),str(last)],capture_output=True,check=True,timeout=60);(d/'final_state.vtk').write_bytes(converted.stdout)
        dump(d/'final_state_conversion.json',{'created_utc':now(),'exit_code':converted.returncode,'wall_s':time.perf_counter()-start,'cap_s':60,'native_animation':rel(last),'sha256':sha(last)})
        field=vtk(converted.stdout.decode('utf8'));U=field['Displacement'].reshape(-1,3)[np.argsort(field['NODE_ID'])];end=float(field['time']);final_target=np.asarray(case['knot_gaps_mm'][-1]);endmotion=float(abs(U[4:]-final_target).max())
        checks={'normal_native_completion':e['normal_termination'] and e['no_USER_BREAK_or_STOP'],'binary_all_channels_agree':binary_ok,'native_load_nonzero':np.max(abs(q))>1e-4,'native_final_clock_reaches_requested_end':end>=case['end_ms']-1e-6,'native_overshoot_within_one_declared_step':end<=case['end_ms']+case['dt_cap_ms']+1e-6,
          'reference_uniform_top_motion':uniform<=lim['prescribed_motion_mm'],'prescribed_and_free_axes_motion':motion<=lim['prescribed_motion_mm'],'final_field_motion':endmotion<=lim['prescribed_motion_mm'],'fixed_bottom_fields':bool(np.all(U[:4]==0)),
          'mass_8g':bool(np.allclose(H['MASS'],8,rtol=1e-6,atol=1e-6)),'no_added_mass':bool(np.all(H['ADDED MASS']==0)),'native_three_axis_traction':force_error<=lim['traction_maximum_relative'],
          'global_work_energy':float(abs(residual).max())<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'native_impulse_work':abs(work-EW[-1])<=lim['work_energy_fraction']*target+lim['absolute_energy_J'],'complete_reference_work_vs_native_IE':float(abs(model_work-IE).max())<=lim['work_energy_fraction']*target+lim['absolute_energy_J']}
        reload=None
        if domain=='elastic':checks['no_reference_damage']=bool(np.all(state[:,1]==0))
        else:
            checks['reference_damage_irreversible']=bool(np.all(np.diff(state[:,1])>=-1e-12))
            if expected_G is not None:
                checks['mixed_power_law_G']=abs(IE[-1]/area*1000-expected_G)<=lim['work_per_area_G_fraction']*expected_G
                reload=abs(float(np.interp(.75,T,IE)-np.interp(.25,T,IE)))/target;checks['equal_peak_reload_no_new_energy']=reload<=lim['equal_peak_energy_fraction']
        row={'case':case['id'],'pass':all(checks.values()),'checks':{k:bool(v) for k,v in checks.items()},'failed_checks':[k for k,v in checks.items() if not v],'native_rows':len(T),'last_TH_time_ms':float(T[-1]),'native_final_field_time_ms':end,'force_relative_error':force_error,'maximum_motion_error_mm':motion,'maximum_top_nonuniformity_mm':uniform,'maximum_global_energy_residual_J':float(abs(residual).max()),'impulse_work_error_J':abs(work-EW[-1]),'maximum_reference_work_IE_error_J':float(abs(model_work-IE).max()),'final_native_IE_J':float(IE[-1]),'maximum_IE_J':float(IE.max()),'energy_scale_J':target,'native_G_N_mm':float(IE[-1]/area*1000),'expected_G_N_mm':expected_G,'reload_energy_difference_fraction':reload,'native_history_rollback_not_directly_instrumented':True,'whole_transfer_qualified':False}
        np.savez_compressed(d/'surface_diagnostics.npz',time_ms=T,gap_mm=q,native_force_N=forces,reference_force_N=reference,reference_state=state,IE_J=IE,KE_J=KE,EW_J=EW,reference_work_J=model_work,residual_J=residual)
        dump(d/'loaded_mechanical_review.json',row);rows.append(row);print(json.dumps({'case':case['id'],'pass':row['pass'],'failed':row['failed_checks'],'force_error':force_error,'end_ms':end}),flush=True)
    lookup={r['case']:r for r in rows};comparison=cfg.get('comparison_cases',['ELASTIC_MIXED','ELASTIC_MIXED_HALF'] if stage=='elastic' else ['DAMAGE_MIXED','DAMAGE_MIXED_HALF']);base=lookup.get(comparison[0]);half=lookup.get(comparison[1]);half_error=None
    if base and half and 'maximum_IE_J' in base and 'maximum_IE_J' in half:half_error=abs(base['maximum_IE_J']-half['maximum_IE_J'])/max(base['energy_scale_J'],1e-30)
    checks={'all_loaded_cases_pass':all(r['pass'] for r in rows),'half_dt_IE_peak':half_error is not None and half_error<=lim['half_dt_work_fraction']}
    dump(OUT/(stage+'_mechanical_review.json'),{'created_utc':now(),'cases':rows,'checks':checks,'pass':all(checks.values()),'half_dt_difference_fraction':half_error,'native_state_rollback_directly_qualified':False,'whole_insertion_ready':False,'new_whole_duration_credit_s':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','elastic','damage']);a=p.parse_args().action
    if a=='declare':declare_review()
    else:review(a)
