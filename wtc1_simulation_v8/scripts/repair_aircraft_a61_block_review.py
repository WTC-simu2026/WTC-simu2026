"""Preserve R0 bit-equality failure; reuse predeclared matrix tolerance in R1."""
from prepare_aircraft_a61_surface_iteration import ROOT,OUT,CFG,guard,read,dump,sha,now,rel
import shutil,subprocess,sys,time,json,ast

def main():
    c=guard();r0=read(OUT/'symmetric_surface_iteration_review.json')
    assert [r['name'] for r in r0['checks'] if not r['pass']]==['nonuniform_triangular_block_reconstruction']
    saved=OUT/'preserved_R0';saved.mkdir()
    src=ROOT/'wtc1_simulation_v8/scripts/surface_iteration_aircraft_a61.py'
    for p in [src,OUT/'prototype.log',OUT/'prototype_execution.json',OUT/'symmetric_surface_iteration_review.json']:shutil.copy2(p,saved/p.name)
    dest=src.with_name('surface_iteration_aircraft_a61_r1.py');assert not dest.exists()
    s=src.read_text(encoding='utf8')
    old='np.array_equal(reconstructed,K)';new="np.max(abs(reconstructed-K))<=lim['matrix_relative_tolerance']*np.max(abs(K))"
    assert s.count(old)==1;s=s.replace(old,new).replace("OUT/'symmetric_surface_iteration_review.json'","OUT/'symmetric_surface_iteration_review_R1.json'")
    ast.parse(s);dest.write_text(s,encoding='utf8',newline='\n')
    dump(OUT/'block_tolerance_correction_predeclaration.json',{'created_utc':now(),'R0_failed_gate_preserved':True,'reason':'Bitwise equality exceeded by rounding under nonuniform quadrature. Use the already predeclared matrix relative tolerance1e-12 instead; no numerical/mechanical threshold changed.','source':rel(src),'source_sha256':sha(src),'derived':rel(dest),'derived_sha256':sha(dest),'changed_check':old,'new_check':new,'new_native_solver_runs':0})
    start=time.perf_counter();r=subprocess.run([sys.executable,str(dest)],capture_output=True,timeout=c['prototype']['cap_s']);(OUT/'prototype_R1.log').write_bytes(r.stdout+r.stderr)
    dump(OUT/'prototype_R1_execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':c['prototype']['cap_s'],'CPU':1,'GPU':False,'script_sha256':sha(dest)})
    print(r.stdout.decode('utf8',errors='replace'),flush=True);assert r.returncode==0

if __name__=='__main__':main()
