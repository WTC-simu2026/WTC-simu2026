"""Retain the strict Starter failure; permit only the declared diagnostic overlaps."""
import re
import numpy as np
from run_aircraft_a18 import *
from audit_aircraft_a02 import numbers_after

guard();d=OUT/'r0'/CASE;g=read(d/'generation.json');n=g['name'];assert not (d/'engine.log').exists() and not (d/'initial_overlap_diagnostic_gate.json').exists()
s=(d/'starter.log').read_text(errors='replace');listing=(d/(n+'_0000.out')).read_text(errors='replace');parent=(SOURCE/(read(SOURCE/'generation.json')['name']+'_0000.out')).read_text(errors='replace')
ids=re.findall(r'WARNING ID\s*:\s*(\d+)',s);assert sorted(ids)==['1166','343'];assert read(d/'starter_gate.json')=={'exit_ok':True,'warnings':2,'errors':0,'pass':False}
warning_sections=re.findall(r'^WARNING ID\s*:\s*\d+.*?(?=^WARNING ID|^ INTERFACE NUMBER)',listing,re.S|re.M)
assert len(warning_sections)==2 and all('-- INTERFACE ID: 2' in b for b in warning_sections)
assert all('576 INITIAL PENETRATIONS' in b for b in warning_sections)
m=read(d/'mesh.json');x=np.array(m['nodes_mm']);rad=m['radome_node_ids'];assert sum(x[i-1,0]!=2000 for i in rad)==576
mc=[np.array(numbers_after(q,'TOTAL MASS AND MASS CENTER',4)) for q in [parent,listing]];I=[np.array(numbers_after(q,'TOTAL INERTIA',6)) for q in [parent,listing]]
checks={'zero_errors':True,'only_expected_self_contact_warning_ids':True,'only_interface2_initial_overlap':True,'overlap_node_count_equals_split_nonroot_corners':True,'native_mass_relative':bool(abs(mc[1][0]-mc[0][0])/mc[0][0]<1e-6),'native_CG_error_mm':bool(np.max(abs(mc[1][1:]-mc[0][1:]))<.001),'native_inertia_relative':bool(np.max(abs(I[1]-I[0]))/np.max(abs(I[0]))<1e-6)}
dump(d/'initial_overlap_diagnostic_gate.json',{'created_utc':now(),'configuration_sha256':streamsha(CFG),'starter_zero_warning_gate_retained_failed':True,'checks':checks,'warning_ids':ids,'interface_id':2,'initial_overlap_nodes':576,'native_mass_CG_parent':mc[0].tolist(),'native_mass_CG_new':mc[1].tolist(),'native_inertia_parent':I[0].tolist(),'native_inertia_new':I[1].tolist(),'exploratory_engine_allowed':all(checks.values()),'physical_contact_gate_pass':False,'reason':'Initial coincidence explicitly declared before Starter, native Inacti1000 ignores pairs until exit/reentry. No parameter or geometry correction. This bounded diagnostic tests actual initial work, mass and kinematics; warnings remain failures for a zero-warning qualified transfer.','deck_unchanged_since_Starter':True,'before_any_A18_Engine':True})
assert all(checks.values());print({'diagnostic_allowed':True,'initial_overlap_nodes':576,'mass_difference_kg':(mc[1][0]-mc[0][0])*.001,'CG_error_mm':float(np.max(abs(mc[1][1:]-mc[0][1:]))),'inertia_relative_change':float(np.max(abs(I[1]-I[0]))/np.max(abs(I[0])))},flush=True)
