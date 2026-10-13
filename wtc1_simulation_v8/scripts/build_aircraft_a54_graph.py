"""Authorized, bounded A53 graph patch build in a fresh isolated A54 workspace."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shlex
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'wtc1_simulation_v8/output/aircraft_a54'
CFG = ROOT / 'wtc1_simulation_v8/data/aircraft_a54_predeclaration.json'
PREP = ROOT / 'wtc1_simulation_v8/data/aircraft_a54_preparation.json'
CAND = ROOT / 'wtc1_simulation_v8/openradioss_runtime/a54_type2_graph_candidate'
PIN = '3d75ff13d1946f6d28a43920eac4fa2aae41b27a'


def now():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def dump(path, data):
    with Path(path).open('x', encoding='utf8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def linux(path):
    value = Path(path).resolve().as_posix()
    assert value.startswith('C:/'), value
    return '/mnt/c/' + value[3:]


def harness():
    result = subprocess.run(['C:/Program Files/PowerShell/7/pwsh.exe', '-NoProfile',
        '-Command', "& './harness/tools/Test-WtcHarness.ps1' | ConvertTo-Json"],
        cwd=ROOT, capture_output=True, check=True, timeout=60)
    value = json.loads(result.stdout.decode('utf-8-sig'))
    assert value['Status'] == 'PASS'
    return value


def declare():
    assert not OUT.exists() and not CFG.exists() and not CAND.exists()
    assert CAND.resolve().is_relative_to((ROOT/'wtc1_simulation_v8/openradioss_runtime').resolve())
    h = harness()
    state = read(ROOT/'harness/state.json')
    assert state['current_iteration'] == 'AIRCRAFT-A53' and state['next_iteration'] == 'AIRCRAFT-A54'
    prep = read(PREP)
    patch = prep['patch']
    for path, expected in [(patch['patch_path'], patch['patch_sha256']),
                           (patch['proposed_source_path'], patch['proposed_sha256'])]:
        assert sha(ROOT/path) == expected
    for key in ['cached_source_archive', 'cached_dependency_archive']:
        row = prep['build_after_authorization'][key]
        assert sha(ROOT/row['path']) == row['sha256']
    assert sha(ROOT/prep['preservation']['protected_A44_binary']) == prep['preservation']['protected_A44_binary_sha256']
    OUT.mkdir()
    dump(OUT/'harness_before_build.json', h)
    for name in ['state.json', 'publication_cycle.json', 'experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/name, OUT/('before_'+Path(name).name))
    authorization = {'received_utc': now(), 'explicit_human_authorization': True,
        'answer': "oui j'autorise, continue l'objectif1 : creer la video 3d des 10 premieres secondes de l'impact modelisé sur le WTC1",
        'proposal': prep['authorization']['proposal'], 'proposal_sha256': sha(ROOT/prep['authorization']['proposal']),
        'source_pin': PIN, 'patch_sha256': patch['patch_sha256'], 'cap_s': 3600,
        'maximum_CPU_threads': 6, 'GPU': False, 'new_installation': False,
        'scope': 'Exact A53 graph patch, third separate Engine and fresh bounded qualification controls; continue objective1 subject to physical gates. Prior authorizations are not reused.'}
    dump(OUT/'software_authorization.json', authorization)
    config = {'declared_utc': now(), 'iteration': 'AIRCRAFT-A54', 'seed': 1102079,
        'random_draws': 0, 'preparation': rel(PREP), 'preparation_sha256': sha(PREP),
        'authorization': authorization, 'patch': patch,
        'build': prep['build_after_authorization'],
        'native_controls': prep['native_controls_after_successful_build'],
        'preservation': prep['preservation'], 'retained_limitations': prep['retained_limitations'],
        'target_physical_s': 10, 'best_whole_physical_s': .0200001220703125,
        'new_whole_duration_credit_s': 0, 'whole_insertion_ready': False, 'objective1_complete': False}
    dump(CFG, config)
    dump(OUT/'declaration_guard.json', {'created_utc': now(), 'sha256': sha(CFG), 'before_build': True})
    previous = ROOT/'wtc1_simulation_v8/output/aircraft_a53'
    rows = {}
    for name in ['preservation_before_metadata.json', 'artifact_manifest.json']:
        for row in read(previous/name)['files']:
            st = (ROOT/row['path']).stat()
            assert st.st_size == row['bytes'], row['path']
            rows[row['path']] = {**row, 'mtime_ns_before': st.st_mtime_ns}
    for path in [PREP, ROOT/'harness/handoffs/PREPARATION_A54_2026-10-13.md',
                 previous/'publication_verification.json', previous/'artifact_manifest.json']:
        st = path.stat()
        rows[rel(path)] = {'path': rel(path), 'bytes': st.st_size, 'sha256': sha(path), 'mtime_ns_before': st.st_mtime_ns}
    dump(OUT/'preservation_before_metadata.json', {'created_utc': now(), 'files': list(rows.values()),
        'method': 'Saved SHA256 manifests plus fresh size/mtime capture; archives not rescanned.'})
    print(json.dumps({'A54_declared': True, 'explicit_new_authorization_saved': True,
        'old_files_preservation_inventory': len(rows)}), flush=True)


def guard():
    assert sha(CFG) == read(OUT/'declaration_guard.json')['sha256']
    config = read(CFG)
    assert config['authorization']['explicit_human_authorization']
    assert config['authorization']['source_pin'] == PIN
    assert read(ROOT/'harness/state.json') == read(OUT/'before_state.json')
    return config


def build():
    config = guard()
    assert not CAND.exists()
    CAND.mkdir()
    logs = OUT/'build_logs'; logs.mkdir()
    scripts = OUT/'build_scripts'; scripts.mkdir()
    started = time.time(); deadline = started+3600
    dump(OUT/'build_clock.json', {'started_epoch': started, 'deadline_epoch': deadline, 'limit_s': 3600})
    q = lambda path: shlex.quote(linux(path))
    image = CAND/'build_workspace.ext4'
    mount = CAND/'native_workspace'
    source = config['build']['cached_source_archive']
    dependency = config['build']['cached_dependency_archive']
    for row in [source, dependency]:
        assert sha(ROOT/row['path']) == row['sha256']
    old_binary = ROOT/config['preservation']['protected_A44_binary']
    old_hash = sha(old_binary)
    shutil.copy2(ROOT/source['path'], CAND/'source.tar.gz')
    shutil.copy2(ROOT/config['patch']['patch_path'], CAND/'type2_graph_routing.patch')
    assert sha(CAND/'type2_graph_routing.patch') == config['patch']['patch_sha256']
    dump(OUT/'source_archive.json', {'created_utc': now(), 'pin': PIN,
        'copied_from_verified_cache': source['path'], 'sha256': sha(CAND/'source.tar.gz'),
        'bytes': (CAND/'source.tar.gz').stat().st_size, 'new_download': False})

    def shell(name, body, cleanup=False):
        remaining = int(deadline-time.time())
        assert cleanup or remaining > 0, 'one-hour build cap exhausted'
        cap = 45 if cleanup else remaining
        path = scripts/(name+'.sh')
        path.write_text('set -eu\n'+body+'\n', encoding='utf8', newline='\n')
        argv = ['wsl.exe','-d','Ubuntu','-u','root','--','timeout',
            '--signal=TERM','--kill-after=5',str(cap),'bash',linux(path)]
        start = time.perf_counter()
        print(json.dumps({'build_step': name, 'remaining_s': remaining}), flush=True)
        result = subprocess.run(argv, capture_output=True, timeout=cap+15)
        (logs/(name+'.log')).write_bytes(result.stdout+result.stderr)
        dump(logs/(name+'.execution.json'), {'created_utc': now(), 'argv': argv,
            'exit_code': result.returncode, 'wall_s': time.perf_counter()-start, 'cap_s': cap})
        assert result.returncode == 0, name

    mounted = False
    try:
        shell('01_workspace', f'test ! -e {q(image)}\ntest ! -e {q(mount)}\ntruncate -s 8G {q(image)}\nmkfs.ext4 -q -F {q(image)}\nmkdir {q(mount)}\nmount -o loop {q(image)} {q(mount)}')
        mounted = True
        shell('02_sources', f'mkdir {q(mount)}/source {q(mount)}/dependency\ntar -xzf {q(CAND/"source.tar.gz")} --strip-components=1 -C {q(mount)}/source\ntar -xzf {q(ROOT/dependency["path"])} --strip-components=1 -C {q(mount)}/dependency')
        verifier = scripts/'verify_source.py'
        shutil.copy2(ROOT/'wtc1_simulation_v8/output/aircraft_a44/build_scripts/verify_source.py', verifier)
        shell('03_verify_pristine', f'python3 {q(verifier)} {q(mount)} {q(OUT)} {q(ROOT/"wtc1_simulation_v8/output/aircraft_a43")} {q(ROOT/"wtc1_simulation_v8/output/aircraft_a35")}')
        target = mount/'source'/config['patch']['source_path']
        shell('04_exact_patch', f'test "$(sha256sum {q(target)} | cut -d " " -f 1)" = {config["patch"]["original_sha256"]}\ncd {q(mount)}/source\npatch --batch --fuzz=0 -p1 < {q(CAND/"type2_graph_routing.patch")}\ntest "$(sha256sum {q(target)} | cut -d " " -f 1)" = {config["patch"]["proposed_sha256"]}\ncmp {q(target)} {q(ROOT/config["patch"]["proposed_source_path"])}')
        dump(OUT/'exact_patch_application.json', {'created_utc': now(), 'pass': True,
            'applied': True, 'changed_source_files': [config['patch']['source_path']],
            'patch_sha256': config['patch']['patch_sha256'],
            'original_sha256': config['patch']['original_sha256'],
            'applied_sha256': config['patch']['proposed_sha256'], 'matches_A53_proposed_file_exactly': True,
            'old_source_binary_or_workspace_modified': False})
        shell('05_dependencies', f'cp {q(mount)}/source/EXTLIB_VERSION.json {q(CAND)}/EXTLIB_VERSION.original.json\ncp -a {q(mount)}/dependency/extlib {q(mount)}/source/extlib\ncp {q(mount)}/dependency/EXTLIB_VERSION.json {q(mount)}/source/EXTLIB_VERSION.json\ncp {q(mount)}/dependency/EXTLIB_VERSION.json {q(mount)}/source/extlib/EXTLIB_VERSION.json\ngfortran --version\ncmake --version\nmpirun --version\ndpkg-query -W libmumps-5.6 libopenmpi3 liblapack3 libscalapack-openmpi2.2')
        layout = ROOT/config['build']['library_layout']
        flags = f'-Darch=linux64_gf -Dprecision=dp -DMPI=ompi -Ddebug=0 -Dstatic_link=0 -Dmpi_incdir=/usr/lib/x86_64-linux-gnu/openmpi/include -Dmpi_libdir=/usr/lib/x86_64-linux-gnu/openmpi/lib -Dmumps_root={q(layout/"mumps")} -Dscalapack_root={q(layout/"scalapack")} -Dlapack_root={q(layout/"lapack")} -DCMAKE_Fortran_COMPILER=gfortran -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DEXEC_NAME=engine_linux64_gf_ompi'
        shell('06_configure', f'cmake -S {q(mount)}/source/engine -B {q(mount)}/engine_build {flags}')
        shell('07_compile', f'cmake --build {q(mount)}/engine_build --parallel 6')
        dest = CAND/'isolated_exec'
        shell('08_export', f'test ! -e {q(dest)}\nmkdir {q(dest)}\ncp {q(mount)}/source/exec/engine_linux64_gf_ompi {q(dest)}/\ncp -a {q(mount)}/source/hm_cfg_files {q(CAND)}/hm_cfg_files\ncp {q(mount)}/engine_build/CMakeCache.txt {q(OUT)}/engine_CMakeCache.txt\nldd {q(dest)}/engine_linux64_gf_ompi\nnm -n {q(dest)}/engine_linux64_gf_ompi > {q(OUT)}/engine_symbols.txt')
        binary = dest/'engine_linux64_gf_ompi'
        assert sha(old_binary) == old_hash
        assert time.time() <= deadline
        dump(OUT/'build_finished.json', {'created_utc': now(), 'build_success': True,
            'source_pin': PIN, 'binary_sha256': sha(binary), 'bytes': binary.stat().st_size,
            'wall_s': time.time()-started, 'within_hour': True, 'CPU_threads': 6, 'GPU': False,
            'old_A44_binary_preserved': True, 'no_installation': True, 'Starter_not_built': True,
            'exact_A53_graph_patch_applied': True, 'native_or_physical_qualification': False,
            'source_license': 'AGPL-3.0-or-later'})
        print(json.dumps({'build_success': True, 'wall_s': time.time()-started, 'binary_sha256': sha(binary)}), flush=True)
    except BaseException as exc:
        dump(OUT/'build_failure.json', {'created_utc': now(), 'error': str(exc),
            'wall_s': time.time()-started, 'partial_outputs_preserved': True})
        raise
    finally:
        if mounted:
            shell('09_unmount', f'sync\numount {q(mount)}', cleanup=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['declare', 'build'])
    globals()[parser.parse_args().action]()
