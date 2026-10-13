"""Preserved A54 R1: reconcile patch LF output with the approved CRLF file exactly."""
import build_aircraft_a54_graph as base
from pathlib import Path
import hashlib
import json
import shlex
import shutil
import subprocess
import time

ROOT, read, dump, sha, now, linux = base.ROOT, base.read, base.dump, base.sha, base.now, base.linux
OUT=ROOT/'wtc1_simulation_v8/output/aircraft_a56'
CFG=ROOT/'wtc1_simulation_v8/data/aircraft_a56_predeclaration.json'
CAND = ROOT/'wtc1_simulation_v8/openradioss_runtime/a56_type43_scratch_candidate'
ATT = OUT/'build_attempt_0'



def declare():
    assert not OUT.exists() and not CFG.exists() and not CAND.exists()
    h=base.harness();assert h['CurrentIteration']=='AIRCRAFT-A55'
    a55=ROOT/'wtc1_simulation_v8/output/aircraft_a55'
    auth=read(a55/'new_patch_authorization.json');scratch=read(a55/'smstr_patch_proposal_review.json')
    assert auth['explicit_human_authorization'] and auth['patch_sha256']==scratch['patch_sha256']
    assert sha(ROOT/auth['proposal'])==auth['proposal_sha256']
    for key,expected in [('patch_path','patch_sha256'),('proposed_source_path','proposed_sha256')]:assert sha(ROOT/scratch[key])==scratch[expected]
    old=read(base.CFG);OUT.mkdir()
    for name in ['state.json','publication_cycle.json','experiments/registry.jsonl']:shutil.copy2(ROOT/'harness'/name,OUT/('before_'+Path(name).name))
    dump(OUT/'harness_before_build.json',h)
    dump(OUT/'software_authorization.json',auth)
    config={'created_utc':now(),'iteration':'AIRCRAFT-A56','seed':1102081,'random_draws':0,'source_pin':base.PIN,'authorization':auth,'scratch_patch':scratch,'patch':old['patch'],'build':old['build'],'preservation':old['preservation'],'execution':{'maximum_build_s':3600,'CPU_build':6,'native_cap_s':180,'CPU_native':1,'GPU':False},'target_physical_s':10,'best_whole_physical_s':.0200001220703125,'objective1_complete':False}
    dump(CFG,config);dump(OUT/'declaration_guard.json',{'created_utc':now(),'sha256':sha(CFG),'before_build':True})
    previous=read(a55/'preservation_before_metadata.json');pins={row['path']:row for row in previous['files']}
    for row in read(a55/'artifact_manifest.json')['files']:pins[row['path']]=row
    for p in [a55/'artifact_manifest.json',a55/'publication_verification.json']:pins[base.rel(p)]={'path':base.rel(p),'bytes':p.stat().st_size,'sha256':sha(p)}
    rows=[]
    for row in pins.values():
        st=(ROOT/row['path']).stat();assert st.st_size==row['bytes'];rows.append({**row,'mtime_ns_before':st.st_mtime_ns})
    dump(OUT/'preservation_before_metadata.json',{'created_utc':now(),'files':rows,'old_SHA256_manifests_retained':True})
    print(json.dumps({'A56_declared':True,'explicit_scratch_authorization':True}),flush=True)

def guard():
    assert read(ROOT/'harness/state.json')==read(OUT/'before_state.json')
    assert sha(CFG)==read(OUT/'declaration_guard.json')['sha256']
    config=read(CFG);assert config['authorization']['explicit_human_authorization']
    return config

def run():
    config = guard()
    assert not CAND.exists() and not ATT.exists()
    assert CAND.resolve().is_relative_to((ROOT/'wtc1_simulation_v8/openradioss_runtime').resolve())
    started=time.time();deadline=started+3600
    dump(OUT/'build_clock.json',{'started_epoch':started,'deadline_epoch':deadline,'limit_s':3600})
    assert time.time() < deadline
    CAND.mkdir(); ATT.mkdir()
    logs = ATT/'build_logs'; logs.mkdir()
    scripts = ATT/'build_scripts'; scripts.mkdir()
    patch = config['patch']
    proposed = ROOT/patch['proposed_source_path']
    proposed_bytes = proposed.read_bytes()
    assert sha(proposed) == patch['proposed_sha256']
    lf_hash = hashlib.sha256(proposed_bytes.replace(b'\r\n',b'\n')).hexdigest()
    dump(ATT/'attempt_predeclaration.json', {'created_utc': now(), 'iteration': 'AIRCRAFT-A56',
        'attempt': 'R0', 'seed': 1102081, 'random_draws': 0,
        'authorization': 'Explicit approval of exact A55 scratch proposal plus retained A53 graph patch.',
        'previous_A54_attempts_preserved': True, 'graph_EOL_procedure_reused': True,
        'original_deadline_epoch_unchanged': deadline, 'candidate': base.rel(CAND),
        'approved_source_sha256': patch['proposed_sha256'], 'approved_source_LF_sha256': lf_hash,
        'repair': 'Check patched Linux LF output against LF-normalized approved content, then copy the unmodified approved CRLF file and require its exact original SHA256.',
        'physics_or_acceptance_criteria_changed': False, 'GPU': False, 'maximum_CPU_threads': 6})
    source = config['build']['cached_source_archive']
    dependency = config['build']['cached_dependency_archive']
    for row in [source, dependency]:
        assert sha(ROOT/row['path']) == row['sha256']
    shutil.copy2(ROOT/source['path'], CAND/'source.tar.gz')
    shutil.copy2(ROOT/patch['patch_path'], CAND/'type2_graph_routing.patch')
    assert sha(CAND/'type2_graph_routing.patch') == patch['patch_sha256']
    q = lambda path: shlex.quote(linux(path))
    image = CAND/'build_workspace.ext4'; mount = CAND/'native_workspace'
    old_binary = ROOT/config['preservation']['protected_A44_binary']
    old_hash = sha(old_binary)

    def shell(name, body, cleanup=False):
        remaining = int(deadline-time.time())
        assert cleanup or remaining > 0, 'original one-hour build cap exhausted'
        cap = 45 if cleanup else remaining
        script = scripts/(name+'.sh')
        script.write_text('set -eu\n'+body+'\n', encoding='utf8', newline='\n')
        argv = ['wsl.exe','-d','Ubuntu','-u','root','--','timeout',
            '--signal=TERM','--kill-after=5',str(cap),'bash',linux(script)]
        started = time.perf_counter()
        print(json.dumps({'attempt':'R0','build_step':name,'remaining_s':remaining}),flush=True)
        result = subprocess.run(argv,capture_output=True,timeout=cap+15)
        (logs/(name+'.log')).write_bytes(result.stdout+result.stderr)
        dump(logs/(name+'.execution.json'),{'created_utc':now(),'argv':argv,
            'exit_code':result.returncode,'wall_s':time.perf_counter()-started,'cap_s':cap})
        assert result.returncode==0,name

    mounted=False
    try:
        shell('01_workspace',f'test ! -e {q(image)}\ntest ! -e {q(mount)}\ntruncate -s 8G {q(image)}\nmkfs.ext4 -q -F {q(image)}\nmkdir {q(mount)}\nmount -o loop {q(image)} {q(mount)}'); mounted=True
        shell('02_sources',f'mkdir {q(mount)}/source {q(mount)}/dependency\ntar -xzf {q(CAND/"source.tar.gz")} --strip-components=1 -C {q(mount)}/source\ntar -xzf {q(ROOT/dependency["path"])} --strip-components=1 -C {q(mount)}/dependency')
        verifier=scripts/'verify_source.py'
        shutil.copy2(ROOT/'wtc1_simulation_v8/output/aircraft_a44/build_scripts/verify_source.py',verifier)
        shell('03_verify_pristine',f'python3 {q(verifier)} {q(mount)} {q(ATT)} {q(ROOT/"wtc1_simulation_v8/output/aircraft_a43")} {q(ROOT/"wtc1_simulation_v8/output/aircraft_a35")}')
        target=mount/'source'/patch['source_path']
        shell('04_exact_patch',f'test "$(sha256sum {q(target)} | cut -d " " -f 1)" = {patch["original_sha256"]}\ncd {q(mount)}/source\npatch --batch --fuzz=0 -p1 < {q(CAND/"type2_graph_routing.patch")}\ntest "$(sha256sum {q(target)} | cut -d " " -f 1)" = {lf_hash}\ncp {q(proposed)} {q(target)}\ntest "$(sha256sum {q(target)} | cut -d " " -f 1)" = {patch["proposed_sha256"]}\ncmp {q(target)} {q(proposed)}')
        dump(OUT/'exact_patch_application.json',{'created_utc':now(),'pass':True,'attempt':'R0',
            'applied':True,'changed_source_files':[patch['source_path']],
            'patch_sha256':patch['patch_sha256'],'original_sha256':patch['original_sha256'],
            'patched_LF_sha256':lf_hash,'applied_sha256':patch['proposed_sha256'],
            'matches_A53_proposed_file_exactly':True,'previous_attempt_preserved':True,
            'old_source_binary_or_workspace_modified':False})
        scratch=config['scratch_patch']
        target_scratch=mount/'source'/scratch['target']
        scratch_file=ROOT/scratch['patch_path']
        scratch_proposed=ROOT/scratch['proposed_source_path']
        assert sha(scratch_file)==scratch['patch_sha256']
        assert sha(scratch_proposed)==scratch['proposed_sha256']
        shutil.copy2(scratch_file,CAND/'type43_smstr_scratch.patch')
        shell('04b_exact_scratch_patch',f'test "$(sha256sum {q(target_scratch)} | cut -d " " -f 1)" = {scratch["source_sha256"]}\ncd {q(mount)}/source\npatch --batch --fuzz=0 -p1 < {q(CAND/"type43_smstr_scratch.patch")}\ntest "$(sha256sum {q(target_scratch)} | cut -d " " -f 1)" = {scratch["proposed_sha256"]}\ncmp {q(target_scratch)} {q(scratch_proposed)}')
        dump(OUT/'exact_scratch_patch_application.json',{'created_utc':now(),'pass':True,'applied':True,'only_new_changed_file':scratch['target'],'patch_sha256':scratch['patch_sha256'],'applied_source_sha256':scratch['proposed_sha256'],'source_and_restart_widths_unchanged':True,'native_or_physical_qualified':False})
        shell('05_dependencies',f'cp {q(mount)}/source/EXTLIB_VERSION.json {q(CAND)}/EXTLIB_VERSION.original.json\ncp -a {q(mount)}/dependency/extlib {q(mount)}/source/extlib\ncp {q(mount)}/dependency/EXTLIB_VERSION.json {q(mount)}/source/EXTLIB_VERSION.json\ncp {q(mount)}/dependency/EXTLIB_VERSION.json {q(mount)}/source/extlib/EXTLIB_VERSION.json\ngfortran --version\ncmake --version\nmpirun --version\ndpkg-query -W libmumps-5.6 libopenmpi3 liblapack3 libscalapack-openmpi2.2')
        layout=ROOT/config['build']['library_layout']
        flags=f'-Darch=linux64_gf -Dprecision=dp -DMPI=ompi -Ddebug=0 -Dstatic_link=0 -Dmpi_incdir=/usr/lib/x86_64-linux-gnu/openmpi/include -Dmpi_libdir=/usr/lib/x86_64-linux-gnu/openmpi/lib -Dmumps_root={q(layout/"mumps")} -Dscalapack_root={q(layout/"scalapack")} -Dlapack_root={q(layout/"lapack")} -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=engine_linux64_gf_ompi'
        shell('06_configure',f'cmake -S {q(mount)}/source/engine -B {q(mount)}/engine_build {flags}')
        shell('07_compile',f'cmake --build {q(mount)}/engine_build --parallel 6')
        dest=CAND/'isolated_exec'
        shell('08_export',f'test ! -e {q(dest)}\nmkdir {q(dest)}\ncp {q(mount)}/source/exec/engine_linux64_gf_ompi {q(dest)}/\ncp -a {q(mount)}/source/hm_cfg_files {q(CAND)}/hm_cfg_files\ncp {q(mount)}/engine_build/CMakeCache.txt {q(OUT)}/engine_CMakeCache.txt\nldd {q(dest)}/engine_linux64_gf_ompi\nnm -n {q(dest)}/engine_linux64_gf_ompi > {q(OUT)}/engine_symbols.txt')
        binary=dest/'engine_linux64_gf_ompi'
        assert sha(old_binary)==old_hash and time.time()<=deadline
        dump(OUT/'build_finished.json',{'created_utc':now(),'build_success':True,'attempt':'R0',
            'candidate_directory':base.rel(CAND),'source_pin':base.PIN,
            'binary_sha256':sha(binary),'bytes':binary.stat().st_size,
            'wall_s_from_original_start':time.time()-read(OUT/'build_clock.json')['started_epoch'],
            'within_original_hour':True,'CPU_threads':6,'GPU':False,
            'old_A44_binary_preserved':True,'no_installation':True,'Starter_not_built':True,
            'exact_A53_graph_patch_applied':True,'exact_A55_scratch_patch_applied':True,'native_or_physical_qualification':False,
            'source_license':'AGPL-3.0-or-later','prior_A54_EOL_guard_failure_preserved':True})
        print(json.dumps({'build_success':True,'attempt':'R0','binary_sha256':sha(binary)}),flush=True)
    except BaseException as exc:
        dump(ATT/'build_failure.json',{'created_utc':now(),'error':str(exc),'partial_outputs_preserved':True})
        raise
    finally:
        if mounted:shell('09_unmount',f'sync\numount {q(mount)}',cleanup=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('action',choices=['declare','run']);globals()[p.parse_args().action]()
