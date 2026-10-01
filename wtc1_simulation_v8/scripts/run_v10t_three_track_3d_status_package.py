from __future__ import annotations

import csv
import hashlib
import json
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10t_three_track_3d_status_package.json"
SCRIPT_PATH = Path(__file__).resolve()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content.rstrip() + "\n")


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def abs_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise RuntimeError(f"Unexpected {label}: {actual!r} != {expected!r}")


def csv_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def verified_file(item: dict[str, Any], read_mode: str) -> dict[str, Any]:
    path = abs_path(item["path"])
    role = item.get("role", item.get("id", "file"))
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != str(item["expected_sha256"]).lower():
        raise RuntimeError(f"Hash mismatch for {role}: expected {item['expected_sha256']}, got {actual}")
    row: dict[str, Any] = {
        "role": role,
        "path": display_path(path),
        "sha256": actual,
        "bytes": path.stat().st_size,
        "read_mode": read_mode,
        "status": "PASS",
    }
    for key in ("evidence_class", "use", "allowed_credit", "expected_version_prefix"):
        if key in item:
            row[key] = item[key]
    return row


def get_item(items: list[dict[str, Any]], identity: str) -> dict[str, Any]:
    matches = [item for item in items if item.get("role") == identity or item.get("id") == identity]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one configured item {identity}, got {len(matches)}")
    return matches[0]


def get_path(items: list[dict[str, Any]], identity: str) -> Path:
    return abs_path(get_item(items, identity)["path"])


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    require_equal("configuration iteration", config.get("iteration"), "V10T")
    expected = config["expected"]
    actual_counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_input_file_count": len(config["cached_input_files"]),
        "official_source_hash_only_file_count": len(config["official_source_hash_only_files"]),
        "software_file_count": len(config["software_files"]),
        "track_count": len(config["track_contract"]["required_track_ids"]),
        "stage_count": len(config["track_contract"]["stage_ids"]),
        "render_count": len(config["visual_contract"]["renders"]),
    }
    for key, actual in actual_counts.items():
        require_equal(key, actual, expected[key])
    require_equal(
        "status matrix row predeclaration",
        actual_counts["track_count"] * actual_counts["stage_count"],
        expected["status_matrix_row_count"],
    )
    require_equal("static frame start", config["visual_contract"]["frame_start"], 1)
    require_equal("static frame end", config["visual_contract"]["frame_end"], 1)
    require_equal("static-only contract", config["visual_contract"]["static_only"], True)
    if "AUCUNE PRÉDICTION D’EFFONDREMENT" not in config["visual_contract"]["permanent_banner"]:
        raise RuntimeError("Permanent non-prediction banner is missing")
    filenames = [row["filename"] for row in config["visual_contract"]["renders"]]
    if len(set(filenames)) != len(filenames):
        raise RuntimeError("Duplicate V10T render filename")
    return config


def find_true_claims(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            lowered = key.lower()
            if isinstance(child, bool) and child and (
                "physical_release" in lowered
                or "physical_validation" in lowered
                or ("historical" in lowered and ("claim" in lowered or "conclusion" in lowered))
            ):
                found.append(path)
            elif isinstance(child, (int, float)) and not isinstance(child, bool) and child != 0 and (
                "physical_release_count" in lowered or "historical_outcome_assignment_count" in lowered
            ):
                found.append(path)
            found.extend(find_true_claims(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(find_true_claims(child, f"{prefix}[{index}]"))
    return found


def track_by_id(document: dict[str, Any], track_id: str) -> dict[str, Any]:
    matches = [row for row in document["tracks"] if row["track_id"] == track_id]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one track {track_id}, got {len(matches)}")
    return matches[0]


def image_dimensions(path: Path) -> list[int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise RuntimeError(f"Invalid PNG header: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return [width, height]


def image_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Missing image: {path}")
    return {
        "path": display_path(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "dimensions_px": image_dimensions(path),
    }


def extract_metrics(
    config: dict[str, Any],
    p_tracks: dict[str, Any],
    q_tracks: dict[str, Any],
    r_tracks: dict[str, Any],
    s_tracks: dict[str, Any],
    q_temperature_rows: list[dict[str, str]],
    r_material_rows: list[dict[str, str]],
) -> dict[str, Any]:
    expected = config["expected"]
    p_official = track_by_id(p_tracks, "OFFICIAL_MODEL_DEPENDENT_REFERENCE")
    damage_segments = sum(
        int(case["damage_reference"]["expanded_segment_count_floors93_99"])
        for case in p_official["cases"]
    )
    q_official = track_by_id(q_tracks, "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE")
    sfrm_inputs = q_official["sfrm_inputs"]
    sfrm_available = sum(value is not None for value in sfrm_inputs.values())
    hot_endpoint_blocked = sum(csv_bool(row["maximum_above_600_c"]) for row in q_temperature_rows)
    complete_material = sum(row["range_status"] == "COMPLETE_IN_DOMAIN_REFERENCE_ONLY" for row in r_material_rows)
    partial_material = sum(row["range_status"] == "PARTIAL_DOMAIN_BLOCKED" for row in r_material_rows)
    s_control = track_by_id(s_tracks, "CONTROL_ZERO_INITIATION_PROPAGATION")
    s_official = track_by_id(s_tracks, "OFFICIAL_DEPENDENT_PROPAGATION_BLOCKED")
    requirement = s_official["minimum_physical_requirement_summary"]
    metrics = {
        "impact_damage_official_reference_segment_count": damage_segments,
        "temperature_range_count": len(q_temperature_rows),
        "temperature_endpoint_count": len(q_temperature_rows) * 2,
        "temperature_hot_endpoint_blocked_count": hot_endpoint_blocked,
        "complete_material_range_count": complete_material,
        "partial_material_range_count": partial_material,
        "sfrm_available_field_count": sfrm_available,
        "sfrm_total_field_count": len(sfrm_inputs),
        "control_record_check_count": int(s_control["control_audit"]["check_count"]),
        "control_record_pass_count": int(s_control["control_audit"]["pass_count"]),
        "control_conservation_identity_pass_count": int(s_control["control_conservation_identity_pass_count"]),
        "minimum_physical_requirement_count": int(requirement["requirement_count"]),
        "minimum_physical_ready_count": int(requirement["physical_ready_count"]),
        "minimum_physical_blocking_count": int(requirement["blocking_count"]),
        "visualization_status_release_count": int(s_tracks["summary"]["visualization_status_release_count"]),
        "physical_state_release_count": 0,
        "historical_outcome_assignment_count": 0,
    }
    for key, actual in metrics.items():
        require_equal(key, actual, expected[key])
    return metrics


def build_status_matrix(
    config: dict[str, Any],
    documents: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    mapping = {
        "CONTROL_SOFTWARE_ZERO": {
            "IMPACT_DAMAGE": ("V10P", "CONTROL_ZERO_INPUT"),
            "FIRE_THERMAL": ("V10Q", "CONTROL_ZERO_FIRE"),
            "THERMAL_INITIATION": ("V10R", "CONTROL_ZERO_THERMAL_INPUT"),
            "PROPAGATION_ARREST": ("V10S", "CONTROL_ZERO_INITIATION_PROPAGATION"),
        },
        "OFFICIAL_MODEL_DEPENDENT_REFERENCE": {
            "IMPACT_DAMAGE": ("V10P", "OFFICIAL_MODEL_DEPENDENT_REFERENCE"),
            "FIRE_THERMAL": ("V10Q", "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE"),
            "THERMAL_INITIATION": ("V10R", "OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE"),
            "PROPAGATION_ARREST": ("V10S", "OFFICIAL_DEPENDENT_PROPAGATION_BLOCKED"),
        },
        "UNKNOWN_PHYSICAL_EVENT": {
            "IMPACT_DAMAGE": ("V10P", "UNKNOWN_PHYSICAL_DAMAGE"),
            "FIRE_THERMAL": ("V10Q", "UNKNOWN_EVENT_FIRE"),
            "THERMAL_INITIATION": ("V10R", "UNKNOWN_PHYSICAL_INITIATION"),
            "PROPAGATION_ARREST": ("V10S", "UNKNOWN_PHYSICAL_PROPAGATION_OR_ARREST"),
        },
    }
    visual_encodings = {
        "CONTROL_SOFTWARE_ZERO": "BLUE_LABEL_CONTROL_ONLY",
        "OFFICIAL_MODEL_DEPENDENT_REFERENCE": "ORANGE_LABEL_OFFICIAL_DEPENDENT",
        "UNKNOWN_PHYSICAL_EVENT": "MAGENTA_LABEL_UNKNOWN",
    }
    rows: list[dict[str, Any]] = []
    for track_id in config["track_contract"]["required_track_ids"]:
        for stage_id in config["track_contract"]["stage_ids"]:
            iteration, source_track_id = mapping[track_id][stage_id]
            source = track_by_id(documents[iteration], source_track_id)
            rows.append({
                "track_id": track_id,
                "stage_id": stage_id,
                "source_iteration": iteration,
                "source_track_id": source_track_id,
                "source_status": source["status"],
                "epistemic_class": source["epistemic_class"],
                "visualization_status_released": True,
                "physical_state_released": False,
                "historical_outcome_assigned": False,
                "visual_encoding": visual_encodings[track_id],
                "geometry_deformation_or_motion": "NONE",
            })
    require_equal("status matrix rows", len(rows), config["expected"]["status_matrix_row_count"])
    return rows


def run_blender(config: dict[str, Any], outputs: dict[str, Path]) -> dict[str, Any]:
    software_item = config["software_files"][0]
    executable = abs_path(software_item["path"])
    master = get_path(config["protected_files"], "blender_master")
    builder = outputs["blender_builder_script"]
    derivative = outputs["derivative_blend"]
    internal_manifest = outputs["blender_internal_manifest"]
    log_path = outputs["blender_execution_log"]
    for path, label in ((derivative, "derivative"), (internal_manifest, "internal manifest"), (log_path, "execution log")):
        if path.exists():
            raise RuntimeError(f"Fresh V10T run refuses to overwrite existing {label}: {path}")
    command = [str(executable), "--background", str(master), "--python", str(builder)]
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=int(config["execution_policy"]["maximum_runtime_seconds"]),
        check=False,
    )
    elapsed = time.perf_counter() - started
    log = "\n".join(
        [
            "V10T Blender visualization-only execution",
            f"started_at_utc={utc_now()}",
            f"elapsed_seconds={elapsed:.6f}",
            f"return_code={completed.returncode}",
            "command=" + json.dumps(command, ensure_ascii=False),
            "--- STDOUT ---",
            completed.stdout,
            "--- STDERR ---",
            completed.stderr,
        ]
    )
    write_text(log_path, log)
    if completed.returncode != 0:
        raise RuntimeError(f"Blender V10T failed with return code {completed.returncode}; see {log_path}")
    return {
        "invoked_this_process": True,
        "return_code": completed.returncode,
        "elapsed_seconds": elapsed,
        "command": command,
        "stdout_tail": completed.stdout.splitlines()[-20:],
        "stderr_tail": completed.stderr.splitlines()[-20:],
    }


def audit_blender_outputs(
    config: dict[str, Any],
    outputs: dict[str, Path],
    execution: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    expected = config["expected"]
    visual = config["visual_contract"]
    manifest = load_json(outputs["blender_internal_manifest"])
    require_equal("Blender manifest iteration", manifest["iteration"], "V10T")
    require_equal("Blender manifest status", manifest["validation_status"], "PASS_STATIC_LABELLED_BLENDER_VISUALIZATION_ONLY")
    if not manifest["blender_version"].startswith(config["software_files"][0]["expected_version_prefix"]):
        raise RuntimeError(f"Unexpected Blender version {manifest['blender_version']}")
    require_equal("created scene count", manifest["created_scene_count"], expected["scene_count"])
    require_equal("render count", manifest["render_count"], expected["render_count"])
    require_equal("permanent banner", manifest["permanent_banner"], visual["permanent_banner"])
    require_equal("master unchanged", manifest["master"]["unchanged"], True)
    require_equal("master overwritten", manifest["master"]["overwritten"], False)
    require_equal("master before hash", manifest["master"]["sha256_before"], config["protected_files"][0]["expected_sha256"])
    require_equal("master after hash", manifest["master"]["sha256_after"], config["protected_files"][0]["expected_sha256"])
    require_equal("derivative new path", manifest["derivative"]["new_path"], True)
    require_equal("derivative path", manifest["derivative"]["path"], display_path(outputs["derivative_blend"]))
    require_equal("derivative hash", manifest["derivative"]["sha256"], sha256_file(outputs["derivative_blend"]))
    physics = manifest["static_and_physics_audit"]
    checks = {
        "scene_count": manifest["created_scene_count"] == expected["scene_count"],
        "render_count": manifest["render_count"] == expected["render_count"],
        "frame_one_only": physics["all_created_scenes_frame_1_only"] is True,
        "keyframes_zero": physics["v10t_keyframe_count"] == expected["v10t_keyframe_count"],
        "rigid_bodies_zero": physics["v10t_rigid_body_count"] == expected["v10t_rigid_body_count"],
        "particle_systems_zero": physics["v10t_particle_system_count"] == expected["v10t_particle_system_count"],
        "fluid_modifiers_zero": physics["v10t_fluid_modifier_count"] == expected["v10t_fluid_modifier_count"],
        "rigid_body_worlds_zero": physics["created_scene_rigidbody_world_count"] == 0,
        "structural_solver_not_run": physics["structural_solver_executed"] is False,
        "thermal_solver_not_run": physics["thermal_solver_executed"] is False,
        "fire_solver_not_run": physics["fire_solver_executed"] is False,
        "propagation_solver_not_run": physics["propagation_solver_executed"] is False,
        "collision_or_fracture_not_run": physics["collision_or_fracture_executed"] is False,
        "blender_physics_not_run": physics["blender_physics_executed"] is False,
        "blender_not_used_as_validation": physics["blender_used_as_physical_validation"] is False,
        "physical_state_release_zero": manifest["track_release_summary"]["physical_state_release_count"] == 0,
        "historical_outcome_assignment_zero": manifest["track_release_summary"]["historical_outcome_assignment_count"] == 0,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("Blender audit failed: " + ", ".join(failed))

    expected_dimensions = visual["render_resolution_px"]
    shot_by_id = {row["id"]: row for row in visual["renders"]}
    image_rows = []
    for record in manifest["renders"]:
        if record["shot_id"] not in shot_by_id:
            raise RuntimeError(f"Unexpected rendered shot {record['shot_id']}")
        shot = shot_by_id[record["shot_id"]]
        expected_path = outputs["render_directory"] / shot["filename"]
        current = image_record(expected_path)
        require_equal(f"{record['shot_id']} path", record["path"], current["path"])
        require_equal(f"{record['shot_id']} hash", record["sha256"], current["sha256"])
        require_equal(f"{record['shot_id']} dimensions", current["dimensions_px"], expected_dimensions)
        image_rows.append({"shot_id": record["shot_id"], "kind": record["kind"], **current})
    require_equal("unique rendered shot count", len({row["shot_id"] for row in image_rows}), expected["render_count"])
    proof = image_record(outputs["proof_sheet"])
    require_equal("proof dimensions", proof["dimensions_px"], visual["proof_sheet_resolution_px"])
    require_equal("proof hash", manifest["proof_sheet"]["sha256"], proof["sha256"])

    render_manifest = {
        "iteration": "V10T",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_MACHINE_READABLE_RENDER_INTEGRITY",
        "render_count": len(image_rows),
        "renders": image_rows,
        "proof_sheet": proof,
        "permanent_banner_declared": visual["permanent_banner"],
        "manual_visual_inspection_required": True,
    }
    blender_audit = {
        "iteration": "V10T",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_STATIC_NO_PHYSICS_TECHNICAL_AUDIT",
        "blender_version": manifest["blender_version"],
        "execution": execution,
        "internal_manifest": {
            "path": display_path(outputs["blender_internal_manifest"]),
            "sha256": sha256_file(outputs["blender_internal_manifest"]),
            "bytes": outputs["blender_internal_manifest"].stat().st_size,
        },
        "derivative": manifest["derivative"],
        "master": manifest["master"],
        "checks": checks,
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "static_and_physics_audit": physics,
    }
    return blender_audit, render_manifest


def read_visual_qa(config: dict[str, Any], outputs: dict[str, Path], render_manifest: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    path = outputs["visual_qa"]
    if not path.is_file():
        return None, "PENDING_MANUAL_VISUAL_QA"
    qa = load_json(path)
    require_equal("visual QA iteration", qa.get("iteration"), "V10T")
    require_equal("visual QA status", qa.get("validation_status"), "PASS")
    required_checks = [
        "proof_sheet_not_blank",
        "six_views_present",
        "permanent_banner_visible",
        "critical_text_legible",
        "tower_geometry_visible_where_expected",
        "reference_zone_is_visibly_a_frame_not_a_field",
        "no_depicted_collapse_or_postimpact_motion",
        "no_critical_label_clipped",
    ]
    checks = qa.get("checks", {})
    if [name for name in required_checks if checks.get(name) is not True]:
        raise RuntimeError("Visual QA is missing one or more required PASS checks")
    expected_paths = [row["path"] for row in render_manifest["renders"]] + [render_manifest["proof_sheet"]["path"]]
    require_equal("visual QA inspected images", sorted(qa.get("inspected_image_paths", [])), sorted(expected_paths))
    require_equal("visual QA image count", len(expected_paths), config["expected"]["manual_visual_qa_image_count"])
    return qa, "PASS"


def report_text(
    generated_at: str,
    config: dict[str, Any],
    metrics: dict[str, Any],
    blender_audit: dict[str, Any],
    render_manifest: dict[str, Any],
    qa_status: str,
    final_status: str,
) -> str:
    derivative = blender_audit["derivative"]
    return "\n".join(
        [
            "# WTC 1 — V10T : visualisation 3D des statuts à trois pistes",
            "",
            f"Généré : `{generated_at}`",
            "",
            f"Statut : **{final_status}**",
            "",
            "## Résultat",
            "",
            f"Le paquet crée un nouveau dérivé Blender statique (`{derivative['path']}`), {render_manifest['render_count']} vues fixes et une planche de contrôle. Le master V4.2 conserve son empreinte SHA-256. Toutes les scènes V10T sont limitées à l’image 1, sans image clé, corps rigide, particule, fluide, collision, fracture ou solveur physique.",
            "",
            "Les trois pistes restent séparées :",
            "",
            "- **contrôle logiciel zéro** : test de chaîne uniquement, jamais un non-effondrement historique ;",
            "- **références dépendantes du modèle officiel** : statuts et plages transcrits, jamais promus en état physique indépendant ;",
            "- **événement physique** : indéterminé de l’impact jusqu’à la propagation ou l’arrêt.",
            "",
            "## Mesures représentées",
            "",
            f"- impact/dommages : {metrics['impact_damage_official_reference_segment_count']} segments de référence sur les trois cas officiels dépendants ;",
            f"- feu/thermique : {metrics['temperature_range_count']} plages, {metrics['temperature_hot_endpoint_blocked_count']} extrémités chaudes hors domaine commun, et {metrics['sfrm_available_field_count']}/{metrics['sfrm_total_field_count']} champs SFRM disponibles ;",
            f"- initiation : {metrics['complete_material_range_count']} plages entièrement évaluables dans le domaine déclaré, {metrics['partial_material_range_count']} partielles, aucune initiation physique ;",
            f"- propagation/arrêt : {metrics['minimum_physical_ready_count']}/{metrics['minimum_physical_requirement_count']} entrées physiques prêtes, donc aucun calcul de propagation.",
            "",
            "## Contrôles",
            "",
            f"- rendu technique : {blender_audit['pass_count']}/{blender_audit['check_count']} contrôles passés ;",
            f"- inspection visuelle : **{qa_status}** ;",
            f"- états physiques libérés vers Blender : {metrics['physical_state_release_count']} ;",
            f"- issue historique assignée : {metrics['historical_outcome_assignment_count']}.",
            "",
            "## Discipline de preuve",
            "",
            "1. **Faits observés** : identités de fichiers, dimensions et empreintes des rendus, scènes statiques, compteurs nuls de physique Blender.",
            "2. **Résultats du modèle officiel** : les nombres affichés sont uniquement les références déjà transcrites dans V10P–V10R et restent dépendants de ce modèle.",
            "3. **Affirmations des archives** : aucune archive externe n’est lue dans V10T ; un PDF officiel local est seulement rehaché.",
            "4. **Hypothèses du modèle** : couleurs, cadrages, cartes et cadre des étages 93–99 sont des choix de présentation sans crédit mécanique.",
            "5. **Résultats dérivés** : matrice 3 pistes × 4 étapes, paquet Blender, six vues et planche de contrôle.",
            "6. **Contradictions et inconnues** : dommages physiques, feu réel, historiques thermiques par membre, initiation, propagation, arrêt et issue finale restent inconnus.",
            "",
            "## Décision",
            "",
            "V10T fournit la visualisation 3D auditée de l’état du programme, pas une animation de l’événement. L’absence de mouvement d’effondrement est une contrainte de preuve, pas un résultat de non-effondrement.",
            "",
            "## Prochaine étape",
            "",
            config["next_iteration"]["objective"],
        ]
    )


def main() -> int:
    started = time.perf_counter()
    generated_at = utc_now()
    reuse_existing = "--reuse-existing" in sys.argv[1:]
    unexpected_args = [arg for arg in sys.argv[1:] if arg != "--reuse-existing"]
    if unexpected_args:
        raise RuntimeError(f"Unexpected arguments: {unexpected_args}")
    config = load_config()
    expected = config["expected"]
    outputs = {key: abs_path(value) for key, value in config["outputs"].items()}

    regression_rows = [verified_file(item, "FULL_ARTIFACT") for item in config["regression_files"]]
    protected_rows = [verified_file(item, "HASH_ONLY_PROTECTED") for item in config["protected_files"]]
    cached_rows = [verified_file(item, "FULL_ARTIFACT") for item in config["cached_input_files"]]
    official_rows = [verified_file(item, "HASH_ONLY_NO_PAGE_READ") for item in config["official_source_hash_only_files"]]
    software_rows = [verified_file(item, "EXECUTABLE_HASH_ONLY") for item in config["software_files"]]
    if not outputs["blender_builder_script"].is_file():
        raise RuntimeError(f"Missing Blender builder: {outputs['blender_builder_script']}")

    cached = config["cached_input_files"]
    regression = config["regression_files"]
    p_tracks = load_json(get_path(cached, "V10P_TRACK_MANIFEST"))
    q_tracks = load_json(get_path(cached, "V10Q_TRACK_MANIFEST"))
    r_tracks = load_json(get_path(cached, "V10R_TRACK_MANIFEST"))
    s_tracks = load_json(get_path(regression, "v10s_track_manifest"))
    p_gate = load_json(get_path(cached, "V10P_GATE"))
    q_gate = load_json(get_path(cached, "V10Q_GATE"))
    r_gate = load_json(get_path(cached, "V10R_GATE"))
    s_gate = load_json(get_path(regression, "v10s_gate"))
    require_equal("V10P gate", p_gate["validation_status"], "PASS")
    require_equal("V10Q gate", q_gate["validation_status"], "PASS")
    require_equal("V10R gate", r_gate["validation_status"], "PASS_SOFTWARE_PREPROCESSOR_ONLY")
    require_equal("V10S gate", s_gate["validation_status"], "PASS_SOFTWARE_STATUS_CONTRACT_ONLY")
    all_true_claims = []
    for iteration, document in (("V10P", p_tracks), ("V10Q", q_tracks), ("V10R", r_tracks), ("V10S", s_tracks)):
        all_true_claims.extend(f"{iteration}:{path}" for path in find_true_claims(document))
    if all_true_claims:
        raise RuntimeError("Upstream physical or historical claim unexpectedly true: " + ", ".join(all_true_claims))

    q_temperature_rows = read_csv(get_path(cached, "V10Q_TEMPERATURE_MATRIX"))
    r_material_rows = read_csv(get_path(cached, "V10R_MATERIAL_MATRIX"))
    metrics = extract_metrics(config, p_tracks, q_tracks, r_tracks, s_tracks, q_temperature_rows, r_material_rows)
    status_rows = build_status_matrix(config, {"V10P": p_tracks, "V10Q": q_tracks, "V10R": r_tracks, "V10S": s_tracks})

    if reuse_existing:
        for key in ("derivative_blend", "blender_internal_manifest", "blender_execution_log"):
            if not outputs[key].is_file():
                raise RuntimeError(f"Cannot reuse missing V10T output: {outputs[key]}")
        execution = {
            "invoked_this_process": False,
            "reused_existing_single_blender_run": True,
            "return_code": 0,
            "execution_log": display_path(outputs["blender_execution_log"]),
        }
    else:
        execution = run_blender(config, outputs)

    master_after_hash = sha256_file(get_path(config["protected_files"], "blender_master"))
    require_equal("post-Blender master hash", master_after_hash, config["protected_files"][0]["expected_sha256"])
    blender_audit, render_manifest = audit_blender_outputs(config, outputs, execution)
    qa, qa_status = read_visual_qa(config, outputs, render_manifest)
    final_status = "PASS_STATIC_LABELLED_3D_STATUS_PACKAGE" if qa_status == "PASS" else "PENDING_MANUAL_VISUAL_QA"

    regression_audit = {
        "iteration": "V10T",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "regression_files_reverified_count": len(regression_rows),
        "protected_files_reverified_count": len(protected_rows),
        "cached_input_files_reverified_count": len(cached_rows),
        "official_source_hash_only_files_reverified_count": len(official_rows),
        "software_files_reverified_count": len(software_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "cached_input_files": cached_rows,
        "official_source_hash_only_files": official_rows,
        "software_files": software_rows,
        "master_sha256_after_blender": master_after_hash,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
    }
    source_manifest = {
        "iteration": "V10T",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "configuration": {"path": display_path(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "runner": {"path": display_path(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "blender_builder": {
            "path": display_path(outputs["blender_builder_script"]),
            "sha256": sha256_file(outputs["blender_builder_script"]),
        },
        "source_files": cached_rows + official_rows,
        "software_files": software_rows,
        "evidence_classes": {
            "observed_facts": "Current file identities, rendered image dimensions and hashes, static-scene and no-physics counters.",
            "official_model_results": "Only cached official-model-dependent impact/damage and thermal references already transcribed by V10P-V10R.",
            "archive_claims": "No source archive is read. One local official PDF is hash-checked without page access.",
            "model_hypotheses": "Colors, framing, cards and the Floors 93-99 reference frame are presentation choices with zero mechanical credit.",
            "derived_results": "Three-track by four-stage status matrix, derivative blend, six stills and proof sheet.",
            "unknowns": "Historical damage, fire, member temperatures, initiation, propagation, arrest and final outcome remain unknown.",
        },
    }
    gate = {
        "iteration": "V10T",
        "generated_at_utc": generated_at,
        "validation_status": final_status,
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "source_identity_gate": "PASS_11_CACHED_PLUS_1_OFFICIAL_HASH_ONLY",
        "software_identity_gate": "PASS_BLENDER_5_2_HASH",
        "three_track_separation_gate": "PASS_3_OF_3",
        "stage_status_matrix_gate": "PASS_12_OF_12_STATUS_ROWS",
        "static_scene_gate": "PASS_7_OF_7_FRAME_1_ONLY",
        "render_integrity_gate": "PASS_6_OF_6_PLUS_PROOF_SHEET",
        "manual_visual_qa_gate": qa_status,
        "blender_physics_gate": "PASS_ZERO_KEYFRAMES_RIGID_BODIES_PARTICLES_FLUIDS",
        "blender_feedback_to_calculations": False,
        "physical_state_release_gate": "CLOSED_0_RELEASED",
        "historical_outcome_assignment_gate": "CLOSED_0_ASSIGNED",
        "collapse_or_noncollapse_conclusion_authorized": False,
        "structural_solver_run_count": 0,
        "thermal_solver_run_count": 0,
        "fire_solver_run_count": 0,
        "propagation_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 1,
    }
    results = {
        "iteration": "V10T",
        "generated_at_utc": generated_at,
        "validation_status": final_status,
        "dataset": config["dataset"],
        "configuration": {"path": display_path(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "runner": {"path": display_path(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "blender_builder": {"path": display_path(outputs["blender_builder_script"]), "sha256": sha256_file(outputs["blender_builder_script"])},
        "source_summary": {
            "regression_file_count": len(regression_rows),
            "protected_file_count": len(protected_rows),
            "cached_input_file_count": len(cached_rows),
            "official_source_hash_only_file_count": len(official_rows),
            "software_file_count": len(software_rows),
        },
        "metrics": metrics,
        "status_matrix_summary": {
            "track_count": expected["track_count"],
            "stage_count": expected["stage_count"],
            "row_count": len(status_rows),
            "physical_state_release_count": sum(csv_bool(row["physical_state_released"]) for row in status_rows),
            "historical_outcome_assignment_count": sum(csv_bool(row["historical_outcome_assigned"]) for row in status_rows),
        },
        "blender_summary": {
            "version": blender_audit["blender_version"],
            "master": blender_audit["master"],
            "derivative": blender_audit["derivative"],
            "technical_check_count": blender_audit["check_count"],
            "technical_pass_count": blender_audit["pass_count"],
            "render_count": render_manifest["render_count"],
            "proof_sheet": render_manifest["proof_sheet"],
        },
        "manual_visual_qa_status": qa_status,
        "manual_visual_qa": qa,
        "gates": gate,
        "execution_counts": {
            "structural_solver_run_count": 0,
            "thermal_solver_run_count": 0,
            "fire_solver_run_count": 0,
            "propagation_solver_run_count": 0,
            "other_solver_run_count": 0,
            "gpu_compute_run_count": 0,
            "blender_run_count": 1,
        },
        "epistemic_separation": source_manifest["evidence_classes"],
        "runtime_seconds": time.perf_counter() - started,
        "next_iteration": config["next_iteration"],
    }

    write_json(outputs["regression_audit"], regression_audit)
    write_json(outputs["source_manifest"], source_manifest)
    write_csv(
        outputs["status_matrix"],
        [
            "track_id", "stage_id", "source_iteration", "source_track_id", "source_status",
            "epistemic_class", "visualization_status_released", "physical_state_released",
            "historical_outcome_assigned", "visual_encoding", "geometry_deformation_or_motion",
        ],
        status_rows,
    )
    write_json(outputs["blender_audit"], blender_audit)
    write_json(outputs["render_manifest"], render_manifest)
    write_json(outputs["handoff_gate"], gate)
    write_text(outputs["report"], report_text(generated_at, config, metrics, blender_audit, render_manifest, qa_status, final_status))
    write_json(outputs["results"], results)

    if qa_status == "PASS":
        artifact_roles = [
            "regression_audit", "source_manifest", "status_matrix", "blender_audit", "render_manifest",
            "visual_qa", "handoff_gate", "report", "results", "blender_execution_log",
            "blender_internal_manifest", "derivative_blend",
        ]
        artifacts = []
        for role in artifact_roles:
            path = outputs[role]
            if not path.is_file():
                raise RuntimeError(f"Missing final V10T artifact {role}: {path}")
            artifacts.append({"role": role, "path": display_path(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
        for record in render_manifest["renders"]:
            path = abs_path(record["path"])
            artifacts.append({"role": f"render_{record['shot_id']}", "path": record["path"], "sha256": record["sha256"], "bytes": record["bytes"]})
        proof = render_manifest["proof_sheet"]
        artifacts.append({"role": "proof_sheet", "path": proof["path"], "sha256": proof["sha256"], "bytes": proof["bytes"]})
        require_equal("audited artifact count", len(artifacts), expected["audited_artifact_count"])
        offline_audit = {
            "iteration": "V10T",
            "generated_at_utc": generated_at,
            "validation_status": "PASS",
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
            "configuration": {"path": display_path(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
            "runner": {"path": display_path(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
            "blender_builder": {"path": display_path(outputs["blender_builder_script"]), "sha256": sha256_file(outputs["blender_builder_script"])},
            "regression_files_reverified_count": len(regression_rows),
            "cached_input_files_reverified_count": len(cached_rows),
            "official_source_hash_only_files_reverified_count": len(official_rows),
            "official_source_pdf_page_read_count": 0,
            "official_source_pdf_text_extraction_count": 0,
            "protected_blender_master_unchanged": True,
            "manual_visual_qa_status": qa_status,
            "source_archive_read": False,
            "source_archive_modified": False,
            "official_sources_directory_modified": False,
            "physical_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
            "structural_solver_run_count": 0,
            "thermal_solver_run_count": 0,
            "fire_solver_run_count": 0,
            "propagation_solver_run_count": 0,
            "other_solver_run_count": 0,
            "gpu_compute_run_count": 0,
            "blender_run_count": 1,
        }
        write_json(outputs["offline_audit"], offline_audit)

    print(
        json.dumps(
            {
                "iteration": "V10T",
                "status": final_status,
                "tracks": expected["track_count"],
                "stages": expected["stage_count"],
                "status_rows": len(status_rows),
                "renders": render_manifest["render_count"],
                "scenes": config["expected"]["scene_count"],
                "manual_visual_qa": qa_status,
                "physical_state_releases": 0,
                "historical_outcomes_assigned": 0,
                "blender_runs": 1,
                "next_iteration": config["next_iteration"]["id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if qa_status == "PASS" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"V10T ERROR: {exc}", file=sys.stderr)
        raise
