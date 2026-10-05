"""L saved F energy ledger, unshifted binary values and exact event cells."""
from __future__ import annotations
import csv,json,time,platform
from fractions import Fraction as Q
import numpy as np
import run_impact_i02i_deletion_ledger as run
import audit_impact_i02i_output_precision as precision
import decode_impact_i02i_t01 as reader
h=run.h;ROOT,OUT,CFG=run.ROOT,run.OUT,run.CFG
peak=lambda a:float(np.max(abs(a)))

def add(a,b):return a[0]+b[0],a[1]+b[1]
def sub(a,b):return a[0]-b[1],a[1]-b[0]
def energy_cell(value):return tuple(x/1000 for x in precision.rounding_interval32(value))
def square_cell(value,k):return tuple(x/(2*Q(str(k))*1000) for x in precision.squared_range(*precision.rounding_interval32(value)))
def intervals(row,kt,kn):
    c={'IE':energy_cell(row[1]),'KE':energy_cell(row[2]),'WE':energy_cell(row[9]),'Ux':square_cell(row[24],kt),'Uy':square_cell(row[25],kn)}
    c['D']=sub(sub(c['IE'],c['Ux']),c['Uy']);return c
def pack(cell):
    lo,hi=cell;dl,dh=precision.interval_float(lo,hi)
    return {'lower_J':dl,'upper_J':dh,'lower_exact':str(lo),'upper_exact':str(hi),'contains_zero':bool(lo<=0<=hi)}

def case(cfg,c,dest,saved):
    dest.mkdir()
    for item in c['inputs'].values():assert h.sha(ROOT/item['path'])==item['sha256']
    data=(ROOT/c['inputs']['T01']['path']).read_bytes();a,meta=reader.decode(data,cfg['binary_schema'],c['title'])
    other=reader.strided_check(data,cfg['binary_schema'])
    with (ROOT/c['inputs']['csv']['path']).open(encoding='utf-8',newline='') as f:rows=list(csv.reader(f))
    headers=rows.pop(0);assert len(headers)==41 and len(rows)==len(a)
    mismatches=[]
    for j,(binary,row) in enumerate(zip(a,rows)):
        if len(row)!=41:mismatches.append({'row':j,'wrong_columns':len(row)});continue
        mismatches.extend({'row':j,'column':k} for k,value in enumerate(binary) if format(value,'.6e')!=row[k].strip())
    p=cfg['connector'];kt,kn=p['kt_N_per_mm'],p['kn_N_per_mm'];scale=c['energy_scale_J'];g=cfg['gates']
    t=a[:,0];ie=a[:,1]*.001;ke=a[:,2]*.001;we=a[:,9]*.001;fx=a[:,24];fy=a[:,25];ux=fx*fx/(2*kt)*.001;uy=fy*fy/(2*kn)*.001
    rawD=ie-ux-uy;off=a[:,23];events=np.flatnonzero((off[:-1]==1)&(off[1:]==0))+1
    checks={'binary_schema_exact_EOF':meta['exact_EOF_consumed'],'independent_readers_equal':np.array_equal(a,other),
        'all_values_reproduce_CSV':not mismatches,'old_row_count_preserved':len(a)==saved['sampling']['rows'],
        'IE_three_channels_identical':np.array_equal(a[:,1],a[:,10]) and np.array_equal(a[:,1],a[:,28]),
        'finite_increasing_times':np.isfinite(a).all() and np.all(np.diff(t)>0),'OFF_binary_values':np.all((off==0)|(off==1)),
        'expected_event_count':len(events)==c['expected_event_count'],'OFF_irreversible':np.all(np.diff(off)<=0),
        'mass':peak(a[:,6]-.2)/.2<=g['mass_fraction'],'no_added_mass':peak(a[:,17])<=g['no_added_mass_g'],
        'raw_energy_balance':peak(ie+ke-we-ie[0]-ke[0]+we[0])/scale<=g['energy_fraction'],
        'old_F_same_row_gate_preserved':saved['checks']['strict_same_row_OFF_FX']==bool(np.all(abs(fx[off==0])<=g['force_zero_N'])),
        'initial_zero':peak(a[0,[1,2,9,24,25,29,30,35,36]])<=1e-12}
    result={'case':c['id'],'metadata':meta,'checks':checks,'rows':len(a),'values_compared':int(a.size),
        'raw_energy_balance_fraction':peak(ie+ke-we-ie[0]-ke[0]+we[0])/scale,
        'raw_final':{'IE_J':float(ie[-1]),'KE_J':float(ke[-1]),'WE_J':float(we[-1]),'Ux_J':float(ux[-1]),'Uy_J':float(uy[-1]),'D_J':float(rawD[-1])},
        'raw_F_same_row_OFF_FX_pass':bool(saved['checks']['strict_same_row_OFF_FX']),'input_T01_sha256':c['inputs']['T01']['sha256'],
        'input_CSV_sha256':c['inputs']['csv']['sha256'],'raw_rows_near_event':[],'event':None,'no_phase_shift':True}
    if len(events)==1:
        j=int(events[0]);pre=j-1;post=j+2;assert pre>=0 and post<len(a)
        candidates=np.flatnonzero((np.arange(len(a))>=j)&(abs(fx)<=g['force_zero_N'])&(abs(fy)<=g['force_zero_N']))
        zero=int(candidates[0]) if len(candidates) else None
        cells_pre=intervals(a[pre],kt,kn);cells_post=intervals(a[post],kt,kn)
        deltas={key:sub(cells_post[key],cells_pre[key]) for key in cells_pre}
        lost=sub(add(cells_pre['Ux'],cells_pre['Uy']),add(cells_post['Ux'],cells_post['Uy']))
        ledger=sub(sub(deltas['D'],lost),sub(deltas['WE'],deltas['KE']))
        numbers={'IE':ie,'KE':ke,'WE':we,'Ux':ux,'Uy':uy,'D':rawD};change={k:float(v[post]-v[pre]) for k,v in numbers.items()}
        reference=c['normal_work_J']+float(ux[pre])+change['WE']-change['KE']
        mismatch=float(ie[post]-reference);retained_excess=float(ie[post]-c['normal_work_J'])
        expected_F=saved['events'][0];fixed=c['id'].startswith('FIXED');after=c['id'].startswith('AFTER')
        checks.update(selected_rows_available=post<len(a),forces_zero_on_selected_post=peak(a[post:,24:26])<=g['force_zero_N'],
            saved_F_event_row_preserved=j==expected_F['row'],saved_F_lag_preserved=zero is not None and zero-j==expected_F['lag_rows'],
            retained_ledger_consistency=abs(mismatch)/scale<=g['energy_fraction'],
            normal_IE_baseline_before=abs(float(ie[pre]-ux[pre]-uy[pre])-c['normal_work_J'])/scale<=g['energy_fraction'],
            post_recoverable_force_proxy_zero=ux[post]==0 and uy[post]==0,
            final_IE_same_as_post=abs(float(ie[-1]-ie[post]))/scale<=g['energy_fraction'])
        if fixed:
            reserve=cfg['reference']['linear_x_at_0p02_mm_J']
            checks.update(fixed_X_reserve=abs(float(ux[pre])-reserve)/reserve<=g['reservoir_fraction'],
                fixed_IE_excess_is_reserve=abs(retained_excess-reserve)/reserve<=g['reservoir_fraction'],
                fixed_no_recorded_KE_gain=abs(change['KE'])/reserve<=g['reservoir_fraction'],
                fixed_no_recorded_WE_change=abs(change['WE'])/reserve<=g['reservoir_fraction'])
        if after:checks['zero_reserve_control']=float(ux[pre])==0 and abs(retained_excess)/scale<=g['energy_fraction']
        for z in range(max(0,j-2),min(len(a),j+4)):
            result['raw_rows_near_event'].append({'row':z,'time_ms':float(t[z]),'OFF':float(off[z]),'Fx_N':float(fx[z]),'Fy_N':float(fy[z]),
                **{key+'_J':float(values[z]) for key,values in numbers.items()},
                'recoverable_partition_asserted':bool(z==pre or z>=post)})
        result['event']={'OFF_row':j,'pre_row':pre,'post_row':post,'pre_time_ms':float(t[pre]),'OFF_time_ms':float(t[j]),'post_time_ms':float(t[post]),
            'force_zero_row':zero,'raw_force_lag_rows':None if zero is None else zero-j,
            'Fx_on_OFF_N':float(fx[j]),'pre_Ux_J':float(ux[pre]),'pre_Uy_J':float(uy[pre]),'post_IE_J':float(ie[post]),
            'post_IE_minus_normal_work_J':retained_excess,'raw_changes_J':change,'retention_reference_post_IE_J':reference,
            'retention_mismatch_J':mismatch,'missing_energy_if_IE_replaced_by_normal_work_J':retained_excess,
            'exact_pre_intervals':{k:pack(v) for k,v in cells_pre.items()},'exact_post_intervals':{k:pack(v) for k,v in cells_post.items()},
            'exact_change_intervals':{k:pack(v) for k,v in deltas.items()},'exact_deleted_reserve_interval':pack(lost),'exact_event_balance_interval':pack(ledger),
            'no_partition_on_OFF_or_next_row':True,'internal_transfer_route_identified':False,'prescribed_motion_not_free_release':True}
    else:
        checks.update(elastic_return_control=abs(float(ie[-1]))/scale<=g['energy_fraction'],
            X_reserve_peak=abs(float(ux.max())-cfg['reference']['linear_x_at_0p02_mm_J'])/scale<=g['reservoir_fraction'],
            no_normal_load=peak(fy)==0 and peak(a[:,36])==0,no_OFF=np.all(off==1))
    checks={k:bool(v) for k,v in checks.items()};result.update(checks=checks,all_checks_pass=all(checks.values()))
    h.dump(dest/'audit.json',result);h.dump(dest/'CSV_mismatches.json',mismatches)
    # Saved sparse views retain original values/times; full old histories stay pinned.
    selected=sorted(set(np.linspace(0,len(a)-1,401,dtype=int).tolist()+[r['row'] for r in result['raw_rows_near_event']]))
    with (dest/'ledger_view.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['original_row','time_ms','OFF','Fx_N','Fy_N','IE_J','KE_J','WE_J','Ux_force_proxy_J','Uy_force_proxy_J','IE_minus_Ux_Uy_J'])
        writer.writerows([[z,float(t[z]),float(off[z]),float(fx[z]),float(fy[z]),float(ie[z]),float(ke[z]),float(we[z]),float(ux[z]),float(uy[z]),float(rawD[z])] for z in selected])
    return result,data

def audit():
    dest=OUT/'verification_r1';assert not dest.exists();dest.mkdir();cfg=run.read(CFG);tick=time.perf_counter()
    assert h.sha(reader.__file__)==cfg['reader_sha256'];saved=run.read(ROOT/cfg['cached_references']['saved_F_summary']['path'])
    assert len(saved['strict_same_row_OFF_FX_failed_cases'])==5 and not saved['all_scientific_checks_pass']
    results={};decoder_checks=None
    for c in cfg['cases']:
        results[c['id']],data=case(cfg,c,dest/c['id'],saved['cases'][c['id']])
        if decoder_checks is None:decoder_checks=precision.reject_tests(data,cfg['binary_schema'],c['title'])
    synthetic=[]
    for fx,fy in [(Q(0),Q(0)),(Q(430),Q(0)),(Q(409),Q(495)),(Q(-17),Q(7))]:
        row=np.zeros(41);row[1]=np.float32(float(fx*fx/(2*Q(21500))+fy*fy/(2*Q(56000))));row[24]=np.float32(float(fx));row[25]=np.float32(float(fy))
        lo,hi=intervals(row,21500,56000)['D'];synthetic.append({'Fx_exact':str(fx),'Fy_exact':str(fy),'zero_contained':bool(lo<=0<=hi)})
    decoder_checks['known_elastic_energy_cells']=all(v['zero_contained'] for v in synthetic)
    h.dump(dest/'decoder_reference_checks.json',{'pass':all(decoder_checks.values()),'checks':decoder_checks,'synthetic':synthetic})
    ref=run.read(OUT/'reference_verification.json');comparisons=[]
    for a,b in [('FIXED_CAP200NS','FIXED_CAP100NS'),('FIXED_CAP100NS','FIXED_CAP050NS'),('PROP_CAP100NS','PROP_CAP050NS'),('AFTER_CAP100NS','AFTER_CAP050NS')]:
        va=results[a]['event'];vb=results[b]['event'];scale=.0043 if a.startswith(('FIXED','PROP')) else .03
        metrics={key:abs(va[key]-vb[key])/scale for key in ['post_IE_J','post_IE_minus_normal_work_J','pre_Ux_J']}
        checks={key:value<=cfg['gates']['reservoir_fraction'] for key,value in metrics.items()}
        comparisons.append({'cases':[a,b],'fractions':metrics,'checks':checks,'original_event_rows_not_rephased':True})
    elapsed=time.perf_counter()-tick
    s={'iteration':'IMPACT-I02I-L','created_utc':h.NOW(),'cases':results,'comparisons':comparisons,
        'case_checks_passed':sum(sum(r['checks'].values()) for r in results.values()),'case_checks_total':sum(len(r['checks']) for r in results.values()),
        'comparison_checks_passed':sum(sum(r['checks'].values()) for r in comparisons),'comparison_checks_total':sum(len(r['checks']) for r in comparisons),
        'reference_checks_passed':sum(ref['checks'].values())+sum(decoder_checks.values()),'reference_checks_total':len(ref['checks'])+len(decoder_checks),
        'all_declared_checks_pass':all(r['all_checks_pass'] for r in results.values()) and all(all(r['checks'].values()) for r in comparisons) and ref['pass'] and all(decoder_checks.values()) and elapsed<=cfg['gates']['maximum_diagnostic_seconds'],
        'runtime_seconds':elapsed,'total_rows':sum(r['rows'] for r in results.values()),'total_values':sum(r['values_compared'] for r in results.values()),
        'config_sha256':h.sha(CFG),'audit_sha256':h.sha(__file__),'software':{'python':platform.python_version(),'numpy':np.__version__,'interval_arithmetic':'Fraction exact'},
        'old_F_same_row_failures_preserved':len(saved['strict_same_row_OFF_FX_failed_cases']),
        'solver_jobs':0,'old_solver_rerun':False,'numeric_retention_ledger_compatible':all(r['all_checks_pass'] for r in results.values()),
        'internal_transfer_route_identified':False,'free_mixed_separation_tested':False,'release_policy_complete':False,
        'physical_fracture_calibrated':False,'physical_propagation_qualified':False,'aircraft_impact_qualified':False}
    h.dump(dest/'summary.json',s)
    print(json.dumps({'pass':s['all_declared_checks_pass'],'case_checks':[s['case_checks_passed'],s['case_checks_total']],
        'comparisons':[s['comparison_checks_passed'],s['comparison_checks_total']],'reference':[s['reference_checks_passed'],s['reference_checks_total']],
        'rows':s['total_rows'],'values':s['total_values'],'seconds':elapsed,'failed':{n:[k for k,v in r['checks'].items() if not v] for n,r in results.items()},
        'event_interval_zero':{n:r['event']['exact_event_balance_interval']['contains_zero'] for n,r in results.items() if r['event']}}),flush=True)

if __name__=='__main__':audit()
