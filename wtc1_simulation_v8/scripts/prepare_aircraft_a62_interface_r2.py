"""Use the existing native my_real macro in the compiler-only explicit interface."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel
import ast,json

def main():
    src=ROOT/'wtc1_simulation_v8/scripts/resume_aircraft_a62_interface.py';dest=ROOT/'wtc1_simulation_v8/scripts/resume_aircraft_a62_interface_r2.py';assert not dest.exists()
    s=src.read_text(encoding='utf8')
    replacements=[('IMPORT :: ELBUF_STRUCT_,NIXS,NPROPMI,WP','IMPORT :: ELBUF_STRUCT_,NIXS,NPROPMI'),('REAL(KIND=WP) X(*),BUFMAT(*),K_DIAG(*),K_LT(*)','my_real X(*),BUFMAT(*),K_DIAG(*),K_LT(*)'),('build_attempt_R1_interface','build_attempt_R2_interface_precision'),("'R1_interface'","'R2_interface_precision'"),('s8zke3_R1_interface.proposed.F','s8zke3_R2_interface.proposed.F'),('type43_surface_interface_R1.patch','type43_surface_interface_R2_precision.patch'),('exact_interface_declaration_application.json','exact_interface_declaration_R2_application.json')]
    for old,new in replacements:assert old in s,old;s=s.replace(old,new)
    s=s.replace("patch=CAND/'type43_surface_interface_R2_precision.patch';target=cfg['surface_patch']['target'];patch.write_text(''.join(difflib.unified_diff(s.splitlines(True),repaired.splitlines(True)","previous=CAND/'s8zke3_R1_interface.proposed.F';assert previous.exists()\n    patch=CAND/'type43_surface_interface_R2_precision.patch';target=cfg['surface_patch']['target'];patch.write_text(''.join(difflib.unified_diff(previous.read_text(encoding='utf8').splitlines(True),repaired.splitlines(True)")
    old='= {sha(original)}\\ncd {q(mount)}/source';new='= {sha(previous)}\\ncd {q(mount)}/source';assert old in s;s=s.replace(old,new)
    s=s.replace('GNU explicit interface required for TARGET dummy; R0 exact approved source applied and compile failure retained.','R1 used a WP kind absent from its host scope. Declare the same argument types using the native my_real macro; R0/R1 failures remain preserved. No executable equation changed.')
    ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n')
    dump(ROOT/'wtc1_simulation_v8/output/aircraft_a62/interface_r2_derivation.json',{'created_utc':now(),'source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest),'correction':'explicit interface precision uses existing my_real macro, no WP assumed','R0_R1_failures_preserved':True,'same_original_hour_cap_and_sixth_candidate':True,'mechanical_equations_unchanged':True})
    print(json.dumps({'R2_interface_precision_ready':True}),flush=True)

if __name__=='__main__':main()
