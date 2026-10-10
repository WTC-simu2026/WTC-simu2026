"""Use geometric material moments, preserving the failed parent-moment comparison."""
from run_aircraft_a20_whole import *

def main():
    whole_guard(); p=D/'geometric_moment_addendum.json';assert not p.exists()
    oldgate=read(D/'native_insertion_gate.json');parts=read(D/'initial_diagnostic'/'part_moments.json');geom=read(D/'initial_diagnostic'/'discretization_moments.json')
    old,new=parts['old'],parts['new'];m=read(D/'mesh.json');rows=geom['rows']
    protocol={'declared_utc':now(),'before_whole_impact_engine':not (D/'engine.log').exists(),
        'reason':'The old radome native part centroid is 1053.83601mm; the same physical triangular material area integrates to1048.26570561mm. The replacement agrees with the geometric integral. Comparing the replacement to the old inconsistent native centroid is not a preservation test of the physical geometry.',
        'reference':'Unchanged non-radome native parts, plus analytical surface area times uniform original areal budget2.214kg/m2, symmetrically extruded layers.',
        'unchanged_thresholds':{'mass_relative':1e-6,'CG_mm':.001,'inertia_relative':1e-6},
        'old_failed_gate_sha256':streamsha(D/'native_insertion_gate.json'),'no_change_to_mesh_material_density_or_ADMAS':True,
        'native_nodal_mass_is_separate':'RBE2/RBE3 constraint-reduced animation masses are not assumed physical input masses. Initial animation has a1.144154kg sum increase and must be independently reconciled in the whole diagnostic; the discrepancy is retained.'}
    if not (D/'geometric_moment_protocol.json').exists():dump(D/'geometric_moment_protocol.json',protocol)
    M0=np.array(oldgate['mass_CG_old']);M1=np.array(oldgate['mass_CG_new']);rm=float(geom['analytic_mass_g']);rc=np.array(geom['analytic_centroid_mm'])
    oldrm=old['21']['mass_g'];oldrc=np.array(old['21']['centroid_mm'])
    predicted_M=M0[0]-oldrm+rm;predicted_cg=(M0[0]*M0[1:]-oldrm*oldrc+rm*rc)/predicted_M
    ids=m['radome_core_part_ids']+m['radome_skin_part_ids'];newrm=sum(new[str(i)]['mass_g'] for i in ids)
    newrc=sum((new[str(i)]['mass_g']*np.array(new[str(i)]['centroid_mm']) for i in ids),np.zeros(3))/newrm
    checks={'nonradome_native_parts_identical':all(new[i]==v for i,v in old.items() if i!='21'),
        'same_declared_material_budget':abs(newrm-rm)/rm<1e-6,'native_radome_centroid_matches_geometry':bool(np.max(abs(newrc-rc))<.001),
        'total_mass_matches_geometric_reference':abs(M1[0]-predicted_M)/predicted_M<1e-6,
        'CG_matches_geometric_reference':bool(np.max(abs(M1[1:]-predicted_cg))<.001),
        'native_inertia_preserved':oldgate['checks']['inertia_preserved'],'no_new_undeclared_solver_warning':oldgate['checks']['only_declared_initial_self_warnings'],
        'zero_starter_errors':oldgate['checks']['zero_errors'],'native_core_and_skin_controls_pass':oldgate['checks']['scoped_coupling_controls_pass']}
    checks={k:bool(v) for k,v in checks.items()}
    r={'created_utc':now(),'checks':checks,'geometric_radome_mass_g':rm,'native_new_radome_mass_g':newrm,
        'geometric_radome_centroid_mm':rc.tolist(),'old_native_radome_centroid_mm':oldrc.tolist(),'new_native_radome_centroid_mm':newrc.tolist(),
        'predicted_total_mass_g':float(predicted_M),'predicted_total_CG_mm':predicted_cg.tolist(),'actual_total_CG_mm':M1[1:].tolist(),
        'CG_prediction_error_mm':(M1[1:]-predicted_cg).tolist(),'original_parent_CG_gate_failed_and_retained':True,
        'original_whole_declaration_all_checks_pass':False,'geometric_reference_addendum_pass':all(checks.values()),
        'exploratory_20ms_engine_allowed':all(checks.values()),'physical_impact_qualified':False,
        'native_animation_mass_discrepancy_unresolved':True,'seconds_extension_allowed':False,
        'cause_of_old_native_radome_moment_error_identified':False,'old_solver_reruns':0,'no_density_or_geometry_fit':True}
    dump(p,r);print(r,flush=True);assert all(checks.values())

if __name__=='__main__':main()
