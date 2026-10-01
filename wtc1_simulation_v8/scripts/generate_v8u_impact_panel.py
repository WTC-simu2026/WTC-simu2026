#!/usr/bin/env python3
"""Generate the deterministic V8U OpenRadioss impact-surrogate decks.

The geometry is deliberately small and source-traceable.  It is a solver
qualification surrogate, not an aircraft or full WTC facade reconstruction.
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


class ShellMesh:
    def __init__(self, target_size: float):
        self.target_size = target_size
        self.nodes: list[tuple[float, float, float]] = []
        self.node_index: dict[tuple[float, float, float], int] = {}
        self.shells: dict[int, list[tuple[int, int, int, int]]] = {1: [], 2: []}

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
    ) -> None:
        ulen = math.sqrt(sum(value * value for value in uvec))
        vlen = math.sqrt(sum(value * value for value in vvec))
        nu = max(1, math.ceil(ulen / self.target_size))
        nv = max(1, math.ceil(vlen / self.target_size))
        grid: list[list[int]] = []
        for j in range(nv + 1):
            row: list[int] = []
            fv = j / nv
            for i in range(nu + 1):
                fu = i / nu
                xyz = tuple(
                    origin[k] + fu * uvec[k] + fv * vvec[k] for k in range(3)
                )
                row.append(self.node(xyz))
            grid.append(row)
        for j in range(nv):
            for i in range(nu):
                self.shells[part].append(
                    (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
                )


def generate_geometry(config: dict, mesh_size: float) -> tuple[ShellMesh, list[int]]:
    geometry = config["geometry"]
    mesh = ShellMesh(mesh_size)
    centers = [float(value) for value in geometry["column_centers_x_mm"]]
    width = float(geometry["column_width_mm"])
    depth = float(geometry["column_depth_mm"])
    height = float(geometry["story_height_mm"])
    panel_width = float(geometry["panel_width_mm"])
    spandrel_height = float(geometry["spandrel_height_mm"])
    y_breaks = [-height / 2.0, -spandrel_height / 2.0, spandrel_height / 2.0, height / 2.0]

    # Closed square shell columns.  Each vertical face is segmented at the
    # spandrel boundaries so shared-node weld lines remain conforming.
    for center in centers:
        x0, x1 = center - width / 2.0, center + width / 2.0
        for ya, yb in zip(y_breaks[:-1], y_breaks[1:]):
            dy = yb - ya
            mesh.rectangle((x0, ya, 0.0), (width, 0.0, 0.0), (0.0, dy, 0.0), 1)
            mesh.rectangle((x1, ya, depth), (-width, 0.0, 0.0), (0.0, dy, 0.0), 1)
            mesh.rectangle((x0, ya, depth), (0.0, 0.0, -depth), (0.0, dy, 0.0), 1)
            mesh.rectangle((x1, ya, 0.0), (0.0, 0.0, depth), (0.0, dy, 0.0), 1)

    # Front spandrel strip fills only the gaps and panel overhangs.  Column
    # front faces occupy the overlap zones, avoiding duplicate coincident shells.
    column_intervals = sorted((center - width / 2.0, center + width / 2.0) for center in centers)
    x_segments: list[tuple[float, float]] = []
    cursor = -panel_width / 2.0
    for left, right in column_intervals:
        if left > cursor:
            x_segments.append((cursor, left))
        cursor = max(cursor, right)
    if cursor < panel_width / 2.0:
        x_segments.append((cursor, panel_width / 2.0))
    for xa, xb in x_segments:
        mesh.rectangle(
            (xa, -spandrel_height / 2.0, 0.0),
            (xb - xa, 0.0, 0.0),
            (0.0, spandrel_height, 0.0),
            2,
        )

    fixed: list[int] = []
    tolerance = 1.0e-5
    for node_id, (_, y, _) in enumerate(mesh.nodes, start=1):
        if abs(abs(y) - height / 2.0) <= tolerance:
            fixed.append(node_id)
    return mesh, fixed


def fixed_fields(*values: object, width: int = 20) -> str:
    return "".join(f"{str(value):>{width}}" for value in values)


def write_starter(config: dict, case: dict, output: Path) -> dict:
    mesh_size = float(case["mesh_target_mm"])
    failure_strain = float(case["failure_strain"])
    mesh, fixed_nodes = generate_geometry(config, mesh_size)
    geometry = config["geometry"]
    material = config["material"]
    projectile = config["projectile"]
    run_name = f"V8U_{case['id']}"
    reference_node = len(mesh.nodes) + 1

    lines: list[str] = [
        "#RADIOSS STARTER",
        "# V8U source-traceable solver-qualification surrogate; not a WTC impact reconstruction",
        "/BEGIN",
        f"{run_name:<80}",
        f"{2019:10d}{0:10d}",
        fixed_fields("g", "mm", "ms"),
        fixed_fields("g", "mm", "ms"),
        "/TITLE",
        f"{run_name} rigid-sphere facade-surrogate qualification",
        "/ANALY",
        f"{0:10d}{'':10s}{0:10d}{0:10d}",
        "/DEF_SHELL",
        f"{0:10d}{0:10d}{0:10d}{0:10d}{0:10d}{'':20s}{0:10d}{0:10d}",
        "/SPMD",
        f"{0:10d}{0:10d}{0:20d}{int(case['threads']):20d}",
        "/MAT/PLAS_JOHNS/1",
        "NIST-adjacent 60 ksi perimeter-column steel; V8U surrogate",
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
        "/NODE",
    ]
    for node_id, (x, y, z) in enumerate(mesh.nodes, start=1):
        lines.append(f"{node_id:10d}{x:20.9g}{y:20.9g}{z:20.9g}")
    sphere_center_z = float(projectile["diameter_mm"]) / 2.0
    lines.append(f"{reference_node:10d}{0.0:20.9g}{0.0:20.9g}{sphere_center_z:20.9g}")

    lines += [
        "/BCS/1",
        "FIXED_COLUMN_ENDS",
        f"{'111':>6}{'111':>4}{0:10d}{2:10d}",
        "/GRNOD/NODE/2",
        "FIXED_COLUMN_ENDS",
    ]
    for group in chunks(fixed_nodes):
        lines.append("".join(f"{value:10d}" for value in group))

    element_id = 1
    for part_id, title in ((1, "COLUMN_SHELLS"), (2, "SPANDREL_SHELLS")):
        lines += [
            f"/PART/{part_id}",
            title,
            f"{part_id:10d}{1:10d}{0:10d}",
            f"/SHELL/{part_id}",
        ]
        for shell in mesh.shells[part_id]:
            lines.append(f"{element_id:10d}" + "".join(f"{node:10d}" for node in shell))
            element_id += 1

    lines += [
        "/PROP/SHELL/1",
        "COLUMN_5_16_IN_QEPH",
        f"{24:10d}{0:10d}{0:10d}{0:10d}",
        fixed_fields(0, 0, 0, 0, 0),
        f"{5:10d}{0:10d}{float(geometry['column_shell_thickness_mm']):20g}{0:20g}{1:10d}",
        "/PROP/SHELL/2",
        "SPANDREL_3_8_IN_QEPH",
        f"{24:10d}{0:10d}{0:10d}{0:10d}",
        fixed_fields(0, 0, 0, 0, 0),
        f"{5:10d}{0:10d}{float(geometry['spandrel_shell_thickness_mm']):20g}{0:20g}{1:10d}",
        "/RWALL/SPHER/1",
        "RIGID_ENGINE_MASS_SURROGATE",
        f"{reference_node:10d}{0:10d}{1:10d}{2:10d}",
        f"{0:20g}{0:20g}{float(projectile['diameter_mm']):20g}{0:20g}{0:10d}",
        fixed_fields(projectile["mass_g"], 0, 0, projectile["initial_velocity_z_mm_per_ms"]),
        "/GRNOD/PART/1",
        "ALL_FACADE_SURROGATE_NODES",
        f"{1:10d}{2:10d}",
        "/TH/RWALL/1",
        "TH_RWALL_ENGINE_SURROGATE",
        "FNZ",
        f"{1:10d}",
        "/END",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return {
        "run_name": run_name,
        "case_id": case["id"],
        "mesh_target_mm": mesh_size,
        "failure_strain": failure_strain,
        "threads": int(case["threads"]),
        "node_count_target": len(mesh.nodes),
        "node_count_total": len(mesh.nodes) + 1,
        "shell_count_columns": len(mesh.shells[1]),
        "shell_count_spandrel": len(mesh.shells[2]),
        "shell_count_total": len(mesh.shells[1]) + len(mesh.shells[2]),
        "fixed_node_count": len(fixed_nodes),
        "reference_node": reference_node,
    }


def write_engine(config: dict, case: dict, output: Path) -> None:
    run_name = f"V8U_{case['id']}"
    execution = config["execution"]
    lines = [
        "/ANIM/DT",
        fixed_fields(0, execution["animation_interval_ms"]),
        "/ANIM/SHELL/EPSP/ALL",
        "/ANIM/SHELL/DAMA",
        "/ANIM/VECT/VEL",
        "/ANIM/VECT/DISP",
        "/ANIM/GZIP",
        "/MON/ON",
        "/PRINT/-100/100",
        f"/RUN/{run_name}/1",
        fixed_fields(execution["termination_time_ms"]),
        "/TFILE/4",
        fixed_fields(execution["time_history_interval_ms"]),
        "/VERS/2019",
    ]
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    case = next((item for item in config["cases"] if item["id"] == args.case_id), None)
    if case is None:
        raise SystemExit(f"Unknown case: {args.case_id}")
    args.output.mkdir(parents=True, exist_ok=True)
    run_name = f"V8U_{case['id']}"
    metadata = write_starter(config, case, args.output / f"{run_name}_0000.rad")
    write_engine(config, case, args.output / f"{run_name}_0001.rad")
    (args.output / "generation_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(metadata, separators=(",", ":")))


if __name__ == "__main__":
    main()
