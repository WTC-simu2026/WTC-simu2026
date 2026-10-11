"""Authorized, isolated and bounded Linux candidate; no physics source changes."""
import argparse, datetime as dt, hashlib, json, pathlib, subprocess, time, urllib.request, shutil
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a35'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a35_mumps_build_predeclaration.json'
CAND=ROOT/'wtc1_simulation_v8/openradioss_runtime/a34_mumps_candidate'
PIN='bad6688602d770e019b75773d2d5a48b4f9bd918'
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def read(p): return json.loads(p.read_text(encoding='utf8'))
def dump(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def linux(p): return '/mnt/'+p.drive[0].lower()+'/'+p.as_posix()[3:]
def harness():
 r=subprocess.run(['pwsh','-NoProfile','-File',str(ROOT/'harness/tools/Test-WtcHarness.ps1')],capture_output=True,text=True,encoding='utf8');assert r.returncode==0,r.stdout+r.stderr;return r.stdout
def declare():
 assert not OUT.exists() and not CFG.exists() and not CAND.exists()
 st=read(ROOT/'harness/state.json');assert st['current_iteration']=='AIRCRAFT-A34'
 assert read(ROOT/'wtc1_simulation_v8/output/aircraft_a34/publication_verification.json')['pass']
 OUT.mkdir();(OUT/'harness_before.txt').write_text(harness(),encoding='utf8')
 for n in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/n,OUT/('before_'+pathlib.Path(n).name))
 proposal=ROOT/'wtc1_simulation_v8/output/aircraft_a33/native_build_preflight/build_proposal.json'
 c={'iteration':'AIRCRAFT-A35','declared_utc':now(),'seed':1102060,'random_draws':0,'purpose':'Enable and measure a native implicit route toward the actual10physicalseconds, not a slowed20ms video.',
 'authorization':{'human_answer':'Oui, installer et compiler le solveur séparé','scope':'MinimalUbuntuWSLdependencies and separateMUMPSbuild, onehour maximum','proposal':rel(proposal),'proposal_sha256':sha(proposal),'received_before_installation':True},
 'source':{'repository':'https://github.com/gabrielrussell/OpenRadioss','commit':PIN,'license':'AGPL-3.0','tree':rel(ROOT/'wtc1_simulation_v8/output/aircraft_a31/implicit_capability/sources/preserved_source_tree.json'),'verify_git_blobs':True},
 'destination':rel(CAND),'configuration':{'arch':'linux64_gf','precision':'dp','MPI':'ompi','maximum_compile_threads':6,'GPU':False,'physics_source_patch':False,'replace_Windows_solver':False,'binary_publication':False},
 'packages':['gfortran','libopenmpi-dev','libmumps-dev','libscalapack-openmpi-dev','liblapack-dev'],'required_library_layout_dependencies':'libtmglib-dev only if the pinned build requires libtmglib.a; mandatory package dependencies recorded before installation','general_upgrade':False,
 'execution':{'wall_limit_seconds':3600,'estimated_minutes':[15,60],'workspace_GB':[2,8],'start_at_first_install_or_download':True},
 'gates':{'source_integrity':'Pinned tree and Gitblob content','build':'SeparateStarter/Engine, SHA256, exactflags, linkedMUMPS and logs','native':'Fresh1mmcubePCG/MUMPS and explicit sameversion; finite histories, mass, energy, work and fields. Build success is not physical validation.'},
 'deferred':{'mechanical_draft':rel(ROOT/'wtc1_simulation_v8/scripts/run_aircraft_a35.py'),'run':False,'reason':'NewexplicitMUMPSauthorization changes priority; no mechanicalcampaign declared or run.'},'objective1_complete':False,'whole_insertion_ready':False}
 dump(CFG,c);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_environment_changes':True});CAND.mkdir()
 print({'A35_declared':True,'build_only_wall_cap_seconds':3600},flush=True)
def guard(): assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
def begin():
 guard();p=OUT/'build_clock.json';assert not p.exists();t=time.time();dump(p,{'started_utc':now(),'started_epoch':t,'deadline_epoch':t+3600,'wall_cap_seconds':3600})
def remain(): return read(OUT/'build_clock.json')['deadline_epoch']-time.time()
def shell(name,s,root=False):
 guard();p=OUT/'build_scripts'/f'{name}.sh';assert not p.exists();p.parent.mkdir(exist_ok=True)
 log=OUT/'build_logs'/f'{name}.log';log.parent.mkdir(exist_ok=True)
 p.write_text('#!/bin/bash\nset -euo pipefail\nexec >"'+linux(log)+'" 2>&1\n'+s+'\n',encoding='utf8',newline='\n')
 timeout=int(remain());assert timeout>0
 cmd=['wsl.exe','-d','Ubuntu']+(['-u','root'] if root else [])+['--','timeout','--signal=TERM','--kill-after=10',str(timeout),'bash',linux(p)]
 t=time.time();print({'start':name,'remaining_seconds':timeout},flush=True)
 with (OUT/'build_logs'/f'{name}.launcher.log').open('wb') as f:
  r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+25)
 meta={'created_utc':now(),'argv':cmd,'exit_code':r.returncode,'seconds':time.time()-t,'log':rel(log),'log_sha256':sha(log),'script_sha256':sha(p)};dump(OUT/'build_logs'/f'{name}.execution.json',meta);print(meta,flush=True);assert r.returncode==0,log
def install():
 begin()
 shell('01_inventory_before',"date -u\nuname -a\ncat /etc/os-release\ncmake --version\ngcc --version\ndpkg-query -W -f='${binary:Package}\t${Version}\t${Status}\\n' > '"+linux(OUT/'package_inventory_before.txt')+"'\n",True)
 shell('02_apt_update','apt-get update',True)
 shell('03_apt_simulation','apt-get --simulate install --no-install-recommends gfortran libopenmpi-dev libmumps-dev libscalapack-openmpi-dev liblapack-dev libtmglib-dev',True)
 shell('04_apt_install','DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gfortran libopenmpi-dev libmumps-dev libscalapack-openmpi-dev liblapack-dev libtmglib-dev',True)
 shell('05_inventory_after',"dpkg-query -W -f='${binary:Package}\t${Version}\t${Status}\\n' > '"+linux(OUT/'package_inventory_after.txt')+"'\ngfortran --version\nmpifort --showme\nmpicc --showme\nfind /usr/lib/x86_64-linux-gnu -maxdepth 3 \\( -name '*mumps*' -o -name '*pord*' -o -name '*scalapack*' -o -name '*lapack*' -o -name '*blas*' -o -name '*tmglib*' \\) -print\nls /usr/include/*mumps*",True)
def source():
 guard();assert remain()>0;arc=CAND/'source.tar.gz';assert not arc.exists();url=f'https://codeload.github.com/gabrielrussell/OpenRadioss/tar.gz/{PIN}'
 with urllib.request.urlopen(url,timeout=min(120,remain())) as src,arc.open('wb') as dst:shutil.copyfileobj(src,dst)
 dump(OUT/'source_archive.json',{'url':url,'sha256':sha(arc),'bytes':arc.stat().st_size,'downloaded_utc':now()})
 shell('06_extract_source',"mkdir '"+linux(CAND/'source')+"'\ntar -xzf '"+linux(arc)+"' --strip-components=1 -C '"+linux(CAND/'source')+"'")
 verify_source()
def verify_source():
 guard();tree=read(ROOT/'wtc1_simulation_v8/output/aircraft_a31/implicit_capability/sources/preserved_source_tree.json');rows=[];excluded=[];bad=[]
 for e in tree['tree']:
  if e['type']!='blob':continue
  p=CAND/'source'/e['path']
  if not p.is_file():excluded.append(e);continue
  b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();n=b.replace(b'\r\n',b'\n');nh=hashlib.sha1(b'blob '+str(len(n)).encode()+b'\0'+n).hexdigest()
  kind='exact' if h==e['sha'] else 'GitHub_archive_CRLF_checkout' if nh==e['sha'] else 'mismatch'
  if kind=='mismatch':bad.append(e)
  rows.append({'path':e['path'],'expected_git_blob_sha1':e['sha'],'archive_git_blob_sha1':h,'LF_git_blob_sha1':nh,'comparison':kind,'bytes':len(b)})
 # GitHub archive intentionally excludes files identified by export-ignore only.
 dump(OUT/'source_git_verification.json',{'created_utc':now(),'commit':PIN,'files':rows,'missing':excluded,'mismatches':bad,'all_existing_git_blobs_match':not bad,'source_physics_modified':False,'initial_strict_failure':'ArchiveWindowsBATcontainsCRLF; pinnedrawandLF-normalization matchexactGitblob. No contents edited.'});print({'source_verified':len(rows),'missing':len(excluded),'mismatches':[e['path'] for e in bad]},flush=True);assert not bad and not excluded
def build():
 guard();assert read(OUT/'source_git_verification.json')['all_existing_git_blobs_match']
 lay=linux(CAND/'library_layout');src=linux(CAND/'source');eng=linux(CAND/'engine_build');sta=linux(CAND/'starter_build')
 # GNU ld INPUT bridge preserves the installed shared-library names and source CMake.
 shell('07_library_layout',f'''mkdir -p '{lay}/mumps/lib' '{lay}/scalapack' '{lay}/lapack'
ln -s /usr/include '{lay}/mumps/include'
for lib in dmumps mumps_common pord; do printf 'INPUT ( /usr/lib/x86_64-linux-gnu/lib%s.so )\\n' "$lib" > '{lay}/mumps/lib/lib'"$lib"'.a'; done
printf 'INPUT ( /usr/lib/x86_64-linux-gnu/libscalapack-openmpi.so )\\n' > '{lay}/scalapack/libscalapack.a'
for lib in lapack tmglib; do printf 'INPUT ( /usr/lib/x86_64-linux-gnu/lib%s.so )\\n' "$lib" > '{lay}/lapack/lib'"$lib"'.a'; done
printf 'INPUT ( /usr/lib/x86_64-linux-gnu/libblas.so )\\n' > '{lay}/lapack/librefblas.a'
find '{lay}' -type f -print -exec cat {{}} \\;
file '{src}/extlib/zlib/linux64/lib/libz.a' '{src}/extlib/md5/linux64/libmd5.a'
''')
 conf={'created_utc':now(),'source_modified':False,'library_layout':'GNUldINPUTscripts referencing actual installed Ubuntu shared libraries; .a layout paths are not claims of static libraries.','MUMPS':'Ubuntu5.6.2; interface compatibility must be proven by fresh native probes','engine_flags':{'arch':'linux64_gf','precision':'dp','MPI':'ompi','mpi_incdir':'/usr/lib/x86_64-linux-gnu/openmpi/include','mpi_libdir':'/usr/lib/x86_64-linux-gnu/openmpi/lib','mumps_root':lay+'/mumps','scalapack_root':lay+'/scalapack','lapack_root':lay+'/lapack','no_python':1,'debug':0},'compile_threads':6}
 dump(OUT/'actual_build_configuration.json',conf)
 shell('08_engine_configure',f"cmake -S '{src}/engine' -B '{eng}' -Darch=linux64_gf -Dprecision=dp -DMPI=ompi -Ddebug=0 -Dno_python=1 -Dstatic_link=0 -Dmpi_incdir=/usr/lib/x86_64-linux-gnu/openmpi/include -Dmpi_libdir=/usr/lib/x86_64-linux-gnu/openmpi/lib -Dmumps_root='{lay}/mumps' -Dscalapack_root='{lay}/scalapack' -Dlapack_root='{lay}/lapack' -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=engine_linux64_gf_ompi")
 shell('09_engine_compile',f"cmake --build '{eng}' --parallel 6")
 shell('10_starter_configure',f"cmake -S '{src}/starter' -B '{sta}' -Darch=linux64_gf -Dprecision=dp -Ddebug=0 -Dno_python=1 -Dstatic_link=0 -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=starter_linux64_gf -DUSE_OPEN_READER=OFF")
 shell('11_starter_compile',f"cmake --build '{sta}' --parallel 6")
 dump(OUT/'build_finished.json',{'created_utc':now(),'seconds':time.time()-read(OUT/'build_clock.json')['started_epoch'],'limit_seconds':3600,'build_commands_completed':True,'native_physical_validation':False})
def recover_extlib():
 guard();assert remain()>0 and read(OUT/'build_logs/09_engine_compile.execution.json')['exit_code']!=0
 pin=read(OUT/'extlib_mirror_tree.json')['sha'];arc=CAND/'extlib_mirror.tar.gz';assert not arc.exists()
 c={'declared_utc':now(),'reason':'Pinnedv82automaticdownload fails; publicmirror has revision59. This is a different dependency revision, not v82 equivalence.','mirror':'https://github.com/xupeiwust/OpenRadioss_extlib','pin':pin,'source_physics_changes':False,'only_tracked_source_override':'EXTLIB_VERSION.json dependencyconfiguration, original archived','starter_reader':'BuildOpenReaderfrompinnedOpenRadioss source; no unavailableproprietaryreader','acceptance':'Nativeprobes and actualcards required; no scientificgates waived','original_deadline_epoch':read(OUT/'build_clock.json')['deadline_epoch']};dump(OUT/'extlib_recovery_predeclaration.json',c)
 url=f'https://codeload.github.com/xupeiwust/OpenRadioss_extlib/tar.gz/{pin}'
 with urllib.request.urlopen(url,timeout=min(120,remain())) as src,arc.open('wb') as dst:shutil.copyfileobj(src,dst)
 dump(OUT/'extlib_archive.json',{'url':url,'sha256':sha(arc),'bytes':arc.stat().st_size,'downloaded_utc':now(),'license':'AGPL3project with individuallicensespreserved'})
 dest=CAND/'extlib_mirror';shell('12_extract_extlib',f"mkdir '{linux(dest)}'\ntar -xzf '{linux(arc)}' --strip-components=1 -C '{linux(dest)}'")
 tree=read(OUT/'extlib_mirror_tree.json');rows=[]
 for e in tree['tree']:
  if e['type']!='blob':continue
  p=dest/e['path'];b=p.read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();n=b.replace(b'\r\n',b'\n');nh=hashlib.sha1(b'blob '+str(len(n)).encode()+b'\0'+n).hexdigest();assert e['sha'] in [h,nh],e['path'];rows.append({'path':e['path'],'git_blob_sha1':e['sha'],'sha256':sha(p),'bytes':len(b)})
 dump(OUT/'extlib_git_verification.json',{'created_utc':now(),'pin':pin,'files':rows,'pass':True})
 source=CAND/'source';shutil.copy2(source/'EXTLIB_VERSION.json',CAND/'EXTLIB_VERSION.original_pinned.json');shutil.copy2(dest/'EXTLIB_VERSION.json',source/'EXTLIB_VERSION.json');shutil.copytree(dest/'extlib',source/'extlib',dirs_exist_ok=False);shutil.copy2(dest/'EXTLIB_VERSION.json',source/'extlib/EXTLIB_VERSION.json')
 dump(OUT/'build_metadata_override.json',{'created_utc':now(),'file':'EXTLIB_VERSION.json','old_sha256':sha(CAND/'EXTLIB_VERSION.original_pinned.json'),'new_sha256':sha(source/'EXTLIB_VERSION.json'),'old':read(CAND/'EXTLIB_VERSION.original_pinned.json'),'new':read(source/'EXTLIB_VERSION.json'),'physics_source_modified':False})
 print({'extlib_revision':read(source/'EXTLIB_VERSION.json')['version'],'verified_files':len(rows),'remaining_seconds':remain()},flush=True)
def resume_build():
 guard();assert read(OUT/'extlib_git_verification.json')['pass'];src=linux(CAND/'source');eng=linux(CAND/'engine_build');sta=linux(CAND/'starter_build');rdr=linux(CAND/'reader_build')
 shell('13_engine_compile_with_pinned_dependency',f"cmake --build '{eng}' --parallel 6")
 shell('14_reader_configure',f"cmake -S '{src}/reader' -B '{rdr}' -Darch=linux64 -Dcom=0 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++")
 shell('15_reader_compile',f"cmake --build '{rdr}' --parallel 6")
 shell('16_starter_configure',f"cmake -S '{src}/starter' -B '{sta}' -Darch=linux64_gf -Dprecision=dp -Ddebug=0 -Dno_python=1 -Dstatic_link=0 -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=starter_linux64_gf -DUSE_OPEN_READER=1")
 shell('17_starter_compile',f"cmake --build '{sta}' --parallel 6")
 dump(OUT/'build_finished.json',{'created_utc':now(),'seconds':time.time()-read(OUT/'build_clock.json')['started_epoch'],'limit_seconds':3600,'build_commands_completed':True,'native_physical_validation':False,'dependency_revision_override':rel(OUT/'build_metadata_override.json'),'reader':'pinnedopensource'})
def fast_build():
 guard();assert remain()>0;assert read(OUT/'build_logs/13_engine_compile_with_pinned_dependency.execution.json')['exit_code']!=0
 image=CAND/'build_workspace_w2.ext4';mount=CAND/'fast_workspace_w2'
 assert not image.exists() and not mount.exists();assert image.resolve().is_relative_to(CAND.resolve()) and mount.resolve().is_relative_to(CAND.resolve())
 u='https://api.github.com/repos/AgenteScontro/OpenRadioss_extlib/git/trees/main?recursive=1';tree=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'WTC1-reproducible-research'}),timeout=30));assert not tree.get('truncated');dump(OUT/'extlib_v67_tree.json',tree);pin=tree['sha']
 c={'declared_utc':now(),'attempt':'w2','purpose':'Resolve provenH3D_NF_FORMATheader incompatibility and measuredslowDrvFSdependency scanning; no mechanicalsourcepatch','extlib_repository':'https://github.com/AgenteScontro/OpenRadioss_extlib','extlib_pin':pin,'expected_revision':67,'source_commit':PIN,'CPU_threads':6,'precision':'dp','MPI':'ompi','image':rel(image),'mount':rel(mount),'sparse_image_GB':8,'within_original_deadline_epoch':read(OUT/'build_clock.json')['deadline_epoch'],'old_attempts_preserved':True};dump(OUT/'build_w2_predeclaration.json',c)
 arc=CAND/'extlib_v67.tar.gz';assert not arc.exists();url=f'https://codeload.github.com/AgenteScontro/OpenRadioss_extlib/tar.gz/{pin}'
 with urllib.request.urlopen(url,timeout=min(120,remain())) as src,arc.open('wb') as dst:shutil.copyfileobj(src,dst)
 dump(OUT/'extlib_v67_archive.json',{'downloaded_utc':now(),'url':url,'sha256':sha(arc),'bytes':arc.stat().st_size})
 m=linux(mount);im=linux(image);original=linux(CAND/'source.tar.gz');dep=linux(arc);lay=linux(CAND/'library_layout');export=linux(CAND/'isolated_exec')
 # All files stay within the approved candidate directory, including the backing image.
 shell('18_ext4_workspace_setup',f"test ! -e '{im}'\ntest ! -e '{m}'\ntruncate -s 8G '{im}'\nmkfs.ext4 -q -F '{im}'\nmkdir '{m}'\nmount -o loop '{im}' '{m}'\nmkdir '{m}/source' '{m}/dependency'\ntar -xzf '{original}' --strip-components=1 -C '{m}/source'\ntar -xzf '{dep}' --strip-components=1 -C '{m}/dependency'\ncp -a '{m}/dependency/extlib' '{m}/source/extlib'\ncp '{m}/dependency/EXTLIB_VERSION.json' '{m}/source/EXTLIB_VERSION.json'\ncp '{m}/dependency/EXTLIB_VERSION.json' '{m}/source/extlib/EXTLIB_VERSION.json'\nfindmnt '{m}'",True)
 verify=OUT/'build_scripts/verify_w2.py';verify.write_text('''import pathlib,json,hashlib,sys
root=pathlib.Path(sys.argv[1]);out=pathlib.Path(sys.argv[2]);base=json.loads((out/'source_git_verification.json').read_text());changes=[]
for r in base['files']:
 b=(root/'source'/r['path']).read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest()
 if h!=r['archive_git_blob_sha1']:changes.append(r['path'])
assert changes==['EXTLIB_VERSION.json'],changes
tree=json.loads((out/'extlib_v67_tree.json').read_text());rows=[]
for r in tree['tree']:
 if r['type']!='blob':continue
 b=(root/'dependency'/r['path']).read_bytes();h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\\0'+b).hexdigest();n=b.replace(b'\\r\\n',b'\\n');nh=hashlib.sha1(b'blob '+str(len(n)).encode()+b'\\0'+n).hexdigest();assert r['sha'] in [h,nh],r['path'];rows.append({'path':r['path'],'git_blob_sha1':r['sha'],'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
assert json.loads((root/'source/EXTLIB_VERSION.json').read_text())['version']=='67'
assert b'H3D_NF_FORMAT' in (root/'source/extlib/h3d/includes/h3dpublic_defs.h').read_bytes()
(out/'source_w2_verification.json').write_text(json.dumps({'pass':True,'tracked_physics_source_unchanged':True,'tracked_changes':changes,'dependency_files':rows,'dependency_pin':tree['sha'],'revision':67},indent=2))
''',encoding='utf8',newline='\n')
 shell('19_w2_source_verification',f"python3 '{linux(verify)}' '{m}' '{linux(OUT)}'",True)
 shell('20_w2_engine_configure',f"cmake -S '{m}/source/engine' -B '{m}/engine_build' -Darch=linux64_gf -Dprecision=dp -DMPI=ompi -Ddebug=0 -Dno_python=1 -Dstatic_link=0 -Dmpi_incdir=/usr/lib/x86_64-linux-gnu/openmpi/include -Dmpi_libdir=/usr/lib/x86_64-linux-gnu/openmpi/lib -Dmumps_root='{lay}/mumps' -Dscalapack_root='{lay}/scalapack' -Dlapack_root='{lay}/lapack' -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=engine_linux64_gf_ompi",True)
 shell('21_w2_engine_compile',f"cmake --build '{m}/engine_build' --parallel 6",True)
 shell('22_w2_reader_configure',f"cmake -S '{m}/source/reader' -B '{m}/reader_build' -Darch=linux64 -Dcom=0 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++",True)
 shell('23_w2_reader_compile',f"cmake --build '{m}/reader_build' --parallel 6",True)
 shell('24_w2_starter_configure',f"cmake -S '{m}/source/starter' -B '{m}/starter_build' -Darch=linux64_gf -Dprecision=dp -Ddebug=0 -Dno_python=1 -Dstatic_link=0 -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=starter_linux64_gf -DUSE_OPEN_READER=1",True)
 shell('25_w2_starter_compile',f"cmake --build '{m}/starter_build' --parallel 6",True)
 shell('26_w2_export',f"test ! -e '{export}'\nmkdir '{export}'\ncp -a '{m}/source/exec/.' '{export}/'\ncp '{m}/engine_build/CMakeCache.txt' '{linux(OUT)}/engine_w2_CMakeCache.txt'\ncp '{m}/starter_build/CMakeCache.txt' '{linux(OUT)}/starter_w2_CMakeCache.txt'\nsync\numount '{m}'",True)
 dump(OUT/'build_finished.json',{'created_utc':now(),'seconds':time.time()-read(OUT/'build_clock.json')['started_epoch'],'limit_seconds':3600,'build_commands_completed':True,'native_physical_validation':False,'source_verification':rel(OUT/'source_w2_verification.json'),'binary_directory':rel(CAND/'isolated_exec'),'dependency_revision':67,'source_commit':PIN,'reader':'pinnedopensource','original_failed_attempts_preserved':True})
def resume_w3():
 guard();assert read(OUT/'build_logs/21_w2_engine_compile.execution.json')['exit_code']==2
 m=linux(CAND/'fast_workspace_w2');export=linux(CAND/'isolated_exec');o=linux(OUT)
 p=OUT/'build_w3_predeclaration.json'
 if not p.exists():dump(p,{'declared_utc':now(),'reason':'PinnedsourcePYTHON_DISABLEDbranch has undeclaredmy_real. EnabledefaultPythoninterface rather than edit any source code. NoPythonloads or callbacks in native decks.','changed_configuration_only':{'no_python':[1,0]},'physics_source_patch':False,'old_attempts_preserved':True,'original_deadline_epoch':read(OUT/'build_clock.json')['deadline_epoch'],'source_commit':PIN,'dependency_revision':67,'CPU_threads':6})
 # WSL shuts down when idle in this environment; the backing image retains all files.
 shell('34_w3_workspace_remount',f"mountpoint -q '{m}' || mount -o loop '{linux(CAND/'build_workspace_w2.ext4')}' '{m}'\ncp '{m}/engine_build/CMakeCache.txt' '{o}/engine_w2_CMakeCache_retained.txt'\ncmake -S '{m}/source/engine' -B '{m}/engine_build' -Dno_python=0",True)
 shell('28_w3_engine_compile',f"cmake --build '{m}/engine_build' --parallel 6",True)
 shell('29_w3_reader_configure',f"cmake -S '{m}/source/reader' -B '{m}/reader_build' -Darch=linux64 -Dcom=0 -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++",True)
 shell('30_w3_reader_compile',f"cmake --build '{m}/reader_build' --parallel 6",True)
 shell('31_w3_starter_configure',f"cmake -S '{m}/source/starter' -B '{m}/starter_build' -Darch=linux64_gf -Dprecision=dp -Ddebug=0 -Dno_python=0 -Dstatic_link=0 -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=starter_linux64_gf -DUSE_OPEN_READER=1",True)
 shell('32_w3_starter_compile',f"cmake --build '{m}/starter_build' --parallel 6",True)
 shell('33_w3_export',f"test ! -e '{export}'\nmkdir '{export}'\ncp -a '{m}/source/exec/.' '{export}/'\ncp '{m}/engine_build/CMakeCache.txt' '{o}/engine_final_CMakeCache.txt'\ncp '{m}/starter_build/CMakeCache.txt' '{o}/starter_final_CMakeCache.txt'\nsync\numount '{m}'",True)
 dump(OUT/'build_finished.json',{'created_utc':now(),'seconds':time.time()-read(OUT/'build_clock.json')['started_epoch'],'limit_seconds':3600,'build_commands_completed':True,'native_physical_validation':False,'source_verification':rel(OUT/'source_w2_verification.json'),'binary_directory':rel(CAND/'isolated_exec'),'dependency_revision':67,'source_commit':PIN,'reader':'pinnedopensource','python_interface':'defaultenabled, unusedbydecks','original_failed_attempts_preserved':True})
def resume_w4():
 guard();assert read(OUT/'build_logs/32_w3_starter_compile.execution.json')['exit_code']==2
 m=linux(CAND/'fast_workspace_w2');export=linux(CAND/'isolated_exec');o=linux(OUT)
 p=CAND/'compatibility/h3dpublic_import.h';assert not p.exists();p.parent.mkdir()
 # Only declarations: bodies already exist in the pinned h3dreader_dl.c loader.
 content='''/* Candidate build interface declarations; not a replacement H3D SDK.
   Basis: pinned common_source/output/h3d/h3d_build_cpp/h3dreader_dl.c
   declares these three wrappers and states its opaque handle is the writer handle.
   H3D checksums/import are not qualified; native decks use text + ANIM/TH. */
#ifndef WTC_A35_H3D_IMPORT_DECLARATIONS
#define WTC_A35_H3D_IMPORT_DECLARATIONS
#include <stdint.h>
#include <h3dpublic_defs.h>
extern "C" {
H3DFileInfo* Hyper3DImportOpen(const char*, H3DMessageFunctionType, H3DErrorFunctionType);
bool Hyper3DImportClose(H3DFileInfo*);
bool Hyper3DLookupString(H3DFileInfo*, uint32_t, const char**);
}
#endif
'''
 p.write_text(content,encoding='utf8',newline='\n')
 dump(OUT/'build_w4_predeclaration.json',{'declared_utc':now(),'reason':'Missingh3dpublic_import.h only requiredforStarterH3Dchecksumwrapper. DeclarethethreeexistingCwrapper interfaces using pinnedloader and SDKwriterhandle typedefs. No bodies/no-op/stub introduced.','header':rel(p),'header_sha256':sha(p),'basis_source':rel(CAND/'source/common_source/output/h3d/h3d_build_cpp/h3dreader_dl.c'),'basis_sha256':sha(CAND/'source/common_source/output/h3d/h3d_build_cpp/h3dreader_dl.c'),'physics_source_patch':False,'H3D_import_and_checksum_qualified':False,'native_inputs':'textRADIOSS,noH3Dimport; nativeANIM/THoutputs','original_deadline_epoch':read(OUT/'build_clock.json')['deadline_epoch'],'CPU_threads':6})
 shell('35_w4_header_setup',f"mountpoint -q '{m}' || mount -o loop '{linux(CAND/'build_workspace_w2.ext4')}' '{m}'\ncp '{linux(p)}' '{m}/source/extlib/h3d/includes/h3dpublic_import.h'\npython3 '{linux(OUT/'build_scripts/verify_w2.py')}' '{m}' '{o}'",True)
 shell('36_w4_starter_compile',f"cmake --build '{m}/starter_build' --parallel 6",True)
 shell('37_w4_export',f"test ! -e '{export}'\nmkdir '{export}'\ncp -a '{m}/source/exec/.' '{export}/'\ncp '{m}/engine_build/CMakeCache.txt' '{o}/engine_final_CMakeCache.txt'\ncp '{m}/starter_build/CMakeCache.txt' '{o}/starter_final_CMakeCache.txt'\nsync\numount '{m}'",True)
 dump(OUT/'build_finished.json',{'created_utc':now(),'seconds':time.time()-read(OUT/'build_clock.json')['started_epoch'],'limit_seconds':3600,'build_commands_completed':True,'native_physical_validation':False,'source_verification':rel(OUT/'source_w2_verification.json'),'binary_directory':rel(CAND/'isolated_exec'),'dependency_revision':67,'source_commit':PIN,'reader':'pinnedopensource','python_interface':'defaultenabled, unusedbydecks','H3D_checksum_interface':'threewrapperdeclarations,noimplementationchanges; notqualified','original_failed_attempts_preserved':True})
def export_partial():
 guard();assert read(OUT/'build_logs/36_w4_starter_compile.execution.json')['exit_code']==2
 m=linux(CAND/'fast_workspace_w2');export=linux(CAND/'isolated_exec');o=linux(OUT)
 dump(OUT/'partial_export_predeclaration.json',{'created_utc':now(),'reason':'LinuxStarterlink failsfiveOpenReaderinterfaces absentfrompinnedsource. No inventedphysics/parserstubs. PreservecompiledEngine and Reader; separatelydeclarefreshWindowsStarter→LinuxEnginecompatibilityprobes.','full_build_success':False,'original_deadline_epoch':read(OUT/'build_clock.json')['deadline_epoch']})
 shell('38_partial_engine_export',f"mountpoint -q '{m}' || mount -o loop '{linux(CAND/'build_workspace_w2.ext4')}' '{m}'\ntest ! -e '{export}'\nmkdir '{export}'\ncp -a '{m}/source/exec/.' '{export}/'\ncp '{m}/engine_build/CMakeCache.txt' '{o}/engine_final_CMakeCache.txt'\ncp '{m}/starter_build/CMakeCache.txt' '{o}/starter_failed_CMakeCache.txt'\nsync\numount '{m}'",True)
 dump(OUT/'build_finished.json',{'created_utc':now(),'seconds':time.time()-read(OUT/'build_clock.json')['started_epoch'],'limit_seconds':3600,'build_commands_completed':False,'engine_built':True,'Linux_starter_built':False,'terminal_build_status':'partial_engine_and_reader__LinuxStarter_link_failed','native_physical_validation':False,'source_verification':rel(OUT/'source_w2_verification.json'),'binary_directory':rel(CAND/'isolated_exec'),'dependency_revision':67,'source_commit':PIN,'reader':'pinnedopensource','python_interface':'defaultenabled, unusedbydecks','H3D_import':'unqualified','original_failed_attempts_preserved':True})
def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','install','source','verify_source','build','recover_extlib','resume_build','fast_build','resume_w3','resume_w4','export_partial']);globals()[p.parse_args().action]()
if __name__=='__main__':main()
