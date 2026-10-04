"""Post-declaration saved-history diagnostic; adds no qualification gate."""
import json
import numpy as np
import run_impact_i02i_dtcap as f
import audit_impact_i02i_fixed_penalty as columns

def main():
    output=f.OUT/'residual_plateau_diagnostic.json';assert not output.exists()
    cases={}
    for name in ['AFTER_CAP100NS','AFTER_CAP050NS']:
        folder=f.OUT/name;h,a=f.inherited.cached.read_history(folder)
        idx={s.strip():i for i,s in enumerate(h)};nodes=columns.columns(h,'NODES',6)
        p=a[:,idx['X-MOMENTUM']];j=a[:,nodes[1][4]]+a[:,nodes[2][4]]
        residual=j-p;row=int(np.argmax(np.abs(residual)))
        meta=json.loads((folder/'generation.json').read_text(encoding='utf-8'))
        times=np.array([v[0] for v in meta['x_path']]);nearest=int(np.argmin(np.abs(times-a[row,0])))
        cases[name]={'maximum_row':row,'time_ms':float(a[row,0]),
            'residual_N_ms':float(residual[row]),'global_momentum_N_ms':float(p[row]),
            'nodal_momentum_N_ms':float(.1*(a[row,nodes[1][2]]+a[row,nodes[2][2]])),
            'nearest_input_function_time_ms':float(times[nearest]),
            'distance_to_input_function_knot_ms':float(abs(times[nearest]-a[row,0])),
            'rows_near_maximum':[{'time_ms':float(a[q,0]),'raw_residual_N_ms':float(residual[q]),
                'momentum_N_ms':float(p[q]),'node2_velocity_mm_per_ms':float(a[q,nodes[2][2]])}
                for q in range(max(0,row-2),min(len(a),row+3))]}
    f.dump(output,{'created_utc':f.NOW(),'cases':cases,'script_sha256':f.sha(__file__),
        'diagnostic_added_after_predeclaration':True,'qualification_gates_changed':False,
        'no_solver_rerun':True,'interpretation':'Coincidence with a tabulated input knot is a diagnostic; it does not establish the internal algorithm or prove an input-table cause. Keep the nonvanishing refinement plateau open.'})
    print(json.dumps(cases),flush=True)
if __name__=='__main__':main()
