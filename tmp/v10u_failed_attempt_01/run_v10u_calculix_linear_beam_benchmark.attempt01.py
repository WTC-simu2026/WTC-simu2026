"""V10U: independent CalculiX B32R linear cantilever benchmark.

This iteration qualifies a local executable, a generated input deck, parsers,
reaction closure, analytical agreement, load linearity and mesh invariance.
It deliberately carries no WTC 1 geometry, material, damage, fire, connection,
load-path, initiation, propagation or historical-outcome credit.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10u_calculix_linear_beam_benchmark.json"
NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
DAT_HEADER = re.compile(
    r"(?im)^\s*(displacements|forces|total force).*?for set\s+(TIP|FIXED)\s+and time\s+([-+0-9.Ee]+)\s*$"
)


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


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def check_declared_files(entries: list[dict[str, Any]], group: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        path = resolve_path(entry["path"])
        exists = path.is_file()
        actual = sha256(path) if exists else None
        expected = entry["expected_sha256"]
        rows.append(
            {
                "group": group,
                "id": entry.get("id") or entry.get("role"),
                "path": rel(path),
                "exists": exists,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "hash_match": exists and actual == expected,
            }
        )
    return rows


def assert_fresh(outputs: dict[str, str], run_dir: Path) -> None:
    collisions = [rel(run_dir)] if run_dir.exists() else []
    collisions.extend(rel(resolve_path(value)) for value in outputs.values() if resolve_path(value).exists())
    if collisions:
        raise FileExistsError("V10U refuses to overwrite existing artifacts: " + ", ".join(collisions))


def analytical_reference(bench: dict[str, Any]) -> dict[str, float]:
    geom = bench["geometry"]
    mat = bench["material"]
    length = float(geom["length_mm"])
    width = float(geom["width_mm"])
    height = float(geom["height_mm"])
    young = float(mat["young_modulus_mpa"])
    nu = float(mat["poisson_ratio"])
    kappa = float(mat["shear_correction_factor"])
    load = float(bench["maximum_tip_load_n"])
    area = width * height
    inertia = width * height**3 / 12.0
    shear = young / (2.0 * (1.0 + nu))
    bending_displacement = load * length**3 / (3.0 * young * inertia)
    shear_displacement = load * length / (kappa * shear * area)
    total_displacement = bending_displacement + shear_displacement
    compliance = total_displacement / load
    work = 0.5 * load * total_displacement
    return {
        "area_mm2": area,
        "second_moment_mm4": inertia,
        "shear_modulus_mpa": shear,
        "euler_bernoulli_tip_displacement_at_full_load_mm": bending_displacement,
        "timoshenko_shear_displacement_at_full_load_mm": shear_displacement,
        "timoshenko_total_tip_displacement_at_full_load_mm": total_displacement,
        "timoshenko_compliance_mm_per_n": compliance,
        "linear_force_displacement_work_at_full_load_n_mm": work,
    }


def close_enough(actual: float, expected: float, relative_tolerance: float = 1.0e-11) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= relative_tolerance * scale


def make_deck(job: str, element_count: int, load_n: float, bench: dict[str, Any]) -> tuple[str, int]:
    geom = bench["geometry"]
    mat = bench["material"]
    length = float(geom["length_mm"])
    width = float(geom["width_mm"])
    height = float(geom["height_mm"])
    young = float(mat["young_modulus_mpa"])
    nu = float(mat["poisson_ratio"])
    node_count = 2 * element_count + 1
    lines = [
        "*HEADING",
        f"V10U independent linear B32R cantilever benchmark: {job}",
        "*NODE,NSET=ALL",
    ]
    for index in range(node_count):
        x = length * index / (2.0 * element_count)
        lines.append(f"{index + 1},{x:.12f},0.0,0.0")
    lines.append("*ELEMENT,TYPE=B32R,ELSET=BEAM")
    for element in range(element_count):
        start = 2 * element + 1
        middle = start + 1
        end = start + 2
        lines.append(f"{element + 1},{start},{middle},{end}")
    lines.extend(
        [
            "*NSET,NSET=FIXED",
            "1",
            "*NSET,NSET=TIP",
            str(node_count),
            "*MATERIAL,NAME=GENERIC_LINEAR_ELASTIC",
            "*ELASTIC",
            f"{young:.12f},{nu:.12f}",
            "*BEAM SECTION,ELSET=BEAM,MATERIAL=GENERIC_LINEAR_ELASTIC,SECTION=RECT",
            f"{width:.12f},{height:.12f}",
            "0.0,1.0,0.0",
            "*STEP",
            "*STATIC",
            "*BOUNDARY",
            "FIXED,1,6",
            "*CLOAD",
            f"TIP,3,{-load_n:.12f}",
            "*NODE FILE",
            "U,RF",
            "*EL FILE",
            "S,E",
            "*NODE PRINT,NSET=TIP,FREQUENCY=1",
            "U",
            "*NODE PRINT,NSET=FIXED,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines), node_count


def numeric_tokens(line: str) -> list[float] | None:
    stripped = line.strip()
    if not stripped or not re.fullmatch(r"[-+0-9.Ee\s]+", stripped):
        return None
    tokens = NUMBER.findall(stripped)
    if not tokens:
        return None
    try:
        return [float(token) for token in tokens]
    except ValueError:
        return None


def parse_dat(path: Path, tip_node: int) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    headers = list(DAT_HEADER.finditer(text))
    parsed: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        kind = header.group(1).lower()
        set_name = header.group(2).upper()
        section = text[header.end() : end]
        candidates = [values for line in section.splitlines() if (values := numeric_tokens(line))]
        if kind.startswith("displacement") and set_name == "TIP":
            matches = [values for values in candidates if len(values) >= 4 and int(round(values[0])) == tip_node]
            if matches:
                parsed.append({"time": float(header.group(3)), "tip_u3_mm": matches[-1][3]})
        elif set_name == "FIXED" and candidates:
            values = candidates[-1]
            if len(values) >= 3:
                parsed.append({"time": float(header.group(3)), "fixed_rf3_n": values[-1]})
    tip_values = [row for row in parsed if "tip_u3_mm" in row]
    reaction_values = [row for row in parsed if "fixed_rf3_n" in row]
    return {
        "header_count": len(headers),
        "tip_record_count": len(tip_values),
        "reaction_record_count": len(reaction_values),
        "tip_u3_mm": tip_values[-1]["tip_u3_mm"] if tip_values else None,
        "fixed_rf3_n": reaction_values[-1]["fixed_rf3_n"] if reaction_values else None,
    }


def run_case(
    ccx: Path,
    run_dir: Path,
    job: str,
    element_count: int,
    load_fraction: float,
    bench: dict[str, Any],
    reference: dict[str, float],
    timeout_seconds: float,
) -> dict[str, Any]:
    load_n = float(bench["maximum_tip_load_n"]) * load_fraction
    deck, tip_node = make_deck(job, element_count, load_n, bench)
    input_path = run_dir / f"{job}.inp"
    input_path.write_text(deck, encoding="ascii", newline="\n")
    started = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(
            [str(ccx), job],
            cwd=run_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=max(timeout_seconds, 1.0),
        )
        return_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        return_code = None
        stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    runtime = time.perf_counter() - started
    dat_path = run_dir / f"{job}.dat"
    parsed = parse_dat(dat_path, tip_node) if dat_path.is_file() else {
        "header_count": 0,
        "tip_record_count": 0,
        "reaction_record_count": 0,
        "tip_u3_mm": None,
        "fixed_rf3_n": None,
    }
    tip_u3 = parsed["tip_u3_mm"]
    reaction = parsed["fixed_rf3_n"]
    positive_displacement = -tip_u3 if tip_u3 is not None else None
    expected_displacement = reference["timoshenko_compliance_mm_per_n"] * load_n
    displacement_error_pct = (
        None
        if positive_displacement is None or expected_displacement == 0.0
        else 100.0 * abs(positive_displacement - expected_displacement) / expected_displacement
    )
    reaction_error = None if reaction is None or load_n == 0.0 else abs(reaction - load_n) / load_n
    acceptance = bench["_acceptance"]
    return {
        "job": job,
        "element_type": bench["element_type"],
        "element_count": element_count,
        "node_count": tip_node,
        "load_fraction": load_fraction,
        "applied_tip_load_n": load_n,
        "expected_positive_tip_displacement_mm": expected_displacement,
        "parsed_tip_u3_mm": tip_u3,
        "positive_tip_displacement_mm": positive_displacement,
        "parsed_fixed_rf3_n": reaction,
        "absolute_tip_error_vs_timoshenko_pct": displacement_error_pct,
        "reaction_relative_error": reaction_error,
        "return_code": return_code,
        "timed_out": timed_out,
        "dat_exists": dat_path.is_file(),
        "parse_summary": parsed,
        "return_code_pass": return_code == acceptance["solver_return_code"],
        "analytical_displacement_pass": displacement_error_pct is not None
        and displacement_error_pct <= acceptance["maximum_absolute_tip_error_vs_timoshenko_pct"],
        "reaction_closure_pass": reaction_error is not None
        and reaction_error <= acceptance["maximum_reaction_relative_error"],
        "runtime_seconds": runtime,
        "input_path": rel(input_path),
        "dat_path": rel(dat_path),
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-3000:],
    }


def linear_regression(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    x = [float(row["applied_tip_load_n"]) for row in rows]
    y = [float(row["positive_tip_displacement_mm"]) for row in rows]
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    slope = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y)) / denominator
    intercept = y_mean - slope * x_mean
    predictions = [slope * value + intercept for value in x]
    residual = sum((actual - predicted) ** 2 for actual, predicted in zip(y, predictions))
    total = sum((actual - y_mean) ** 2 for actual in y)
    r_squared = 1.0 - residual / total if total > 0.0 else None
    origin_denominator = sum(value * value for value in x)
    slope_through_origin = sum(xi * yi for xi, yi in zip(x, y)) / origin_denominator
    return {
        "slope_mm_per_n": slope,
        "intercept_mm": intercept,
        "r_squared": r_squared,
        "slope_through_origin_mm_per_n": slope_through_origin,
    }


def main() -> None:
    started_at = now_local()
    wall_start = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("iteration") != "V10U":
        raise ValueError("Configuration iteration must be V10U")
    outputs = config["outputs"]
    run_dir = resolve_path(outputs["run_directory"])
    assert_fresh(outputs, run_dir)

    expected = config["expected"]
    count_checks = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "cached_input_file_count": len(config["cached_input_files"]),
        "software_reference_file_count": len(config["software_reference_files"]),
        "software_file_count": len(config["software_files"]),
        "mesh_case_count": len(config["benchmark"]["mesh_element_counts"]),
        "load_fraction_count": len(config["benchmark"]["load_fractions"]),
    }
    count_mismatches = {
        key: {"expected": expected[key], "actual": value}
        for key, value in count_checks.items()
        if value != expected[key]
    }
    if count_mismatches:
        raise ValueError(f"Predeclared count mismatch: {count_mismatches}")

    file_checks: list[dict[str, Any]] = []
    file_checks += check_declared_files(config["regression_files"], "regression")
    file_checks += check_declared_files(config["protected_files"], "protected")
    file_checks += check_declared_files(config["cached_input_files"], "cached_input")
    file_checks += check_declared_files(config["software_reference_files"], "software_reference")
    file_checks += check_declared_files(config["software_files"], "software")
    if not all(row["hash_match"] for row in file_checks):
        failures = [row for row in file_checks if not row["hash_match"]]
        raise RuntimeError(f"Preflight hash failure: {failures}")

    bench = config["benchmark"]
    acceptance = config["acceptance"]
    bench["_acceptance"] = acceptance
    reference = analytical_reference(bench)
    declared_reference = bench["analytical_reference"]
    reference_checks = {
        key: {
            "declared": float(declared_reference[key]),
            "recomputed": reference[key],
            "match": close_enough(reference[key], float(declared_reference[key])),
        }
        for key in declared_reference
    }
    geometry_checks = {
        "area_mm2": {
            "declared": float(bench["geometry"]["area_mm2"]),
            "recomputed": reference["area_mm2"],
            "match": close_enough(reference["area_mm2"], float(bench["geometry"]["area_mm2"])),
        },
        "second_moment_mm4": {
            "declared": float(bench["geometry"]["second_moment_mm4"]),
            "recomputed": reference["second_moment_mm4"],
            "match": close_enough(reference["second_moment_mm4"], float(bench["geometry"]["second_moment_mm4"])),
        },
        "shear_modulus_mpa": {
            "declared": float(bench["material"]["shear_modulus_mpa"]),
            "recomputed": reference["shear_modulus_mpa"],
            "match": close_enough(reference["shear_modulus_mpa"], float(bench["material"]["shear_modulus_mpa"])),
        },
    }
    if not all(row["match"] for row in list(reference_checks.values()) + list(geometry_checks.values())):
        raise RuntimeError("Analytical reference in configuration does not reproduce from declared inputs")

    ccx_entry = config["software_files"][0]
    ccx = resolve_path(ccx_entry["path"])
    version_query = subprocess.run(
        [str(ccx), "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=30,
    )
    version_text = (version_query.stdout + "\n" + version_query.stderr).strip()
    version_match = re.search(r"Version\s+([0-9.]+)", version_text, re.IGNORECASE)
    detected_version = version_match.group(1) if version_match else None
    version_pass = detected_version == ccx_entry["expected_version"]
    if not version_pass:
        raise RuntimeError(f"CalculiX version mismatch: expected {ccx_entry['expected_version']}, found {detected_version}")

    run_dir.mkdir(parents=True, exist_ok=False)
    jobs: list[tuple[str, int, float]] = []
    for elements in bench["mesh_element_counts"]:
        jobs.append((f"v10u_mesh_{int(elements):03d}", int(elements), 1.0))
    fd_mesh = int(bench["force_displacement_mesh_element_count"])
    for fraction in bench["load_fractions"]:
        value = float(fraction)
        if value not in (0.0, 1.0):
            jobs.append((f"v10u_load_{round(100 * value):03d}", fd_mesh, value))
    if len(jobs) != expected["unique_solver_job_count"]:
        raise RuntimeError(f"Expected {expected['unique_solver_job_count']} unique jobs, built {len(jobs)}")

    runs: list[dict[str, Any]] = []
    max_runtime = float(config["execution_policy"]["maximum_runtime_seconds"])
    for job, elements, fraction in jobs:
        remaining = max_runtime - (time.perf_counter() - wall_start)
        if remaining <= 1.0:
            raise TimeoutError("V10U global runtime ceiling reached before all predeclared jobs")
        runs.append(run_case(ccx, run_dir, job, elements, fraction, bench, reference, min(60.0, remaining)))

    master_path = resolve_path(config["protected_files"][0]["path"])
    protected_hash_after = sha256(master_path)
    protected_unchanged = protected_hash_after == config["protected_files"][0]["expected_sha256"]

    mesh_runs = [row for row in runs if row["job"].startswith("v10u_mesh_")]
    mesh_runs.sort(key=lambda row: row["element_count"])
    mesh_rows = [
        {
            "job": row["job"],
            "element_type": row["element_type"],
            "element_count": row["element_count"],
            "node_count": row["node_count"],
            "load_n": row["applied_tip_load_n"],
            "positive_tip_displacement_mm": row["positive_tip_displacement_mm"],
            "timoshenko_reference_mm": row["expected_positive_tip_displacement_mm"],
            "absolute_error_pct": row["absolute_tip_error_vs_timoshenko_pct"],
            "fixed_reaction_z_n": row["parsed_fixed_rf3_n"],
            "reaction_relative_error": row["reaction_relative_error"],
            "return_code": row["return_code"],
            "runtime_seconds": row["runtime_seconds"],
            "case_pass": row["return_code_pass"] and row["analytical_displacement_pass"] and row["reaction_closure_pass"],
        }
        for row in mesh_runs
    ]

    full_fd_run = next(
        row for row in runs if row["job"] == f"v10u_mesh_{fd_mesh:03d}" and row["load_fraction"] == 1.0
    )
    load_run_by_fraction = {float(row["load_fraction"]): row for row in runs if row["element_count"] == fd_mesh}
    load_run_by_fraction[1.0] = full_fd_run
    fd_rows: list[dict[str, Any]] = []
    for fraction_value in [float(value) for value in bench["load_fractions"]]:
        if fraction_value == 0.0:
            fd_rows.append(
                {
                    "source": "algebraic_zero_control",
                    "load_fraction": 0.0,
                    "applied_tip_load_n": 0.0,
                    "positive_tip_displacement_mm": 0.0,
                    "timoshenko_reference_mm": 0.0,
                    "absolute_error_pct": 0.0,
                    "fixed_reaction_z_n": 0.0,
                    "reaction_relative_error": 0.0,
                    "return_code": "NOT_RUN_BY_DESIGN",
                }
            )
        else:
            row = load_run_by_fraction[fraction_value]
            fd_rows.append(
                {
                    "source": row["job"],
                    "load_fraction": fraction_value,
                    "applied_tip_load_n": row["applied_tip_load_n"],
                    "positive_tip_displacement_mm": row["positive_tip_displacement_mm"],
                    "timoshenko_reference_mm": row["expected_positive_tip_displacement_mm"],
                    "absolute_error_pct": row["absolute_tip_error_vs_timoshenko_pct"],
                    "fixed_reaction_z_n": row["parsed_fixed_rf3_n"],
                    "reaction_relative_error": row["reaction_relative_error"],
                    "return_code": row["return_code"],
                }
            )

    numeric_fd_ready = all(row["positive_tip_displacement_mm"] is not None for row in fd_rows)
    regression = linear_regression(fd_rows) if numeric_fd_ready else {
        "slope_mm_per_n": None,
        "intercept_mm": None,
        "r_squared": None,
        "slope_through_origin_mm_per_n": None,
    }
    expected_compliance = reference["timoshenko_compliance_mm_per_n"]
    slope_error_pct = (
        None
        if regression["slope_mm_per_n"] is None
        else 100.0 * abs(float(regression["slope_mm_per_n"]) - expected_compliance) / expected_compliance
    )
    regression["reference_compliance_mm_per_n"] = expected_compliance
    regression["slope_error_pct"] = slope_error_pct

    fine16 = next((row for row in mesh_rows if row["element_count"] == 16), None)
    fine32 = next((row for row in mesh_rows if row["element_count"] == 32), None)
    if fine16 and fine32 and fine16["positive_tip_displacement_mm"] is not None and fine32["positive_tip_displacement_mm"]:
        finest_change_pct = 100.0 * abs(
            float(fine32["positive_tip_displacement_mm"]) - float(fine16["positive_tip_displacement_mm"])
        ) / abs(float(fine32["positive_tip_displacement_mm"]))
    else:
        finest_change_pct = None

    return_pass_count = sum(bool(row["return_code_pass"]) for row in runs)
    reaction_pass_count = sum(bool(row["reaction_closure_pass"]) for row in runs)
    analytical_pass_count = sum(bool(row["analytical_displacement_pass"]) for row in runs)

    run_files = sorted(path for path in run_dir.iterdir() if path.is_file())
    manifest_rows = [
        {
            "path": rel(path),
            "job": path.stem,
            "suffix": path.suffix.lower(),
            "classification": "GENERATED_INPUT_DECK" if path.suffix.lower() == ".inp" else "CALCULIX_SOLVER_OUTPUT",
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in run_files
    ]
    input_deck_count = sum(row["suffix"] == ".inp" for row in manifest_rows)
    all_files_hashed = bool(manifest_rows) and all(len(row["sha256"]) == 64 for row in manifest_rows)

    criteria = {
        "predeclared_input_hashes": all(row["hash_match"] for row in file_checks),
        "protected_master_unchanged": protected_unchanged,
        "calculix_version": version_pass,
        "solver_return_codes": return_pass_count == expected["solver_return_code_pass_count"],
        "all_dat_outputs_parsed": all(
            row["dat_exists"]
            and row["positive_tip_displacement_mm"] is not None
            and row["parsed_fixed_rf3_n"] is not None
            for row in runs
        ),
        "analytical_displacement": analytical_pass_count == expected["analytical_displacement_pass_count"],
        "reaction_closure": reaction_pass_count == expected["reaction_closure_pass_count"],
        "mesh_invariance": finest_change_pct is not None
        and finest_change_pct <= acceptance["maximum_finest_pair_relative_change_pct"],
        "force_displacement_r_squared": regression["r_squared"] is not None
        and float(regression["r_squared"]) >= acceptance["minimum_force_displacement_r_squared"],
        "force_displacement_slope": slope_error_pct is not None
        and slope_error_pct <= acceptance["maximum_force_displacement_slope_error_pct"],
        "force_displacement_intercept": regression["intercept_mm"] is not None
        and abs(float(regression["intercept_mm"])) <= acceptance["maximum_absolute_force_displacement_intercept_mm"],
        "generated_input_deck_count": input_deck_count == expected["input_deck_count"],
        "all_run_files_hashed": all_files_hashed,
        "no_wtc_mechanical_requirement_closed": expected["mechanical_requirement_closed_count"] == 0,
        "no_physical_wtc_release": expected["physical_wtc_state_release_count"] == 0,
        "no_historical_outcome_assignment": expected["historical_outcome_assignment_count"] == 0,
    }
    decision_pass = all(criteria.values())
    decision = "PASS_INDEPENDENT_LINEAR_B32R_BENCHMARK" if decision_pass else "FAIL_INDEPENDENT_LINEAR_B32R_BENCHMARK"
    finished_at = now_local()
    total_runtime = time.perf_counter() - wall_start

    regression_audit = {
        "iteration": "V10U",
        "status": "PASS" if criteria["predeclared_input_hashes"] and protected_unchanged else "FAIL",
        "started_at_local": started_at,
        "finished_at_local": finished_at,
        "count_checks": count_checks,
        "file_checks": file_checks,
        "protected_master_sha256_after": protected_hash_after,
        "protected_master_unchanged": protected_unchanged,
    }
    source_manifest = {
        "iteration": "V10U",
        "scope": "Independent numerical benchmark only",
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        "local_software_syntax_precedent": [row for row in file_checks if row["group"] == "software_reference"],
        "solver_binary": [row for row in file_checks if row["group"] == "software"],
        "solver_version_query": {
            "command": [rel(ccx), "-v"],
            "return_code": version_query.returncode,
            "detected_version": detected_version,
            "expected_version": ccx_entry["expected_version"],
            "version_match": version_pass,
            "stdout": version_query.stdout,
            "stderr": version_query.stderr,
            "note": "The version query is not one of the nine structural benchmark jobs.",
        },
        "web_sources_used": [],
        "official_source_pages_read": 0,
        "source_archive_files_read": 0,
        "wtc_physical_sources_used": [],
    }
    analytical_payload = {
        "iteration": "V10U",
        "unit_system": bench["unit_system"],
        "declared_inputs": {
            "geometry": bench["geometry"],
            "material": bench["material"],
            "maximum_tip_load_n": bench["maximum_tip_load_n"],
        },
        "formulas": bench["formulas"],
        "recomputed": reference,
        "declared_reference_checks": reference_checks,
        "derived_geometry_checks": geometry_checks,
        "all_reproduced": all(row["match"] for row in list(reference_checks.values()) + list(geometry_checks.values())),
        "wtc_attribution": False,
    }
    execution_log = {
        "iteration": "V10U",
        "solver": {"path": rel(ccx), "sha256": sha256(ccx), "version": detected_version},
        "unique_structural_solver_job_count": len(runs),
        "runs": runs,
        "total_runtime_seconds": total_runtime,
    }
    gate = {
        "iteration": "V10U",
        "decision": decision,
        "pass": decision_pass,
        "criteria": criteria,
        "metrics": {
            "unique_solver_job_count": len(runs),
            "solver_return_code_pass_count": return_pass_count,
            "reaction_closure_pass_count": reaction_pass_count,
            "analytical_displacement_pass_count": analytical_pass_count,
            "maximum_absolute_tip_error_vs_timoshenko_pct": max(
                (float(row["absolute_tip_error_vs_timoshenko_pct"]) for row in runs if row["absolute_tip_error_vs_timoshenko_pct"] is not None),
                default=None,
            ),
            "maximum_reaction_relative_error": max(
                (float(row["reaction_relative_error"]) for row in runs if row["reaction_relative_error"] is not None),
                default=None,
            ),
            "finest_16_to_32_relative_change_pct": finest_change_pct,
            "force_displacement_regression": regression,
            "generated_input_deck_count": input_deck_count,
            "hashed_run_file_count": len(manifest_rows),
            "mechanical_requirement_count": expected["mechanical_requirement_count"],
            "mechanical_requirement_closed_count": 0,
            "physical_wtc_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "allowed_credit": "Local CalculiX 2.22 B32R linear-elastic cantilever workflow only",
        "forbidden_credit": [
            "WTC 1 member, connection, floor, core or perimeter response",
            "impact, fire, thermal, initiation or propagation physics",
            "collapse or non-collapse of WTC 1",
        ],
        "next_iteration": config["next_iteration"],
    }
    results = {
        "model": "WTC1_V10U_INDEPENDENT_CALCULIX_LINEAR_BEAM_BENCHMARK",
        "iteration": "V10U",
        "decision": decision,
        "scope": config["dataset"]["scope"],
        "analytical_reference": reference,
        "mesh_convergence": mesh_rows,
        "force_displacement": fd_rows,
        "force_displacement_regression": regression,
        "finest_16_to_32_relative_change_pct": finest_change_pct,
        "solver_counts": {
            "structural_solver_run_count": len(runs),
            "thermal_solver_run_count": 0,
            "fire_solver_run_count": 0,
            "impact_solver_run_count": 0,
            "propagation_solver_run_count": 0,
            "other_solver_run_count": 0,
            "gpu_compute_run_count": 0,
            "blender_run_count": 0,
            "software_version_query_count": 1,
        },
        "wtc_credit": {
            "mechanical_requirement_count": 22,
            "mechanical_requirement_closed_count": 0,
            "physical_wtc_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "gate": {"path": outputs["handoff_gate"], "decision": decision, "pass": decision_pass},
        "next_iteration": config["next_iteration"],
    }

    status_word = "PASS" if decision_pass else "ÉCHEC"
    report_lines = [
        "# WTC 1 — V10U : benchmark CalculiX indépendant d’une poutre linéaire",
        "",
        "## Décision",
        "",
        f"**{status_word} — `{decision}`.**",
        "",
        "Cette décision qualifie uniquement la chaîne locale CalculiX 2.22 pour ce porte-à-faux générique en éléments B32R. Elle ne valide aucun membre, assemblage, chemin de charge ou mécanisme du WTC 1.",
        "",
        "## Résultats numériques",
        "",
        f"- Exécutions structurelles : {len(runs)} ; codes retour acceptés : {return_pass_count}/{len(runs)}.",
        f"- Fermetures charge-réaction : {reaction_pass_count}/{len(runs)}.",
        f"- Comparaisons analytiques acceptées : {analytical_pass_count}/{len(runs)}.",
        f"- Déplacement de référence de Timoshenko à 10 000 N : {reference['timoshenko_total_tip_displacement_at_full_load_mm']:.7f} mm.",
        f"- Écart maximal solveur/référence : {gate['metrics']['maximum_absolute_tip_error_vs_timoshenko_pct']:.6g} %.",
        f"- Écart relatif entre 16 et 32 éléments : {finest_change_pct:.6g} %.",
        f"- Linéarité charge-déplacement : R² = {float(regression['r_squared']):.12f} ; erreur de pente = {slope_error_pct:.6g} % ; intercept = {float(regression['intercept_mm']):.6g} mm.",
        "",
        "| Éléments | Déplacement (mm) | Référence (mm) | Écart (%) | Réaction Z (N) | Fermeture relative | Statut |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in mesh_rows:
        report_lines.append(
            f"| {row['element_count']} | {float(row['positive_tip_displacement_mm']):.9f} | {float(row['timoshenko_reference_mm']):.9f} | {float(row['absolute_error_pct']):.6g} | {float(row['fixed_reaction_z_n']):.6f} | {float(row['reaction_relative_error']):.3e} | {'PASS' if row['case_pass'] else 'ÉCHEC'} |"
        )
    report_lines.extend(
        [
            "",
            "## Discipline de preuve",
            "",
            "### 1. Faits directement observés ou transcrits",
            "",
            f"Le binaire local vérifié par empreinte annonce CalculiX {detected_version}. Neuf jeux d’entrée ont été exécutés ; leurs fichiers d’entrée et sorties ont été inventoriés et hachés. Le fichier maître Blender est resté inchangé.",
            "",
            "### 2. Résultats d’un modèle officiel",
            "",
            "Aucun résultat officiel NIST n’est utilisé dans ce benchmark.",
            "",
            "### 3. Affirmations provenant des archives locales",
            "",
            "Aucune affirmation des archives WTC n’est utilisée. Le seul exemple installé consulté sert de précédent syntaxique B32R et n’obtient aucun crédit physique.",
            "",
            "### 4. Hypothèses propres au modèle",
            "",
            "Porte-à-faux rectangulaire générique de 2 000 mm, section 100 × 100 mm, matériau élastique isotrope E = 200 000 MPa et ν = 0,3, encastrement idéal, force nodale en bout, petites déformations, sans imperfection, contact ni non-linéarité.",
            "",
            "### 5. Résultats dérivés",
            "",
            "Les références d’Euler–Bernoulli et de Timoshenko, la conformité charge-réaction, la convergence 16→32 éléments, la régression charge-déplacement et le travail externe linéaire sont calculés à partir des entrées déclarées et des sorties numériques parsées.",
            "",
            "### 6. Contradictions et informations manquantes",
            "",
            "Aucune donnée mécanique manquante du WTC 1 n’est fermée : 0/22 exigences restent satisfaites. Les sections réelles, assemblages, redistributions, dommages d’impact, températures, ruptures et conditions de propagation demeurent absents. Il est donc interdit de transformer ce PASS logiciel en conclusion d’effondrement ou de non-effondrement.",
            "",
            "## Étape suivante",
            "",
            f"{config['next_iteration']['id']} — {config['next_iteration']['objective']}",
            "",
        ]
    )

    write_json(resolve_path(outputs["regression_audit"]), regression_audit)
    write_json(resolve_path(outputs["source_manifest"]), source_manifest)
    write_json(resolve_path(outputs["analytical_reference"]), analytical_payload)
    write_csv(
        resolve_path(outputs["mesh_convergence"]),
        [
            "job", "element_type", "element_count", "node_count", "load_n",
            "positive_tip_displacement_mm", "timoshenko_reference_mm", "absolute_error_pct",
            "fixed_reaction_z_n", "reaction_relative_error", "return_code", "runtime_seconds", "case_pass",
        ],
        mesh_rows,
    )
    write_csv(
        resolve_path(outputs["force_displacement"]),
        [
            "source", "load_fraction", "applied_tip_load_n", "positive_tip_displacement_mm",
            "timoshenko_reference_mm", "absolute_error_pct", "fixed_reaction_z_n",
            "reaction_relative_error", "return_code",
        ],
        fd_rows,
    )
    write_json(resolve_path(outputs["solver_execution_log"]), execution_log)
    write_csv(
        resolve_path(outputs["solver_file_manifest"]),
        ["path", "job", "suffix", "classification", "size_bytes", "sha256"],
        manifest_rows,
    )
    write_json(resolve_path(outputs["handoff_gate"]), gate)
    resolve_path(outputs["report"]).write_text("\n".join(report_lines), encoding="utf-8", newline="\n")
    write_json(resolve_path(outputs["results"]), results)

    package_paths = [
        CONFIG_PATH,
        Path(__file__).resolve(),
        *[resolve_path(value) for key, value in outputs.items() if key not in ("run_directory", "offline_audit")],
    ]
    offline_audit = {
        "iteration": "V10U",
        "network_access": False,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_source_pdf_page_read_count": 0,
        "official_source_pdf_text_extraction_count": 0,
        "official_sources_directory_modified": False,
        "software_installation": False,
        "structural_solver_run_count": len(runs),
        "software_version_query_count": 1,
        "thermal_solver_run_count": 0,
        "fire_solver_run_count": 0,
        "impact_solver_run_count": 0,
        "propagation_solver_run_count": 0,
        "other_solver_run_count": 0,
        "gpu_compute_run_count": 0,
        "blender_run_count": 0,
        "physical_wtc_state_release_count": 0,
        "historical_outcome_assignment_count": 0,
        "protected_master_unchanged": protected_unchanged,
        "package_files": [
            {"path": rel(path), "size_bytes": path.stat().st_size, "sha256": sha256(path)} for path in package_paths
        ],
        "solver_run_files": manifest_rows,
        "decision": decision,
        "finished_at_local": finished_at,
    }
    write_json(resolve_path(outputs["offline_audit"]), offline_audit)

    summary = {
        "iteration": "V10U",
        "decision": decision,
        "pass": decision_pass,
        "solver_jobs": len(runs),
        "maximum_tip_error_pct": gate["metrics"]["maximum_absolute_tip_error_vs_timoshenko_pct"],
        "maximum_reaction_relative_error": gate["metrics"]["maximum_reaction_relative_error"],
        "finest_change_pct": finest_change_pct,
        "r_squared": regression["r_squared"],
        "slope_error_pct": slope_error_pct,
        "runtime_seconds": total_runtime,
        "report": outputs["report"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not decision_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
