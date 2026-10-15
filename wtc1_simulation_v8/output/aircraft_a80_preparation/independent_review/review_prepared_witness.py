"""Independent static review of prepared A81 decks, without any native run."""
from pathlib import Path
import datetime
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PREP = ROOT / 'tmp/aircraft_a80_contact_path/witness_preparation'
NAME = 'A81_COHESIVE_COMPRESSION_PARTIAL_OPEN_RECLOSE'
BASE = ROOT / 'wtc1_simulation_v8/output/aircraft_a67/native/FREE_Ismstr4'
WHOLE = ROOT / 'wtc1_simulation_v8/output/aircraft_a79/SELF_PAIR_PRINT/A79_SELF_PAIR_PRINT_0000.rad'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def blocks(p):
    d, key = {}, None
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('/'):
            key = line
            assert key not in d
            d[key] = []
        elif key and line.strip() and not line.startswith('#'):
            d[key].append(line)
    return d


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def rel(p):
    return p.relative_to(ROOT).as_posix()


def main():
    destination = HERE / 'independent_static_witness_review.json'
    assert not destination.exists(), 'Never overwrite an earlier review.'
    configpath = PREP / 'configuration_A81_proposed.json'
    p0, p1 = [PREP / (NAME + suffix) for suffix in ['_0000.rad', '_0001.rad']]
    base0, base1 = [BASE / ('A67_FREE_Ismstr4' + suffix) for suffix in ['_0000.rad', '_0001.rad']]
    old_native_listing = BASE / 'A67_FREE_Ismstr4_0000.out'
    inputs = [configpath, p0, p1, base0, base1, WHOLE, old_native_listing,
        ROOT / 'wtc1_simulation_v8/scripts/review_aircraft_a67_current_area.py']
    before = {rel(p): sha(p) for p in inputs}
    c, d, e, b, be, w = read(configpath), blocks(p0), blocks(p1), blocks(base0), blocks(base1), blocks(WHOLE)
    native_text = old_native_listing.read_text(errors='replace')
    samples = [tuple(map(float, line.split())) for line in d['/FUNCT/92'][1:]]
    knots = c['load']['knots_ms_mm']

    def reference(t):
        for (a, x), (z, y) in zip(knots, knots[1:]):
            if t <= z:
                q = min(1., max(0., (t - a) / (z - a)))
                return x + (y - x) * (q ** 3 * (10 + q * (-15 + 6 * q)))
        return knots[-1][1]

    error = max(abs(x - reference(t)) for t, x in samples)
    h = c['time']['TH_ms']; dt = c['time']['dt_cap_ms']
    times = [t for t, _ in samples]
    func = dict(samples)
    groups = {int(key.rsplit('/', 1)[1]): [int(n) for l in vals[1:] for n in l.split()]
        for key, vals in d.items() if key.startswith('/GRNOD/NODE/')}
    imp = d['/IMPDISP/92'][1]
    nodes = {int(l[:10]): list(map(float, l[10:].split())) for l in d['/NODE']}
    bottom = [nodes[n] for n in [1, 2, 3, 4]]
    normal = (0., 0., 1.)
    material_numeric_exact = d['/MAT/LAW117/1'][1:] == w['/MAT/LAW117/117'][1:] == b['/MAT/LAW117/1'][1:]
    property_numeric_exact = d['/PROP/TYPE43/1'][1:] == w['/PROP/TYPE43/117'][1:] == b['/PROP/TYPE43/1'][1:]
    compression_plateau = [x for t, x in samples if .08 <= t <= .10]
    reopening_plateau = [x for t, x in samples if .4 <= t <= .42]
    reclosed_plateau = [x for t, x in samples if .62 <= t <= .65]
    checks = {
        'prepared_hashes_match_configuration': all(sha(PREP / row['path']) == row['sha256'] for row in c['inputs']),
        'LAW117_numeric_card_exact_current_A79_and_A67': material_numeric_exact,
        'TYPE43_numeric_card_exact_current_A79_and_A67': property_numeric_exact,
        'eight_nodes_and_ordered_brick_equal_A67': d['/NODE'] == b['/NODE'] and d['/BRICK/1'] == b['/BRICK/1'],
        'coincident_square_faces_area100_normal_positive_Z': bottom == [[0., 0., 0.], [10., 0., 0.], [10., 10., 0.], [0., 10., 0.]] and [nodes[n] for n in [5, 6, 7, 8]] == bottom,
        'instrument_ADMAS_exact_A67_8g': d['/ADMAS/5/1'] == b['/ADMAS/5/1'] and sum(float(l[:20]) for l in d['/ADMAS/5/1'][1:]) == 8,
        'bottom_fixed_and_top_rotations_fixed_XY_unconstrained': d['/BCS/1'] == b['/BCS/1'] and d['/BCS/2'] == b['/BCS/2'] and c['load']['top_XY_free'],
        'only_imposed_translation_is_top_Z_with_unit_scales': [key for key in d if key.startswith('/IMPDISP/')] == ['/IMPDISP/92'] and imp[10:20].strip() == 'Z' and int(imp[:10]) == 92 and groups[int(imp[40:50])] == [5, 6, 7, 8] and list(map(float, d['/IMPDISP/92'][2].split())) == [1., 1., 0., 1e30],
        'no_initial_velocity_or_general_contact': not any(key.startswith(('/INIVEL/', '/INTER/')) for key in d),
        'FUNCT_matches_declared_C2_samples_to_decimal_precision': error < 5e-12,
        'FUNCT_time_axis_strict_and_half_dt_sampled': all(z > a and abs((z - a) - h) < 1e-13 for a, z in zip(times, times[1:])) and times[0] == 0 and times[-1] == .651 and h == dt / 2,
        'specified_negative_positive_negative_sequence_exact_at_knots': all(abs(func[t] - x) < 5e-12 for t, x in knots),
        'intact_compression_hold_minus005_present': len(compression_plateau) > 100 and all(x == -.05 for x in compression_plateau),
        'opening_hold_plus03_present': len(reopening_plateau) > 100 and all(x == .3 for x in reopening_plateau),
        'reclosure_hold_minus005_present': len(reclosed_plateau) > 100 and all(x == -.05 for x in reclosed_plateau),
        'all_openings_below_half_mm_nominal_gap': max(x for _, x in samples) == .3 < .5,
        'Newmark_linear_solver_nonlinear_limits_exact_A67': all(e[key] == be[key] for key in ['/IMPL/DYNA/2', '/IMPL/SOLVER/2', '/IMPL/NONLIN/1']),
        'fixed_dt_or_stop_matches_configuration': list(map(float, e['/IMPL/DT/STOP'][0].split())) == [dt, dt] and float(e['/IMPL/DTINI'][0]) == dt == .000125,
        'RUN_target_and_TH_ANIM_timing_consistent': float(e[f'/RUN/{NAME}/1'][0]) == c['time']['RUN_stop_ms'] == c['time']['target_ms'] + dt / 2 and float(e['/TFILE/4'][0]) == h and list(map(float, e['/ANIM/DT'][0].split())) == [0., h],
        'only_bounded_two_native_processes_proposed': c['maximum_native_processes'] == 2 and c['Starter'] == c['Engine_conditional'] == c['cpu'] == 1 and c['each_cap_s'] == 180 and not any(c[key] for key in ['GPU', 'source_patch', 'compile', 'installation', 'whole_impact_extension']),
        'all_inspected_inputs_unchanged': all(sha(ROOT / p) == hash_value for p, hash_value in before.items()),
    }
    review = {
        'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'pass_static_preparation_review_only': all(checks.values()), 'checks': checks,
        'maximum_FUNCT_reference_difference_mm': error, 'FUNCT_sample_count': len(samples), 'normal_initial': normal,
        'existing_A67_native_readback_only': {'material_criterion': 1, 'damage_evolution': 1, 'ISYM': 0,
            'normal_failure_displacement_mm': 2 * 50 / 450,
            'source': rel(old_native_listing), 'one_based_lines': [188, 190, 199, 205, 208, 213],
            'this_is_not_an_A81_Starter_readback': True},
        'conditional_pure_mode_I_reference': {'delta_initiation_mm': 450 / 4400, 'delta_failure_mm': 2 * 50 / 450,
            'intact_compression_support_force_at_minus005_N': 22000., 'normal_tension_peak_force_N': 45000.,
            'fracture_work_Nmm': 5000., 'fracture_work_J': 5., 'elastic_compression_energy_Nmm': 550., 'elastic_compression_energy_J': .55,
            'conditions': ['native criterion1 and linear evolution1 and ISYM0', 'measured pure normal separation', 'constant100mm2 projected current area',
                'no per_GP deletion or missing user output inferred solely from the imposed displacement'],
            'delta03_does_not_by_itself_certify_rupture_or_damage': True},
        'native_gates_required_before_interpreting_result': {
            'Starter': ['normal exit and classified zero error/warning gate', 'native material EN ET TN TT GI GII defaults criterion evolution ISYM and TYPE43 readback', 'mass8g and no added mass', 'all references valid'],
            'output_observability': ['all actual accepted steps and actual target state, not interpolation count', 'TH binary and CSV data agree; node and element labels bind',
                'confirm whether USR fields are populated for TYPE43; absent or zero generic fields do not establish zero damage',
                'record OFF and integration-point failure messages independently; distinguish deleted fields from repaired or healed state'],
            'measured_mode_I_and_geometry': ['fixed bottom', 'uniform top_Z matches actual imposed time series', 'top XY drift and tangential slips remain within predeclared precision/physical bounds',
                'all4 Gauss projected areas stay positive and sum100mm2; normal remains positiveZ', 'off-axis stress is negligible, otherwise scalar pure-mode reference is inapplicable'],
            'compression_before_opening': ['use bottom support impulse slope on .08-.10ms hold; expected signed force is positive22000N in ordinary support convention',
                'preserve A67 force comparison tolerance2percent unless a separately declared criterion is justified', 'no initial spurious impulse or energy'],
            'rupture_and_reclosure': ['certify rupture by native damage/status or4 integration-point failure messages, never delta03 alone',
                'measure bottom impulse slope on .62-.65ms hold and compare with initial identical compression',
                'zero or deficient post-rupture compression while nominal gap never exited rejects WAITING-until-gap-exit policy; a completed witness is still an observation success',
                'do not infer contact qualification from a model containing no contact'],
            'balances': ['REAC exported in A67 was cumulative impulse, not instantaneous force; validate semantics again',
                'sum all external impulses versus measured momentum', 'subtract prescribed top inertia using measured acceleration; bottom reaction avoids that inertia',
                'external work versus kinetic plus internal/dissipated energy; keep erosion/deletion and mass changes explicit',
                'units: native impulse times0.001 givesNs; energy times0.001 givesJ; g*mm/ms2 givesN'],
        },
        'static_caveats': ['top_XY_free preserves dynamic unknowns but native pure-mode gates remain required',
            'sampled quintic trajectory is piecewise linear in native FUNCT; it is not an exact continuously differentiable prescription',
            'the related source compression stress branch does not prove a deleted element continues to transmit compression',
            'A67 controls cover small elastic motions; they do not validate this new irreversible loop'],
        'new_native': 0, 'existing_or_sealed_artifact_modified': False, 'physical_qualification': False,
        'authorization_already_granted_by_this_review': False,
        'inputs': [{'path': path, 'sha256': hash_value} for path, hash_value in before.items()],
        'reviewer': {'path': rel(Path(__file__)), 'sha256': sha(Path(__file__))},
    }
    with destination.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(review, f, ensure_ascii=True, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({'pass_static': review['pass_static_preparation_review_only'], 'checks': checks,
        'samples': len(samples), 'FUNCT_max_error_mm': error, 'new_native': 0}, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
