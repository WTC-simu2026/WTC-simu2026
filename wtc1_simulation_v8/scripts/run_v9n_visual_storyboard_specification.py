#!/usr/bin/env python3
"""Generate the V9N visualization-only storyboard specification.

Only cached V8S and V9M JSON artifacts are read. No source archive, network,
solver, Blender process or post-contact physics is used.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v9n_visual_storyboard_specification.json"


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
            raise KeyError(f"Missing JSON path component {part!r} in {dotted_path!r}")
        value = value[part]
    return value


def compare(actual: Any, comparator: str, expected: Any) -> bool:
    if comparator == "equals":
        if isinstance(actual, float) or isinstance(expected, float):
            return math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12)
        return actual == expected
    raise ValueError(f"Unsupported comparator: {comparator}")


def verify_files(config: dict[str, Any]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for relative, expected in config["regression_files"].items():
        path = ROOT / relative
        exists = path.is_file()
        actual = sha256(path) if exists else None
        records[relative] = {
            "exists": exists,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "passed": exists and actual == expected,
        }
    return {"files": records, "passed": all(record["passed"] for record in records.values())}


def evaluate_metrics(config: dict[str, Any], cache: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    evaluated: list[dict[str, Any]] = []
    for declared in config["regression_metrics"]:
        relative = declared["results"]
        if relative not in cache:
            cache[relative] = load_json(ROOT / relative)
        actual = get_path(cache[relative], declared["path"])
        evaluated.append({
            **declared,
            "actual": actual,
            "passed": compare(actual, declared["comparator"], declared["expected"]),
        })
    return evaluated


def build_branches(config: dict[str, Any], v8s_results: dict[str, Any]) -> list[dict[str, Any]]:
    branches: list[dict[str, Any]] = []
    for branch_id, style in config["branch_style"].items():
        case = v8s_results["derived_results"]["cases"][branch_id]
        inputs = case["inputs"]
        kin = case["derived_kinematics"]
        positions = []
        for event_time_s in config["precontact_event_times_s"]:
            if event_time_s > 0:
                raise ValueError("V9N pre-contact event times must not exceed first contact")
            lead_s = -float(event_time_s)
            positions.append({
                "event_time_s": event_time_s,
                "distance_before_facade_m": kin["velocity_normal_to_facade_mps"] * lead_s,
                "height_above_contact_reference_m": kin["velocity_downward_mps"] * lead_s,
                "distance_along_velocity_vector_to_contact_m": inputs["speed_mps"] * lead_s,
                "motion_status": "constant_velocity_rigid_silhouette_precontact_only",
            })
        branches.append({
            "id": branch_id,
            "label": style["label"],
            "style": style,
            "input_status": "official_NIST_global_model_input_envelope_transcribed_in_V8S_not_probability",
            "inputs": {
                "mass_factor": inputs["mass_factor"],
                "mass_lb": inputs["mass_lb"],
                "mass_kg": inputs["mass_kg"],
                "speed_mph": inputs["speed_mph"],
                "speed_mps": inputs["speed_mps"],
                "trajectory_pitch_deg": inputs["trajectory_pitch_deg"],
                "orientation_pitch_deg": inputs["orientation_pitch_deg"],
                "roll_deg": inputs["roll_deg"],
            },
            "derived_precontact_kinematics": {
                "velocity_normal_to_facade_mps": kin["velocity_normal_to_facade_mps"],
                "velocity_downward_mps": kin["velocity_downward_mps"],
                "tail_clearance_time_s_data_card_only": kin["tail_clearance_time_s"],
            },
            "precontact_positions": positions,
            "maximum_animated_event_time_s": 0.0,
            "postcontact_motion_authorized": False,
        })
    return branches


def resolve_provenance(
    config: dict[str, Any],
    v8s_config: dict[str, Any],
    v8s_results: dict[str, Any],
    v9m_results: dict[str, Any],
    branches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    resolved_map: dict[str, Any] = {
        "P01_AIRCRAFT_GEOMETRY": v8s_config["aircraft_geometry"],
        "P02_VIDEO_KINEMATICS": v8s_config["video_kinematics"],
        "P03_THREE_GLOBAL_CASES": v8s_config["nist_global_input_cases"],
        "P04_DAMAGE_REFINED_LOCATION": v8s_config["damage_refined_kinematics"],
        "P05_TOWER_GEOMETRY": v8s_config["tower_geometry"],
        "P06_DERIVED_PRECONTACT_OFFSETS": {
            branch["id"]: branch["precontact_positions"] for branch in branches
        },
        "P07_TAIL_CLEARANCE_SCALE": {
            "less_severe_s": v8s_results["derived_results"]["cases"]["less_severe"]["derived_kinematics"]["tail_clearance_time_s"],
            "base_s": v8s_results["derived_results"]["cases"]["base"]["derived_kinematics"]["tail_clearance_time_s"],
            "more_severe_s": v8s_results["derived_results"]["cases"]["more_severe"]["derived_kinematics"]["tail_clearance_time_s"],
            "official_approx_s": v8s_results["comparison_to_reserved_official_outputs"]["tail_clearance"]["nist_reported_approx_s"],
            "display_rule": "data_card_only_no_aircraft_motion_after_contact",
        },
        "P08_PHYSICAL_QUALIFICATION_BOUNDARY": {
            "physical_facade_impact_qualification_passed": v9m_results["physical_facade_impact_qualification_passed"],
            "projectile_rupture_qualification_passed": v9m_results["projectile_rupture_qualification_passed"],
            "eroding_impulse_convergence_passed": v9m_results["eroding_impulse_convergence_passed"],
            "global_wtc_impact_physics_qualification_passed": v9m_results["global_wtc_impact_physics_qualification_passed"],
            "blender_physics_validation_passed": v9m_results["blender_physics_validation_passed"],
        },
    }
    items = []
    for declared in config["provenance_items"]:
        items.append({**declared, "resolved_value": resolved_map[declared["id"]]})
    return items


def validate_shots(config: dict[str, Any]) -> dict[str, Any]:
    shots = config["shot_templates"]
    camera_ids = {camera["id"] for camera in config["camera_definitions"]}
    provenance_ids = {item["id"] for item in config["provenance_items"]}
    start_at_zero = shots[0]["presentation_start_s"] == 0
    contiguous = all(
        shots[index]["presentation_end_s"] == shots[index + 1]["presentation_start_s"]
        for index in range(len(shots) - 1)
    )
    final_duration_matches = shots[-1]["presentation_end_s"] == config["storyboard_policy"]["presentation_duration_s"]
    cameras_known = all(shot["camera_id"] in camera_ids for shot in shots)
    provenance_known = all(
        set(shot["required_provenance_ids"]).issubset(provenance_ids) for shot in shots
    )
    positive_duration = all(shot["presentation_end_s"] > shot["presentation_start_s"] for shot in shots)
    precontact_motion_shots = [shot for shot in shots if shot["mode"] == "precontact_motion"]
    precontact_motion_bounded = all(max(shot["event_time_range_s"]) <= 0 for shot in precontact_motion_shots)
    postcontact_motion_shots = [
        shot for shot in shots
        if shot["mode"] in {"precontact_motion", "postcontact_motion"}
        and max(shot.get("event_time_range_s", [0])) > 0
    ]
    contact_shots = [shot for shot in shots if shot["mode"] == "frozen_contact_frame"]
    timing_cards = [shot for shot in shots if shot["mode"] == "postcontact_data_card_no_motion"]
    return {
        "start_at_zero": start_at_zero,
        "presentation_intervals_contiguous": contiguous,
        "final_duration_matches": final_duration_matches,
        "all_camera_ids_known": cameras_known,
        "all_provenance_ids_known": provenance_known,
        "all_shot_durations_positive": positive_duration,
        "precontact_motion_bounded_at_first_contact": precontact_motion_bounded,
        "precontact_motion_shot_count": len(precontact_motion_shots),
        "postcontact_motion_shot_count": len(postcontact_motion_shots),
        "frozen_contact_shot_count": len(contact_shots),
        "postcontact_data_card_count": len(timing_cards),
        "postcontact_motion_absent": len(postcontact_motion_shots) == 0,
        "contact_frame_is_frozen": len(contact_shots) == 1 and contact_shots[0].get("event_time_s") == 0.0,
        "timing_scale_is_card_only": len(timing_cards) == 1 and timing_cards[0].get("event_time_display_only") is True,
    }


def build_report(
    result: dict[str, Any],
    storyboard: dict[str, Any],
    provenance: list[dict[str, Any]],
) -> str:
    branch_rows = []
    for branch in storyboard["branches"]:
        inputs = branch["inputs"]
        kin = branch["derived_precontact_kinematics"]
        at_minus_quarter = next(
            item for item in branch["precontact_positions"] if item["event_time_s"] == -0.25
        )
        branch_rows.append(
            f"| {branch['label']} | {inputs['mass_kg']:.1f} | {inputs['speed_mph']:.0f} | "
            f"{inputs['trajectory_pitch_deg']:.1f}° | {at_minus_quarter['distance_before_facade_m']:.2f} | "
            f"{at_minus_quarter['height_above_contact_reference_m']:.2f} | {kin['tail_clearance_time_s_data_card_only']:.6f} |"
        )

    shot_rows = []
    for shot in storyboard["shots"]:
        shot_rows.append(
            f"| {shot['id']} | {shot['presentation_start_s']}–{shot['presentation_end_s']} s | "
            f"{shot['camera_id']} | `{shot['mode']}` | {shot['purpose']} |"
        )

    unknowns = [
        "rupture du projectile, des moteurs, des ailes ou du fuselage",
        "force, impulsion et pression sur la façade",
        "endommagement des colonnes, allèges, planchers et noyau",
        "trajectoires de débris et dispersion du carburant",
        "incendie, stabilité post-impact et réponse globale de la tour",
    ]

    return f"""# WTC 1 — V9N — Storyboard 3D illustratif

## Conclusion courte

V9N est une **spécification visuelle**, pas une simulation physique. Elle définit une présentation de 75 secondes et 11 plans. Le mouvement 3D est limité à l’approche avant contact. À `t = 0`, l’image se fige et toute la suite utilise uniquement des fiches explicatives.

Le bandeau « **VISUALISATION ILLUSTRATIVE — NON VALIDÉE PHYSIQUEMENT** » est obligatoire sur chaque plan. Aucun processus Blender n’a été lancé en V9N.

## 1. Faits directement observés ou transcrits

- Les huit fichiers de régression V8S/V9M correspondent à leurs empreintes enregistrées.
- V8S contient trois enveloppes d’entrée : basse, base et haute.
- La façade de référence est la face nord ; la largeur et la profondeur de tour gelées valent 63,1444 m.
- Les détails locaux de plaques, soudures, boulons, vitrages et assemblages restent incomplets.
- V9M maintient à `false` la qualification physique de l’impact façade, de la rupture, de la convergence avec érosion et de la réponse globale.

## 2. Résultats du modèle officiel utilisés

Les vitesses, angles, facteurs de masse et positions raffinées sont des entrées ou résultats officiels déjà transcrits dans V8S. Ils sont montrés avec leur provenance NIST. Les positions raffinées contre les dégâts de façade sont explicitement signalées comme **non indépendantes** du motif qu’elles ont servi à reproduire.

Le repère d’environ 0,25 s pour le dégagement de la queue est affiché sur une fiche de temps. Il ne déclenche aucun mouvement après contact.

## 3. Affirmations provenant de l’archive locale

Aucune nouvelle affirmation n’est introduite. L’archive source n’a été ni lue ni rescannée.

## 4. Hypothèses propres au storyboard

- Avant le contact seulement, la silhouette est rigide et se déplace à vitesse constante.
- Les couleurs, cadrages, durées et dispositions sont des choix de présentation.
- Les trois branches sont des enveloppes d’entrée, pas des probabilités de l’événement réel.
- Le photoréalisme éventuel ne devra jamais être présenté comme une précision physique.

## 5. Résultats dérivés

Les décalages avant contact sont calculés directement à partir des composantes de vitesse V8S. Exemple à `t = -0,25 s` :

| Branche | Masse (kg) | Vitesse (mph) | Pente | Distance avant façade (m) | Hauteur au-dessus du contact (m) | Repère de dégagement de queue (s, fiche seulement) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(branch_rows)}

Ces distances sont des positions géométriques avant contact. Aucune position positive après `t = 0` n’est produite.

### Découpage prévu

| Plan | Temps de présentation | Vue | Mode | Fonction |
|---|---:|---|---|---|
{chr(10).join(shot_rows)}

## 6. Contradictions et informations manquantes

Les éléments suivants restent inconnus ou physiquement non qualifiés :

{chr(10).join(f'- {item}' for item in unknowns)}

La valeur visuelle d’une scène ne résout aucun de ces manques. En particulier, aucun avion intact ne doit être animé au-delà du plan de contact nord.

## Règles de réalisation pour V9O

- Créer un nouveau fichier Blender ; ne pas modifier le master existant.
- Désactiver toute dynamique de corps rigide, collision, fracture, particules, carburant, feu ou structure.
- Animer uniquement les positions à temps négatif puis figer à `t = 0`.
- Remplacer les temps post-contact par des fiches graphiques.
- Afficher le bandeau de non-validation sur chaque image.
- Produire d’abord une planche-contact basse résolution, pas une animation finale coûteuse.

## Décision

La spécification est complète et contrôlée : {result['storyboard_shot_count']} plans, {result['camera_count']} vues définies, {result['provenance_item_count']} éléments de provenance et zéro plan de mouvement post-contact. La voie physique demeure dormante.
"""


def main() -> int:
    started = datetime.now().astimezone()
    config = load_json(CONFIG_PATH)
    v8s_config = load_json(ROOT / "wtc1_simulation_v8/data/v8s_wtc1_aircraft_impact_replay.json")
    v8s_results = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v8s_impact_avion.json")
    v9m_results = load_json(ROOT / "wtc1_simulation_v8/output/resultats_wtc1_v9m_cloture_branche_impact.json")
    cache = {
        "wtc1_simulation_v8/output/resultats_wtc1_v8s_impact_avion.json": v8s_results,
        "wtc1_simulation_v8/output/resultats_wtc1_v9m_cloture_branche_impact.json": v9m_results,
    }

    regressions = verify_files(config)
    metrics = evaluate_metrics(config, cache)
    metrics_passed = all(metric["passed"] for metric in metrics)
    branches = build_branches(config, v8s_results)
    provenance = resolve_provenance(config, v8s_config, v8s_results, v9m_results, branches)
    shot_checks = validate_shots(config)

    shots = config["shot_templates"]
    counts = {
        "branch_count": len(branches),
        "precontact_event_time_count": len(config["precontact_event_times_s"]),
        "camera_count": len(config["camera_definitions"]),
        "overlay_requirement_count": len(config["global_overlay_requirements"]),
        "provenance_item_count": len(provenance),
        "shot_count": len(shots),
        "precontact_motion_shot_count": shot_checks["precontact_motion_shot_count"],
        "frozen_contact_shot_count": shot_checks["frozen_contact_shot_count"],
        "postcontact_motion_shot_count": shot_checks["postcontact_motion_shot_count"],
        "forbidden_visual_claim_count": len(config["forbidden_visual_claims"]),
    }
    expected = config["expected_counts"]
    count_gates = {name: counts[name] == value for name, value in expected.items()}

    branch_ids = {branch["id"] for branch in branches}
    required_branch_ids = set(config["branch_style"])
    all_positions_nonnegative = all(
        point["distance_before_facade_m"] >= 0
        and point["height_above_contact_reference_m"] >= 0
        and point["distance_along_velocity_vector_to_contact_m"] >= 0
        for branch in branches
        for point in branch["precontact_positions"]
    )
    all_animated_times_nonpositive = all(
        point["event_time_s"] <= 0
        for branch in branches
        for point in branch["precontact_positions"]
    )
    safety_gates = {
        "V8S_and_V9M_regression_hashes_unchanged": regressions["passed"],
        "V8S_and_V9M_regression_metrics_unchanged": metrics_passed,
        "three_frozen_branches_match": branch_ids == required_branch_ids,
        "all_derived_precontact_offsets_nonnegative": all_positions_nonnegative,
        "all_animated_event_times_at_or_before_contact": all_animated_times_nonpositive,
        "all_shot_structure_checks_pass": all(
            bool(value) for key, value in shot_checks.items()
            if key not in {
                "precontact_motion_shot_count",
                "postcontact_motion_shot_count",
                "frozen_contact_shot_count",
                "postcontact_data_card_count",
            }
        ),
        "all_predeclared_counts_match": all(count_gates.values()),
        "permanent_non_validation_banner_present": bool(config["storyboard_policy"]["permanent_banner"]),
        "contact_stop_banner_present": bool(config["storyboard_policy"]["contact_boundary_banner"]),
        "postcontact_aircraft_motion_forbidden": config["storyboard_policy"]["post_contact_aircraft_motion_authorized"] is False,
        "postcontact_motion_shot_count_zero": shot_checks["postcontact_motion_shot_count"] == 0,
        "all_scope_gates_closed": all(value is False for value in config["scope_gates"].values()),
        "no_source_archive_network_solver_or_Blender": all(
            config["scope_gates"][name] is False
            for name in (
                "new_source_acquisition_authorized",
                "web_search_authorized",
                "source_archive_read_authorized",
                "source_archive_rescan_authorized",
                "solver_execution_authorized",
                "blender_execution_authorized",
            )
        ),
        "physical_track_remains_dormant": v9m_results["physical_track_reopening_authorized"] is False,
        "Blender_not_used_as_physical_validation": v9m_results["blender_physics_validation_passed"] is False,
    }
    execution_validated = all(safety_gates.values())

    uncertainty_overlay = {
        "speed_mph": {
            "base": v8s_config["video_kinematics"]["impact_speed_mph"],
            "plus_minus": v8s_config["video_kinematics"]["impact_speed_uncertainty_mph"],
            "status": "official_video_analysis_transcribed_in_V8S",
        },
        "vertical_approach_deg": {
            "base": v8s_config["video_kinematics"]["vertical_approach_deg_below_horizontal"],
            "plus_minus": v8s_config["video_kinematics"]["vertical_approach_uncertainty_deg"],
            "status": "official_video_analysis_transcribed_in_V8S",
        },
        "roll_deg": {
            "base": v8s_config["video_kinematics"]["roll_deg_left_wing_down"],
            "plus_minus": v8s_config["video_kinematics"]["roll_uncertainty_deg"],
            "status": "official_video_analysis_transcribed_in_V8S",
        },
        "damage_refined_nose_location_m": {
            "west_of_centerline": v8s_config["damage_refined_kinematics"]["nose_impact_west_of_centerline_ft"] * 0.3048,
            "horizontal_plus_minus": v8s_config["damage_refined_kinematics"]["nose_impact_horizontal_uncertainty_ft"] * 0.3048,
            "above_floor_96": v8s_config["damage_refined_kinematics"]["nose_impact_above_floor_96_ft"] * 0.3048,
            "vertical_plus_minus": v8s_config["damage_refined_kinematics"]["nose_impact_vertical_uncertainty_ft"] * 0.3048,
            "status": "official_damage_refined_setup_not_independent_validation",
        },
        "tower_geometry_warning": v8s_config["tower_geometry"]["geometry_status"],
    }

    storyboard = {
        "iteration": "V9N",
        "generated_at": started.isoformat(),
        "status": "validated_visualization_only_storyboard_specification_not_rendered" if execution_validated else "invalid_storyboard_specification_or_safety_gate_failed",
        "storyboard_policy": config["storyboard_policy"],
        "branch_style": config["branch_style"],
        "branches": branches,
        "uncertainty_overlay": uncertainty_overlay,
        "cameras": config["camera_definitions"],
        "global_overlays": config["global_overlay_requirements"],
        "shots": shots,
        "forbidden_visual_claims": config["forbidden_visual_claims"],
        "next_iteration": config["next_iteration"],
        "Blender_executed": False,
        "solver_executed": False,
    }
    provenance_output = {
        "iteration": "V9N",
        "generated_at": started.isoformat(),
        "evidence_policy": config["evidence_policy"],
        "cached_inputs": config["cached_inputs"],
        "provenance_items": provenance,
        "provenance_item_count": len(provenance),
        "source_archive_read": False,
        "source_archive_rescanned": False,
    }
    checklist_output = {
        "iteration": "V9N",
        "generated_at": started.isoformat(),
        "regressions": {**regressions, "metrics": metrics, "metrics_passed": metrics_passed},
        "shot_checks": shot_checks,
        "counts": counts,
        "count_gates": count_gates,
        "safety_gates": safety_gates,
        "passed": execution_validated,
    }
    result = {
        "iteration": "V9N",
        "generated_at": started.isoformat(),
        "status": "completed_validated_visualization_only_storyboard_specification_no_blender_no_solver" if execution_validated else "invalid_storyboard_specification_or_safety_gate_failed",
        "iteration_execution_validated": execution_validated,
        "storyboard_specification_gate_passed": execution_validated,
        "configuration": str(CONFIG_PATH.relative_to(ROOT)).replace("\\", "/"),
        "storyboard_specification": config["output"]["storyboard_specification"],
        "provenance_matrix": config["output"]["provenance_matrix"],
        "safety_checklist": config["output"]["safety_checklist"],
        "scope": config["dataset"]["scope"],
        "evidence_policy": config["evidence_policy"],
        "regressions_passed": regressions["passed"] and metrics_passed,
        "storyboard_duration_s": config["storyboard_policy"]["presentation_duration_s"],
        "storyboard_shot_count": len(shots),
        "branch_count": len(branches),
        "camera_count": len(config["camera_definitions"]),
        "overlay_requirement_count": len(config["global_overlay_requirements"]),
        "provenance_item_count": len(provenance),
        "precontact_motion_shot_count": shot_checks["precontact_motion_shot_count"],
        "frozen_contact_shot_count": shot_checks["frozen_contact_shot_count"],
        "postcontact_motion_shot_count": shot_checks["postcontact_motion_shot_count"],
        "maximum_animated_event_time_s": config["storyboard_policy"]["maximum_animated_event_time_s"],
        "permanent_non_validation_banner": config["storyboard_policy"]["permanent_banner"],
        "physical_track_reopening_authorized": False,
        "physical_facade_impact_qualification_passed": False,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "scope_gates": config["scope_gates"],
        "safety_gate_summary": {"gates": safety_gates, "passed": execution_validated},
        "next_iteration": config["next_iteration"],
        "interpretation": (
            "V9N validates only a visualization specification. Three frozen V8S input envelopes are represented by constant-velocity rigid silhouettes at four non-positive event times. "
            "All motion stops at first contact; later timing is shown on a data card only. Eleven shots, five cameras, five overlay requirements and eight provenance items are defined, with zero post-contact motion shots. "
            "No Blender or solver process is executed, and no physical facade, rupture, debris, fuel, fire or tower-response claim is made."
        ),
        "runtime": {
            "started_at": started.isoformat(),
            "completed_at": datetime.now().astimezone().isoformat(),
            "software": "Python standard-library deterministic cached storyboard synthesis",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "random_seed": config["dataset"]["random_seed"],
            "network_access_used": False,
            "new_source_acquired": False,
            "source_archive_read": False,
            "source_archive_rescanned": False,
            "solver_executed": False,
            "blender_executed": False,
            "physics_engine_executed": False,
            "external_contact_made": False,
            "FOIA_request_sent": False,
        },
    }

    write_json(ROOT / config["output"]["storyboard_specification"], storyboard)
    write_json(ROOT / config["output"]["provenance_matrix"], provenance_output)
    write_json(ROOT / config["output"]["safety_checklist"], checklist_output)
    write_json(ROOT / config["output"]["results"], result)
    write_text(ROOT / config["output"]["report"], build_report(result, storyboard, provenance))

    print(json.dumps({
        "iteration": "V9N",
        "execution_validated": execution_validated,
        "branch_count": len(branches),
        "shot_count": len(shots),
        "postcontact_motion_shot_count": shot_checks["postcontact_motion_shot_count"],
        "maximum_animated_event_time_s": config["storyboard_policy"]["maximum_animated_event_time_s"],
        "solver_executed": False,
        "blender_executed": False,
        "next_iteration": config["next_iteration"]["id"],
    }, ensure_ascii=False, indent=2))
    return 0 if execution_validated else 1


if __name__ == "__main__":
    sys.exit(main())
