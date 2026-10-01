#!/usr/bin/env python3
"""Generate deterministic V8W free-flight and facade-contact decks.

V8W preserves the V8V equivalent projectile but replaces its all-projectile
self-contact with two directional, non-conflicting core/cowling contacts.  The
model remains a qualification surrogate, not a JT9D reconstruction.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_v8v_deformable_projectile import (
    ShellMesh,
    add_closed_box,
    add_facade,
    add_open_cowling,
    chunks,
    fixed_fields,
    material_lines,
    shell_property_lines,
    type7_lines,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def write_starter(config: dict, case: dict, output: Path) -> dict:
    phase = str(case["phase"])
    projectile_mesh = float(case["projectile_mesh_target_mm"])
    facade_mesh = (
        float(case["facade_mesh_target_mm"])
        if case.get("facade_mesh_target_mm") is not None
        else None
    )
    projectile = config["projectile"]
    core = projectile["engine_core"]
    cowling = projectile["cowling"]
    facade_geometry = config["facade_geometry"]
    mesh = ShellMesh()
    fixed_nodes: set[int] = set()
    if phase == "facade_impact":
        if facade_mesh is None:
            raise ValueError("facade_impact requires facade_mesh_target_mm")
        fixed_nodes = add_facade(mesh, facade_geometry, facade_mesh)
    elif phase != "free_flight":
        raise ValueError(f"Unknown V8W phase: {phase}")

    add_closed_box(
        mesh,
        float(core["width_mm"]),
        float(core["height_mm"]),
        float(core["front_z_mm"]),
        float(core["rear_z_mm"]),
        3,
        projectile_mesh,
    )
    add_open_cowling(mesh, cowling, projectile_mesh)

    core_area = mesh.part_area(3)
    cowling_area = mesh.part_area(4)
    core_thickness = float(core["target_mass_g"]) / (
        float(core["material"]["density_g_per_mm3"]) * core_area
    )
    cowling_thickness = float(cowling["target_mass_g"]) / (
        float(cowling["material"]["density_g_per_mm3"]) * cowling_area
    )
    pair_activation_gap = 0.5 * (core_thickness + cowling_thickness)
    opening_clearance = 0.5 * (
        float(cowling["front_opening_width_mm"]) - float(core["width_mm"])
    )
    net_opening_clearance = opening_clearance - pair_activation_gap
    run_name = f"V8W_{case['id']}"

    lines: list[str] = [
        "#RADIOSS STARTER",
        "# V8W pairwise-contact qualification surrogate; not a WTC impact reconstruction",
        "/BEGIN",
        f"{run_name:<80}",
        f"{2026:10d}{0:10d}",
        fixed_fields("g", "mm", "ms"),
        fixed_fields("g", "mm", "ms"),
        "/TITLE",
        f"{run_name} {phase} pairwise core-cowling qualification",
        "/ANALY",
        f"{0:10d}{'':10s}{0:10d}{0:10d}",
        "/DEF_SHELL",
        f"{0:10d}{0:10d}{0:10d}{0:10d}{0:10d}{'':20s}{0:10d}{0:10d}",
        "/SPMD",
        f"{0:10d}{0:10d}{0:20d}{int(case['threads']):20d}",
    ]
    if phase == "facade_impact":
        lines += material_lines(
            1,
            "NIST-adjacent 60 ksi facade steel; unchanged V8V surrogate",
            config["facade_material"],
            float(config["facade_material"]["failure_plastic_strain"]),
        )
    lines += material_lines(
        2,
        "Equivalent deformable engine-core steel; unchanged V8V hypothesis",
        core["material"],
        float(case["core_failure_strain"]),
    )
    lines += material_lines(
        3,
        "Equivalent deformable cowling aluminum; widened-opening V8W hypothesis",
        cowling["material"],
        float(case["cowling_failure_strain"]),
    )
    lines.append("/NODE")
    for node_id, (x, y, z) in enumerate(mesh.nodes, start=1):
        lines.append(f"{node_id:10d}{x:20.9g}{y:20.9g}{z:20.9g}")

    if phase == "facade_impact":
        lines += [
            "/BCS/1",
            "FIXED_FACADE_COLUMN_ENDS",
            f"{'111':>6}{'111':>4}{0:10d}{10:10d}",
            "/GRNOD/NODE/10",
            "FIXED_FACADE_COLUMN_ENDS",
        ]
        for group in chunks(sorted(fixed_nodes)):
            lines.append("".join(f"{value:10d}" for value in group))

    element_id = 1
    element_ranges: dict[str, dict[str, int]] = {}
    part_specs = []
    if phase == "facade_impact":
        part_specs += [
            (1, "FACADE_COLUMN_SHELLS", 1, 1),
            (2, "FACADE_SPANDREL_SHELLS", 1, 2),
        ]
    part_specs += [
        (3, "DEFORMABLE_ENGINE_CORE_EQUIVALENT", 2, 3),
        (4, "DEFORMABLE_COWLING_EQUIVALENT", 3, 4),
    ]
    for part_id, title, material_id, property_id in part_specs:
        start_id = element_id
        lines += [
            f"/PART/{part_id}",
            title,
            f"{property_id:10d}{material_id:10d}{0:10d}",
            f"/SHELL/{part_id}",
        ]
        for shell in mesh.shells[part_id]:
            lines.append(f"{element_id:10d}" + "".join(f"{node:10d}" for node in shell))
            element_id += 1
        element_ranges[str(part_id)] = {
            "first": start_id,
            "last": element_id - 1,
            "count": len(mesh.shells[part_id]),
        }

    if phase == "facade_impact":
        lines += shell_property_lines(
            1,
            "FACADE_COLUMN_5_16_IN_QEPH",
            float(facade_geometry["column_shell_thickness_mm"]),
        )
        lines += shell_property_lines(
            2,
            "FACADE_SPANDREL_3_8_IN_QEPH",
            float(facade_geometry["spandrel_shell_thickness_mm"]),
        )
    lines += shell_property_lines(3, "ENGINE_CORE_EQUIVALENT_MASS_QEPH", core_thickness)
    lines += shell_property_lines(4, "COWLING_EQUIVALENT_MASS_QEPH", cowling_thickness)
    lines += [
        "/GRNOD/PART/20",
        "ALL_PROJECTILE_NODES",
        f"{3:10d}{4:10d}",
        "/GRNOD/PART/21",
        "CORE_NODES_ONLY",
        f"{3:10d}",
        "/GRNOD/PART/22",
        "COWLING_NODES_ONLY",
        f"{4:10d}",
        "/SURF/PART/31",
        "COWLING_SURFACE_ONLY",
        f"{4:10d}",
        "/SURF/PART/32",
        "CORE_SURFACE_ONLY",
        f"{3:10d}",
        "/INIVEL/TRA/1",
        "PROJECTILE_INITIAL_TRANSLATIONAL_VELOCITY",
        f"{0.0:20g}{0.0:20g}{float(projectile['initial_velocity_z_mm_per_ms']):20g}{20:10d}{0:10d}",
        f"{0.0:20g}{0:10d}",
    ]
    if phase == "facade_impact":
        lines += [
            "/SURF/PART/30",
            "FACADE_SHELL_SURFACE",
            f"{1:10d}{2:10d}",
        ]
        lines += type7_lines(1, "PROJECTILE_TO_FACADE_DEFORMABLE_CONTACT", 20, 30)
    lines += type7_lines(2, "CORE_NODES_TO_COWLING_SURFACE", 21, 31)
    lines += type7_lines(3, "COWLING_NODES_TO_CORE_SURFACE", 22, 32)
    if phase == "facade_impact":
        lines += [
            "/TH/INTER/1",
            "TH_FACADE_CONTACT",
            f"{'FNZ':>10}",
            f"{1:10d}",
        ]
    lines += [
        "/TH/INTER/2",
        "TH_CORE_TO_COWLING_CONTACT",
        f"{'FNZ':>10}",
        f"{2:10d}",
        "/TH/INTER/3",
        "TH_COWLING_TO_CORE_CONTACT",
        f"{'FNZ':>10}",
        f"{3:10d}",
        "/TH/PART/2",
        "TH_PROJECTILE_PARTS",
        "".join(f"{value:>10}" for value in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")),
        f"{3:10d}{4:10d}",
        "/END",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    projectile_nodes = mesh.part_nodes(3) | mesh.part_nodes(4)
    return {
        "run_name": run_name,
        "case_id": case["id"],
        "phase": phase,
        "facade_mesh_target_mm": facade_mesh,
        "projectile_mesh_target_mm": projectile_mesh,
        "time_step_scale": float(case["time_step_scale"]),
        "threads": int(case["threads"]),
        "node_count_total": len(mesh.nodes),
        "shell_count_total": sum(len(values) for values in mesh.shells.values()),
        "fixed_node_count": len(fixed_nodes),
        "projectile_node_count": len(projectile_nodes),
        "element_ranges": element_ranges,
        "projectile": {
            "core_mid_surface_area_mm2": core_area,
            "cowling_mid_surface_area_mm2": cowling_area,
            "core_equivalent_thickness_mm": core_thickness,
            "cowling_equivalent_thickness_mm": cowling_thickness,
            "type7_pair_activation_gap_mm": pair_activation_gap,
            "front_opening_mid_surface_radial_clearance_mm": opening_clearance,
            "front_opening_net_shell_surface_clearance_mm": net_opening_clearance,
            "net_clearance_to_activation_gap_ratio": net_opening_clearance / pair_activation_gap,
            "core_target_mass_g": float(core["target_mass_g"]),
            "cowling_target_mass_g": float(cowling["target_mass_g"]),
            "total_target_mass_g": float(projectile["total_target_mass_g"]),
        },
        "contact_interfaces": {
            "facade": 1 if phase == "facade_impact" else None,
            "core_to_cowling": 2,
            "cowling_to_core": 3,
            "all_projectile_self_contact_present": False,
        },
    }


def write_engine(config: dict, case: dict, output: Path) -> None:
    run_name = f"V8W_{case['id']}"
    execution = config["execution"]
    termination = (
        execution["free_flight_termination_time_ms"]
        if case["phase"] == "free_flight"
        else execution["facade_impact_termination_time_ms"]
    )
    lines = [
        "/ANIM/DT",
        fixed_fields(0, execution["animation_interval_ms"]),
        "/ANIM/SHELL/EPSP/ALL",
        "/ANIM/SHELL/DAMA",
        "/ANIM/ELEM/ENER",
        "/ANIM/VECT/VEL",
        "/ANIM/VECT/DISP",
        "/ANIM/VECT/CONT",
        "/ANIM/GZIP",
        "/DT",
        fixed_fields(case["time_step_scale"], 0),
        "/MON/ON",
        "/PRINT/-100/100",
        f"/RUN/{run_name}/1",
        fixed_fields(termination),
        "/TFILE/4",
        fixed_fields(execution["time_history_interval_ms"]),
        "/VERS/2026",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    case = next((item for item in config["cases"] if item["id"] == args.case_id), None)
    if case is None:
        raise SystemExit(f"Unknown case: {args.case_id}")
    args.output.mkdir(parents=True, exist_ok=True)
    run_name = f"V8W_{case['id']}"
    metadata = write_starter(config, case, args.output / f"{run_name}_0000.rad")
    write_engine(config, case, args.output / f"{run_name}_0001.rad")
    (args.output / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()
