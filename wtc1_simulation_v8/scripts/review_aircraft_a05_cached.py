"""Correct only derived audit metrics from saved arrays; retain first audits."""
import numpy as np
from run_aircraft_a05 import OUT,CFG,read,dump,sha,rel,now,harness,preserved
from audit_aircraft_a04 import histories

def main():
    s=read(OUT/'r3/summary.json');paths={k:OUT/v for k,v in read(OUT/'case_selection.json')['case_directories'].items()};proof=[];a=read(CFG)['acceptance']
    for r in s['cases']:
        d=paths[r['case']['id']];z=np.load(d/'balance_history_SI.npz');e=z['energy_residual_J'];gen=z['generated_energy_J'];mask=gen>a['local_energy_comparison_minimum_J'];r['maximum_local_energy_residual_fraction_above_1kJ']=float(np.max(abs(e[mask])/gen[mask],initial=0));ok=bool(np.all(abs(e[mask])<=a['local_energy_residual_generated_energy_fraction']*gen[mask]+a['CSV_KE_precision_allowance_J']));assert ok==r['checks']['energy_local_within_declared_limit']
        r['maximum_face_reference_strength_ratio']=max(q.get('radome_face_strength_ratio',0) for q in r['states']);r['first_saved_face_reference_exceeded_ms']=next((q['time_ms'] for q in r['states'] if q.get('radome_face_strength_ratio',0)>1),None)
        H=histories(d/(read(d/'generation.json')['name']+'T01.csv'));keys=[k for k in H if k.startswith('SELF_CONTACT_RAW_HISTORY')];r['maximum_self_contact_raw_Nms']=float(np.max(abs(np.column_stack([H[k] for k in keys])))) if keys else None
        assert np.all(z['global_plastic_work_J']<=np.array([q for q in histories(d/(read(d/'generation.json')['name']+'T01.csv'))['INTERNAL ENERGY']]+([r['final_energy_terms_J']['INTERNAL ENERGY']*1000] if len(z['time_s'])==len(H['time'])+1 else []))*.001+1)
        proof.append({'case':r['case']['id'],'original_audit':rel(d/'audit.json'),'original_sha256':sha(d/'audit.json'),'balance_arrays_sha256':sha(d/'balance_history_SI.npz')})
    a0=np.load(paths['COMP_NOSC']/'verified_states_SI.npz');a1=np.load(paths['COMP_SELF']/'verified_states_SI.npz');s['self_contact_comparison']={'maximum_raw_Nms':next(r for r in s['cases'] if r['case']['id']=='COMP_SELF')['maximum_self_contact_raw_Nms'],'saved_displacements_bitwise_identical':bool(np.array_equal(a0['displacement_m'],a1['displacement_m'])),'horizon_ms':2,'does_not_test_active_self_contact':True}
    s.update(created_utc=now(),authoritative_cached_review=True,metric_correction='First composite audits shadowed local-energy ratio with last face-strength ratio; recomputed all local ratios from saved energy histories, unchanged pass/fail. RBE3 virtual cells ELEMENT_ID=0 excluded from signed radome collection; their zero fields did not change diagnostic maxima.',saved_first_audit_proof=proof,old_files_preserved=preserved(),harness_after_computations=harness())
    dst=OUT/'cached_review';dst.mkdir();dump(dst/'review.json',s);print({'integrity':s['integrity_only_pass'],'comparisons':s['comparisons'],'self_contact':s['self_contact_comparison']})

if __name__=='__main__':main()
