"""Two remaining authorized A62 controls: fully free elastic cohesive oscillator."""
from build_aircraft_a54_graph import ROOT,read,dump,sha,now,rel,harness
from pathlib import Path
import probe_aircraft_a54 as launcher
from material_aircraft_a60 import path_values
import numpy as np,shutil,subprocess,time,ast,json,argparse,re

OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a63'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a63_predeclaration.json'
CONTROL=CFG
RUNTIME=launcher.RUNTIME

def engine():
    c=read(CFG);assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256'];assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    built=read(ROOT/'wtc1_simulation_v8/output/aircraft_a62/build_finished.json');p=ROOT/built['candidate_directory'];b=p/'isolated_exec/engine_linux64_gf_ompi';assert sha(b)==c['binary_sha256'];return p,b

def declare():
    assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A62'
    prior=ROOT/'wtc1_simulation_v8/output/aircraft_a62';a=read(prior/'scientific_assessment.json');assert a['authorized_native_controls_remaining']==2 and len(list(prior.rglob('engine.execution.json')))==10
    p=read(prior/'native_controls_predeclaration.json')['cohesive'];accept=read(ROOT/'wtc1_simulation_v8/data/aircraft_a45_contact_predeclaration.json')['acceptance'];cases=[]
    for identifier,dt in [('FREE_ELASTIC',.001),('FREE_ELASTIC_HALF',.0005)]:
        cases.append({'id':identifier,'stage':'free','L_mm':10,'dt_cap_ms':dt,'imposed_axes':[],'knot_times_ms':[0,1],'knot_gaps_mm':[[0,0,0],[0,0,0]],'end_ms':1,'initial_free_velocity_mm_ms':[0,1,0],'all_top_translations_free':True,'no_imposed_displacements_or_velocities_during_run':True})
    OUT.mkdir();dump(OUT/'harness_before.json',h)
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    c={'created_utc':now(),'iteration':'AIRCRAFT-A63','seed':1102088,'random_draws':0,'binary_sha256':a['binary_sha256'],'cohesive':p,'cases':cases,'acceptance':accept,
      'purpose':'Separate unconstrained Newmark dynamics from prescribed-axis counter conventions. Verify exact linear oscillator, all physical nodal momentum/energy and support-only impulse on the already authorized Engine.',
      'source_protocol':'Pinned Newmark gamma.5 beta.25: endpointV[n]=2*published secant[n]-endpointV[n-1]. All moving DOFs here are FREE; no constrained-motion velocity reconstruction assumed.',
      'analytical_reference':{'top_mass_g':4,'area_mm2':100,'initial_speed_mm_ms':1,'initial_energy_J':.002,'surface_stiffness_N_mm':p['ET_N_mm3']*100,'omega_per_ms':(100*p['ET_N_mm3']/4)**.5,'Newmark_phase_step':'2*atan(omega*dt/2)','exact_elastic_gap':'v0/omega*sin(n*phase_step)','exact_elastic_velocity':'v0*cos(n*phase_step)','parameter_fitting':False},
      'extra_analytical_displacement_tolerance_mm':accept['free_displacement_mm'],'extra_analytical_velocity_tolerance_mm_ms':accept['free_velocity_mm_ms'],
      'authorized_A61_native_maximum_across_A62_A63':12,'A62_native_already_executed':10,'maximum_new_native_runs':2,'each_cap_s':180,'CPU':1,'GPU':False,'new_software_changes_or_compilation':False,
      'whole_mass_material_budgets_changed':False,'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'new_whole_credit_s':0}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_native_execution':True})
    pins={r['path']:r for r in read(prior/'preservation_before_metadata.json')['files']}
    for r in read(prior/'artifact_manifest.json')['files']:pins[r['path']]=r
    for q in [prior/'artifact_manifest.json',prior/'publication_verification.json']:pins[rel(q)]={'path':rel(q),'bytes':q.stat().st_size,'sha256':sha(q)}
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':[{**r,'mtime_ns_before':(ROOT/r['path']).stat().st_mtime_ns} for r in pins.values()]})
    print(json.dumps({'A63_declared':True,'remaining_controls':2,'total_authorized_limit':12,'no_imposed_trajectory':True}),flush=True)

# Reuse only the already tested owned input generator; no sealed file is changed.
source=(ROOT/'wtc1_simulation_v8/scripts/probe_aircraft_a62_surface.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='generate');s=ast.get_source_segment(source,node).replace("name='A62_'","name='A63_'")
exec(compile(s,__file__,'exec'))

def run():
    engine();results=[];prior=ROOT/'wtc1_simulation_v8/output/aircraft_a62'
    for case in read(CFG)['cases']:
        ordinal=len(list(prior.rglob('engine.execution.json')))+len(list(OUT.rglob('engine.execution.json')))+1;assert ordinal<=12
        d,name=generate(case);dump(d/'native_launch_declaration.json',{'created_utc':now(),'ordinal_across_A62_A63':ordinal,'maximum_authorized':12,'cap_s':180,'CPU':1,'GPU':False,'binary_sha256':sha(engine()[1])})
        launcher.engine=engine;result=launcher.run_native(d,name)
        if result['parent_exit_code']==0 and result['normal_termination']:
            start=time.perf_counter();r=subprocess.run([str(RUNTIME/'th_to_csv_win64.exe'),name+'T01'],cwd=d,capture_output=True,timeout=60);(d/'converter.log').write_bytes(r.stdout+r.stderr);dump(d/'converter.execution.json',{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.perf_counter()-start,'cap_s':60});result['converter_exit_code']=r.returncode
        results.append({'case':case['id'],**result});print(json.dumps(results[-1]),flush=True)
    dump(OUT/'free_execution_review.json',{'created_utc':now(),'cases':results,'all_normal':all(r['parent_exit_code']==0 and r['normal_termination'] for r in results),'no_physical_pass_inferred_from_NORMAL':True,'authorized_total_consumed':12})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
