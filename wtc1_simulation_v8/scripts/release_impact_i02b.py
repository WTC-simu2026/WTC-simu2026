"""Release saved I02B results and I02A-derived media; never rerun a solver."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / 'wtc1_simulation_v8/output/impact_i02b_joint_coupon'
VIEW = ROOT / 'wtc1_3d_v4/output/impact_i02b/paraview_i02a'
RENDER = ROOT / 'wtc1_3d_v4/renders/impact_i02b'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def hashes_match(mapping):
    return bool(mapping) and all((ROOT / p).is_file() and sha(ROOT / p) == digest for p, digest in mapping.items())


def preserved_release(path):
    release = read(path)
    return release['delivery_status'] == 'PASS' and hashes_match(release['artifact_sha256'])


parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=('pre_state', 'post_state'), required=True)
args = parser.parse_args()
checks = {}
records = {}
campaign = read(SIM / 'campaign_audit.json')
rows = campaign['case_results']
case_checks = [passed for row in rows.values() for passed in row['checks'].values()]
checks['campaign_17_marks_pass'] = campaign['status'] == 'PASS' and len(campaign['checks']) == 17 and all(campaign['checks'].values())
checks['thirteen_cases_231_checks_pass'] = len(rows) == campaign['accepted_cases'] == 13 and len(case_checks) == 231 and all(case_checks)
checks['normal_termination_no_warning_or_mass_scaling'] = all(r['normal_termination'] and not r['warning_ids'] and r['max_added_mass_g'] == 0 for r in rows.values())
checks['physical_mixed_mode_and_spatial_qualification_false'] = not any(campaign[k] for k in ('physical_boeing_joint_qualification', 'spatial_joint_convergence', 'mixed_mode_postpeak_qualification'))
checks['three_energy_outcomes'] = rows['DYNAMIC_G_LOW_V10_R1']['any_complete_separation'] and rows['DYNAMIC_HIGH_ENERGY_R1']['any_complete_separation'] and not rows['DYNAMIC_G_HIGH_V10_R1']['any_complete_separation']
checks['low_initial_energy_no_separation'] = not rows['DYNAMIC_LOW_ENERGY_R1']['any_complete_separation']
checks['cyclic_slip_retained'] = abs(rows['NORMAL_BASE_CYCLE_R2']['partial_cycle_slip_mm'] - .1875) < 1e-6
records['accepted_case_checks'] = len(case_checks)
records['accepted_execution_seconds'] = sum(r['seconds'] for r in rows.values())
records['max_energy_residual_fraction'] = max(r['max_global_energy_residual_fraction'] for r in rows.values())
records['max_force_reference_error_fraction'] = max(r['max_force_reference_error_fraction'] for r in rows.values())
records['max_momentum_error_fraction'] = max(r['boundary_impulse_momentum_error_fraction'] for r in rows.values())
manifest = read(SIM / 'source_manifest.json')
checks['all_manifest_inputs_and_outputs_current'] = hashes_match(manifest['files'])
records['manifest_hash_count'] = len(manifest['files'])
for name in rows:
    execution = read(SIM / name / 'execution.json')
    checks[f'{name}_successful_executable_identity'] = all(r['returncode'] == 0 and sha(Path(r['command'][0])) == r['executable_sha256'] for r in execution)

presentation = read(SIM / 'presentation.json')
checks['presentation_pass'] = presentation['status'] == 'PASS' and all(presentation['checks'].values())
checks['mp4_current'] = sha(ROOT / presentation['video']) == presentation['video_sha256']
source_frames = ROOT / 'wtc1_3d_v4/renders/impact_i02a/annotated_frames'
checks['twenty_five_cached_frames_preserved'] = len(presentation['source_frame_sha256']) == 25 and all(sha(source_frames / p) == h for p, h in presentation['source_frame_sha256'].items())
with Image.open(SIM / 'synthese_impact_i02b.png') as picture:
    checks['summary_image_reopens'] = picture.size == (1520, 1120)
    picture.verify()
transfer = read(VIEW / 'transfer_audit.json')
states = transfer['states']
checks['paraview_25_exact_states'] = transfer['status'] == 'PASS' and len(states) == 25 and all(all(s['checks'].values()) and s['max_coordinate_error_mm'] == 0 for s in states)
checks['paraview_states_current'] = all(sha(VIEW / f"state_{s['state']:03d}.vtp") == s['sha256'] for s in states)
source_npz = ROOT / 'wtc1_simulation_v8/output/impact_i02a_structured_wing/CONTACT_M050_R1/computed_frames.npz'
checks['paraview_cached_npz_preserved'] = sha(source_npz) == transfer['source_sha256'] == '3a75a853c4e2c71accedce25e289d5994614eab0e09e420505cb8e3b092f4f9e'
datasets = ET.parse(VIEW / 'I02A_solver_states_ms.pvd').findall('./Collection/DataSet')
checks['pvd_times_files_and_units'] = len(datasets) == len(states) and transfer['length_units'] == 'mm' and transfer['time_units'] == 'ms' and all(
    d.attrib['file'] == f"state_{s['state']:03d}.vtp" and abs(float(d.attrib['timestep']) - s['time_ms']) < 1e-8
    for d, s in zip(datasets, states))

for name, path in {
    'impact_i02a': 'wtc1_simulation_v8/output/impact_i02a_structured_wing/release_audit.json',
    'impact_i01': 'wtc1_simulation_v8/output/impact_i01_first_contact/release_audit.json',
    'impact_i02_geom': 'wtc1_3d_v4/output/impact_i02_geom/final/release_audit.json',
}.items():
    checks[name + '_preserved'] = preserved_release(ROOT / path)
for name in ('v11f_panel_coupling', 'v11r_integrated_panel'):
    old_manifest = read(ROOT / 'wtc1_simulation_v8/output' / name / 'offline_manifest.json')
    preserved = []
    for key, value in old_manifest.items():
        if 'sha256' not in key or not isinstance(value, dict):
            continue
        for path, digest in value.items():
            target = ROOT / 'wtc1_simulation_v8/output' / name / path if key == 'output_sha256' else ROOT / path
            if name in str(target) or ('v11f_' in str(target) if name.startswith('v11f') else 'v11r_' in str(target)):
                preserved.append(target.is_file() and sha(target) == digest)
    checks[name + '_preserved'] = bool(preserved) and all(preserved)
    records[name + '_hash_count'] = len(preserved)

artifacts = [
    ROOT / 'wtc1_simulation_v8/data/impact_i02b_joint_coupon.json',
    *[ROOT / 'wtc1_simulation_v8/scripts' / f'{p}_impact_i02b.py' for p in ('run', 'audit', 'present', 'release')],
    *[SIM / p for p in ('campaign_audit.json', 'source_manifest.json', 'presentation.json', 'rapport_impact_i02b.md', 'synthese_impact_i02b.png')],
    ROOT / 'harness/handoffs/WTC1_IMPACT_I02B_HANDOFF.md',
    ROOT / 'wtc1_3d_v4/scripts/export_i02a_paraview_i02b.py',
    *[VIEW / p for p in ('I02A_solver_states_ms.pvd', 'transfer_audit.json', 'README.md')],
    RENDER / 'I02A_etats_verifies.mp4', RENDER / 'encoding.log',
]
checks['all_release_artifacts_exist'] = all(p.is_file() for p in artifacts)
checks['report_and_handoff_substantive'] = (SIM / 'rapport_impact_i02b.md').stat().st_size > 5000 and (ROOT / 'harness/handoffs/WTC1_IMPACT_I02B_HANDOFF.md').stat().st_size > 1000

pwsh = r'C:\Program Files\PowerShell\7\pwsh.exe'
command = '& ./harness/tools/Test-WtcHarness.ps1 | ConvertTo-Json -Depth 6 -Compress'
process = subprocess.run([pwsh, '-NoProfile', '-Command', command], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
(SIM / f'harness_{args.phase}.log').write_text(process.stdout + process.stderr, encoding='utf-8')
try:
    harness = json.loads(process.stdout)
except json.JSONDecodeError:
    harness = {'Status': 'FAIL', 'raw': process.stdout}
checks['harness_pass'] = process.returncode == 0 and harness.get('Status') == 'PASS'
state = read(ROOT / 'harness/state.json')
registry = [json.loads(line) for line in (ROOT / 'harness/experiments/registry.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
registered = sum(r.get('experiment_id') == 'WTC1-IMPACT-I02B' for r in registry)
if args.phase == 'pre_state':
    checks['pre_state_route'] = state['current_iteration'] == 'IMPACT-I02A' and state['next_iteration'] == 'IMPACT-I02B'
    checks['pre_registry_absent'] = registered == 0 and len(registry) == 100
else:
    pre = read(SIM / 'release_audit_pre_state.json')
    checks['pre_state_audit_pass_and_artifacts_unchanged'] = pre['delivery_status'] == 'PASS' and hashes_match(pre['artifact_sha256'])
    checks['post_state_route'] = state['current_iteration'] == 'IMPACT-I02B' and state['next_iteration'] == 'IMPACT-I02C'
    checks['post_registry_once'] = registered == 1 and len(registry) == 101
    checks['post_state_qualification_matches'] = state['impact_i02b_key_results']['accepted_cases'] == 13 and not state['impact_i02b_key_results']['physical_boeing_joint_qualification']

result = {
    'phase': args.phase, 'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    'delivery_status': 'PASS' if all(checks.values()) else 'FAIL',
    'meaning': 'Uniaxial connector numerical verification and cached I02A media transfer; not physical Boeing joint, mixed-mode, spatial convergence or WTC1 impact validation.',
    'checks': checks, 'records': records, 'harness': harness,
    'artifact_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in artifacts},
}
target = SIM / ('release_audit.json' if args.phase == 'post_state' else 'release_audit_pre_state.json')
target.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': result['delivery_status'], 'checks': len(checks), 'failed': [k for k, v in checks.items() if not v], 'records': records, 'harness': harness}, indent=2))
sys.exit(0 if all(checks.values()) else 1)
