#!/usr/bin/env python3
"""Generate deterministic V8V OpenRadioss deformable-contact decks.

The model is a qualification surrogate.  The projectile is an equivalent-mass
two-part shell assembly, not a geometric or constitutive reconstruction of a
JT9D engine.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def chunks(values: list[int], width: int = 8):
    for start in range(0, len(values), width):
        yield values[start : start + width]


def norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def subtract(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(a[index] - b[index] for index in range(3))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


class ShellMesh:
    def __init__(self) -> None:
        self.nodes: list[tuple[float, float, float]] = []
        self.node_index: dict[tuple[float, float, float], int] = {}
        self.shells: dict[int, list[tuple[int, int, int, int]]] = {1: [], 2: [], 3: [], 4: []}

    def node(self, xyz: tuple[float, float, float]) -> int:
        key = tuple(round(value, 6) for value in xyz)
        if key not in self.node_index:
            self.nodes.append(key)
            self.node_index[key] = len(self.nodes)
        return self.node_index[key]

    def rectangle(
        self,
        origin: tuple[float, float, float],
        uvec: tuple[float, float, float],
        vvec: tuple[float, float, float],
        part: int,
        target_size: float,
    ) -> None:
        nu = max(1, math.ceil(norm(uvec) / target_size))
        nv = max(1, math.ceil(norm(vvec) / target_size))
        grid: list[list[int]] = []
        for j in range(nv + 1):
            row: list[int] = []
            fv = j / nv
            for i in range(nu + 1):
                fu = i / nu
                xyz = tuple(origin[k] + fu * uvec[k] + fv * vvec[k] for k in range(3))
                row.append(self.node(xyz))
            grid.append(row)
        for j in range(nv):
            for i in range(nu):
                self.shells[part].append(
                    (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
                )

    def quad_area(self, shell: tuple[int, int, int, int]) -> float:
        a, b, c, d = (self.nodes[node_id - 1] for node_id in shell)
        area_abc = 0.5 * norm(cross(subtract(b, a), subtract(c, a)))
        area_acd = 0.5 * norm(cross(subtract(c, a), subtract(d, a)))
        return area_abc + area_acd

    def part_area(self, part: int) -> float:
        return sum(self.quad_area(shell) for shell in self.shells[part])

    def part_nodes(self, part: int) -> set[int]:
        return {node for shell in self.shells[part] for node in shell}


def add_facade(mesh: ShellMesh, geometry: dict, target_size: float) -> set[int]:
    centers = [float(value) for value in geometry["column_centers_x_mm"]]
    width = float(geometry["column_width_mm"])
    depth = float(geometry["column_depth_mm"])
    story_height = float(geometry["story_height_mm"])
    total_height = story_height * int(geometry["story_count"])
    panel_width = float(geometry["panel_width_mm"])
    spandrel_height = float(geometry["spandrel_height_mm"])
    spandrel_centers = [float(value) for value in geometry["spandrel_center_y_mm"]]
    facade_nodes_before = len(mesh.nodes)

    y_breaks = {-total_height / 2.0, total_height / 2.0}
    for center_y in spandrel_centers:
        y_breaks.add(center_y - spandrel_height / 2.0)
        y_breaks.add(center_y + spandrel_height / 2.0)
    ordered_y = sorted(y_breaks)

    for center_x in centers:
        x0, x1 = center_x - width / 2.0, center_x + width / 2.0
        for ya, yb in zip(ordered_y[:-1], ordered_y[1:]):
            dy = yb - ya
            mesh.rectangle((x0, ya, 0.0), (width, 0.0, 0.0), (0.0, dy, 0.0), 1, target_size)
            mesh.rectangle((x1, ya, -depth), (-width, 0.0, 0.0), (0.0, dy, 0.0), 1, target_size)
            mesh.rectangle((x0, ya, -depth), (0.0, 0.0, depth), (0.0, dy, 0.0), 1, target_size)
            mesh.rectangle((x1, ya, 0.0), (0.0, 0.0, -depth), (0.0, dy, 0.0), 1, target_size)

    column_intervals = sorted((center - width / 2.0, center + width / 2.0) for center in centers)
    x_segments: list[tuple[float, float]] = []
    cursor = -panel_width / 2.0
    for left, right in column_intervals:
        if left > cursor:
            x_segments.append((cursor, left))
        cursor = max(cursor, right)
    if cursor < panel_width / 2.0:
        x_segments.append((cursor, panel_width / 2.0))
    for center_y in spandrel_centers:
        for xa, xb in x_segments:
            mesh.rectangle(
                (xa, center_y - spandrel_height / 2.0, 0.0),
                (xb - xa, 0.0, 0.0),
                (0.0, spandrel_height, 0.0),
                2,
                target_size,
            )

    facade_node_ids = set(range(facade_nodes_before + 1, len(mesh.nodes) + 1))
    tolerance = 1.0e-5
    return {
        node_id
        for node_id in facade_node_ids
        if abs(abs(mesh.nodes[node_id - 1][1]) - total_height / 2.0) <= tolerance
    }


def add_closed_box(
    mesh: ShellMesh,
    width: float,
    height: float,
    front_z: float,
    rear_z: float,
    part: int,
    target_size: float,
) -> None:
    x0, x1 = -width / 2.0, width / 2.0
    y0, y1 = -height / 2.0, height / 2.0
    length = rear_z - front_z
    mesh.rectangle((x0, y0, front_z), (width, 0.0, 0.0), (0.0, height, 0.0), part, target_size)
    mesh.rectangle((x1, y0, rear_z), (-width, 0.0, 0.0), (0.0, height, 0.0), part, target_size)
    mesh.rectangle((x0, y0, front_z), (0.0, height, 0.0), (0.0, 0.0, length), part, target_size)
    mesh.rectangle((x1, y1, front_z), (0.0, -height, 0.0), (0.0, 0.0, length), part, target_size)
    mesh.rectangle((x1, y0, front_z), (-width, 0.0, 0.0), (0.0, 0.0, length), part, target_size)
    mesh.rectangle((x0, y1, front_z), (width, 0.0, 0.0), (0.0, 0.0, length), part, target_size)


def add_open_cowling(mesh: ShellMesh, cowling: dict, target_size: float) -> None:
    outer_w = float(cowling["outer_width_mm"])
    outer_h = float(cowling["outer_height_mm"])
    inner_w = float(cowling["front_opening_width_mm"])
    inner_h = float(cowling["front_opening_height_mm"])
    front_z = float(cowling["front_z_mm"])
    rear_z = float(cowling["rear_z_mm"])
    length = rear_z - front_z
    x0, x1 = -outer_w / 2.0, outer_w / 2.0
    y0, y1 = -outer_h / 2.0, outer_h / 2.0
    ix0, ix1 = -inner_w / 2.0, inner_w / 2.0
    iy0, iy1 = -inner_h / 2.0, inner_h / 2.0

    mesh.rectangle((x0, y0, front_z), (0.0, outer_h, 0.0), (0.0, 0.0, length), 4, target_size)
    mesh.rectangle((x1, y1, front_z), (0.0, -outer_h, 0.0), (0.0, 0.0, length), 4, target_size)
    mesh.rectangle((x1, y0, front_z), (-outer_w, 0.0, 0.0), (0.0, 0.0, length), 4, target_size)
    mesh.rectangle((x0, y1, front_z), (outer_w, 0.0, 0.0), (0.0, 0.0, length), 4, target_size)
    mesh.rectangle((x0, iy1, front_z), (outer_w, 0.0, 0.0), (0.0, y1 - iy1, 0.0), 4, target_size)
    mesh.rectangle((x1, iy0, front_z), (-outer_w, 0.0, 0.0), (0.0, y0 - iy0, 0.0), 4, target_size)
    mesh.rectangle((x0, iy0, front_z), (ix0 - x0, 0.0, 0.0), (0.0, inner_h, 0.0), 4, target_size)
    mesh.rectangle((x1, iy1, front_z), (ix1 - x1, 0.0, 0.0), (0.0, -inner_h, 0.0), 4, target_size)


def fixed_fields(*values: object, width: int = 20) -> str:
    return "".join(f"{str(value):>{width}}" for value in values)


def material_lines(material_id: int, title: str, material: dict, failure_strain: float) -> list[str]:
    return [
        f"/MAT/PLAS_JOHNS/{material_id}",
        title,
        fixed_fields(material["density_g_per_mm3"], 0),
        f"{float(material['young_modulus_mpa']):20g}{float(material['poisson_ratio']):20g}{1:10d}",
        fixed_fields(
            material["yield_strength_mpa"],
            material["ultimate_tensile_strength_mpa"],
            material["engineering_strain_at_uts"],
            failure_strain,
            0,
        ),
        fixed_fields(
            material["rate_coefficient_c"],
            material["reference_strain_rate_per_ms"],
            1,
            1,
            0,
            0,
        ),
        fixed_fields(0, 0, 0, 0),
    ]


def type7_lines(interface_id: int, title: str, secondary_group: int, main_surface: int) -> list[str]:
    return [
        f"/INTER/TYPE7/{interface_id}",
        title,
        f"{secondary_group:10d}{main_surface:10d}{4:10d}{0:10d}{2:10d}{'':10s}{0:10d}{2:10d}{0:10d}{0:10d}",
        f"{1.0:20g}{0.0:20g}{0.0:20g}{'':20s}{0:10d}{0:10d}",
        f"{0.0:20g}{0.0:20g}{0.0:20g}{0.0:20g}{0:10d}{0:10d}",
        f"{1.0:20g}{0.0:20g}{0.0:20g}{0.0:20g}{1.0e30:20g}",
        f"{'':7s}{0:1d}{0:1d}{0:1d}{'':20s}{0:10d}{0.0:20g}{0.0:20g}{0.2:20g}",
        f"{0:10d}{0:10d}{0.0:20g}{0:10d}{0:10d}{0:10d}{0.0:20g}{0:10d}",
    ]


def shell_property_lines(property_id: int, title: str, thickness: float) -> list[str]:
    return [
        f"/PROP/SHELL/{property_id}",
        title,
        f"{24:10d}{0:10d}{0:10d}{0:10d}{0:10d}{'':10s}{0.0:20g}",
        fixed_fields(0, 0, 0, 0, 0),
        f"{5:10d}{0:10d}{thickness:20g}{0.0:20g}{'':10s}{0:10d}{0:10d}",
    ]


def write_starter(config: dict, case: dict, output: Path) -> dict:
    facade_mesh = float(case["facade_mesh_target_mm"])
    projectile_mesh = float(case["projectile_mesh_target_mm"])
    facade_geometry = config["facade_geometry"]
    projectile = config["projectile"]
    core = projectile["engine_core"]
    cowling = projectile["cowling"]
    mesh = ShellMesh()
    fixed_nodes = add_facade(mesh, facade_geometry, facade_mesh)
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
    core_thickness = float(core["target_mass_g"]) / (float(core["material"]["density_g_per_mm3"]) * core_area)
    cowling_thickness = float(cowling["target_mass_g"]) / (
        float(cowling["material"]["density_g_per_mm3"]) * cowling_area
    )
    run_name = f"V8V_{case['id']}"

    lines: list[str] = [
        "#RADIOSS STARTER",
        "# V8V deformable contact qualification surrogate; not a WTC impact reconstruction",
        "/BEGIN",
        f"{run_name:<80}",
        f"{2026:10d}{0:10d}",
        fixed_fields("g", "mm", "ms"),
        fixed_fields("g", "mm", "ms"),
        "/TITLE",
        f"{run_name} deformable engine-cowling and three-story facade qualification",
        "/ANALY",
        f"{0:10d}{'':10s}{0:10d}{0:10d}",
        "/DEF_SHELL",
        f"{0:10d}{0:10d}{0:10d}{0:10d}{0:10d}{'':20s}{0:10d}{0:10d}",
        "/SPMD",
        f"{0:10d}{0:10d}{0:20d}{int(case['threads']):20d}",
    ]
    lines += material_lines(1, "NIST-adjacent 60 ksi facade steel; V8V surrogate", config["facade_material"], float(config["facade_material"]["failure_plastic_strain"]))
    lines += material_lines(2, "Equivalent deformable engine-core steel; V8V hypothesis", core["material"], float(case["core_failure_strain"]))
    lines += material_lines(3, "Equivalent deformable cowling aluminum; V8V hypothesis", cowling["material"], float(case["cowling_failure_strain"]))
    lines.append("/NODE")
    for node_id, (x, y, z) in enumerate(mesh.nodes, start=1):
        lines.append(f"{node_id:10d}{x:20.9g}{y:20.9g}{z:20.9g}")

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
    part_specs = (
        (1, "FACADE_COLUMN_SHELLS", 1, 1),
        (2, "FACADE_SPANDREL_SHELLS", 1, 2),
        (3, "DEFORMABLE_ENGINE_CORE_EQUIVALENT", 2, 3),
        (4, "DEFORMABLE_COWLING_EQUIVALENT", 3, 4),
    )
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

    lines += shell_property_lines(1, "FACADE_COLUMN_5_16_IN_QEPH", float(facade_geometry["column_shell_thickness_mm"]))
    lines += shell_property_lines(2, "FACADE_SPANDREL_3_8_IN_QEPH", float(facade_geometry["spandrel_shell_thickness_mm"]))
    lines += shell_property_lines(3, "ENGINE_CORE_EQUIVALENT_MASS_QEPH", core_thickness)
    lines += shell_property_lines(4, "COWLING_EQUIVALENT_MASS_QEPH", cowling_thickness)
    lines += [
        "/GRNOD/PART/20",
        "ALL_PROJECTILE_NODES_FOR_FACADE_CONTACT",
        f"{3:10d}{4:10d}",
        "/GRNOD/PART/21",
        "ALL_PROJECTILE_NODES_FOR_SELF_CONTACT",
        f"{3:10d}{4:10d}",
        "/SURF/PART/30",
        "FACADE_SHELL_SURFACE",
        f"{1:10d}{2:10d}",
        "/SURF/PART/31",
        "PROJECTILE_SHELL_SURFACE",
        f"{3:10d}{4:10d}",
        "/INIVEL/TRA/1",
        "PROJECTILE_INITIAL_TRANSLATIONAL_VELOCITY",
        f"{0.0:20g}{0.0:20g}{float(projectile['initial_velocity_z_mm_per_ms']):20g}{20:10d}{0:10d}",
        f"{0.0:20g}{0:10d}",
    ]
    lines += type7_lines(1, "PROJECTILE_TO_FACADE_DEFORMABLE_CONTACT", 20, 30)
    lines += type7_lines(2, "PROJECTILE_CORE_COWLING_SELF_CONTACT", 21, 31)
    lines += [
        "/TH/INTER/1",
        "TH_FACADE_CONTACT",
        f"{'FNZ':>10}",
        f"{1:10d}",
        "/TH/PART/2",
        "TH_PROJECTILE_PARTS",
        "".join(f"{value:>10}" for value in ("IE", "KE", "ZMOM", "MASS", "HE", "ERODED", "VZ")),
        f"{3:10d}{4:10d}",
        "/END",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    projectile_nodes = mesh.part_nodes(3) | mesh.part_nodes(4)
    metadata = {
        "run_name": run_name,
        "case_id": case["id"],
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
            "core_target_mass_g": float(core["target_mass_g"]),
            "cowling_target_mass_g": float(cowling["target_mass_g"]),
            "total_target_mass_g": float(projectile["total_target_mass_g"]),
        },
    }
    return metadata


def write_engine(config: dict, case: dict, output: Path) -> None:
    run_name = f"V8V_{case['id']}"
    execution = config["execution"]
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
        fixed_fields(execution["termination_time_ms"]),
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
    run_name = f"V8V_{case['id']}"
    metadata = write_starter(config, case, args.output / f"{run_name}_0000.rad")
    write_engine(config, case, args.output / f"{run_name}_0001.rad")
    (args.output / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()
