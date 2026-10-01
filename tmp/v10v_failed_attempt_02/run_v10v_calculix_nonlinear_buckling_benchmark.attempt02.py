"""V10V: independent CalculiX eigenvalue and postbuckling benchmark.

The model is a generic pin-ended, square B32R column.  Perfect geometry is
used for eigenvalue extraction; a stress-free sinusoidal crooked geometry is
used for displacement-controlled geometrically nonlinear response.  Nothing
in this benchmark is a WTC 1 physical assignment or historical outcome.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import statistics
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10v_calculix_nonlinear_buckling_benchmark.json"
NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
NONLINEAR_HEADER = re.compile(
    r"(?im)^\s*(displacements|forces|total force).*?for set\s+(TOP|MID|BOTTOM)\s+and time\s+([-+0-9.Ee]+)\s*$"
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
        raise FileExistsError("V10V refuses to overwrite existing artifacts: " + ", ".join(collisions))


def analytical_reference(bench: dict[str, Any]) -> dict[str, float]:
    geom = bench["geometry"]
    mat = bench["material"]
    length = float(geom["length_mm"])
    width = float(geom["width_mm"])
    height = float(geom["height_mm"])
    young = float(mat["young_modulus_mpa"])
    nu = float(mat["poisson_ratio"])
    kappa = float(mat["shear_correction_factor"])
    area = width * height
    inertia = width * height**3 / 12.0
    shear = young / (2.0 * (1.0 + nu))
    euler = math.pi**2 * young * inertia / length**2
    timoshenko = euler / (1.0 + euler / (kappa * shear * area))
    critical_shortening = timoshenko * length / (young * area)
    return {
        "area_mm2": area,
        "second_moment_mm4": inertia,
        "shear_modulus_mpa": shear,
        "euler_critical_load_n": euler,
        "timoshenko_shear_corrected_critical_load_n": timoshenko,
        "timoshenko_critical_axial_shortening_mm": critical_shortening,
    }


def close_enough(actual: float, expected: float, relative_tolerance: float = 1.0e-11) -> bool:
    return abs(actual - expected) <= relative_tolerance * max(abs(expected), 1.0)


def beam_nodes(element_count: int, bench: dict[str, Any], imperfect: bool) -> list[tuple[int, float, float, float]]:
    length = float(bench["geometry"]["length_mm"])
    imperfection = float(bench["nonlinear_cases"]["initial_midspan_amplitude_mm"])
    nodes: list[tuple[int, float, float, float]] = []
    for index in range(2 * element_count + 1):
        z = length * index / (2.0 * element_count)
        x = imperfection * math.sin(math.pi * z / length) if imperfect else 0.0
        nodes.append((index + 1, x, 0.0, z))
    return nodes


def common_model_lines(job: str, element_count: int, bench: dict[str, Any], imperfect: bool) -> tuple[list[str], int, int]:
    geom = bench["geometry"]
    mat = bench["material"]
    nodes = beam_nodes(element_count, bench, imperfect)
    tip_node = len(nodes)
    mid_node = element_count + 1
    lines = ["*HEADING", f"V10V independent B32R column benchmark: {job}", "*NODE,NSET=ALL"]
    for node_id, x, y, z in nodes:
        lines.append(f"{node_id},{x:.12f},{y:.12f},{z:.12f}")
    lines.append("*ELEMENT,TYPE=B32R,ELSET=COLUMN")
    for element in range(element_count):
        start = 2 * element + 1
        lines.append(f"{element + 1},{start},{start + 1},{start + 2}")
    lines.extend(
        [
            "*NSET,NSET=BOTTOM",
            "1",
            "*NSET,NSET=MID",
            str(mid_node),
            "*NSET,NSET=TOP",
            str(tip_node),
            "*MATERIAL,NAME=GENERIC_LINEAR_ELASTIC",
            "*ELASTIC",
            f"{float(mat['young_modulus_mpa']):.12f},{float(mat['poisson_ratio']):.12f}",
            "*BEAM SECTION,ELSET=COLUMN,MATERIAL=GENERIC_LINEAR_ELASTIC,SECTION=RECT",
            f"{float(geom['width_mm']):.12f},{float(geom['height_mm']):.12f}",
            "0.0,1.0,0.0",
        ]
    )
    return lines, tip_node, mid_node


def make_eigen_deck(job: str, element_count: int, bench: dict[str, Any]) -> str:
    lines, _, _ = common_model_lines(job, element_count, bench, imperfect=False)
    eigen = bench["eigenvalue_cases"]
    lines.extend(
        [
            "*STEP",
            "*BUCKLE",
            f"{int(eigen['requested_mode_count'])},0.01",
            "*BOUNDARY",
            "BOTTOM,1,3",
            "BOTTOM,6,6",
            "TOP,1,2",
            "*CLOAD",
            f"TOP,3,{-float(eigen['reference_compressive_load_n']):.12f}",
            "*NODE FILE",
            "U",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines)


def make_nonlinear_deck(job: str, element_count: int, bench: dict[str, Any]) -> tuple[str, int, int]:
    lines, tip_node, mid_node = common_model_lines(job, element_count, bench, imperfect=True)
    nonlinear = bench["nonlinear_cases"]
    lines.extend(
        [
            f"*STEP,NLGEOM,INC={int(nonlinear['maximum_increment_count'])}",
            "*STATIC",
            f"{float(nonlinear['initial_time_increment']):.12g},1.0,{float(nonlinear['minimum_time_increment']):.12g},{float(nonlinear['maximum_time_increment']):.12g}",
            "*BOUNDARY",
            "BOTTOM,1,3",
            "BOTTOM,6,6",
            "TOP,1,2",
            f"TOP,3,3,{-float(nonlinear['target_axial_shortening_mm']):.12f}",
            "*NODE FILE",
            "U,RF",
            "*EL FILE",
            "S,E",
            "*NODE PRINT,NSET=TOP,FREQUENCY=1",
            "U",
            "*NODE PRINT,NSET=MID,FREQUENCY=1",
            "U",
            "*NODE PRINT,NSET=BOTTOM,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*NODE PRINT,NSET=TOP,TOTALS=ONLY,FREQUENCY=1",
            "RF",
            "*END STEP",
            "",
        ]
    )
    return "\n".join(lines), tip_node, mid_node


def parse_eigenvalues(path: Path) -> list[float]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values: list[float] = []
    active = False
    for line in text.splitlines():
        if "EIGENVALUE OUTPUT" in line.upper() or "BUCKLING FACTOR OUTPUT" in line.upper():
            active = True
            continue
        if not active:
            continue
        match = re.match(r"\s*\d+\s+([-+0-9.Ee]+)\s*$", line)
        if match:
            values.append(float(match.group(1)))
        elif values and line.strip() and not line.lstrip().upper().startswith("MODE"):
            break
    return values


def numeric_tokens(line: str) -> list[float] | None:
    stripped = line.strip()
    if not stripped or not re.fullmatch(r"[-+0-9.Ee\s]+", stripped):
        return None
    tokens = NUMBER.findall(stripped)
    try:
        return [float(token) for token in tokens] if tokens else None
    except ValueError:
        return None


def parse_nonlinear_curve(path: Path, top_node: int, mid_node: int) -> tuple[list[dict[str, float]], int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    headers = list(NONLINEAR_HEADER.finditer(text))
    by_time: dict[float, dict[str, float]] = {}
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        kind = header.group(1).lower()
        set_name = header.group(2).upper()
        time_value = round(float(header.group(3)), 12)
        row = by_time.setdefault(time_value, {"time": time_value})
        candidates = [
            values
            for line in text[header.end() : end].splitlines()
            if (values := numeric_tokens(line))
        ]
        if kind.startswith("displacement"):
            wanted = top_node if set_name == "TOP" else mid_node if set_name == "MID" else None
            matches = [
                values for values in candidates if wanted is not None and len(values) >= 4 and int(round(values[0])) == wanted
            ]
            if matches:
                values = matches[-1]
                if set_name == "TOP":
                    row["top_u3_mm"] = values[3]
                elif set_name == "MID":
                    row["mid_u1_mm"] = values[1]
        elif candidates and set_name in ("BOTTOM", "TOP"):
            values = candidates[-1]
            if len(values) >= 3:
                row[f"{set_name.lower()}_rf3_n"] = values[-1]
    required = ("top_u3_mm", "mid_u1_mm", "bottom_rf3_n", "top_rf3_n")
    curve = [row for _, row in sorted(by_time.items()) if all(field in row for field in required)]
    return curve, len(headers)


def imperfect_reference(shortening_mm: float, bench: dict[str, Any], reference: dict[str, float]) -> tuple[float, float]:
    if shortening_mm <= 0.0:
        return 0.0, float(bench["nonlinear_cases"]["initial_midspan_amplitude_mm"])
    length = float(bench["geometry"]["length_mm"])
    area = float(reference["area_mm2"])
    young = float(bench["material"]["young_modulus_mpa"])
    pcrit = float(reference["timoshenko_shear_corrected_critical_load_n"])
    e0 = float(bench["nonlinear_cases"]["initial_midspan_amplitude_mm"])

    def predicted_shortening(ratio: float) -> float:
        amplitude = e0 / (1.0 - ratio)
        axial = ratio * pcrit * length / (young * area)
        geometric = math.pi**2 * (amplitude**2 - e0**2) / (4.0 * length)
        return axial + geometric

    low = 0.0
    high = 1.0 - 1.0e-12
    for _ in range(120):
        middle = 0.5 * (low + high)
        if predicted_shortening(middle) < shortening_mm:
            low = middle
        else:
            high = middle
    ratio = 0.5 * (low + high)
    return ratio * pcrit, e0 / (1.0 - ratio)


def run_solver(ccx: Path, run_dir: Path, job: str, deck: str, timeout_seconds: float) -> dict[str, Any]:
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
    return {
        "job": job,
        "input_path": rel(input_path),
        "dat_path": rel(run_dir / f"{job}.dat"),
        "return_code": return_code,
        "timed_out": timed_out,
        "runtime_seconds": time.perf_counter() - started,
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-3000:],
    }


def monotonic_non_decreasing(values: list[float], tolerance: float = 1.0e-8) -> bool:
    return all(later + tolerance >= earlier for earlier, later in zip(values, values[1:]))


def format_optional(value: Any, spec: str) -> str:
    return "—" if value is None else format(float(value), spec)


def integrate_work(curve: list[dict[str, Any]]) -> float:
    points = [(0.0, 0.0)] + [
        (float(row["shortening_mm"]), float(row["compression_n"])) for row in curve
    ]
    work = 0.0
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        work += 0.5 * (y0 + y1) * (x1 - x0)
    return work


def main() -> None:
    started_at = now_local()
    wall_start = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("iteration") != "V10V":
        raise ValueError("Configuration iteration must be V10V")
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
        "eigenvalue_case_count": len(bench["eigenvalue_cases"]["element_counts"]),
        "nonlinear_case_count": len(bench["nonlinear_cases"]["element_counts"]),
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
    declared = bench["analytical_reference"]
    declared_checks = {
        key: {"declared": float(declared[key]), "recomputed": reference[key], "match": close_enough(reference[key], float(declared[key]))}
        for key in (
            "euler_critical_load_n",
            "timoshenko_shear_corrected_critical_load_n",
            "timoshenko_critical_axial_shortening_mm",
        )
    }
    derived_checks = {
        "area_mm2": close_enough(reference["area_mm2"], float(bench["geometry"]["area_mm2"])),
        "second_moment_mm4": close_enough(reference["second_moment_mm4"], float(bench["geometry"]["second_moment_mm4"])),
        "shear_modulus_mpa": close_enough(reference["shear_modulus_mpa"], float(bench["material"]["shear_modulus_mpa"])),
        "initial_imperfection_ratio": close_enough(
            float(bench["geometry"]["length_mm"]) / float(bench["nonlinear_cases"]["initial_midspan_amplitude_mm"]),
            float(bench["nonlinear_cases"]["initial_imperfection_ratio"]),
        ),
    }
    if not all(row["match"] for row in declared_checks.values()) or not all(derived_checks.values()):
        raise RuntimeError("Declared analytical values do not reproduce from inputs")

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
    max_runtime = float(config["execution_policy"]["maximum_runtime_seconds"])
    run_logs: list[dict[str, Any]] = []
    eigen_rows: list[dict[str, Any]] = []
    for elements_raw in bench["eigenvalue_cases"]["element_counts"]:
        elements = int(elements_raw)
        job = f"v10v_eigen_{elements:03d}"
        remaining = max_runtime - (time.perf_counter() - wall_start)
        log = run_solver(ccx, run_dir, job, make_eigen_deck(job, elements, bench), min(60.0, remaining))
        dat_path = run_dir / f"{job}.dat"
        eigenvalues = parse_eigenvalues(dat_path) if dat_path.is_file() else []
        positive = [value for value in eigenvalues if value > 0.0]
        first = min(positive) if positive else None
        error_pct = (
            None
            if first is None
            else 100.0 * abs(first - reference["timoshenko_shear_corrected_critical_load_n"]) / reference["timoshenko_shear_corrected_critical_load_n"]
        )
        row = {
            "job": job,
            "element_count": elements,
            "return_code": log["return_code"],
            "parsed_eigenvalue_count": len(eigenvalues),
            "all_parsed_eigenvalues_n": eigenvalues,
            "first_positive_eigenvalue_n": first,
            "timoshenko_reference_n": reference["timoshenko_shear_corrected_critical_load_n"],
            "absolute_error_pct": error_pct,
            "return_code_pass": log["return_code"] == acceptance["solver_return_code"],
            "analytical_pass": error_pct is not None and error_pct <= acceptance["maximum_eigenvalue_error_vs_timoshenko_pct"],
            "runtime_seconds": log["runtime_seconds"],
        }
        log.update({"analysis": "EIGENVALUE_BUCKLING", "element_count": elements, "parse": row})
        run_logs.append(log)
        eigen_rows.append(row)

    nonlinear_summaries: list[dict[str, Any]] = []
    all_curve_rows: list[dict[str, Any]] = []
    e0 = float(bench["nonlinear_cases"]["initial_midspan_amplitude_mm"])
    critical_shortening = reference["timoshenko_critical_axial_shortening_mm"]
    post_min = float(bench["nonlinear_cases"]["postcritical_window_minimum_shortening_factor"]) * critical_shortening
    target_shortening = float(bench["nonlinear_cases"]["target_axial_shortening_mm"])
    for elements_raw in bench["nonlinear_cases"]["element_counts"]:
        elements = int(elements_raw)
        job = f"v10v_nonlinear_{elements:03d}"
        deck, top_node, mid_node = make_nonlinear_deck(job, elements, bench)
        remaining = max_runtime - (time.perf_counter() - wall_start)
        log = run_solver(ccx, run_dir, job, deck, min(90.0, remaining))
        dat_path = run_dir / f"{job}.dat"
        raw_curve, header_count = parse_nonlinear_curve(dat_path, top_node, mid_node) if dat_path.is_file() else ([], 0)
        curve: list[dict[str, Any]] = []
        for point_index, raw in enumerate(raw_curve, start=1):
            shortening = max(0.0, -float(raw["top_u3_mm"]))
            amplitude = abs(e0 + float(raw["mid_u1_mm"]))
            bottom = float(raw["bottom_rf3_n"])
            top = float(raw["top_rf3_n"])
            compression = abs(bottom)
            equilibrium = abs(bottom + top) / max(abs(bottom), abs(top), 1.0)
            analytical_force, analytical_amplitude = imperfect_reference(shortening, bench, reference)
            analytical_error = (
                0.0
                if analytical_force == 0.0 and compression == 0.0
                else 100.0 * abs(compression - analytical_force) / analytical_force if analytical_force > 0.0 else None
            )
            point = {
                "case": job,
                "element_count": elements,
                "point_index": point_index,
                "time": float(raw["time"]),
                "shortening_mm": shortening,
                "midspan_u1_mm": float(raw["mid_u1_mm"]),
                "total_midspan_amplitude_mm": amplitude,
                "bottom_reaction_z_n": bottom,
                "top_reaction_z_n": top,
                "compression_n": compression,
                "end_reaction_equilibrium_relative_residual": equilibrium,
                "small_slope_reference_reaction_n": analytical_force,
                "small_slope_reference_amplitude_mm": analytical_amplitude,
                "reaction_error_vs_small_slope_pct": analytical_error,
                "postcritical_window": shortening >= post_min,
            }
            curve.append(point)
            all_curve_rows.append(point)

        shortenings = [float(row["shortening_mm"]) for row in curve]
        amplitudes = [float(row["total_midspan_amplitude_mm"]) for row in curve]
        post_rows = [row for row in curve if row["postcritical_window"]]
        post_errors = [float(row["reaction_error_vs_small_slope_pct"]) for row in post_rows if row["reaction_error_vs_small_slope_pct"] is not None]
        final = curve[-1] if curve else None
        target_error = (
            None if final is None else abs(float(final["shortening_mm"]) - target_shortening) / target_shortening
        )
        maximum_equilibrium = max(
            (float(row["end_reaction_equilibrium_relative_residual"]) for row in curve), default=None
        )
        final_reaction_ratio = (
            None if final is None else float(final["compression_n"]) / reference["timoshenko_shear_corrected_critical_load_n"]
        )
        final_amplification = None if final is None else float(final["total_midspan_amplitude_mm"]) / e0
        summary = {
            "job": job,
            "element_count": elements,
            "return_code": log["return_code"],
            "dat_header_count": header_count,
            "curve_point_count": len(curve),
            "postcritical_curve_point_count": len(post_rows),
            "last_time": None if final is None else final["time"],
            "target_shortening_mm": target_shortening,
            "final_shortening_mm": None if final is None else final["shortening_mm"],
            "target_shortening_relative_error": target_error,
            "final_compression_n": None if final is None else final["compression_n"],
            "final_reaction_to_critical_ratio": final_reaction_ratio,
            "final_midspan_amplitude_mm": None if final is None else final["total_midspan_amplitude_mm"],
            "final_lateral_amplification_ratio": final_amplification,
            "maximum_end_reaction_equilibrium_relative_residual": maximum_equilibrium,
            "median_postcritical_reaction_error_vs_small_slope_pct": statistics.median(post_errors) if post_errors else None,
            "maximum_postcritical_reaction_error_vs_small_slope_pct": max(post_errors) if post_errors else None,
            "monotonic_shortening": monotonic_non_decreasing(shortenings),
            "monotonic_lateral_amplification": monotonic_non_decreasing(amplitudes, tolerance=1.0e-6),
            "derived_external_work_n_mm": integrate_work(curve),
            "return_code_pass": log["return_code"] == acceptance["solver_return_code"],
            "target_reached_pass": target_error is not None and target_error <= acceptance["maximum_target_shortening_relative_error"],
            "equilibrium_pass": maximum_equilibrium is not None
            and maximum_equilibrium <= acceptance["maximum_end_reaction_equilibrium_relative_residual"],
            "postcritical_point_count_pass": len(post_rows) >= acceptance["minimum_postcritical_curve_point_count_per_case"],
            "amplification_pass": final_amplification is not None
            and final_amplification >= acceptance["minimum_final_lateral_amplification_ratio"],
            "final_reaction_ratio_pass": final_reaction_ratio is not None
            and acceptance["minimum_final_reaction_to_critical_ratio"] <= final_reaction_ratio <= acceptance["maximum_final_reaction_to_critical_ratio"],
            "runtime_seconds": log["runtime_seconds"],
        }
        log.update(
            {
                "analysis": "GEOMETRICALLY_NONLINEAR_IMPERFECT_COLUMN",
                "element_count": elements,
                "top_node": top_node,
                "mid_node": mid_node,
                "parse_summary": summary,
            }
        )
        run_logs.append(log)
        nonlinear_summaries.append(summary)

    if len(run_logs) != expected["unique_solver_job_count"]:
        raise RuntimeError(f"Expected {expected['unique_solver_job_count']} jobs, obtained {len(run_logs)}")

    eigen_rows.sort(key=lambda row: int(row["element_count"]))
    nonlinear_summaries.sort(key=lambda row: int(row["element_count"]))
    eigen_previous, eigen_current = eigen_rows[-2], eigen_rows[-1]
    eigen_finest_change_pct = (
        None
        if eigen_previous["first_positive_eigenvalue_n"] is None or eigen_current["first_positive_eigenvalue_n"] is None
        else 100.0
        * abs(float(eigen_current["first_positive_eigenvalue_n"]) - float(eigen_previous["first_positive_eigenvalue_n"]))
        / abs(float(eigen_current["first_positive_eigenvalue_n"]))
    )
    nonlinear_previous, nonlinear_current = nonlinear_summaries[-2], nonlinear_summaries[-1]
    final_reaction_change_pct = (
        None
        if nonlinear_previous["final_compression_n"] is None or nonlinear_current["final_compression_n"] is None
        else 100.0
        * abs(float(nonlinear_current["final_compression_n"]) - float(nonlinear_previous["final_compression_n"]))
        / abs(float(nonlinear_current["final_compression_n"]))
    )
    final_amplitude_change_pct = (
        None
        if nonlinear_previous["final_midspan_amplitude_mm"] is None or nonlinear_current["final_midspan_amplitude_mm"] is None
        else 100.0
        * abs(float(nonlinear_current["final_midspan_amplitude_mm"]) - float(nonlinear_previous["final_midspan_amplitude_mm"]))
        / abs(float(nonlinear_current["final_midspan_amplitude_mm"]))
    )

    return_pass_count = sum(log["return_code"] == acceptance["solver_return_code"] for log in run_logs)
    eigen_pass_count = sum(bool(row["analytical_pass"]) for row in eigen_rows)
    nonlinear_target_count = sum(bool(row["target_reached_pass"]) for row in nonlinear_summaries)
    nonlinear_equilibrium_count = sum(bool(row["equilibrium_pass"]) for row in nonlinear_summaries)

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
        "eigenvalue_analytical_agreement": eigen_pass_count == expected["eigenvalue_pass_count"],
        "eigenvalue_mesh_convergence": eigen_finest_change_pct is not None
        and eigen_finest_change_pct <= acceptance["maximum_eigenvalue_finest_pair_relative_change_pct"],
        "nonlinear_target_shortening": nonlinear_target_count == expected["nonlinear_target_reached_count"],
        "nonlinear_end_reaction_equilibrium": nonlinear_equilibrium_count == expected["nonlinear_equilibrium_pass_count"],
        "nonlinear_postcritical_point_count": all(row["postcritical_point_count_pass"] for row in nonlinear_summaries),
        "nonlinear_monotonic_shortening": all(row["monotonic_shortening"] for row in nonlinear_summaries)
        == acceptance["require_monotonic_shortening"],
        "nonlinear_monotonic_lateral_amplification": all(row["monotonic_lateral_amplification"] for row in nonlinear_summaries)
        == acceptance["require_monotonic_lateral_amplification"],
        "nonlinear_final_amplification": all(row["amplification_pass"] for row in nonlinear_summaries),
        "nonlinear_final_reaction_ratio": all(row["final_reaction_ratio_pass"] for row in nonlinear_summaries),
        "finest_postbuckling_small_slope_comparator": nonlinear_current["median_postcritical_reaction_error_vs_small_slope_pct"] is not None
        and float(nonlinear_current["median_postcritical_reaction_error_vs_small_slope_pct"])
        <= acceptance["maximum_finest_postbuckling_median_analytical_error_pct"],
        "nonlinear_final_reaction_mesh_convergence": final_reaction_change_pct is not None
        and final_reaction_change_pct <= acceptance["maximum_nonlinear_finest_pair_final_reaction_change_pct"],
        "nonlinear_final_amplitude_mesh_convergence": final_amplitude_change_pct is not None
        and final_amplitude_change_pct <= acceptance["maximum_nonlinear_finest_pair_final_amplitude_change_pct"],
        "generated_input_deck_count": input_deck_count == expected["input_deck_count"],
        "all_run_files_hashed": all_run_files_hashed,
        "no_wtc_mechanical_requirement_closed": expected["mechanical_requirement_closed_count"] == 0,
        "no_physical_wtc_release": expected["physical_wtc_state_release_count"] == 0,
        "no_historical_outcome_assignment": expected["historical_outcome_assignment_count"] == 0,
    }
    decision_pass = all(criteria.values())
    decision = "PASS_INDEPENDENT_B32R_NONLINEAR_BUCKLING_BENCHMARK" if decision_pass else "FAIL_INDEPENDENT_B32R_NONLINEAR_BUCKLING_BENCHMARK"
    finished_at = now_local()
    total_runtime = time.perf_counter() - wall_start

    regression_audit = {
        "iteration": "V10V",
        "status": "PASS" if criteria["predeclared_input_hashes"] and protected_unchanged else "FAIL",
        "started_at_local": started_at,
        "finished_at_local": finished_at,
        "count_checks": count_checks,
        "file_checks": file_checks,
        "protected_master_sha256_after": protected_after,
        "protected_master_unchanged": protected_unchanged,
    }
    source_manifest = {
        "iteration": "V10V",
        "scope": "Independent numerical benchmark only",
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        "local_software_syntax_precedent": [row for row in file_checks if row["group"] == "software_reference"],
        "solver_binary": [row for row in file_checks if row["group"] == "software"],
        "solver_version_query": {
            "return_code": version_query.returncode,
            "detected_version": detected_version,
            "expected_version": ccx_entry["expected_version"],
            "version_match": version_pass,
            "stdout": version_query.stdout,
            "stderr": version_query.stderr,
            "note": "Version query is not one of the seven structural benchmark jobs.",
        },
        "web_sources_used": [],
        "official_source_pages_read": 0,
        "source_archive_files_read": 0,
        "wtc_physical_sources_used": [],
    }
    analytical_payload = {
        "iteration": "V10V",
        "unit_system": bench["unit_system"],
        "declared_inputs": {
            "geometry": bench["geometry"],
            "material": bench["material"],
            "eigenvalue_cases": bench["eigenvalue_cases"],
            "nonlinear_cases": bench["nonlinear_cases"],
        },
        "recomputed": reference,
        "declared_reference_checks": declared_checks,
        "derived_input_checks": derived_checks,
        "imperfect_column_equations": declared["imperfect_column_equations"],
        "comparator_limit": "Small-slope imperfect-column relation; acceptance uses median error only on the finest mesh and cannot validate arbitrary finite-rotation postbuckling.",
        "wtc_attribution": False,
    }
    execution_log = {
        "iteration": "V10V",
        "solver": {"path": rel(ccx), "sha256": sha256(ccx), "version": detected_version},
        "unique_structural_solver_job_count": len(run_logs),
        "runs": run_logs,
        "total_runtime_seconds": total_runtime,
    }
    gate = {
        "iteration": "V10V",
        "decision": decision,
        "pass": decision_pass,
        "criteria": criteria,
        "metrics": {
            "unique_solver_job_count": len(run_logs),
            "solver_return_code_pass_count": return_pass_count,
            "eigenvalue_pass_count": eigen_pass_count,
            "eigenvalue_finest_pair": {
                "previous_element_count": eigen_previous["element_count"],
                "current_element_count": eigen_current["element_count"],
                "relative_change_pct": eigen_finest_change_pct,
            },
            "nonlinear_target_reached_count": nonlinear_target_count,
            "nonlinear_equilibrium_pass_count": nonlinear_equilibrium_count,
            "nonlinear_finest_pair": {
                "previous_element_count": nonlinear_previous["element_count"],
                "current_element_count": nonlinear_current["element_count"],
                "final_reaction_relative_change_pct": final_reaction_change_pct,
                "final_amplitude_relative_change_pct": final_amplitude_change_pct,
            },
            "finest_postbuckling_median_analytical_error_pct": nonlinear_current["median_postcritical_reaction_error_vs_small_slope_pct"],
            "generated_input_deck_count": input_deck_count,
            "hashed_run_file_count": len(manifest_rows),
            "mechanical_requirement_count": expected["mechanical_requirement_count"],
            "mechanical_requirement_closed_count": 0,
            "physical_wtc_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "allowed_credit": "Local CalculiX 2.22 B32R eigenvalue and geometrically nonlinear imperfect-column workflow only",
        "forbidden_credit": [
            "WTC 1 member, connection, floor, core or perimeter response",
            "temperature-dependent material response, impact damage or fracture",
            "collapse initiation, propagation, arrest, collapse or non-collapse of WTC 1",
        ],
        "next_iteration": config["next_iteration"],
    }
    results = {
        "model": "WTC1_V10V_INDEPENDENT_CALCULIX_NONLINEAR_BUCKLING_BENCHMARK",
        "iteration": "V10V",
        "decision": decision,
        "scope": config["dataset"]["scope"],
        "analytical_reference": reference,
        "eigenvalue_convergence": eigen_rows,
        "postbuckling_summary": nonlinear_summaries,
        "mesh_comparisons": {
            "eigenvalue_finest_relative_change_pct": eigen_finest_change_pct,
            "nonlinear_final_reaction_relative_change_pct": final_reaction_change_pct,
            "nonlinear_final_amplitude_relative_change_pct": final_amplitude_change_pct,
        },
        "solver_counts": {
            "structural_solver_run_count": len(run_logs),
            "software_version_query_count": 1,
            "thermal_solver_run_count": 0,
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
        "# WTC 1 — V10V : benchmark indépendant de flambement non linéaire",
        "",
        "## Décision",
        "",
        f"**{'PASS' if decision_pass else 'ÉCHEC'} — `{decision}`.**",
        "",
        "La décision qualifie uniquement ce cas générique CalculiX B32R : extraction de charge critique, colonne initialement courbe, grandes déformations et raccourcissement imposé. Elle ne représente aucune colonne du WTC 1.",
        "",
        "## Flambement propre",
        "",
        f"Référence de Timoshenko : {reference['timoshenko_shear_corrected_critical_load_n']:.6f} N ; Euler : {reference['euler_critical_load_n']:.6f} N.",
        "",
        "| Éléments | Première charge propre (N) | Écart (%) | Code retour | Statut |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in eigen_rows:
        report.append(
            f"| {row['element_count']} | {format_optional(row['first_positive_eigenvalue_n'], '.6f')} | {format_optional(row['absolute_error_pct'], '.6g')} | {row['return_code']} | {'PASS' if row['analytical_pass'] and row['return_code_pass'] else 'ÉCHEC'} |"
        )
    report.extend(
        [
            "",
            f"Variation du couple de maillages le plus fin ({eigen_previous['element_count']}→{eigen_current['element_count']}) : {eigen_finest_change_pct:.6g} %.",
            "",
            "## Réponse après la charge critique",
            "",
            f"Imperfection initiale : {e0:.3f} mm (L/{float(bench['nonlinear_cases']['initial_imperfection_ratio']):.0f}) ; raccourcissement cible : {target_shortening:.3f} mm ; seuil de fenêtre postcritique : {post_min:.6f} mm.",
            "",
            "| Éléments | Points | Points postcritiques | Raccourcissement final (mm) | Réaction finale / Pcr | Amplitude finale (mm) | Amplification | Résidu d'équilibre max | Erreur médiane analytique (%) |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in nonlinear_summaries:
        report.append(
            f"| {row['element_count']} | {row['curve_point_count']} | {row['postcritical_curve_point_count']} | {format_optional(row['final_shortening_mm'], '.6f')} | {format_optional(row['final_reaction_to_critical_ratio'], '.6f')} | {format_optional(row['final_midspan_amplitude_mm'], '.6f')} | {format_optional(row['final_lateral_amplification_ratio'], '.3f')} | {format_optional(row['maximum_end_reaction_equilibrium_relative_residual'], '.3e')} | {format_optional(row['median_postcritical_reaction_error_vs_small_slope_pct'], '.6g')} |"
        )
    report.extend(
        [
            "",
            f"Convergence {nonlinear_previous['element_count']}→{nonlinear_current['element_count']} : réaction finale {final_reaction_change_pct:.6g} %, amplitude finale {final_amplitude_change_pct:.6g} %.",
            "",
            "Le travail externe est intégré sous chaque courbe réaction–raccourcissement. C’est un résultat dérivé ; aucune égalité avec une énergie interne de solveur non extraite n’est revendiquée.",
            "",
            "## Discipline de preuve",
            "",
            "### 1. Faits directement observés ou transcrits",
            "",
            f"Le binaire local haché annonce CalculiX {detected_version}. Sept jeux d’entrée ont été exécutés. Leurs fichiers d’entrée et sorties sont hachés, les réactions des deux appuis sont parsées à chaque incrément convergé et le maître Blender reste inchangé.",
            "",
            "### 2. Résultats d’un modèle officiel",
            "",
            "Aucun résultat officiel NIST n’est utilisé.",
            "",
            "### 3. Affirmations provenant des archives locales",
            "",
            "Aucune affirmation des archives WTC n’est utilisée. Un exemple FreeCAD installé sert seulement de précédent syntaxique pour B32R.",
            "",
            "### 4. Hypothèses propres au modèle",
            "",
            "Colonne générique bi-articulée de 2 000 mm, section carrée 40 × 40 mm, élasticité isotrope, imperfection sinusoïdale de 2 mm, appuis idéaux, sans contact, plasticité, température, endommagement ni rupture.",
            "",
            "### 5. Résultats dérivés",
            "",
            "Les charges critiques d’Euler et de Timoshenko, la relation approchée de colonne imparfaite, les résidus d’équilibre, les convergences de maillage et les travaux externes proviennent des entrées déclarées et des sorties CalculiX parsées.",
            "",
            "### 6. Contradictions et informations manquantes",
            "",
            "La relation postcritique analytique est une approximation à faibles pentes, non une solution exacte à rotations finies. Le benchmark ne contient aucune section, liaison, charge, imperfection, température ou rupture propre au WTC 1. Il ferme donc 0/22 exigences mécaniques et ne permet aucune conclusion d’effondrement ou de non-effondrement.",
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
        resolve_path(outputs["eigenvalue_convergence"]),
        [
            "job", "element_count", "return_code", "parsed_eigenvalue_count", "first_positive_eigenvalue_n",
            "timoshenko_reference_n", "absolute_error_pct", "return_code_pass", "analytical_pass", "runtime_seconds",
        ],
        eigen_rows,
    )
    write_csv(
        resolve_path(outputs["postbuckling_summary"]),
        [
            "job", "element_count", "return_code", "dat_header_count", "curve_point_count", "postcritical_curve_point_count",
            "last_time", "target_shortening_mm", "final_shortening_mm", "target_shortening_relative_error",
            "final_compression_n", "final_reaction_to_critical_ratio", "final_midspan_amplitude_mm",
            "final_lateral_amplification_ratio", "maximum_end_reaction_equilibrium_relative_residual",
            "median_postcritical_reaction_error_vs_small_slope_pct", "maximum_postcritical_reaction_error_vs_small_slope_pct",
            "monotonic_shortening", "monotonic_lateral_amplification", "derived_external_work_n_mm",
            "return_code_pass", "target_reached_pass", "equilibrium_pass", "postcritical_point_count_pass",
            "amplification_pass", "final_reaction_ratio_pass", "runtime_seconds",
        ],
        nonlinear_summaries,
    )
    write_csv(
        resolve_path(outputs["postbuckling_curve"]),
        [
            "case", "element_count", "point_index", "time", "shortening_mm", "midspan_u1_mm",
            "total_midspan_amplitude_mm", "bottom_reaction_z_n", "top_reaction_z_n", "compression_n",
            "end_reaction_equilibrium_relative_residual", "small_slope_reference_reaction_n",
            "small_slope_reference_amplitude_mm", "reaction_error_vs_small_slope_pct", "postcritical_window",
        ],
        all_curve_rows,
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
        "iteration": "V10V",
        "network_access": False,
        "source_archive_read": False,
        "source_archive_modified": False,
        "official_source_pdf_page_read_count": 0,
        "official_source_pdf_text_extraction_count": 0,
        "official_sources_directory_modified": False,
        "software_installation": False,
        "structural_solver_run_count": len(run_logs),
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

    print(
        json.dumps(
            {
                "iteration": "V10V",
                "decision": decision,
                "pass": decision_pass,
                "solver_jobs": len(run_logs),
                "eigenvalue_finest_change_pct": eigen_finest_change_pct,
                "nonlinear_final_reaction_change_pct": final_reaction_change_pct,
                "nonlinear_final_amplitude_change_pct": final_amplitude_change_pct,
                "finest_postbuckling_median_analytical_error_pct": nonlinear_current["median_postcritical_reaction_error_vs_small_slope_pct"],
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
