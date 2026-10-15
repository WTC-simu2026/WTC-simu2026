"""At most four approved Engine processes, with prior/local gates and no Starter."""
from build_aircraft_a87_null_relative import ROOT,OUT,CFG,PLAN,CAND,guard as build_guard,read,dump,sha,now,linux
from build_aircraft_a54_graph import rel,harness
from read_aircraft_a81_th_binary import decode
from pathlib import Path
import json,shlex,shutil,subprocess,time,re,csv,ast
import numpy as np

CONTROL=ROOT/'wtc1_simulation_v8/data/aircraft_a87_controls.json'


def engine():
    build_guard();b=read(OUT/'build_finished.json')
    assert b['build_success'] and b['exact_A86_null_relative_applied']
    binary=CAND/'isolated_exec/engine_linux64_gf_ompi';assert sha(binary)==b['binary_sha256']
    assert read(OUT/'exact_null_relative_patch_application.json')['pass']
    return binary


def declare():
    binary=engine();assert not CONTROL.exists()
    p=read(PLAN)
    for case in p['cases']:
        for row in case['inputs']:assert sha(ROOT/row['path'])==row['sha256']
    dump(CONTROL,{'created_utc':now(),'iteration':'AIRCRAFT-A87','seed':1102110,'random_draws':0,
        'binary_sha256':sha(binary),'plan_sha256':sha(PLAN),'driver_sha256':sha(Path(__file__)),
        'cases':p['cases'],'maximum_Engine':4,'maximum_Starter':0,'CPU_threads':1,'each_cap_s':180,
        'GPU_installation_whole_dynamics':False,'zero_native_converters':True,
        'reused_analysis':'review_aircraft_a67_current_area.case_review on new outputs only',
        'old_analysis_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/review_aircraft_a67_current_area.py'),
        'TH_reader_sha256':sha(ROOT/'wtc1_simulation_v8/scripts/read_aircraft_a81_th_binary.py')})
    dump(OUT/'controls_guard.json',{'created_utc':now(),'sha256':sha(CONTROL),'before_any_Engine':True})
    print('A87 controls declared: four maximum, all conditional gates retained.',flush=True)


def guard():
    binary=engine();c=read(CONTROL);assert sha(CONTROL)==read(OUT/'controls_guard.json')['sha256']
    assert sha(binary)==c['binary_sha256'] and sha(PLAN)==c['plan_sha256'] and sha(Path(__file__))==c['driver_sha256']
    assert sha(ROOT/'wtc1_simulation_v8/scripts/review_aircraft_a67_current_area.py')==c['old_analysis_sha256']
    assert sha(ROOT/'wtc1_simulation_v8/scripts/read_aircraft_a81_th_binary.py')==c['TH_reader_sha256']
    return c


def run_native(case,ordinal):
    c=guard();assert ordinal==len(list(OUT.rglob('native_launch_declaration.json')))+1 and ordinal<=4
    d=OUT/'native'/case['case'];assert not d.exists();d.mkdir(parents=True)
    for row in case['inputs']:
        p=ROOT/row['path'];shutil.copy2(p,d/p.name);assert sha(d/p.name)==row['sha256']
    assert not list(d.glob('*_0000.rad'))
    dump(d/'generation.json',{'created_utc':now(),'name':case['name'],'case':case,'inputs_exact':True,'new_Starter':False})
    q=lambda p:shlex.quote(linux(p));binary=engine();script=d/'engine.launch.sh'
    script.write_text('set -eu\ncd '+q(d)+'\nexport OMP_NUM_THREADS=1 OMP_THREAD_LIMIT=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n'
        'export OPENRADIOSS_PATH='+q(CAND)+'\nexport RAD_CFG_PATH='+q(CAND/'hm_cfg_files')+'\nexec '+q(binary)+' -i '+shlex.quote(case['name']+'_0001.rad')+' > engine.log 2>&1\n',encoding='utf8',newline='\n')
    dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal':ordinal,'maximum_Engine':4,'Starter':0,
        'CPU_threads':1,'cap_s':180,'counts_even_if_failed_or_timeout':True,'controls_sha256':sha(CONTROL)})
    argv=['wsl.exe','-d','Ubuntu','--','timeout','--signal=TERM','--kill-after=5','180','bash',linux(script)]
    start=time.perf_counter();code=None;timed=False;out=b'';err=b''
    try:
        r=subprocess.run(argv,capture_output=True,timeout=195);code=r.returncode;out=r.stdout;err=r.stderr
    except subprocess.TimeoutExpired as e:timed=True;out=e.stdout or b'';err=e.stderr or b''
    (d/'engine.launcher.log').write_bytes(out+err)
    text=(d/'engine.log').read_text(encoding='utf8',errors='replace') if (d/'engine.log').exists() else ''
    execution={'created_utc':now(),'argv':argv,'parent_exit_code':code,'timed_out':timed or code in [124,137],
        'wall_s':time.perf_counter()-start,'CPU_threads':1,'cap_s':180,'binary_sha256':sha(binary)}
    dump(d/'engine.execution.json',execution)
    completion={**execution,'normal_termination':'NORMAL TERMINATION' in text,
        'error_or_abort':bool(re.search(r'ERROR TERMINATION|USER BREAK|MPI_ABORT|STOP\s*:|STOP\s+66',text,re.I)),
        'mechanical_qualification_not_inferred':True}
    dump(d/'completion_review.json',completion)
    return d,completion


def regression(case,d):
    name=case['name'];reference=ROOT/f"wtc1_simulation_v8/output/aircraft_a67/native/{case['case']}"
    meta,arrays,flat=decode(d/(name+'T01'));oldmeta,oldarrays,oldflat=decode(reference/(name+'T01'))
    assert meta==oldmeta and flat.shape==oldflat.shape
    # A native CSV from this exact saved schema labels the new binary payload.
    with (reference/(name+'T01.csv')).open(encoding='utf-8-sig') as f:keys=next(csv.reader(f))
    while keys and (not keys[-1].strip() or keys[-1].startswith('(null)')):keys.pop()
    assert len(keys)==flat.shape[1]
    with (d/(name+'T01.csv')).open('x',encoding='utf8',newline='') as f:
        w=csv.writer(f);w.writerow(keys);w.writerows([[format(v,'.6e') for v in row] for row in flat])
    close=bool(np.allclose(flat,oldflat,rtol=6e-7,atol=1e-12))
    dump(d/'cached_native_comparison.json',{'created_utc':now(),'pass':close,'new_native_binary_rows':len(flat),'columns':flat.shape[1],
        'same_schema':True,'binary_all_values_identical':bool(np.array_equal(flat,oldflat)),
        'maximum_absolute_channel_difference':float(abs(flat-oldflat).max()),
        'old_reference_read_only':True,'CSV_is_own_Python_transcription_not_new_native_converter':True})
    import review_aircraft_a67_current_area as old_review
    old_review.OUT=OUT
    original=read(ROOT/'wtc1_simulation_v8/data/aircraft_a67_controls.json')
    source_case=next(cc for cc in original['cases'] if cc['id']==case['case'])
    mechanical,_=old_review.case_review(source_case,original)
    result={'case':case['case'],'pass':bool(close and mechanical['pass']),
        'cached_binary_comparison_pass':close,'mechanical_review_pass':mechanical['pass'],
        'scope':mechanical['scope'],'no_new_physical_thresholds':True}
    dump(d/'regression_gate.json',result);return result


def loop_review(case,d):
    name=case['name'];meta,a,flat=decode(d/(name+'T01'));t=a['time'][:,0];count=len(t);dt=.000125
    byid={g['id']:(k,g) for k,g in enumerate(meta['groups'])}
    U=np.zeros((count,8,3));sec=np.zeros_like(U);imp=np.zeros_like(U)
    for axis,gid in enumerate([2,3,4]):
        k,g=byid[gid];assert [e['id'] for e in g['entities']]==list(range(1,9))
        assert g['variables']==[axis+1,axis+4,620+axis]
        data=a['group_'+str(k)].reshape(count,8,3);U[:,:,axis]=data[:,:,0];sec[:,:,axis]=data[:,:,1];imp[:,:,axis]=data[:,:,2]
    V=np.empty_like(U);V[0]=0
    for j in range(1,count):V[j]=2*sec[j]-V[j-1]
    K=.0005*np.sum(V**2,axis=(1,2));global_=a['global'];assert meta['global_ids']==list(range(1,23))
    IE=global_[:,0]*.001;nativeK=global_[:,1]*.001;nativeW=global_[:,8]*.001
    other=global_[:,7]*.001+global_[:,10]*.001+global_[:,12:16].sum(axis=1)*.001
    residual=K+IE+other-nativeW
    k,g=byid[10];element=a['group_'+str(k)];assert g['variables']==[1,4,137,140,141,142,145,148]
    fields={str(var):{'minimum':float(element[:,j].min()),'maximum':float(element[:,j].max()),
        'nonzero_rows':int(np.count_nonzero(element[:,j]))} for j,var in enumerate(g['variables'])}
    support=imp[:,:4,2].sum(axis=1)
    def plateau(lo,hi):
        ix=np.flatnonzero((t>=lo)&(t<=hi))
        if len(ix)<3:return None
        return float(-(support[ix[-1]]-support[ix[0]])/(t[ix[-1]]-t[ix[0]]))
    before=plateau(.082,.098);after=plateau(.625,.645)
    checks={'normal_Engine_and_positive_time_target':count>5000 and t[-1]>=.65-1e-6,
        'actual_regular_saved_history':count>1 and bool(np.allclose(np.diff(t),dt,rtol=6e-4,atol=1e-9)),
        'literal_independent_energy_threshold':float(abs(residual).max())<=1e-7,
        'physical_reconstructed_KE_vs_native':float(abs(K-nativeK).max())<=1e-7,
        'pre_rupture_compression_plateau_reference':before is not None and abs(abs(before)-22000)<=440,
        'post_reclosure_compression_plateau_reference':after is not None and abs(abs(after)-22000)<=440,
        'prescribed_top_Z_target_reclosed':abs(float(U[-1,4:,2].mean())+.05)<=2e-5,
        'free_top_XY_small':float(abs(U[:,4:,:2]).max())<=2e-5,
        'uniform_top_Z':float(abs(U[:,4:,2]-U[:,4:,2].mean(axis=1)[:,None]).max())<=2e-5,
        'native_USR_population_qualified':False,
        'native_damage_and_rupture_semantics_certified':False,
        'full_reaction_work_independent_closure_certified':False}
    # A stress/USR number or OFF transition alone does not certify its state semantics.
    review={'created_utc':now(),'case':case['case'],'pass':False,'checks':checks,
        'failed_checks':[k for k,v in checks.items() if not v],'native_rows':count,'last_saved_ms':float(t[-1]),
        'global_energy_residual_J_max':float(abs(residual).max()),'unchanged_energy_limit_J':1e-7,
        'KE_reconstruction_vs_native_J_max':float(abs(K-nativeK).max()),
        'energy_formula':'physical nodal KE + native internal/rotation/spring/hourglass/contact energies - native external work; independent reaction work still requires certification',
        'native_external_work_J_range':[float(nativeW.min()),float(nativeW.max())],
        'pre_compression_force_N':before,'post_reclosure_force_N':after,'fields_raw_observed_ranges':fields,
        'field_population_and_deletion_semantics_not_inferred_from_zero_or_transition':True,
        'zero_denominator_guard_marker_count':(d/(name+'_0001.out')).read_text(encoding='utf8',errors='replace').count('WTC1 EXACT NULL FREE RELATIVE CRITERIA'),
        'whole_CHECK_condition_not_met':True,'whole_dynamic_extension':False,'physical_whole_credit_s':0}
    np.savez_compressed(d/'loop_diagnostics.npz',time_ms=t,U_mm=U,secant_velocity_mm_ms=sec,source_endpoint_velocity_mm_ms=V,
        cumulative_node_reaction_N_ms=imp,physical_KE_J=K,native_KE_J=nativeK,native_IE_J=IE,native_external_work_J=nativeW,
        energy_residual_J=residual,native_element_channels=element)
    dump(d/'loop_review.json',review);return {'case':case['case'],'pass':False,'last_saved_ms':float(t[-1]),'failed_checks':review['failed_checks']}


def run():
    c=guard();assert not list(OUT.rglob('native_launch_declaration.json'))
    results=[]
    for ordinal,case in enumerate(c['cases'],1):
        if ordinal>1 and not all(r['pass'] for r in results):break
        d,completion=run_native(case,ordinal)
        if completion['parent_exit_code']!=0 or not completion['normal_termination'] or completion['error_or_abort']:
            result={'case':case['case'],'pass':False,'reason':'Native Engine incomplete or stopped','completion':completion}
        else:
            try:
                if ordinal<=2:result=regression(case,d)
                elif ordinal==3:result=loop_review(case,d)
                else:raise RuntimeError('Whole CHECK cannot be reached before certified local gates')
            except Exception as exc:
                result={'case':case['case'],'pass':False,'reason':'Analysis incomplete; preserve native data without retry','analysis_error':repr(exc)}
                dump(d/'analysis_incomplete.json',{'created_utc':now(),**result})
        results.append(result)
        dump(OUT/f'control_progress_{ordinal}.json',{'created_utc':now(),'results':results,'Engine_consumed':ordinal,'maximum':4})
        print(json.dumps(result),flush=True)
    used=len(list(OUT.rglob('native_launch_declaration.json')))
    dump(OUT/'controls_execution_review.json',{'created_utc':now(),'results':results,'new_Engine':used,'new_Starter':0,
        'maximum_Engine':4,'unconsumed_conditional_slots':4-used,'unconsumed_slots_not_reassigned':True,
        'new_native_converter':0,'whole_CHECK_executed':any(r['case']=='WHOLE_ORIGINAL_CHECK' for r in results),
        'whole_dynamic_extension':False,'all_local_physical_gates_pass':bool(len(results)>=3 and all(r['pass'] for r in results))})
    dump(OUT/'harness_after_controls.json',harness())

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
