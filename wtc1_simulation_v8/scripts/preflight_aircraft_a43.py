"""Read-only dependency preflight after the localized LAW117 incompatibility."""
from probe_aircraft_a42 import ROOT,RUNTIME,read,dump,rel,now,harness,streamsha,build
from pathlib import Path
import argparse,json,shutil,time,urllib.request,concurrent.futures,re
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a43'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a43_predeclaration.json'
PARENT=ROOT/'wtc1_simulation_v8/output/aircraft_a42'

def guard():assert streamsha(CFG)==read(OUT/'declaration_guard.json')['sha256']

def declare():
 assert not OUT.exists() and not CFG.exists();h=harness();assert h['CurrentIteration']=='AIRCRAFT-A42' and read(PARENT/'publication_verification.json')['pass'];OUT.mkdir();dump(OUT/'harness_before.json',h)
 for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
 dump(CFG,{'declared_utc':now(),'iteration':'AIRCRAFT-A43','seed':1102068,'random_draws':0,'purpose':'Read-only preflight for a same-version Starter/Reader. Identify missing interfaces and real compatible dependency delivery before further software modification. No fake symbols, physics patches or binary restart edits.','source_commit':build.PIN,'Linux_engine_sha256':streamsha(build.CAND/'isolated_exec/engine_linux64_gf_ompi'),'source_dependency_metadata':read(build.CAND/'EXTLIB_VERSION.original_pinned.json'),'evidence':rel(PARENT/'material_restart_layout_review.json'),'execution':{'no_native_dynamics':True,'no_compilation':True,'no_installation':True,'read_only_network_metadata':True,'maximum_metadata_requests':24,'per_request_timeout_s':15,'GPU':False},'objective1_complete':False})
 dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':streamsha(CFG),'before_work':True});pins={r['path']:r for name in ['preservation_before.json','artifact_manifest.json'] for r in read(PARENT/name)['files']}
 for name in ['artifact_manifest.json','publication_verification.json']:p=PARENT/name;pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':streamsha(p)}
 dump(OUT/'preservation_before.json',{'created_utc':now(),'files':list(pins.values()),'source_archives_not_rescanned':True});dump(OUT/'previous_goal_turn_audit.json',{'created_utc':now(),'classification':'progress','evidence':'A42 uniquely validated native LAW117 header mismatch; same fresh native state works Windows and fails Linux;92newfiles and31481oldfiles integrity verified.','same_blocker_without_new_evidence':False});print({'A43_declared':True},flush=True)

def fetch(url):
 t=time.perf_counter()
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'WTC1-reproducible-preflight','Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})
  with urllib.request.urlopen(req,timeout=15) as r:b=r.read(12000000);data=json.loads(b);return {'url':url,'status':r.status,'data':data,'wall_s':time.perf_counter()-t}
 except Exception as e:return {'url':url,'error':str(e),'wall_s':time.perf_counter()-t}

def search():
 guard();p=OUT/'external_dependency_repository_search.json';assert not p.exists();r=fetch('https://api.github.com/search/repositories?q=OpenRadioss_extlib&per_page=20');dump(p,{'created_utc':now(),'response':r});print({'metadata_search_status':r.get('status'),'repository_names':[q['full_name'] for q in r.get('data',{}).get('items',[])]},flush=True)

def metadata():
 guard();repos=read(OUT/'external_dependency_repository_search.json')['response'].get('data',{}).get('items',[]);requests=[('https://raw.githubusercontent.com/'+r['full_name']+'/'+r['default_branch']+'/EXTLIB_VERSION.json') for r in repos];assert len(requests)<=20;p=OUT/'external_dependency_versions.json';assert not p.exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:rows=list(ex.map(fetch,requests))
 dump(p,{'created_utc':now(),'responses':rows,'no_software_download_install_or_build':True});print([{'url':r['url'],'version':r.get('data',{}).get('version'),'error':r.get('error')} for r in rows],flush=True)

def preserve():
 from finalize_aircraft_a22 import verify_files
 guard();p=OUT/'preservation_verification.json';assert not p.exists();t=time.perf_counter();rows=read(OUT/'preservation_before.json')['files'];n=verify_files(rows);dump(p,{'created_utc':now(),'pass':True,'files':n,'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'source_archives_not_rescanned':True,'old_artifacts_unchanged':True});print({'preserved_old_files':n},flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','search','metadata','preserve']);globals()[p.parse_args().action]()
