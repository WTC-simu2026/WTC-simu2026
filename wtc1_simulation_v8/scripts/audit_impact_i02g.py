"""Audit one or all IMPACT-I02G M(T) coupon cases from saved histories."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02g_mt_coupon.json"
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02g_mt_coupon"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def finite(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite history value")
    return number


def entity_columns(headers: list[str], title: str, variables_per_entity: int) -> dict[int, list[str]]:
    selected = [header for header in headers if header.startswith(title)]
    grouped: dict[int, list[str]] = {}
    for header in selected:
        match = re.match(re.escape(title) + r"\s+(\d+)\s+", header)
        if not match:
            raise ValueError("Cannot parse entity header: " + header)
        grouped.setdefault(int(match.group(1)), []).append(header)
    for entity_id, columns in grouped.items():
        columns.sort(key=lambda item: int(re.search(r"var\s+(\d+)$", item).group(1)))
        if len(columns) != variables_per_entity:
            raise ValueError(f"Unexpected variable count for {title} {entity_id}: {len(columns)}")
    return grouped


def interpolate(xs: list[float], ys: list[float], target: float) -> float:
    if target <= xs[0]:
        return ys[0]
    if target >= xs[-1]:
        return ys[-1]
    for index in range(len(xs) - 1):
        if xs[index] <= target <= xs[index + 1]:
            fraction = (target - xs[index]) / (xs[index + 1] - xs[index])
            return ys[index] + fraction * (ys[index + 1] - ys[index])
    raise ValueError("Interpolation target not bracketed")


def contiguous_extension(side_pairs: list[dict], off_by_element: dict[int, float]) -> float:
    ordered = sorted(side_pairs, key=lambda pair: abs(pair["x_mm"]))
    extension = 0.0
    for pair in ordered:
        if off_by_element[pair["element_id"]] >= 0.5:
            break
        extension += pair["tributary_width_mm"]
    return extension


def audit_case(directory: Path, cfg: dict) -> dict:
    metadata = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    execution = json.loads((directory / "execution.json").read_text(encoding="utf-8"))
    if len(execution) != 3 or any(record["returncode"] != 0 for record in execution):
        raise ValueError("Incomplete solver execution")
    csv_path = next(directory.glob("*.csv"))
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        seam_columns = entity_columns(headers, "SEAM_HISTORY", 6)
        grip_columns = entity_columns(headers, "UPPER_GRIP_HISTORY", 3)
        node_columns = entity_columns(headers, "SEAM_NODE_HISTORY", 2)
        rows = list(reader)
    if not rows:
        raise ValueError("Empty time history")
    width = float(cfg["geometry"]["width_mm"])
    thickness = float(cfg["geometry"]["thickness_mm"])
    crack_half = float(cfg["geometry"]["initial_total_crack_length_mm"]) / 2.0
    b = thickness
    pairs = metadata["seam_pairs"]
    left_pairs = [pair for pair in pairs if pair["side"] == "left"]
    right_pairs = [pair for pair in pairs if pair["side"] == "right"]
    all_x = [-width / 2.0 + width * index / metadata["mesh"]["nx"] for index in range(metadata["mesh"]["nx"] + 1)]
    lower_nodes = metadata["lower_seam_nodes"]
    upper_nodes = metadata["upper_seam_nodes"]
    states = []
    softening_onset = None
    complete_separation_onset = None
    last_extension = -1.0
    advance_states = []
    peak_stress = -1.0
    peak_state = None
    maximum_residual = 0.0
    maximum_residual_time = 0.0
    maximum_mass_error = 0.0
    expected_mass = float(metadata["expected_mass_g"])
    external_max = max(abs(finite(row["EXTERNAL WORK"])) for row in rows)
    for row in rows:
        time_ms = finite(row["time"])
        internal_mj = finite(row["INTERNAL ENERGY"])
        kinetic_mj = finite(row["KINETIC ENERGY"])
        external_mj = finite(row["EXTERNAL WORK"])
        mass_g = finite(row["MASS"])
        mass_error = abs(mass_g - expected_mass) / expected_mass
        maximum_mass_error = max(maximum_mass_error, mass_error)
        if abs(external_mj) > max(1.0e-9, 0.01 * external_max):
            residual = abs(external_mj - internal_mj - kinetic_mj) / max(abs(external_mj), abs(internal_mj) + abs(kinetic_mj), 1.0e-12)
            if residual > maximum_residual:
                maximum_residual = residual
                maximum_residual_time = time_ms
        upper_grip_reaction_raw_n = abs(sum(finite(row[columns[2]]) for columns in grip_columns.values()))
        grip_displacement_mm = sum(finite(row[columns[0]]) for columns in grip_columns.values()) / len(grip_columns)
        off_by_element = {element_id: finite(row[columns[0]]) for element_id, columns in seam_columns.items()}
        seam_force_n = abs(sum(finite(row[columns[2]]) for columns in seam_columns.values()))
        remote_stress = seam_force_n / (width * thickness)
        left_extension = contiguous_extension(left_pairs, off_by_element)
        right_extension = contiguous_extension(right_pairs, off_by_element)
        extension = 0.5 * (left_extension + right_extension)
        openings = []
        for lower_node, upper_node in zip(lower_nodes, upper_nodes):
            lower_dy = finite(row[node_columns[lower_node][1]])
            upper_dy = finite(row[node_columns[upper_node][1]])
            openings.append(max(0.0, upper_dy - lower_dy))
        opening_by_x = dict(zip(all_x, openings))
        left_tip = -crack_half - left_extension
        right_tip = crack_half + right_extension
        left_open_b = interpolate(all_x, openings, left_tip + b)
        right_open_b = interpolate(all_x, openings, right_tip - b)
        left_open_2b = interpolate(all_x, openings, left_tip + 2.0 * b)
        right_open_2b = interpolate(all_x, openings, right_tip - 2.0 * b)
        ctoa_b = 0.5 * (
            math.degrees(2.0 * math.atan2(left_open_b, 2.0 * b))
            + math.degrees(2.0 * math.atan2(right_open_b, 2.0 * b))
        )
        ctoa_2b = 0.5 * (
            math.degrees(2.0 * math.atan2(left_open_2b, 4.0 * b))
            + math.degrees(2.0 * math.atan2(right_open_2b, 4.0 * b))
        )
        state = {
            "time_ms": time_ms,
            "grip_displacement_mm": grip_displacement_mm,
            "remote_stress_mpa": remote_stress,
            "cohesive_section_force_N": seam_force_n,
            "upper_grip_reaction_raw_sum_N": upper_grip_reaction_raw_n,
            "left_extension_mm": left_extension,
            "right_extension_mm": right_extension,
            "mean_extension_mm": extension,
            "ctoa_B_deg": ctoa_b,
            "ctoa_2B_deg": ctoa_2b,
            "internal_energy_J": internal_mj * 0.001,
            "kinetic_energy_J": kinetic_mj * 0.001,
            "external_work_J": external_mj * 0.001,
        }
        states.append(state)
        if remote_stress > peak_stress:
            peak_stress = remote_stress
            peak_state = state
        fracture_pairs = pairs if metadata["case"]["mode"] == "fracture" else []
        if fracture_pairs and softening_onset is None:
            initiated = []
            for pair in fracture_pairs:
                opening = opening_by_x[pair["x_mm"]]
                if opening >= pair["delta0_mm"]:
                    initiated.append(pair["element_id"])
            if initiated:
                softening_onset = {
                    "time_ms": time_ms,
                    "remote_stress_mpa": remote_stress,
                    "maximum_remote_stress_before_or_at_onset_mpa": max(item["remote_stress_mpa"] for item in states),
                    "initiated_spring_ids": initiated,
                }
        if extension > 0 and complete_separation_onset is None:
            complete_separation_onset = {
                "time_ms": time_ms,
                "remote_stress_mpa": remote_stress,
                "maximum_remote_stress_before_or_at_onset_mpa": max(item["remote_stress_mpa"] for item in states),
                "mean_extension_mm": extension,
            }
        if extension > last_extension + 1.0e-9:
            if extension > 0:
                advance_states.append(state)
            last_extension = extension
    settled = [state for state in advance_states if state["mean_extension_mm"] >= cfg["gates"]["minimum_required_crack_extension_mm_for_ctoa"]]
    final = states[-1]
    section_work_j = 0.001 * sum(
        0.5 * (previous["cohesive_section_force_N"] + current["cohesive_section_force_N"])
        * (current["grip_displacement_mm"] - previous["grip_displacement_mm"])
        for previous, current in zip(states[:-1], states[1:])
    )
    section_work_error = abs(section_work_j - final["external_work_J"]) / max(abs(final["external_work_J"]), 1.0e-12)
    peak_ke_ratio = peak_state["kinetic_energy_J"] / max(peak_state["internal_energy_J"], 1.0e-12)
    starter_out = next(directory.glob("*_0000.out")).read_text(encoding="utf-8", errors="replace")
    engine_out = next(directory.glob("*_0001.out")).read_text(encoding="utf-8", errors="replace")
    result = {
        "case": metadata["case"],
        "normal_termination": "NORMAL TERMINATION" in engine_out and "ERROR TERMINATION" not in engine_out,
        "starter_error_count": len(re.findall(r"ERROR ID", starter_out)),
        "starter_warning_count": len(re.findall(r"WARNING ID", starter_out)),
        "engine_error_count": len(re.findall(r"ERROR ID", engine_out)),
        "engine_warning_count": len(re.findall(r"WARNING ID", engine_out)),
        "history_rows": len(rows),
        "initial_mass_g": finite(rows[0]["MASS"]),
        "expected_mass_g": expected_mass,
        "maximum_mass_error_fraction": maximum_mass_error,
        "peak_remote_stress_mpa": peak_stress,
        "peak_stress_time_ms": peak_state["time_ms"],
        "kinetic_to_internal_at_peak_stress": peak_ke_ratio,
        "maximum_global_energy_residual_fraction": maximum_residual,
        "maximum_global_energy_residual_time_ms": maximum_residual_time,
        "integrated_cohesive_section_work_J": section_work_j,
        "final_external_work_J": final["external_work_J"],
        "section_work_to_external_error_fraction": section_work_error,
        "softening_onset": softening_onset,
        "complete_separation_onset": complete_separation_onset,
        "advance_states": advance_states,
        "settled_ctoa_states": settled,
        "final_state": final,
        "expected_full_ligament_fracture_energy_J": metadata["expected_full_ligament_fracture_energy_J"],
        "final_spring_energy_J": finite(rows[-1]["SPRING ENERGY"]) * 0.001,
        "gates": {
            "normal_termination": "NORMAL TERMINATION" in engine_out and "ERROR TERMINATION" not in engine_out,
            "no_solver_errors": "ERROR ID" not in starter_out and "ERROR ID" not in engine_out,
            "mass": maximum_mass_error <= cfg["gates"]["maximum_initial_mass_error_fraction"],
            "energy": maximum_residual <= cfg["gates"]["maximum_global_energy_residual_fraction"],
            "section_force_work_closure": section_work_error <= cfg["gates"]["maximum_section_work_to_external_error_fraction"],
            "quasi_static_at_peak": peak_ke_ratio <= cfg["gates"]["maximum_kinetic_to_internal_energy_fraction_at_peak_force"],
            "no_propagation_if_control": metadata["case"]["mode"] == "fracture" or final["mean_extension_mm"] == 0,
        },
    }
    result["all_case_gates_pass"] = all(result["gates"].values())
    dump(directory / "case_audit_r2.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir")
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    if args.case_dir:
        directories = [OUTPUT / args.case_dir]
    else:
        directories = sorted(path for path in OUTPUT.iterdir() if (path / "execution.json").exists() and len(json.loads((path / "execution.json").read_text(encoding="utf-8"))) == 3)
    results = [audit_case(directory, cfg) for directory in directories]
    print(json.dumps([
        {
            "case": result["case"]["id"],
            "pass": result["all_case_gates_pass"],
            "peak_MPa": result["peak_remote_stress_mpa"],
            "softening_onset": result["softening_onset"],
            "complete_separation_onset": result["complete_separation_onset"],
            "final_da_mm": result["final_state"]["mean_extension_mm"],
            "final_CTOA_B_deg": result["final_state"]["ctoa_B_deg"],
            "energy_residual": result["maximum_global_energy_residual_fraction"],
        }
        for result in results
    ], indent=2))


if __name__ == "__main__":
    main()
