"""Prepare, render and audit an immutable V10Y case as a Blender derivative.

Stages are explicit so the preview can be inspected before rendering video.
This runner never changes the harness state or experiment registry.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import importlib.util
import json
import math
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'wtc1_simulation_v8/data/v10z_blender_exploratory_visualization.json'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def stamp():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def record(path):
    return {'path': str(path.relative_to(ROOT)).replace('\\', '/') if path.is_relative_to(ROOT) else str(path),
            'sha256': digest(path), 'size_bytes': path.stat().st_size}


def paths(config):
    return {key: ROOT / value for key, value in config['outputs'].items()}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def verified(entries):
    rows = []
    for entry in entries:
        path = ROOT / entry['path']
        row = {**entry, **record(path)}
        row['hash_match'] = row['sha256'] == entry['expected_sha256']
        rows.append(row)
    require(all(r['hash_match'] for r in rows), 'Regression/source identity changed')
    return rows


def interpolate_motion(events, relative_time):
    """Reconstruct each V10Y constant-force interval, including momentum jumps."""
    times = [e['relative_time_s'] for e in events]
    index = max(0, bisect.bisect_right(times, relative_time) - 1)
    start = events[index]
    if index == len(events) - 1:
        return {**start, 'model_time_s': times[-1]}
    end = events[index + 1]
    dt = end['relative_time_s'] - start['relative_time_s']
    distance = end['upper_block_drop_m'] - start['upper_block_drop_m']
    a = 2 * (distance - start['velocity_m_s'] * dt) / (dt * dt)
    elapsed = max(0.0, relative_time - start['relative_time_s'])
    return {**start, 'model_time_s': relative_time,
            'upper_block_drop_m': start['upper_block_drop_m'] + start['velocity_m_s'] * elapsed + 0.5 * a * elapsed**2,
            'velocity_m_s': start['velocity_m_s'] + a * elapsed,
            'crush_front_floor': start['crush_front_floor'],
            'within_story_fraction': (start['velocity_m_s'] * elapsed + 0.5 * a * elapsed**2) / distance}


def prepare(config, out):
    require(not out['selected_driver'].exists(), 'Prepared driver already exists; reuse the prepared stage')
    started = time.perf_counter()
    upstream = load(ROOT / config['regression_files'][0]['path'])
    regressions = verified(config['regression_files'] + config['protected_files'] + config['software_files'])
    upstream_files = verified(upstream['regression_files'] + upstream['protected_files'])
    spec = importlib.util.spec_from_file_location('v10y_readonly_replay', ROOT / config['regression_files'][1]['path'])
    model = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model)
    with (ROOT / config['regression_files'][2]['path']).open(encoding='utf-8-sig', newline='') as f:
        grid = list(csv.DictReader(f))
    selection = config['selection']
    sid = selection['scenario_id']
    scenario = next(row for row in model.grid_scenarios(upstream) if row['scenario_id'] == sid)
    cached = next(row for row in grid if row['scenario_id'] == sid)
    temp = model.build_temperature_index(model.read_csv(ROOT / upstream['documented_inputs']['temperature_envelopes']['path']))
    damage_item = next(x for x in upstream['regression_files'] if x['role'] == 'v10p_damage_matrix')
    damage = model.build_core_damage_retention(model.read_csv(ROOT / damage_item['path']), upstream)
    summary, capacity, ledger, events = model.simulate_scenario(scenario, upstream, temp, damage, True)
    comparisons = []
    for key, value in summary.items():
        cached_value = cached[key]
        actual = None if cached_value == '' else cached_value
        if isinstance(value, bool):
            passed = str(value) == actual
        elif isinstance(value, (int, float)):
            passed = float(actual) == float(value)
        else:
            passed = actual == value
        comparisons.append({'field': key, 'cached': cached_value, 'replayed': value, 'pass': passed})
    require(all(x['pass'] for x in comparisons), 'Selected V10Y row did not replay exactly')
    progressing = [r for r in grid if r['outcome_label'] == selection['expected_outcome']]
    target = selection['observed_chronology_comparison_s']
    minimum_error = min(abs(float(r['initiation_time_s_after_impact']) - target) for r in progressing)
    ties = [r['scenario_id'] for r in progressing if abs(float(r['initiation_time_s_after_impact']) - target) == minimum_error]
    require(sid in ties, 'Selected case is not in the closest-time group')
    require(summary['initiation_time_s_after_impact'] == selection['expected_initiation_time_s_after_impact'], 'Unexpected initiation time')
    require(summary['collapse_duration_s'] == selection['expected_collapse_duration_s'], 'Unexpected propagation duration')
    require(len(events) == config['expected']['selected_scenario_event_count'], 'Unexpected event count')
    v = config['visual_contract']
    t0 = summary['initiation_time_s_after_impact']
    h = upstream['documented_inputs']['tower']['upper_office_story_height_m']
    upper_bottom = (summary['initiation_floor'] - upstream['exploratory_model']['initial_upper_block_floor_equivalent_offset']) * h
    capacity_by_time = {}
    for row in capacity:
        capacity_by_time.setdefault(row['time_s'], []).append(row)
    frames = []
    for frame in range(v['frame_start'], v['frame_end'] + 1):
        if frame <= v['thermal_end_frame']:
            thermal_time = math.floor((t0 - 10) * (frame - 1) / (v['thermal_end_frame'] - 1) / 10) * 10.0
            phase = 'IMPACT_DAMAGE_INPUT' if frame == 1 else 'THERMAL_FAST_FORWARD'
            motion = {'upper_block_drop_m': 0.0, 'velocity_m_s': 0.0, 'moving_mass_kg': 0.0, 'crush_front_floor': None, 'model_time_s': None}
        elif frame < v['collapse_start_frame']:
            thermal_time, phase = t0, 'CAPACITY_INITIATION_BEFORE_ASSUMED_DROP'
            motion = {'upper_block_drop_m': 0.0, 'velocity_m_s': 0.0, 'moving_mass_kg': summary['initial_upper_block_mass_kg'], 'crush_front_floor': summary['initiation_floor'], 'model_time_s': None}
        else:
            thermal_time, phase = t0, 'REDUCED_MODEL_PROPAGATION'
            rel_time = min((frame - v['collapse_start_frame']) / v['fps'], events[-1]['relative_time_s'])
            motion = interpolate_motion(events, rel_time)
            if rel_time == events[-1]['relative_time_s']:
                phase = 'FINAL_MODEL_EVENT_NOT_SETTLED_DEBRIS'
        controlling = max(capacity_by_time[thermal_time], key=lambda r: r['demand_over_capacity'])
        frames.append({'frame': frame, 'phase': phase, 'thermal_sample_time_s': thermal_time,
                       'time_after_impact_s': thermal_time + (motion['model_time_s'] or 0.0),
                       'controlling_floor': controlling['floor'], 'controlling_dcr': controlling['demand_over_capacity'],
                       'selected_truss_temperature_c_by_floor': {str(r['floor']): r['floor_truss_temperature_selected_c'] for r in capacity_by_time[thermal_time]},
                       'upper_block_bottom_z_m': upper_bottom - motion['upper_block_drop_m'], **motion})
    transition_checks = []
    for i in range(len(events) - 1):
        a, b = events[i:i+2]
        dt = b['relative_time_s'] - a['relative_time_s']
        distance = b['upper_block_drop_m'] - a['upper_block_drop_m']
        acc = 2 * (distance - a['velocity_m_s'] * dt) / dt**2
        pre_accretion_v = a['velocity_m_s'] + acc * dt
        after_v = pre_accretion_v * a['moving_mass_kg'] / b['moving_mass_kg']
        transition_checks.append(abs(after_v - b['velocity_m_s']))
    require(max(transition_checks) < 1e-8, 'Between-event trajectory does not reproduce V10Y momentum changes')
    audit = {'iteration': 'V10Z', 'created_at': stamp(), 'status': 'PASS_SELECTED_DRIVER_EXACT_REPLAY',
             'field_checks': comparisons, 'field_check_count': len(comparisons),
             'closest_progressing_tie_count': len(ties), 'closest_progressing_case_ids': ties,
             'minimum_absolute_initiation_error_s': minimum_error,
             'max_between_event_end_velocity_error_m_s': max(transition_checks),
             'event_count': len(events), 'frame_count': len(frames),
             'max_energy_residual': summary['maximum_normalized_energy_residual'],
             'elapsed_s': time.perf_counter() - started}
    driver = {'iteration': 'V10Z', 'status': 'EXPLORATORY_VISUALIZATION_DRIVER_NOT_VALIDATED_DYNAMICS',
              'configuration': record(CONFIG), 'source_runner': record(ROOT / config['regression_files'][1]['path']),
              'scenario': scenario, 'summary': summary, 'events': events, 'energy_ledger': ledger, 'frames': frames,
              'geometry': {'story_height_m': h, 'uniform_model_roof_height_m': 110 * h,
                           'upper_block_original_bottom_m': upper_bottom,
                           'display_mass_geometry_coupling': 'NONE: deleted level visuals remain in numerical moving mass'},
              'initial_drop_duration_included_in_reported_propagation_time': False,
              'initial_freefall_equivalent_time_s_diagnostic_only': math.sqrt(2 * events[0]['upper_block_drop_m'] / upstream['exploratory_model']['gravity_m_s2']),
              'initial_mass_plus_accreted_mass_floor_equivalents': summary['final_moving_mass_kg'] / scenario['floor_mass_kg'],
              'omitted_initial_floor_mass_equivalents_in_v10y': 110 - summary['final_moving_mass_kg'] / scenario['floor_mass_kg'],
              'permanent_banner': v['permanent_banner']}
    write(out['regression_audit'], {'iteration': 'V10Z', 'created_at': stamp(), 'files': regressions, 'upstream_input_files': upstream_files, 'all_pass': True})
    write(out['selected_driver'], driver)
    write(out['driver_audit'], audit)
    write(out['source_manifest'], {'iteration': 'V10Z', 'created_at': stamp(), 'configuration': record(CONFIG),
                                 'runner': record(Path(__file__)), 'builder': record(out['blender_builder_script']),
                                 'inputs': regressions, 'upstream_inputs': upstream_files,
                                 'epistemic_policy': config['epistemic_policy'], 'network_access': False})
    print(json.dumps({k: audit[k] for k in ['status', 'field_check_count', 'closest_progressing_tie_count', 'event_count', 'frame_count']}, ensure_ascii=False))


def blender_stage(config, out, stage):
    scratch = ROOT / config['scratch_directory']
    scratch.mkdir(parents=True, exist_ok=True)
    marker = scratch / f'{stage}_execution.json'
    require(not marker.exists(), f'{stage} already ran; inspect its outputs before any retry')
    source = ROOT / config['protected_files'][0]['path'] if stage == 'preview' else scratch / 'preview.blend'
    command = [config['software_files'][0]['path'], '--background', str(source), '--threads', '4',
               '--python-exit-code', '1', '--python', str(out['blender_builder_script']), '--', stage]
    started = time.perf_counter()
    logfile = scratch / f'{stage}_blender.log'
    with logfile.open('w', encoding='utf-8') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                timeout=config['execution_policy']['maximum_runtime_seconds'],
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    write(marker, {'iteration': 'V10Z', 'created_at': stamp(), 'stage': stage, 'command': command,
                   'return_code': result.returncode, 'elapsed_s': time.perf_counter() - started,
                   'configuration': record(CONFIG), 'builder': record(out['blender_builder_script']), 'log': record(logfile)})
    require(result.returncode == 0, f'Blender {stage} failed; see {logfile}')
    print(marker.read_text(encoding='utf-8'))


def proof_sheet(config, out):
    v = config['visual_contract']
    paths_to_images = [out['render_directory'] / f'{i+1:02d}_{label}.png' for i, label in enumerate(v['still_labels'])]
    sheet = Image.new('RGB', (1536, 1296), '#101b2b')
    for i, path in enumerate(paths_to_images):
        with Image.open(path) as im:
            require(list(im.size) == v['resolution_px'], f'Wrong image size: {path}')
            sheet.paste(im.convert('RGB'), ((i % 2) * 768, (i // 2) * 432))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 23)
    except OSError:
        font = ImageFont.load_default(size=23)
    text = ('WTC 1 | V10Z\n\nGRID-0119 : exemple sélectionné parmi les ex aequo.\n'
            'Initiation : 96 min 50 s après impact.\nÉcart à la référence : 5 min 04 s en avance.\n'
            'Progression après chute initiale : 14,13 s.\n\n'
            'Le modèle suppose la chute initiale de 1,83 m.\n'
            'Les niveaux disparus restent dans la masse calculée.\n'
            'Le résidu final ne représente pas des débris calculés.\n\n'
            'V10Y contient aussi des cas sans initiation et avec arrêt.\n'
            'Ces résultats dépendent des hypothèses du modèle.')
    draw.multiline_text((802, 890), text, font=font, fill='#dfebfa', spacing=7)
    sheet.save(out['proof_sheet'])
    return paths_to_images


def finalize(config, out):
    require(not out['results'].exists(), 'Completed V10Z cannot be overwritten')
    driver, audit = load(out['selected_driver']), load(out['driver_audit'])
    manifest, qa = load(out['blender_internal_manifest']), load(out['visual_qa'])
    verified(config['regression_files'] + config['protected_files'] + config['software_files'])
    require(qa['status'] == 'PASS', 'Manual visual review still pending')
    for item in qa['reviewed_files']:
        require(digest(ROOT / item['path']) == item['sha256'], 'Reviewed file changed')
    images = proof_sheet(config, out) if not out['proof_sheet'].exists() else [out['render_directory'] / f'{i+1:02d}_{label}.png' for i, label in enumerate(config['visual_contract']['still_labels'])]
    criteria = {'exact_driver_replay': audit['status'] == 'PASS_SELECTED_DRIVER_EXACT_REPLAY',
                'master_unchanged': manifest['master_unchanged'], 'video_decoded': manifest['video']['decoded'],
                'video_frame_count': manifest['video']['frame_duration'] == config['visual_contract']['frame_end'],
                'video_dimensions': manifest['video']['dimensions_px'] == config['visual_contract']['resolution_px'],
                'all_baked_frame_positions_match_driver': manifest['animation_audit']['maximum_position_error_m'] < 1e-4,
                'no_blender_physics': manifest['animation_audit']['physics_object_count'] == 0,
                'keyframes_present': manifest['animation_audit']['keyframe_count'] >= 100,
                'manual_visual_review': qa['status'] == 'PASS'}
    require(all(criteria.values()), f'V10Z criteria failed: {criteria}')
    summary = driver['summary']
    rendered = [{'frame': frame, **record(path)} for frame, path in zip(config['visual_contract']['still_frames'], images)]
    write(out['render_manifest'], {'iteration': 'V10Z', 'images': rendered, 'proof_sheet': record(out['proof_sheet']), 'video': record(out['video'])})
    gate = {'iteration': 'V10Z', 'created_at': stamp(), 'decision': 'PASS_LABELLED_EXPLORATORY_DRIVER_VISUALIZATION',
            'criteria': criteria, 'physical_validation': False, 'documentary_requirement_closure_count': 0,
            'scientific_validation_claim_count': 0}
    write(out['handoff_gate'], gate)
    scratch = ROOT / config['scratch_directory']
    executions = [load(scratch / f'{stage}_execution.json') for stage in ('preview', 'render')]
    source_manifest = load(out['source_manifest'])
    prepared_builder = record(scratch / 'builder_at_preview.py')
    require(prepared_builder['sha256'] == source_manifest['builder']['sha256'], 'Prepared builder snapshot mismatch')
    source_manifest['builder_at_prepare'] = prepared_builder
    source_manifest['builder'] = record(out['blender_builder_script'])
    source_manifest['runner_at_finalization'] = record(Path(__file__))
    source_manifest['implementation_revision'] = {
        'reason': 'Blender 5.2 requires image_settings.media_type=VIDEO before selecting FFMPEG.',
        'primary_documentation': 'https://developer.blender.org/docs/release_notes/4.5/pipeline_assets_io/',
        'local_api_verified': True,
        'rejected_encoding_setup': record(scratch / 'rejected_render_01/render_execution.json'),
        'prior_framing_preview': record(ROOT / 'tmp/v10z_attempt_01/preview_execution.json'),
        'physical_model_changes': 0,
        'accepted_blender_execution_count': 2,
        'rejected_preview_count': 1,
        'rejected_encoding_setup_count': 1,
        'read_only_blender_api_probe_count': 2,
        'design_research_network_access': True,
        'render_execution_network_access': False
    }
    write(out['source_manifest'], source_manifest)
    out['blender_execution_log'].write_text('\n\n'.join((scratch / f'{stage}_blender.log').read_text(encoding='utf-8') for stage in ('preview', 'render')), encoding='utf-8')
    report = f'''# WTC 1 — V10Z : première animation pilotée par V10Y

Statut : **visualisation exploratoire opérationnelle**, contrôlée contre le calcul réduit. Le résultat ne constitue pas une validation historique.

Le fichier Blender contient une scène animée de 110 niveaux schématiques et conserve séparément la scène de référence V4.2. La vidéo dure {config['visual_contract']['video_seconds']:.2f} s (220 images à 12 images/s) : les quatre premières secondes accélèrent l'évolution thermique, puis le mouvement suit le temps de propagation du modèle. Les cinq vues de contrôle et la planche permettent une lecture rapide.

## Résultat du scénario

GRID-0119 initie au niveau {summary['initiation_floor']} après {summary['initiation_time_s_after_impact']:.0f} s, soit 96 min 50 s après l'impact. Il est 304 s en avance sur les 6114 s de la chronologie de comparaison. Il appartient à un groupe de {audit['closest_progressing_tie_count']} cas progressants ayant cet écart minimal : ce choix a été effectué après observation de la grille, et n'est ni unique, ni une validation indépendante.

La progression atteint le dernier niveau du modèle après {summary['collapse_duration_s']:.6f} s. La vitesse atteint {summary['maximum_velocity_m_s']:.3f} m/s et la masse mobile finale vaut {summary['final_moving_mass_kg']/1e6:.1f} millions de kg. Cette progression utilise l'énergie gravitationnelle après initiation et les résistances V10Y déclarées. Les autres résultats de la grille restent présents : 288 progressions, 144 arrêts après initiation et 297 cas sans initiation. Ces nombres ne sont pas des probabilités de l'événement réel.

## Ce que représente l'image

La maquette reprend les niveaux uniformes de 3,6576 m de V10Y, soit 402,336 m, tandis que le master V4.2 conserve sa hauteur de référence de 416,9664 m. Le bloc supérieur suit la translation calculée. Les niveaux inférieurs sont masqués au passage des événements de rupture ; leur masse reste dans le bilan d'accrétion du calcul. Leur disparition n'est donc pas une prévision de poussière ou de volume de débris. La couleur de la zone 93–99 code une température d'enveloppe par niveau : la répartition locale des flammes n'est pas calculée.

Les positions entre deux événements sont reconstruites avec l'accélération constante de l'intervalle V10Y. Les pertes de vitesse aux événements suivent l'accrétion inélastique du même calcul. Les positions ont été enregistrées à chacune des 220 images ; l'interpolation à des instants intermédiaires dans Blender sert uniquement à l'affichage. Le fichier fonctionne sans script automatique à son ouverture.

## Limites mises en évidence pendant le transfert

- La première ligne V10Y contient déjà une chute de 1,8288 m et une vitesse non nulle à son temps relatif zéro. Les 14,1263 s excluent donc la durée de cette chute supposée. Son équivalent en chute libre serait {driver['initial_freefall_equivalent_time_s_diagnostic_only']:.4f} s ; ce diagnostic ne la rend pas mécaniquement justifiée.
- La masse initiale plus les étages accré­tés totalise {driver['initial_mass_plus_accreted_mass_floor_equivalents']:.1f} étages équivalents. Un demi-étage du niveau d'initiation n'est pas compté dans V10Y. L'animation conserve cette limite et ne corrige pas silencieusement le calcul.
- L'état final conserve une énergie cinétique élevée ({summary['final_kinetic_energy_j']/1e9:.2f} GJ). Il marque l'arrivée au dernier événement, pas la stabilisation des débris au sol. L'arrêt de la vidéo n'est pas un arrêt mécanique.
- L'impact est représenté par des dommages d'entrée, l'échauffement par des plages dépendantes des calculs officiels, et la propagation par un mécanisme vertical unique. La chaîne n'est pas encore une simulation 3D complète de l'avion, des incendies, des assemblages et de l'effondrement.

## Statut des informations

1. **Faits observés ou transcrits** : identités et empreintes des fichiers, dimensions des médias, chronologie et géométrie héritées des dossiers locaux vérifiés.
2. **Résultats de modèle officiel** : branches de dommages et plages de températures NIST reprises par V10Y.
3. **Affirmations des archives locales** : aucune nouvelle archive inspectée, aucune nouvelle affirmation ajoutée.
4. **Hypothèses propres** : réserve à froid 1,8, quantile thermique 0,55, masse 3,2 millions de kg par étage, résistance de référence 1,2 GJ, demi-hauteur de chute initiale ; autres hypothèses inchangées dans la configuration V10Y.
5. **Résultats dérivés** : rejeu exact de {audit['field_check_count']} champs, {len(driver['events'])} événements, {len(driver['frames'])} poses, animation, vidéo et vues fixes.
6. **Contradictions et inconnues** : avance de 304 s, durée initiale omise, demi-étage manquant, bilan de débris et dynamique latérale non résolus.

## Vérification et reprise

Les contrôles de reproduction, de conservation des sources, des 220 poses, d'ouverture et de métadonnées vidéo et de revue visuelle des cinq vues passent. L'erreur maximale de position enregistrée est {manifest['animation_audit']['maximum_position_error_m']:.3g} m. La maquette ne contient aucun objet de physique Blender. Le master conserve son SHA-256. Le rendu ne renvoie aucune donnée au calcul. Le rapport demande/capacité est arrondi à l'écran : l'affichage 1,0000 juste avant initiation ne remplace pas la valeur exacte du pilote.

Exécution conservée : Python {platform.python_version()}, Blender {manifest['blender_version']}, deux passages Blender acceptés, durée cumulée {sum(e['elapsed_s'] for e in executions):.1f} s. Un aperçu au cadrage insuffisant et une tentative de réglage vidéo interrompue sont conservés dans les dossiers de travail. Deux interrogations locales de l'API ont servi à corriger le format vidéo, dont le changement de sélection est documenté dans les [notes officielles Blender](https://developer.blender.org/docs/release_notes/4.5/pipeline_assets_io/). Configuration, scripts, pilote, manifestes, revue et bilans sont conservés.

Prochaine priorité : corriger le raccord initiation–propagation, fermer l'inventaire de masse et traiter les forces résistantes dès le premier déplacement ; ensuite introduire les chemins d'efforts spatiaux noyau/façades/planchers. Ce transfert fournit un premier résultat visible et révèle les simplifications qui influencent le verdict.
'''
    out['report'].write_text(report, encoding='utf-8')
    result = {'iteration': 'V10Z', 'created_at': stamp(), 'decision': gate['decision'], 'selected_scenario': driver['scenario'],
              'summary': summary, 'closest_progressing_tie_count': audit['closest_progressing_tie_count'],
              'initial_drop_duration_excluded': True, 'omitted_floor_mass_equivalents': driver['omitted_initial_floor_mass_equivalents_in_v10y'],
              'checks': criteria, 'blender_version': manifest['blender_version'], 'executions': executions,
              'artifacts': {k: record(p) for k, p in out.items() if p.is_file() and k not in ['results', 'offline_audit']},
              'preserved_execution_revisions': source_manifest['implementation_revision'],
              'physical_validation': False, 'scientific_validation_claim_count': 0, 'next_iteration': config['next_iteration']}
    write(out['results'], result)
    write(out['offline_audit'], {'iteration': 'V10Z', 'status': 'PASS', 'created_at': stamp(),
                                'artifacts': [record(p) for k, p in out.items() if p.is_file() and k != 'offline_audit'],
                                'source_master_unchanged': True})
    print(json.dumps({'decision': gate['decision'], 'criteria': criteria, 'report': str(out['report'])}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'preview', 'render', 'proof', 'finalize'])
    args = parser.parse_args()
    config = load(CONFIG)
    out = paths(config)
    if args.stage == 'prepare':
        prepare(config, out)
    elif args.stage in ['preview', 'render']:
        blender_stage(config, out, args.stage)
    elif args.stage == 'proof':
        proof_sheet(config, out)
    else:
        finalize(config, out)


if __name__ == '__main__':
    main()
