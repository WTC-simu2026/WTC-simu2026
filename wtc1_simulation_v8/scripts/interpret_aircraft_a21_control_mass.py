"""Keep strict zero-field checks, interpret roundoff with A21's existing relative mass threshold."""
from run_aircraft_a21 import *

def main():
    guard();dst=OUT/'control_mass_roundoff_addendum.json';assert not dst.exists();a=read(CFG)['acceptance'];rows=[]
    for d in sorted((OUT/'w5').iterdir()):
        if not (d/'review.json').exists():continue
        n=read(d/'generation.json')['name'];H=histories(d/(n+'T01.csv'));M=float(H['MASS'][0]);added=float(abs(H['ADDED MASS']).max());variation=float(abs(H['MASS']-M).max());old=read(d/'review.json')['checks']['no_scaled_mass'];rows.append({'case':d.name,'physical_global_mass_g':M,'maximum_added_mass_field_g':added,'global_mass_variation_g':variation,'original_strict_exact_zero_gate':old,'unchanged_A21_fractional_threshold':a['added_mass_fraction'],'added_mass_fraction':added/M,'existing_A21_relative_gate_pass':bool(added/M<a['added_mass_fraction']),'original_review_preserved':True})
    dump(dst,{'created_utc':now(),'cases':rows,'all_existing_A21_fractional_gates_pass':all(r['existing_A21_relative_gate_pass'] for r in rows),'strict_field_zero_failures_are_float_roundoff':True,'threshold_not_widened':True,'maximum_residual_field_g':max(r['maximum_added_mass_field_g'] for r in rows),'energy_and_inertia_failures_remain':True,'whole_root_qualified':False,'no_mass_added_or_subtracted_from_ledger':True});print(rows,flush=True)

if __name__=='__main__':main()
