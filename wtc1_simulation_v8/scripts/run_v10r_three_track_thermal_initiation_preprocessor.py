from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10r_three_track_thermal_initiation_preprocessor.json"
SCRIPT_PATH = Path(__file__).resolve()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


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


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise RuntimeError(f"Unexpected {label}: {actual!r} != {expected!r}")


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    require_equal("configuration iteration", config.get("iteration"), "V10R")
    expected = config["expected"]
    counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_input_file_count": len(config["cached_input_files"]),
        "official_source_hash_only_file_count": len(config["official_source_hash_only_files"]),
        "track_count": len(config["track_contract"]["required_track_ids"]),
    }
    for key, actual in counts.items():
        require_equal(key, actual, expected[key])
    require_equal(
        "track order",
        config["track_contract"]["required_track_ids"],
        [
            "CONTROL_ZERO_THERMAL_INPUT",
            "OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE",
            "UNKNOWN_PHYSICAL_INITIATION",
        ],
    )
    material = config["track_contract"]["material_model"]
    require_equal(
        "conservative joint material domain",
        material["conservative_joint_evaluation_range_c"],
        [0.0, 600.0],
    )
    require_equal(
        "declared Young modulus domain",
        material["young_modulus_declared_valid_temperature_range_c"],
        [0.0, 600.0],
    )
    return config


def yield_ratio(temp_c: float, parameters: dict[str, float]) -> float:
    a2 = float(parameters["A2"])
    exponent = -0.5 * (
        (temp_c / float(parameters["s1_c"])) ** float(parameters["m1"])
        + (temp_c / float(parameters["s2_c"])) ** float(parameters["m2"])
    )
    return (1.0 - a2) * math.exp(exponent) + a2


def young_modulus_gpa(temp_c: float, parameters: dict[str, float]) -> float:
    return (
        float(parameters["e0"])
        + float(parameters["e1"]) * temp_c
        + float(parameters["e2"]) * temp_c**2
        + float(parameters["e3"]) * temp_c**3
    )


def material_value(
    temp_c: float,
    domain: list[float],
    fy_parameters: dict[str, float],
    e_parameters: dict[str, float],
    fy20: float,
    e20: float,
) -> dict[str, Any]:
    valid = float(domain[0]) <= temp_c <= float(domain[1])
    if not valid:
        return {
            "domain_valid": False,
            "yield_ratio_direct": None,
            "yield_ratio_to_20c": None,
            "young_modulus_gpa": None,
            "young_modulus_ratio_to_20c": None,
        }
    fy = yield_ratio(temp_c, fy_parameters)
    e = young_modulus_gpa(temp_c, e_parameters)
    return {
        "domain_valid": True,
        "yield_ratio_direct": fy,
        "yield_ratio_to_20c": fy / fy20,
        "young_modulus_gpa": e,
        "young_modulus_ratio_to_20c": e / e20,
    }


def build_material_law_audit(
    config: dict[str, Any], transfer: dict[str, Any]
) -> dict[str, Any]:
    declared = transfer["steel_temperature_model"]
    selected = config["track_contract"]["material_model"]
    identity_checks = {
        "yield_equation_exact": declared["yield_ratio_equation"]
        == selected["yield_ratio_equation"],
        "yield_parameters_exact": declared["yield_ratio_parameters"]
        == selected["yield_ratio_parameters"],
        "young_modulus_equation_exact": declared["young_modulus_gpa_equation_0_to_600_c"]
        == selected["young_modulus_gpa_equation"],
        "young_modulus_parameters_exact": declared["young_modulus_parameters"]
        == selected["young_modulus_parameters"],
        "young_modulus_domain_exact": [
            float(value) for value in declared["young_modulus_valid_temperature_range_c"]
        ]
        == selected["young_modulus_declared_valid_temperature_range_c"],
    }
    if not all(identity_checks.values()):
        raise RuntimeError(
            "Material transcription identity failed: "
            + ", ".join(key for key, value in identity_checks.items() if not value)
        )
    fy_parameters = selected["yield_ratio_parameters"]
    e_parameters = selected["young_modulus_parameters"]
    reference_temperature = float(selected["reference_temperature_c"])
    fy20 = yield_ratio(reference_temperature, fy_parameters)
    e20 = young_modulus_gpa(reference_temperature, e_parameters)
    anchors = []
    for temp_c in selected["anchor_temperatures_c"]:
        value = material_value(
            float(temp_c),
            selected["conservative_joint_evaluation_range_c"],
            fy_parameters,
            e_parameters,
            fy20,
            e20,
        )
        anchors.append({"temperature_c": float(temp_c), **value})
    start, end = selected["conservative_joint_evaluation_range_c"]
    step = float(selected["domain_grid_step_c"])
    point_count = int(round((float(end) - float(start)) / step)) + 1
    temperatures = [float(start) + index * step for index in range(point_count)]
    fy_grid = [yield_ratio(value, fy_parameters) for value in temperatures]
    e_grid = [young_modulus_gpa(value, e_parameters) for value in temperatures]
    fy_monotonic = [right <= left + 1e-12 for left, right in zip(fy_grid, fy_grid[1:])]
    e_monotonic = [right <= left + 1e-12 for left, right in zip(e_grid, e_grid[1:])]
    if not all(fy_monotonic) or not all(e_monotonic):
        raise RuntimeError("Selected material law is not non-increasing over the predeclared grid")
    expected = config["expected"]
    require_equal("material anchor count", len(anchors), expected["material_anchor_count"])
    require_equal(
        "material domain grid point count",
        len(temperatures),
        expected["material_domain_grid_point_count"],
    )
    require_equal(
        "yield monotonic check count",
        len(fy_monotonic),
        expected["yield_monotonic_adjacent_check_count"],
    )
    require_equal(
        "Young modulus monotonic check count",
        len(e_monotonic),
        expected["young_modulus_monotonic_adjacent_check_count"],
    )
    return {
        "iteration": "V10R",
        "identity_check_count": len(identity_checks),
        "identity_pass_count": sum(identity_checks.values()),
        "identity_checks": identity_checks,
        "selected_equations": {
            "yield_ratio": selected["yield_ratio_equation"],
            "young_modulus_gpa": selected["young_modulus_gpa_equation"],
        },
        "selected_parameters": {
            "yield_ratio": fy_parameters,
            "young_modulus": e_parameters,
        },
        "declared_yield_ratio_domain": None,
        "declared_young_modulus_domain_c": selected[
            "young_modulus_declared_valid_temperature_range_c"
        ],
        "conservative_joint_domain_c": selected["conservative_joint_evaluation_range_c"],
        "reference_temperature_c": reference_temperature,
        "yield_ratio_direct_at_20c": fy20,
        "young_modulus_gpa_at_20c": e20,
        "anchors": anchors,
        "anchor_count": len(anchors),
        "domain_grid": {
            "start_c": start,
            "end_c": end,
            "step_c": step,
            "point_count": len(temperatures),
            "yield_nonincreasing_adjacent_check_count": len(fy_monotonic),
            "yield_nonincreasing_pass_count": sum(fy_monotonic),
            "young_modulus_nonincreasing_adjacent_check_count": len(e_monotonic),
            "young_modulus_nonincreasing_pass_count": sum(e_monotonic),
            "yield_ratio_direct_minimum": min(fy_grid),
            "yield_ratio_direct_maximum": max(fy_grid),
            "young_modulus_gpa_minimum": min(e_grid),
            "young_modulus_gpa_maximum": max(e_grid),
        },
        "tail_model_invoked": False,
        "above_600c_evaluation_count": 0,
        "member_property_assignment_count": 0,
        "physical_validation": False,
    }


def build_material_matrix(
    config: dict[str, Any], input_rows: list[dict[str, str]], law_audit: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected = config["expected"]
    require_equal(
        "V10Q temperature row count",
        len(input_rows),
        expected["temperature_envelope_row_count"],
    )
    material = config["track_contract"]["material_model"]
    domain = material["conservative_joint_evaluation_range_c"]
    fy_parameters = material["yield_ratio_parameters"]
    e_parameters = material["young_modulus_parameters"]
    fy20 = float(law_audit["yield_ratio_direct_at_20c"])
    e20 = float(law_audit["young_modulus_gpa_at_20c"])
    rows: list[dict[str, Any]] = []
    for input_row in input_rows:
        minimum_c = float(input_row["temperature_min_c"])
        maximum_c = float(input_row["temperature_max_c"])
        if minimum_c > maximum_c:
            raise RuntimeError("Input temperature range is reversed")
        low = material_value(
            minimum_c, domain, fy_parameters, e_parameters, fy20, e20
        )
        high = material_value(
            maximum_c, domain, fy_parameters, e_parameters, fy20, e20
        )
        if low["domain_valid"] and high["domain_valid"]:
            status = "COMPLETE_IN_DOMAIN_REFERENCE_ONLY"
        elif low["domain_valid"] or high["domain_valid"]:
            status = "PARTIAL_DOMAIN_BLOCKED"
        else:
            status = "FULLY_DOMAIN_BLOCKED"
        complete = status == "COMPLETE_IN_DOMAIN_REFERENCE_ONLY"
        rows.append(
            {
                "track_id": "OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE",
                "upstream_track_id": input_row["track_id"],
                "component_family": input_row["component_family"],
                "floor": int(input_row["floor"]),
                "time_min": int(float(input_row["time_min"])),
                "time_s": float(input_row["time_s"]),
                "temperature_min_c": minimum_c,
                "temperature_max_c": maximum_c,
                "minimum_joint_domain_valid": low["domain_valid"],
                "maximum_joint_domain_valid": high["domain_valid"],
                "yield_ratio_direct_at_minimum": low["yield_ratio_direct"],
                "yield_ratio_direct_at_maximum": high["yield_ratio_direct"],
                "yield_ratio_to_20c_at_minimum": low["yield_ratio_to_20c"],
                "yield_ratio_to_20c_at_maximum": high["yield_ratio_to_20c"],
                "young_modulus_gpa_at_minimum": low["young_modulus_gpa"],
                "young_modulus_gpa_at_maximum": high["young_modulus_gpa"],
                "young_modulus_ratio_to_20c_at_minimum": low[
                    "young_modulus_ratio_to_20c"
                ],
                "young_modulus_ratio_to_20c_at_maximum": high[
                    "young_modulus_ratio_to_20c"
                ],
                "complete_yield_ratio_interval_lower": high["yield_ratio_direct"]
                if complete
                else None,
                "complete_yield_ratio_interval_upper": low["yield_ratio_direct"]
                if complete
                else None,
                "complete_young_modulus_gpa_interval_lower": high["young_modulus_gpa"]
                if complete
                else None,
                "complete_young_modulus_gpa_interval_upper": low["young_modulus_gpa"]
                if complete
                else None,
                "range_status": status,
                "tail_model_invoked": False,
                "exact_member_temperature_assignment": False,
                "member_section_assignment": False,
                "member_capacity_assignment": False,
                "initiation_state_assignment": False,
                "physical_initiation_release": False,
                "evidence_class": "OFFICIAL_MODEL_DEPENDENT_RANGE_PLUS_DERIVED_REDUCTION_REFERENCE",
            }
        )
    endpoint_valid_count = sum(
        int(row["minimum_joint_domain_valid"]) + int(row["maximum_joint_domain_valid"])
        for row in rows
    )
    endpoint_count = 2 * len(rows)
    complete_count = sum(
        row["range_status"] == "COMPLETE_IN_DOMAIN_REFERENCE_ONLY" for row in rows
    )
    partial_count = sum(row["range_status"] == "PARTIAL_DOMAIN_BLOCKED" for row in rows)
    fully_blocked_count = sum(row["range_status"] == "FULLY_DOMAIN_BLOCKED" for row in rows)
    blocked = [row for row in rows if not row["maximum_joint_domain_valid"]]
    by_family = {
        family: sum(row["component_family"] == family for row in blocked)
        for family in expected["blocked_maxima_by_family"]
    }
    by_time = {
        str(value): sum(row["time_min"] == int(value) for row in blocked)
        for value in expected["blocked_maxima_by_time_min"]
    }
    by_floor = {
        str(value): sum(row["floor"] == int(value) for row in blocked)
        for value in expected["blocked_maxima_by_floor"]
    }
    checks = {
        "temperature_endpoint_count": endpoint_count,
        "joint_domain_valid_endpoint_count": endpoint_valid_count,
        "joint_domain_blocked_endpoint_count": endpoint_count - endpoint_valid_count,
        "complete_reduced_property_range_count": complete_count,
        "partial_domain_blocked_range_count": partial_count,
        "fully_blocked_range_count": fully_blocked_count,
    }
    for key, actual in checks.items():
        require_equal(key, actual, expected[key])
    require_equal("blocked maxima by family", by_family, expected["blocked_maxima_by_family"])
    require_equal("blocked maxima by time", by_time, expected["blocked_maxima_by_time_min"])
    require_equal("blocked maxima by floor", by_floor, expected["blocked_maxima_by_floor"])
    return rows, {
        "temperature_envelope_row_count": len(rows),
        **checks,
        "blocked_maxima_by_family": by_family,
        "blocked_maxima_by_time_min": by_time,
        "blocked_maxima_by_floor": by_floor,
        "tail_model_invocation_count": 0,
        "member_temperature_assignment_count": 0,
        "member_section_assignment_count": 0,
        "member_capacity_assignment_count": 0,
        "physical_initiation_release_count": 0,
    }


def deterministic_signature(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "elastic_modulus_tail"}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def ensemble_signature(row: dict[str, Any]) -> str:
    payload = {key: value for key, value in row.items() if key != "elastic_modulus_tail"}
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def audit_legacy_v8e(
    config: dict[str, Any],
    v8e: dict[str, Any],
    temperature_rows: list[dict[str, str]],
    cold_gate_passed: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected = config["expected"]
    rules = config["track_contract"]["legacy_v8e_audit"]
    tail_models = set(rules["tail_models"])
    deterministic = list(v8e["deterministic_cases"])
    ensembles = list(v8e["smooth_field_ensemble"])
    require_equal(
        "V8E deterministic row count",
        len(deterministic),
        expected["v8e_deterministic_row_count"],
    )
    require_equal(
        "V8E ensemble row count", len(ensembles), expected["v8e_ensemble_row_count"]
    )

    deterministic_groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    deterministic_maxima: dict[int, float] = {}
    for index, row in enumerate(deterministic):
        deterministic_groups[(int(row["time_min"]), str(row["field"]))].append(row)
        deterministic_maxima[index] = max(
            float(floor["temperature_max_assigned_c"])
            for floor in row["floors"].values()
        )
    deterministic_pair_identical: dict[tuple[int, str], bool] = {}
    for key, rows in deterministic_groups.items():
        require_equal(f"deterministic tail pair size {key}", len(rows), 2)
        require_equal(
            f"deterministic tail labels {key}",
            {row["elastic_modulus_tail"] for row in rows},
            tail_models,
        )
        deterministic_pair_identical[key] = len(
            {deterministic_signature(row) for row in rows}
        ) == 1

    core_maximum_by_time: dict[int, float] = {}
    v8e_floors = {int(value) for value in v8e["facts_transferred"]["floors"]}
    for time_min in v8e["facts_transferred"]["times_min"]:
        candidates = [
            float(row["temperature_max_c"])
            for row in temperature_rows
            if row["component_family"] == "core_column"
            and int(row["floor"]) in v8e_floors
            and int(float(row["time_min"])) == int(time_min)
        ]
        if not candidates:
            raise RuntimeError(f"No V8E core maximum support at {time_min} min")
        core_maximum_by_time[int(time_min)] = max(candidates)

    ensemble_groups: dict[tuple[int, float], list[dict[str, Any]]] = defaultdict(list)
    for row in ensembles:
        ensemble_groups[(int(row["time_min"]), float(row["gamma"]))].append(row)
    ensemble_pair_identical: dict[tuple[int, float], bool] = {}
    for key, rows in ensemble_groups.items():
        require_equal(f"ensemble tail pair size {key}", len(rows), 2)
        require_equal(
            f"ensemble tail labels {key}",
            {row["elastic_modulus_tail"] for row in rows},
            tail_models,
        )
        ensemble_pair_identical[key] = len({ensemble_signature(row) for row in rows}) == 1

    audit_rows: list[dict[str, Any]] = []
    for index, row in enumerate(deterministic):
        maximum = deterministic_maxima[index]
        inside = maximum <= 600.0
        failed_floor_count = sum(not bool(value["equilibrium"]) for value in row["floors"].values())
        audit_rows.append(
            {
                "record_type": "DETERMINISTIC_CASE",
                "time_min": int(row["time_min"]),
                "elastic_modulus_tail": row["elastic_modulus_tail"],
                "field_or_gamma": row["field"],
                "maximum_assigned_or_supported_temperature_c": maximum,
                "declared_modulus_domain_status": "INSIDE_0_600_C" if inside else "EXCEEDS_600_C",
                "tail_pair_outcome_identical": deterministic_pair_identical[
                    (int(row["time_min"]), str(row["field"]))
                ],
                "system_equilibrium_all_floors": row["system_equilibrium_all_floors"],
                "system_no_equilibrium_fraction": None,
                "failed_floor_count": failed_floor_count,
                "v8e_fraction_is_event_probability": False,
                "cold_gate_passed": cold_gate_passed,
                "result_physically_authorized": False,
                "withheld_reason": "FAILED_COLD_GATE_AND_SYNTHETIC_FIELD"
                if inside
                else "FAILED_COLD_GATE_SYNTHETIC_FIELD_AND_UNDECLARED_MODULUS_TAIL",
            }
        )
    for row in ensembles:
        maximum = core_maximum_by_time[int(row["time_min"])]
        audit_rows.append(
            {
                "record_type": "SMOOTH_FIELD_AGGREGATE",
                "time_min": int(row["time_min"]),
                "elastic_modulus_tail": row["elastic_modulus_tail"],
                "field_or_gamma": float(row["gamma"]),
                "maximum_assigned_or_supported_temperature_c": maximum,
                "declared_modulus_domain_status": "EXCEEDS_600_C",
                "tail_pair_outcome_identical": ensemble_pair_identical[
                    (int(row["time_min"]), float(row["gamma"]))
                ],
                "system_equilibrium_all_floors": None,
                "system_no_equilibrium_fraction": row["system_no_equilibrium_fraction"],
                "failed_floor_count": None,
                "v8e_fraction_is_event_probability": False,
                "cold_gate_passed": cold_gate_passed,
                "result_physically_authorized": False,
                "withheld_reason": "FAILED_COLD_GATE_SYNTHETIC_ENSEMBLE_AND_UNDECLARED_MODULUS_TAIL",
            }
        )
    deterministic_inside = sum(
        row["record_type"] == "DETERMINISTIC_CASE"
        and row["declared_modulus_domain_status"] == "INSIDE_0_600_C"
        for row in audit_rows
    )
    deterministic_outside = len(deterministic) - deterministic_inside
    deterministic_inside_pairs = [
        key
        for key, rows in deterministic_groups.items()
        if max(
            float(floor["temperature_max_assigned_c"])
            for floor in rows[0]["floors"].values()
        )
        <= 600.0
    ]
    deterministic_outside_pairs = [
        key for key in deterministic_groups if key not in deterministic_inside_pairs
    ]
    deterministic_inside_identical = sum(
        deterministic_pair_identical[key] for key in deterministic_inside_pairs
    )
    deterministic_outside_divergent = sum(
        not deterministic_pair_identical[key] for key in deterministic_outside_pairs
    )
    ensemble_identical = sum(ensemble_pair_identical.values())
    ensemble_divergent = len(ensemble_pair_identical) - ensemble_identical
    checks = {
        "v8e_deterministic_inside_domain_row_count": deterministic_inside,
        "v8e_deterministic_outside_domain_row_count": deterministic_outside,
        "v8e_deterministic_tail_pair_count": len(deterministic_groups),
        "v8e_deterministic_inside_domain_identical_pair_count": deterministic_inside_identical,
        "v8e_deterministic_outside_domain_divergent_pair_count": deterministic_outside_divergent,
        "v8e_ensemble_outside_domain_row_count": len(ensembles),
        "v8e_ensemble_tail_pair_count": len(ensemble_groups),
        "v8e_ensemble_identical_pair_count": ensemble_identical,
        "v8e_ensemble_divergent_pair_count": ensemble_divergent,
        "v8e_total_audit_row_count": len(audit_rows),
    }
    for key, actual in checks.items():
        require_equal(key, actual, expected[key])
    return audit_rows, {
        "deterministic_row_count": len(deterministic),
        "deterministic_inside_domain_row_count": deterministic_inside,
        "deterministic_outside_domain_row_count": deterministic_outside,
        "deterministic_tail_pair_count": len(deterministic_groups),
        "deterministic_inside_domain_identical_pair_count": deterministic_inside_identical,
        "deterministic_outside_domain_divergent_pair_count": deterministic_outside_divergent,
        "ensemble_row_count": len(ensembles),
        "ensemble_outside_domain_row_count": len(ensembles),
        "ensemble_tail_pair_count": len(ensemble_groups),
        "ensemble_identical_pair_count": ensemble_identical,
        "ensemble_divergent_pair_count": ensemble_divergent,
        "total_audit_row_count": len(audit_rows),
        "legacy_outcome_physical_authorization_count": 0,
        "fractions_are_event_probabilities": False,
    }


def build_cold_gate_join(
    config: dict[str, Any], v8j: dict[str, Any], material_summary: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    gate = v8j["gate_result"]
    contract = config["track_contract"]["cold_gate_join"]
    require_equal("V8J cold gate passed", bool(gate["passed"]), False)
    require_equal("V8J cold gate status", gate["status"], contract["observed_status"])
    rows = [
        {
            "track_id": "CONTROL_ZERO_THERMAL_INPUT",
            "thermal_input_status": "SOFTWARE_ZERO_CONTROL",
            "reduced_property_status": "IDENTITY_CONTROL_ONLY",
            "cold_gate_passed": False,
            "cold_gate_application": "NOT_APPLICABLE_TO_SOFTWARE_SENTINEL",
            "join_status": "CONTROL_NO_INITIATION_SOFTWARE_ONLY",
            "initiation_time_s": None,
            "physical_initiation_release": False,
            "historical_claim": False,
        },
        {
            "track_id": "OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE",
            "thermal_input_status": (
                f"{material_summary['complete_reduced_property_range_count']}_COMPLETE_"
                f"{material_summary['partial_domain_blocked_range_count']}_PARTIAL_RANGES"
            ),
            "reduced_property_status": "REFERENCE_ONLY_NO_MEMBER_ASSIGNMENT",
            "cold_gate_passed": False,
            "cold_gate_application": gate["status"],
            "join_status": "INDETERMINATE_BLOCKED_FAILED_COLD_GATE_AND_MEMBER_INPUTS",
            "initiation_time_s": None,
            "physical_initiation_release": False,
            "historical_claim": False,
        },
        {
            "track_id": "UNKNOWN_PHYSICAL_INITIATION",
            "thermal_input_status": "UNKNOWN_EVENT_MEMBER_THERMAL_STATE",
            "reduced_property_status": "UNKNOWN",
            "cold_gate_passed": False,
            "cold_gate_application": gate["status"],
            "join_status": "INDETERMINATE_UNKNOWN_EVENT_INPUTS_AND_FAILED_COLD_GATE",
            "initiation_time_s": None,
            "physical_initiation_release": False,
            "historical_claim": False,
        },
    ]
    require_equal(
        "cold gate join row count", len(rows), config["expected"]["cold_gate_join_row_count"]
    )
    return rows, {
        "required_condition": v8j["gate_definition"]["required_condition"],
        "pass_policy": v8j["gate_definition"]["pass_policy"],
        "observed_passed": bool(gate["passed"]),
        "observed_status": gate["status"],
        "observed_reason": gate["reason"],
        "thermal_runs_authorized_by_v8j": bool(gate["thermal_runs_authorized"]),
        "blender_coupling_authorized_by_v8j": bool(gate["blender_coupling_authorized"]),
        "missing_information": v8j["missing_information"],
        "join_rule": contract["join_rule"],
        "join_row_count": len(rows),
        "physical_initiation_release_count": 0,
    }


def build_tracks(
    config: dict[str, Any],
    v10q_tracks: dict[str, Any],
    v10o_trace: dict[str, Any],
    material_summary: dict[str, Any],
    legacy_summary: dict[str, Any],
    cold_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    upstream = {row["track_id"]: row for row in v10q_tracks["tracks"]}
    control_thermal = v10o_trace["records"]["I05_THERMAL_TO_INITIATION"]
    if upstream["CONTROL_ZERO_FIRE"]["thermal_record"] != control_thermal:
        raise RuntimeError("V10Q control thermal record differs from the frozen V10O record")
    missing_member_inputs = {
        "member_ids": None,
        "member_sections": None,
        "member_restraints_and_effective_lengths": None,
        "connection_force_displacement_laws": None,
        "member_temperature_histories": None,
        "initial_load_and_demand_histories": None,
        "geometric_imperfections": None,
        "thermal_expansion_restraint": None,
        "failure_criteria": None,
    }
    tracks = [
        {
            "track_id": "CONTROL_ZERO_THERMAL_INPUT",
            "upstream_track_id": "CONTROL_ZERO_FIRE",
            "epistemic_class": "SYNTHETIC_SOFTWARE_CONTROL_NOT_HISTORICAL",
            "status": "CONTROL_NO_INITIATION_SOFTWARE_ONLY",
            "thermal_record": control_thermal,
            "normalized_control_reduction_factors": {
                "yield_ratio_to_control": 1.0,
                "young_modulus_ratio_to_control": 1.0,
                "definition": "software identity only, not a WTC property assignment",
            },
            "initiation_time_s": None,
            "failed_member_ids": [],
            "trigger_mode": "CONTROL_NONE",
            "downstream_software_status_release": True,
            "downstream_physical_release": False,
            "historical_noncollapse_claim": False,
            "physical_validation": False,
        },
        {
            "track_id": "OFFICIAL_DEPENDENT_REDUCED_PROPERTY_REFERENCE",
            "upstream_track_id": "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE",
            "epistemic_class": "OFFICIAL_MODEL_DEPENDENT_RANGE_PLUS_DERIVED_REDUCED_PROPERTY_REFERENCE",
            "status": "INDETERMINATE_BLOCKED_FAILED_COLD_GATE_AND_MEMBER_INPUTS",
            "upstream_status": upstream[
                "OFFICIAL_MODEL_DEPENDENT_THERMAL_REFERENCE"
            ]["status"],
            "material_reduction_matrix": {
                "path": config["outputs"]["material_matrix"],
                "row_count": material_summary["temperature_envelope_row_count"],
                "complete_in_domain_range_count": material_summary[
                    "complete_reduced_property_range_count"
                ],
                "partial_domain_blocked_range_count": material_summary[
                    "partial_domain_blocked_range_count"
                ],
                "tail_model_invocation_count": 0,
            },
            "legacy_v8e_domain_audit": {
                "path": config["outputs"]["legacy_v8e_audit"],
                "row_count": legacy_summary["total_audit_row_count"],
                "physical_authorization_count": 0,
                "fractions_are_event_probabilities": False,
            },
            "cold_load_path_gate": cold_summary,
            "member_resolved_inputs": missing_member_inputs,
            "initiation_time_s": None,
            "failed_member_ids": None,
            "trigger_mode": None,
            "downstream_software_status_release": True,
            "downstream_physical_release": False,
            "historical_initiation_claim": False,
            "physical_validation": False,
        },
        {
            "track_id": "UNKNOWN_PHYSICAL_INITIATION",
            "upstream_track_id": "UNKNOWN_EVENT_FIRE",
            "epistemic_class": "UNKNOWN_EVENT_THERMAL_MECHANICAL_AND_INITIATION_STATE",
            "status": "INDETERMINATE_UNKNOWN_EVENT_INPUTS_AND_FAILED_COLD_GATE",
            "upstream_status": upstream["UNKNOWN_EVENT_FIRE"]["status"],
            "member_resolved_inputs": {key: None for key in missing_member_inputs},
            "material_reduction_history": None,
            "cold_load_path_state": None,
            "initiation_time_s": None,
            "failed_member_ids": None,
            "trigger_mode": None,
            "blocking_reasons": [
                "physical event member-temperature histories are unknown",
                "member identities, sections, restraints, connections and load histories are incomplete",
                "the canonical post-impact cold-load-path gate did not pass",
                "47 published range maxima exceed the declared Young-modulus polynomial domain",
                "official ranges and V8E synthetic fields do not identify the physical member state",
            ],
            "downstream_software_status_release": True,
            "downstream_physical_release": False,
            "historical_initiation_claim": False,
            "physical_validation": False,
        },
    ]
    require_equal(
        "constructed track order",
        [row["track_id"] for row in tracks],
        config["track_contract"]["required_track_ids"],
    )
    summary = {
        "track_count": len(tracks),
        "track_ids": [row["track_id"] for row in tracks],
        "software_status_release_count": sum(
            bool(row["downstream_software_status_release"]) for row in tracks
        ),
        "physical_initiation_release_count": sum(
            bool(row["downstream_physical_release"]) for row in tracks
        ),
        "historical_initiation_promotion_count": sum(
            bool(row.get("historical_initiation_claim", False)) for row in tracks
        ),
        "unknown_physical_fields_null": all(
            value is None
            for value in tracks[2]["member_resolved_inputs"].values()
        )
        and tracks[2]["material_reduction_history"] is None
        and tracks[2]["cold_load_path_state"] is None
        and tracks[2]["initiation_time_s"] is None
        and tracks[2]["failed_member_ids"] is None
        and tracks[2]["trigger_mode"] is None,
    }
    require_equal(
        "physical initiation release count",
        summary["physical_initiation_release_count"],
        config["expected"]["physical_initiation_release_count"],
    )
    require_equal(
        "historical initiation promotion count",
        summary["historical_initiation_promotion_count"],
        config["expected"]["historical_initiation_promotion_count"],
    )
    if not summary["unknown_physical_fields_null"]:
        raise RuntimeError("Unknown physical initiation track received a non-null physical field")
    return tracks, summary


def report_text(
    generated_at: str,
    config: dict[str, Any],
    material_summary: dict[str, Any],
    legacy_summary: dict[str, Any],
    cold_summary: dict[str, Any],
) -> str:
    by_family = material_summary["blocked_maxima_by_family"]
    by_time = material_summary["blocked_maxima_by_time_min"]
    return "\n".join(
        [
            "# WTC 1 — V10R : préprocesseur thermique → initiation",
            "",
            f"Généré le {generated_at}. Aucun solveur structurel ou thermique, GPU ou Blender n’est lancé.",
            "",
            "## Résultat principal",
            "",
            "Le préprocesseur conserve trois pistes non fusionnées. Il transforme les plages thermiques dépendantes du modèle officiel en facteurs mécaniques réduits uniquement là où le domaine sélectionné est déclaré exploitable. Il ne crée ni température de membre, ni capacité de membre, ni état d’initiation physique.",
            "",
            "Sur 105 plages, 58 ont leurs deux extrémités dans le domaine conservateur 0–600 °C. Les 47 autres ne conservent que leur extrémité froide calculable ; leur extrémité chaude et l’intervalle mécanique complet restent `null`. Aucun des deux prolongements V8B au-delà de 600 °C n’est invoqué.",
            "",
            "## Domaine et comptages",
            "",
            f"- Extrémités évaluées dans le domaine : {material_summary['joint_domain_valid_endpoint_count']}/210.",
            f"- Extrémités bloquées : {material_summary['joint_domain_blocked_endpoint_count']}/210.",
            f"- Plages bloquées par famille : noyau {by_family['core_column']}, périmètre {by_family['perimeter_column']}, treillis {by_family['floor_truss']}.",
            f"- Plages bloquées aux temps 20/40/60/80/100 min : {by_time['20']}/{by_time['40']}/{by_time['60']}/{by_time['80']}/{by_time['100']}.",
            "- Le rapport de limite d’élasticité à 20 °C issu de l’équation vaut 0,982493, pas exactement 1 ; une seconde colonne normalisée à la valeur de 20 °C évite de confondre les deux conventions.",
            "- Les deux lois sont décroissantes sur les 600 intervalles de la grille 0–600 °C.",
            "",
            "## Audit rétrospectif V8E",
            "",
            f"V8E contient {legacy_summary['deterministic_row_count']} lignes déterministes : {legacy_summary['deterministic_inside_domain_row_count']} restent entièrement dans 0–600 °C et {legacy_summary['deterministic_outside_domain_row_count']} utilisent un prolongement. Les {legacy_summary['deterministic_outside_domain_divergent_pair_count']}/25 paires hors domaine donnent des résultats différents selon le prolongement choisi.",
            "",
            f"Les {legacy_summary['ensemble_row_count']} agrégats de champs lisses atteignent au moins une température supérieure à 600 °C. Parmi leurs 20 paires, {legacy_summary['ensemble_divergent_pair_count']} divergent et {legacy_summary['ensemble_identical_pair_count']} coïncident. Une coïncidence d’agrégat ne valide pas le prolongement ; toutes ces fractions restent des sensibilités de champs synthétiques, jamais des probabilités de l’événement réel.",
            "",
            "## Jonction avec le gate froid",
            "",
            f"Le gate V8J reste `{cold_summary['observed_status']}` : un composant chargé demeure déconnecté et la topologie survivante, la raideur, la ductilité et l’affectation des assemblages ne sont pas établies. Même les 58 plages arithmétiquement complètes ne peuvent donc pas produire une initiation physique. La jonction correcte est `INDETERMINATE_BLOCKED`, et non « effondrement » ou « non-effondrement ».",
            "",
            "## Séparation des preuves",
            "",
            "1. **Faits observés ici** : empreintes, comptes, domaine déclaré, valeurs nulles et divergence des paires V8E.",
            "2. **Résultats du modèle officiel** : les plages thermiques restent des sorties NIST dépendantes de leurs entrées.",
            "3. **Archives** : aucune archive externe n’est lue ; deux PDF officiels locaux sont seulement rehachés.",
            "4. **Hypothèses du modèle** : le domaine conjoint 0–600 °C est une restriction conservatrice ; les champs V8E sont synthétiques.",
            "5. **Résultats dérivés** : facteurs de réduction, contrôles de monotonie et audit des prolongements.",
            "6. **Inconnues** : températures, sections, charges, assemblages, défauts et critères de rupture membre par membre.",
            "",
            "## Décision",
            "",
            "Le paquet logiciel V10R est valide comme préprocesseur et comme audit de domaine. La piste physique reste fermée : zéro état d’initiation est libéré, et aucune conclusion historique d’effondrement ou de non-effondrement n’est autorisée.",
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
    v10q_temperature_rows = load_csv(
        get_role_path(regression_items, "v10q_temperature_matrix")
    )
    v10q_tracks = load_json(get_role_path(regression_items, "v10q_track_manifest"))
    v10q_gate = load_json(get_role_path(regression_items, "v10q_gate"))
    transfer = load_json(get_role_path(cached_items, "NIST_WTC1_TRANSFER_TRANSCRIPTION"))
    v8e = load_json(get_role_path(cached_items, "V8E_SYNTHETIC_THERMAL_RESULTS"))
    v8j = load_json(get_role_path(cached_items, "V8J_COLD_LOAD_PATH_GATE"))
    v10o_trace = load_json(get_role_path(cached_items, "V10O_ZERO_CONTROL_TRACE"))

    require_equal("V10Q gate validation", v10q_gate["validation_status"], "PASS")
    require_equal(
        "V10Q physical thermal releases", v10q_gate["downstream_physical_release_count"], 0
    )
    require_equal(
        "V10Q track count", len(v10q_tracks["tracks"]), expected["track_count"]
    )

    law_audit = build_material_law_audit(config, transfer)
    material_rows, material_summary = build_material_matrix(
        config, v10q_temperature_rows, law_audit
    )
    cold_gate_passed = bool(v8j["gate_result"]["passed"])
    legacy_rows, legacy_summary = audit_legacy_v8e(
        config, v8e, v10q_temperature_rows, cold_gate_passed
    )
    cold_rows, cold_summary = build_cold_gate_join(config, v8j, material_summary)
    tracks, track_summary = build_tracks(
        config,
        v10q_tracks,
        v10o_trace,
        material_summary,
        legacy_summary,
        cold_summary,
    )

    require_equal("cold gate expected false", cold_gate_passed, expected["cold_gate_passed"])
    zero_counts = {
        "member_temperature_assignment_count": material_summary[
            "member_temperature_assignment_count"
        ],
        "member_section_assignment_count": material_summary["member_section_assignment_count"],
        "member_capacity_assignment_count": material_summary[
            "member_capacity_assignment_count"
        ],
        "structural_solver_run_count": 0,
        "thermal_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    for key, actual in zero_counts.items():
        require_equal(key, actual, expected[key])

    regression_audit = {
        "iteration": "V10R",
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
        "iteration": "V10R",
        "generated_at_utc": generated_at,
        "validation_status": "PASS",
        "configuration": {
            "path": rel(CONFIG_PATH),
            "sha256": sha256_file(CONFIG_PATH),
        },
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_files": cached_rows + official_rows,
        "evidence_classes": {
            "observed_facts": "Current file identities, table counts, null fields, equation-domain checks and cached tail-pair comparisons.",
            "official_model_results": "The temperature envelopes remain dependent NIST model outputs, not event measurements.",
            "archive_claims": "No external archive is read in V10R; two local official PDFs are hash-checked only.",
            "model_hypotheses": "The 0-600 C conservative joint domain and every V8E spatial field remain explicit modelling choices.",
            "derived_results": "Within-domain reduction factors, monotonicity checks, blocked counts and legacy tail sensitivity.",
            "unknowns": "Member-resolved thermal histories, sections, restraints, loads, connections, imperfections and failure criteria remain unresolved.",
        },
    }
    track_manifest = {
        "iteration": "V10R",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_THREE_TRACK_STATUS_HANDOFF_ONLY",
        "tracks": tracks,
        "summary": track_summary,
        "non_merging_rule": "No official-dependent or synthetic reference may be promoted into the unknown physical-event branch.",
    }
    gate = {
        "iteration": "V10R",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_SOFTWARE_PREPROCESSOR_ONLY",
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "source_identity_gate": "PASS_6_CACHED_PLUS_2_OFFICIAL_HASH_ONLY",
        "three_track_separation_gate": "PASS_3_OF_3",
        "temperature_range_input_gate": "PASS_105_OF_105",
        "material_law_identity_gate": "PASS_5_OF_5",
        "material_law_monotonicity_gate": "PASS_600_OF_600_FOR_EACH_LAW",
        "complete_reduced_property_range_gate": "PASS_58_REFERENCE_RANGES_ONLY",
        "partial_domain_blocked_range_gate": "BLOCKED_47_OF_105",
        "silent_above_600c_extrapolation_gate": "PASS_NONE_PERFORMED",
        "legacy_v8e_domain_gate": "WITHHELD_110_OF_110_FROM_PHYSICAL_INITIATION",
        "legacy_v8e_tail_dependence_gate": "25_OF_25_OUTSIDE_DOMAIN_DETERMINISTIC_PAIRS_DIVERGE_AND_11_OF_20_ENSEMBLE_PAIRS_DIVERGE",
        "cold_load_path_gate": cold_summary["observed_status"],
        "thermal_to_initiation_physical_handoff_gate": "CLOSED_INDETERMINATE",
        "historical_physical_initiation_promotion_count": 0,
        "downstream_physical_release_count": 0,
        "v10s_status_contract_authorized": True,
        "v10s_physical_propagation_run_authorized": False,
        "mechanical_source_gate": "OPEN_0_OF_22_REQUIREMENTS",
        "historical_collapse_or_noncollapse_conclusion_authorized": False,
        "member_temperature_assignment_count": 0,
        "member_section_assignment_count": 0,
        "member_capacity_assignment_count": 0,
        "structural_solver_run_count": 0,
        "thermal_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    runtime_seconds = time.perf_counter() - started
    results = {
        "iteration": "V10R",
        "generated_at_utc": generated_at,
        "validation_status": "PASS_THREE_TRACK_PREPROCESSOR_ONLY",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_summary": {
            "regression_file_count": len(regression_rows),
            "protected_file_count": len(protected_rows),
            "cached_input_file_count": len(cached_rows),
            "official_source_hash_only_file_count": len(official_rows),
        },
        "material_law_summary": law_audit,
        "material_range_summary": material_summary,
        "legacy_v8e_summary": legacy_summary,
        "cold_gate_summary": cold_summary,
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
    write_json(outputs["track_manifest"], track_manifest)
    write_csv(
        outputs["material_matrix"],
        [
            "track_id",
            "upstream_track_id",
            "component_family",
            "floor",
            "time_min",
            "time_s",
            "temperature_min_c",
            "temperature_max_c",
            "minimum_joint_domain_valid",
            "maximum_joint_domain_valid",
            "yield_ratio_direct_at_minimum",
            "yield_ratio_direct_at_maximum",
            "yield_ratio_to_20c_at_minimum",
            "yield_ratio_to_20c_at_maximum",
            "young_modulus_gpa_at_minimum",
            "young_modulus_gpa_at_maximum",
            "young_modulus_ratio_to_20c_at_minimum",
            "young_modulus_ratio_to_20c_at_maximum",
            "complete_yield_ratio_interval_lower",
            "complete_yield_ratio_interval_upper",
            "complete_young_modulus_gpa_interval_lower",
            "complete_young_modulus_gpa_interval_upper",
            "range_status",
            "tail_model_invoked",
            "exact_member_temperature_assignment",
            "member_section_assignment",
            "member_capacity_assignment",
            "initiation_state_assignment",
            "physical_initiation_release",
            "evidence_class",
        ],
        material_rows,
    )
    write_json(outputs["material_law_audit"], law_audit)
    write_csv(
        outputs["legacy_v8e_audit"],
        [
            "record_type",
            "time_min",
            "elastic_modulus_tail",
            "field_or_gamma",
            "maximum_assigned_or_supported_temperature_c",
            "declared_modulus_domain_status",
            "tail_pair_outcome_identical",
            "system_equilibrium_all_floors",
            "system_no_equilibrium_fraction",
            "failed_floor_count",
            "v8e_fraction_is_event_probability",
            "cold_gate_passed",
            "result_physically_authorized",
            "withheld_reason",
        ],
        legacy_rows,
    )
    write_csv(
        outputs["cold_gate_join_matrix"],
        [
            "track_id",
            "thermal_input_status",
            "reduced_property_status",
            "cold_gate_passed",
            "cold_gate_application",
            "join_status",
            "initiation_time_s",
            "physical_initiation_release",
            "historical_claim",
        ],
        cold_rows,
    )
    write_json(outputs["handoff_gate"], gate)
    write_text(
        outputs["report"],
        report_text(
            generated_at, config, material_summary, legacy_summary, cold_summary
        ),
    )
    write_json(outputs["results"], results)

    audit_roles = [
        "regression_audit",
        "source_manifest",
        "track_manifest",
        "material_matrix",
        "material_law_audit",
        "legacy_v8e_audit",
        "cold_gate_join_matrix",
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
        "iteration": "V10R",
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
        "material_law_extrapolation_above_600c_count": 0,
        "member_temperature_assignment_count": 0,
        "member_section_assignment_count": 0,
        "member_capacity_assignment_count": 0,
        "historical_physical_initiation_promotion_count": 0,
        "downstream_physical_release_count": 0,
        "structural_solver_run_count": 0,
        "thermal_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(outputs["offline_audit"], offline_audit)

    print(
        json.dumps(
            {
                "iteration": "V10R",
                "status": results["validation_status"],
                "tracks": track_summary["track_count"],
                "temperature_ranges": material_summary["temperature_envelope_row_count"],
                "complete_in_domain_ranges": material_summary[
                    "complete_reduced_property_range_count"
                ],
                "partial_domain_blocked_ranges": material_summary[
                    "partial_domain_blocked_range_count"
                ],
                "valid_endpoints": material_summary["joint_domain_valid_endpoint_count"],
                "blocked_endpoints": material_summary["joint_domain_blocked_endpoint_count"],
                "legacy_v8e_rows_withheld": legacy_summary["total_audit_row_count"],
                "cold_gate_passed": cold_gate_passed,
                "physical_initiation_releases": track_summary[
                    "physical_initiation_release_count"
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
        print(f"V10R ERROR: {exc}", file=sys.stderr)
        raise
