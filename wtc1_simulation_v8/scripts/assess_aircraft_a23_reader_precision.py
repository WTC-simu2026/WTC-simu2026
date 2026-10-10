"""Bound printed VTK precision separately from literal initial diagnostic failures."""
from run_aircraft_a23 import *

def printed_bound(x):
    out=np.zeros_like(x);nz=abs(x)>0
    # The converter prints %g: six significant digits, in addition to float32 animation storage.
    out[nz]=.5*10.**(np.floor(np.log10(abs(x[nz])))-5)
    return out

def main():
    rows=[]
    for revision in ['w0','w1']:
        original=read(OUT/f'native_fields_{revision}_audit.json')
        for r in original['samples']:
            cid=r['case'];g=read(OUT/revision/cid/'generation.json');xyz=np.asarray(g['nodes_mm']);q=vtk((ROOT/r['vtk']).read_text(encoding='utf-8'));order=np.argsort(q['NODE_ID'])
            p=q['points'].reshape(-1,3)[order];d=q['Displacement'].reshape(-1,3)[order];difference=abs(p-xyz-d)
            bound=printed_bound(p)+printed_bound(d)+4*np.finfo(np.float32).eps*np.maximum.reduce([abs(p),abs(d),abs(xyz)])+1e-8
            checks={k:v for k,v in r['checks'].items() if k!='displacement_coordinate_identity'}
            checks['identity_with_explicit_printing_bound']=bool(np.all(difference<=bound))
            rows.append({'revision':revision,'case':cid,'time_ms':r['time_ms'],'native_sha256':r['native_sha256'],
              'vtk_sha256':r['vtk_sha256'],'literal_2e_minus5_mm_gate':r['checks']['displacement_coordinate_identity'],
              'maximum_coordinate_identity_error_mm':float(difference.max()),'maximum_bound_mm':float(bound.max()),
              'maximum_excess_mm':float(np.maximum(difference-bound,0).max()),'checks':checks,'pass':all(checks.values())})
    dump(OUT/'native_reader_precision_addendum.json',{'created_utc':now(),'samples':rows,'pass':all(r['pass'] for r in rows),
      'literal_initial_checks_retained':True,'solver_acceptance_thresholds_unchanged':True,
      'different_observation_question':'check coordinate identity against float32 storage and six significant digit printed conversion, not the unbounded assertion that text is exact',
      'native_field_audit_failed_attempt':'initial reader reloaded compressed NPZ for each node/component; reader stopped only and corrected to cache arrays once. Existing VTK conversions retained; no native solver interrupted or rerun.',
      'old_native_solvers_rerun':0,'physical_validation':False})
    dump(OUT/'postprocessor_recovery.json',{'created_utc':now(),'native_cases_completed':26,
      'w0_pair_failure':'assertion of exact reference/connected TFILE timestamps; recovered within common temporal support with saved native histories, no extrapolation.',
      'w1_pair_failure':'postprocessor inherited w0 extension path then requested w1-only last_clip_IE_J key. New cached reader selects revision explicitly.',
      'original_generators_and_reviews_retained':True,'native_reruns':0,'replacement_results':'coupling_summary.json, paired_w0_cached_audit.json, paired_w1_cached_audit.json',
      'cached_boundary_diagnostic_serialization':'NumPy bool cast to Python bool before JSON write; no prior diagnostic file was overwritten.'})
    print({'native_precision_addendum':all(r['pass'] for r in rows),'samples':len(rows)},flush=True)

if __name__=='__main__':main()
