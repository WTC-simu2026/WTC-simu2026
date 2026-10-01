#!/usr/bin/env python3
"""Validate and report the V9O Blender visualization-only storyboard preview."""

from __future__ import annotations

import hashlib
import json
import platform
import struct
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9o_blender_storyboard_preview.json"


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


def png_dimensions(path: Path) -> list[int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Not a valid PNG header: {path}")
    return list(struct.unpack(">II", header[16:24]))


def verify_regressions(config: dict[str, Any]) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for relative, expected_hash in config["regression_files"].items():
        path = ROOT / relative
        actual_hash = sha256(path) if path.is_file() else None
        files[relative] = {
            "exists": path.is_file(),
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "passed": path.is_file() and actual_hash == expected_hash,
        }
    metrics = []
    cache: dict[str, dict[str, Any]] = {}
    for declaration in config["regression_metrics"]:
        relative = declaration["results"]
        cache.setdefault(relative, load_json(ROOT / relative))
        actual = get_path(cache[relative], declaration["path"])
        expected = declaration["expected"]
        metrics.append({**declaration, "actual": actual, "passed": actual == expected})
    return {
        "files": files,
        "metrics": metrics,
        "passed": all(item["passed"] for item in files.values()) and all(item["passed"] for item in metrics),
    }


def verify_renders(config: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    expected_frames = config["shot_renders"]
    records = manifest["renders"]
    record_by_path = {record["path"]: record for record in records}
    checks = []
    for shot in expected_frames:
        relative = f"{config['output']['render_directory']}/{shot['filename']}"
        path = ROOT / relative
        record = record_by_path.get(relative)
        actual_hash = sha256(path) if path.is_file() else None
        actual_dimensions = png_dimensions(path) if path.is_file() else None
        expected_dimensions = config["blender"]["individual_frame_resolution_px"]
        checks.append({
            "shot_id": shot["shot_id"],
            "path": relative,
            "exists": path.is_file(),
            "expected_sha256": record.get("sha256") if record else None,
            "actual_sha256": actual_hash,
            "expected_dimensions_px": expected_dimensions,
            "actual_dimensions_px": actual_dimensions,
            "passed": bool(
                path.is_file()
                and record
                and actual_hash == record["sha256"]
                and actual_dimensions == expected_dimensions
                and record["dimensions_px"] == expected_dimensions
            ),
        })
    proof_relative = config["output"]["proof_sheet"]
    proof_path = ROOT / proof_relative
    proof_record = manifest["proof_sheet"]
    proof_dimensions = png_dimensions(proof_path) if proof_path.is_file() else None
    expected_proof_dimensions = config["blender"]["proof_sheet_resolution_px"]
    proof_check = {
        "path": proof_relative,
        "exists": proof_path.is_file(),
        "expected_sha256": proof_record["sha256"],
        "actual_sha256": sha256(proof_path) if proof_path.is_file() else None,
        "expected_dimensions_px": expected_proof_dimensions,
        "actual_dimensions_px": proof_dimensions,
    }
    proof_check["passed"] = bool(
        proof_check["exists"]
        and proof_check["actual_sha256"] == proof_check["expected_sha256"]
        and proof_dimensions == expected_proof_dimensions
        and proof_record["dimensions_px"] == expected_proof_dimensions
    )
    return {
        "shots": checks,
        "proof_sheet": proof_check,
        "passed": len(checks) == config["expected_counts"]["shot_render_count"]
        and all(item["passed"] for item in checks)
        and proof_check["passed"],
    }


def build_report(result: dict[str, Any], config: dict[str, Any]) -> str:
    master = result["artifact_checks"]["master"]
    derivative = result["artifact_checks"]["derivative"]
    internal = result["blender_internal_audit"]
    physics = internal["physics"]
    branches = internal["branches"]
    branch_rows = "\n".join(
        f"| {branch_id} | {record['contact_frame']} | {record['actual_location_keyframe_frames']} | "
        f"{'PASS' if record['postcontact_freeze_verified'] else 'FAIL'} |"
        for branch_id, record in branches.items()
    )
    return f"""# WTC 1 — V9O — Aperçu Blender du storyboard

## Conclusion courte

V9O est validée comme **visualisation 3D illustrative à basse résolution**, et uniquement comme cela. Le fichier produit montre trois silhouettes rigides pendant l’approche, puis les fige au premier contact. Il ne calcule ni l’impact, ni la rupture, ni les débris, ni le feu, ni la réponse de la tour.

Validation générale : **{result['validation_status']}**.

## 1. Faits contrôlés

- Le fichier maître V4.2 conserve son empreinte SHA-256 : `{master['actual_sha256']}`.
- Un nouveau fichier dérivé existe : `{derivative['path']}` ({derivative['size_bytes']} octets).
- Onze vues PNG de 640 × 360 et une planche de contrôle de 1280 × 540 existent et correspondent au manifeste.
- Le fichier dérivé a été rouvert par Blender {internal['blender']['version']} pour un audit indépendant en lecture seule.
- Les trois scènes V9O, les trois caméras et les onze repères temporels sont effectivement enregistrés.

## 2. Résultats provenant du modèle officiel

Les trois enveloppes d’approche, leurs vitesses et leurs orientations restent celles déjà transcrites et gelées en V9N. V9O ne les requalifie pas et ne les transforme pas en probabilités.

## 3. Affirmations des archives locales

Aucune nouvelle affirmation d’archive n’a été introduite. L’archive source n’a été ni lue ni rescannée en V9O.

## 4. Hypothèses propres au modèle visuel

- silhouette d’avion rigide et simplifiée ;
- interpolation à vitesse constante avant contact ;
- couleurs, éclairage, cadrages et décalages latéraux destinés à la lisibilité ;
- géométrie de façade partiellement reconstruite déjà documentée en V4.2/V9N.

Ces choix sont graphiques. Ils ne constituent pas une validation physique.

## 5. Résultats dérivés

| Branche | Image de contact | Images-clés de position | Immobilité après contact |
|---|---:|---|---|
{branch_rows}

- Corps rigides Blender : **{physics['rigid_body_object_count']}**.
- Systèmes de particules : **{physics['particle_system_object_count']}**.
- Modificateurs fluides : **{physics['fluid_modifier_count']}**.
- Monde de corps rigides : **{physics['rigidbody_world_scene_count']}**.
- Solveur structurel exécuté : **non**.
- Physique Blender exécutée : **non**.

## 6. Contradictions, limites et informations manquantes

Restent non qualifiés : le contact déformable-déformable à l’échelle pertinente, la rupture du projectile et de la façade, la convergence de l’impulsion, les débris, le carburant, le feu, les dommages du noyau et la réponse globale. Par conséquent, V9O ne permet pas de dire qu’une simulation physique de l’impact de l’avion sur la façade a réussi.

## Décision

V9O ferme l’étape de **prévisualisation fixe**. Elle autorise V9P à fabriquer un animatique de 75 secondes à partir du seul fichier dérivé validé, avec le bandeau permanent et l’arrêt au contact. Elle n’autorise toujours aucune simulation physique globale.

## Reproductibilité

- Configuration : `{config['output']['configuration'] if 'configuration' in config['output'] else 'wtc1_simulation_v8/data/v9o_blender_storyboard_preview.json'}`
- Constructeur Blender : `wtc1_3d_v4/scripts/build_v9o_storyboard_preview.py`
- Audit Blender : `{config['output']['blender_audit_script']}`
- Manifeste : `{config['output']['visualization_manifest']}`
- Planche de contrôle : `{config['output']['proof_sheet']}`
- Graine déclarée : `{config['dataset']['random_seed']}` (exécution déterministe, sans tirage aléatoire utilisé)
"""


def main() -> None:
    config = load_json(CONFIG_PATH)
    manifest_path = ROOT / config["output"]["visualization_manifest"]
    internal_path = ROOT / config["output"]["blender_internal_audit"]
    derivative_path = ROOT / config["master_policy"]["derivative_blend"]
    master_path = ROOT / config["master_policy"]["master_blend"]
    results_path = ROOT / config["output"]["results"]
    report_path = ROOT / config["output"]["report"]
    manifest = load_json(manifest_path)
    internal = load_json(internal_path)
    regressions = verify_regressions(config)
    renders = verify_renders(config, manifest)

    master_check = {
        "path": config["master_policy"]["master_blend"],
        "expected_sha256": config["master_policy"]["master_expected_sha256"],
        "actual_sha256": sha256(master_path),
        "unchanged": sha256(master_path) == config["master_policy"]["master_expected_sha256"],
    }
    derivative_hash = sha256(derivative_path) if derivative_path.is_file() else None
    derivative_check = {
        "path": config["master_policy"]["derivative_blend"],
        "exists": derivative_path.is_file(),
        "size_bytes": derivative_path.stat().st_size if derivative_path.is_file() else None,
        "manifest_sha256": manifest["derivative"]["sha256"],
        "actual_sha256": derivative_hash,
        "new_path": derivative_path.resolve() != master_path.resolve(),
    }
    derivative_check["passed"] = bool(
        derivative_check["exists"]
        and derivative_check["new_path"]
        and derivative_hash == manifest["derivative"]["sha256"]
        and derivative_check["size_bytes"] == manifest["derivative"]["size_bytes"]
    )

    expected = config["expected_counts"]
    branches = internal["branches"]
    scene_flags = internal["scenes"]["storyboard_flags"]
    structural_checks = {
        "internal_audit_pass": internal["status"] == "PASS",
        "opened_derivative_hash_matches": internal["opened_file_sha256"] == derivative_hash,
        "master_unchanged": master_check["unchanged"] and internal["master"]["unchanged"],
        "required_scenes_present": internal["scenes"]["present"] == internal["scenes"]["required"],
        "storyboard_scene_flags_safe": scene_flags["visualization_only"] is True
        and scene_flags["physical_validation"] is False
        and scene_flags["postcontact_motion_authorized"] is False,
        "permanent_banner_recorded": scene_flags["permanent_banner"] == config["permanent_text"]["banner"],
        "timeline_marker_count": len(internal["timeline_markers"]) == expected["timeline_marker_count"],
        "new_camera_count": len(internal["cameras"]) == expected["new_camera_count"],
        "branch_count": len(branches) == expected["branch_count"],
        "keyframe_frames_match": all(record["keyframe_frames_match"] for record in branches.values()),
        "postcontact_freeze_verified": all(record["postcontact_freeze_verified"] for record in branches.values()),
        "rigid_body_count_zero": internal["physics"]["rigid_body_object_count"] == expected["rigid_body_object_count"],
        "particle_count_zero": internal["physics"]["particle_system_object_count"] == expected["particle_system_count"],
        "fluid_count_zero": internal["physics"]["fluid_modifier_count"] == expected["fluid_modifier_count"],
        "rigidbody_world_absent": internal["physics"]["rigidbody_world_scene_count"] == 0,
        "no_solver_or_blender_physics": internal["physics"]["structural_solver_executed"] is False
        and internal["physics"]["blender_physics_executed"] is False,
        "blender_not_physical_validation": internal["physics"]["physical_validation"] is False,
        "runtime_scope_preserved": all(value is False for value in internal["scope"].values()),
        "expected_blender_version": internal["blender"]["version"].startswith(config["blender"]["expected_version_prefix"]),
    }
    passed = bool(
        regressions["passed"]
        and renders["passed"]
        and master_check["unchanged"]
        and derivative_check["passed"]
        and all(structural_checks.values())
        and manifest["storyboard_scene"]["maximum_animated_event_time_s"] == 0.0
        and manifest["storyboard_scene"]["postcontact_motion_keyframe_count"] == 0
    )

    result = {
        "iteration": "V9O",
        "validation_status": "PASS" if passed else "FAIL",
        "iteration_execution_validated": passed,
        "generated_at_local": datetime.now().astimezone().isoformat(),
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "random_seed_declared": config["dataset"]["random_seed"],
            "random_draw_used": False,
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "network_access_used": False,
            "external_contact_made": False,
            "foia_request_sent": False,
            "structural_solver_executed": False,
            "blender_visualization_executed": True,
            "blender_physics_executed": False,
        },
        "configuration": {
            "path": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(CONFIG_PATH),
        },
        "scripts": {
            "builder": {
                "path": "wtc1_3d_v4/scripts/build_v9o_storyboard_preview.py",
                "sha256": sha256(ROOT / "wtc1_3d_v4/scripts/build_v9o_storyboard_preview.py"),
            },
            "blender_internal_audit": {
                "path": config["output"]["blender_audit_script"],
                "sha256": sha256(ROOT / config["output"]["blender_audit_script"]),
            },
            "report_audit": {
                "path": str(Path(__file__).resolve().relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(Path(__file__).resolve()),
            },
        },
        "regression": regressions,
        "artifact_checks": {
            "master": master_check,
            "derivative": derivative_check,
            "manifest": {"path": config["output"]["visualization_manifest"], "sha256": sha256(manifest_path)},
            "blender_internal_audit": {"path": config["output"]["blender_internal_audit"], "sha256": sha256(internal_path)},
            "renders": renders,
        },
        "structural_checks": structural_checks,
        "blender_internal_audit": internal,
        "storyboard_shot_count": len(config["shot_renders"]),
        "three_dimensional_shot_count": sum(shot["kind"] == "three_dimensional" for shot in config["shot_renders"]),
        "card_shot_count": sum(shot["kind"] == "card" for shot in config["shot_renders"]),
        "branch_count": len(branches),
        "maximum_animated_event_time_s": manifest["storyboard_scene"]["maximum_animated_event_time_s"],
        "postcontact_motion_keyframe_count": manifest["storyboard_scene"]["postcontact_motion_keyframe_count"],
        "physical_track_reopening_authorized": False,
        "blender_visualization_is_physical_validation": False,
        "evidence_separation": config["evidence_policy"],
        "limitations": [
            "Rigid schematic silhouettes are not a deformable aircraft model.",
            "No deformable-deformable contact, rupture or impulse convergence was calculated.",
            "No damage, debris, fuel, fire, core response or global tower response was calculated.",
            "The visual result cannot validate impact physics.",
        ],
        "next_iteration": config["next_iteration"],
    }
    write_json(results_path, result)
    write_text(report_path, build_report(result, config))
    print(json.dumps({
        "iteration": "V9O",
        "validation_status": result["validation_status"],
        "storyboard_shot_count": result["storyboard_shot_count"],
        "branch_count": result["branch_count"],
        "postcontact_motion_keyframe_count": result["postcontact_motion_keyframe_count"],
        "rigid_body_object_count": internal["physics"]["rigid_body_object_count"],
        "particle_system_count": internal["physics"]["particle_system_object_count"],
        "fluid_modifier_count": internal["physics"]["fluid_modifier_count"],
        "master_unchanged": master_check["unchanged"],
        "next_iteration": config["next_iteration"]["id"],
    }, ensure_ascii=False, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
