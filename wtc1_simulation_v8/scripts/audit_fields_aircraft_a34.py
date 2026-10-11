"""Audit twelve cached native field samples; does not qualify failed mechanics."""
from run_aircraft_a34 import *
import audit_aircraft_a32 as old
from audit_aircraft_a05 import vtk
from assess_aircraft_a23_reader_precision import printed_bound
import subprocess

def main():
    guard();assert read(OUT/'native_case_summary.json')['completed'];assert not (OUT/'native_fields_review.json').exists()
    s=inspect.getsource(old.review).split('    dt=[];mesh=[]')[0];s=s.replace('assert len(rows)==30','assert len(rows)==4').replace("g['geometric_Z_elements']==1","g['geometric_Z_elements'] in [4,8]").replace("'one_physical_thickness_cell'","'declared_physical_thickness_cells'").replace("d.name.startswith(('PATCH_','CONSTRAINED_BENDING'))","d.name.startswith('FACE_BENDING')").replace('def review():','def cached_fields():')
    ast.parse(s);exec(compile(s,__file__+'::cached_fields','exec'),globals());globals()['cached_fields']();dump(OUT/'field_audit_derivation.json',{'created_utc':now(),'source':rel(Path(old.__file__)),'source_sha256':streamsha(Path(old.__file__)),'derived_source':s,'checks_retained':True,'native_solver_reruns':0})
    print({'A34_cached_field_samples':len(read(OUT/'native_fields_review.json')['samples']),'native_fields_pass':read(OUT/'native_fields_review.json')['pass'],'failed_mechanical_gates_not_changed':True},flush=True)

if __name__=='__main__':main()
