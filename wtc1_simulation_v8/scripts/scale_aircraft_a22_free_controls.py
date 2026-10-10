"""New declared amplitude controls, making all three free rotations observable above the fixed absolute floor."""
from run_aircraft_a22 import ROOT,OUT,CFG,read,dump,now,streamsha,guard
from pathlib import Path
import importlib.util,ast

def main():
    guard();summary=read(OUT/'connector_review.json');assert len(summary['cases'])==18
    conf=ROOT/'wtc1_simulation_v8/data/aircraft_a22_free_scale_declaration.json';assert not conf.exists();c=read(CFG);c.update(declared_utc=now(),revision='w2',cases=['FREE_ROTATION_X','FREE_ROTATION_Y','FREE_ROTATION_Z']);c['motion']['free_angular_rad_ms']=10
    c['purpose']='Amplitude100x, energy10000x free rotations on N8, keeping geometry/mass/material/thresholds unchanged. The initial0.1rad/ms Y reference is1.25e-8J, below absolute1e-7J; that pass alone does not qualify inertia. No mass/density fitting.'
    c['parent_configuration_sha256']=streamsha(CFG);c['execution']['only_segments_per_spoke']=8;dump(conf,c)
    src=Path(__file__).with_name('run_aircraft_a22_w1.py');dst=src.with_name('run_aircraft_a22_w2.py');assert not dst.exists();s=src.read_text(encoding='utf-8');s=s.replace("data/aircraft_a22_predeclaration.json", "data/aircraft_a22_free_scale_declaration.json").replace("OUT/'declaration_guard.json'", "OUT/'w2_guard.json'").replace("d=OUT/'w1'/f'{cid}_N{nseg}'", "d=OUT/'w2'/f'{cid}_N{nseg}'")
    assert s.count("*.1 if cid.startswith('FREE_ROTATION_')")==2;s=s.replace("*.1 if cid.startswith('FREE_ROTATION_')", "*10 if cid.startswith('FREE_ROTATION_')")
    ast.parse(s);dst.write_text(s,encoding='utf-8',newline='\n');dump(OUT/'w2_guard.json',{'created_utc':now(),'sha256':streamsha(conf),'new_script_sha256':streamsha(dst),'before_all_w2_solver':True,'parent_control_summary_sha256':streamsha(OUT/'connector_review.json')});dump(OUT/'connector_review_before_w2.json',summary)
    spec=importlib.util.spec_from_file_location('a22_w2',dst);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);rows=[]
    for cid in c['cases']:
        module.run_one(8,cid);r=read(OUT/'w2'/f'{cid}_N8'/'review.json');rows.append({**r,'revision':'w2','free_angular_rad_ms':10})
    merged=summary['cases']+rows;dump(OUT/'connector_review.json',{**summary,'created_utc':now(),'cases':merged,'all_pass':all(r['pass'] for r in merged),'implementation_all_pass':all(r['pass'] for r in merged),'finite_connector_qualified_for_whole':False,'new_native_Engine_executions':21,'extra_observable_free_controls':3,'weak_original_free_rotation_floor_retained':True})
    print({'all_native_controls':len(merged),'high_energy_free_controls':3,'all_pass':all(r['pass'] for r in merged)},flush=True)

if __name__=='__main__':main()
