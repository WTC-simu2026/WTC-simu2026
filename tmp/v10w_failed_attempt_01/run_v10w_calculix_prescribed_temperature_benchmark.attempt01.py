"""V10W: independent prescribed-temperature mechanical benchmark.

Three generic B32R bar cases test uniform free thermal expansion, uniform
fully restrained expansion, and free expansion under a linear axial
temperature gradient.  The temperature fields are prescribed inside a purely
mechanical static step; no heat-transfer or fire problem is solved.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10w_calculix_prescribed_temperature_benchmark.json"
NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
DAT_HEADER = re.compile(
    r"(?im)^\s*(displacements|forces|total force).*?for set\s+(TIP|BASE)\s+and time\s+([-+0-9.Ee]+)\s*$"
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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def check_files(entries: list[dict[str, Any]], group: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        path = resolve_path(entry["path"])
        exists = path.is_file()
        actual = sha256(path) if exists else None
        rows.append(
            {
                "group": group,
                "id": entry.get("id") or entry.get("role"),
                "path": rel(path),
                "exists": exists,
                "expected_sha256": entry["expected_sha256"],
                "actual_sha256": actual,
                "hash_match": exists and actual == entry["expected_sha256"],
            }
        )
    return rows


def assert_fresh(outputs: dict[str, str], run_dir: Path) -> None:
    collisions = [rel(run_dir)] if run_dir.exists() else []
    collisions.extend(rel(resolve_path(value)) for value in outputs.values() if resolve_path(value).exists())
    if collisions:
        raise FileExistsError("V10W refuses to overwrite existing artifacts: " + ", ".join(collisions))


def analytical_reference(bench: dict[str, Any]) -> dict[str, float]:
    length = float(bench["geometry"]["length_mm"])
    width = float(bench["geometry"]["width_mm"])
    height = float(bench["geometry"]["height_mm"])
    area = width * height
    young = float(bench["material"]["young_modulus_mpa"])
    alpha = float(bench["material"]["thermal_expansion_per_c"])
    delta_temperature = float(bench["temperature"]["maximum_temperature_change_c"])
    uniform_displacement = alpha * delta_temperature * length
    restrained_force = young * area * alpha * delta_temperature
    restrained_stress = young * alpha * delta_temperature
    gradient_displacement = alpha * delta_temperature * length / 2.0
    return {
        "area_mm2": area,
        "uniform_free_tip_displacement_mm": uniform_displacement,
        "uniform_restrained_force_magnitude_n": restrained_force,
        "uniform_restrained_axial_stress_mpa": restrained_stress,
        "axial_linear_gradient_free_tip_displacement_mm": gradient_displacement,
    }


def close_enough(actual: float, expected: float, relative_tolerance: float = 1.0e-12) -> bool:
    return abs(actual - expected) <= relative_tolerance * max(abs(expected), 1.0)


def temperatures_for(case_id: str, node_count: int, maximum_temperature_c: float) -> list[float]:
    if case_id in ("UNIFORM_FREE", "UNIFORM_RESTRAINED"):
        return [maximum_temperature_c] * node_count
    if case_id == "AXIAL_LINEAR_GRADIENT_FREE":
        return [maximum_temperature_c * index / (node_count - 1) for index in range(node_count)]
    raise ValueError(f"Unknown case {case_id}")


def make_deck(job: str, case: dict[str, Any], element_count: int, bench: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    length = float(bench["geometry"]["length_mm"])
    width = float(bench["geometry"]["width_mm"])
    height = float(bench["geometry"]["height_mm"])
    young = float(bench["material"]["young_modulus_mpa"])
    nu = float(bench["material"]["poisson_ratio"])
    alpha = float(bench["material"]["thermal_expansion_per_c"])
    zero = float(bench["material"]["expansion_reference_temperature_c"])
    maximum_temperature = float(bench["temperature"]["maximum_temperature_change_c"])
    node_count = 2 * element_count + 1
    temperatures = temperatures_for(case["id"], node_count, maximum_temperature)
    lines = [
        "*HEADING",
        f"V10W independent prescribed-temperature B32R benchmark: {job}",
        "*NODE,NSET=ALL",
    ]
    for index in range(node_count):
        x = length * index / (node_count - 1)
        lines.append(f"{index + 1},{x:.12f},0.0,0.0")
    lines.append("*ELEMENT,TYPE=B32R,ELSET=BAR")
    for element in range(element_count):
        start = 2 * element + 1
        lines.append(f"{element + 1},{start},{start + 1},{start + 2}")
    lines.extend(
        [
            "*NSET,NSET=BASE",
            "1",
            "*NSET,NSET=TIP",
            str(node_count),
            "*MATERIAL,NAME=GENERIC_THERMOELASTIC",
            "*ELASTIC",
            f"{young:.12f},{nu:.12f}",
            f"*EXPANSION,ZERO={zero:.12f}",
            f"{alpha:.12g}",
            "*BEAM SECTION,ELSET=BAR,MATERIAL=GENERIC_THERMOELASTIC,SECTION=RECT",
            f"{width:.12f},{height:.12f}",
            "0.0,1.0,0.0",
            "*INITIAL CONDITIONS,TYPE=TEMPERATURE",
            f"ALL,{float(bench['temperature']['initial_temperature_c']):.12f}",
            "*STEP",
            "*STATIC",
            "*BOUNDARY",
            "BASE,1,6",
        ]
    )
    if bool(case["tip_axial_constraint"]):
        lines.append("TIP,1,1")
    lines.append("*TEMPERATURE,OP=NEW")
    for node_id, temperature in enumerate(temperatures, start=1):
        lines.append(f"{node_id},{temperature:.12f},0.0,0.0")
    lines.extend(
        [
            "*NODE FILE",
            "U,RF",
            "*EL FILE",
            "S,E",
            "*NODE PRINT,NSET=TIP,FREQUENCY=1",
            "U",
            "*NODE PRINT,NSET=BASE,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*NODE PRINT,NSET=TIP,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*END STEP",
            "",
        ]
    )
    expected_temperatures = temperatures_for(case["id"], node_count, maximum_temperature)
    assignment_pass = (
        len(temperatures) == node_count
        and all(close_enough(actual, expected) for actual, expected in zip(temperatures, expected_temperatures))
    )
    audit = {
        "job": job,
        "case_id": case["id"],
        "element_count": element_count,
        "original_beam_node_count": node_count,
        "explicit_temperature_assignment_count": len(temperatures),
        "minimum_assigned_temperature_c": min(temperatures),
        "maximum_assigned_temperature_c": max(temperatures),
        "arithmetic_mean_assigned_temperature_c": sum(temperatures) / len(temperatures),
        "temperature_assignment_pass": assignment_pass,
    }
    return "\n".join(lines), audit


def numeric_tokens(line: str) -> list[float] | None:
    stripped = line.strip()
    if not stripped or not re.fullmatch(r"[-+0-9.Ee\s]+", stripped):
        return None
    tokens = NUMBER.findall(stripped)
    try:
        return [float(token) for token in tokens] if tokens else None
    except ValueError:
        return None


def parse_dat(path: Path, tip_node: int) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    headers = list(DAT_HEADER.finditer(text))
    records: list[dict[str, Any]] = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        kind = header.group(1).lower()
        set_name = header.group(2).upper()
        candidates = [
            values for line in text[header.end() : end].splitlines() if (values := numeric_tokens(line))
        ]
        if kind.startswith("displacement") and set_name == "TIP":
            matches = [values for values in candidates if len(values) >= 4 and int(round(values[0])) == tip_node]
            if matches:
                records.append({"time": float(header.group(3)), "tip_u1_mm": matches[-1][1]})
        elif candidates and set_name in ("BASE", "TIP"):
            values = candidates[-1]
            if len(values) >= 3:
                records.append({"time": float(header.group(3)), f"{set_name.lower()}_rf1_n": values[-3]})
    tips = [row for row in records if "tip_u1_mm" in row]
    bases = [row for row in records if "base_rf1_n" in row]
    tip_forces = [row for row in records if "tip_rf1_n" in row]
    return {
        "header_count": len(headers),
        "tip_displacement_record_count": len(tips),
        "base_reaction_record_count": len(bases),
        "tip_reaction_record_count": len(tip_forces),
        "tip_u1_mm": tips[-1]["tip_u1_mm"] if tips else None,
        "base_rf1_n": bases[-1]["base_rf1_n"] if bases else None,
        "tip_rf1_n": tip_forces[-1]["tip_rf1_n"] if tip_forces else None,
    }


def run_case(
    ccx: Path,
    run_dir: Path,
    case: dict[str, Any],
    element_count: int,
    bench: dict[str, Any],
    reference: dict[str, float],
    acceptance: dict[str, Any],
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    job = f"v10w_{case['id'].lower()}_{element_count:03d}"
    deck, temperature_audit = make_deck(job, case, element_count, bench)
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
    node_count = 2 * element_count + 1
    parsed = parse_dat(dat_path, node_count) if dat_path.is_file() else {
        "header_count": 0,
        "tip_displacement_record_count": 0,
        "base_reaction_record_count": 0,
        "tip_reaction_record_count": 0,
        "tip_u1_mm": None,
        "base_rf1_n": None,
        "tip_rf1_n": None,
    }
    displacement = parsed["tip_u1_mm"]
    base_reaction = parsed["base_rf1_n"]
    tip_reaction = parsed["tip_rf1_n"]
    expected_displacement = float(case["analytical_tip_displacement_mm"])
    displacement_relative_error = (
        None
        if displacement is None or expected_displacement == 0.0
        else abs(float(displacement) - expected_displacement) / abs(expected_displacement)
    )
    zero_displacement_absolute_error = (
        None if displacement is None or expected_displacement != 0.0 else abs(float(displacement))
    )
    restrained = bool(case["tip_axial_constraint"])
    expected_force = float(case.get("analytical_restraint_force_magnitude_n", 0.0))
    if restrained and base_reaction is not None and tip_reaction is not None:
        force_error = max(
            abs(abs(float(base_reaction)) - expected_force) / expected_force,
            abs(abs(float(tip_reaction)) - expected_force) / expected_force,
        )
        equilibrium_residual = abs(float(base_reaction) + float(tip_reaction)) / max(
            abs(float(base_reaction)), abs(float(tip_reaction)), 1.0
        )
        free_reaction_absolute = None
    elif not restrained and base_reaction is not None and tip_reaction is not None:
        force_error = None
        equilibrium_residual = None
        free_reaction_absolute = max(abs(float(base_reaction)), abs(float(tip_reaction)))
    else:
        force_error = None
        equilibrium_residual = None
        free_reaction_absolute = None

    if restrained:
        analytical_pass = (
            zero_displacement_absolute_error is not None
            and zero_displacement_absolute_error <= acceptance["maximum_zero_displacement_absolute_error_mm"]
            and force_error is not None
            and force_error <= acceptance["maximum_restrained_force_relative_error"]
            and equilibrium_residual is not None
            and equilibrium_residual <= acceptance["maximum_restrained_end_reaction_equilibrium_relative_residual"]
        )
    else:
        analytical_pass = (
            displacement_relative_error is not None
            and displacement_relative_error <= acceptance["maximum_nonzero_displacement_relative_error"]
            and free_reaction_absolute is not None
            and free_reaction_absolute <= acceptance["maximum_free_case_reaction_absolute_n"]
        )
    row = {
        "job": job,
        "case_id": case["id"],
        "element_type": bench["element_type"],
        "element_count": element_count,
        "node_count": node_count,
        "tip_axial_constraint": restrained,
        "expected_tip_displacement_mm": expected_displacement,
        "parsed_tip_u1_mm": displacement,
        "displacement_relative_error": displacement_relative_error,
        "zero_displacement_absolute_error_mm": zero_displacement_absolute_error,
        "expected_restraint_force_magnitude_n": expected_force,
        "parsed_base_rf1_n": base_reaction,
        "parsed_tip_rf1_n": tip_reaction,
        "restrained_force_relative_error": force_error,
        "restrained_end_reaction_equilibrium_relative_residual": equilibrium_residual,
        "free_reaction_maximum_absolute_n": free_reaction_absolute,
        "return_code": return_code,
        "timed_out": timed_out,
        "dat_exists": dat_path.is_file(),
        "parse_summary": parsed,
        "return_code_pass": return_code == acceptance["solver_return_code"],
        "temperature_assignment_pass": temperature_audit["temperature_assignment_pass"],
        "analytical_pass": analytical_pass,
        "case_pass": return_code == acceptance["solver_return_code"]
        and temperature_audit["temperature_assignment_pass"]
        and analytical_pass,
        "runtime_seconds": runtime,
        "input_path": rel(input_path),
        "dat_path": rel(dat_path),
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-3000:],
    }
    return row, temperature_audit


def finest_pair_change(rows: list[dict[str, Any]], field: str) -> float | None:
    ordered = sorted(rows, key=lambda row: int(row["element_count"]))
    if len(ordered) < 2 or ordered[-1][field] is None or ordered[-2][field] is None:
        return None
    current = abs(float(ordered[-1][field]))
    previous = abs(float(ordered[-2][field]))
    return 100.0 * abs(current - previous) / max(current, 1.0e-30)


def format_optional(value: Any, spec: str) -> str:
    return "—" if value is None else format(float(value), spec)


def main() -> None:
    started_at = now_local()
    wall_start = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("iteration") != "V10W":
        raise ValueError("Configuration iteration must be V10W")
    outputs = config["outputs"]
    run_dir = resolve_path(outputs["run_directory"])
    assert_fresh(outputs, run_dir)
    bench = config["benchmark"]
    expected = config["expected"]
    acceptance = config["acceptance"]

    count_checks = {
        "regression_file_count": len(config["regression_files"]),
        "protected_file_count": len(config["protected_files"]),
        "software_reference_file_count": len(config["software_reference_files"]),
        "software_file_count": len(config["software_files"]),
        "case_count": len(bench["cases"]),
        "mesh_case_count": len(bench["mesh_element_counts"]),
    }
    mismatches = {
        key: {"expected": expected[key], "actual": value}
        for key, value in count_checks.items()
        if expected[key] != value
    }
    if mismatches:
        raise ValueError(f"Predeclared count mismatch: {mismatches}")

    file_checks: list[dict[str, Any]] = []
    file_checks += check_files(config["regression_files"], "regression")
    file_checks += check_files(config["protected_files"], "protected")
    file_checks += check_files(config["software_reference_files"], "software_reference")
    file_checks += check_files(config["software_files"], "software")
    if not all(row["hash_match"] for row in file_checks):
        raise RuntimeError(f"Preflight hash failure: {[row for row in file_checks if not row['hash_match']]}")

    reference = analytical_reference(bench)
    case_map = {case["id"]: case for case in bench["cases"]}
    reference_checks = {
        "area_mm2": close_enough(reference["area_mm2"], float(bench["geometry"]["area_mm2"])),
        "uniform_free_tip_displacement_mm": close_enough(
            reference["uniform_free_tip_displacement_mm"],
            float(case_map["UNIFORM_FREE"]["analytical_tip_displacement_mm"]),
        ),
        "uniform_restrained_force_magnitude_n": close_enough(
            reference["uniform_restrained_force_magnitude_n"],
            float(case_map["UNIFORM_RESTRAINED"]["analytical_restraint_force_magnitude_n"]),
        ),
        "uniform_restrained_axial_stress_mpa": close_enough(
            reference["uniform_restrained_axial_stress_mpa"],
            float(case_map["UNIFORM_RESTRAINED"]["analytical_axial_stress_mpa"]),
        ),
        "gradient_free_tip_displacement_mm": close_enough(
            reference["axial_linear_gradient_free_tip_displacement_mm"],
            float(case_map["AXIAL_LINEAR_GRADIENT_FREE"]["analytical_tip_displacement_mm"]),
        ),
    }
    if not all(reference_checks.values()):
        raise RuntimeError(f"Analytical reference mismatch: {reference_checks}")

    ccx_entry = config["software_files"][0]
    ccx = resolve_path(ccx_entry["path"])
    version_query = subprocess.run(
        [str(ccx), "-v"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, timeout=30
    )
    version_text = version_query.stdout + "\n" + version_query.stderr
    version_match = re.search(r"Version\s+([0-9.]+)", version_text, re.IGNORECASE)
    detected_version = version_match.group(1) if version_match else None
    version_pass = detected_version == ccx_entry["expected_version"]
    if not version_pass:
        raise RuntimeError(f"CalculiX version mismatch: {detected_version}")

    run_dir.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    temperature_audits: list[dict[str, Any]] = []
    max_runtime = float(config["execution_policy"]["maximum_runtime_seconds"])
    for case in bench["cases"]:
        for elements_raw in bench["mesh_element_counts"]:
            remaining = max_runtime - (time.perf_counter() - wall_start)
            row, temperature_audit = run_case(
                ccx,
                run_dir,
                case,
                int(elements_raw),
                bench,
                reference,
                acceptance,
                min(60.0, remaining),
            )
            rows.append(row)
            temperature_audits.append(temperature_audit)
    if len(rows) != expected["unique_solver_job_count"]:
        raise RuntimeError(f"Expected {expected['unique_solver_job_count']} jobs, got {len(rows)}")

    by_case = {
        case_id: sorted([row for row in rows if row["case_id"] == case_id], key=lambda row: row["element_count"])
        for case_id in case_map
    }
    mesh_convergence = {
        "UNIFORM_FREE_tip_displacement_change_pct": finest_pair_change(by_case["UNIFORM_FREE"], "parsed_tip_u1_mm"),
        "UNIFORM_RESTRAINED_force_change_pct": finest_pair_change(by_case["UNIFORM_RESTRAINED"], "parsed_base_rf1_n"),
        "AXIAL_LINEAR_GRADIENT_FREE_tip_displacement_change_pct": finest_pair_change(
            by_case["AXIAL_LINEAR_GRADIENT_FREE"], "parsed_tip_u1_mm"
        ),
    }
    return_pass_count = sum(bool(row["return_code_pass"]) for row in rows)
    analytical_pass_count = sum(bool(row["analytical_pass"]) for row in rows)
    temperature_pass_count = sum(bool(row["temperature_assignment_pass"]) for row in rows)

    protected_path = resolve_path(config["protected_files"][0]["path"])
    protected_after = sha256(protected_path)
    protected_unchanged = protected_after == config["protected_files"][0]["expected_sha256"]
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
    all_run_files_hashed = bool(manifest_rows) and all(len(row["sha256"]) == 64 for row in manifest_rows)

    criteria = {
        "predeclared_input_hashes": all(row["hash_match"] for row in file_checks),
        "protected_master_unchanged": protected_unchanged,
        "calculix_version": version_pass,
        "solver_return_codes": return_pass_count == expected["solver_return_code_pass_count"],
        "all_outputs_parsed": all(
            row["dat_exists"]
            and row["parsed_tip_u1_mm"] is not None
            and row["parsed_base_rf1_n"] is not None
            and row["parsed_tip_rf1_n"] is not None
            for row in rows
        ),
        "analytical_cases": analytical_pass_count == expected["analytical_case_pass_count"],
        "explicit_temperature_assignments": temperature_pass_count == expected["temperature_assignment_audit_pass_count"],
        "uniform_free_mesh_invariance": mesh_convergence["UNIFORM_FREE_tip_displacement_change_pct"] is not None
        and mesh_convergence["UNIFORM_FREE_tip_displacement_change_pct"]
        <= acceptance["maximum_finest_pair_nonzero_displacement_change_pct"],
        "uniform_restrained_mesh_invariance": mesh_convergence["UNIFORM_RESTRAINED_force_change_pct"] is not None
        and mesh_convergence["UNIFORM_RESTRAINED_force_change_pct"]
        <= acceptance["maximum_finest_pair_restrained_force_change_pct"],
        "gradient_free_mesh_invariance": mesh_convergence["AXIAL_LINEAR_GRADIENT_FREE_tip_displacement_change_pct"] is not None
        and mesh_convergence["AXIAL_LINEAR_GRADIENT_FREE_tip_displacement_change_pct"]
        <= acceptance["maximum_finest_pair_nonzero_displacement_change_pct"],
        "generated_input_deck_count": input_deck_count == expected["input_deck_count"],
        "all_run_files_hashed": all_run_files_hashed,
        "heat_transfer_solver_not_run": expected["heat_transfer_solver_run_count"] == 0,
        "coupled_temperature_displacement_solver_not_run": expected["coupled_temperature_displacement_solver_run_count"] == 0,
        "no_wtc_mechanical_requirement_closed": expected["mechanical_requirement_closed_count"] == 0,
        "no_physical_wtc_release": expected["physical_wtc_state_release_count"] == 0,
        "no_historical_outcome_assignment": expected["historical_outcome_assignment_count"] == 0,
    }
    decision_pass = all(criteria.values())
    decision = "PASS_INDEPENDENT_PRESCRIBED_TEMPERATURE_MECHANICAL_BENCHMARK" if decision_pass else "FAIL_INDEPENDENT_PRESCRIBED_TEMPERATURE_MECHANICAL_BENCHMARK"
    finished_at = now_local()
    total_runtime = time.perf_counter() - wall_start

    regression_audit = {
        "iteration": "V10W",
        "status": "PASS" if criteria["predeclared_input_hashes"] and protected_unchanged else "FAIL",
        "started_at_local": started_at,
        "finished_at_local": finished_at,
        "count_checks": count_checks,
        "file_checks": file_checks,
        "protected_master_sha256_after": protected_after,
        "protected_master_unchanged": protected_unchanged,
    }
    source_manifest = {
        "iteration": "V10W",
        "scope": "Independent numerical benchmark only",
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        "design_research": config["design_research"],
        "local_software_syntax_precedent": [row for row in file_checks if row["group"] == "software_reference"],
        "solver_binary": [row for row in file_checks if row["group"] == "software"],
        "solver_version_query": {
            "return_code": version_query.returncode,
            "detected_version": detected_version,
            "expected_version": ccx_entry["expected_version"],
            "version_match": version_pass,
            "stdout": version_query.stdout,
            "stderr": version_query.stderr,
            "note": "Version query is not one of the twelve structural benchmark jobs.",
        },
        "official_wtc_source_pages_read": 0,
        "source_archive_files_read": 0,
        "wtc_physical_sources_used": [],
    }
    analytical_payload = {
        "iteration": "V10W",
        "unit_system": bench["unit_system"],
        "declared_inputs": {
            "geometry": bench["geometry"],
            "material": bench["material"],
            "temperature": bench["temperature"],
            "cases": bench["cases"],
        },
        "formulas": bench["analytical_formulas"],
        "recomputed": reference,
        "declared_reference_checks": reference_checks,
        "all_reproduced": all(reference_checks.values()),
        "heat_transfer_solved": False,
        "wtc_attribution": False,
    }
    execution_log = {
        "iteration": "V10W",
        "solver": {"path": rel(ccx), "sha256": sha256(ccx), "version": detected_version},
        "analysis_type": bench["analysis_type"],
        "unique_structural_solver_job_count": len(rows),
        "runs": rows,
        "total_runtime_seconds": total_runtime,
    }
    gate = {
        "iteration": "V10W",
        "decision": decision,
        "pass": decision_pass,
        "criteria": criteria,
        "metrics": {
            "unique_solver_job_count": len(rows),
            "solver_return_code_pass_count": return_pass_count,
            "analytical_case_pass_count": analytical_pass_count,
            "temperature_assignment_audit_pass_count": temperature_pass_count,
            "mesh_convergence": mesh_convergence,
            "generated_input_deck_count": input_deck_count,
            "hashed_run_file_count": len(manifest_rows),
            "mechanical_requirement_count": expected["mechanical_requirement_count"],
            "mechanical_requirement_closed_count": 0,
            "physical_wtc_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "allowed_credit": "Local CalculiX 2.22 B32R mechanical response to explicitly prescribed temperature fields only",
        "forbidden_credit": [
            "heat-transfer, compartment-fire, SFRM or member-temperature prediction",
            "WTC 1 member, connection, floor, core or perimeter response",
            "collapse initiation, propagation, arrest, collapse or non-collapse of WTC 1",
        ],
        "next_iteration": config["next_iteration"],
    }
    results = {
        "model": "WTC1_V10W_INDEPENDENT_CALCULIX_PRESCRIBED_TEMPERATURE_BENCHMARK",
        "iteration": "V10W",
        "decision": decision,
        "scope": config["dataset"]["scope"],
        "analytical_reference": reference,
        "cases": rows,
        "temperature_assignment_audit": temperature_audits,
        "mesh_convergence": mesh_convergence,
        "solver_counts": {
            "structural_solver_run_count": len(rows),
            "software_version_query_count": 1,
            "heat_transfer_solver_run_count": 0,
            "coupled_temperature_displacement_solver_run_count": 0,
            "fire_solver_run_count": 0,
            "impact_solver_run_count": 0,
            "propagation_solver_run_count": 0,
            "other_solver_run_count": 0,
            "gpu_compute_run_count": 0,
            "blender_run_count": 0,
        },
        "wtc_credit": {
            "mechanical_requirement_count": 22,
            "mechanical_requirement_closed_count": 0,
            "physical_wtc_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "next_iteration": config["next_iteration"],
    }

    report = [
        "# WTC 1 — V10W : benchmark mécanique à température prescrite",
        "",
        "## Décision",
        "",
        f"**{'PASS' if decision_pass else 'ÉCHEC'} — `{decision}`.**",
        "",
        "Cette décision qualifie uniquement la conversion locale d’un champ de température imposé en dilatation ou effort axial dans un barreau B32R générique. Aucun transfert de chaleur, incendie ou champ thermique WTC 1 n’est calculé.",
        "",
        "## Références analytiques",
        "",
        f"- Dilatation uniforme libre : {reference['uniform_free_tip_displacement_mm']:.6f} mm.",
        f"- Effort uniforme totalement empêché : {reference['uniform_restrained_force_magnitude_n']:.6f} N, soit {reference['uniform_restrained_axial_stress_mpa']:.6f} MPa dérivés.",
        f"- Gradient axial linéaire libre : {reference['axial_linear_gradient_free_tip_displacement_mm']:.6f} mm.",
        "",
        "| Cas | Éléments | Déplacement (mm) | Réaction base (N) | Réaction extrémité (N) | Erreur déplacement | Erreur effort | Statut |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        displacement_error = row["displacement_relative_error"]
        if displacement_error is None:
            displacement_error = row["zero_displacement_absolute_error_mm"]
        report.append(
            f"| {row['case_id']} | {row['element_count']} | {format_optional(row['parsed_tip_u1_mm'], '.9f')} | {format_optional(row['parsed_base_rf1_n'], '.6f')} | {format_optional(row['parsed_tip_rf1_n'], '.6f')} | {format_optional(displacement_error, '.3e')} | {format_optional(row['restrained_force_relative_error'], '.3e')} | {'PASS' if row['case_pass'] else 'ÉCHEC'} |"
        )
    report.extend(
        [
            "",
            "## Convergence des maillages les plus fins",
            "",
            f"- Dilatation uniforme libre : {format_optional(mesh_convergence['UNIFORM_FREE_tip_displacement_change_pct'], '.6g')} %.",
            f"- Effort uniforme empêché : {format_optional(mesh_convergence['UNIFORM_RESTRAINED_force_change_pct'], '.6g')} %.",
            f"- Gradient axial libre : {format_optional(mesh_convergence['AXIAL_LINEAR_GRADIENT_FREE_tip_displacement_change_pct'], '.6g')} %.",
            "",
            "## Discipline de preuve",
            "",
            "### 1. Faits directement observés ou transcrits",
            "",
            f"Le binaire local haché annonce CalculiX {detected_version}. Douze jeux d’entrée sont exécutés, chaque nœud original reçoit explicitement une température, toutes les sorties sont inventoriées et le maître Blender reste inchangé.",
            "",
            "### 2. Résultats d’un modèle officiel",
            "",
            "Aucun résultat officiel NIST n’est utilisé.",
            "",
            "### 3. Affirmations provenant des archives locales",
            "",
            "Aucune affirmation des archives WTC n’est utilisée. La documentation CalculiX sert uniquement à distinguer température prescrite en étape mécanique et analyse thermique couplée.",
            "",
            "### 4. Hypothèses propres au modèle",
            "",
            "Barreau générique de 1 000 mm et 10 × 10 mm, E = 200 000 MPa, ν = 0,3, coefficient de dilatation constant 12×10⁻⁶ /°C, température initiale et de référence 0 °C, élévation synthétique maximale 100 °C, comportement linéaire et petites déformations.",
            "",
            "### 5. Résultats dérivés",
            "",
            "Les déplacements, l’effort empêché, la contrainte axiale dérivée, les erreurs analytiques, les équilibres de réactions et les variations de maillage proviennent des paramètres déclarés et des sorties CalculiX parsées.",
            "",
            "### 6. Contradictions et informations manquantes",
            "",
            "Aucun flux thermique, convection, rayonnement, feu de compartiment, SFRM, historique température-temps ou loi matériau dépendante de la température n’est résolu. Le benchmark ferme 0/22 exigences mécaniques WTC et ne permet aucune conclusion d’effondrement ou de non-effondrement.",
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
        resolve_path(outputs["case_matrix"]),
        [
            "job", "case_id", "element_type", "element_count", "node_count", "tip_axial_constraint",
            "expected_tip_displacement_mm", "parsed_tip_u1_mm", "displacement_relative_error",
            "zero_displacement_absolute_error_mm", "expected_restraint_force_magnitude_n", "parsed_base_rf1_n",
            "parsed_tip_rf1_n", "restrained_force_relative_error",
            "restrained_end_reaction_equilibrium_relative_residual", "free_reaction_maximum_absolute_n",
            "return_code", "temperature_assignment_pass", "analytical_pass", "case_pass", "runtime_seconds",
        ],
        rows,
    )
    write_csv(
        resolve_path(outputs["temperature_assignment_audit"]),
        [
            "job", "case_id", "element_count", "original_beam_node_count",
            "explicit_temperature_assignment_count", "minimum_assigned_temperature_c",
            "maximum_assigned_temperature_c", "arithmetic_mean_assigned_temperature_c",
            "temperature_assignment_pass",
        ],
        temperature_audits,
    )
    write_json(resolve_path(outputs["solver_execution_log"]), execution_log)
    write_csv(
        resolve_path(outputs["solver_file_manifest"]),
        ["path", "job", "suffix", "classification", "size_bytes", "sha256"],
        manifest_rows,
    )
    write_json(resolve_path(outputs["handoff_gate"]), gate)
    resolve_path(outputs["report"]).write_text("\n".join(report), encoding="utf-8", newline="\n")
    write_json(resolve_path(outputs["results"]), results)

    package_paths = [
        CONFIG_PATH,
        Path(__file__).resolve(),
        *[resolve_path(value) for key, value in outputs.items() if key not in ("run_directory", "offline_audit")],
    ]
    offline_audit = {
        "iteration": "V10W",
        "design_research_network_access_before_execution": True,
        "execution_network_access": False,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_wtc_source_pdf_page_read_count": 0,
        "official_sources_directory_modified": False,
        "software_installation": False,
        "structural_solver_run_count": len(rows),
        "software_version_query_count": 1,
        "heat_transfer_solver_run_count": 0,
        "coupled_temperature_displacement_solver_run_count": 0,
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

    print(
        json.dumps(
            {
                "iteration": "V10W",
                "decision": decision,
                "pass": decision_pass,
                "solver_jobs": len(rows),
                "analytical_case_pass_count": analytical_pass_count,
                "temperature_assignment_pass_count": temperature_pass_count,
                "mesh_convergence": mesh_convergence,
                "runtime_seconds": total_runtime,
                "report": outputs["report"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if not decision_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
