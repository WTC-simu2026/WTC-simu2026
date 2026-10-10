"""A19 staged cached fragment-energy diagnosis and declared corrective experiments."""
import argparse,json,re,shutil,urllib.request
from pathlib import Path
from run_aircraft_a18 import ROOT,RUNTIME,read,dump,rel,now,harness,execute,env,streamsha,ff,ii,CASE
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a19'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a19_predeclaration.json'
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a18'
SOURCE=PREV/'r0'/CASE

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def declare():
    assert not OUT.exists() and not CFG.exists();v=harness();assert v['Status']=='PASS' and v['CurrentIteration']=='AIRCRAFT-A18';OUT.mkdir();dump(OUT/'harness_before.json',v)
    for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+Path(n).name))
    pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
    for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json']:pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
    dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'archives_rescanned':False})
    c={'iteration':'AIRCRAFT-A19','declared_utc':now(),'seed':1102044,'random_draws':0,'user_objective_physical_duration_s':10,'objective1_complete':False,
       'scope':'Diagnose native negative radome IE from saved A18 states, then declare a targeted correction before new native experiments. Not historical fitting.',
       'source':rel(SOURCE),'cached_analysis':{'all_native_frames':True,'focus_part_id':21,'reader':'FASTMAGI10 shell prefix; scalar specific energy and element mass, nodal positions/velocities, shell stresses and strains',
         'validation_frames':[0,65,-1],'converter_tolerance_relative':5e-6,'converter_tolerance_absolute':1e-6,
         'geometry':'initial/current metric singular stretches and area, no false inversion label from an initial-normal dot product under rotation',
         'rotation':'recover angular velocity from actual RBE2 offset nodal velocities by least squares; rank deficiencies reported, not filled',
         'energy':'element_specific_energy * initial element mass; compare independently to native part IE and keep differences',
         'selection':'locate most negative energy facets only for defect diagnosis, not for fitting a physical result or selecting a movie'},
       'execution_policy':{'no_old_solver_reruns':True,'new_solver_declaration_required':True,'conditional_target':'a new fresh coupled run20ms or longer only after negative-energy mechanism is addressed in explicitly declared mechanics',
         'do_not_compensate_by_mass_G_or_RKE':True,'hours_long_cost_announced_before_launch':True},
       'sources':['https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type51_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/prop_type19_ply_starter_r.htm','https://help.altair.com/hwsolvers/rad/topics/solvers/rad/tsai_wu_formulation_starter_r.htm'],
       'physical_impact_qualified':False,'NIST_outcomes_used_as_target':False,'sources_read_only':True}
    dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_any_A19_analysis_or_solver':True});sd=OUT/'sources';sd.mkdir();src=[]
    for i,url in enumerate(c['sources']):
        p=sd/f'primary_{i}.html';p.write_bytes(urllib.request.urlopen(url,timeout=60).read());src.append({'path':rel(p),'url':url,'sha256':streamsha(p),'bytes':p.stat().st_size,'redistribution':'exclude_third_party'})
    for p in [SOURCE/'mesh.json',SOURCE/'generation.json',SOURCE/'review.json',SOURCE/'verified_states_SI.npz',PREV/'negative_energy_diagnostic.json']:
        src.append({'path':rel(p),'sha256':streamsha(p),'bytes':p.stat().st_size})
    dump(OUT/'source_manifest.json',{'created_utc':now(),'files':src,'old_solver_reruns':0,'archives_rescanned':False});print({'declared':'AIRCRAFT-A19','old_files_pinned':len(pins)},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare']);globals()[p.parse_args().action]()
