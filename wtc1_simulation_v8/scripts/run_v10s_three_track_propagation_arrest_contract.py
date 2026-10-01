from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10s_three_track_propagation_arrest_contract.json"
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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
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


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise RuntimeError(f"Unexpected {label}: {actual!r} != {expected!r}")


def verified_file(item: dict[str, Any], read_mode: str) -> dict[str, Any]:
    path = abs_path(item["path"])
    role = item.get("role", item.get("id", "file"))
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != str(item["expected_sha256"]).lower():
        raise RuntimeError(
            f"Hash mismatch for {role}: expected {item['expected_sha256']}, got {actual}"
        )
    row: dict[str, Any] = {
        "role": role,
        "path": rel(path),
        "sha256": actual,
        "bytes": path.stat().st_size,
        "read_mode": read_mode,
        "status": "PASS",
    }
    for key in ("evidence_class", "use"):
        if key in item:
            row[key] = item[key]
    return row


def get_role_path(items: list[dict[str, Any]], role: str) -> Path:
    matches = [item for item in items if item.get("role") == role or item.get("id") == role]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one path for {role}, got {len(matches)}")
    return abs_path(matches[0]["path"])


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    require_equal("configuration iteration", config.get("iteration"), "V10S")
    expected = config["expected"]
    counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_input_file_count": len(config["cached_input_files"]),
        "official_source_hash_only_file_count": len(config["official_source_hash_only_files"]),
        "track_count": len(config["track_contract"]["required_track_ids"]),
        "legacy_interface_count": len(config["track_contract"]["legacy_interface_ids"]),
        "initiation_state_v2_required_field_count": len(
            config["propagation_contract_v2"]["initiation_state_v2"]["required_fields"]
        ),
        "propagation_outcome_v2_required_field_count": len(
            config["propagation_contract_v2"]["propagation_outcome_v2"]["required_fields"]
        ),
        "minimum_physical_requirement_count": len(config["minimum_physical_requirements"]),
        "conservation_ledger_field_count": len(config["conservation_ledger_fields"]),
    }
    for key, actual in counts.items():
        require_equal(key, actual, expected[key])
    require_equal(
        "track order",
        config["track_contract"]["required_track_ids"],
        [
            "CONTROL_ZERO_INITIATION_PROPAGATION",
            "OFFICIAL_DEPENDENT_PROPAGATION_BLOCKED",
            "UNKNOWN_PHYSICAL_PROPAGATION_OR_ARREST",
        ],
    )
    requirement_ids = [row["id"] for row in config["minimum_physical_requirements"]]
    if len(set(requirement_ids)) != len(requirement_ids):
        raise RuntimeError("Duplicate minimum physical requirement ID")
    return config


def audit_control_records(
    config: dict[str, Any], trace: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    i07 = trace["records"]["I07_INITIATION_TO_PROPAGATION"]
    i08 = trace["records"]["I08_PROPAGATION_TO_ENSEMBLE"]
    p07 = i07["payload"]
    p08 = i08["payload"]
    checks = {
        "i07_schema_id": i07["schema_id"] == "initiation_state_v1",
        "i07_time_zero": close(p07["time_s"], 0.0),
        "i07_failed_members_empty": p07["failed_members"] == [],
        "i07_displacements_empty": p07["displacements_m"] == {},
        "i07_velocities_empty": p07["velocities_m_s"] == {},
        "i07_participating_mass_zero": close(p07["participating_mass_kg"], 0.0),
        "i07_energy_zero": close(p07["energy_J"], 0.0),
        "i07_instability_time_null": p07["instability_time_s_or_null"] is None,
        "i07_control_label": p07["initiation_label"] == "CONTROL_NO_INITIATION",
        "i08_schema_id": i08["schema_id"] == "propagation_outcome_v1",
        "i08_control_outcome": p08["outcome_label"] == "CONTROL_NO_PROPAGATION",
        "i08_arrest_story_null": p08["arrest_story_or_null"] is None,
        "i08_energy_residual_zero": close(p08["energy_residual_J"], 0.0),
        "i08_momentum_residual_zero": close(p08["momentum_residual_kg_m_s"], 0.0),
        "i08_not_historical_probability": p08["fraction_is_historical_probability"] is False,
        "i08_explicit_not_historical_noncollapse_flag": "NOT_HISTORICAL_NONCOLLAPSE"
        in p08["validation_flags"],
    }
    expected = config["expected"]
    require_equal("control record check count", len(checks), expected["control_record_check_count"])
    require_equal(
        "control record pass count", sum(checks.values()), expected["control_record_pass_count"]
    )
    if not all(checks.values()):
        raise RuntimeError(
            "Control record audit failed: "
            + ", ".join(key for key, value in checks.items() if not value)
        )
    return i07, i08, {
        "check_count": len(checks),
        "pass_count": sum(checks.values()),
        "checks": checks,
        "terminal_label": p08["outcome_label"],
        "terminal_label_is_historical_noncollapse": False,
    }


def v2_field_names(config: dict[str, Any]) -> tuple[set[str], set[str]]:
    contract = config["propagation_contract_v2"]
    initiation = {row["name"] for row in contract["initiation_state_v2"]["required_fields"]}
    outcome = {row["name"] for row in contract["propagation_outcome_v2"]["required_fields"]}
    return initiation, outcome


def audit_legacy_interfaces(
    config: dict[str, Any],
    graph: dict[str, Any],
    schemas: dict[str, Any],
    trace: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    graph_by_id = {row["id"]: row for row in graph["interfaces"]}
    initiation_v2, outcome_v2 = v2_field_names(config)
    mapping: dict[tuple[str, str], list[str]] = {
        ("I07_INITIATION_TO_PROPAGATION", "time_s"): ["time_s"],
        ("I07_INITIATION_TO_PROPAGATION", "failed_members"): ["failed_members"],
        ("I07_INITIATION_TO_PROPAGATION", "displacements_m"): ["node_displacements_m"],
        ("I07_INITIATION_TO_PROPAGATION", "velocities_m_s"): ["node_velocities_m_s"],
        ("I07_INITIATION_TO_PROPAGATION", "participating_mass_kg"): [
            "participating_mass_by_component_kg",
            "total_participating_mass_kg",
        ],
        ("I07_INITIATION_TO_PROPAGATION", "energy_J"): [
            "kinetic_energy_J",
            "potential_energy_reference_J",
            "internal_energy_J",
        ],
        ("I07_INITIATION_TO_PROPAGATION", "boundary_state"): ["boundary_state"],
        ("I07_INITIATION_TO_PROPAGATION", "provenance"): ["provenance"],
        ("I08_PROPAGATION_TO_ENSEMBLE", "case_id"): ["case_id"],
        ("I08_PROPAGATION_TO_ENSEMBLE", "outcome_label"): ["outcome_label"],
        ("I08_PROPAGATION_TO_ENSEMBLE", "arrest_story_or_null"): [
            "arrest_story_or_null"
        ],
        ("I08_PROPAGATION_TO_ENSEMBLE", "conservation_residuals"): [
            "conservation_residuals"
        ],
        ("I08_PROPAGATION_TO_ENSEMBLE", "validation_flags"): ["validation_flags"],
        ("I08_PROPAGATION_TO_ENSEMBLE", "parameter_provenance"): [
            "parameter_provenance"
        ],
    }
    rows: list[dict[str, Any]] = []
    for interface_id in config["track_contract"]["legacy_interface_ids"]:
        graph_row = graph_by_id[interface_id]
        schema = schemas["interfaces"][interface_id]
        payload_schema = schema["payload_fields"]
        control_payload = trace["records"][interface_id]["payload"]
        required = [value.strip() for value in graph_row["required_fields"].split(",")]
        for field in required:
            schema_present = field in payload_schema
            control_present = field in control_payload
            targets = mapping[(interface_id, field)]
            v2_names = initiation_v2 if interface_id.startswith("I07") else outcome_v2
            addressed = all(target in v2_names for target in targets)
            if schema_present:
                resolution = "LEGACY_EXACT_FIELD_RETAINED_OR_REFINED_IN_V2"
            elif field == "boundary_state":
                resolution = "LEGACY_GAP_V2_ADDS_BOUNDARY_STATE"
            elif field == "conservation_residuals":
                resolution = "LEGACY_SPLIT_SCALARS_INCOMPLETE_V2_ADDS_AGGREGATE_MASS_VECTOR_MOMENTUM_ENERGY"
            else:
                resolution = "UNEXPECTED_UNRESOLVED_GAP"
            rows.append(
                {
                    "interface_id": interface_id,
                    "graph_schema_id": graph_row["schema"],
                    "graph_required_field": field,
                    "legacy_schema_exact_field_present": schema_present,
                    "legacy_control_payload_exact_field_present": control_present,
                    "v2_target_fields": ",".join(targets),
                    "v2_field_addressed": addressed,
                    "resolution": resolution,
                    "physical_data_available": False,
                }
            )
    expected = config["expected"]
    total = len(rows)
    exact_present = sum(row["legacy_schema_exact_field_present"] for row in rows)
    gaps = total - exact_present
    addressed = sum(row["v2_field_addressed"] for row in rows)
    by_interface = {}
    for interface_id in config["track_contract"]["legacy_interface_ids"]:
        selected = [row for row in rows if row["interface_id"] == interface_id]
        by_interface[interface_id] = {
            "graph_required_field_count": len(selected),
            "exact_present_field_count": sum(
                row["legacy_schema_exact_field_present"] for row in selected
            ),
            "exact_gap_count": sum(
                not row["legacy_schema_exact_field_present"] for row in selected
            ),
            "v2_addressed_count": sum(row["v2_field_addressed"] for row in selected),
        }
    require_equal("legacy graph required field count", total, expected["legacy_graph_required_field_count"])
    require_equal(
        "legacy exact present field count",
        exact_present,
        expected["legacy_schema_exact_present_field_count"],
    )
    require_equal("legacy exact gap count", gaps, expected["legacy_schema_exact_gap_count"])
    require_equal(
        "legacy fields addressed by v2",
        addressed,
        expected["legacy_graph_field_addressed_by_v2_count"],
    )
    require_equal(
        "I07 graph field count",
        by_interface["I07_INITIATION_TO_PROPAGATION"]["graph_required_field_count"],
        expected["i07_graph_required_field_count"],
    )
    require_equal(
        "I07 exact gap count",
        by_interface["I07_INITIATION_TO_PROPAGATION"]["exact_gap_count"],
        expected["i07_exact_gap_count"],
    )
    require_equal(
        "I08 graph field count",
        by_interface["I08_PROPAGATION_TO_ENSEMBLE"]["graph_required_field_count"],
        expected["i08_graph_required_field_count"],
    )
    require_equal(
        "I08 exact gap count",
        by_interface["I08_PROPAGATION_TO_ENSEMBLE"]["exact_gap_count"],
        expected["i08_exact_gap_count"],
    )
    if addressed != total:
        raise RuntimeError("Version-2 contract does not address every graph-required field")
    return rows, {
        "interface_count": len(config["track_contract"]["legacy_interface_ids"]),
        "graph_required_field_count": total,
        "legacy_schema_exact_present_field_count": exact_present,
        "legacy_schema_exact_gap_count": gaps,
        "v2_addressed_field_count": addressed,
        "by_interface": by_interface,
        "gap_fields": [
            {
                "interface_id": row["interface_id"],
                "field": row["graph_required_field"],
                "resolution": row["resolution"],
            }
            for row in rows
            if not row["legacy_schema_exact_field_present"]
        ],
        "v2_schema_is_physical_data": False,
    }


def build_minimum_requirement_rows(
    config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    for source in config["minimum_physical_requirements"]:
        rows.append(
            {
                **source,
                "physical_value": None,
                "source_document_or_model": None,
                "validation_evidence": None,
                "blocks_physical_propagation": not bool(source["physical_ready"]),
                "schema_specification_is_physical_evidence": False,
            }
        )
    ready = sum(bool(row["physical_ready"]) for row in rows)
    blocking = sum(bool(row["blocks_physical_propagation"]) for row in rows)
    expected = config["expected"]
    require_equal("minimum input rows", len(rows), expected["minimum_physical_requirement_count"])
    require_equal(
        "minimum physical ready rows", ready, expected["minimum_physical_ready_requirement_count"]
    )
    require_equal(
        "minimum physical blocking rows",
        blocking,
        expected["minimum_physical_blocking_requirement_count"],
    )
    by_category: dict[str, dict[str, int]] = {}
    for category in sorted({row["category"] for row in rows}):
        selected = [row for row in rows if row["category"] == category]
        by_category[category] = {
            "requirement_count": len(selected),
            "physical_ready_count": sum(row["physical_ready"] for row in selected),
            "blocking_count": sum(row["blocks_physical_propagation"] for row in selected),
        }
    return rows, {
        "requirement_count": len(rows),
        "physical_ready_count": ready,
        "blocking_count": blocking,
        "by_category": by_category,
    }


def vector_add(left: list[float], right: list[float]) -> list[float]:
    return [float(a) + float(b) for a, b in zip(left, right)]


def vector_subtract(left: list[float], right: list[float]) -> list[float]:
    return [float(a) - float(b) for a, b in zip(left, right)]


def vector_close(left: list[float], right: list[float]) -> bool:
    return len(left) == len(right) and all(close(a, b) for a, b in zip(left, right))


def build_conservation_ledger(
    config: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    fields = config["conservation_ledger_fields"]
    track_ids = config["track_contract"]["required_track_ids"]
    control_values: dict[str, Any] = {}
    for row in fields:
        control_values[row["field"]] = (
            [0.0, 0.0, 0.0] if row["value_kind"] == "vector3" else 0.0
        )
    rows = []
    for track_id in track_ids:
        for field in fields:
            if track_id == "CONTROL_ZERO_INITIATION_PROPAGATION":
                value = control_values[field["field"]]
                status = "CONTROL_ZERO_SENTINEL"
            elif track_id == "OFFICIAL_DEPENDENT_PROPAGATION_BLOCKED":
                value = None
                status = "NULL_UPSTREAM_INITIATION_BLOCKED"
            else:
                value = None
                status = "NULL_PHYSICAL_EVENT_UNKNOWN"
            rows.append(
                {
                    "track_id": track_id,
                    "field": field["field"],
                    "category": field["category"],
                    "value_kind": field["value_kind"],
                    "unit": field["unit"],
                    "value_json": None
                    if value is None
                    else json.dumps(value, separators=(",", ":")),
                    "status": status,
                    "value_is_physical_event_data": False,
                    "physical_ledger_ready": False,
                }
            )
    mass_balance = (
        control_values["initial_participating_mass_kg"]
        + control_values["entrained_mass_kg"]
        - control_values["ejected_mass_kg"]
        - control_values["final_accounted_mass_kg"]
    )
    momentum_balance = vector_subtract(
        vector_add(
            control_values["initial_momentum_vector_kg_m_s"],
            control_values["external_impulse_vector_N_s"],
        ),
        control_values["final_momentum_vector_kg_m_s"],
    )
    energy_balance = (
        control_values["initial_gravitational_potential_J"]
        + control_values["initial_kinetic_J"]
        + control_values["external_work_J"]
        - control_values["internal_strain_energy_J"]
        - control_values["fracture_energy_J"]
        - control_values["contact_dissipation_J"]
        - control_values["damping_dissipation_J"]
    )
    identity_checks = {
        "zero_control_mass_identity": close(
            mass_balance, control_values["mass_residual_kg"]
        ),
        "zero_control_vector_momentum_identity": vector_close(
            momentum_balance, control_values["momentum_residual_vector_kg_m_s"]
        ),
        "zero_control_energy_identity": close(
            energy_balance, control_values["final_energy_residual_J"]
        ),
    }
    populated = sum(row["value_json"] is not None for row in rows)
    null_count = len(rows) - populated
    expected = config["expected"]
    require_equal("conservation ledger rows", len(rows), expected["conservation_ledger_row_count"])
    require_equal(
        "control ledger populated fields",
        populated,
        expected["control_ledger_populated_field_count"],
    )
    require_equal("blocked ledger null fields", null_count, expected["blocked_ledger_null_field_count"])
    require_equal(
        "control conservation identity check count",
        len(identity_checks),
        expected["control_conservation_identity_check_count"],
    )
    require_equal(
        "control conservation identity pass count",
        sum(identity_checks.values()),
        expected["control_conservation_identity_pass_count"],
    )
    if not all(identity_checks.values()):
        raise RuntimeError("Zero-control conservation identity failed")
    return rows, {
        "ledger_field_count": len(fields),
        "track_count": len(track_ids),
        "row_count": len(rows),
        "control_populated_field_count": populated,
        "blocked_null_field_count": null_count,
        "control_identity_checks": identity_checks,
        "control_identity_check_count": len(identity_checks),
        "control_identity_pass_count": sum(identity_checks.values()),
        "physical_ledger_ready_track_count": 0,
        "physical_value_count": 0,
    }


def build_contract_v2(
    generated_at: str,
    config: dict[str, Any],
    interface_summary: dict[str, Any],
    requirement_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_SCHEMA_COVERAGE_ONLY",
        "contract_version": "2.0.0",
        "schemas": config["propagation_contract_v2"],
        "legacy_interface_audit": interface_summary,
        "minimum_physical_requirement_summary": requirement_summary,
        "outcome_label_vocabulary": [
            "PROPAGATES",
            "ARRESTS",
            "INDETERMINATE",
        ],
        "outcome_label_rule": "No physical label may be emitted until every blocking requirement and conservation/convergence gate passes.",
        "physical_ready": False,
        "physical_data_assignment_count": 0,
    }


def build_tracks(
    config: dict[str, Any],
    v10r_tracks: dict[str, Any],
    v10r_gate: dict[str, Any],
    control_i07: dict[str, Any],
    control_i08: dict[str, Any],
    control_audit: dict[str, Any],
    requirement_summary: dict[str, Any],
    ledger_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    upstream = {row["track_id"]: row for row in v10r_tracks["tracks"]}
    require_equal(
        "V10R physical release count", v10r_gate["downstream_physical_release_count"], 0
    )
    official_upstream = upstream["OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE"]
    unknown_upstream = upstream["UNKNOWN_PHYSICAL_INITIATION"]
    if "INDETERMINATE" not in official_upstream["status"]:
        raise RuntimeError("Official-dependent upstream track is not explicitly indeterminate")
    if "INDETERMINATE" not in unknown_upstream["status"]:
        raise RuntimeError("Unknown physical upstream track is not explicitly indeterminate")
    tracks = [
        {
            "track_id": "CONTROL_ZERO_INITIATION_PROPAGATION",
            "upstream_track_id": "CONTROL_ZERO_THERMAL_INPUT",
            "epistemic_class": "SYNTHETIC_ZERO_INPUT_SOFTWARE_CONTROL_NOT_HISTORICAL",
            "status": "CONTROL_NO_PROPAGATION_SOFTWARE_ONLY",
            "initiation_record_v1": control_i07,
            "propagation_outcome_v1": control_i08,
            "control_audit": control_audit,
            "control_conservation_identity_pass_count": ledger_summary[
                "control_identity_pass_count"
            ],
            "historical_noncollapse_claim": False,
            "downstream_visualization_status_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
        {
            "track_id": "OFFICIAL_DEPENDENT_PROPAGATION_BLOCKED",
            "upstream_track_id": "OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE",
            "epistemic_class": "OFFICIAL_MODEL_DEPENDENT_REFERENCE_WITH_NO_PHYSICAL_INITIATION_STATE",
            "status": "NOT_RUN_UPSTREAM_INITIATION_BLOCKED",
            "upstream_status": official_upstream["status"],
            "initiation_state_v2": None,
            "propagation_outcome_v2": None,
            "conservation_ledger_status": "NULL_UPSTREAM_INITIATION_BLOCKED",
            "minimum_physical_requirement_summary": requirement_summary,
            "outcome_label": None,
            "arrest_story_or_null": None,
            "historical_collapse_claim": False,
            "historical_noncollapse_claim": False,
            "downstream_visualization_status_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
        {
            "track_id": "UNKNOWN_PHYSICAL_PROPAGATION_OR_ARREST",
            "upstream_track_id": "UNKNOWN_PHYSICAL_INITIATION",
            "epistemic_class": "UNKNOWN_HISTORICAL_INITIATION_PROPAGATION_AND_ARREST_STATE",
            "status": "INDETERMINATE_UNKNOWN_PHYSICAL_EVENT",
            "upstream_status": unknown_upstream["status"],
            "initiation_state_v2": None,
            "propagation_outcome_v2": None,
            "mass_ledger": None,
            "vector_momentum_ledger": None,
            "energy_ledger": None,
            "contact_and_failure_history": None,
            "outcome_label": None,
            "arrest_story_or_null": None,
            "blocking_requirement_count": requirement_summary["blocking_count"],
            "historical_collapse_claim": False,
            "historical_noncollapse_claim": False,
            "downstream_visualization_status_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
    ]
    require_equal(
        "constructed track order",
        [row["track_id"] for row in tracks],
        config["track_contract"]["required_track_ids"],
    )
    physical_releases = sum(bool(row["downstream_physical_release"]) for row in tracks)
    summary = {
        "track_count": len(tracks),
        "track_ids": [row["track_id"] for row in tracks],
        "visualization_status_release_count": sum(
            bool(row["downstream_visualization_status_release"]) for row in tracks
        ),
        "physical_propagation_release_count": physical_releases,
        "historical_physical_initiation_assignment_count": 0,
        "historical_physical_propagation_assignment_count": 0,
        "control_terminal_label": control_i08["payload"]["outcome_label"],
        "control_terminal_label_is_historical_noncollapse": False,
        "official_dependent_outcome_is_null": tracks[1]["propagation_outcome_v2"] is None,
        "unknown_physical_ledgers_and_outcome_null": all(
            tracks[2][key] is None
            for key in (
                "initiation_state_v2",
                "propagation_outcome_v2",
                "mass_ledger",
                "vector_momentum_ledger",
                "energy_ledger",
                "contact_and_failure_history",
                "outcome_label",
                "arrest_story_or_null",
            )
        ),
    }
    require_equal(
        "physical propagation release count",
        physical_releases,
        config["expected"]["physical_propagation_release_count"],
    )
    if not summary["official_dependent_outcome_is_null"]:
        raise RuntimeError("Official-dependent propagation outcome must remain null")
    if not summary["unknown_physical_ledgers_and_outcome_null"]:
        raise RuntimeError("Unknown physical propagation branch received a non-null state")
    return tracks, summary


def report_text(
    generated_at: str,
    config: dict[str, Any],
    interface_summary: dict[str, Any],
    requirement_summary: dict[str, Any],
    ledger_summary: dict[str, Any],
    track_summary: dict[str, Any],
) -> str:
    categories = requirement_summary["by_category"]
    return "\n".join(
        [
            "# WTC 1 — V10S : contrat initiation → propagation/arrêt",
            "",
            f"Généré le {generated_at}. Aucun solveur de propagation, GPU ou Blender n’est lancé.",
            "",
            "## Résultat principal",
            "",
            "La chaîne logicielle possède désormais un contrat explicite pour séparer l’initiation de la propagation ou de l’arrêt. Ce contrat ne simule pas l’effondrement : la piste dépendante du modèle officiel s’arrête avant propagation, et la piste physique conserve un résultat entièrement inconnu.",
            "",
            f"Le contrôle nul reproduit exactement les enregistrements V10O et termine par `{track_summary['control_terminal_label']}`. Cette étiquette décrit uniquement un scénario logiciel sans masse, vitesse, énergie ni rupture ; elle n’est pas un résultat historique de non-effondrement.",
            "",
            "## Deux lacunes de contrat détectées",
            "",
            f"La comparaison exacte des interfaces I07/I08 trouve {interface_summary['legacy_schema_exact_present_field_count']}/{interface_summary['graph_required_field_count']} champs présents et deux écarts :",
            "",
            "- `boundary_state` est exigé par le graphe I07 mais absent du payload I07 V10O ;",
            "- `conservation_residuals` est exigé par I08, alors que V10O ne conserve que deux scalaires séparés, sans bilan de masse ni vecteur de quantité de mouvement.",
            "",
            "Le schéma V2 ajoute ces informations et distingue explicitement masse, quantité de mouvement vectorielle et énergie. Cela ferme une lacune de spécification, pas une lacune de données physiques.",
            "",
            "## Entrées physiques minimales",
            "",
            f"Les {requirement_summary['requirement_count']} exigences restent bloquantes : {categories['initial_state']['blocking_count']} pour l’état initial, {categories['resistance']['blocking_count']} pour la résistance et les interactions, {categories['validation']['blocking_count']} pour la validation numérique, et {categories['output']['blocking_count']} pour les sorties/critères. Zéro exigence est physiquement prête.",
            "",
            "Elles couvrent notamment les champs de déplacement et de vitesse, la masse participante par étage, les états d’effort, les lois d’assemblage et de contact, le flambement/post-flambement, la rupture objectivée au maillage, l’entraînement des débris, les frontières de la tour basse, puis les convergences en temps et en espace.",
            "",
            "## Bilans de conservation",
            "",
            f"Le gabarit contient {ledger_summary['ledger_field_count']} termes par piste, soit {ledger_summary['row_count']} lignes. Les {ledger_summary['control_populated_field_count']} valeurs égales à zéro du contrôle satisfont les trois identités masse/quantité de mouvement/énergie. Les {ledger_summary['blocked_null_field_count']} cellules des deux pistes non contrôles restent vides ; aucune tolérance physique n’est fabriquée.",
            "",
            "## Séparation des preuves",
            "",
            "1. **Faits observés ici** : empreintes, champs exacts des interfaces, deux écarts de schéma, comptages et identités nulles.",
            "2. **Résultats du modèle officiel** : aucun résultat officiel de propagation globale n’est importé ou supposé.",
            "3. **Archives** : aucune archive externe n’est lue ; un PDF officiel local est seulement rehaché.",
            "4. **Hypothèses du modèle** : le schéma V2 et la liste minimale sont des exigences de conception, pas des propriétés du WTC 1.",
            "5. **Résultats dérivés** : couverture de schéma, matrice des blocages et gabarit de conservation.",
            "6. **Inconnues** : l’état d’initiation, la propagation, l’arrêt et tous leurs bilans physiques.",
            "",
            "## Décision",
            "",
            "V10S ferme la chaîne de statuts sans fermer la question physique. Zéro simulation de propagation est exécutée, zéro résultat physique est libéré et aucune conclusion historique d’effondrement ou de non-effondrement n’est autorisée.",
            "",
            "## Prochaine étape",
            "",
            config["next_iteration"]["objective"],
        ]
    )


def main() -> int:
    started = time.perf_counter()
    generated_at = utc_now()
    config = load_config()
    expected = config["expected"]

    regression_rows = [
        verified_file(item, "FULL_ARTIFACT") for item in config["regression_files"]
    ]
    protected_rows = [
        verified_file(item, "HASH_ONLY_PROTECTED") for item in config["protected_files"]
    ]
    cached_rows = [
        verified_file(item, "FULL_ARTIFACT") for item in config["cached_input_files"]
    ]
    official_rows = [
        verified_file(item, "HASH_ONLY_NO_PAGE_READ")
        for item in config["official_source_hash_only_files"]
    ]

    regression_items = config["regression_files"]
    cached_items = config["cached_input_files"]
    v10r_tracks = load_json(get_role_path(regression_items, "v10r_track_manifest"))
    v10r_gate = load_json(get_role_path(regression_items, "v10r_gate"))
    graph = load_json(get_role_path(cached_items, "V10N_SOLVER_NEUTRAL_COUPLING_GRAPH"))
    schemas = load_json(get_role_path(cached_items, "V10O_INTERFACE_SCHEMAS"))
    trace = load_json(get_role_path(cached_items, "V10O_ZERO_CONTROL_TRACE"))

    require_equal("V10R gate status", v10r_gate["validation_status"], "PASS_SOFTWARE_PREPROCESSOR_ONLY")
    require_equal("V10R track count", len(v10r_tracks["tracks"]), expected["track_count"])

    control_i07, control_i08, control_audit = audit_control_records(config, trace)
    interface_rows, interface_summary = audit_legacy_interfaces(config, graph, schemas, trace)
    requirement_rows, requirement_summary = build_minimum_requirement_rows(config)
    ledger_rows, ledger_summary = build_conservation_ledger(config)
    contract_v2 = build_contract_v2(
        generated_at, config, interface_summary, requirement_summary
    )
    tracks, track_summary = build_tracks(
        config,
        v10r_tracks,
        v10r_gate,
        control_i07,
        control_i08,
        control_audit,
        requirement_summary,
        ledger_summary,
    )

    zero_counts = {
        "historical_physical_initiation_assignment_count": track_summary[
            "historical_physical_initiation_assignment_count"
        ],
        "historical_physical_propagation_assignment_count": track_summary[
            "historical_physical_propagation_assignment_count"
        ],
        "physical_propagation_release_count": track_summary[
            "physical_propagation_release_count"
        ],
        "structural_solver_run_count": 0,
        "propagation_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    for key, actual in zero_counts.items():
        require_equal(key, actual, expected[key])

    regression_audit = {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "regression_files_reverified_count": len(regression_rows),
        "protected_files_reverified_count": len(protected_rows),
        "cached_input_files_reverified_count": len(cached_rows),
        "official_source_hash_only_files_reverified_count": len(official_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "cached_input_files": cached_rows,
        "official_source_hash_only_files": official_rows,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
    }
    source_manifest = {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_files": cached_rows + official_rows,
        "evidence_classes": {
            "observed_facts": "Current file identities, exact interface fields, null states, counts and zero-control algebra.",
            "official_model_results": "No official global-propagation result is imported; upstream thermal references remain dependent and blocked.",
            "archive_claims": "No external archive is read; one local official PDF is hash-checked only.",
            "model_hypotheses": "The version-2 schemas and minimum requirement catalogue are design constraints, not WTC properties.",
            "derived_results": "Legacy interface coverage, gap resolutions, blocking matrix and conservation template.",
            "unknowns": "Historical initiation, participating mass, dynamic state, resistance, contact, propagation, arrest and conservation ledgers remain unresolved.",
        },
    }
    track_manifest = {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_THREE_TRACK_STATUS_CONTRACT_ONLY",
        "tracks": tracks,
        "summary": track_summary,
        "non_merging_rule": config["track_contract"]["status_rules"]["non_merging"],
    }
    gate = {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_SOFTWARE_STATUS_CONTRACT_ONLY",
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "source_identity_gate": "PASS_3_CACHED_PLUS_1_OFFICIAL_HASH_ONLY",
        "three_track_separation_gate": "PASS_3_OF_3",
        "v10o_control_replay_gate": "PASS_16_OF_16",
        "legacy_interface_exact_coverage_gate": "GAP_12_OF_14_FIELDS_PRESENT",
        "legacy_interface_gap_count": interface_summary["legacy_schema_exact_gap_count"],
        "v2_schema_coverage_gate": "PASS_14_OF_14_GRAPH_FIELDS_ADDRESSED_SCHEMA_ONLY",
        "minimum_physical_input_gate": "CLOSED_0_OF_32_READY",
        "control_conservation_gate": "PASS_3_OF_3_ZERO_SENTINEL_ONLY",
        "official_dependent_conservation_gate": "INDETERMINATE_ALL_17_FIELDS_NULL",
        "unknown_physical_conservation_gate": "INDETERMINATE_ALL_17_FIELDS_NULL",
        "initiation_to_propagation_physical_handoff_gate": "CLOSED_UPSTREAM_INITIATION_BLOCKED",
        "propagation_or_arrest_physical_gate": "CLOSED_NOT_RUN",
        "historical_physical_initiation_assignment_count": 0,
        "historical_physical_propagation_assignment_count": 0,
        "downstream_physical_release_count": 0,
        "v10t_visualization_status_package_authorized": True,
        "v10t_predicted_collapse_motion_authorized": False,
        "mechanical_source_gate": "OPEN_0_OF_22_REQUIREMENTS",
        "historical_collapse_or_noncollapse_conclusion_authorized": False,
        "structural_solver_run_count": 0,
        "propagation_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    runtime_seconds = time.perf_counter() - started
    results = {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_THREE_TRACK_PROPAGATION_STATUS_CONTRACT_ONLY",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_summary": {
            "regression_file_count": len(regression_rows),
            "protected_file_count": len(protected_rows),
            "cached_input_file_count": len(cached_rows),
            "official_source_hash_only_file_count": len(official_rows),
        },
        "control_audit": control_audit,
        "interface_summary": interface_summary,
        "requirement_summary": requirement_summary,
        "contract_v2_summary": {
            "initiation_state_v2_required_field_count": len(
                config["propagation_contract_v2"]["initiation_state_v2"]["required_fields"]
            ),
            "propagation_outcome_v2_required_field_count": len(
                config["propagation_contract_v2"]["propagation_outcome_v2"]["required_fields"]
            ),
            "physical_ready": False,
        },
        "conservation_ledger_summary": ledger_summary,
        "track_summary": track_summary,
        "gates": gate,
        "execution_counts": zero_counts,
        "epistemic_separation": source_manifest["evidence_classes"],
        "runtime_seconds": runtime_seconds,
        "next_iteration": config["next_iteration"],
    }

    outputs = {key: abs_path(value) for key, value in config["outputs"].items()}
    write_json(outputs["regression_audit"], regression_audit)
    write_json(outputs["source_manifest"], source_manifest)
    write_csv(
        outputs["interface_gap_matrix"],
        [
            "interface_id",
            "graph_schema_id",
            "graph_required_field",
            "legacy_schema_exact_field_present",
            "legacy_control_payload_exact_field_present",
            "v2_target_fields",
            "v2_field_addressed",
            "resolution",
            "physical_data_available",
        ],
        interface_rows,
    )
    write_csv(
        outputs["minimum_input_matrix"],
        [
            "id",
            "category",
            "requirement",
            "unit",
            "current_status",
            "physical_ready",
            "physical_value",
            "source_document_or_model",
            "validation_evidence",
            "blocks_physical_propagation",
            "schema_specification_is_physical_evidence",
        ],
        requirement_rows,
    )
    write_json(outputs["contract_v2"], contract_v2)
    write_csv(
        outputs["conservation_ledger"],
        [
            "track_id",
            "field",
            "category",
            "value_kind",
            "unit",
            "value_json",
            "status",
            "value_is_physical_event_data",
            "physical_ledger_ready",
        ],
        ledger_rows,
    )
    write_json(outputs["track_manifest"], track_manifest)
    write_json(outputs["handoff_gate"], gate)
    write_text(
        outputs["report"],
        report_text(
            generated_at,
            config,
            interface_summary,
            requirement_summary,
            ledger_summary,
            track_summary,
        ),
    )
    write_json(outputs["results"], results)

    audit_roles = [
        "regression_audit",
        "source_manifest",
        "interface_gap_matrix",
        "minimum_input_matrix",
        "contract_v2",
        "conservation_ledger",
        "track_manifest",
        "handoff_gate",
        "report",
        "results",
    ]
    artifacts = []
    for role in audit_roles:
        path = outputs[role]
        if not path.is_file():
            raise RuntimeError(f"Expected output was not written: {path}")
        artifacts.append(
            {
                "role": role,
                "path": rel(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    offline_audit = {
        "iteration": "V10S",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "regression_files_reverified_count": len(regression_rows),
        "cached_input_files_reverified_count": len(cached_rows),
        "official_source_hash_only_files_reverified_count": len(official_rows),
        "official_source_pdf_page_read_count": 0,
        "official_source_pdf_text_extraction_count": 0,
        "protected_blender_master_unchanged": True,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_sources_directory_modified": False,
        "historical_physical_initiation_assignment_count": 0,
        "historical_physical_propagation_assignment_count": 0,
        "downstream_physical_release_count": 0,
        "structural_solver_run_count": 0,
        "propagation_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(outputs["offline_audit"], offline_audit)

    print(
        json.dumps(
            {
                "iteration": "V10S",
                "status": results["validation_status"],
                "tracks": track_summary["track_count"],
                "legacy_graph_fields": interface_summary["graph_required_field_count"],
                "legacy_exact_gaps": interface_summary["legacy_schema_exact_gap_count"],
                "v2_addressed_fields": interface_summary["v2_addressed_field_count"],
                "minimum_physical_requirements": requirement_summary["requirement_count"],
                "minimum_physical_ready": requirement_summary["physical_ready_count"],
                "conservation_rows": ledger_summary["row_count"],
                "control_identity_checks_passed": ledger_summary[
                    "control_identity_pass_count"
                ],
                "physical_propagation_releases": track_summary[
                    "physical_propagation_release_count"
                ],
                "solver_runs": 0,
                "next_iteration": config["next_iteration"]["id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"V10S ERROR: {exc}", file=sys.stderr)
        raise
