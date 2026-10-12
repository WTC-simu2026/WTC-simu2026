"""Prepared one-hour isolated Engine build. Requires explicit authorization record."""
from preflight_aircraft_a43 import ROOT,read,dump,rel,now,streamsha,build
from pathlib import Path
import time,subprocess,shutil,urllib.request,hashlib,shlex
PIN='3d75ff13d1946f6d28a43920eac4fa2aae41b27a'
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a44'
CAND=ROOT/'wtc1_simulation_v8/openradioss_runtime/a44_legacy_mumps_candidate'
PREFLIGHT=ROOT/'wtc1_simulation_v8/output/aircraft_a43'
DEPS=build.CAND/'extlib_v67.tar.gz'

def run():
 authorization=read(OUT/'software_authorization.json');assert authorization['explicit_human_authorization'] and authorization['source_pin']==PIN and authorization['cap_s']==3600;assert read(ROOT/'harness/state.json')['current_iteration']=='AIRCRAFT-A43';assert read(PREFLIGHT/'publication_verification.json')['pass'];assert not CAND.exists();assert CAND.resolve().is_relative_to((ROOT/'wtc1_simulation_v8/openradioss_runtime').resolve());CAND.mkdir();logs=OUT/'build_logs';logs.mkdir();scripts=OUT/'build_scripts';scripts.mkdir();started=time.time();deadline=started+3600;dump(OUT/'build_clock.json',{'started_epoch':started,'deadline_epoch':deadline,'limit_s':3600});dep_review=read(ROOT/'wtc1_simulation_v8/output/aircraft_a35/extlib_v67_archive.json');assert streamsha(DEPS)==dep_review['sha256'];old_binary=build.CAND/'isolated_exec/engine_linux64_gf_ompi';oldsha=streamsha(old_binary);image=CAND/'build_workspace.ext4';mount=CAND/'native_workspace';archive=CAND/'source.tar.gz';q=lambda p:shlex.quote(build.linux(p))
 def shell(name,body,cleanup=False):
  left=max(1,int(deadline-time.time()));assert cleanup or left>1,'one-hour build budget exhausted';p=scripts/(name+'.sh');p.write_text('set -eu\n'+body+'\n',encoding='utf8',newline='\n');cap=45 if cleanup else left;args=['wsl.exe','-d','Ubuntu','-u','root','--','timeout','--signal=TERM','--kill-after=5',str(cap),'bash',build.linux(p)];t=time.time();r=subprocess.run(args,capture_output=True,timeout=cap+15);(logs/(name+'.log')).write_bytes(r.stdout+r.stderr);dump(logs/(name+'.execution.json'),{'created_utc':now(),'exit_code':r.returncode,'wall_s':time.time()-t,'cap_s':cap,'argv':args});assert r.returncode==0,name
 mounted=False
 try:
  url=f'https://codeload.github.com/gabrielrussell/OpenRadioss/tar.gz/{PIN}'
  with urllib.request.urlopen(url,timeout=min(60,max(1,deadline-time.time()))) as src,archive.open('wb') as dst:shutil.copyfileobj(src,dst)
  dump(OUT/'source_archive.json',{'url':url,'pin':PIN,'sha256':streamsha(archive),'bytes':archive.stat().st_size})
  shell('01_workspace',f'test ! -e {q(image)}\ntest ! -e {q(mount)}\ntruncate -s 8G {q(image)}\nmkfs.ext4 -q -F {q(image)}\nmkdir {q(mount)}\nmount -o loop {q(image)} {q(mount)}');mounted=True
  shell('02_sources',f'mkdir {q(mount)}/source {q(mount)}/dependency\ntar -xzf {q(archive)} --strip-components=1 -C {q(mount)}/source\ntar -xzf {q(DEPS)} --strip-components=1 -C {q(mount)}/dependency')
  verifier=scripts/'verify_source.py';verifier.write_text('''import pathlib,json,hashlib,sys
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);pre=pathlib.Path(sys.argv[3]);old=pathlib.Path(sys.argv[4]);rows=[]
for tree,sub in [(json.loads((pre/'legacy_candidate_git_tree.json').read_text())['data'],'source'),(json.loads((old/'extlib_v67_tree.json').read_text()),'dependency')]:
 assert not tree.get('truncated')
 for e in tree['tree']:
  if e['type']!='blob':continue
  p=root/sub/e['path'];b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest();n=b.replace(b'\\r\\n',b'\\n');nh=hashlib.sha1(b'blob '+str(len(n)).encode()+b'\\0'+n).hexdigest();assert e['sha'] in [h,nh],e['path'];rows.append({'kind':sub,'path':e['path'],'git_blob_sha1':e['sha'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(out/'source_and_dependency_verification.json').write_text(json.dumps({'pass':True,'files':rows,'no_physics_source_patch':True},indent=2))
''',encoding='utf8',newline='\n');shell('03_verify',f'python3 {q(verifier)} {q(mount)} {q(OUT)} {q(PREFLIGHT)} {q(ROOT/"wtc1_simulation_v8/output/aircraft_a35")}')
  # Only build dependency metadata differs; all tracked mechanical source stays pinned.
  shell('04_dependencies',f'cp {q(mount)}/source/EXTLIB_VERSION.json {q(CAND)}/EXTLIB_VERSION.original.json\ncp -a {q(mount)}/dependency/extlib {q(mount)}/source/extlib\ncp {q(mount)}/dependency/EXTLIB_VERSION.json {q(mount)}/source/EXTLIB_VERSION.json\ncp {q(mount)}/dependency/EXTLIB_VERSION.json {q(mount)}/source/extlib/EXTLIB_VERSION.json');lay=build.CAND/'library_layout';flags=f'-Darch=linux64_gf -Dprecision=dp -DMPI=ompi -Ddebug=0 -Dstatic_link=0 -Dmpi_incdir=/usr/lib/x86_64-linux-gnu/openmpi/include -Dmpi_libdir=/usr/lib/x86_64-linux-gnu/openmpi/lib -Dmumps_root={q(lay/"mumps")} -Dscalapack_root={q(lay/"scalapack")} -Dlapack_root={q(lay/"lapack")} -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=engine_linux64_gf_ompi'
  shell('05_configure',f'cmake -S {q(mount)}/source/engine -B {q(mount)}/engine_build {flags}');shell('06_compile',f'cmake --build {q(mount)}/engine_build --parallel 6');dest=CAND/'isolated_exec';shell('07_export',f'test ! -e {q(dest)}\nmkdir {q(dest)}\ncp {q(mount)}/source/exec/engine_linux64_gf_ompi {q(dest)}/\ncp -a {q(mount)}/source/hm_cfg_files {q(CAND)}/hm_cfg_files\ncp {q(mount)}/engine_build/CMakeCache.txt {q(OUT)}/engine_CMakeCache.txt\nldd {q(dest)}/engine_linux64_gf_ompi');binary=dest/'engine_linux64_gf_ompi';assert binary.exists();assert streamsha(old_binary)==oldsha;dump(OUT/'build_finished.json',{'created_utc':now(),'build_success':True,'source_pin':PIN,'binary_sha256':streamsha(binary),'bytes':binary.stat().st_size,'wall_s':time.time()-started,'within_hour':time.time()<=deadline,'old_MUMPS_binary_preserved':True,'old_Windows_solver_preserved':True,'no_installation':True,'no_physics_source_patch':True,'Starter_not_built':True,'CPU_threads':6,'GPU':False,'native_compatibility_or_physical_validation':False})
 finally:
  if mounted:shell('08_unmount',f'sync\numount {q(mount)}',cleanup=True)

if __name__=='__main__':run()
