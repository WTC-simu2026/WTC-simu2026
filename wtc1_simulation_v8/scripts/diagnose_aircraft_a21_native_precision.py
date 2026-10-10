"""Compare cached A20 native float32 global ledger with its printed CSV ledger."""
from run_aircraft_a21 import *
from recover_aircraft_a05_history import records

def main():
    guard(); dst=OUT/'native_precision_review.json'; assert not dst.exists()
    names=list(histories(SOURCE/'A20_CORE3D_TIED_20T01.csv'))[:23]
    schema=read(SOURCE/'history_recovery.json'); nr=schema['records_per_frame']; h=schema['header_records']
    rr=records(SOURCE/'A20_CORE3D_TIED_20T01'); ro=records(SOURCE/'observer/A20_CORE3D_TIED_20T02')
    rows=[]
    for i in range(schema['rows']):
        rows.append(np.concatenate([np.frombuffer(p,dtype='>f4').astype(float) for p in rr[h+i*nr:h+i*nr+2]]))
    rows.append(np.concatenate([np.frombuffer(p,dtype='>f4').astype(float) for p in ro[h:h+2]]))
    raw=np.asarray(rows); assert raw.shape==(1001,23); H=dict(zip(names,raw.T)); T=H['time']
    c=read(CFG)['acceptance']; terms=['KINETIC ENERGY','ROTATION ENERGY','INTERNAL ENERGY','HOURGLASS ENERGY','SPRING ENERGY','ELASTIC CONTACT ENERGY','FRICTIONAL CONTACT ENERGY','DAMPING CONTACT ENERGY ']
    total=sum(H[k] for k in terms)*.001; R=total-total[0]-H['EXTERNAL WORK']*.001
    G=sum(H[k] for k in terms if k!='KINETIC ENERGY')*.001
    excess=abs(R)-c['local_energy_residual_generated_energy_fraction']*G-c['CSV_KE_precision_allowance_J']
    active=G>c['local_energy_comparison_minimum_J']; bad=active&(excess>0)
    csv=np.load(OUT/'cached_energy_ledger_SI.npz'); delta=R-csv['residual_J']
    window=[]
    for lo,hi in read(CFG)['cached_analysis']['time_windows_ms']:
        mask=(T>=lo)&(T<=hi); ix=np.flatnonzero(mask); worst=ix[np.argmax(excess[mask])]
        window.append({'window_ms':[lo,hi],'failed_rows':int(bad[mask].sum()),'first_failure_ms':float(T[np.flatnonzero(mask&bad)[0]]) if (mask&bad).any() else None,'maximum_gate_excess_J':float(excess[worst]),'worst_time_ms':float(T[worst]),'residual_at_worst_J':float(R[worst]),'generated_at_worst_J':float(G[worst])})
    ix={int(np.argmax(excess)),int(np.argmax(abs(delta))),len(T)-1}
    if bad.any():ix.add(int(np.flatnonzero(bad)[0]))
    result={'created_utc':now(),'source':'cached native big endian float32 T01/T02 global records, independently mapped to the already verified native CSV column order','source_rows':len(T),'energy_terms':terms,'native_initial_KE_J':float(H['KINETIC ENERGY'][0]*.001),'native_KE_quantization_J':float(np.spacing(np.float32(H['KINETIC ENERGY'][0]))*.001),'maximum_printed_CSV_residual_difference_J':float(abs(delta).max()),'native_failed_rows':int(bad.sum()),'printed_CSV_failed_rows':read(OUT/'cached_energy_localization.json')['local_energy_failed_rows'],'windows':window,'samples':[{'time_ms':float(T[i]),'native_residual_J':float(R[i]),'CSV_residual_J':float(csv['residual_J'][i]),'difference_J':float(delta[i]),'generated_energy_J':float(G[i]),'gate_excess_J':float(excess[i])} for i in sorted(ix)],'printed_CSV_precision_alone_explains_failure':not bool(bad.any()),'thresholds_unchanged':True,'no_inferred_energy_added':True,'no_new_engine_run':True,'physical_impact_qualified':False}
    np.savez_compressed(OUT/'native_global_energy_SI.npz',time_ms=T,residual_J=R,generated_energy_J=G,gate_excess_J=excess,**{k.replace(' ','_').strip('_')+'_J':H[k]*.001 for k in terms})
    dump(dst,result); print(result,flush=True)

if __name__=='__main__':main()
