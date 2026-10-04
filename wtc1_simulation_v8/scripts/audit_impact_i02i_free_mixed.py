"""K saved binary/CSV histories against separable free XY reference.

Exact rational representation intervals are predeclared; raw signs retained.
No phase shift, extrapolation, old solver, clipping or physical calibration.
"""
from __future__ import annotations
import csv,json,re,time,platform
from fractions import Fraction as Q
import numpy as np
import run_impact_i02i_free_mixed as run
import reference_impact_i02i_free_mixed as ref
import audit_impact_i02i_output_precision as precision
import decode_impact_i02i_t01 as reader
h=run.h;ROOT,OUT,CFG=run.ROOT,run.OUT,run.CFG
peak=lambda a:float(np.max(abs(a)))

def cell_D(row,kt,kn):
    il,ih=precision.rounding_interval32(row[1]);xl,xh=precision.squared_range(*precision.rounding_interval32(row[24]))
    yl,yh=precision.squared_range(*precision.rounding_interval32(row[25]))
    return (il-xh/(2*kt)-yh/(2*kn))/1000,(ih-xl/(2*kt)-yl/(2*kn))/1000

def case(cfg,c,dest):
    dest.mkdir();folder=OUT/c['id'];gen=run.read(folder/'generation.json');name=gen['name']
    tfile=folder/(name+'T01');data=tfile.read_bytes();a,meta=reader.decode(data,cfg['binary_schema'],name)
    independent=reader.strided_check(data,cfg['binary_schema']);csvpath=folder/(name+'T01.csv')
    with csvpath.open(encoding='utf-8',newline='') as f:rows=list(csv.reader(f))
    headers=rows.pop(0);assert len(headers)==41 and np.asarray(rows).shape==a.shape
    mismatches=[(i,k) for i,row in enumerate(a) for k,v in enumerate(row) if format(v,'.6e')!=rows[i][k].strip()]
    t=a[:,0];p=cfg['references'][c['family']];pn=p['normal'];m=p['moving_mass_g'];e0=p['initial_energy_J'];cap=c['maximum_dt_ms']
    x=a[:,35]-a[:,29];y=a[:,36]-a[:,30];vx=a[:,37];vy=a[:,38];fx=a[:,24];fy=a[:,25];ie=a[:,1]*.001;ke=a[:,2]*.001;we=a[:,9]*.001
    ux=fx*fx/(2*p['kt_N_per_mm'])*.001;uy=fy*fy/(2*pn['k_N_per_mm'])*.001;D=ie-ux-uy
    exact=ref.state(t,p);maximum=np.maximum.accumulate(y);hist=ref.normal.history_state(y,maximum,pn)
    integral_x=np.r_[0,np.cumsum(-.5*(fx[1:]+fx[:-1])*np.diff(t))];integral_y=np.r_[0,np.cumsum(-.5*(fy[1:]+fy[:-1])*np.diff(t))]
    work=np.r_[0,np.cumsum((.5*(fx[1:]+fx[:-1])*np.diff(x)+.5*(fy[1:]+fy[:-1])*np.diff(y))*.001)]
    frac={}
    scales={'x_mm':p['amplitude_x_mm'],'y_mm':pn['turning_gap_mm'],'vx_mm_per_ms':p['vx0_mm_per_ms'],
        'vy_mm_per_ms':pn['v0_mm_per_ms'],'Fx_N':p['force_x_amplitude_N'],'Fy_N':pn['force_amplitude_N'],
        'Px_N_ms':p['initial_Px_N_ms'],'Py_N_ms':p['initial_Py_N_ms']}
    actual={'x_mm':x,'y_mm':y,'vx_mm_per_ms':vx,'vy_mm_per_ms':vy,'Fx_N':fx,'Fy_N':fy,'Px_N_ms':a[:,3],'Py_N_ms':a[:,4]}
    for key,scale in scales.items():frac[key]=peak(actual[key]-exact[key])/scale
    for axis,axiscol,vcol,fcol,jcol,p0,integral in [('X',3,37,24,33,p['initial_Px_N_ms'],integral_x),('Y',4,38,25,34,p['initial_Py_N_ms'],integral_y)]:
        frac['nodal_P'+axis]=peak(m*(a[:,vcol]+a[:,vcol-6])-a[:,axiscol])/p0
        frac['initial_P_impulse_'+axis]=peak(a[:,jcol]+a[:,jcol+6]+p0-a[:,axiscol])/p0
        frac['force_integral_'+axis]=peak(a[:,jcol]-integral)/p0
    frac['history_Fx']=peak(fx-p['kt_N_per_mm']*x)/p['force_x_amplitude_N'];frac['history_Fy']=peak(fy-hist['force_N'])/pn['force_amplitude_N']
    energy={'energy_balance':e0+we-ie-ke,'history_IE':ie-.5*p['kt_N_per_mm']*x*x*.001-hist['IE_J'],
        'force_work':ie-work,'time_IE':ie-exact['IE_J'],'time_KE':ke-exact['KE_J'],'Ux':ux-exact['Ux_J'],'Uy':uy-exact['Uy_J'],
        'retained':D-exact['Dy_J'],'history_retained':D-hist['retained_J']}
    frac.update({k:peak(v)/e0 for k,v in energy.items()})
    kt=Q(str(p['kt_N_per_mm']));kn=Q(str(pn['k_N_per_mm']));intervals=[];negative_upper=[];zero_incompatible=[];elastic=maximum<=pn['delta0_mm']
    for i,row in enumerate(a):
        lo,hi=cell_D(row,kt,kn);raw=(precision.qfloat(row[1])-precision.qfloat(row[24])**2/(2*kt)-precision.qfloat(row[25])**2/(2*kn))/1000
        if hi<0:negative_upper.append(i)
        if elastic[i] and not lo<=0<=hi:zero_incompatible.append(i)
        dl,dh=precision.interval_float(lo,hi);intervals.append([float(t[i]),bool(elastic[i]),float(raw),dl,dh,bool(lo<=0<=hi),str(lo),str(hi)])
    endlo,endhi=precision.rounding_interval32(t[-1]);windowlo=Q(str(c['end_ms']))-2*Q(str(cap));windowhi=Q(str(c['end_ms']))
    crossings=np.flatnonzero((vy[:-1]>=0)&(vy[1:]<0));turn=None
    if len(crossings)==1:
        z=int(crossings[0]);turn=float(t[z]+(t[z+1]-t[z])*vy[z]/(vy[z]-vy[z+1]))
    jobs=run.read(folder/'execution.json');pre=run.read(folder/'preflight.json');text=(folder/(name+'_0001.out')).read_text(errors='replace')
    cycles=int(re.search(r'TOTAL NUMBER OF CYCLES\s*(?:\.\s*)*[:=]?\s*(\d+)',text).group(1));g=cfg['gates']
    checks={k:v<=(g['work_fraction'] if k=='force_work' else g['energy_fraction'] if k in energy else g['raw_amplitude_fraction']) for k,v in frac.items()}
    starter=(folder/(name+'_0000.rad')).read_text();engine=(folder/(name+'_0001.rad')).read_text()
    checks.update(preflight=pre['pass'],three_jobs=len(jobs)==3 and all(j['returncode']==0 for j in jobs),normal_termination='NORMAL TERMINATION' in text,
        one_TH_per_cycle=len(t)==cycles,binary_exact_EOF=meta['exact_EOF_consumed'],independent_readers=np.array_equal(a,independent),
        all_values_reproduce_CSV=not mismatches,IE_three_channels=np.array_equal(a[:,1],a[:,10]) and np.array_equal(a[:,1],a[:,28]),
        finite_time=np.isfinite(a).all() and np.all(np.diff(t)>0),binary_schema_guard=h.sha(reader.__file__)==cfg['binary_reader_sha256'],
        free_XY_cards='FREE_XY_BLOCK_Z_ROT\n   001 111' in starter and '/IMPDISP' not in starter and '/TFILE/4' in engine,
        cap=peak(a[:,7])<=cap*(1+g['maximum_solver_dt_relative_tolerance']),record_cap=peak(np.diff(t))<=cap+g['csv_time_difference_tolerance_ms'],
        quantized_end_coverage=max(endlo,windowlo)<=min(endhi,windowhi),quantized_retained_nonnegative=not negative_upper,
        quantized_elastic_zero_compatible=not zero_incompatible,no_OFF=np.all(a[:,23]==1),positive_y=np.all(y[1:]>0) and y[0]==0,
        before_failure=y.max()<pn['deltaf_mm'],one_normal_turn=len(crossings)==1,
        turn_time=turn is not None and abs(turn-pn['turn_time_ms'])<=g['turn_time_steps']*cap+g['csv_time_difference_tolerance_ms'],
        peak_y=abs(y.max()-pn['turning_gap_mm'])/pn['turning_gap_mm']<=g['raw_amplitude_fraction'],
        no_external_work=peak(we)<=g['no_external_work_J'],mass=peak(a[:,6]-.2)/.2<=g['mass_fraction'],added_mass=peak(a[:,17])<=g['added_mass_g'],
        fixed_support=peak(a[:,29:33])<=g['fixed_gap_mm'],free_axis_reactions=peak(a[:,39:41])<=g['free_axis_reaction_N_ms'],
        no_other_axis_P=peak(a[:,5])<=g['other_axis_momentum_N_ms'],initial_IE=abs(ie[0])<=g['no_external_work_J'],
        initial_KE=abs(ke[0]-e0)/e0<=g['initial_fraction'],initial_Px=abs(a[0,3]-p['initial_Px_N_ms'])/p['initial_Px_N_ms']<=g['initial_fraction'],
        initial_Py=abs(a[0,4]-p['initial_Py_N_ms'])/p['initial_Py_N_ms']<=g['initial_fraction'],
        initial_vx=abs(vx[0]-p['vx0_mm_per_ms'])/p['vx0_mm_per_ms']<=g['initial_fraction'],initial_vy=abs(vy[0]-pn['v0_mm_per_ms'])/pn['v0_mm_per_ms']<=g['initial_fraction'],
        fresh=gen['fresh_state'] and gen['no_restart'],unchanged_history=gen['history_properties_unchanged'],
        case_budget=sum(j['seconds'] for j in jobs)<=cfg['execution']['maximum_case_wall_seconds'])
    if c['family']=='FREE_MIXED_ARREST':
        settled=t>=pn['zero_force_time_ms']+2*cap
        checks.update(normal_force_zero_after_unload=np.any(settled) and peak(fy[settled])<=g['force_zero_N'],
            normal_free_return_velocity=peak(vy[settled]-pn['release_velocity_mm_per_ms'])/pn['v0_mm_per_ms']<=g['raw_amplitude_fraction'],
            retained_after_unload=peak(D[settled]-pn['retained_work_J'])/e0<=g['energy_fraction'])
    checks={k:bool(v) for k,v in checks.items()};worst=int(np.argmin(D))
    metrics={'fractions':frac,'rows':len(t),'cycles':cycles,'values_compared':int(a.size),'unmatched_values':mismatches,
        'raw_end_coverage_without_quantization':bool(0<=c['end_ms']-t[-1]<=2*cap),'end_record_ms':float(t[-1]),
        'time_cell_exact':[str(endlo),str(endhi)],'turn_time_ms':turn,'maximum_y_mm':float(y.max()),
        'final':{k:float(v[-1]) for k,v in {**actual,'IE_J':ie,'KE_J':ke,'Ux_J':ux,'Uy_J':uy,'raw_D_J':D,'Jx_N_ms':a[:,33],'Jy_N_ms':a[:,34]}.items()},
        'initial_KE_J':float(ke[0]),'minimum_raw_D_J':float(D.min()),'negative_raw_D_rows':int((D<0).sum()),
        'raw_sign_at_old_I_threshold_pass_diagnostic_only':bool(D.min()>=-g['raw_signed_D_J_reported_without_override']),
        'negative_interval_upper_rows':negative_upper,'elastic_zero_incompatible_rows':zero_incompatible,'worst_D_row':worst,
        'maximum_solver_dt_ms':peak(a[:,7]),'maximum_record_interval_ms':peak(np.diff(t)),
        'seconds':sum(j['seconds'] for j in jobs),'maximum_WE_J':peak(we),'OFF_range':[float(a[:,23].min()),float(a[:,23].max())]}
    with (dest/'comparison.csv').open('w',encoding='utf-8',newline='') as f:
        keys=list(actual)+['IE_J','KE_J','Ux_J','Uy_J','raw_D_J','history_D_J','work_J','Jx_N_ms','Jy_N_ms']
        values={**actual,'IE_J':ie,'KE_J':ke,'Ux_J':ux,'Uy_J':uy,'raw_D_J':D,'history_D_J':hist['retained_J'],'work_J':work,'Jx_N_ms':a[:,33],'Jy_N_ms':a[:,34]}
        writer=csv.writer(f);writer.writerow(['time_ms']+keys);writer.writerows(np.column_stack([t]+[values[k] for k in keys]))
    with (dest/'retained_intervals.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['time_ms','historically_elastic','raw_D_J','lower_J','upper_J','zero_compatible','exact_lower','exact_upper']);writer.writerows(intervals)
    result={'case':c,'metadata':meta,'metrics':metrics,'checks':checks,'all_checks_pass':all(checks.values()),
        'binary_sha256':h.sha(tfile),'CSV_sha256':h.sha(csvpath),'no_phase_shift':True,'no_old_gates_reassessed':True}
    h.dump(dest/'audit.json',result);return result,(t,{**actual,'IE_J':ie,'KE_J':ke,'Jx_N_ms':a[:,33],'Jy_N_ms':a[:,34],'raw_D_J':D}),data

def audit():
    dest=OUT/'verification_r1';assert not dest.exists(),'Preserve audits';dest.mkdir();cfg=run.read(CFG);tick=time.perf_counter()
    assert h.sha(OUT/'reference_verification.json')==cfg['reference_guard_sha256'];results={};series={};refs={}
    for c in cfg['cases']:
        results[c['id']],series[c['id']],data=case(cfg,c,dest/c['id'])
        if not refs:refs=precision.reject_tests(data,cfg['binary_schema'],'I02IK_'+c['id'])
    synthetic=[]
    for fx,fy in [(Q(0),Q(0)),(Q(1,8),Q(7)),(Q(123),Q(495)),(Q(-17),Q(17))]:
        exact=fx*fx/(2*Q(21500))+fy*fy/(2*Q(56000));row=np.zeros(41);row[1]=np.float32(float(exact));row[24]=np.float32(float(fx));row[25]=np.float32(float(fy))
        lo,hi=cell_D(row,Q(21500),Q(56000));synthetic.append({'Fx_exact':str(fx),'Fy_exact':str(fy),'IE_exact_Nmm':str(exact),'zero_contained':bool(lo<=0<=hi)})
    refs['known_two_force_elastic_states']=all(s['zero_contained'] for s in synthetic);h.dump(dest/'decoder_reference_checks.json',{'checks':refs,'synthetic':synthetic,'pass':all(refs.values())})
    comparisons=[]
    for family,query in cfg['comparison_times_ms'].items():
        c1,c2=[c for c in cfg['cases'] if c['family']==family];t1,a=series[c1['id']];t2,b=series[c2['id']];p=cfg['references'][family]
        scales={'x_mm':p['amplitude_x_mm'],'y_mm':p['normal']['turning_gap_mm'],'vx_mm_per_ms':p['vx0_mm_per_ms'],'vy_mm_per_ms':p['normal']['v0_mm_per_ms'],
            'Fx_N':p['force_x_amplitude_N'],'Fy_N':p['normal']['force_amplitude_N'],'Px_N_ms':p['initial_Px_N_ms'],'Py_N_ms':p['initial_Py_N_ms'],
            'IE_J':p['initial_energy_J'],'KE_J':p['initial_energy_J'],'Jx_N_ms':p['initial_Px_N_ms'],'Jy_N_ms':p['initial_Py_N_ms'],'raw_D_J':p['initial_energy_J']}
        values={k:peak(np.interp(query,t1,a[k])-np.interp(query,t2,b[k]))/scale for k,scale in scales.items()}
        checks={k:v<=cfg['gates']['comparison_fraction'] for k,v in values.items()};checks['coverage']=bool(all(max(t1[0],t2[0])<=q<=min(t1[-1],t2[-1]) for q in query))
        comparisons.append({'family':family,'times_ms':query,'fractions':values,'checks':checks})
    reference=run.read(OUT/'reference_verification.json');execution=run.read(OUT/'execution_complete.json')
    summary={'iteration':'IMPACT-I02I-K','created_utc':h.NOW(),'cases':results,'comparisons':comparisons,
        'case_checks_passed':sum(sum(v['checks'].values()) for v in results.values()),'case_checks_total':sum(len(v['checks']) for v in results.values()),
        'comparison_checks_passed':sum(sum(v['checks'].values()) for v in comparisons),'comparison_checks_total':sum(len(v['checks']) for v in comparisons),
        'reference_checks_passed':sum(reference['checks'].values())+sum(refs.values()),'reference_checks_total':len(reference['checks'])+len(refs),
        'all_declared_checks_pass':all(v['all_checks_pass'] for v in results.values()) and all(all(v['checks'].values()) for v in comparisons) and reference['pass'] and all(refs.values()),
        'runtime_seconds':execution['runtime_seconds'],'audit_seconds':time.perf_counter()-tick,'total_rows':sum(v['metrics']['rows'] for v in results.values()),
        'software':{'python':platform.python_version(),'numpy':np.__version__,'interval_arithmetic':'exact Fraction'},'config_sha256':h.sha(CFG),'audit_sha256':h.sha(__file__),
        'no_old_solver_rerun':True,'old_I_four_sign_failures_preserved':True,'old_J_three_raw_endpoint_failures_preserved':True,
        'official_schema_verified':False,'mixed_fracture_calibrated':False,'physical_propagation_qualified':False,'aircraft_impact_qualified':False}
    h.dump(dest/'summary.json',summary)
    print(json.dumps({'pass':summary['all_declared_checks_pass'],'case_checks':[summary['case_checks_passed'],summary['case_checks_total']],
        'comparisons':[summary['comparison_checks_passed'],summary['comparison_checks_total']],'references':[summary['reference_checks_passed'],summary['reference_checks_total']],
        'failed':{n:[k for k,v in r['checks'].items() if not v] for n,r in results.items()},'comparison_failed':{r['family']:[k for k,v in r['checks'].items() if not v] for r in comparisons},
        'negative_upper':{n:r['metrics']['negative_interval_upper_rows'] for n,r in results.items()},'zero_incompatible':{n:r['metrics']['elastic_zero_incompatible_rows'] for n,r in results.items()}}),flush=True)

if __name__=='__main__':audit()
