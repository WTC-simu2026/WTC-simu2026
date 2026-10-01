"""V10Y: first integrated exploratory WTC 1 impact-fire-gravity chain.

This reduced-order model deliberately trades source completeness for an
executable first version.  Official-model-dependent damage and temperature
envelopes are combined with visibly labelled hypotheses for reserve, story
mass, energy absorption and local load redistribution.  Collapse propagation,
when it occurs, receives gravity energy only.  Grid frequencies are not event
probabilities and no result is a scientific or historical validation.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10y_integrated_exploratory_chain.json"


def now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def check_files(entries: list[dict[str, Any]], group: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        path = resolve_path(entry["path"])
        exists = path.is_file()
        actual = sha256(path) if exists else None
        rows.append(
            {
                "group": group,
                "role": entry["role"],
                "path": rel(path),
                "exists": exists,
                "expected_sha256": entry["expected_sha256"],
                "actual_sha256": actual,
                "hash_match": exists and actual == entry["expected_sha256"],
            }
        )
    return rows


def assert_fresh(outputs: dict[str, str]) -> None:
    collisions = [rel(resolve_path(value)) for value in outputs.values() if resolve_path(value).exists()]
    if collisions:
        raise FileExistsError("V10Y refuses to overwrite existing artifacts: " + ", ".join(collisions))


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def yield_ratio_direct(temperature_c: float, law: dict[str, Any]) -> float:
    p = law["parameters"]
    return (1.0 - float(p["A2"])) * math.exp(
        -0.5
        * (
            (temperature_c / float(p["s1_c"])) ** float(p["m1"])
            + (temperature_c / float(p["s2_c"])) ** float(p["m2"])
        )
    ) + float(p["A2"])


def normalized_yield_ratio(temperature_c: float, law: dict[str, Any]) -> float:
    reference = float(law["normalization_temperature_c"])
    return yield_ratio_direct(temperature_c, law) / yield_ratio_direct(reference, law)


def build_temperature_index(rows: list[dict[str, str]]) -> dict[tuple[str, int], list[dict[str, float]]]:
    index: dict[tuple[str, int], list[dict[str, float]]] = {}
    for row in rows:
        key = (row["component_family"], int(row["floor"]))
        index.setdefault(key, []).append(
            {
                "time_s": float(row["time_s"]),
                "low_c": float(row["temperature_min_c"]),
                "high_c": float(row["temperature_max_c"]),
            }
        )
    for values in index.values():
        values.sort(key=lambda row: row["time_s"])
    return index


def interpolated_temperature_range(
    index: dict[tuple[str, int], list[dict[str, float]]],
    family: str,
    floor: int,
    time_s: float,
) -> tuple[float, float, str]:
    rows = index[(family, floor)]
    if time_s <= 0.0:
        return 20.0, 20.0, "DECLARED_INITIAL_REFERENCE"
    if time_s >= rows[-1]["time_s"]:
        return rows[-1]["low_c"], rows[-1]["high_c"], "HOLD_LAST_AFTER_6000S" if time_s > 6000.0 else "SOURCE_KNOT"
    prior = {"time_s": 0.0, "low_c": 20.0, "high_c": 20.0}
    for current in rows:
        if time_s <= current["time_s"]:
            span = current["time_s"] - prior["time_s"]
            fraction = (time_s - prior["time_s"]) / span
            low = prior["low_c"] + fraction * (current["low_c"] - prior["low_c"])
            high = prior["high_c"] + fraction * (current["high_c"] - prior["high_c"])
            status = "SOURCE_KNOT" if abs(time_s - current["time_s"]) < 1.0e-9 else "LINEAR_INTERPOLATION_HYPOTHESIS"
            return low, high, status
        prior = current
    raise RuntimeError("Temperature interpolation fell through")


def build_core_damage_retention(
    rows: list[dict[str, str]], config: dict[str, Any]
) -> dict[tuple[str, int], float]:
    weights = config["exploratory_model"]["core_damage_state_capacity_loss_weights"]
    total_columns = float(config["documented_inputs"]["impact_damage_aggregate"]["total_core_column_count"])
    loss_by_key: dict[tuple[str, int], float] = {}
    for row in rows:
        key = (row["case_id"], int(row["floor"]))
        loss_by_key[key] = loss_by_key.get(key, 0.0) + float(weights[row["reported_state"]])
    return {key: clamp(1.0 - loss / total_columns, 0.0, 1.0) for key, loss in loss_by_key.items()}


def temperature_capacity_state(
    scenario: dict[str, Any],
    floor: int,
    time_s: float,
    config: dict[str, Any],
    temperature_index: dict[tuple[str, int], list[dict[str, float]]],
    core_damage: dict[tuple[str, int], float],
) -> dict[str, Any]:
    model = config["exploratory_model"]
    quantile = float(scenario["temperature_quantile"])
    temperatures: dict[str, float] = {}
    ranges: dict[str, tuple[float, float]] = {}
    statuses: dict[str, str] = {}
    membership_pass = True
    for family in ("core_column", "perimeter_column", "floor_truss"):
        low, high, status = interpolated_temperature_range(temperature_index, family, floor, time_s)
        selected = low + quantile * (high - low)
        temperatures[family] = selected
        ranges[family] = (low, high)
        statuses[family] = status
        membership_pass = membership_pass and low - 1.0e-12 <= selected <= high + 1.0e-12

    impact_case = scenario["impact_case"]
    core_retention = core_damage.get((impact_case, floor), 1.0)
    perimeter_base_loss = float(model["perimeter_base_capacity_loss_fraction_by_floor"].get(str(floor), 0.0))
    perimeter_multiplier = float(model["perimeter_damage_case_multipliers"][impact_case])
    perimeter_retention = clamp(1.0 - perimeter_base_loss * perimeter_multiplier, 0.0, 1.0)
    law = config["documented_inputs"]["steel_yield_reduction"]
    core_hot = normalized_yield_ratio(temperatures["core_column"], law)
    perimeter_hot = normalized_yield_ratio(temperatures["perimeter_column"], law)
    onset = float(model["truss_pull_temperature_onset_c"])
    full = float(model["truss_pull_temperature_full_c"])
    pull_index = clamp((temperatures["floor_truss"] - onset) / (full - onset), 0.0, 1.0)
    pull_penalty = float(scenario["maximum_truss_pull_capacity_penalty"]) * pull_index
    shares = model["vertical_capacity_shares"]
    combined_retention = (
        float(shares["core"]) * core_retention * core_hot
        + float(shares["perimeter"]) * perimeter_retention * perimeter_hot * (1.0 - pull_penalty)
    )
    capacity_over_demand = (
        float(scenario["cold_capacity_demand_reserve"])
        * combined_retention
        / float(scenario["load_redistribution_factor"])
    )
    return {
        "scenario_id": scenario["scenario_id"],
        "time_s": time_s,
        "time_min": time_s / 60.0,
        "floor": floor,
        "temperature_quantile": quantile,
        "core_temperature_low_c": ranges["core_column"][0],
        "core_temperature_high_c": ranges["core_column"][1],
        "core_temperature_selected_c": temperatures["core_column"],
        "perimeter_temperature_low_c": ranges["perimeter_column"][0],
        "perimeter_temperature_high_c": ranges["perimeter_column"][1],
        "perimeter_temperature_selected_c": temperatures["perimeter_column"],
        "floor_truss_temperature_low_c": ranges["floor_truss"][0],
        "floor_truss_temperature_high_c": ranges["floor_truss"][1],
        "floor_truss_temperature_selected_c": temperatures["floor_truss"],
        "interpolation_status": "|".join(sorted(set(statuses.values()))),
        "temperature_membership_pass": membership_pass,
        "core_damage_retention": core_retention,
        "perimeter_damage_retention": perimeter_retention,
        "core_hot_yield_ratio_to_20c": core_hot,
        "perimeter_hot_yield_ratio_to_20c": perimeter_hot,
        "truss_pull_index": pull_index,
        "truss_pull_capacity_penalty": pull_penalty,
        "combined_capacity_retention": combined_retention,
        "capacity_over_demand": capacity_over_demand,
        "demand_over_capacity": 1.0 / max(capacity_over_demand, 1.0e-30),
    }


def evaluate_initiation(
    scenario: dict[str, Any],
    config: dict[str, Any],
    temperature_index: dict[tuple[str, int], list[dict[str, float]]],
    core_damage: dict[tuple[str, int], float],
    keep_rows: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    model = config["exploratory_model"]
    end_time = int(round(float(model["simulation_end_after_impact_s"])))
    step = int(round(float(model["thermal_time_step_s"])))
    floors = list(range(93, 100))
    initiation: dict[str, Any] | None = None
    all_rows: list[dict[str, Any]] = []
    maximum_dcr = -math.inf
    maximum_row: dict[str, Any] | None = None
    cold_maximum_dcr = -math.inf
    snapshot: dict[int, dict[str, Any]] = {}
    all_membership_pass = True
    for time_s in range(0, end_time + 1, step):
        time_rows = [
            temperature_capacity_state(scenario, floor, float(time_s), config, temperature_index, core_damage)
            for floor in floors
        ]
        for row in time_rows:
            dcr = float(row["demand_over_capacity"])
            if time_s == 0:
                cold_maximum_dcr = max(cold_maximum_dcr, dcr)
            if dcr > maximum_dcr:
                maximum_dcr = dcr
                maximum_row = row
            all_membership_pass = all_membership_pass and bool(row["temperature_membership_pass"])
        controlling = max(time_rows, key=lambda row: float(row["demand_over_capacity"]))
        if initiation is None and float(controlling["demand_over_capacity"]) >= 1.0:
            initiation = dict(controlling)
            snapshot = {int(row["floor"]): dict(row) for row in time_rows}
        if keep_rows:
            all_rows.extend(time_rows)
    audit = {
        "cold_maximum_dcr": cold_maximum_dcr,
        "maximum_dcr_in_window": maximum_dcr,
        "maximum_dcr_floor": None if maximum_row is None else int(maximum_row["floor"]),
        "maximum_dcr_time_s": None if maximum_row is None else float(maximum_row["time_s"]),
        "all_temperature_membership_pass": all_membership_pass,
    }
    return initiation, audit, all_rows, snapshot


def propagate(
    scenario: dict[str, Any],
    initiation: dict[str, Any] | None,
    initiation_snapshot: dict[int, dict[str, Any]],
    config: dict[str, Any],
    keep_rows: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if initiation is None:
        return (
            {
                "outcome_label": "NO_INITIATION_WITHIN_THERMAL_WINDOW",
                "arrest_story": None,
                "arrest_fraction_through_story": None,
                "stories_failed": 0,
                "collapse_duration_s": None,
                "maximum_velocity_m_s": 0.0,
                "initial_upper_block_mass_kg": None,
                "final_moving_mass_kg": None,
                "initial_gravity_release_j": 0.0,
                "gravity_work_during_propagation_j": 0.0,
                "structural_resistance_work_j": 0.0,
                "inelastic_accretion_loss_j": 0.0,
                "final_kinetic_energy_j": 0.0,
                "maximum_normalized_energy_residual": 0.0,
            },
            [],
            [],
        )
    model = config["exploratory_model"]
    tower = config["documented_inputs"]["tower"]
    gravity = float(model["gravity_m_s2"])
    height = float(tower["upper_office_story_height_m"])
    top_floor = int(tower["above_grade_floor_count"])
    initiation_floor = int(initiation["floor"])
    floor_mass = float(scenario["floor_mass_kg"])
    moving_floor_equivalents = top_floor - initiation_floor + float(model["initial_upper_block_floor_equivalent_offset"])
    moving_mass = moving_floor_equivalents * floor_mass
    initial_mass = moving_mass
    drop_fraction = float(scenario["initial_drop_fraction_of_story"])
    initial_gravity_release = moving_mass * gravity * height * drop_fraction
    velocity = math.sqrt(2.0 * gravity * height * drop_fraction)
    maximum_velocity = velocity
    relative_time = 0.0
    cumulative_drop = height * drop_fraction
    total_gravity = 0.0
    total_resistance = 0.0
    total_accretion_loss = 0.0
    maximum_residual = 0.0
    ledger_rows: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = [
        {
            "scenario_id": scenario["scenario_id"],
            "event_index": 0,
            "relative_time_s": 0.0,
            "crush_front_floor": initiation_floor,
            "event": "INITIATION_AND_INITIAL_DROP",
            "story_fraction": drop_fraction,
            "upper_block_drop_m": cumulative_drop,
            "velocity_m_s": velocity,
            "moving_mass_kg": moving_mass,
        }
    ] if keep_rows else []
    stories_failed = 0
    arrest_story: int | None = None
    arrest_fraction: float | None = None
    base_resistance = float(scenario["intact_story_resistance_at_floor98_GJ"]) * 1.0e9
    gradient = float(model["story_resistance_gradient_to_ground"])
    outcome = "GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL"

    for event_index, floor in enumerate(range(initiation_floor - 1, 0, -1), start=1):
        kinetic_start = 0.5 * moving_mass * velocity * velocity
        gravity_full = moving_mass * gravity * height
        intact_factor = 1.0 + gradient * max(0.0, 98.0 - float(floor)) / 97.0
        capacity_retention = (
            float(initiation_snapshot[floor]["combined_capacity_retention"])
            if floor in initiation_snapshot
            else 1.0
        )
        resistance_full = base_resistance * intact_factor * capacity_retention
        available_after_full_crush = kinetic_start + gravity_full - resistance_full
        mass_before = moving_mass
        velocity_start = velocity
        if available_after_full_crush <= 0.0:
            resistance_per_m = resistance_full / height
            net_decelerating_force = resistance_per_m - moving_mass * gravity
            distance = kinetic_start / max(net_decelerating_force, 1.0e-30)
            distance = clamp(distance, 0.0, height)
            gravity_used = moving_mass * gravity * distance
            resistance_used = resistance_per_m * distance
            acceleration = gravity - resistance_per_m / moving_mass
            delta_time = -velocity / acceleration if acceleration < 0.0 and velocity > 0.0 else 0.0
            relative_time += delta_time
            cumulative_drop += distance
            residual = kinetic_start + gravity_used - resistance_used
            normalized_residual = abs(residual) / max(kinetic_start + gravity_used + resistance_used, 1.0)
            maximum_residual = max(maximum_residual, normalized_residual)
            total_gravity += gravity_used
            total_resistance += resistance_used
            arrest_story = floor
            arrest_fraction = distance / height
            velocity = 0.0
            outcome = "INITIATED_THEN_ARRESTED"
            if keep_rows:
                ledger_rows.append(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "event_index": event_index,
                        "story": floor,
                        "event": "ARREST_WITHIN_STORY",
                        "mass_before_kg": mass_before,
                        "story_mass_accreted_kg": 0.0,
                        "kinetic_start_j": kinetic_start,
                        "gravity_work_j": gravity_used,
                        "structural_resistance_work_j": resistance_used,
                        "kinetic_before_accretion_j": 0.0,
                        "inelastic_accretion_loss_j": 0.0,
                        "kinetic_end_j": 0.0,
                        "energy_residual_j": residual,
                        "normalized_energy_residual": normalized_residual,
                        "intact_story_resistance_j": base_resistance * intact_factor,
                        "capacity_retention_multiplier": capacity_retention,
                        "available_story_resistance_j": resistance_full,
                    }
                )
                timeline_rows.append(
                    {
                        "scenario_id": scenario["scenario_id"],
                        "event_index": event_index,
                        "relative_time_s": relative_time,
                        "crush_front_floor": floor,
                        "event": "ARREST_WITHIN_STORY",
                        "story_fraction": arrest_fraction,
                        "upper_block_drop_m": cumulative_drop,
                        "velocity_m_s": 0.0,
                        "moving_mass_kg": moving_mass,
                    }
                )
            break

        kinetic_before_accretion = available_after_full_crush
        velocity_before_accretion = math.sqrt(2.0 * kinetic_before_accretion / moving_mass)
        delta_time = 2.0 * height / max(velocity_start + velocity_before_accretion, 1.0e-30)
        relative_time += delta_time
        cumulative_drop += height
        new_mass = moving_mass + floor_mass
        velocity_after = moving_mass * velocity_before_accretion / new_mass
        kinetic_end = 0.5 * new_mass * velocity_after * velocity_after
        accretion_loss = kinetic_before_accretion - kinetic_end
        residual = kinetic_start + gravity_full - resistance_full - accretion_loss - kinetic_end
        normalized_residual = abs(residual) / max(
            kinetic_start + gravity_full + resistance_full + accretion_loss + kinetic_end,
            1.0,
        )
        maximum_residual = max(maximum_residual, normalized_residual)
        total_gravity += gravity_full
        total_resistance += resistance_full
        total_accretion_loss += accretion_loss
        stories_failed += 1
        moving_mass = new_mass
        velocity = velocity_after
        maximum_velocity = max(maximum_velocity, velocity_before_accretion, velocity_after)
        if keep_rows:
            ledger_rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "event_index": event_index,
                    "story": floor,
                    "event": "STORY_FAILED_AND_MASS_ACCRETED",
                    "mass_before_kg": mass_before,
                    "story_mass_accreted_kg": floor_mass,
                    "kinetic_start_j": kinetic_start,
                    "gravity_work_j": gravity_full,
                    "structural_resistance_work_j": resistance_full,
                    "kinetic_before_accretion_j": kinetic_before_accretion,
                    "inelastic_accretion_loss_j": accretion_loss,
                    "kinetic_end_j": kinetic_end,
                    "energy_residual_j": residual,
                    "normalized_energy_residual": normalized_residual,
                    "intact_story_resistance_j": base_resistance * intact_factor,
                    "capacity_retention_multiplier": capacity_retention,
                    "available_story_resistance_j": resistance_full,
                }
            )
            timeline_rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "event_index": event_index,
                    "relative_time_s": relative_time,
                    "crush_front_floor": floor - 1,
                    "event": "STORY_FAILED_AND_MASS_ACCRETED",
                    "story_fraction": 1.0,
                    "upper_block_drop_m": cumulative_drop,
                    "velocity_m_s": velocity,
                    "moving_mass_kg": moving_mass,
                }
            )

    final_kinetic = 0.5 * moving_mass * velocity * velocity
    summary = {
        "outcome_label": outcome,
        "arrest_story": arrest_story,
        "arrest_fraction_through_story": arrest_fraction,
        "stories_failed": stories_failed,
        "collapse_duration_s": relative_time,
        "maximum_velocity_m_s": maximum_velocity,
        "initial_upper_block_mass_kg": initial_mass,
        "final_moving_mass_kg": moving_mass,
        "initial_gravity_release_j": initial_gravity_release,
        "gravity_work_during_propagation_j": total_gravity,
        "structural_resistance_work_j": total_resistance,
        "inelastic_accretion_loss_j": total_accretion_loss,
        "final_kinetic_energy_j": final_kinetic,
        "maximum_normalized_energy_residual": maximum_residual,
    }
    return summary, ledger_rows, timeline_rows


def simulate_scenario(
    scenario: dict[str, Any],
    config: dict[str, Any],
    temperature_index: dict[tuple[str, int], list[dict[str, float]]],
    core_damage: dict[tuple[str, int], float],
    keep_rows: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    initiation, initiation_audit, capacity_rows, snapshot = evaluate_initiation(
        scenario, config, temperature_index, core_damage, keep_rows
    )
    propagation, ledger_rows, timeline_rows = propagate(scenario, initiation, snapshot, config, keep_rows)
    aircraft = config["documented_inputs"]["aircraft_cases"][scenario["impact_case"]]
    summary = {
        **{key: scenario[key] for key in scenario},
        "aircraft_kinetic_energy_GJ_reference_only": float(aircraft["kinetic_energy_GJ"]),
        "aircraft_energy_reinjected_after_initiation": False,
        **initiation_audit,
        "initiation_time_s_after_impact": None if initiation is None else float(initiation["time_s"]),
        "initiation_time_min_after_impact": None if initiation is None else float(initiation["time_min"]),
        "initiation_floor": None if initiation is None else int(initiation["floor"]),
        "initiation_dcr": None if initiation is None else float(initiation["demand_over_capacity"]),
        **propagation,
    }
    return summary, capacity_rows, ledger_rows, timeline_rows


def grid_scenarios(config: dict[str, Any]) -> list[dict[str, Any]]:
    grid = config["exploratory_model"]["sensitivity_grid"]
    rows: list[dict[str, Any]] = []
    axes = (
        grid["impact_case"],
        grid["temperature_quantile"],
        grid["cold_capacity_demand_reserve"],
        grid["floor_mass_kg"],
        grid["intact_story_resistance_at_floor98_GJ"],
        grid["initial_drop_fraction_of_story"],
    )
    for index, values in enumerate(itertools.product(*axes), start=1):
        impact, quantile, reserve, mass, resistance, drop = values
        rows.append(
            {
                "scenario_id": f"GRID-{index:04d}",
                "scenario_class": "DETERMINISTIC_SENSITIVITY_GRID_NOT_PROBABILITY",
                "impact_case": impact,
                "temperature_quantile": float(quantile),
                "cold_capacity_demand_reserve": float(reserve),
                "load_redistribution_factor": float(grid["fixed_load_redistribution_factor"]),
                "maximum_truss_pull_capacity_penalty": float(grid["fixed_maximum_truss_pull_capacity_penalty"]),
                "floor_mass_kg": float(mass),
                "intact_story_resistance_at_floor98_GJ": float(resistance),
                "initial_drop_fraction_of_story": float(drop),
            }
        )
    return rows


def run_ensemble(
    config: dict[str, Any],
    temperature_index: dict[tuple[str, int], list[dict[str, float]]],
    core_damage: dict[tuple[str, int], float],
    keep_named_rows: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    named_summaries: list[dict[str, Any]] = []
    capacity_rows: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    timeline_rows: list[dict[str, Any]] = []
    for declared in config["exploratory_model"]["named_scenarios"]:
        scenario = {"scenario_class": "NAMED_EXPLORATORY_ENVELOPE", **declared}
        summary, capacity, ledger, timeline = simulate_scenario(
            scenario, config, temperature_index, core_damage, keep_named_rows
        )
        named_summaries.append(summary)
        capacity_rows.extend(capacity)
        ledger_rows.extend(ledger)
        timeline_rows.extend(timeline)
    grid_summaries: list[dict[str, Any]] = []
    for scenario in grid_scenarios(config):
        summary, _, _, _ = simulate_scenario(scenario, config, temperature_index, core_damage, False)
        grid_summaries.append(summary)
    return named_summaries, grid_summaries, capacity_rows, ledger_rows, timeline_rows


def canonical_digest(named: list[dict[str, Any]], grid: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        {"named": named, "grid": grid},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parameter_ledger(config: dict[str, Any]) -> list[dict[str, Any]]:
    model = config["exploratory_model"]
    tower = config["documented_inputs"]["tower"]
    chronology = config["documented_inputs"]["chronology"]
    aggregate = config["documented_inputs"]["impact_damage_aggregate"]
    rows = [
        ("tower.floor_count", tower["above_grade_floor_count"], "floor", "DOCUMENTED_INPUT", tower["source"], "vertical extent"),
        ("tower.story_height", tower["upper_office_story_height_m"], "m", "DOCUMENTED_INPUT", tower["source"], "vertical kinematics"),
        ("chronology.observed_survival", chronology["observed_survival_after_impact_s"], "s", "DOCUMENTED_FACT_COMPARISON_ONLY", chronology["source"], "comparison, not calibration"),
        ("impact.north_severe_columns", aggregate["north_wall_columns_severed_or_heavily_damaged"], "column", "OFFICIAL_REPORT_TRANSCRIPTION", aggregate["source"], "aggregate damage context"),
        ("impact.south_severe_columns", aggregate["south_wall_columns_severed_or_heavily_damaged"], "column", "OFFICIAL_REPORT_TRANSCRIPTION", aggregate["source"], "aggregate damage context"),
        ("impact.core_severe_columns", aggregate["core_columns_severed_or_heavily_damaged"], "column", "OFFICIAL_REPORT_TRANSCRIPTION", aggregate["source"], "aggregate damage context"),
        ("capacity.core_share", model["vertical_capacity_shares"]["core"], "fraction", "EXPLORATORY_HYPOTHESIS", "declared V10Y parameter", "capacity mixture"),
        ("capacity.perimeter_share", model["vertical_capacity_shares"]["perimeter"], "fraction", "EXPLORATORY_HYPOTHESIS", "declared V10Y parameter", "capacity mixture"),
        ("impact.core_state_weights", model["core_damage_state_capacity_loss_weights"], "mapping", "EXPLORATORY_HYPOTHESIS_USING_OFFICIAL_MODEL_STATES", "V10P states plus V10Y weights", "floorwise core retention"),
        ("impact.perimeter_floor_profile", model["perimeter_base_capacity_loss_fraction_by_floor"], "mapping", "EXPLORATORY_HYPOTHESIS_CONSTRAINED_BY_AGGREGATE", "V8J aggregate plus V10Y profile", "floorwise perimeter retention"),
        ("thermal.interpolation", "linear between knots; hold after 6000 s", "rule", "EXPLORATORY_HYPOTHESIS", "V10Y", "continuous capacity history"),
        ("thermal.yield_reduction", config["documented_inputs"]["steel_yield_reduction"]["equation"], "equation", "OFFICIAL_MODEL_DEPENDENT_WITH_EXPLICIT_HIGH_T_EXTENSION", "nist_wtc1_transfer.json", "hot strength"),
        ("initiation.rule", model["initiation_rule"], "rule", "EXPLORATORY_HYPOTHESIS", "V10Y", "first DCR crossing"),
        ("propagation.rule", model["propagation_rule"], "rule", "EXPLORATORY_HYPOTHESIS", "V10Y", "crush-down or arrest"),
        ("propagation.energy_sources", model["energy_sources_after_initiation"], "list", "MODEL_CONSTRAINT", "V10Y", "energy ledger"),
        ("propagation.absent_sources", model["explicitly_absent_energy_sources"], "list", "MODEL_CONSTRAINT", "V10Y", "causal isolation"),
    ]
    for scenario in model["named_scenarios"]:
        for key in (
            "temperature_quantile", "cold_capacity_demand_reserve", "load_redistribution_factor",
            "maximum_truss_pull_capacity_penalty", "floor_mass_kg",
            "intact_story_resistance_at_floor98_GJ", "initial_drop_fraction_of_story"
        ):
            unit = "kg" if key == "floor_mass_kg" else "GJ" if key.endswith("_GJ") else "fraction_or_ratio"
            rows.append(
                (
                    f"{scenario['scenario_id']}.{key}", scenario[key], unit, "EXPLORATORY_HYPOTHESIS",
                    "predeclared V10Y named scenario", "named envelope"
                )
            )
    return [
        {
            "parameter_id": key,
            "value": json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value,
            "unit": unit,
            "epistemic_class": epistemic,
            "source_or_reason": source,
            "model_use": use,
        }
        for key, value, unit, epistemic, source, use in rows
    ]


def create_dashboard(
    path: Path,
    capacity_rows: list[dict[str, Any]],
    named: list[dict[str, Any]],
    timeline_rows: list[dict[str, Any]],
    observed_survival_s: float,
) -> None:
    width, height = 1120.0, 780.0
    left, right = 100.0, 35.0
    top1, panel_h, gap = 75.0, 270.0, 95.0
    top2 = top1 + panel_h + gap
    plot_w = width - left - right
    colours = {"RESISTANT_ENVELOPE":"#1565c0", "CENTRAL_EXPLORATORY":"#ef6c00", "VULNERABLE_ENVELOPE":"#c62828"}

    def x1(value: float) -> float:
        return left + value / 105.0 * plot_w

    max_dcr = max(2.0, min(5.0, max(float(row["demand_over_capacity"]) for row in capacity_rows) * 1.05))

    def y1(value: float) -> float:
        return top1 + (max_dcr - value) / max_dcr * panel_h

    max_time = max((float(row["relative_time_s"]) for row in timeline_rows), default=15.0)
    max_time = max(5.0, max_time * 1.05)

    def x2(value: float) -> float:
        return left + value / max_time * plot_w

    def y2(floor: float) -> float:
        return top2 + (110.0 - floor) / 110.0 * panel_h

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#202124}.title{font-size:22px;font-weight:600}.subtitle{font-size:16px;font-weight:600}.tick{font-size:12px}.legend{font-size:13px}.note{font-size:12px;fill:#555}</style>',
        f'<text x="{width/2:.1f}" y="32" text-anchor="middle" class="title">V10Y — chaîne exploratoire impact + feux localisés + gravité</text>',
        f'<text x="{left:.1f}" y="{top1-18:.1f}" class="subtitle">Initiation : demande / capacité maximale sur les étages 93–99</text>',
    ]
    for minute in [0, 20, 40, 60, 80, 100]:
        x = x1(float(minute))
        svg.append(f'<line x1="{x:.2f}" y1="{top1:.2f}" x2="{x:.2f}" y2="{top1+panel_h:.2f}" stroke="#e0e0e0"/>')
        svg.append(f'<text x="{x:.2f}" y="{top1+panel_h+21:.2f}" text-anchor="middle" class="tick">{minute}</text>')
    for value in [0.0, 0.5, 1.0, 1.5, 2.0]:
        if value <= max_dcr:
            y = y1(value)
            svg.append(f'<line x1="{left:.2f}" y1="{y:.2f}" x2="{left+plot_w:.2f}" y2="{y:.2f}" stroke="#e0e0e0"/>')
            svg.append(f'<text x="{left-10:.2f}" y="{y+4:.2f}" text-anchor="end" class="tick">{value:g}</text>')
    svg.append(f'<line x1="{left:.2f}" y1="{y1(1.0):.2f}" x2="{left+plot_w:.2f}" y2="{y1(1.0):.2f}" stroke="#111" stroke-width="1.4" stroke-dasharray="7 5"/>')
    observed_x = x1(observed_survival_s / 60.0)
    svg.append(f'<line x1="{observed_x:.2f}" y1="{top1:.2f}" x2="{observed_x:.2f}" y2="{top1+panel_h:.2f}" stroke="#555" stroke-width="1.2" stroke-dasharray="3 4"/>')
    for scenario in named:
        sid = scenario["scenario_id"]
        grouped: dict[float, float] = {}
        for row in capacity_rows:
            if row["scenario_id"] == sid:
                minute = float(row["time_min"])
                grouped[minute] = max(grouped.get(minute, -math.inf), float(row["demand_over_capacity"]))
        points = " ".join(f"{x1(minute):.2f},{y1(value):.2f}" for minute, value in sorted(grouped.items()))
        svg.append(f'<polyline points="{points}" fill="none" stroke="{colours[sid]}" stroke-width="2.2"/>')
    svg.append(f'<rect x="{left:.2f}" y="{top1:.2f}" width="{plot_w:.2f}" height="{panel_h:.2f}" fill="none" stroke="#444"/>')
    svg.append(f'<text x="{left+plot_w/2:.2f}" y="{top1+panel_h+45:.2f}" text-anchor="middle" class="tick">Temps après impact (min)</text>')
    svg.append(f'<text x="{left:.1f}" y="{top2-18:.1f}" class="subtitle">Propagation : position du front d’écrasement après initiation</text>')
    for floor in [110, 90, 70, 50, 30, 10, 0]:
        y = y2(float(floor))
        svg.append(f'<line x1="{left:.2f}" y1="{y:.2f}" x2="{left+plot_w:.2f}" y2="{y:.2f}" stroke="#e0e0e0"/>')
        svg.append(f'<text x="{left-10:.2f}" y="{y+4:.2f}" text-anchor="end" class="tick">{floor}</text>')
    for sid, colour in colours.items():
        rows = [row for row in timeline_rows if row["scenario_id"] == sid]
        if rows:
            points = " ".join(
                f"{x2(float(row['relative_time_s'])):.2f},{y2(float(row['crush_front_floor'])):.2f}"
                for row in rows
            )
            svg.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="2.2"/>')
    svg.append(f'<rect x="{left:.2f}" y="{top2:.2f}" width="{plot_w:.2f}" height="{panel_h:.2f}" fill="none" stroke="#444"/>')
    svg.append(f'<text x="{left+plot_w/2:.2f}" y="{top2+panel_h+42:.2f}" text-anchor="middle" class="tick">Temps après initiation (s)</text>')
    legend_y = height - 24.0
    legend_x = left
    for index, scenario in enumerate(named):
        sid = scenario["scenario_id"]
        x = legend_x + index * 315.0
        svg.append(f'<line x1="{x:.1f}" y1="{legend_y:.1f}" x2="{x+28:.1f}" y2="{legend_y:.1f}" stroke="{colours[sid]}" stroke-width="3"/>')
        svg.append(f'<text x="{x+36:.1f}" y="{legend_y+4:.1f}" class="legend">{sid}</text>')
    svg.append('</svg>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def main() -> None:
    started_at = now_local()
    wall_start = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("iteration") != "V10Y":
        raise ValueError("Configuration iteration must be V10Y")
    outputs = config["outputs"]
    assert_fresh(outputs)
    expected = config["expected"]
    acceptance = config["acceptance"]
    if len(config["regression_files"]) != expected["regression_file_count"]:
        raise ValueError("Regression file count differs from predeclaration")
    if len(config["protected_files"]) != expected["protected_file_count"]:
        raise ValueError("Protected file count differs from predeclaration")
    if len(config["exploratory_model"]["named_scenarios"]) != expected["named_scenario_count"]:
        raise ValueError("Named scenario count differs from predeclaration")

    file_checks = check_files(config["regression_files"], "regression") + check_files(config["protected_files"], "protected")
    if not all(row["hash_match"] for row in file_checks):
        raise RuntimeError(f"Preflight hash failure: {[row for row in file_checks if not row['hash_match']]}")
    temperature_rows = read_csv(resolve_path(config["documented_inputs"]["temperature_envelopes"]["path"]))
    damage_entry = next(entry for entry in config["regression_files"] if entry["role"] == "v10p_damage_matrix")
    damage_rows = read_csv(resolve_path(damage_entry["path"]))
    temperature_index = build_temperature_index(temperature_rows)
    core_damage = build_core_damage_retention(damage_rows, config)
    if len(temperature_index) != 21:
        raise RuntimeError(f"Expected 21 family-floor temperature histories, got {len(temperature_index)}")

    named, grid, capacity_rows, ledger_rows, timeline_rows = run_ensemble(
        config, temperature_index, core_damage, True
    )
    replay_named, replay_grid, _, _, _ = run_ensemble(config, temperature_index, core_damage, False)
    digest_first = canonical_digest(named, grid)
    digest_replay = canonical_digest(replay_named, replay_grid)
    deterministic_replay = digest_first == digest_replay
    if len(grid) != expected["sensitivity_grid_case_count"]:
        raise RuntimeError(f"Expected {expected['sensitivity_grid_case_count']} grid cases, got {len(grid)}")

    outcome_vocabulary = set(acceptance["outcome_vocabulary"])
    all_summaries = named + grid
    outcome_counts = Counter(row["outcome_label"] for row in grid)
    all_labels_valid = all(row["outcome_label"] in outcome_vocabulary for row in all_summaries)
    all_named_cold_stable = all(float(row["cold_maximum_dcr"]) < 1.0 for row in named)
    all_temperature_membership = all(bool(row["all_temperature_membership_pass"]) for row in all_summaries)
    maximum_energy_residual = max(float(row["maximum_normalized_energy_residual"]) for row in all_summaries)
    master_check = next(row for row in file_checks if row["group"] == "protected")

    criteria = {
        "regression_hashes_pass": all(row["hash_match"] for row in file_checks if row["group"] == "regression"),
        "protected_master_unchanged": bool(master_check["hash_match"]),
        "named_scenario_count": len(named) == acceptance["named_scenario_count"],
        "sensitivity_grid_case_count": len(grid) == acceptance["sensitivity_grid_case_count"],
        "all_named_scenarios_cold_stable_immediately_after_impact": all_named_cold_stable,
        "all_interpolated_temperatures_inside_declared_envelopes": all_temperature_membership,
        "all_outcome_labels_from_vocabulary": all_labels_valid,
        "energy_ledger_residual": maximum_energy_residual <= acceptance["maximum_normalized_energy_residual"],
        "deterministic_replay_exact": deterministic_replay,
        "aircraft_energy_not_reinjected": all(not row["aircraft_energy_reinjected_after_initiation"] for row in all_summaries),
        "grid_fraction_not_historical_probability": acceptance["grid_fraction_is_historical_probability"] is False,
        "documentary_requirement_closure_count_zero": acceptance["documentary_requirement_closure_count"] == 0,
        "scientific_validation_claim_count_zero": acceptance["scientific_validation_claim_count"] == 0,
    }
    decision = "PASS_EXPLORATORY_MODEL_INTEGRITY_NOT_PHYSICAL_VALIDATION" if all(criteria.values()) else "FAIL_EXPLORATORY_MODEL_INTEGRITY"

    ledger = parameter_ledger(config)
    visualization_driver = {
        "iteration": "V10Y",
        "created_at": now_local(),
        "status": "EXPLORATORY_REDUCED_ORDER_DRIVER_NOT_VALIDATED_DYNAMICS",
        "tower": config["documented_inputs"]["tower"],
        "permanent_labels": [
            "MODÈLE EXPLORATOIRE — NON VALIDÉ SCIENTIFIQUEMENT",
            "IMPACT + FEUX LOCALISÉS + GRAVITÉ UNIQUEMENT",
            "BLENDER VISUALISE LES SORTIES V10Y; IL NE CALCULE PAS LA STRUCTURE"
        ],
        "scenarios": [
            {
                "scenario_id": summary["scenario_id"],
                "outcome_label": summary["outcome_label"],
                "initiation_time_s_after_impact": summary["initiation_time_s_after_impact"],
                "initiation_floor": summary["initiation_floor"],
                "arrest_story": summary["arrest_story"],
                "events": [row for row in timeline_rows if row["scenario_id"] == summary["scenario_id"]],
            }
            for summary in named
        ],
        "recommended_animation_scenario": (
            next((row["scenario_id"] for row in named if row["scenario_id"] == "CENTRAL_EXPLORATORY" and row["outcome_label"] != "NO_INITIATION_WITHIN_THERMAL_WINDOW"), None)
            or next((row["scenario_id"] for row in named if row["outcome_label"] == "GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL"), None)
            or next((row["scenario_id"] for row in named if row["outcome_label"] == "INITIATED_THEN_ARRESTED"), None)
            or "RESISTANT_ENVELOPE"
        ),
    }

    create_dashboard(
        resolve_path(outputs["dashboard"]),
        capacity_rows,
        named,
        timeline_rows,
        float(config["documented_inputs"]["chronology"]["observed_survival_after_impact_s"]),
    )
    write_csv(
        resolve_path(outputs["parameter_ledger"]),
        ["parameter_id", "value", "unit", "epistemic_class", "source_or_reason", "model_use"],
        ledger,
    )
    write_csv(
        resolve_path(outputs["capacity_timeline"]),
        [
            "scenario_id", "time_s", "time_min", "floor", "temperature_quantile",
            "core_temperature_low_c", "core_temperature_high_c", "core_temperature_selected_c",
            "perimeter_temperature_low_c", "perimeter_temperature_high_c", "perimeter_temperature_selected_c",
            "floor_truss_temperature_low_c", "floor_truss_temperature_high_c", "floor_truss_temperature_selected_c",
            "interpolation_status", "temperature_membership_pass", "core_damage_retention",
            "perimeter_damage_retention", "core_hot_yield_ratio_to_20c",
            "perimeter_hot_yield_ratio_to_20c", "truss_pull_index", "truss_pull_capacity_penalty",
            "combined_capacity_retention", "capacity_over_demand", "demand_over_capacity"
        ],
        capacity_rows,
    )
    summary_fields = [
        "scenario_id", "scenario_class", "impact_case", "temperature_quantile",
        "cold_capacity_demand_reserve", "load_redistribution_factor", "maximum_truss_pull_capacity_penalty",
        "floor_mass_kg", "intact_story_resistance_at_floor98_GJ", "initial_drop_fraction_of_story",
        "aircraft_kinetic_energy_GJ_reference_only", "aircraft_energy_reinjected_after_initiation",
        "cold_maximum_dcr", "maximum_dcr_in_window", "maximum_dcr_floor", "maximum_dcr_time_s",
        "all_temperature_membership_pass", "initiation_time_s_after_impact", "initiation_time_min_after_impact",
        "initiation_floor", "initiation_dcr", "outcome_label", "arrest_story",
        "arrest_fraction_through_story", "stories_failed", "collapse_duration_s", "maximum_velocity_m_s",
        "initial_upper_block_mass_kg", "final_moving_mass_kg", "initial_gravity_release_j",
        "gravity_work_during_propagation_j", "structural_resistance_work_j",
        "inelastic_accretion_loss_j", "final_kinetic_energy_j", "maximum_normalized_energy_residual"
    ]
    write_csv(resolve_path(outputs["named_summary"]), summary_fields, named)
    write_csv(resolve_path(outputs["sensitivity_grid"]), summary_fields, grid)
    write_csv(
        resolve_path(outputs["energy_ledger"]),
        [
            "scenario_id", "event_index", "story", "event", "mass_before_kg", "story_mass_accreted_kg",
            "kinetic_start_j", "gravity_work_j", "structural_resistance_work_j",
            "kinetic_before_accretion_j", "inelastic_accretion_loss_j", "kinetic_end_j",
            "energy_residual_j", "normalized_energy_residual", "intact_story_resistance_j",
            "capacity_retention_multiplier", "available_story_resistance_j"
        ],
        ledger_rows,
    )
    write_csv(
        resolve_path(outputs["propagation_timeline"]),
        [
            "scenario_id", "event_index", "relative_time_s", "crush_front_floor", "event",
            "story_fraction", "upper_block_drop_m", "velocity_m_s", "moving_mass_kg"
        ],
        timeline_rows,
    )
    write_json(resolve_path(outputs["visualization_driver"]), visualization_driver)

    regression_payload = {
        "iteration": "V10Y",
        "created_at": now_local(),
        "decision": "PASS" if criteria["regression_hashes_pass"] and criteria["protected_master_unchanged"] else "FAIL",
        "checks": file_checks,
    }
    source_manifest = {
        "iteration": "V10Y",
        "created_at": now_local(),
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        "runner": {"path": rel(Path(__file__)), "sha256": sha256(Path(__file__))},
        "upstream_checks": file_checks,
        "epistemic_policy": config["epistemic_policy"],
        "warning": "Hash identity and model integrity do not convert official-model outputs or exploratory hypotheses into independent historical measurements."
    }
    gate = {
        "iteration": "V10Y",
        "created_at": now_local(),
        "decision": decision,
        "criteria": criteria,
        "metrics": {
            "named_scenario_count": len(named),
            "sensitivity_grid_case_count": len(grid),
            "reduced_order_solver_run_count": len(named) + len(grid),
            "outcome_counts_in_grid": dict(sorted(outcome_counts.items())),
            "outcome_fractions_in_grid_not_probabilities": {
                key: count / len(grid) for key, count in sorted(outcome_counts.items())
            },
            "maximum_normalized_energy_residual": maximum_energy_residual,
            "deterministic_digest": digest_first,
            "deterministic_replay_digest": digest_replay,
            "documentary_requirement_closure_count": 0,
            "scientific_validation_claim_count": 0,
        },
        "allowed_claim": "Within this declared reduced-order hypothesis space, the model can report whether impact-selected damage plus localized fire weakening allows initiation and whether gravity then progresses or arrests the crush front.",
        "forbidden_claims": [
            "A grid fraction is the probability that WTC 1 collapsed or would collapse.",
            "A progressing scenario proves the historical collapse mechanism.",
            "A non-initiating or arrested scenario disproves aircraft-plus-fire causation.",
            "The model is a complete three-dimensional finite-element reconstruction."
        ]
    }
    global_named = [row for row in named if row["outcome_label"] == "GLOBAL_PROGRESSION_TO_GROUND_IN_REDUCED_MODEL"]
    arrest_named = [row for row in named if row["outcome_label"] == "INITIATED_THEN_ARRESTED"]
    no_init_named = [row for row in named if row["outcome_label"] == "NO_INITIATION_WITHIN_THERMAL_WINDOW"]
    results = {
        "iteration": "V10Y",
        "decision": decision,
        "model_status": "FIRST_EXECUTABLE_EXPLORATORY_VERSION_NOT_SCIENTIFIC_VALIDATION",
        "named_scenarios": named,
        "grid_summary": {
            "case_count": len(grid),
            "outcome_counts": dict(sorted(outcome_counts.items())),
            "outcome_fractions_not_probabilities": {key: count / len(grid) for key, count in sorted(outcome_counts.items())},
        },
        "bounded_answer": {
            "global_progression_found_in_named_scenarios": bool(global_named),
            "arrest_found_in_named_scenarios": bool(arrest_named),
            "no_initiation_found_in_named_scenarios": bool(no_init_named),
            "interpretation": (
                "YES_WITHIN_DECLARED_HYPOTHESES: at least one named scenario progresses to ground using impact-selected damage, localized fire weakening and gravity only. This demonstrates numerical possibility in the reduced model, not historical proof."
                if global_named
                else "NOT_IN_NAMED_SCENARIOS: no named scenario progressed to ground. Grid results must be inspected before drawing even a model-bounded conclusion."
            )
        },
        "energy_source_audit": {
            "after_initiation": config["exploratory_model"]["energy_sources_after_initiation"],
            "explicitly_absent": config["exploratory_model"]["explicitly_absent_energy_sources"],
            "aircraft_kinetic_energy_reinjected": False,
            "maximum_normalized_residual": maximum_energy_residual,
        },
        "epistemic_accounting": {
            "documented_facts": [
                "110 above-grade floors, approximately 3.6576 m upper-office story height and impact over Floors 93-99 in the selected cache.",
                "Selected chronology: impact at 08:46:26 and collapse initiation at 10:28:20, 6114 s apart."
            ],
            "official_model_results": [
                "Less/base/more-severe aircraft and core-damage cases from V10P.",
                "Floor/family/time structural-temperature ranges from V10Q."
            ],
            "model_hypotheses": [
                "Floorwise perimeter capacity-loss profile, capacity shares, cold reserves and redistribution factors.",
                "Temperature quantiles and linear interpolation/hold-last policy.",
                "Floor mass, story energy absorption, initial drop fraction, crush-down resistance gradient and perfectly inelastic mass accretion."
            ],
            "derived_results": [
                "Capacity-demand histories, initiation times/floors, gravity/resistance/accretion ledgers and propagation or arrest outcomes."
            ],
            "contradictions_and_unknowns": [
                "The V8J strict cold load-path gate remains scientifically unresolved; V10Y substitutes explicit hypotheses rather than closing it.",
                "Temperature ranges are not member-resolved histories and values above 600 C extend beyond the conservative joint V10R domain.",
                "Story resistance is not derived from a complete as-built connection/member model.",
                "The one-dimensional crush front cannot reproduce three-dimensional tilting, asymmetric failure, debris ejection or facade peeling."
            ]
        },
        "next_iteration": config["next_iteration"],
    }
    write_json(resolve_path(outputs["regression_audit"]), regression_payload)
    write_json(resolve_path(outputs["source_manifest"]), source_manifest)
    write_json(resolve_path(outputs["handoff_gate"]), gate)
    write_json(resolve_path(outputs["results"]), results)

    report_lines = [
        "# WTC 1 — V10Y — première chaîne exploratoire intégrée",
        "",
        f"**Décision d'intégrité : `{decision}`**",
        "",
        "## Réponse bornée à la question",
        "",
        results["bounded_answer"]["interpretation"],
        "",
        "Le test n'ajoute ni explosif, ni thermite, ni force imposée vers le bas. Après l'initiation, la seule énergie motrice est la gravité. L'impact intervient par la branche de dommages et l'incendie par la réduction de capacité.",
        "",
        "## Trois scénarios lisibles",
        "",
        "| Scénario | Impact | Quantile thermique | DCR froid max. | Initiation | Étage | Issue du modèle | Arrêt | Durée verticale (s) |",
        "|:---|:---|---:|---:|---:|---:|:---|---:|---:|",
    ]
    for row in named:
        initiation_min = "—" if row["initiation_time_min_after_impact"] is None else f"{float(row['initiation_time_min_after_impact']):.2f}"
        initiation_floor = "—" if row["initiation_floor"] is None else str(int(row["initiation_floor"]))
        arrest = "—" if row["arrest_story"] is None else f"{int(row['arrest_story'])} ({100.0*float(row['arrest_fraction_through_story']):.1f} %)"
        duration = "—" if row["collapse_duration_s"] is None else f"{float(row['collapse_duration_s']):.3f}"
        report_lines.append(
            f"| {row['scenario_id']} | {row['impact_case']} | {float(row['temperature_quantile']):.2f} | "
            f"{float(row['cold_maximum_dcr']):.3f} | {initiation_min} min | {initiation_floor} | "
            f"{row['outcome_label']} | {arrest} | {duration} |"
        )
    report_lines.extend(
        [
            "",
            "## Grille de sensibilité",
            "",
            f"La grille contient {len(grid)} combinaisons déterministes. Les nombres ci-dessous sont des fréquences de grille, pas des probabilités historiques :",
            "",
        ]
    )
    for label in sorted(outcome_vocabulary):
        count = outcome_counts.get(label, 0)
        report_lines.append(f"- `{label}` : {count}/{len(grid)} ({100.0*count/len(grid):.1f} % de la grille).")
    report_lines.extend(
        [
            "",
            "## Bilan d'énergie et reproductibilité",
            "",
            f"- Résidu énergétique normalisé maximal : {maximum_energy_residual:.3e}.",
            f"- Rejeu déterministe exact : {'OUI' if deterministic_replay else 'NON'} (`{digest_first}`).",
            "- L'énergie cinétique de l'avion est conservée comme référence d'impact mais n'est jamais réinjectée après l'initiation.",
            "",
            "## Ce qui est documenté et ce qui est supposé",
            "",
            "Les cas d'impact, les états de dommages du noyau et les enveloppes de température proviennent des transcriptions antérieures du modèle officiel. Les réserves de capacité, la répartition verticale noyau/périmètre, le profil de dommages du périmètre, les masses d'étage et les énergies de résistance sont des hypothèses V10Y explicites.",
            "",
            "## Limites décisives",
            "",
            "Cette version est un modèle vertical réduit, pas une tour 3D en éléments finis. Elle ne calcule ni rupture détaillée de l'avion, ni incendie CFD, ni assemblages réels, ni flambement local, ni fracture, ni basculement asymétrique. Une issue progressive montre seulement qu'une chaîne cohérente existe dans certaines plages déclarées; une issue arrêtée montre que la conclusion dépend fortement de paramètres encore hypothétiques.",
            "",
            "Aucune des 22 exigences documentaires mécaniques n'est déclarée satisfaite par cette substitution exploratoire.",
            "",
        ]
    )
    resolve_path(outputs["report"]).write_text("\n".join(report_lines), encoding="utf-8")

    required_paths = [resolve_path(value) for key, value in outputs.items() if key != "offline_audit"]
    artifact_rows = []
    for path in [CONFIG_PATH, Path(__file__), *required_paths]:
        artifact_rows.append(
            {
                "path": rel(path),
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256(path) if path.is_file() else None,
            }
        )
    offline = {
        "iteration": "V10Y",
        "created_at": now_local(),
        "decision": "PASS" if all(row["exists"] and row["sha256"] for row in artifact_rows) else "FAIL",
        "artifact_count": len(artifact_rows),
        "artifacts": artifact_rows,
        "offline_audit_self_excluded": True,
        "source_archive_modified": False,
        "protected_master_unchanged": bool(master_check["hash_match"]),
    }
    write_json(resolve_path(outputs["offline_audit"]), offline)

    elapsed = time.perf_counter() - wall_start
    print(
        json.dumps(
            {
                "iteration": "V10Y",
                "decision": decision,
                "runtime_seconds": elapsed,
                "named": [
                    {
                        "scenario_id": row["scenario_id"],
                        "initiation_min": row["initiation_time_min_after_impact"],
                        "initiation_floor": row["initiation_floor"],
                        "outcome": row["outcome_label"],
                        "arrest_story": row["arrest_story"],
                        "collapse_duration_s": row["collapse_duration_s"],
                    }
                    for row in named
                ],
                "grid_outcomes": dict(sorted(outcome_counts.items())),
                "maximum_normalized_energy_residual": maximum_energy_residual,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if elapsed > float(config["execution_policy"]["maximum_runtime_seconds"]):
        raise SystemExit("V10Y exceeded the predeclared runtime limit")
    if not all(criteria.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
