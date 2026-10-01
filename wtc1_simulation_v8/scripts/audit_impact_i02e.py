"""Audit one saved IMPACT-I02E case from independent solver histories."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

from run_impact_i02c import ROOT, dump


DEFAULT_CFG_PATH = ROOT / "wtc1_simulation_v8/data/impact_i02e_skin_stringer_zone.json"
PART_TITLES = {
    1: "FACADE_COLUMN",
    2: "WING_SKINS",
    3: "WING_SPARS",
    4: "WING_RIBS",
    5: "WING_STRINGER_WEB",
    6: "WING_STRINGER_FREE_FLANGE",
    7: "WING_STRINGER_ATTACH_FLANGE",
}
WING_PARTS = (2, 3, 4, 5, 6, 7)


def find_column(headers: list[str], title: str, variable: str) -> int:
    hits = [index for index, header in enumerate(headers) if title in header and re.search(r"\b" + re.escape(variable) + r"\b", header)]
    if len(hits) != 1:
        raise RuntimeError(f"Ambiguous column {title}/{variable}: {[headers[index] for index in hits]}")
    return hits[0]


def load_config(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "extends" not in raw:
        return raw
    base = load_config(ROOT / raw["extends"])
    merged = json.loads(json.dumps(base))
    for key, value in raw.items():
        if key == "extends":
            continue
        if key == "gates":
            merged["gates"].update(value)
        else:
            merged[key] = value
    return merged


def audit(case_id: str, cfg: dict) -> dict:
    directory = ROOT / cfg["output_root"] / case_id
    meta = json.loads((directory / "generation.json").read_text(encoding="utf-8"))
    case = meta["case"]
    path = directory / f"{meta['name']}T01.csv"
    with path.open(encoding="utf-8-sig", newline="") as stream:
        headers = next(csv.reader(stream))
    values = np.loadtxt(path, delimiter=",", skiprows=1)
    if values.ndim == 1:
        values = values[None, :]
    if values.shape[1] != len(headers):
        raise RuntimeError("Header/data column mismatch")
    time_ms = values[:, 0]

    part_columns = {
        part: {
            variable: find_column(headers, title, variable)
            for variable in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")
        }
        for part, title in PART_TITLES.items()
    }
    contact_hits = [index for index, header in enumerate(headers) if "CONTACT_IMPULSE" in header]
    reaction_columns = [index for index, header in enumerate(headers) if "FIXED_SUPPORT_REACTIONS" in header]
    brick_columns = [index for index, header in enumerate(headers) if "COHESIVE_HISTORY" in header]
    joint_columns = [index for index, header in enumerate(headers) if "JOINT_NODE_HISTORY" in header]

    initial_total = values[0, 1] + values[0, 2] + values[0, 8] + values[0, 11]
    total = values[:, 1] + values[:, 2] + values[:, 8] + values[:, 11]
    external_work = values[:, 9]
    energy_residual = total - initial_total - external_work
    initial_ke_J = values[0, 2] * 0.001
    energy_scale = max(initial_ke_J, float(np.max(np.abs(total))) * 0.001, 1.0e-12)

    initial_global_pz = values[0, 5]
    total_delta_pz = (values[:, 5] - initial_global_pz) * 0.001
    initial_wing_pz = sum(values[0, part_columns[part]["ZMOM"]] for part in WING_PARTS)
    wing_pz = sum(values[:, part_columns[part]["ZMOM"]] for part in WING_PARTS)
    wing_delta_pz = (wing_pz - initial_wing_pz) * 0.001
    if contact_hits:
        contact_impulse = (values[:, contact_hits[0]] - values[0, contact_hits[0]]) * 0.001
    else:
        contact_impulse = np.zeros(len(values))
    reaction_impulse = (
        np.sum(values[:, reaction_columns] - values[0, reaction_columns], axis=1) * 0.001
        if reaction_columns
        else np.zeros(len(values))
    )

    expected_total_mass = sum(meta["expected_shell_mass_g_by_part"].values()) + meta["expected_cohesive_mass_g"]
    initial_mass = values[0, 6]
    wing_shell_mass_history = sum(values[:, part_columns[part]["MASS"]] for part in WING_PARTS)
    facade_mass_history = values[:, part_columns[1]["MASS"]]
    measured_wing_total_mass = initial_mass - facade_mass_history[0]
    wing_shell_ie_J = sum(values[:, part_columns[part]["IE"]] for part in WING_PARTS) * 0.001
    shell_hourglass_J = sum(values[:, part_columns[part]["HE"]] for part in PART_TITLES) * 0.001

    brick = None
    active_fraction = np.ones(len(values))
    joint_work_J = np.zeros(len(values))
    cohesive_force_local_N = np.zeros((len(values), 3))
    any_deleted = False
    all_deleted = False
    no_healing = True
    if meta["bricks"]:
        expected = len(meta["bricks"]) * 8
        if len(brick_columns) != expected:
            raise RuntimeError(f"Expected {expected} cohesive columns, got {len(brick_columns)}")
        brick = values[:, brick_columns].reshape(len(values), len(meta["bricks"]), 8)
        off = brick[:, :, 0]
        areas = np.asarray(meta["brick_areas_mm2"])
        active_fraction = (off @ areas) / areas.sum()
        joint_work_J = brick[:, :, 1].sum(axis=1) * 0.001
        cohesive_force_local_N[:, 0] = brick[:, :, 7] @ areas
        cohesive_force_local_N[:, 1] = brick[:, :, 6] @ areas
        cohesive_force_local_N[:, 2] = brick[:, :, 4] @ areas
        any_deleted = bool(np.any(off == 0))
        all_deleted = bool(np.all(off[-1] == 0))
        no_healing = all(
            not np.any(off[:, element] == 0)
            or np.all(off[np.argmax(off[:, element] == 0) :, element] == 0)
            for element in range(off.shape[1])
        )

    mean_relative_displacement = np.zeros((len(values), 3))
    max_pair_relative_displacement = np.zeros(len(values))
    if joint_columns:
        if len(joint_columns) % 6:
            raise RuntimeError("Joint-node history is not six columns per node")
        raw_joint = values[:, joint_columns].reshape(len(values), len(joint_columns) // 6, 6)
        node_ids = []
        for local_index in range(len(joint_columns) // 6):
            match = re.search(r"JOINT_NODE_HISTORY\s+(\d+)", headers[joint_columns[6 * local_index]])
            if not match:
                raise RuntimeError("Cannot recover joint node ID")
            node_ids.append(int(match.group(1)))
        order = {node_id: index for index, node_id in enumerate(node_ids)}
        bottom = np.asarray([order[node] for node in meta["joint_bottom_nodes"]])
        top = np.asarray([order[node] for node in meta["joint_top_nodes"]])
        relative = raw_joint[:, top, :3] - raw_joint[:, bottom, :3]
        mean_relative_displacement = relative.mean(axis=1)
        max_pair_relative_displacement = np.linalg.norm(relative, axis=2).max(axis=1)

    wing_mass_for_speed = sum(values[:, part_columns[part]["MASS"]] for part in WING_PARTS)
    wing_weighted_vz = sum(
        values[:, part_columns[part]["MASS"]] * values[:, part_columns[part]["VZ"]]
        for part in WING_PARTS
    ) / np.maximum(wing_mass_for_speed, 1.0e-30)
    configured_speed = case.get("speed_m_per_s", cfg["speed"]["m_per_s"])
    free_speed_error = abs(wing_weighted_vz[-1] + configured_speed) / max(abs(configured_speed), 1.0) if not case["contact"] else None

    starter_text = (directory / "starter.log").read_text(encoding="utf-8", errors="replace")
    listing_text = (directory / f"{meta['name']}_0000.out").read_text(encoding="utf-8", errors="replace")
    engine_text = (directory / "engine.log").read_text(encoding="utf-8", errors="replace")
    warning_occurrences = re.findall(r"WARNING ID\s*:\s*(\d+)", starter_text + "\n" + listing_text, flags=re.IGNORECASE)
    warning_ids = sorted(set(warning_occurrences))
    penetration_counts = [int(value) for value in re.findall(r"THERE ARE\s+(\d+)\s+INITIAL PENETRATIONS", listing_text, flags=re.IGNORECASE)]
    cycles = re.findall(r"TOTAL NUMBER OF CYCLES\s*:\s*(\d+)", engine_text)
    facade_nodes = {
        node
        for quad, part in zip(meta["quads"], meta["quad_parts"])
        if part == 1
        for node in quad
    }
    wing_nodes = {
        node
        for quad, part in zip(meta["quads"], meta["quad_parts"])
        if part in WING_PARTS
        for node in quad
    }
    contact_sets_disjoint = not facade_nodes.intersection(wing_nodes)

    contact_abs = abs(contact_impulse[-1])
    wing_delta_abs = abs(wing_delta_pz[-1])
    support_abs = abs(reaction_impulse[-1])
    total_delta_abs = abs(total_delta_pz[-1])
    measured_initial_ke_error = abs(initial_ke_J - meta["expected_initial_wing_ke_J"]) / max(meta["expected_initial_wing_ke_J"], 1.0e-30)
    result = {
        "case": case_id,
        "variant": case["variant"],
        "mesh_mm": case["mesh_mm"],
        "contact": case["contact"],
        "normal_termination": "NORMAL TERMINATION" in engine_text.upper(),
        "warning_ids": warning_ids,
        "warning_occurrences": warning_occurrences,
        "contact_main_secondary_node_sets_disjoint": contact_sets_disjoint,
        "initial_penetration_counts": penetration_counts,
        "history_rows": len(values),
        "last_history_time_ms": float(time_ms[-1]),
        "configured_end_ms": meta["end_ms"],
        "cycles": int(cycles[-1]) if cycles else None,
        "nodes": len(meta["nodes_mm"]),
        "shells": len(meta["quads"]),
        "cohesive_bricks": len(meta["bricks"]),
        "initial_global_mass_g": float(initial_mass),
        "expected_global_mass_g": expected_total_mass,
        "initial_mass_error_fraction": float(abs(initial_mass - expected_total_mass) / expected_total_mass),
        "mass_variation_fraction": float(np.max(abs(values[:, 6] - initial_mass)) / initial_mass),
        "max_dynamic_added_mass_fraction": float(np.max(abs(values[:, 17])) / initial_mass),
        "expected_wing_shell_mass_g": meta["expected_wing_shell_mass_g"],
        "initial_wing_shell_part_mass_g": float(wing_shell_mass_history[0]),
        "measured_wing_total_mass_g": float(measured_wing_total_mass),
        "declared_numerical_connection_mass_g": meta["expected_cohesive_mass_g"],
        "declared_numerical_mass_over_wing_shell_mass": meta["expected_cohesive_mass_g"] / meta["expected_wing_shell_mass_g"],
        "initial_ke_J": float(initial_ke_J),
        "expected_initial_ke_J": meta["expected_initial_wing_ke_J"],
        "initial_ke_error_fraction": float(measured_initial_ke_error),
        "max_abs_energy_error_fraction": float(np.max(abs(energy_residual)) * 0.001 / energy_scale),
        "max_hourglass_over_initial_ke": float(np.max(abs(shell_hourglass_J)) / max(initial_ke_J, 1.0e-30)),
        "final_contact_impulse_abs_Ns": float(contact_abs),
        "final_wing_shell_momentum_change_abs_Ns": float(wing_delta_abs),
        "contact_wing_momentum_error_fraction": float(abs(contact_abs - wing_delta_abs) / max(contact_abs, wing_delta_abs, 1.0)),
        "final_support_reaction_impulse_abs_Ns": float(support_abs),
        "final_total_momentum_change_abs_Ns": float(total_delta_abs),
        "support_total_momentum_error_fraction": float(abs(support_abs - total_delta_abs) / max(support_abs, total_delta_abs, 1.0)),
        "final_mass_weighted_wing_shell_vz_m_per_s": float(wing_weighted_vz[-1]),
        "free_flight_speed_error_fraction": float(free_speed_error) if free_speed_error is not None else None,
        "max_free_flight_internal_energy_over_initial_ke": float(np.max(values[:, 1]) * 0.001 / max(initial_ke_J, 1.0e-30)) if not case["contact"] else None,
        "max_wing_shell_internal_energy_J": float(np.max(wing_shell_ie_J)),
        "final_joint_work_J": float(joint_work_J[-1]),
        "max_joint_work_J": float(np.max(joint_work_J)),
        "final_active_area_fraction": float(active_fraction[-1]),
        "minimum_active_area_fraction": float(np.min(active_fraction)),
        "any_cohesive_deletion": any_deleted,
        "all_cohesive_deleted": all_deleted,
        "cohesive_no_healing": bool(no_healing),
        "peak_cohesive_resultant_N": float(np.max(np.linalg.norm(cohesive_force_local_N, axis=1))),
        "peak_cohesive_normal_abs_N": float(np.max(abs(cohesive_force_local_N[:, 2]))),
        "peak_cohesive_tangential_N": float(np.max(np.linalg.norm(cohesive_force_local_N[:, :2], axis=1))),
        "final_mean_relative_displacement_mm": mean_relative_displacement[-1].tolist(),
        "max_pair_relative_displacement_mm": float(np.max(max_pair_relative_displacement)),
        "max_wing_eroded_shells": float(
            np.max(sum(values[:, part_columns[part]["ERODED"]] for part in WING_PARTS))
        ),
        "execution_seconds": sum(record["seconds"] for record in json.loads((directory / "execution.json").read_text(encoding="utf-8"))),
        "scope": "Local I02A-like bay versus one bounded representative facade column; not a Boeing wing, full WTC1 facade, physical fracture validation or historical conclusion.",
    }

    gate = cfg["gates"]
    checks = {
        "normal_termination": result["normal_termination"],
        "starter_warnings": (
            len(warning_ids) <= gate["max_starter_warnings"]
            or (
                set(warning_ids).issubset(set(gate.get("allowed_disjoint_contact_warning_ids", [])))
                and contact_sets_disjoint
            )
        ),
        "initial_penetrations": max(penetration_counts or [0]) <= gate["max_initial_penetrations"],
        "initial_mass": result["initial_mass_error_fraction"] <= gate["max_mass_relative_error"],
        "mass_preserved": result["mass_variation_fraction"] <= gate["max_mass_variation_fraction"],
        "no_dynamic_mass_scaling": result["max_dynamic_added_mass_fraction"] <= gate["max_added_mass_fraction"],
        "initial_ke": result["initial_ke_error_fraction"] <= gate["max_initial_ke_error_fraction"],
        "global_energy": result["max_abs_energy_error_fraction"] <= gate["max_abs_energy_error_fraction"],
        "hourglass": result["max_hourglass_over_initial_ke"] <= gate["max_hourglass_over_initial_ke"],
        "complete_history": meta["end_ms"] - time_ms[-1] <= 1.1 * cfg["execution"]["history_dt_ms"],
        "wing_shells_not_eroded": result["max_wing_eroded_shells"] == 0,
        "declared_numerical_mass_bounded": result["declared_numerical_mass_over_wing_shell_mass"] <= gate["max_declared_numerical_mass_over_wing_shell_mass"],
        "cohesive_no_healing": result["cohesive_no_healing"],
    }
    if case["contact"]:
        checks.update(
            contact_wing_momentum=result["contact_wing_momentum_error_fraction"] <= gate["max_contact_wing_momentum_error_fraction"],
            support_total_momentum=result["support_total_momentum_error_fraction"] <= gate["max_support_total_momentum_error_fraction"],
            nonzero_contact=result["final_contact_impulse_abs_Ns"] > 0,
        )
    else:
        checks.update(
            free_flight_speed=result["free_flight_speed_error_fraction"] <= gate["max_free_flight_speed_error_fraction"],
            free_flight_internal_energy=result["max_free_flight_internal_energy_over_initial_ke"] <= gate["max_free_flight_internal_energy_over_ke"],
            no_cohesive_deletion=not result["any_cohesive_deletion"],
        )
    if case["variant"] == "unbreakable":
        checks["unbreakable_zone_active"] = result["minimum_active_area_fraction"] >= gate["minimum_unbreakable_active_area_fraction"]
    result["checks"] = {key: bool(value) for key, value in checks.items()}
    result["status"] = "PASS" if all(result["checks"].values()) else "FAIL"
    history = {
        "time_ms": time_ms.tolist(),
        "global_ke_J": (values[:, 2] * 0.001).tolist(),
        "global_ie_J": (values[:, 1] * 0.001).tolist(),
        "global_rotation_J": (values[:, 8] * 0.001).tolist(),
        "global_contact_J": (values[:, 11] * 0.001).tolist(),
        "energy_residual_J": (energy_residual * 0.001).tolist(),
        "contact_impulse_Ns": contact_impulse.tolist(),
        "wing_shell_delta_pz_Ns": wing_delta_pz.tolist(),
        "support_reaction_impulse_Ns": reaction_impulse.tolist(),
        "total_delta_pz_Ns": total_delta_pz.tolist(),
        "joint_work_J": joint_work_J.tolist(),
        "active_area_fraction": active_fraction.tolist(),
        "cohesive_force_local_N": cohesive_force_local_N.tolist(),
        "mean_relative_displacement_mm": mean_relative_displacement.tolist(),
        "max_pair_relative_displacement_mm": max_pair_relative_displacement.tolist(),
    }
    dump(directory / "history.json", history)
    dump(directory / "results.json", result)
    dump(
        directory / "column_map.json",
        {
            "headers": headers,
            "part_columns": part_columns,
            "contact_columns": contact_hits,
            "reaction_columns": reaction_columns,
            "brick_columns": brick_columns,
            "joint_columns": joint_columns,
        },
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--config", type=Path, default=DEFAULT_CFG_PATH)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    result = audit(args.case, load_config(config_path))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
