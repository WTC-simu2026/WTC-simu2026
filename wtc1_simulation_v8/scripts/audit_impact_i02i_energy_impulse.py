"""Additional saved-history diagnostic for I02I-D; no solver or gate revision.

Normalize the signed momentum residual by boundary impulse as in B. Also
report normalization by small net momentum, which exposes cancellation and
time staggering. Do not promote this additional diagnostic to a declared gate.
"""
import json
from pathlib import Path
import numpy as np
import run_impact_i02i_energy as d
import audit_impact_i02i_fixed_penalty as previous

def main():
    path=d.OUT/'impulse_diagnostics.json'
    assert not path.exists(), 'Preserve saved diagnostics'
    cfg=json.loads(d.CFG.read_text(encoding='utf-8'));cases={}
    for case in cfg['cases']:
        folder=d.OUT/case['id'];headers,a=d.cached.read_history(folder)
        nodes=previous.columns(headers,'NODES',6);idx={s.strip():i for i,s in enumerate(headers)};metrics={}
        for axis,impulse,velocity in [('X',4,2),('Y',5,3)]:
            j1=a[:,nodes[1][impulse]];j2=a[:,nodes[2][impulse]]
            momentum=a[:,idx[axis+'-MOMENTUM']];residual=j1+j2-momentum
            boundary=max(float(np.max(np.abs(j1))),float(np.max(np.abs(j2))),1e-15)
            momentum_peak=float(np.max(np.abs(momentum)))
            nodal=.5*cfg['connector']['mass_g']*(a[:,nodes[1][velocity]]+a[:,nodes[2][velocity]])
            metrics[axis]={'max_abs_residual_N_ms':float(np.max(np.abs(residual))),
                'boundary_impulse_scale_N_ms':boundary,
                'residual_fraction_of_boundary_impulse':float(np.max(np.abs(residual)))/boundary,
                'peak_global_momentum_N_ms':momentum_peak,
                'residual_fraction_of_net_momentum':None if momentum_peak==0 else float(np.max(np.abs(residual)))/momentum_peak,
                'nodal_mass_velocity_to_global_momentum_max_error_N_ms':float(np.max(np.abs(nodal-momentum))),
                'node1_final_impulse_N_ms':float(j1[-1]),'node2_final_impulse_N_ms':float(j2[-1])}
        ci=previous.columns(headers,'SEAM_HISTORY',6)[1]
        off=a[:,ci[0]];max_active=np.max(np.diff(a[:,0])[off[1:]>=.5])
        metrics['sampling']={'last_recorded_time_ms':float(a[-1,0]),
            'declared_run_end_ms':json.loads((folder/'generation.json').read_text(encoding='utf-8'))['end_ms'],
            'max_active_recorded_dt_ms':float(max_active),
            'max_all_recorded_dt_ms':float(np.max(np.diff(a[:,0]))),
            'final_record_is_not_exact_run_end':True,
            'interpretation':'One record per engine cycle, including larger steps after deletion. Last record precedes run end: no endpoint is extrapolated.'}
        cases[case['id']]=metrics
    result={'created_utc':d.NOW(),'iteration':'IMPACT-I02I-D','cases':cases,
        'script_sha256':d.sha(__file__),'config_sha256':d.sha(d.CFG),
        'diagnostic_added_after_predeclaration':True,'new_scientific_gate_added':False,
        'interpretation':'Signed reaction impulse sum vs global momentum, in N ms. Small net momentum is the cancellation of large opposite impulses; finite CSV precision and solver time staggering limit interpretation. Neither a small boundary-normalized residual nor imposed motion validates free-body inertia.',
        'no_solver_rerun':True}
    d.dump(path,result)
    print(json.dumps({'cases':len(cases),'max_absolute_residual_N_ms':max(v[a]['max_abs_residual_N_ms'] for v in cases.values() for a in ['X','Y']),'max_boundary_normalized_residual_fraction':max(v[a]['residual_fraction_of_boundary_impulse'] for v in cases.values() for a in ['X','Y'])}))

if __name__=='__main__':main()
