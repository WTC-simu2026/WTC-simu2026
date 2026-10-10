"""Format-only new revision; reuse four completed w0 controls and preserve rejected INIVEL input."""
from run_aircraft_a22 import ROOT,OUT,CFG,read,dump,now,streamsha,guard
from pathlib import Path
import importlib.util,ast

def main():
    guard();decl=OUT/'w1_declaration.json';assert not decl.exists()
    src=Path(__file__).with_name('run_aircraft_a22.py');dst=src.with_name('run_aircraft_a22_w1.py');assert not dst.exists();s=src.read_text(encoding='utf-8')
    old="ff(*v)+ii(ni,0)]";new="ff(*v)+ii(ni,0),ff(0)+ii(0)]";assert s.count(old)==1;s=s.replace(old,new)
    old="ff(*omega)+ii(1000,0)]";new="ff(*omega)+ii(1000,0),ff(0)+ii(0)]";assert s.count(old)==1;s=s.replace(old,new)
    s=s.replace("d=OUT/'w0'/f'{cid}_N{nseg}'", "d=OUT/'w1'/f'{cid}_N{nseg}'")
    ast.parse(s);dst.write_text(s,encoding='utf-8',newline='\n')
    dump(decl,{'created_utc':now(),'revision':'w1','configuration_sha256':streamsha(CFG),'source_script_sha256':streamsha(src),'new_script_sha256':streamsha(dst),'before_all_new_w1_executions':True,'scope':'Add required second INIVEL record Tstart0,sensor0, documented current2026 syntax and identical to inherited whole-aircraft input. Original free-translation Starter warning100217 retained; no Engine was launched for that rejected input. No geometry, initial velocity, mass, material, threshold or other scientific parameter change. Reuse four completed w0 prescribed controls without rerun.','source':'https://help.altair.com/hwsolvers/rad/topics/solvers/rad/inivel_starter_r.htm'})
    spec=importlib.util.spec_from_file_location('a22_w1',dst);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);rows=[]
    for nseg in [4,8]:
        for cid in read(CFG)['cases']:
            cached=OUT/'w0'/f'{cid}_N{nseg}'/'review.json'
            if cached.exists():r=read(cached);revision='w0'
            else:module.run_one(nseg,cid);r=read(OUT/'w1'/f'{cid}_N{nseg}'/'review.json');revision='w1'
            r={**r,'revision':revision};rows.append(r)
    dump(OUT/'connector_review.json',{'created_utc':now(),'cases':rows,'all_pass':all(r['pass'] for r in rows),'finite_connector_qualified_for_whole':False,'implementation_all_pass':all(r['pass'] for r in rows),'strength_or_fracture_qualified':False,'whole_impact_qualified':False,'objective1_complete':False,'old_solver_reruns':0,'reused_completed_w0_controls':4,'w0_free_Starter_failure_retained':True,'new_native_Engine_executions':14})

if __name__=='__main__':main()
