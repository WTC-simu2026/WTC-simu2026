"""J independent binary reader and exact rational quantization diagnosis.

No executable call, inferred phase, clipping, or old gate reassessment.
"""
from __future__ import annotations
import csv,json,math,platform,struct,time
from fractions import Fraction as Q
import numpy as np
import run_impact_i02i_output_precision as j
import decode_impact_i02i_t01 as reader
h=j.h;ROOT,OUT,CFG=j.ROOT,j.OUT,j.CFG

def qfloat(value):return Q.from_float(float(value))
def rounding_interval32(value):
    """Closed nearest-rounding cell, exact dyadic midpoints (no tolerance)."""
    x=np.float32(value);lo=float(np.nextafter(x,np.float32(-np.inf)));hi=float(np.nextafter(x,np.float32(np.inf)));q=qfloat(x)
    return (qfloat(lo)+q)/2,(q+qfloat(hi))/2
def decimal_error(token):
    mantissa,exp=token.lower().split('e');places=len(mantissa.split('.')[1])
    return Q(1,2)*Q(10)**(int(exp)-places)
def squared_range(lo,hi):
    return (Q(0) if lo<=0<=hi else min(lo*lo,hi*hi)),max(lo*lo,hi*hi)
def retained_interval(ie,f,k):
    il,ih=ie;fl,fh=f;ul,uh=squared_range(fl,fh)
    return (il-uh/(2*k))/1000,(ih-ul/(2*k))/1000
def interval_float(lo,hi):return math.nextafter(float(lo),-math.inf),math.nextafter(float(hi),math.inf)

def reject_tests(data,schema,title):
    rec=reader.records(data);mutations={}
    a=bytearray(data);a[rec[0][0]+4+len(rec[0][1])+3]^=1;mutations['wrong_trailing_marker']=bytes(a)
    a=bytearray(data);a[4:8]=struct.pack('>i',3041);mutations['wrong_version']=bytes(a)
    a=bytearray(data);pos=rec[11][0]+4;a[pos:pos+4]=struct.pack('>i',99);mutations['wrong_spring_code']=bytes(a)
    mutations['truncated_last_row']=data[:-1];mutations['extra_tail']=data+b'\0'
    checks={}
    for name,value in mutations.items():
        try:reader.decode(value,schema,title);checks[name]=False
        except (ValueError,UnicodeError,struct.error):checks[name]=True
    return checks

def case(cfg,c,dest):
    dest.mkdir();inputs=c['inputs']
    for entry in inputs.values():assert h.sha(ROOT/entry['path'])==entry['sha256']
    data=(ROOT/inputs['T01']['path']).read_bytes();a,meta=reader.decode(data,cfg['schema'],c['title'])
    other=reader.strided_check(data,cfg['schema']);stride_match=np.array_equal(a,other)
    with (ROOT/inputs['csv']['path']).open(encoding='utf-8',newline='') as f:csvrows=list(csv.reader(f))
    headers=csvrows.pop(0);dec=np.asarray(csvrows,dtype=np.float64)
    assert len(headers)==41 and dec.shape==a.shape,'CSV coverage mismatch'
    raw_tokens=[[format(value,'.6e') for value in row] for row in a]
    token_match=[[left==right.strip() for left,right in zip(raw,csvrow)] for raw,csvrow in zip(raw_tokens,csvrows)]
    unmatched=[{'row':r,'column':col,'field':headers[col],'from_binary':raw_tokens[r][col],'saved':csvrows[r][col]} for r,row in enumerate(token_match) for col,match in enumerate(row) if not match]
    # Variable identities derive from stored codes and saved /TH requests;
    # whole CSV equality independently checks all row and column offsets.
    t=a[:,0];ie=a[:,1]*.001;spring=a[:,10]*.001;element=a[:,28]*.001;force=a[:,25];gap=a[:,36]-a[:,30]
    U=force*force/(2*cfg['k_N_per_mm'])*.001;D=ie-U
    csv_D=dec[:,1]*.001-dec[:,25]**2/(2*cfg['k_N_per_mm'])*.001
    history=np.maximum.accumulate(gap);elastic=history<=c['references']['delta0_mm'];k=Q(str(cfg['k_N_per_mm']))
    interval_rows=[];bad_binary=[];bad_csv=[];all_negative_binary=0;all_negative_csv=0
    for r,row in enumerate(a):
        ib=rounding_interval32(row[1]);fb=rounding_interval32(row[25]);lo,hi=retained_interval(ib,fb,k)
        c_ie=Q(csvrows[r][1]);c_f=Q(csvrows[r][25]);ci=qfloat(row[1]);cf=qfloat(row[25])
        ei=decimal_error(csvrows[r][1]);ef=decimal_error(csvrows[r][25])
        ic=(c_ie+ib[0]-ci-ei,c_ie+ib[1]-ci+ei);fc=(c_f+fb[0]-cf-ef,c_f+fb[1]-cf+ef)
        lc,hc=retained_interval(ic,fc,k)
        contains=lo<=0<=hi;cc=lc<=0<=hc
        raw_Q=(qfloat(row[1])-qfloat(row[25])**2/(2*k))/1000
        csv_Q=(c_ie-c_f*c_f/(2*k))/1000
        bn=raw_Q<0;cn=csv_Q<0;all_negative_binary+=bn;all_negative_csv+=cn
        if bn and elastic[r] and not contains:bad_binary.append(r)
        if cn and not cc:bad_csv.append(r)
        bl,bh=interval_float(lo,hi);cl,ch=interval_float(lc,hc)
        interval_rows.append([float(t[r]),bool(elastic[r]),float(raw_Q),bl,bh,bool(contains),float(csv_Q),cl,ch,bool(cc)])
    worst=int(np.argmin(D));lo,hi=retained_interval(rounding_interval32(a[worst,1]),rounding_interval32(a[worst,25]),k)
    e0=c['references']['initial_energy_J'];balance=float(np.max(abs(e0-ie-a[:,2]*.001+a[:,9]*.001))/e0)
    old=j.read(j.OLD/'verification_r1/summary.json')['cases'][c['id']]
    starter=(ROOT/inputs['starter']['path']).read_text();engine=(ROOT/inputs['engine']['path']).read_text()
    checks={'exact_framing_and_EOF':meta['exact_EOF_consumed'],'header_and_cards':'/TFILE/4' in engine and 'OFF        FX        FY        LX        LY        IE' in starter,
        'independent_readers_exact':bool(stride_match),'all_values_reproduce_CSV':not unmatched,
        'all_global_spring_IE_bits_equal':bool(np.array_equal(a[:,1],a[:,10]) and np.array_equal(a[:,1],a[:,28])),
        'exact_old_row_count':len(a)==old['metrics']['rows'],'finite_time':bool(np.isfinite(a).all() and np.all(np.diff(t)>0)),
        'no_truncation_or_extrapolation':bool(0<=c['saved_case']['end_ms']-t[-1]<=cfg['gates']['end_coverage_steps']*c['saved_case']['maximum_dt_ms']),
        'binary_negative_elastic_zero_compatible':not bad_binary,'CSV_negative_zero_compatible':not bad_csv,
        'energy_balance':balance<=cfg['gates']['energy_balance_fraction'],
        'old_I_sign_gate_remains_failed':not old['checks']['retained_nonnegative'] and not old['all_checks_pass'],
        'no_OFF_or_new_compression':bool(np.all(a[:,23]==1) and np.all(gap[1:]>0)),
        'no_other_force_reservoir':bool(np.all(a[:,24]==0))}
    cap=c['saved_case']['maximum_dt_ms'];metrics={'rows':len(a),'values_compared':a.size,'unmatched_values':len(unmatched),
        'max_CSV_binary_difference_by_field':{headers[col].strip():float(np.max(abs(a[:,col]-dec[:,col]))) for col in range(41)},
        'binary_min_retained_J':float(D.min()),'CSV_min_retained_J':float(csv_D.min()),
        'max_CSV_binary_retained_difference_J':float(np.max(abs(csv_D-D))),
        'binary_negative_rows':int(all_negative_binary),'CSV_negative_rows':int(all_negative_csv),
        'binary_negative_elastic_incompatible_rows':bad_binary,'CSV_negative_incompatible_rows':bad_csv,
        'old_threshold_J':1e-10,'binary_min_below_old_threshold_diagnostic_only':bool(D.min() < -1e-10),
        'binary_energy_balance_fraction':balance,'binary_final_IE_J':float(ie[-1]),'binary_final_U_J':float(U[-1]),
        'binary_final_D_J':float(D[-1]),'binary_final_KE_J':float(a[-1,2]*.001),'binary_final_velocity_mm_per_ms':float(a[-1,38]),
        'worst_binary':{'row':worst,'t_ms':float(t[worst]),'raw_D_J':float(D[worst]),
            'lower_J':float(lo),'upper_J':float(hi),'lower_exact':str(lo),'upper_exact':str(hi)},
        'all_IE_three_channels_identical':checks['all_global_spring_IE_bits_equal'],'record_interval_limit_ms':cap}
    with (dest/'decoded_binary.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(headers);writer.writerows([[format(x,'.17e') for x in row] for row in a])
    with (dest/'retained_intervals.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['time_ms','history_still_elastic','binary_IE_minus_U_J','binary_lower_J','binary_upper_J',
            'binary_zero_compatible','CSV_IE_minus_U_J','CSV_lower_J','CSV_upper_J','CSV_zero_compatible']);writer.writerows(interval_rows)
    result={'case':c['id'],'family':c['family'],'metadata':meta,'metrics':metrics,'checks':checks,
        'all_checks_pass':all(checks.values()),'binary_sha256':inputs['T01']['sha256'],'CSV_sha256':inputs['csv']['sha256'],
        'no_old_gate_promoted':True,'no_phase_shift':True,'no_physical_calibration':True}
    h.dump(dest/'audit.json',result);h.dump(dest/'CSV_mismatches.json',unmatched)
    return result,data

def audit():
    dest=OUT/'verification_r1';assert not dest.exists(),'Keep audits';dest.mkdir()
    tick=time.perf_counter();cfg=j.read(CFG);results={};malformed=None
    assert h.sha(j.OLD/'verification_r1/summary.json')==cfg['saved_I_summary_sha256']
    for c in cfg['cases']:
        results[c['id']],data=case(cfg,c,dest/c['id'])
        if malformed is None:malformed=reject_tests(data,cfg['schema'],c['title'])
    # Exact reference identity: binary-format bounds must contain zero for
    # known dyadic elastic states rounded independently, not just saved data.
    synthetic=[];k=Q(str(cfg['k_N_per_mm']))
    for f_exact in [Q(0),Q(1,8),Q(7),Q(123),Q(495)]:
        ie_exact=f_exact*f_exact/(2*k)
        f32=float(np.float32(float(f_exact)));ie32=float(np.float32(float(ie_exact)))
        lo,hi=retained_interval(rounding_interval32(ie32),rounding_interval32(f32),k)
        synthetic.append({'force_exact':str(f_exact),'IE_exact_N_mm':str(ie_exact),'zero_contained':bool(lo<=0<=hi),
            'lower_exact':str(lo),'upper_exact':str(hi)})
    refchecks={**malformed,'known_elastic_states':all(r['zero_contained'] for r in synthetic)}
    h.dump(dest/'decoder_reference_checks.json',{'checks':refchecks,'synthetic_states':synthetic,'pass':all(refchecks.values())})
    elapsed=time.perf_counter()-tick
    summary={'iteration':'IMPACT-I02I-J','created_utc':h.NOW(),'cases':results,
        'case_checks_passed':sum(sum(r['checks'].values()) for r in results.values()),'case_checks_total':sum(len(r['checks']) for r in results.values()),
        'reference_checks_passed':sum(refchecks.values()),'reference_checks_total':len(refchecks),
        'all_declared_checks_pass':all(r['all_checks_pass'] for r in results.values()) and all(refchecks.values()) and elapsed<=cfg['gates']['maximum_diagnostic_seconds'],
        'runtime_seconds':elapsed,'software':{'python':platform.python_version(),'numpy':np.__version__,'exact_interval':'Python Fraction'},
        'configuration_sha256':h.sha(CFG),'audit_sha256':h.sha(__file__),'reader_sha256':h.sha(reader.__file__),
        'total_rows':sum(r['metrics']['rows'] for r in results.values()),'total_values':sum(r['metrics']['values_compared'] for r in results.values()),
        'no_solver_run':True,'no_converter_run':True,'no_old_solver_rerun':True,'old_I_four_sign_failures_preserved':True,
        'official_binary_schema_verified':False,'bounded_binary_decoder_verified':all(r['all_checks_pass'] for r in results.values()),
        'interpretation':'Sign within finite representation intervals is unresolved, not corrected. Exact converter code and internal double-precision history unavailable.',
        'physical_propagation_qualified':False,'mixed_mode_qualified':False,'aircraft_impact_qualified':False,
        'source_convention_verified':False,'E_sensitivities_resolved':False}
    h.dump(dest/'summary.json',summary)
    print(json.dumps({'pass':summary['all_declared_checks_pass'],'cases':[summary['case_checks_passed'],summary['case_checks_total']],
        'reference':[summary['reference_checks_passed'],summary['reference_checks_total']],'rows':summary['total_rows'],'values':summary['total_values'],
        'seconds':elapsed,'failed':{n:[k for k,v in r['checks'].items() if not v] for n,r in results.items()},
        'binary_min_D_J':{n:r['metrics']['binary_min_retained_J'] for n,r in results.items()},
        'binary_negative_incompatible':{n:r['metrics']['binary_negative_elastic_incompatible_rows'] for n,r in results.items()},
        'CSV_negative_incompatible':{n:r['metrics']['CSV_negative_incompatible_rows'] for n,r in results.items()}}),flush=True)

if __name__=='__main__':audit()
