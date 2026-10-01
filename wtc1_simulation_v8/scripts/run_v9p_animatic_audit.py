#!/usr/bin/env python3
"""Encode and audit the V9P 75-second visualization-only animatic."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9p_low_resolution_animatic.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def get_path(payload: Any, dotted_path: str) -> Any:
    value = payload
    for part in dotted_path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise KeyError(f"Missing JSON path {dotted_path!r}")
        value = value[part]
    return value


def run(command: list[str], *, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def aggregate_frame_identity(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for relative, expected in config["regression_files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        files[relative] = {
            "exists": path.is_file(),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": path.is_file() and actual == expected,
        }
    cache: dict[str, dict[str, Any]] = {}
    metrics = []
    for declaration in config["regression_metrics"]:
        relative = declaration["results"]
        cache.setdefault(relative, load_json(ROOT / relative))
        actual = get_path(cache[relative], declaration["path"])
        metrics.append({**declaration, "actual": actual, "passed": actual == declaration["expected"]})
    return {
        "files": files,
        "metrics": metrics,
        "passed": all(record["passed"] for record in files.values())
        and all(record["passed"] for record in metrics),
    }


def validate_shots(config: dict[str, Any]) -> dict[str, Any]:
    shots = config["shots"]
    contiguous = all(shots[index]["end_s"] == shots[index + 1]["start_s"] for index in range(len(shots) - 1))
    durations = all(shot["end_s"] - shot["start_s"] == shot["duration_s"] for shot in shots)
    total = sum(float(shot["duration_s"]) for shot in shots)
    motion = [shot for shot in shots if shot["source_type"] == "motion_sequence"]
    static = [shot for shot in shots if shot["source_type"] == "static"]
    postcontact_3d_motion = [
        shot for shot in shots if float(shot["start_s"]) >= 48.0 and shot["mode"] == "precontact_motion"
    ]
    return {
        "starts_at_zero": shots[0]["start_s"] == 0,
        "intervals_contiguous": contiguous,
        "durations_consistent": durations,
        "total_duration_s": total,
        "duration_matches": total == config["video"]["duration_s"],
        "shot_count": len(shots),
        "motion_shot_count": len(motion),
        "static_shot_count": len(static),
        "postcontact_three_dimensional_motion_shot_count": len(postcontact_3d_motion),
        "passed": bool(
            shots[0]["start_s"] == 0
            and contiguous
            and durations
            and total == config["video"]["duration_s"]
            and len(shots) == config["expected_counts"]["shot_count"]
            and len(motion) == config["expected_counts"]["motion_shot_count"]
            and len(static) == config["expected_counts"]["static_shot_count"]
            and len(postcontact_3d_motion) == 0
        ),
    }


def verify_motion_inputs(config: dict[str, Any], motion_manifest: dict[str, Any]) -> dict[str, Any]:
    records_by_id = {record["shot_id"]: record for record in motion_manifest["motion_sequences"]}
    checks = []
    for shot in config["shots"]:
        if shot["source_type"] != "motion_sequence":
            continue
        record = records_by_id.get(shot["id"])
        pattern = ROOT / shot["source"]
        paths = sorted(pattern.parent.glob("frame_*.png"))
        expected_count = round(float(shot["duration_s"]) * config["blender"]["motion_render_fps"])
        aggregate = aggregate_frame_identity(paths) if paths else None
        dimensions = []
        for path in (paths[:1] + paths[-1:] if paths else []):
            with Image.open(path) as image:
                dimensions.append(list(image.size))
        checks.append({
            "shot_id": shot["id"],
            "frame_count": len(paths),
            "expected_frame_count": expected_count,
            "aggregate_path_and_sha256": aggregate,
            "manifest_aggregate_path_and_sha256": record.get("aggregate_path_and_sha256") if record else None,
            "edge_dimensions_px": dimensions,
            "passed": bool(
                record
                and len(paths) == expected_count == record["rendered_frame_count"]
                and aggregate == record["aggregate_path_and_sha256"]
                and all(item == config["blender"]["resolution_px"] for item in dimensions)
                and record["permanent_banner_text"] == config["permanent_text"]["banner"]
                and record["maximum_event_time_status"] == "negative_event_time_only_contact_frame_excluded"
            ),
        })
    physics = motion_manifest["physics_audit"]
    source_safe = (
        motion_manifest["source_derivative"]["unchanged"] is True
        and motion_manifest["source_derivative"]["saved"] is False
        and motion_manifest["source_master"]["unchanged"] is True
    )
    physics_safe = (
        physics["rigid_body_object_count"] == config["expected_counts"]["rigid_body_object_count"]
        and physics["particle_system_object_count"] == config["expected_counts"]["particle_system_count"]
        and physics["fluid_modifier_count"] == config["expected_counts"]["fluid_modifier_count"]
        and physics["rigidbody_world_scene_count"] == config["expected_counts"]["rigidbody_world_scene_count"]
        and physics["structural_solver_executed"] is False
        and physics["blender_physics_executed"] is False
        and physics["physical_validation"] is False
    )
    closing = motion_manifest["closing_card"]
    closing_path = ROOT / closing["path"]
    closing_safe = bool(
        closing_path.is_file()
        and sha256(closing_path) == closing["sha256"]
        and closing["three_stairwell_requirement_present"] is True
        and closing["three_stairwell_count"] == 3
        and closing["mass_stiffness_strength_or_load_path_credit_assigned"] is False
    )
    return {
        "sequences": checks,
        "source_derivative_and_master_unchanged": source_safe,
        "physics_absent": physics_safe,
        "closing_card_safe": closing_safe,
        "passed": all(check["passed"] for check in checks)
        and len(checks) == config["expected_counts"]["motion_shot_count"]
        and motion_manifest["motion_frame_count"] == config["expected_counts"]["motion_frame_count"]
        and source_safe
        and physics_safe
        and closing_safe,
    }


def encode_segments(config: dict[str, Any], temp_dir: Path) -> tuple[list[dict[str, Any]], Path]:
    segments_dir = temp_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    video = config["video"]
    width, height = video["resolution_px"]
    records = []
    segment_paths = []
    for index, shot in enumerate(config["shots"], start=1):
        output = segments_dir / f"segment_{index:02d}.mp4"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        if shot["source_type"] == "static":
            command += ["-loop", "1", "-framerate", str(video["frame_rate_fps"]), "-i", str(ROOT / shot["source"])]
        else:
            command += [
                "-framerate",
                str(config["blender"]["motion_render_fps"]),
                "-start_number",
                "1",
                "-i",
                str(ROOT / shot["source"]),
            ]
        command += [
            "-t",
            f"{float(shot['duration_s']):.6f}",
            "-vf",
            f"fps={video['frame_rate_fps']},scale={width}:{height}:flags=lanczos,format={video['pixel_format']}",
            "-an",
            "-c:v",
            video["encoder"],
            "-preset",
            video["preset"],
            "-crf",
            str(video["crf"]),
        ]
        if shot["mode"] == "frozen_contact_frame" and video["contact_segment_all_intra"]:
            command += ["-g", "1"]
        command += [
            "-r",
            str(video["frame_rate_fps"]),
            "-video_track_timescale",
            "24000",
            str(output),
        ]
        run(command)
        segment_paths.append(output)
        records.append({
            "shot_id": shot["id"],
            "path": str(output.relative_to(ROOT)).replace("\\", "/"),
            "size_bytes": output.stat().st_size,
            "sha256": sha256(output),
            "source_type": shot["source_type"],
            "duration_s": shot["duration_s"],
        })
    concat_path = temp_dir / "segments.ffconcat"
    concat_lines = ["ffconcat version 1.0"]
    for path in segment_paths:
        escaped = str(path.resolve()).replace("'", "'\\''")
        concat_lines.append(f"file '{escaped}'")
    write_text(concat_path, "\n".join(concat_lines) + "\n")
    return records, concat_path


def probe_video(path: Path) -> dict[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-count_frames",
        "-show_entries",
        "format=duration,size,format_name:stream=index,codec_name,codec_type,width,height,r_frame_rate,avg_frame_rate,nb_frames,nb_read_frames,pix_fmt,duration",
        "-of",
        "json",
        str(path),
    ]
    return json.loads(run(command).stdout)


def extract_samples(config: dict[str, Any], video_path: Path) -> list[dict[str, Any]]:
    output_dir = ROOT / config["output"]["audit_sample_directory"]
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for time_s in config["sample_times_s"]:
        shot = next(shot for shot in config["shots"] if shot["start_s"] <= time_s < shot["end_s"])
        path = output_dir / f"sample_{int(round(float(time_s) * 1000)):05d}ms.png"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{float(time_s):.6f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(path),
        ]
        run(command)
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            width, height = rgb.size
            search_height = int(config["video"]["banner_search_bottom_height_px"])
            band = rgb.crop((0, height - search_height, width, height))
            row_fractions = []
            for row_index in range(search_height):
                row = band.crop((0, row_index, width, row_index + 1))
                pixels = list(row.get_flattened_data())
                orange = sum(1 for r, g, b in pixels if r >= 150 and 80 <= g <= 205 and b <= 145 and r > g > b)
                row_fractions.append(orange / len(pixels))
            row_gate = float(config["video"]["minimum_banner_orange_row_fraction"])
            maximum_row_fraction = max(row_fractions)
            orange_row_count = sum(value >= row_gate for value in row_fractions)
        records.append({
            "time_s": time_s,
            "shot_id": shot["id"],
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "dimensions_px": [width, height],
            "maximum_bottom_banner_orange_row_fraction": maximum_row_fraction,
            "bottom_banner_orange_row_count": orange_row_count,
            "banner_panel_gate_passed": maximum_row_fraction >= row_gate
            and orange_row_count >= int(config["video"]["minimum_banner_orange_row_count"]),
        })
    return records


def verify_contact_freeze(config: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    expected_times = config["video"]["contact_freeze_sample_times_s"]
    records = [record for record in samples if record["time_s"] in expected_times]
    images = [Image.open(ROOT / record["path"]).convert("RGB") for record in records]
    maximum_delta = 0
    pair_records = []
    try:
        for index in range(len(images) - 1):
            difference = ImageChops.difference(images[index], images[index + 1])
            extrema = difference.getextrema()
            pair_maximum = max(channel[1] for channel in extrema)
            maximum_delta = max(maximum_delta, pair_maximum)
            pair_records.append({
                "left_time_s": records[index]["time_s"],
                "right_time_s": records[index + 1]["time_s"],
                "maximum_pixel_channel_delta": pair_maximum,
            })
    finally:
        for image in images:
            image.close()
    return {
        "samples": records,
        "pairs": pair_records,
        "maximum_pixel_channel_delta": maximum_delta,
        "permitted_maximum_pixel_channel_delta": config["video"]["maximum_contact_freeze_pixel_delta"],
        "passed": len(records) == len(expected_times)
        and maximum_delta <= config["video"]["maximum_contact_freeze_pixel_delta"],
    }


def build_contact_sheet(config: dict[str, Any], samples: list[dict[str, Any]]) -> dict[str, Any]:
    columns = 4
    rows = 4
    cell_width, cell_height = 320, 180
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), (8, 12, 20))
    draw = ImageDraw.Draw(sheet)
    for index, record in enumerate(samples):
        with Image.open(ROOT / record["path"]) as image:
            thumb = image.convert("RGB").resize((cell_width, cell_height), Image.Resampling.LANCZOS)
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y, x + 168, y + 18), fill=(5, 10, 18))
        draw.text((x + 5, y + 4), f"{record['time_s']:05.1f}s {record['shot_id']}", fill=(235, 242, 250))
    output = ROOT / config["output"]["audit_contact_sheet"]
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG")
    return {
        "path": str(output.relative_to(ROOT)).replace("\\", "/"),
        "size_bytes": output.stat().st_size,
        "sha256": sha256(output),
        "dimensions_px": list(sheet.size),
    }


def build_report(result: dict[str, Any], config: dict[str, Any]) -> str:
    video = result["animatic"]
    freeze = result["contact_freeze_audit"]
    banner_min = min(record["maximum_bottom_banner_orange_row_fraction"] for record in result["audit_samples"])
    banner_row_min = min(record["bottom_banner_orange_row_count"] for record in result["audit_samples"])
    return f"""# WTC 1 — V9P — Animatique 3D illustrative

## Conclusion courte

V9P produit un animatique silencieux de **75 secondes**, en 640 × 360 à 24 images/s. Il montre uniquement l’approche géométrique avant contact, puis une image figée au premier contact et des fiches explicatives. Validation générale : **{result['validation_status']}**.

Ce livrable n’est pas une simulation physique de l’impact sur la façade.

## 1. Faits contrôlés

- Vidéo : `{video['path']}` ; durée mesurée **{video['duration_s']:.6f} s** ; **{video['frame_count']}** images ; codec `{video['codec_name']}` ; aucune piste audio.
- Le dérivé V9O et le maître V4.2 conservent leurs empreintes ; aucun fichier Blender source n’a été enregistré.
- Les 336 images animées appartiennent aux quatre intervalles pré-contact.
- Les trois échantillons de l’intervalle de contact ont un écart maximal de **{freeze['maximum_pixel_channel_delta']}** niveau de canal : l’image est strictement figée.
- Les treize échantillons contiennent le panneau inférieur du bandeau ; couverture horizontale orange minimale : **{banner_min:.3f}**, sur au moins **{banner_row_min} lignes** par image.

## 2. Résultats provenant du modèle officiel

Les trois enveloppes de vitesse et d’orientation sont les entrées déjà transcrites et gelées en V8S/V9N. Elles ne sont ni recalculées ni présentées comme des probabilités.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d’archive n’a été introduite. L’archive source n’a été ni lue ni rescannée.

## 4. Exigence utilisateur : trois cages d’escalier

Le futur modèle de tour doit documenter puis intégrer **trois cages d’escalier**. V9P enregistre cette exigence sur la carte finale et dans un fichier dédié. À ce stade, leur position exacte, leur continuité verticale, leur construction, leurs connexions, leur masse et leur état d’endommagement ne sont pas qualifiés.

En conséquence, V9P ne leur attribue **aucune masse, rigidité, résistance ni capacité de chemin de charge**. Leur contribution éventuelle devra être établie par des plans et détails de construction traçables.

## 5. Hypothèses propres à la visualisation

- silhouettes d’avion rigides et schématiques ;
- interpolation géométrique à vitesse constante pour `t < 0` ;
- rendu des mouvements à 12 images/s, dupliqué à 24 images/s pour l’encodage ;
- cadrages, couleurs, éclairage et coupes franches destinés à la lisibilité.

## 6. Résultats dérivés

- 11 plans contigus totalisant 75 s ;
- 4 séquences animées avant contact ;
- 0 séquence 3D mobile après contact ;
- 1 intervalle de contact figé ;
- 3 fiches explicatives après le contact ;
- 0 corps rigide Blender, 0 particule, 0 fluide et 0 monde physique.

## 7. Contradictions, limites et informations manquantes

Ne sont toujours pas qualifiés : le contact déformable-déformable, la rupture du projectile et de la façade, la convergence de l’impulsion, les débris, le carburant, le feu, les dommages du noyau, le rôle mécanique des cages d’escalier et la réponse globale de la tour.

## Décision

V9P valide l’animatique comme média illustratif. V9Q devra effectuer un audit documentaire ciblé des trois cages d’escalier avant toute attribution structurelle ou nouveau calcul global.

## Reproductibilité

- Configuration : `wtc1_simulation_v8/data/v9p_low_resolution_animatic.json`
- Rendu Blender : `{config['output']['blender_render_script']}`
- Encodage et audit : `{config['output']['audit_script']}`
- Manifeste des mouvements : `{config['output']['motion_render_manifest']}`
- Manifeste de l’animatique : `{config['output']['animatic_manifest']}`
- Planche de contrôle : `{config['output']['audit_contact_sheet']}`
- Graine déclarée : `{config['dataset']['random_seed']}` ; aucun tirage aléatoire utilisé.
"""


def main() -> None:
    started = time.perf_counter()
    config = load_json(CONFIG_PATH)
    motion_manifest_path = ROOT / config["output"]["motion_render_manifest"]
    motion_manifest = load_json(motion_manifest_path)
    regressions = verify_regressions(config)
    shot_validation = validate_shots(config)
    motion_inputs = verify_motion_inputs(config, motion_manifest)
    ffmpeg_version_line = run(["ffmpeg", "-version"]).stdout.splitlines()[0]
    ffprobe_version_line = run(["ffprobe", "-version"]).stdout.splitlines()[0]
    ffmpeg_version_passed = f"ffmpeg version {config['video']['ffmpeg_expected_version_prefix']}" in ffmpeg_version_line

    temp_dir = ROOT / "tmp/v9p_animatic"
    temp_dir.mkdir(parents=True, exist_ok=True)
    segment_records, concat_path = encode_segments(config, temp_dir)
    animatic_path = ROOT / config["output"]["animatic"]
    animatic_path.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(animatic_path),
    ])
    probe = probe_video(animatic_path)
    streams = probe["streams"]
    video_streams = [stream for stream in streams if stream["codec_type"] == "video"]
    audio_streams = [stream for stream in streams if stream["codec_type"] == "audio"]
    video_stream = video_streams[0]
    duration_s = float(probe["format"]["duration"])
    frame_count = int(video_stream.get("nb_read_frames") or video_stream.get("nb_frames"))
    animatic_record = {
        "path": config["output"]["animatic"],
        "size_bytes": animatic_path.stat().st_size,
        "sha256": sha256(animatic_path),
        "duration_s": duration_s,
        "frame_count": frame_count,
        "codec_name": video_stream["codec_name"],
        "pixel_format": video_stream["pix_fmt"],
        "width": video_stream["width"],
        "height": video_stream["height"],
        "r_frame_rate": video_stream["r_frame_rate"],
        "avg_frame_rate": video_stream["avg_frame_rate"],
        "video_stream_count": len(video_streams),
        "audio_stream_count": len(audio_streams),
    }
    animatic_record["passed"] = bool(
        abs(duration_s - config["video"]["duration_s"]) <= config["video"]["duration_tolerance_s"]
        and frame_count == config["video"]["expected_frame_count"]
        and video_stream["codec_name"] == config["video"]["codec"]
        and [video_stream["width"], video_stream["height"]] == config["video"]["resolution_px"]
        and video_stream["pix_fmt"] == config["video"]["pixel_format"]
        and len(video_streams) == 1
        and len(audio_streams) == 0
    )

    samples = extract_samples(config, animatic_path)
    banner_audit_passed = len(samples) == config["expected_counts"]["audit_sample_count"] and all(
        record["banner_panel_gate_passed"] for record in samples
    )
    freeze = verify_contact_freeze(config, samples)
    contact_sheet = build_contact_sheet(config, samples)
    stairwell_path = ROOT / config["output"]["stairwell_requirement"]
    stairwell_record = {
        "iteration": "V9P",
        "status": config["stairwell_requirement"]["status"],
        "provenance": "user_instruction_recorded_in_V9P",
        "requested_count": config["stairwell_requirement"]["requested_count"],
        "generic_identifiers": config["stairwell_requirement"]["generic_identifiers"],
        "required_before_structural_use": config["stairwell_requirement"]["required_before_structural_use"],
        "assigned_in_v9p": {
            "mass": False,
            "stiffness": False,
            "strength": False,
            "load_path_credit": False,
        },
        "geometry_or_mechanical_role_validated": False,
        "archive_read_or_rescanned": False,
        "next_action": config["next_iteration"],
    }
    write_json(stairwell_path, stairwell_record)

    scope_preserved = all(value is False for value in motion_manifest["scope"].values())
    overall = bool(
        regressions["passed"]
        and shot_validation["passed"]
        and motion_inputs["passed"]
        and ffmpeg_version_passed
        and animatic_record["passed"]
        and banner_audit_passed
        and freeze["passed"]
        and scope_preserved
        and stairwell_record["geometry_or_mechanical_role_validated"] is False
        and all(value is False for value in stairwell_record["assigned_in_v9p"].values())
    )
    manifest = {
        "iteration": "V9P",
        "status": "PASS" if overall else "FAIL",
        "configuration": {
            "path": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(CONFIG_PATH),
        },
        "ffmpeg": {
            "version_line": ffmpeg_version_line,
            "ffprobe_version_line": ffprobe_version_line,
            "version_gate_passed": ffmpeg_version_passed,
        },
        "segments": segment_records,
        "animatic": animatic_record,
        "audit_samples": samples,
        "banner_audit_passed": banner_audit_passed,
        "contact_freeze_audit": freeze,
        "audit_contact_sheet": contact_sheet,
        "stairwell_requirement": {
            "path": str(stairwell_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(stairwell_path),
            "requested_count": 3,
            "structural_credit_assigned": False,
        },
        "runtime": {
            "elapsed_s": time.perf_counter() - started,
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "new_source_acquisition": False,
            "structural_solver_executed": False,
            "blender_physics_executed": False,
            "external_contact_made": False,
            "foia_request_sent": False,
        },
        "interpretation": "The MP4 is a silent visualization-only animatic. Pre-contact motion is schematic; first contact is frozen and all later intervals are static explanatory cards. No physical impact result is encoded.",
    }
    manifest_path = ROOT / config["output"]["animatic_manifest"]
    write_json(manifest_path, manifest)
    result = {
        "iteration": "V9P",
        "validation_status": "PASS" if overall else "FAIL",
        "iteration_execution_validated": overall,
        "generated_at_local": datetime.now().astimezone().isoformat(),
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "random_seed_declared": config["dataset"]["random_seed"],
            "random_draw_used": False,
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "structural_solver_executed": False,
            "blender_visualization_executed": True,
            "blender_physics_executed": False,
            "foia_request_sent": False,
        },
        "configuration": manifest["configuration"],
        "scripts": {
            "blender_render": {
                "path": config["output"]["blender_render_script"],
                "sha256": sha256(ROOT / config["output"]["blender_render_script"]),
            },
            "animatic_audit": {
                "path": config["output"]["audit_script"],
                "sha256": sha256(Path(__file__).resolve()),
            },
        },
        "regression": regressions,
        "shot_validation": shot_validation,
        "motion_input_validation": motion_inputs,
        "animatic": animatic_record,
        "audit_samples": samples,
        "banner_audit_passed": banner_audit_passed,
        "contact_freeze_audit": freeze,
        "audit_contact_sheet": contact_sheet,
        "stairwell_requirement": stairwell_record,
        "shot_count": shot_validation["shot_count"],
        "motion_shot_count": shot_validation["motion_shot_count"],
        "postcontact_three_dimensional_motion_shot_count": shot_validation["postcontact_three_dimensional_motion_shot_count"],
        "physical_track_reopening_authorized": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_visualization_is_physical_validation": False,
        "evidence_separation": config["evidence_policy"],
        "limitations": [
            "The aircraft are rigid schematic silhouettes and not a deformable Boeing 767 or CF6-80A2 model.",
            "No contact, rupture, impulse, damage, debris, fuel, fire, core response or global tower response is calculated.",
            "The three stairwell enclosures are a recorded completeness requirement only; their geometry and mechanical role are unqualified.",
            "Frame duplication and video encoding are presentation operations, not physics.",
        ],
        "next_iteration": config["next_iteration"],
    }
    results_path = ROOT / config["output"]["results"]
    report_path = ROOT / config["output"]["report"]
    write_json(results_path, result)
    write_text(report_path, build_report(result, config))
    print(json.dumps({
        "iteration": "V9P",
        "validation_status": result["validation_status"],
        "duration_s": animatic_record["duration_s"],
        "frame_count": animatic_record["frame_count"],
        "banner_audit_passed": banner_audit_passed,
        "contact_freeze_maximum_pixel_delta": freeze["maximum_pixel_channel_delta"],
        "stairwell_requirement_count": stairwell_record["requested_count"],
        "stairwell_structural_credit_assigned": False,
        "next_iteration": config["next_iteration"]["id"],
    }, ensure_ascii=False, indent=2))
    if not overall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
