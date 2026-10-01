from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10p_three_track_impact_damage_handoff.json"
SCRIPT_PATH = Path(__file__).resolve()
CASES = ("less_severe", "base", "more_severe")


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


def verify_hash(item: dict[str, Any], read_mode: str = "FULL_ARTIFACT") -> dict[str, Any]:
    path = abs_path(item["path"])
    role = item.get("role", item.get("id", "file"))
    if not path.is_file():
        raise RuntimeError(f"Missing {role}: {path}")
    actual = sha256_file(path)
    if actual.lower() != item["expected_sha256"].lower():
        raise RuntimeError(f"Hash mismatch for {role}: expected {item['expected_sha256']}, got {actual}")
    row = {
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


def load_config() -> dict[str, Any]:
    config = load_json(CONFIG_PATH)
    if config.get("iteration") != "V10P":
        raise RuntimeError("Configuration iteration must be V10P")
    expected = config["expected"]
    counts = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_input_file_count": len(config["cached_input_files"]),
        "official_source_hash_only_file_count": len(config["official_source_hash_only_files"]),
        "track_count": len(config["track_contract"]["required_track_ids"]),
    }
    for key, actual in counts.items():
        if actual != expected[key]:
            raise RuntimeError(f"Unexpected {key}: {actual} != {expected[key]}")
    if config["track_contract"]["required_track_ids"] != [
        "CONTROL_ZERO_INPUT",
        "OFFICIAL_MODEL_DEPENDENT_REFERENCE",
        "UNKNOWN_PHYSICAL_DAMAGE",
    ]:
        raise RuntimeError("Track contract differs from predeclared three-track order")
    if config["execution_policy"]["physical_damage_assignment"]:
        raise RuntimeError("V10P cannot authorize physical damage assignment")
    return config


def close(left: float, right: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def add_ledger_row(
    rows: list[dict[str, Any]],
    *,
    ledger_id: str,
    track_id: str,
    case_id: str,
    category: str,
    quantity: str,
    reference_value: float | None,
    recomputed_value: float | None,
    unit: str,
    status: str,
    evidence_class: str,
    closure_scope: str,
    missing_for_full_closure: str,
) -> None:
    residual = None
    relative = None
    if reference_value is not None and recomputed_value is not None:
        residual = float(reference_value) - float(recomputed_value)
        relative = residual / float(reference_value) if float(reference_value) != 0.0 else 0.0
    rows.append(
        {
            "ledger_id": ledger_id,
            "track_id": track_id,
            "case_id": case_id,
            "category": category,
            "quantity": quantity,
            "reference_value": reference_value if reference_value is not None else "",
            "recomputed_value": recomputed_value if recomputed_value is not None else "",
            "unit": unit,
            "residual_reference_minus_recomputed": residual if residual is not None else "",
            "relative_residual": relative if relative is not None else "",
            "status": status,
            "evidence_class": evidence_class,
            "closure_scope": closure_scope,
            "missing_for_full_closure": missing_for_full_closure,
        }
    )


def kinematic_and_mass_ledgers(
    transfer: dict[str, Any], v8s: dict[str, Any], conversions: dict[str, float]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case_audits: list[dict[str, Any]] = []
    lb_to_kg = float(conversions["lb_to_kg"])
    mph_to_m_s = float(conversions["mph_to_m_s"])
    base_weight_lb = float(transfer["aircraft"]["base_total_weight_lb"])
    for case_id in CASES:
        source_case = transfer["aircraft"]["cases"][case_id]
        cached = v8s["derived_results"]["cases"][case_id]
        mass_kg = base_weight_lb * float(source_case["mass_factor"]) * lb_to_kg
        speed_m_s = float(source_case["speed_mph"]) * mph_to_m_s
        momentum_mn_s = mass_kg * speed_m_s / 1e6
        energy_gj = 0.5 * mass_kg * speed_m_s**2 / 1e9
        cached_mass = float(cached["inputs"]["mass_kg"])
        cached_speed = float(cached["inputs"]["speed_mps"])
        cached_p = float(cached["derived_kinematics"]["momentum_total_mn_s"])
        cached_e = float(cached["derived_kinematics"]["kinetic_energy_gj"])
        assertions = {
            "mass_conversion": close(cached_mass, mass_kg),
            "speed_conversion": close(cached_speed, speed_m_s),
            "scalar_momentum": close(cached_p, momentum_mn_s),
            "scalar_kinetic_energy": close(cached_e, energy_gj),
        }
        if not all(assertions.values()):
            raise RuntimeError(f"Incoming kinematic replay failed for {case_id}: {assertions}")
        case_audits.append(
            {
                "case_id": case_id,
                "status": "PASS_INCOMING_SCALAR_LEDGER_ONLY",
                "assertions": assertions,
                "mass_kg": cached_mass,
                "speed_m_s": cached_speed,
                "momentum_mn_s": cached_p,
                "kinetic_energy_gj": cached_e,
            }
        )
        for quantity, reference, recomputed, unit in (
            ("mass_from_weight", cached_mass, mass_kg, "kg"),
            ("speed_from_mph", cached_speed, speed_m_s, "m/s"),
            ("incoming_scalar_momentum", cached_p, momentum_mn_s, "MN s"),
            ("incoming_scalar_kinetic_energy", cached_e, energy_gj, "GJ"),
        ):
            add_ledger_row(
                rows,
                ledger_id=f"KIN-{case_id}-{quantity}",
                track_id="OFFICIAL_MODEL_DEPENDENT_REFERENCE",
                case_id=case_id,
                category="INCOMING_KINEMATICS",
                quantity=quantity,
                reference_value=reference,
                recomputed_value=recomputed,
                unit=unit,
                status="PASS_ARITHMETIC_REPLAY",
                evidence_class="OFFICIAL_INPUT_TRANSCRIPTION_WITH_DERIVED_KINEMATICS",
                closure_scope="incoming aircraft scalar accounting only",
                missing_for_full_closure="postimpact velocities, tower reaction impulse and internal-energy histories",
            )
        d = cached["derived_kinematics"]
        component_p = math.hypot(
            float(d["momentum_normal_to_facade_mn_s"]),
            float(d["momentum_downward_mn_s"]),
        )
        component_e = float(d["kinetic_energy_normal_component_gj"]) + float(
            d["kinetic_energy_vertical_component_gj"]
        )
        add_ledger_row(
            rows,
            ledger_id=f"KIN-{case_id}-reported-components-momentum",
            track_id="OFFICIAL_MODEL_DEPENDENT_REFERENCE",
            case_id=case_id,
            category="INCOMING_COMPONENT_ACCOUNTING",
            quantity="reported_normal_plus_vertical_momentum_magnitude",
            reference_value=cached_p,
            recomputed_value=component_p,
            unit="MN s",
            status="PARTIAL_RESIDUAL_RETAINED",
            evidence_class="DERIVED_FROM_CACHED_COMPONENTS",
            closure_scope="only the recorded normal and downward components",
            missing_for_full_closure="lateral component is not separately recorded in the cached derived kinematics",
        )
        add_ledger_row(
            rows,
            ledger_id=f"KIN-{case_id}-reported-components-energy",
            track_id="OFFICIAL_MODEL_DEPENDENT_REFERENCE",
            case_id=case_id,
            category="INCOMING_COMPONENT_ACCOUNTING",
            quantity="reported_normal_plus_vertical_kinetic_energy",
            reference_value=cached_e,
            recomputed_value=component_e,
            unit="GJ",
            status="PARTIAL_RESIDUAL_RETAINED",
            evidence_class="DERIVED_FROM_CACHED_COMPONENTS",
            closure_scope="only the recorded normal and vertical components",
            missing_for_full_closure="lateral component is not separately recorded in the cached derived kinematics",
        )

    components = v8s["derived_results"]["base_case_component_energy"]
    base = v8s["derived_results"]["cases"]["base"]
    component_weight_lb = sum(float(item["weight_lb"]) for item in components)
    component_mass_kg = sum(float(item["mass_kg"]) for item in components)
    component_energy_gj = sum(float(item["translational_kinetic_energy_gj"]) for item in components)
    component_fraction = sum(float(item["mass_fraction"]) for item in components)
    base_mass = float(base["inputs"]["mass_kg"])
    base_energy = float(base["derived_kinematics"]["kinetic_energy_gj"])
    for quantity, reference, recomputed, unit in (
        ("component_weight_sum", base_weight_lb, component_weight_lb, "lb"),
        ("component_mass_sum", base_mass, component_mass_kg, "kg"),
        ("component_mass_fraction_sum", 1.0, component_fraction, "1"),
        ("component_translational_energy_sum", base_energy, component_energy_gj, "GJ"),
    ):
        status = "PASS_COMPONENT_ACCOUNTING" if close(reference, recomputed, 1e-8) else "FAIL"
        if status == "FAIL":
            raise RuntimeError(f"Base component accounting failed for {quantity}")
        add_ledger_row(
            rows,
            ledger_id=f"MASS-base-{quantity}",
            track_id="OFFICIAL_MODEL_DEPENDENT_REFERENCE",
            case_id="base",
            category="BASE_COMPONENT_ACCOUNTING",
            quantity=quantity,
            reference_value=reference,
            recomputed_value=recomputed,
            unit=unit,
            status=status,
            evidence_class="CACHED_V8S_COMPONENT_BREAKDOWN",
            closure_scope="incoming aircraft component accounting at common translational speed",
            missing_for_full_closure="component deformation, rotation, separation and postimpact velocities",
        )

    distribution = transfer["base_case_fuel_and_debris_lb"]
    bins = [value for key, value in distribution.items() if key != "totals"]
    fuel_bin_sum = sum(float(item["fuel"]) for item in bins)
    debris_bin_sum = sum(float(item["aircraft_debris"]) for item in bins)
    stated_fuel = float(distribution["totals"]["fuel"])
    stated_debris = float(distribution["totals"]["aircraft_debris"])
    nonfuel_mass = base_weight_lb - float(transfer["aircraft"]["fuel_weight_lb"])
    table_rows = (
        (
            "fuel_distribution_bin_sum",
            stated_fuel,
            fuel_bin_sum,
            "PUBLISHED_BIN_ROUNDING_RESIDUAL_RETAINED",
            "20 lb difference between stated total and displayed bins",
        ),
        (
            "aircraft_debris_distribution_bin_sum",
            stated_debris,
            debris_bin_sum,
            "PUBLISHED_BIN_ROUNDING_RESIDUAL_RETAINED",
            "250 lb difference between stated total and displayed bins",
        ),
        (
            "nonfuel_aircraft_mass_vs_stated_debris_total",
            nonfuel_mass,
            stated_debris,
            "PARTIAL_TABLE_ACCOUNTING_NOT_FULL_MASS_LEDGER",
            "21,500 lb of nonfuel aircraft mass is outside the stated debris total; disposition is not resolved by this table",
        ),
    )
    for quantity, reference, recomputed, status, missing in table_rows:
        add_ledger_row(
            rows,
            ledger_id=f"DIST-base-{quantity}",
            track_id="OFFICIAL_MODEL_DEPENDENT_REFERENCE",
            case_id="base",
            category="PUBLISHED_BASE_DISTRIBUTION",
            quantity=quantity,
            reference_value=reference,
            recomputed_value=recomputed,
            unit="lb",
            status=status,
            evidence_class="OFFICIAL_MODEL_OUTPUT_TRANSCRIPTION",
            closure_scope="published rounded fuel/debris table only; outside combines impact-face rebound and south-side passage",
            missing_for_full_closure=missing,
        )
    for quantity, missing in (
        (
            "full_postimpact_mass_conservation",
            "object-by-object retained/rebounded/exiting masses and treatment of the 21,500 lb not in the stated debris total",
        ),
        (
            "full_postimpact_vector_momentum_conservation",
            "object-by-object exit/rebound velocities, tower reaction impulse and complete time history",
        ),
        (
            "full_postimpact_energy_conservation",
            "kinetic, elastic, plastic, fracture, thermal, acoustic and numerical-energy histories",
        ),
    ):
        add_ledger_row(
            rows,
            ledger_id=f"POST-base-{quantity}",
            track_id="UNKNOWN_PHYSICAL_DAMAGE",
            case_id="base_envelope",
            category="FULL_POSTIMPACT_CONSERVATION",
            quantity=quantity,
            reference_value=None,
            recomputed_value=None,
            unit="not computable",
            status="INDETERMINATE_MISSING_REQUIRED_OUTPUTS",
            evidence_class="UNKNOWN",
            closure_scope="full physical impact event",
            missing_for_full_closure=missing,
        )
    summary = {
        "incoming_case_audits": case_audits,
        "incoming_scalar_ledger_pass_count": sum(item["status"].startswith("PASS") for item in case_audits),
        "base_component_count": len(components),
        "base_component_weight_sum_lb": component_weight_lb,
        "base_component_mass_sum_kg": component_mass_kg,
        "base_component_energy_sum_gj": component_energy_gj,
        "fuel_bin_sum_lb": fuel_bin_sum,
        "fuel_stated_total_lb": stated_fuel,
        "fuel_bin_rounding_residual_lb": stated_fuel - fuel_bin_sum,
        "debris_bin_sum_lb": debris_bin_sum,
        "debris_stated_total_lb": stated_debris,
        "debris_bin_rounding_residual_lb": stated_debris - debris_bin_sum,
        "nonfuel_aircraft_mass_lb": nonfuel_mass,
        "nonfuel_mass_not_in_stated_debris_total_lb": nonfuel_mass - stated_debris,
        "full_postimpact_mass_momentum_energy_ledger_closed_count": 0,
    }
    return rows, summary


def expand_and_compare_damage(
    transfer: dict[str, Any], v8a: dict[str, Any], floors: list[int]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    per_case: dict[str, Any] = {}
    allowed_states = {"severed", "heavy", "moderate", "light"}
    for case_id in CASES:
        source_rows = transfer["core_damage"][case_id]
        expanded: dict[int, dict[str, str]] = {floor: {} for floor in floors}
        seen: set[tuple[int, int]] = set()
        for source_row in source_rows:
            column = int(source_row["column"])
            state = source_row["state"]
            if state not in allowed_states:
                raise RuntimeError(f"Unexpected damage state {state}")
            for floor in source_row["floors"]:
                if floor not in floors:
                    continue
                key = (column, int(floor))
                if key in seen:
                    raise RuntimeError(f"Duplicate damage segment in {case_id}: {key}")
                seen.add(key)
                expanded[int(floor)][str(column)] = state
                v8a_state = v8a["impact_damage_cases"][case_id]["floor_results"][str(floor)][
                    "reported_damage_states"
                ].get(str(column))
                rows.append(
                    {
                        "case_id": case_id,
                        "column_id": column,
                        "floor": floor,
                        "member_segment_id": f"CORE-{column}-F{floor}",
                        "reported_state": state,
                        "max_lateral_deformation_in": source_row.get("max_lateral_deformation_in", ""),
                        "max_lateral_deformation_m": (
                            float(source_row["max_lateral_deformation_in"]) * 0.0254
                            if "max_lateral_deformation_in" in source_row
                            else ""
                        ),
                        "reference_removal_if_severed_or_heavy": state in {"severed", "heavy"},
                        "final_case_b_rule_applies": case_id == "more_severe" and state in {"severed", "heavy"},
                        "v8a_reported_state": v8a_state or "",
                        "v8a_transformation_match": v8a_state == state,
                        "evidence_class": "OFFICIAL_MODEL_OUTPUT_DEPENDENT_TRANSCRIPTION",
                        "independent_observation": False,
                        "physical_damage_assignment": False,
                        "downstream_physical_release": False,
                    }
                )
        state_counts = Counter(row["reported_state"] for row in rows if row["case_id"] == case_id)
        removal_count = sum(
            row["reference_removal_if_severed_or_heavy"] for row in rows if row["case_id"] == case_id
        )
        per_case[case_id] = {
            "source_entry_count": len(source_rows),
            "expanded_segment_count_floors93_99": sum(len(value) for value in expanded.values()),
            "expanded_state_counts": dict(sorted(state_counts.items())),
            "reference_removal_segment_count": removal_count,
            "expanded_member_states": [
                {
                    "member_segment_id": f"CORE-{column}-F{floor}",
                    "column_id": column,
                    "floor": floor,
                    "state": state,
                }
                for floor in floors
                for column, state in sorted((int(column), state) for column, state in expanded[floor].items())
            ],
        }
        for floor in floors:
            expected_states = expanded[floor]
            observed_states = v8a["impact_damage_cases"][case_id]["floor_results"][str(floor)][
                "reported_damage_states"
            ]
            expected_removed = sorted(
                int(column) for column, state in expected_states.items() if state in {"severed", "heavy"}
            )
            observed_removed = sorted(
                int(value)
                for value in v8a["impact_damage_cases"][case_id]["floor_results"][str(floor)][
                    "removed_if_heavy_treated_as_severed"
                ]
            )
            state_match = expected_states == observed_states
            removal_match = expected_removed == observed_removed
            comparisons.append(
                {
                    "case_id": case_id,
                    "floor": floor,
                    "source_state_count": len(expected_states),
                    "v8a_state_count": len(observed_states),
                    "state_mapping_exact_match": state_match,
                    "source_reference_removed_count": len(expected_removed),
                    "v8a_removed_count": len(observed_removed),
                    "removal_mapping_exact_match": removal_match,
                    "status": "PASS_CACHED_TRANSFORMATION_CONSISTENCY" if state_match and removal_match else "FAIL",
                }
            )
    if any(not row["v8a_transformation_match"] for row in rows):
        raise RuntimeError("At least one expanded damage row differs from V8A")
    if any(row["status"] == "FAIL" for row in comparisons):
        raise RuntimeError("At least one case/floor damage transformation comparison failed")
    summary = {
        "case_count": len(CASES),
        "expanded_segment_count": len(rows),
        "case_floor_comparison_count": len(comparisons),
        "case_floor_comparison_pass_count": sum(row["status"].startswith("PASS") for row in comparisons),
        "reference_removal_segment_count_all_cases": sum(row["reference_removal_if_severed_or_heavy"] for row in rows),
        "final_case_b_removal_segment_count": sum(row["final_case_b_rule_applies"] for row in rows),
        "final_case_b_unique_removed_column_count": len(
            {row["column_id"] for row in rows if row["final_case_b_rule_applies"]}
        ),
        "per_case": per_case,
    }
    return rows, comparisons, summary


def build_tracks(
    config: dict[str, Any],
    transfer: dict[str, Any],
    v8s: dict[str, Any],
    v9m: dict[str, Any],
    v10o_trace: dict[str, Any],
    damage_summary: dict[str, Any],
    ledger_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    v8s_cases = v8s["derived_results"]["cases"]
    official_cases = []
    for case_id in CASES:
        case = v8s_cases[case_id]
        official_cases.append(
            {
                "case_id": case_id,
                "kinematics": {
                    "mass_kg": case["inputs"]["mass_kg"],
                    "speed_m_s": case["inputs"]["speed_mps"],
                    "trajectory_pitch_deg": case["inputs"]["trajectory_pitch_deg"],
                    "orientation_pitch_deg": case["inputs"]["orientation_pitch_deg"],
                    "roll_deg": case["inputs"]["roll_deg"],
                    "momentum_total_MN_s": case["derived_kinematics"]["momentum_total_mn_s"],
                    "kinetic_energy_GJ": case["derived_kinematics"]["kinetic_energy_gj"],
                },
                "damage_reference": damage_summary["per_case"][case_id],
                "fuel_distribution_lb": (
                    transfer["base_case_fuel_and_debris_lb"] if case_id == "base" else None
                ),
                "debris_distribution_lb": (
                    transfer["base_case_fuel_and_debris_lb"] if case_id == "base" else None
                ),
                "distribution_scope_warning": (
                    "The base table combines north-face rebound and material passing through the south side; it is not a far-side-only measurement."
                    if case_id == "base"
                    else "No less/more-severe distribution table is carried in the selected cached transcription."
                ),
                "physical_validation": False,
                "downstream_physical_release": False,
            }
        )
    masses = [float(v8s_cases[case]["inputs"]["mass_kg"]) for case in CASES]
    speeds = [float(v8s_cases[case]["inputs"]["speed_mps"]) for case in CASES]
    momenta = [float(v8s_cases[case]["derived_kinematics"]["momentum_total_mn_s"]) for case in CASES]
    energies = [float(v8s_cases[case]["derived_kinematics"]["kinetic_energy_gj"]) for case in CASES]
    blockers = list(v9m["controlling_physical_blockers"])
    tracks = [
        {
            "track_id": "CONTROL_ZERO_INPUT",
            "epistemic_class": "SYNTHETIC_SOFTWARE_CONTROL_NOT_HISTORICAL",
            "status": "PASS_SOFTWARE_SENTINEL_ONLY",
            "source": {
                "path": "wtc1_simulation_v8/output/v10o_null_control_trace.json",
                "sha256": sha256_file(abs_path("wtc1_simulation_v8/output/v10o_null_control_trace.json")),
            },
            "kinematics": {
                "mass_kg": 0.0,
                "velocity_vector_m_s": [0.0, 0.0, 0.0],
                "kinetic_energy_J": 0.0,
            },
            "damage_handoff": {
                "member_states": [],
                "opening_polygons_m": [],
                "debris_mass_kg": 0.0,
                "fuel_mass_kg": 0.0,
                "module_status": "CONTROL_ZERO_DAMAGE",
            },
            "terminal_v10o_label": v10o_trace["terminal_control_outcome"]["label"],
            "historical_noncollapse_conclusion": False,
            "downstream_software_control_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
        {
            "track_id": "OFFICIAL_MODEL_DEPENDENT_REFERENCE",
            "epistemic_class": "OFFICIAL_MODEL_OUTPUT_DEPENDENT_NOT_INDEPENDENT_OBSERVATION",
            "status": "PASS_REFERENCE_TRANSCRIPTION_AND_ACCOUNTING_ONLY",
            "source": {
                "path": "wtc1_simulation_v8/data/nist_wtc1_transfer.json",
                "sha256": sha256_file(abs_path("wtc1_simulation_v8/data/nist_wtc1_transfer.json")),
                "official_source_ids": ["NCSTAR1_2B_V2", "NCSTAR1_6D_LOCAL"],
            },
            "cases": official_cases,
            "ledger_summary": ledger_summary,
            "independent_damage_validation": False,
            "downstream_software_reference_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
            "usage_rule": "May drive explicitly labelled dependent sensitivity calculations only; cannot identify the unique historical damage state.",
        },
        {
            "track_id": "UNKNOWN_PHYSICAL_DAMAGE",
            "epistemic_class": "UNKNOWN_PHYSICAL_STATE_WITH_SOURCE_BOUNDED_KINEMATICS",
            "status": "BLOCKED_PHYSICAL_DAMAGE_UNRESOLVED",
            "kinematic_envelope": {
                "mass_kg": {"minimum": min(masses), "maximum": max(masses)},
                "speed_m_s": {"minimum": min(speeds), "maximum": max(speeds)},
                "momentum_MN_s": {"minimum": min(momenta), "maximum": max(momenta)},
                "kinetic_energy_GJ": {"minimum": min(energies), "maximum": max(energies)},
                "source_class": "OFFICIAL_INPUT_TRANSCRIPTION_WITH_DERIVED_KINEMATICS",
            },
            "damage_handoff": {
                "member_states": None,
                "opening_polygons_m": None,
                "debris_distribution": None,
                "fuel_distribution": None,
                "module_status": "UNKNOWN_PHYSICAL_DAMAGE",
            },
            "full_postimpact_conservation": {
                "mass": "INDETERMINATE",
                "vector_momentum": "INDETERMINATE",
                "energy": "INDETERMINATE",
            },
            "blocking_reasons": blockers
            + [
                "independent observed facade-damage mask with refined orientation remains unavailable",
                "object-by-object postimpact mass and velocity histories remain unavailable",
            ],
            "downstream_software_unknown_status_release": True,
            "downstream_physical_release": False,
            "physical_validation": False,
        },
    ]
    if [track["track_id"] for track in tracks] != config["track_contract"]["required_track_ids"]:
        raise RuntimeError("Constructed track order differs from predeclaration")
    return tracks


def make_report(
    config: dict[str, Any],
    damage_summary: dict[str, Any],
    ledger_summary: dict[str, Any],
    comparisons: list[dict[str, Any]],
) -> str:
    return "\n".join(
        [
            "# WTC 1 — V10P : transfert impact → dommage en trois pistes",
            "",
            f"Généré le {utc_now()}. Aucun solveur, calcul GPU ou lancement Blender n’est effectué.",
            "",
            "## Résultat principal",
            "",
            "Le transfert impact→dommage est désormais représenté par trois pistes qui ne sont jamais fusionnées :",
            "",
            "1. **Contrôle nul** : reprise du scénario sentinelle V10O, utile uniquement pour tester le logiciel.",
            "2. **Référence dépendante du modèle officiel** : cas moins sévère, de base et plus sévère, recopiés sans interpolation. Ces dommages sont des sorties de modèle, pas une observation indépendante du dommage réel.",
            "3. **Dommage physique inconnu** : les bornes cinématiques sont conservées, mais les états de membres, ouvertures, débris et distribution de carburant restent `null`. Cette piste bloque toute libération physique en aval.",
            "",
            "## Contrôles obtenus",
            "",
            f"- Bilans cinématiques scalaires entrants : {ledger_summary['incoming_scalar_ledger_pass_count']}/3 cas reproduits.",
            f"- Décomposition de masse/énergie du cas de base : {ledger_summary['base_component_count']} composants, sommes cohérentes avec l’entrée.",
            f"- Transcription dommage → V8A : {sum(row['status'].startswith('PASS') for row in comparisons)}/{len(comparisons)} couples cas/étage identiques.",
            f"- Segments de dommage référencés sur les étages 93–99 : {damage_summary['expanded_segment_count']} ; dont {damage_summary['reference_removal_segment_count_all_cases']} sévères/lourds à travers les trois cas.",
            f"- Cas B final plus sévère : {damage_summary['final_case_b_removal_segment_count']} segments, {damage_summary['final_case_b_unique_removed_column_count']} colonnes distinctes.",
            "",
            "## Résidus conservés, pas effacés",
            "",
            f"- Somme des cases carburant : {ledger_summary['fuel_bin_sum_lb']:.0f} lb contre {ledger_summary['fuel_stated_total_lb']:.0f} lb annoncées ; résidu {ledger_summary['fuel_bin_rounding_residual_lb']:.0f} lb.",
            f"- Somme des cases débris : {ledger_summary['debris_bin_sum_lb']:.0f} lb contre {ledger_summary['debris_stated_total_lb']:.0f} lb annoncées ; résidu {ledger_summary['debris_bin_rounding_residual_lb']:.0f} lb.",
            f"- Masse non-carburant moins total de débris annoncé : {ledger_summary['nonfuel_mass_not_in_stated_debris_total_lb']:.0f} lb. Ce manque dans le tableau n’est ni supprimé ni interprété comme une destruction de masse.",
            "",
            "Les totaux « extérieur de la tour » combinent le rebond côté nord et le passage côté sud. Ils ne constituent donc pas une mesure de masse ayant traversé seule la façade opposée.",
            "",
            "## Ce qui reste indéterminé",
            "",
            "Aucun bilan complet après impact ne peut être fermé : il manque les vitesses par objet, l’impulsion transmise à la tour, ainsi que les histoires d’énergie élastique, plastique, de rupture, thermique et numérique. Le résultat est donc 0/3 pour la fermeture physique masse–quantité de mouvement–énergie après impact.",
            "",
            "## Séparation des preuves",
            "",
            "1. **Faits observés dans V10P** : empreintes, sommes, conversions et concordance exacte entre la transcription et la transformation V8A.",
            "2. **Résultats du modèle officiel** : les cartes de dommage et distributions restent explicitement dépendantes de NIST.",
            "3. **Archives locales** : aucune archive source externe au projet n’est lue ; deux PDF officiels locaux sont seulement rehachés.",
            "4. **Hypothèses** : aucune nouvelle carte ou distribution n’est inventée.",
            "5. **Résultats dérivés** : bilans entrants, résidus tabulaires, matrices développées et comparaison V8A.",
            "6. **Inconnues** : dommage physique réel, ouvertures, débris, carburant et bilans complets après impact.",
            "",
            "## Décision",
            "",
            "La référence officielle peut alimenter des sensibilités portant son étiquette de dépendance ; la piste inconnue doit rester bloquée. Aucun état n’est libéré comme dommage historique validé, et aucune conclusion d’effondrement ou de non-effondrement n’est autorisée.",
            "",
            "## Prochaine étape",
            "",
            config["next_iteration"]["objective"],
        ]
    )


def main() -> int:
    started = time.perf_counter()
    config = load_config()
    regression_rows = [verify_hash(item) for item in config["regression_files"]]
    protected_rows = [verify_hash(item) for item in config["protected_files"]]
    cached_rows = [verify_hash(item) for item in config["cached_input_files"]]
    official_rows = [
        verify_hash(item, read_mode="HASH_ONLY_NO_PAGE_OR_TEXT_EXTRACTION")
        for item in config["official_source_hash_only_files"]
    ]
    regression = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_file_count": len(regression_rows),
        "protected_file_count": len(protected_rows),
        "regression_files": regression_rows,
        "protected_files": protected_rows,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_source_pdf_hash_only_count": len(official_rows),
        "official_source_pdf_page_read_count": 0,
        "official_source_pdf_text_extraction_count": 0,
        "official_sources_directory_modified": False,
        "blender_master_unchanged": True,
    }
    source_manifest = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "cached_input_count": len(cached_rows),
        "official_source_hash_only_count": len(official_rows),
        "cached_inputs": cached_rows,
        "official_source_hash_only_files": official_rows,
        "source_use_rule": "The two PDFs provide file-identity continuity only in V10P. Damage values are consumed from the hashed cached transcription and remain official-model dependent.",
    }

    inputs = {item["id"]: abs_path(item["path"]) for item in config["cached_input_files"]}
    transfer = load_json(inputs["NIST_WTC1_TRANSFER_TRANSCRIPTION"])
    v8a = load_json(inputs["V8A_TRANSFER_RESULTS"])
    v8s = load_json(inputs["V8S_IMPACT_KINEMATICS"])
    v9m = load_json(inputs["V9M_IMPACT_BRANCH_CLOSURE"])
    v10o_trace = load_json(abs_path("wtc1_simulation_v8/output/v10o_null_control_trace.json"))

    ledger_rows, ledger_summary = kinematic_and_mass_ledgers(
        transfer, v8s, config["track_contract"]["unit_conversions"]
    )
    damage_rows, comparisons, damage_summary = expand_and_compare_damage(
        transfer, v8a, config["track_contract"]["analysis_floors"]
    )
    expected = config["expected"]
    checks = {
        "official_kinematic_case_count": len(ledger_summary["incoming_case_audits"]) == expected["official_kinematic_case_count"],
        "incoming_scalar_ledger_case_count": ledger_summary["incoming_scalar_ledger_pass_count"] == expected["incoming_kinematic_ledger_case_count"],
        "base_component_count": ledger_summary["base_component_count"] == expected["base_component_count"],
        "official_damage_case_count": damage_summary["case_count"] == expected["official_damage_case_count"],
        "official_damage_expanded_segment_count": damage_summary["expanded_segment_count"] == expected["official_damage_expanded_segment_count"],
        "official_damage_floor_comparison_count": damage_summary["case_floor_comparison_count"] == expected["official_damage_floor_comparison_count"],
        "official_damage_floor_comparison_pass_count": damage_summary["case_floor_comparison_pass_count"] == expected["official_damage_floor_comparison_pass_count"],
        "official_reference_removal_segment_count": damage_summary["reference_removal_segment_count_all_cases"] == expected["official_reference_removal_segment_count"],
        "fuel_bin_rounding_residual": close(ledger_summary["fuel_bin_rounding_residual_lb"], expected["fuel_bin_rounding_residual_lb"]),
        "debris_bin_rounding_residual": close(ledger_summary["debris_bin_rounding_residual_lb"], expected["debris_bin_rounding_residual_lb"]),
        "nonfuel_mass_not_in_stated_debris_total": close(
            ledger_summary["nonfuel_mass_not_in_stated_debris_total_lb"],
            expected["nonfuel_mass_not_in_stated_debris_total_lb"],
        ),
        "full_postimpact_ledger_closed_count": ledger_summary["full_postimpact_mass_momentum_energy_ledger_closed_count"] == expected["full_postimpact_mass_momentum_energy_ledger_closed_count"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"Predeclared count or ledger gate failed: {[key for key, value in checks.items() if not value]}")
    tracks = build_tracks(config, transfer, v8s, v9m, v10o_trace, damage_summary, ledger_summary)
    if len(tracks) != expected["track_count"]:
        raise RuntimeError("Unexpected three-track manifest count")
    if any(track["downstream_physical_release"] for track in tracks):
        raise RuntimeError("A V10P track attempted physical downstream release")
    unknown = next(track for track in tracks if track["track_id"] == "UNKNOWN_PHYSICAL_DAMAGE")
    if any(value is not None for key, value in unknown["damage_handoff"].items() if key != "module_status"):
        raise RuntimeError("Unknown physical damage branch contains a non-null damage/distribution field")

    track_manifest = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_THREE_TRACK_SOFTWARE_HANDOFF_ONLY",
        "contract": config["track_contract"],
        "tracks": tracks,
        "damage_transformation_comparisons": comparisons,
        "epistemic_nonmerge_rule": "CONTROL, OFFICIAL_MODEL_DEPENDENT and UNKNOWN_PHYSICAL_DAMAGE records must retain distinct track_id and epistemic_class fields in every downstream artifact.",
        "historical_physical_damage_promotion_count": 0,
        "downstream_physical_release_count": 0,
    }
    ledger_audit = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_BOUNDED_ACCOUNTING_WITH_FULL_POSTIMPACT_CLOSURE_INDETERMINATE",
        "predeclared_checks": checks,
        "damage_summary": damage_summary,
        "ledger_summary": ledger_summary,
        "ledger_row_count": len(ledger_rows),
        "full_postimpact_mass_momentum_energy_ledger_closed_count": 0,
        "interpretation": "Incoming scalar accounting and cached transformations replay. Full postimpact conservation cannot be evaluated from the available outputs and remains indeterminate, not failed and not passed.",
    }
    gate = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS",
        "regression_gate": "PASS",
        "protected_blender_master_gate": "PASS_UNCHANGED",
        "source_identity_gate": "PASS_5_CACHED_PLUS_2_OFFICIAL_HASH_ONLY",
        "three_track_separation_gate": "PASS_3_OF_3",
        "incoming_scalar_mass_energy_momentum_gate": "PASS_3_OF_3",
        "damage_transcription_to_v8a_gate": f"PASS_{damage_summary['case_floor_comparison_pass_count']}_OF_{damage_summary['case_floor_comparison_count']}",
        "fuel_bin_sum_gate": "ROUNDING_RESIDUAL_RETAINED_20_LB",
        "debris_bin_sum_gate": "ROUNDING_RESIDUAL_RETAINED_250_LB",
        "nonfuel_mass_accounting_gate": "PARTIAL_21500_LB_NOT_IN_STATED_DEBRIS_TOTAL",
        "full_postimpact_mass_conservation_gate": "INDETERMINATE",
        "full_postimpact_vector_momentum_gate": "INDETERMINATE",
        "full_postimpact_energy_gate": "INDETERMINATE",
        "physical_impact_damage_gate": "CLOSED_V9M",
        "historical_physical_damage_promotion_count": 0,
        "downstream_physical_release_count": 0,
        "v10q_dependent_fire_reference_handoff_authorized": True,
        "v10q_physical_fire_initial_condition_authorized": False,
        "mechanical_source_gate": "OPEN_0_OF_22_REQUIREMENTS",
        "historical_collapse_or_noncollapse_conclusion_authorized": False,
        "physical_assignment_count": 0,
        "solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    runtime_seconds = time.perf_counter() - started
    if runtime_seconds > config["execution_policy"]["maximum_runtime_seconds"]:
        raise RuntimeError("V10P exceeded the predeclared runtime limit")

    outputs = config["outputs"]
    write_json(abs_path(outputs["regression_audit"]), regression)
    write_json(abs_path(outputs["source_manifest"]), source_manifest)
    write_json(abs_path(outputs["track_manifest"]), track_manifest)
    write_csv(
        abs_path(outputs["damage_matrix"]),
        [
            "case_id", "column_id", "floor", "member_segment_id", "reported_state",
            "max_lateral_deformation_in", "max_lateral_deformation_m",
            "reference_removal_if_severed_or_heavy", "final_case_b_rule_applies",
            "v8a_reported_state", "v8a_transformation_match", "evidence_class",
            "independent_observation", "physical_damage_assignment", "downstream_physical_release",
        ],
        damage_rows,
    )
    write_csv(abs_path(outputs["conservation_ledger"]), list(ledger_rows[0].keys()), ledger_rows)
    write_json(abs_path(outputs["ledger_audit"]), ledger_audit)
    write_json(abs_path(outputs["handoff_gate"]), gate)
    write_text(abs_path(outputs["report"]), make_report(config, damage_summary, ledger_summary, comparisons))

    results = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
        "validation_status": "PASS_THREE_TRACK_SOFTWARE_HANDOFF_ONLY",
        "dataset": config["dataset"],
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256_file(CONFIG_PATH)},
        "script": {"path": rel(SCRIPT_PATH), "sha256": sha256_file(SCRIPT_PATH)},
        "source_summary": {"cached_input_count": len(cached_rows), "official_source_hash_only_count": len(official_rows)},
        "track_summary": {
            "track_ids": [track["track_id"] for track in tracks],
            "track_count": len(tracks),
            "official_reference_case_count": len(CASES),
            "unknown_damage_fields_null": True,
            "downstream_physical_release_count": 0,
        },
        "damage_summary": {
            key: value for key, value in damage_summary.items() if key != "per_case"
        },
        "ledger_summary": ledger_summary,
        "gates": gate,
        "epistemic_separation": {
            "observed_facts": "File identities, cached numeric values, arithmetic sums and exact cached transformation comparisons.",
            "official_model_results": "All less/base/more-severe damage and fuel/debris distributions remain dependent NIST model outputs.",
            "archive_claims": "No external source archive is read; two local official PDFs are hash-checked only.",
            "model_hypotheses": "No new damage, opening, debris or fuel distribution is invented.",
            "derived_results": "Incoming scalar ledgers, published-table residuals, expanded damage matrix and V8A consistency.",
            "unknowns": "The physical damage state and full postimpact mass, momentum and energy ledgers remain indeterminate.",
        },
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "next_iteration": config["next_iteration"],
    }
    write_json(abs_path(outputs["results"]), results)

    artifact_roles = [
        "regression_audit", "source_manifest", "track_manifest", "damage_matrix",
        "conservation_ledger", "ledger_audit", "handoff_gate", "report", "results",
    ]
    artifacts = []
    for role in artifact_roles:
        path = abs_path(outputs[role])
        if not path.is_file():
            raise RuntimeError(f"Missing output {role}: {path}")
        artifacts.append({"role": role, "path": rel(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    offline = {
        "iteration": "V10P",
        "generated_at_utc": utc_now(),
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
        "historical_physical_damage_promotion_count": 0,
        "downstream_physical_release_count": 0,
        "physical_assignment_count": 0,
        "solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
    }
    write_json(abs_path(outputs["offline_audit"]), offline)

    print(
        json.dumps(
            {
                "iteration": "V10P",
                "status": "PASS_THREE_TRACK_SOFTWARE_HANDOFF_ONLY",
                "tracks": len(tracks),
                "incoming_scalar_ledgers_passed": ledger_summary["incoming_scalar_ledger_pass_count"],
                "damage_segments": damage_summary["expanded_segment_count"],
                "damage_case_floor_comparisons_passed": damage_summary["case_floor_comparison_pass_count"],
                "fuel_bin_residual_lb": ledger_summary["fuel_bin_rounding_residual_lb"],
                "debris_bin_residual_lb": ledger_summary["debris_bin_rounding_residual_lb"],
                "full_postimpact_ledgers_closed": 0,
                "physical_damage_promotions": 0,
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
        print(f"V10P ERROR: {exc}", file=sys.stderr)
        raise
