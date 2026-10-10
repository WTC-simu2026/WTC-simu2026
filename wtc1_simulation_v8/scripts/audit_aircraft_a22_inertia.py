"""Cached native channel comparison; infer observed inertia without adding any energy to the ledger."""
from run_aircraft_a22 import OUT,read,dump,now,histories,guard
import numpy as np

def main():
    guard();p=OUT/'native_inertia_audit.json';assert not p.exists();rows=[]
    for revision in ['w0','w1']:
        for d in sorted((OUT/revision).glob('ROTATION_*')):
            if not (d/'review.json').exists():continue
            g=read(d/'generation.json');r=read(d/'review.json');H=histories(d/(g['name']+'T01.csv'));T=H['time'];keys=[k for k in H if k.startswith('NATIVE_CONNECTOR_NODES')];m=np.asarray(g['physical_lumped_mass_g']);v=np.column_stack([H[k] for k in keys]).reshape(len(T),len(m),9);axis='XYZ'.index(g['case'][-1]);w=v[:,:,6+axis].mean(axis=1);kinetic_from_known_masses=.5*np.sum(m[None,:,None]*v[:,:,3:6]**2,axis=(1,2))*.001
            mask=(T>.1)&(T<.9)&(abs(w)>1);I_observed=2*H['ROTATION ENERGY'][mask]/w[mask]**2;physical_cross=np.asarray(g['physical_cross_section_inertia_g_mm2'])[axis,axis]
            expected_peak=r['peak_expected_prescribed_KE_J'];delta=r['peak_native_KE_J']-expected_peak
            rows.append({'revision':revision,'case':g['case'],'nseg':g['nseg'],'maximum_native_translational_KE_minus_known_nodal_KE_J':float(abs(H['KINETIC ENERGY']*.001-kinetic_from_known_masses).max()),'observed_native_rotational_inertia_median_g_mm2':float(np.median(I_observed)),'observed_native_rotational_inertia_range_g_mm2':[float(I_observed.min()),float(I_observed.max())],'independent_physical_section_inertia_g_mm2':float(physical_cross),'peak_total_KE_difference_J':delta,'peak_total_KE_relative_difference':delta/expected_peak,'original_review_pass':r['pass'],'native_RKE_not_reconstructed_or_added':True})
    dump(p,{'created_utc':now(),'cases':rows,'old_solver_reruns':0,'all_native_energy_balance_checks_pass':all(read(OUT/r['revision']/f"{r['case']}_N{r['nseg']}"/'review.json')['checks']['native_energy_balance'] for r in rows),'observed_inertia_is_a_diagnostic_not_a_corrected_native_field':True,'whole_A21_energy_cause_proven':False,'original_failed_gates_unchanged':True})
    print({'native_inertia_cases_audited':len(rows),'observed_inertia':[{'axis':r['case'][-1],'nseg':r['nseg'],'observed':r['observed_native_rotational_inertia_median_g_mm2'],'physical':r['independent_physical_section_inertia_g_mm2']} for r in rows]},flush=True)

if __name__=='__main__':main()
