"""Audit one or all IMPACT-I02H locally refined M(T) coupon cases."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import audit_impact_i02g as i02g_audit


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02h_local_cohesive.json"
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02h_local_cohesive"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def contiguous_extension(side_pairs: list[dict], off_by_element: dict[int, float]) -> float:
    extension = 0.0
    for pair in sorted(side_pairs, key=lambda item: abs(item["x_mm"])):
        if off_by_element[pair["element_id"]] >= 0.5:
            break
        extension += pair["tributary_width_mm"]
    return extension


def audit_case(directory: Path, cfg: dict, allow_partial: bool = False) -> dict:
    metadata = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    execution = json.loads((directory / "execution.json").read_text(encoding="utf-8"))
    if not allow_partial and (len(execution) != 3 or any(record["returncode"] != 0 for record in execution)):
        raise ValueError("Incomplete solver execution")
    csv_path = next(directory.glob("*.csv"))
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = list(reader.fieldnames or [])
        seam_columns = i02g_audit.entity_columns(headers, "SEAM_HISTORY", 6)
        grip_columns = i02g_audit.entity_columns(headers, "UPPER_GRIP_HISTORY", 3)
        node_columns = i02g_audit.entity_columns(headers, "SEAM_NODE_HISTORY", 2)
        rows = list(reader)
    if not rows:
        raise ValueError("Empty time history")

    finite = i02g_audit.finite
    width = float(cfg["geometry"]["width_mm"])
    thickness = float(cfg["geometry"]["thickness_mm"])
    crack_half = float(cfg["geometry"]["initial_total_crack_length_mm"]) / 2.0
    b = thickness
    pairs = metadata["seam_pairs"]
    left_pairs = [pair for pair in pairs if pair["side"] == "left"]
    right_pairs = [pair for pair in pairs if pair["side"] == "right"]
    all_x = metadata["mesh"]["x_coordinates_mm"]
    lower_nodes = metadata["lower_seam_nodes"]
    upper_nodes = metadata["upper_seam_nodes"]

    states: list[dict] = []
    softening_onset = None
    complete_separation_onset = None
    last_extension = -1.0
    advance_states: list[dict] = []
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
        left_open_b = i02g_audit.interpolate(all_x, openings, left_tip + b)
        right_open_b = i02g_audit.interpolate(all_x, openings, right_tip - b)
        left_open_2b = i02g_audit.interpolate(all_x, openings, left_tip + 2.0 * b)
        right_open_2b = i02g_audit.interpolate(all_x, openings, right_tip - 2.0 * b)
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
        if metadata["case"]["mode"] == "fracture" and softening_onset is None:
            initiated = [pair["element_id"] for pair in pairs if opening_by_x[pair["x_mm"]] >= pair["delta0_mm"]]
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

    final = states[-1]
    minimum_ctoa_extension = float(cfg["gates"]["minimum_required_crack_extension_mm_for_ctoa"])
    advance_ctoa_states = [state for state in advance_states if state["mean_extension_mm"] >= minimum_ctoa_extension]
    history_ctoa_states = [state for state in states if state["mean_extension_mm"] >= minimum_ctoa_extension]
    sampled_ctoa_states: list[dict] = []
    for state in history_ctoa_states:
        if not sampled_ctoa_states or state["time_ms"] - sampled_ctoa_states[-1]["time_ms"] >= 0.05:
            sampled_ctoa_states.append(state)

    final_openings = {}
    final_off = {}
    last_row = rows[-1]
    for lower_node, upper_node, x in zip(lower_nodes, upper_nodes, all_x):
        final_openings[x] = max(0.0, finite(last_row[node_columns[upper_node][1]]) - finite(last_row[node_columns[lower_node][1]]))
    for element_id, columns in seam_columns.items():
        final_off[element_id] = finite(last_row[columns[0]])
    final_tip_profile = []
    for pair in sorted(pairs, key=lambda item: abs(item["x_mm"]))[:16]:
        opening = final_openings[pair["x_mm"]]
        if final_off[pair["element_id"]] < 0.5:
            damage = 1.0
        elif pair["deltaf_mm"] is None or opening <= pair["delta0_mm"]:
            damage = 0.0
        else:
            damage = min(1.0, (opening - pair["delta0_mm"]) / (pair["deltaf_mm"] - pair["delta0_mm"]))
        final_tip_profile.append({
            "x_mm": pair["x_mm"],
            "side": pair["side"],
            "opening_mm": opening,
            "active_flag": final_off[pair["element_id"]],
            "damage_fraction_geometric": damage,
        })

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
        "mesh": metadata["mesh"],
        "normal_termination": "NORMAL TERMINATION" in engine_out and "ERROR TERMINATION" not in engine_out,
        "starter_error_count": len(re.findall(r"ERROR ID", starter_out)),
        "starter_warning_count": len(re.findall(r"WARNING ID", starter_out)),
        "engine_error_count": len(re.findall(r"ERROR ID", engine_out)),
        "engine_warning_count": len(re.findall(r"WARNING ID", engine_out)),
        "history_rows": len(rows),
        "execution_seconds_recorded": sum(record["seconds"] for record in execution),
        "partial_history": allow_partial and len(execution) != 3,
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
        "advance_ctoa_states_after_2p3mm": advance_ctoa_states,
        "sampled_ctoa_states_after_2p3mm": sampled_ctoa_states,
        "distinct_extensions_after_2p3mm": sorted(set(state["mean_extension_mm"] for state in advance_ctoa_states)),
        "final_state": final,
        "final_tip_profile": final_tip_profile,
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
    dump(directory / ("partial_diagnostic.json" if allow_partial else "case_audit.json"), result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir")
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    if args.case_dir:
        directories = [OUTPUT / args.case_dir]
    else:
        directories = sorted(path for path in OUTPUT.iterdir() if (path / "execution.json").exists() and len(json.loads((path / "execution.json").read_text(encoding="utf-8"))) == 3)
    results = [audit_case(directory, cfg, args.allow_partial) for directory in directories]
    print(json.dumps([
        {
            "case": result["case"]["id"],
            "pass": result["all_case_gates_pass"],
            "peak_MPa": result["peak_remote_stress_mpa"],
            "complete_separation": result["complete_separation_onset"],
            "advance_count": len(result["advance_states"]),
            "final_extension_mm": result["final_state"]["mean_extension_mm"],
            "ctoa_advance_states_after_2p3mm": len(result["advance_ctoa_states_after_2p3mm"]),
            "seconds_recorded": result["execution_seconds_recorded"],
        }
        for result in results
    ], indent=2))


if __name__ == "__main__":
    main()
