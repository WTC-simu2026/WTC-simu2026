#!/usr/bin/env python3
"""Run and audit the predeclared V8W conditional qualification matrix."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from run_v8v_deformable_projectile import (
    find_column,
    nested_value,
    parse_cycle_record,
    relative_difference,
    run_process,
    sha256,
)


CORE_TITLE = "DEFORMABLE_ENGINE_CORE_EQUIVALENT"
COWLING_TITLE = "DEFORMABLE_COWLING_EQUIVALENT"
FACADE_CONTACT_TITLE = "TH_FACADE_CONTACT"
CORE_TO_COWLING_TITLE = "TH_CORE_TO_COWLING_CONTACT"
COWLING_TO_CORE_TITLE = "TH_COWLING_TO_CORE_CONTACT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace unregistered V8W outputs only")
    return parser.parse_args()


def verify_regressions(config: dict, project_root: Path) -> dict:
    regression = config["regressions"]
    files: dict[str, dict] = {}
    files_passed = True
    for relative_path, expected_hash in regression["required_files"].items():
        path = project_root / relative_path
        actual_hash = sha256(path) if path.exists() else None
        passed = actual_hash == expected_hash
        files_passed = files_passed and passed
        files[relative_path] = {
            "exists": path.exists(),
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "passed": passed,
        }

    tolerance = float(regression["numeric_absolute_tolerance"])
    metrics: list[dict] = []
    metrics_passed = True
    result_cache: dict[str, dict] = {}
    for specification in regression["required_metrics"]:
        relative_results = specification["results"]
        if relative_results not in result_cache:
            result_cache[relative_results] = json.loads(
                (project_root / relative_results).read_text(encoding="utf-8")
            )
        actual = nested_value(result_cache[relative_results], specification["path"])
        expected = specification["expected"]
        if isinstance(expected, bool):
            passed = actual is expected
        else:
            passed = math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance)
        metrics_passed = metrics_passed and passed
        metrics.append({**specification, "actual": actual, "passed": passed})
    return {
        "files": files,
        "metrics": metrics,
        "files_passed": files_passed,
        "metrics_passed": metrics_passed,
        "passed": files_passed and metrics_passed,
    }


def safe_remove_case(case_dir: Path, output_root: Path) -> None:
    resolved_case = case_dir.resolve()
    resolved_root = output_root.resolve()
    if resolved_case == resolved_root or resolved_root not in resolved_case.parents:
        raise RuntimeError(f"Refusing unsafe recursive removal: {resolved_case}")
    shutil.rmtree(resolved_case)


def rupture_summary(engine_stdout: str, metadata: dict) -> dict:
    matches = re.findall(
        r"RUPTURE OF SHELL ELEMENT\s*:\s*(\d+)\s+AT TIME\s*:\s*([0-9.Ee+\-]+)",
        engine_stdout,
    )
    unique_ids = {int(item[0]) for item in matches}
    by_part: dict[str, dict] = {}
    for part_id, bounds in metadata["element_ranges"].items():
        part_ids = {
            element_id
            for element_id in unique_ids
            if bounds["first"] <= element_id <= bounds["last"]
        }
        by_part[part_id] = {
            "unique_element_count": len(part_ids),
            "fraction_of_initial_part_shells": len(part_ids) / max(bounds["count"], 1),
        }
    return {
        "event_count": len(matches),
        "unique_element_count": len(unique_ids),
        "first_time_ms": min((float(item[1]) for item in matches), default=None),
        "last_time_ms": max((float(item[1]) for item in matches), default=None),
        "by_part": by_part,
        "projectile_unique_element_count": sum(
            by_part.get(part_id, {}).get("unique_element_count", 0) for part_id in ("3", "4")
        ),
        "facade_unique_element_count": sum(
            by_part.get(part_id, {}).get("unique_element_count", 0) for part_id in ("1", "2")
        ),
    }


def read_time_history(csv_path: Path, projectile: dict, phase: str) -> dict:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) < 2:
        raise RuntimeError(f"Time history too short: {csv_path}")
    first, last = rows[0], rows[-1]
    part_columns: dict[str, dict[str, str]] = {}
    for part_key, title in (("core", CORE_TITLE), ("cowling", COWLING_TITLE)):
        part_columns[part_key] = {
            variable: find_column(first, title, variable)
            for variable in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")
        }

    def contact_history(prefix: str) -> dict:
        column = find_column(first, prefix)
        values = [float(row[column]) for row in rows]
        active = [index for index, value in enumerate(values) if abs(value) > 0.0]
        return {
            "column": column,
            "channel_interpretation": "cumulative FNZ impulse; end-minus-start",
            "start_time_ms": float(rows[min(active)]["time"]) if active else None,
            "end_time_ms": float(rows[max(active)]["time"]) if active else None,
            "signed_impulse_g_mm_per_ms": values[-1] - values[0],
            "absolute_impulse_g_mm_per_ms": abs(values[-1] - values[0]),
            "peak_absolute_channel_g_mm_per_ms": max(abs(value) for value in values),
        }

    core_to_cowling = contact_history(CORE_TO_COWLING_TITLE)
    cowling_to_core = contact_history(COWLING_TO_CORE_TITLE)
    facade_contact = contact_history(FACADE_CONTACT_TITLE) if phase == "facade_impact" else None

    def part_sum(row: dict[str, str], variable: str) -> float:
        return sum(float(row[part_columns[part_key][variable]]) for part_key in ("core", "cowling"))

    initial_projectile_momentum = part_sum(first, "ZMOM")
    final_projectile_momentum = part_sum(last, "ZMOM")
    projectile_momentum_change = final_projectile_momentum - initial_projectile_momentum
    initial_projectile_mass = part_sum(first, "MASS")
    final_projectile_mass = part_sum(last, "MASS")
    target_mass = float(projectile["total_target_mass_g"])
    initial_total_energy = (
        float(first["INTERNAL ENERGY"])
        + float(first["KINETIC ENERGY"])
        + float(first["ROTATION ENERGY"])
    )
    final_total_energy = (
        float(last["INTERNAL ENERGY"])
        + float(last["KINETIC ENERGY"])
        + float(last["ROTATION ENERGY"])
    )
    external_work = float(last["EXTERNAL WORK"])
    energy_error = 100.0 * (final_total_energy - initial_total_energy - external_work) / max(
        abs(initial_total_energy), 1.0e-30
    )
    elastic_contact_values = [float(row["ELASTIC CONTACT ENERGY"]) for row in rows]
    if facade_contact and facade_contact["start_time_ms"] is not None:
        pre_facade_values = [
            value
            for row, value in zip(rows, elastic_contact_values)
            if float(row["time"]) < float(facade_contact["start_time_ms"])
        ]
    else:
        pre_facade_values = elastic_contact_values
    facade_impulse = facade_contact["absolute_impulse_g_mm_per_ms"] if facade_contact else 0.0
    momentum_balance_error = (
        abs(facade_impulse - abs(projectile_momentum_change))
        / max(abs(projectile_momentum_change), 1.0e-30)
        if phase == "facade_impact"
        else None
    )
    return {
        "row_count": len(rows),
        "time_final_ms": float(last["time"]),
        "facade_contact": facade_contact,
        "core_to_cowling_contact": core_to_cowling,
        "cowling_to_core_contact": cowling_to_core,
        "initial_projectile_z_momentum_g_mm_per_ms": initial_projectile_momentum,
        "final_projectile_z_momentum_g_mm_per_ms": final_projectile_momentum,
        "projectile_z_momentum_change_g_mm_per_ms": projectile_momentum_change,
        "projectile_z_momentum_change_relative_fraction": abs(projectile_momentum_change)
        / max(abs(initial_projectile_momentum), 1.0e-30),
        "facade_contact_impulse_to_projectile_momentum_change_relative_error": momentum_balance_error,
        "initial_projectile_mass_g": initial_projectile_mass,
        "final_projectile_mass_g": final_projectile_mass,
        "projectile_initial_mass_relative_error": abs(initial_projectile_mass - target_mass) / target_mass,
        "projectile_mass_change_relative_fraction": abs(final_projectile_mass - initial_projectile_mass)
        / max(abs(initial_projectile_mass), 1.0e-30),
        "projectile_remaining_mass_fraction": final_projectile_mass / initial_projectile_mass,
        "projectile_eroded_element_count": int(round(part_sum(last, "ERODED"))),
        "core": {
            variable.lower(): float(last[part_columns["core"][variable]])
            for variable in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")
        },
        "cowling": {
            variable.lower(): float(last[part_columns["cowling"][variable]])
            for variable in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")
        },
        "projectile_final_mass_weighted_velocity_z_mm_per_ms": final_projectile_momentum
        / max(final_projectile_mass, 1.0e-30),
        "initial_total_energy_solver": initial_total_energy,
        "final_internal_energy_solver": float(last["INTERNAL ENERGY"]),
        "final_kinetic_energy_solver": float(last["KINETIC ENERGY"]),
        "final_rotational_energy_solver": float(last["ROTATION ENERGY"]),
        "final_total_energy_solver": final_total_energy,
        "external_work_solver": external_work,
        "derived_energy_error_percent": energy_error,
        "initial_elastic_contact_energy_solver": elastic_contact_values[0],
        "final_elastic_contact_energy_solver": elastic_contact_values[-1],
        "maximum_absolute_elastic_contact_energy_solver": max(
            abs(value) for value in elastic_contact_values
        ),
        "maximum_absolute_elastic_contact_energy_to_initial_energy_fraction": max(
            abs(value) for value in elastic_contact_values
        )
        / max(abs(initial_total_energy), 1.0e-30),
        "maximum_pre_facade_elastic_contact_energy_solver": max(
            (abs(value) for value in pre_facade_values), default=0.0
        ),
        "hourglass_energy_solver": float(last["HOURGLASS ENERGY"]),
        "hourglass_to_initial_energy_fraction": abs(float(last["HOURGLASS ENERGY"]))
        / max(abs(initial_total_energy), 1.0e-30),
        "added_mass_g": float(last["ADDED MASS"]),
        "percentage_added_mass": float(last["PERCENTAGE ADDED MASS"]),
        "added_mass_fraction": float(last["PERCENTAGE ADDED MASS"]) / 100.0,
    }


def run_case(
    case: dict,
    config: dict,
    project_root: Path,
    generator: Path,
    output_root: Path,
    starter: Path,
    engine: Path,
    converter: Path,
    environment: dict[str, str],
    force: bool,
) -> dict:
    case_dir = output_root / case["id"]
    if case_dir.exists():
        if not force:
            raise RuntimeError(f"Existing unregistered V8W case requires --force: {case_dir}")
        safe_remove_case(case_dir, output_root)
    case_dir.mkdir(parents=True)
    config_path = project_root / "wtc1_simulation_v8/data/v8w_projectile_freeflight_pairwise_contact.json"
    generation = run_process(
        Path(os.sys.executable),
        [
            str(generator),
            "--config",
            str(config_path),
            "--case-id",
            case["id"],
            "--output",
            str(case_dir),
        ],
        project_root,
        environment,
        case_dir / "generation.log",
    )
    if generation["exit_code"] != 0:
        raise RuntimeError(f"Generator failed for {case['id']}")
    metadata = json.loads((case_dir / "generation_metadata.json").read_text(encoding="utf-8"))
    run_name = metadata["run_name"]
    case_environment = environment.copy()
    case_environment["OMP_NUM_THREADS"] = str(case["threads"])
    starter_run = run_process(
        starter,
        ["-i", f"{run_name}_0000.rad", "-np", "1"],
        case_dir,
        case_environment,
        case_dir / "starter.log",
    )
    if starter_run["exit_code"] != 0:
        raise RuntimeError(f"Starter failed for {case['id']}")
    engine_run = run_process(
        engine,
        ["-i", f"{run_name}_0001.rad"],
        case_dir,
        case_environment,
        case_dir / "engine.log",
    )
    if engine_run["exit_code"] != 0:
        raise RuntimeError(f"Engine failed for {case['id']}")
    converter_run = run_process(
        converter,
        [f"{run_name}T01"],
        case_dir,
        case_environment,
        case_dir / "converter.log",
    )
    if converter_run["exit_code"] != 0:
        raise RuntimeError(f"Time-history conversion failed for {case['id']}")
    engine_output = case_dir / f"{run_name}_0001.out"
    engine_output_text = engine_output.read_text(encoding="utf-8", errors="replace")
    initial_penetrations = [
        int(value)
        for value in re.findall(
            r"THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS", starter_run["stdout"]
        )
    ]
    result = {
        **case,
        **metadata,
        "starter": {
            "exit_code": starter_run["exit_code"],
            "elapsed_seconds": starter_run["elapsed_seconds"],
            "warning_count": starter_run["stdout"].count("WARNING ID"),
            "initial_penetration_warning_count": len(initial_penetrations),
            "initial_penetrating_node_count": sum(initial_penetrations),
        },
        "engine": {
            "exit_code": engine_run["exit_code"],
            "elapsed_seconds": engine_run["elapsed_seconds"],
            "normal_termination": "NORMAL TERMINATION" in engine_output_text,
            "last_printed_cycle": parse_cycle_record(engine_output_text),
        },
        "time_history": read_time_history(
            case_dir / f"{run_name}T01.csv", config["projectile"], case["phase"]
        ),
        "rupture": rupture_summary(engine_run["stdout"], metadata),
        "artifacts": {
            "starter": str((case_dir / f"{run_name}_0000.rad").relative_to(project_root)).replace("\\", "/"),
            "engine": str((case_dir / f"{run_name}_0001.rad").relative_to(project_root)).replace("\\", "/"),
            "time_history_csv": str((case_dir / f"{run_name}T01.csv").relative_to(project_root)).replace("\\", "/"),
            "engine_output": str(engine_output.relative_to(project_root)).replace("\\", "/"),
        },
    }
    print(
        json.dumps(
            {
                "event": "case_completed",
                "case": case["id"],
                "phase": case["phase"],
                "normal_termination": result["engine"]["normal_termination"],
                "elapsed_seconds": result["engine"]["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    return result


def basic_checks(cases: list[dict], gates: dict) -> dict:
    return {
        "all_starter_exit_code_zero": all(case["starter"]["exit_code"] == 0 for case in cases),
        "all_engine_exit_code_zero": all(case["engine"]["exit_code"] == 0 for case in cases),
        "all_normal_termination": all(case["engine"]["normal_termination"] for case in cases),
        "initial_penetrations": max(
            case["starter"]["initial_penetrating_node_count"] for case in cases
        )
        <= gates["maximum_initial_penetrating_node_count"],
        "projectile_initial_mass": max(
            case["time_history"]["projectile_initial_mass_relative_error"] for case in cases
        )
        <= gates["maximum_projectile_initial_mass_relative_error"],
        "added_mass": max(case["time_history"]["added_mass_fraction"] for case in cases)
        <= gates["maximum_added_mass_fraction"],
        "hourglass_energy": max(
            case["time_history"]["hourglass_to_initial_energy_fraction"] for case in cases
        )
        <= gates["maximum_hourglass_to_initial_energy_fraction"],
    }


def free_flight_checks(cases: list[dict], gates: dict, regression_passed: bool) -> dict:
    checks = {"regressions_unchanged": regression_passed, **basic_checks(cases, gates)}
    checks.update(
        {
            "energy_error": max(
                abs(case["time_history"]["derived_energy_error_percent"]) for case in cases
            )
            <= gates["free_flight_maximum_absolute_energy_error_percent"],
            "elastic_contact_energy": max(
                case["time_history"][
                    "maximum_absolute_elastic_contact_energy_to_initial_energy_fraction"
                ]
                for case in cases
            )
            <= gates["free_flight_maximum_elastic_contact_energy_to_initial_energy_fraction"],
            "pairwise_contact_impulse": max(
                max(
                    case["time_history"]["core_to_cowling_contact"][
                        "absolute_impulse_g_mm_per_ms"
                    ],
                    case["time_history"]["cowling_to_core_contact"][
                        "absolute_impulse_g_mm_per_ms"
                    ],
                )
                / max(
                    abs(case["time_history"]["initial_projectile_z_momentum_g_mm_per_ms"]),
                    1.0e-30,
                )
                for case in cases
            )
            <= gates["free_flight_maximum_pairwise_contact_impulse_to_initial_momentum_fraction"],
            "z_momentum_conservation": max(
                case["time_history"]["projectile_z_momentum_change_relative_fraction"]
                for case in cases
            )
            <= gates["free_flight_maximum_z_momentum_change_relative_fraction"],
            "mass_conservation": max(
                case["time_history"]["projectile_mass_change_relative_fraction"] for case in cases
            )
            <= gates["free_flight_maximum_mass_change_relative_fraction"],
            "zero_erosion": max(
                case["time_history"]["projectile_eroded_element_count"] for case in cases
            )
            <= gates["free_flight_maximum_eroded_elements"],
        }
    )
    return checks


def impact_checks(cases: list[dict], gates: dict) -> tuple[dict, dict, dict]:
    by_id = {case["id"]: case for case in cases}
    medium = by_id["IM_M050_P050_DT090_T1"]
    fine = by_id["IM_M025_P025_DT090_T1"]
    half_step = by_id["IM_M050_P050_DT045_T1"]
    threaded = by_id["IM_M050_P050_DT090_T4"]
    failure_low = by_id["IM_M050_P050_DT090_FLO_T1"]
    failure_high = by_id["IM_M050_P050_DT090_FHI_T1"]

    def impulse(case: dict) -> float:
        return case["time_history"]["facade_contact"]["absolute_impulse_g_mm_per_ms"]

    def final_momentum(case: dict) -> float:
        return case["time_history"]["final_projectile_z_momentum_g_mm_per_ms"]

    convergence = {
        "medium_to_fine_contact_impulse_relative_difference": relative_difference(
            impulse(medium), impulse(fine)
        ),
        "medium_to_fine_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(medium), final_momentum(fine)
        ),
        "half_time_step_contact_impulse_relative_difference": relative_difference(
            impulse(medium), impulse(half_step)
        ),
        "half_time_step_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(medium), final_momentum(half_step)
        ),
        "thread_repeatability_contact_impulse_relative_difference": relative_difference(
            impulse(medium), impulse(threaded)
        ),
        "thread_repeatability_projectile_final_momentum_relative_difference": relative_difference(
            final_momentum(medium), final_momentum(threaded)
        ),
    }
    failure_ordering = (
        failure_low["time_history"]["projectile_eroded_element_count"]
        >= medium["time_history"]["projectile_eroded_element_count"]
        >= failure_high["time_history"]["projectile_eroded_element_count"]
    )
    checks = basic_checks(cases, gates)
    checks.update(
        {
            "energy_error": max(
                abs(case["time_history"]["derived_energy_error_percent"]) for case in cases
            )
            <= gates["impact_maximum_absolute_energy_error_percent"],
            "baseline_projectile_erosion": medium["time_history"][
                "projectile_eroded_element_count"
            ]
            >= gates["impact_baseline_minimum_projectile_eroded_elements"],
            "baseline_projectile_remaining_mass": medium["time_history"][
                "projectile_remaining_mass_fraction"
            ]
            >= gates["impact_baseline_minimum_projectile_remaining_mass_fraction"],
            "projectile_failure_ordering": failure_ordering
            if gates["impact_projectile_failure_ordering_required"]
            else True,
            "contact_impulse_momentum_balance": max(
                case["time_history"][
                    "facade_contact_impulse_to_projectile_momentum_change_relative_error"
                ]
                for case in cases
            )
            <= gates["impact_maximum_contact_impulse_to_projectile_momentum_change_relative_error"],
            "medium_to_fine_contact_impulse": convergence[
                "medium_to_fine_contact_impulse_relative_difference"
            ]
            <= gates["impact_medium_to_fine_contact_impulse_relative_difference"],
            "medium_to_fine_projectile_final_momentum": convergence[
                "medium_to_fine_projectile_final_momentum_relative_difference"
            ]
            <= gates["impact_medium_to_fine_projectile_final_momentum_relative_difference"],
            "half_time_step_contact_impulse": convergence[
                "half_time_step_contact_impulse_relative_difference"
            ]
            <= gates["impact_half_time_step_contact_impulse_relative_difference"],
            "half_time_step_projectile_final_momentum": convergence[
                "half_time_step_projectile_final_momentum_relative_difference"
            ]
            <= gates["impact_half_time_step_projectile_final_momentum_relative_difference"],
            "thread_repeatability_contact_impulse": convergence[
                "thread_repeatability_contact_impulse_relative_difference"
            ]
            <= gates["impact_thread_repeatability_contact_impulse_relative_difference"],
            "thread_repeatability_projectile_final_momentum": convergence[
                "thread_repeatability_projectile_final_momentum_relative_difference"
            ]
            <= gates["impact_thread_repeatability_projectile_final_momentum_relative_difference"],
        }
    )
    ordering = {
        "low_eroded_elements": failure_low["time_history"]["projectile_eroded_element_count"],
        "baseline_eroded_elements": medium["time_history"]["projectile_eroded_element_count"],
        "high_eroded_elements": failure_high["time_history"]["projectile_eroded_element_count"],
        "passed": failure_ordering,
    }
    return checks, convergence, ordering


def write_checkpoint(path: Path, regression: dict, cases: list[dict], stage: str) -> None:
    path.write_text(
        json.dumps(
            {
                "iteration": "V8W",
                "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
                "stage": stage,
                "regressions_passed": regression["passed"],
                "completed_case_ids": [case["id"] for case in cases],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    args = parse_args()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v8w_projectile_freeflight_pairwise_contact.json"
    generator_path = simulation_root / "scripts" / "generate_v8w_pairwise_contact.py"
    output_root = simulation_root / "openradioss_benchmarks" / "v8w_pairwise_contact"
    summary_path = simulation_root / "output" / "resultats_wtc1_v8w_contact_pairwise.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v8w_contact_pairwise.md"
    checkpoint_path = simulation_root / "output" / "journal_wtc1_v8w_execution.json"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if summary_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing V8W result: {summary_path}")
    if args.force and registry_path.exists() and '"experiment_id":"WTC1-V8W"' in registry_path.read_text(
        encoding="utf-8"
    ):
        raise SystemExit("Refusing to replace registered V8W outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    regression = verify_regressions(config, project_root)
    if not regression["passed"]:
        raise SystemExit("V8U/V8V regression verification failed before V8W execution")
    runtime_root = simulation_root / "openradioss_runtime" / "v20260728-win64"
    starter = runtime_root / "starter_win64.exe"
    engine = runtime_root / "engine_win64.exe"
    converter = runtime_root / "th_to_csv_win64.exe"
    for executable in (starter, engine, converter):
        if not executable.exists():
            raise SystemExit(f"Missing runtime executable: {executable}")

    environment = os.environ.copy()
    environment.update(
        {
            "OPENRADIOSS_PATH": r"C:\OpenRadioss",
            "RAD_CFG_PATH": r"C:\OpenRadioss\hm_cfg_files",
            "RAD_H3D_PATH": r"C:\OpenRadioss\extlib\h3d\lib\win64",
            "KMP_STACKSIZE": "400m",
        }
    )
    output_root.mkdir(parents=True, exist_ok=True)
    simulation_root.joinpath("output").mkdir(parents=True, exist_ok=True)
    case_results: list[dict] = []
    overall_started = time.perf_counter()
    gates = config["predeclared_gates"]
    free_cases = [case for case in config["cases"] if case["phase"] == "free_flight"]
    impact_cases = [case for case in config["cases"] if case["phase"] == "facade_impact"]

    for case in free_cases:
        case_results.append(
            run_case(
                case,
                config,
                project_root,
                generator_path,
                output_root,
                starter,
                engine,
                converter,
                environment,
                args.force,
            )
        )
        write_checkpoint(checkpoint_path, regression, case_results, "free_flight_running")
    free_results = [case for case in case_results if case["phase"] == "free_flight"]
    free_gate_checks = free_flight_checks(free_results, gates, regression["passed"])
    free_passed = all(free_gate_checks.values())
    print(
        json.dumps({"event": "free_flight_gate", "status": "PASS" if free_passed else "FAIL", "checks": free_gate_checks}),
        flush=True,
    )

    facade_matrix_executed = False
    impact_gate_checks: dict[str, bool] = {}
    convergence: dict = {}
    failure_ordering: dict = {}
    if free_passed:
        facade_matrix_executed = True
        for case in impact_cases:
            case_results.append(
                run_case(
                    case,
                    config,
                    project_root,
                    generator_path,
                    output_root,
                    starter,
                    engine,
                    converter,
                    environment,
                    args.force,
                )
            )
            write_checkpoint(checkpoint_path, regression, case_results, "facade_matrix_running")
        impact_results = [case for case in case_results if case["phase"] == "facade_impact"]
        impact_gate_checks, convergence, failure_ordering = impact_checks(impact_results, gates)
    impact_passed = facade_matrix_executed and all(impact_gate_checks.values())
    qualification_passed = free_passed and impact_passed

    results = {
        "iteration": "V8W",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "regressions": regression,
        "cases": case_results,
        "free_flight_gate_checks": free_gate_checks,
        "projectile_free_flight_qualification_passed": free_passed,
        "facade_matrix_executed": facade_matrix_executed,
        "impact_gate_checks": impact_gate_checks,
        "convergence": convergence,
        "projectile_failure_ordering": failure_ordering,
        "deformable_subassembly_qualification_passed": qualification_passed,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "runtime": {
            "total_elapsed_seconds": time.perf_counter() - overall_started,
            "starter_sha256": sha256(starter),
            "engine_sha256": sha256(engine),
            "converter_sha256": sha256(converter),
            "config_sha256": sha256(config_path),
            "generator_sha256": sha256(generator_path),
            "runner_sha256": sha256(Path(__file__)),
            "source_installation_modified": False,
            "system32_modified": False,
            "source_archive_rescanned": False,
        },
        "plot": {
            "path": None,
            "reason": "No visualization is used as a physical validation; solver histories and decks are preserved."
        },
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    write_checkpoint(checkpoint_path, regression, case_results, "complete")

    free_rows = []
    for case in free_results:
        th = case["time_history"]
        free_rows.append(
            f"| {case['id']} | {case['projectile_mesh_target_mm']:.0f} | "
            f"{th['maximum_absolute_elastic_contact_energy_solver']:.6g} | "
            f"{th['projectile_z_momentum_change_relative_fraction']:.3e} | "
            f"{th['projectile_eroded_element_count']} | {th['derived_energy_error_percent']:.6f} |"
        )
    impact_results = [case for case in case_results if case["phase"] == "facade_impact"]
    impact_rows = []
    for case in impact_results:
        th = case["time_history"]
        impact_rows.append(
            f"| {case['id']} | {case['facade_mesh_target_mm']:.0f} | {case['projectile_mesh_target_mm']:.0f} | "
            f"{th['facade_contact']['absolute_impulse_g_mm_per_ms'] / 1.0e6:.3f} | "
            f"{th['projectile_eroded_element_count']} | {th['projectile_remaining_mass_fraction']:.3%} | "
            f"{th['derived_energy_error_percent']:.3f} |"
        )
    free_failed = [name for name, passed in free_gate_checks.items() if not passed]
    impact_failed = [name for name, passed in impact_gate_checks.items() if not passed]
    report = f"""# WTC 1 — V8W : vol libre et contacts pairwise du projectile déformable

## Résultat

Le contrôle en vol libre est **{'PASS' if free_passed else 'FAIL'}**. La matrice d'impact façade a été **{'exécutée' if facade_matrix_executed else 'bloquée conformément au protocole'}** et son portail est **{'PASS' if impact_passed else 'FAIL'}**. Le portail V8W complet est donc **{'PASS' if qualification_passed else 'FAIL'}**.

Échecs du vol libre : {', '.join(free_failed) if free_failed else 'aucun'}. Échecs de l'impact : {', '.join(impact_failed) if impact_failed else ('aucun' if facade_matrix_executed else 'non évalué')}.

Ce verdict porte seulement sur le projectile équivalent à deux coques et sur la petite façade V8V. Il ne valide ni un JT9D réel, ni l'avion complet, ni l'impact global du WTC 1, ni l'incendie ou l'effondrement, ni Blender comme validation physique, ni une hypothèse de démolition.

## 1. Faits directement documentés

- La documentation officielle Radioss définit TYPE7 comme un contact entre une surface principale et un groupe de nœuds secondaires. Un nœud n'est exclu que du segment auquel il est directement connecté ; TYPE7 ne traite pas le contact arête-arête.
- Avec `Igap=2`, le jeu variable des deux coques est calculé à partir de leurs demi-épaisseurs lorsque cette somme dépasse le jeu minimal.
- V8U et V8V sont restés inchangés selon les empreintes et métriques gelées : **{'PASS' if regression['passed'] else 'FAIL'}**.
- Aucune archive source n'a été rescannée ou modifiée.

## 2. Résultats d'un modèle officiel

- Aucun nouveau résultat NIST n'est utilisé comme cible de V8W. Les données de façade, masse et vitesse restent celles déjà gelées dans V8V ; elles ne constituent pas une validation indépendante de l'impact réel.

## 3. Hypothèses propres au modèle

- Le noyau et le capotage carrés restent des équivalents de masse, pas une géométrie JT9D.
- L'auto-contact V8V entre tous les nœuds et toutes les coques du projectile est supprimé. Il est remplacé par deux contacts directionnels : noyau vers capotage, puis capotage vers noyau.
- L'ouverture frontale du capotage passe de 1 000 à 1 200 mm. Le jeu radial de surfaces moyennes est de 150 mm ; après les demi-épaisseurs équivalentes, la marge initiale calculée est d'environ {free_results[0]['projectile']['front_opening_net_shell_surface_clearance_mm']:.3f} mm, soit {free_results[0]['projectile']['net_clearance_to_activation_gap_ratio']:.3f} fois le jeu d'activation TYPE7.
- Les matériaux, ruptures, façade tronquée et absence de contact arête-arête restent des hypothèses ou limites V8V.

## 4. Résultats dérivés — vol libre

| Cas | Maille projectile (mm) | Énergie de contact max. | Variation relative qdm Z | Éléments érodés | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|
{chr(10).join(free_rows)}

Le vol libre exigeait simultanément : aucune croissance d'énergie de contact, aucune érosion, conservation de la quantité de mouvement et de la masse, aucune masse ajoutée et une erreur d'énergie inférieure à 0,1 % aux trois maillages.

## 5. Résultats dérivés — impact sur la façade simplifiée

| Cas | Maille façade (mm) | Maille projectile (mm) | Impulsion façade (kN·s) | Éléments projectile érodés | Masse projectile restante | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(impact_rows) if impact_rows else '| Non exécuté | — | — | — | — | — | — |'}

Écart d'impulsion moyen-fin : **{convergence.get('medium_to_fine_contact_impulse_relative_difference', float('nan')):.3%}** (seuil inchangé 10 %). Répétabilité 1/4 fils : **{convergence.get('thread_repeatability_contact_impulse_relative_difference', float('nan')):.3%}**. Ordre de rupture basse / nominale / haute : **{failure_ordering.get('low_eroded_elements', '—')} / {failure_ordering.get('baseline_eroded_elements', '—')} / {failure_ordering.get('high_eroded_elements', '—')}**.

## 6. Contradictions, inconnues et décision

- Le bordereau exact du panneau 124, la géométrie et les liaisons JT9D, le contact arête-arête, les ailes, le carburant et le fuselage restent inconnus ou non qualifiés.
- Une terminaison normale du solveur signifie seulement que le calcul s'est achevé ; elle ne prouve pas que le modèle physique réel est correct.
- Le portail global WTC 1, le couplage thermique et la dynamique Blender restent fermés, même si V8W passe.

La prochaine itération doit traiter seulement les portails V8W encore en échec. Une simulation globale n'est autorisée que lorsque l'énergie, la masse, la quantité de mouvement, la répétabilité, la rupture et la convergence d'impulsion passent ensemble.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": "PASS" if qualification_passed else "FAIL",
                "free_flight": "PASS" if free_passed else "FAIL",
                "facade_impact": "PASS" if impact_passed else "FAIL",
                "results": str(summary_path),
                "report": str(report_path),
                "runtime_seconds": results["runtime"]["total_elapsed_seconds"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
