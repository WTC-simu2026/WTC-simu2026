"""One authorized A81 Starter and one strictly conditional Engine; no retries.

The driver saves native execution evidence only. A separate reader must qualify
actual histories, constitutive output populations and physical balances.
"""
from pathlib import Path
import argparse
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import time

from build_aircraft_a54_graph import ROOT, read, dump, sha, now, rel, linux, harness

OUT = ROOT/'wtc1_simulation_v8/output/aircraft_a81'
CFG = ROOT/'wtc1_simulation_v8/data/aircraft_a81_predeclaration.json'
AUTH = ROOT/'wtc1_simulation_v8/data/aircraft_a81_authorization.json'
PLAN = ROOT/'wtc1_simulation_v8/data/aircraft_a80_proposal.json'
PROOF = ROOT/'outputs/github_publication/updates_2026-10-15_aircraft_a78_a79/final_remote_verification.json'
CASE = 'A81_COHESIVE_LOOP'
NAME = 'A81_COHESIVE_COMPRESSION_PARTIAL_OPEN_RECLOSE'
PLAN_SHA = '75c00344ac10a8015e8b5a6df817187a5ad74599499ace6ede1f26764f79e7db'
RECEIPT = 'request_user_input_async/call_a5c8cd61518347429f6bb01020760042/0'
ANSWER = 'Oui, exécuter le témoin A81 après vérification de la publication'
STARTER_SHA = '961eca1640c321b0cb4893c8481942e5162e89ea292d64e964deea1b5ead96d6'
ENGINE_SHA = '09a2f856d0eddb13ba56c80c578a12d058cb2cee1e403d46074b1b77b29aa158'
NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?'


def checked_path(value):
    path = (ROOT/value).resolve()
    path.relative_to(ROOT.resolve())
    return path


def prerequisite_guard():
    """Fail closed before declaration AND before each native attempt."""
    proof = read(PROOF)
    assert proof['pass'] and proof['cadence_pending_count'] == 0
    assert proof['next_iteration'] == 'AIRCRAFT-A80'
    assert proof['release'].endswith('/snapshot-2026-10-15-aircraft-a78-a79')
    for key, commit_key in [('scientific_ci', 'scientific_commit'), ('final_ci', 'final_commit')]:
        assert proof[key]['conclusion'] == 'success' and proof[key]['head_sha'] == proof[commit_key]
        assert re.fullmatch(r'[0-9a-f]{40}', proof[commit_key])
    assert proof['final_tree']['pass'] and proof['final_tree']['commit'] == proof['final_commit']
    state = read(ROOT/'harness/state.json')
    cycle = read(ROOT/'harness/publication_cycle.json')
    assert state['current_iteration'] == 'AIRCRAFT-A80' and state['next_iteration'] == 'AIRCRAFT-A81'
    assert cycle['last_published_iteration'] == 'AIRCRAFT-A79'
    assert cycle['last_published_release'] == 'snapshot-2026-10-15-aircraft-a78-a79'
    assert cycle['pending_iterations'] == ['AIRCRAFT-A80'] and cycle['pending_count'] == 1
    registry = ROOT/'harness/experiments/registry.jsonl'
    assert len([json.loads(line) for line in registry.read_text(encoding='utf-8-sig').splitlines() if line.strip()]) == 199
    auth = read(AUTH); plan = read(PLAN)
    assert auth['explicit_human_authorization'] and auth['answer'] == ANSWER and auth['question_item'] == RECEIPT
    assert auth['plan_path'] == rel(PLAN) and auth['plan_sha256'] == sha(PLAN) == PLAN_SHA
    assert auth['maximum_Starter'] == auth['maximum_Engine'] == auth['CPU_threads'] == 1
    assert auth['Engine_conditional_on_Starter_gate'] and auth['each_cap_s'] == 180
    assert auth['condition_A78_A79_final_publication_verified'] and auth['publication_proof_path'] == rel(PROOF)
    assert auth['prior_budgets_not_reset']
    assert all(auth[key] is False for key in ['GPU', 'source_patch', 'compilation', 'installation', 'whole_dynamic_extension'])
    assert plan['name'] == NAME and plan['Starter'] == plan['Engine_conditional'] == plan['cpu'] == 1
    assert plan['maximum_native_processes'] == 2 and plan['each_cap_s'] == 180
    assert all(plan[key] is False for key in ['GPU', 'source_patch', 'compile', 'installation', 'whole_impact_extension'])
    assert plan['publication_A78_A79_must_be_verified_before_native_A81']
    assert plan['proposal'] == auth['proposal'] and plan['proposal_sha256'] == auth['proposal_sha256'] == sha(checked_path(auth['proposal']))
    assert sha(checked_path(plan['prepared_configuration'])) == plan['prepared_configuration_sha256']
    assert read(checked_path(plan['static_scope_review']))['pass']
    assert read(checked_path(plan['independent_review']))['pass_static_preparation_review_only']
    assert read(checked_path(plan['independent_final_addendum']))['pass_static_final_addendum_only']
    expected = {NAME+'_0000.rad', NAME+'_0001.rad'}
    assert {Path(row['path']).name for row in plan['inputs']} == expected and len(plan['inputs']) == 2
    for row in plan['inputs']:
        assert row['path'].startswith('wtc1_simulation_v8/output/aircraft_a80_preparation/A81_COHESIVE_LOOP/')
        path = checked_path(row['path'])
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
    assert len(plan['unchanged_software']) == 2
    assert [row['sha256'] for row in plan['unchanged_software']] == [STARTER_SHA, ENGINE_SHA]
    for row in plan['unchanged_software'] + plan['sources']:
        assert sha(checked_path(row['path'])) == row['sha256']
    return plan, auth


def declare():
    assert not OUT.exists() and not CFG.exists(), 'Never overwrite or reset an earlier A81 attempt'
    plan, auth = prerequisite_guard()
    h = harness()
    assert h['CurrentIteration'] == 'AIRCRAFT-A80' and h['NextIteration'] == 'AIRCRAFT-A81' and h['RegistryEntries'] == 199
    # Both previous iterations must already be sealed, and all their files stay
    # immutable. This inspection never executes or recompiles prior software.
    pins = {}
    for number in [79, 80]:
        folder = ROOT/f'wtc1_simulation_v8/output/aircraft_a{number}'
        assert read(folder/'publication_verification.json')['pass']
        for row in read(folder/'artifact_manifest.json')['files']:
            path = checked_path(row['path']); assert sha(path) == row['sha256']
            pins[row['path']] = {**row, 'mtime_ns_before': path.stat().st_mtime_ns}
        for path in [folder/'artifact_manifest.json', folder/'publication_verification.json']:
            pins[rel(path)] = {'path': rel(path), 'bytes': path.stat().st_size, 'sha256': sha(path), 'mtime_ns_before': path.stat().st_mtime_ns}
    OUT.mkdir()
    dump(OUT/'authorization.json', auth); dump(OUT/'harness_before.json', h)
    for name in ['state.json', 'publication_cycle.json', 'experiments/registry.jsonl']:
        shutil.copy2(ROOT/'harness'/name, OUT/('before_'+Path(name).name))
    configuration = {**plan, 'iteration': 'AIRCRAFT-A81', 'case': CASE, 'declared_utc': now(),
        'authorization': auth, 'authorization_sha256': sha(AUTH), 'plan_sha256': sha(PLAN),
        'publication_proof_path': rel(PROOF), 'publication_proof_sha256': sha(PROOF),
        'driver_path': rel(Path(__file__)), 'driver_sha256': sha(Path(__file__)),
        'new_explicit_human_authorization_required': False,
        'maximum_Starter': 1, 'maximum_Engine': 1, 'conditional_Engine_not_reassigned': True,
        'observation_qualification_pending': True, 'whole_integration_ready': False}
    dump(CFG, configuration)
    dump(OUT/'declaration_guard.json', {'created_utc': now(), 'sha256': sha(CFG), 'before_any_native': True})
    dump(OUT/'preservation_before_metadata.json', {'created_utc': now(), 'files': list(pins.values()),
        'old_failed_gates_and_budgets_preserved': True, 'archive_rescanned': False})
    print(json.dumps({'A81_declared': True, 'maximum_Starter': 1, 'maximum_Engine_conditional': 1}), flush=True)


def guard():
    prerequisite_guard()
    assert sha(CFG) == read(OUT/'declaration_guard.json')['sha256']
    c = read(CFG)
    assert sha(AUTH) == c['authorization_sha256'] and read(AUTH) == c['authorization']
    assert sha(PLAN) == c['plan_sha256'] and sha(PROOF) == c['publication_proof_sha256']
    assert sha(Path(__file__)) == c['driver_sha256']
    for name in ['state.json', 'publication_cycle.json', 'experiments/registry.jsonl']:
        assert sha(ROOT/'harness'/name) == sha(OUT/('before_'+Path(name).name))
    return c


def engine():
    c = guard()
    binary = checked_path(c['unchanged_software'][1]['path'])
    assert sha(binary) == ENGINE_SHA
    candidate = binary.parent.parent
    assert (candidate/'hm_cfg_files').is_dir()
    return candidate, binary


def native_outputs(d):
    return [{'path': rel(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}
            for path in sorted(d.iterdir()) if path.is_file()]


def consume(d, phase, ordinal):
    guard()
    assert phase in ['starter', 'engine'] and not (d/(phase+'_launch_declaration.json')).exists()
    assert len(list(OUT.rglob(phase+'_launch_declaration.json'))) == 0
    dump(d/(phase+'_launch_declaration.json'), {'created_utc': now(), 'phase': phase, 'ordinal': ordinal,
        'maximum_this_phase': 1, 'maximum_native_total': 2, 'counts_even_if_aborted_failed_or_expired': True,
        'CPU_threads': 1, 'GPU': False, 'cap_s': 180, 'config_sha256': sha(CFG),
        'authorization_sha256': sha(AUTH), 'publication_proof_sha256': sha(PROOF)})


def run_starter(d, c):
    consume(d, 'starter', 1)
    binary = checked_path(c['unchanged_software'][0]['path'])
    en = os.environ.copy()
    en.update(RAD_CFG_PATH='C:/OpenRadioss/hm_cfg_files', RAD_H3D_PATH='C:/OpenRadioss/extlib/h3d/lib/win64',
        OPENRADIOSS_PATH='C:/OpenRadioss', OMP_NUM_THREADS='1', OMP_THREAD_LIMIT='1', RAD_HMPP_DOMAINS='1',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', KMP_STACKSIZE='400m')
    argv = [str(binary), '-i', NAME+'_0000.rad', '-np', '1']
    start = time.perf_counter(); code = None; timed = False; exception = None
    with (d/'starter.log').open('xb') as stream:
        try:
            code = subprocess.run(argv, cwd=d, env=en, stdout=stream, stderr=subprocess.STDOUT, timeout=180).returncode
        except subprocess.TimeoutExpired:
            timed = True
        except OSError as exc:
            exception = {'type': type(exc).__name__, 'message': str(exc)}
    execution = {'created_utc': now(), 'argv': argv, 'exit_code': code, 'wall_s': time.perf_counter()-start,
        'timed_out': timed, 'exception': exception, 'CPU_threads': 1, 'GPU': False, 'cap_s': 180,
        'binary_sha256': sha(binary), 'attempt_consumed': True}
    dump(d/'starter.execution.json', execution)
    dump(d/'starter_outputs_before_analysis.json', {'created_utc': now(), 'files': native_outputs(d)})
    return execution


def one_value(text, label):
    found = []
    for line in text.splitlines():
        if not line.strip().startswith(label):
            continue
        match = re.search(r'=\s*('+NUMBER+r')\s*$', line)
        if match:
            found.append(float(match.group(1).replace('D', 'E').replace('d', 'e')))
    return found[0] if len(found) == 1 else None


def starter_gate(d, execution, c):
    path = d/(NAME+'_0000.out')
    text = path.read_text(errors='replace') if path.exists() else ''
    log = (d/'starter.log').read_text(errors='replace')
    errors = [int(v) for v in re.findall(r'(\d+)\s+ERROR\(S\)', text+'\n'+log)]
    warnings = [int(v) for v in re.findall(r'(\d+)\s+WARNING\(S\)', text+'\n'+log)]
    material = text.split('MATERIAL LAWS', 1)[-1].split('PROPERTY SETS', 1)[0] if 'MATERIAL LAWS' in text else ''
    fields = {
        'LAW': ('MATERIAL LAW.', 117), 'density': ('INITIAL DENSITY', 1e-20),
        'EN': ('STIFFNESS NORMAL TO THE PLANE', 4400), 'ET': ('STIFFNESS IN TO THE PLANE', 800),
        'TN': ('PEAK TRACTION IN NORMAL DIRECTION', 450), 'TT': ('PEAK TRACTION IN TANGENTIAL DIRECTION', 100),
        'GI': ('ENERGY RELEASE RATE FOR MODE I.', 50), 'GII': ('ENERGY RELEASE RATE FOR MODE II', 50),
        'propagation_criterion': ('CHOICE OF PROPAGATION CRITERION', 1),
        'failure_criterion': ('CHOICE OF THE FAILURE CRITERION', 1),
        'damage_evolution': ('CHOICE OF THE DAMAGE EVOLUTION', 1),
        'ISYM': ('SYMMETRIC TENSION/COMPRESSION FLAG', 0),
        'mode_I_failure_displacement_mm': ('MAXIMUM DISPLACEMENT (FAILURE) FOR MODE I ', 2*50/450)}
    values = {key: one_value(material, label) for key, (label, expected) in fields.items()}
    # Print punctuation for MODE I varies from other labels; its complete line
    # remains a unique native observation, never an assumed source default.
    if values['mode_I_failure_displacement_mm'] is None:
        values['mode_I_failure_displacement_mm'] = one_value(material, 'MAXIMUM DISPLACEMENT (FAILURE) FOR MODE I .')
    checks = {key+'_printed_exact': values[key] is not None and math.isclose(values[key], expected, rel_tol=1e-11, abs_tol=0)
              for key, (label, expected) in fields.items()}
    mass = None
    if 'TOTAL MASS AND MASS CENTER' in text:
        for line in text.split('TOTAL MASS AND MASS CENTER', 1)[1].splitlines():
            tokens = line.split()
            if len(tokens) == 4 and all(re.fullmatch(NUMBER, token) for token in tokens):
                mass = [float(v.replace('D', 'E').replace('d', 'e')) for v in tokens]; break
    added = one_value(text, 'TOTAL ADDED MASS')
    property_text = text.split('PROPERTY SETS', 1)[-1].split('PARTS', 1)[0] if 'PROPERTY SETS' in text else ''
    checks.update({
        'exit0_without_timeout_or_launch_exception': execution['exit_code'] == 0 and not execution['timed_out'] and execution['exception'] is None,
        'native_out_exists_and_normal_termination': path.is_file() and 'NORMAL TERMINATION' in text,
        'all_native_error_summaries_zero': bool(errors) and all(v == 0 for v in errors),
        'all_native_warning_summaries_zero': bool(warnings) and all(v == 0 for v in warnings),
        'no_native_error_or_warning_ID': re.search(r'\b(?:ERROR|WARNING)\s+id\s*:', text+'\n'+log, re.I) is None,
        'LAW117_on_part1_printed': re.search(r'MATERIAL\s*:\s*1\s*\(LAW\s+117\)', text) is not None,
        'TYPE43_on_part1_printed': re.search(r'PROPERTY\s*:\s*1\s*\(TYPE\s+43\)', text) is not None,
        'Ismstr4_property_printed': one_value(property_text, 'SMALL STRAIN FLAG') == 4,
        'mass8g_native': mass is not None and abs(mass[0]-8) <= 8*c['inherits_A67_acceptance_formulae']['mass_relative'],
        'ADMAS8g_native': added is not None and abs(added-8) <= 8*c['inherits_A67_acceptance_formulae']['added_mass_relative'],
        'one_nonempty_native_initial_restart': (d/(NAME+'_0000_0001.rst')).is_file() and (d/(NAME+'_0000_0001.rst')).stat().st_size > 0})
    review = {'created_utc': now(), 'checks': checks, 'pass': all(checks.values()),
        'errors': errors, 'warnings': warnings, 'native_material_values': values,
        'native_mass_and_center_g_mm': mass, 'native_ADMAS_g': added,
        'expected_native_defaults': {'failure_criterion': 1, 'linear_damage_evolution': 1, 'ISYM': 0},
        'generic_ISOLID0_information_not_relabelled_warning': True,
        'source_binary_identity_not_assumed': True, 'physical_law_qualification_pending': True,
        'strict_gate_not_relaxed_by_exit0': True, 'conditional_Engine_not_reassigned_on_failure': True}
    dump(d/'starter_gate_review.json', review)
    return review


def run_engine(d):
    candidate, binary = engine()
    q = lambda p: shlex.quote(linux(p))
    script = d/'engine.launch.sh'; assert not script.exists()
    script.write_text('set -eu\ncd '+q(d)+'\n'
        'export OMP_NUM_THREADS=1 OMP_THREAD_LIMIT=1 RAD_HMPP_DOMAINS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1\n'
        'export OPENRADIOSS_PATH='+q(candidate)+'\nexport RAD_CFG_PATH='+q(candidate/'hm_cfg_files')+'\n'
        'exec '+q(binary)+' -i '+shlex.quote(NAME+'_0001.rad')+' > engine.log 2>&1\n', encoding='utf-8', newline='\n')
    consume(d, 'engine', 2)
    argv = ['wsl.exe', '-d', 'Ubuntu', '--', 'timeout', '--signal=TERM', '--kill-after=5', '180', 'bash', linux(script)]
    start = time.perf_counter(); code = None; timed = False; exception = None; stdout = b''; stderr = b''
    try:
        result = subprocess.run(argv, capture_output=True, timeout=195)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        timed = True; stdout, stderr = exc.stdout or b'', exc.stderr or b''
    except OSError as exc:
        exception = {'type': type(exc).__name__, 'message': str(exc)}
    (d/'engine.launcher.log').write_bytes(stdout+stderr)
    execution = {'created_utc': now(), 'argv': argv, 'parent_exit_code': code, 'wall_s': time.perf_counter()-start,
        'timed_out': timed or code in [124, 137], 'parent_timeout_s': 195, 'exception': exception,
        'CPU_threads': 1, 'GPU': False, 'cap_s': 180, 'binary_sha256': sha(binary), 'attempt_consumed': True}
    dump(d/'engine.execution.json', execution)
    dump(d/'engine_outputs_before_analysis.json', {'created_utc': now(), 'files': native_outputs(d)})
    text = (d/'engine.log').read_text(errors='replace') if (d/'engine.log').exists() else ''
    completion = {'created_utc': now(), 'parent_exit_code': code, 'normal_termination': 'NORMAL TERMINATION' in text,
        'kill_or_abort': bool(re.search(r'USERBREAK|SIGSEGV|ABORT', text, re.I)),
        'error_summaries': [int(v) for v in re.findall(r'(\d+)\s+ERROR\(S\)', text)],
        'warning_summaries': [int(v) for v in re.findall(r'(\d+)\s+WARNING\(S\)', text)],
        'observation_qualification_pending': True, 'physical_qualification_pending': True}
    dump(d/'completion_review.json', completion)
    return execution, completion


def run():
    c = guard()
    assert not list(OUT.rglob('*_launch_declaration.json')), 'Any prior attempt consumes its slot; no rerun'
    d = OUT/CASE; assert not d.exists(); d.mkdir()
    for row in c['inputs']:
        source = checked_path(row['path']); target = d/source.name
        shutil.copy2(source, target); assert sha(target) == row['sha256']
    dump(d/'generation.json', {'created_utc': now(), 'name': NAME, 'case': CASE, 'area_mm2': 100,
        'nodal_instrument_masses_g': [1]*8, 'units': c['units'], 'configuration_sha256': sha(CFG),
        'fresh_intact_start': True, 'general_contact_present': False, 'whole_aircraft_run': False,
        'initial_kinetic_energy_J': 0, 'plan': rel(PLAN), 'plan_sha256': sha(PLAN)})
    starter_execution = run_starter(d, c)
    starter = starter_gate(d, starter_execution, c)
    engine_execution = None; completion = None
    if starter['pass']:
        engine_execution, completion = run_engine(d)
    else:
        dump(d/'engine_conditional_skipped.json', {'created_utc': now(), 'reason': 'strict_Starter_gate_failed',
            'failed_checks': [key for key, value in starter['checks'].items() if not value],
            'Engine_attempted': False, 'conditional_slot_unused_not_reassigned': True, 'no_retry': True})
    review = {'created_utc': now(), 'iteration': 'AIRCRAFT-A81', 'new_Starter': 1,
        'new_Engine': int(engine_execution is not None), 'Starter_remaining': 0,
        'Engine_remaining': 0 if engine_execution is not None else 1,
        'conditional_unused_Engine_not_reassigned': engine_execution is None,
        'starter_execution': starter_execution, 'Starter_gate_pass': starter['pass'],
        'starter_errors': starter['errors'], 'starter_warnings': starter['warnings'],
        'engine_execution': engine_execution, 'engine_completion': completion,
        'observation_qualification_pending': True, 'physical_qualification_pending': True,
        'reader_or_converter_executed': False, 'software_patch_compilation_GPU_installation': False,
        'whole_dynamic_extension': False, 'new_whole_credit_s': 0, 'objective1_complete': False,
        'old_failed_gates_and_budgets_preserved': True}
    dump(OUT/'native_execution_review.json', review)
    print(json.dumps({'A81_native_finished': True, 'new_Starter': 1, 'new_Engine': review['new_Engine'],
        'Starter_gate_pass': starter['pass'], 'observation_qualification_pending': True}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['declare', 'run'])
    globals()[parser.parse_args().action]()
