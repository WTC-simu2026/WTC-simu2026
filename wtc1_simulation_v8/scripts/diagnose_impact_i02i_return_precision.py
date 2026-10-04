"""Saved-output rounding diagnostic; never changes an I declared gate."""
from __future__ import annotations
import csv,json,math
import numpy as np
import run_impact_i02i_free_return as i
h=i.h

def uncertainty(token):
    # Observed decimal format: one leading digit and six decimals. Include
    # both that quantization and half a float32 ULP, without clipping values.
    mantissa,exp=token.lower().split('e');digits=len(mantissa.split('.')[1]);value=float(token)
    decimal=.5*10.**(int(exp)-digits)
    binary=.5*abs(float(np.spacing(np.float32(value))))
    return decimal+binary

def diagnose():
    dest=i.OUT/'precision_diagnostic_r1.json';assert not dest.exists()
    cfg=json.loads(i.CFG.read_text());summary=json.loads((i.OUT/'verification_r1/summary.json').read_text());cases={}
    for c in cfg['cases']:
        p=next((i.OUT/c['id']).glob('*.csv'));rows=list(csv.reader(p.open(encoding='utf-8')));headers=rows.pop(0)
        import audit_impact_i02i_fixed_penalty as cols
        fi=cols.columns(headers,'SEAM_HISTORY',6)[1][2];ei=next(j for j,s in enumerate(headers) if s.strip()=='INTERNAL ENERGY')
        k=cfg['references'][c['family']]['k_N_per_mm'];negative=[]
        for j,row in enumerate(rows):
            f=float(row[fi]);ie=float(row[ei])*.001;u=.5*f*f/k*.001;d=ie-u
            if d<0:
                ef=uncertainty(row[fi]);ee=uncertainty(row[ei])*.001
                bound=ee+((abs(f)+ef)**2-f*f)/(2*k)*.001
                negative.append({'row':j,'t_ms':float(row[0]),'raw_retained_J':d,'rounding_bound_J':bound,
                    'zero_in_rounding_interval':bool(-d<=bound)})
        cases[c['id']]={'negative_rows':len(negative),'all_negative_rows_compatible_with_rounding':all(r['zero_in_rounding_interval'] for r in negative),
            'worst':min(negative,key=lambda r:r['raw_retained_J']) if negative else None,
            'declared_gate_still_failed':not summary['cases'][c['id']]['checks']['retained_nonnegative'],
            'raw_csv_sha256':h.sha(p),'negative_row_details':negative}
    h.dump(dest,{'created_utc':h.NOW(),'cases':cases,'script_sha256':h.sha(__file__),
        'interpretation':'Conditional finite representation bound, observed .6e CSV plus configured TFILE/4 float32; compatible is not proof of internal algorithm.',
        'gate_override':False,'no_clipping':True,'no_phase_shift':True,'no_engine_run':True})
    print(json.dumps({name:{key:v[key] for key in ['negative_rows','all_negative_rows_compatible_with_rounding','worst','declared_gate_still_failed']} for name,v in cases.items()}),flush=True)

if __name__=='__main__':diagnose()
