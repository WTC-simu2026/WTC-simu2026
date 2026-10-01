"""V10X: independent displacement-controlled cyclic plasticity benchmark.

Four generic T3D2 meshes are taken through the same five-step axial
displacement history.  CalculiX reactions are compared point by point with a
one-dimensional linear-isotropic-hardening return map, including unloading,
load reversal, cycle energy, equilibrium and mesh invariance.  No WTC-specific
physical parameter or historical outcome is assigned by this benchmark.
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
CONFIG_PATH = ROOT / "wtc1_simulation_v8/data/v10x_calculix_cyclic_plasticity_benchmark.json"
NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?")
DAT_HEADER = re.compile(
    r"(?i)^\s*(displacements|forces|total force).*?for set\s+(TIP|BASE)\s+and time\s+([-+0-9.Ee]+)\s*$"
)
STEP_HEADER = re.compile(r"S\s+T\s+E\s+P\s+(\d+)", re.IGNORECASE)


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
    for key, value in outputs.items():
        if key == "run_directory":
            continue
        path = resolve_path(value)
        if path.exists():
            collisions.append(rel(path))
    if collisions:
        raise FileExistsError("V10X refuses to overwrite existing artifacts: " + ", ".join(collisions))


def analytical_reference(bench: dict[str, Any]) -> dict[str, float]:
    length = float(bench["geometry"]["length_mm"])
    area = float(bench["geometry"]["area_mm2"])
    young = float(bench["material"]["young_modulus_mpa"])
    yield_stress = float(bench["material"]["yield_stress_mpa"])
    plastic_table = bench["material"]["plastic_table"]
    if len(plastic_table) != 2:
        raise ValueError("V10X attempt 03 requires exactly two plastic-table points")
    hardening = (
        float(plastic_table[1]["true_stress_mpa"]) - float(plastic_table[0]["true_stress_mpa"])
    ) / (
        float(plastic_table[1]["equivalent_plastic_strain"])
        - float(plastic_table[0]["equivalent_plastic_strain"])
    )
    declared_hardening = float(bench["material"]["plastic_hardening_modulus_mpa"])
    if not close_enough(hardening, declared_hardening):
        raise ValueError("Plastic-table slope does not match the declared hardening modulus")
    history = [float(value) for value in bench["displacement_history_mm"]]
    u_max = max(abs(value) for value in history)
    yield_strain = yield_stress / young
    yield_displacement = yield_strain * length
    yield_force = yield_stress * area
    subincrements = 100000
    plastic_strain = 0.0
    accumulated_plastic_strain = 0.0
    prior_u = history[0]
    prior_force = 0.0
    total_work = 0.0
    cycle_energy = 0.0
    initial_loading_work = 0.0
    final_stress = 0.0
    for segment_index, (start, target) in enumerate(zip(history, history[1:])):
        for index in range(1, subincrements + 1):
            displacement = start + (target - start) * index / subincrements
            strain = displacement / length
            trial_stress = young * (strain - plastic_strain)
            radius = yield_stress + hardening * accumulated_plastic_strain
            yield_function = abs(trial_stress) - radius
            if yield_function > 0.0:
                delta_gamma = yield_function / (young + hardening)
                sign = 1.0 if trial_stress >= 0.0 else -1.0
                plastic_strain += delta_gamma * sign
                accumulated_plastic_strain += delta_gamma
                final_stress = trial_stress - young * delta_gamma * sign
            else:
                final_stress = trial_stress
            force = final_stress * area
            increment_work = 0.5 * (prior_force + force) * (displacement - prior_u)
            total_work += increment_work
            if segment_index == 0:
                initial_loading_work += increment_work
            else:
                cycle_energy += increment_work
            prior_u = displacement
            prior_force = force
    return {
        "length_mm": length,
        "area_mm2": area,
        "young_modulus_mpa": young,
        "yield_stress_mpa": yield_stress,
        "yield_strain": yield_strain,
        "yield_displacement_mm": yield_displacement,
        "yield_force_n": yield_force,
        "plastic_hardening_modulus_mpa": hardening,
        "maximum_displacement_magnitude_mm": u_max,
        "closed_cycle_dissipation_n_mm": cycle_energy,
        "initial_loading_work_n_mm": initial_loading_work,
        "return_map_subincrements_per_segment": subincrements,
        "final_accumulated_plastic_strain": accumulated_plastic_strain,
        "final_signed_plastic_strain": plastic_strain,
        "final_stress_mpa": final_stress,
        "total_history_work_n_mm": total_work,
    }


def close_enough(actual: float, expected: float, relative_tolerance: float = 1.0e-12) -> bool:
    return abs(actual - expected) <= relative_tolerance * max(abs(expected), 1.0)


def make_deck(job: str, element_count: int, bench: dict[str, Any]) -> str:
    length = float(bench["geometry"]["length_mm"])
    area = float(bench["geometry"]["area_mm2"])
    young = float(bench["material"]["young_modulus_mpa"])
    poisson = float(bench["material"]["poisson_ratio"])
    plastic_table = bench["material"]["plastic_table"]
    increment = bench["static_increment"]
    targets = [float(value) for value in bench["step_target_displacements_mm"]]
    node_count = element_count + 1
    lines = [
        "*HEADING",
        f"V10X independent cyclic plasticity T3D2 benchmark: {job}",
        "*NODE,NSET=ALL",
    ]
    for index in range(node_count):
        x = length * index / element_count
        lines.append(f"{index + 1},{x:.12f},0.0,0.0")
    lines.append("*ELEMENT,TYPE=T3D2,ELSET=BAR")
    for index in range(element_count):
        lines.append(f"{index + 1},{index + 1},{index + 2}")
    lines.extend(
        [
            "*NSET,NSET=BASE",
            "1",
            "*NSET,NSET=TIP",
            str(node_count),
            "*MATERIAL,NAME=GENERIC_PERFECT_PLASTIC",
            "*ELASTIC",
            f"{young:.12f},{poisson:.12f}",
            "*PLASTIC",
        ]
    )
    for row in plastic_table:
        lines.append(f"{float(row['true_stress_mpa']):.12f},{float(row['equivalent_plastic_strain']):.12f}")
    lines.extend(
        [
            "*SOLID SECTION,ELSET=BAR,MATERIAL=GENERIC_PERFECT_PLASTIC",
            f"{area:.12f}",
        ]
    )
    for step_index, target in enumerate(targets, start=1):
        lines.extend(
            [
                f"*STEP,INC={int(increment['maximum_increments'])}",
                "*STATIC",
                (
                    f"{float(increment['initial']):.12g},{float(increment['step_time']):.12g},"
                    f"{float(increment['minimum']):.12g},{float(increment['maximum']):.12g}"
                ),
                "*BOUNDARY",
                "ALL,2,3,0.0",
                "BASE,1,1,0.0",
                f"TIP,1,1,{target:.12f}",
                "*NODE FILE",
                "U,RF",
                "*NODE PRINT,NSET=TIP,FREQUENCY=1",
                "U",
                "*NODE PRINT,NSET=BASE,TOTALS=ONLY,FREQUENCY=1",
                "RF",
                "*NODE PRINT,NSET=TIP,TOTALS=ONLY,FREQUENCY=1",
                "RF",
                "*END STEP",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def numeric_tokens(line: str) -> list[float] | None:
    stripped = line.strip()
    if not stripped or not re.fullmatch(r"[-+0-9.Ee\s]+", stripped):
        return None
    try:
        values = [float(token) for token in NUMBER.findall(stripped)]
    except ValueError:
        return None
    return values or None


def next_numeric(lines: list[str], start: int) -> list[float] | None:
    for line in lines[start : min(start + 12, len(lines))]:
        values = numeric_tokens(line)
        if values:
            return values
    return None


def parse_dat(path: Path, tip_node: int) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    current_step = 0
    records: list[dict[str, Any]] = []
    header_count = 0
    for index, line in enumerate(lines):
        step_match = STEP_HEADER.search(line)
        if step_match:
            current_step = int(step_match.group(1))
            continue
        header = DAT_HEADER.match(line)
        if not header:
            continue
        header_count += 1
        values = next_numeric(lines, index + 1)
        if values is None:
            continue
        kind = header.group(1).lower()
        set_name = header.group(2).upper()
        step_time = float(header.group(3))
        if kind.startswith("displacement") and set_name == "TIP":
            if len(values) >= 4 and int(round(values[0])) == tip_node:
                records.append(
                    {
                        "sequence": len(records) + 1,
                        "step": current_step,
                        "step_time": step_time,
                        "tip_u1_mm": float(values[1]),
                        "base_rf1_n": None,
                        "tip_rf1_n": None,
                    }
                )
        elif records and set_name in ("BASE", "TIP") and len(values) >= 3:
            records[-1][f"{set_name.lower()}_rf1_n"] = float(values[-3])
    complete = [
        row
        for row in records
        if row["base_rf1_n"] is not None and row["tip_rf1_n"] is not None
    ]
    return {
        "line_count": len(lines),
        "header_count": header_count,
        "record_count": len(records),
        "complete_record_count": len(complete),
        "step_ids": sorted({int(row["step"]) for row in records}),
        "records": records,
    }


def add_analytical_path(records: list[dict[str, Any]], bench: dict[str, Any]) -> None:
    length = float(bench["geometry"]["length_mm"])
    area = float(bench["geometry"]["area_mm2"])
    young = float(bench["material"]["young_modulus_mpa"])
    yield_stress = float(bench["material"]["yield_stress_mpa"])
    hardening = float(bench["material"]["plastic_hardening_modulus_mpa"])
    plastic_strain = 0.0
    accumulated_plastic_strain = 0.0
    prior_u = 0.0
    prior_solver_force = 0.0
    prior_analytical_force = 0.0
    for row in records:
        displacement = float(row["tip_u1_mm"])
        strain = displacement / length
        trial_stress = young * (strain - plastic_strain)
        current_yield_stress = yield_stress + hardening * accumulated_plastic_strain
        yield_function = abs(trial_stress) - current_yield_stress
        if yield_function > 0.0:
            delta_gamma = yield_function / (young + hardening)
            sign = 1.0 if trial_stress >= 0.0 else -1.0
            plastic_strain += delta_gamma * sign
            accumulated_plastic_strain += delta_gamma
            analytical_stress = trial_stress - young * delta_gamma * sign
        else:
            delta_gamma = 0.0
            analytical_stress = trial_stress
        if delta_gamma > 0.0 and analytical_stress >= 0.0:
            state = "TENSION_PLASTIC"
        elif delta_gamma > 0.0:
            state = "COMPRESSION_PLASTIC"
        else:
            state = "ELASTIC_OR_YIELD_BOUNDARY"
        analytical_force = analytical_stress * area
        solver_force = float(row["tip_rf1_n"]) if row["tip_rf1_n"] is not None else math.nan
        base_force = float(row["base_rf1_n"]) if row["base_rf1_n"] is not None else math.nan
        force_error = abs(solver_force - analytical_force)
        equilibrium = abs(base_force + solver_force) / max(abs(base_force), abs(solver_force), 1.0)
        delta_u = displacement - prior_u
        row.update(
            {
                "analytical_stress_mpa": analytical_stress,
                "analytical_tip_force_n": analytical_force,
                "analytical_plastic_strain": plastic_strain,
                "analytical_accumulated_plastic_strain": accumulated_plastic_strain,
                "analytical_current_yield_stress_mpa": yield_stress + hardening * accumulated_plastic_strain,
                "analytical_state": state,
                "force_absolute_error_n": force_error,
                "force_error_over_yield_force": force_error / (yield_stress * area),
                "equilibrium_relative_residual": equilibrium,
                "solver_incremental_work_n_mm": 0.5 * (prior_solver_force + solver_force) * delta_u,
                "analytical_incremental_work_n_mm": 0.5 * (prior_analytical_force + analytical_force) * delta_u,
            }
        )
        prior_u = displacement
        prior_solver_force = solver_force
        prior_analytical_force = analytical_force


def integrate_path(records: list[dict[str, Any]], force_field: str) -> float:
    if len(records) < 2:
        return 0.0
    total = 0.0
    for previous, current in zip(records, records[1:]):
        total += 0.5 * (float(previous[force_field]) + float(current[force_field])) * (
            float(current["tip_u1_mm"]) - float(previous["tip_u1_mm"])
        )
    return total


def percent_change(current: float, previous: float) -> float:
    return 100.0 * abs(current - previous) / max(abs(current), 1.0e-30)


def create_plot(path: Path, curve_rows: list[dict[str, Any]], reference: dict[str, float]) -> None:
    meshes = sorted({int(row["element_count"]) for row in curve_rows})
    width, height = 1000.0, 660.0
    left, right, top, bottom = 105.0, 35.0, 65.0, 90.0
    plot_width = width - left - right
    plot_height = height - top - bottom
    x_min, x_max = -2.75, 2.75
    y_min, y_max = -30.0, 30.0

    def sx(value: float) -> float:
        return left + (value - x_min) * plot_width / (x_max - x_min)

    def sy(value: float) -> float:
        return top + (y_max - value) * plot_height / (y_max - y_min)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#202124}.tick{font-size:13px}.label{font-size:16px}.legend{font-size:13px}.title{font-size:21px;font-weight:600}</style>',
        f'<text x="{width / 2:.1f}" y="32" text-anchor="middle" class="title">V10X — boucle force-déplacement du barreau générique</text>',
    ]
    for x_tick in [-2.5, -1.25, 0.0, 1.25, 2.5]:
        x = sx(x_tick)
        svg.append(f'<line x1="{x:.2f}" y1="{top:.2f}" x2="{x:.2f}" y2="{top + plot_height:.2f}" stroke="#dddddd" stroke-width="1"/>')
        svg.append(f'<text x="{x:.2f}" y="{top + plot_height + 24:.2f}" text-anchor="middle" class="tick">{x_tick:g}</text>')
    for y_tick in [-25.0, -12.5, 0.0, 12.5, 25.0]:
        y = sy(y_tick)
        svg.append(f'<line x1="{left:.2f}" y1="{y:.2f}" x2="{left + plot_width:.2f}" y2="{y:.2f}" stroke="#dddddd" stroke-width="1"/>')
        svg.append(f'<text x="{left - 12:.2f}" y="{y + 5:.2f}" text-anchor="end" class="tick">{y_tick:g}</text>')
    svg.extend(
        [
            f'<rect x="{left:.2f}" y="{top:.2f}" width="{plot_width:.2f}" height="{plot_height:.2f}" fill="none" stroke="#444444" stroke-width="1.2"/>',
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 28:.2f}" text-anchor="middle" class="label">Déplacement imposé à l’extrémité (mm)</text>',
            f'<text x="28" y="{top + plot_height / 2:.2f}" text-anchor="middle" class="label" transform="rotate(-90 28 {top + plot_height / 2:.2f})">Réaction à l’extrémité (kN)</text>',
        ]
    )
    yield_kn = float(reference["yield_force_n"]) / 1000.0
    for signed_yield in (-yield_kn, yield_kn):
        svg.append(
            f'<line x1="{left:.2f}" y1="{sy(signed_yield):.2f}" x2="{left + plot_width:.2f}" y2="{sy(signed_yield):.2f}" stroke="#777777" stroke-width="1" stroke-dasharray="3 5"/>'
        )
    colours = ["#1565c0", "#ef6c00", "#2e7d32", "#8e24aa"]
    legend_x = left + 14.0
    legend_y = top + 22.0
    for index, mesh in enumerate(meshes):
        rows = [row for row in curve_rows if int(row["element_count"]) == mesh]
        points = " ".join(
            f"{sx(float(row['tip_u1_mm'])):.2f},{sy(float(row['tip_rf1_n']) / 1000.0):.2f}"
            for row in rows
        )
        colour = colours[index % len(colours)]
        svg.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="2" stroke-linejoin="round"/>')
        y = legend_y + 20.0 * index
        svg.append(f'<line x1="{legend_x:.1f}" y1="{y:.1f}" x2="{legend_x + 28:.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="2"/>')
        svg.append(f'<text x="{legend_x + 36:.1f}" y="{y + 4:.1f}" class="legend">CalculiX — {mesh} éléments</text>')
    finest = max(meshes)
    analytical = [row for row in curve_rows if int(row["element_count"]) == finest]
    analytical_points = " ".join(
        f"{sx(float(row['tip_u1_mm'])):.2f},{sy(float(row['analytical_tip_force_n']) / 1000.0):.2f}"
        for row in analytical
    )
    analytical_legend_y = legend_y + 20.0 * len(meshes)
    svg.extend(
        [
            f'<polyline points="{analytical_points}" fill="none" stroke="#111111" stroke-width="1.5" stroke-dasharray="8 5"/>',
            f'<line x1="{legend_x:.1f}" y1="{analytical_legend_y:.1f}" x2="{legend_x + 28:.1f}" y2="{analytical_legend_y:.1f}" stroke="#111111" stroke-width="1.5" stroke-dasharray="8 5"/>',
            f'<text x="{legend_x + 36:.1f}" y="{analytical_legend_y + 4:.1f}" class="legend">Référence analytique</text>',
            '</svg>',
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def run_job(
    ccx: Path,
    run_dir: Path,
    element_count: int,
    bench: dict[str, Any],
    acceptance: dict[str, Any],
    reference: dict[str, float],
    timeout_seconds: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    job = f"v10x_cyclic_{element_count:03d}"
    input_path = run_dir / f"{job}.inp"
    input_path.write_text(make_deck(job, element_count, bench), encoding="ascii", newline="\n")
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
    parsed = parse_dat(dat_path, element_count + 1) if dat_path.is_file() else {
        "line_count": 0,
        "header_count": 0,
        "record_count": 0,
        "complete_record_count": 0,
        "step_ids": [],
        "records": [],
    }
    records = parsed.pop("records")
    add_analytical_path(records, bench)
    for row in records:
        row.update({"job": job, "element_count": element_count, "node_count": element_count + 1})

    targets = [float(value) for value in bench["step_target_displacements_mm"]]
    endpoint_rows = []
    for step, target in enumerate(targets, start=1):
        step_rows = [row for row in records if int(row["step"]) == step]
        endpoint = step_rows[-1] if step_rows else None
        endpoint_rows.append(
            {
                "step": step,
                "target_mm": target,
                "actual_mm": None if endpoint is None else float(endpoint["tip_u1_mm"]),
                "absolute_error_mm": None if endpoint is None else abs(float(endpoint["tip_u1_mm"]) - target),
            }
        )
    max_target_error = max(
        (float(row["absolute_error_mm"]) for row in endpoint_rows if row["absolute_error_mm"] is not None),
        default=math.inf,
    )
    first_peak_candidates = [row for row in records if int(row["step"]) == 1]
    cycle_records = []
    if first_peak_candidates:
        first_peak = first_peak_candidates[-1]
        cycle_records = records[records.index(first_peak) :]
    solver_cycle_energy = integrate_path(cycle_records, "tip_rf1_n")
    sampled_analytical_cycle_energy = integrate_path(cycle_records, "analytical_tip_force_n")
    closed_cycle_energy = float(reference["closed_cycle_dissipation_n_mm"])
    energy_error = abs(solver_cycle_energy - closed_cycle_energy) / closed_cycle_energy
    sampled_energy_error = abs(solver_cycle_energy - sampled_analytical_cycle_energy) / max(
        abs(sampled_analytical_cycle_energy), 1.0
    )
    maximum_force_error = max((float(row["force_absolute_error_n"]) for row in records), default=math.inf)
    maximum_force_relative_error = max(
        (float(row["force_error_over_yield_force"]) for row in records), default=math.inf
    )
    maximum_equilibrium_residual = max(
        (float(row["equilibrium_relative_residual"]) for row in records), default=math.inf
    )
    analytical_pass = (
        return_code == acceptance["solver_return_code"]
        and parsed["complete_record_count"] == parsed["record_count"]
        and parsed["step_ids"] == list(range(1, len(targets) + 1))
        and max_target_error <= acceptance["maximum_target_displacement_absolute_error_mm"]
        and maximum_force_error <= acceptance["maximum_force_absolute_error_n"]
        and maximum_force_relative_error <= acceptance["maximum_force_relative_error"]
        and maximum_equilibrium_residual <= acceptance["maximum_end_reaction_equilibrium_relative_residual"]
        and energy_error <= acceptance["maximum_cycle_energy_relative_error"]
        and solver_cycle_energy > 0.0
    )
    summary = {
        "job": job,
        "element_count": element_count,
        "node_count": element_count + 1,
        "return_code": return_code,
        "timed_out": timed_out,
        "dat_exists": dat_path.is_file(),
        "parsed_record_count": parsed["record_count"],
        "complete_record_count": parsed["complete_record_count"],
        "parsed_step_ids": parsed["step_ids"],
        "maximum_target_displacement_absolute_error_mm": max_target_error,
        "maximum_force_absolute_error_n": maximum_force_error,
        "maximum_force_relative_error": maximum_force_relative_error,
        "maximum_equilibrium_relative_residual": maximum_equilibrium_residual,
        "solver_closed_cycle_work_n_mm": solver_cycle_energy,
        "sampled_analytical_closed_cycle_work_n_mm": sampled_analytical_cycle_energy,
        "analytical_reference_cycle_dissipation_n_mm": closed_cycle_energy,
        "cycle_energy_relative_error": energy_error,
        "sampled_curve_energy_relative_error": sampled_energy_error,
        "positive_dissipation": solver_cycle_energy > 0.0,
        "endpoint_audit": endpoint_rows,
        "parse_summary": parsed,
        "return_code_pass": return_code == acceptance["solver_return_code"],
        "analytical_pass": analytical_pass,
        "runtime_seconds": runtime,
        "input_path": rel(input_path),
        "dat_path": rel(dat_path),
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-3000:],
    }
    return summary, records


def main() -> None:
    started_at = now_local()
    wall_start = time.perf_counter()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("iteration") != "V10X":
        raise ValueError("Configuration iteration must be V10X")
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
        "mesh_case_count": len(bench["mesh_element_counts"]),
        "step_count_per_job": len(bench["step_target_displacements_mm"]),
    }
    mismatches = {
        key: {"expected": expected[key], "actual": actual}
        for key, actual in count_checks.items()
        if expected[key] != actual
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
    declared_reference = bench["predeclared_analytical_reference"]
    reference_checks = {
        "declared_area": close_enough(reference["area_mm2"], float(bench["geometry"]["area_mm2"])),
        "yield_displacement": close_enough(reference["yield_displacement_mm"], float(declared_reference["yield_displacement_mm"])),
        "yield_force": close_enough(reference["yield_force_n"], float(declared_reference["initial_yield_force_n"])),
        "hardening_modulus": close_enough(reference["plastic_hardening_modulus_mpa"], 1000.0),
        "closed_cycle_dissipation": close_enough(
            reference["closed_cycle_dissipation_n_mm"],
            float(declared_reference["closed_cycle_dissipation_n_mm"]),
            relative_tolerance=1.0e-9,
        ),
        "initial_loading_work": close_enough(
            reference["initial_loading_work_n_mm"],
            float(declared_reference["initial_loading_work_n_mm"]),
            relative_tolerance=1.0e-9,
        ),
    }
    if not all(reference_checks.values()):
        raise RuntimeError(f"Analytical reference mismatch: {reference_checks}")

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
    version_text = version_query.stdout + "\n" + version_query.stderr
    version_match = re.search(r"Version\s+([0-9.]+)", version_text, re.IGNORECASE)
    detected_version = version_match.group(1) if version_match else None
    version_pass = detected_version == ccx_entry["expected_version"]
    if not version_pass:
        raise RuntimeError(f"CalculiX version mismatch: {detected_version}")

    run_dir.mkdir(parents=True, exist_ok=False)
    summaries: list[dict[str, Any]] = []
    curve_rows: list[dict[str, Any]] = []
    maximum_runtime = float(config["execution_policy"]["maximum_runtime_seconds"])
    for raw_count in bench["mesh_element_counts"]:
        remaining = maximum_runtime - (time.perf_counter() - wall_start)
        summary, records = run_job(
            ccx,
            run_dir,
            int(raw_count),
            bench,
            acceptance,
            reference,
            min(60.0, remaining),
        )
        summaries.append(summary)
        curve_rows.extend(records)
    if len(summaries) != expected["unique_solver_job_count"]:
        raise RuntimeError(f"Expected {expected['unique_solver_job_count']} jobs, got {len(summaries)}")

    ordered = sorted(summaries, key=lambda row: int(row["element_count"]))
    force_mesh_change = percent_change(
        float(ordered[-1]["maximum_force_absolute_error_n"]),
        float(ordered[-2]["maximum_force_absolute_error_n"]),
    ) if max(float(ordered[-1]["maximum_force_absolute_error_n"]), float(ordered[-2]["maximum_force_absolute_error_n"])) > 1.0e-12 else 0.0
    peak_force_mesh_change = percent_change(
        max(abs(float(row["tip_rf1_n"])) for row in curve_rows if int(row["element_count"]) == int(ordered[-1]["element_count"])),
        max(abs(float(row["tip_rf1_n"])) for row in curve_rows if int(row["element_count"]) == int(ordered[-2]["element_count"])),
    )
    energy_mesh_change = percent_change(
        float(ordered[-1]["solver_closed_cycle_work_n_mm"]),
        float(ordered[-2]["solver_closed_cycle_work_n_mm"]),
    )

    create_plot(resolve_path(outputs["plot"]), curve_rows, reference)

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
    return_pass_count = sum(bool(row["return_code_pass"]) for row in summaries)
    analytical_pass_count = sum(bool(row["analytical_pass"]) for row in summaries)

    criteria = {
        "predeclared_input_hashes": all(row["hash_match"] for row in file_checks),
        "protected_master_unchanged": protected_unchanged,
        "calculix_version": version_pass,
        "solver_return_codes": return_pass_count == expected["solver_return_code_pass_count"],
        "all_five_steps_parsed": all(row["parsed_step_ids"] == [1, 2, 3, 4, 5] for row in summaries),
        "all_records_complete": all(row["parsed_record_count"] == row["complete_record_count"] for row in summaries),
        "analytical_force_and_energy": analytical_pass_count == expected["analytical_job_pass_count"],
        "positive_cycle_dissipation": all(bool(row["positive_dissipation"]) for row in summaries),
        "finest_pair_peak_force_mesh_invariance": peak_force_mesh_change <= acceptance["maximum_finest_pair_force_change_pct"],
        "finest_pair_cycle_energy_mesh_invariance": energy_mesh_change <= acceptance["maximum_finest_pair_cycle_energy_change_pct"],
        "input_deck_count": input_deck_count == expected["input_deck_count"],
        "all_solver_files_hashed": all_run_files_hashed,
        "wtc_mechanical_requirement_closure_count_zero": acceptance["wtc_mechanical_requirement_closure_count"] == 0,
        "physical_wtc_release_count_zero": acceptance["physical_wtc_state_release_count"] == 0,
        "historical_outcome_assignment_count_zero": acceptance["historical_outcome_assignment_count"] == 0,
    }
    decision = (
        "PASS_INDEPENDENT_CALCULIX_T3D2_CYCLIC_PLASTICITY_BENCHMARK"
        if all(criteria.values())
        else "FAIL_INDEPENDENT_CALCULIX_T3D2_CYCLIC_PLASTICITY_BENCHMARK"
    )

    regression_payload = {
        "iteration": "V10X",
        "created_at": now_local(),
        "decision": "PASS" if all(row["hash_match"] for row in file_checks) and protected_unchanged else "FAIL",
        "file_checks": file_checks,
        "protected_master_sha256_after": protected_after,
    }
    source_manifest = {
        "iteration": "V10X",
        "created_at": now_local(),
        "configuration": {"path": rel(CONFIG_PATH), "sha256": sha256(CONFIG_PATH)},
        "runner": {"path": rel(Path(__file__)), "sha256": sha256(Path(__file__))},
        "design_sources": config["design_research"]["sources"],
        "software_reference_checks": [row for row in file_checks if row["group"] == "software_reference"],
        "epistemic_status": "Software and analytical benchmark sources only; zero WTC physical-evidence credit.",
    }
    execution_log = {
        "iteration": "V10X",
        "started_at": started_at,
        "finished_at": now_local(),
        "wall_runtime_seconds": time.perf_counter() - wall_start,
        "solver": {"path": rel(ccx), "version": detected_version, "version_pass": version_pass},
        "jobs": summaries,
        "counts": {
            "structural_solver_runs": len(summaries),
            "heat_transfer_runs": 0,
            "fire_runs": 0,
            "impact_runs": 0,
            "propagation_runs": 0,
            "gpu_runs": 0,
            "blender_runs": 0,
        },
    }
    gate = {
        "iteration": "V10X",
        "created_at": now_local(),
        "decision": decision,
        "criteria": criteria,
        "metrics": {
            "solver_job_count": len(summaries),
            "solver_return_code_pass_count": return_pass_count,
            "analytical_job_pass_count": analytical_pass_count,
            "maximum_force_absolute_error_n": max(float(row["maximum_force_absolute_error_n"]) for row in summaries),
            "maximum_force_relative_error": max(float(row["maximum_force_relative_error"]) for row in summaries),
            "maximum_cycle_energy_relative_error": max(float(row["cycle_energy_relative_error"]) for row in summaries),
            "maximum_equilibrium_relative_residual": max(float(row["maximum_equilibrium_relative_residual"]) for row in summaries),
            "finest_pair_peak_force_change_pct": peak_force_mesh_change,
            "finest_pair_cycle_energy_change_pct": energy_mesh_change,
            "diagnostic_finest_pair_force_error_change_pct": force_mesh_change,
            "high_resolution_reference_cycle_dissipation_n_mm": reference["closed_cycle_dissipation_n_mm"],
            "mechanical_requirement_closed_count": 0,
            "physical_wtc_state_release_count": 0,
            "historical_outcome_assignment_count": 0,
        },
        "allowed_claim": "CalculiX 2.22 reproduces this generic axial elastoplastic loading-unloading benchmark within the predeclared numerical tolerances.",
        "forbidden_claims": [
            "The benchmark validates any WTC 1 steel, connection, impact, fire, initiation or propagation model.",
            "The benchmark shows that WTC 1 must collapse or must arrest.",
            "The hysteresis curve is a measured WTC material law."
        ],
    }
    results = {
        "iteration": "V10X",
        "decision": decision,
        "scope": config["dataset"]["scope"],
        "analytical_reference": reference,
        "mesh_summaries": summaries,
        "mesh_invariance": {
            "finest_mesh_element_count": int(ordered[-1]["element_count"]),
            "previous_mesh_element_count": int(ordered[-2]["element_count"]),
            "peak_force_change_pct": peak_force_mesh_change,
            "cycle_energy_change_pct": energy_mesh_change,
        },
        "epistemic_accounting": {
            "directly_observed_or_transcribed_facts": [],
            "official_model_results": [],
            "local_archive_claims": [],
            "model_hypotheses": [
                "A generic 1000 mm by 100 mm2 axial bar is represented by T3D2 elements.",
                "The material is rate-independent elastoplastic with E=200000 MPa, initial yield stress 250 MPa and linear isotropic hardening H=1000 MPa.",
                "The prescribed displacement history is synthetic and has no WTC attribution."
            ],
            "derived_results": [
                f"Analytical yield displacement: {reference['yield_displacement_mm']:.6f} mm.",
                f"Analytical yield force: {reference['yield_force_n']:.3f} N.",
                f"Analytical closed-cycle dissipation: {reference['closed_cycle_dissipation_n_mm']:.3f} N mm."
            ],
            "contradictions_and_missing_information": [
                "No WTC-specific cyclic material curve, temperature dependence, strain-rate dependence, fracture, connection or geometric instability is tested here.",
                "A T3D2 axial bar cannot represent bending, local buckling, fracture or progressive floor-system failure."
            ]
        },
        "next_iteration": config["next_iteration"],
    }

    write_json(resolve_path(outputs["regression_audit"]), regression_payload)
    write_json(resolve_path(outputs["source_manifest"]), source_manifest)
    write_json(resolve_path(outputs["analytical_reference"]), reference)
    write_csv(
        resolve_path(outputs["response_curve"]),
        [
            "job", "element_count", "node_count", "sequence", "step", "step_time", "tip_u1_mm",
            "base_rf1_n", "tip_rf1_n", "analytical_tip_force_n", "analytical_stress_mpa",
            "analytical_plastic_strain", "analytical_accumulated_plastic_strain",
            "analytical_current_yield_stress_mpa", "analytical_state", "force_absolute_error_n",
            "force_error_over_yield_force", "equilibrium_relative_residual",
            "solver_incremental_work_n_mm", "analytical_incremental_work_n_mm"
        ],
        curve_rows,
    )
    write_csv(
        resolve_path(outputs["summary"]),
        [
            "job", "element_count", "node_count", "return_code", "parsed_record_count",
            "complete_record_count", "maximum_target_displacement_absolute_error_mm",
            "maximum_force_absolute_error_n", "maximum_force_relative_error",
            "maximum_equilibrium_relative_residual", "solver_closed_cycle_work_n_mm",
            "sampled_analytical_closed_cycle_work_n_mm", "analytical_reference_cycle_dissipation_n_mm",
            "cycle_energy_relative_error", "sampled_curve_energy_relative_error",
            "positive_dissipation", "analytical_pass", "runtime_seconds"
        ],
        summaries,
    )
    write_json(resolve_path(outputs["solver_execution_log"]), execution_log)
    write_csv(
        resolve_path(outputs["solver_file_manifest"]),
        ["path", "job", "suffix", "classification", "size_bytes", "sha256"],
        manifest_rows,
    )
    write_json(resolve_path(outputs["handoff_gate"]), gate)
    write_json(resolve_path(outputs["results"]), results)

    report_lines = [
        "# WTC 1 — V10X — benchmark indépendant de plasticité cyclique",
        "",
        f"**Décision : `{decision}`**",
        "",
        "## Résultat utile",
        "",
        "Ce benchmark vérifie uniquement que CalculiX 2.22 reproduit le chargement, la plastification, le déchargement, l'inversion et la dissipation d'un barreau axial générique. Il ne constitue pas encore une simulation du WTC 1.",
        "",
        f"- Force d'écoulement analytique : {reference['yield_force_n'] / 1000.0:.3f} kN.",
        f"- Déplacement d'écoulement analytique : {reference['yield_displacement_mm']:.3f} mm.",
        f"- Dissipation analytique du cycle fermé : {reference['closed_cycle_dissipation_n_mm'] / 1000.0:.3f} J.",
        f"- Erreur de force maximale : {gate['metrics']['maximum_force_absolute_error_n']:.6g} N.",
        f"- Erreur relative maximale d'énergie : {100.0 * gate['metrics']['maximum_cycle_energy_relative_error']:.6g} %.",
        f"- Variation d'énergie entre 8 et 32 éléments : {energy_mesh_change:.6g} %.",
        "",
        "## Résultats par maillage",
        "",
        "| Éléments | Enregistrements | Travail du cycle (J) | Erreur énergie (%) | Erreur force max. (N) | Verdict |",
        "|---:|---:|---:|---:|---:|:---|",
    ]
    for row in ordered:
        report_lines.append(
            f"| {int(row['element_count'])} | {int(row['parsed_record_count'])} | "
            f"{float(row['solver_closed_cycle_work_n_mm']) / 1000.0:.6f} | "
            f"{100.0 * float(row['cycle_energy_relative_error']):.6f} | "
            f"{float(row['maximum_force_absolute_error_n']):.6g} | "
            f"{'PASS' if row['analytical_pass'] else 'FAIL'} |"
        )
    report_lines.extend(
        [
            "",
            "## Statut des preuves",
            "",
            "- Faits/sources : syntaxe du solveur et résultats numériques produits par les quatre calculs locaux.",
            "- Hypothèses du modèle : barreau axial générique, petite déformation, écrouissage isotrope linéaire et indépendance de la vitesse.",
            "- Résultats dérivés : comparaison point par point, équilibre des réactions, aire de la boucle et invariance de maillage.",
            "- Informations manquantes : lois WTC à chaud et à grande vitesse, rupture, assemblages, flambement local et géométrie réelle.",
            "",
            "## Limite de conclusion",
            "",
            "Aucune des 22 exigences mécaniques documentaires WTC 1 n'est déclarée fermée par V10X. Le prochain modèle exploratoire pourra utiliser des plages hypothétiques clairement signalées, mais pas convertir ce test logiciel en validation historique.",
            "",
        ]
    )
    resolve_path(outputs["report"]).write_text("\n".join(report_lines), encoding="utf-8")

    required_output_paths = [
        resolve_path(value)
        for key, value in outputs.items()
        if key not in ("run_directory", "offline_audit")
    ]
    artifact_rows = []
    for path in [CONFIG_PATH, Path(__file__), *required_output_paths, *run_files]:
        artifact_rows.append(
            {
                "path": rel(path),
                "exists": path.is_file(),
                "size_bytes": path.stat().st_size if path.is_file() else None,
                "sha256": sha256(path) if path.is_file() else None,
            }
        )
    offline_audit = {
        "iteration": "V10X",
        "created_at": now_local(),
        "decision": "PASS" if all(row["exists"] and row["sha256"] for row in artifact_rows) else "FAIL",
        "artifact_count": len(artifact_rows),
        "artifacts": artifact_rows,
        "offline_audit_self_excluded": True,
        "source_archive_modified": False,
        "protected_master_unchanged": protected_unchanged,
    }
    write_json(resolve_path(outputs["offline_audit"]), offline_audit)

    print(json.dumps({"iteration": "V10X", "decision": decision, "metrics": gate["metrics"]}, ensure_ascii=False, indent=2))
    if not all(criteria.values()):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
