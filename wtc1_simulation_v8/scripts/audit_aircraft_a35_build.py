"""Keep build availability, source preservation and physical qualification separate."""
from build_aircraft_a35_mumps import *
PREV=ROOT/'wtc1_simulation_v8/output/aircraft_a34'
def preserve():
 guard();dest=OUT/'preservation_verification.json';assert not dest.exists()
 pins={r['path']:r for f in ['preservation_before.json','artifact_manifest.json'] for r in read(PREV/f)['files']}
 for p in [PREV/'artifact_manifest.json',PREV/'publication_verification.json',ROOT/'outputs/github_publication/updates_2026-10-11_aircraft_a32_a33/final_remote_verification.json']:
  pins[rel(p)]={'path':rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
 rows=list(pins.values());dump(OUT/'preservation_before.json',{'created_utc':now(),'files':rows,'archives_rescanned':False});t=time.perf_counter()
 for i,r in enumerate(rows):
  p=ROOT/r['path'];assert p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['path']
  if (i+1)%3000==0:print({'old_files':i+1,'of':len(rows)},flush=True)
 dump(dest,{'created_utc':now(),'pass':True,'files':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows),'wall_seconds':time.perf_counter()-t,'sources_not_rescanned':True});print({'A35_old_preserved':len(rows)},flush=True)
def build_review():
 guard();finished=read(OUT/'build_finished.json');assert finished.get('engine_built') or finished['build_commands_completed'];dest=OUT/'candidate_binary_review.json';assert not dest.exists();bindir=ROOT/finished['binary_directory'];binaries=[bindir/n for n in ['engine_linux64_gf_ompi','libopen_reader_linux64.so']];assert all(p.is_file() for p in binaries)
 rows=[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in binaries];t=time.perf_counter();metadata=[]
 for p in binaries:
  r=subprocess.run(['wsl.exe','-d','Ubuntu','--','env','LD_LIBRARY_PATH='+linux(bindir),'ldd',linux(p)],capture_output=True,text=True,encoding='utf8',timeout=30);assert r.returncode==0;metadata.append({'path':rel(p),'exit_code':r.returncode,'ldd':r.stdout})
 tree=read(OUT/'source_git_verification.json');changes=[]
 for e in tree['files']:
  p=CAND/'source'/e['path'];b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  if h!=e['archive_git_blob_sha1']:changes.append(e['path'])
 assert changes==['EXTLIB_VERSION.json'],changes
 current=CAND.parent/'v20260728-win64/engine_win64.exe';original=read(CFG)['authorization']['proposal'];proposal=read(ROOT/original);assert sha(current)==proposal['current_binary_preserved']['sha256']
 ldd='\n'.join(m['ldd'] for m in metadata);checks={'all_binaries_present':True,'MUMPS_dynamically_linked':'libdmumps' in ldd,'MPI_dynamically_linked':'libmpi' in ldd,'no_missing_libraries':'not found' not in ldd,'tracked_physics_source_unchanged':read(OUT/'source_w2_verification.json')['tracked_physics_source_unchanged'],'Windows_solver_unchanged':True,'build_within_one_hour':read(OUT/'build_finished.json')['seconds']<=3600}
 dump(dest,{'created_utc':now(),'checks':checks,'engine_candidate_availability_pass':all(checks.values()),'full_build_availability_pass':bool(all(checks.values()) and finished['build_commands_completed']),'Linux_Starter_built':bool(finished.get('Linux_starter_built',False)),'files':rows,'dynamic_libraries':metadata,'tracked_source_changes':changes,'actual_build':finished,'earlier_dependency_override':read(OUT/'build_metadata_override.json'),'native_physical_validation':False,'whole_impact_qualified':False,'objective1_complete':False,'seconds':time.perf_counter()-t});(OUT/'harness_after_software.txt').write_text(harness(),encoding='utf8');print({'A35_candidate_binary':checks,'full_build_availability_pass':False},flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['preserve','build_review']);globals()[p.parse_args().action]()
