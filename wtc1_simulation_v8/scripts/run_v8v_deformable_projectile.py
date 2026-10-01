#!/usr/bin/env python3
"""Run and audit the predeclared V8V deformable-contact matrix."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


CORE_TITLE = "DEFORMABLE_ENGINE_CORE_EQUIVALENT"
COWLING_TITLE = "DEFORMABLE_COWLING_EQUIVALENT"
CONTACT_TITLE = "TH_FACADE_CONTACT"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace an unregistered V8V output matrix")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_process(executable: Path, arguments: list[str], cwd: Path, environment: dict[str, str], log: Path) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(
        [str(executable), *arguments],
        cwd=str(cwd),
        env=environment,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    elapsed = time.perf_counter() - started
    log.write_text(completed.stdout, encoding="utf-8", newline="\n")
    return {"exit_code": completed.returncode, "elapsed_seconds": elapsed, "stdout": completed.stdout}


def relative_difference(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1.0e-30)


def nested_value(data: dict, dotted_path: str):
    current = data
    for component in dotted_path.split("."):
        current = current[component]
    return current


def verify_v8u_regression(config: dict, project_root: Path) -> dict:
    regression = config["v8u_regression"]
    files: dict[str, dict] = {}
    hashes_passed = True
    for relative_path, expected_hash in regression["required_files"].items():
        path = project_root / relative_path
        actual_hash = sha256(path) if path.exists() else None
        passed = actual_hash == expected_hash
        hashes_passed = hashes_passed and passed
        files[relative_path] = {
            "exists": path.exists(),
            "expected_sha256": expected_hash,
            "actual_sha256": actual_hash,
            "passed": passed,
        }
    result_path = project_root / "wtc1_simulation_v8/output/resultats_wtc1_v8u_impact_openradioss.json"
    prior_results = json.loads(result_path.read_text(encoding="utf-8"))
    tolerance = float(regression["numeric_absolute_tolerance"])
    metrics: dict[str, dict] = {}
    metrics_passed = True
    for dotted_path, expected in regression["required_metrics"].items():
        actual = nested_value(prior_results, dotted_path)
        if isinstance(expected, bool):
            passed = actual is expected
        else:
            passed = math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance)
        metrics_passed = metrics_passed and passed
        metrics[dotted_path] = {"expected": expected, "actual": actual, "passed": passed}
    return {
        "files": files,
        "metrics": metrics,
        "hashes_passed": hashes_passed,
        "metrics_passed": metrics_passed,
        "passed": hashes_passed and metrics_passed,
    }


def parse_cycle_record(output_text: str) -> dict | None:
    records: list[dict] = []
    for line in output_text.splitlines():
        tokens = line.strip().split()
        if len(tokens) < 13 or not tokens[0].isdigit() or not tokens[5].endswith("%"):
            continue
        try:
            records.append(
                {
                    "line": line.rstrip(),
                    "cycle": int(tokens[0]),
                    "time_ms": float(tokens[1]),
                    "time_step_ms": float(tokens[2]),
                    "element_type": tokens[3],
                    "element_id": int(tokens[4]),
                    "energy_error_percent": float(tokens[5][:-1]),
                    "internal_energy_solver": float(tokens[6]),
                    "translational_kinetic_energy_solver": float(tokens[7]),
                    "rotational_kinetic_energy_solver": float(tokens[8]),
                    "external_work_solver": float(tokens[9]),
                    "mass_error": float(tokens[10]),
                    "total_mass_g": float(tokens[11]),
                    "added_mass_g": float(tokens[12]),
                }
            )
        except ValueError:
            continue
    return records[-1] if records else None


def find_column(row: dict[str, str], prefix: str, variable: str | None = None) -> str:
    matches = [name for name in row if name.startswith(prefix) and (variable is None or name.rstrip().endswith(variable))]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one column for prefix={prefix!r}, variable={variable!r}; got {matches}")
    return matches[0]


def read_time_history(csv_path: Path, projectile: dict) -> dict:
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
    contact_column = find_column(first, CONTACT_TITLE)
    times = [float(row["time"]) for row in rows]
    contact_forces = [float(row[contact_column]) for row in rows]
    # In the converted OpenRadioss T01 output used by this project, the FNZ
    # interface channel is cumulative: its end-minus-start change balances the
    # independently reported projectile Z-momentum change.  Do not integrate
    # the already accumulated channel a second time.
    contact_impulse_signed = contact_forces[-1] - contact_forces[0]
    contact_impulse = abs(contact_impulse_signed)

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
    active_indices = [index for index, value in enumerate(contact_forces) if abs(value) > 0.0]
    return {
        "row_count": len(rows),
        "time_final_ms": times[-1],
        "contact_force_channel": contact_column,
        "contact_fnz_channel_peak_absolute_g_mm_per_ms": max(abs(value) for value in contact_forces),
        "contact_fnz_channel_interpretation": "cumulative impulse; end-minus-start, cross-checked against projectile Z-momentum change",
        "contact_start_time_ms": times[min(active_indices)] if active_indices else None,
        "contact_end_time_ms": times[max(active_indices)] if active_indices else None,
        "contact_impulse_signed_g_mm_per_ms": contact_impulse_signed,
        "contact_impulse_absolute_g_mm_per_ms": contact_impulse,
        "initial_projectile_z_momentum_g_mm_per_ms": initial_projectile_momentum,
        "final_projectile_z_momentum_g_mm_per_ms": final_projectile_momentum,
        "projectile_z_momentum_change_g_mm_per_ms": projectile_momentum_change,
        "contact_impulse_to_projectile_momentum_change_relative_error": abs(
            contact_impulse - abs(projectile_momentum_change)
        )
        / max(abs(projectile_momentum_change), 1.0e-30),
        "initial_projectile_mass_g": initial_projectile_mass,
        "final_projectile_mass_g": final_projectile_mass,
        "projectile_initial_mass_relative_error": abs(initial_projectile_mass - target_mass) / target_mass,
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
        "hourglass_energy_solver": float(last["HOURGLASS ENERGY"]),
        "hourglass_to_initial_energy_fraction": abs(float(last["HOURGLASS ENERGY"]))
        / max(abs(initial_total_energy), 1.0e-30),
        "added_mass_g": float(last["ADDED MASS"]),
        "percentage_added_mass": float(last["PERCENTAGE ADDED MASS"]),
        "added_mass_fraction": float(last["PERCENTAGE ADDED MASS"]) / 100.0,
    }


def rupture_summary(engine_stdout: str, metadata: dict) -> dict:
    matches = re.findall(r"RUPTURE OF SHELL ELEMENT\s*:\s*(\d+)\s+AT TIME\s*:\s*([0-9.Ee+\-]+)", engine_stdout)
    unique_ids = {int(item[0]) for item in matches}
    by_part: dict[str, dict] = {}
    for part_id, bounds in metadata["element_ranges"].items():
        part_ids = {element_id for element_id in unique_ids if bounds["first"] <= element_id <= bounds["last"]}
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
        "projectile_unique_element_count": by_part["3"]["unique_element_count"]
        + by_part["4"]["unique_element_count"],
        "facade_unique_element_count": by_part["1"]["unique_element_count"]
        + by_part["2"]["unique_element_count"],
    }


def safe_remove_case(case_dir: Path, output_root: Path) -> None:
    resolved_case = case_dir.resolve()
    resolved_root = output_root.resolve()
    if resolved_case == resolved_root or resolved_root not in resolved_case.parents:
        raise RuntimeError(f"Refusing unsafe recursive removal: {resolved_case}")
    shutil.rmtree(resolved_case)


def main() -> None:
    args = parse_args()
    simulation_root = Path(__file__).resolve().parents[1]
    project_root = simulation_root.parent
    config_path = simulation_root / "data" / "v8v_openradioss_deformable_projectile.json"
    generator_path = simulation_root / "scripts" / "generate_v8v_deformable_projectile.py"
    output_root = simulation_root / "openradioss_benchmarks" / "v8v_deformable_projectile"
    summary_path = simulation_root / "output" / "resultats_wtc1_v8v_projectile_deformable.json"
    report_path = simulation_root / "output" / "rapport_wtc1_v8v_projectile_deformable.md"
    registry_path = project_root / "harness" / "experiments" / "registry.jsonl"
    if summary_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing V8V result: {summary_path}")
    if args.force and registry_path.exists() and '"experiment_id":"WTC1-V8V"' in registry_path.read_text(encoding="utf-8"):
        raise SystemExit("Refusing to replace registered V8V outputs")

    config = json.loads(config_path.read_text(encoding="utf-8"))
    regression = verify_v8u_regression(config, project_root)
    runtime_root = simulation_root / "openradioss_runtime" / "v20260728-win64"
    starter = runtime_root / "starter_win64.exe"
    engine = runtime_root / "engine_win64.exe"
    converter = runtime_root / "th_to_csv_win64.exe"
    if not converter.exists():
        shutil.copy2(Path(r"C:\OpenRadioss\exec\th_to_csv_win64.exe"), converter)
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

    for case in config["cases"]:
        case_dir = output_root / case["id"]
        if case_dir.exists() and args.force:
            safe_remove_case(case_dir, output_root)
        case_dir.mkdir(parents=True, exist_ok=True)
        generation = run_process(
            Path(os.sys.executable),
            [
                str(generator_path),
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
            for value in re.findall(r"THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS", starter_run["stdout"])
        ]
        time_history = read_time_history(case_dir / f"{run_name}T01.csv", config["projectile"])
        case_results.append(
            {
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
                "time_history": time_history,
                "rupture": rupture_summary(engine_run["stdout"], metadata),
                "artifacts": {
                    "starter": str((case_dir / f"{run_name}_0000.rad").relative_to(project_root)).replace("\\", "/"),
                    "engine": str((case_dir / f"{run_name}_0001.rad").relative_to(project_root)).replace("\\", "/"),
                    "time_history_csv": str((case_dir / f"{run_name}T01.csv").relative_to(project_root)).replace("\\", "/"),
                    "engine_output": str(engine_output.relative_to(project_root)).replace("\\", "/"),
                },
            }
        )

    by_id = {case["id"]: case for case in case_results}
    medium = by_id["M050_P050_DT090_T1"]
    fine = by_id["M025_P025_DT090_T1"]
    half_step = by_id["M050_P050_DT045_T1"]
    threaded = by_id["M050_P050_DT090_T4"]
    failure_low = by_id["M050_P050_DT090_FLO_T1"]
    failure_high = by_id["M050_P050_DT090_FHI_T1"]
    convergence = {
        "medium_to_fine_contact_impulse_relative_difference": relative_difference(
            medium["time_history"]["contact_impulse_absolute_g_mm_per_ms"],
            fine["time_history"]["contact_impulse_absolute_g_mm_per_ms"],
        ),
        "medium_to_fine_projectile_final_momentum_relative_difference": relative_difference(
            medium["time_history"]["final_projectile_z_momentum_g_mm_per_ms"],
            fine["time_history"]["final_projectile_z_momentum_g_mm_per_ms"],
        ),
        "half_time_step_contact_impulse_relative_difference": relative_difference(
            medium["time_history"]["contact_impulse_absolute_g_mm_per_ms"],
            half_step["time_history"]["contact_impulse_absolute_g_mm_per_ms"],
        ),
        "half_time_step_projectile_final_momentum_relative_difference": relative_difference(
            medium["time_history"]["final_projectile_z_momentum_g_mm_per_ms"],
            half_step["time_history"]["final_projectile_z_momentum_g_mm_per_ms"],
        ),
        "thread_repeatability_contact_impulse_relative_difference": relative_difference(
            medium["time_history"]["contact_impulse_absolute_g_mm_per_ms"],
            threaded["time_history"]["contact_impulse_absolute_g_mm_per_ms"],
        ),
        "thread_repeatability_projectile_final_momentum_relative_difference": relative_difference(
            medium["time_history"]["final_projectile_z_momentum_g_mm_per_ms"],
            threaded["time_history"]["final_projectile_z_momentum_g_mm_per_ms"],
        ),
    }
    failure_ordering = (
        failure_low["time_history"]["projectile_eroded_element_count"]
        >= medium["time_history"]["projectile_eroded_element_count"]
        >= failure_high["time_history"]["projectile_eroded_element_count"]
    )
    gates = config["predeclared_gates"]
    gate_checks = {
        "v8u_regression_hashes_and_metrics_unchanged": regression["passed"],
        "all_starter_exit_code_zero": all(case["starter"]["exit_code"] == 0 for case in case_results),
        "all_engine_exit_code_zero": all(case["engine"]["exit_code"] == 0 for case in case_results),
        "all_normal_termination": all(case["engine"]["normal_termination"] for case in case_results),
        "initial_penetrations": max(case["starter"]["initial_penetrating_node_count"] for case in case_results)
        <= gates["maximum_initial_penetration_warning_count"],
        "energy_error": max(abs(case["time_history"]["derived_energy_error_percent"]) for case in case_results)
        <= gates["maximum_absolute_energy_error_percent"],
        "added_mass": max(case["time_history"]["added_mass_fraction"] for case in case_results)
        <= gates["maximum_added_mass_fraction"],
        "hourglass_energy": max(case["time_history"]["hourglass_to_initial_energy_fraction"] for case in case_results)
        <= gates["maximum_hourglass_to_initial_energy_fraction"],
        "projectile_initial_mass": max(
            case["time_history"]["projectile_initial_mass_relative_error"] for case in case_results
        )
        <= gates["maximum_projectile_initial_mass_relative_error"],
        "baseline_projectile_erosion": medium["time_history"]["projectile_eroded_element_count"]
        >= gates["baseline_minimum_projectile_eroded_elements"],
        "baseline_projectile_remaining_mass": medium["time_history"]["projectile_remaining_mass_fraction"]
        >= gates["baseline_minimum_projectile_remaining_mass_fraction"],
        "projectile_failure_ordering": failure_ordering if gates["projectile_failure_ordering_required"] else True,
        "contact_impulse_momentum_balance": max(
            case["time_history"]["contact_impulse_to_projectile_momentum_change_relative_error"]
            for case in case_results
        )
        <= gates["maximum_contact_impulse_to_projectile_momentum_change_relative_error"],
        "medium_to_fine_contact_impulse": convergence["medium_to_fine_contact_impulse_relative_difference"]
        <= gates["medium_to_fine_contact_impulse_relative_difference"],
        "medium_to_fine_projectile_final_momentum": convergence[
            "medium_to_fine_projectile_final_momentum_relative_difference"
        ]
        <= gates["medium_to_fine_projectile_final_momentum_relative_difference"],
        "half_time_step_contact_impulse": convergence["half_time_step_contact_impulse_relative_difference"]
        <= gates["half_time_step_contact_impulse_relative_difference"],
        "half_time_step_projectile_final_momentum": convergence[
            "half_time_step_projectile_final_momentum_relative_difference"
        ]
        <= gates["half_time_step_projectile_final_momentum_relative_difference"],
        "thread_repeatability_contact_impulse": convergence[
            "thread_repeatability_contact_impulse_relative_difference"
        ]
        <= gates["thread_repeatability_contact_impulse_relative_difference"],
        "thread_repeatability_projectile_final_momentum": convergence[
            "thread_repeatability_projectile_final_momentum_relative_difference"
        ]
        <= gates["thread_repeatability_projectile_final_momentum_relative_difference"],
    }
    qualification_passed = all(gate_checks.values())
    results = {
        "iteration": "V8V",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "configuration": str(config_path.relative_to(project_root)).replace("\\", "/"),
        "scope": config["dataset"]["scope"],
        "v8u_regression": regression,
        "cases": case_results,
        "convergence": convergence,
        "projectile_failure_ordering": {
            "low_eroded_elements": failure_low["time_history"]["projectile_eroded_element_count"],
            "baseline_eroded_elements": medium["time_history"]["projectile_eroded_element_count"],
            "high_eroded_elements": failure_high["time_history"]["projectile_eroded_element_count"],
            "passed": failure_ordering,
        },
        "gate_checks": gate_checks,
        "deformable_subassembly_qualification_passed": qualification_passed,
        "global_wtc_impact_physics_qualification_passed": False,
        "blender_physics_validation_passed": False,
        "comparison_to_official_model": {
            "nist_engine_component_speed_loss_range_mph": [56.0, 74.0],
            "classification": "official_model_result",
            "comparability": "diagnostic context only; V8V uses square equivalent-mass shell parts, a simplified three-story facade panel, normal impact and hypothetical projectile constitutive laws",
        },
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
        },
        "plot": {"path": None, "reason": "No plot is required for the qualification verdict; solver histories and case decks are preserved."},
    }
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    table_rows = []
    for case in case_results:
        th = case["time_history"]
        table_rows.append(
            f"| {case['id']} | {case['facade_mesh_target_mm']:.0f} | {case['projectile_mesh_target_mm']:.0f} | "
            f"{case['time_step_scale']:.2f} | {case['threads']} | {th['contact_impulse_absolute_g_mm_per_ms'] / 1.0e6:.3f} | "
            f"{th['contact_impulse_to_projectile_momentum_change_relative_error']:.3%} | "
            f"{th['projectile_eroded_element_count']} | {th['projectile_remaining_mass_fraction']:.3%} | "
            f"{th['derived_energy_error_percent']:.3f} |"
        )
    failed = [name for name, passed in gate_checks.items() if not passed]
    gate_text = "PASS" if qualification_passed else "FAIL: " + ", ".join(failed)
    report = f"""# WTC 1 — V8V : projectile moteur/capotage minimal déformable

## Résultat

La matrice V8V s'est exécutée sans modifier les archives sources, `C:\\OpenRadioss`, `System32` ni les artefacts V8U. Le contrôle de régression V8U par empreintes et métriques est **{'PASS' if regression['passed'] else 'FAIL'}**. Le portail V8V pré-déclaré est **{gate_text}**.

Ce verdict concerne uniquement un projectile équivalent à deux parties déformables, deux interfaces `/INTER/TYPE7` et un panneau de façade simplifié de trois colonnes par trois étages. Il ne valide ni un JT9D réel, ni l'impact global du vol AA11, ni l'incendie, l'initiation ou la propagation de l'effondrement, ni Blender comme solveur physique, ni une hypothèse d'explosif ou de thermite.

## 1. Faits directement documentés

- NIST décrit les panneaux préfabriqués de façade comme des assemblages de trois colonnes par trois étages, avec colonnes caisson nominales de 14 pouces, entraxe de 40 pouces et allèges de 52 pouces.
- Un acier périphérique spécifié à 60 ksi et une plaque voisine de 5/16 pouce sont documentés près des étages 97–100. Ces données voisines ne constituent pas le bordereau exact du panneau 124 au niveau 96.
- Le registre V8S attribue 20 100 lb aux deux moteurs avec capotages ; V8V conserve exactement la moitié comme masse cible du projectile équivalent.
- La documentation officielle Radioss définit TYPE7 comme un contact nœud-segment déformable et expose, par `/TH/INTER` et `/TH/PART`, les forces de contact, quantités de mouvement, masses, énergies et éléments érodés utilisés ici.

## 2. Résultats d'un modèle officiel utilisés seulement comme contexte

- Les pertes de vitesse de moteur de 56 à 74 mph proviennent de sous-modèles NIST. Elles ne sont pas des observations directes et ne sont pas un portail V8V, car la géométrie et les lois du projectile V8V ne sont pas celles du modèle NIST.

## 3. Hypothèses propres à V8V

- Le noyau moteur est une boîte fermée en coques d'acier équivalent ; le capotage est une boîte ouverte à l'arrière en coques d'aluminium équivalent. Ce ne sont pas des géométries JT9D.
- Les épaisseurs uniformes du projectile sont recalées sur 3 600,0 kg pour le noyau et 958,603 kg pour le capotage. Elles représentent une masse équivalente, pas des épaisseurs réelles.
- Les résistances, déformations de rupture et liaisons du projectile sont des hypothèses de qualification. Le contact est sans frottement et le contact arête-arête TYPE11 n'est pas inclus.
- La façade étendue correspond à l'échelle trois colonnes par trois étages, mais ses soudures, boulons, plaques d'épissure, planchers et sièges de fermes restent absents.

## 4. Résultats dérivés

| Cas | Maille façade (mm) | Maille projectile (mm) | Facteur pas | Fils | Impulsion (MN·s) | Écart bilan qdm | Éléments projectile érodés | Masse projectile restante | Erreur énergie (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

- Écart moyen-fin d'impulsion : **{convergence['medium_to_fine_contact_impulse_relative_difference']:.3%}** (seuil 10 %).
- Écart au demi-pas d'impulsion : **{convergence['half_time_step_contact_impulse_relative_difference']:.3%}** (seuil 10 %).
- Répétabilité 1/4 fils de l'impulsion : **{convergence['thread_repeatability_contact_impulse_relative_difference']:.3%}** (seuil 1 %).
- Maximum de l'écart entre la variation du canal cumulatif FNZ et la variation de quantité de mouvement : **{max(case['time_history']['contact_impulse_to_projectile_momentum_change_relative_error'] for case in case_results):.3%}** (seuil 5 %).
- Ordre d'érosion rupture basse / nominale / haute : **{failure_low['time_history']['projectile_eroded_element_count']} / {medium['time_history']['projectile_eroded_element_count']} / {failure_high['time_history']['projectile_eroded_element_count']}**, portail **{'PASS' if failure_ordering else 'FAIL'}**.

## 5. Contradictions, inconnues et décision

- Le bordereau exact des plaques du panneau 124 au niveau 96 reste **inconnu** dans le jeu local gelé ; aucune archive n'a été rescannée pour V8V.
- La géométrie, les matériaux, les assemblages et les lois de rupture à grande vitesse du JT9D restent **non qualifiés**.
- TYPE7 ne qualifie pas à lui seul le contact arête-arête, la fragmentation tridimensionnelle, les ailes, le carburant ou le fuselage.
- Le portail global impact WTC 1, le couplage thermique et la dynamique Blender restent **fermés**, indépendamment du verdict numérique V8V.

La suite doit conserver V8U et V8V comme régressions. Un passage à une sous-structure plus globale n'est autorisé que si les portails d'impulsion, de pas de temps, de quantité de mouvement, d'énergie, de répétabilité et de rupture ci-dessus sont tous satisfaits ; sinon l'itération suivante doit corriger uniquement les échecs identifiés.
"""
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": gate_text,
                "results": str(summary_path),
                "report": str(report_path),
                "runtime_seconds": results["runtime"]["total_elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
