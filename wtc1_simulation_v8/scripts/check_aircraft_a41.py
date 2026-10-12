"""Separate free-fixture CHECK capability from the cached whole-model abort."""
from probe_aircraft_a41 import *
import probe_aircraft_a41 as experiment

def declare():
 guard();p=OUT/'model_check_predeclaration.json';assert not p.exists();source=PARENT/'FREE_RREF_FIXED_I/phase1';g=read(source.parent/'generation.json');f=source/(g['name']+'_0000_0001.rst');assert streamsha(f)==next(r['sha256'] for r in read(PARENT/'artifact_manifest.json')['files'] if r['path']==rel(f));dump(p,{'created_utc':now(),'seed':1102066,'before_native_check':True,'source':rel(source),'generation_sha256':streamsha(source.parent/'generation.json'),'state':rel(f),'state_sha256':streamsha(f),'purpose':'Run CHECK on an already qualified simple free fixture, using cached initial preparation. Native failure here prevents assigning the earlier whole CHECK abort to TYPE25 alone.','no_physical_advance_credited':True,'no_old_successful_solver_replay':True,'per_process_cap_s':180,'CPU_threads':1,'GPU':False})

def run():
 guard();dec=read(OUT/'model_check_predeclaration.json');assert dec['before_native_check'];d=OUT/'model_check_free';assert not d.exists();d.mkdir();source=ROOT/dec['state'];shutil.copy2(source,d/source.name);assert streamsha(d/source.name)==dec['state_sha256'];g=read((ROOT/dec['source']).parent/'generation.json');g['case']['platform']='Linux';dump(d/'generation.json',g);n=g['name'];native37.CFG=CFG;(d/(n+'_0001.rad')).write_text(experiment.cards(n,1,'I',.001,.001,'FREE',True),encoding='utf8');native37.native(d,n,1);text=(d/'engine.log').read_text(errors='replace');dump(d/'capability_review.json',{'created_utc':now(),'mode':'CHECK','native_completion':read(d/'completion.json'),'execution':read(d/'engine.log.execution.json'),'checking_report_text_saved':True,'normal_termination':'NORMAL TERMINATION' in text,'physical_seconds_credit':0.,'cause_not_inferred_from_exit_code':True,'original_source_state_unchanged':streamsha(source)==dec['state_sha256']});print({'free_check_exit':read(d/'engine.log.execution.json')['exit_code'],'no_physical_advance_credited':True},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
