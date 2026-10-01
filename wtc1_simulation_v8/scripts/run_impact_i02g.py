"""Generate and run immutable IMPACT-I02G M(T) cohesive-seam coupons."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "wtc1_simulation_v8/data/impact_i02g_mt_coupon.json"
RUNTIME = ROOT / "wtc1_simulation_v8/openradioss_runtime/v20260728-win64"
OUTPUT = ROOT / "wtc1_simulation_v8/output/impact_i02g_mt_coupon"


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ff(*values: object) -> str:
    return "".join(f"{value:20.12g}" if isinstance(value, (int, float)) else f"{value:>20}" for value in values)


def ii(*values: object) -> str:
    return "".join(f"{value:10d}" if isinstance(value, int) else f"{value:>10}" for value in values)


def chunks(values: list[int], width: int = 10) -> list[list[int]]:
    return [values[start : start + width] for start in range(0, len(values), width)]


def material_lines(material: dict) -> list[str]:
    return [
        "/MAT/PLAS_JOHNS/1",
        "AA2024_T3_EPP_NO_SHELL_FAILURE",
        ff(material["density_g_per_mm3"], 0),
        ff(material["young_modulus_mpa"], material["poisson_ratio"]) + ii(0),
        ff(material["yield_strength_mpa"], 0, 1, 0, 0),
        ff(0, 0, 0, 0, 0, 0),
        ff(0, 0, 0, 0),
    ]


def shell_property_lines(thickness: float) -> list[str]:
    return [
        "/PROP/SHELL/1",
        "FULLY_INTEGRATED_2024_T3_SHEET",
        f"{24:10d}{-1:10d}{0:10d}{0:10d}{0:10d}{'':10s}{0.0:20g}",
        ff(0, 0, 0, 0, 0),
        f"{5:10d}{'':10s}{thickness:20.12g}",
    ]


def mapped_x(x: float, y: float, width: float, half_length: float, orientation_deg: float) -> float:
    if orientation_deg == 0:
        return x
    edge_fade = max(0.0, 1.0 - (2.0 * x / width) ** 2)
    grip_fade = max(0.0, 1.0 - (abs(y) / half_length) ** 2)
    return x + math.tan(math.radians(orientation_deg)) * y * edge_fade * grip_fade


def add_spring_property(
    lines: list[str],
    property_id: int,
    function_x: int,
    function_y: int,
    kx: float,
    ky: float,
    peak_force: float,
    delta0: float,
    deltaf: float | None,
    non_failing: bool,
) -> None:
    lines += [
        f"/PROP/TYPE8/{property_id}",
        f"COHESIVE_SEAM_NODE_{property_id}",
        ff(0, 0) + ii(1, 0, 0, 0, 0, 1),
    ]
    # Local X: linear tangential transfer without failure.
    lines += [ff(kx, 0, 1, 0, 1), ii(function_x, 2, 0, 0, 0, "") + ff(-1.0e30, 1.0e30), ff(1, 0, 1, 0)]
    # Local Y: normal cohesive traction; either non-failing or triangular softening.
    ymax = 1.0e30 if non_failing else float(deltaf)
    lines += [ff(ky, 0, 1, 0, 1), ii(function_y, 2, 0, 0, 0, "") + ff(-1.0e30, ymax), ff(1, 0, 1, 0)]
    for _ in range(4):
        lines += [ff(0, 0, 1, 0, 1), ii(0, 0, 0, 0, 0, "") + ff(-1.0e30, 1.0e30), ff(1, 0, 1, 0)]
    lines += [ii(0) + ff(1.0e30)]
    limit = 10.0
    lines += [f"/FUNCT/{function_x}", f"SEAM_TANGENTIAL_LINEAR_{property_id}", ff(-limit, -kx * limit), ff(0, 0), ff(limit, kx * limit)]
    lines += [f"/FUNCT/{function_y}", f"SEAM_NORMAL_{property_id}"]
    if non_failing:
        lines += [ff(-limit, -ky * limit), ff(0, 0), ff(limit, ky * limit)]
    else:
        lines += [ff(-limit, -ky * limit), ff(0, 0), ff(delta0, peak_force), ff(float(deltaf), 0), ff(limit, 0)]


def generate(cfg: dict, case: dict, directory: Path) -> dict:
    geometry = cfg["geometry"]
    material = cfg["material"]
    seam = cfg["seam"]
    execution = cfg["execution"]
    width = float(geometry["width_mm"])
    length = float(geometry["length_mm"])
    half_length = length / 2.0
    thickness = float(geometry["thickness_mm"])
    crack_half = float(geometry["initial_total_crack_length_mm"]) / 2.0
    h = float(case["h_mm"])
    nx = round(width / h)
    ny_half = round(half_length / h)
    if not math.isclose(width / nx, h, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("Width must be an integer multiple of h")
    xs = [-width / 2.0 + width * index / nx for index in range(nx + 1)]
    y_lower = [-half_length + half_length * index / ny_half for index in range(ny_half + 1)]
    y_upper = [half_length * index / ny_half for index in range(ny_half + 1)]
    orientation = float(case["mesh_orientation_deg"])
    nodes: list[tuple[float, float, float]] = []
    grids: list[list[list[int]]] = []
    for ys in (y_lower, y_upper):
        grid: list[list[int]] = []
        for y in ys:
            row = []
            for x in xs:
                row.append(len(nodes) + 1)
                nodes.append((mapped_x(x, y, width, half_length, orientation), y, 0.0))
            grid.append(row)
        grids.append(grid)
    shells: list[tuple[int, int, int, int]] = []
    for grid in grids:
        for iy in range(ny_half):
            for ix in range(nx):
                shells.append((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))
    edge_lengths = []
    signed_areas = []
    for quad in shells:
        points = [nodes[node_id - 1] for node_id in quad]
        edge_lengths.extend(
            math.hypot(points[(index + 1) % 4][0] - points[index][0], points[(index + 1) % 4][1] - points[index][1])
            for index in range(4)
        )
        signed_areas.append(
            0.5
            * sum(
                points[index][0] * points[(index + 1) % 4][1]
                - points[(index + 1) % 4][0] * points[index][1]
                for index in range(4)
            )
        )
    lower_seam = grids[0][-1]
    upper_seam = grids[1][0]
    lower_grip = grids[0][0]
    upper_grip = grids[1][-1]
    all_nodes = list(range(1, len(nodes) + 1))
    anchor_node = min(lower_grip, key=lambda node_id: abs(nodes[node_id - 1][0]))
    seam_pairs: list[dict] = []
    ligament_segments = []
    dx = width / nx
    for ix, x in enumerate(xs):
        if abs(x) + 1.0e-9 < crack_half:
            continue
        side = "left" if x < 0 else "right"
        end_weight = 0.5 if math.isclose(abs(x), width / 2.0, abs_tol=1.0e-9) or math.isclose(abs(x), crack_half, abs_tol=1.0e-9) else 1.0
        tributary_width = dx * end_weight
        ligament_segments.append(tributary_width)
        seam_pairs.append({
            "x_mm": x,
            "side": side,
            "lower_node": lower_seam[ix],
            "upper_node": upper_seam[ix],
            "tributary_width_mm": tributary_width,
        })
    expected_ligament_width = width - 2.0 * crack_half
    if not math.isclose(sum(ligament_segments), expected_ligament_width, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("Cohesive tributary widths do not equal intact ligament width")
    mode = case["mode"]
    non_failing = mode in ("elastic", "no_propagation")
    target_displacement = float(execution["elastic_target_displacement_mm"] if mode == "elastic" else execution["fracture_target_displacement_mm"])
    gf = case.get("Gf_N_per_mm")
    deltaf = None if gf is None else 2.0 * float(gf) / float(seam["peak_normal_traction_mpa"])
    name = "I02G_" + case["id"]
    lines = [
        "#RADIOSS STARTER",
        "# NASA-size M(T) geometry with prescribed-path cohesive seam; not calibrated 3D tearing",
        "/BEGIN",
        name,
        ii(2026, 0),
        ff("g", "mm", "ms"),
        ff("g", "mm", "ms"),
        "/TITLE",
        name,
        "/ANALY",
        ii(0, "", 0, 0),
        "/SPMD",
        ii(0, 0) + ff(0, 1),
    ]
    lines += material_lines(material)
    lines += ["/SKEW/FIX/1", "GLOBAL_XY_SEAM_AXES", ff(0, 0, 0), ff(0, 1, 0), ff(0, 0, 1), "/NODE"]
    lines += [ii(node_id) + ff(*xyz) for node_id, xyz in enumerate(nodes, 1)]
    lines += ["/PART/1", "AA2024_T3_MIDDLE_CRACK_SHEET", ii(1, 1, 0), "/SHELL/1"]
    lines += [ii(element_id, *quad) for element_id, quad in enumerate(shells, 1)]
    lines += shell_property_lines(thickness)
    shear_modulus = material["young_modulus_mpa"] / (2.0 * (1.0 + material["poisson_ratio"]))
    spring_ids = []
    for index, pair in enumerate(seam_pairs):
        property_id = 1000 + index
        element_id = len(shells) + index + 1
        function_x = 3000 + 2 * index
        function_y = function_x + 1
        area = thickness * pair["tributary_width_mm"]
        normal_stiffness = material["young_modulus_mpa"] / h * area
        tangent_stiffness = shear_modulus / h * area
        peak_force = seam["peak_normal_traction_mpa"] * area
        delta0 = peak_force / normal_stiffness
        add_spring_property(lines, property_id, function_x, function_y, tangent_stiffness, normal_stiffness, peak_force, delta0, deltaf, non_failing)
        lines += [f"/PART/{property_id}", f"SEAM_CONNECTION_{index}", ii(property_id, 0, 0), f"/SPRING/{property_id}", ii(element_id, pair["lower_node"], pair["upper_node"], 0, 0, 0, 0, "", "", 1)]
        pair.update({
            "element_id": element_id,
            "property_id": property_id,
            "area_mm2": area,
            "normal_stiffness_N_per_mm": normal_stiffness,
            "tangent_stiffness_N_per_mm": tangent_stiffness,
            "peak_force_N": peak_force,
            "delta0_mm": delta0,
            "deltaf_mm": deltaf,
        })
        spring_ids.append(element_id)
    groups = {
        1: ("ALL_SHEET_NODES", all_nodes),
        2: ("LOWER_GRIP", lower_grip),
        3: ("UPPER_GRIP", upper_grip),
        4: ("X_ANCHOR", [anchor_node]),
        5: ("SEAM_NODES", lower_seam + upper_seam),
    }
    for group_id, (title, group_nodes) in groups.items():
        lines += [f"/GRNOD/NODE/{group_id}", title]
        lines += [ii(*group) for group in chunks(group_nodes)]
    lines += [
        "/BCS/1",
        "IN_PLANE_SHELL_MOTION_ONLY",
        f"{'001':>6}{'111':>4}" + ii(0, 1),
        "/BCS/2",
        "FIX_LOWER_GRIP_Y",
        f"{'010':>6}{'000':>4}" + ii(0, 2),
        "/BCS/3",
        "REMOVE_RIGID_X_TRANSLATION",
        f"{'100':>6}{'000':>4}" + ii(0, 4),
    ]
    end_ms = float(execution["end_ms"])
    path = []
    for index in range(401):
        u = index / 400.0
        smooth = 3.0 * u * u - 2.0 * u * u * u
        path.append((u * end_ms, smooth * target_displacement))
    lines += ["/FUNCT/90", "SMOOTH_UPPER_GRIP_DISPLACEMENT"]
    lines += [ff(t, displacement) for t, displacement in path]
    lines += [
        "/IMPDISP/1",
        "UPPER_GRIP_Y_DISPLACEMENT",
        ii(90, "Y", 0, 0, 3, "", 0),
        ff(1, 1, 0, 1.0e30),
        "/TH/PART/1",
        "SHEET_ENERGY_MASS",
        ii("IE", "KE", "MASS", "HE"),
        ii(1),
        "/TH/SPRING/2",
        "SEAM_HISTORY",
        ii("OFF", "FX", "FY", "LX", "LY", "IE"),
    ]
    lines += [ii(element_id, "") + f"SEAM_{index}" for index, element_id in enumerate(spring_ids)]
    lines += ["/TH/NODE/3", "UPPER_GRIP_HISTORY", ii("DY", "VY", "REACY")]
    lines += [ii(node_id, 0) for node_id in upper_grip]
    lines += ["/TH/NODE/4", "SEAM_NODE_HISTORY", ii("DX", "DY")]
    lines += [ii(node_id, 0) for node_id in lower_seam + upper_seam]
    lines += ["/UNIT/1", "I02G_G_MM_MS", ff("g", "mm", "ms"), "/END"]
    starter = directory / f"{name}_0000.rad"
    starter.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    dt_scale = float(case.get("dt_scale", execution["dt_scale"]))
    animation_dt = end_ms / (int(execution["animation_states"]) - 1)
    engine = [
        "/ANIM/DT",
        ff(0, animation_dt),
        "/ANIM/VECT/DISP",
        "/ANIM/VECT/VEL",
        "/ANIM/ELEM/ENER",
        "/DT",
        ff(dt_scale, 0),
        "/MON/ON",
        "/PRINT/-100/100",
        f"/RUN/{name}/1",
        ff(end_ms),
        "/TFILE/4",
        ff(execution["history_dt_ms"]),
        "/VERS/2026",
    ]
    engine_file = directory / f"{name}_0001.rad"
    engine_file.write_text("\n".join(engine) + "\n", encoding="utf-8", newline="\n")
    expected_mass = width * length * thickness * material["density_g_per_mm3"]
    expected_fracture_energy = None if gf is None else float(gf) * expected_ligament_width * thickness * 0.001
    metadata = {
        "name": name,
        "case": case,
        "nodes_mm": nodes,
        "shells": [{"id": element_id, "nodes": quad} for element_id, quad in enumerate(shells, 1)],
        "mesh": {
            "nx": nx,
            "ny_half": ny_half,
            "dx_mm": dx,
            "dy_mm": half_length / ny_half,
            "orientation_deg": orientation,
            "minimum_edge_mm": min(edge_lengths),
            "maximum_edge_mm": max(edge_lengths),
            "minimum_signed_area_mm2": min(signed_areas),
            "maximum_signed_area_mm2": max(signed_areas),
        },
        "seam_pairs": seam_pairs,
        "lower_seam_nodes": lower_seam,
        "upper_seam_nodes": upper_seam,
        "lower_grip_nodes": lower_grip,
        "upper_grip_nodes": upper_grip,
        "anchor_node": anchor_node,
        "target_displacement_mm": target_displacement,
        "loading_path_ms_mm": path,
        "expected_mass_g": expected_mass,
        "expected_intact_ligament_width_mm": expected_ligament_width,
        "cohesive_tributary_width_sum_mm": sum(ligament_segments),
        "expected_full_ligament_fracture_energy_J": expected_fracture_energy,
        "deltaf_mm": deltaf,
        "material": material,
        "generator_sha256": sha(Path(__file__)),
        "config_sha256": sha(CFG),
        "source_sha256": {source["path"]: source["sha256"] for source in cfg["sources"] if "path" in source},
    }
    dump(directory / "generation.json", metadata)
    return metadata


def execute(executable: Path, arguments: list[str], directory: Path, environment: dict, log_name: str, timeout: int) -> dict:
    start = time.perf_counter()
    process = subprocess.run([str(executable), *arguments], cwd=directory, env=environment, capture_output=True, timeout=timeout)
    (directory / log_name).write_bytes(process.stdout + process.stderr)
    record = {
        "command": [str(executable), *arguments],
        "returncode": process.returncode,
        "seconds": time.perf_counter() - start,
        "executable_sha256": sha(executable),
    }
    if process.returncode:
        raise RuntimeError(f"{log_name} failed in {directory}")
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--revision", default="R0")
    args = parser.parse_args()
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    case = next(item for item in cfg["cases"] if item["id"] == args.case).copy()
    case["id"] = case["id"].replace("_R0", "_" + args.revision)
    directory = OUTPUT / case["id"]
    if directory.exists():
        raise RuntimeError("Existing case preserved: " + str(directory))
    directory.mkdir(parents=True)
    metadata = generate(cfg, case, directory)
    environment = os.environ.copy()
    environment.update(
        RAD_CFG_PATH="C:/OpenRadioss/hm_cfg_files",
        RAD_H3D_PATH="C:/OpenRadioss/extlib/h3d/lib/win64",
        OPENRADIOSS_PATH="C:/OpenRadioss",
        OMP_NUM_THREADS=str(cfg["execution"]["threads"]),
        KMP_STACKSIZE="400m",
    )
    records = []
    jobs = [
        ("starter_win64.exe", ["-i", metadata["name"] + "_0000.rad", "-np", "1"], "starter.log"),
        ("engine_win64.exe", ["-i", metadata["name"] + "_0001.rad"], "engine.log"),
        ("th_to_csv_win64.exe", [metadata["name"] + "T01"], "converter.log"),
    ]
    for executable, arguments, log_name in jobs:
        records.append(execute(RUNTIME / executable, arguments, directory, environment, log_name, cfg["execution"]["maximum_case_wall_seconds"]))
        dump(directory / "execution.json", records)
    print(json.dumps({
        "case": case["id"],
        "seconds": sum(record["seconds"] for record in records),
        "nodes": len(metadata["nodes_mm"]),
        "shells": len(metadata["shells"]),
        "seam_springs": len(metadata["seam_pairs"]),
        "expected_mass_g": metadata["expected_mass_g"],
        "deltaf_mm": metadata["deltaf_mm"],
    }))


if __name__ == "__main__":
    main()
